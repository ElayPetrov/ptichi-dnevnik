import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
R=lambda **k: {**dict(id=0,date='',time='',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
DATA=[R(id=4,date='2026-07-01',place='Копринка',bg='Сойка',la='Garrulus glandarius',fam='Вранови',geo='42.60100,25.30100')]
def trial(port,fname,typed_place=None,coords=None,vw=1280,vh=720):
  with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page(viewport={'width':vw,'height':vh})
    pg.add_init_script("localStorage.setItem('bird-journal-v3',%s)"%json.dumps(json.dumps(DATA,ensure_ascii=False)))
    pg.goto(f'http://localhost:{port}/{fname}');pg.wait_for_function("OBS.length===1")
    pg.click('#toggle');pg.fill('#f-bg','Сврака')
    if coords: pg.locator('#f-geo').click(); pg.keyboard.insert_text(coords)     # like pasting
    if typed_place: pg.locator('#f-place').click(); pg.locator('#f-place').press_sequentially(typed_place)
    pg.evaluate("window.__ev=[];for(const t of ['mousedown','mouseup','click'])document.addEventListener(t,e=>__ev.push(t+':'+(e.target.id||e.target.className||e.target.tagName)),true)")
    pg.click('#savebtn');pg.wait_for_timeout(150)
    n=pg.evaluate("OBS.length")-1; last=pg.evaluate("OBS[OBS.length-1]")
    r=(('saved' if n==1 else 'NOT SAVED'), last.get('geo') if n==1 else None, pg.evaluate("__ev")); b.close(); return r
if __name__=='__main__':
  port=int(sys.argv[1]); srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
  try:
    for fname in sys.argv[2:]:
      for vw,vh in [(1280,720),(390,844)]:
        print(fname,f'{vw}x{vh}','paste coords then tap   ->',trial(port,fname,coords='42.61985, 25.39560',vw=vw,vh=vh))
        print(fname,f'{vw}x{vh}','type known place, tap  ->',trial(port,fname,typed_place='Копринка',vw=vw,vh=vh))
  finally: srv.terminate()
