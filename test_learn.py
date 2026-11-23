# „🎓 Уроци“ (2026-11-23.2): a Duolingo-style course of general bird knowledge in Видове. Chapter 1 „Какво е птица“ with four
# lessons; info cards, true/false, multiple choice, pictures, pairs and „tap the bird“; a wrong answer comes back at the end of the
# lesson; points and a streak; practice from done lessons; progress kept on the device, merged in sync and backups.
import json,subprocess,sys,time,datetime,re
sys.path.insert(0,'/home/claude')
from sbstack import Stack
from playwright.sync_api import sync_playwright
T=datetime.date.today();TS=T.isoformat();port=int(sys.argv[1]) if len(sys.argv)>1 else 9016;fails=0
D=lambda n:(T-datetime.timedelta(days=n)).isoformat()
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
OBS=[dict(id=1,date=TS,time='08:00',place='Казанлък',count='',bg='Кос',la='Turdus merula',en='Common Blackbird',fam='Дроздове',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None)]
SB='https://test-proj.supabase.co';UMD='/home/claude/sb/package/dist/umd/supabase.js';CDN='https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.117.3/dist/umd/supabase.js'
src=open('ptichi-dnevnik.html',encoding='utf-8').read()
open('learn-test.html','w',encoding='utf-8').write(re.sub(r"const SB_URL='[^']*'","const SB_URL='"+SB+"'",src))
cur=lambda pg:pg.evaluate("LP&&LP.q[LP.i]?{k:LP.q[LP.i].k,id:LP.q[LP.i].id,a:LP.q[LP.i].a,n:(LP.q[LP.i].p||[]).length}:null")
def answer(pg,right=True):   # answers whatever is on screen; returns its kind
  x=cur(pg)
  if not x:return None
  k=x['k']
  if k=='info':pg.click('[data-lnext]');return k
  if k=='pr':
    if not right:pg.click('[data-lpl="0"]');pg.click('[data-lpr="1"]')
    for i in range(x['n']):pg.click(f'[data-lpl="{i}"]');pg.click(f'[data-lpr="{i}"]')
  elif k=='tap':pg.click('#lrBody [data-lpart="%s"]'%(x['a'] if right else ('tail' if x['a']!='tail' else 'beak')));pg.click('[data-lcheck]')
  elif k=='tf':pg.click('[data-lopt="%s"]'%(('1' if x['a'] else '0') if right else ('0' if x['a'] else '1')));pg.click('[data-lcheck]')
  else:pg.click('[data-lopt="%s"]'%('0' if right else '1'));pg.click('[data-lcheck]')
  pg.click('[data-lnext]');return k
def finish(pg,right=True):
  while cur(pg):answer(pg,right)
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
st=None
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  def page(data,w=390,store=None):
    ctx=b.new_context(viewport={'width':w,'height':844});pg=ctx.new_page();pg.errs=[]
    pg.on('pageerror',lambda e:pg.errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
    pg.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-quiet','true');localStorage.setItem('bird-journal-tips','{\"all\":1}');%ssessionStorage.setItem('s','1')}"
                       %(json.dumps(json.dumps(data,ensure_ascii=False)),("localStorage.setItem('bird-journal-learn',%s);"%json.dumps(json.dumps(store))) if store else ''))
    pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(500);return pg
  pg=page(OBS,w=360)
  pg.click('.tab[data-v="life"]');pg.wait_for_timeout(200)
  check('L1 Видове has a fourth sub-tab „🎓 Уроци“; all four fit on one line on a 360 px phone',
        (pg.evaluate("[...document.querySelectorAll('.lifetabs button')].map(b=>b.textContent.replace(/ · \\d+/,''))"),pg.evaluate("new Set([...document.querySelectorAll('.lifetabs button')].map(b=>b.offsetTop)).size")),
        (['Моите','Всички','🌳 Дървото','🎓 Уроци'],1))
  pg.click('[data-lifeall="3"]');pg.wait_for_timeout(300)
  check('L2 the path: four chapters, the first open with its first lesson, the rest locked; the coming ones listed by name, the guide chapter first; 0 points, no „Упражнявай“ yet; no search or filters',
        (pg.evaluate("[...document.querySelectorAll('.lunit:not(.soon)')].map(u=>u.querySelector('h3').textContent+(u.classList.contains('locked')?' (locked)':''))"),
         pg.evaluate("[...document.querySelectorAll('[data-lunit=\"u1\"] .lnode')].map(n=>[n.querySelector('.lname').textContent,n.className.replace('lnode','').trim(),n.disabled])"),
         pg.evaluate("document.querySelector('.lunit.soon p').innerText.split('\\n')"),pg.inner_text('.lrnhead').split('\n')[0],pg.locator('[data-lprac]').count(),
         pg.is_visible('#q'),pg.is_visible('#filters')),
        (['Какво е птица','Пера и цветове (locked)','Клюнове и храна (locked)','Крака и полет (locked)'],
         [['Перата','cur',False],['Клюн, кости, яйца','lock',True],['Тялото на птицата','lock',True],['Птиците са динозаври','lock',True]],
         ['Думите на определителя','Гласове','Гнездене','Миграция','Как разпознаваме','Групите птици'],'0 точки',0,False,False))
  # the player
  pg.click('[data-lstart="u1a"]');pg.wait_for_timeout(200)
  check('L3 a lesson opens full-screen: empty progress bar, an info card with a picture and „Продължи“',
        (pg.evaluate("document.getElementById('lrnDlg').open"),pg.evaluate("document.querySelector('#lrnDlg .lrbar i').style.width"),pg.inner_text('#lrBody h3'),pg.locator('#lrBody .lpic').count(),pg.inner_text('#lrFoot')),
        (True,'0%','Само птиците имат пера',1,'Продължи'))
  pg.click('[data-lnext]');pg.wait_for_timeout(100)
  n0=pg.evaluate("LP.q.length")
  pg.click('[data-lopt="1"]');pg.click('[data-lcheck]');pg.wait_for_timeout(100)
  check('L4 true/false, answered wrong: red, „Не съвсем.“, the right answer and why; the bar moved for the card, not for the mistake',
        (pg.evaluate("[...document.querySelectorAll('#lrBody .lopt')].map(b=>b.textContent+':'+b.className.replace('lopt','').trim())"),pg.evaluate("document.getElementById('lrFoot').className"),
         pg.inner_text('#lrFoot .lfb'),pg.evaluate("document.querySelector('#lrnDlg .lrbar i').style.width")),
        (['Вярно:bad','Невярно:ok'],'bad','Не съвсем.\nВерният отговор: Невярно\nПрилепът е бозайник: има козина вместо пера и кърми малките си. Летенето не прави едно животно птица.','11%'))
  check('L5 ...and the question comes back at the end of the lesson', (pg.evaluate("LP.q.length")-n0,pg.evaluate("LP.q[LP.q.length-1].id")), (1,'u1a2'))
  pg.click('[data-lnext]');answer(pg)     # u1a3
  check('L6 picture choice: three pictures with names', (cur(pg)['k'],sorted(pg.evaluate("[...document.querySelectorAll('#lrBody .lpics .lopt')].map(b=>b.textContent+(b.querySelector('svg')?'+pic':''))"))),
        ('pic',['Пеперуда+pic','Прилеп+pic','Птица+pic']))
  pg.click('[data-lopt="0"]');pg.click('[data-lcheck]');pg.wait_for_timeout(80)
  check('L7 the right one: green, „Точно така!“ with the explanation', (pg.evaluate("document.querySelector('#lrBody [data-lopt=\"0\"]').classList.contains('ok')"),pg.evaluate("document.getElementById('lrFoot').className"),pg.inner_text('#lrFoot .lfb b')),
        (True,'ok','Точно така!'))
  pg.click('[data-lnext]')
  check('L8 multiple choice: the options come shuffled, the right one is judged by content', (cur(pg)['k'],sorted(pg.evaluate("[...document.querySelectorAll('#lrBody [data-lopt]')].map(b=>b.textContent)"))),
        ('ch',['От кератин','От кост','От хрущял']))
  answer(pg);answer(pg)   # u1a5, u1a6 info
  check('L9 pairs: two columns of four', (cur(pg)['k'],pg.locator('#lrBody [data-lpl]').count(),pg.locator('#lrBody [data-lpr]').count(),pg.is_visible('#lrFoot')), ('pr',4,4,False))
  pg.click('[data-lpl="0"]');pg.click('[data-lpr="1"]');pg.wait_for_timeout(60)
  wrong=pg.evaluate("[document.querySelector('[data-lpl=\"0\"]').className,document.querySelector('[data-lpr=\"1\"]').disabled]")
  pg.click('[data-lpl="0"]');pg.click('[data-lpr="0"]');pg.wait_for_timeout(60)
  right=pg.evaluate("[document.querySelector('[data-lpl=\"0\"]').classList.contains('gone'),document.querySelector('[data-lpr=\"0\"]').disabled]")
  for i in range(1,4):pg.click(f'[data-lpl="{i}"]');pg.click(f'[data-lpr="{i}"]')
  check('L10 a wrong pair shakes and stays, a right pair fades out; when all are matched: „Готово!“ and the note',
        (wrong,right,pg.inner_text('#lrFoot .lfb')),(['lopt shake',False],[True,True],'Готово!\nМаховите пера са по крилата, а кормилните - на опашката.'))
  pg.click('[data-lnext]');finish(pg)
  check('L11 the end: +10 points (there were mistakes), 1 day in a row, accuracy', pg.evaluate("[...document.querySelectorAll('.lend .lstats span')].map(s=>s.innerText.replace('\\n',' '))"),
        ['+10 точки','🔥 1 ден подред','78% верни'])
  pg.click('[data-lclose]');pg.wait_for_timeout(200)
  check('L12 back on the path: „Перата“ ✓, the next lesson open; 10 points; „Упражнявай“ appears',
        (pg.evaluate("[...document.querySelectorAll('[data-lunit=\"u1\"] .lnode')].map(n=>n.className.replace('lnode','').trim())"),pg.inner_text('.lrnhead').split('\n')[0],pg.locator('[data-lprac]').count(),pg.evaluate("document.getElementById('lrnDlg').open")),
        (['done','cur','lock','lock'],'10 точки',1,False))
  pg.click('[data-lstart="u1b"]');finish(pg)
  check('L13 a lesson without mistakes: +15 points', pg.inner_text('.lend .lstats span:first-child').replace('\n',' '), '+15 точки')
  pg.click('[data-lclose]');pg.click('[data-lstart="u1c"]');pg.wait_for_timeout(150)
  check('L14 the labelled drawing: seven parts named, not tappable', (pg.evaluate("[...document.querySelectorAll('#lrBody .lbird text')].map(t=>t.textContent).sort()"),pg.locator('#lrBody .lbird.lab').count()),
        (sorted(['Клюн','Глава','Гърди','Гръб','Крило','Опашка','Крака']),1))
  pg.click('#lrBody [data-lpart="tail"]');pg.wait_for_timeout(60)
  check('L15 ...tapping it selects nothing', pg.locator('#lrBody .lp.sel').count(), 0)
  pg.click('[data-lnext]')
  check('L16 „Докосни клюна“: the bird has its seven parts to tap', (pg.inner_text('#lrBody .lq'),sorted(pg.evaluate("[...document.querySelectorAll('#lrBody [data-lpart]')].map(e=>e.dataset.lpart)"))),
        ('Докосни клюна',sorted(['beak','head','breast','back','wing','tail','legs'])))
  pg.click('#lrBody [data-lpart="tail"]');sel=pg.evaluate("[...document.querySelectorAll('#lrBody .lp.sel')].map(e=>e.dataset.lpart)");pg.click('[data-lcheck]');pg.wait_for_timeout(60)
  check('L17 a wrong part: picked shows blue, then red, and the beak green; „Верният отговор: Клюн“',
        (sel,pg.evaluate("[...document.querySelectorAll('#lrBody .lp.bad')].map(e=>e.dataset.lpart)"),pg.evaluate("[...document.querySelectorAll('#lrBody .lp.ok')].map(e=>e.dataset.lpart)"),pg.inner_text('#lrFoot .lfb').split('\n')[1]),
        (['tail'],['tail'],['beak'],'Верният отговор: Клюн'))
  pg.click('[data-lnext]');pg.click('#lrBody [data-lpart="tail"]');pg.click('[data-lcheck]')
  check('L18 the right part: „Точно така!“', pg.inner_text('#lrFoot .lfb b'), 'Точно така!')
  pg.click('[data-lnext]');pg.click('[data-lclose]');pg.wait_for_timeout(150)
  check('L19 closing half-way keeps the lesson unfinished (no ✓, no points), the answers given are remembered',
        (pg.evaluate("lrnDone('u1c')"),pg.inner_text('.lrnhead').split('\n')[0],pg.evaluate("[LRN.x.u1c2.s,LRN.x.u1c2.w]")),(False,'25 точки',[1,1]))
  # practice: done lessons only, the ones you got wrong first
  pg.click('[data-lprac]');pg.wait_for_timeout(150)
  q=pg.evaluate("LP.q.map(x=>x.id)")
  check('L20 „Упражнявай“: up to 8 questions from done lessons only, no info cards, the one you got wrong included',
        (len(q),all(i[:3] in ('u1a','u1b') for i in q),any(pg.evaluate("LP.q.map(x=>x.k)").count('info') for _ in [0]),'u1a2' in q),(8,True,False,True))
  finish(pg)
  check('L21 practice done without mistakes: +5 points', (pg.inner_text('.lend .lbig'),pg.inner_text('.lend .lstats span:first-child').replace('\n',' ')), ('Без нито една грешка!','+5 точки'))
  pg.click('[data-lclose]')
  # stored on the device
  pg.reload();pg.wait_for_timeout(400);pg.click('.tab[data-v="life"]');pg.click('[data-lifeall="3"]');pg.wait_for_timeout(200)
  check('L22 kept after reopening the app', (pg.evaluate("[...document.querySelectorAll('[data-lunit=\"u1\"] .lnode')].map(n=>n.className.replace('lnode','').trim())"),pg.inner_text('.lrnhead').split('\n')[0]),
        (['done','done','cur','lock'],'30 точки'))
  # streak
  pg.evaluate("LRN.days=['%s','%s','%s'];render()"%(D(3),D(2),D(1)))
  s1=pg.inner_text('.lrnhead').split('\n')[1]
  pg.evaluate("LRN.days=['%s','%s','%s','%s'];render()"%(D(3),D(2),D(1),TS));s2=pg.inner_text('.lrnhead').split('\n')[1]
  pg.evaluate("LRN.days=['%s','%s'];render()"%(D(4),D(2)));s3=pg.inner_text('.lrnhead').split('\n')[1]
  check('L23 the streak: yesterday still counts, today adds one, a missed day starts over', (s1,s2,s3), ('🔥 3 дни подред','🔥 4 дни подред','🔥 0 дни подред'))
  # merging two devices, and backups
  m=pg.evaluate("""(()=>{const a={v:1,d:{u1a:{n:2,p:1,t:'2026-11-20'}},x:{u1a2:{s:3,w:2,t:'2026-11-20'}},days:['2026-11-20'],pr:1},
      b={v:1,d:{u1a:{n:1,p:1,t:'2026-11-22'},u1b:{n:1,p:0,t:'2026-11-22'}},x:{u1a2:{s:1,w:0,t:'2026-11-22'}},days:['2026-11-22'],pr:0},
      r=lrnMerge(a,b),r2=lrnMerge(r.v,b);return [r.v.d,r.v.x,r.v.days,r.v.pr,r.ch>0,r2.ch];})()""")
  check('L24 two devices merge without losing anything (most times, latest date, every day) - and merging again changes nothing',
        m,[{'u1a':{'n':2,'p':1,'t':'2026-11-22'},'u1b':{'n':1,'p':0,'t':'2026-11-22'}},{'u1a2':{'s':3,'w':2,'t':'2026-11-22'}},['2026-11-20','2026-11-22'],1,True,0])
  check('L25 the backup carries the progress', json.loads(pg.evaluate("bakData()")).get('lrn',{}).get('d',{}).get('u1b',{}).get('p'), 1)
  pg.evaluate("mergeIn({obs:OBS,lrn:{d:{u1c:{n:1,p:0,t:'%s'}},days:['%s']}});render()"%(TS,TS))
  check('L26 progress from the other device (sync) is merged in: „Тялото на птицата“ ✓ appears', pg.evaluate("[...document.querySelectorAll('[data-lunit=\"u1\"] .lnode')].map(n=>n.className.replace('lnode','').trim())"), ['done','done','done','cur'])
  # the content itself
  bad=pg.evaluate("""(()=>{const e=[],ids=new Set(),dash=/[—–]/,word=/(^|[^А-Яа-я])[Вв]пиш|[Пп]ълнот/;
    for(const u of COURSE.units)for(const l of u.ls)for(const x of l.ex){if(ids.has(x.id))e.push('dup '+x.id);ids.add(x.id);
      const t=JSON.stringify(x);if(dash.test(t)||word.test(t))e.push('words '+x.id);
      if(x.k==='ch'&&!(x.o.length>=2))e.push('opts '+x.id);if(x.k==='pic'&&x.o.some(o=>!LPIC[o.p]))e.push('pic '+x.id);
      if(x.k==='tap'&&!LPARTS[x.a])e.push('part '+x.id);if(x.k==='info'&&x.pic&&x.pic!=='diagram'&&!LPIC[x.pic])e.push('infopic '+x.id);}
    return [e,ids.size];})()""")
  check('L27 the content holds together: unique ids, real pictures and parts, short dashes only, no „впиши“/„пълнота“', bad, [[],124])
  # chapter 2 opens after chapter 1; pictures of beaks; a chapter put in later doesn't lock what you've started
  pg.click('[data-lstart="u1d"]');finish(pg);pg.click('[data-lclose]');pg.wait_for_timeout(150)
  check('L31 finishing chapter 1 opens „Пера и цветове“ with its first lesson', (pg.evaluate("document.querySelector('[data-lunit=\"u3\"]').classList.contains('locked')"),
        pg.evaluate("[...document.querySelectorAll('[data-lunit=\"u3\"] .lnode')].map(n=>n.className.replace('lnode','').trim())")), (False,['cur','lock','lock','lock']))
  pg.evaluate("for(const l of ['u3a','u3b','u3c','u3d'])LRN.d[l]={n:1,p:0,t:'%s'};render()"%TS);pg.click('[data-lstart="u4a"]');pg.wait_for_timeout(150)
  info=(pg.locator('#lrBody .linfo .lpic').count(),pg.inner_text('#lrBody h3'));pg.click('[data-lnext]');pg.wait_for_timeout(100)
  check('L32 „Клюнове и храна“: a card with a drawn beak, then three beaks to choose from', (info,cur(pg)['k'],pg.locator('#lrBody .lpics .lopt svg').count(),
        sorted(pg.evaluate("[...document.querySelectorAll('#lrBody .lpics .lopt')].map(b=>b.textContent)"))), ((1,'Клюнът е инструмент'),'pic',3,['Къс и дебел','С кука','Тънък и остър']))
  pg.click('[data-lclose]');pg.wait_for_timeout(100)
  pg.evaluate("COURSE.units.splice(1,0,{id:'ux',t:'Нова глава',d:'',ls:[{id:'uxa',t:'Нов урок',ex:[{id:'uxa1',k:'info',t:'a',x:'b'}]}]});render()")
  lock=pg.evaluate("Object.fromEntries([...document.querySelectorAll('.lunit[data-lunit]')].map(u=>[u.dataset.lunit,u.classList.contains('locked')]))")
  pg.evaluate("COURSE.units.splice(1,1);render()")
  check('L33 a chapter put in later before the others: it opens after chapter 1, and a chapter you have started stays open', lock,
        {'u1':False,'ux':False,'u3':False,'u4':False,'u5':True})
  check('L28 no page errors', pg.errs, [])
  # an empty journal: the lessons are still there
  e=page([])
  e.click('.tab[data-v="life"]');e.wait_for_timeout(200)
  btn=e.locator('#view [data-lifeall="3"]').count();e.click('#view [data-lifeall="3"]');e.wait_for_timeout(200)
  check('L29 with an empty journal, Видове offers „🎓 Уроци за птиците“, and the lessons open', (btn,e.locator('[data-lunit="u1"] .lnode').count(),e.errs), (1,4,[]))
  # two devices on one account
  st=Stack('/home/claude/supabase-setup.sql')
  def dev():
    ctx=b.new_context(viewport={'width':390,'height':844});d=ctx.new_page();d.errs=[]
    d.on('pageerror',lambda x:d.errs.append(str(x)));d.on('dialog',lambda x:x.accept())
    ctx.route(SB+'/**',st.handle);ctx.route(CDN,lambda r:r.fulfill(path=UMD,headers={'access-control-allow-origin':'*','content-type':'application/javascript'}))
    d.add_init_script("if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-v3','[]');localStorage.setItem('bird-journal-tips','{\"all\":1}');sessionStorage.setItem('s','1')}")
    d.goto(f'http://localhost:{port}/learn-test.html');d.wait_for_timeout(300);d.click('#acct');return d
  synced=lambda d:d.wait_for_function("!syncing&&sbStat.length>0",timeout=15000)
  def sync(d):d.evaluate("lastSync=0");d.evaluate("syncNow()");d.wait_for_timeout(150);synced(d)
  ph=dev();ph.fill('#sb-name','Иван');ph.fill('#sb-mail','ivan@test.bg');ph.fill('#sb-pw','птица123');ph.click('[data-sb="up"]');ph.wait_for_selector('.fr .msg')
  st.confirm('ivan@test.bg');ph.click('[data-sb="in"]');synced(ph)
  ph.evaluate("view='life';LIFEALL=3;render()");ph.click('[data-lstart="u1a"]');finish(ph);ph.click('[data-lclose]');sync(ph)
  lap=dev();lap.fill('#sb-mail','ivan@test.bg');lap.fill('#sb-pw','птица123');lap.click('[data-sb="in"]');synced(lap)
  lap.evaluate("view='life';LIFEALL=3;render()")
  got1=(lap.evaluate("lrnDone('u1a')"),lap.inner_text('.lrnhead').split('\n')[0])
  lap.click('[data-lstart="u1b"]');finish(lap);lap.click('[data-lclose]');sync(lap);sync(ph)
  check('L30 sync: a lesson done on the phone is done on the laptop too, and the other way round; same points on both',
        (got1,ph.evaluate("[lrnDone('u1a'),lrnDone('u1b')]"),ph.evaluate("lrnXP()")==lap.evaluate("lrnXP()"),'lrn' in st.journal(st.uid('ivan@test.bg')),ph.errs+lap.errs),
        ((True,'15 точки'),[True,True],True,True,[]))
  b.close()
finally:
  srv.terminate()
  if st:st.stop()
print('FAILURES:',fails)
