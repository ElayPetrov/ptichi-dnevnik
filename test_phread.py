# A chosen photo is read from the phone only once (some phones fail when the same file is read twice at the same time),
# and each kind of failure gets a truthful message and is logged.
import json,subprocess,sys,time
from playwright.sync_api import sync_playwright
port=int(sys.argv[1]) if len(sys.argv)>1 else 8992;fails=0
def check(n,got,exp):
  global fails;ok=got==exp;fails+=not ok
  print(('PASS ' if ok else 'FAIL ')+n+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
srv=subprocess.Popen([sys.executable,'-m','http.server',str(port)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
try:
 with sync_playwright() as p:
  b=p.chromium.launch();pg=b.new_page(viewport={'width':390,'height':844});errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
  msgs=[];pg.on('dialog',lambda d:(msgs.append(d.message),d.accept()))
  pg.add_init_script("""localStorage.setItem('bird-journal-tips','{"all":1}');
    window.__reads=0;window.__urlFile=0;const ab=File.prototype.arrayBuffer,sl=File.prototype.slice,cu=URL.createObjectURL;
    File.prototype.arrayBuffer=function(){__reads++;return ab.call(this);};File.prototype.slice=function(...a){__reads++;return sl.apply(this,a);};
    URL.createObjectURL=function(o){if(o instanceof File)__urlFile++;return cu.call(URL,o);};""")
  pg.goto(f'http://localhost:{port}/ptichi-dnevnik.html');pg.wait_for_timeout(400)
  pg.click('#toggle');pg.set_input_files('#f-photo','/home/claude/exif.jpg');pg.wait_for_function("phNew.length===1",timeout=8000);pg.wait_for_timeout(200)
  check('H1 the chosen photo is read from the phone exactly once, and never opened straight from the file', (pg.evaluate("__reads"),pg.evaluate("__urlFile")), (1,0))
  check('H2 ...and both the photo and its own data still work', (pg.is_visible('#prev'),pg.inner_text('#f-exif span')), (True,'📷 15 октомври 2026, 08:14 · има място'))   # no own place within 2 km in this empty journal
  pg.click('#cancel');pg.click('#toggle');pg.set_input_files('#f-photo','/home/claude/fake.heic');pg.wait_for_timeout(800)
  check('H3 a real HEIC photo is called HEIC', msgs[-1:], ['Тази снимка е във формат HEIC, който браузърът не отваря. Избери друга или снимай в JPEG.'])
  pg.set_input_files('#f-photo','/home/claude/broken.jpg');pg.wait_for_timeout(800)
  check('H4 any other photo that can’t be opened is not wrongly called HEIC', msgs[-1:], ['Тази снимка не може да се отвори в браузъра. Опитай с друга.'])
  pg.evaluate("File.prototype.arrayBuffer=function(){return Promise.reject(new DOMException('x','NotReadableError'));};0")
  pg.set_input_files('#f-photo','/home/claude/a.jpg');pg.wait_for_timeout(800)
  check('H5 a photo the phone won’t let us read gets its own message', msgs[-1:], ['Снимката не можа да се прочете от телефона. Опитай пак или я избери от „Файлове“.'])
  check('H6 each failure is written to the error log with its cause', [e['msg'] for e in pg.evaluate("ERRQ")][-3:], ['photo decode (heic)','photo decode','photo read: NotReadableError'])
  pg.reload();pg.wait_for_timeout(400);pg.click('#toggle');pg.set_input_files('#f-photo','/home/claude/a.jpg');pg.wait_for_function("phNew.length===1",timeout=8000)
  n0=len(msgs);pg.set_input_files('#f-photo2',['/home/claude/broken.jpg','/home/claude/b.jpg']);pg.wait_for_function("phx.length===1",timeout=8000);pg.wait_for_timeout(300)
  check('H7 an extra photo that can’t be opened is reported, not silently dropped (the good one is kept)', (msgs[n0:],pg.evaluate("phx.length")), (['Тази снимка не може да се отвори в браузъра. Опитай с друга.'],1))
  check('H8 no page errors', errs, [])
  b.close()
finally: srv.terminate()
print('FAILURES:',fails)
