import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-20',time='09:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8958;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
TILE=bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'+'1f15c489'+'0000000d49444154789c6360f8cf000000030101007a2d0a1b0000000049454e44ae426082')
data=[R(id=1,bg='Сврака',place='Розариум',geo='42.62100,25.39200')]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();errs=[]
  def page(leaflet=True):
    pg=b.new_page(viewport={'width':420,'height':860});pg.on('pageerror',lambda e:errs.append(str(e)))
    if leaflet: pg.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/leaflet.js',content_type='application/javascript'))
    else: pg.route('https://cdnjs.cloudflare.com/**',lambda r:r.abort())
    pg.route('https://server.arcgisonline.com/**',lambda r:r.fulfill(body=TILE,content_type='image/png'))
    pg.add_init_script("localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
    pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(250);return pg
  pg=page()
  order=pg.evaluate("""(()=>{const f=document.getElementById('form'),q=s=>f.querySelector(s);
    const ids=[...f.querySelectorAll('input,select,textarea')].map(e=>e.id);
    const seq=['#f-fam','.sts','#f-unsure','#beh','#f-date'].map(q),before=(a,b)=>!!(a.compareDocumentPosition(b)&Node.DOCUMENT_POSITION_FOLLOWING);
    return [ids,seq.every((e,i)=>i===0||before(seq[i-1],e))];})()""")
  check('K1 the form runs: count and name, Latin, English, family, heard/saw/photographed, unsure, behaviour, date and time, place, coordinates, note, photo',
    order, [['f-count','f-bg','f-la','f-en','f-fam','f-alt-in','f-date','f-time','f-place','f-geo','f-sess','f-note','f-photo'],True])   # f-alt-in: „Може да е и“, under „не съм сигурен“
  pg.click('#toggle');row=pg.evaluate("(()=>{const r=e=>document.getElementById(e).getBoundingClientRect();return [Math.abs(r('f-count').top-r('f-bg').top)<2,Math.abs(r('f-date').top-r('f-time').top)<2,r('f-count').width<r('f-bg').width/3,document.activeElement.id];})()");pg.click('#cancel')
  check('K1b on a phone: count beside the name (narrow), date beside time, the cursor in the name', row, [True,True,True,'f-bg'])
  pg.click('#toggle');pg.fill('#f-bg','Кос');pg.click('#geoMap')
  pg.wait_for_function("(typeof pickM!=='undefined')&&pickM&&document.querySelector('#pickMap .leaflet-tile-loaded')",timeout=6000)
  c=pg.evaluate("[pickM.getCenter().lat.toFixed(4),pickM.getCenter().lng.toFixed(4),pickM.getZoom()]")
  check('K2 the map opens where you last logged with coordinates', c, ['42.6210','25.3920',15])
  box=pg.locator('#pickMap').bounding_box();pg.mouse.click(box['x']+box['width']*0.7,box['y']+box['height']*0.3);pg.wait_for_timeout(150)
  shown=pg.inner_text('#pickTxt');at=pg.evaluate("pickAt.map(v=>v.toFixed(5)).join(',')")
  check('K3 a tap drops the pin and shows its coordinates', (pg.is_enabled('#pickOk'),shown==at.replace(',',', ')), (True,True))
  pg.click('#pickOk');pg.wait_for_timeout(100)
  check('K4 Готово puts the point in the form', (pg.input_value('#f-geo'),pg.inner_text('#geoHint'),pg.evaluate("document.getElementById('pickDlg').open")), (at,'посочено на картата',False))
  pg.fill('#f-place','Розариум');pg.locator('#f-place').dispatch_event('change');pg.wait_for_timeout(100)
  check('K5 typing a known place afterwards does not move your pin', pg.input_value('#f-geo'), at)
  pg.click('#geoMap');pg.wait_for_timeout(400)
  c2=pg.evaluate("[pickAt.map(v=>v.toFixed(5)).join(','),pickM.getZoom(),document.getElementById('pickOk').disabled]")
  check('K6 reopening starts at the point already in the form, pin in place', c2, [at,15,False])
  pg.click('#pickCancel');pg.click('#savebtn');pg.wait_for_timeout(300)
  check('K7 the record is saved with that point', pg.evaluate("OBS.find(o=>o.bg==='Кос').geo"), at)
  off=page(leaflet=False);off.click('#toggle');off.click('#geoMap');off.wait_for_timeout(1500)
  check('K8 without signal it says the map needs the internet', off.inner_text('#pickTxt'), 'Картата иска връзка с интернет.')
  check('K9 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
