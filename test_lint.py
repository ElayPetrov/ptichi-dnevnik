# Guards against a mistake made twice on 2 Nov 2026: a // comment written in the middle of a line of code
# turns everything after it on that line into comment — the code silently stops running.
# Fails if any line has code before a // and code-looking text after it.
import re,sys
s=open('ptichi-dnevnik.html',encoding='utf-8').read()
js=re.search(r'<script>(.*)</script>',s,re.S).group(1);bad=[]
for n,line in enumerate(js.split('\n'),1):
    for m in re.finditer(r'(?<![:\'"\\])//',line):
        pre=line[:m.start()]
        if pre.count("'")%2 or pre.count('"')%2 or pre.count('`')%2:continue   # inside a string
        if not pre.strip():break                                             # a whole-line comment is fine
        tail=line[m.end():]
        # code that got swallowed still ends like code (; { }) and contains a statement
        if tail.rstrip().endswith((';','{','}')) and re.search(r";\s*[A-Za-z_$]|\bconst\s|\blet\s|\bawait\s|\breturn\b|\bif\(|\bfor\(|\b[A-Za-z_$]\w*\.\w+\s*=[^=>]|\)\s*;\s*$",tail):bad.append((n,line.strip()[:160]))
        break
fails=len(bad)
print(('PASS' if not bad else 'FAIL')+' L1 no code hidden behind a // comment on the same line'+(''.join('\n     line %d: %s'%b for b in bad)))
print('FAILURES:',fails)
