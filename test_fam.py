# 3 Nov 2026: Иван's groups everywhere, 40 family badges (20 with levels, 20 single), Етолог with breeding codes,
# the seven new badges, reached targets that keep counting after removal, and folding sections.
import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
T=datetime.date.today().isoformat()
R=lambda **k:{**dict(id=0,date=T,time='08:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo='42.61000,25.30000',photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8996;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,bg='Речна чайка',fam='Чайки и рибарки'),R(id=2,bg='Речна рибарка'),R(id=3,bg='Козодой'),R(id=4,bg='Кос',beh=['пее']),R(id=5,bg='Сойка',bc=14),
      R(id=6,bg='Авлига',bc=2),R(id=7,bg='Чухал',h=1,s=0),R(id=8,bg='Сврака',**{'as':{'m':2}},count='3'),R(id=9,bg='Розово фламинго'),
      R(id=10,bg='Обикновен скорец',geo='42.73600,25.39300'),R(id=11,bg='Сойка',date='2025-01-01',geo='42.69770,23.32190')]
outs=[{'id':'s1','date':T,'place':'Копринка','start':'07:00','end':'09:00','complete':True,'upd':1,'trk':[[42.61,25.30,1],[42.62,25.30,2]],'dist':12.4}]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});ctx.route('https://**',lambda r:r.abort() if 'localhost' not in r.request.url else r.continue_())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-outings',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}"%(json.dumps(json.dumps(data,ensure_ascii=False)),json.dumps(json.dumps(outs,ensure_ascii=False))))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(500)
  check('F1 your 40 groups (+ „Друго“) are the app’s groups, in field-guide order', (pg.evaluate("FAMS.length"),pg.evaluate("FAMS[0]"),pg.evaluate("FAMS[FAMS.length-1]")), (41,'Водоплаващи','Друго'))
  check('F2 gulls and terns are separate; an old record’s stored group name no longer matters', pg.evaluate("[grp(OBS.find(o=>o.id===1)),grp(OBS.find(o=>o.id===2))]"), ['Чайки','Рибарки'])
  B=lambda i:pg.evaluate(f"(d=>d?[d.g,tiersNow()[d.id].v,tiersNow()[d.id].t]:null)(BDEF.find(d=>d.id==={json.dumps(i)}))")
  check('F3 40 family badges: 20 with levels, 20 single', (pg.evaluate("BDEF.filter(d=>d.sec==='fam').length"),pg.evaluate("BDEF.filter(d=>d.sec==='fam1').length"),pg.evaluate("BDEF.filter(d=>d.sec==='fam1').every(d=>d.g.length===1)")), (20,20,True))
  check('F4 totals are the lower count: Дъждосвирцови 36 → 11/18/32, Чайки 9 → 3/5/8', (B('f:Дъждосвирцови птици')[0],B('f:Чайки')[0]), ([11,18,32],[3,5,8]))
  check('F5 a small family is won at more than half: Козодои 1/1 (won), Скорецови 1 of 2 (not yet)', (B('f:Козодои')[1:],B('f:Скорецови')[0],B('f:Скорецови')[2]), ([1,1],[2],0))
  check('F6 Етолог counts behaviour or a breeding code', B('etho')[1], 3)
  check('F7 Атласист counts species with B or C codes only (Сойка C14, not Авлига A2)', B('atlas')[1], 1)
  check('F8 По слух: species only heard', B('ear')[1], 1)
  check('F9 Броячът: records with a sex/age split', B('counter')[1], 1)
  check('F10 Квадрати: 10×10 km squares with records', B('squares')[1], 3)
  check('F11 Пътят: km walked on paths', B('path')[1], 12)
  check('F12 Рядкости: rare species (the flamingo)', B('rare')[1], 1)
  pg.evaluate("tgAdd({bg:'Сврака',la:'Pica pica',en:'Eurasian magpie'});TG[tgKey({la:'Pica pica'})].t=Date.now()-864e5;saveTg();tgMarkReached()")
  m1=B('mission')[1];pg.evaluate("tgDel(tgKey({la:'Pica pica'}))")
  check('F13 Мисията изпълнена: a reached target counts, and still counts after you remove it', (m1,B('mission')[1]), (1,1))
  pg.evaluate("tgAdd({bg:'Сива врана',la:'Corvus cornix',en:'Hooded crow'});tgMarkReached()")
  check('F14 ...but a target you haven’t seen since adding it doesn’t count', B('mission')[1], 1)
  pg.click('.tab[data-v="badges"]');pg.wait_for_timeout(200)
  heads=pg.evaluate("[...document.querySelectorAll('[data-bdf]')].map(b=>b.querySelector('span').textContent)")
  check('F15 Значки: seven sections, each folding (folded at first), with its level count', (heads[-2:],pg.evaluate("[...document.querySelectorAll('[data-bdf]+.bdg2')].filter(x=>x.style.display!=='none').length")), (['Семейства','Малки семейства'],0))
  pg.click('[data-bdf="fam1"]');pg.wait_for_timeout(100)
  won=pg.evaluate("(()=>{const c=document.querySelector('[data-bid=\"f:Козодои\"]');return [c.querySelector('.bdt').textContent,c.className.includes('t3')]})()")
  check('F16 a won single badge says „спечелена“ with the gold ring; the section stays open', (won,pg.evaluate("JSON.parse(localStorage.getItem('bird-journal-bdfold')).fam1")), (['спечелена',True],True))
  pg.click('.tab[data-v="life"]');pg.wait_for_timeout(150);pg.click('[data-lifeall="1"]');pg.wait_for_timeout(200)
  check('F17 „Всички видове“: each family folds, folded at first, with its count', (pg.locator('[data-alf]').count(),pg.evaluate("[...document.querySelectorAll('[data-alf]+.allsp')].filter(x=>x.style.display!=='none').length"),pg.inner_text('[data-alf="Чайки"] small')), (41,0,'1 / 18'))
  pg.click('[data-alf="Чайки"]');pg.wait_for_timeout(80)
  check('F18 ...tapping opens it', pg.evaluate("document.querySelector('[data-alf=\"Чайки\"]+.allsp').style.display"), '')
  check('F19 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
