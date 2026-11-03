# Checkbox rows in the profile („Известия на този телефон“ and „Тих режим“): the boxes stand in one straight column,
# all the same size, each level with the first line of its text; long text wraps inside the card; nothing widens the page.
import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
port=int(sys.argv[1]) if len(sys.argv)>1 else 9001;fails=0
FILE=sys.argv[2] if len(sys.argv)>2 else 'ptichi-dnevnik.html'
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
FAKE="""const sub={endpoint:'https://x/1',toJSON(){return {endpoint:'https://x/1',keys:{p256dh:'P',auth:'A'}}},unsubscribe:async()=>true};
try{Object.defineProperty(navigator.serviceWorker,'ready',{get:()=>Promise.resolve({pushManager:{getSubscription:async()=>sub,subscribe:async()=>sub}})});}catch(e){}
window.Notification={permission:'granted',requestPermission:async()=>'granted'};"""
GEO="""(()=>{const W=document.documentElement.clientWidth,R=[...document.querySelectorAll('#view .qtog')].map(l=>{const i=l.querySelector('input').getBoundingClientRect(),t=l.querySelector('span')||l,tr=t.getBoundingClientRect(),c=l.closest('.arr').getBoundingClientRect();
  return {x:Math.round(i.left-c.left),w:Math.round(i.width),h:Math.round(i.height),dy:Math.round(Math.abs(i.top-tr.top)),tx:Math.round(tr.left-c.left),out:tr.right>c.right-10+0.5||l.getBoundingClientRect().right>c.right+0.5};});
  return {rows:R.length,xs:[...new Set(R.map(r=>r.x))].length,sizes:[...new Set(R.map(r=>r.w+'x'+r.h))],txs:[...new Set(R.map(r=>r.tx))].length,level:R.every(r=>r.dy<=3),inside:R.every(r=>!r.out),wide:document.documentElement.scrollWidth>W};})()"""
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch()
  for w in (320,390):
    ctx=b.new_context(viewport={'width':w,'height':800});ctx.route('https://**',lambda r:r.abort() if 'localhost' not in r.request.url else r.continue_())
    pg=ctx.new_page();pg.add_init_script(FAKE+"localStorage.setItem('bird-journal-tips','{\"all\":1}');localStorage.setItem('bird-journal-quiet','true')")
    pg.goto(f'http://localhost:{port}/{FILE}');pg.wait_for_timeout(400)
    pg.evaluate("ME={id:'me',email:'i@t.bg'};MYNAME='Иван'");pg.click('#acct');pg.wait_for_timeout(500)
    g=pg.evaluate(GEO)
    check(f'R1 {w} px: six rows, the boxes in one straight column, all the same size', (g['rows'],g['xs'],g['sizes']), (6,1,['20x20']))
    check(f'R2 {w} px: the texts start in one column, each box level with its first line', (g['txs'],g['level']), (1,True))
    check(f'R3 {w} px: long texts wrap inside the card; the page doesn’t get wider', (g['inside'],g['wide']), (True,False))
    if w==390:pg.locator('.pushk').scroll_into_view_if_needed();pg.wait_for_timeout(100);pg.locator('.pushk').screenshot(path='/tmp/rows.png')
    ctx.close()
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
