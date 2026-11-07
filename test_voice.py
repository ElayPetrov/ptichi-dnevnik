# Voice recording (2026-11-07.1): the parser (Bulgarian plurals and counted forms, numbers in words, „около/поне“,
# „чух/видях/снимах“, unknown words kept), the 🎙 panel (typed or keyboard-dictated text, live dictation, voice notes),
# drafts saved at once as „за преглед“ (not counted), and review in Дневник. The phone's speech recognition,
# microphone and vibration are stand-ins here.
import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
T=datetime.date.today().isoformat()
port=int(sys.argv[1]) if len(sys.argv)>1 else 9004;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
MOCK="""window.SRLOG=[];window.SpeechRecognition=class{constructor(){SRLOG.push('new');window.LASTSR=this;}
  start(){SRLOG.push('start:'+this.lang+(this.continuous?':cont':':one'));const F=x=>Object.assign([{transcript:x}],{isFinal:true});   // like Chrome on Android: the same final, again and again
    setTimeout(()=>{if(!this.onresult)return;this.onresult({resultIndex:0,results:[F('сойка две кос три')]});this.onresult({resultIndex:0,results:[F('сойка две кос три')]});
      this.onresult({resultIndex:0,results:[F('сойка две кос три'),F('сойка две кос три')]});},60);}
  stop(){SRLOG.push('stop');}};
  navigator.vibrate=p=>{(window.VIB=window.VIB||[]).push(p);return true;};
  navigator.mediaDevices.getUserMedia=async()=>({getTracks:()=>[{stop(){}}]});
  window.MediaRecorder=class{constructor(){this.mimeType='audio/webm';}start(){}stop(){this.ondataavailable({data:new Blob(['abc'],{type:'audio/webm'})});this.onstop();}};"""
P=lambda pg,t:pg.evaluate("t=>vcParse(t).map(e=>(e.unk?'?'+e.raw:e.bg)+(e.count?' ×'+e.count+(e.cq?'('+e.cq+')':''):'')+(e.h&&!e.s?' чут':''))",t)
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();ctx=b.new_context(viewport={'width':390,'height':844});ctx.route('https://**',lambda r:r.abort() if 'localhost' not in r.request.url else r.continue_())
  pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
  pg.add_init_script(MOCK+"if(!sessionStorage.getItem('s')){localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true');sessionStorage.setItem('s','1')}")
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  check('V1 either order and no punctuation: „сойка две кос три чух авлига“', P(pg,'сойка две кос три чух авлига'), ['Сойка ×2','Кос ×3','Авлига чут'])
  check('V2 plurals, counted forms and adjectives agree: „два големи пъстри кълвача“, „пет бели щъркела“', (P(pg,'два големи пъстри кълвача'),P(pg,'пет бели щъркела')), (['Голям пъстър кълвач ×2'],['Бял щъркел ×5']))
  check('V3 numbers in words, approximate and minimum counts', (P(pg,'двайсет и пет скорци'),P(pg,'около двайсет речни чайки'),P(pg,'поне петдесет гугутки'),P(pg,'десетина домашни врабчета')),
    (['Обикновен скорец ×25'],['Речна чайка ×20(est)'],['Гугутка ×50(min)'],['Домашно врабче ×10(est)']))
  check('V4 everyday names and the plain noun for „обикновен…“ species: „козодой“, „чинка“, „мишелов“', (P(pg,'чух козодой'),P(pg,'десет чинки'),P(pg,'мишелов')), (['Европейски козодой чут'],['Обикновена чинка ×10'],['Обикновен мишелов']))
  check('V5b how you met it, in its other forms: „кос, два, сниман“, „чут кос“', (P(pg,'кос, два, сниман'),P(pg,'чут кос')), (['Кос ×2'],['Кос чут']))
  check('V5 what it can’t tell apart, or doesn’t know, is kept for you to fix — never guessed', (P(pg,'три щъркела'),P(pg,'сойка две гос')), (['?щъркела'],['Сойка ×2','?гос']))
  pg.evaluate("SESS={id:'s1',date:'%s',time:'08:00',place:'Копринка',geo:null,at:Date.now(),t0:'08:00'};VCPOS='42.61000,25.30000'"%T)
  pg.click('#vcOpen');pg.wait_for_timeout(150);pg.evaluate("VCPOS='42.61000,25.30000'")
  pg.fill('#vc-text','две сойки, кос три, гос');pg.click('#vc-add');pg.wait_for_timeout(200)
  rs=pg.evaluate("OBS.filter(o=>o.rv).map(o=>[o.bg,o.count,o.u,o.sess,o.place,o.geo,o.date===today(),!!o.time])")
  check('V6 „Добави“: saved at once as drafts — time, date, place, outing and position — even the unknown word', rs,
    [['Сойка','2',1,'s1','Копринка','42.61000,25.30000',True,True],['Кос','3',1,'s1','Копринка','42.61000,25.30000',True,True],['гос','',1,'s1','Копринка','42.61000,25.30000',True,True]])
  check('V7 the panel lists what was just added, the unknown one marked', (pg.locator('#vc-list .vcrow').count(),pg.locator('#vc-list .vcrow.unk').count()), (3,1))
  check('V8 drafts don’t count yet', pg.evaluate("SURE().filter(o=>o.rv).length"), 0)
  pg.click('#vc-done');pg.wait_for_timeout(150)
  check('V9 Дневник: „3 гласови записа чакат преглед“ with „✓ потвърди разпознатите (2)“, and a tag on each', ('3' in pg.inner_text('.rvbar'),pg.inner_text('[data-rvall]'),pg.locator('.rvtag').count(),pg.locator('[data-rvok]').count()),
    (True,'✓ потвърди разпознатите (2)',3,2))
  sid=pg.evaluate("OBS.find(o=>o.rv&&o.bg==='Сойка').id");pg.click(f'[data-rvok="{sid}"]');pg.wait_for_timeout(150)
  check('V10 „✓ потвърди“ makes it a normal record that counts', pg.evaluate(f"(o=>[!!o.rv,o.u,SURE().includes(o)])(OBS.find(o=>o.id==={sid}))"), [False,0,True])
  kid=pg.evaluate("OBS.find(o=>o.rv&&o.bg==='Кос').id");pg.click(f'[data-ed="{kid}"]');pg.wait_for_timeout(150)
  st=pg.evaluate("[document.getElementById('f-unsure').getAttribute('aria-pressed'),document.getElementById('f-bg').value]");pg.click('#savebtn');pg.wait_for_timeout(200)
  check('V11 opening a draft in the form shows it as sure; saving it there clears „за преглед“', (st,pg.evaluate(f"(o=>[!!o.rv,!!o.u])(OBS.find(o=>o.id==={kid}))")), (['false','Кос'],[False,False]))
  pg.click('#cancel') if pg.is_visible('#cancel') else None
  pg.click('[data-rvall]') if pg.locator('[data-rvall]').count() else None;pg.wait_for_timeout(100)
  check('V12 the unknown one stays for you to fix', pg.evaluate("OBS.filter(o=>o.rv).map(o=>o.bg)"), ['гос'])
  pg.click('#vcOpen');pg.wait_for_timeout(150)
  check('V13 Android: the big microphone is there', pg.is_visible('#vc-mic'), True)
  pg.click('#vc-mic');pg.wait_for_timeout(400)
  check('V14 live: Bulgarian, one phrase at a time; the browser re-sending the same phrase doesn\'t add it again (one „кос“ stays one), vibration for each', (pg.evaluate("SRLOG.slice(0,2)"),pg.evaluate("OBS.filter(o=>o.rv&&(o.bg==='Сойка'||o.bg==='Кос')).length"),pg.evaluate("(window.VIB||[]).length>0")), (['new','start:bg-BG:one'],2,True))
  pg.evaluate("LASTSR.onend()");pg.wait_for_timeout(100)
  check('V15 if the browser stops listening after a pause, it starts again until you tap', pg.evaluate("SRLOG.filter(x=>x.startsWith('start')).length"), 2)
  pg.click('#vc-mic');pg.wait_for_timeout(100)
  check('V16 tapping again stops it', (pg.evaluate("SRLOG[SRLOG.length-1]"),pg.evaluate("VON")), ('stop',False))
  pg.click('#vc-memo');pg.wait_for_timeout(150);pg.click('#vc-memo');pg.wait_for_timeout(400)
  pg.click('#vc-done');pg.wait_for_timeout(150)
  check('V17 a voice note is kept on the phone and shows in Дневник with ▶, „превърни в записи“ and ×', (pg.evaluate("VMEMO.length"),pg.locator('[data-vplay]').count(),pg.locator('[data-vconv]').count(),pg.locator('[data-vdel]').count()), (1,1,1,1))
  check('V18 ...its sound is stored', pg.evaluate("getPhoto('v:'+VMEMO[0].id).then(b=>!!b&&b.size)"), 3)
  pg.click('[data-vdel]');pg.wait_for_timeout(150)
  check('V19 × deletes it', pg.evaluate("VMEMO.length"), 0)
  check('V22 English too: „two jays blackbird three heard golden oriole“, with Eurasian/Common left out as people say it', P(pg,'two jays blackbird three heard golden oriole'), ['Сойка ×2','Кос ×3','Авлига чут'])
  check('V23 English counts and plurals: „about twenty black-headed gulls“, „five greylag geese“, „a pair of mallards“, „twenty-five starlings“',
    (P(pg,'about twenty black-headed gulls'),P(pg,'five greylag geese'),P(pg,'a pair of mallards'),P(pg,'twenty-five starlings')),
    (['Речна чайка ×20(est)'],['Сива гъска ×5'],['Зеленоглава патица ×2'],['Обикновен скорец ×25']))
  check('V24 Latin names and mixed sentences; an English word that only looks alike is not guessed („heron“ is not „herring gull“)',
    (P(pg,'Turdus merula 2'),P(pg,'две сойки three blackbirds'),P(pg,'heron two')), (['Кос ×2'],['Сойка ×2','Кос ×3'],['?heron']))
  pg.click('#vcOpen');pg.wait_for_timeout(150);pg.click('[data-vclang="en"]');pg.wait_for_timeout(80);pg.click('#vc-mic');pg.wait_for_timeout(200)
  check('V25 live dictation in English when switched to „English“ — remembered for next time', (pg.evaluate("SRLOG.filter(x=>x.startsWith('start')).pop()"),pg.evaluate("localStorage.getItem('bird-journal-vclang')"),'two jays' in pg.inner_text('#vc-hint')),
    ('start:en-GB:one','"en"',True))
  pg.click('#vc-mic');pg.click('[data-vclang="bg"]');pg.click('#vc-done')
  check('V20 no page errors', errs, [])
  ctx2=b.new_context(viewport={'width':390,'height':844},user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148')
  ctx2.route('https://**',lambda r:r.abort());q=ctx2.new_page()
  q.add_init_script(MOCK+"Object.defineProperty(navigator,'standalone',{get:()=>true});localStorage.setItem('bird-journal-tips','{\"all\":1}')")
  q.goto(f'http://localhost:{port}/ptichi-dnevnik.html');q.wait_for_timeout(400);q.click('#vcOpen');q.wait_for_timeout(150)
  check('V21 iPhone from the Home Screen: no live microphone (unreliable there) — use the keyboard’s microphone in the box', (q.is_visible('#vc-mic'),'микрофона на клавиатурата' in q.inner_text('#vc-hint')), (False,True))
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
