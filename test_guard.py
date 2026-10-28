# Two people, two devices each, plus someone signing in to their own account on the other person's browser.
import json,subprocess,sys,time,re
sys.path.insert(0,'/home/claude')
from sbstack import Stack
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='',time='',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]);fails=0;SB='https://test-proj.supabase.co'
open('share-test.html','w',encoding='utf-8').write(re.sub(r"const SB_URL='[^']*'","const SB_URL='"+SB+"'",open('ptichi-dnevnik.html',encoding='utf-8').read()))
UMD='/home/claude/sb/package/dist/umd/supabase.js';CDN='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.3/dist/umd/supabase.js'
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
st=Stack('/home/claude/supabase-setup.sql')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  def device(data):
    ctx=b.new_context();pg=ctx.new_page();pg.errs=[];pg.on('pageerror',lambda e:pg.errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
    ctx.route(SB+'/**',st.handle);ctx.route(CDN,lambda r:r.fulfill(path=UMD,headers={'access-control-allow-origin':'*','content-type':'application/javascript'}))
    pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(data,ensure_ascii=False)))
    pg.goto(f'http://localhost:{port}/share-test.html');pg.wait_for_timeout(300);pg.click('#acct');return pg
  def synced(pg): pg.wait_for_function("!syncing&&sbStat.length>0&&sbStat!=='синхронизира…'",timeout=15000)
  def join(pg,name,mail):
    pg.fill('#sb-name',name);pg.fill('#sb-mail',mail);pg.fill('#sb-pw','птица123');pg.click('[data-sb="up"]');pg.wait_for_selector('.fr .msg');st.confirm(mail);pg.click('[data-sb="in"]');synced(pg)
  def signin(pg,mail): pg.fill('#sb-mail',mail);pg.fill('#sb-pw','птица123');pg.click('[data-sb="in"]');synced(pg)
  def sync(pg): pg.evaluate("lastSync=0;syncNow()");pg.wait_for_timeout(150);synced(pg)
  names=lambda pg:sorted(pg.evaluate("OBS.map(o=>o.bg)"))
  cloud=lambda mail:sorted(o['bg'] for o in st.journal(st.uid(mail))['obs'])
  iph=device([R(id=1,date='2026-10-20',bg='Сврака')]);join(iph,'Иван','ivan@test.bg')
  plap=device([]);join(plap,'Петър','petar@test.bg')                       # Petar's laptop first, empty
  pph=device([R(id=11,date='2026-10-19',bg='Кос'),R(id=12,date='2026-10-19',bg='Сойка')]);signin(pph,'petar@test.bg')
  sync(plap);check("G1 the friend's laptop catches up with his phone, exactly as yours did", names(plap), ['Кос','Сойка'])
  plap.click('.tab[data-v="log"]');plap.click('#toggle');plap.fill('#f-bg','Щиглец');plap.click('#savebtn');plap.wait_for_timeout(5500);sync(pph)
  check('G2 ...and what he adds on either device ends up on both', (names(pph),cloud('petar@test.bg')), (['Кос','Сойка','Щиглец'],)*2)
  code=pph.evaluate("MYCODE");iph.fill('#fr-code',code);iph.click('[data-sb="add"]');iph.wait_for_selector('.fr .ar.tap')
  check("G3 you see his merged journal, whichever device he logged on", iph.inner_text('.fr .ar.tap small').startswith('3 вида · 3 записа'), True)
  # Petar signs in to HIS account on Ivan's phone browser: the two journals must not mix
  iph.click('#acct');iph.click('[data-sb="out"]');iph.fill('#sb-mail','petar@test.bg');iph.fill('#sb-pw','птица123');iph.click('[data-sb="in"]')
  iph.wait_for_function("ME&&ME.email==='petar@test.bg'&&!syncing&&sbStat.length>0&&sbStat!=='синхронизира…'",timeout=15000)
  check("G4 his account on your browser: the app refuses to upload your journal into it", (iph.evaluate("sbStat"),cloud('petar@test.bg')),
        ('Дневникът на този телефон е свързан с друг профил — не го качвам.',['Кос','Сойка','Щиглец']))
  check("G5 ...and nothing of his lands in your local journal", names(iph), ['Сврака'])
  # new sign-ups switched off in Supabase: a newcomer gets a plain Bulgarian message, not the raw English error
  nd=device([]);nd.context.route(SB+'/auth/v1/signup*',lambda r:r.fulfill(status=422,content_type='application/json',
     body=json.dumps({'code':422,'error_code':'signup_disabled','msg':'Signups not allowed for this instance'})))
  nd.fill('#sb-name','Непознат');nd.fill('#sb-mail','new@test.bg');nd.fill('#sb-pw','птица123');nd.click('[data-sb="up"]');nd.wait_for_selector('.fr .msg')
  check('G6 with new sign-ups switched off, a newcomer is told so in Bulgarian', nd.inner_text('.fr .msg'), 'Засега не се приемат нови профили.')
  check('G7 no page errors', iph.errs+plap.errs+pph.errs+nd.errs, [])
  b.close()
finally: srv.terminate();st.stop()
print('FAILURES:',fails)
