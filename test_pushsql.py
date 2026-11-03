# The notifications' SQL (sql/2026-11-03-push.sql) on a local Postgres, after supabase-setup.sql, with a stand-in
# for pg_net that only writes down each knock: who may see which phones, and when the helper is woken.
import psycopg2, uuid, subprocess, json
subprocess.run(['su','postgres','-c',"psql -q -c 'drop database if exists sbp' -c 'create database sbp'"],check=True,capture_output=True)
c=psycopg2.connect(dbname='sbp',user='tester',password='t',host='localhost'); c.autocommit=True; cur=c.cursor()
STUB=open('test_sql.py',encoding='utf-8').read().split('STUB="""')[1].split('"""')[0]
cur.execute(STUB)
cur.execute("""create schema extensions; create schema net; create table net.calls(body jsonb, url text, headers jsonb);
create function net.http_post(url text, body jsonb default '{}', params jsonb default '{}', headers jsonb default '{}', timeout_milliseconds int default 1000) returns bigint
 language sql as $$ insert into net.calls values (body, url, headers) returning 1::bigint $$;
grant usage on schema net to anon, authenticated; grant insert on net.calls to anon, authenticated; grant execute on function net.http_post to anon, authenticated;""")
sql=open(('setup.sql' if __import__('os').path.exists('setup.sql') else 'supabase-setup.sql'),encoding='utf-8').read(); cur.execute(sql)
P=open(('2026-11-03-push.sql' if __import__('os').path.exists('2026-11-03-push.sql') else 'sql/2026-11-03-push.sql'),encoding='utf-8').read().split('end $$;',1)[1]   # pg_net itself is the stand-in above
cur.execute(P); cur.execute(P)   # twice: must be safe to re-run
A,B=[str(uuid.uuid4()) for _ in range(2)]
for u in (A,B): cur.execute("insert into auth.users values (%s)",(u,))
fails=0
def check(n,got,exp):
    global fails; ok=got==exp; fails+=not ok
    print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
def as_(u,q,args=()):
    cur.execute("begin"); cur.execute("set local role authenticated"); cur.execute("select set_config('request.jwt.claim.sub',%s,true)",(u,))
    try:
        cur.execute(q,args); r=cur.fetchall() if cur.description else cur.rowcount; cur.execute("commit"); return r
    except Exception as e:
        cur.execute("rollback"); return 'ERR: '+str(e).split('\n')[0]
calls=lambda:(cur.execute("select body from net.calls"),[r[0] for r in cur.fetchall()])[1]
as_(A,"insert into public.push_subs(endpoint,p256dh,auth) values ('https://x/1','k','a')")
check('Q1 a phone saves its own subscription (four kinds on by default; „Браво“ off)', as_(A,"select kinds from public.push_subs"), [(['ask','idp','inv','comment'],)])
check('Q2 nobody else sees or changes it', (as_(B,"select count(*) from public.push_subs"),as_(B,"update public.push_subs set kinds='{}'"),as_(B,"delete from public.push_subs")), ([(0,)],0,0))
check('Q3 nor can anyone save one in someone else\'s name', as_(B,"insert into public.push_subs(user_id,endpoint,p256dh,auth) values (%s,'https://x/2','k','a')",(A,))[:4], 'ERR:')
check('Q4 the same phone again just updates its kinds', (as_(A,"insert into public.push_subs(endpoint,p256dh,auth,kinds) values ('https://x/1','k','a','{ask}') on conflict (user_id,endpoint) do update set kinds=excluded.kinds"),as_(A,"select kinds from public.push_subs")), (1,[(['ask'],)]))
closed=lambda r:r==[(0,)] or str(r).startswith('ERR: permission denied')   # no rows (Supabase grants, no rules) or no access at all
check('Q5 the helper\'s keys and memory are closed to everyone', (closed(as_(A,"select count(*) from public.push_keys")),closed(as_(A,"select count(*) from public.push_state"))), (True,True))
cur.execute("delete from net.calls")
J=lambda d:json.dumps(d,ensure_ascii=False)
as_(A,"insert into public.journals(user_id,data) values (%s,%s)",(A,J({'obs':[{'id':1,'bg':'Кос'}],'outs':[]})))
n1=len(calls())
as_(A,"update public.journals set data=%s where user_id=%s",(J({'obs':[{'id':1,'bg':'Кос','note':'пее'}],'outs':[]}),A))
n2=len(calls())
as_(A,"update public.journals set data=%s where user_id=%s",(J({'obs':[{'id':1,'bg':'Кос'},{'id':2,'bg':'Непозната птица','ask':5}],'outs':[]}),A))
n3=len(calls())
as_(A,"update public.journals set data=%s where user_id=%s",(J({'obs':[{'id':1,'bg':'Кос'},{'id':2,'bg':'Червеногръдка','askOk':{'by':B}}],'outs':[{'id':'s1','inv':{B:7}}]}),A))
n4=len(calls())
check('Q6 the helper is woken on a new journal, not on ordinary edits, and on new questions, answers and invitations', (n1,n2,n3,n4), (1,1,2,3))
check('Q7 the knock carries only who, never the content', calls()[-1], {'table':'journals','owner':A})
cur.execute("select url, headers->>'apikey' from net.calls order by ctid desc limit 1")
check('Q7b ...to the helper\'s address, with the project\'s publishable key (Supabase now requires one)', cur.fetchone(), ('https://szyituwdlbwpqkfuklxq.supabase.co/functions/v1/push','sb_publishable_B74aN3lH5shn4ECtrTYsTw_I4OAhL4M'))
cur.execute("insert into public.viewers(owner,viewer) values (%s,%s)",(A,B))   # (in the app this happens through the friend code)
as_(B,"insert into public.social(owner,item,kind,body) values (%s,'q:2','comment','🔎 Червеногръдка (Erithacus rubecula)')",(A,))
last=calls()[-1]
check('Q8 a new comment, suggestion or bravo wakes it with just the row\'s number', (last['table'],len(last['id'])), ('social',36))
cur.execute("drop function net.http_post(text,jsonb,jsonb,jsonb,int)")
check('Q9 if the knock itself fails, saving the journal still works', as_(A,"update public.journals set data=%s where user_id=%s",(J({'obs':[{'id':3,'ask':1}],'outs':[]}),A)), 1)
print('FAILURES:',fails)
