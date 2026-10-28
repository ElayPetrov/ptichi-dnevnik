import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-27',time='12:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8973;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
names=['Сврака','Сойка','Кос','Чинка','Голям синигер','Син синигер','Гугутка','Щиглец','Врабче','Зеленика','Червеногръдка','Скорец','Сива врана','Гарван','Чучулига',
       'Бяла стърчиопашка','Полско врабче','Сива чапла','Голяма бяла чапла','Лиска','Голям гмурец','Зеленоглава патица','Обикновен мишелов','Черна каня','Керкенез']
data=[R(id=i+1,bg=n,date=f'2026-09-{(i%27)+1:02d}') for i,n in enumerate(names)]
fr={'obs':[R(id=100+j,bg=n,date=f'2026-10-{(j%27)+1:02d}') for j,n in enumerate(names)],'outs':[]}   # newer, so his cards come first
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':700});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);pg.click('.tab[data-v="life"]');pg.wait_for_timeout(250)
  card=pg.locator('.sp[data-k]').nth(18);card.scroll_into_view_if_needed();pg.evaluate("window.scrollBy(0,-120)");pg.wait_for_timeout(150)
  y0=pg.evaluate("Math.round(scrollY)");name=card.locator('.nm').inner_text()
  card.locator('.nm').click();pg.wait_for_timeout(250)
  check('K1 opening a species far down the list shows its page from the top', (pg.locator('[data-spback]').count()>0,pg.evaluate("Math.round(scrollY)")<y0), (True,True))
  pg.click('[data-spback]');pg.wait_for_timeout(250)
  check('K2 „назад“ returns the list to where you were, not the top', abs(pg.evaluate("Math.round(scrollY)")-y0)<=2, True)
  check('K3 ...with that species still in view', pg.evaluate(f"(()=>{{const c=[...document.querySelectorAll('.sp .nm')].find(n=>n.textContent==={json.dumps(name,ensure_ascii=False)});const r=c.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight;}})()"), True)
  pg.evaluate("ME={id:'me',email:'i@t.bg'};MYNAME='Иван';FR={fol:[{id:'u2',name:'Петър',data:%s}],fans:[]};"%json.dumps(fr,ensure_ascii=False))
  pg.click('.tab[data-v="friends"]');pg.wait_for_timeout(300)
  who=pg.locator('.fc .fwho').nth(8);who.scroll_into_view_if_needed();pg.wait_for_timeout(150);y1=pg.evaluate("Math.round(scrollY)")
  who.click();pg.wait_for_timeout(250);pg.click('[data-frback]');pg.wait_for_timeout(250)
  check('K4 the same in the feed: back from a friend\'s journal returns to where you were', abs(pg.evaluate("Math.round(scrollY)")-y1)<=2, True)
  check('K5 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
