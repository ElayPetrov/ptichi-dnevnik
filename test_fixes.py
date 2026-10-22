import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='',time='',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
DATA=[R(id=1,date='2025-05-01',bg='Син синигер',la='Parus caeruleus',place='Розариум'),
 R(id=2,date='2026-04-01',bg='Син синигер',la='Cyanistes caeruleus',en='Eurasian Blue Tit',place='Розариум'),
 R(id=3,date='2026-05-01',bg='Сврака',place='Копринка'),
 R(id=4,date='2026-06-10',bg='Сврака',la='Pica pica',place='Копринка'),
 R(id=5,date='2026-06-11',en='Eurasian Magpie',la='Pica pica',place='Копринка'),
 R(id=6,date='2026-07-01',bg='Сойка',la='Garrulus glandarius',place='Копринка'),
 R(id=7,date='2026-07-02',la='Larus michahellis',place='Язовир')]
port=int(sys.argv[1]);fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  def page(data=DATA,sess=None,dialog=None):
    ctx=b.new_context();pg=ctx.new_page();pg.errs=[];pg.dialogs=[]
    pg.on('pageerror',lambda e:pg.errs.append(str(e)))
    def on_d(d):
      pg.dialogs.append(d.message); d.accept() if dialog!='dismiss' else d.dismiss()
    pg.on('dialog',on_d)
    init="localStorage.setItem('bird-journal-v3',%s);"%json.dumps(json.dumps(data,ensure_ascii=False))
    if sess is not None: init+="localStorage.setItem('bird-journal-session',%s);"%json.dumps(json.dumps(sess,ensure_ascii=False))
    pg.add_init_script("if(!sessionStorage.getItem('s')){"+init+"sessionStorage.setItem('s','1')}")
    pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_function("OBS.length===%d"%len(data));return pg
  tab=lambda pg,v:pg.click(f'.tab[data-v="{v}"]')
  # ---------- 1: one species, one entry ----------
  pg=page()
  check('1a species count merges split names', pg.inner_text('#n-sp'), '4')
  check('1b one нов вид tag per species', pg.locator('.tag.nw').count(), 4)
  tab(pg,'life'); cards=pg.eval_on_selector_all('.sp',"els=>els.map(e=>[e.querySelector('.nm').textContent,[...e.querySelectorAll('.meta')].map(m=>m.textContent),e.querySelector('.cnt').textContent])")
  bt=[c for c in cards if c[0]=='Син синигер'][0]
  check('1c renamed genus is one species, newest name shown, old one listed', (bt[1][0],bt[1][1],bt[2]), ('Eurasian Blue Tit · Cyanistes caeruleus','също: Parus caeruleus','2×'))
  sv=[c for c in cards if c[0]=='Сврака'][0]
  check('1d bg-only + bg/la + en/la records join', (sv[1][0],sv[2]), ('Eurasian Magpie · Pica pica','3×'))
  check('1e Latin-only species gets a title', any(c[0]=='Larus michahellis' for c in cards), True)
  pg.click('#filters .chip[data-f="year"]'); check('1f "this year" filter keys by species', pg.locator('.sp').count(), 4)
  tab(pg,'phen'); pg.click('[data-pm="grid"]'); check('1g phenology rows', pg.locator('table.ph2 tbody tr').count(), 4)
  tab(pg,'places'); pl=dict(pg.eval_on_selector_all('.pl',"els=>els.map(e=>[e.querySelector('.nm').textContent,e.querySelector('.cnt').firstChild.textContent])"))
  check('1h places count merged species', pl, {'Копринка':'2','Розариум':'1','Язовир':'1'})
  check('1i no page errors', pg.errs, [])
  pg=page(DATA+[R(id=8,date='2026-08-01',bg='Сврака',la='Garrulus glandarius',place='Копринка')])
  tab(pg,'life'); cards=pg.eval_on_selector_all('.sp',"els=>els.map(e=>[e.querySelector('.nm').textContent,[...e.querySelectorAll('.meta')].map(m=>m.textContent)])")
  merged=[c for c in cards if c[0]=='Сврака'][0]
  check('1j a wrong name that bridges two species is visible', (pg.inner_text('#n-sp'), merged[1][1]), ('3','също: Pica pica · Сойка'))
  # ---------- 5: outing banner ----------
  pg=page()
  pg.click('#sessStart')
  for nm in ['Сврака','Сврака','Сойка']:
    pg.fill('#f-bg',nm); pg.click('#savebtn')
  check('5a banner counts species, not records', pg.inner_text('#sessTxt').split(' · ')[-1], '2 вида')
  sid=pg.evaluate("SESS.id"); rid=pg.evaluate("OBS[OBS.length-1].id")
  pg.evaluate("closeForm()"); pg.click(f'[data-ed="{rid}"]'); pg.fill('#f-note','поправка'); pg.click('#savebtn')
  check('5b editing keeps the outing link', pg.evaluate(f"OBS.find(o=>o.id==={rid}).sess"), sid)
  check('5c ...and the count', pg.inner_text('#sessTxt').split(' · ')[-1], '2 вида')
  pg.click('#sessEnd')
  # ---------- 2: stale outing ----------
  old={'id':'s1','date':'2026-10-18','time':'08:00','place':'Розариум','geo':None}
  pg=page(sess=old); pg.click('#toggle')
  check('2a outing without activity stamp asks once', len(pg.dialogs), 1)
  check('2b continuing keeps its date', pg.input_value('#f-date'), '2026-10-18')
  pg.evaluate("closeForm()"); pg.click('#toggle'); check('2c ...and does not ask again', len(pg.dialogs), 1)
  pg=page(sess={**old,'at':int(time.time()*1000)-7*3600*1000},dialog='dismiss'); pg.click('#toggle')
  check('2d declining ends it; record gets today', (len(pg.dialogs),pg.evaluate("SESS"),pg.input_value('#f-date')==pg.evaluate("today()")), (1,None,True))
  pg=page(sess={**old,'at':int(time.time()*1000)-3600*1000}); pg.click('#toggle')
  check('2e an active outing does not ask', (len(pg.dialogs),pg.input_value('#f-date')), (0,'2026-10-18'))
  # ---------- 3: photos ----------
  pg=page()
  keys=lambda: sorted(pg.evaluate("new Promise(r=>{const q=idb.transaction('p','readonly').objectStore('p').getAllKeys();q.onsuccess=()=>r(q.result)})"))
  pg.click('#toggle'); pg.fill('#f-bg','Тест'); pg.set_input_files('#f-photo','a.jpg'); pg.wait_for_function("phNew.length===1")
  pg.click('#savebtn'); rec=pg.evaluate("OBS.find(o=>o.bg==='Тест')"); a=rec['photo']
  check('3a saved photo is stored', keys(), [a])
  pg.click(f'[data-ed="{rec["id"]}"]'); pg.click('#rmph'); pg.click('#cancel')
  check('3b махни then Отказ keeps the photo', (keys(), pg.evaluate(f"OBS.find(o=>o.id==={rec['id']}).photo")), ([a],a))
  pg.click(f'[data-ed="{rec["id"]}"]'); pg.set_input_files('#f-photo','b.jpg'); pg.wait_for_function("phNew.length===1"); bb=pg.evaluate("photo"); pg.click('#cancel')
  check('3c replacing then Отказ drops the new one, keeps the old', keys(), [a])
  pg.click(f'[data-ed="{rec["id"]}"]'); pg.set_input_files('#f-photo','b.jpg'); pg.wait_for_function("phNew.length===1"); bb=pg.evaluate("photo"); pg.click('#savebtn')
  check('3d replacing then Запиши deletes the old one', (keys(), pg.evaluate(f"OBS.find(o=>o.id==={rec['id']}).photo")), ([bb],bb))
  pg.click(f'[data-ed="{rec["id"]}"]'); pg.click('#rmph'); pg.click('#savebtn')
  check('3e махни then Запиши deletes it', (keys(), pg.evaluate(f"OBS.find(o=>o.id==={rec['id']}).photo")), ([],None))
  pg.click('#toggle'); pg.fill('#f-bg','Тест2'); pg.set_input_files('#f-photo','a.jpg'); pg.wait_for_function("phNew.length===1"); pg.click('#cancel')
  check('3f new photo then Отказ leaves no orphan', keys(), [])
  check('3g no page errors', pg.errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
