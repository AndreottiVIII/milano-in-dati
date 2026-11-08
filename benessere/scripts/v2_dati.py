"""Dati per la pagina Benessere (versione nuova): docs/benessere/data/v2_dati.json
Legge solo i file gia' presenti in docs/benessere/data/. Uso: python -I -X utf8 benessere/scripts/v2_dati.py"""
import csv, json, os, collections
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(R, 'docs', 'benessere', 'data')
def rd(n): return list(csv.DictReader(open(os.path.join(D, n), encoding='utf-8')))
def fl(x):
    try:
        return float(x) if x not in ('', None) else None
    except ValueError:
        return None
st = json.load(open(os.path.join(D, 'strisce.json'), encoding='utf-8'))
pos = {r['codice']: r for r in rd('milano_posizione_ultimo_anno.csv')}
cm = rd('cm14_ultimo_anno.csv')
ser = rd('milano_italia_serie.csv')
cam = rd('milano_cambiamenti.csv')

# serie per indicatore
S = collections.defaultdict(lambda: collections.defaultdict(dict))
for r in ser:
    S[r['codice']][r['territorio']][int(r['anno'])] = fl(r['valore'])
# valori delle 14 citta
V = collections.defaultdict(list)
for r in cm:
    V[r['codice']].append([r['citta_metropolitana'], fl(r['valore']), int(float(r['rango_14'])) if r['rango_14'] else None])

ind = []
for i in st['ind']:
    c = i['c']; p = pos[c]
    s = S[c]
    anni = sorted(set(s['Milano']) | set(s['Italia']))
    ind.append({'c': c, 'n': i['n'], 'd': i['d'], 'u': i['u'], 'pol': i['pol'], 'a': i['a'], 'k': i['k'], 'r': i['r'],
                'r14': i['r14'], 'vm': i['vm'], 'vi': i['vi'], 'dec': i['dec'],
                'mn': fl(p['valore_min_province']), 'mx': fl(p['valore_max_province']),
                'cm': sorted(V[c], key=lambda x: (x[2] is None, x[2] or 0)),
                'anni': anni, 'm': [s['Milano'].get(a) for a in anni], 'i': [s['Italia'].get(a) for a in anni],
                'l': [s['Lombardia'].get(a) for a in anni]})

# medie per dominio e citta' (solo polarita' scritta dall'Istat, come la graduatoria)
doms = st['domini']
acc = collections.defaultdict(lambda: collections.defaultdict(list))
for r in cm:
    if r['livello_polarita'] in ('istat', 'istat_testo') and r['percentile_107']:
        acc[r['citta_metropolitana']][r['dominio']].append(float(r['percentile_107']))
citta = []
for n, dd in acc.items():
    allv = [x for v in dd.values() for x in v]
    citta.append({'n': n, 'tot': round(sum(allv) / len(allv), 1),
                  'd': [round(sum(dd[d]) / len(dd[d]), 1) if dd.get(d) else None for d in doms]})
citta.sort(key=lambda x: -x['tot'])

# cambi di posto dal 2019
ch = []
for r in cam:
    if r['orizzonte'] == 'rispetto al 2019' and r['livello_polarita'] in ('istat', 'istat_testo') and r['rango_107_base'] and r['rango_107_ultimo']:
        ch.append({'c': r['codice'], 'n': r['indicatore'], 'ab': int(r['anno_base']), 'au': int(r['anno_ultimo']),
                   'rb': int(float(r['rango_107_base'])), 'ru': int(float(r['rango_107_ultimo']))})
for x in ch: x['g'] = x['rb'] - x['ru']
ch.sort(key=lambda x: -x['g'])
out = {'domini': doms, 'citta': citta, 'ind': ind, 'cambi': ch}
json.dump(out, open(os.path.join(D, 'v2_dati.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(ind), len(citta), len(ch), [c['n'] for c in citta][:3], citta[2])
