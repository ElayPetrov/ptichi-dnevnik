import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='',time='',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]);fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  def page(data=None,extra='',dialog='accept'):
    ctx=b.new_context();pg=ctx.new_page();pg.errs=[];pg.dialogs=[]
    pg.on('pageerror',lambda e:pg.errs.append(str(e)))
    pg.on('dialog',lambda d:(pg.dialogs.append(d.message),d.accept() if dialog=='accept' else d.dismiss()))
    pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');%ssessionStorage.setItem('s','1')}"%(json.dumps(json.dumps(data or [],ensure_ascii=False)),extra))   # no welcome in these checks
    pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300);return pg
  def save(pg,bg,dt=None,unsure=False,la=None):
    if not pg.evaluate("form.classList.contains('on')"): pg.click('#toggle')
    pg.fill('#f-bg',bg)
    if la: pg.fill('#f-la',la)
    if dt: pg.fill('#f-date',dt[0]); pg.fill('#f-time',dt[1])
    if unsure: pg.click('#f-unsure')
    pg.click('#savebtn')
  stat=lambda pg:{k:pg.inner_text('#n-'+k) for k in ('obs','sp')}
  # ---------- certainty ----------
  pg=page([R(id=1,date='2026-05-01',bg='Сврака',la='Pica pica',place='Розариум')])
  save(pg,'Белоглав лешояд',('2026-10-01','09:00'),unsure=True)
  rec=pg.evaluate("OBS.find(o=>o.bg==='Белоглав лешояд')")
  check('C1 switch saves the record as unsure', rec.get('u'), 1)
  check('C2 unsure record counts nowhere in the totals', stat(pg), {'obs':'1','sp':'1'})
  card=pg.locator('.o',has_text='Белоглав лешояд')
  check('C3 Дневник shows it with a ? tag and no нов вид', (card.locator('.tag.u').count(),card.locator('.tag.nw').count()), (1,0))
  pg.click('.tab[data-v="life"]')
  check('C4 life list leaves it out but names it below', (pg.locator('.sp').count(),'Само с несигурни записи (не се броят): Белоглав лешояд' in pg.inner_text('#view')), (1,True))
  pg.click('.tab[data-v="map"]'); check('C5 places count only sure records', pg.locator('.pl').count(), 1)
  pg.click('.tab[data-v="phen"]'); check('C6 first dates ignore it', 'Белоглав' in pg.inner_text('#view'), False)
  pg.click('.tab[data-v="log"]')
  rid=rec['id']; pg.click(f'[data-ed="{rid}"]')
  check('C7 editing shows the switch on', pg.get_attribute('#f-unsure','aria-pressed'), 'true')
  pg.click('#f-unsure'); pg.click('#savebtn')
  check('C8 switching it off makes it count, and it becomes нов вид', (pg.evaluate(f"OBS.find(o=>o.id==={rid}).u"),stat(pg),pg.locator('.o',has_text='Белоглав лешояд').locator('.tag.nw').count()), (0,{'obs':'2','sp':'2'},1))
  save(pg,'Червен ангел',None,unsure=True)
  with pg.expect_download() as dl: pg.click('#acct');pg.click('#exp')
  csv=open(dl.value.path(),encoding='utf-8-sig').read().splitlines()
  check('C9 CSV has the new columns and marks the unsure record', (csv[0].endswith('Несигурен,Излет,Пълен списък'),[l for l in csv if 'Червен ангел' in l][0].split(',')[-3]), (True,'"да"'))
  check('C10 no page errors', pg.errs, [])
  # ---------- outings ----------
  pg=page([])
  pg.click('#sessStart'); t0=pg.evaluate("SESS.t0")
  save(pg,'Сврака'); save(pg,'Сойка')
  pg.click('#sessEnd')
  check('O1 live outing: panel opens with start = when Излет was tapped, end = now',
        (pg.is_visible('.sessend'),pg.input_value('#se-start'),pg.input_value('#se-end')), (True,t0,pg.evaluate("nowTime()")))
  pg.click('[data-done="1"]')
  o=pg.evaluate("OUTS[0]")
  check('O2 "Да, всички" saves a complete outing and ends it', (len(pg.evaluate("OUTS")),o['complete'],o['start'],pg.evaluate("SESS"),pg.is_visible('#sess')), (1,True,t0,None,False))
  pg.click('#sessStart'); save(pg,'Чапла',('2026-10-18','06:15')); save(pg,'Кос',('2026-10-18','07:40'))
  pg.click('#sessEnd')
  check('O3 writing up afterwards: defaults are first and last record', (pg.input_value('#se-start'),pg.input_value('#se-end')), ('06:15','07:40'))
  pg.fill('#se-end','08:00'); pg.click('[data-done="0"]')
  o=pg.evaluate("OUTS.find(x=>x.date==='2026-10-18')")
  check('O4 edited end time and "само някои" are kept', (o['start'],o['end'],o['complete']), ('06:15','08:00',False))
  pg.click('#sessStart'); pg.evaluate("closeForm()"); pg.click('#sessEnd')
  check('O5 outing with no records just ends, nothing saved', (pg.evaluate("SESS"),len(pg.evaluate("OUTS"))), (None,2))
  pg.click('.tab[data-v="outs"]')
  cards=pg.eval_on_selector_all('.ou',"els=>els.map(e=>[e.querySelector('.nm').textContent,e.querySelector('.meta').textContent,e.querySelector('.tag').textContent])")
  check('O6 Излети lists newest first with time, duration, species and completeness',
        (cards[1],pg.inner_text('.outsum').split(' · ')[0]), (['18 октомври 2026','06:15–08:00 · 1 ч 45 мин · 2 вида','частичен списък'],'2 излета'))
  pg.locator('.ou').nth(1).click()
  check('O7 tapping a card shows its species, its records with „промени“, and „+ птица“ / „промени излета“',
    (pg.locator('.ou .sl span').count(),pg.locator('.ou .orr').count(),pg.is_visible('.ou [data-oadd]'),pg.is_visible('.ou [data-oedit]')), (2,2,True,True))
  pg.click('.ou [data-oedit]'); pg.select_option('#od-comp',''); pg.click('#od-save')
  check('O8 completeness can be changed back to "not marked" in the outing editor', pg.evaluate("OUTS.find(x=>x.date==='2026-10-18').complete"), None)
  pg.click('.ou [data-oedit]'); pg.click('#od-del')   # the card stays open after saving the editor
  check('O9 deleting an outing keeps its records, loose', (len(pg.evaluate("OUTS")),pg.evaluate("OBS.filter(o=>o.date==='2026-10-18'&&!o.sess).length"),pg.locator('.ou').count()), (1,2,1))
  with pg.expect_download() as dl: pg.click('#acct');pg.click('#bak')
  body=json.load(open(dl.value.path(),encoding='utf-8'))
  check('O10 backups carry outings now (v5)', (body['v'],len(body['outs'])), (6,1))
  check('O11 no page errors', pg.errs, [])
  # ---------- stale outing, legacy records, restore ----------
  sess={'id':'s9','date':'2026-10-18','time':'08:00','place':'Розариум','geo':None,'at':int(time.time()*1000)-7*3600*1000,'live':True,'t0':'07:05','d0':'2026-10-18'}
  pg=page([R(id=11,date='2026-10-18',time='07:20',bg='Сврака',sess='s9'),R(id=12,date='2026-10-18',time='08:00',bg='Сойка',sess='s9')],
          extra="localStorage.setItem('bird-journal-session',%s);"%json.dumps(json.dumps(sess)),dialog='dismiss')
  pg.click('#toggle'); o=pg.evaluate("OUTS[0]")
  check('O12 a forgotten outing you decline is saved, ending at its last record', (o['start'],o['end'],o['complete'],pg.evaluate("SESS")), ('07:05','08:00',None,None))
  pg=page([R(id=21,date='2026-09-01',time='07:00',bg='Сврака',sess='s1'),R(id=22,date='2026-09-01',time='08:10',bg='Кос',sess='s1')])
  pg.click('.tab[data-v="outs"]')
  check('O13 records from before this version still show as an outing', (pg.locator('.ou').count(),pg.inner_text('.ou .tag')), (1,'пълнотата не е отбелязана'))
  tf='/home/claude/v4.json'; open(tf,'w',encoding='utf-8').write(json.dumps({'v':4,'obs':[R(id=31,date='2026-05-01',bg='Пчелояд',sess='s5')],'beh':['пее']},ensure_ascii=False))
  pg.set_input_files('#impf',tf); pg.wait_for_timeout(300)
  check('O14 an old v4 backup still restores', (pg.evaluate("OBS.length"),pg.evaluate("OUTS.length"),pg.locator('.ou').count()), (1,0,1))
  check('O15 no page errors', pg.errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
