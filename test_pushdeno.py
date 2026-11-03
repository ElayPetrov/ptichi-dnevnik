# The push helper end to end in Deno (Supabase's runtime), the real file unmodified: a stand-in for Supabase's REST API
# and a stand-in phone push service on one local server; Node then decrypts what the "phone" received with the
# independent http_ece library and verifies the VAPID signature.  Needs: /tmp/denobin/deno, /tmp/pushtest (http_ece).
import json,subprocess,sys,time,threading,urllib.request,urllib.parse,os
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
P=int(sys.argv[1]) if len(sys.argv)>1 else 8999;DP=8000;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
# the phone's keys, made in Node the way a browser makes them
phone=json.loads(subprocess.run(['node','-e',"const c=require('crypto');const e=c.createECDH('prime256v1');e.generateKeys();const a=c.randomBytes(16);"
  "console.log(JSON.stringify({priv:e.getPrivateKey('hex'),pub:e.getPublicKey().toString('base64url'),auth:a.toString('base64url')}))"],capture_output=True,text=True,check=True).stdout)
EP=lambda k:f'http://localhost:{P}/push/{k}'
DB={'push_keys':[],'push_state':[],'push_subs':[
  {'id':'a','user_id':'u2','endpoint':EP('alive'),'p256dh':phone['pub'],'auth':phone['auth'],'kinds':['ask','idp','inv','comment']},
  {'id':'d','user_id':'u2','endpoint':EP('dead'),'p256dh':phone['pub'],'auth':phone['auth'],'kinds':['idp']},
  {'id':'m','user_id':'me','endpoint':EP('mine'),'p256dh':phone['pub'],'auth':phone['auth'],'kinds':['ask']}],
  'social':[{'id':'r1','owner':'u2','item':'q:5','author':'me','kind':'comment','body':'🔎 Сива овесарка (Emberiza calandra)\nдебел клюн'}],
  'profiles':[{'user_id':'me','name':'Иван'},{'user_id':'u2','name':'Петър'}],
  'journals':[{'user_id':'u2','data':{'obs':[{'id':1,'bg':'Кос','date':'2026-11-03'}],'outs':[]}}],'viewers':[{'owner':'u2','viewer':'me'}]}
GOT=[];LOG=[]
def rows(t,q):
  r=DB.get(t,[])
  for k,v in urllib.parse.parse_qsl(q):
    if k in('select',):continue
    if v.startswith('eq.'):r=[x for x in r if str(x.get(k))==v[3:]]
    elif v.startswith('in.('):L=[s.strip('"') for s in v[4:-1].split(',')];r=[x for x in r if str(x.get(k)) in L]
  return r
class H(BaseHTTPRequestHandler):
  def log_message(self,*a):pass
  def _send(self,code,obj=None):
    b=json.dumps(obj).encode() if obj is not None else b'';self.send_response(code);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(b)
  def do_GET(self):
    u=urllib.parse.urlparse(self.path);t=u.path.split('/rest/v1/')[-1]
    LOG.append(('GET',t,self.headers.get('apikey')));self._send(200,rows(t,u.query))
  def do_POST(self):
    u=urllib.parse.urlparse(self.path);n=int(self.headers.get('Content-Length') or 0);body=self.rfile.read(n)
    if u.path.startswith('/push/'):
      k=u.path.split('/')[-1];GOT.append({'k':k,'body':body.hex(),'auth':self.headers.get('Authorization'),'enc':self.headers.get('Content-Encoding'),'ttl':self.headers.get('TTL')})
      return self._send(410 if k=='dead' else 201)
    t=u.path.split('/rest/v1/')[-1];o=json.loads(body)
    key='owner' if t=='push_state' else 'id';DB[t]=[x for x in DB.get(t,[]) if x.get(key)!=o.get(key)]+[o];LOG.append(('POST',t,self.headers.get('Prefer')));self._send(201)
  def do_DELETE(self):
    u=urllib.parse.urlparse(self.path);t=u.path.split('/rest/v1/')[-1];gone=rows(t,u.query);DB[t]=[x for x in DB[t] if x not in gone];LOG.append(('DELETE',t));self._send(204)
srv=ThreadingHTTPServer(('localhost',P),H);threading.Thread(target=srv.serve_forever,daemon=True).start()
env={**os.environ,'SUPABASE_URL':f'http://localhost:{P}','SUPABASE_SERVICE_ROLE_KEY':'svc-key'}
deno=subprocess.Popen(['/tmp/denobin/deno','run','--allow-net','--allow-env','supabase/functions/push/index.ts'],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
for _ in range(60):
  try: urllib.request.urlopen(f'http://localhost:{DP}/',timeout=1);break
  except Exception as e:
    if hasattr(e,'code'):break
    time.sleep(0.5)
def call(method='POST',body=None,q=''):
  req=urllib.request.Request(f'http://localhost:{DP}/{q}',method=method,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
  try:r=urllib.request.urlopen(req,timeout=20);return r.status,json.loads(r.read())
  except urllib.error.HTTPError as e:return e.code,json.loads(e.read() or b'{}')
def decrypt(hexbody):
  js=("const ece=require('/tmp/pushtest/node_modules/http_ece');const c=require('crypto');const e=c.createECDH('prime256v1');e.setPrivateKey(process.argv[1],'hex');"
      "process.stdout.write(ece.decrypt(Buffer.from(process.argv[2],'hex'),{version:'aes128gcm',privateKey:e,authSecret:Buffer.from(process.argv[3],'base64url')}).toString('utf8'))")
  return json.loads(subprocess.run(['node','-e',js,phone['priv'],hexbody,phone['auth']],capture_output=True,text=True,check=True).stdout)
def vapid_ok(auth,pub):
  js=("const c=require('crypto');const m=/^vapid t=([^.]+)\\.([^.]+)\\.([^,]+), k=(.+)$/.exec(process.argv[1]);const k=Buffer.from(process.argv[2],'base64url');"
      "const key=c.createPublicKey({key:{kty:'EC',crv:'P-256',x:k.subarray(1,33).toString('base64url'),y:k.subarray(33).toString('base64url')},format:'jwk'});"
      "const ok=c.verify('sha256',Buffer.from(m[1]+'.'+m[2]),{key,dsaEncoding:'ieee-p1363'},Buffer.from(m[3],'base64url'));"
      "process.stdout.write(JSON.stringify([ok,JSON.parse(Buffer.from(m[2],'base64url')).aud,m[4]===process.argv[2]]))")
  return json.loads(subprocess.run(['node','-e',js,auth,pub],capture_output=True,text=True,check=True).stdout)
try:
  st,k=call('GET',q='?key=1');st2,k2=call('GET',q='?key=1')
  check('E1 Deno: the helper makes its keys on the first call, stores them, and hands out the same public key after', (st,len(k.get('key','')),k==k2,len(DB['push_keys']),[x for x in LOG if x[0]=='POST'][0][2]), (200,87,True,1,'resolution=merge-duplicates'))
  check('E2 ...it talks to the database with the service key', all(x[2]=='svc-key' for x in LOG if x[0]=='GET'), True)
  st,r=call(body={'table':'social','id':'r1'})
  alive=[g for g in GOT if g['k']=='alive']
  check('E3 a suggestion on Петър’s question: his phones that want „idp“ get it, the dead one is removed, the suggester’s own phone stays quiet', (st,r,[g['k'] for g in GOT],[s['id'] for s in DB['push_subs']]), (200,{'sent':1},['alive','dead'],['a','m']))
  check('E4 the phone decrypts exactly what was meant (independent decryptor)', decrypt(alive[0]['body']), {'t':'Иван предложи вид','b':'Сива овесарка (Emberiza calandra)','u':'./?go=q:5','g':'idp:q:5','k':'idp'})
  check('E5 the request carries a valid VAPID signature for that push service, aes128gcm, a day to live', (vapid_ok(alive[0]['auth'],DB['push_keys'][0]['pub']),alive[0]['enc'],alive[0]['ttl']), ([True,f'http://localhost:{P}',True],'aes128gcm','86400'))
  GOT.clear();st,r=call(body={'table':'journals','owner':'u2'})
  check('E6 the first look at Петър’s journal only remembers it', (r,len(GOT),DB['push_state'][0]['seen']), ({'sent':0},0,{'ask':[],'ok':[],'inv':[]}))
  DB['journals'][0]['data']['obs'].append({'id':2,'bg':'Непозната птица','date':'2026-11-03','place':'Копринка','ask':9,'note':'малка, кафява'})
  st,r=call(body={'table':'journals','owner':'u2'})
  check('E7 a new question reaches his follower’s phone, readable', (r,[g['k'] for g in GOT],decrypt(GOT[0]['body'])['t'] if GOT else None,decrypt(GOT[0]['body'])['b'] if GOT else None), ({'sent':1},['mine'],'Петър пита: какво е това?','3 ное, Копринка — малка, кафява'))
  GOT.clear();st,r=call(body={'test':EP('alive')})
  check('E8 „Изпрати пробно“ reaches exactly that phone', (r['sent'],[g['k'] for g in GOT],decrypt(GOT[0]['body'])['b'] if GOT else None), (1,['alive'],'Известията работят на този телефон 🐦'))
  check('E9 a bad call is refused, nothing crashes', call(body={'nonsense':1})[0], 400)
finally:
  deno.terminate();out=deno.communicate(timeout=10)[0];srv.shutdown()
  if fails:print(out[-1500:])
print('FAILURES:',fails)
