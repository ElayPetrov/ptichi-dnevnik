import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-27',time='12:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8972;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
old={'bird-journal-v3':[R(id=1,bg='Кос'),R(id=2,bg='Сойка')],'bird-journal-outings':[{'id':'s1','date':'2026-10-27','place':'Копринка','complete':True,'upd':1}],
     'bird-journal-friends':{'fol':[{'id':'u2','name':'Петър','data':{'obs':[R(id=9,bg='Чинка')],'outs':[]}}],'fans':[]},
     'bird-journal-social':[{'id':'x','owner':'u2','item':'d:2026-10-27','author':'me','kind':'bravo'}],'bird-journal-days':{'2026-10-27':True}}
idb="""k=>new Promise(r=>{const q=indexedDB.open('birdjournal',1);q.onsuccess=()=>{const g=q.result.transaction('kv').objectStore('kv').get(k);g.onsuccess=()=>r(g.result==null?null:g.result.length);};})"""
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});pg=ctx.new_page();errs=[];alerts=[]
  pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:(alerts.append(d.message),d.accept()))
  pg.add_init_script("if(!sessionStorage.getItem('seeded')){sessionStorage.setItem('seeded','1');%s}"%''.join(f"localStorage.setItem({json.dumps(k)},{json.dumps(json.dumps(v,ensure_ascii=False))});" for k,v in old.items()))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(500)
  check('S1 opening the new version brings over the journal, outings, friends\' copies and reactions', (pg.evaluate("OBS.map(o=>o.bg)"),pg.evaluate("OUTS.length"),pg.evaluate("lsGet(KF,null).fol[0].name"),pg.evaluate("SOC.length")), (['Кос','Сойка'],1,'Петър',1))
  ls=pg.evaluate("['bird-journal-v3','bird-journal-outings','bird-journal-friends','bird-journal-social'].map(k=>localStorage.getItem(k))")
  check('S2 ...into IndexedDB, and frees localStorage only after a successful write', (ls,[pg.evaluate(idb,k)>0 for k in ['bird-journal-v3','bird-journal-outings','bird-journal-friends','bird-journal-social']]), ([None]*4,[True]*4))
  check('S3 small things (folded days) stay in localStorage', pg.evaluate("JSON.parse(localStorage.getItem('bird-journal-days'))"), {'2026-10-27':True})
  pg.click('#toggle');pg.fill('#f-bg','Чинка');pg.click('#savebtn');pg.wait_for_timeout(300)
  check('S4 a new record is written to IndexedDB, not localStorage', (pg.evaluate("JSON.parse(stGet(K)).length"),pg.evaluate("localStorage.getItem('bird-journal-v3')")), (3,None))
  pg.reload();pg.wait_for_timeout(500)
  check('S5 ...and is there after a reload', pg.evaluate("OBS.map(o=>o.bg).sort()"), ['Кос','Сойка','Чинка'])
  pg.evaluate("OBS=Array.from({length:40000},(_,i)=>({id:100000+i,date:'2026-0'+(1+i%9)+'-1'+(i%9),time:'08:00',place:'Язовир Копринка, източният бряг',count:'',bg:'Голяма бяла чапла',en:'Great Egret',la:'Ardea alba',fam:'Чапли и щъркели',note:'Стоеше на плитчината до тръстиките',h:0,s:1,p:0,beh:[],geo:'42.6301,25.3205',photo:null,upd:1}));save()")
  pg.wait_for_timeout(1500);size=pg.evaluate("stGet(K).length")
  pg.reload();pg.wait_for_timeout(1500)
  check('S6 a journal far beyond localStorage\'s ~5 MB (40,000 records) saves without a warning and survives a reload', (size>10_000_000,pg.evaluate("OBS.length"),alerts), (True,40000,[]))
  check('S7 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
