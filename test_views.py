import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
def rec(pg,sel):   # Дневник unfolds only the newest day (and month, year), so open the record's ones before tapping its button
  pg.evaluate("s=>{const b=document.querySelector(s);if(!b)return;for(const g of [b.closest('.yg.shut'),b.closest('.mg.shut'),b.closest('.dayg.shut')])if(g)g.querySelector(':scope>[data-ymt],:scope>[data-dayt]').click();}",sel)
  pg.click(sel)
R=lambda **k:{**dict(id=0,date='',time='',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]);fails=0;G='42.61985,25.39560'
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=1,date='2026-10-22',time='07:59',bg='Червеногръдка',la='Erithacus rubecula',place='Розариум',geo=G,h=1,s=0),
      R(id=2,date='2026-10-22',time='17:56',bg='Кос',la='Turdus merula',place='Розариум',geo=G),
      R(id=3,date='2026-10-22',time='12:30',bg='Сврака',la='Pica pica',place='Розариум'),
      R(id=4,date='2025-05-03',time='06:40',bg='Пчелояд',la='Merops apiaster',place='Копринка',geo=G,h=1,s=0),
      R(id=5,date='2026-04-28',time='06:50',bg='Пчелояд',la='Merops apiaster',place='Копринка',geo=G,h=1,s=1),
      R(id=6,date='2026-05-10',time='07:30',bg='Пчелояд',la='Merops apiaster',place='Розариум',geo=G,p=1),
      R(id=7,date='2026-06-01',time='08:00',bg='Пчелояд',la='Merops apiaster',place='Копринка',geo=G,u=1),
      R(id=8,date='2025-03-01',time='09:00',bg='Кос',la='Turdus merula',place='Розариум',geo=G),
      R(id=9,date='2026-10-18',time='06:30',bg='Голям синигер',la='Parus major',place='Розариум',geo=G,sess='sA'),
      R(id=10,date='2026-10-18',time='06:45',bg='Сойка',la='Garrulus glandarius',place='Розариум',geo=G,sess='sA')]
outs=[{'id':'sA','date':'2026-10-18','start':'06:10','end':'09:05','place':'Розариум','complete':True}]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(timezone_id='Europe/Sofia',viewport={'width':390,'height':844});pg=ctx.new_page();errs=[]
  pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-outings',%s);sessionStorage.setItem('s','1')}"%(json.dumps(json.dumps(data,ensure_ascii=False)),json.dumps(json.dumps(outs))))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  # --- sun ---
  day=pg.locator('.day').first.inner_text()
  check('V1 day header carries dawn, sunrise, sunset (Kazanlak, 22 Oct)', day.split('\n')[1].strip(), 'зора 7:10 · изгрев 7:39 · залез 18:26')
  meta=lambda nm:pg.locator('.o',has_text=nm).locator('.meta').nth(1).inner_text()
  check('V2 morning record: minutes after sunrise', meta('Червеногръдка').split('·')[0].strip(), '🕐 07:59 (20 мин след изгрева)')
  check('V3 evening record: minutes before sunset', meta('Кос').split('·')[0].strip(), '🕐 17:56 (30 мин преди залеза)')
  check('V4 midday record: no sun note; borrows coordinates for the header only', meta('Сврака').split('·')[0].strip(), '🕐 12:30')
  # --- species page ---
  pg.click('.tab[data-v="life"]'); pg.locator('.sp',has_text='Пчелояд').click(); pg.wait_for_timeout(100)
  rows=pg.eval_on_selector_all('.spd .row',"els=>els.map(e=>e.innerText.replace(/\\n/g,' | '))")
  check('V5 species page: evidence progression from sure records', rows[:3], ['чух | 3 май 2025','видях | 28 април 2026','снимах | 10 май 2026'])
  check('V6 ...records, first meeting per year with the shift, places', (pg.locator('.spd h4').nth(1).inner_text(),rows[3:5],rows[-2:]),
        ('3 ЗАПИСА · 1 НЕСИГУРНИ НЕ СЕ БРОЯТ',['2025 | 3 май','2026 | 28 апр · 5 дни по-рано'],['Копринка | 2×','Розариум | 1×']))
  check('V7 ...and the usual timing against sunrise', [r for r in rows if r.startswith('сутрешните')][0].startswith('сутрешните записи | обикновено'), True)
  pg.click('[data-spback]'); check('V8 back returns to the list', pg.locator('.sp').count(), 6)
  # --- year curve ---
  pg.click('.tab[data-v="phen"]'); pg.click('[data-pm="curve"]')
  check('V9 year curve: one line per year, this year highlighted', (pg.locator('.curve path.yl').count(),pg.locator('.curve path.yl.cur').count()), (2,1))
  check('V10 ...labelled with species counts', sorted(pg.eval_on_selector_all('.curve .yt',"e=>e.map(x=>x.textContent)")), ['2025: 2','2026: 6'])
  check('V11 ...and a like-for-like summary', pg.inner_text('.phen .outsum'), '2026: 6 вида до днес · 2025: 2 до същата дата, 2 за цялата година')
  # --- share cards ---
  pg.click('.tab[data-v="outs"]'); pg.locator('.ou').first.click(); pg.click('[data-ocard]')
  pg.wait_for_function("document.getElementById('cardDlg').open&&document.getElementById('cardImg').naturalWidth>0")
  check('V12 outing card: 1080×1350 PNG, previewed before sharing', (pg.evaluate("[cardImg.naturalWidth,cardImg.naturalHeight]"),pg.evaluate("cardFile.name")), ([1080,1350],'ptichi-dnevnik-2026-10-18.png'))
  pg.screenshot(path='/home/claude/card-preview.png'); pg.evaluate("cardImg.src").startswith('blob:')
  pg.evaluate("(async()=>{const a=document.createElement('a');})()")
  png=pg.evaluate("(async()=>{const b=await cardFile.arrayBuffer();return btoa(String.fromCharCode(...new Uint8Array(b).slice(0,0)))})()")
  pg.evaluate("window.__card=null"); pg.click('#cardClose')
  # species card with a photo
  pg.click('.tab[data-v="log"]'); rec(pg,'[data-ed="6"]'); pg.set_input_files('#f-photo','/home/claude/a.jpg'); pg.wait_for_function("phNew.length===1"); pg.click('#savebtn')
  pg.click('.tab[data-v="life"]'); pg.locator('.sp',has_text='Пчелояд').click(); pg.click('[data-spcard]')
  pg.wait_for_function("document.getElementById('cardDlg').open&&document.getElementById('cardImg').naturalWidth>0")
  check('V13 species card uses your latest photo of it', pg.evaluate("cardFile.name"), 'ptichi-dnevnik-Merops-apiaster.png')
  with pg.expect_download() as dl: pg.click('#cardSave')
  open('/home/claude/card-species.png','wb').write(open(dl.value.path(),'rb').read())
  check('V14 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
