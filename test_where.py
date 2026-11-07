# „📍 Къде да го търся“ (2026-11-07.5): from GBIF (no key) — loads only when opened; month chart, heat map of Bulgaria,
# the nearest places to your latest GPS record; cached for a week; in Цели a button opens it. GBIF is a stand-in here.
import json,subprocess,sys,time,datetime,re
from playwright.sync_api import sync_playwright
T=datetime.date.today().isoformat()
port=int(sys.argv[1]) if len(sys.argv)>1 else 9006;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
TILE=bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'+'1f15c489'+'0000000d49444154789c6360f8cf000000030101007a2d0a1b0000000049454e44ae426082')
CALLS=[]
def gbif(route):
  u=route.request.url;CALLS.append(u)
  if '/v1/species/match' in u:
    body={'usageKey':2490384,'matchType':'EXACT'} if 'Garrulus' in u or 'Corvus' in u else {'matchType':'NONE'}
  elif 'facet=month' in u:
    body={'count':1234,'facets':[{'field':'MONTH','counts':[{'name':'5','count':300},{'name':'6','count':150},{'name':'1','count':20}]}]}
  elif 'geoDistance' in u:
    body={'results':[{'decimalLatitude':42.66,'decimalLongitude':25.40,'eventDate':'2025-05-03T07:00','locality':'Казанлък, парк Тюлбето','datasetName':'EOD - eBird Observation Dataset'},
                     {'decimalLatitude':42.661,'decimalLongitude':25.401,'eventDate':'2025-06-10','locality':'Казанлък, парк Тюлбето','datasetName':'EOD - eBird Observation Dataset'},
                     {'decimalLatitude':42.80,'decimalLongitude':25.10,'eventDate':'2024-09-01','locality':'','datasetName':'iNaturalist research-grade observations'}]}
  elif '/v2/map/' in u: return route.fulfill(body=TILE,content_type='image/png')
  else: body={}
  route.fulfill(body=json.dumps(body),content_type='application/json')
data=[{'id':1,'date':T,'time':'08:00','place':'Тюлбето','count':'','bg':'Кос','en':'','la':'','fam':'','note':'','h':0,'s':1,'p':0,'beh':[],'geo':'42.65000,25.39000','photo':None}]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844})
  ctx.route('https://api.gbif.org/**',gbif)
  ctx.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/'+('leaflet.css' if r.request.url.endswith('.css') else 'leaflet.js'),content_type='text/css' if r.request.url.endswith('.css') else 'application/javascript'))
  ctx.route('https://server.arcgisonline.com/**',lambda r:r.fulfill(body=TILE,content_type='image/png'))
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  pg.evaluate("spOpen({bg:'Сойка',la:'Garrulus glandarius',en:'Eurasian jay'})");pg.wait_for_timeout(300)
  check('W1 a bird card has „📍 Къде да го търся“, folded, and nothing is fetched until you open it', (pg.locator('details.where').count(),pg.evaluate("document.querySelector('details.where').open"),len(CALLS)), (1,False,0))
  pg.click('details.where summary');pg.wait_for_timeout(1500)
  bars=pg.evaluate("[...document.querySelectorAll('.whmb i')].map(i=>parseInt(i.style.height))")
  check('W2 opened: a bar for each month, tallest in May (from GBIF’s counts for Bulgaria), and the total', (len(bars),bars.index(max(bars)),'1 234 находки' in pg.inner_text('.whb') or '1234 находки' in pg.inner_text('.whb')), (12,4,True))
  rows=pg.evaluate("[...document.querySelectorAll('.whn .row')].map(r=>r.innerText.replace(/\\s+/g,' ').trim())")
  check('W3 the nearest places to your latest GPS record, nearest first, grouped by place, with the last date and the source', (len(rows),rows[0].startswith('Казанлък, парк Тюлбето'),'2×' in rows[0],'eBird' in rows[0],'iNaturalist' in rows[1]), (2,True,True,True,True))
  check('W4 a heat map of Bulgaria from GBIF (map tiles for this species and country)', (pg.locator('.whmap.leaflet-container').count(),any('/v2/map/occurrence/density/' in u and 'taxonKey=2490384' in u and 'country=BG' in u for u in CALLS)), (1,True))
  check('W5 the source is named and linked', ('GBIF.org' in pg.inner_text('.whsrc'),pg.evaluate("document.querySelector('.whsrc a').href").startswith('https://www.gbif.org/occurrence/map?taxon_key=2490384')), (True,True))
  n0=len([u for u in CALLS if '/v1/' in u]);pg.click("[data-spback]");pg.wait_for_timeout(100);pg.evaluate("spOpen({bg:'Сойка',la:'Garrulus glandarius',en:'Eurasian jay'})");pg.wait_for_timeout(200)
  pg.click('details.where summary');pg.wait_for_timeout(600)
  check('W6 opening it again uses what’s kept on the phone (a week) — no new questions to GBIF', len([u for u in CALLS if '/v1/' in u])-n0, 0)
  pg.click("[data-spback]");pg.wait_for_timeout(100);pg.evaluate("spOpen({bg:'Непозната',la:'Avis nulla',en:''})");pg.wait_for_timeout(200)
  pg.click('details.where summary');pg.wait_for_timeout(600)
  check('W7 a species GBIF doesn’t know says so', 'Няма данни за този вид в GBIF.' in pg.inner_text('.whb'), True)
  pg.click("[data-spback]");pg.evaluate("tgAdd({bg:'Сива врана',la:'Corvus cornix',en:'Hooded crow'})");pg.click('.tab[data-v="goals"]');pg.wait_for_timeout(200)
  pg.click('[data-tgwhere="Corvus cornix"]');pg.wait_for_timeout(1500)
  check('W8 Цели: „📍 Къде да го търся“ opens the bird’s card with the section open and loaded', (pg.evaluate("document.querySelector('details.where').open"),pg.locator('.whmb').count()), (True,12))
  check('W9 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
