# Forgotten password (2026-11-03.8): „Забравена парола?“ sends Supabase's recovery email back to Перá; the email's link
# opens Перá on a „Нова парола“ card (even if that phone was signed out); „Смени паролата“ sits folded in the profile.
# Supabase is a stand-in here (it records the calls); the email and the link itself are Supabase's.
import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
port=int(sys.argv[1]) if len(sys.argv)>1 else 9003;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
FAKE="""(()=>{window.CALLS=[];const mk=t=>{const p=new Proxy({},{get(o,k){if(k==='then')return r=>r({data:[],error:null});return (...a)=>{CALLS.push([t,k]);return p;};}});return p;};
  SB={from:t=>mk(t),rpc:async()=>({data:'',error:null}),auth:{signOut:async()=>{},getSession:async()=>({data:{session:null}}),
    resetPasswordForEmail:async(m,o)=>{CALLS.push(['reset',m,o.redirectTo]);return {error:null};},updateUser:async(u)=>{CALLS.push(['update',u.password]);return {error:null};}}};
  sbClient=async()=>SB;})()"""
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});ctx.route('https://**',lambda r:r.abort() if 'localhost' not in r.request.url else r.continue_())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true')")
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);pg.evaluate(FAKE)
  pg.click('#acct');pg.wait_for_timeout(300)
  check('W1 the sign-in form offers „Забравена парола?“', pg.locator('[data-sb="forgot"]').inner_text(), 'Забравена парола?')
  pg.click('[data-sb="forgot"]');pg.wait_for_timeout(200)
  check('W2 without an e-mail it asks for one, and sends nothing', ('Впиши имейла си' in pg.inner_text('.fr .msg'),[c for c in pg.evaluate("CALLS") if c[0]=='reset']), (True,[]))
  pg.fill('#sb-mail','ivan@example.bg');pg.click('[data-sb="forgot"]');pg.wait_for_timeout(300)
  check('W3 with the e-mail: Supabase sends the recovery letter, whose link leads back to Перá', ([c for c in pg.evaluate("CALLS") if c[0]=='reset'][0][1:],pg.evaluate("SB_SITE")==[c for c in pg.evaluate("CALLS") if c[0]=='reset'][0][2]), (['ivan@example.bg',pg.evaluate("SB_SITE")],True))
  check('W4 ...and says so', pg.inner_text('.fr .msg').startswith('Изпратих писмо до ivan@example.bg.'), True)
  pg.evaluate("pwRecovery({user:{id:'me',email:'ivan@example.bg'}})");pg.wait_for_timeout(300)
  check('W5 the link signs you in and opens „Нова парола“ at the top of the profile (and no second password form)', (pg.evaluate("view"),pg.inner_text('.pcard h3'),pg.locator('.pwchg').count()), ('acct','Нова парола',0))
  pg.fill('#pw-new','abc');pg.fill('#pw-new2','abc');pg.click('[data-sb="pwset"]');pg.wait_for_timeout(150)
  m1=pg.inner_text('.pwrec .msg');pg.fill('#pw-new','птица123');pg.fill('#pw-new2','птица124');pg.click('[data-sb="pwset"]');pg.wait_for_timeout(150)
  m2=pg.inner_text('.pwrec .msg')
  check('W6 too short, or the two not matching: it says what’s wrong and changes nothing', (m1,m2,[c for c in pg.evaluate("CALLS") if c[0]=='update']), ('Паролата трябва да е поне 6 знака.','Двете не съвпадат — напиши я още веднъж.',[]))
  pg.fill('#pw-new','птица123');pg.fill('#pw-new2','птица123');pg.click('[data-sb="pwset"]');pg.wait_for_timeout(300)
  check('W7 a good one is saved; the card goes; the profile says it’s changed', ([c for c in pg.evaluate("CALLS") if c[0]=='update'],pg.locator('.pwrec').count(),'Паролата е сменена' in pg.inner_text('#view')), ([['update','птица123']],0,True))
  pg.evaluate("pwMsg='';render()");pg.wait_for_timeout(200)
  check('W8 signed in normally: „Смени паролата“ is folded in its own card, above „Изход“', (pg.evaluate("document.querySelector('.pwchg').open"),pg.evaluate("[...document.querySelectorAll('.pcard h3')].map(h=>h.textContent).pop()")), (False,'Парола'))
  check('W9 no page errors', errs, [])
  pg2=ctx.new_page();e2=[];pg2.on('pageerror',lambda e:e2.append(str(e)))
  pg2.goto(f'http://localhost:{port}/ptichi-dnevnik.html#access_token=x&type=recovery');pg2.wait_for_timeout(600)
  check('W10 opening the e-mail’s link, even signed out on that phone, goes straight to the profile to finish', (pg2.evaluate("RECLINK"),pg2.evaluate("view"),e2), (True,'acct',[]))
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
