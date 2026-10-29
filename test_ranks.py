import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-27',time='12:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8971;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
dates=lambda n:[f'{2026-j//336}-{(j%336)//28+1:02d}-{j%28+1:02d}' for j in range(n)]
data=[];i=1
for nm,n in [('Кос',150),('Сойка',50),('Голям синигер',12),('Червеногръдка',3)]:
  for d in dates(n):data.append(R(id=i,bg=nm,date=d));i+=1
data+= [R(id=5000+j,bg='Червеногръдка',date='2026-02-15',time=f'1{j%10}:00') for j in range(20)]   # twenty records on one day: still one day
data+= [R(id=6000+j,bg='Тъмна ливадарка',la='Saxicola maurus',date=d) for j,d in enumerate(dates(11))]   # not in the built-in list
data+= [R(id=7000+j,bg='Сива овесарка',u=1,date=d) for j,d in enumerate(dates(15))]   # unsure only: not listed, no rank
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);pg.click('.tab[data-v="life"]');pg.wait_for_timeout(250)
  cards=pg.evaluate("Object.fromEntries([...document.querySelectorAll('.sp')].map(c=>[c.querySelector('.nm').textContent,[[...c.querySelector('.th').classList].find(x=>x.startsWith('rk')),c.querySelector('.rkm').textContent]]))")
  check('R1 Кос, 150 days: gold „Познавач“', cards['Кос'], ['rk3','Познавач 150 дни с вида'])
  check('R2 Сойка, 50 days: silver „Приятел“, 100 more to „Познавач“', cards['Сойка'], ['rk2','Приятел 50 дни с вида · още 100 до „Познавач“'])
  check('R3 Голям синигер, 12 days: bronze „Познат“', cards['Голям синигер'], ['rk1','Познат 12 дни с вида · още 38 до „Приятел“'])
  check('R4 Червеногръдка: days, not records — twenty records on one day are one day (4 days, no ring yet)', cards['Червеногръдка'], ['rk0','4 дни с вида · още 6 до „Познат“'])
  check('R5 a species not in the built-in list gets its ring too', cards['Тъмна ливадарка'], ['rk1','Познат 11 дни с вида · още 39 до „Приятел“'])
  check('R6 only species you have sure records of are listed', ('Сива овесарка' in cards,len(cards)), (False,5))
  check('R7 a one-line legend explains the crowns (hidden while searching)', (pg.locator('.splegend').count(),(pg.fill('#q','кос'),pg.wait_for_timeout(200),pg.locator('.splegend').count())[2]), (1,0))
  pg.fill('#q','');pg.wait_for_timeout(150);pg.click('.sp[data-k] >> text=Сойка');pg.wait_for_timeout(250)
  check('R8 the species page: the ring on its bird, the rank, and a bar towards the next', (pg.evaluate("[...document.querySelector('.spd .th').classList].includes('rk2')"),pg.inner_text('.rkline'),pg.locator('.rkbar').count()),
    (True,'Приятел 50 дни с вида · още 100 до „Познавач“',1))
  pg.click('.tab[data-v="badges"]');pg.wait_for_timeout(250)
  bd=pg.evaluate("(()=>{const c=document.querySelector('.bd2[data-bid=\"g:Кълвачи\"]');return [c.querySelector('.bdn').textContent,c.querySelector('.bdh').textContent,getComputedStyle(c.querySelector('.bdh')).fontStyle,getComputedStyle(c.querySelector('.bdn')).fontStyle];})()")
  check('R9 badge cards: progress and description on separate lines in different styles, no list sizes', bd, ['0 / 3 до бронз','видове от групата','italic','normal'])
  pg.click('.tab[data-v="life"]');pg.wait_for_timeout(200)
  cr=pg.evaluate("[...document.querySelectorAll('.sp')].map(c=>{const k=c.querySelector('.crown');return [c.querySelector('.nm').textContent,k?[...k.classList].find(x=>x.startsWith('rk')):null,getComputedStyle(c.querySelector('.th')).boxShadow];}).filter(x=>['Кос','Сойка','Червеногръдка'].includes(x[0]))")
  check('R11 a crown in the bird\'s corner instead of a ring: gold, silver, none yet', sorted([[n,c,b=='none'] for n,c,b in cr]), [['Кос','rk3',True],['Сойка','rk2',True],['Червеногръдка',None,True]])
  check('R10 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
