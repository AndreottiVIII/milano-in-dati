"""Striscia dei blocchi nelle elezioni comunali: per ogni Consiglio comunale (1964-2021) 100 tessere per famiglia di partiti.
Legge docs/elezioni/data/index.json (la stessa fonte della pagina) e docs/amministratori/data/sindaci_milano.csv
(sindaco in carica 60 giorni dopo il voto). Le tessere si contano con i resti piu' alti, come l'emiciclo della pagina.
uso: python -I -X utf8 50_comunali_blocchi.py [cartella docs]
Scrive: docs/elezioni/data/comunali_blocchi.json
"""
import sys, os, json, csv, datetime

docs = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'docs')
idx = json.load(open(os.path.join(docs, 'elezioni', 'data', 'index.json'), encoding='utf-8-sig'))
sind = list(csv.DictReader(open(os.path.join(docs, 'amministratori', 'data', 'sindaci_milano.csv'), encoding='utf-8-sig')))
ORDER = ['Sinistra', 'Centrosinistra', 'M5S', 'Centro', 'Centrodestra', 'Lega', 'Destra', 'Altri']
col = {f['nome']: f['colore'] for f in idx['famiglie']}


def sindaco(d):
    dd = datetime.date.fromisoformat(d) + datetime.timedelta(days=60)
    best = None
    for s in sind:
        a = datetime.date.fromisoformat(s['inizio'])
        b = datetime.date.fromisoformat(s['fine']) if s['fine'] else datetime.date(2100, 1, 1)
        if a <= dd < b:
            best = s['sindaco']
    return best


def seats(v, n=100):
    tot = sum(v)
    q = [x * n / tot for x in v]
    s = [int(x) for x in q]
    for i in sorted(range(len(v)), key=lambda i: q[i] - s[i], reverse=True)[: n - sum(s)]:
        s[i] += 1
    return s


els = sorted((e for e in idx['elezioni'] if e['tipo'] == 'comunali_consiglio'), key=lambda e: e['data'], reverse=True)
righe = []
for e in els:
    fam = {}
    for (nm, fi), s in zip(e['par'], seats(e['city']['v'])):
        fam[e['fam'][fi]] = fam.get(e['fam'][fi], 0) + s
    c = e['city']
    righe.append({
        'anno': e['anno'], 'data': e['data'],
        'sindaco': (sindaco(e['data']) or '').split()[-1],
        'seggi': [fam.get(f, 0) for f in ORDER],
        'elettori': c.get('e') or None, 'votanti': c.get('vt') or None,
    })
    assert sum(righe[-1]['seggi']) == 100
out = {'ordine': ORDER, 'colori': [col[f] for f in ORDER], 'elezioni': righe}
dest = os.path.join(docs, 'elezioni', 'data', 'comunali_blocchi.json')
json.dump(out, open(dest, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('scritto', dest, len(righe), 'elezioni')
for r in righe:
    print(r['anno'], r['sindaco'], r['seggi'], r['elettori'], r['votanti'])
