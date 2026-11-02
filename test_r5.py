import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
T=datetime.date.today();D=lambda n:(T-datetime.timedelta(days=n)).isoformat()
R=lambda **k:{**dict(id=0,date=D(5),time='12:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8987;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
mine=[R(id=1,bg='Кос',date=D(20),place='Тюлбето'),R(id=2,bg='Кос',date=D(3)),R(id=3,bg='Сойка',date=D(40)),R(id=4,bg='Авлига',date=D(1),beh=['двойка'])]
# a friend with 5 early-morning... simpler: 20 outings worth of records would be heavy; use the species badge: 100+ species is too many — use „Голямо ято“ (flock 200 in one record)
fr={'obs':[R(id=50,bg='Кос'),R(id=51,bg='Сврака',p=1,count='250'),R(id=52,bg='Сива чапла',date=D(1))],'outs':[],
    'tg':{'ciconia nigra':{'bg':'Черен щъркел','la':'Ciconia nigra','en':'Black stork','t':2}},'bdg':{}}
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});ctx.route('https://**',lambda r:r.abort() if 'localhost' not in r.request.url else r.continue_())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');}"%json.dumps(json.dumps(mine,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  # breeding codes
  pg.click('#toggle')
  check('B1 „🥚 гнездене ▸“ sits on the count line, folded like sex and age', (pg.inner_text('#f-bctog'),pg.is_visible('#f-bcbox')), ('🥚 гнездене ▸',False))
  pg.click('#f-bctog');opts=pg.evaluate("[...document.querySelectorAll('#f-bc optgroup')].map(g=>[g.label,g.children.length])")
  check('B2 a small menu with the 16 codes in three groups', opts, [['A · възможно',2],['B · вероятно',7],['C · потвърдено',7]])
  pg.click('#f-bchelp');pg.wait_for_timeout(100)
  check('B3 „?“ opens the explanation of the codes', (pg.evaluate("document.getElementById('bcDlg').open"),pg.locator('#bc-list .bcrow').count(),'Никога не приближавай гнездо' in pg.inner_text('#bcDlg')), (True,16,True))
  pg.click('#bc-close');pg.fill('#f-bg','Голям синигер');pg.select_option('#f-bc','14');pg.wait_for_timeout(50)
  check('B4 the chosen code shows on the fold link', pg.inner_text('#f-bctog'), '🥚 C14 носи храна или фекална торбичка ▾')
  chips=pg.evaluate("[...document.querySelectorAll('#beh .bh')].map(b=>b.dataset.b)")
  check('B5 „гнезди“, „с малки“, „двойка“ are no longer offered as tags for new records', [t for t in ('гнезди','с малки','двойка') if t in chips], [])
  pg.click('#savebtn');pg.wait_for_timeout(150);pg.click('#cancel') if pg.is_visible('#cancel') else None
  check('B6 saved as code 14, shown as a green chip', (pg.evaluate("OBS.find(o=>o.bg==='Голям синигер').bc"),pg.evaluate("[...document.querySelectorAll('#view .tag.bc')].map(t=>[t.textContent,t.classList.contains('bcC')])")), (14,[['C14 носи храна или фекална торбичка',True]]))
  pg.evaluate("OBS.push({...OBS.find(o=>o.bg==='Голям синигер'),id:77,date:'2025-05-10',bc:4});save();")
  pg.click('.tab[data-v="life"]');pg.locator('.sp .nm',has_text='Голям синигер').first.click();pg.wait_for_timeout(150)
  check('B7 the bird card: the strongest evidence per year', pg.inner_text('.bcline'), '🥚 Гнездене: '+str(T.year)+' — потвърдено (C14) · 2025 — вероятно (B4)')
  pg.click('[data-spback]')
  # sorting
  order=lambda:pg.evaluate("[...document.querySelectorAll('#view .sp .nm')].map(n=>n.textContent)")
  check('B8 Моите видове: a „Подреди“ menu, name A–Я by default', (pg.input_value('#spSort'),order()), ('name',['Авлига','Голям синигер','Кос','Сойка']))
  pg.select_option('#spSort','recs');pg.wait_for_timeout(100)
  check('B9 „брой записи“ puts the most recorded first', order()[:2], ['Голям синигер','Кос'])
  pg.select_option('#spSort','grp');pg.wait_for_timeout(100)
  check('B10 „по група“ adds group headings, and the choice is remembered', (pg.locator('#view h3.bdsec').count()>=2,pg.evaluate("localStorage.getItem('bird-journal-spsort')")), (True,'"grp"'))
  pg.select_option('#spSort','name')
  # the feed filter
  pg.evaluate("ME={id:'me',email:'i@t.bg'};MYNAME='Иван';FR={fol:[{id:'u2',name:'Петър',data:%s,updated_at:new Date(Date.now()-2*3600e3).toISOString()}],fans:[]};"%json.dumps(fr,ensure_ascii=False))
  pg.click('.tab[data-v="friends"]');pg.wait_for_timeout(300)
  n=lambda:pg.locator('.fc').count();pet=lambda:pg.locator('.fc',has_text='Петър').count()
  na,pa=n(),pet();pg.click('[data-fdf="me"]');pg.wait_for_timeout(150);nm_,pm=n(),pet();pg.click('[data-fdf="fr"]');pg.wait_for_timeout(150);nf,pf=n(),pet()
  check('B11 Приятели: „Всички · Мои · На приятели“ filter the posts', (nm_+nf==na,nm_>0,pm,nf==pf==pa,pg.evaluate("localStorage.getItem('bird-journal-feedf')")), (True,True,0,True,'"fr"'))
  pg.click('[data-fdf="all"]')
  # the friend's profile
  pg.evaluate("fsel='u2';view='friends';render()");pg.wait_for_timeout(250)
  check('B12 the header: his initial in his colour, name, „последно: преди 2 ч“', (pg.inner_text('.fav'),pg.inner_text('.fhn h2'),pg.inner_text('.fhs')), ('П','Петър','последно: преди 2 ч'))
  check('B13 the comparison bar: само твои / общи / само на Петър', pg.evaluate("[...document.querySelectorAll('.cbar>div')].map(d=>d.querySelector('span').textContent+':'+d.querySelector('b').textContent)"),
    ['само твои:3','общи вида:1','само на Петър:2'])
  check('B14 his latest find', (pg.inner_text('.fnew small'),pg.inner_text('.fnew b')), ('ПОСЛЕДНА НАХОДКА · ВЧЕРА','Сива чапла'))
  pg.click('[data-ffold="bd"]');pg.wait_for_timeout(100)
  check('B15 his badges are computed from his records (his log is empty): „Голямо ято“ bronze for a flock of 250, with your level', pg.evaluate("[...document.querySelectorAll('.fbm')].map(m=>m.querySelector('b').textContent+'|'+m.querySelector('span').textContent+'|'+m.querySelector('small').textContent)"),
    ['Голямо ято|бронз|ти: —'])
  pg.click('[data-ffold="rec"]');pg.wait_for_timeout(100)
  check('B16 his latest records as a timeline with coloured dots', (pg.locator('.ftl .ftr').count(),pg.locator('.ftl .ftr.l3').count()), (3,1))
  check('B17 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
