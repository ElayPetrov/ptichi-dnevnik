import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-22',time='09:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8964;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,bg='Сврака',photo='phgone'),R(id=2,bg='Сойка',photo='phbad')]   # one photo missing from this device, one unreadable
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page();errs=[];alerts=[]
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:(alerts.append(d.message),d.accept()))
  pg.add_init_script("localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(250)
  pg.evaluate("""new Promise(r=>{const q=indexedDB.open('birdphotos',1);q.onsuccess=()=>{const t=q.result.transaction('p','readwrite');
    t.objectStore('p').put(new Blob(['not a picture'],{type:'image/jpeg'}),'phbad');t.oncomplete=()=>r();};})""")
  pg.reload();pg.wait_for_timeout(400)
  box=lambda nm:pg.locator('.o',has_text=nm).locator('.ph')
  check('P1 a photo missing from this device says so in Дневник', box('Сврака').inner_text(), 'снимката я няма на това устройство')
  check('P2 a stored photo that will not open says so', box('Сойка').inner_text(), 'снимката не се отваря')
  pg.click('.tab[data-v="life"]');pg.wait_for_timeout(300)
  th=pg.locator('.sp',has_text='Сврака').locator('.th')
  check('P3 its life-list thumbnail is marked instead of left blank', (th.get_attribute('class').split().count('bad'),th.inner_text(),th.get_attribute('title')), (1,'?','снимката я няма на това устройство'))
  pg.click('.tab[data-v="log"]');pg.click('#toggle');pg.fill('#f-bg','Кос')
  pg.set_input_files('#f-photo',files=[{'name':'IMG_0001.heic','mimeType':'image/heic','buffer':b'\x00\x00\x00\x18ftypheic not decodable here'}]);pg.wait_for_timeout(400)
  check('P4 picking a photo the browser cannot open warns at once', len(alerts)==1 and 'HEIC' in alerts[0], True)
  check('P5 ...and attaches nothing', (pg.is_visible('#prev'),pg.evaluate("photo")), (False,None))
  pg.set_input_files('#f-photo','a.jpg');pg.wait_for_function("document.getElementById('prev').naturalWidth>0");pg.click('#savebtn');pg.wait_for_timeout(400)
  ok=pg.evaluate("(()=>{const i=[...document.querySelectorAll('.o')].find(e=>e.textContent.includes('Кос')).querySelector('.ph img');return !!i&&i.naturalWidth>0;})()")
  check('P6 a normal photo still saves and shows in Дневник', ok, True)
  check('P7 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
