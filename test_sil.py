import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='',time='',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8961;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,date='2026-10-01',bg='Горска улулица',la='Strix aluco',fam='Сови'),R(id=2,date='2026-10-02',bg='Чинка',la='Fringilla coelebs',fam='Чинки'),
      R(id=3,date='2026-10-03',bg='Сврака',la='Pica pica'),R(id=4,date='2026-10-04',bg='Непозната птица',fam='Друго'),
      R(id=5,date='2026-10-05',bg='Горска улулица',la='Strix aluco')]   # a later record without a family still keeps the owl
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300);pg.click('.tab[data-v="life"]')
  ph=lambda nm:pg.locator('.sp',has_text=nm).locator('.th.none').inner_html()
  check('S1 an owl gets the owl (the one with eye holes), even if its latest record has no family', ('class="sil"' in ph('Горска улулица'),'evenodd' in ph('Горска улулица')), (True,True))
  check('S2 finches get the thick-billed songbird', ('class="sil"' in ph('Чинка'),'70,35 82,41 70,47' in ph('Чинка')), (True,True))
  check('S3 no family, or Друго: the usual bird', ('class="sil"' in ph('Сврака'),'class="sil"' in ph('Непозната птица')), (False,False))
  pg.locator('.sp',has_text='Горска улулица').click()
  check('S4 the species page shows its silhouette by the name', pg.locator('.spd .th.none svg.sil').count(), 1)
  pg.click('[data-spcard]');pg.wait_for_function("document.getElementById('cardDlg').open&&document.getElementById('cardImg').naturalWidth>0")
  px=pg.evaluate("""(()=>{const i=document.getElementById('cardImg'),c=document.createElement('canvas');c.width=i.naturalWidth;c.height=i.naturalHeight;
    const x=c.getContext('2d');x.drawImage(i,0,0);return [...x.getImageData(540,258,1,1).data].slice(0,3);})()""")
  check('S5 a species card without a photo puts the silhouette in the scene (dark olive at its centre)', all(v<110 for v in px), True)
  check('S6 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
