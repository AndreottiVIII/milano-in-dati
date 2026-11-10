"""Costruisce i file di docs/negozi/data/ dai dati grezzi in negozi/raw/.
Uso: python -I -X utf8 negozi/scripts/build.py <percorso di milano-in-dati>"""
import csv, json, sys, collections as C
from pathlib import Path
R = Path(sys.argv[1]); RAW = R/'negozi'/'raw'; OUT = R/'docs'/'negozi'/'data'; OUT.mkdir(parents=True, exist_ok=True)
def rd(n, enc='utf-8-sig'): return list(csv.DictReader(open(RAW/n, encoding=enc, errors='replace'), delimiter=';'))
def wr(n, rows, cols):
    with open(OUT/n, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f, delimiter=';'); w.writerow(cols)
        for r in rows: w.writerow([r[c] for c in cols])
def num(s):
    s = (s or '').strip()
    return float(s) if s else None

# ---- serie 2003-2025 (ds512). La superficie dei negozi di vicinato e' identica 2003-2011: non si usa.
TIPO = {'Esercizi di vicinato': 'vicinato', 'Medie strutture di vendita': 'medie', 'Grandi strutture di vendita': 'grandi'}
serie = []
for r in rd('ds512.csv'):
    t = TIPO[r['struttura tipo']]; a = int(r['anno'])
    n = num(r['Numero strutture']); sup = num(r['Superficie di vendita'])
    if t == 'vicinato' and a <= 2011: sup = None
    serie.append(dict(anno=a, tipo=t, strutture='' if n is None else int(n), superficie_mq='' if sup is None else int(sup)))
serie.sort(key=lambda x: (x['tipo'], x['anno']))
wr('serie_2003_2025.csv', serie, ['anno', 'tipo', 'strutture', 'superficie_mq'])

# ---- negozi di vicinato oggi (ds49)
neg = rd('ds49.csv')
def sett(s):
    s = (s or '').lower().replace(' ', '')
    if 'monopolio' in s: return 'Tabacchi'
    if 'farmacie' in s: return 'Farmacie'
    if 'carburanti' in s: return 'Carburanti'
    if not s: return 'Non indicato'
    na = 'nonalimentare' in s; al = 'alimentare' in s.replace('nonalimentare', '')
    if na and al: return 'Misto'
    if na: return 'Non alimentare'
    return 'Alimentare'
cs = C.Counter(sett(x['settore_merceologico']) for x in neg)
wr('settori_2026.csv', [dict(settore=k, negozi=v) for k, v in cs.most_common()], ['settore', 'negozi'])

nilpop = {}; nilname = {}
g = json.load(open(OUT/'nil.geojson', encoding='utf-8'))
for f in g['features']:
    nilpop[str(f['properties']['i'])] = f['properties']['ab']; nilname[str(f['properties']['i'])] = f['properties']['n']
cn = C.Counter(x['ID_NIL'] for x in neg if x['ID_NIL'])
senza = sum(1 for x in neg if not x['ID_NIL'])
nil = []
for i in sorted(nilpop, key=int):
    n = cn.get(i, 0); ab = nilpop[i]
    nil.append(dict(id=i, quartiere=nilname[i], negozi=n, abitanti=ab, ogni1000=round(1000*n/ab, 1) if ab else ''))
wr('quartieri.csv', nil, ['id', 'quartiere', 'negozi', 'abitanti', 'ogni1000'])
cv = C.Counter(x['DescrizioneVia'].strip() for x in neg if x['DescrizioneVia'].strip())
vie = [dict(via=k, negozi=v) for k, v in cv.most_common(15)]
wr('vie_top15.csv', vie, ['via', 'negozi'])

# ---- 2018 (ds202)
TIP = {'EV': 'Negozi', 'PE': 'Bar e ristoranti (in piano)', 'FP': 'Bar e ristoranti (fuori piano)', 'PA': 'Servizi alla persona',
       'AE': 'Attività alimentari', 'HH': 'Panifici', 'MG': 'Medie e grandi strutture', 'ED': 'Edicole', 'VA': 'Case vacanza', 'EA': 'Altri alloggi'}
ini = C.Counter(); ces = C.Counter()
for r in rd('ds202.csv', 'utf-8'):
    l = r['Label']; t = r['Tipo']
    if l not in TIP: continue
    if l == 'EV':
        if t == 'Iniziale vendita': ini[l] += 1
        elif t == 'Cessazione vendita': ces[l] += 1
        continue
    if l == 'PA' and 'Affido' in t: continue
    if l == 'ED' and ('occupazione' in t or "d'ufficio" in t): continue
    if l == 'PE' and t == 'Cessazione Affitto/per Trasf Somm in piano': continue
    if t.startswith('Iniziale'): ini[l] += 1
    elif t.startswith('Cessazione'): ces[l] += 1
s18 = [dict(attivita=TIP[l], avvii=ini[l], cessazioni=ces[l], saldo=ini[l]-ces[l]) for l in TIP]
wr('aperture_chiusure_2018.csv', s18, ['attivita', 'avvii', 'cessazioni', 'saldo'])

# ---- mercati
mer = []
for r in rd('ds2471.csv'):
    mer.append(dict(tipo='coperto', nome=r['MCC'].title(), aperto='sì' if r['attivo'] == 'SI' else 'no', box=r['NUM_BOX'], lon=round(float(r['LONG_X_4326']), 5), lat=round(float(r['LAT_Y_4326']), 5)))
giorni = ['LUNEDI', 'MARTEDI', 'MERCOLEDI', 'GIOVEDI', 'VENERDI', 'SABATO', 'DOMENICA']
gc = C.Counter()
for r in rd('ds291.csv'):
    if r['status mss'] != 'attivo': continue
    gg = [d for d in giorni if r[d].strip()]
    for d in gg: gc[d] += 1
    mer.append(dict(tipo='scoperto', nome=r['MERCATO'].title(), aperto='sì', box=r['POSTEGGI_A'], lon=round(float(r['LONG_X_4326']), 5), lat=round(float(r['LAT_Y_4326']), 5)))
wr('mercati.csv', mer, ['tipo', 'nome', 'aperto', 'box', 'lon', 'lat'])
wr('mercati_giorni.csv', [dict(giorno=d.title(), mercati=gc[d]) for d in giorni], ['giorno', 'mercati'])

# ---- riepilogo
v = {(s['tipo'], s['anno']): s['strutture'] for s in serie}
rie = dict(
    serie={t: {str(a): v[(t, a)] for a in range(2003, 2026)} for t in ['vicinato', 'medie', 'grandi']},
    settori=dict(cs), quartieri=nil, senza_quartiere=senza, totale=len(neg), vie=vie, s2018=s18,
    mercati=mer, giorni={d.title(): gc[d] for d in giorni},
    superficie={t: {s['anno']: s['superficie_mq'] for s in serie if s['tipo'] == t} for t in ['vicinato', 'medie', 'grandi']})
json.dump(rie, open(OUT/'riepilogo.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
# geojson alleggerito
for f in g['features']:
    p = f['properties']; f['properties'] = dict(i=p['i'], n=p['n'], ab=p['ab'])
def rr(c):
    return [rr(x) for x in c] if isinstance(c[0], list) else [round(c[0], 5), round(c[1], 5)]
for f in g['features']: f['geometry']['coordinates'] = rr(f['geometry']['coordinates'])
json.dump(g, open(OUT/'nil.geojson', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(cs, senza, len(neg)); print(s18); print(gc); print(vie[:5]); print(sorted(nil, key=lambda x: -x['negozi'])[:5])
