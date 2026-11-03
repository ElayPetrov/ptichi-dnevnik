# Release C, part 1 — „Попитай приятелите“: ask from the form, friends see it at the top of Приятели and suggest a species,
# you accept one (the record takes its names and becomes sure), the suggester earns „Определител“.
import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
T=datetime.date.today().isoformat()
port=int(sys.argv[1]) if len(sys.argv)>1 else 8997;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
friendAsk={'id':501,'date':T,'time':'09:10','place':'Копринка','count':'','bg':'Сива овесарка','en':'','la':'','fam':'','note':'Пееше от жицата, сива и дебелоклюна.','h':1,'s':1,'p':0,'u':1,'alt':['Жълта овесарка'],'beh':[],'geo':None,'photo':None,'ask':1}
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});ctx.route('https://**',lambda r:r.abort() if 'localhost' not in r.request.url else r.continue_())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true')")
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  pg.click('#toggle');pg.click('#f-unsure');pg.wait_for_timeout(80)
  check('A1 signed out: „Попитай приятелите“ shows under „не съм сигурен“, disabled, saying a profile is needed', (pg.is_visible('#f-askrow'),pg.is_disabled('#f-ask'),pg.inner_text('#f-askhint')), (True,True,'Нужен е профил, за да питаш приятелите.'))
  pg.click('#cancel')
  # signed in, with a friend; posting goes into SOC directly (no network in this test)
  pg.evaluate("""ME={id:'me',email:'i@t.bg'};MYNAME='Иван';FR={fol:[{id:'u2',name:'Петър',data:{obs:[%s],outs:[]},updated_at:'2026-11-03T08:00:00Z'}],fans:[{id:'u2',name:'Петър'}]};SOC=[];SOCN['u2']='Петър';
    socAdd=async(owner,item,kind,body)=>{SOC.push({id:'s'+SOC.length,owner,item,author:ME.id,kind,body,created_at:new Date().toISOString()});render();};render();"""%json.dumps(friendAsk,ensure_ascii=False))
  pg.click('#toggle');pg.click('#f-unsure');pg.wait_for_timeout(80)
  check('A2 signed in: the box is enabled', pg.is_disabled('#f-ask'), False)
  pg.check('#f-ask');pg.click('#savebtn');pg.wait_for_timeout(200)
  me=pg.evaluate("(o=>[o.bg,o.u,!!o.ask])(OBS[OBS.length-1])")
  check('A3 an unnamed bird you ask about saves as „Непозната птица“, unsure, asking', me, ['Непозната птица',1,True])
  pg.click('#cancel') if pg.is_visible('#cancel') else None
  pg.click('.tab[data-v="log"]');pg.wait_for_timeout(150)
  check('A4 your record shows „🔎 питаш приятелите“', pg.locator('[data-qown]').first.inner_text(), '🔎 питаш приятелите')
  pg.click('.tab[data-v="friends"]');pg.wait_for_timeout(200)
  check('A5 Приятели: Петър’s question at the top, with his guess, note and „Още няма предложения“, and a dot on the tab', (pg.inner_text('.askc b'),'Мисли, че може да е Сива овесарка или Жълта овесарка' in pg.inner_text('.askc'),'Пееше от жицата' in pg.inner_text('.askc'),'Още няма предложения.' in pg.inner_text('.askc'),pg.evaluate("pendingSocial()")), ('Петър пита: какво е това?',True,True,True,1))
  pg.click('[data-qprop]');pg.wait_for_timeout(100);pg.fill('#id-bg','Сива овесарка');pg.wait_for_timeout(80)
  check('A6 the suggestion dialog looks the name up as you type', pg.inner_text('#id-la'), 'Emberiza calandra · Corn bunting')
  pg.fill('#id-cm','Дебел клюн и песен като ключове.');pg.click('#id-ok');pg.wait_for_timeout(150)
  check('A7 the suggestion is posted on the question, as readable text', pg.evaluate("SOC.map(s=>[s.owner,s.item,s.kind,s.body])"), [['u2','q:501','comment','🔎 Сива овесарка (Emberiza calandra)\nДебел клюн и песен като ключове.']])
  check('A8 ...it shows on the card, the button now offers another, and the dot goes', (pg.inner_text('.askc .qchip b'),pg.inner_text('[data-qprop]'),pg.evaluate("pendingSocial()")), ('Сива овесарка','Предложи друг вид',0))
  # the owner's side: Петър suggests a species for my question; I accept it
  my=pg.evaluate("OBS[OBS.length-1].id")
  pg.evaluate(f"SOC.push({{id:'x1',owner:'me',item:'q:{my}',author:'u2',kind:'comment',body:'🔎 Червеногръдка (Erithacus rubecula)\\nоранжевите гърди',created_at:new Date().toISOString()}});render()")
  pg.click('.tab[data-v="log"]');pg.wait_for_timeout(150)
  check('A9 your tag counts the suggestions', pg.locator('[data-qown]').first.inner_text(), '🔎 питаш приятелите · 1 предложение')
  pg.locator('[data-qown]').first.click();pg.wait_for_timeout(100)
  check('A10 the question lists each suggestion: who, the name, why', ('Червеногръдка' in pg.inner_text('#q-list'),'Петър' in pg.inner_text('#q-list'),'оранжевите гърди' in pg.inner_text('#q-list')), (True,True,True))
  pg.click('[data-qok="0"]');pg.wait_for_timeout(150)
  check('A11 accepting gives the record the species’ names and makes it sure, crediting Петър', pg.evaluate(f"(o=>[o.bg,o.la,o.en,o.fam,o.u,o.askOk.by])(OBS.find(o=>o.id==={my}))"), ['Червеногръдка','Erithacus rubecula','European robin','Славеи, червеноопашки, каменарчета',0,'u2'])
  check('A12 ...and the record says „✓ определено от Петър“', pg.locator('.asktag.ok').first.inner_text(), '✓ определено от Петър')
  pg.evaluate("FR.fol[0].data.obs[0].askOk={by:'me',at:Date.now(),was:'Сива овесарка'}")
  check('A13 „Определител“: your suggestions that friends accepted', pg.evaluate("BDEF.find(d=>d.id==='idhelp').v(SURE())"), 1)
  pg.click('.tab[data-v="friends"]');pg.wait_for_timeout(150)
  check('A14 an answered question leaves „Помогни с определянето“', pg.locator('.askc').count(), 0)
  pg.evaluate("OBS.push({id:777,date:'%s',time:'',place:'',count:'',bg:'Непозната птица',en:'',la:'',fam:'',note:'',h:1,s:0,p:0,u:1,beh:[],ask:5});save();render()"%T)
  pg.click('.tab[data-v="log"]');pg.wait_for_timeout(100);pg.click('[data-qown="777"]');pg.wait_for_timeout(80);pg.click('#q-close');pg.wait_for_timeout(100)
  check('A15 closing a question without an answer keeps the record, unsure, no longer asking', pg.evaluate("(o=>[!!o,o.u,'ask' in o])(OBS.find(o=>o.id===777))"), [True,1,False])
  check('A16 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
