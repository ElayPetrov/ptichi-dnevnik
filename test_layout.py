import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-24',time='09:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8963;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
SP=['Сврака','Сойка','Кос','Чинка','Голям синигер','Син синигер','Гугутка','Щиглец','Врабче','Зеленика','Червеногръдка']
data=[R(id=i+1,bg=n,place='Копринка',geo='42.6300,25.3200',photo=f'p{i}',time=f'08:{10+i:02d}') for i,n in enumerate(SP)]+\
     [R(id=50,bg='Сива чапла',geo='42.62112,25.39188'),R(id=51,bg='Голяма бяла чапла',geo='42.62133,25.39201'),R(id=52,bg='Кълвач',geo='42.70000,25.40000'),R(id=53,bg='Скорец')]
TILE=bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'+'1f15c489'+'0000000d49444154789c6360f8cf000000030101007a2d0a1b0000000049454e44ae426082')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':360,'height':800});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/leaflet.js',content_type='application/javascript'))
  pg.route('https://server.arcgisonline.com/**',lambda r:r.fulfill(body=TILE,content_type='image/png'))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300)
  pg.evaluate("""new Promise(r=>{const q=indexedDB.open('birdphotos',1);q.onsuccess=async()=>{const im=await (await fetch('a.jpg')).blob();
    const t=q.result.transaction('p','readwrite');for(let i=0;i<11;i++)t.objectStore('p').put(im,'p'+i);t.oncomplete=()=>r();};})""")
  tabs=pg.evaluate("[...document.querySelectorAll('.tab')].map(t=>t.textContent)")
  check('L1 the tabs: Дневник, Приятели, Моите видове, Излети, Карта, Места, Фенология, Значки', tabs, ['Дневник','Приятели','Моите видове','Излети','Карта','Места','Фенология','Значки'])
  fit=pg.evaluate("(()=>{const W=document.documentElement.clientWidth,r=[...document.querySelectorAll('.tab')].map(t=>t.getBoundingClientRect());return [r.every(x=>x.left>=0&&x.right<=W),new Set(r.map(x=>Math.round(x.top))).size];})()")
  check('L2 on a 360 px phone all eight show at once, in two rows', fit, [True,2])
  pg.click('.tab[data-v="badges"]');pg.wait_for_timeout(150);nb=pg.locator('.bd2').count()
  pg.click('.tab[data-v="life"]');pg.wait_for_timeout(150)
  check('L3 the badges live in Значки, no longer in Моите видове', (nb,pg.locator('#view .bd2').count()), (30,0))
  pg.click('.tab[data-v="places"]');pg.wait_for_timeout(200)
  names=pg.evaluate("[...document.querySelectorAll('.pl .nm')].map(e=>e.textContent)")
  check('L4 Места: named places first, then each unnamed point by its coordinates, then the records with neither', names, ['Копринка','42.621, 25.392','42.700, 25.400','без място и координати'])
  check('L5 ...the unnamed ones are marked „без име“', pg.locator('.pl.unnamed .tag').count(), 2)
  pg.click('.plh[data-pl="n:Копринка"]');pg.wait_for_function("document.querySelector('#plmap .leaflet-tile-loaded')",timeout=6000)
  check('L6 tapping a place opens it: a small map with its point, its species and every record, each with „промени“',
    (pg.locator('#plmap path.leaflet-interactive').count(),pg.locator('.pl.on .sl span').count(),pg.locator('.pl.on .orr').count(),pg.locator('.pl.on .orr [data-ed]').count()), (1,11,11,11))
  pg.click('.plh[data-pl="n:Копринка"]');pg.wait_for_timeout(150)
  check('L7 tapping it again closes it', pg.locator('.pl.on').count(), 0)
  pg.click('.tab[data-v="map"]');pg.wait_for_timeout(200)
  first=pg.evaluate("document.querySelector('.mapbar .chip').dataset.mm")
  pg.click('[data-mm="real"]');pg.wait_for_function("document.querySelector('[data-tk]')",timeout=6000)
  rows=pg.evaluate("(()=>{const a=document.querySelector('[data-mm=\"real\"]').getBoundingClientRect(),t=document.querySelector('[data-tk]').getBoundingClientRect();return t.top>=a.bottom;})()")
  check('L8 Карта: „Истинска карта“ first, its map styles on a row beneath it', (first,rows), ('real',True))
  pg.click('[data-mm="grid"]');pg.wait_for_timeout(200)
  i=pg.evaluate("window.__C.findIndex(c=>c.name==='Копринка')");pg.locator(f'svg .pt[data-c="{i}"]').click()
  pg.wait_for_function("document.querySelectorAll('#mp .phstrip .th img').length===11",timeout=6000)
  sc=pg.evaluate("(()=>{const s=document.querySelector('#mp .phstrip');return [document.querySelectorAll('#mp .phstrip figure').length,s.scrollWidth>s.clientWidth,getComputedStyle(s).overflowX,document.querySelector('#mp .phcount').textContent];})()")
  check('L9 a point shows all 11 photos, not 8, in a strip that swipes sideways', sc, [11,True,'auto','11 снимки — плъзни настрани'])
  check('L10 nothing pushes the page sideways', pg.evaluate("document.documentElement.scrollWidth<=document.documentElement.clientWidth"), True)
  pg.evaluate("ME={id:'u1',email:'ivan@test.bg'};MYNAME='Иван';MYCODE='ABCDEFGHJKLM';FR={fol:[],fans:[]};view='acct';render()")
  check('L11 the account view: friends first; your code, who sees you, and you with „изход“ further down',
    pg.evaluate("[...document.querySelectorAll('.fr h3')].map(h=>h.textContent)"), ['Дневници на приятели','Добави приятел','Твоят код','Виждат твоя дневник','Ти'])
  check('L12 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
