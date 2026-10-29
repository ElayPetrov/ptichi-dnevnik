import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
port=int(sys.argv[1]) if len(sys.argv)>1 else 8975;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
GROUPS=['.s-birds','.s-snow','.s-trees .crown','.s-trees .bare','.s-roses','.s-swallows','.s-swifts','.s-cranes']
EXP={'winter':['.s-birds','.s-snow','.s-trees .bare'],'spring':['.s-trees .crown','.s-swallows'],'roses':['.s-trees .crown','.s-roses','.s-swifts'],
     'summer':['.s-trees .crown','.s-swifts'],'autumn':['.s-trees .crown','.s-cranes']}
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  data=[dict(id=1,date='2026-10-04',time='08:00',place='Язовир Копринка',count='',bg='Голяма бяла чапла',en='',la='Ardea alba',fam='Чапли и щъркели',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None,sess='s1')]
  pg.add_init_script("localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300)
  pg.evaluate("skyAt=new Date(new Date().setHours(12,0,0,0));applySeason(document.querySelector('.hero').dataset.season)")   # these checks are about daytime; the night sky has its own suite
  dates=['2026-01-15','2026-02-28','2026-03-01','2026-04-30','2026-05-01','2026-06-30','2026-07-01','2026-08-31','2026-09-01','2026-11-30','2026-12-01']
  check('S1 months map to seasons (Dec–Feb winter, Mar–Apr spring, May–Jun roses, Jul–Aug summer, Sep–Nov autumn)',
    pg.evaluate("ds=>ds.map(d=>seasonOf(new Date(d+'T12:00')))",dates),
    ['winter','winter','spring','spring','roses','roses','summer','summer','autumn','autumn','winter'])
  check('S2 the header opens in today\'s season', pg.evaluate("document.querySelector('.hero').dataset.season===seasonOf(new Date())"), True)
  shown={}
  for s in EXP:
    pg.evaluate(f"applySeason('{s}')")
    shown[s]=[g for g in GROUPS if pg.evaluate("g=>[...document.querySelectorAll('.hero '+g)].some(e=>getComputedStyle(e).display!=='none')",g)]
  check('S3 each season shows only its own details', shown, EXP)
  pg.evaluate("applySeason('autumn')")
  light=pg.evaluate("getComputedStyle(document.querySelector('.hero')).getPropertyValue('--hill2').trim()")
  pg.click('#acct');pg.click('#theme');dark=pg.evaluate("getComputedStyle(document.querySelector('.hero')).getPropertyValue('--hill2').trim()")
  pg.click('#acct');pg.click('#theme');back=pg.evaluate("getComputedStyle(document.querySelector('.hero')).getPropertyValue('--hill2').trim()")
  check('S4 the season keeps through a theme switch, in that theme\'s colours', (light,dark,back,pg.evaluate("document.querySelector('.hero').dataset.season")), ('#b4884c','#4c3b23','#b4884c','autumn'))
  px="""(()=>{const i=document.getElementById('cardImg'),c=document.createElement('canvas');c.width=i.naturalWidth;c.height=i.naturalHeight;
    const x=c.getContext('2d');x.drawImage(i,0,0);return [...x.getImageData(540,412,1,1).data].slice(0,3);})()"""
  hexrgb=lambda h:[int(h[i:i+2],16) for i in (1,3,5)]
  pg.evaluate("outCard('s1')");pg.wait_for_function("document.getElementById('cardDlg').open&&document.getElementById('cardImg').naturalWidth>0")
  got=pg.evaluate(px);check('S5 an October outing card has autumn hills', max(abs(a-b) for a,b in zip(got,hexrgb('#8c5c36')))<=6, True)
  pg.evaluate("document.getElementById('cardDlg').close()")
  pg.click('.tab[data-v="life"]');pg.locator('.sp',has_text='Голяма бяла чапла').click();pg.click('[data-spcard]')
  pg.wait_for_function("document.getElementById('cardDlg').open&&document.getElementById('cardImg').naturalWidth>0")
  got=pg.evaluate(px);exp=pg.evaluate("SEASONS[seasonOf(new Date())].l.hill3")
  check('S6 a species card has hills in today\'s season', max(abs(a-b) for a,b in zip(got,hexrgb(exp)))<=6, True)
  check('S7 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
