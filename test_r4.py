import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-20',time='12:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8986;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
mine=[R(id=1,bg='Кос',la='Turdus merula',date='2026-10-12',place='Тюлбето'),R(id=2,bg='Сойка'),R(id=3,bg='Жълта стърчиопашка',la='Motacilla flava',date='2026-05-01')]
fr={'obs':[R(id=50,bg='Кос'),R(id=51,bg='Сврака',p=1),R(id=52,bg='Сива чапла',date='2026-11-01'),R(id=53,bg='Чайка sp.',la='Larus sp.')],'outs':[],
    'tg':{'turdus merula':{'bg':'Кос','la':'Turdus merula','en':'Common blackbird','t':1},'ciconia nigra':{'bg':'Черен щъркел','la':'Ciconia nigra','en':'Black stork','t':2}},
    'bdg':{'early:1':'2026-05-01','early:2':'2026-06-01','early:3':'2026-07-01','records:1':'2026-08-01'}}
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});ctx.route('https://**',lambda r:r.abort() if 'localhost' not in r.request.url else r.continue_())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');localStorage.setItem('bird-journal-badges',JSON.stringify({'early:1':'x'}));}"%json.dumps(json.dumps(mine,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  # the form
  pg.click('#toggle')
  box=lambda s:pg.evaluate(f"(()=>{{const r=document.querySelector('{s}').getBoundingClientRect();return [Math.round(r.width),Math.round(r.top)]}})()")
  w=[box('#f-bg')[0],box('#f-la')[0],box('#f-en')[0]]
  check('A1 the three names are equal, one per line on a phone', (len(set(w)),box('#f-bg')[1]<box('#f-la')[1]<box('#f-en')[1]), (1,True))
  check('A2 the count line sits right under the names: Брой, the kind menu, „♂♀ по пол и възраст“', (box('#f-count')[1]>box('#f-en')[1],abs(box('#f-count')[1]-box('#f-cqs')[1])<30,pg.inner_text('#f-astog')), (True,True,'♂♀ по пол и възраст ▸'))
  pg.click('#f-astog');pg.wait_for_timeout(80)
  check('A3 the sex-and-age counters open as a compact grid, two per row', pg.evaluate("(()=>{const r=[...document.querySelectorAll('#f-as .asr')].map(x=>Math.round(x.getBoundingClientRect().top));return new Set(r).size})()"), 3)
  # „sp.“ from any field
  for f,v in (('#f-bg','чайка sp.'),('#f-la','Larus sp.'),('#f-en','gull sp.')):
    for x in ('#f-bg','#f-la','#f-en'):pg.fill(x,'')
    pg.evaluate("for(const k of ['bg','la','en','fam'])fo[k]='',fc[k]=''")
    pg.fill(f,v);pg.locator(f).dispatch_event('change');pg.wait_for_timeout(60)
    got=[pg.input_value('#f-bg'),pg.input_value('#f-la'),pg.input_value('#f-en')]
    check(f'A4 „sp.“ typed in {f}: the other names fill in', [g if x!=f else '·' for x,g in zip(('#f-bg','#f-la','#f-en'),got)], [g if x!=f else '·' for x,g in zip(('#f-bg','#f-la','#f-en'),['Чайка sp.','Larus sp.','Larus sp.'])])
  pg.fill('#f-count','3');pg.click('#savebtn');pg.wait_for_timeout(200)
  pg.click('#cancel') if pg.is_visible('#cancel') else None
  check('A5 a „sp.“ record is a record, not a species: no card, no count, a small „sp.“ tag', (pg.evaluate("SURE().some(o=>/sp\\./.test(o.la))"),pg.inner_text('#n-sp'),pg.locator('#view .o .tag.sp').count(),pg.locator('#view .tag.nn').count()), (False,'3',1,0))
  # subspecies
  pg.click('#toggle');pg.fill('#f-la','Motacilla flava feldegg');pg.locator('#f-la').dispatch_event('change');pg.wait_for_timeout(80)
  check('A6 a third Latin word: the Bulgarian and English come from the species, the Latin keeps all three', (pg.input_value('#f-bg'),pg.input_value('#f-la')), ('Жълта стърчиопашка','Motacilla flava feldegg'))
  pg.click('#savebtn');pg.wait_for_timeout(200);pg.click('#cancel') if pg.is_visible('#cancel') else None
  check('A7 ...it counts towards its species (no new species) and shows „(feldegg)“', (pg.inner_text('#n-sp'),pg.evaluate("[...document.querySelectorAll('#view .o .ssp')].map(x=>x.textContent)")), ('3',['(feldegg)']))
  pg.evaluate("window.__f=[];offer=(n,c)=>__f.push([n,c]);0");pg.click('#acct');pg.click('#ebird');pg.click('#eb-ok');pg.wait_for_timeout(300)
  rows=[l.split(',') for l in pg.evaluate("__f[0][1]").strip().split('\n')]
  check('A8 the eBird export: „Larus sp.“ as genus + sp., the subspecies with all three words', (sorted([r[1]+' '+r[2] for r in rows if r[1] in ('Larus','Motacilla')])), ['Larus sp.','Motacilla flava','Motacilla flava feldegg'])   # May's plain record is its own list
  pg.click('[data-acctback]')
  # a friend's profile
  pg.evaluate("ME={id:'me',email:'i@t.bg'};MYNAME='Иван';FR={fol:[{id:'u2',name:'Петър',data:%s,updated_at:new Date().toISOString()}],fans:[]};tgAdd({bg:'Кос',la:'Turdus merula',en:'Common blackbird'});"%json.dumps(fr,ensure_ascii=False))
  pg.evaluate("BDG={'early:1':'2026-05-01'};fsel='u2';view='friends';render()");pg.wait_for_timeout(200)
  top=pg.evaluate("[...document.querySelectorAll('#view .cmp')].map(c=>[...c.querySelectorAll('div')].map(d=>d.querySelector('span').textContent+':'+d.querySelector('b').textContent))")
  check('A9 at the top: общи / само твои / само на Петър, then his наблюдения, видени, снимани, дни на терен', top,
    [['общи вида:1','само твои:2','само на Петър:2'],['наблюдения:3','видени:2','снимани:1','дни на терен:2']])   # his „sp.“ record is left out
  heads=pg.evaluate("[...document.querySelectorAll('#view .fsh span')].map(s=>s.textContent)")
  check('A10 five folding sections, all folded to start', (heads[1:],pg.evaluate("[...document.querySelectorAll('#view .fsb')].filter(b=>b.style.display!=='none').length")),
    (['Видовете на Петър · 3','Последни записи','Цели на Петър · 2','Значки на Петър · 2 · 1 златна'],0))
  pg.click('[data-ffold="tg"]');pg.wait_for_timeout(80)
  tg=pg.evaluate("[...document.querySelectorAll('[data-ffold=tg]+.fsb .ar')].map(a=>a.innerText.replace(/\\n+/g,' | '))")
  check('A11 his targets: not yet seen first; a shared one says „и ти го търсиш“ and where you last saw it; one he reached has ✓', tg,
    ['Черен щъркел','Кос ✓ | ✓ и ти го търсиш · ти си го виждал — последно 12 октомври 2026, Тюлбето · вече го е видял'])
  pg.click('[data-ffold="bd"]');pg.wait_for_timeout(80)
  check('A12 his badges, gold first, with your level beside each', pg.evaluate("[...document.querySelectorAll('[data-ffold=bd]+.fsb .ar')].map(a=>a.innerText.replace(/\\n+/g,' | '))"),
    ['Ранобудник — злато | ти: бронз','Неуморен — бронз | ти: още нямаш'])
  pg.evaluate("render()");pg.wait_for_timeout(80)
  check('A13 the open sections stay open (remembered)', pg.evaluate("[...document.querySelectorAll('#view .fsh')].filter(h=>h.getAttribute('aria-expanded')==='true').map(h=>h.dataset.ffold)"), ['tg','bd'])
  check('A14 his „sp.“ record isn\'t counted as a species in the comparison', 'Чайка sp.' in pg.inner_text('#view'), False)
  check('A15 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
