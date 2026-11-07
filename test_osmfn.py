# The „osm“ helper (supabase/functions/osm/index.ts) in Deno, against stand-in Overpass servers: only Перá's short
# questions; all servers asked at once, the first good answer wins; every reason when all fail; CORS; a week of caching.
import json,subprocess,sys,time,threading,urllib.request,os
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
P=int(sys.argv[1]) if len(sys.argv)>1 else 8996;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
class H(BaseHTTPRequestHandler):
  def log_message(self,*a):pass
  def do_GET(self):   # stand-in EEA service
    self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers()
    self.wfile.write(json.dumps({'type':'FeatureCollection','features':[{'properties':{'SITECODE':'BG0000270','SITENAME':'Atanasovsko ezero'},'path':self.path}]}).encode())
  def do_POST(self):
    n=int(self.headers.get('Content-Length') or 0);self.rfile.read(n);k=self.path.strip('/')
    if k=='slow':time.sleep(3)
    if k in('broken','plain'):
      self.send_response(500 if k=='broken' else 200);self.end_headers();self.wfile.write(b'<html>busy</html>');return
    self.send_response(200);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps({'elements':[{'type':'area','id':3600000011,'tags':{'name':k}}]}).encode())
srv=ThreadingHTTPServer(('localhost',P),H);threading.Thread(target=srv.serve_forever,daemon=True).start()
def run(servers):
  env={**os.environ,'OSM_SERVERS':','.join(f'http://localhost:{P}/{s}' for s in servers),'EEA_URL':f'http://localhost:{P}/eea/query'}
  d=subprocess.Popen(['/tmp/denobin/deno','run','--allow-net','--allow-env','supabase/functions/osm/index.ts'],env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
  for _ in range(60):
    try:urllib.request.urlopen('http://localhost:8000/',timeout=1);break
    except Exception as e:
      if hasattr(e,'code'):break
      time.sleep(.3)
  return d
def get(q=None,method='GET'):
  u='http://localhost:8000/'+('' if q is None else '?data='+urllib.parse.quote(q))
  req=urllib.request.Request(u,method=method)
  try:r=urllib.request.urlopen(req,timeout=30);return r.status,{k.lower():v for k,v in r.headers.items()},r.read().decode()
  except urllib.error.HTTPError as e:return e.code,{k.lower():v for k,v in e.headers.items()},e.read().decode()
import urllib.parse
Q='[out:json][timeout:10];is_in(42.62,25.4)->.a;area.a["name"];out tags;'
d=run(['slow','fast','broken'])
try:
  st,h,b=get('')
  check('F1 only Перá’s short questions: an empty or foreign one is refused', (st,json.loads(b)), (400,{'error':'bad query'}))
  check('F1b ...and so is anything not starting with [out:json]', get('node(1);out;')[0], 400)
  t0=time.time();st,h,b=get(Q);dt=time.time()-t0
  check('F2 all servers asked at once — the fast one answers, without waiting for the slow one', (st,json.loads(b)['elements'][0]['tags']['name'],dt<2.5,h.get('x-pera-via','').split(' ')[0]), (200,'fast',True,f'localhost:{P}'))
  check('F3 the phone may keep the answer for a week; any page may call it (CORS)', (h.get('cache-control'),h.get('access-control-allow-origin')), ('public, max-age=604800','*'))
  check('F4 the browser’s preflight is answered', get(None,'OPTIONS')[0], 200)
  u='http://localhost:8000/?eea='+urllib.parse.quote('?where=1%3D1&geometry=27.3,42.4,27.6,42.65&f=geojson')
  r=urllib.request.urlopen(u,timeout=20);o=json.loads(r.read());hh={k.lower():v for k,v in r.headers.items()}
  check('F6 ?eea= passes a Natura 2000 question to the EEA service (only that one), cached for a month', (o['features'][0]['properties']['SITENAME'],o['features'][0]['path'].startswith('/eea/query?where=1%3D1'),hh.get('cache-control')), ('Atanasovsko ezero',True,'public, max-age=2592000'))
  try:urllib.request.urlopen('http://localhost:8000/?eea='+urllib.parse.quote('http://evil.example/x'),timeout=10);bad=None
  except urllib.error.HTTPError as e2:bad=e2.code
  check('F7 ...anything else after ?eea= is refused', bad, 400)
finally:
  d.terminate();d.wait()
d=run(['broken','plain','broken'])
try:
  st,h,b=get(Q);o=json.loads(b)
  check('F5 when every server fails: 502 and each one’s reason', (st,o['error'],sorted(x.split(': ',1)[1] for x in o['why'])), (502,'overpass',['500','500','not JSON']))
finally:
  d.terminate();d.wait();srv.shutdown()
print('FAILURES:',fails)
