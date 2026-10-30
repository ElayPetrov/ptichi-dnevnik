import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k:{**dict(id=0,date='2026-10-27',time='12:00',place='Копринка',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
port=int(sys.argv[1]) if len(sys.argv)>1 else 8982;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
data=[R(id=i+1,bg='Кос',date=f'2026-10-{i%27+1:02d}') for i in range(30)]+[R(id=40,bg='Сойка'),R(id=41,bg='Горска дърволазка',u=1)]
WAV=open('/home/claude/silence.wav','rb').read();asked=[]
X=lambda i,t,c='Bulgaria':{'id':str(i),'file':'https://xeno-canto.org/%d/download'%i,'rec':'Петър Рекордист','lic':'//creativecommons.org/licenses/by-nc-sa/4.0/','cnt':c,'url':'//xeno-canto.org/%d'%i,'len':'0:20','q':'A'}
def fn(route):
  sp=route.request.url.split('sp=')[1];asked.append(sp)
  d={'song':X(1001,'song'),'call':X(1002,'call','Romania')} if 'Turdus' in sp else {'song':X(2001,'song'),'call':None}
  route.fulfill(status=200,content_type='application/json',body=json.dumps(d))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required']);ctx=b.new_context(viewport={'width':390,'height':844})
  ctx.route('https://szyituwdlbwpqkfuklxq.supabase.co/functions/v1/xc**',fn)
  ctx.route('https://xeno-canto.org/**',lambda r:r.fulfill(status=200,content_type='audio/wav',body=WAV))
  ctx.route('https://*.wikipedia.org/**',lambda r:r.abort())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  pg.add_init_script("if(!localStorage.getItem('bird-journal-v3'))localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(data,ensure_ascii=False)))
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400);pg.evaluate("yayHide&&yayHide()")
  links=pg.evaluate("[...document.querySelectorAll('#view .o .nm')].slice(0,40).map(n=>[n.textContent.split(' ·')[0],!!n.querySelector('[data-sprf]')])")
  check('S1 in Дневник every bird\'s name opens its card (an unsure-only bird gets the lighter one)', (['Кос',True] in links,['Горска дърволазка',True] in links), (True,True))
  pg.evaluate("for(const d of new Set(OBS.map(o=>o.date)))setDay(d,true);render()")   # all days open, so there is something to scroll
  nm=pg.locator('[data-sprf]:visible').filter(has_text='Кос').nth(4);nm.scroll_into_view_if_needed();pg.wait_for_timeout(100);y0=pg.evaluate("Math.round(scrollY)");nm.click();pg.wait_for_timeout(300)
  check('S2 ...it opens the bird\'s page, with „← Дневник“ to go back', (pg.evaluate("view"),pg.inner_text('[data-spback]')), ('life','← Дневник'))
  pg.wait_for_selector('.xcw.has',timeout=5000)
  check('S3 under the picture: small „▶ песен“ and „▶ обаждане“', pg.evaluate("[...document.querySelectorAll('.spd .xcb button')].map(b=>b.textContent)"), ['▶ песен','▶ обаждане'])
  pg.click('[data-xcplay="song"]');pg.wait_for_timeout(300)
  check('S4 tapping plays it, with the recordist and licence shown and linked', (pg.evaluate("!!xcAud&&!xcAud.paused"),pg.inner_text('[data-xcplay="song"]'),pg.inner_text('.spd .xccr'),pg.get_attribute('.spd .xccr','href')),
    (True,'■ песен','XC1001 · Петър Рекордист · CC BY-NC-SA 4.0 · xeno-canto (Bulgaria)','https://xeno-canto.org/1001'))
  pg.click('[data-xcplay="call"]');pg.wait_for_timeout(300)
  check('S5 one sound at a time: the call replaces the song', (pg.inner_text('[data-xcplay="song"]'),pg.inner_text('[data-xcplay="call"]'),'Romania' in pg.inner_text('.spd .xccr')), ('▶ песен','■ обаждане',True))
  pg.click('[data-xcplay="call"]');pg.wait_for_timeout(150)
  check('S6 tapping again stops it', (pg.evaluate("xcAud"),pg.inner_text('[data-xcplay="call"]')), (None,'▶ обаждане'))
  pg.click('[data-xcplay="song"]');pg.wait_for_timeout(200);pg.click('[data-spback]');pg.wait_for_timeout(250)
  check('S7 „← Дневник“ goes back to the same spot, and the sound stops', (pg.evaluate("view"),abs(pg.evaluate("Math.round(scrollY)")-y0)<=3,pg.evaluate("xcAud")), ('log',True,None))
  pg.click('.tab[data-v="life"]');pg.locator('.sp .nm',has_text='Сойка').first.click();pg.wait_for_selector('.xcw.has',timeout=5000)
  check('S8 a bird without a call recording gets only „▶ песен“; from Моите видове the button says „← Моите видове“', (pg.evaluate("[...document.querySelectorAll('.spd .xcb button')].map(b=>b.textContent)"),pg.inner_text('[data-spback]')), (['▶ песен'],'← Моите видове'))
  pg.click('[data-spback]');pg.locator('.sp .nm',has_text='Кос').first.click();pg.wait_for_selector('.xcw.has',timeout=5000)
  check('S9 the choice is remembered: the helper is asked once per bird', sorted(asked), ['Garrulus%20glandarius','Turdus%20merula'])
  pg.click('.tab[data-v="log"]');pg.click('#toggle');pg.fill('#f-bg','Кос');pg.locator('#f-bg').dispatch_event('change');pg.click('#f-unsure');pg.fill('#f-alt-in','Сойка');pg.click('#f-alt-add');pg.click('#f-cmp')
  pg.wait_for_function("document.querySelectorAll('#cmp-list .xcw.has').length===2",timeout=5000)
  pg.locator('#cmp-list [data-xcplay="song"]').first.click();pg.wait_for_timeout(250);on=pg.evaluate("!!xcAud");pg.click('#cmp-close');pg.wait_for_timeout(100)
  check('S10 „Сравни“ has the same buttons under each candidate; closing it stops the sound', (on,pg.evaluate("xcAud")), (True,None))
  pg.click('#cancel')
  ctx.unroute('https://szyituwdlbwpqkfuklxq.supabase.co/functions/v1/xc**');ctx.route('https://szyituwdlbwpqkfuklxq.supabase.co/functions/v1/xc**',lambda r:r.abort())
  pg.evaluate("XCI={};lsSet(KXC,XCI)");pg.click('.tab[data-v="life"]');pg.locator('.sp .nm',has_text='Кос').first.click();pg.wait_for_timeout(800)
  check('S11 if the helper can\'t be reached, no buttons and no errors', (pg.locator('.spd .xcw.has').count(),errs), (0,[]))
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
