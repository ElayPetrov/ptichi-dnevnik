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
    pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(data,ensure_ascii=False)))
    pg.goto(f'http://localhost:{port}/{file}');pg.wait_for_timeout(300)
    if photo: rec(pg,'[data-ed="2"]');pg.set_input_files('#f-photo','/home/claude/a.jpg');pg.wait_for_function("phNew.length===1");pg.click('#savebtn')
    pg.click('#acct');return pg
  def join(pg,name,mail,pw='птица123'):
    pg.fill('#sb-name',name);pg.fill('#sb-mail',mail);pg.fill('#sb-pw',pw);pg.click('[data-sb="up"]');pg.wait_for_selector('.fr .msg')
    msg=pg.inner_text('.fr .msg');st.confirm(mail)
    assert (pg.input_value('#sb-mail'),pg.input_value('#sb-pw'))==(mail,pw), 'form should keep email and password after sign-up'
    pg.click('[data-sb="in"]');pg.wait_for_selector('.fr .code');pg.wait_for_function("sbStat.startsWith('синхронизирано')");return msg
  # ---- Ivan joins ----
  iv=person(IVAN,photo=True)
  check('F1 signing up asks to confirm the address first', join(iv,'Иван','ivan@test.bg').startswith('Готово. Отвори писмото'), True)
  code=iv.evaluate("MYCODE");uI=st.uid('ivan@test.bg')
  check('F2 signed in: name, a 12-character code shown in groups, synced', (iv.evaluate("[...document.querySelectorAll('.fr h3')].find(h=>h.textContent==='Ти').nextElementSibling.querySelector('b').textContent").strip(),len(code),iv.inner_text('.fr .code')), ('Иван',12,'-'.join([code[:4],code[4:8],code[8:]])))
  j=st.journal(uI);check('F3 his journal is in the cloud copy, with all records and outings', (len(j['obs']),j['v'],'outs' in j), (4,6,True))
  ph=iv.evaluate("OBS.find(o=>o.id===2).photo");check('F4 ...and his photo is uploaded into his own folder', (uI+'/'+ph+'.jpg') in st.files, True)
  check('F5 footer now says who can see the records', 'само хората, на които си дал кода си' in iv.inner_text('#priv'), True)
  # ---- Petar joins, follows Ivan ----
  pe=person(PETAR);join(pe,'Петър','petar@test.bg')
  pe.fill('#fr-code',code.lower()[:6]+'-'+code[6:]);pe.click('[data-sb="add"]');pe.wait_for_selector('.fr .ar.tap')
  check('F6 Petar adds Ivan by code: Ivan appears with his sure species', pe.inner_text('.fr .ar.tap b'), 'Иван')
  check('F7 ...counted like the life list (unsure records left out)', pe.inner_text('.fr .ar.tap small').startswith('3 вида · 3 записа'), True)
  pe.click('.fr .ar.tap');pe.wait_for_selector('.cmp')
  check('F8 comparison: shared / only Petar / only Ivan, matched by any shared name', pe.eval_on_selector_all('.cmp b',"e=>e.map(x=>x.textContent)"), ['2','1','1'])
  check('F9 ...and the lists behind the numbers', pe.eval_on_selector_all('.chips',"e=>e.map(x=>x.innerText.replace(/\\n/g,', '))"), ['Пчелояд','Кос'])
  pe.wait_for_selector('[data-fph] img',timeout=5000)
  check("F10 Ivan's photo loads for Petar", pe.locator('[data-fph] img').count(), 1)
  pe.fill('#q','') ; pe.click('[data-frback]')
  pe.click('#acct')   # back to the account view (a friend's journal opens in Приятели)
  pe.fill('#fr-code','NOPE-NOPE-NOPE');pe.click('[data-sb="add"]');pe.wait_for_selector('.fr .msg')
  check('F11 a wrong code is refused politely', pe.inner_text('.fr .msg'), 'Няма такъв код.')
  pe.fill('#fr-code',pe.evaluate("MYCODE"));pe.click('[data-sb="add"]');pe.wait_for_timeout(500)
  check('F12 your own code too', pe.inner_text('.fr .msg'), 'Това е твоят код.')
  iv.click('[data-sb="refresh"]');iv.wait_for_selector('[data-unfan]')
  check('F13 Ivan sees that Petar can view his journal', iv.locator('[data-unfan]').locator('xpath=../..').inner_text().split('\n')[0], 'Петър')
  # ---- Ivan adds a record: it reaches Petar ----
  iv.click('.tab[data-v="log"]');iv.click('#toggle');iv.fill('#f-bg','Червеногръдка');iv.click('#savebtn');iv.wait_for_timeout(5500)
  check('F14 a new record is uploaded a few seconds after saving', len(st.journal(uI)['obs']), 5)
  pe.click('[data-sb="refresh"]');pe.wait_for_timeout(800)
  check('F15 ...and Petar sees it after Обнови', pe.inner_text('.fr .ar.tap small').startswith('4 вида · 4 записа'), True)
  # ---- Petar offline: last download still readable ----
  # the test page has no offline worker, so emulate a fresh start with the network gone instead of reloading
  pe.ctx.unroute(SB+'/**');pe.ctx.unroute(CDN);pe.ctx.route(SB+'/**',lambda r:r.abort('internetdisconnected'));pe.ctx.route(CDN,lambda r:r.abort('internetdisconnected'))
  pe.evaluate("SB=null;sbP=null;ME=null;sbTried=false;FR=null;fsel=null;document.querySelectorAll('script[src*=supabase]').forEach(s=>s.remove());delete window.supabase;view='acct';render()")
  pe.wait_for_function("document.querySelector('.fr h3')&&document.querySelector('.fr h3').textContent==='Без връзка'",timeout=5000)
  check("F16 offline: Ivan's journal is still there from the last download", (pe.locator('.fr .ar.tap').count(),pe.inner_text('.fr h3')), (1,'Без връзка'))
  pe.click('.fr .ar.tap');check('F17 ...and opens', pe.locator('.cmp').count(), 1)
  pe.ctx.unroute(SB+'/**');pe.ctx.unroute(CDN);pe.ctx.route(SB+'/**',st.handle);pe.ctx.route(CDN,lambda r:r.fulfill(path=UMD,headers={'access-control-allow-origin':'*','content-type':'application/javascript'}))
  # ---- Ivan on a second phone with an empty journal ----
  i2=person([]);i2.fill('#sb-mail','ivan@test.bg');i2.fill('#sb-pw','птица123');i2.click('[data-sb="in"]')
  i2.wait_for_function("sbStat.startsWith('синхронизирано')")
  check('F18 second phone: signing in brings his journal down, cloud copy intact', (i2.evaluate("OBS.length"),len(st.journal(uI)['obs'])), (5,5))
  i2.wait_for_function(f"getPhoto({json.dumps(ph)}).then(b=>!!b)",timeout=5000)
  check('F19 ...including his photo', True, True)
  # ---- Ivan removes Petar ----
  iv.click('#acct');iv.wait_for_selector('[data-unfan]');iv.click('[data-unfan]');iv.wait_for_timeout(800)
  pe.reload();pe.wait_for_timeout(500);pe.click('#acct');pe.wait_for_selector('.fr h3');pe.wait_for_timeout(1500)
  check('F20 after Ivan removes him, Petar no longer sees the journal', pe.locator('.fr .ar.tap').count(), 0)
  iv.click('[data-sb="out"]');iv.wait_for_selector('#sb-mail')
  check('F21 signing out keeps the journal on the phone and restores the footer', (iv.evaluate("OBS.length"),iv.inner_text('#priv').startswith('Записите се пазят в този браузър')), (5,True))
  iv.fill('#sb-mail','ivan@test.bg');iv.fill('#sb-pw','грешна');iv.click('[data-sb="in"]');iv.wait_for_selector('.fr .msg')
  check('F22 wrong password says so', iv.inner_text('.fr .msg'), 'Грешен имейл или парола.')
  nc=person([],file='noconf-test.html')
  check('F23 the build without a project address just says sharing is not set up', 'Споделянето още не е настроено.' in nc.inner_text('#view'), True)
  check('F24 no page errors anywhere', iv.errs+pe.errs+i2.errs+nc.errs, [])
  b.close()
finally: srv.terminate();st.stop()
print('FAILURES:',fails)
