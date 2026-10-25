import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-25',time='09:00',place='Тюлбето',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8967;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,bg='Градинска дърволазка',la='Certhia brachydactyla',date='2026-10-20')]   # a sure Short-toed Treecreeper from before
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300)
  pg.click('#toggle');pg.fill('#f-bg','Горска дърволазка');pg.locator('#f-bg').dispatch_event('change')
  check('A1 „Може да е и“ stays hidden until „не съм сигурен“ is on', pg.is_visible('#f-alt-row'), False)
  pg.click('#f-unsure')
  check('A2 ...then it appears, suggesting the other treecreeper (same genus)', (pg.is_visible('#f-alt-row'),pg.evaluate("[...document.querySelectorAll('[data-alts]')].map(b=>b.dataset.alts)")), (True,['Градинска дърволазка']))
  pg.click('[data-alts="Градинска дърволазка"]');pg.fill('#f-alt-in','Зидарка');pg.click('#f-alt-add')
  chips=lambda:pg.evaluate("[...document.querySelectorAll('#f-alt .altc')].map(c=>c.firstChild.textContent)")
  check('A3 a tap adds the suggestion; any other name can be typed in', chips(), ['Градинска дърволазка','Зидарка'])
  pg.click('#f-alt [data-altx="1"]')
  check('A4 × removes one', chips(), ['Градинска дърволазка'])
  pg.click('#savebtn');pg.wait_for_timeout(300)
  r=pg.evaluate("OBS.find(o=>o.bg==='Горска дърволазка')")
  check('A5 saved as unsure, with its alternatives', (r['u'],r['alt']), (1,['Градинска дърволазка']))
  check('A6 Дневник shows „или Градинска дърволазка“', pg.locator('.o.uns .altnm').first.inner_text(), 'или Градинска дърволазка')
  check('A7 the alternatives don\'t merge species or count: still 1 species, the sure Short-toed one', (pg.evaluate("new Set(SURE().map(key)).size"),pg.evaluate("key(OBS[0])!==key(OBS[1])")), (1,True))
  pg.fill('#q','градинска');pg.wait_for_timeout(200)
  check('A8 searching an alternative finds the unsure record too', pg.locator('.o').count(), 2)
  pg.fill('#q','');pg.click('.tab[data-v="life"]');pg.wait_for_timeout(200)
  check('A9 Моите видове lists it among the unsure-only ones with its alternatives', 'Горска дърволазка / Градинска дърволазка' in pg.inner_text('#view'), True)
  pg.click('.tab[data-v="log"]');pg.click(f'[data-ed="{r["id"]}"]');pg.wait_for_timeout(150)
  check('A10 editing shows them again', chips(), ['Градинска дърволазка'])
  pg.click('#f-unsure');pg.click('#savebtn');pg.wait_for_timeout(300)
  check('A11 once you\'re sure (unsure off), they are dropped', pg.evaluate("OBS.find(o=>o.bg==='Горска дърволазка').alt||null"), None)
  pg.click('#toggle');pg.fill('#f-bg','Матовоглав синигер');pg.locator('#f-bg').dispatch_event('change');pg.click('#f-unsure')
  check('A12 Willow tit suggests the other two Poecile tits', pg.evaluate("[...document.querySelectorAll('[data-alts]')].map(b=>b.dataset.alts).sort()"), ['Жалобен синигер','Лъскавоглав синигер'])
  pg.click('#cancel')
  narrow=b.new_page(viewport={'width':340,'height':800});narrow.on('pageerror',lambda e:errs.append(str(e)))
  narrow.add_init_script("localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps([R(id=5,bg='Средиземноморска чайка',count='12',u=1,alt=['Жълтокрака чайка','Белоглава чайка'])],ensure_ascii=False)))
  narrow.goto(f'http://localhost:{port}/ptichi-dnevnik.html');narrow.wait_for_timeout(300)
  lay=narrow.evaluate("""(()=>{const o=document.querySelector('.o'),n=o.querySelector('.oh .nm').getBoundingClientRect(),x=o.querySelector('.oh .x').getBoundingClientRect(),a=o.querySelector('.altnm').getBoundingClientRect(),c=o.getBoundingClientRect();
    return [n.right<=x.left+0.5,x.right<=c.right+0.5,a.top>=n.bottom-1];})()""")
  check('A14 a long name with a count never runs under „промени ×“, and the alternatives sit on their own line below', lay, [True,True,True])
  check('A13 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
