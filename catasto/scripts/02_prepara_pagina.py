"""Dal file pulito/catasto_categorie.csv e dalla popolazione già nel sito prepara i dati della pagina
in docs/catasto/data/. Uso (dalla cartella del progetto): python -I -X utf8 catasto/scripts/02_prepara_pagina.py"""
import os, csv, json
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))      # catasto/
P = os.path.dirname(R)                                               # progetto
OUT = os.path.join(P, 'docs', 'catasto', 'data'); os.makedirs(OUT, exist_ok=True)
ANNI = list(range(2018, 2026))
D = {}; NOME = {}
for r in csv.DictReader(open(os.path.join(R, 'pulito', 'catasto_categorie.csv'), encoding='utf-8'), delimiter=';'):
    D[(int(r['anno']), r['provincia'], r['tipo'], r['categoria'])] = (int(r['unita']), float(r['rendita_euro']))
    if r['tipo'] == 'cap': NOME[r['provincia']] = r['capoluogo']
CAT = {  # nome corto, descrizione
 'A01': ('Signorili', 'Abitazioni di tipo signorile'), 'A02': ('Civili', 'Abitazioni di tipo civile'),
 'A03': ('Economiche', 'Abitazioni di tipo economico'), 'A04': ('Popolari', 'Abitazioni di tipo popolare'),
 'A05': ('Ultrapopolari', 'Abitazioni di tipo ultrapopolare'), 'A06': ('Rurali', 'Abitazioni di tipo rurale'),
 'A07': ('Villini', 'Abitazioni in villini'), 'A08': ('Ville', 'Abitazioni in ville'),
 'A09': ('Castelli', 'Castelli e palazzi di pregio storico'), 'A10': ('Uffici', 'Uffici e studi privati'),
 'C01': ('Negozi', 'Negozi e botteghe'), 'C02': ('Magazzini', 'Magazzini e depositi, cantine'),
 'C03': ('Laboratori', 'Laboratori per arti e mestieri'), 'C06': ('Box', 'Box, autorimesse e posti auto coperti'),
 'D02': ('Alberghi', 'Alberghi e pensioni'), 'D05': ('Banche', 'Banche, cambio e assicurazioni')}
KEYS = list(CAT)
HOME = ['A%02d' % i for i in range(1, 10)]
def g(a, p, t, c): return D.get((a, p, t, c), (0, 0.0))
def serie(p, t):
    return {c: {'u': [g(a, p, t, c)[0] for a in ANNI], 'r': [round(g(a, p, t, c)[1]) for a in ANNI]} for c in KEYS}
provs = sorted({k[1] for k in D if k[0] == 2025 and k[2] == 'cap'})
def italia():
    o = {}
    for c in KEYS:
        o[c] = {'u': [sum(g(a, p, t, c)[0] for p in provs for t in ('cap', 'resto')) for a in ANNI],
                'r': [round(sum(g(a, p, t, c)[1] for p in provs for t in ('cap', 'resto'))) for a in ANNI]}
    return o
# città capoluogo 2025
citta = []
for p in provs:
    d = {'n': NOME[p], 's': p, 'u': {}, 'r': {}}
    for c in KEYS:
        u, r = g(2025, p, 'cap', c); d['u'][c] = u; d['r'][c] = round(r)
    d['case'] = sum(g(2025, p, 'cap', c)[0] for c in HOME)
    citta.append(d)
citta.sort(key=lambda x: -x['case'])
# abitanti 2025 (ISTAT, dal file della pagina Auto)
pop = {}
for r in csv.DictReader(open(os.path.join(P, 'docs', 'auto', 'data', 'confronto_citta.csv'), encoding='utf-8'), delimiter=';'):
    if r['anno'] == '2025' and r['tipo'] in ('comune', 'resto_provincia', 'provincia'):
        pop[(r['territorio'], r['tipo'])] = int(float(r['popolazione']))
GC = {'Milano': 'MI', 'Roma': 'RM', 'Torino': 'TO', 'Napoli': 'NA', 'Bologna': 'BO', 'Firenze': 'FI', 'Genova': 'GE', 'Verona': 'VR', 'Bari': 'BA', 'Palermo': 'PA'}
grandi = []
for n, s in GC.items():
    ab = pop[(n, 'comune')]; box = g(2025, s, 'cap', 'C06')[0]; neg = g(2025, s, 'cap', 'C01')[0]
    grandi.append({'n': n, 'ab': ab, 'box': box, 'neg': neg, 'box100': round(box / ab * 100, 2), 'neg1000': round(neg / ab * 1000, 2)})
J = {'meta': {'anni': ANNI, 'fonte': 'Agenzia delle Entrate, Osservatorio del Mercato Immobiliare, Statistiche catastali 2018-2025 (catasto fabbricati al 31 dicembre)',
              'ab_milano': pop[('Milano', 'comune')], 'ab_resto': pop[('Milano', 'resto_provincia')], 'ab_prov': pop[('Milano', 'provincia')]},
     'cat': {k: {'n': v[0], 'd': v[1]} for k, v in CAT.items()},
     'milano': serie('MI', 'cap'), 'resto': serie('MI', 'resto'), 'roma': serie('RM', 'cap'), 'italia': italia(),
     'citta': citta, 'grandi': grandi}
json.dump(J, open(os.path.join(OUT, 'catasto.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
# CSV per chi vuole scaricare: serie 2018-2025 per categoria
with open(os.path.join(OUT, 'serie_categorie.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['territorio', 'anno', 'categoria', 'nome', 'unita', 'rendita_totale_euro'])
    for ter, key in (('Milano', 'milano'), ('Resto della provincia di Milano', 'resto'), ('Roma', 'roma'), ('Italia', 'italia')):
        for c in KEYS:
            for i, a in enumerate(ANNI):
                w.writerow([ter, a, c, CAT[c][1], J[key][c]['u'][i], J[key][c]['r'][i]])
with open(os.path.join(OUT, 'capoluoghi_2025.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['citta', 'provincia', 'abitazioni_A1_A9'] + ['unita_' + c for c in KEYS] + ['rendita_media_' + c for c in KEYS])
    for d in citta:
        w.writerow([d['n'], d['s'], d['case']] + [d['u'][c] for c in KEYS] +
                   [round(d['r'][c] / d['u'][c], 1) if d['u'][c] else '' for c in KEYS])
with open(os.path.join(OUT, 'grandi_citta_2025.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';'); w.writerow(['citta', 'abitanti_2025', 'box', 'negozi', 'box_ogni_100_abitanti', 'negozi_ogni_1000_abitanti'])
    for d in grandi: w.writerow([d['n'], d['ab'], d['box'], d['neg'], d['box100'], d['neg1000']])
print('ok', os.path.getsize(os.path.join(OUT, 'catasto.json')), 'byte')
for d in grandi: print(d)
