# eBird (2026-11-09.1), through the Supabase helper with the key in Supabase's secrets: real names for the orange eBird
# spots, „Наскоро тук“ (30 days) in a spot's panel, „eBird наблизо“ on each target in Цели; without a key nothing
# changes and Перá stops asking after one try. EEA, GBIF and the helper are stand-ins here.
import json,subprocess,sys,time,io,urllib.parse,datetime
from playwright.sync_api import sync_playwright
from PIL import Image
T=datetime.date.today();Y=(T-datetime.timedelta(days=1)).isoformat()
port=int(sys.argv[1]) if len(sys.argv)>1 else 9009;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
def png(c,a=255):
  b=io.BytesIO();Image.new('RGBA',(256,256),c+(a,)).save(b,'PNG');return b.getvalue()
G=png((214,222,200));C0=(42.62,25.40);SPOT=(42.605,25.425)
HAVEKEY=[True];EBQ=[]
def helper(route):
  u=route.request.url;q=urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
  if 'ebird' in q:
    path=q['ebird'][0];EBQ.append(path)
    if not HAVEKEY[0]: return route.fulfill(status=503,body='{"error":"no key"}',content_type='application/json')
    if path.startswith('ref/hotspot/info/'): body={'locId':path.rsplit('/',1)[1],'name':'Atanasovsko Lake--Saltpans'}
    elif path.startswith('data/obs/L2205561/recent'): body=[{'comName':'Eurasian Blackbird','sciName':'Turdus merula','obsDt':Y+' 08:10','howMany':3},{'comName':'Gray Heron','sciName':'Ardea cinerea','obsDt':Y+' 08:20','howMany':1}]
    elif path.startswith('codes?'): body={'Corvus cornix':'hoocro1'}
    elif path.startswith('data/obs/geo/recent/hoocro1'): body=[{'comName':'Hooded Crow','sciName':'Corvus cornix','obsDt':Y+' 09:00','lat':42.70,'lng':25.40,'locName':'Atanasovsko Lake--Saltpans'},{'obsDt':(T-datetime.timedelta(days=9)).isoformat(),'lat':42.62,'lng':25.41,'locName':'Другаде'}]
    else: body=[]
    return route.fulfill(body=json.dumps(body),content_type='application/json')
  route.fulfill(status=400,body='{}')
def gbif(route):
  u=urllib.parse.unquote(route.request.url)
  if 'facet=locality' in u: body={'facets':[{'field':'LOCALITY','counts':[{'name':'L2205561','count':300}]}]}
  elif 'locality=' in u: body={'results':[{'decimalLatitude':SPOT[0],'decimalLongitude':SPOT[1]}]*20}
  elif 'facet=year' in u: body={'count':300,'facets':[{'field':'YEAR','counts':[{'name':'2025','count':30}]},{'field':'MONTH','counts':[{'name':'5','count':20}]}]}
  elif 'facet=speciesKey' in u: body={'facets':[{'field':'SPECIES_KEY','counts':[{'name':'2482507','count':30}]}]}
  else: body={'results':[{'speciesKey':2482507,'species':'Turdus merula'}],'count':1}
  route.fulfill(body=json.dumps(body),content_type='application/json')
def click_ll(pg,la,lo):
  pt=pg.evaluate(f"(()=>{{const m=document.getElementById('exmap')._lmap,p=m.latLngToContainerPoint([{la},{lo}]),r=document.getElementById('exmap').getBoundingClientRect();return [r.left+p.x,r.top+p.y]}})()")
  pg.mouse.click(pt[0],pt[1])
def session(b):
  ctx=b.new_context(viewport={'width':390,'height':844})
  ctx.route('https://bio.discomap.eea.europa.eu/**',lambda r:r.fulfill(body='{"type":"FeatureCollection","features":[]}',content_type='application/json'))
  ctx.route('https://szyituwdlbwpqkfuklxq.supabase.co/functions/v1/osm**',helper);ctx.route('https://api.gbif.org/**',gbif)
  ctx.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/'+('leaflet.css' if r.request.url.endswith('.css') else 'leaflet.js'),content_type='text/css' if r.request.url.endswith('.css') else 'application/javascript'))
  for pat in ['https://server.arcgisonline.com/**','https://*.basemaps.cartocdn.com/**','https://*.tile.openstreetmap.org/**']:ctx.route(pat,lambda r:r.fulfill(body=G,content_type='image/png'))
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');localStorage.setItem('bird-journal-explore','{\"mode\":\"pl\",\"sp\":null}');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps([{'id':7,'date':T.isoformat(),'time':'08:00','place':'','count':'','bg':'Кос','en':'Eurasian blackbird','la':'Turdus merula','fam':'','note':'','h':0,'s':1,'p':0,'beh':[],'geo':'%.5f,%.5f'%C0,'photo':None}],ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);return ctx,pg,errs
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  ctx,pg,errs=session(b)
  pg.click('.tab[data-v="map"]');pg.click('[data-mm="gbif"]');pg.wait_for_timeout(3000)
  tip=pg.evaluate("document.getElementById('exmap')._places.LH.getLayers().filter(l=>l.getTooltip&&l.getTooltip()).map(l=>l.getTooltip().getContent())")
  check('B1 with the key: the orange eBird spot gets its real name from eBird (instead of „eBird място L2205561“)', tip, ['Atanasovsko Lake--Saltpans'])
  pg.evaluate("document.getElementById('exmap')._lmap.setView([%f,%f],13)"%SPOT);pg.wait_for_timeout(1500);pg.locator('#exmap').scroll_into_view_if_needed();click_ll(pg,*SPOT);pg.wait_for_timeout(2500)
  t=pg.inner_text('#explace')
  h4=pg.evaluate("[...document.querySelectorAll('#explace .psub')].map(h=>h.textContent)")
  check('B2 tapping it: titled with the real name, and „Наскоро тук“ — what eBird birders saw there in the last 30 days', (t.split('\n')[0].startswith('Atanasovsko Lake--Saltpans · 300 находки тук'),'Наскоро тук · eBird, последните 30 дни · 2 вида' in h4), (True,True))
  rows=pg.evaluate("[...document.querySelectorAll('#explace .whpl')].pop().querySelectorAll('.prw').length")
  got=pg.evaluate("[...[...document.querySelectorAll('#explace .whpl')].pop().querySelectorAll('.prw')].map(r=>[r.querySelector('.nmlink,i')?r.querySelector('.nmlink,i').textContent:r.querySelector('.pnm').firstChild.textContent,r.classList.contains('got'),r.innerText.includes('ново за теб'),r.innerText.includes('вчера')])")
  check('B3 ...in Bulgarian, with when (вчера), ✓ for yours and „ново за теб“ for the rest', got, [['Кос',True,False,True],['Сива чапла',False,True,True]])
  pg.evaluate("tgAdd({bg:'Сива врана',la:'Corvus cornix',en:'Hooded crow'})");pg.click('.tab[data-v="goals"]');pg.wait_for_timeout(2000)
  check('B4 Цели: the nearest recent eBird sighting within 50 km — when, how far, where', pg.inner_text('[data-tgeb="Corvus cornix"]'), 'eBird наблизо: вчера · 8,8 км · Atanasovsko Lake--Saltpans')
  check('B5 no page errors (with the key)', errs, []);ctx.close()
  HAVEKEY[0]=False;EBQ.clear();ctx,pg,errs=session(b)
  pg.click('.tab[data-v="map"]');pg.click('[data-mm="gbif"]');pg.wait_for_timeout(3000)
  tip=pg.evaluate("document.getElementById('exmap')._places.LH.getLayers().filter(l=>l.getTooltip&&l.getTooltip()).map(l=>l.getTooltip().getContent())")
  pg.evaluate("tgAdd({bg:'Сива врана',la:'Corvus cornix',en:'Hooded crow'})");pg.click('.tab[data-v="goals"]');pg.wait_for_timeout(1500)
  check('B6 without a key: everything as before — the code as the name, no eBird lines — and Перá stopped asking after one try', (tip,pg.locator('.tgeb:not(:empty)').count(),len(EBQ),pg.evaluate("EBOK")), (['eBird място L2205561'],0,1,False))
  check('B7 no page errors (without the key)', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
