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
CALLS=[];OSMQ=[];EMPTY=[False];NOMQ=[]
REFUSE=set();NOM=['res'];NOMQ=[]
def osm(route):
  u=route.request.url;host=u.split('/')[2]
  body=urllib.parse.unquote_plus(route.request.post_data or (u.split('data=',1)[1] if 'data=' in u else ''));OSMQ.append((host,body))
  if host in REFUSE or 'all' in REFUSE: return route.fulfill(status=429,body='Too Many Requests')
  if 'is_in(' in body and 'area.a' in body:   # step 1 (light): only the names of the areas containing the point
    els=[] if EMPTY[0] else [{'type':'area','id':3600000011,'tags':{'name':'Копринка','boundary':'protected_area'}},
                             {'type':'area','id':2400000022,'tags':{'name':'Язовир Копринка','natural':'water','water':'reservoir'}}]
  elif 'way(22)' in body: els=[OSM['elements'][1]]
  elif 'rel(11)' in body: els=[OSM['elements'][0]]
  else: els=[]
  route.fulfill(body=json.dumps({'elements':els}),content_type='application/json')
BIG=[False]
def nominatim(route):   # Nominatim: the natural feature here (reverse), or a place's ready outline (lookup)
  NOMQ.append(route.request.url)
  if '/lookup' in route.request.url:
    if NOM[0]=='fail': return route.fulfill(status=503,body='busy')
    u=route.request.url
    if 'osm_ids=R11' in u:
      ring=[[25.0,41.5],[26.5,41.5],[26.5,43.0],[25.0,43.0],[25.0,41.5]] if BIG[0] else [[b,a] for a,b in A+B[1:]]
    elif 'osm_ids=W22' in u: ring=[[r['lon'],r['lat']] for r in res]
    else: return route.fulfill(body='[]',content_type='application/json')
    return route.fulfill(body=json.dumps([{'geojson':{'type':'Polygon','coordinates':[ring]}}]),content_type='application/json')
  if NOM[0]=='fail': return route.fulfill(status=503,body='busy')
  if NOM[0]=='none': return route.fulfill(body=json.dumps({'error':'Unable to geocode'}),content_type='application/json')
  if NOM[0]=='pen':   # what Nominatim really answered outside the lake: the Balkan Peninsula, which does contain the tap
    return route.fulfill(body=json.dumps({'osm_type':'relation','osm_id':9,'name':'Балкански полуостров','type':'peninsula','category':'natural','geojson':{'type':'Polygon','coordinates':[[[13.5,36.0],[30.0,36.0],[30.0,46.5],[13.5,46.5],[13.5,36.0]]]},'namedetails':{'name':'Балкански полуостров'}}),content_type='application/json')
  ring=[[r['lon'],r['lat']] for r in res] if NOM[0]=='res' else [[25.0,42.0],[25.05,42.0],[25.05,42.05],[25.0,42.05],[25.0,42.0]]   # 'far': a lake somewhere else
  route.fulfill(body=json.dumps({'osm_type':'way','osm_id':22,'name':'Язовир Копринка','type':'reservoir','category':'natural','geojson':{'type':'Polygon','coordinates':[ring]},'namedetails':{'name':'Язовир Копринка'}}),content_type='application/json')
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
  [ctx.route(h,osm) for h in ['https://overpass-api.de/**','https://overpass.kumi.systems/**','https://overpass.private.coffee/**']];ctx.route('https://nominatim.openstreetmap.org/**',nominatim);ctx.route('https://api.gbif.org/**',gbif)
  ctx.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/'+('leaflet.css' if r.request.url.endswith('.css') else 'leaflet.js'),content_type='text/css' if r.request.url.endswith('.css') else 'application/javascript'))
  for pat in ['https://server.arcgisonline.com/**','https://*.basemaps.cartocdn.com/**','https://*.tile.openstreetmap.org/**']:ctx.route(pat,lambda r:r.fulfill(body=G,content_type='image/png'))
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps([{'id':7,'date':T,'time':'08:00','place':'','count':'','bg':'Кос','en':'','la':'','fam':'','note':'','h':0,'s':1,'p':0,'beh':[],'geo':'%.5f,%.5f'%C0,'photo':None}],ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);pg.click('.tab[data-v="map"]');pg.click('[data-mm="gbif"]');pg.wait_for_timeout(1200)
  check('O1 three ways to tap: ● точка, ▦ квадрат and 🏞 място', pg.evaluate("[...document.querySelectorAll('[data-exm]')].map(b=>b.textContent)"), ['● точка','▦ квадрат','🏞 място'])
  pg.click('[data-exm="pl"]');pg.wait_for_timeout(1200);n0=len(CALLS);tap(pg);pg.wait_for_timeout(2400)
  ov=[b for h,b in OSMQ if 'is_in(' in b]
  check('O2 Nominatim first (the natural feature here); Overpass only for the NAMES of the areas around — a light question, no outlines or frames', (len(NOMQ)>0 and 'layer=natural' in NOMQ[0],bool(ov) and 'area.a' in ov[0] and 'out tags;' in ov[0] and ' bb' not in ov[0] and 'geom' not in ov[0]), (True,True))
  check('O3 the lake (from Nominatim) and the protected area (from Overpass) are both offered, smallest first — the reservoir not duplicated, and chosen', pg.evaluate("[...document.querySelectorAll('[data-exarea]')].map(b=>[b.textContent,b.getAttribute('aria-pressed')])"), [['Язовир Копринка язовир','true'],['Копринка защитена територия','false']])
  check('O4 the place is outlined on the map, and named in the panel', (pg.locator('#exmap path.leaflet-interactive').count(),pg.inner_text('#explace .whpl b')), (1,'Язовир Копринка · язовир'))
  q=[u for u in CALLS[n0:] if 'geometry=POLYGON' in u];P=poly(q[0]) if q else []
  check('O5 GBIF gets the shape itself: closed, anticlockwise, simplified to ≤ 61 points', (P[0]==P[-1],area(P)>0,len(P)<=61), (True,True,True))
  check('O6 ...widened for the shore: every point of the reservoir’s edge lies inside what was sent, and it never crosses itself', (all(inside((r['lon'],r['lat']),P) for r in res[:-1]),selfcross(P)), (True,False))
  pg.click('[data-exarea="1"]');pg.wait_for_timeout(1200)
  q2=[u for u in CALLS if 'geometry=POLYGON' in u][-1];P2=poly(q2)
  check('O7 choosing the protected area: its outline comes from Nominatim (ready and simplified), +300 m, sent and named', (any('/lookup' in u and 'osm_ids=R11' in u for u in NOMQ),P2[0]==P2[-1],len(P2),pg.inner_text('#explace .whpl b')), (True,True,5,'Копринка · защитена територия'))
  sh=pg.evaluate("""(()=>{const c=[];for(let i=0;i<=40;i++){const a=Math.PI*(0.15+1.7*i/40);c.push([42.62+0.02*Math.sin(a),25.40+0.03*Math.cos(a)]);}
    for(let i=40;i>=0;i--){const a=Math.PI*(0.15+1.7*i/40);c.push([42.62+0.018*Math.sin(a),25.40+0.027*Math.cos(a)]);}c.push(c[0]);return gbShape(c,300).map(x=>[x[1],x[0]]);})()""")
  check('O8 a C-shaped lake with a narrow gap: widening would cross itself — the outline falls back to a safe one', selfcross([tuple(x) for x in sh]), False)
  EMPTY[0]=True;NOM[0]='none';pg.evaluate("OSMC.clear()");tap(pg,.75,.8);pg.wait_for_timeout(1200)
  check('O9 tapping outside any named place says so (and suggests point or square)', 'Тук няма именувано място' in pg.inner_text('#explace'), True)
  EMPTY[0]=False;NOM[0]='none';REFUSE.add('overpass-api.de');OSMQ.clear();pg.evaluate("OSMC.clear()");tap(pg,.6,.7);pg.wait_for_timeout(2200)
  check('O2b with nothing from Nominatim and the first Overpass server refusing („too many requests“), Перá asks the next one', ([h for h,b in OSMQ[:2]],pg.locator('[data-exarea]').count()), (['overpass-api.de','overpass.kumi.systems'],2))
  REFUSE.discard('overpass-api.de');NOM[0]='far';OSMQ.clear();pg.evaluate("OSMC.clear()");EMPTY[0]=True;tap(pg,.6,.7);pg.wait_for_timeout(2200)
  check('O12 a lake Nominatim offers that the tap is NOT inside (its nearest) is not shown', 'Тук няма именувано място' in pg.inner_text('#explace'), True)
  NOM[0]='pen';EMPTY[0]=False;OSMQ.clear();pg.evaluate("OSMC.clear()");tap(pg);pg.wait_for_timeout(2500)
  check('O14 Nominatim\'s „Балкански полуостров“ (it does contain the spot) is not a place — the reservoir and the reserve from Overpass are offered instead', (pg.evaluate("[...document.querySelectorAll('[data-exarea]')].map(b=>b.textContent)"),'полуостров' in pg.inner_text('#explace')), (['Язовир Копринка язовир','Копринка защитена територия'],False))
  NOM[0]='res';EMPTY[0]=False;REFUSE.add('all');pg.evaluate("OSMC.clear()");tap(pg);pg.wait_for_timeout(2500)
  check('O13 even with every Overpass server refusing, Nominatim alone still gives the lake', (pg.inner_text('#explace .whpl b'),'не отговаря' in pg.inner_text('#explace')), ('Язовир Копринка · язовир',False))
  NOM[0]='none';pg.evaluate("OSMC.clear()");tap(pg,.53,.53);pg.wait_for_timeout(2500)
  check('O15 Nominatim fine but every Overpass server failing: it says honestly what it could and couldn\'t check', 'Тук няма езеро или язовир; резерватите и парковете не можах да проверя' in pg.inner_text('#explace'), True)
  NOM[0]='fail';pg.evaluate("OSMC.clear()");tap(pg,.52,.52);pg.wait_for_timeout(2500)
  log=pg.evaluate("[...errSeen].find(k=>k.startsWith('OpenStreetMap не отговаря — ')&&k.includes('nominatim: 503'))||''")
  check('O11 if everything fails, it says so — and the log tells what EACH source answered and how long it took', ('OpenStreetMap не отговаря' in pg.inner_text('#explace'),'nominatim: 503' in log,'overpass-api.de: 429' in log,'overpass.kumi.systems: 429' in log,'overpass.private.coffee: 429' in log,' с' in log), (True,True,True,True,True,True))
  NOM[0]='none';REFUSE.clear();BIG[0]=True;pg.evaluate("OSMC.clear()");tap(pg,.54,.54);pg.wait_for_timeout(2500)
  pg.click('[data-exarea="1"]');pg.wait_for_timeout(2000)
  check('O16 a place bigger than 3000 km² is refused once its outline is known — choose another or use the square', 'е твърде голямо място' in pg.inner_text('#explace'), True)
  check('O10 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
