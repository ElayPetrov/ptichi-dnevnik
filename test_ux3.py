# 3 Nov 2026: nothing sticks out past the screen (the sunrise line and every two-column row), the map's style
# chips as small sub-tabs on one row, and „Всички видове“ in Моите видове.
import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-05-10',time='08:30',place='Язовир Копринка, източния бряг до старата помпена станция',count='',bg='Кос',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo='42.61000,25.30000',photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8995;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=i,date=f'2026-05-{10+i:02d}',time='08:4'+str(i)) for i in range(1,6)]+[R(id=9,bg='Розово фламинго',la='Phoenicopterus roseus')]
TILE=bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'+'1f15c489'+'0000000d49444154789c6360f8cf000000030101007a2d0a1b0000000049454e44ae426082')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':340,'height':780},timezone_id='Europe/Sofia')
  ctx.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/leaflet.js',content_type='application/javascript'))
  ctx.route('https://server.arcgisonline.com/**',lambda r:r.fulfill(body=TILE,content_type='image/png'));ctx.route('https://tile.openstreetmap.org/**',lambda r:r.fulfill(body=TILE,content_type='image/png'))
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  wide=lambda:pg.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth")
  pg.click('.tab[data-v="life"]');pg.wait_for_timeout(150);pg.locator('.sp .nm',has_text='Кос').first.click();pg.wait_for_timeout(200)
  check('X1 the bird card: „Сутрин обикновено го срещаш … след изгрева.“', pg.inner_text('.sunl').startswith('Сутрин обикновено го срещаш '), True)
  check('X2 ...and nothing on the card sticks out past a 340 px screen (long place names included)', wide(), False)
  pg.click('[data-spback]');pg.wait_for_timeout(100)
  check('X3 Моите видове starts with „Моите · 2 / Всички видове · 413“', pg.evaluate("[...document.querySelectorAll('.lifetabs button')].map(b=>b.textContent)"), ['Моите · 2','Всички видове · 413'])
  pg.click('[data-lifeall="1"]');pg.wait_for_timeout(200)
  check('X4 „Всички видове“: every species, by group with counts, a tick on the ones you have', (pg.locator('.asp').count(),pg.locator('.asp.got').count(),pg.inner_text('h3.bdsec >> nth=0')), (413,2,'Грабливи 0 / 37'))
  check('X5 ...plain names, no pictures; rare ones marked', (pg.locator('.allsp img').count(),pg.locator('.asp .rr').count()), (0,73))
  pg.locator('.asp .nmlink',has_text='Сребриста чайка').click();pg.wait_for_timeout(200)
  check('X6 tapping a species you don’t have opens its card (photo, sounds, links)', 'Още нямаш сигурни записи на този вид.' in pg.inner_text('#view'), True)
  pg.click('[data-spback]');pg.wait_for_timeout(150)
  check('X7 „назад“ returns to the full list', pg.evaluate("LIFEALL"), True)
  pg.click('[data-lifeall="0"]');pg.wait_for_timeout(100)
  pg.click('.tab[data-v="map"]');pg.wait_for_timeout(300)
  if pg.evaluate("mapMode")!='real':pg.click('[data-mm="real"]');pg.wait_for_timeout(300)
  geo=pg.evaluate("(()=>{const m=document.querySelector('[data-mm=real]').getBoundingClientRect(),s=[...document.querySelectorAll('.tilesub .sub')].map(b=>b.getBoundingClientRect());return [s.length,new Set(s.map(r=>Math.round(r.top))).size,s.every(r=>r.height<m.height),document.documentElement.scrollWidth>document.documentElement.clientWidth]})()")
  check('X8 the map’s styles are small sub-tabs on one row, smaller than „Истинска карта“, without widening the page', geo, [5,1,True,False])
  check('X9 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
