# „Какво видях?“ (2026-11-11.2): step-by-step identification. From the form: when/where → GBIF's birds within 30 km in
# this and the neighbouring months; size; up to 3 colours; up to 2 places; every step skippable. Ranking = local
# frequency × fit (mismatch lowers, never removes). „Това е“ fills the form. Also the Excel → data converter.
import json,subprocess,sys,time,datetime,urllib.parse,shutil,io
from PIL import Image
from playwright.sync_api import sync_playwright
T=datetime.date.today();m=T.month
MONTHS='month=12&month=1,2' if m==1 else 'month=11,12&month=1' if m==12 else f'month={m-1},{m+1}'
port=int(sys.argv[1]) if len(sys.argv)>1 else 9011;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
R=lambda **k:{**dict(id=0,date=T.isoformat(),time='08:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
NEAR={1001:('Turdus merula',400),1002:('Parus major',300),1003:('Erithacus rubecula',150),1004:('Pica pica',200),1005:('Garrulus glandarius',80)}
CALLS=[]
def gbif(route):
  u=urllib.parse.unquote(route.request.url);CALLS.append(u)
  if 'facet=speciesKey' in u: body={'facets':[{'field':'SPECIES_KEY','counts':[{'name':str(k),'count':n} for k,(la,n) in NEAR.items()]}]}
  elif 'limit=300' in u: body={'results':[{'speciesKey':k,'species':la} for k,(la,n) in NEAR.items()]}
  else: body={'count':1130,'facets':[]}
  route.fulfill(body=json.dumps(body),content_type='application/json')
def tile():
  bb=io.BytesIO();Image.new('RGB',(256,256),(214,222,200)).save(bb,'PNG');return bb.getvalue()
TILE=tile()
def session(b,geo=True,gps=None):
  kw=dict(viewport={'width':390,'height':844})
  if gps:kw.update(geolocation={'latitude':gps[0],'longitude':gps[1]},permissions=['geolocation'])
  ctx=b.new_context(**kw);ctx.route('https://api.gbif.org/**',gbif)
  ctx.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/'+('leaflet.css' if r.request.url.endswith('.css') else 'leaflet.js'),content_type='text/css' if r.request.url.endswith('.css') else 'application/javascript'))
  for pat in ['https://server.arcgisonline.com/**','https://*.basemaps.cartocdn.com/**','https://*.tile.openstreetmap.org/**','https://*.tile.opentopomap.org/**']:ctx.route(pat,lambda r:r.fulfill(body=TILE,content_type='image/png'))
  for pat in ['https://*.wikipedia.org/**','https://upload.wikimedia.org/**','https://commons.wikimedia.org/**','https://*.supabase.co/**']:ctx.route(pat,lambda r:r.abort())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  obs=[R(id=1,bg='Кос',la='Turdus merula',geo='42.62000,25.40000' if geo else None)]
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(obs,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);return ctx,pg,errs
def answer(pg,size=None,cols=(),wh=()):
  pg.click('#idBody [data-idnext]');pg.wait_for_timeout(100)
  if size:pg.click(f'#idBody [data-idsize="{size}"]');pg.wait_for_timeout(80);pg.click('#idBody [data-idnext]')
  else:pg.click('#idBody [data-idskip]')
  pg.wait_for_timeout(100)
  for c in cols:pg.click(f'#idBody [data-idcol="{c}"]')
  pg.click('#idBody [data-idnext]' if cols else '#idBody [data-idskip]');pg.wait_for_timeout(100)
  for w in wh:pg.click(f'#idBody [data-idwh="{w}"]')
  pg.click('#idBody [data-idnext]' if wh else '#idBody [data-idskip]');pg.wait_for_timeout(300)
top=lambda pg,n=5:pg.evaluate(f"[...document.querySelectorAll('#idBody .idr b')].slice(0,{n}).map(b=>b.textContent)")
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  ctx,pg,errs=session(b)
  pg.click('#toggle');pg.wait_for_timeout(200)
  check('I1 the form has „🔍 Не знам — какво видях?“ under the names', pg.inner_text('#f-idbtn'), '🔍 Не знам — какво видях?')
  pg.click('#f-idbtn');pg.wait_for_timeout(1200)
  check('I2 step 1: GBIF is asked for the birds within 30 km, in this and the neighbouring months', any('geoDistance=42.620,25.400,30km' in u and MONTHS in u and 'facet=speciesKey' in u for u in CALLS), True)
  check('I3 ...and says how many are around', pg.evaluate("document.getElementById('whatDlg').open") and '5 вида са намирани наоколо' in pg.inner_text('#idBody'), True)
  answer(pg,2,('k','y'),('D',))
  t5=top(pg)
  check('I4 „кос“, black and yellow, in trees — here and now the кос comes first', t5[0], 'Кос')
  check('I5 ...and the авлига, which matches those traits just as well but isn’t around this season, sinks — still in the list, not removed', ('Авлига' in t5,'Авлига' in pg.evaluate("[...document.querySelectorAll('#idBody .idr b')].map(b=>b.textContent)") or pg.locator('#idBody [data-idmore]').count()>0), (False,True))
  check('I6 each result says why: size, colours (♀ too), where, how common here now', pg.inner_text('#idBody .idr small'), 'кос · черно, жълто (♀ кафяво) · на земята, в дървета / храсти · честа тук сега')
  check('I7 ...with its photo and sounds in place', (pg.locator('#idBody .idr .refsm[data-ref]').count()>=12,pg.locator('#idBody .idr .xcw[data-xc]').count()>=12), (True,True))
  n0=pg.locator('#idBody .idr').count();pg.click('#idBody [data-idmore]');pg.wait_for_timeout(200)
  check('I8 „Покажи още“ shows the next ones', (n0,pg.locator('#idBody .idr').count()), (12,24))
  pg.click('#idBody [data-idpick="Turdus merula"]');pg.wait_for_timeout(300)
  check('I9 „Това е“ closes it and fills the form: Bulgarian, Latin and English', (pg.evaluate("document.getElementById('whatDlg').open"),pg.input_value('#f-bg'),pg.input_value('#f-la'),bool(pg.input_value('#f-en'))), (False,'Кос','Turdus merula',True))
  pg.click('#f-idbtn');pg.wait_for_timeout(600);answer(pg)
  check('I10 skipping every step: the most common birds here and now', top(pg,3), ['Кос','Голям синигер','Сврака'])
  pg.click('#idBody [data-idback]');pg.wait_for_timeout(100)
  check('I11 „Промени отговорите“ goes back to the size step', pg.inner_text('#idBody h3'), 'Колко голяма?')
  check('I12 no page errors', errs, []);ctx.close()
  ctx,pg,errs=session(b,geo=False);pg.click('#toggle');pg.wait_for_timeout(200);pg.click('#f-idbtn');pg.wait_for_timeout(400)
  check('I13 without a position it says so, and ranks by the traits alone', 'Без местоположение' in pg.inner_text('#idBody'), True)
  answer(pg,2,('k','y'),('D',))
  check('I14 ...then the авлига and the кос fit equally — which is exactly why step 1 matters', sorted(top(pg,2)), ['Авлига','Кос'])
  check('I15 no page errors (without a position)', errs, []);ctx.close()
  # step 1 can be changed; the pictures; size waits for „Напред“
  ctx,pg,errs=session(b,gps=(42.70,25.50));pg.click('#toggle');pg.wait_for_timeout(200);pg.click('#f-idbtn');pg.wait_for_timeout(700)
  CALLS.clear();pg.fill('#id-date','2026-06-15');pg.dispatch_event('#id-date','change');pg.wait_for_timeout(700)
  check('J1 changing the date asks GBIF again for that season (June → May–July)', any('month=5,7' in u and 'facet=speciesKey' in u for u in CALLS), True)
  CALLS.clear();pg.click('#idBody [data-idgps]');pg.wait_for_timeout(900)
  check('J2 „📍 Тук (GPS)“ takes the phone\'s position and asks GBIF there', (any('geoDistance=42.700,25.500,30km' in u for u in CALLS),'по GPS' in pg.inner_text('#idBody .idrow0')), (True,True))
  CALLS.clear();pg.click('#idBody [data-idmap]');pg.wait_for_timeout(1200)
  box=pg.locator('#pickMap').bounding_box();pg.mouse.click(box['x']+box['width']*0.7,box['y']+box['height']*0.4);pg.wait_for_timeout(300);pg.click('#pickOk');pg.wait_for_timeout(900)
  check('J3 „🗺 На картата“: the record\'s map opens on top, the chosen point comes back to „Какво видях?“ (and GBIF is asked there) — the record\'s own place is untouched',
        (pg.evaluate("document.getElementById('pickDlg').open"),pg.evaluate("document.getElementById('whatDlg').open"),'избрано на картата' in pg.inner_text('#idBody .idrow0'),any('geoDistance=' in u and '42.700,25.500' not in u for u in CALLS),pg.input_value('#f-geo') if pg.locator('#f-geo').count() else ''), (False,True,True,True,''))
  pg.click('#idBody [data-idnopos]');pg.wait_for_timeout(300)
  check('J4 „Без място“: traits only, and it says so', ('без място' in pg.inner_text('#idBody .idrow0'),'Без местоположение' in pg.inner_text('#idBody')), (True,True))
  pg.click('#idBody [data-idnext]');pg.wait_for_timeout(150);pg.click('#idBody [data-idsize="3"]');pg.wait_for_timeout(200)
  check('J5 choosing a size doesn\'t jump ahead — only „Напред“ does', (pg.inner_text('#idBody h3'),pg.get_attribute('#idBody [data-idsize="3"]','aria-pressed')), ('Колко голяма?','true'))
  hs=pg.evaluate("[...document.querySelectorAll('#idBody .idszb svg')].map(s=>Math.round(s.getBoundingClientRect().height))")
  check('J6 the five sizes show the reference birds\' silhouettes, growing from врабче to гъска/чапла', (len(hs),hs==sorted(hs) and hs[0]<hs[-1],pg.evaluate("[...document.querySelectorAll('#idBody .idszb small')].map(x=>x.textContent)")), (5,True,['до 17 см','18–27 см','28–38 см','39–60 см','над 60 см']))
  pg.click('#idBody [data-idnext]');pg.wait_for_timeout(150);pg.click('#idBody [data-idcol="y"]');pg.click('#idBody [data-idcol="k"]');pg.wait_for_timeout(150)
  check('J7 colours are filled circles in muted tones; the chosen ones show their order', (pg.locator('#idBody .idcolb .idsw').count(),pg.evaluate("getComputedStyle(document.querySelector('#idBody [data-idcol=\"y\"] .idsw')).backgroundColor"),pg.inner_text('#idBody [data-idcol="y"] small'),pg.inner_text('#idBody [data-idcol="k"] small')), (11,'rgb(210, 172, 62)','1','2'))
  pg.click('#idBody [data-idnext]');pg.wait_for_timeout(150)
  check('J8 each place has its own small sketch', (pg.locator('#idBody .idwhb svg.idwi').count(),pg.evaluate("[...document.querySelectorAll('#idBody .idwhb span')].map(x=>x.textContent)")), (7,['на вода','летеше','на земята','в дървета / храсти','на жица / ограда','в тръстика','по скали']))
  check('J9 no page errors (changing place and date)', errs, []);ctx.close()
  b.close()
finally: srv.terminate()
# the converter: refuses unknown words, writes when clean
from openpyxl import load_workbook
src='/home/claude/belezi/pera-belezi-za-pregled.xlsx';bad='/tmp/belezi-bad.xlsx';shutil.copy(src,bad)
wb=load_workbook(bad);ws=wb['Белези'];ws['G2']='ръжд, кафяво';ws['E3']='2–4';wb.save(bad)
r=subprocess.run([sys.executable,'belezi_to_js.py',bad,'/tmp/kv-test.html'],capture_output=True,text=True)
check('C1 the converter refuses a typo and a non-neighbouring size, naming the rows — nothing is written', (r.returncode,'ред 2 (Aythya nyroca): непознат цвят „ръжд“' in r.stdout,'ред 3 (Tadorna tadorna): размер „2–4“' in r.stdout), (1,True,True))
open('/tmp/kv-test.html','w',encoding='utf-8').write('x\n// <KV>\nconst KV={};\n// </KV>\ny')
r=subprocess.run([sys.executable,'belezi_to_js.py',src,'/tmp/kv-test.html'],capture_output=True,text=True);t=open('/tmp/kv-test.html',encoding='utf-8').read()
check('C2 ...and with a clean file writes all 340, colours in your order („Сойка“: бежово, синьо, черно, бяло)', (r.stdout.strip(),'"Garrulus glandarius":"3|eskw||D"' in t), ('340 вида записани.',True))
print('FAILURES:',fails)
