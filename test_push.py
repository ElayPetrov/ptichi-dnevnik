# Release C, part 2 — phone notifications in the app: the profile section (switching on, the five kinds, test, off),
# the iPhone Home Screen hint, blocked permission, sign-out forgetting the phone, and ?go= from a tapped notification.
# The browser's push machinery and Supabase are stand-ins here; the helper itself is tested in test_pushfn.mjs.
import json,subprocess,sys,time,datetime
from playwright.sync_api import sync_playwright
T=datetime.date.today().isoformat()
port=int(sys.argv[1]) if len(sys.argv)>1 else 8998;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
FAKE="""
window.CALLS=[];window.SUBBED=null;window.PERM=window.PERM||'default';
const sub={endpoint:'https://fcm.googleapis.com/fcm/send/xyz',toJSON(){return {endpoint:this.endpoint,keys:{p256dh:'P256',auth:'AUTH'}}},unsubscribe:async()=>{CALLS.push(['unsubscribe']);window.SUBBED=null;return true;}};
const reg={pushManager:{getSubscription:async()=>window.SUBBED,subscribe:async(o)=>{CALLS.push(['subscribe',o.userVisibleOnly,o.applicationServerKey.length]);window.SUBBED=sub;return sub;}}};
try{Object.defineProperty(navigator.serviceWorker,'ready',{get:()=>Promise.resolve(reg)});}catch(e){}
window.Notification={get permission(){return window.PERM},requestPermission:async()=>{CALLS.push(['permission']);if(window.PERM==='default')window.PERM='granted';return window.PERM;}};
const of=window.fetch;window.fetch=async(u,o)=>{if(String(u).includes('/functions/v1/push')){
  window.FNKEYS=(window.FNKEYS||[]).concat([(o&&o.headers&&o.headers.apikey)||null]);
  if(String(u).includes('key=1')){CALLS.push(['key']);return new Response(JSON.stringify({key:'BA'+'x'.repeat(85)}),{status:200});}
  CALLS.push(['post',JSON.parse(o.body)]);return new Response(JSON.stringify({sent:1}),{status:200});}return of(u,o);};
"""
SBFAKE="""(()=>{const mk=t=>{const p=new Proxy({},{get(o,k){if(k==='then')return r=>r({data:[],error:null});return (...a)=>{CALLS.push([t,k,...a.map(x=>typeof x==='object'?JSON.parse(JSON.stringify(x)):x)]);return p;};}});return p;};
  SB={from:t=>mk(t),auth:{signOut:async()=>{CALLS.push(['signOut']);}}};ME={id:'me',email:'i@t.bg'};MYNAME='Иван';})()"""
data=[{'id':42,'date':T,'time':'08:00','place':'Копринка','count':'','bg':'Непозната птица','en':'','la':'','fam':'','note':'','h':1,'s':0,'p':0,'u':1,'beh':[],'ask':1}]
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  def page(ua=None,perm='default',url='ptichi-dnevnik.html'):
    ctx=b.new_context(viewport={'width':390,'height':844},**({'user_agent':ua} if ua else {}));ctx.route('https://**',lambda r:r.abort() if 'localhost' not in r.request.url else r.continue_())
    pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)));pg.on('dialog',lambda d:d.accept())
    pg.add_init_script("window.PERM=%s;"%json.dumps(perm)+FAKE+"localStorage.setItem('bird-journal-v3',%s);localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true')"%json.dumps(json.dumps(data,ensure_ascii=False)))
    pg.goto(f'http://localhost:{port}/'+url);pg.wait_for_timeout(500);pg.evaluate(SBFAKE);return pg,errs
  pg,errs=page()
  pg.click('#acct');pg.wait_for_timeout(300)
  check('U1 the profile has „Известия на този телефон“ with „Включи известията“', ('Известия на този телефон' in pg.inner_text('#view'),pg.locator('[data-push="on"]').count()), (True,1))
  pg.click('[data-push="on"]');pg.wait_for_timeout(400)
  c=pg.evaluate("CALLS")
  check('U2 switching on: asks permission, fetches the helper’s key, subscribes with it, saves this phone with four kinds („Браво“ off)',
    ([x[0] for x in c][:3],c[2][1:],[x for x in c if x[0]=='push_subs' and x[1]=='upsert'][0][2]),
    (['permission','key','subscribe'],[True,65],{'endpoint':'https://fcm.googleapis.com/fcm/send/xyz','p256dh':'P256','auth':'AUTH','kinds':['ask','idp','inv','comment'],'updated_at':[x for x in c if x[0]=='push_subs' and x[1]=='upsert'][0][2]['updated_at']}))
  check('U3 ...and shows the five kinds, four ticked, with „Изпрати пробно“ and „Спри известията тук“',
    (pg.locator('[data-pushk]').count(),pg.locator('[data-pushk]:checked').count(),pg.locator('[data-push="test"]').count(),pg.locator('[data-push="off"]').count()), (5,4,1,1))
  pg.evaluate("CALLS.length=0");pg.check('[data-pushk="bravo"]');pg.wait_for_timeout(200)
  check('U4 ticking „Браво“ updates this phone’s kinds', [x for x in pg.evaluate("CALLS") if x[1]=='update'][0][2]['kinds'], ['ask','idp','inv','comment','bravo'])
  pg.evaluate("CALLS.length=0");pg.click('[data-push="test"]');pg.wait_for_timeout(300)
  check('U5 „Изпрати пробно“ asks the helper to message exactly this phone', ([x for x in pg.evaluate("CALLS") if x[0]=='post'][0][1],'Изпратено' in pg.inner_text('#pushSlot')), ({'test':'https://fcm.googleapis.com/fcm/send/xyz'},True))
  check('U5b every call to the helper carries the project\'s publishable key (Supabase now requires it)', pg.evaluate("[...new Set(FNKEYS)]"), [pg.evaluate("SB_KEY")])
  pg.evaluate("CALLS.length=0");pg.click('[data-push="off"]');pg.wait_for_timeout(300)
  c=pg.evaluate("CALLS")
  check('U6 „Спри известията тук“ removes this phone and unsubscribes', ([x[1:] for x in c if x[0]=='push_subs'][:2],[x[0] for x in c if x[0]=='unsubscribe'],pg.locator('[data-push="on"]').count()),
    ([['delete'],['eq','endpoint','https://fcm.googleapis.com/fcm/send/xyz']],['unsubscribe'],1))
  pg.click('[data-push="on"]');pg.wait_for_timeout(300);pg.evaluate("CALLS.length=0")
  pg.locator('[data-sb="out"]').first.click();pg.wait_for_timeout(400)   # the real „Изход“ button
  check('U7 signing out forgets the phone first (no notifications for the next person on it)', [x[0] if x[0]!='push_subs' else x[1] for x in pg.evaluate("CALLS")][:3], ['delete','eq','unsubscribe'])
  check('U8 no page errors', errs, [])
  pg,errs=page(ua='Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1')
  pg.click('#acct');pg.wait_for_timeout(300)
  check('U9 iPhone in Safari: how to add Перá to the Home Screen, no button', ('Добави към началния екран' in pg.inner_text('#pushSlot'),pg.locator('[data-push="on"]').count()), (True,0))
  pg,errs=page(perm='denied')
  pg.click('#acct');pg.wait_for_timeout(300)
  check('U10 notifications blocked in the phone’s settings: says where to allow them', 'спрени в настройките' in pg.inner_text('#pushSlot'), True)
  pg,errs=page(url='ptichi-dnevnik.html?go=friends');pg.wait_for_timeout(900)
  check('U11 a tapped notification „?go=friends“ opens Приятели (and the address is cleaned)', (pg.evaluate("view"),pg.evaluate("location.search")), ('friends',''))
  pg,errs=page(url='ptichi-dnevnik.html?go=q:42');pg.wait_for_timeout(1200)
  check('U12 a suggestion on your question „?go=q:42“ opens that question', (pg.evaluate("view"),pg.evaluate("document.getElementById('qDlg').open")), ('log',True))
  check('U13 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
