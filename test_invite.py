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
  D='2026-10-25'
  IV=[R(id=1,date=D,time='08:10',bg='Сврака',la='Pica pica',place='Копринка',sess='sX',note='моя бележка',p=1,s=0),
      R(id=2,date=D,time='08:30',bg='Сойка',place='Копринка',sess='sX',geo='42.63,25.32'),
      R(id=3,date=D,time='08:50',bg='Мишелов',place='Копринка',sess='sX',u=1),R(id=4,date=D,time='09:10',bg='Кос',place='Копринка',sess='sX')]
  PE=[R(id=21,date=D,time='08:40',bg='Кос',la='Turdus merula')]   # Petar logged the blackbird himself that day
  iv=person(IV);join(iv,'Иван','ivan@test.bg');code=iv.evaluate("MYCODE")
  pe=person(PE);join(pe,'Петър','petar@test.bg');pe.fill('#fr-code',code);pe.click('[data-sb="add"]');pe.wait_for_selector('.fr .ar.tap')
  pid=pe.evaluate("ME.id");iv.evaluate("loadFriends()")
  def invite(pg):
    pg.click('.tab[data-v="outs"]');pg.wait_for_timeout(150)
    if not pg.locator('.ou .orl').count(): pg.locator('.ou').first.click()
    pg.click('.ou [data-oinv]');pg.wait_for_selector('#inv-list input');pg.check('#inv-list input');pg.click('#inv-ok');pg.evaluate("syncNow()")
  invite(iv)
  j=st.journal(iv.evaluate("ME.id"));o=[x for x in j['outs'] if x['id']=='sX'][0]
  check('I1 Ivan invites Petar from the outing card; the invitation travels in his journal', pid in (o.get('inv') or {}), True)
  pe.evaluate("loadFriends()");pe.click('.tab[data-v="log"]');pe.wait_for_timeout(200)
  check('I2 Petar sees the invitation atop Дневник', pe.inner_text('.invb span'), 'Иван те покани в излета си от 25 октомври 2026 · Копринка · 3 вида')
  pe.click('.invb [data-inv]');pe.wait_for_selector('#imp-list input')
  rows=pe.evaluate("[...document.querySelectorAll('#imp-list .impr')].map(l=>[l.querySelector('b').textContent,l.querySelector('input').checked,!!l.querySelector('small')])")
  check('I3 the checklist: all ticked, except the blackbird he already has that day', rows, [['Сврака',True,False],['Сойка',True,False],['Мишелов ?',True,False],['Кос',False,True]])
  pe.uncheck('#imp-list .impr:nth-child(2) input');pe.click('#imp-ok');pe.wait_for_timeout(300)
  got=pe.evaluate("(()=>{const o=OUTS.find(y=>y.with==='Иван');const rs=OBS.filter(r=>r.sess===o.id).map(r=>[r.bg,r.s,r.p,r.u,r.note,r.photo]).sort();return [o.orig.o,o.start,o.end,rs];})()")
  check('I4 accepting copies the ticked birds into his own outing „с Иван“: no photo, no note, no „снимах“', got, ['sX','08:10','09:10',[['Мишелов',1,0,1,'',None],['Сврака',1,0,0,'',None]]])   # Ivan's outing times (here from his first and last record)
  check('I5 one summary card instead of many pop-ups', pe.evaluate("document.getElementById('yay').innerText.includes('Добавен излет с Иван')"), True)
  pe.evaluate("syncNow()")
  check('I6 the invitation is gone, and his answer is in his journal for his other devices', (pe.locator('.invb').count(),list(st.journal(pid).get('ans',{}).values())[0]['a']), (0,'a'))
  check('I7 his Дневник shows the outing „с Иван“', 'с Иван' in pe.inner_text('.og .ogt'), True)
  iv.evaluate("(()=>{const o=OBS.find(r=>r.id===1);o.count='5';o.upd=Date.now();save();})()");iv.evaluate("syncNow()");pe.evaluate("loadFriends()")
  check('I8 Ivan changing his record later changes nothing on Petar\'s side', pe.evaluate("OBS.find(r=>r.bg==='Сврака').count"), '')
  iv.evaluate(f"(()=>{{OBS.push({{id:9,date:'{D}',time:'09:20',place:'Копринка',count:'',bg:'Чинка',en:'',la:'',fam:'',note:'',h:0,s:1,p:0,beh:[],geo:null,photo:null,sess:'sX',upd:Date.now()}});save();}})()")
  invite(iv);pe.evaluate("loadFriends()");pe.wait_for_timeout(200);pe.click('.invb [data-inv]');pe.wait_for_selector('#imp-list input')
  rows=pe.evaluate("[...document.querySelectorAll('#imp-list .impr b')].map(b=>b.textContent)")
  check('I9 invited again (after a forgotten bird): only what he hasn\'t copied is listed', rows, ['Сойка','Кос','Чинка'])
  pe.uncheck('#imp-list .impr:nth-child(1) input');pe.click('#imp-ok');pe.wait_for_timeout(300)
  check('I10 ...and the new bird joins the same outing', pe.evaluate("(()=>{const o=OUTS.filter(y=>y.with==='Иван');return [o.length,OBS.filter(r=>r.sess===o[0].id).length];})()"), [1,3])
  invite(iv);pe.evaluate("loadFriends()");pe.wait_for_timeout(200);pe.click('.invb [data-inv]');pe.click('#imp-no');pe.wait_for_timeout(200)
  check('I11 declining removes the invitation', (pe.locator('.invb').count(),pe.evaluate("Object.values(ANS).some(a=>a.a==='d')")), (0,True))
  lone=b.new_page();lone.on('pageerror',lambda e:iv.errs.append(str(e)));lone.add_init_script("localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(IV,ensure_ascii=False)))
  lone.goto(f'http://localhost:{port}/ptichi-dnevnik.html');lone.wait_for_timeout(300);lone.click('.tab[data-v="outs"]');lone.locator('.ou').first.click();lone.click('.ou [data-oinv]')
  check('I12 not signed in: the invite explains what is needed', lone.inner_text('#inv-note'), 'Влез в „Приятели“, за да каниш приятели в излетите си.')
  check('I13 no page errors', iv.errs+pe.errs, [])
  b.close()
finally: srv.terminate();st.stop()
print('FAILURES:',fails)
