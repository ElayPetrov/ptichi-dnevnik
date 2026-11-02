import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-05-01',time='08:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8988;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
mine=[R(id=1,bg='Кос',date='2025-06-01'),R(id=2,bg='Кос',date='2026-03-02',time='05:12'),R(id=3,bg='Кос',date='2026-04-10'),R(id=4,bg='Селска лястовица',date='2026-03-28',sess='s1'),
      R(id=5,bg='Сойка',date='2026-03-28',sess='s1',time='21:40'),R(id=6,bg='Авлига',date='2026-05-01',place='Тюлбето'),R(id=7,bg='Кос',date='2026-11-01',place='Тюлбето')]
outs=[{'id':'s1','date':'2026-03-28','place':'Копринка','start':'07:00','end':'10:00','complete':True,'with':'Петър','upd':1}]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});ctx.route('https://**',lambda r:r.abort() if 'localhost' not in r.request.url else r.continue_())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-outings',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');}"%(json.dumps(json.dumps(mine,ensure_ascii=False)),json.dumps(json.dumps(outs,ensure_ascii=False))))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  # the egg is gone
  pg.click('#toggle')
  check('R1 „гнездене ▸“ without the egg', pg.inner_text('#f-bctog'), 'гнездене ▸')
  # photos
  pg.fill('#f-bg','Голям синигер');pg.set_input_files('#f-photo','/home/claude/a.jpg');pg.wait_for_function("phNew.length===1",timeout=8000)
  check('R2 „+ още снимки“ appears once there is a main photo', pg.locator('#phxrow .phxadd').count(), 1)
  pg.set_input_files('#f-photo2',['/home/claude/b.jpg','/home/claude/a.jpg','/home/claude/b.jpg']);pg.wait_for_function("phx.length===3",timeout=8000);pg.wait_for_timeout(200)
  m0=pg.evaluate("photo")
  pg.click('#phxrow [data-phxmain="1"]');pg.wait_for_timeout(100)
  check('R3 ★ makes an extra photo the main one; the old main joins the extras', (pg.evaluate("phx.includes("+json.dumps(m0)+")"),pg.evaluate("photo")!=m0,pg.evaluate("phx.length")), (True,True,3))
  pg.click('#phxrow [data-phxdel="2"]');pg.wait_for_timeout(100)
  check('R4 × removes an extra photo', pg.evaluate("phx.length"), 2)
  pg.click('#savebtn');pg.wait_for_timeout(300);pg.click('#cancel') if pg.is_visible('#cancel') else None
  rec=pg.evaluate("OBS.find(o=>o.bg==='Голям синигер')")
  check('R5 saved: one main photo, two extras', (bool(rec['photo']),len(rec.get('photos') or [])), (True,2))
  pg.wait_for_selector('#view .phw .ph img',timeout=5000)
  check('R6 Дневник shows only the main photo, with a „+2“', (pg.locator('#view .phw .ph').count(),pg.inner_text('#view .phw .phn')), (1,'+2'))
  pg.click('#view .phw .ph img');pg.wait_for_timeout(500)
  check('R7 tapping it opens all three, to swipe through', (pg.evaluate("document.getElementById('lb').open"),pg.locator('#lbx img').count(),pg.evaluate("[...document.querySelectorAll('#lbx img')].every(i=>!!i.src)")), (True,3,True))
  pg.evaluate("document.getElementById('lb').close()")
  rid=rec['id'];pg.click(f'[data-ed="{rid}"]');pg.wait_for_timeout(200)
  check('R8 editing shows the extras again', pg.locator('#phxrow .phxi').count(), 2)
  pg.click('#phxrow [data-phxdel="0"]');pg.click('#phxrow [data-phxdel="0"]');pg.select_option('#f-cqs','est');pg.click('#savebtn');pg.wait_for_timeout(300)
  pg.click('#cancel') if pg.is_visible('#cancel') else None
  check('R9 removing the extras on edit really removes them (and they are marked for deletion online)', (pg.evaluate(f"OBS.find(o=>o.id==={rid}).photos||null"),len(pg.evaluate("JSON.parse(localStorage.getItem('bird-journal-photo-del')||'[]')"))>=2), (None,True))
  pg.click(f'[data-ed="{rid}"]');pg.select_option('#f-cqs','exact');pg.click('#savebtn');pg.wait_for_timeout(200);pg.click('#cancel') if pg.is_visible('#cancel') else None
  check('R10 switching back to „точно“ on edit clears the old kind (it used to stick)', pg.evaluate(f"OBS.find(o=>o.id==={rid}).cq||null"), None)
  # replies and notifications
  pg.evaluate("""ME={id:'me',email:'i@t.bg'};MYNAME='Иван';FR={fol:[{id:'u2',name:'Петър',data:{obs:[{id:50,date:'2026-11-01',time:'09:00',place:'Тюлбето',count:'',bg:'Кос',en:'',la:'',fam:'',note:'',h:0,s:1,p:0,beh:[],geo:null,photo:null}],outs:[]}}],fans:[]};
    SOC=[{id:'c1',owner:'u2',item:'d:2026-11-01',author:'me',kind:'comment',body:'Хубав кос!',created_at:'2026-11-01T10:00:00Z'}];SOCN={u3:'Мария'};FR.fans=[{id:'u3',name:'Мария'}];""")
  pg.click('.tab[data-v="friends"]');pg.wait_for_timeout(300)
  pg.evaluate("SOC.push({id:'c2',owner:'u2',item:'d:2026-11-01',author:'u3',kind:'comment',body:'@Иван: благодаря, и аз го видях',created_at:'2026-11-01T11:00:00Z'});paintDots()")
  check('R11 someone answers after your comment: the dot on Приятели lights', pg.evaluate("document.querySelector('.tab[data-v=friends]').classList.contains('dot')||isNewItem(fdItems().find(i=>i.key==='d:2026-11-01'&&!i.p.me))"), True)
  pg.evaluate("feedVisit=null;render()");pg.wait_for_timeout(200)
  card=pg.locator('.fc').filter(has_text='Петър').first
  check('R12 ...and the post says „нов отговор“', card.locator('.nreply').count(), 1)
  card.locator('[data-cm]').click();pg.wait_for_timeout(150)
  check('R13 a reply shows as „↪ Иван“', pg.evaluate("[...document.querySelectorAll('.cmr .cmre')].map(x=>x.textContent)"), ['↪ Иван'])
  pg.locator('.cmr [data-cmrep]').first.click();pg.wait_for_timeout(80)
  check('R14 „отговори“ starts your comment with „@Мария: “', pg.evaluate("document.activeElement.value"), '@Мария: ')
  # the year
  pg.click('.tab[data-v="log"]')
  check('R15 no banner outside 15 Dec – 15 Jan', pg.locator('.yrban').count(), 0)
  pg.evaluate("bannerYear=()=>2026;render()");pg.wait_for_timeout(100)
  check('R16 the banner from 15 December: slim, with „виж я“', pg.inner_text('.yrban .yrgo'), '✨ Твоята 2026 в Перá е готова — виж я')
  pg.click('[data-yrhide]');pg.wait_for_timeout(100)
  check('R17 × hides it, says where to find it, and it stays hidden', (pg.inner_text('.yrnote'),pg.evaluate("render(),document.querySelectorAll('.yrban').length")), ('Скрито. „Твоята година“ е винаги в профила (кръгчето горе вдясно).',0))
  pg.click('#acct');pg.wait_for_timeout(150)
  check('R18 the profile always has „Твоята година“, with past years', (pg.inner_text('[data-yr="2026"]').strip(),pg.locator('.chip[data-yr="2025"]').count()), ('✨ Твоята 2026',1))
  pg.click('button.btn[data-yr="2026"]');pg.wait_for_timeout(200)
  ks=[]
  for _ in range(15):
    ks.append(pg.inner_text('#yr-card .yrk'))
    if pg.inner_text('#yr-next')=='Затвори':break
    pg.click('#yr-next');pg.wait_for_timeout(40)
  check('R19 the story: opening, numbers, bird of the year … summary', [ks[0],ks[1],ks[2],ks[-1]], ['ПЕРÁ · 2026','ГОЛЕМИТЕ ЧИСЛА','ПТИЦАТА НА ГОДИНАТА ТИ','ТВОЯТА 2026 В ПЕРÁ'])
  D=pg.evaluate("(()=>{OBS=OBS.filter(o=>o.bg!=='Голям синигер');const D=yearData(2026);return [Object.keys(D.sp).length,D.days,D.outs.length,D.hrs,D.top.nm,D.lif.map(x=>x.o.bg),D.early.time,D.late.time,D.mate[0],D.bestDay[1].size]})()")
  check('R20 the numbers are right (species, days, outings, hours, bird of the year, new ones, earliest/latest, companion, best day)', D, [4,5,1,3,'Кос',['Селска лястовица','Сойка','Авлига'],'05:12','21:40','Петър',2])
  pg.click('#yr-share');pg.wait_for_timeout(600)
  check('R21 „Сподели“ turns the card into an image to share', pg.evaluate("document.getElementById('cardDlg').open"), True)
  check('R22 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
