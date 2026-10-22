# A small stand-in for Supabase: real Postgres + real PostgREST (so the real policies and REST rules apply),
# with sign-up/sign-in and file storage imitated closely enough for supabase-js to talk to them.
import base64,hmac,hashlib,json,time,uuid,subprocess,os,urllib.request,urllib.error,psycopg2,re
SECRET='test-secret-for-postgrest-at-least-32-characters'
def b64(b): return base64.urlsafe_b64encode(b).rstrip(b'=').decode()
def make_jwt(p): h=b64(b'{"alg":"HS256","typ":"JWT"}');q=b64(json.dumps(p).encode());return h+'.'+q+'.'+b64(hmac.new(SECRET.encode(),(h+'.'+q).encode(),hashlib.sha256).digest())
def read_jwt(t):
    try:
        h,q,s=t.split('.');assert b64(hmac.new(SECRET.encode(),(h+'.'+q).encode(),hashlib.sha256).digest())==s
        return json.loads(base64.urlsafe_b64decode(q+'='*(-len(q)%4)))
    except Exception: return None
STUB="""
do $$ begin
 if not exists (select from pg_roles where rolname='anon') then create role anon nologin; end if;
 if not exists (select from pg_roles where rolname='authenticated') then create role authenticated nologin; end if;
 if not exists (select from pg_roles where rolname='authenticator') then create role authenticator login noinherit password 'auth'; end if; end $$;
grant anon, authenticated to authenticator;
create schema auth; create table auth.users(id uuid primary key, email text unique, pw text, confirmed boolean default false, meta jsonb default '{}');
create function auth.uid() returns uuid language sql stable as $$
  select coalesce(nullif(current_setting('request.jwt.claim.sub', true), ''), (nullif(current_setting('request.jwt.claims', true), '')::jsonb ->> 'sub'))::uuid $$;
grant usage on schema auth to anon, authenticated; grant execute on function auth.uid() to anon, authenticated;
create schema storage;
create table storage.buckets(id text primary key, name text not null, public boolean default false, file_size_limit bigint, allowed_mime_types text[]);
create table storage.objects(id uuid primary key default gen_random_uuid(), bucket_id text references storage.buckets(id), name text not null, unique(bucket_id,name));
alter table storage.objects enable row level security;
create function storage.foldername(name text) returns text[] language sql immutable as $$ select (string_to_array(name,'/'))[1:array_length(string_to_array(name,'/'),1)-1] $$;
grant usage on schema storage to anon, authenticated; grant select, insert, update, delete on storage.objects to authenticated;
grant execute on function storage.foldername(text) to anon, authenticated;
grant usage on schema public to anon, authenticated;
"""
class Stack:
    def __init__(self,sql_path,port=3333):
        subprocess.run(['su','postgres','-c',"psql -q -c 'drop database if exists sbt' -c 'create database sbt'"],check=True,capture_output=True)
        self.db=psycopg2.connect(dbname='sbt',user='tester',password='t',host='localhost');self.db.autocommit=True
        c=self.db.cursor();c.execute(STUB);c.execute(open(sql_path,encoding='utf-8').read())
        open('/tmp/pgrst.conf','w').write(f'db-uri = "postgres://authenticator:auth@localhost:5432/sbt"\ndb-schemas = "public"\ndb-anon-role = "anon"\njwt-secret = "{SECRET}"\nserver-port = {port}\n')
        self.p=subprocess.Popen(['/home/claude/sb/postgrest','/tmp/pgrst.conf'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);self.port=port
        for _ in range(100):   # until the schema cache is loaded (503 before that)
            try: urllib.request.urlopen(f'http://localhost:{port}/rpc/ping');break
            except urllib.error.HTTPError as e:
                if e.code!=503: break
                time.sleep(.2)
            except Exception: time.sleep(.2)
        self.files={};self.refresh={};self.calls=[]
    def stop(self): self.p.terminate();self.db.close()
    def confirm(self,email): self.db.cursor().execute("update auth.users set confirmed=true where email=%s",(email,))
    def journal(self,uid):
        c=self.db.cursor();c.execute("select data from public.journals where user_id=%s",(uid,));r=c.fetchone();return r and r[0]
    def uid(self,email):
        c=self.db.cursor();c.execute("select id::text from auth.users where email=%s",(email,));r=c.fetchone();return r and r[0]
    def as_user(self,sub,q,args=()):
        c=self.db.cursor();c.execute("begin");c.execute("set local role authenticated")
        c.execute("select set_config('request.jwt.claims',%s,true)",(json.dumps({'sub':sub,'role':'authenticated'}),))
        try: c.execute(q,args);r=c.fetchall() if c.description else c.rowcount;c.execute("commit");return r
        except Exception as e: c.execute("rollback");return e
    # --- auth ---
    def user_obj(self,uid,email,meta):
        now=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())
        return {'id':uid,'aud':'authenticated','role':'authenticated','email':email,'email_confirmed_at':now,'user_metadata':meta,'app_metadata':{'provider':'email','providers':['email']},
                'identities':[{'identity_id':str(uuid.uuid4()),'id':uid,'user_id':uid,'identity_data':{'email':email,'sub':uid},'provider':'email','created_at':now}],'created_at':now,'updated_at':now}
    def session(self,uid,email,meta):
        exp=int(time.time())+3600;rt=uuid.uuid4().hex;self.refresh[rt]=(uid,email,meta)
        return {'access_token':make_jwt({'sub':uid,'role':'authenticated','aud':'authenticated','email':email,'exp':exp}),'token_type':'bearer','expires_in':3600,'expires_at':exp,'refresh_token':rt,'user':self.user_obj(uid,email,meta)}
    def auth(self,method,path,qs,body,hdr):
        c=self.db.cursor()
        if path=='/signup':
            c.execute("select 1 from auth.users where email=%s",(body['email'],))
            if c.fetchone(): return 422,{'code':422,'error_code':'user_already_exists','msg':'User already registered'}
            if len(body.get('password',''))<6: return 422,{'code':422,'error_code':'weak_password','msg':'Password should be at least 6 characters.'}
            uid=str(uuid.uuid4());meta=body.get('data') or {}
            c.execute("insert into auth.users(id,email,pw,meta) values (%s,%s,%s,%s)",(uid,body['email'],body['password'],json.dumps(meta)))
            u=self.user_obj(uid,body['email'],meta);u['email_confirmed_at']=None;u['confirmation_sent_at']=u['created_at'];return 200,u
        if path=='/token' and 'grant_type=password' in qs:
            c.execute("select id::text,pw,confirmed,meta from auth.users where email=%s",(body.get('email'),));r=c.fetchone()
            if not r or r[1]!=body.get('password'): return 400,{'code':400,'error_code':'invalid_credentials','msg':'Invalid login credentials'}
            if not r[2]: return 400,{'code':400,'error_code':'email_not_confirmed','msg':'Email not confirmed'}
            return 200,self.session(r[0],body['email'],r[3])
        if path=='/token' and 'grant_type=refresh_token' in qs:
            t=self.refresh.get(body.get('refresh_token'))
            return (200,self.session(*t)) if t else (400,{'code':400,'error_code':'refresh_token_not_found','msg':'Invalid Refresh Token'})
        if path=='/user':
            p=read_jwt(hdr.get('authorization','')[7:]) or {}
            c.execute("select email,meta from auth.users where id::text=%s",(p.get('sub'),));r=c.fetchone()
            return (200,self.user_obj(p['sub'],r[0],r[1])) if r else (401,{'msg':'bad jwt'})
        if path=='/logout': return 204,None
        return 404,{'msg':'not handled '+path}
    # --- storage (rules checked by the real storage policies, as the signed-in user) ---
    def storage(self,method,path,body,hdr):
        p=read_jwt(hdr.get('authorization','')[7:]) or {};sub=p.get('sub')
        if not sub: return 400,{'statusCode':'403','error':'Unauthorized','message':'no user'}
        m=re.match(r'/object/list/([^/]+)$',path)
        if m and method=='POST':
            pre=(json.loads(body or b'{}').get('prefix') or '').strip('/')
            r=self.as_user(sub,"select name from storage.objects where bucket_id=%s and name like %s",(m.group(1),pre+'/%'))
            return 200,[{'name':n[len(pre)+1:],'id':str(uuid.uuid4()),'metadata':{}} for (n,) in r]
        m=re.match(r'/object/([^/]+)$',path)
        if m and method=='DELETE':
            names=json.loads(body).get('prefixes',[])
            r=self.as_user(sub,"delete from storage.objects where bucket_id=%s and name = any(%s) returning name",(m.group(1),names))
            for (n,) in r: self.files.pop(n,None)
            return 200,[{'name':n} for (n,) in r]
        m=re.match(r'/object/([^/]+)/(.+)$',path)
        if m and method in ('POST','PUT'):
            b,n=m.group(1),m.group(2)
            ex=self.as_user(sub,"select 1 from storage.objects where bucket_id=%s and name=%s",(b,n))
            r=self.as_user(sub,"update storage.objects set name=name where bucket_id=%s and name=%s",(b,n)) if ex else self.as_user(sub,"insert into storage.objects(bucket_id,name) values (%s,%s)",(b,n))
            if isinstance(r,Exception) or r==0: return 400,{'statusCode':'403','error':'Unauthorized','message':'new row violates row-level security policy'}
            self.files[n]=body;return 200,{'Key':b+'/'+n,'Id':str(uuid.uuid4())}
        if m and method=='GET':
            b,n=m.group(1),m.group(2)
            r=self.as_user(sub,"select 1 from storage.objects where bucket_id=%s and name=%s",(b,n))
            if isinstance(r,Exception) or not r or n not in self.files: return 400,{'statusCode':'404','error':'not_found','message':'Object not found'}
            return 200,('bytes',self.files[n])
        return 404,{'message':'not handled '+path}
    # --- REST: straight to PostgREST ---
    def rest(self,method,path,qs,body,hdr):
        if method=='PATCH' and getattr(self,'before_patch',None): f=self.before_patch;self.before_patch=None;f()   # imitate another device writing first
        h={k:v for k,v in hdr.items() if k in ('content-type','prefer','accept','range','accept-profile','content-profile')}
        tok=hdr.get('authorization','')[7:]
        if tok.count('.')==2: h['authorization']='Bearer '+tok
        req=urllib.request.Request(f'http://localhost:{self.port}{path}'+('?'+qs if qs else ''),data=body if method not in ('GET','HEAD') else None,method=method,headers=h)
        try: r=urllib.request.urlopen(req);return r.status,('raw',r.read(),dict(r.headers))
        except urllib.error.HTTPError as e: return e.code,('raw',e.read(),dict(e.headers))
    def handle(self,route,request):
        from urllib.parse import urlparse
        u=urlparse(request.url);hdr={k.lower():v for k,v in request.headers.items()};origin=hdr.get('origin','*')
        cors={'access-control-allow-origin':origin,'access-control-allow-credentials':'true','access-control-allow-methods':'GET,POST,PUT,PATCH,DELETE,OPTIONS',
              'access-control-allow-headers':'authorization,apikey,content-type,prefer,x-client-info,x-upsert,accept-profile,content-profile,range,x-supabase-api-version,cache-control',
              'access-control-expose-headers':'content-range,content-type,x-supabase-api-version'}
        if request.method=='OPTIONS': return route.fulfill(status=204,headers=cors)
        body=request.post_data_buffer;path=u.path;self.calls.append((request.method,path))
        if path.startswith('/auth/v1'): st,res=self.auth(request.method,path[8:],u.query,json.loads(body) if body else {},hdr)
        elif path.startswith('/storage/v1'): st,res=self.storage(request.method,path[11:],body,hdr)
        elif path.startswith('/rest/v1'): st,res=self.rest(request.method,path[8:],u.query,body,hdr)
        else: st,res=404,{'msg':'?'}
        if isinstance(res,tuple) and res[0]=='raw':
            hh={**cors,**{k.lower():v for k,v in res[2].items() if k.lower() in ('content-type','content-range','preference-applied')}};return route.fulfill(status=st,headers=hh,body=res[1])
        if isinstance(res,tuple) and res[0]=='bytes': return route.fulfill(status=st,headers={**cors,'content-type':'image/jpeg'},body=res[1])
        return route.fulfill(status=st,headers={**cors,'content-type':'application/json'},body='' if res is None else json.dumps(res))
