import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-27',time='12:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8983;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
mine=[R(id=i+1,bg='Кос',date=f'2026-10-{i%20+1:02d}',sess='s1' if i<2 else None) for i in range(25)]+[R(id=50,bg='Сойка',sess='s1',date='2026-10-01')]
outs=[{'id':'s1','date':'2026-10-01','place':'Копринка','start':'08:00','end':'10:00','complete':True,'upd':1}]
fr={'obs':[R(id=100,bg='Кос',date='2026-10-28'),R(id=101,bg='Черен щъркел',date='2026-10-28')],'outs':[]}
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});ctx.route('https://**',lambda r:r.abort() if 'localhost' not in r.request.url else r.continue_())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-outings',%s);}"%(json.dumps(json.dumps(mine,ensure_ascii=False)),json.dumps(json.dumps(outs,ensure_ascii=False))))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);pg.evaluate("yayHide&&yayHide()")
  pg.evaluate("ME={id:'me',email:'i@t.bg'};MYNAME='Иван';FR={fol:[{id:'u2',name:'Петър',data:%s}],fans:[]};"%json.dumps(fr,ensure_ascii=False))
  # Приятели: open Petar's post, tap a bird you have, then one you don't
  pg.click('.tab[data-v="friends"]');pg.wait_for_timeout(300)
  card=pg.locator('.fc').filter(has_text='Петър').first;card.locator('.fcn').click();pg.wait_for_timeout(200)
  ln=card.locator('.fcr [data-sprf]',has_text='Кос').first;ln.scroll_into_view_if_needed();pg.wait_for_timeout(100);y0=pg.evaluate("Math.round(scrollY)")
  ln.click();pg.wait_for_timeout(250)
  check('N1 in an opened post, a bird you have opens your bird card, with „← Приятели“', (pg.evaluate("view"),pg.evaluate("spSel==='~'"),pg.inner_text('[data-spback]'),'дни с вида' in pg.inner_text('.spd')), ('life',False,'← Приятели',True))
  pg.click('[data-spback]');pg.wait_for_timeout(250)
  check('N2 back to Приятели, the post still open, at the same spot', (pg.evaluate("view"),pg.locator('.fc .fcr .o').count()>0,abs(pg.evaluate("Math.round(scrollY)")-y0)<=3), ('friends',True,True))
  pg.locator('.fc .fcr [data-sprf]',has_text='Черен щъркел').first.click();pg.wait_for_timeout(250)
  t=pg.inner_text('.spd')
  check('N3 a bird you don\'t have yet opens a lighter card: names, links, „Още нямаш сигурни записи…“', ('Черен щъркел' in t,'Ciconia nigra' in t,'Още нямаш сигурни записи на този вид.' in t,pg.locator('.spd .idl a').count(),pg.locator('[data-spcard]').count()), (True,True,True,3,0))
  check('N3b ...with room for its photo and its sounds', (pg.locator('.spd .refbig[data-ref="Ciconia nigra"]').count(),pg.locator('.spd .xcw[data-xc="Ciconia nigra"]').count()), (1,1))
  pg.click('[data-spback]');pg.wait_for_timeout(200)
  # Излети: open the outing; both the species chips and the records' names lead to the card
  pg.click('.tab[data-v="outs"]');pg.locator('.ou').first.click();pg.wait_for_timeout(200)
  check('N4 an opened outing: its species and its records\' names are links', (pg.locator('.ou .sl [data-sprf]').count(),pg.locator('.ou .orr [data-sprf]').count()), (2,3))
  pg.locator('.ou .orr [data-sprf]',has_text='Сойка').first.click();pg.wait_for_timeout(250)
  check('N5 ...opens the bird card with „← Излети“; back leaves the outing open', (pg.inner_text('[data-spback]'),pg.inner_text('.spd .big')), ('← Излети','Сойка'))
  pg.click('[data-spback]');pg.wait_for_timeout(200)
  check('N5b ...the outing is still open', (pg.evaluate("view"),pg.locator('.ou .orr').count()), ('outs',3))
  # Цели
  pg.click('.tab[data-v="goals"]');pg.fill('#tg-in','Черен щъркел');pg.click('#tg-add');pg.wait_for_timeout(150)
  pg.locator('.tgc [data-sprf]').first.click();pg.wait_for_timeout(250)
  check('N6 a target\'s name opens its card, with „← Цели“', (pg.inner_text('[data-spback]'),'Черен щъркел' in pg.inner_text('.spd')), ('← Цели',True))
  pg.click('[data-spback]');pg.wait_for_timeout(150)
  check('N6b ...and back on Цели', pg.evaluate("view"), 'goals')
  pg.click('.tab[data-v="life"]');pg.locator('.sp .nm',has_text='Кос').first.click();pg.wait_for_timeout(200)
  check('N7 opened from Моите видове it says „← Моите видове“ again', pg.inner_text('[data-spback]'), '← Моите видове')
  pg.click('[data-spback]');pg.click('.tab[data-v="log"]');pg.wait_for_timeout(150)
  check('N8 in Дневник every bird\'s name is a link, unsure ones too', pg.evaluate("[...document.querySelectorAll('#view .o .nm')].filter(n=>n.offsetParent).every(n=>n.querySelector('[data-sprf]'))"), True)
  check('N9 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
