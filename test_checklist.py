import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
T=datetime.date.today().isoformat()
R=lambda **k:{**dict(id=0,date='2026-10-20',time='08:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo='42.6200,25.3900',photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8977;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,bg='Кос'),R(id=2,bg='Кос',date='2026-09-02'),R(id=3,bg='Сойка'),R(id=4,bg='Голяма бяла чапла',geo='43.20,27.90')]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844},geolocation={'latitude':42.62,'longitude':25.39},permissions=['geolocation'])
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  pg.click('#ckOpen');pg.wait_for_function("ckPos!==null",timeout=5000);pg.wait_for_timeout(100)
  check('C1 „Списък“ opens any time; before an outing it says to start one to count', ('Започни излет' in pg.inner_text('#ck-list'),pg.is_visible('#ck-tools')), (True,False))
  sug=pg.evaluate("[...document.querySelectorAll('[data-cksug]')].map(b=>b.dataset.cksug)")
  check('C2 suggestions come from what you\'ve had near here — and none are added by themselves', (sug[:2],pg.evaluate("CKL.length")), (['Кос','Сойка'],0))
  pg.click('[data-cksug="Кос"]');pg.fill('#ck-in','Сива чапла');pg.click('#ck-add');pg.fill('#ck-in','Изобщо не птица');pg.click('#ck-add')
  check('C3 add by tapping a suggestion or by name; unknown names are refused with a note', (pg.evaluate("CKL.map(x=>x.bg)"),'го няма в списъка' in pg.inner_text('#ck-msg')), (['Кос','Сива чапла'],True))
  pg.click('#ck-close');pg.click('#sessStart');pg.wait_for_timeout(200);pg.click('#cancel') if pg.is_visible('#cancel') else None
  pg.click('#ckOpen');pg.wait_for_function("ckPos!==null",timeout=5000)
  pg.click('[data-cktap="0"]');pg.wait_for_timeout(150)
  r=pg.evaluate("OBS.filter(o=>o.sess===SESS.id&&o.bg==='Кос').map(o=>[o.count,o.geo,o.date,!!o.time])")
  check('C4 during an outing a tap logs it: count 1, here and now, in the outing', r, [['1','42.62000,25.39000',T,True]])
  pg.click('[data-cktap="0"]');pg.wait_for_timeout(150)
  check('C5 tapping again nearby adds to the same record', pg.evaluate("OBS.filter(o=>o.sess===SESS.id&&o.bg==='Кос').map(o=>o.count)"), ['2'])
  ctx.set_geolocation({'latitude':42.625,'longitude':25.39});pg.wait_for_function("ckPos==='42.62500,25.39000'",timeout=5000);pg.click('[data-cktap="0"]');pg.wait_for_timeout(150)
  check('C6 more than 300 m further on, it is a new record at the new point', pg.evaluate("OBS.filter(o=>o.sess===SESS.id&&o.bg==='Кос').map(o=>[o.count,o.geo]).sort()"), [['1','42.62500,25.39000'],['2','42.62000,25.39000']])
  check('C7 the row shows the total for the outing and the open batch a long press will open', (pg.inner_text('.ckr .ckc'),pg.inner_text('.ckr .ckn small')), ('3','сега 1 — задръж за описание'))
  pg.click('[data-ckminus="0"]');pg.wait_for_timeout(100);c1=pg.inner_text('.ckr .ckc');pg.click('#ck-undo');pg.wait_for_timeout(100)
  check('C8 „−“ takes one back, „отмени последното“ undoes it', (c1,pg.inner_text('.ckr .ckc')), ('2','3'))
  pg.click('#ck-mode');pg.click('[data-cktap="1"]');pg.wait_for_timeout(150)
  check('C9 in „чух“ mode a tap records the bird as heard', pg.evaluate("OBS.filter(o=>o.bg==='Сива чапла').map(o=>[o.h,o.s])"), [[1,0]])
  pg.click('#ck-mode');pg.click('[data-cktap="1"]');pg.click('[data-cktap="1"]');pg.wait_for_timeout(150)
  check('C9b switching back to „видях“ starts a separate record: heard and seen are not mixed', pg.evaluate("OBS.filter(o=>o.bg==='Сива чапла').map(o=>[o.h,o.s,o.count]).sort()"), [[0,1,'2'],[1,0,'1']])
  check('C10 a first-ever species gets its „Честито, нов вид!“', 'Честито' in pg.evaluate("document.getElementById('yay').innerText"), True)
  pg.evaluate("yayHide()");b0=pg.locator('[data-cktap="0"]').bounding_box();pg.mouse.move(b0['x']+20,b0['y']+15);pg.mouse.down();pg.wait_for_timeout(700);pg.mouse.up();pg.wait_for_timeout(200)
  check('C11 a long press opens the current batch in the form, with its count', (pg.evaluate("form.classList.contains('on')"),pg.input_value('#f-bg'),pg.input_value('#f-count'),pg.inner_text('#savebtn')), (True,'Кос','1','Запази промените'))
  pg.fill('#f-note','на брега, храни се');pg.click('#savebtn');pg.wait_for_timeout(200)
  pg.click('#ckOpen');pg.wait_for_function("ckPos!==null",timeout=5000);pg.click('[data-cktap="0"]');pg.click('[data-cktap="0"]');pg.wait_for_timeout(150)
  k=pg.evaluate("OBS.filter(o=>o.sess===SESS.id&&o.bg==='Кос'&&o.geo==='42.62500,25.39000').map(o=>[o.count,o.note]).sort()")
  check('C14 after describing it, new taps start a second batch; both stay separate records', k, [['1','на брега, храни се'],['2','']])
  b1=pg.locator('[data-cktap="0"]').bounding_box();pg.mouse.move(b1['x']+20,b1['y']+15);pg.mouse.down();pg.wait_for_timeout(700);pg.mouse.up();pg.wait_for_timeout(200)
  check('C15 ...and a long press now opens that second batch', (pg.input_value('#f-count'),pg.input_value('#f-note')), ('2',''))
  pg.click('#cancel')
  pg.click('#toggle');pg.fill('#f-bg','Сойка');pg.click('#savebtn');pg.wait_for_timeout(200);pg.click('#cancel') if pg.is_visible('#cancel') else None
  pg.evaluate("CKL.push({bg:'Сойка',la:'Garrulus glandarius',en:'Eurasian jay',fam:''});ckSave()")
  pg.click('#ckOpen');pg.wait_for_function("ckPos!==null",timeout=5000);pg.click('[data-cktap="2"]');pg.wait_for_timeout(150)
  check('C16 a record made through the form is never added to by taps', pg.evaluate("OBS.filter(o=>o.sess===SESS.id&&o.bg==='Сойка').map(o=>o.count).sort()"), ['','1'])
  check('C17 opening the list focuses no text field (no keyboard), and your list comes before the field and the suggestions',
    (pg.evaluate("document.activeElement.tagName!=='INPUT'"),pg.evaluate("(()=>{const y=id=>document.getElementById(id).getBoundingClientRect().top;return y('ck-list')<y('ck-in')&&y('ck-in')<y('ck-sug');})()")), (True,True))
  pg.click('#ck-close');pg.reload();pg.wait_for_timeout(400)
  check('C12 the list stays for the next outing', pg.evaluate("CKL.map(x=>x.bg)"), ['Кос','Сива чапла','Сойка'])
  check('C13 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
