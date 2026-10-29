"""Estrae il catalogo dei file open data di Eligendo dalla pagina opendata.php.
Uso: python -I 30_eligendo_catalogo.py <opendata.php.html> <uscita.json>"""
import re, json, sys, collections
BS = chr(92)
t = open(sys.argv[1], encoding='utf-8', errors='replace').read()
i = t.find('var dataSet = ') + len('var dataSet = ')
depth = 0; instr = False; k = i
while True:
    c = t[k]
    if instr:
        if c == BS: k += 1
        elif c == '"': instr = False
    else:
        if c == '"': instr = True
        elif c == '[': depth += 1
        elif c == ']':
            depth -= 1
            if depth == 0: break
    k += 1
raw = re.sub(r',\s*\]', ']', t[i:k+1])
ds = json.loads(raw)
json.dump(ds, open(sys.argv[2], 'w', encoding='utf-8'), ensure_ascii=False)
print(len(ds), collections.Counter(r[0] for r in ds))
for r in ds:
    if r[0] != 'catalogoagid': print(r[:6])
print(t[k+1:k+3000])
