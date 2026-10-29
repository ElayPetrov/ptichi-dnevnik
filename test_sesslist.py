import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
port=int(sys.argv[1]) if len(sys.argv)>1 else 8978;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300)
  pg.click('#sessStart');pg.fill('#f-bg','Кос');pg.fill('#f-count','3');pg.click('#savebtn');pg.wait_for_timeout(150)
  pg.fill('#f-bg','Сойка');pg.click('#f-unsure');pg.click('#savebtn');pg.wait_for_timeout(150);pg.click('#cancel')
  check('S1 the green banner says it can be opened, and starts closed', (pg.evaluate("getComputedStyle(document.getElementById('sessTxt')).cursor"),pg.is_visible('#sessList')), ('pointer',False))
  pg.click('#sessTxt');pg.wait_for_timeout(150)
  rows=pg.evaluate("[...document.querySelectorAll('#sessList .ssr .n')].map(n=>n.textContent)")
  check('S2 tapping it lists the outing\'s records, newest first, unsure marked', rows, ['Сойка ?','Кос · 3'])
  check('S3 ...each with a pencil and an ×', (pg.locator('#sessList [data-ed]').count(),pg.locator('#sessList [data-del]').count()), (2,2))
  pg.click('#sessList .ssr:nth-child(2) [data-ed]');pg.wait_for_timeout(200)
  check('S4 the pencil opens that record in the form', (pg.input_value('#f-bg'),pg.inner_text('#savebtn')), ('Кос','Запази промените'))
  pg.click('#cancel');pg.click('#sessList .ssr:nth-child(1) [data-del]');pg.wait_for_timeout(200)
  check('S5 × deletes it (after asking), and the list and banner follow', (pg.evaluate("[...document.querySelectorAll('#sessList .ssr .n')].map(n=>n.textContent)"),pg.inner_text('#sessTxt').split(' · ')[-1]), (['Кос · 3'],'1 вид'))
  pg.click('#sessTxt');pg.wait_for_timeout(100)
  check('S6 tapping again closes it', pg.is_visible('#sessList'), False)
  check('S7 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
