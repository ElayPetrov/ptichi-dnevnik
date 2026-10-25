import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
Y=datetime.date.today().year
R=lambda **k:{**dict(id=0,date=f'{Y}-10-24',time='09:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8965;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,bg='Сврака',h=1,s=0),R(id=2,bg='Сойка',date=f'{Y}-09-12'),R(id=3,bg='Кос',date=f'{Y}-09-02'),R(id=4,bg='Кос',date=f'{Y}-08-15'),R(id=5,bg='Чинка',date=f'{Y-1}-12-30'),
      R(id=10,bg='Голям синигер',sess='sA',geo='42.6300,25.3200',photo='q0',time='08:10'),R(id=11,bg='Син синигер',sess='sA',geo='42.6320,25.3240',photo='q1',time='08:30'),R(id=12,bg='Гугутка',sess='sA',geo='42.6340,25.3260',photo='q2',time='08:50')]
outs=[{'id':'sA','date':f'{Y}-10-24','place':'Копринка','start':'08:00','end':'09:30','complete':True,'upd':1}]
TILE=bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'+'1f15c489'+'0000000d49444154789c6360f8cf000000030101007a2d0a1b0000000049454e44ae426082')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':360,'height':800});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.route('https://server.arcgisonline.com/**',lambda r:r.fulfill(body=TILE,content_type='image/png'))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-outings',%s);}"%(json.dumps(json.dumps(data,ensure_ascii=False)),json.dumps(json.dumps(outs,ensure_ascii=False))))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300)
  pg.evaluate("""new Promise(r=>{const q=indexedDB.open('birdphotos',1);q.onsuccess=async()=>{const im=await (await fetch('a.jpg')).blob();
    const t=q.result.transaction('p','readwrite');for(let i=0;i<3;i++)t.objectStore('p').put(im,'q'+i);t.oncomplete=()=>r();};})""")
  pg.reload();pg.wait_for_timeout(300)
  # filters
  ch=pg.evaluate("[...document.querySelectorAll('#filters .chip')].map(c=>[c.dataset.f,!!c.querySelector('svg'),c.getAttribute('aria-label')])")
  check('Q1 the filters: Всички, then ear, eye, camera and calendar icons; „Тази година“ is gone',
    ch, [['all',False,None],['h',True,'Само чути'],['s',True,'Видени'],['p',True,'Снимани'],['ylist',True,'Годишен списък']])
  fit=pg.evaluate("(()=>{const W=document.documentElement.clientWidth;return [...document.querySelectorAll('#filters .chip')].every(c=>{const r=c.getBoundingClientRect();return r.left>=0&&r.right<=W;});})()")
  check('Q2 all five show on a 360 px phone without swiping', fit, True)
  pg.click('#filters [data-f="h"]');pg.wait_for_timeout(150)
  check('Q3 the chosen filter shows its word, and „само чути“ keeps only heard-only birds',
    (pg.is_visible('#filters [data-f="h"] .lbl'),pg.is_visible('#filters [data-f="s"] .lbl'),pg.evaluate("[...document.querySelectorAll('.o .nm')].map(n=>n.firstChild.textContent)")), (True,False,['Сврака']))
  pg.click('#filters [data-f="all"]');pg.wait_for_timeout(150)
  # months and years
  hdr=pg.evaluate("[...document.querySelectorAll('.ymh')].map(h=>[h.dataset.ymt,h.parentElement.classList.contains('shut')])")
  check('Q4 years and months fold: this year and this month open, the older ones folded',
    hdr, [[f'y:{Y}',False],[f'm:{Y}-10',False],[f'm:{Y}-09',True],[f'm:{Y}-08',True],[f'y:{Y-1}',True],[f'm:{Y-1}-12',True]])
  pg.click(f'[data-ymt="m:{Y}-09"]');pg.reload();pg.wait_for_timeout(300)
  check('Q5 a month you open stays open', pg.evaluate(f"document.querySelector('[data-ymt=\"m:{Y}-09\"]').parentElement.classList.contains('shut')"), False)
  check('Q6 the month line counts its records and species', pg.inner_text(f'[data-ymt="m:{Y}-09"] .dcount'), '2 записа · 2 вида')
  pg.fill('#q','чинка');pg.wait_for_timeout(200)
  check('Q7 searching opens the year and month with a match', pg.evaluate("[...document.querySelectorAll('.yg,.mg')].every(g=>!g.classList.contains('shut'))"), True)
  pg.fill('#q','');pg.wait_for_timeout(150)
  # outings: a little map and the photos on the card
  pg.click('.tab[data-v="outs"]');pg.wait_for_timeout(300)
  m=pg.evaluate("(()=>{const m=document.querySelector('.ou .oumap');return [!!m,m&&m.querySelectorAll('img').length>0,m&&m.querySelectorAll('i').length];})()")
  check('Q8 each outing card shows a little map with its points, before opening', m, [True,True,3])
  pg.wait_for_function("document.querySelectorAll('.ou .ouph .th img').length===3",timeout=5000)
  pg.click('.ou .ouph .th img >> nth=0');pg.wait_for_timeout(200)
  check('Q9 ...and all its photos; tapping one opens the photo, not the card', (pg.evaluate("document.getElementById('lb').open"),pg.locator('.ou .orl').count()), (True,0))
  pg.evaluate("document.getElementById('lb').close()")
  # phenology
  pg.click('.tab[data-v="phen"]');pg.wait_for_timeout(250)
  check('Q10 Фенология: По месеци (shown first), Годишна крива, Първи срещи', (pg.evaluate("[...document.querySelectorAll('[data-pm]')].map(c=>c.textContent)"),pg.locator('table.ph2').count()), (['По месеци','Годишна крива','Първи срещи'],1))
  w=pg.evaluate("(()=>{const p=document.querySelector('.phen'),t=document.querySelector('table.ph2 thead tr').getBoundingClientRect();return [p.scrollWidth<=p.clientWidth,document.documentElement.scrollWidth<=document.documentElement.clientWidth,t.right<=document.documentElement.clientWidth];})()")
  check('Q11 ...all twelve months fit a 360 px screen in one row, no sideways scrolling', w, [True,True,True])
  g=pg.evaluate("""(()=>{const tr=document.querySelector('table.ph2 tbody tr'),n=tr.querySelector('td.sp1'),cells=[...tr.querySelectorAll('td')].slice(1,13),
      hd=[...document.querySelectorAll('table.ph2 thead th')].slice(1,13);
    const one=n.getBoundingClientRect().height<26,full=n.scrollWidth<=n.clientWidth+1&&getComputedStyle(n).textOverflow!=='ellipsis',
      row=new Set(cells.map(c=>Math.round(c.getBoundingClientRect().top))).size===1,
      lined=cells.every((c,i)=>Math.abs(c.getBoundingClientRect().left-hd[i].getBoundingClientRect().left)<1.5),
      below=cells[0].getBoundingClientRect().top>n.getBoundingClientRect().bottom-1,
      sticky=getComputedStyle(document.querySelector('table.ph2 thead')).position==='sticky';
    return [n.textContent,one,full,row,lined,below,sticky];})()""")
  check('Q11b ...each bird\'s full name on one line, its twelve months beneath it, lined up under the month letters that stay pinned on top',
    g, ['Голям синигер',True,True,True,True,True,True])
  check('Q13 the code it shares and sign-up emails use the address the app was opened from (not the old Netlify one)', pg.evaluate("SB_SITE"), f'http://localhost:{port}/')
  check('Q12 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
