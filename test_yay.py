import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-20',time='09:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8959;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
NAMES=['Сврака','Сойка','Кос','Чинка','Голям синигер','Син синигер','Гугутка','Щиглец','Врабче']   # nine species already in the journal
data=[R(id=i+1,bg=n) for i,n in enumerate(NAMES)]+[R(id=50,bg='Сокол',u=1)]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300)
  shown=lambda:pg.evaluate("!document.getElementById('yay').hidden")
  def add(name,unsure=False,photo=None):
    pg.click('#toggle');pg.fill('#f-bg',name);pg.locator('#f-bg').dispatch_event('change')   # „видях“ is on by default
    if unsure: pg.click('#f-unsure')
    if photo: pg.set_input_files('#f-photo',photo);pg.wait_for_function("document.getElementById('prev').naturalWidth>0")
    pg.click('#savebtn');pg.wait_for_timeout(250)
  add('Сврака')
  check('Y1 another record of a species you already have: no pop-up', shown(), False)
  add('Кукувица',unsure=True)
  check('Y2 an unsure new species: no pop-up (it doesn\'t count)', shown(), False)
  add('Горска зидарка')
  t=pg.inner_text('#yay')
  check('Y3 a new species: „Честито, нов вид!“, its names and its number', ('Честито, нов вид!' in t,'Горска зидарка' in t,'Sitta europaea' in t,'Вид № 10 в дневника ти' in t), (True,True,True,True))
  check('Y4 ...and the 10th gets a round-number line', 'Кръгла бройка — 10 вида!' in t, True)
  check('Y5 it shows the family\'s silhouette', pg.locator('#yay .yaypic svg.sil').count(), 1)
  pg.wait_for_timeout(5600)
  check('Y6 it hides by itself after a few seconds', shown(), False)
  add('Кос')   # existing
  add('Червеногръдка',photo='a.jpg')
  pg.wait_for_function("(()=>{const i=document.querySelector('#yay .yaypic img');return !!i&&i.complete&&i.naturalWidth>0;})()",timeout=4000)
  check('Y7 with a photo, it shows your photo; no round number at 11', (pg.locator('#yay .yaypic img').count(),'Кръгла' in pg.inner_text('#yay')), (1,False))
  pg.click('#yay .yaycard');pg.wait_for_function("document.getElementById('cardDlg').open&&document.getElementById('cardImg').naturalWidth>0",timeout=6000)
  pg.wait_for_timeout(450)
  check('Y8 its „картичка за споделяне“ opens the share card for that species, and the pop-up closes', (pg.evaluate("document.getElementById('cardDlg').open"),'Erithacus-rubecula' in pg.evaluate("cardFile&&cardFile.name"),shown()), (True,True,False))
  pg.evaluate("document.getElementById('cardDlg').close()")
  # during an outing the form reopens for the next bird and keeps the cursor; the pop-up doesn't get in the way
  pg.click('#sessStart');pg.fill('#f-bg','Зеленика');pg.locator('#f-bg').dispatch_event('change');pg.click('[data-s="h"]');pg.click('#savebtn');pg.wait_for_timeout(300)
  check('Y9 during an outing it shows while the cursor stays in the name for the next bird', (shown(),pg.evaluate("document.activeElement.id")), (True,'f-bg'))
  pg.keyboard.type('Кос');check('Y10 ...so you can just keep typing', pg.input_value('#f-bg'), 'Кос')
  pg.mouse.click(200,60);pg.wait_for_timeout(500)
  check('Y11 a tap on it closes it at once', shown(), False)
  check('Y12 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
