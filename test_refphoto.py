import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-27',time='12:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8981;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,bg='Кос'),R(id=2,bg='Сойка')]
IMG=open('/home/claude/a.jpg','rb').read();asked=[]
def wiki(route):
  t=route.request.url.split('/summary/')[1];asked.append(t)
  if 'Garrulus' in t:return route.fulfill(status=200,content_type='application/json',body='{}')   # an article without a picture
  route.fulfill(status=200,content_type='application/json',body=json.dumps({'thumbnail':{'source':'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Test_'+t+'.jpg/320px-Test_'+t+'.jpg'}}))
def commons(route):
  route.fulfill(status=200,content_type='application/json',body=json.dumps({'query':{'pages':{'1':{'imageinfo':[{'thumburl':'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/T.jpg/480px-T.jpg','url':'https://upload.wikimedia.org/wikipedia/commons/a/ab/T.jpg',
    'descriptionurl':'https://commons.wikimedia.org/wiki/File:T.jpg','extmetadata':{'Artist':{'value':'<a href="x">Иван Тестов</a><img src=x onerror="window.__x=1">'},'LicenseShortName':{'value':'CC BY-SA 4.0'}}}]}}}}))
def net(ctx,on=True):
  ctx.unroute('**/*') if False else None
  if on:
    ctx.route('https://en.wikipedia.org/api/rest_v1/page/summary/**',wiki);ctx.route('https://commons.wikimedia.org/w/api.php**',commons)
    ctx.route('https://upload.wikimedia.org/**',lambda r:r.fulfill(status=200,content_type='image/jpeg',body=IMG))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});net(ctx)
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);pg.evaluate("yayHide&&yayHide()")
  pg.click('.tab[data-v="life"]');pg.wait_for_timeout(200)
  check('P1 the list of your birds shows no reference photos (those are your own)', pg.locator('#view .refbig,#view .refsm').count(), 0)
  pg.locator('.sp .nm',has_text='Кос').first.click();pg.wait_for_selector('.refbig.has img',timeout=5000)
  check('P2 the bird\'s page shows the photo at the top with its credit, linked to Commons', (pg.inner_text('.refbig .refcr'),pg.get_attribute('.refbig .refcr','href')),
    ('Снимка: Иван Тестов · CC BY-SA 4.0 · Wikimedia Commons','https://commons.wikimedia.org/wiki/File:T.jpg'))
  check('P3 ...the small silhouette steps aside and the crown sits on the photo; nothing ran from the credit text', (pg.is_visible('.sphd .thw'),pg.evaluate("window.__x||0")), (False,0))
  check('P3b the whole photo fits a box of fixed height (nothing cut off), the sides filled with a blurred copy', pg.evaluate("(()=>{const w=document.querySelector('.refbig .refpic');return [Math.round(w.getBoundingClientRect().height),getComputedStyle(w.querySelector('img')).objectFit,!!w.querySelector('.refbg')]})()"), [220,'contain',True])
  pg.click('[data-spback]');pg.locator('.sp .nm',has_text='Сойка').first.click();pg.wait_for_timeout(800)
  check('P4 an article without a picture: the silhouette stays', (pg.locator('.refbig.has').count(),pg.is_visible('.sphd .thw')), (0,True))
  # offline: the blackbird's photo was kept, the jay never had one
  ctx.unroute('https://en.wikipedia.org/api/rest_v1/page/summary/**');ctx.unroute('https://commons.wikimedia.org/w/api.php**');ctx.unroute('https://upload.wikimedia.org/**')
  ctx.route('https://*.wikipedia.org/**',lambda r:r.abort());ctx.route('https://*.wikimedia.org/**',lambda r:r.abort())
  pg.reload();pg.wait_for_timeout(400);pg.evaluate("yayHide&&yayHide()");pg.click('.tab[data-v="life"]');pg.locator('.sp .nm',has_text='Кос').first.click();pg.wait_for_timeout(600)
  check('P5 without signal the kept photo still shows, with its credit', (pg.locator('.refbig.has img').count(),pg.locator('.refbig .refcr').count()), (1,1))
  ctx.unroute('https://*.wikipedia.org/**');ctx.unroute('https://*.wikimedia.org/**');net(ctx)
  pg.click('.tab[data-v="log"]');pg.click('#toggle');pg.fill('#f-bg','Горска дърволазка');pg.locator('#f-bg').dispatch_event('change');pg.click('#f-unsure');pg.click('[data-alts="Градинска дърволазка"]');pg.click('#f-cmp')
  pg.wait_for_function("document.querySelectorAll('#cmp-list .refsm.has img').length===2",timeout=6000)
  check('P6 „Сравни“ puts a small photo beside each candidate, with its credit', pg.evaluate("[...document.querySelectorAll('#cmp-list .refsm .refcr')].map(a=>a.textContent.startsWith('Снимка:'))"), [True,True])
  pg.click('#cmp-close');pg.click('#cancel')
  pg.click('.tab[data-v="goals"]');pg.fill('#tg-in','Императорски пингвин');pg.click('#tg-add');pg.fill('#tgx-la','Aptenodytes forsteri');pg.fill('#tgx-en','Emperor Penguin');pg.click('#tgx-ok')
  pg.wait_for_function("document.querySelector('.tgc .refsm.has img')",timeout=6000)
  check('P7 Цели cards get a small photo, the credit one tap away (©) — also for a species the user added', (pg.get_attribute('.tgc .refsm .refc','title'),'Aptenodytes_forsteri' in asked), ('Снимка: Иван Тестов · CC BY-SA 4.0 · Wikimedia Commons',True))
  # little room on the phone: the photo is shown but not kept
  pg.evaluate("navigator.storage.estimate=async()=>({quota:100e6,usage:80e6});delete REFI['Ardea cinerea']")
  pg.evaluate("OBS.push({id:9,date:'2026-10-27',time:'12:00',place:'',count:'',bg:'Сива чапла',en:'',la:'',fam:'',note:'',h:0,s:1,p:0,beh:[],geo:null,photo:null});save()")
  pg.click('.tab[data-v="life"]');pg.locator('.sp .nm',has_text='Сива чапла').first.click();pg.wait_for_selector('.refbig.has img',timeout=5000)
  kept=pg.evaluate("getPhoto('ref:Ardea cinerea').then(b=>!!b)")
  check('P8 with less than ~50 MB free, the photo is shown but not kept', kept, False)
  pg.click('#acct');pg.wait_for_function("document.getElementById('refInfo').textContent.includes('Примерните снимки')",timeout=3000)
  pg.click('[data-refclear]');pg.wait_for_timeout(300)
  check('P9 „Изчисти примерните снимки“ in Данни empties them', (pg.evaluate("getPhoto('ref:Turdus merula').then(b=>!!b)"),pg.evaluate("refUsed()")), (False,0))
  check('P10 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
