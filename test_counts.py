import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-11-01',time='12:00',place='Копринка',count='',bg='Кос',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo='42.62,25.39',photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8985;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
TILE=bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'+'1f15c489'+'0000000d49444154789c6360f8cf000000030101007a2d0a1b0000000049454e44ae426082')
data=[R(id=1,count='~40',bg='Зеленоглава патица'),R(id=2,count='20+',bg='Лиска'),R(id=3,count='1',beh=['мъжки'],bg='Кос')]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
tiles=[]
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844})
  ctx.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/leaflet.js',content_type='application/javascript'))
  def tile(r):tiles.append(r.request.url);r.fulfill(body=TILE,content_type='image/png')
  ctx.route('https://server.arcgisonline.com/**',tile);ctx.route('https://tile.openstreetmap.org/**',tile)
  ctx.route('https://*.wikipedia.org/**',lambda r:r.abort());ctx.route('https://szyituwdlbwpqkfuklxq.supabase.co/**',lambda r:r.abort())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');}"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  pg.click('#toggle')
  check('C1 the form: a small „точно / поне / около“ menu showing „точно“, and „по пол и възраст“ folded away', (pg.evaluate("[...document.querySelectorAll('#f-cqs option')].map(o=>o.textContent)"),pg.input_value('#f-cqs'),pg.is_visible('#f-as')),
    (['точно','поне','около'],'exact',False))
  pg.fill('#f-count','40');pg.fill('#f-bg','Голям корморан');pg.select_option('#f-cqs','est');pg.click('#savebtn');pg.wait_for_timeout(150)
  pg.click('#toggle') if not pg.is_visible('#f-count') else None
  pg.fill('#f-count','15');pg.fill('#f-bg','Сива чапла');pg.select_option('#f-cqs','min');pg.click('#savebtn');pg.wait_for_timeout(150)
  pg.click('#toggle') if not pg.is_visible('#f-count') else None
  pg.fill('#f-count','12');pg.fill('#f-bg','Голям синигер');pg.click('#f-astog')
  for k,n in (('m',3),('f',2),('juv',1)):
    for _ in range(n):pg.click(f'[data-asp="{k}"]')
  check('C2 the sex-and-age counters fill in, and the fold shows what\'s set', pg.inner_text('#f-astog'), '♂♀ 3♂ 2♀ · млади 1 ▾')
  pg.click('#savebtn');pg.wait_for_timeout(150)
  recs=pg.evaluate("Object.fromEntries(OBS.filter(o=>o.id>9).map(o=>[o.bg,[o.count,o.cq||'',o.as||null]]))")
  check('C3 saved: the number, its kind, and the parts', recs, {'Голям корморан':['40','est',None],'Сива чапла':['15','min',None],'Голям синигер':['12','',{'m':3,'f':2,'juv':1}]})
  pg.click('#cancel') if pg.is_visible('#cancel') else None
  shown=pg.evaluate("Object.fromEntries([...document.querySelectorAll('#view .o .nm')].map(n=>{const t=n.innerText.split(' · ');return [t[0],t.slice(1).join(' · ')]}))")
  check('C4 Дневник shows „около 40“, „поне 15“, „12 · 3♂ 2♀ · млади 1“; old „~40“ and „20+“ unchanged', [shown.get('Голям корморан'),shown.get('Сива чапла'),shown.get('Голям синигер'),shown.get('Зеленоглава патица'),shown.get('Лиска')],
    ['около 40','поне 15','12 · 3♂ 2♀ · млади 1','~40','20+'])
  check('C5 old free-text counts read as estimate / minimum, and the numbers badges use are unchanged', pg.evaluate("[cqOf({count:'~40'}),cqOf({count:'20+'}),cqOf({count:'около 7'}),cqOf({count:'20-30'}),cntNum('~40'),cntNum('20+')]"), ['est','min','est','est',40,20])
  pg.click('#toggle');pg.fill('#f-count','2');pg.fill('#f-bg','Сойка');pg.click('#f-astog')
  for _ in range(3):pg.click('[data-asp="m"]')
  check('C6 the parts never exceed the total', (pg.evaluate("fAS.m"),'не може да са повече' in pg.inner_text('#f-asmsg')), (2,True))
  pg.fill('#f-count','');pg.click('[data-asp="f"]');pg.click('#savebtn');pg.wait_for_timeout(150)
  check('C7 with no total, the total comes from the parts', pg.evaluate("[OBS.find(o=>o.bg==='Сойка').count,OBS.find(o=>o.bg==='Сойка').as]"), ['3',{'m':2,'f':1}])
  pg.click('#cancel') if pg.is_visible('#cancel') else None
  pg.evaluate("for(const d of new Set(OBS.map(o=>o.date)))setDay(d,true);render()")   # yesterday's day is folded
  pg.click('[data-ed="3"]');pg.wait_for_timeout(150)
  chips=pg.evaluate("[...document.querySelectorAll('#beh .bh')].map(b=>b.dataset.b)")
  check('C8 an old record keeps its „мъжки“ tag when edited', ('мъжки' in chips,pg.evaluate("document.querySelector('#beh [data-b=\"мъжки\"]').classList.contains('on')")), (True,True))
  pg.click('#cancel');pg.click('#toggle');pg.wait_for_timeout(100)
  chips=pg.evaluate("[...document.querySelectorAll('#beh .bh')].map(b=>b.dataset.b)")
  check('C9 a new record no longer offers „мъжки“, „женски“, „млада“ as tags', [t for t in ('мъжки','женски','млада') if t in chips], [])
  pg.click('#cancel')
  sg=[o for o in pg.evaluate("OBS") if o['bg']=='Голям синигер'][0]['id']
  pg.click(f'[data-ed="{sg}"]');pg.wait_for_timeout(150)
  check('C10 editing loads the kind and the parts back into the form', (pg.evaluate("fCQ"),pg.evaluate("fAS"),pg.is_visible('#f-as')), ('exact',{'m':3,'f':2,'juv':1},True))
  pg.click('#cancel')
  pg.evaluate("window.__f=[];offer=(n,c)=>__f.push([n,c]);0");pg.click('#acct');pg.click('#exp');pg.wait_for_timeout(150)
  csv=pg.evaluate("__f[0][1]").split('\n')
  row=[l for l in csv if 'Голям синигер' in l][0]
  check('C11 Експорт CSV gets „Вид брой“ and „Пол и възраст“ after „Брой“', ('Брой,Вид брой,Пол и възраст,Гнездене,Чух' in csv[0],'"около"' in [l for l in csv if 'Голям корморан' in l][0],'"3♂ 2♀ · млади 1"' in row), (True,True,True))
  pg.evaluate("__f=[]");pg.click('#ebird');pg.click('#eb-ok');pg.wait_for_timeout(300)
  eb=[l for l in pg.evaluate("__f[0][1]").split('\n') if 'Parus' in l][0].split(',')
  check('C12 the eBird export: the number, and sex and age in the species comment', (eb[3],'3♂ 2♀ · млади 1' in eb[4]), ('12',True))
  pg.click('[data-acctback]')
  check('C13 Карта offers four styles; „Улици“ is OpenStreetMap now (no key)', (pg.evaluate("Object.values(TILES).map(t=>t.name)"),pg.evaluate("TILES.street.url")), (['Сателит','Сателит + надписи','Топо','Улици'],'https://tile.openstreetmap.org/{z}/{x}/{y}.png'))
  pg.click('#toggle');pg.click('#geoMap');pg.wait_for_function("pickM&&pickM.__tls&&pickM.__tls.length",timeout=8000);pg.wait_for_timeout(500)
  check('C14 choosing a place: „Сателит + надписи“ by default — the photo plus roads and names on top', (pg.evaluate("pickKey"),pg.evaluate("pickM.__tls.length"),any('World_Transportation' in u for u in tiles),any('World_Boundaries_and_Places' in u for u in tiles)), ('hyb',3,True,True))
  pg.click('[data-ptk="street"]');pg.wait_for_timeout(500)
  check('C15 its own style switch, remembered apart from Карта', (pg.evaluate("localStorage.getItem('bird-journal-picktiles')"),pg.evaluate("tileKey"),any('tile.openstreetmap.org' in u for u in tiles)), ('street','sat',True))
  check('C16 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
