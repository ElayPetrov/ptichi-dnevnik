# „+ същия вид на ново място“ (2026-11-16.1): under every record, next to „+ друг вид тук“ — a copy of the record, saved at
# once: the same species, but here and now (the outing's fresh GPS point, else the phone's position; a saved place within
# 2 km gives the name); count, note, photo and behaviour stay with the old place; a notice with „↶ Отмени“.
import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
T=datetime.date.today().isoformat();port=int(sys.argv[1]) if len(sys.argv)>1 else 9014;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
R=lambda **k:{**dict(id=0,date='2026-11-01',time='08:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
OBS=[R(id=1,bg='Кос',en='Common blackbird',la='Turdus merula',fam='Дроздове',h=1,s=1,p=1,count='3',note='пееше на покрива',beh=['A1'],place='Копринка',geo='42.62000,25.40000'),
     R(id=2,date='2026-10-20',bg='Сива чапла',la='Ardea cinerea',u=1,alt=['Голяма бяла чапла'],place='Копринка',geo='42.62000,25.40000'),
     R(id=3,date='2026-10-01',bg='Сврака',la='Pica pica',place='Язовира',geo='42.70500,25.50500')]
def session(b,gps=True):
  kw=dict(viewport={'width':390,'height':844})
  if gps:kw.update(geolocation={'latitude':42.70,'longitude':25.50},permissions=['geolocation'])
  ctx=b.new_context(**kw);pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(OBS,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);pg.click('.tab[data-v="log"]');pg.wait_for_timeout(300);return ctx,pg,errs
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  ctx,pg,errs=session(b)
  check('S1 under every record, next to „+ друг вид тук“: „+ същия вид на ново място“', pg.evaluate("[...document.querySelectorAll('.agains')].map(a=>[...a.querySelectorAll('button')].map(x=>x.textContent)).slice(0,1)"), [['+ друг вид тук','+ същия вид на ново място']])
  pg.evaluate("document.querySelectorAll('.o').forEach(x=>{if(x.querySelector('[data-samehere=\"1\"]'))x.dataset.mark=1})")
  pg.click('[data-samehere="1"]');pg.wait_for_timeout(900)
  n=pg.evaluate("OBS.filter(o=>o.la==='Turdus merula').sort((a,b)=>b.id-a.id)[0]")
  check('S2 a copy is saved at once: the same names, group, „чух/видях“ — today, now, at the phone’s position', (len(pg.evaluate("OBS.filter(o=>o.la==='Turdus merula')")),n['bg'],n['en'],n['fam'],n['h'],n['s'],n['date'],n['geo']), (2,'Кос','Common blackbird','Дроздове',1,1,T,'42.70000,25.50000'))
  check('S3 ...count, note, photo, behaviour and „снимах“ stay with the old place', (n['count'],n['note'],n['photo'],n['beh'],n['p']), ('','',None,[],0))
  check('S4 ...named after your saved place within 2 km', n['place'], 'Язовира')
  check('S5 a notice says so, with „↶ Отмени“', (pg.is_visible('#snack'),'„Кос“ - записан и тук (до Язовира).' in pg.inner_text('#snack'),pg.locator('#snack [data-undosame]').count()), (True,True,1))
  pg.click('#snack [data-undosame]');pg.wait_for_timeout(300)
  check('S6 „↶ Отмени“ removes the copy (the original stays)', (len(pg.evaluate("OBS.filter(o=>o.la==='Turdus merula')")),pg.evaluate("OBS.some(o=>o.id===1)"),'Отменено.' in pg.inner_text('#snack')), (1,True,True))
  pg.evaluate("sameHere(2)");pg.wait_for_timeout(900)   # older days are folded in Дневник — the button itself is checked in S1
  c=pg.evaluate("OBS.filter(o=>o.la==='Ardea cinerea').sort((a,b)=>b.id-a.id)[0]")
  check('S7 an unsure record stays unsure in its copy, with its „може да е и“', (c['u'],c.get('alt')), (1,['Голяма бяла чапла']))
  check('S8 no page errors', errs, []);ctx.close()
  ctx,pg,errs=session(b)
  pg.click('#sessStart');pg.wait_for_timeout(300);pg.evaluate("closeForm()")
  pg.evaluate("SESS.trkOn=true;SESS.trk=[[42.55,25.30,Date.now()/1000-30]]")
  pg.evaluate("sameHere(3)");pg.wait_for_timeout(700)
  c=pg.evaluate("OBS.filter(o=>o.la==='Pica pica').sort((a,b)=>b.id-a.id)[0]")
  check('S9 during an outing with the path on, the fresh path point is used (not the phone) and the copy joins the outing', (c['geo'],c.get('sess')==pg.evaluate("SESS.id")), ('42.55000,25.30000',True))
  check('S10 no page errors (outing)', errs, []);ctx.close()
  ctx,pg,errs=session(b,gps=False);pg.click('[data-samehere="1"]');pg.wait_for_timeout(1500)
  check('S11 without a position: nothing is saved, and it says why', (len(pg.evaluate("OBS.filter(o=>o.la==='Turdus merula')")),'Няма местоположение' in pg.inner_text('#snack')), (1,True))
  check('S12 no page errors (no position)', errs, []);ctx.close()
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
