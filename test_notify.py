import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-27',time='12:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8969;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
mine=[R(id=1,date='2026-10-27',time='12:00',bg='Сойка',sess='m1')]
fr={'obs':[R(id=10,date='2026-10-20',time='08:10',bg='Сива чапла',sess='s1'),R(id=11,date='2026-10-20',time='08:30',bg='Лиска',sess='s1')],'outs':[{'id':'s1','date':'2026-10-20','place':'Копринка','start':'08:00','end':'09:00'}]}
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_context(viewport={'width':390,'height':844},timezone_id='Europe/Sofia').new_page();   # local time, so 06:00 is before sunrise
  errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(mine,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300)
  check('N1 the round button is a little bird: head, beak and eye', pg.evaluate("[!!document.querySelector('#acct .beak'),document.querySelectorAll('#acct circle').length]"), [True,2])
  sign="ME={id:'me1',email:'i@t.bg'};MYNAME='Иван';FR={fol:[{id:'u2',name:'Петър',data:%s}],fans:[{id:'u2',name:'Петър'}]};SOC=[];render();"%json.dumps(fr,ensure_ascii=False)
  pg.evaluate(sign)
  dot=lambda v:pg.evaluate(f"document.querySelector('.tab[data-v=\"{v}\"]').classList.contains('dot')")
  check('N2 the first time, what is already there counts as seen: no dot', dot('friends'), False)
  pg.evaluate("FR.fol[0].data.obs.push({id:12,date:'2026-10-20',time:'08:50',place:'Копринка',count:'',bg:'Голям корморан',en:'',la:'',fam:'',note:'',h:0,s:1,p:0,beh:[],geo:null,photo:null,sess:'s1'});render()")
  check('N3 a friend adds a bird to an old outing: an orange dot on Приятели', dot('friends'), True)
  tab=lambda v:(pg.click(f'.tab[data-v="{v}"]'),pg.wait_for_timeout(200))
  tab('friends');order=lambda:pg.evaluate("[...document.querySelectorAll('.fc')].map(c=>c.querySelector('.fchn b').firstChild.textContent+(c.classList.contains('new')?' (ново)':''))")
  check('N4 opening Приятели: that card comes first, marked „ново“, and the dot goes', (order(),dot('friends')), (['Петър (ново)','Ти'],False))
  pg.evaluate("render()")
  check('N5 nothing jumps while you look', order(), ['Петър (ново)','Ти'])
  tab('log');tab('friends')
  check('N6 after you leave and come back it is back in its place, no longer new', order(), ['Ти','Петър'])
  tab('log');pg.evaluate("SOC.push({id:'c1',owner:'me1',item:'o:m1',author:'u2',kind:'comment',body:'Браво!',created_at:'2026-10-28T10:00:00Z'});render()")
  check('N7 a friend comments on your outing: dot', dot('friends'), True)
  tab('friends')
  check('N8 ...and your card comes first, marked „ново“', order(), ['Ти (ново)','Петър'])
  tab('log');pg.evaluate("SOC.push({id:'b1',owner:'me1',item:'o:m1',author:'me1',kind:'bravo',body:null,created_at:'2026-10-28T11:00:00Z'});render()")
  check('N9 your own „Браво“ on your outing doesn\'t count as new', dot('friends'), False)
  check('N10 Значки: no dot while nothing new is earned', dot('badges'), False)
  pg.evaluate("OBS.push({id:50,date:'2026-10-27',time:'06:00',place:'Копринка',count:'',bg:'Кос',en:'',la:'',fam:'',note:'',h:0,s:1,p:0,beh:[],geo:'42.62,25.39',photo:null,upd:Date.now()});save();render()")
  check('N11 a bird before sunrise earns Ранобудник: dot on Значки', dot('badges'), True)
  tab('badges')
  check('N12 opening Значки marks it „ново“ and the dot goes', (pg.evaluate("[...document.querySelectorAll('.bd.new b')].map(b=>b.firstChild.textContent)"),dot('badges')), (['Ранобудник'],False))
  tab('log');tab('badges')
  check('N13 seen once, it is no longer new', pg.locator('.bd.new').count(), 0)
  check('N14 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
