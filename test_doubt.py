# „Несигурни“ filter in Дневник (2026-11-11.1): records with „?“, only to group („sp.“) or asked friends and not yet
# answered; a line saying how many of each; an honest empty message; „по видове“ lists them by name with counts.
import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
T=datetime.date.today().isoformat();port=int(sys.argv[1]) if len(sys.argv)>1 else 9010;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
R=lambda **k:{**dict(id=0,date=T,time='08:00',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
OBS=[R(id=1,time='08:00',bg='Кос',la='Turdus merula'),
     R(id=2,time='08:10',bg='Сива чапла',la='Ardea cinerea',u=1,alt=['Голяма бяла чапла']),
     R(id=3,time='08:20',bg='чайка sp.',la='Larus sp.'),
     R(id=4,time='08:30',bg='Горска зидарка',la='Sitta europaea',u=1,ask=1),
     R(id=5,time='08:40',bg='Сойка',la='Garrulus glandarius',ask=1,askOk={'by':'x','at':T})]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(OBS,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(500);pg.click('.tab[data-v="log"]');pg.wait_for_timeout(300)
  check('D1 a „Несигурни“ chip, after „Годишен списък“', pg.evaluate("[...document.querySelectorAll('#filters [data-f]')].map(b=>b.dataset.f)"), ['all','h','s','p','ylist','q'])
  names=lambda:pg.evaluate("[...document.querySelectorAll('.o .nm')].map(x=>x.textContent.trim()).filter(Boolean)")
  allN=names()
  pg.click('#filters [data-f="q"]');pg.wait_for_timeout(300)
  got=names()
  check('D2 it shows the „?“ records, „sp.“ and the unanswered question — not the sure one, not the answered one', sorted(x.split(' ·')[0].replace(' ?','').strip() for x in got), ['Горска зидарка','Сива чапла','чайка sp.'])
  check('D3 ...with a line saying how many of each', pg.inner_text('.dbtnote'), '3 несигурни записа: 2 с „?“ · 1 само до група („sp.“) · 1 чака отговор от приятели. Докосни запис, за да го определиш.')
  check('D4 the chip shows its label while pressed', (pg.get_attribute('#filters [data-f="q"]','aria-pressed'),pg.is_visible('#filters [data-f="q"] .lbl')), ('true',True))
  pg.click('.tab[data-v="life"]');pg.wait_for_timeout(300)
  check('D5 „по видове“ lists the doubtful records by name (alternatives shown), with how many', pg.evaluate("[...document.querySelectorAll('.dbtrow')].map(r=>[r.querySelector('span').textContent,r.querySelector('small').textContent])"),
        [['Горска зидарка','1'],['Сива чапла / Голяма бяла чапла','1'],['чайка sp.','1']])
  pg.click('.tab[data-v="log"]');pg.click('#filters [data-f="all"]');pg.wait_for_timeout(300)
  check('D6 back to „Всички“: all five records again', (len(names()),len(allN)), (5,5))
  pg.evaluate("OBS.forEach(o=>{o.u=0;o.ask=0;});OBS=OBS.filter(o=>!isSp(o));render()");pg.click('#filters [data-f="q"]');pg.wait_for_timeout(300)
  check('D7 with nothing doubtful, it says so plainly', pg.inner_text('.empty'), 'Няма несигурни записи — всичко е определено.')
  check('D8 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
