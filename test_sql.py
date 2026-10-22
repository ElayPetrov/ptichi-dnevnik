# Runs supabase-setup.sql against a local Postgres with stand-ins for Supabase's auth and storage
# schemas, then checks the access rules the way three users would hit them.
import psycopg2, uuid, subprocess
subprocess.run(['su','postgres','-c',"psql -q -c 'drop database if exists sb' -c 'create database sb'"],check=True,capture_output=True)
# tester role created beforehand
c=psycopg2.connect(dbname='sb',user='tester',password='t',host='localhost'); c.autocommit=True; cur=c.cursor()
STUB="""
do $$ begin if not exists (select from pg_roles where rolname='anon') then create role anon nologin; end if;
 if not exists (select from pg_roles where rolname='authenticated') then create role authenticated nologin; end if; end $$;
create schema auth; create table auth.users(id uuid primary key);
create function auth.uid() returns uuid language sql stable as $$ select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid $$;
grant usage on schema auth to anon, authenticated; grant execute on function auth.uid() to anon, authenticated;
create schema storage;
create table storage.buckets(id text primary key, name text not null, public boolean default false, file_size_limit bigint, allowed_mime_types text[]);
create table storage.objects(id uuid primary key default gen_random_uuid(), bucket_id text references storage.buckets(id), name text not null);
alter table storage.objects enable row level security;
create function storage.foldername(name text) returns text[] language sql immutable as $$ select (string_to_array(name,'/'))[1:array_length(string_to_array(name,'/'),1)-1] $$;
grant usage on schema storage to anon, authenticated; grant select, insert, update, delete on storage.objects to authenticated;
grant execute on function storage.foldername(text) to anon, authenticated;
grant usage on schema public to anon, authenticated;
"""
cur.execute(STUB)
sql=open('supabase-setup.sql',encoding='utf-8').read()
cur.execute(sql); cur.execute(sql)   # twice: must be safe to re-run
A,B,C=[str(uuid.uuid4()) for _ in range(3)]
for u in (A,B,C): cur.execute("insert into auth.users values (%s)",(u,))
fails=0
def check(n,got,exp):
    global fails; ok=got==exp; fails+=not ok
    print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
def as_(u,q,args=(),role='authenticated'):
    cur.execute("begin"); cur.execute(f"set local role {role}")
    if u: cur.execute("select set_config('request.jwt.claim.sub',%s,true)",(u,))
    try:
        cur.execute(q,args); r=cur.fetchall() if cur.description else cur.rowcount; cur.execute("commit"); return r
    except Exception as e:
        cur.execute("rollback"); return 'ERR: '+str(e).split('\n')[0]
for u,n in ((A,'Иван'),(B,'Петър'),(C,'Непознат')): as_(u,"insert into public.profiles(user_id,name) values (%s,%s)",(u,n))
codeA=as_(A,"select public.my_code()")[0][0]
check('S1 own profile gets a 12-character code', (len(codeA),codeA.isalnum()), (12,True))
check('S2 cannot create a profile for someone else', as_(A,"insert into public.profiles(user_id,name) values (%s,'x')",(C,))[:4], 'ERR:')
check('S3 write own journal', as_(A,"insert into public.journals(user_id,data) values (%s,%s)",(A,'{"v":5,"obs":[{"id":1,"bg":"Сврака"}]}')), 1)
check("S4 cannot write someone else's journal", as_(B,"insert into public.journals(user_id,data) values (%s,'{}')",(A,))[:4], 'ERR:')
check('S5 a stranger sees nothing', as_(B,"select count(*) from public.journals where user_id=%s",(A,))[0][0], 0)
check('S6 own code is refused', as_(A,"select public.follow(%s)",(codeA,))[:20], 'ERR: own code')
check('S7 wrong code is refused', as_(B,"select public.follow('NOPE00000000')")[:20], 'ERR: unknown code')
check('S8 code works with dashes and lowercase', as_(B,"select public.follow(%s)",(codeA[:4].lower()+'-'+codeA[4:8]+'-'+codeA[8:],))[0][0], A)
check("S9 after following: B reads A's journal and name", (as_(B,"select data->'obs'->0->>'bg' from public.journals where user_id=%s",(A,))[0][0],as_(B,"select name from public.profiles where user_id=%s",(A,))[0][0]), ('Сврака','Иван'))
check("S10 ...but cannot change it", as_(B,"update public.journals set data='{}' where user_id=%s",(A,)), 0)
check("S11 A sees who follows and their name", as_(A,"select v.viewer, p.name from public.viewers v join public.profiles p on p.user_id=v.viewer where v.owner=%s",(A,)), [(B,'Петър')])
check("S12 the third user still sees nothing", as_(C,"select count(*) from public.journals where user_id=%s",(A,))[0][0], 0)
check("S13 nobody can add a viewer link directly", as_(C,"insert into public.viewers(owner,viewer) values (%s,%s)",(A,C))[:4], 'ERR:')
check("S14 anonymous requests see no journals", as_(None,"select count(*) from public.journals",role='anon')[:4], 'ERR:')
check("S15 the keep-alive ping works without signing in", type(as_(None,"select public.ping()",role='anon')[0][0]).__name__, 'datetime')
check("S16 upload into own photo folder", as_(A,"insert into storage.objects(bucket_id,name) values ('photos',%s)",(A+'/ph1.jpg',)), 1)
check("S17 cannot upload into someone else's folder", as_(A,"insert into storage.objects(bucket_id,name) values ('photos',%s)",(B+'/ph1.jpg',))[:4], 'ERR:')
check("S18 follower sees the photo, stranger does not", (as_(B,"select count(*) from storage.objects where name=%s",(A+'/ph1.jpg',))[0][0],as_(C,"select count(*) from storage.objects where name=%s",(A+'/ph1.jpg',))[0][0]), (1,0))
as_(A,"delete from public.viewers where owner=%s and viewer=%s",(A,B))
check("S19 A removes B: journal and photos are closed again", (as_(B,"select count(*) from public.journals where user_id=%s",(A,))[0][0],as_(B,"select count(*) from storage.objects where name=%s",(A+'/ph1.jpg',))[0][0]), (0,0))
cur.execute("update public.journals set updated_at='2000-01-01' where user_id=%s",(A,)); as_(A,"update public.journals set data='{\"v\":5}' where user_id=%s",(A,))
cur.execute("select updated_at > now() - interval '1 minute' from public.journals where user_id=%s",(A,))
check("S20 server stamps the time of every save", cur.fetchone()[0], True)
check("S21 a profile's code column is not readable, even your own via select", as_(A,"select code from public.profiles where user_id=%s",(A,))[:4], 'ERR:')
as_(B,"select public.follow(%s)",(codeA,))   # B follows A again, so A can now see B's profile
check("S22 ...so the person you share with cannot pick up your code to follow you back", (as_(A,"select name from public.profiles where user_id=%s",(B,)),as_(A,"select code from public.profiles where user_id=%s",(B,))[:4]), ([('Петър',)],'ERR:'))
newA=as_(A,"select public.new_code()")[0][0]
check("S23 a new code replaces the old one; the old one stops working", (newA!=codeA,as_(C,"select public.follow(%s)",(codeA,))[:22],as_(C,"select public.follow(%s)",(newA,))[0][0]), (True,'ERR: unknown code',A))
check("S24 cannot rename someone else", as_(B,"update public.profiles set name='x' where user_id=%s",(A,)), 0)
print('FAILURES:',fails)
