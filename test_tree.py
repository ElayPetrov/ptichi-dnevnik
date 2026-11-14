# „🌳 Дървото“ (2026-11-14.1): the tree of life of Bulgaria's birds, like OneZoom — a leaf per species, orders/families
# as branches (AVONET), your species lit, names by zoom level; chapters with the three names, the path, your records,
# Bulgarian then English Wikipedia text with credits; back; „Покажи на дървото“; search. Wikipedia is a stand-in here.
import json,subprocess,sys,time,datetime,urllib.parse
from playwright.sync_api import sync_playwright
T=datetime.date.today().isoformat();port=int(sys.argv[1]) if len(sys.argv)>1 else 9012;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
BG={'Passeriformes':'Врабчоподобни','Anseriformes':'Гъскоподобни','Turdidae':'Дроздови','Corvidae':'Вранови','Paridae':'Синигерови'}
WIKI_DOWN=[False]
def en(route):
  if WIKI_DOWN[0]:return route.abort()
  q=urllib.parse.parse_qs(urllib.parse.urlparse(route.request.url).query);titles=q.get('titles',[''])[0].split('|')
  if 'extracts' in q.get('prop',[''])[0]:
    t=titles[0]
    if t=='Turdus merula':pg={'title':'Common blackbird','extract':'The common blackbird is a true thrush.\n\n== Description ==\nThe adult male is all black.\n\n== References ==\nSome ref.','langlinks':[{'lang':'bg','*':'Кос (птица)'}]}
    elif t=='Turdidae':pg={'title':'Thrush (bird)','extract':'Thrushes are a family of passerine birds.','langlinks':[{'lang':'bg','*':'Дроздови'}]}
    else:pg={'title':t,'missing':''}
    return route.fulfill(body=json.dumps({'query':{'pages':{'1':pg}}}),content_type='application/json')
  pages={str(i):{'title':t,**({'langlinks':[{'lang':'bg','*':BG[t]}]} if t in BG else {})} for i,t in enumerate(titles)}
  route.fulfill(body=json.dumps({'query':{'pages':pages}}),content_type='application/json')
def bg(route):
  if WIKI_DOWN[0]:return route.abort()
  q=urllib.parse.parse_qs(urllib.parse.urlparse(route.request.url).query);t=q.get('titles',[''])[0]
  X={'Кос (птица)':'Косът е птица от семейство Дроздови.\n\n== Разпространение ==\nСреща се в цяла България.\n\n== Източници ==\nИзточник.','Дроздови':'Дроздовите са семейство птици.'}
  pg={'title':t,'extract':X[t]} if t in X else {'title':t,'missing':''}
  route.fulfill(body=json.dumps({'query':{'pages':{'1':pg}}}),content_type='application/json')
R=lambda **k:{**dict(id=0,date=T,time='08:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
OBS=[R(id=1,bg='Кос',la='Turdus merula'),R(id=2,time='09:00',bg='Кос',la='Turdus merula'),R(id=3,bg='Голям синигер',la='Parus major'),R(id=4,bg='Сврака',la='Pica pica'),R(id=5,bg='Сива чапла',la='Ardea cinerea',u=1)]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844})
  ctx.route('https://en.wikipedia.org/w/api.php**',en);ctx.route('https://bg.wikipedia.org/w/api.php**',bg)
  for pat in ['https://en.wikipedia.org/api/**','https://commons.wikimedia.org/**','https://upload.wikimedia.org/**','https://*.supabase.co/**','https://api.gbif.org/**']:ctx.route(pat,lambda r:r.abort())
  ctx.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/'+('leaflet.css' if r.request.url.endswith('.css') else 'leaflet.js'),content_type='text/css' if r.request.url.endswith('.css') else 'application/javascript'))
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(OBS,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);pg.click('.tab[data-v="life"]')
  check('T1 „Видове“ has a third sub-tab, „🌳 Дървото“', pg.evaluate("[...document.querySelectorAll('[data-lifeall]')].map(b=>b.textContent)")[2], '🌳 Дървото')
  pg.click('[data-lifeall="2"]');pg.wait_for_timeout(1500)
  lv=lambda f:pg.evaluate(f"Object.values(TRM._layers).filter(l=>l.options&&l.options.leaf{f}).length")
  check('T2 a leaf for every species in Перá’s list — your sure species lit (the „?“ one isn’t)', (lv(''),lv('&&l.options.seen')), (413,3))
  check('T3 order names in Bulgarian from Wikipedia; Latin where Wikipedia has none', ('Врабчоподобни' in pg.evaluate("[...document.querySelectorAll('.tlo')].map(x=>x.textContent)"),pg.evaluate("[...document.querySelectorAll('.tlo')].some(x=>/formes$/.test(x.textContent))")), (True,True))
  n0=pg.locator('.tls').count();pg.evaluate("TRM.setZoom(TRM._z0+2.5,{animate:false}),0");pg.wait_for_timeout(500)
  check('T4 species names appear only when zoomed in', (n0,pg.locator('.tls').count()>0), (0,True))
  pg.evaluate("TRM.setZoom(TRM._z0,{animate:false}),0");pg.wait_for_timeout(300)
  pg.evaluate("tdOpen('sp','Turdus merula')");pg.wait_for_timeout(800)
  nm=pg.evaluate("[...document.querySelectorAll('#tdBody .tdnames > *')].map(x=>x.textContent)")
  check('T5 a leaf’s chapter: Bulgarian, Latin and English names', (nm[0],nm[1],bool(nm[2])), ('Кос','Turdus merula',True))
  path=pg.evaluate("[...document.querySelectorAll('#tdBody .tdpath button')].map(x=>x.textContent)")
  check('T6 ...its place on the tree, from the top: Птици › … › Врабчоподобни › … › Дроздови', (path[0],'Врабчоподобни' in path,path[-1]), ('Aves',True,'Дроздови'))
  check('T7 ...and your records: twice, the „?“ record not counted', pg.inner_text('#tdBody .note2'), 'Видял си го 2 пъти · последно '+pg.evaluate("human(today())"))
  w=pg.inner_text('#tdwp')
  check('T8 the Bulgarian Wikipedia article first, its sections kept, „Източници“ left out', ('Косът е птица от семейство Дроздови.' in w,'Разпространение' in w,'Източник.' not in w), (True,True,True))
  check('T9 ...credited, with links to the article and the licence', pg.evaluate("[...document.querySelectorAll('#tdwp > .tdcr a')].map(a=>a.href)"), ['https://bg.wikipedia.org/wiki/%D0%9A%D0%BE%D1%81_(%D0%BF%D1%82%D0%B8%D1%86%D0%B0)','https://creativecommons.org/licenses/by-sa/4.0/deed.bg'])
  check('T10 the English article under „По-подробно на английски“, folded, without its references, credited', (pg.evaluate("document.querySelector('#tdwp details.tden').open"),pg.evaluate("document.querySelector('#tdwp details.tden').textContent.includes('The adult male is all black.')"),pg.evaluate("document.querySelector('#tdwp details.tden').textContent.includes('Some ref.')"),pg.evaluate("document.querySelector('#tdwp details.tden .tdcr a').href")), (False,True,False,'https://en.wikipedia.org/wiki/Common_blackbird'))
  pg.click('#tdBody .tdpath button:last-child');pg.wait_for_timeout(800)
  check('T11 a branch’s chapter (the family): its species in Bulgaria and how many you’ve seen, ✓ on yours', (pg.inner_text('#tdTitle'),pg.inner_text('#tdBody > .note2'),pg.evaluate("[...document.querySelectorAll('#tdBody .tdkids .chip.got')].map(c=>c.textContent)")), ('Дроздови','В България: 7 вида · видял си 1.',['✓ Кос']))
  check('T12 ...with the family’s Wikipedia text', 'Дроздовите са семейство птици.' in pg.inner_text('#tdwp'), True)
  pg.click('#treeDlg .tdback');pg.wait_for_timeout(500)
  check('T13 „‹“ goes back to the previous chapter', pg.inner_text('#tdTitle'), 'Кос')
  z0=pg.evaluate("TRM.getZoom()");pg.click('#tdBody [data-tdshow]');pg.wait_for_timeout(1300)
  check('T14 „Покажи на дървото“ closes the chapter and flies to the leaf', (pg.evaluate("document.getElementById('treeDlg').open"),pg.evaluate("TRM.getZoom()")>z0), (False,True))
  pg.fill('#tr-q','Сврака');pg.dispatch_event('#tr-q','change');pg.wait_for_timeout(1600)
  check('T15 search: a species flies into view and its chapter opens', (pg.evaluate("document.getElementById('treeDlg').open"),pg.inner_text('#tdTitle')), (True,'Сврака'))
  pg.click('#treeDlg [data-tdclose]');WIKI_DOWN[0]=True;pg.evaluate("WPM.clear();localStorage.removeItem('bird-journal-wp');tdOpen('sp','Parus major')");pg.wait_for_timeout(900)
  check('T16 if Wikipedia doesn’t answer, it says so', pg.inner_text('#tdwp'), 'Уикипедия не отговаря — опитай пак след малко.')
  check('T17 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
