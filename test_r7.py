import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-20',time='12:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8989;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
# a blackbird at three places on one day (records 3, days 1, birds 2+4+1), a jay on two days (records 2, days 2, birds 2), a coot flock (1 record, 40 birds)
data=[R(id=1,bg='Кос',place='А',geo='42.60,25.30',count='2'),R(id=2,bg='Кос',place='Б',geo='42.62,25.35',count='4',beh=['пее']),R(id=3,bg='Кос',place='В',geo='42.64,25.40',beh=['пее']),
      R(id=4,bg='Сойка',date='2026-10-20'),R(id=5,bg='Сойка',date='2026-10-21'),R(id=6,bg='Лиска',count='~40')]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');}"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);pg.click('.tab[data-v="life"]');pg.wait_for_timeout(200)
  corner=pg.evaluate("Object.fromEntries([...document.querySelectorAll('#view .sp')].map(c=>[c.querySelector('.nm').textContent,c.querySelector('.cnt').innerText.replace(/\\n+/g,' | ')]))")
  check('D1 each card’s corner: days, then records and birds', corner, {'Кос':'1 ден | 3 записа | 7 птици','Сойка':'2 дни | 2 записа | 2 птици','Лиска':'1 ден | 1 запис | 40 птици'})
  order=lambda:pg.evaluate("[...document.querySelectorAll('#view .sp .nm')].map(n=>n.textContent)")
  pg.select_option('#spSort','days');pg.wait_for_timeout(80);d=order()
  pg.select_option('#spSort','recs');pg.wait_for_timeout(80);r=order()
  pg.select_option('#spSort','birds');pg.wait_for_timeout(80);bb=order()
  check('D2 sorting by days, by records, and by birds (new)', (d[0],r[0],bb), ('Сойка','Кос',['Лиска','Кос','Сойка']))
  check('D3 one bird at three places on one day is one day — crowns can’t be won in a day', pg.evaluate("spDays()['bg|кос'].size"), 1)
  check('D4 Неуморен and Етолог count one per species and day, places no longer separately', (pg.evaluate("BDEF.find(d=>d.id==='records').v(SURE())"),pg.evaluate("BDEF.find(d=>d.id==='etho').v(SURE())"),pg.evaluate("BDEF.find(d=>d.id==='records').how")), (4,1,'записи (по един за вид и ден)'))
  check('D5 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
