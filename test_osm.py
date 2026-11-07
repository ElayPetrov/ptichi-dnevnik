# „🏞 място“ (2026-11-07.16): outlined places on the map — green: the Natura 2000 bird areas (EEA, BG only; a split area
# sent as several parts); orange: „hot spots“ where GBIF finds are dense (≥12 within 400 m, named after their most
# frequent locality, from zoom 11); tap an outline for its birds; EEA straight, else through the helper; failures logged.
# EEA, GBIF and the helper are stand-ins here.
import json,subprocess,sys,time,io,math,urllib.parse,datetime,random
from playwright.sync_api import sync_playwright
from PIL import Image
T=datetime.date.today().isoformat();random.seed(7)
port=int(sys.argv[1]) if len(sys.argv)>1 else 9008;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
def png(c,a=255):
  b=io.BytesIO();Image.new('RGBA',(256,256),c+(a,)).save(b,'PNG');return b.getvalue()
G=png((214,222,200));C0=(42.62,25.40);H0=(42.6150,25.3700)
sq=lambda la0,lo0,la1,lo1:[[lo0,la0],[lo1,la0],[lo1,la1],[lo0,la1],[lo0,la0]]
EEAF={'type':'FeatureCollection','features':[
  {'type':'Feature','properties':{'SITECODE':'BG0000270','SITENAME':'Atanasovsko ezero'},'geometry':{'type':'Polygon','coordinates':[sq(42.60,25.39,42.64,25.43)]}},
  {'type':'Feature','properties':{'SITECODE':'BG0000273','SITENAME':'Burgasko ezero'},'geometry':{'type':'MultiPolygon','coordinates':[[sq(42.66,25.44,42.68,25.47)],[sq(42.69,25.44,42.70,25.46)]]}},
  {'type':'Feature','properties':{'SITECODE':'GR1110001','SITENAME':'Elsewhere'},'geometry':{'type':'Polygon','coordinates':[sq(42.55,25.30,42.57,25.32)]}}]}
PTS=[{'decimalLatitude':H0[0]+random.uniform(-.0012,.0012),'decimalLongitude':H0[1]+random.uniform(-.0015,.0015),'locality':'Atanasovsko Lake--Saltpans' if i<30 else 'Атанасовско езеро'} for i in range(40)]
PTS+=[{'decimalLatitude':42.55+i*.02,'decimalLongitude':25.20+i*.03,'locality':'Някъде'} for i in range(8)]
CALLS=[];EEAQ=[];PROXYQ=[];EEA_MODE=['ok'];PROXY_MODE=['ok']
def eea(route):
  EEAQ.append(route.request.url)
  if EEA_MODE[0]=='fail': return route.abort()   # e.g. the browser refusing it
  route.fulfill(body=json.dumps(EEAF),content_type='application/json')
def proxy(route):
  PROXYQ.append(route.request.url)
  if PROXY_MODE[0]=='fail': return route.fulfill(status=502,body='{"error":"eea"}')
  route.fulfill(body=json.dumps(EEAF),content_type='application/json')
def gbif(route):
  u=urllib.parse.unquote(route.request.url);CALLS.append(u)
  if '/v2/map/' in u: return route.fulfill(body=png((230,120,40),40),content_type='image/png')
  if 'geometry=POLYGON' in u and 'limit=300' in u and 'taxonKey=212' in u and 'facet' not in u:   # finds in view (for the hot spots)
    body={'results':PTS if 'offset=0' in u else [],'endOfRecords':'offset=0' not in u}
  elif 'facet=year' in u: body={'count':321,'facets':[{'field':'YEAR','counts':[{'name':'2012','count':4},{'name':'2025','count':40}]},{'field':'MONTH','counts':[{'name':'4','count':50},{'name':'10','count':40}]}]}
  elif 'facet=speciesKey' in u: body={'facets':[{'field':'SPECIES_KEY','counts':[{'name':'2482507','count':30}]}]}
  else: body={'results':[{'speciesKey':2482507,'species':'Turdus merula'}],'count':1}
  route.fulfill(body=json.dumps(body),content_type='application/json')
def wkt(u):
  s=u.split('geometry=',1)[1].split('&')[0];return s
def ringsOf(w):
  inner=w[w.index('((')+2:w.rindex('))')];parts=inner.split(')), ((') if w.startswith('MULTIPOLYGON') else [inner]
  return [[tuple(map(float,p.split())) for p in part.replace('(','').replace(')','').split(', ')] for part in parts]
def area(P):return sum(P[i][0]*P[i+1][1]-P[i+1][0]*P[i][1] for i in range(len(P)-1))/2
def selfcross(P):
  n=len(P)-1
  def o(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
  for i in range(n):
    for j in range(i+2,n):
      if i==0 and j==n-1:continue
      a,b,c,d=P[i],P[i+1],P[j],P[j+1]
      if (o(a,b,c)>0)!=(o(a,b,d)>0) and (o(c,d,a)>0)!=(o(c,d,b)>0):return True
  return False
def click_ll(pg,la,lo):   # a finger on the map at that latitude/longitude
  pt=pg.evaluate(f"(()=>{{const m=document.getElementById('exmap')._lmap,p=m.latLngToContainerPoint([{la},{lo}]),r=document.getElementById('exmap').getBoundingClientRect();return [r.left+p.x,r.top+p.y]}})()")
  pg.mouse.click(pt[0],pt[1])
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844})
  ctx.route('https://bio.discomap.eea.europa.eu/**',eea);ctx.route('https://szyituwdlbwpqkfuklxq.supabase.co/functions/v1/osm**',proxy);ctx.route('https://api.gbif.org/**',gbif)
  ctx.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/'+('leaflet.css' if r.request.url.endswith('.css') else 'leaflet.js'),content_type='text/css' if r.request.url.endswith('.css') else 'application/javascript'))
  for pat in ['https://server.arcgisonline.com/**','https://*.basemaps.cartocdn.com/**','https://*.tile.openstreetmap.org/**']:ctx.route(pat,lambda r:r.fulfill(body=G,content_type='image/png'))
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps([{'id':7,'date':T,'time':'08:00','place':'','count':'','bg':'Кос','en':'','la':'','fam':'','note':'','h':0,'s':1,'p':0,'beh':[],'geo':'%.5f,%.5f'%C0,'photo':None}],ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);pg.click('.tab[data-v="map"]');pg.click('[data-mm="gbif"]');pg.wait_for_timeout(1200)
  check('Q1 three ways to tap: ● точка, ▦ квадрат and 🏞 място', pg.evaluate("[...document.querySelectorAll('[data-exm]')].map(b=>b.textContent)"), ['● точка','▦ квадрат','🏞 място'])
  pg.click('[data-exm="pl"]');pg.wait_for_timeout(1800);pg.locator('#exmap').scroll_into_view_if_needed()
  zones=pg.evaluate("document.getElementById('exmap')._places.LZ.getLayers().map(l=>l.getTooltip().getContent())")
  check('Q2 the Natura 2000 bird areas in view are drawn (green), with their names — only the Bulgarian ones', sorted(zones), ['Atanasovsko ezero','Burgasko ezero'])
  check('Q3 at zoom 10 no hot spots yet — the hint says to zoom in for them', (pg.evaluate("document.getElementById('exmap')._places.LH.getLayers().length"),'Приближи още' in pg.inner_text('#exhint')), (0,True))
  pg.evaluate("document.getElementById('exmap')._lmap.setView([%f,%f],13)"%H0);pg.wait_for_timeout(2200)
  hs=pg.evaluate("document.getElementById('exmap')._places.LH.getLayers().map(l=>l.getTooltip().getContent())")
  check('Q4 zoomed in: the dense finds become one orange place, named after their most frequent location; scattered finds don’t', hs, ['Atanasovsko Lake--Saltpans'])
  n0=len(CALLS);click_ll(pg,*H0);pg.wait_for_timeout(1500)
  check('Q5 tapping the orange place: its birds, under its name and number of finds', pg.inner_text('#explace .whpl b'), 'Atanasovsko Lake--Saltpans · 40 находки тук')
  q=[u for u in CALLS[n0:] if 'facet=year' in u];R=ringsOf(wkt(q[0])) if q else [[]]
  check('Q6 ...GBIF gets its outline: one closed, anticlockwise, non-crossing shape around the finds', (len(R),R[0][0]==R[0][-1],area(R[0])>0,selfcross(R[0])), (1,True,True,False))
  pg.evaluate("document.getElementById('exmap')._lmap.setView([42.632,25.425],13)");pg.wait_for_timeout(1500);n0=len(CALLS);click_ll(pg,42.632,25.425);pg.wait_for_timeout(1500)
  check('Q7 tapping the green area: its birds, named as a Natura 2000 bird area', pg.inner_text('#explace .whpl b'), 'Atanasovsko ezero · зона за птици (Натура 2000)')
  pg.evaluate("document.getElementById('exmap')._lmap.setView([42.67,25.455],13)");pg.wait_for_timeout(1500);n0=len(CALLS);click_ll(pg,42.67,25.455);pg.wait_for_timeout(1500)
  q=[u for u in CALLS[n0:] if 'facet=year' in u]
  check('Q8 an area in two parts goes to GBIF as both parts (MULTIPOLYGON)', (wkt(q[0]).startswith('MULTIPOLYGON') if q else None,len(ringsOf(wkt(q[0]))) if q else 0), (True,2))
  click_ll(pg,42.6555,25.43);pg.wait_for_timeout(600)
  check('Q9 tapping outside every outline tells you what to tap', 'Докосни очертано място' in pg.inner_text('#explace'), True)
  EEA_MODE[0]='fail';pg.evaluate("SPAC.clear()");PROXYQ.clear();pg.evaluate("document.getElementById('exmap')._lmap.setView([42.62,25.40],10)");pg.wait_for_timeout(2500)
  check('Q10 if the phone can’t reach the EEA itself, the areas come through the Supabase helper', (len(PROXYQ)>0 and '?eea=' in PROXYQ[0],len(pg.evaluate("document.getElementById('exmap')._places.LZ.getLayers()"))), (True,2))
  PROXY_MODE[0]='fail';pg.evaluate("SPAC.clear()");pg.evaluate("document.getElementById('exmap')._lmap.setView([42.621,25.401],10)");pg.wait_for_timeout(2500)
  log=pg.evaluate("[...errSeen].find(k=>k.startsWith('Натура 2000 не отговаря — '))||''")
  check('Q11 if neither works, the reason is logged (both attempts)', ('eea: ' in log,'eea (Supabase): 502' in log), (True,True))
  EEA_MODE[0]='ok';pg.evaluate("document.getElementById('exmap')._lmap.setView([42.62,25.40],8)");pg.wait_for_timeout(1500)
  check('Q12 zoomed far out: nothing drawn, and the hint says to zoom in', (pg.evaluate("document.getElementById('exmap')._places.LZ.getLayers().length"),'Приближи картата' in pg.inner_text('#exhint')), (0,True))
  sh=pg.evaluate("""(()=>{const c=[];for(let i=0;i<=40;i++){const a=Math.PI*(0.15+1.7*i/40);c.push([42.62+0.02*Math.sin(a),25.40+0.03*Math.cos(a)]);}
    for(let i=40;i>=0;i--){const a=Math.PI*(0.15+1.7*i/40);c.push([42.62+0.018*Math.sin(a),25.40+0.027*Math.cos(a)]);}c.push(c[0]);return gbShape(c,300).map(x=>[x[1],x[0]]);})()""")
  check('Q13 a C-shaped outline with a narrow gap: widening would cross itself — it falls back to a safe one', selfcross([tuple(x) for x in sh]), False)
  check('Q14 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
