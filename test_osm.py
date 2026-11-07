# „🏞 място“ in Карта → „Изследвай“ (2026-11-07.10): the named areas (OpenStreetMap) containing a tap, smallest first;
# the chosen one outlined and sent to GBIF as its own shape — simplified, +300 m of shore, closed, anticlockwise, never
# self-crossing. OpenStreetMap and GBIF are stand-ins here.
import json,subprocess,sys,time,io,math,urllib.parse,datetime
from playwright.sync_api import sync_playwright
from PIL import Image
T=datetime.date.today().isoformat()
port=int(sys.argv[1]) if len(sys.argv)>1 else 9008;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
def png(c,a=255):
  b=io.BytesIO();Image.new('RGBA',(256,256),c+(a,)).save(b,'PNG');return b.getvalue()
G=png((40,160,60))
C0=(42.62,25.40)
# the reservoir: 80 points, wobbly, around the tap; the protected area: a bigger square made of two open pieces
res=[{'lat':C0[0]+0.02*math.sin(2*math.pi*i/80)*(1+0.15*math.sin(7*i)),'lon':C0[1]+0.03*math.cos(2*math.pi*i/80)*(1+0.15*math.cos(5*i))} for i in range(80)];res.append(res[0])
A=[(42.58,25.34),(42.58,25.46),(42.66,25.46)];B=[(42.66,25.46),(42.66,25.34),(42.58,25.34)]
OSM={'elements':[
  {'type':'relation','id':11,'tags':{'name':'Копринка','boundary':'protected_area'},'members':[
    {'type':'way','role':'outer','geometry':[{'lat':a,'lon':b} for a,b in A]},{'type':'way','role':'outer','geometry':[{'lat':a,'lon':b} for a,b in B]}]},
  {'type':'way','id':22,'tags':{'name':'Язовир Копринка','natural':'water','water':'reservoir'},'geometry':res}]}
CALLS=[];OSMQ=[];EMPTY=[False]
def osm(route):
  body=urllib.parse.unquote_plus(route.request.post_data or '');OSMQ.append(body)
  route.fulfill(body=json.dumps({'elements':[]} if EMPTY[0] else OSM),content_type='application/json')
def gbif(route):
  u=urllib.parse.unquote(route.request.url);CALLS.append(u)
  if '/v2/map/' in u: return route.fulfill(body=G,content_type='image/png')
  if 'facet=year' in u: body={'count':321,'facets':[{'field':'YEAR','counts':[{'name':'2012','count':4},{'name':'2025','count':40}]},{'field':'MONTH','counts':[{'name':'4','count':50},{'name':'10','count':40}]}]}
  elif 'facet=speciesKey' in u: body={'facets':[{'field':'SPECIES_KEY','counts':[{'name':'2482507','count':30}]}]}
  else: body={'results':[{'speciesKey':2482507,'species':'Turdus merula'}],'count':1}
  route.fulfill(body=json.dumps(body),content_type='application/json')
def poly(u):
  w=u.split('geometry=POLYGON((')[1].split('))')[0];return [tuple(map(float,p.split())) for p in w.split(', ')]   # (lon,lat)
def area(P):return sum(P[i][0]*P[i+1][1]-P[i+1][0]*P[i][1] for i in range(len(P)-1))/2
def inside(pt,P):
  x,y=pt;c=False
  for i in range(len(P)-1):
    (x1,y1),(x2,y2)=P[i],P[i+1]
    if (y1>y)!=(y2>y) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:c=not c
  return c
def selfcross(P):
  n=len(P)-1
  def o(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
  for i in range(n):
    for j in range(i+2,n):
      if i==0 and j==n-1:continue
      a,b,c,d=P[i],P[i+1],P[j],P[j+1]
      if (o(a,b,c)>0)!=(o(a,b,d)>0) and (o(c,d,a)>0)!=(o(c,d,b)>0):return True
  return False
def tap(pg,fx=.5,fy=.5):
  m=pg.locator('#exmap');m.scroll_into_view_if_needed();pg.wait_for_timeout(150);b=m.bounding_box();pg.mouse.click(b['x']+b['width']*fx,b['y']+b['height']*fy)
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844})
  ctx.route('https://overpass-api.de/**',osm);ctx.route('https://api.gbif.org/**',gbif)
  ctx.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/'+('leaflet.css' if r.request.url.endswith('.css') else 'leaflet.js'),content_type='text/css' if r.request.url.endswith('.css') else 'application/javascript'))
  for pat in ['https://server.arcgisonline.com/**','https://*.basemaps.cartocdn.com/**','https://*.tile.openstreetmap.org/**']:ctx.route(pat,lambda r:r.fulfill(body=G,content_type='image/png'))
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps([{'id':7,'date':T,'time':'08:00','place':'','count':'','bg':'Кос','en':'','la':'','fam':'','note':'','h':0,'s':1,'p':0,'beh':[],'geo':'%.5f,%.5f'%C0,'photo':None}],ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);pg.click('.tab[data-v="map"]');pg.click('[data-mm="gbif"]');pg.wait_for_timeout(1200)
  check('O1 three ways to tap: ● точка, ▦ квадрат and 🏞 място (the hexagons stay in all)', pg.evaluate("[...document.querySelectorAll('[data-exm]')].map(b=>b.textContent)"), ['● точка','▦ квадрат','🏞 място'])
  pg.click('[data-exm="pl"]');pg.wait_for_timeout(1200);n0=len(CALLS);tap(pg);pg.wait_for_timeout(1800)
  check('O2 the tap asks OpenStreetMap which named areas contain that point', ('is_in(42.6' in (OSMQ[-1] if OSMQ else ''),'nature_reserve' in (OSMQ[-1] if OSMQ else '')), (True,True))
  chips=pg.evaluate("[...document.querySelectorAll('[data-exarea]')].map(b=>[b.textContent,b.getAttribute('aria-pressed')])")
  check('O3 both areas offered, the smallest (the reservoir) first and chosen', chips, [['Язовир Копринка язовир','true'],['Копринка защитена територия','false']])
  check('O4 the place is outlined on the map, and named in the panel', (pg.locator('#exmap path.leaflet-interactive').count(),pg.inner_text('#explace .whpl b')), (1,'Язовир Копринка · язовир'))
  q=[u for u in CALLS[n0:] if 'geometry=POLYGON' in u];P=poly(q[0]) if q else []
  check('O5 GBIF gets the shape itself: closed, anticlockwise, simplified to ≤ 61 points', (P[0]==P[-1],area(P)>0,len(P)<=61), (True,True,True))
  check('O6 ...widened for the shore: every point of the reservoir’s edge lies inside what was sent, and it never crosses itself', (all(inside((r['lon'],r['lat']),P) for r in res[:-1]),selfcross(P)), (True,False))
  pg.click('[data-exarea="1"]');pg.wait_for_timeout(1200)
  q2=[u for u in CALLS if 'geometry=POLYGON' in u][-1];P2=poly(q2)
  check('O7 choosing the protected area: its two pieces joined into one outline (+300 m), sent and named', (P2[0]==P2[-1],len(P2),pg.inner_text('#explace .whpl b')), (True,5,'Копринка · защитена територия'))
  sh=pg.evaluate("""(()=>{const c=[];for(let i=0;i<=40;i++){const a=Math.PI*(0.15+1.7*i/40);c.push([42.62+0.02*Math.sin(a),25.40+0.03*Math.cos(a)]);}
    for(let i=40;i>=0;i--){const a=Math.PI*(0.15+1.7*i/40);c.push([42.62+0.018*Math.sin(a),25.40+0.027*Math.cos(a)]);}c.push(c[0]);return gbShape(c,300).map(x=>[x[1],x[0]]);})()""")
  check('O8 a C-shaped lake with a narrow gap: widening would cross itself — the outline falls back to a safe one', selfcross([tuple(x) for x in sh]), False)
  EMPTY[0]=True;pg.evaluate("OSMC.clear()");tap(pg,.75,.8);pg.wait_for_timeout(1200)
  check('O9 tapping outside any named place says so (and suggests point or square)', 'Тук няма именувано място' in pg.inner_text('#explace'), True)
  check('O10 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
