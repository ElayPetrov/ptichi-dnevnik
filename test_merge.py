import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
T=datetime.date.today();D=lambda n:(T-datetime.timedelta(days=n)).isoformat()
R=lambda **k:{**dict(id=0,date=D(1),time='12:00',place='Копринка',count='',bg='Кос',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo='42.62,25.39',photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8974;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,date=D(1)),R(id=2,date=D(1),bg='Сойка'),R(id=3,date=D(10)),R(id=4,date=D(200),place='Тюлбето',geo='42.63,25.40'),R(id=5,date=D(400)),R(id=6,date=D(20),u=1)]
TILE=bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'+'1f15c489'+'0000000d49444154789c6360f8cf000000030101007a2d0a1b0000000049454e44ae426082')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/leaflet.js',content_type='application/javascript'))
  pg.route('https://server.arcgisonline.com/**',lambda r:r.fulfill(body=TILE,content_type='image/png'))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  st=pg.evaluate("[...document.querySelectorAll('.stats .st')].map(s=>[s.querySelector('b').textContent,s.querySelector('span').textContent])")
  check('G1 a sixth box: days in the field over the last 365 days (sure records; a year ago doesn\'t count)', st[-1], ['3','дни на терен'])
  rows=pg.evaluate("new Set([...document.querySelectorAll('.stats .st')].map(s=>Math.round(s.getBoundingClientRect().top))).size")
  check('G2 six boxes in two even rows of three on a phone', (len(st),rows), (6,2))
  check('G3 no Места tab any more', pg.locator('.tab[data-v="places"]').count(), 0)
  pg.click('.tab[data-v="map"]');pg.wait_for_function("document.querySelector('#lmap .leaflet-tile-loaded')",timeout=8000)
  check('G4 Карта: the map on top, then „Места“ with every place', (pg.evaluate("document.querySelector('#plsec').previousElementSibling.textContent"),pg.evaluate("[...document.querySelectorAll('#plsec .pl .nm')].map(n=>n.textContent)")), ('Места',['Копринка','Тюлбето']))
  pg.evaluate("document.getElementById('lmap').dataset.mark='same'")
  pg.click('.plh[data-pl="n:Копринка"]');pg.wait_for_timeout(400)
  check('G5 opening a place redraws only the list; the map above stays as you left it', (pg.evaluate("document.getElementById('lmap')&&document.getElementById('lmap').dataset.mark"),pg.locator('#plsec .pl.on .orr').count()), ('same',4))
  check('G6 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
