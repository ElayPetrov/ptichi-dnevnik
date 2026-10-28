import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
port=int(sys.argv[1]) if len(sys.argv)>1 else 8970;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
REC="(o=>({id:0,date:'2026-10-27',time:'12:00',place:'',count:'',bg:'',en:'',la:'',fam:'',note:'',h:0,s:1,p:0,beh:[],geo:null,photo:null,...o}))"
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844},timezone_id='Europe/Sofia');pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(300)
  def val(recs,ids,outs='[]'):
    return pg.evaluate(f"(()=>{{const R={REC};let i=1;OBS=({recs}).map(o=>R({{id:i++,...o}}));OUTS={outs};const T=tiersNow();return {json.dumps(ids)}.map(k=>[T[k].v,T[k].t]);}})()")
  d=lambda n:f"'2026-{(n//28)%12+1:02d}-{n%28+1:02d}'"
  check('B1 Неуморен counts honestly: ten sparrows in one place on one day are one record, on ten days ten',
    val("[...Array(10)].map(()=>({bg:'Врабче',place:'Тюлбето'})).concat([...Array(10)].map((_,j)=>({bg:'Сврака',place:'Тюлбето',date:'2026-09-'+String(j+1).padStart(2,'0')})))",['records']), [[11,0]])
  check('B2 Изследовател: a walk with a bird every 100 m is one or two places, points 5 km apart are each a place',
    val("[...Array(10)].map((_,j)=>({bg:'Кос',geo:(42.62+j*0.0009).toFixed(4)+',25.39'})).concat([...Array(5)].map((_,j)=>({bg:'Кос',geo:(42.7+j*0.045).toFixed(4)+',25.39'})))",['places'])[0][0]<=7, True)
  check('B3 Моят участък: 30 days at one spot is bronze (25)', val("[...Array(30)].map((_,j)=>({bg:'Кос',geo:'42.6210,25.3920',date:"+"'2026-'+String(Math.floor(j/28)+1).padStart(2,'0')+'-'+String(j%28+1).padStart(2,'0')}))",['patch']), [[30,1]])
  check('B4 Постоянство: the best 365-day stretch counts, so a quiet year doesn\'t erase a busy one',
    val("[...Array(60)].map((_,j)=>({bg:'Кос',date:'2024-'+String(Math.floor(j/28)+1).padStart(2,'0')+'-'+String(j%28+1).padStart(2,'0')})).concat([{bg:'Кос',date:'2026-05-05'}])",['steady']), [[60,1]])
  sp26=json.dumps(['Сврака','Сойка','Кос','Чинка','Голям синигер','Син синигер','Гугутка','Щиглец','Врабче','Зеленика','Голям пъстър кълвач','Сив кълвач','Сирийски пъстър кълвач','Малък пъстър кълвач','Червеногръдка','Дрозд певец','Скорец','Сива врана','Гарван','Чучулига','Бяла стърчиопашка','Полска врабчица','Испанско врабче','Голяма белочела гъска','Зеленоглава патица','Сива чапла','Голяма бяла чапла','Малка бяла чапла','Лиска','Голям гмурец','Малък гмурец'],ensure_ascii=False)
  check('B5 Богат излет and Голям ден: 26 species on one outing, 31 over two outings that day',
    val(f"{sp26}.slice(0,26).map(n=>({{bg:n,sess:'s1'}})).concat({sp26}.slice(26).map(n=>({{bg:n,sess:'s2'}})))",['bigout','bigday']), [[26,1],[31,1]])
  check('B6 Зимни гости: December and the January–February after it are one winter',
    val(f"{sp26}.slice(0,10).map(n=>({{bg:n,date:'2025-12-20'}})).concat({sp26}.slice(10,27).map(n=>({{bg:n,date:'2026-01-15'}}))).concat({sp26}.slice(0,5).map(n=>({{bg:n,date:'2026-12-20'}})))",['winter']), [[27,1]])
  check('B7 Голямо ято reads counts carefully: „~500“ 500, „10–20“ 10, „3+2“ 5, „1000+“ 1000 (silver)',
    val("[{bg:'Скорец',count:'~500'},{bg:'Гарван',count:'10–20'},{bg:'Сврака',count:'3+2'},{bg:'Бял щъркел',count:'1000+'}]",['flock']), [[1000,2]])
  check('B8 Летописец: a note counts from 20 characters', val("[{bg:'Кос',note:'пее'},{bg:'Сойка',note:'Пееше дълго на върха на ореха.'}]",['notes']), [[1,0]])
  g=pg.evaluate("BDEF.filter(d=>d.id.startsWith('g:')).map(d=>[d.name,d.g])")
  check('B9 group badges scale with the group: Кълвачи 4 / 7 / 9 of 10, Грабливи 10 / 20 / 27 of 29',
    (dict(g)['Кълвачи'],dict(g)['Грабливи'],len(g)), ([4,7,9],[10,20,27],8))
  check('B10 Семейства counts scientific families', val("[{bg:'Сврака'},{bg:'Сойка'},{bg:'Кос'},{bg:'Голям синигер'}]",['fams']), [[3,0]])
  soc=pg.evaluate("""(()=>{ME={id:'me'};FR={fol:[{id:'u2',name:'Петър',data:{obs:[],outs:[{id:'x',date:'2026-10-20',orig:{u:'me',o:'m1'}}]}}],fans:[]};
    SOC=[{owner:'u2',item:'o:x',author:'me',kind:'bravo'},{owner:'me',item:'o:m1',author:'u2',kind:'bravo'},{owner:'me',item:'o:m1',author:'me',kind:'bravo'},
         {owner:'u2',item:'o:x',author:'me',kind:'comment'},{owner:'me',item:'o:m1',author:'me',kind:'comment'}];
    OUTS=[{id:'m1',date:'2026-10-20'},{id:'m2',date:'2026-10-21',with:'Мария',orig:{u:'u3',o:'z'}}];const T=tiersNow();return [T.bravo.v,T.talk.v,T.together.v];})()""")
  check('B11 Браво counts given and received (not to yourself), Събеседник only comments on friends\', Заедно both directions', soc, [2,1,2])
  pg.evaluate("ME=null;FR=null;SOC=[];OUTS=[];")
  # launch: levels already reached show as one summary card, not a flood, and count as seen
  data=[{'id':j+1,'date':f'2026-10-{j+1:02d}','time':'06:00','place':'Тюлбето','count':'','bg':'Кос','en':'','la':'','fam':'','note':'','h':0,'s':1,'p':0,'beh':[],'geo':'42.62,25.39','photo':None} for j in range(5)]
  l=ctx.new_page();l.on('pageerror',lambda e:errs.append(str(e)))
  l.add_init_script("if(!localStorage.getItem('t-once')){localStorage.clear();localStorage.setItem('t-once','1');localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-seen-badges','[\"early\"]');localStorage.setItem('bird-journal-days','{}');}"%json.dumps(json.dumps(data)))
  l.goto(f'http://localhost:{port}/ptichi-dnevnik.html');l.wait_for_timeout(400)
  check('B12 after the update: one card „Новите значки — вече имаш 1 бронзови“, and no dot for them', (l.evaluate("document.getElementById('yay').innerText.replace(/\\n/g,' | ')"),l.evaluate("document.querySelector('.tab[data-v=\"badges\"]').classList.contains('dot')")),
    ('Новите значки | Вече имаш 1 бронзови | Виж ги в „Значки“',False))
  l.evaluate("yayHide()");l.reload();l.wait_for_timeout(400)
  check('B13 ...only once', l.evaluate("document.getElementById('yay').classList.contains('on')"), False)
  # reaching a new level while logging: pop-up, remembered with the record, shown in the feed
  for j in range(19):l.evaluate(f"OBS.push({{id:{100+j},date:'2026-09-{j+1:02d}',time:'06:00',place:'Тюлбето',count:'',bg:'Кос',en:'',la:'',fam:'',note:'',h:0,s:1,p:0,beh:[],geo:'42.62,25.39',photo:null}})")
  l.evaluate("save();render()");l.click('#toggle');l.fill('#f-bg','Сойка');l.fill('#f-date','2026-08-20');l.fill('#f-time','06:10');l.click('#savebtn');l.wait_for_timeout(300)
  txt=[]
  for _ in range(3):txt.append(l.evaluate("document.getElementById('yay').innerText"));l.evaluate("yayHide()");l.wait_for_timeout(450)
  txt=' || '.join(txt)
  check('B14 the 25th morning before sunrise: „Нова значка! Ранобудник — сребро“', 'Ранобудник — сребро' in txt, True)
  rid=l.evaluate("OBS.find(o=>o.bg==='Сойка').id")
  check('B15 ...remembered with that record (it travels with the journal for the friends\' feed)', l.evaluate("BDG['early:2']&&BDG['early:2'].r"), rid)
  l.evaluate("ME={id:'me',email:'i@t.bg'};MYNAME='Иван';FR={fol:[],fans:[]};");l.click('.tab[data-v="friends"]');l.wait_for_timeout(300)
  if l.locator('[data-feedmore]').count():l.click('[data-feedmore]');l.wait_for_timeout(300)   # that day is older than the first 20 cards
  check('B16 the feed card of that day shows „значка: Ранобудник — сребро“', 'значка: Ранобудник — сребро' in l.inner_text('#view'), True)
  l.click('.tab[data-v="badges"]');l.wait_for_timeout(200)
  check('B17 Значки: six sections, 31 badges, „от 93 нива“, and the new silver marked „ново“',
    (l.evaluate("[...document.querySelectorAll('.bdsec')].map(h=>h.textContent)"),l.locator('.bd2').count(),'от 93 нива' in l.inner_text('.bdintro'),
     l.evaluate("[...document.querySelectorAll('.bd2.new b')].map(b=>b.firstChild.textContent)")),
    (['На терен','Списъкът','Сезони','Наука','Приятели','Семейства'],31,True,['Ранобудник']))
  check('B18 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
