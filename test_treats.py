import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-20',time='12:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo='42.6194,25.3956',photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8961;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
td=datetime.date.today();md=td.strftime('%m-%d')
base=[R(id=1,date='2025-03-10',bg='Кос',fam='Дроздове'),R(id=2,date=f'2025-{md}',bg='Сойка'),R(id=3,date=f'2024-{md}',bg='Сврака'),R(id=4,date=f'2024-{md}',bg='Чинка')]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();errs=[]
  def page(data,scheme='light'):
    ctx=b.new_context(viewport={'width':390,'height':844},timezone_id='Europe/Sofia',color_scheme=scheme);pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
    pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300);return pg
  def add(pg,name,date=None,t=None,fam=None,photo=None,keep=False):
    if not keep: pg.click('#toggle')
    pg.fill('#f-bg',name);pg.locator('#f-bg').dispatch_event('change')
    if date: pg.fill('#f-date',date)
    if t: pg.fill('#f-time',t)
    if fam: pg.select_option('#f-fam',fam)
    if photo: pg.set_input_files('#f-photo',photo);pg.wait_for_function("document.getElementById('prev').naturalWidth>0")
    pg.click('#savebtn');pg.wait_for_timeout(250)
  card=lambda pg:pg.evaluate("document.getElementById('yay').hidden?'':document.getElementById('yay').innerText")
  clear=lambda pg:(pg.evaluate("yayQ=[];yayHide()"),pg.wait_for_timeout(420))
  pg=page(base)
  # ---- first of the year ----
  add(pg,'Кос','2026-03-06');t=card(pg)
  check('T1 first record of a known species this year: „Първа среща за 2026“, compared with last year', ('Първа среща за 2026' in t,'4 дни по-рано от миналата година' in t), (True,True))
  clear(pg);add(pg,'Кос','2026-04-01')
  check('T2 the second record that year: no pop-up', card(pg), '')
  # ---- badges ----
  pg.evaluate("(()=>{for(let j=0;j<4;j++)OBS.push({id:900+j,date:'2026-10-1'+j,time:'06:30',place:'Тюлбето',count:'',bg:'Кос',en:'',la:'',fam:'',note:'',h:0,s:1,p:0,beh:[],geo:'42.62,25.39',photo:null});save();})()")   # four earlier mornings
  add(pg,'Червеногръдка','2026-10-22','07:00');texts=[]
  for _ in range(3):
    texts.append(card(pg));pg.evaluate("yayHide()");pg.wait_for_timeout(420)
  check('T3 the fifth morning before sunrise: first the new species, then „Нова значка! Ранобудник — бронз“', (any('Честито, нов вид!' in x for x in texts),any('Нова значка!' in x and 'Ранобудник — бронз' in x for x in texts)), (True,True))
  clear(pg);add(pg,'Горска улулица','2026-10-22','21:30','Сови');texts=[]
  for _ in range(3):
    texts.append(card(pg));pg.evaluate("yayHide()");pg.wait_for_timeout(420)
  check('T4 an owl after dark: „Нощна смяна“', any('Нощна смяна' in x for x in texts), True)
  clear(pg);add(pg,'Синигер за проба','2026-10-22','06:50')
  check('T5 a badge pops up only the first time', 'Нова значка' in ' '.join([card(pg)]+[ (pg.evaluate("yayHide()"),pg.wait_for_timeout(420),card(pg))[2] for _ in range(2)]), False)
  pg.click('.tab[data-v="badges"]');pg.wait_for_timeout(200)
  st=pg.evaluate("Object.fromEntries([...document.querySelectorAll('.bd2')].map(d=>[d.querySelector('b').firstChild.textContent,[d.querySelector('.bdt').textContent,d.querySelector('.bdn').textContent]]))")
  check('T6 the Значки tab: bronze Нощна смяна for the owl after dark, bronze Ранобудник for five mornings', (st['Нощна смяна'][0],st['Ранобудник'][0]), ('Бронз','Бронз'))
  check('T7 ...with progress „5 / 25 до сребро“ and Фотограф „0 / 50 до бронз“', (st['Ранобудник'][1],st['Фотограф'][1]), ('5 / 25 до сребро','0 / 50 до бронз'))
  # ---- СТО! ----
  hundred=[R(id=1000+i,bg=f'Вид {i}') for i in range(99)]
  p2=page(hundred);add(p2,'Сврака');t=card(p2)
  check('T8 species number 100 is „СТО!“', ('СТО!' in t,'Вид № 100' in t,p2.evaluate("document.getElementById('yay').classList.contains('gold')")), (True,True,True))
  # ---- end of the outing ----
  p3=page(base);p3.click('#sessStart');p3.wait_for_timeout(150)
  add(p3,'Зеленика',t='08:10',keep=True);add(p3,'Щиглец',t='08:40',keep=True);add(p3,'Сойка',t='09:05',keep=True)
  clear(p3);p3.click('#sessEnd');p3.click('[data-done="1"]');p3.wait_for_timeout(300);t=card(p3)
  check('T9 finishing an outing sums it up', ('Край на излета' in t,'3 вида · 3 записа' in t,'2 нови за дневника' in t,'първа птица: Зеленика в 08:10' in t), (True,True,True,True))
  p3.click('#yay [data-yayout]');p3.wait_for_function("document.getElementById('cardDlg').open",timeout=6000)
  check('T10 ...and its „картичка за споделяне“ opens the outing card', p3.evaluate("document.getElementById('cardDlg').open"), True)
  # ---- „На днешна дата“ ----
  p4=page(base);t=p4.inner_text('.otd') if p4.locator('.otd').count() else ''
  check('T11 „На днешна дата“ lists earlier years with records today, newest first', ('2025' in t and 'Сойка' in t, t.index('2025')<t.index('2024') if '2024' in t else False), (True,True))
  p4.click(f'[data-otd="2024-{md}"]');p4.wait_for_timeout(300)
  check('T12 tapping a year opens that day', p4.evaluate(f"!document.querySelector('[data-dayt=\"2024-{md}\"]').closest('.dayg').classList.contains('shut')"), True)
  p5=page([R(id=1,date='2026-10-01',bg='Кос')])
  check('T13 nothing from earlier years today: no line at all', p5.locator('.otd').count(), 0)
  # ---- the sky ----
  ph=lambda pg,mins:pg.evaluate(f"(()=>{{const d=new Date();d.setHours(0,0,0,0);const S=sunOf(ymd(d.getTime()));skyAt=new Date(d.getFullYear(),d.getMonth(),d.getDate(),0,({mins})(S));applySeason(document.querySelector('.hero').dataset.season);return document.querySelector('.hero').dataset.sky;}})()")
  got=[ph(p5,"S=>S.dawn-20"),ph(p5,"S=>S.rise+10"),ph(p5,"S=>720"),ph(p5,"S=>S.set-10"),ph(p5,"S=>S.set+60")]
  check('T14 the sky follows the day: night, dawn, day, dusk, night', got, ['night','dawn','day','dusk','night'])
  night=p5.evaluate("(()=>{const h=document.querySelector('.hero'),vis=s=>getComputedStyle(h.querySelector(s)).display!=='none';return [vis('.s-night'),vis('.sun'),!!h.querySelector('.s-owl'),h.querySelectorAll('#stars circle').length>20,getComputedStyle(h).getPropertyValue('--hill2').trim()===SEASONS[h.dataset.season].d.hill2];})()")
  check('T15 at night: stars, moon and an owl, no sun, and the hills go dark even in the light theme', night, [True,False,True,True,True])
  check('T16 the moon\'s phase is right (full moon of 7 Oct 2025)', p5.evaluate("Math.abs(moonPhase(Date.UTC(2025,9,7,3,47))-.5)<.03"), True)
  check('T17 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
