# iPhone: the first open (welcome → „Запиши първата“) must leave the form usable; on iPhone the app never moves the
# keyboard focus by code (a field focused without a tap can stay without a keyboard). Plus „J“ → jay.
# (This is Chrome with an iPhone identity — it checks Перá's side; Safari's own behaviour can only be tried on a phone.)
import subprocess,sys,time
from playwright.sync_api import sync_playwright
port=int(sys.argv[1]) if len(sys.argv)>1 else 9005;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
IPH='Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  ctx=b.new_context(viewport={'width':390,'height':844},user_agent=IPH);ctx.route('https://**',lambda r:r.abort())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("Object.defineProperty(navigator,'standalone',{get:()=>true})")   # opened from the Home Screen, as your testers do
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(900)
  check('I1 a new user’s first open shows the welcome cards', pg.evaluate("document.getElementById('wlDlg').open"), True)
  pg.evaluate("wlI=WLC.length-1;wlDraw()");pg.wait_for_timeout(80);pg.click('[data-wl="first"]');pg.wait_for_timeout(400)
  st=pg.evaluate("[document.getElementById('wlDlg').open,document.getElementById('form').classList.contains('on'),document.activeElement&&document.activeElement.id,Math.round(scrollY)]")
  check('I2 „Запиши първата“ on iPhone: the welcome closes, then the form opens, with no field focused by code, at the top', [st[0],st[1],st[2]!='f-bg',st[3]], [False,True,True,0])
  pg.fill('#f-bg','Кос');pg.wait_for_timeout(80)
  check('I3 ...and the name field takes typing', pg.evaluate("document.getElementById('f-bg').value"), 'Кос')
  pg.click('#cancel');pg.wait_for_timeout(100);pg.click('#toggle');pg.wait_for_timeout(150)
  check('I4 „+ Ново наблюдение“ on iPhone doesn’t focus a field by code', pg.evaluate("document.activeElement&&document.activeElement.id")!='f-bg', True)
  pg.click('#cancel');pg.click('#vcOpen');pg.wait_for_timeout(150)
  check('I5 the voice panel on iPhone explains the language comes from the keyboard', 'Езикът е този на клавиатурата' in pg.inner_text('#vc-hint'), True)
  check('I6 „J“ is how English recognition writes „jay“: „J three“, „two J’s“', (pg.evaluate("vcParse('J three').map(e=>e.bg+' ×'+e.count)"),pg.evaluate("vcParse(\"two J's\").map(e=>e.bg+' ×'+e.count)")), (['Сойка ×3'],['Сойка ×2']))
  check('I7 no page errors', errs, [])
  c2=b.new_context(viewport={'width':390,'height':844});c2.route('https://**',lambda r:r.abort());q=c2.new_page()
  q.add_init_script("localStorage.setItem('bird-journal-tips','{\"all\":1}')");q.goto(f'http://localhost:{port}/ptichi-dnevnik.html');q.wait_for_timeout(400);q.click('#toggle');q.wait_for_timeout(150)
  check('I8 on Android and computers the form still puts the cursor in the name field', q.evaluate("document.activeElement&&document.activeElement.id"), 'f-bg')
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
