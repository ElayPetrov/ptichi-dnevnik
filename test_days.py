import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='',time='09:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8955;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,date='2026-10-20',bg='Сврака',photo='phold'),R(id=2,date='2026-10-20',bg='Сойка'),
      R(id=3,date='2026-10-21',bg='Сокол',u=1),R(id=4,date='2026-10-21',bg='Кос'),
      R(id=5,date='2026-10-22',bg='Чинка'),R(id=6,date='2026-10-22',bg='Щиглец'),R(id=7,date='2026-10-22',bg='Чинка',time='10:00')]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(250)
  pg.evaluate("""new Promise(r=>{const q=indexedDB.open('birdphotos',1);q.onsuccess=async()=>{const im=await (await fetch('a.jpg')).blob();
    const t=q.result.transaction('p','readwrite');t.objectStore('p').put(im,'phold');t.oncomplete=()=>r();};})""")
  pg.reload();pg.wait_for_timeout(300)
  state=lambda:pg.evaluate("[...document.querySelectorAll('.dayg')].map(g=>g.querySelector('[data-dayt]').dataset.dayt+(g.classList.contains('shut')?':shut':':open'))")
  check('D1 only the newest day is open at first', state(), ['2026-10-22:open','2026-10-21:shut','2026-10-20:shut'])
  head=lambda d:pg.locator(f'[data-dayt="{d}"] .dcount').inner_text()
  check('D2 each day header counts its records and species; unsure records add a record, not a species', (head('2026-10-22'),head('2026-10-21'),head('2026-10-20')), ('3 записа · 2 вида','2 записа · 1 вид','2 записа · 2 вида'))
  ph=lambda:pg.evaluate("(()=>{const d=document.querySelector('[data-ph=\"phold\"]');return [!!d.dataset.loaded,!!d.querySelector('img')];})()")
  check('D3 a photo in a folded day is not loaded yet', ph(), [False,False])
  pg.click('[data-dayt="2026-10-20"]');pg.wait_for_function("(()=>{const i=document.querySelector('[data-ph=\"phold\"] img');return i&&i.complete&&i.naturalWidth>0;})()",timeout=4000)
  pg.click('[data-dayt="2026-10-22"]')
  check('D4 tapping opens or folds a day, and its photo loads when opened', state(), ['2026-10-22:shut','2026-10-21:shut','2026-10-20:open'])
  pg.reload();pg.wait_for_timeout(300)
  check('D5 your choices are remembered after a reload', state(), ['2026-10-22:shut','2026-10-21:shut','2026-10-20:open'])
  pg.fill('#q','ко');pg.wait_for_timeout(150)
  check('D6 searching opens every day with a match', state(), ['2026-10-21:open'])
  pg.fill('#q','');pg.wait_for_timeout(150)
  check('D7 ...and clearing the search brings your choices back', state(), ['2026-10-22:shut','2026-10-21:shut','2026-10-20:open'])
  pg.click('#toggle');pg.fill('#f-date','2026-10-21');pg.fill('#f-bg','Гугутка');pg.click('#savebtn');pg.wait_for_timeout(300)
  check('D8 a record saved into a folded day opens that day, so it does not seem to vanish', (state()[1],pg.locator('.dayg',has_text='Гугутка').locator('.o',has_text='Гугутка').is_visible()), ('2026-10-21:open',True))
  check('D9 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
