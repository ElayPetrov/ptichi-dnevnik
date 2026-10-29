import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
port=int(sys.argv[1]);fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  def page(sess=None):
    ctx=b.new_context();pg=ctx.new_page();pg.errs=[];pg.dialogs=[]
    pg.on('pageerror',lambda e:pg.errs.append(str(e)));pg.on('dialog',lambda d:(pg.dialogs.append(d.message),d.accept()))
    init="localStorage.setItem('bird-journal-v3','[]');localStorage.setItem('bird-journal-tips','{\"all\":1}');"   # an empty journal would otherwise get the welcome
    if sess: init+="localStorage.setItem('bird-journal-session',%s);"%json.dumps(json.dumps(sess,ensure_ascii=False))
    pg.add_init_script("if(!sessionStorage.getItem('s')){"+init+"sessionStorage.setItem('s','1')}")
    pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300);return pg
  form=lambda pg:(pg.input_value('#f-date'),pg.input_value('#f-time'))
  now=lambda pg:tuple(pg.evaluate("[today(),nowTime()]"))
  ago=lambda pg,m:tuple(pg.evaluate(f"(()=>{{const d=new Date(Date.now()-{m}*6e4),z=n=>String(n).padStart(2,'0');return [d.getFullYear()+'-'+z(d.getMonth()+1)+'-'+z(d.getDate()),z(d.getHours())+':'+z(d.getMinutes())]}})()"))
  def save(pg,bg,dt=None):
    pg.fill('#f-bg',bg)
    if dt: pg.fill('#f-date',dt[0]); pg.fill('#f-time',dt[1])
    pg.click('#savebtn')
  pg=page(); pg.click('#sessStart')
  check('M1 new outing starts at now', form(pg), now(pg))
  save(pg,'Сврака',('2026-10-18','06:15'))
  check('M2 writing up: next record continues from the last one', (form(pg),pg.evaluate("SESS.live")), (('2026-10-18','06:15'),False))
  save(pg,'Сойка',('2026-10-18','06:40'))
  check('M3 ...and keeps following it', form(pg), ('2026-10-18','06:40'))
  save(pg,'Кос',ago(pg,10))
  check('M4 a record timed within 30 min of saving flips to live: next is now', (form(pg),pg.evaluate("SESS.live")), (now(pg),True))
  save(pg,'Червеногръдка',None)
  check('M5 live stays live when you keep the default', (form(pg),pg.evaluate("SESS.live")), (now(pg),True))
  t=ago(pg,50); save(pg,'Синигер',t)
  check('M6 a catch-up entry from 50 min ago does not switch live off', (form(pg),pg.evaluate("SESS.live")), (now(pg),True))
  rid=pg.evaluate("OBS.find(o=>o.bg==='Сврака').id"); pg.evaluate("closeForm()"); pg.click(f'[data-again="{rid}"]')
  check('M7 "+ друг вид тук" still copies that record\'s moment', form(pg), ('2026-10-18','06:15'))
  check('M8 no errors or prompts', (pg.errs,pg.dialogs), ([],[]))
  pg=page(sess={'id':'s1','date':'2026-10-18','time':'08:00','place':'Розариум','geo':None,'at':int(time.time()*1000)-600000})
  pg.click('#toggle')
  check('M9 outing from the previous version keeps its old behaviour until a save', form(pg), ('2026-10-18','08:00'))
  pg=page(); pg.click('#sessStart'); save(pg,'Сврака',None)
  check('M10 live walk: first record at now sets live', (form(pg),pg.evaluate("SESS.live")), (now(pg),True))
  save(pg,'Сойка',ago(pg,120)); save(pg,'Кос',None)
  check('M11 ...stays live through a catch-up two hours back', (form(pg),pg.evaluate("SESS.live")), (now(pg),True))
  pg.click('#sessEnd'); pg.click('[data-done="1"]'); pg.click('#sessStart'); t=ago(pg,180); save(pg,'Чапла',t)
  check('M12 writing up this morning\'s walk: continues from the first record', (form(pg),pg.evaluate("SESS.live")), (t,False))
  check('M13 no errors or prompts', (pg.errs,pg.dialogs), ([],[]))
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
