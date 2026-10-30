import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
T=datetime.date.today();D=lambda n:(T-datetime.timedelta(days=n)).isoformat()
R=lambda **k:{**dict(id=0,date=D(1),time='12:00',place='Казанлък',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo='42.62,25.39',photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8975;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
mine=[R(id=1,bg='Кос',date=D(2))]
fr={'obs':[R(id=50,bg='Черен щъркел',la='Ciconia nigra',place='Копринка',geo='42.62,25.54',date=D(3),time='08:00'),R(id=51,bg='Сойка',date=D(5))],'outs':[],
    'tg':{'ciconia nigra':{'bg':'Черен щъркел','la':'Ciconia nigra','en':'Black Stork','t':1}},'spx':[{'bg':'Розово фламинго','la':'Phoenicopterus roseus','en':'Greater Flamingo'}]}
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(mine,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  tabs=pg.evaluate("[...document.querySelectorAll('.tab')].map(t=>t.textContent)");rows=pg.evaluate("new Set([...document.querySelectorAll('.tab')].map(t=>Math.round(t.getBoundingClientRect().top))).size")
  check('G1 Цели is the eighth tab, where Места was: two full rows of four', (tabs,rows), (['Дневник','Приятели','Моите видове','Излети','Карта','Цели','Фенология','Значки'],2))
  pg.evaluate("ME={id:'me',email:'i@t.bg'};MYNAME='Иван';FR={fol:[{id:'u2',name:'Петър',data:%s}],fans:[]};SPXC=null;fillLists();"%json.dumps(fr,ensure_ascii=False))
  pg.click('.tab[data-v="goals"]');pg.wait_for_timeout(200)
  check('G2 empty to begin with: only what you add appears', (pg.locator('.tgc').count(),pg.locator('.empty').count()), (0,1))
  pg.fill('#tg-in','Черен щъркел');pg.click('#tg-add');pg.wait_for_timeout(200)
  card=lambda:pg.evaluate("[...document.querySelectorAll('.tgc')].map(c=>{const k=c.cloneNode(true);k.querySelectorAll('.idl').forEach(x=>x.remove());document.body.appendChild(k);const s=k.innerText.replace(/\\n+/g,' | ');k.remove();return s;})")   # the identification links are checked in test_idlinks
  check('G3 a species from the list: its names filled in, Петър\'s last sighting with distance, and that he is after it too', card(),
    ['Черен щъркел | Ciconia nigra · Black stork | × | Последно: Петър, преди 3 дни, Копринка, 12 км | И Петър го търси.'])
  pg.fill('#tg-in','Розово фламинго');pg.click('#tg-add');pg.wait_for_timeout(200)
  check('G4 a species a friend added to the group\'s list is found too', card()[0].split(' | ')[:2], ['Розово фламинго','Phoenicopterus roseus · Greater Flamingo'])
  pg.fill('#tg-in','Императорски пингвин');pg.click('#tg-add');pg.wait_for_timeout(150)
  check('G5 a name not in any list asks for all three names', (pg.is_visible('#tg-new'),pg.input_value('#tgx-bg')), (True,'Императорски пингвин'))
  pg.fill('#tgx-la','aptenodytes');pg.click('#tgx-ok');pg.wait_for_timeout(100)
  check('G6 ...and refuses until all three are there, the Latin as „Род вид“', pg.inner_text('#tgx-msg'), 'Трябват и трите имена.')
  pg.fill('#tgx-la','Aptenodytes forsteri');pg.fill('#tgx-en','Emperor Penguin');pg.click('#tgx-ok');pg.wait_for_timeout(200)
  check('G7 then it is a target and joins the group\'s list (shared through your journal)', (len(card()),pg.evaluate("SPXO.map(x=>x.la)")), (3,['Aptenodytes forsteri']))
  pg.click('#toggle');pg.fill('#f-bg','Императорски пингвин');pg.locator('#f-bg').dispatch_event('change');pg.wait_for_timeout(150)
  check('G8 the new species now fills the form: Latin and English', (pg.input_value('#f-la'),pg.input_value('#f-en')), ('Aptenodytes forsteri','Emperor Penguin'))
  pg.click('#cancel')
  pg.click('.tab[data-v="log"]');pg.evaluate("FR.fol[0].data.obs.push({id:60,date:'%s',time:'09:00',place:'Тюлбето',count:'',bg:'Императорски пингвин',en:'',la:'Aptenodytes forsteri',fam:'',note:'',h:0,s:1,p:0,beh:[],geo:'42.63,25.40',photo:null});render()"%D(0))
  dot=lambda:pg.evaluate("document.querySelector('.tab[data-v=goals]').classList.contains('dot')")
  check('G9 Петър logs one of your targets nearby: a dot on Цели', dot(), True)
  pg.click('.tab[data-v="goals"]');pg.wait_for_timeout(200)
  check('G10 opening Цели: the card says „ново“ and today\'s sighting, and the dot goes', (pg.evaluate("[...document.querySelectorAll('.tgc.new b')].map(b=>b.firstChild.textContent)"),'Последно: Петър, днес, Тюлбето' in ' '.join(card()),dot()), (['Императорски пингвин'],True,False))
  pg.click('#toggle');pg.fill('#f-bg','Черен щъркел');pg.click('#savebtn');pg.wait_for_timeout(300)
  seen=[]
  for _ in range(3):seen.append(pg.evaluate("document.getElementById('yay').innerText"));pg.evaluate("yayHide()");pg.wait_for_timeout(450)
  check('G11 seeing a target yourself: „Цел постигната!“ (after the new-species card) and a tick on its card', (any('Цел постигната!' in x for x in seen),'✓ видян на' in ' '.join(card())), (True,True))
  pg.evaluate("yayHide()")
  pg.locator('[data-tgdel="phoenicopterus roseus"]').click();pg.wait_for_timeout(150)
  pg.evaluate("mergeIn({obs:[],outs:[],beh:[],del:{},tg:{'phoenicopterus roseus':{bg:'Розово фламинго',la:'Phoenicopterus roseus',en:'Greater Flamingo',t:5}}})");pg.reload();pg.wait_for_timeout(400)
  check('G12 a removed target stays removed, even when an older copy syncs in, and after a reload', pg.evaluate("tgList().map(t=>t.bg).sort()"), ['Императорски пингвин','Черен щъркел'])
  check('G13 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
