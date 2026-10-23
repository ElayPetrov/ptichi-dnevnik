import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-20',time='09:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8957;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,bg='сврака',en='Magpie')]   # his own spelling: lower case, his own English name
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300)
  check('S1 the list holds 268 species, each in one of the app\'s groups, no name used twice',
    pg.evaluate("(()=>{const n=SPL.flatMap(s=>[s[0],s[5]]).filter(Boolean).map(nrm);return [SPL.length,SPL.every(s=>FAMS[s[3]]),new Set(n).size===n.length];})()"), [268,True,True])
  vals=lambda:pg.evaluate("['bg','en','la','fam'].map(k=>fld(k).value)")
  def name(f,v):
    pg.click('#toggle');pg.fill('#f-'+f,v);pg.locator('#f-'+f).dispatch_event('change');r=vals();pg.click('#cancel');return r
  check('S2 a species new to the journal fills from the list', name('bg','Голям синигер'), ['Голям синигер','Great tit','Parus major','Синигери'])
  check('S3 BSPB\'s older Latin name still finds the bird (your typed name stays)', name('la','Carduelis chloris'), ['Зеленика','European greenfinch','Carduelis chloris','Чинки'])
  check('S4 the second Bulgarian name from BSPB works too', name('bg','Гарга'), ['Гарга','Western jackdaw','Corvus monedula','Вранови'])
  check('S5 your own records win; the list only fills what they lack', name('bg','Сврака'), ['Сврака','Magpie','Pica pica','Вранови'])
  pg.click('#toggle');pg.fill('#f-en','my own name');pg.fill('#f-bg','Кос');pg.locator('#f-bg').dispatch_event('change');r=vals();pg.click('#cancel')
  check('S6 a name you typed yourself is never overwritten', r, ['Кос','my own name','Turdus merula','Дроздове'])
  opts=pg.evaluate("[...document.querySelectorAll('#bgnames option')].map(o=>o.value)")
  check('S7 suggestions include the list and your names, once each', (('Горска зидарка' in opts),('Гарга' in opts),sum(1 for o in opts if o.lower()=='сврака')), (True,True,1))
  # counting: names the list knows belong together are one species; records stay as written
  d2=[R(id=11,bg='Боров синигер'),R(id=12,bg='Черен синигер',la='Periparus ater'),R(id=13,la='Carduelis chloris'),R(id=14,bg='Зеленика',la='Chloris chloris'),
      R(id=15,bg='Моя птица'),R(id=16,bg='Друга птица')]
  pg2=b.new_page();pg2.on('pageerror',lambda e:errs.append(str(e)))
  pg2.add_init_script("localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(d2,ensure_ascii=False)))
  pg2.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg2.wait_for_timeout(300)
  k=pg2.evaluate("OBS.map(key)")
  check('S8 a second BSPB name and the main one count as one species', k[0]==k[1], True)
  check('S9 BSPB\'s older Latin name and the current one count as one species', k[2]==k[3], True)
  check('S10 birds the list doesn\'t know stay separate', (k[4]!=k[5], len(set(k))), (True,4))
  check('S11 the records themselves are unchanged', pg2.evaluate("OBS.map(o=>[o.bg,o.la])"), [[r['bg'],r['la']] for r in d2])
  pg2.click('.tab[data-v="life"]');pg2.wait_for_timeout(200)
  check('S12 Моите видове shows 4 species, not 6', pg2.locator('.sp').count(), 4)
  check('S13 comparing with a friend links them too: „Гарга“ and „Чавка“', pg2.evaluate("(()=>{const kk=ufKeyer([{bg:'Гарга'},{bg:'Чавка'}]);return kk({bg:'Гарга'})===kk({bg:'Чавка'});})()"), True)
  check('S14 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
