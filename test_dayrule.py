import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-20',time='12:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8989;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
long='Много дълга бележка за поведението на птицата.'
data=[R(id=1,bg='Кос',place='А',geo='42.60,25.30',beh=['пее'],note=long),R(id=2,bg='Кос',place='Б',geo='42.62,25.35',beh=['пее'],note=long),R(id=3,bg='Кос',place='В',geo='42.64,25.40',beh=['пее'],note=long),
      R(id=4,bg='Сойка',date='2026-10-20'),R(id=5,bg='Сойка',date='2026-10-21')]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');}"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  pg.click('.tab[data-v="life"]');pg.wait_for_timeout(150)
  cards=pg.evaluate("Object.fromEntries([...document.querySelectorAll('#view .sp')].map(c=>[c.querySelector('.nm').textContent,c.querySelector('.cnt').innerText.replace(/\\n/g,' | ')]))")
  check('D1 a card\'s number is days; records and birds small under it (three places on one day = 1 day)', cards, {'Кос':'1 ден | 3 записа | 3 птици','Сойка':'2 дни | 2 записа | 2 птици'})
  pg.select_option('#spSort','days');pg.wait_for_timeout(100)
  check('D2 „дни с вида“ sorting agrees with the number shown', pg.evaluate("[...document.querySelectorAll('#view .sp .nm')].map(n=>n.textContent)"), ['Сойка','Кос'])
  T=pg.evaluate("(()=>{const t=tiersNow();return [t.records.v,t.etho.v,t.notes.v]})()")
  check('D3 Неуморен, Етолог and Летописец count one per species and day: the same bird at three places that day is 1', T, [3,1,1])
  check('D4 the description says so', pg.evaluate("BDEF.find(d=>d.id==='records').how"), 'записи (по един за вид и ден)')
  pg.evaluate("ME={id:'me',email:'i@t.bg'};MYNAME='Иван';FR={fol:[{id:'u2',name:'Петър',data:{obs:%s,outs:[]},updated_at:new Date().toISOString()}],fans:[]};fsel='u2';view='friends';render()"%json.dumps(data,ensure_ascii=False))
  pg.click('[data-ffold="sp"]');pg.wait_for_timeout(100)
  check('D5 a friend\'s species list shows days too', pg.evaluate("[...document.querySelectorAll('[data-ffold=sp]+.fsb .ar')].map(a=>a.querySelector('b').textContent+' | '+a.querySelector(':scope>span').textContent)"), ['Кос | 1 ден','Сойка | 2 дни'])
  check('D6 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
