import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
Y=str(datetime.date.today().year)
R=lambda **k:{**dict(id=0,date=Y+'-05-10',time='08:00',place='',count='',bg='Кос',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8993;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,place='Казанлък',geo='42.61940,25.39560',bc=14),R(id=2,bg='Сойка',place='Казанлък',geo='42.61900,25.39000',date=Y+'-05-11'),
      R(id=3,bg='Кос',place='Казанлък',geo='42.61940,25.39560',date='2025-05-01',bc=4),R(id=4,bg='Авлига',place='Бузлуджа',geo='42.73600,25.39300'),
      R(id=5,bg='Сврака',place='София',geo='42.69770,23.32190')]
TILE=bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'+'1f15c489'+'0000000d49444154789c6360f8cf000000030101007a2d0a1b0000000049454e44ae426082')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  ctx=b.new_context(viewport={'width':390,'height':844},geolocation={'latitude':42.6194,'longitude':25.3956,'accuracy':10},permissions=['geolocation'])
  ctx.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/leaflet.js',content_type='application/javascript'))
  ctx.route('https://server.arcgisonline.com/**',lambda r:r.fulfill(body=TILE,content_type='image/png'));ctx.route('https://tile.openstreetmap.org/**',lambda r:r.fulfill(body=TILE,content_type='image/png'))
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  pg.click('.tab[data-v="map"]');pg.wait_for_timeout(300)
  check('B1 Карта: „Атлас“ instead of „Схема“', pg.evaluate("[...document.querySelectorAll('[data-mm]')].map(b=>b.textContent)"), ['Истинска карта','Атлас'])
  pg.click('[data-mm="grid"]');pg.wait_for_timeout(1200)
  check('B2 your position’s square at the top (from the phone’s GPS)', pg.inner_text('.athead b'), '35T LH 61')
  sq=pg.evaluate("[...document.querySelectorAll('.atq')].map(g=>g.dataset.atq+':'+g.querySelector('.atn').textContent).sort()")
  check('B3 the squares with your records, in both zones, each with its number of species', sq, ['34T FN 92:1','35T LH 61:2','35T LH 63:1'])
  pg.click('[data-atq="35T LH 61"]');pg.wait_for_timeout(150)
  check('B4 tapping a square: its species, days, and the strongest breeding code this year (older years small)', (pg.inner_text('.atd h3'),pg.inner_text('.atd .note2'),pg.evaluate("[...document.querySelectorAll('.atd .ar')].map(a=>a.innerText.replace(/\\s+/g,' ').trim())")),
    ('35T LH 61','2 вида · 3 дни в квадрата',['Кос C14 B4 · 2025 2×','Сойка 1×']))
  pg.click('[data-mm="real"]');pg.wait_for_function("window.__map",timeout=8000);pg.wait_for_timeout(400)
  a=pg.evaluate("document.querySelectorAll('#lmap path.leaflet-interactive').length")
  pg.click('[data-atov]');pg.wait_for_function(f"window.__map&&document.querySelectorAll('#lmap path.leaflet-interactive').length==={a}+3",timeout=8000)
  check('B5 „▦ квадрати“ draws your squares over the real map, and is remembered', (pg.evaluate("Object.keys(atlasData()).length"),pg.evaluate("localStorage.getItem('bird-journal-atlasov')")), (3,'true'))
  # the path
  pg.click('.tab[data-v="log"]');pg.click('#sessStart');pg.wait_for_timeout(200);pg.click('#cancel')
  check('B6 the outing banner has „📍 път“, off until you switch it on', (pg.inner_text('#sessTrk'),pg.evaluate("!!SESS.trkOn")), ('📍 път',False))
  pg.click('#sessTrk');pg.wait_for_timeout(800)
  for la,lo in [(42.6200,25.3960),(42.6230,25.3960),(42.6260,25.3960),(42.62605,25.39601),(42.6290,25.3960)]:
    ctx.set_geolocation({'latitude':la,'longitude':lo,'accuracy':8});pg.wait_for_timeout(500)
  t=pg.evaluate("SESS.trk.length");d=pg.evaluate("SESS.dist")
  check('B7 walking ~1 km north: points every 25 m or more, the distance measured (tiny jitters ignored)', (t,round(d,1),pg.inner_text('#sessTrk')), (5,1.1,'📍 1,1 км ⏸'))   # the first point is where you stood when switching it on
  pg.click('#sessTrk');ctx.set_geolocation({'latitude':42.6400,'longitude':25.3960,'accuracy':8});pg.wait_for_timeout(500)
  check('B8 pausing stops adding points; the banner says so', (pg.evaluate("SESS.trk.length"),pg.inner_text('#sessTrk')), (5,'📍 1,1 км ▶'))
  pg.click('#sessTrk');pg.wait_for_timeout(300)
  pg.click('#toggle');pg.fill('#f-bg','Сойка');pg.click('#savebtn');pg.wait_for_timeout(200);pg.click('#cancel') if pg.is_visible('#cancel') else None
  pg.evaluate("yayHide&&yayHide()");pg.click('#sessEnd');pg.wait_for_timeout(150);pg.fill('#se-start','07:00');pg.fill('#se-end','09:00');pg.click('#sess [data-done="1"]');pg.wait_for_timeout(600)
  o=pg.evaluate("OUTS[OUTS.length-1]")
  check('B9 the ended outing keeps its path and distance; the GPS stops', (len(o.get('trk') or [])>=5,round(o.get('dist',0),1),pg.evaluate("trkW")), (True,2.3,None))   # resuming 1,2 km further adds that stretch
  pg.evaluate("yayHide&&yayHide()");pg.click('.tab[data-v="outs"]');pg.wait_for_timeout(150);pg.locator('.ou').first.click();pg.wait_for_timeout(150)
  check('B10 Излети: the opened outing shows its path and „път: 2,3 км“', (pg.locator('.trk svg path').count(),pg.inner_text('.trk .note2').startswith('път: 2,3 км')), (1,True))
  pg.evaluate("window.__f=[];offer=(n,c)=>__f.push([n,c]);0");pg.click('#acct');pg.click('#ebird');pg.click('#eb-ok');pg.wait_for_timeout(300)
  row=[l.split(',') for l in pg.evaluate("__f[0][1]").strip().split('\n') if 'Сойка' in l or 'Eurasian jay' in l.lower() or 'Garrulus' in l][-1]
  check('B11 eBird: a Traveling list with the measured distance (in miles)', (row[12],row[16]), ('Traveling','1.43'))
  pg.click('[data-acctback]');pg.click('.tab[data-v="log"]');pg.click('#sessStart');pg.wait_for_timeout(600)
  check('B12 the next outing remembers: „Записвай пътя“ is on from the start', (pg.evaluate("!!SESS.trkOn"),pg.evaluate("trkW!==null")), (True,True))
  check('B13 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
