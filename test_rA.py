import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-20',time='12:00',place='Копринка',count='',bg='Кос',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo='42.6100,25.3000',photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8991;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});ctx.route('https://**',lambda r:r.abort() if 'localhost' not in r.request.url else r.continue_())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps([R(id=1)],ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  # the error log
  pg.evaluate("window.__ins=[];SB={from:t=>({insert:async rows=>{__ins.push([t,rows]);return {error:null};}})};ME={id:'me',email:'i@t.bg'};")
  pg.evaluate("setTimeout(()=>{throw new Error('проба грешка')},0)");pg.wait_for_timeout(300)
  pg.evaluate("setTimeout(()=>{throw new Error('проба грешка')},0)");pg.wait_for_timeout(300)
  sent=pg.evaluate("__ins.flatMap(x=>x[1].map(r=>[x[0],r.msg,r.ver===VER,r.user_id,r.view]))")
  check('A1 an error on the phone is sent to the error log — once, with version, user and screen', sent, [['app_errors','Uncaught Error: проба грешка',True,'me','log']])
  check('A2 ...and leaves the queue once sent', pg.evaluate("ERRQ.length"), 0)
  pg.evaluate("window.dispatchEvent(new ErrorEvent('error',{message:'от добавка',filename:'chrome-extension://abc/x.js',lineno:1}))");pg.wait_for_timeout(200)
  check('A3 errors from browser add-ons are ignored', pg.evaluate("__ins.length"), 1)
  pg.evaluate("SB={from:t=>({insert:async rows=>({error:{message:'offline'}})})};logErr('без връзка','')");pg.wait_for_timeout(200)
  check('A4 when sending fails, the error waits in the queue for later', pg.evaluate("ERRQ.map(e=>e.msg)"), ['без връзка'])
  # „Съобщи за проблем“
  pg.evaluate("window.__sh=null;navigator.share=async d=>{__sh=d;}")
  pg.click('#acct');pg.wait_for_timeout(150);pg.click('[data-report]');pg.wait_for_timeout(150)
  t=pg.evaluate("__sh&&__sh.text")
  check('A5 „Съобщи за проблем“ opens a ready message with version, phone and the last errors', (t.startswith('Проблем в Перá'),'версия '+pg.evaluate('VER') in t,'екран 390×844' in t,'последни грешки: без връзка' in t), (True,True,True,True))
  pg.click('[data-acctback]')
  # the gallery
  pg.click('#toggle');pg.fill('#f-bg','Сойка');pg.set_input_files('#f-photo','/home/claude/a.jpg');pg.wait_for_function("phNew.length===1",timeout=8000)
  pg.set_input_files('#f-photo2',['/home/claude/b.jpg']);pg.wait_for_function("phx.length===1",timeout=8000);pg.click('#savebtn');pg.wait_for_timeout(300);pg.click('#cancel') if pg.is_visible('#cancel') else None
  pg.click('#toggle');pg.fill('#f-bg','Авлига');pg.fill('#f-place','Тюлбето');pg.set_input_files('#f-photo','/home/claude/b.jpg');pg.wait_for_function("phNew.length===1",timeout=8000);pg.click('#savebtn');pg.wait_for_timeout(300);pg.click('#cancel') if pg.is_visible('#cancel') else None
  pg.click('#acct');pg.wait_for_timeout(150)
  check('A6 „📷 Снимки“ in your profile, folded, counting every photo (main and extra)', (pg.inner_text('[data-ffold="myph"] span'),pg.is_visible('[data-ffold="myph"]+.fsb')), ('📷 Снимки · 3',False))
  pg.click('[data-ffold="myph"]');pg.wait_for_timeout(400)
  names=lambda:pg.evaluate("[...document.querySelectorAll('[data-ffold=myph]+.fsb .galc span')].map(s=>s.textContent)")
  check('A7 the grid shows each photo with its species, newest first', names(), ['Авлига','Сойка','Сойка'])
  pg.select_option('[data-galsort]','place');pg.wait_for_timeout(300)
  check('A8 sorting by place (and it is remembered)', (pg.evaluate("[...document.querySelectorAll('[data-ffold=myph]+.fsb .galc')].map(b=>OBS.find(o=>o.id==b.dataset.galr).place)"),pg.evaluate("localStorage.getItem('bird-journal-galsort')")), (['Тюлбето','',''],'"place"'))   # the two jay photos have no place: they come last
  pg.wait_for_selector('[data-ffold=myph]+.fsb .galc img',timeout=5000);first=pg.inner_text('[data-ffold=myph]+.fsb .galc span');pg.locator('[data-ffold=myph]+.fsb .galc').first.click();pg.wait_for_timeout(200)
  check('A9 tapping a photo opens it full-screen with its species, date and „покажи записа“', (pg.evaluate("document.getElementById('lb').open"),first in pg.inner_text('#lbcap'),pg.locator('#lbcap [data-galrec]').count()), (True,True,1))
  rid=pg.get_attribute('#lbcap [data-galrec]','data-galrec');pg.click('#lbcap [data-galrec]');pg.wait_for_timeout(300)
  check('A10 „покажи записа“ takes you to that record in Дневник', (pg.evaluate("view"),pg.evaluate(f"!!document.querySelector('#view [data-ed=\"{rid}\"]').closest('.o').classList.contains('flash')")), ('log',True))
  # a friend's gallery
  pg.evaluate("FR={fol:[{id:'u2',name:'Петър',data:{obs:[{id:90,date:'2026-10-01',time:'09:00',place:'Тюлбето',count:'',bg:'Червеногръдка',en:'',la:'',fam:'',note:'',h:0,s:1,p:1,beh:[],geo:null,photo:'phF'}],outs:[]},updated_at:new Date().toISOString()}],fans:[]};fsel='u2';view='friends';render()")
  pg.wait_for_timeout(200)
  check('A11 a friend’s profile has „📷 Снимки на Петър“ with names', (pg.inner_text('[data-ffold="ph"] span'),pg.evaluate("[...document.querySelectorAll('[data-ffold=ph]+.fsb .galc span')].map(s=>s.textContent)")), ('📷 Снимки на Петър · 1',['Червеногръдка']))
  # the photo's own data
  pg.evaluate("fsel=null;view='log';render()");pg.click('#toggle');pg.fill('#f-bg','Кос');pg.fill('#f-date','2026-11-02');pg.fill('#f-time','18:00')
  pg.set_input_files('#f-photo','/home/claude/exif.jpg');pg.wait_for_function("phNew.length===1",timeout=8000);pg.wait_for_timeout(200)
  check('A12 a photo carrying its own date and place: a small line under it, no window', (pg.is_visible('#f-exif'),pg.inner_text('#f-exif span')), (True,'📷 15 октомври 2026, 08:14 · близо до Копринка'))
  pg.click('[data-exif="1"]');pg.wait_for_timeout(100)
  check('A13 „вземи“ fills in the date, time and place', (pg.input_value('#f-date'),pg.input_value('#f-time'),pg.input_value('#f-geo'),pg.is_visible('#f-exif')), ('2026-10-15','08:14','42.61050,25.30020',False))
  pg.click('#cancel');pg.click('#toggle');pg.set_input_files('#f-photo','/home/claude/a.jpg');pg.wait_for_function("phNew.length===1",timeout=8000);pg.wait_for_timeout(200)
  check('A14 a photo without such data shows nothing', pg.is_visible('#f-exif'), False)
  pg.click('#cancel');pg.click('#toggle');pg.set_input_files('#f-photo','/home/claude/exif.jpg');pg.wait_for_function("phNew.length===1",timeout=8000);pg.wait_for_timeout(200);pg.click('[data-exif="0"]')
  check('A15 „×“ ignores it and keeps your date', (pg.is_visible('#f-exif'),pg.input_value('#f-date')!='2026-10-15'), (False,True))
  real=[e for e in errs if 'проба грешка' not in e]
  check('A16 no page errors (apart from the test’s own)', real, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
