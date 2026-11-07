"""Ingressi medi per varco e per anno (feriali normali), per l'anello della pagina Area C rifatta.
Feriale normale = lavorativo, non festivo, non agosto, non 24/12-6/1 (colonne di calendario.csv).
Scrive docs/area-c/data/ac2_varchi_per_anno.json. Uso: python -I -X utf8 area-c/scripts/10_dati_pagina_v2.py"""
import csv, json, os, collections
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(R, 'area-c', 'pulito')
normale = set()
for r in csv.DictReader(open(os.path.join(P, 'calendario.csv'), encoding='utf-8'), delimiter=';'):
    if r['lavorativo'] == '1' and not r['festivo'] and r['agosto'] == '0' and r['natale_24dic_6gen'] == '0':
        normale.add(r['data'])
som = collections.defaultdict(float); giorni = collections.defaultdict(set)
for r in csv.DictReader(open(os.path.join(P, 'ingressi_varco_giorno.csv'), encoding='utf-8'), delimiter=';'):
    d = r['data']
    if d in normale and d >= '2017-01-01':
        k = (int(r['id_varco']), int(d[:4]))
        som[k] += float(r['transiti']); giorni[k].add(d)
ANNI = list(range(2017, 2025))
varchi = []
for r in csv.DictReader(open(os.path.join(P, 'varchi.csv'), encoding='utf-8'), delimiter=';'):
    i = int(r['id_varco'])
    v = [round(som[(i, a)] / len(giorni[(i, a)])) if len(giorni.get((i, a), ())) >= 20 else None for a in ANNI]
    varchi.append({'id': i, 'nome': r['nome'], 'lat': round(float(r['lat']), 6), 'lon': round(float(r['lon']), 6), 'v': v})
tot = [round(sum(g['v'][k] or 0 for g in varchi)) for k in range(len(ANNI))]
out = {'anni': ANNI, 'totale': tot, 'varchi': varchi,
       'nota': 'Media degli ingressi in un feriale normale, per varco e per anno. Il 2024 va da gennaio a novembre.'}
dest = os.path.join(R, 'docs', 'area-c', 'data', 'ac2_varchi_per_anno.json')
json.dump(out, open(dest, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(dest, tot)
for g in varchi[:3]: print(g['nome'], g['v'])
