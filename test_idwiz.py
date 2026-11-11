# „Какво видях?“ (2026-11-11.2): step-by-step identification. From the form: when/where → GBIF's birds within 30 km in
# this and the neighbouring months; size; up to 3 colours; up to 2 places; every step skippable. Ranking = local
# frequency × fit (mismatch lowers, never removes). „Това е“ fills the form. Also the Excel → data converter.
import json,subprocess,sys,time,datetime,urllib.parse,shutil
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
def session(b,geo=True):
  ctx=b.new_context(viewport={'width':390,'height':844});ctx.route('https://api.gbif.org/**',gbif)
  for pat in ['https://*.wikipedia.org/**','https://upload.wikimedia.org/**','https://commons.wikimedia.org/**','https://*.supabase.co/**']:ctx.route(pat,lambda r:r.abort())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  obs=[R(id=1,bg='Кос',la='Turdus merula',geo='42.62000,25.40000' if geo else None)]
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(obs,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);return ctx,pg,errs
def answer(pg,size=None,cols=(),wh=()):
  pg.click('#idBody [data-idnext]');pg.wait_for_timeout(100)
  if size:pg.click(f'#idBody [data-idsize="{size}"]')
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
