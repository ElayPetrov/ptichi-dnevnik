# Regression checks from the 2 Nov 2026 bug hunt: the six boxes, levels on cards and filters, the backup round-trip,
# and the year button in the profile.
import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2025-10-20',time='12:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8990;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,bg='Кос',h=1,s=0),R(id=2,bg='Сойка'),R(id=3,bg='Сврака',p=1),R(id=4,bg='Лиска',h=1,s=0),R(id=5,bg='Лиска',date='2025-10-21',s=1,h=0),
      R(id=6,bg='Сива чапла',count='40',cq='est',**{'as':{'m':3}},bc=4,photo=None,photos=None)]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  check('Q1 the six boxes: само чути / видени / снимани count species by their best level again', pg.evaluate("['n-obs','n-sp','n-h','n-s','n-p'].map(id=>document.getElementById(id).textContent)"), ['6','5','1','4','1'])
  pg.click('.tab[data-v="life"]');pg.wait_for_timeout(150)
  check('Q2 species cards carry their level (heard / seen / photographed)', pg.evaluate("Object.fromEntries([...document.querySelectorAll('#view .sp')].map(c=>[c.querySelector('.nm').textContent,[...c.classList].find(x=>/^l\\d$/.test(x))]))"),
    {'Кос':'l1','Сойка':'l2','Сврака':'l3','Лиска':'l2','Сива чапла':'l2'})
  pg.evaluate("filt='h';render()");h=pg.evaluate("[...document.querySelectorAll('#view .sp .nm')].map(n=>n.textContent)")
  pg.evaluate("filt='p';render()");pp=pg.evaluate("[...document.querySelectorAll('#view .sp .nm')].map(n=>n.textContent)");pg.evaluate("filt='all';render()")
  check('Q3 the heard-only and photographed filters work again', (h,pp), (['Кос'],['Сврака']))
  # backup round-trip, now with targets, the group's species and badge levels
  pg.evaluate("tgAdd({bg:'Черен щъркел',la:'Ciconia nigra',en:'Black stork'});spxAdd({bg:'Розово фламинго',la:'Phoenicopterus roseus',en:'Greater Flamingo'});BDG['early:1']={r:1,d:'2025-10-20'};")
  open('/tmp/bak8.json','w',encoding='utf-8').write(pg.evaluate("bakData()"))
  pg2=b.new_page();pg2.on('pageerror',lambda e:errs.append('2:'+str(e)));pg2.on('dialog',lambda d:d.accept())
  pg2.add_init_script("localStorage.setItem('bird-journal-tips','{\"all\":1}')")
  pg2.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg2.wait_for_timeout(400);pg2.click('#acct');pg2.set_input_files('#impf','/tmp/bak8.json');pg2.wait_for_timeout(600)
  check('Q4 a backup restored on a new phone brings back records, targets, the group\'s species and badge levels', (pg2.evaluate("OBS.length"),pg2.evaluate("tgList().map(t=>t.bg)"),pg2.evaluate("SPXO.map(x=>x.la)"),pg2.evaluate("!!BDG['early:1']")),
    (6,['Черен щъркел'],['Phoenicopterus roseus'],True))
  check('Q5 ...and every newer field of a record (kind of count, sex/age, breeding code)', pg2.evaluate("(o=>[o.cq,o.as,o.bc])(OBS.find(o=>o.id===6))"), ['est',{'m':3},4])
  pg.click('#acct');pg.wait_for_timeout(150)
  check('Q6 the profile\'s year button opens the latest year that has records (here 2025)', pg.inner_text('.btn[data-yr]').strip(), '✨ Твоята 2025')
  check('Q7 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
