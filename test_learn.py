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
cur=lambda pg:pg.evaluate("LP&&LP.q[LP.i]?{k:LP.q[LP.i].k,id:LP.q[LP.i].id,a:LP.q[LP.i].a,n:(LP.q[LP.i].p||LP.q[LP.i].o||[]).length,d:LP.q[LP.i].d}:null")
# a real tap on a detailed drawing, at the point where the part's label line would end (its anchor)
TAPXY="k=>{const sv=document.querySelector('#lrBody svg.ltopo'),x=LP.q[LP.i],it=lrnTopoItem(x.d,k),p=sv.createSVGPoint();p.x=it[4][0];p.y=it[4][1];const q=p.matrixTransform(sv.getScreenCTM());return [q.x,q.y]}"
def tap(pg,k):pg.mouse.click(*pg.evaluate(TAPXY,k));pg.wait_for_timeout(40)
def other(pg,k):return pg.evaluate("k=>{const x=LP.q[LP.i],G=lrnTopoG(x.d),[x0,y0,w,h]=(G.views[x.v]||G.views.full).split(' ').map(Number);"
  "return (x.d==='E'?G.marks:G.seq).filter(it=>typeof it!=='string'&&it[0]!==k&&it[4][0]>x0+2&&it[4][0]<x0+w-2&&it[4][1]>y0+2&&it[4][1]<y0+h-2)[0][0]}",k)
def answer(pg,right=True):   # answers whatever is on screen; returns its kind
  x=cur(pg)
  if not x:return None
  k=x['k']
  if k in('info','dx'):pg.click('[data-lnext]');return k
  if k=='ord':
    if not right:pg.click('[data-lord="1"]')
    for i in range(x['n']):pg.click(f'[data-lord="{i}"]')
  elif k=='dt':tap(pg,x['a'] if right else other(pg,x['a']));pg.click('[data-lcheck]')
  elif k=='pr':
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
  def page(data,w=390,store=None,dark=False):
    ctx=b.new_context(viewport={'width':w,'height':844},color_scheme='dark' if dark else 'light');pg=ctx.new_page();pg.errs=[]
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
  check('L2 the path: five chapters, the first open with its first lesson, the rest locked; the coming ones listed by name, the guide chapter first; 0 points, no „Упражнявай“ yet; no search or filters',
        (pg.evaluate("[...document.querySelectorAll('.lunit:not(.soon)')].map(u=>u.querySelector('h3').textContent+(u.classList.contains('locked')?' (locked)':''))"),
         pg.evaluate("[...document.querySelectorAll('[data-lunit=\"u1\"] .lnode')].map(n=>[n.querySelector('.lname').textContent,n.className.replace('lnode','').trim(),n.disabled])"),
         pg.evaluate("document.querySelector('.lunit.soon p').innerText.split('\\n')"),pg.inner_text('.lrnhead').split('\n')[0],pg.locator('[data-lprac]').count(),
         pg.is_visible('#q'),pg.is_visible('#filters')),
        (['Какво е птица','Части на тялото на птица (locked)','Пера и цветове (locked)','Клюнове и храна (locked)','Крака и полет (locked)'],
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
  check('L27 the content holds together: unique ids, real pictures and parts, short dashes only, no „впиши“/„пълнота“', bad, [[],225])
  # chapter 2 opens after chapter 1; pictures of beaks; a chapter put in later doesn't lock what you've started
  pg.click('[data-lstart="u1d"]');finish(pg);pg.click('[data-lclose]');pg.wait_for_timeout(150)
  check('L31 finishing chapter 1 opens „Части на тялото на птица“ with its first lesson; „Пера и цветове“ waits for it',
        (pg.evaluate("document.querySelector('[data-lunit=\"u2\"]').classList.contains('locked')"),
         pg.evaluate("[...document.querySelectorAll('[data-lunit=\"u2\"] .lnode')].map(n=>n.className.replace('lnode','').trim())"),
         pg.evaluate("document.querySelector('[data-lunit=\"u3\"]').classList.contains('locked')")), (False,['cur']+['lock']*7,True))
  pg.evaluate("for(const l of ['u3a','u3b','u3c','u3d'])LRN.d[l]={n:1,p:0,t:'%s'};render()"%TS);pg.click('[data-lstart="u4a"]');pg.wait_for_timeout(150)
  info=(pg.locator('#lrBody .linfo .lpic').count(),pg.inner_text('#lrBody h3'));pg.click('[data-lnext]');pg.wait_for_timeout(100)
  check('L32 „Клюнове и храна“: a card with a drawn beak, then three beaks to choose from', (info,cur(pg)['k'],pg.locator('#lrBody .lpics .lopt svg').count(),
        sorted(pg.evaluate("[...document.querySelectorAll('#lrBody .lpics .lopt')].map(b=>b.textContent)"))), ((1,'Клюнът е инструмент'),'pic',3,['Къс и дебел','С кука','Тънък и остър']))
  pg.click('[data-lclose]');pg.wait_for_timeout(100)
  pg.evaluate("COURSE.units.splice(1,0,{id:'ux',t:'Нова глава',d:'',ls:[{id:'uxa',t:'Нов урок',ex:[{id:'uxa1',k:'info',t:'a',x:'b'}]}]});render()")
  lock=pg.evaluate("Object.fromEntries([...document.querySelectorAll('.lunit[data-lunit]')].map(u=>[u.dataset.lunit,u.classList.contains('locked')]))")
  pg.evaluate("COURSE.units.splice(1,1);render()")
  check('L33 a chapter put in later before the others: it opens after chapter 1, and a chapter you have started stays open', lock,
        {'u1':False,'ux':False,'u2':True,'u3':False,'u4':False,'u5':True})
  # ---- chapter 2: the body parts in the guide's words (2026-11-23.4) ----
  L=lambda u:pg.evaluate("[...document.querySelectorAll('[data-lunit=\"%s\"] .lnode')].map(n=>n.className.replace('lnode','').trim())"%u)
  TXT=lambda sel:pg.evaluate("s=>document.querySelector(s).textContent",sel)
  ON=lambda c:pg.evaluate("c=>[...document.querySelectorAll('#lrBody .tp.'+c)].map(g=>g.className.baseVal.split(' ')[1].slice(3))",c)
  pg.click('[data-lstart="u2a"]');pg.wait_for_timeout(150)
  check('L34 „Главата“ opens with an explore card: the head drawn big, the eight words of the guide to tap, nothing lit yet',
        (cur(pg)['k'],pg.inner_text('#lrBody h3'),pg.evaluate("[...document.querySelectorAll('#lrBody [data-lx]')].map(b=>b.textContent)"),
         pg.locator('#lrBody svg.ltopo.lex').count(),ON('hl'),pg.inner_text('#lrFoot')),
        ('dx','Главата',['теме','чело','тил','ушни пера','ноздра','кулмен','подбрадие','гърло'],1,[],'Продължи'))
  pg.click('#lrBody [data-lx="nozdra"]');pg.wait_for_timeout(60)
  a=(ON('hl'),pg.inner_text('#lrBody .lxcap'),pg.locator('#lrBody .thlr').count(),pg.evaluate("document.querySelector('[data-lx=\"nozdra\"]').getAttribute('aria-pressed')"))
  tap(pg,'til')
  check('L35 a word lights its part in blue (with a ring round a tiny one like the nostril) and names it; tapping the drawing picks the word; seen words get a tick',
        (a,ON('hl'),pg.inner_text('#lrBody .lxcap'),pg.locator('#lrBody .thlr').count(),pg.evaluate("[...document.querySelectorAll('#lrBody .lchip.seen')].map(b=>b.dataset.lx)")),
        ((['nozdra'],'ноздра',1,'true'),['til'],'тил',0,['til','nozdra']))
  pg.click('[data-lnext]');pg.wait_for_timeout(60)
  check('L36 „Докосни частта“: the guide\'s word written big, the head drawn with all 30 parts of the bird tappable',
        (cur(pg)['k'],TXT('#lrBody .lkind'),pg.inner_text('#lrBody .lq'),pg.locator('#lrBody svg.ltopo:not(.lab)').count(),pg.locator('#lrBody [data-lpart]').count()),
        ('dt','Докосни частта','теме',1,30))
  tap(pg,'til');sel=pg.evaluate("[...document.querySelectorAll('#lrBody .lp.sel')].map(e=>e.dataset.lpart)");n0=pg.evaluate("LP.q.length");pg.click('[data-lcheck]');pg.wait_for_timeout(60)
  check('L37 a wrong tap: blue, then red; the wanted part green; „Докосна „тил“ - търсената част е в зелено.“; the question comes back at the end',
        (sel,pg.evaluate("[...document.querySelectorAll('#lrBody .lp.bad')].map(e=>e.dataset.lpart)"),pg.evaluate("[...document.querySelectorAll('#lrBody .lp.ok')].map(e=>e.dataset.lpart)"),
         pg.inner_text('#lrFoot .lfb'),pg.evaluate("LP.q.length")-n0),
        (['til'],['til'],['teme'],'Не съвсем.\nДокосна „тил“ - търсената част е в зелено.',1))
  pg.click('[data-lnext]');tap(pg,'chelo');pg.click('[data-lcheck]');pg.wait_for_timeout(60)
  check('L38 the right part, tapped where the guide\'s line points: „Точно така!“', (pg.inner_text('#lrFoot .lfb b'),pg.evaluate("[...document.querySelectorAll('#lrBody .lp.ok')].map(e=>e.dataset.lpart)")),
        ('Точно така!',['chelo']))
  pg.click('[data-lnext]');pg.wait_for_timeout(60)
  check('L39 „Как се казва синята част?“: only the nape lit, the drawing not tappable, three words of the guide to choose from',
        (cur(pg)['k'],pg.inner_text('#lrBody .lq'),ON('hl'),pg.locator('#lrBody svg.ltopo.lab').count(),pg.locator('#lrBody [data-lpart]').count(),
         sorted(pg.evaluate("[...document.querySelectorAll('#lrBody [data-lopt]')].map(b=>b.textContent)"))),
        ('dn','Как се казва синята част?',['til'],1,0,['теме','тил','ушни пера']))
  finish(pg)
  end=pg.inner_text('.lend .lstats span:first-child').replace('\n',' ');pg.click('[data-lclose]');pg.wait_for_timeout(150)
  check('L40 „Главата“ done (+10, there was a slip): ✓ on the path and „Отгоре“ opens', (end,L('u2')), ('+10 точки',['done','cur']+['lock']*6))
  pg.click('[data-lstart="u2b"]');pg.evaluate("LP.i=8;lrnDraw()");pg.wait_for_timeout(60)
  o0=(cur(pg)['k'],pg.locator('#lrBody [data-lord]').count(),pg.locator('[data-lcheck]').count())
  pg.click('[data-lord="0"]');pg.click('[data-lord="2"]');pg.wait_for_timeout(40)
  mid=(pg.evaluate("[...document.querySelectorAll('#lrBody .lordans span')].map(s=>s.textContent)"),pg.evaluate("document.querySelector('[data-lord=\"2\"]').className"))
  for i in range(1,6):pg.click(f'[data-lord="{i}"]')
  check('L41 „Подреди“: the words shuffled, no „Провери“; one out of turn shakes and stays; the right ones line up with arrows; at the end „Готово!“, remembered as a slip',
        (o0,mid,TXT('#lrBody .lordans'),pg.inner_text('#lrFoot .lfb b'),pg.evaluate("LRN.x.u2b9.w")),
        (('ord',6,0),(['тил'],'lopt shake'),'тил→мантия→гръб→кръст→надопашие→опашка','Готово!',1))
  pg.click('[data-lclose]');pg.evaluate("lrnStart('u2c');LP.i=8;lrnDraw()");pg.wait_for_timeout(60)
  check('L42 a card with the guide\'s own words: marked „В определителя“, quoted word for word; the two parts compared in blue and orange',
        (pg.inner_text('#lrBody h3'),TXT('#lrBody .lguide small'),pg.evaluate("document.querySelector('#lrBody .lguide').textContent.includes('пищял - частта от крака над стъпалото (виж по-долу), разговорно наричана „бедро“.')"),ON('hl'),ON('hl2')),
        ('Пищял и стъпало','В определителя',True,['pishtal'],['stapalo']))
  pg.evaluate("lrnClose();lrnStart('u2e');LP.i=5;lrnDraw()");pg.wait_for_timeout(60)
  nums=pg.evaluate("[...document.querySelectorAll('#lrBody .tnum text')].map(t=>t.textContent).sort((a,b)=>a-b)")
  pg.evaluate("LP.i=6;lrnDraw()");pg.wait_for_timeout(60)
  check('L43 „Крило отгоре“: the card numbers the primaries 1-10 as the guide does; in the question the numbers are gone and one feather is blue',
        (nums,pg.locator('#lrBody .tnum').count(),pg.evaluate("[...document.querySelectorAll('#lrBody path.hl')].map(p=>p.dataset.lf)"),pg.inner_text('#lrBody .lq')),
        (['1','2','3','4','5','6','7','8','9','10'],0,['p2'],'Кой номер е синьото перо?'))
  pg.evaluate("lrnClose();lrnStart('u2g');LP.i=2;lrnDraw()");pg.wait_for_timeout(60)
  check('L44 „Белезите“: the warbler\'s eight marks are what you tap - the bird under them is not',
        sorted(pg.evaluate("[...document.querySelectorAll('#lrBody [data-lpart]')].map(e=>e.dataset.lpart)")),sorted(['vrah_ram','panel_vtori','iv_golemi','iv_sredni','petno_parvi','vrah_parv','petno_krast','yuzdichka']))
  pg.evaluate("lrnClose()")
  res=pg.evaluate("""()=>{const out=[];const box=document.createElement('div');box.style.cssText='position:fixed;left:0;top:0;width:340px;background:#fff;z-index:99999';document.body.appendChild(box);
    for(const d of ['A','C','D','E']){const G=lrnTopoG(d);
      for(const v of Object.keys(G.views)){box.innerHTML=lrnTopo(d,{v,mode:'tap'});const sv=box.querySelector('svg'),[x0,y0,w,h]=G.views[v].split(' ').map(Number);
        for(const it of (d==='E'?G.marks:G.seq)){if(typeof it==='string')continue;const a=it[4];
          if(a[0]<x0+2||a[0]>x0+w-2||a[1]<y0+2||a[1]>y0+h-2)continue;
          const pt=sv.createSVGPoint();pt.x=a[0];pt.y=a[1];const q=pt.matrixTransform(sv.getScreenCTM()),el=document.elementFromPoint(q.x,q.y),g=el&&el.closest('[data-lpart]');
          out.push([d,v,it[0],g?g.dataset.lpart:null]);}}}
    box.remove();return out;}""")
  check('L45 every part on every drawing and zoom is tapped right at the point where the guide\'s line ends (117 places)', (len(res),[r for r in res if r[2]!=r[3]]), (117,[]))
  bad=pg.evaluate("""(()=>{const e=[],T=Object.values(LTERM);for(const u of COURSE.units)for(const l of u.ls)for(const x of l.ex){
     if(!(['dt','dn','dx'].includes(x.k)||x.d))continue;if(!LTOPO[x.d==='E'?'A':x.d]){e.push('drawing '+x.id);continue;}
     const has=k=>!!lrnTopoItem(x.d,k)||(x.d==='C'&&/^p([2-9]|10)$/.test(k));
     if(x.k==='dt'&&!has(x.a))e.push('dt '+x.id);
     if(x.k==='dn'&&(!has(x.h)||(lrnTopoItem(x.d,x.h)&&x.o[0]!==LTERM[x.h])||x.o.some(o=>!/^\\d+$/.test(o)&&!T.includes(o))))e.push('dn '+x.id);
     if(x.k==='dx'&&x.l.some(k=>!has(k)))e.push('dx '+x.id);
     for(const h of [...(x.hl||[]),...(x.hl2||[])])if(!has(h))e.push('hl '+x.id);}
   return [e,T.length,COURSE.units[1].ls.length];})()""")
  check('L46 the chapter uses only the guide\'s 48 terms; every lit or tapped part exists on its drawing; the first option is the guide\'s word for the lit part', bad, [[],48,8])
  for l in ['u2b','u2c','u2d','u2e','u2f','u2g','u2h']:pg.evaluate("lrnStart('%s')"%l);pg.wait_for_timeout(60);finish(pg);pg.click('[data-lclose]');pg.wait_for_timeout(60)
  check('L47 the whole chapter plays through - every tap at the guide\'s point, every name, order, pair and card', (L('u2'),pg.errs), (['done']*8,[]))
  keep=pg.evaluate("JSON.stringify(LRN.d)");pg.evaluate("LRN.d=Object.fromEntries(Object.entries(LRN.d).filter(([k])=>k.startsWith('u2')));lrnStart('prac')");pg.wait_for_timeout(60)
  q=pg.evaluate("LP.q.map(x=>x.k)");finish(pg)
  check('L48 practice from the chapter: no explore or info cards, the new kinds work there too', (len(q),'dx' in q or 'info' in q,pg.inner_text('.lend .lstats span:first-child').replace('\n',' ')), (8,False,'+5 точки'))
  pg.click('[data-lclose]');pg.evaluate("LRN.d=JSON.parse(%s);render()"%json.dumps(keep))
  dk=page(OBS,dark=True);dk.click('.tab[data-v="life"]');dk.click('[data-lifeall="3"]');dk.wait_for_timeout(200);dk.evaluate("lrnStart('u2a')");dk.wait_for_timeout(100)
  css=lambda d,sel,prop:d.evaluate("([s,p])=>getComputedStyle(document.querySelector(s))[p]",[sel,prop])
  pg.evaluate("lrnStart('u2a')");pg.wait_for_timeout(100)
  check('L49 dark by the phone\'s own setting (no theme picked in the app): dark text on the light green, and the darker bird colours',
        (css(dk,'.luhead','color'),css(dk,'#lrBody .tp-korem path','fill'),css(pg,'#lrBody .tp-korem path','fill'),dk.errs),
        ('rgb(20, 22, 14)','rgb(214, 205, 182)','rgb(246, 239, 220)',[]))
  pg.evaluate("lrnClose()")
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
