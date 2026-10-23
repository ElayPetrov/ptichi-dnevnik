import json, subprocess, time, sys
from playwright.sync_api import sync_playwright

R=lambda **k: {**dict(id=0,date='',time='',place='',count='',bg='',en='',la='',fam='',note='',h=0,s=1,p=0,beh=[],geo=None,photo=None),**k}
DATA=[
 R(id=1,date='2026-05-01',place='Розариум, Казанлък',bg='Сврака'),
 R(id=2,date='2026-06-10',place='Розариум, Казанлък',bg='Сврака',la='Pica pica',fam='Вранови',geo='42.61985,25.39560'),
 R(id=3,date='2026-04-02',place='Копринка',en='Eurasian Magpie',la='Pica pica',geo='42.60000,25.30000'),
 R(id=4,date='2026-07-01',place='Копринка',bg='Сойка',la='Garrulus glandarius',fam='Вранови',geo='42.60100,25.30100'),
 R(id=5,date='2026-03-01',place='Язовир',bg='Чайка',en='gull sp.',la='Larus',fam='Чайки и рибарки'),
 R(id=6,date='2026-03-02',place='Язовир',bg='Жълтокрака чайка',en='Yellow-legged Gull',la='Larus michahellis',fam='Чайки и рибарки'),
]
PORT=sys.argv[1] if len(sys.argv)>1 else '8765'
srv=subprocess.Popen([sys.executable,'-m','http.server',PORT],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
time.sleep(1)
fails=0
def check(name,got,exp):
    global fails
    ok=got==exp
    if not ok: fails+=1
    print(('PASS ' if ok else 'FAIL ')+name+('' if ok else f'\n     got {got!r}\n     exp {exp!r}'))
try:
  with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page()
    errs=[]; pg.on('pageerror',lambda e: errs.append(str(e)))
    pg.on('console',lambda m: errs.append('console.'+m.type+': '+m.text) if m.type=='error' and 'fonts.g' not in m.text and 'ERR_' not in m.text else None)
    dialogs=[]; pg.on('dialog',lambda d:(dialogs.append(d.message),d.accept()))
    pg.add_init_script("if(!sessionStorage.getItem('seeded')){localStorage.clear();localStorage.setItem('bird-journal-v3',%s);sessionStorage.setItem('seeded','1');}"%json.dumps(json.dumps(DATA,ensure_ascii=False)))
    pg.goto(f'http://localhost:{PORT}/ptichi-dnevnik.html'); pg.wait_for_function("document.getElementById('n-obs').textContent==='6'")
    # record which inputType real typing produces
    pg.evaluate("window.__it=[];for(const id of ['f-bg','f-la','f-place'])document.getElementById(id).addEventListener('input',e=>__it.push(e.inputType),true)")
    pick=lambda sel,val: pg.evaluate("([s,v])=>{const el=document.querySelector(s);el.focus();el.value=v;el.dispatchEvent(new InputEvent('input',{inputType:'insertReplacementText',bubbles:true}));}",[sel,val])
    vals=lambda: pg.evaluate("['bg','en','la','fam','place','geo'].reduce((o,k)=>(o[k]=document.getElementById('f-'+k).value,o),{})")
    def newform():
        pg.evaluate("closeForm()"); pg.click('#toggle')
    def typein(sel,text,blur=True):
        loc=pg.locator(sel); loc.click(); pg.keyboard.press('Control+A'); pg.keyboard.press('Delete'); loc.press_sequentially(text)
        if blur: pg.keyboard.press('Tab')
    N=lambda v:{k:v[k] for k in ('bg','en','la','fam')}

    newform(); pick('#f-bg','Сврака')
    check('T1 pick bg fills en (one hop), la, fam', N(vals()), dict(bg='Сврака',en='Eurasian Magpie',la='Pica pica',fam='Вранови'))
    pick('#f-bg','Сойка')
    check('T2 switching species swaps the auto-filled names (English, which your records lack, now from the built-in list)', N(vals()), dict(bg='Сойка',en='Eurasian jay',la='Garrulus glandarius',fam='Вранови'))
    typein('#f-bg','Червен ангел')
    check('T3 brand-new name clears auto-filled names', N(vals()), dict(bg='Червен ангел',en='',la='',fam=''))

    newform(); typein('#f-en','My Magpie'); pick('#f-bg','Сврака')
    check('T4 hand-typed English is kept', N(vals()), dict(bg='Сврака',en='My Magpie',la='Pica pica',fam='Вранови'))

    newform(); pick('#f-la','Larus michahellis')
    check('T5 pick Latin fills bg/en/fam', N(vals()), dict(bg='Жълтокрака чайка',en='Yellow-legged Gull',la='Larus michahellis',fam='Чайки и рибарки'))

    newform(); typein('#f-la','Larus',blur=False)
    check('T6a typing a genus prefix does not fill yet', N(vals()), dict(bg='',en='',la='Larus',fam=''))
    pg.locator('#f-la').press_sequentially(' michahellis'); pg.keyboard.press('Tab')
    check('T6b leaving the field fills from the full name', N(vals()), dict(bg='Жълтокрака чайка',en='Yellow-legged Gull',la='Larus michahellis',fam='Чайки и рибарки'))

    newform(); pick('#f-place','Копринка'); v=vals()
    check('T7a place pick fills newest coords', v['geo'], '42.60100,25.30100')
    check('T7b hint says where they came from', pg.inner_text('#geoHint'), 'взети от записа от 1 юли 2026')
    pick('#f-place','Розариум, Казанлък')
    check('T7c switching place swaps auto coords', vals()['geo'], '42.61985,25.39560')
    typein('#f-place','Нова поляна')
    check('T7d new place clears auto coords', vals()['geo'], '')
    pick('#f-place','Язовир')
    check('T7e known place without coords leaves field empty', vals()['geo'], '')

    newform(); typein('#f-geo','42.12345, 25.12345'); pick('#f-place','Копринка')
    check('T8 typed coords are never replaced', vals()['geo'], '42.12345,25.12345')

    newform(); typein('#f-bg','Сврака',blur=False); pick('#f-place','Копринка'); pg.evaluate("form.requestSubmit()")
    last=pg.evaluate("JSON.parse(localStorage.getItem('bird-journal-v3')).slice(-1)[0]")
    check('T9 typed-in-full name + save without leaving field', {k:last[k] for k in ('bg','en','la','fam','geo')},
          dict(bg='Сврака',en='Eurasian Magpie',la='Pica pica',fam='Вранови',geo='42.60100,25.30100'))

    pg.evaluate("openForm(OBS.find(o=>o.id===4))"); typein('#f-bg','Сойка обикновена')
    check('T10a edit: renaming to unknown keeps record names', N(vals()), dict(bg='Сойка обикновена',en='',la='Garrulus glandarius',fam='Вранови'))
    pg.evaluate("openForm(OBS.find(o=>o.id===4))"); pick('#f-bg','Сврака')
    check('T10b edit: picking another known species replaces names', N(vals()), dict(bg='Сврака',en='Eurasian Magpie',la='Pica pica',fam='Вранови'))
    pg.click('#cancel')

    pg.evaluate("closeForm()"); pg.click('#sessStart'); pick('#f-place','Розариум, Казанлък'); pick('#f-bg','Сойка'); pg.click('#savebtn')
    v=vals(); check('T11a outing: next form is seeded with place+coords, names empty', (v['place'],v['geo'],v['bg'],v['la']), ('Розариум, Казанлък','42.61985,25.39560','',''))
    typein('#f-place','Розариум - езерото')
    check('T11b outing: renaming the spot keeps seeded coords (as before)', vals()['geo'], '42.61985,25.39560')
    pick('#f-place','Копринка')
    check('T11c outing: picking another known place replaces them', vals()['geo'], '42.60100,25.30100')
    pg.click('#sessEnd')

    print('inputTypes seen while typing:', sorted(set(pg.evaluate("__it"))))
    print('dialogs:', dialogs); print('errors:', errs or 'none')
    b.close()
finally:
  srv.terminate()
print('FAILURES:',fails)
