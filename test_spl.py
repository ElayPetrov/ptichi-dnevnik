# The species list after adding the official BUNARCO list (2026-11-02.13): 268 BSPB + 145 official = 413.
import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-20',time='08:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8994;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,bg='Розово фламинго',la='Phoenicopterus roseus',en='Greater Flamingo'),R(id=2,bg='Кос',la='Turdus merula'),R(id=3,bg='Брадат лешояд')]
spx=[{'bg':'Розово фламинго','la':'Phoenicopterus roseus','en':'Greater Flamingo'},{'bg':'Измислена птица','la':'Avis inventa','en':'Invented bird'}]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});ctx.route('https://**',lambda r:r.abort() if 'localhost' not in r.request.url else r.continue_())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-species-extra',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');sessionStorage.setItem('s','1')}"%(json.dumps(json.dumps(data,ensure_ascii=False)),json.dumps(json.dumps(spx,ensure_ascii=False))))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(500)
  st=pg.evaluate("""(()=>{const n=x=>nrm(x),la=new Set(SPL.map(e=>n(e[1]))),bg=SPL.map(e=>n(e[0])),mains=new Set(bg);
    const altClash=SPL.flatMap(e=>altsOf(e).filter(a=>mains.has(n(a))&&n(a)!==n(e[0])));
    return [SPL.length,la.size,new Set(bg).size,altClash,SPL.filter(e=>e[6]).length,SPL.slice(268).every(e=>e[0]&&e[1]&&e[2]&&FAMS[e[3]])]})()""")
  check('S1 413 species: every Latin and every Bulgarian name unique, no alternative is another bird’s name, 73 marked rare, all complete', st, [413,413,413,[],73,True])
  look=lambda f,v:pg.evaluate(f"(c=>c&&[c.bg,c.la,c.en,c.fam])(listFind('{f}','{v}'))")
  check('S2 an official new name fills in Latin and English (eBird’s)', look('bg','Северен гмуркач'), ['Северен гмуркач','Gavia immer','Great northern diver','Гмурци и корморани'])   # the list's English name
  check('S3 ...and the Latin finds the official Bulgarian name', look('la','Larus argentatus')[0], 'Сребриста чайка')
  check('S4 an alternative name finds its bird („Глухарче“ → Малка бекасина)', look('bg','Глухарче')[:2], ['Малка бекасина','Lymnocryptes minimus'])
  check('S5 the 2009 Latin name still finds it (Anas falcata → Mareca falcata)', look('la','Anas falcata')[:2], ['Сърпокрила патица','Mareca falcata'])
  check('S6 the snipe exception: „Средна бекасина“ stays the common snipe', look('bg','Средна бекасина')[1], 'Gallinago gallinago')
  check('S7 the group’s own species that the official list has give way; others stay', pg.evaluate("spxAll().map(x=>x.la)"), ['Avis inventa'])
  pg.wait_for_timeout(2800)
  check('S8 ...and the app says so once', ('Розово фламинго' in pg.evaluate("document.getElementById('yay').innerText"),pg.evaluate("localStorage.getItem('bird-journal-spx-merged-1')")), (True,'true'))
  check('S9 their records keep counting as that species (now with the official group)', (pg.evaluate("listFind('bg','Розово фламинго').la"),pg.evaluate("grp(OBS.find(o=>o.id===1))"),pg.evaluate("Object.values(speciesMap()).filter(r=>r.bg==='Розово фламинго').length")), ('Phoenicopterus roseus','Чапли и щъркели',1))
  pg.evaluate("yayHide&&yayHide()");pg.click('.tab[data-v="life"]');pg.wait_for_timeout(150)
  pg.locator('.sp .nm',has_text='Розово фламинго').first.click();pg.wait_for_timeout(150)
  r1=pg.locator('.rareline').count();pg.click('[data-spback]');pg.locator('.sp .nm',has_text='Кос').first.click();pg.wait_for_timeout(150);r2=pg.locator('.rareline').count();pg.click('[data-spback]')
  check('S10 a rare bird’s card says „Рядък (случаен) вид за България“; a common one doesn’t', (r1,r2), (1,0))
  check('S11 the group badges keep today’s totals, and a new bird of prey counts towards Грабливи', (pg.evaluate("BDEF.find(d=>d.id==='g:Грабливи').g"),pg.evaluate("BDEF.find(d=>d.id==='g:Грабливи').v(SURE())")), ([12,20,35],1))
  links=pg.evaluate("(()=>{const d=document.createElement('div');d.innerHTML=idLinks({bg:'Сребриста чайка'});return [...d.querySelectorAll('a')].map(a=>a.href)})()")
  check('S12 a new species links to BSPB’s guide (no page of its own yet), xeno-canto and Wikipedia by its Latin name', (links[0].startswith('https://bspb.org/'),'Larus-argentatus' in links[1]), (True,True))
  pg.click('#toggle');pg.fill('#f-bg','Северен гмуркъч');pg.wait_for_timeout(900)
  check('S13 the typo check knows the new names too', pg.inner_text('#f-typo'), 'Имаше ли предвид Северен гмуркач?')
  check('S14 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
