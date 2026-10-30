import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
from urllib.parse import unquote
R=lambda **k:{**dict(id=0,date='2026-10-27',time='12:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8980;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,bg='Кос'),R(id=2,bg='Розово фламинго',la='Phoenicopterus roseus',en='Greater Flamingo'),R(id=3,bg='Странна птица')]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  ctx.route('https://**',lambda r:r.fulfill(body='ok') if 'localhost' not in r.request.url else r.continue_())
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);pg.click('.tab[data-v="life"]');pg.wait_for_timeout(250)
  L=lambda sel:pg.evaluate(f"Object.fromEntries([...document.querySelectorAll('{sel} .idl a')].map(a=>[a.textContent.replace(' ↗',''),decodeURIComponent(a.href)]))")
  kos=pg.evaluate("(()=>{const c=[...document.querySelectorAll('.sp')].find(c=>c.querySelector('.nm').textContent==='Кос');return Object.fromEntries([...c.querySelectorAll('.idl a')].map(a=>[a.textContent.replace(' ↗',''),decodeURIComponent(a.href)]))})()")
  check('I1 a bird card links to БДЗП, its voices on xeno-canto and Wikipedia', kos,
    {'БДЗП':'https://www.google.com/search?q=site:bspb.org Кос','Гласове':'https://xeno-canto.org/species/Turdus-merula','Уикипедия':'https://bg.wikipedia.org/w/index.php?search=Turdus merula&go=Go'})
  fl=pg.evaluate("(()=>{const c=[...document.querySelectorAll('.sp')].find(c=>c.querySelector('.nm').textContent==='Розово фламинго');return [...c.querySelectorAll('.idl a')].map(a=>decodeURIComponent(a.href))})()")
  check('I2 a bird added by the user works too, by its Latin name', fl[1:], ['https://xeno-canto.org/species/Phoenicopterus-roseus','https://bg.wikipedia.org/w/index.php?search=Phoenicopterus roseus&go=Go'])
  st=pg.evaluate("(()=>{const c=[...document.querySelectorAll('.sp')].find(c=>c.querySelector('.nm').textContent==='Странна птица');return [...c.querySelectorAll('.idl a')].map(a=>decodeURIComponent(a.href))})()")
  check('I3 without a Latin name it searches by the name', st[1:], ['https://xeno-canto.org/explore?query=Странна птица','https://bg.wikipedia.org/w/index.php?search=Странна птица&go=Go'])
  with ctx.expect_page() as np_:pg.locator('.sp .idl a').first.click()
  np_.value.close();pg.wait_for_timeout(150)
  check('I4 a link opens in a new window and doesn\'t open the bird\'s page', (pg.evaluate("spSel"),pg.evaluate("view")), (None,'life'))
  pg.locator('.sp .nm',has_text='Кос').first.click();pg.wait_for_timeout(200)
  check('I5 the bird\'s own page has the links too', list(L('.spd').keys()), ['БДЗП','Гласове','Уикипедия'])
  pg.click('.tab[data-v="goals"]');pg.fill('#tg-in','Черен щъркел');pg.click('#tg-add');pg.wait_for_timeout(200)
  check('I6 so do the Цели cards', list(L('.tgc').keys()), ['БДЗП','Гласове','Уикипедия'])
  pg.click('.tab[data-v="log"]');pg.click('#toggle');pg.fill('#f-bg','Горска дърволазка');pg.locator('#f-bg').dispatch_event('change')
  check('I7 the recording form shows nothing extra until „не съм сигурен“', pg.is_visible('#f-cmp'), False)
  pg.click('#f-unsure');pg.click('[data-alts="Градинска дърволазка"]');pg.wait_for_timeout(100)
  check('I8 ...then just one small „сравни ↗“ link', (pg.is_visible('#f-cmp'),pg.inner_text('#f-cmp')), (True,'сравни ↗'))
  pg.click('#f-cmp');pg.wait_for_timeout(150)
  rows=pg.evaluate("[...document.querySelectorAll('#cmp-list .cmpr')].map(r=>[r.querySelector('b').textContent,r.querySelectorAll('.idl a').length])")
  check('I9 „сравни“ lists the bird and its alternatives, each with its links', rows, [['Горска дърволазка',3],['Градинска дърволазка',3]])
  pg.click('#cmp-close')
  check('I10 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
