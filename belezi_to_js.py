#!/usr/bin/env python3
"""pera-belezi-za-pregled.xlsx → белезите за „Какво видях?“ в index.html (между редовете // <KV> и // </KV>).

Употреба:  python3 belezi_to_js.py pera-belezi-za-pregled.xlsx index.html
Чете лист „Белези“ по имената на колоните (не по местата им). Непознати думи или размери спират всичко
и се изписват с номера на реда — нищо грешно не влиза в приложението тихо.
Формат на всеки вид: 'размер|цветове ♂ или общо|цветове ♀|къде' — размерът е цифра (1–5) или две съседни („34“
за „3–4“); цветовете са букви в реда, в който се забелязват; „къде“ — букви.
"""
import sys,re,json
from openpyxl import load_workbook
CW={'черно':'k','бяло':'w','сиво':'g','кафяво':'b','бежово':'e','ръждиво':'r','жълто':'y','зелено':'z','синьо':'s','червено':'c','розово':'p'}
HW={'вода':'V','въздух':'A','земя':'Z','дървета/храсти':'D','дървета':'D','храсти':'D','жица/ограда':'J','жица':'J','ограда':'J','тръстика':'T','скали':'S'}
def words(v,M):
    out,bad='',[]
    for w in re.split(r'[,;]+',str(v or '')):
        w=w.strip().lower()
        if not w:continue
        c=M.get(w)
        if not c:bad.append(w)
        elif c not in out:out+=c
    return out,bad
def size(v):
    s=str(v if v is not None else '').strip().replace('-','–').replace('—','–')
    if re.fullmatch(r'[1-5](\.0)?',s):return s[0]
    m=re.fullmatch(r'([1-5])\s*–\s*([1-5])',s)
    if m:
        a,b=sorted((int(m.group(1)),int(m.group(2))))
        if b-a==1:return f'{a}{b}'
    return None
def read(xlsx):
    ws=load_workbook(xlsx,data_only=True)['Белези'];H=[(c.value or '').strip() for c in ws[1]]
    def col(name):
        if name not in H:sys.exit(f'Липсва колоната „{name}“ в лист „Белези“.')
        return H.index(name)+1
    cL,cE,cG,cH,cI=col('Латинско име'),col('Размер (1–5)'),col('Цветове (♂ или общо)'),col('Цветове на ♀ (ако са други)'),col('Къде го виждаш')
    KV,problems={},[]
    for r in range(2,ws.max_row+1):
        la=str(ws.cell(r,cL).value or '').strip()
        if not la:continue
        sz=size(ws.cell(r,cE).value)
        m,b1=words(ws.cell(r,cG).value,CW);f,b2=words(ws.cell(r,cH).value,CW);w,b3=words(ws.cell(r,cI).value,HW)
        for b in b1+b2:problems.append(f'ред {r} ({la}): непознат цвят „{b}“')
        for b in b3:problems.append(f'ред {r} ({la}): непознато място „{b}“')
        if not sz:problems.append(f'ред {r} ({la}): размер „{ws.cell(r,cE).value}“ — трябва 1–5 или два съседни, напр. „2–3“')
        if not m:problems.append(f'ред {r} ({la}): няма цветове')
        if not w:problems.append(f'ред {r} ({la}): няма „къде“')
        KV[la]='|'.join([sz or '',m,f if f!=m else '',w])
    return KV,problems
def main():
    if len(sys.argv)!=3:sys.exit(__doc__)
    KV,problems=read(sys.argv[1])
    if problems:print('Не записвам — да се оправят първо:');print('\n'.join(problems));sys.exit(1)
    html=open(sys.argv[2],encoding='utf-8').read()
    a,b=html.find('// <KV>\n'),html.find('// </KV>')
    if a<0 or b<a:sys.exit('В index.html няма редовете // <KV> и // </KV>.')
    body='const KV='+json.dumps(KV,ensure_ascii=False,separators=(',',':'))+';\n'
    open(sys.argv[2],'w',encoding='utf-8').write(html[:a+len('// <KV>\n')]+body+html[b:])
    print(f'{len(KV)} вида записани.')
if __name__=='__main__':main()
