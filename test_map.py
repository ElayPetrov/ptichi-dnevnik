import json,math,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-22',time='',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8961;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
# a three-hour walk: 14 records with their own GPS, ~70 m apart, no place names — plus a named reservoir 6 km away
SP=['Сврака','Сойка','Чинка','Голям синигер','Син синигер','Кос','Червеногръдка','Зеленика','Щиглец','Обикновен мишелов',
    'Голям пъстър кълвач','Горска зидарка','Сива врана','Гугутка']
data=[R(id=i+1,time=f'{8+i//5:02d}:{(i*12)%60:02d}',bg=SP[i],geo=f'{42.6200+i*0.00045:.5f},{25.3900+i*0.00055:.5f}') for i in range(14)]
data+=[R(id=101,bg='Голяма бяла чапла',place='Язовир Копринка',geo='42.62900,25.32000',photo='phmap'),R(id=102,bg='Зеленоглава патица',place='Язовир Копринка',geo='42.63000,25.32100')]
TILE=bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'+'1f15c489'+'0000000d49444154789c6360f8cf000000030101007a2d0a1b0000000049454e44ae426082')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();errs=[]
  def open_map(vw):
    pg=b.new_page(viewport={'width':vw,'height':900});pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/leaflet.js',content_type='application/javascript'))
    pg.route('https://server.arcgisonline.com/**',lambda r:r.fulfill(body=TILE,content_type='image/png'))
    pg.add_init_script("localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
    pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(250)
    pg.evaluate("""new Promise(r=>{const q=indexedDB.open('birdphotos',1);q.onsuccess=async()=>{const im=await (await fetch('a.jpg')).blob();
      const t=q.result.transaction('p','readwrite');t.objectStore('p').put(im,'phmap');t.oncomplete=()=>r();};})""")
    pg.click('.tab[data-v="map"]');pg.wait_for_timeout(150)
    if vw==391:return pg   # left on what opening Карта shows
    pg.click('[data-mm=grid]');pg.wait_for_timeout(150);return pg   # the walk checks below are on Схема
  ph=open_map(390)
  raw=ph.evaluate("clusters().length");n=ph.locator('svg .pt').count()
  check('M1 on a phone the walk no longer fills the map: '+str(raw)+' points drawn as '+str(n), (n<=4, n>=2), (True,True))
  check('M2 merging loses nothing: every record is still in some point', ph.evaluate("window.__C.reduce((a,c)=>a+c.n,0)"), len(data))
  check('M3 the reservoir 6 km away stays its own point, under its name', ph.evaluate("window.__C.some(c=>c.name==='Язовир Копринка'&&c.parts.length===1)"), True)
  i=ph.evaluate("window.__C.findIndex(c=>c.parts.length>1&&!c.parts.some(p=>p.named))");ph.locator(f'svg .pt[data-c="{i}"]').click()
  t=ph.inner_text('#mp');k=ph.evaluate(f"new Set(window.__C[{i}].obs.map(key)).size")
  check('M4 tapping a merged point lists what it gathers, and all its species', ('Събрани тук:' in t,'точки без име' in t,f'{k} вида' in t), (True,True,True))
  j=ph.evaluate("window.__C.findIndex(c=>c.name==='Язовир Копринка')");ph.locator(f'svg .pt[data-c="{j}"]').click()
  try:
    ph.wait_for_function("(()=>{const i=document.querySelector('#mp .phstrip .th img');return !!i&&i.complete&&i.naturalWidth>0;})()",timeout=4000);shown=True
  except Exception: shown=False
  check('M5 a tapped point shows its photos, not blank squares', shown, True)
  dk=open_map(1000);nd=dk.locator('svg .pt').count()
  check('M6 a wide screen merges less than a phone', nd>=n, True)
  dk.click('[data-mm="real"]');dk.wait_for_function("window.__map&&document.querySelectorAll('#lmap path.leaflet-interactive').length>0",timeout=8000);dk.wait_for_timeout(400)
  cnt=lambda:dk.evaluate("document.querySelectorAll('#lmap path.leaflet-interactive').length")
  z0=dk.evaluate("window.__map.getZoom()");a=cnt()
  dk.evaluate("window.__map.setZoom(window.__map.getZoom()+5,{animate:false})");dk.wait_for_timeout(300);bb=cnt();allin=dk.evaluate("window.__C.reduce((a,c)=>a+c.n,0)")
  dk.evaluate(f"window.__map.setZoom({z0}-2,{{animate:false}})");dk.wait_for_timeout(300);c=cnt()
  check(f'M7 the real map re-merges on zoom: {a} points, {bb} zoomed in, {c} zoomed out', (bb>a, a>=c, bb==raw, allin), (True,True,True,len(data)))
  dm=open_map(391);dm.wait_for_function("document.querySelector('#lmap .leaflet-tile-loaded')",timeout=8000)
  check('M9 opening Карта shows the real map, satellite, not Схема', (dm.evaluate("mapMode"),dm.evaluate("tileKey"),dm.locator('#lmap').count()), ('real','sat',1))
  off=b.new_page(viewport={'width':390,'height':900});off.on('pageerror',lambda e:errs.append(str(e)));off.route('https://cdnjs.cloudflare.com/**',lambda r:r.abort())
  off.add_init_script("localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  off.goto(f'http://localhost:{port}/ptichi-dnevnik.html');off.wait_for_timeout(250);off.click('.tab[data-v=map]');off.wait_for_function("mapMode==='grid'&&document.querySelector('svg .pt')",timeout=8000)
  check('M10 without internet it falls back to Схема by itself, with a note', (off.evaluate("mapMode"),'не се зареди' in off.inner_text('#mapmsg')), ('grid',True))
  check('M8 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
