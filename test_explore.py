# Карта → „Изследвай“ (2026-11-07.8): GBIF's map of finds for all birds or one species; tap a point (circle) or an
# atlas square (sent to GBIF as that polygon); the panel lists what's been found there. GBIF is a stand-in here.
import json,subprocess,sys,time,datetime,io,re,urllib.parse
from playwright.sync_api import sync_playwright
from PIL import Image
T=datetime.date.today().isoformat()
port=int(sys.argv[1]) if len(sys.argv)>1 else 9007;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
def png(c,a=255):
  b=io.BytesIO();Image.new('RGBA',(256,256),c+(a,)).save(b,'PNG');return b.getvalue()
GREEN,RED=png((40,160,60)),png((220,30,30),200)
CALLS=[]
def gbif(route):
  u=urllib.parse.unquote(route.request.url);CALLS.append(u)
  if '/v2/map/' in u: return route.fulfill(body=RED,content_type='image/png')
  area='geoDistance=' in u or 'geometry=' in u
  if '/v1/species/match' in u: body={'usageKey':2482513,'matchType':'EXACT'} if 'Pica' in u else {'matchType':'NONE'}
  elif area and 'facet=year' in u and 'taxonKey=212' in u:
    body={'count':540,'facets':[{'field':'YEAR','counts':[{'name':'2010','count':5},{'name':'2025','count':90}]},{'field':'MONTH','counts':[{'name':'5','count':120},{'name':'4','count':90},{'name':'1','count':10}]}]}
  elif area and 'facet=year' in u and 'taxonKey=2482513' in u:
    body={'count':12,'facets':[{'field':'YEAR','counts':[{'name':'2019','count':2},{'name':'2024','count':10}]},{'field':'MONTH','counts':[{'name':'3','count':6},{'name':'2','count':4}]}]}
  elif area and 'facet=speciesKey' in u:
    body={'facets':[{'field':'SPECIES_KEY','counts':[{'name':'2482507','count':200},{'name':'2482513','count':12},{'name':'9999999','count':3}]}]}
  elif area and 'classKey=212' in u:
    body={'results':[{'speciesKey':2482507,'species':'Turdus merula','locality':'Розова долина'},{'speciesKey':2482513,'species':'Pica pica','locality':'Розова долина'}]}
  elif '/v1/species/9999999' in u: body={'species':'Aquila nipalensis'}
  else: body={'results':[],'count':0}
  route.fulfill(body=json.dumps(body),content_type='application/json')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844})
  ctx.route('https://api.gbif.org/**',gbif)
  ctx.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/'+('leaflet.css' if r.request.url.endswith('.css') else 'leaflet.js'),content_type='text/css' if r.request.url.endswith('.css') else 'application/javascript'))
  ctx.route('https://server.arcgisonline.com/**',lambda r:r.fulfill(body=GREEN,content_type='image/png'))
  ctx.route('https://*.basemaps.cartocdn.com/**',lambda r:r.fulfill(body=GREEN,content_type='image/png'))
  ctx.route('https://*.tile.openstreetmap.org/**',lambda r:r.fulfill(body=GREEN,content_type='image/png'))
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}")
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  pg.click('.tab[data-v="map"]');pg.wait_for_timeout(200)
  check('E1 Карта offers „Изследвай“ even with no records of your own (the personal map stays first)', pg.evaluate("[...document.querySelectorAll('[data-mm]')].map(b=>b.textContent)"), ['Истинска карта','Атлас','Изследвай'])
  pg.evaluate("OBS.push({id:7,date:'%s',time:'08:00',place:'Тюлбето',count:'',bg:'Кос',en:'',la:'',fam:'',note:'',h:0,s:1,p:0,beh:[],geo:'42.62000,25.40000',photo:null});save()"%T)
  pg.click('[data-mm="gbif"]');pg.wait_for_timeout(1500)
  check('E2 a map of where all birds have been found in Bulgaria, drawn above the map, near your latest record',
    (any('/v2/map/' in u and 'taxonKey=212' in u and 'country=BG' in u for u in CALLS),pg.evaluate("!!document.querySelector('#exmap .leaflet-gbif-pane img')"),pg.evaluate("document.getElementById('exmap')._lmap.getZoom()")), (True,True,10))
  box=pg.locator('#exmap').bounding_box();pg.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2);pg.wait_for_timeout(1500)
  t=pg.inner_text('#explace')
  check('E3 ● точка: the place, „Птици тук: 540 находки · 3 вида · 2010–2025 · най-много май и април“', (t.startswith('Розова долина и наоколо'),'Птици тук: 540 находки · 3 вида · 2010–2025 · най-много май и април' in t), (True,True))
  rows=pg.evaluate("[...document.querySelectorAll('#explace .asp')].map(a=>[a.querySelector('.nmlink,i').textContent,a.classList.contains('got'),a.innerText.includes('ново за теб')])")
  check('E4 ...and every bird found there, most found first, ✓ yours, „ново за теб“ the rest', rows, [['Кос',True,False],['Сврака',False,True],['Степен орел',False,True]])
  pg.click('[data-exm="sq"]');pg.wait_for_timeout(1500);box=pg.locator('#exmap').bounding_box();n0=len(CALLS)
  pg.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2);pg.wait_for_timeout(1500)
  geo=[u for u in CALLS[n0:] if 'geometry=POLYGON' in u]
  pts=re.findall(r'POLYGON\(\((.*?)\)\)',geo[0])[0].split(', ') if geo else []
  check('E5 ▦ квадрат: the whole 10×10 km atlas square is asked about — a closed square of 4 corners — and drawn', (len(pts),pts[0]==pts[-1] if pts else None,pg.locator('#exmap path.leaflet-interactive').count()), (5,True,1))
  check('E6 ...titled with the square’s atlas code', bool(re.match(r'Квадрат 3[45]T [A-Z]{2} \d\d',pg.inner_text('#explace .whpl b'))), True)
  pg.fill('#ex-sp','Сврака');pg.dispatch_event('#ex-sp','change');pg.wait_for_timeout(1500)
  check('E7 choosing a species shows its own hexagons', any('/v2/map/' in u and 'taxonKey=2482513' in u for u in CALLS), True)
  box=pg.locator('#exmap').bounding_box();pg.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2);pg.wait_for_timeout(1500)
  check('E8 ...and the tap tells that bird’s finds there, with the others below', ('Сврака тук: 12 находки · 2019–2024 · най-често март и февруари' in pg.inner_text('#explace'),pg.locator('#explace .asp').count()), (True,2))
  pg.reload();pg.wait_for_timeout(400);pg.click('.tab[data-v="map"]');pg.wait_for_timeout(300)
  first=pg.evaluate("document.querySelector('[data-mm][aria-pressed=\"true\"]').textContent")
  pg.click('[data-mm="gbif"]');pg.wait_for_timeout(1200)
  check('E9a after reopening, Карта starts on your personal map, as always', first, 'Истинска карта')
  check('E9 „Изследвай“ remembers the square mode and the species', (pg.evaluate("document.getElementById('ex-sp').value"),pg.evaluate("document.querySelector('[data-exm=\"sq\"]').getAttribute('aria-pressed')")), ('Сврака','true'))
  pg.click('[data-exclr]');pg.wait_for_timeout(300);pg.click('[data-mm="real"]');pg.wait_for_timeout(800)
  check('E10 the personal map is still there as before', pg.locator('#lmap').count(), 1)
  check('E11 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
