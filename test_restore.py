# The backup's restore path, rehearsed on a local Postgres with Supabase stand-ins:
# dump the way the backup job does (structure of the app's tables; data of the app's tables AND the accounts),
# restore into a fresh database with the documented psql command, and check nothing is lost.
import psycopg2, uuid, subprocess, os, json
fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
def pg(cmd):return subprocess.run(['su','postgres','-c',cmd],capture_output=True,text=True)
STUB=open('test_sql.py',encoding='utf-8').read().split('STUB="""',1)[1].split('"""',1)[0]
for db in ('bk_src','bk_dst'):pg(f"psql -q -c 'drop database if exists {db}' -c 'create database {db}'")
def conn(db):c=psycopg2.connect(dbname=db,user='tester',password='t',host='localhost');c.autocommit=True;return c,c.cursor()
c,cur=conn('bk_src');cur.execute(STUB);cur.execute(open(('setup.sql' if __import__('os').path.exists('setup.sql') else 'supabase-setup.sql'),encoding='utf-8').read())
A,B=[str(uuid.uuid4()) for _ in range(2)]
for u,n in ((A,'Иван'),(B,'Петър')):
  cur.execute("insert into auth.users values (%s)",(u,));cur.execute("insert into public.profiles(user_id,name) values (%s,%s)",(u,n))
cur.execute("insert into public.journals(user_id,data) values (%s,%s)",(A,json.dumps({'v':6,'obs':[{'id':1,'bg':'Кос','date':'2026-10-30'}]},ensure_ascii=False)))
cur.execute("insert into public.journals(user_id,data) values (%s,%s)",(B,json.dumps({'v':6,'obs':[]})))
cur.execute("insert into public.viewers(owner,viewer) values (%s,%s),(%s,%s)",(A,B,B,A))
cur.execute("insert into public.social(owner,item,author,kind,body) values (%s,'d:2026-10-30',%s,'comment','Браво за коса!')",(A,B))
cur.execute("insert into public.xc_cache(sp,data) values ('Turdus merula','{\"song\":null,\"call\":null}')")
codeA=cur.execute("select code from public.profiles where user_id=%s",(A,)) or cur.fetchone()[0]
tables=['profiles','viewers','journals','social','xc_cache']
before={t:(cur.execute(f"select count(*) from public.{t}") or cur.fetchone()[0]) for t in tables}
before['auth.users']=cur.execute("select count(*) from auth.users") or cur.fetchone()[0]
c.close()
os.makedirs('/tmp/bk',exist_ok=True);os.chmod('/tmp/bk',0o777)
r1=pg("pg_dump --schema-only --schema=public --no-owner -f /tmp/bk/schema.sql bk_src")
r2=pg("pg_dump --data-only --schema=public --schema=auth --no-owner -f /tmp/bk/data.sql bk_src")
# the Supabase CLI's schema dump leaves out „CREATE SCHEMA public“ (every project has it); plain pg_dump doesn't
sch=open('/tmp/bk/schema.sql',encoding='utf-8').read().replace('CREATE SCHEMA public;','');open('/tmp/bk/schema.sql','w',encoding='utf-8').write(sch)
data=open('/tmp/bk/data.sql',encoding='utf-8').read()
check('K1 the copy holds the accounts too, not only the app\'s tables', ('COPY auth.users' in data or 'INSERT INTO auth.users' in data,r1.returncode,r2.returncode), (True,0,0))
c,cur=conn('bk_dst');cur.execute(STUB);c.close()   # a fresh Supabase project already has its own auth and storage
r=pg("psql -q --single-transaction --variable ON_ERROR_STOP=1 --file /tmp/bk/schema.sql --command 'SET session_replication_role = replica' --file /tmp/bk/data.sql --dbname bk_dst")
check('K2 the documented restore command runs cleanly into a fresh database', (r.returncode,r.stderr.strip()[:200]), (0,''))
c,cur=conn('bk_dst')
after={t:(cur.execute(f"select count(*) from public.{t}") or cur.fetchone()[0]) for t in tables}
after['auth.users']=cur.execute("select count(*) from auth.users") or cur.fetchone()[0]
check('K3 every table comes back with every row', after, before)
cur.execute("select data->'obs'->0->>'bg' from public.journals where user_id=%s",(A,))
check('K4 the journal itself is intact (Cyrillic and all)', cur.fetchone()[0], 'Кос')
cur.execute("select code from public.profiles where user_id=%s",(A,))
check('K5 friend codes survive, so friendships keep working', cur.fetchone()[0], codeA)
cur.execute("select count(*) from pg_policies where schemaname='public'");pol=cur.fetchone()[0]
cur.execute("select count(*) from pg_class c join pg_namespace n on n.oid=c.relnamespace where n.nspname='public' and c.relkind='r' and c.relrowsecurity");rls=cur.fetchone()[0]
check('K6 the access rules come back too: row security on every table, and its policies', (rls,pol>=8), (6,True))   # six tables since app_errors (2026-11-02.7)
cur.execute("begin");cur.execute("set local role authenticated");cur.execute("select set_config('request.jwt.claim.sub',%s,true)",(B,))
cur.execute("select count(*) from public.journals");seen=cur.fetchone()[0];cur.execute("rollback")
check('K7 ...and they work: Petar, Ivan\'s friend, sees both journals after the restore', seen, 2)
c.close()
for db in ('bk_src','bk_dst'):pg(f"psql -q -c 'drop database if exists {db}'")
print('FAILURES:',fails)
