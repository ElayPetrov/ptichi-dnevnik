import json,subprocess,sys,time
sys.path.insert(0,'/home/claude')
from sbstack import Stack
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='',time='',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]);fails=0;SB='https://test-proj.supabase.co'
import re
def rec(pg,sel):   # Дневник unfolds only the newest day (and month, year), so open the record's ones before tapping its button
  pg.evaluate("s=>{const b=document.querySelector(s);if(!b)return;for(const g of [b.closest('.yg.shut'),b.closest('.mg.shut'),b.closest('.dayg.shut')])if(g)g.querySelector(':scope>[data-ymt],:scope>[data-dayt]').click();}",sel)
  pg.click(sel)
src=open('ptichi-dnevnik.html',encoding='utf-8').read();assert len(re.findall(r"const SB_URL='[^']*'",src))==1
open('share-test.html','w',encoding='utf-8').write(re.sub(r"const SB_URL='[^']*'","const SB_URL='"+SB+"'",src))
open('noconf-test.html','w',encoding='utf-8').write(re.sub(r"const SB_URL='[^']*'","const SB_URL=''",src))
UMD='/home/claude/sb/package/dist/umd/supabase.js';CDN='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.3/dist/umd/supabase.js'
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
st=Stack('/home/claude/supabase-setup.sql')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
IVAN=[R(id=1,date='2026-05-01',bg='Сврака',la='Pica pica',place='Розариум'),R(id=2,date='2026-05-02',bg='Пчелояд',la='Merops apiaster',place='Копринка',p=1),
      R(id=3,date='2026-06-01',bg='Сойка',place='Розариум'),R(id=4,date='2026-06-02',bg='Белоглав лешояд',u=1)]
PETAR=[R(id=11,date='2026-04-01',bg='Сврака',la='Pica pica'),R(id=12,date='2026-04-02',bg='Кос',la='Turdus merula'),R(id=13,date='2025-08-01',en='Eurasian Jay',la='Garrulus glandarius',bg='Сойка')]
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  def person(data,photo=False,file='share-test.html'):
    ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();pg.errs=[];pg.ctx=ctx
    pg.on('pageerror',lambda e:pg.errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
    ctx.route(SB+'/**',st.handle);ctx.route(CDN,lambda r:r.fulfill(path=UMD,headers={'access-control-allow-origin':'*','content-type':'application/javascript'}))
    pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(data,ensure_ascii=False)))
    pg.goto(f'http://localhost:{port}/{file}');pg.wait_for_timeout(300)
    if photo: rec(pg,'[data-ed="2"]');pg.set_input_files('#f-photo','/home/claude/a.jpg');pg.wait_for_function("phNew.length===1");pg.click('#savebtn')
    pg.click('#acct');return pg
  def join(pg,name,mail,pw='птица123'):
    pg.fill('#sb-name',name);pg.fill('#sb-mail',mail);pg.fill('#sb-pw',pw);pg.click('[data-sb="up"]');pg.wait_for_selector('.fr .msg')
    msg=pg.inner_text('.fr .msg');st.confirm(mail)
    assert (pg.input_value('#sb-mail'),pg.input_value('#sb-pw'))==(mail,pw), 'form should keep email and password after sign-up'
    pg.click('[data-sb="in"]');pg.wait_for_selector('.fr .code');pg.wait_for_function("sbStat.startsWith('синхронизирано')");return msg
  D='2026-10-27'
  IV=[R(id=1,date=D,time='08:10',bg='Сврака',la='Pica pica',place='Копринка',sess='sX',geo='42.63,25.32'),
      R(id=2,date=D,time='08:40',bg='Сойка',place='Копринка',sess='sX',geo='42.632,25.324'),R(id=3,date=D,time='09:00',bg='Кос',place='Копринка',sess='sX')]
  PE=[R(id=21,date='2026-10-28',time='10:00',bg='Чинка',place='Розариум'),R(id=22,date='2026-10-28',time='10:20',bg='Щиглец',place='Розариум')]
  MA=[R(id=31,date='2026-10-26',time='11:00',bg='Гугутка')]
  iv=person(IV);join(iv,'Иван','ivan@test.bg');ivc=iv.evaluate("MYCODE")
  pe=person(PE);join(pe,'Петър','petar@test.bg');pec=pe.evaluate("MYCODE")
  ma=person(MA);join(ma,'Мария','maria@test.bg')
  def follow(pg,code):pg.fill('#fr-code',code);pg.click('[data-sb="add"]');pg.wait_for_timeout(700)
  follow(pe,ivc);follow(iv,pec);follow(ma,ivc)   # Ivan and Petar follow each other; Maria follows only Ivan
  def fresh(*pgs):
    for pg in pgs:pg.evaluate("syncNow()")
    for pg in pgs:pg.evaluate("loadFriends()")
  fresh(iv,pe,ma)
  check('X1 Приятели is the second tab', pe.evaluate("[...document.querySelectorAll('.tab')].map(t=>t.textContent)")[:2], ['Дневник','Приятели'])
  feed=lambda pg:(pg.click('.tab[data-v="friends"]'),pg.wait_for_timeout(250))
  for pg in (iv,pe,ma):feed(pg);pg.click('.tab[data-v="log"]')   # look once, so everything so far counts as seen and cards keep date order
  feed(pe);cards=pe.evaluate("[...document.querySelectorAll('.fc')].map(c=>c.querySelector('.fchn b').textContent+' | '+c.querySelector('.fchn small').textContent)")
  check('X2 the feed: newest first, your own day and Ivan\'s outing', cards, ['Ти | 28 октомври 2026 · 10:00–10:20 · Розариум','Иван | излет · 27 октомври 2026 · 08:10–09:00 · Копринка'])
  ivcard='.fc:nth-of-type(2)'
  c=pe.evaluate(f"(()=>{{const c=document.querySelectorAll('.fc')[1];return [c.querySelector('.fcn').textContent,c.querySelector('.fhl').innerText,c.querySelectorAll('.sl span').length,c.querySelectorAll('.oumap i').length];}})()")
  check('X3 Ivan\'s card: counts, „3 нови вида за Иван“, the species as chips, a little map with its two points', c, ['3 вида · 3 записа','3 нови вида за Иван: Сврака, Сойка, Кос',3,2])
  pe.locator('.fc').nth(1).locator('.fcn').click();pe.wait_for_timeout(200)
  check('X4 tapping opens its records, read-only (no edit or delete)', (pe.locator('.fc .fcr .o').count(),pe.locator('.fc .fcr [data-ed],.fc .fcr [data-del]').count()), (3,0))
  pe.locator('.fc').nth(1).locator('[data-bravo]').click();pe.wait_for_timeout(700)
  check('X5 „Браво“ from Petar', pe.locator('.fc').nth(1).locator('[data-bravo]').inner_text(), 'Браво · 1')
  pe.locator('.fc').nth(1).locator('[data-cm]').click();pe.wait_for_timeout(150);pe.locator('.fc').nth(1).locator('.cmn input').fill('Страхотен излет!');pe.locator('.fc').nth(1).locator('[data-cmsend]').click();pe.wait_for_timeout(700)
  fresh(iv);feed(iv);ivown=iv.locator('.fc.me').first
  ivown.locator('[data-cm]').click();iv.wait_for_timeout(150)
  check('X6 Ivan sees the „Браво“ and the comment on his own outing', (iv.locator('.fc.me .sbn').first.inner_text(),iv.locator('.fc.me .cmr').first.inner_text().replace('\n',' ').replace('×','').strip()), ('Браво от Петър','Петър Страхотен излет!'))
  fresh(ma);feed(ma)
  check('X7 Maria (who sees only Ivan) sees his card with Petar\'s „Браво“, and no cards of Petar', (ma.evaluate("[...document.querySelectorAll('.fc .fchn b')].map(b=>b.textContent)"),'Браво от Петър' in ma.inner_text('#view')), (['Иван','Ти'],True))   # Ivan's outing (27 Oct) is newer than Maria's record (26 Oct)
  pid=pe.evaluate("ME.id")
  bad=ma.evaluate(f"SB.from('social').insert({{owner:'{pid}',item:'d:2026-10-28',kind:'bravo'}}).then(r=>!!r.error)")
  check('X8 the database refuses a reaction from someone who can\'t see that journal', bad, True)
  cid=iv.evaluate("SOC.find(s=>s.kind==='comment').id");ma.evaluate(f"SB.from('social').delete().eq('id','{cid}')");fresh(iv)
  check('X9 ...and someone else\'s comment can\'t be deleted by a third person', iv.evaluate("SOC.some(s=>s.kind==='comment')"), True)
  feed(pe);pe.locator('.fc').nth(1).locator('[data-there]').click();pe.wait_for_timeout(700)
  check('X10 „Бях там“ asks Ivan first', pe.locator('.fc').nth(1).locator('.soc .sbn').inner_text(), '„Бях там“ — чака Иван')
  fresh(iv);feed(iv)
  check('X11 Ivan sees the request on his outing (and a dot on Приятели)', (iv.locator('.fc.me .sreq span').first.inner_text(),iv.evaluate("document.querySelector('.tab[data-v=\"friends\"]').classList.contains('dot')")), ('Петър казва, че е бил(а) на този излет',True))
  iv.locator('.fc.me [data-thok]').click();iv.wait_for_timeout(700);iv.evaluate("syncNow()")
  fresh(pe);feed(pe);pe.click('.invb [data-inv]');pe.wait_for_selector('#imp-list input');pe.click('#imp-ok');pe.wait_for_timeout(400);fresh(pe,iv);feed(iv);feed(pe)
  check('X12 once Ivan accepts, Petar copies the outing and both cards compare it',
    (iv.locator('.fc.me .fcmp').first.inner_text(),pe.evaluate("[...document.querySelectorAll('.fc .fcmp')].map(x=>x.innerText)").count('Общ излет с Иван: и двамата 3 · само ти 0 · само Иван 0')),
    ('Общ излет с Петър: и двамата 3 · само ти 0 · само Петър 0',1))
  iv.click('#acct');iv.wait_for_timeout(200);acc='Твоят код' in iv.inner_text('#view');iv.click('[data-acctback]');iv.wait_for_timeout(200)
  check('X13 the round button opens the profile and friends; „назад“ returns', (acc,iv.evaluate("view")), (True,'friends'))
  import urllib.parse
  reqs=[];pe.on('request',lambda r:reqs.append(urllib.parse.unquote(r.url)) if '/rest/v1/journals' in r.url else None)
  full=lambda:[u for u in reqs if 'select=' in u and 'data' in u.split('select=')[1].split('&')[0]]
  pdot=lambda:pe.evaluate("document.querySelector('.tab[data-v=friends]').classList.contains('dot')")
  pe.click('.tab[data-v="map"]');pe.wait_for_timeout(200);reqs.clear();pe.evaluate("friendsTick()");pe.wait_for_timeout(900)
  check('X15 nothing new: the 2-minute refresh only checks dates (no journal downloaded again), no dot', (len(full()),pdot()), (0,False))
  iv.evaluate("OBS.push({id:Date.now(),date:'2026-10-28',time:'12:30',place:'Копринка',count:'',bg:'Червеношийка',en:'',la:'',fam:'',note:'',h:0,s:1,p:0,beh:[],geo:null,photo:null,upd:Date.now()});save()");iv.evaluate("syncNow()")
  reqs.clear();pe.evaluate("friendsTick()");pe.wait_for_timeout(900)
  check('X16 Ivan logs a bird: the next refresh downloads just his journal and lights the dot, even on Карта', (len(full()),pdot(),pe.evaluate("view")), (1,True,'map'))
  check('X14 no page errors', iv.errs+pe.errs+ma.errs, [])
  b.close()
finally: srv.terminate();st.stop()
print('FAILURES:',fails)
