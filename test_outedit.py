import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
D='2026-10-24'
R=lambda **k:{**dict(id=0,date=D,time='',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo='42.62,25.39',photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8962;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,time='07:30',bg='Сврака'),R(id=2,time='07:45',bg='Сойка'),R(id=3,time='08:10',bg='Кос',sess='sX',place='Копринка'),
      R(id=4,time='08:40',bg='Чинка',sess='sX',place='Копринка'),R(id=5,time='09:05',bg='Щиглец',sess='sX',place='Копринка'),R(id=6,time='11:30',bg='Гугутка'),
      R(id=7,date='2026-10-23',time='10:00',bg='Кълвач')]
outs=[{'id':'sX','date':D,'place':'Копринка','start':'08:00','end':'10:00','complete':False,'upd':1}]
TILE=bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'+'1f15c489'+'0000000d49444154789c6360f8cf000000030101007a2d0a1b0000000049454e44ae426082')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();errs=[]
  def page(w=390,fresh=True):
    pg=b.new_page(viewport={'width':w,'height':844});pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
    pg.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/leaflet.js',content_type='application/javascript'))
    pg.route('https://server.arcgisonline.com/**',lambda r:r.fulfill(body=TILE,content_type='image/png'))
    if fresh: pg.add_init_script("if(!localStorage.getItem('bird-journal-v3')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-outings',%s);}"%(json.dumps(json.dumps(data,ensure_ascii=False)),json.dumps(json.dumps(outs,ensure_ascii=False))))
    pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300);return pg
  pg=page()
  items=lambda:pg.evaluate(f"""[...document.querySelector('[data-dayt="{D}"]').closest('.dayg').querySelector('.dayb').children].map(e=>e.classList.contains('og')?'['+[...e.querySelectorAll('.o .nm')].map(n=>n.firstChild.textContent).join(',')+']':e.querySelector('.nm').firstChild.textContent)""")
  check('E1 within the day: later birds, the outing as one block, earlier birds', items(), ['Гугутка','[Щиглец,Чинка,Кос]','Сойка','Сврака'])
  check('E2 the block header: times, place, records and species', pg.inner_text('.og .ogt').replace('\n',' '), '▾Излет · 08:00–10:00 · Копринка 3 записа · 3 вида')
  pg.click('[data-ogt="sX"]');pg.reload();pg.wait_for_timeout(300)
  check('E3 the outing folds, and stays folded after a reload', (pg.evaluate("document.querySelector('.og').classList.contains('shut')"),pg.locator('.og .o').first.is_visible()), (True,False))
  pg.click('[data-ogt="sX"]')
  pg.click('.og [data-oadd]');pg.wait_for_timeout(150)
  check('E4 „+ птица“ opens the form on that outing: its date, place and the outing selected', (pg.input_value('#f-date'),pg.input_value('#f-place'),pg.input_value('#f-sess'),pg.input_value('#f-time')), (D,'Копринка','sX','10:00'))
  pg.fill('#f-bg','Сива врана');pg.click('#savebtn');pg.wait_for_timeout(300)
  check('E5 ...and the forgotten bird lands inside the outing', items()[1], '[Сива врана,Щиглец,Чинка,Кос]')
  pg.click('[data-ed="2"]');pg.select_option('#f-sess','sX');pg.click('#savebtn');pg.wait_for_timeout(300)
  check('E6 a loose record from that day can be put into the outing afterwards', items(), ['Гугутка','[Сива врана,Щиглец,Чинка,Кос,Сойка]','Сврака'])
  pg.click('[data-ed="4"]');pg.select_option('#f-sess','');pg.click('#savebtn');pg.wait_for_timeout(300)
  check('E7 ...and taken out of it again', 'Чинка' in items(), True)
  pg.click('.og [data-oedit]');pg.fill('#od-start','07:50');pg.fill('#od-end','10:30');pg.fill('#od-place','Язовир Копринка');pg.select_option('#od-comp','1');pg.click('#od-save');pg.wait_for_timeout(200)
  pg.click('.tab[data-v="outs"]');pg.wait_for_timeout(150)
  check('E8 editing the outing in Дневник shows in Излети too', (pg.inner_text('.ou .nm'),pg.inner_text('.ou .meta').split(' · ')[0],pg.inner_text('.ou .tag')), ('24 октомври 2026 · Язовир Копринка','07:50–10:30','пълен списък'))
  pg.locator('.ou').first.click();pg.click('.ou [data-oedit]');pg.fill('#od-end','11:00');pg.click('#od-save');pg.click('.tab[data-v="log"]');pg.wait_for_timeout(150)
  check('E9 ...and editing it in Излети shows in Дневник', pg.inner_text('.og .ogt').split('\n')[0], '▾Излет · 07:50–11:00 · Язовир Копринка')
  pg.click('.og [data-oedit]');pg.fill('#od-date','2026-10-22');pg.click('#od-save');pg.wait_for_timeout(200)
  check('E10 moving the outing to another date moves its records too', pg.evaluate("OBS.filter(o=>o.sess==='sX').map(o=>o.date).every(d=>d==='2026-10-22')"), True)
  pg.fill('#q','щиг');pg.wait_for_timeout(200)
  check('E11 searching shows the outing with just the matching bird, open', (pg.locator('.og').count(),pg.locator('.og .o').count(),pg.evaluate("document.querySelector('.og').classList.contains('shut')")), (1,1,False))
  pg.fill('#q','');pg.wait_for_timeout(150)
  # a live outing: new birds go in, labelled „сега“; „— без излет —“ makes a loose record
  l=page(fresh=False);l.evaluate("localStorage.clear()");l=page()
  l.click('#sessStart');l.fill('#f-bg','Зеленика');l.click('#savebtn');l.wait_for_timeout(250)
  live=l.evaluate("(()=>{const g=document.querySelector('.og.live');return [!!g,g&&g.querySelector('.ogt b').textContent,g&&!!g.querySelector('[data-oedit]'),document.getElementById('f-sess').value===SESS.id];})()")
  check('E12 during an outing: its block says „сега“, no editing yet, and the next record defaults to it', live, [True,'Излет · сега',False,True])
  l.fill('#f-bg','Врабче');l.select_option('#f-sess','');l.click('#savebtn');l.wait_for_timeout(250)
  check('E13 ...„— без излет —“ saves a loose record and closes the form', (l.evaluate("OBS.find(o=>o.bg==='Врабче').sess||''"),l.evaluate("form.classList.contains('on')")), ('',False))
  # narrow phones: nothing pushes the page sideways on Фенология or Карта
  n=page(w=360);res={}
  for tab,sel in [('phen','[data-pm]'),('map','[data-mm]')]:
    n.click(f'.tab[data-v="{tab}"]');n.wait_for_timeout(200)
    for k in n.evaluate(f"[...document.querySelectorAll('{sel}')].map(e=>e.getAttribute('{sel[1:-1]}'))"):
      n.click(f'[{sel[1:-1]}="{k}"]');n.wait_for_timeout(700)
      res[f'{tab}:{k}']=n.evaluate("document.documentElement.scrollWidth<=document.documentElement.clientWidth")
  check('E14 at 360 px wide, Фенология and Карта (both modes) fit the screen', all(res.values()) and len(res)==5, True)
  check('E15 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
