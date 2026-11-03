# 3 Nov 2026 cosmetic round: Дневник remembers folding in every filter (each filter its own; a new record still opens
# its day everywhere), the map's style buttons are small, and the profile is a header card plus sections.
import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
T=datetime.date.today();D=lambda n:(T-datetime.timedelta(days=n)).isoformat()
R=lambda **k:{**dict(id=0,date=D(1),time='08:00',place='Копринка',count='',bg='Кос',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo='42.61000,25.30000',photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 9002;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,date=D(1)),R(id=2,date=D(2),bg='Сойка'),R(id=3,date=D(3),bg='Сврака',h=1,s=0),R(id=4,date=D(2),bg='Авлига',h=1,s=0)]
TILE=bytes.fromhex('89504e470d0a1a0a0000000d4948445200000001000000010806000000'+'1f15c489'+'0000000d49444154789c6360f8cf000000030101007a2d0a1b0000000049454e44ae426082')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844})
  ctx.route('https://cdnjs.cloudflare.com/ajax/libs/leaflet/**',lambda r:r.fulfill(path='/home/claude/sb/leaflet/leaflet.js',content_type='application/javascript'))
  ctx.route('https://server.arcgisonline.com/**',lambda r:r.fulfill(body=TILE,content_type='image/png'))
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  shut=lambda d:pg.evaluate(f"(g=>g?g.classList.contains('shut'):null)(document.querySelector('[data-dayt=\"{d}\"]')&&document.querySelector('[data-dayt=\"{d}\"]').closest('.dayg'))")
  pg.click('[data-f="h"]');pg.wait_for_timeout(150)
  check('C1 a filter shows its days open at first', (shut(D(2)),shut(D(3))), (False,False))
  pg.click(f'[data-dayt="{D(3)}"]');pg.wait_for_timeout(80)
  pg.click('[data-f="all"]');pg.wait_for_timeout(120);pg.click('[data-f="h"]');pg.wait_for_timeout(120)
  check('C2 folding a day in „чух“ is remembered when you come back to „чух“', (shut(D(3)),shut(D(2))), (True,False))
  pg.reload();pg.wait_for_timeout(400);pg.click('[data-f="h"]');pg.wait_for_timeout(150)
  check('C3 ...even after reopening the app', shut(D(3)), True)
  pg.click('[data-f="s"]');pg.wait_for_timeout(120)
  check('C4 each filter keeps its own: in „видях“ that day is still open', shut(D(3)) in (False,None), True)
  pg.click('[data-f="all"]');pg.wait_for_timeout(120)
  allst=shut(D(3))
  pg.click('[data-f="h"]');pg.wait_for_timeout(120)
  pg.evaluate(f"setDay('{D(3)}',true)")   # what saving a record on that day does
  pg.click('[data-f="all"]');pg.wait_for_timeout(80);pg.click('[data-f="h"]');pg.wait_for_timeout(120)
  check('C5 a new record on a folded day opens it in every filter', shut(D(3)), False)
  pg.click('[data-f="all"]');pg.click('.tab[data-v="map"]');pg.wait_for_timeout(400)
  if pg.evaluate("mapMode")!='real':pg.click('[data-mm="real"]');pg.wait_for_timeout(300)
  sz=pg.evaluate("(()=>{const s=getComputedStyle(document.querySelector('.tilesub .sub')),m=document.querySelector('[data-mm=real]').getBoundingClientRect(),b=document.querySelector('.tilesub .sub').getBoundingClientRect();return [parseFloat(s.fontSize),b.height<m.height*0.75]})()")
  check('C7 the map’s style buttons are small (11.5 px text, well under the height of „Истинска карта“)', sz, [11.5,True])
  pg.evaluate("ME={id:'me',email:'ivan@example.bg'};MYNAME='Иван Петров';MYCODE='AB12CD34EF56';FR={fol:[{id:'u2',name:'Петър Георгиев',data:{obs:[],outs:[]},updated_at:'2026-11-03T08:00:00Z'}],fans:[{id:'u4',name:'Георги'}]}")
  pg.click('#acct');pg.wait_for_timeout(500)
  check('C8 the profile opens with a header card: initials, name, e-mail, and four numbers', (pg.inner_text('.phero .fav'),pg.inner_text('.phero h2'),'ivan@example.bg' in pg.inner_text('.phero'),pg.evaluate("[...document.querySelectorAll('.ptiles span')].map(s=>s.textContent)")),
    ('ИП','Иван Петров',True,['вида','записа','излета','нива значки']))
  check('C9 friends and followers get initials avatars; adding a friend sits inside the friends’ card', (pg.locator('.pcard .prow .pav').count(),pg.locator('.pcard #fr-code').count()), (2,1))
  check('C10 „Как се ползва“ is folded inside „Помощ“; sign-out is alone at the bottom', (pg.evaluate("document.querySelector('.phow').open"),pg.locator('.pout [data-sb=\"out\"]').count()), (False,1))
  check('C11 nothing on the profile pushes past a 390 px screen', pg.evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth"), False)
  check('C12 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
