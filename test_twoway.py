# Phone + laptop on one account: the exact situation reported, then edits, deletions, outings, photos and a race.
import json,subprocess,sys,time,re
sys.path.insert(0,'/home/claude')
from sbstack import Stack
from playwright.sync_api import sync_playwright
def rec(pg,sel):   # Дневник shows only the newest day unfolded, so open the record's day before tapping its button
  pg.evaluate("s=>{const b=document.querySelector(s);const g=b&&b.closest('.dayg.shut');if(g)g.querySelector('[data-dayt]').click();}",sel)
  pg.click(sel)
R=lambda **k:{**dict(id=0,date='',time='',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]);fails=0;SB='https://test-proj.supabase.co'
src=open('ptichi-dnevnik.html',encoding='utf-8').read()
open('share-test.html','w',encoding='utf-8').write(re.sub(r"const SB_URL='[^']*'","const SB_URL='"+SB+"'",src))
UMD='/home/claude/sb/package/dist/umd/supabase.js';CDN='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.3/dist/umd/supabase.js'
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
st=Stack('/home/claude/supabase-setup.sql')
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
PHONE=[R(id=1,date='2026-10-20',time='07:10',bg='Сврака',la='Pica pica'),R(id=2,date='2026-10-20',time='07:20',bg='Сойка'),R(id=3,date='2026-10-21',time='08:00',bg='Кос')]
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  def device(data):
    ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();pg.errs=[]
    pg.on('pageerror',lambda e:pg.errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
    ctx.route(SB+'/**',st.handle);ctx.route(CDN,lambda r:r.fulfill(path=UMD,headers={'access-control-allow-origin':'*','content-type':'application/javascript'}))
    pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(data,ensure_ascii=False)))
    pg.goto(f'http://localhost:{port}/share-test.html');pg.wait_for_timeout(300);pg.click('.tab[data-v="friends"]');return pg
  def signin(pg):
    pg.fill('#sb-mail','ivan@test.bg');pg.fill('#sb-pw','птица123');pg.click('[data-sb="in"]');synced(pg)
  def synced(pg): pg.wait_for_function("!syncing&&(sbStat.startsWith('синхронизирано')||sbStat.length>0)",timeout=15000)
  def sync(pg): pg.evaluate("lastSync=0");pg.evaluate("syncNow()");pg.wait_for_timeout(150);synced(pg)
  names=lambda pg:sorted(pg.evaluate("OBS.map(o=>o.bg)"))
  srv_names=lambda:sorted(o['bg'] for o in st.journal(st.uid('ivan@test.bg'))['obs'])
  # account exists; the LAPTOP signs in first, with an empty journal and nothing in the cloud yet
  lap=device([]);lap.fill('#sb-name','Иван');lap.fill('#sb-mail','ivan@test.bg');lap.fill('#sb-pw','птица123');lap.click('[data-sb="up"]');lap.wait_for_selector('.fr .msg')
  st.confirm('ivan@test.bg');lap.click('[data-sb="in"]');synced(lap)
  ph=device(PHONE);signin(ph)
  check('W1 phone signs in after the laptop: its records are in the cloud', srv_names(), ['Кос','Сврака','Сойка'])
  lap.evaluate("document.dispatchEvent(new Event('visibilitychange'))");lap.evaluate("lastSync=0");sync(lap)
  check("W2 the reported bug: laptop now shows the phone's records", names(lap), ['Кос','Сврака','Сойка'])
  check('W3 ...and says where they came from', 'от другото устройство' in lap.evaluate("sbStat"), True)
  # both add a record before syncing
  for pg,nm in ((ph,'Чапла'),(lap,'Щиглец')):
    pg.click('.tab[data-v="log"]');pg.click('#toggle');pg.fill('#f-bg',nm);pg.click('#savebtn')
  ph.wait_for_timeout(5500);sync(lap);sync(ph)
  check('W4 records added on both devices end up on both', (names(ph),names(lap),srv_names()), (['Кос','Сврака','Сойка','Чапла','Щиглец'],)*3)
  # delete on the laptop: must not come back from the phone
  lap.click('.tab[data-v="log"]');rec(lap,f'[data-del="{3}"]');lap.wait_for_timeout(5500);sync(ph);sync(lap)
  check('W5 a record deleted on the laptop disappears on the phone and stays gone', ('Кос' in names(ph),'Кос' in names(lap),'Кос' in srv_names()), (False,False,False))
  # edit on the phone
  ph.click('.tab[data-v="log"]');rec(ph,'[data-ed="1"]');ph.fill('#f-note','на покрива');ph.click('#savebtn');ph.wait_for_timeout(5500);sync(lap)
  check('W6 an edit on the phone reaches the laptop', lap.evaluate("OBS.find(o=>o.id===1).note"), 'на покрива')
  # outings
  ph.click('#sessStart');ph.fill('#f-bg','Скорец');ph.click('#savebtn');ph.click('#sessEnd');ph.click('[data-done="1"]');ph.wait_for_timeout(5500);sync(lap)
  oid=ph.evaluate("OUTS[0].id")
  check('W7 an outing ended on the phone appears on the laptop', lap.evaluate(f"OUTS.some(x=>x.id==='{oid}'&&x.complete===true)"), True)
  lap.click('.tab[data-v="outs"]');lap.locator('.ou').first.click();lap.click('.ou [data-oedit]');lap.click('#od-del');lap.wait_for_timeout(5500);sync(ph)
  check('W8 ...deleted on the laptop, it goes from the phone too; its records stay', (ph.evaluate("OUTS.length"),'Скорец' in names(ph)), (0,True))
  # photos
  ph.click('.tab[data-v="log"]');rec(ph,'[data-ed="2"]');ph.set_input_files('#f-photo','/home/claude/a.jpg');ph.wait_for_function("phNew.length===1");ph.click('#savebtn')
  ph.wait_for_timeout(5500);pid=ph.evaluate("OBS.find(o=>o.id===2).photo");sync(lap)
  check("W9 a photo taken on the phone is pulled onto the laptop", lap.evaluate(f"getPhoto('{pid}').then(b=>!!b)"), True)
  rec(ph,'[data-ed="2"]');ph.click('#rmph');ph.click('#savebtn');ph.wait_for_timeout(5500)
  uid=st.uid('ivan@test.bg');check('W10 removing it on the phone deletes the file from storage', (uid+'/'+pid+'.jpg') in st.files, False)
  # a race: another device writes between this device's download and its upload
  def other_device_writes():
    st.db.cursor().execute("""update public.journals set data=jsonb_set(data,'{obs}',(data->'obs')||'[{"id":999,"date":"2026-10-22","bg":"Бухал","upd":1}]'::jsonb) where user_id=%s""",(uid,))
  st.before_patch=other_device_writes
  ph.click('#toggle');ph.fill('#f-bg','Гугутка');ph.click('#savebtn');ph.wait_for_timeout(6000);synced(ph)
  check('W11 race: the upload notices the other write, merges it and retries — nothing lost', (sorted(set(['Бухал','Гугутка'])&set(names(ph))),sorted(set(['Бухал','Гугутка'])&set(srv_names()))), (['Бухал','Гугутка'],)*2)
  sync(lap);check('W12 everything converges: laptop, phone and cloud agree', (names(lap)==names(ph)==srv_names()), True)
  calls_before=len(st.calls);sync(ph);sync(ph)
  check('W13 nothing new: a sync only checks the timestamp, no re-upload', [c for c in st.calls[calls_before:] if c[0]=='PATCH'], [])
  check('W14 no page errors', ph.errs+lap.errs, [])
  b.close()
finally: srv.terminate();st.stop()
print('FAILURES:',fails)
