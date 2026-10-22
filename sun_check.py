import json,subprocess,datetime
from zoneinfo import ZoneInfo
from astral import LocationInfo
from astral.sun import sun
lat,lon=42.61985,25.39560; tz=ZoneInfo('Europe/Sofia')
loc=LocationInfo('Kazanlak','BG','Europe/Sofia',lat,lon)
dates=['2026-01-15','2026-03-29','2026-04-28','2026-06-21','2026-10-22','2026-10-25','2026-12-21']
js=json.loads(subprocess.run(['node','-e',f"const {{sunTimes}}=require('./sun.js');console.log(JSON.stringify({json.dumps(dates)}.map(d=>sunTimes(d,{lat},{lon}))))"],env={'TZ':'Europe/Sofia','PATH':'/usr/bin:/bin'},capture_output=True,text=True).stdout)
worst=0
for d,j in zip(dates,js):
    s=sun(loc.observer,date=datetime.date.fromisoformat(d),tzinfo=tz,dawn_dusk_depression=6)
    m=lambda t:t.hour*60+t.minute+t.second/60
    diffs={k:round(j[k]-m(s[a]),1) for k,a in (('dawn','dawn'),('rise','sunrise'),('set','sunset'),('dusk','dusk'))}
    worst=max(worst,*map(abs,diffs.values()))
    f=lambda x:f"{int(x//60)}:{int(x%60):02d}"
    print(d,'js: зора',f(j['dawn']),'изгрев',f(j['rise']),'залез',f(j['set']),'| diff vs astral (min):',diffs)
print('worst difference:',worst,'min')
