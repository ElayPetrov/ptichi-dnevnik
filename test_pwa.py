import json,subprocess,sys,time,datetime,os
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='',time='',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]);fails=0;ROOT='/home/claude/netlify'
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
T=datetime.date.today(); D=lambda d:(T+datetime.timedelta(days=d))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port),'-d',ROOT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
URL=f'http://localhost:{port}/'
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  def page(data=None,extra='',**ctxkw):
    ctx=b.new_context(**ctxkw);pg=ctx.new_page();pg.errs=[];pg.dialogs=[];pg.ctx=ctx
    pg.on('pageerror',lambda e:pg.errs.append(str(e)));pg.on('dialog',lambda d:(pg.dialogs.append(d.message),d.accept()))
    if data is not None:
      pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');%ssessionStorage.setItem('s','1')}"%(json.dumps(json.dumps(data,ensure_ascii=False)),extra))   # no welcome in these checks
    pg.goto(URL);pg.wait_for_timeout(400);return pg
  # ---------- installable + offline ----------
  pg=page([]); cdp=pg.ctx.new_cdp_session(pg)
  pg.wait_for_function("navigator.serviceWorker.controller!==null||navigator.serviceWorker.ready.then(()=>true)")
  pg.evaluate("navigator.serviceWorker.ready"); pg.wait_for_timeout(500)
  errs=cdp.send('Page.getInstallabilityErrors')['installabilityErrors']
  check('P1 Chrome sees it as installable', [e['errorId'] for e in errs], [])
  mf=cdp.send('Page.getAppManifest'); check('P2 manifest parses cleanly', (mf.get('errors'),'Пера́' in mf.get('data','')), ([],True))
  pg.reload(); pg.wait_for_function("navigator.serviceWorker.controller!==null")
  pg.click('#toggle'); pg.fill('#f-bg','Сврака'); pg.click('#savebtn')
  pg.ctx.set_offline(True); pg.reload(); pg.wait_for_function("document.getElementById('n-obs').textContent==='1'")
  check('P3 offline: the app opens and shows the saved record', (pg.title(),pg.inner_text('#n-obs')), ('Пера́ — дневник за наблюдение на птици','1'))
  pg.ctx.set_offline(False)
  html=open(ROOT+'/index.html',encoding='utf-8').read()
  import re as _re; open(ROOT+'/index.html','w',encoding='utf-8').write(_re.sub(r"const VER='[^']*'","const VER='TEST-NEW'",html))
  try:
    pg.reload(); pg.wait_for_timeout(300)
    check('P4 online again: a new deploy arrives on the next open', pg.inner_text('#ver'), 'версия TEST-NEW')
    pg.ctx.set_offline(True); pg.reload(); pg.wait_for_timeout(300)
    check('P5 ...and the updated copy is what opens offline', pg.inner_text('#ver'), 'версия TEST-NEW')
    pg.ctx.set_offline(False)
  finally: open(ROOT+'/index.html','w',encoding='utf-8').write(html)
  check('P6 no page errors', pg.errs, [])
  # ---------- backups ----------
  pg=page([R(id=int(time.time()*1000)-i,date=T.isoformat(),bg=f'Вид {i}') for i in range(12)])
  check('B1 12 records and never backed up: reminder shows', (pg.is_visible('#bakNag'),pg.inner_text('#bakNagTxt')), (True,'Още нямаш резервно копие на тези 12 записа.'))
  with pg.expect_download() as dl: pg.click('#acct');pg.click('#bak')
  d=dl.value; body=json.load(open(d.path(),encoding='utf-8'))
  check('B2 backup file is dated and complete', (d.suggested_filename,len(body['obs']),body['v'],body['outs']), (f'ptichi-dnevnik-{T.isoformat()}.json',12,6,[]))
  check('B3 reminder clears; footer shows the date', (pg.is_visible('#bakNag'),pg.inner_text('#bakInfo').startswith('Последно копие: ')), (False,True))
  old=int(time.time()*1000)-40*864e5
  pg=page([R(id=int(old)-5000,date='2026-08-01',bg='Стар')],extra=f"localStorage.setItem('bird-journal-lastbak','{int(old)}');")
  check('B4 40 days, nothing new since: no nagging', pg.is_visible('#bakNag'), False)
  pg.click('#toggle'); pg.fill('#f-bg','Нов'); pg.click('#savebtn')
  check('B5 40 days and a new record: reminder', (pg.is_visible('#bakNag'),pg.inner_text('#bakNagTxt')), (True,'Последното резервно копие е отпреди 40 дни.'))
  tf='/home/claude/shared-copy.txt'; open(tf,'w',encoding='utf-8').write(json.dumps({'v':4,'obs':[R(id=1,date='2026-05-01',bg='От файла')],'beh':['пее']},ensure_ascii=False))
  pg.set_input_files('#impf',tf); pg.wait_for_timeout(300)
  check('B6 restore accepts the .txt copy the share sheet makes', (pg.evaluate("OBS.map(o=>o.bg)"),len(pg.dialogs)), (['От файла'],1))
  pg.click('#acct');check('B7 share button hidden where the browser cannot share files', pg.is_visible('#shr'), pg.evaluate("canShareFiles"))
  # ---------- arrivals ----------
  Y=T.year
  data=[R(id=1,date=f'{Y-1}-04-28',bg='Пчелояд',la='Merops apiaster'),R(id=2,date=f'{Y}-04-23',bg='Пчелояд',la='Merops apiaster'),
        R(id=3,date=D(3).replace(year=Y-1).isoformat(),bg='Белочела гъска',la='Anser albifrons'),
        R(id=4,date=D(-12).replace(year=Y-1).isoformat(),bg='Голям корморан',la='Phalacrocorax carbo'),
        R(id=5,date=f'{Y-1}-06-01',bg='Червеногърба сврачка',la='Lanius collurio'),
        R(id=6,date=f'{Y-1}-01-05',bg='Кос',la='Turdus merula'),R(id=7,date=f'{Y}-01-03',bg='Кос',la='Turdus merula'),
        R(id=8,date=f'{Y}-03-10',bg='Сврака')]
  pg=page(data); pg.click('.tab[data-v="phen"]'); pg.click('[data-pm="arr"]')   # По месеци is the default view now
  rows=lambda i:pg.evaluate(f"[...document.querySelectorAll('.arr')][{i-1}].querySelectorAll('.ar')",None) and pg.evaluate(f"[...[...document.querySelectorAll('.arr')][{i-1}].querySelectorAll('.ar')].map(e=>[e.querySelector('b').textContent,(e.querySelector('small')||{{}}).textContent||'',e.querySelector(':scope>span').textContent])")
  check('A1 expect soon: overdue first, then upcoming; out-of-window species left out', rows(1),
        [['Голям корморан',f'{Y-1}: '+pg.evaluate(f"sd('{D(-12).replace(year=Y-1).isoformat()}')"),'закъснява с 12 дни'],
         ['Белочела гъска',f'{Y-1}: '+pg.evaluate(f"sd('{D(3).replace(year=Y-1).isoformat()}')"),'след 3 дни']])
  check('A2 first dates this year, in order, compared with last year', rows(2),
        [['Кос',f'2 дни по-рано от {Y-1}','3 яну'],['Сврака','','10 мар'],['Пчелояд',f'5 дни по-рано от {Y-1}','23 апр']])
  pg.click('[data-pm="grid"]'); check('A3 month grid still one click away', pg.locator('table.ph2 tbody tr').count(), 6)
  pg=page([R(id=1,date=T.isoformat(),bg='Сврака')]); pg.click('.tab[data-v="phen"]'); pg.click('[data-pm="arr"]')
  check('A4 first year: explains what "expect soon" will do', 'След първата година' in pg.inner_text('.arr'), True)
  # ---------- install hints, status bar ----------
  pg=page([],**p.devices['iPhone 13'])
  check('I1 iPhone in Safari: empty journal explains Add to Home Screen', 'Добави към началния екран' in pg.inner_text('#view'), True)
  pg=page([])
  check('I2 desktop without an install offer: no hint', pg.inner_text('#inst'), '')
  pg.evaluate("(()=>{const e=new Event('beforeinstallprompt');e.prompt=()=>{window.__prompted=1};e.userChoice=Promise.resolve({outcome:'accepted'});dispatchEvent(e)})()")
  check('I3 Android-style install offer shows a button', pg.locator('[data-inst]').count()>=1, True)
  pg.locator('#inst [data-inst]').click(); pg.wait_for_timeout(200)
  check('I4 button opens the browser install prompt, then goes away', (pg.evaluate("window.__prompted"),pg.inner_text('#inst')), (1,''))
  before=pg.evaluate("document.querySelector('meta[name=theme-color]').content"); pg.click('#acct');pg.click('#theme')
  check('I5 status bar follows the theme toggle', (before,pg.evaluate("document.querySelector('meta[name=theme-color]').content")), ('#f1e9d4','#14160e'))
  check('I6 no page errors', pg.errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
