import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
port=int(sys.argv[1]) if len(sys.argv)>1 else 8979;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(700)
  heads=[]
  for _ in range(4):
    heads.append(pg.inner_text('#wl-body h2'))
    if pg.is_visible('#wl-next'):pg.click('#wl-next')
    elif pg.locator('[data-wl="next"]').count():pg.click('[data-wl="next"]')   # the profile card has its own „По-късно“
    pg.wait_for_timeout(80)
  check('O1 a new user gets four welcome cards', heads, ['Добре дошъл в Пера́','Сложи го на началния екран','Профил — по желание, но си струва','Първата ти птица'])
  pg.click('#wl-prev');pg.wait_for_timeout(80);t=pg.inner_text('#wl-body')
  check('O2 the profile card says why and how, and what friends will see', ('копие в облака' in t,'кръгчето с птичката горе вдясно' in t,'точните места' in t), (True,True,True))
  pg.click('[data-wl="acct"]');pg.wait_for_timeout(250)
  check('O3 „Направи профил сега“ goes straight to the profile', (pg.evaluate("document.getElementById('wlDlg').open"),pg.evaluate("view")), (False,'acct'))
  check('O4 the profile holds „Данни“ (the moved buttons) and „Как се ползва“', (pg.locator('#dataSlot #exp').count(),pg.locator('#dataSlot #bak').count(),pg.locator('[data-tipsreset]').count()), (1,1,1))
  pg.click('[data-acctback]');pg.wait_for_timeout(150)
  check('O5 the data buttons are no longer under every tab', pg.locator('.foot #exp').count(), 0)
  check('O6 an empty journal shows no wall of zeros, no filters, no search', (pg.is_visible('.stats'),pg.is_visible('#filters'),pg.is_visible('#q')), (False,False,False))
  pg.click('.tab[data-v="outs"]');pg.wait_for_timeout(150)
  check('O7 empty tabs say what they are for', 'натисни „Излет“' in pg.inner_text('#view'), True)
  pg.click('[data-first]');pg.wait_for_timeout(200)
  check('O8 „Запиши първата птица“ opens the form, with the form tip once', (pg.evaluate("form.classList.contains('on')"),pg.locator('#tip-form .tip').count()), (True,1))
  check('O9 the form\'s examples read as examples', pg.get_attribute('#f-bg','placeholder'), 'напр. Черна червеноопашка')
  pg.click('#tip-form [data-tip]');pg.click('#f-unsure');pg.wait_for_timeout(100)
  check('O10 „Разбрах“ removes it; ticking „не съм сигурен“ shows its own tip', (pg.locator('#tip-form .tip').count(),pg.locator('#tip-unsure .tip').count()), (0,1))
  pg.click('#tip-unsure [data-tip]');pg.click('#f-unsure');pg.fill('#f-bg','Кос');pg.click('#savebtn');pg.wait_for_timeout(200);pg.evaluate("yayHide()")
  for n in ['Сойка','Сврака']:
    pg.click('#toggle') if not pg.evaluate("form.classList.contains('on')") else None;pg.fill('#f-bg',n);pg.click('#savebtn');pg.wait_for_timeout(150);pg.evaluate("yayHide()")
  pg.click('#cancel') if pg.is_visible('#cancel') else None;pg.click('.tab[data-v="log"]');pg.wait_for_timeout(150)
  check('O11 after three records without an outing, Дневник suggests „Излет“; the zeros come back', (pg.locator('[data-tipbox="outing"]').count(),pg.is_visible('.stats')), (1,True))
  pg.click('#sessStart');pg.wait_for_timeout(150);pg.click('#cancel') if pg.is_visible('#cancel') else None
  check('O12 starting an outing explains the green banner and „Списък“', pg.locator('#tip-sess .tip').count(), 1)
  pg.click('.tab[data-v="phen"]');pg.wait_for_timeout(150);a=pg.locator('[data-tipbox="phen"]').count();pg.click('[data-tip="phen"]');pg.click('.tab[data-v="log"]');pg.click('.tab[data-v="phen"]');pg.wait_for_timeout(100)
  check('O13 a tab tip appears once, never again after „Разбрах“', (a,pg.locator('[data-tipbox="phen"]').count()), (1,0))
  check('O14 the record line no longer puts the group next to the time', 'Дроздове' in pg.evaluate("[...document.querySelectorAll('.o .meta')][1]?.textContent||''"), False)
  # someone who already uses the app: nothing appears
  old=b.new_page(viewport={'width':390,'height':844});old.on('pageerror',lambda e:errs.append(str(e)))
  old.add_init_script("localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps([{'id':1,'date':'2026-10-20','time':'08:00','place':'Копринка','count':'','bg':'Кос','en':'','la':'','fam':'','note':'','h':0,'s':1,'p':0,'beh':[],'geo':None,'photo':None}],ensure_ascii=False)))
  old.goto(f'http://localhost:{port}/ptichi-dnevnik.html');old.wait_for_timeout(700);old.click('#toggle');old.wait_for_timeout(100)
  check('O15 an existing journal gets no welcome and no tips', (old.evaluate("document.getElementById('wlDlg').open"),old.locator('.tip').count(),old.evaluate("document.getElementById('acct').classList.contains('dot')")), (False,0,False))
  old.click('#cancel');old.click('#acct');old.wait_for_timeout(200);old.click('[data-tipsreset]');old.wait_for_timeout(200)
  check('O16 „Покажи съветите отново“ brings the welcome (and the tips) back', old.evaluate("document.getElementById('wlDlg').open"), True)
  check('O17 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
