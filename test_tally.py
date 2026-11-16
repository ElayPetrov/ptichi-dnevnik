# Counting on the go in the active outing (2026-11-16.1): under each record in the outing's list, −1 / +1 / +10 / +100;
# the count changes in place (kind kept: „около“ stays „около“), never below 0, saved and marked as edited; the form
# doesn't open, the list stays open; Дневник shows the new count once you stop tapping; it survives a reload.
import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
T=datetime.date.today().isoformat();port=int(sys.argv[1]) if len(sys.argv)>1 else 9013;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}")
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  pg.click('#sessStart');pg.wait_for_timeout(300)
  pg.evaluate("""(()=>{const R=(id,bg,la,count,cq,t)=>({id,date:today(),time:t,place:'',count,cq,bg,en:'',la,fam:'',note:'',h:0,s:1,p:0,beh:[],geo:null,photo:null,sess:SESS.id});
    OBS.push(R(101,'Кос','Turdus merula','','exact','08:10'),R(102,'Сврака','Pica pica','около 20','est','08:20'));save();render();sessUI();})()""")
  pg.evaluate("closeForm()")   # starting an outing opens the form for its first record — close it, then see that the taps don't reopen it
  if not pg.evaluate("document.getElementById('sess').classList.contains('open')"):pg.click('#sessTxt')
  pg.wait_for_timeout(300)
  num=lambda i:pg.inner_text(f'#sessList .ssr:has([data-tal="{i}"]) .sstal b')
  check('C1 every record in the outing’s list has −1 / +1 / +10 / +100 next to its count', (pg.evaluate("[...document.querySelectorAll('#sessList .ssr:first-child .sstal button')].map(b=>b.textContent)"),num(101),num(102)), (['−1','+1','+10','+100'],'0','~20'))
  pg.click('#sessList [data-tal="101"][data-d="1"]');pg.click('#sessList [data-tal="101"][data-d="10"]');pg.click('#sessList [data-tal="101"][data-d="100"]');pg.click('#sessList [data-tal="101"][data-d="-1"]');pg.wait_for_timeout(150)
  check('C2 the taps add up in place: +1 +10 +100 −1 = 110', (num(101),pg.evaluate("OBS.find(o=>o.id===101).count")), ('110','110'))
  check('C3 ...the record is marked as changed (for syncing) and saved', (pg.evaluate("OBS.find(o=>o.id===101).upd>0"),pg.evaluate("JSON.parse(KVC[K]).find(o=>o.id===101).count")), (True,'110'))
  check('C4 the form doesn’t open and the outing’s list stays open', (pg.evaluate("document.getElementById('form').classList.contains('on')"),pg.evaluate("document.getElementById('sess').classList.contains('open')")), (False,True))
  pg.click('#sessList [data-tal="102"][data-d="1"]');pg.wait_for_timeout(150)
  check('C5 an „около 20“ count stays „около“: 21', (num(102),pg.evaluate("cntText(OBS.find(o=>o.id===102))")), ('~21','около 21'))
  for _ in range(3):pg.click('#sessList [data-tal="102"][data-d="-1"]')
  pg.evaluate("OBS.find(o=>o.id===102).count='1'");pg.evaluate("document.getElementById('sessList').innerHTML=sessListHTML()");pg.click('#sessList [data-tal="102"][data-d="-1"]');pg.click('#sessList [data-tal="102"][data-d="-1"]');pg.wait_for_timeout(150)
  check('C6 never below zero — at 0 the count is simply empty', (num(102),pg.evaluate("OBS.find(o=>o.id===102).count")), ('0',''))
  pg.click('#sessList [data-tal="102"][data-d="10"]');pg.wait_for_timeout(1000)
  check('C7 once you stop tapping, Дневник shows the new counts too', pg.evaluate("[...document.querySelectorAll('.o')].map(x=>x.innerText).join(' | ')").count('110')>=1, True)
  pg.reload();pg.wait_for_timeout(500)
  check('C8 the counts survive a reload', pg.evaluate("[OBS.find(o=>o.id===101).count,OBS.find(o=>o.id===102).count]"), ['110','10'])
  check('C9 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
