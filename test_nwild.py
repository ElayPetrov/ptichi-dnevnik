# „не е дива (няма да се брои)“ (2026-11-21.1): a released, domestic, escaped or collection bird. The observation is kept and
# shown with a tag, but counts nowhere - lists, „нов вид“, Цели, atlas, tree, year, friends - and doesn't go to eBird.
# A bird missing from the list is added as a new species the usual way.
import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
T=datetime.date.today().isoformat();port=int(sys.argv[1]) if len(sys.argv)>1 else 9015;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
G='42.62000,25.40000'
R=lambda **k:{**dict(id=0,date=T,time='08:00',place='Язовир Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=G,photo=None),**k}
OBS=[R(id=1,time='08:00',bg='Кос',la='Turdus merula',en='Common Blackbird',fam='Дроздове'),
     R(id=2,time='08:10',bg='Зеленоглава патица',la='Anas platyrhynchos',en='Mallard',fam='Патици'),
     R(id=3,time='08:20',bg='Зеленоглава патица',la='Anas platyrhynchos',en='Mallard',fam='Патици',nwild=1,count='6'),
     R(id=4,time='08:30',bg='Сива гъска',la='Anser anser',en='Greylag Goose',fam='Гъски',nwild=1,count='12')]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844},geolocation={'latitude':42.70,'longitude':25.50},permissions=['geolocation'])
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%json.dumps(json.dumps(OBS,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(500);pg.click('.tab[data-v="log"]');pg.wait_for_timeout(300)
  # the form
  pg.click('#toggle');pg.wait_for_timeout(200)
  check('N1 the form has „не е дива (няма да се брои)“, off, after „не съм сигурен“ and its rows', (pg.inner_text('#f-nwild'),pg.get_attribute('#f-nwild','aria-pressed'),
        pg.evaluate("!!(document.getElementById('f-alt-row').compareDocumentPosition(document.getElementById('f-nwild'))&Node.DOCUMENT_POSITION_FOLLOWING)")), ('не е дива (няма да се брои)','false',True))
  pg.click('#f-nwild');pg.wait_for_timeout(100)
  check('N2 ticking it presses it and explains it once', (pg.get_attribute('#f-nwild','aria-pressed'),pg.inner_text('#tip-nwild .tip span')),
        ('true','За пусната, домашна, избягала птица или птица от колекция. Наблюдението остава в Дневника, но не се брои никъде и не отива в eBird. Дивите птици, дошли сами на същото място, се броят.'))
  # a bird missing from the list: added as a new species the usual way, ticked
  pg.fill('#f-bg','Черен лебед');pg.fill('#f-la','Cygnus atratus');pg.fill('#f-en','Black Swan');pg.fill('#f-count','4');pg.click('#savebtn');pg.wait_for_timeout(300)
  if pg.is_visible('#cancel'):pg.click('#cancel')
  sw=pg.evaluate("OBS.find(o=>o.la==='Cygnus atratus')")
  check('N3 saved with the mark; the bird joins the group\'s list as a new species', (sw and sw.get('nwild'),'Cygnus atratus' in pg.evaluate("SPXO.map(x=>x.la)")), (1,True))
  check('N4 ...with no „нов вид“ celebration', pg.evaluate("[...document.querySelectorAll('.yay')].map(x=>x.textContent).join(' ')").count('нов вид'), 0)
  card=lambda la:pg.evaluate("(la=>{const o=OBS.find(x=>x.la===la&&x.nwild);const c=[...document.querySelectorAll('#view .o')].find(e=>e.querySelector('[data-ed=\"'+o.id+'\"]'));if(!c)return null;const t=[...c.querySelectorAll('.tag')].map(t=>t.textContent);return [c.classList.contains('nwc'),t.includes('не е дива'),t.includes('нов вид')]})(%s)"%json.dumps(la))
  check('N5 in Дневник: dashed card, tag „не е дива“, no „нов вид“ tag', card('Cygnus atratus'), [True,True,False])
  check('N6 counts nowhere: lists, days, atlas, tree, year, badges see only the wild birds',
        pg.evaluate("[SURE().map(o=>o.id).sort(),Object.keys(speciesMap()).length,Object.keys(spDays()).length,Object.values(atlasData()).map(s=>Object.keys(s.sp).length),trMine().size,Object.keys(yearData(new Date().getFullYear()).sp).length]"),
        [[1,2],2,2,[2],2,2])
  pg.click('.tab[data-v="life"]');pg.wait_for_timeout(300)
  check('N7 Видове: „Моите · 2“, and the not-wild-only species named under the list', (pg.evaluate("document.querySelector('[data-lifeall=\"0\"]').textContent"),
        pg.evaluate("[...document.querySelectorAll('#view .note2')].map(x=>x.textContent).find(t=>t.startsWith('Само с „не е дива“'))")),
        ('Моите · 2','Само с „не е дива“ (не се броят): Сива гъска · Черен лебед'))
  pg.evaluate("spSel=key(OBS.find(o=>o.id===2));render()");pg.wait_for_timeout(200)
  check('N8 a species with both: the page counts the wild one and says the other doesn\'t count', pg.evaluate("[...document.querySelectorAll('.spd h4')].map(h=>h.textContent).find(t=>t.includes('наблюдени'))"), '1 наблюдение · 1 с „не е дива“ не се брои')
  pg.evaluate("spSel=null");pg.evaluate("renderUnseen(document.getElementById('view'),{bg:'Сива гъска',la:'Anser anser',en:'Greylag Goose'})")
  check('N9 a species with only not-wild observations: „not yet“, and how many it has', pg.inner_text('#view .spd .note2'), 'Още нямаш сигурни наблюдения на този вид. Имаш 1 наблюдение с „не е дива“ - то не се брои.')
  pg.evaluate("LIFEALL=1;render()");pg.wait_for_timeout(200)
  check('N10 Всички: Черен лебед is under „Добавени от групата“, without ✓', pg.evaluate("[...document.querySelectorAll('#view .asp')].filter(a=>a.textContent.includes('Черен лебед')).map(a=>a.classList.contains('got'))"), [False])
  pg.evaluate("LIFEALL=0;render()")
  # targets
  pg.evaluate("tgAdd({bg:'Сива гъска',la:'Anser anser',en:'Greylag Goose'});tgMarkReached()")
  check('N11 Цели: a not-wild bird doesn\'t reach a target', pg.evaluate("!!TG['anser anser'].got"), False)
  # exports
  pg.click('#acct');pg.wait_for_timeout(400)
  csv=pg.evaluate("""(()=>{let d='';const o=window.offer;window.offer=(n,c)=>{d=c};document.getElementById('exp').click();window.offer=o;return d.replace(/^\\ufeff/,'').trim().split('\\n')})()""")
  hdr=csv[0].split(',');col=hdr.index('Не е дива')
  check('N12 CSV: a „Не е дива“ column after „Несигурен“, „да“ on the not-wild rows only', (hdr[col-1],sorted(l.split('","')[2]+':'+l.split('","')[col].strip('"') for l in csv[1:])),
        ('Несигурен',['Зеленоглава патица:','Зеленоглава патица:да','Кос:','Сива гъска:да','Черен лебед:да']))
  check('N13 eBird: only the wild birds go, and the dialog says why the rest don\'t', (pg.evaluate("ebirdRows().map(r=>r.line.split(',')[0]).sort()"),
        pg.evaluate("openEbird();document.getElementById('eb-txt').textContent.includes('3 наблюдения с „не е дива“ не влизат.')")), (['Common blackbird','Mallard'],True))
  pg.evaluate("document.getElementById('ebDlg').close()")
  # editing
  pg.click('.tab[data-v="log"]');pg.wait_for_timeout(200)
  pg.evaluate("openForm(OBS.find(o=>o.id===4))");pg.wait_for_timeout(150)
  check('N14 opening a not-wild observation shows the tick pressed', pg.get_attribute('#f-nwild','aria-pressed'), 'true')
  pg.click('#f-nwild');pg.click('#savebtn');pg.wait_for_timeout(300)
  if pg.is_visible('#cancel'):pg.click('#cancel')
  check('N15 unticked and saved: the geese count again (one more species)', (pg.evaluate("OBS.find(o=>o.id===4).nwild"),pg.evaluate("Object.keys(speciesMap()).length")), (None,3))
  pg.evaluate("OBS.find(o=>o.id===4).nwild=1;save();render()")
  # same species at a new place keeps the mark
  pg.evaluate("sameHere(3)");pg.wait_for_timeout(900)
  check('N16 „+ същия вид на ново място“ keeps „не е дива“', pg.evaluate("OBS.filter(o=>o.la==='Anas platyrhynchos'&&o.id>100).map(o=>o.nwild)"), [1])
  # friends
  fp="{id:'u2',name:'Петър',obs:[{id:51,date:'%s',time:'09:00',bg:'Кос',la:'Turdus merula',h:0,s:1,p:0},{id:52,date:'%s',time:'09:05',bg:'Черен лебед',la:'Cygnus atratus',en:'Black Swan',nwild:1,h:0,s:1,p:0}],outs:[],bdg:{}}"%(T,T)
  check('N17 a friend\'s not-wild bird: tagged and dashed in the feed, not a „first“ for him, not in his counts',
        pg.evaluate("(()=>{const p=%s,h=fdRec(p,p.obs[1]),d=document.createElement('div');d.innerHTML=h;const c=d.firstElementChild;"
                    "return [c.classList.contains('nwc'),[...c.querySelectorAll('.tag')].map(t=>t.textContent).includes('не е дива'),fdMarks(p).first.has(52),"
                    "friendRows({fol:[{id:'u2',name:'Петър',data:{obs:p.obs,outs:[]},updated_at:new Date().toISOString()}]}).includes('1 вида · 1 наблюдения')]})()"%fp),
        [True,True,False,True])
  check('N18 the mark travels with the journal (backup and sync)', '"nwild":1' in pg.evaluate("bakData()"), True)
  pg.evaluate("ME={id:'me'};unsure=true;syncUnsure()")
  check('N19 „Попитай приятелите“ no longer promises the top of Приятели', pg.inner_text('#f-askhint'), 'Приятелите ти ще го видят в „Приятели“ и ще предложат вид; ти избираш кое да приемеш. Без име се записва като „Непозната птица“.')
  pg.evaluate("ME=null;unsure=false;syncUnsure()")
  check('N20 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
