import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-24',time='09:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None,upd=1),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8964;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,bg='Сврака',place='Копринка',geo='42.6300,25.3200',sess='sA'),R(id=2,bg='Сойка',place='Копринка',u=1),R(id=3,bg='Кос',place='Розариум'),
      R(id=4,bg='Сива чапла',geo='42.62112,25.39188'),R(id=5,bg='Голяма бяла чапла',geo='42.62133,25.39201'),R(id=6,bg='Кълвач',geo='42.70000,25.40000'),
      R(id=7,bg='Чинка',geo='42.66000,25.36000'),R(id=8,bg='Скорец')]
outs=[{'id':'sA','date':'2026-10-24','place':'Копринка','start':'08:00','end':'10:00','complete':True,'upd':1}]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];asked=[];answer=['accept']
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:(asked.append(d.message),d.accept() if answer[0]=='accept' else d.dismiss()))
  pg.route('https://cdnjs.cloudflare.com/**',lambda r:r.abort())   # no map needed here
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-outings',%s);}"%(json.dumps(json.dumps(data,ensure_ascii=False)),json.dumps(json.dumps(outs,ensure_ascii=False))))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300);pg.click('.tab[data-v="map"]');pg.wait_for_timeout(200)
  names=lambda:pg.evaluate("[...document.querySelectorAll('.pl .nm')].map(e=>e.textContent)")
  def ren(k,nm,ok=True):
    pg.click(f'.plh[data-pl="{k}"]');pg.wait_for_timeout(100);answer[0]='accept' if ok else 'dismiss';pg.fill('#pl-name',nm);pg.click('[data-plren]');pg.wait_for_timeout(200)
  ren('n:Копринка','Язовир Копринка',ok=False)
  check('P1 the confirmation says how many records change; cancelling changes nothing', (asked[-1],names()[0]), ('„Язовир Копринка“ ще стане мястото на 2 записа.','Копринка'))
  pg.click('.plh[data-pl="n:Копринка"]');ren('n:Копринка','Язовир Копринка')
  rec=pg.evaluate("OBS.filter(o=>o.id<=2).map(o=>[o.place,o.upd>1])")
  check('P2 renaming a place renames all its records, the unsure one too, and marks them changed for syncing', rec, [['Язовир Копринка',True],['Язовир Копринка',True]])
  check('P3 ...and the outing labelled with that place', pg.evaluate("OUTS.find(x=>x.id==='sA').place"), 'Язовир Копринка')
  check('P4 the place stays open under its new name', pg.evaluate("openPl"), 'n:Язовир Копринка')
  ren('g:42.621, 25.392','Розариум')
  check('P5 an unnamed point given an existing name joins that place (asked first)', ('слеят' in asked[-1],pg.evaluate("OBS.filter(o=>o.place==='Розариум').map(o=>o.id).sort()")), (True,[3,4,5]))
  ren('g:42.700, 25.400','Тюлбето')
  check('P6 naming another unnamed point: its records get the name; other unnamed points stay as they were',
    (pg.evaluate("OBS.find(o=>o.id===6).place"),pg.evaluate("OBS.find(o=>o.id===7).place||''"),'42.660, 25.360' in names()), ('Тюлбето','',True))
  pg.click('.plh[data-pl="x"]');pg.wait_for_timeout(100)
  check('P7 „без място и координати“ cannot be renamed (it could be anywhere)', pg.locator('.pl.on [data-plren]').count(), 0)
  pg.click('.tab[data-v="log"]');pg.click('#toggle')
  opts=pg.evaluate("[...document.querySelectorAll('#places option')].map(o=>o.value)")
  check('P8 the new names are offered when typing a place', ('Язовир Копринка' in opts,'Тюлбето' in opts,'Копринка' in opts), (True,True,False))
  check('P9 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
