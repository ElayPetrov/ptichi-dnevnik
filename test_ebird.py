import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-24',time='08:10',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo='42.6100,25.3000',photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8976;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,bg='Кос',count='2',sess='s1',time='08:10',note='пееше, на "ореха"\nдълго'),R(id=2,bg='Кос',count='3',sess='s1',time='08:40',geo='42.6200,25.3100'),
      R(id=3,bg='Сойка',sess='s1',time='09:00',geo='42.6300,25.3150',h=1,s=0,beh=['храни се']),R(id=4,bg='Сива овесарка',u=1,sess='s1'),
      R(id=5,bg='Сврака',date='2026-10-25',time='17:20',place='Тюлбето',geo='42.6210,25.3920',count='~40'),R(id=6,bg='Кос',date='2026-10-26',time='',place='',geo=None)]
outs=[{'id':'s1','date':'2026-10-24','place':'Язовир Копринка, южен бряг','start':'08:00','end':'10:30','complete':True,'with':'Петър','upd':1}]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-outings',%s);}"%(json.dumps(json.dumps(data,ensure_ascii=False)),json.dumps(json.dumps(outs,ensure_ascii=False))))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  check('E1 a „Към eBird“ button at the bottom, next to Експорт CSV', pg.evaluate("document.getElementById('ebird').previousElementSibling.id"), 'exp')
  pg.evaluate("window.__f=[];offer=(n,c)=>__f.push([n,c]);0");pg.click('#ebird');pg.wait_for_timeout(150)
  check('E2 the dialog says how many rows and lists, that unsure records stay out, and how to import', ('несигурен запис не влиза' in pg.inner_text('#eb-txt'),'eBird Record Format (Extended)' in pg.inner_text('#eb-txt')), (True,True))
  pg.click('#eb-ok');pg.wait_for_timeout(300)
  f=pg.evaluate("__f");name,csv=f[0];rows=[l.split(',') for l in csv.strip().split('\n')]
  check('E3 one file „ebird.csv“, no header row, 19 columns in every row', (name,all(len(r)==19 for r in rows),rows[0][0]!='Common Name'), ('ebird.csv',True,True))
  out=[r for r in rows if r[8]=='10/24/2026']
  kos=[r for r in out if r[1]=='Turdus'][0]
  check('E4 the outing is one list: Traveling, 150 minutes, all reported, 2 observers, distance in miles, one place and point', (kos[12],kos[14],kos[15],kos[13],float(kos[16])>1,kos[5],kos[6],kos[7]),
    ('Traveling','150','Y','2',True,'Язовир Копринка; южен бряг','42.61000','25.30000'))
  check('E5 two records of one species in a list become one row with the counts added; date MM/DD/YYYY, start, province 24 and BG', (len(out),kos[3],kos[9],kos[10],kos[11]), (2,'5','08:00','24','BG'))
  check('E6 notes and behaviour go to the species comments, without quotes, commas or line breaks', kos[4], 'пееше; на ореха дълго')
  soj=[r for r in out if r[1]=='Garrulus'][0]
  check('E7 a bird only heard is marked, with its behaviour; no count means X', (soj[4],soj[3]), ('само чут | храни се','X'))
  sv=[r for r in rows if r[8]=='10/25/2026'][0]
  check('E8 a record outside an outing is its own Incidental list; „~40“ is 40', (sv[12],sv[3],sv[9],sv[15],sv[5]), ('Incidental','40','17:20','N','Тюлбето'))
  nog=[r for r in rows if r[8]=='10/26/2026'][0]
  check('E9 a record without coordinates still gets a province (your usual one) and a place label', (nog[10],nog[5],nog[6]), ('24','Без място',''))
  check('E10 unsure records stay out', any('Emberiza' in r[1] or 'Сива овесарка' in r[0] for r in rows), False)
  check('E11 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
