"""Passo 4: scrive i dati della pagina (docs/incroci/data/) a partire da pulito/ (dopo analisi.py).
Uso: python -I -X utf8 pagina.py <ABS cartella incroci> <ABS docs/incroci/data>
Tutti i dati sono aggregati (incroci, vie, celle di 100 m, totali per anno): nessuna riga per singolo incidente, nessun dato personale."""
import sys, os, json, shutil
import numpy as np, pandas as pd
S, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
R = json.load(open(S + '/pulito/riepilogo.json', encoding='utf-8'))
IC = pd.read_pickle(S + '/pulito/_IC.pkl'); V = pd.read_pickle(S + '/pulito/_V.pkl')
cells = pd.read_csv(S + '/pulito/celle100m.csv'); TR = pd.read_csv(S + '/pulito/tratti_lontani_da_incroci.csv')

def top(col, n, minimo=1):
    return IC[IC[col] >= minimo].sort_values([col, 'inc'], ascending=False).head(n)
TOPS = {'inc': top('inc', 30), 'p3': top('p3', 30), 'feriti': top('feriti', 30), 'morti': top('morti', 30, 2), 'ped': top('ped', 30), 'bici': top('bici', 30), 'moto': top('moto', 30), 'p1': top('p1', 15)}
ids = []
for k, t in TOPS.items():
    for i in t.id:
        if i not in ids: ids.append(int(i))
# la lista per la mappa: i primi 20 per numero di incidenti sono numerati
rank_inc = {int(i): n + 1 for n, i in enumerate(IC.sort_values(['inc'], ascending=False).id)}
rank_p3 = {int(i): n + 1 for n, i in enumerate(IC.sort_values(['p3', 'inc'], ascending=False).id)}
rows = []
for i in ids:
    r = IC[IC.id == i].iloc[0]
    rows.append({'id': int(i), 'nome': r.nome or r.nomi_osm, 'lon': round(float(r.lon), 5), 'lat': round(float(r.lat), 5), 'inc': int(r.inc), 'feriti': int(r.feriti), 'morti': int(r.morti),
                 'ped': int(r.ped), 'ped_morti': int(r.ped_morti), 'bici': int(r.bici), 'moto': int(r.moto), 'auto': int(r.auto), 'monop': int(r.monop), 'p1': int(r.p1), 'p2': int(r.p2), 'p3': int(r.p3),
                 'y': [int(v) for v in r.y], 'sem': int(r.semaforo), 'rank': rank_inc[int(i)], 'rank_p3': rank_p3[int(i)], 'ped_p3': int(r.ped_p3), 'bici_p3': int(r.bici_p3)})
json.dump({'anni': list(range(2010, 2025)), 'incroci': rows, 'liste': {k: [int(i) for i in t.id] for k, t in TOPS.items()}}, open(OUT + '/incroci.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# vie
VK = V[V.km >= 1.0]
def vrow(r): return {'nome': r.nome, 'km': round(float(r.km), 1), 'inc': int(r.inc), 'feriti': int(r.feriti), 'morti': int(r.morti), 'ped': int(r.ped), 'ped_morti': int(r.ped_morti), 'bici': int(r.bici), 'moto': int(r.moto),
                     'p3': int(r.p3), 'km_anno': round(float(r.inc_km_anno), 1), 'km_anno_p3': round(float(r.p3_km_anno), 1), 'ped_km_anno': round(float(r.ped_km_anno), 1), 'cl': r.cl}
vie = {'per_incidenti': [vrow(r) for r in VK.sort_values('inc', ascending=False).head(20).itertuples()],
       'per_km': [vrow(r) for r in VK[VK.inc >= 150].sort_values('inc_km_anno', ascending=False).head(15).itertuples()],
       'pedoni_km': [vrow(r) for r in VK[VK.ped >= 100].sort_values('ped_km_anno', ascending=False).head(10).itertuples()],
       'n_vie': int(len(V)), 'n_vie_1km': int(len(VK))}
json.dump(vie, open(OUT + '/vie.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
tr = TR.head(12)
json.dump([{k: (int(v) if k in ('inc', 'feriti', 'morti', 'ped', 'moto', 'bici', 'p3') else v) for k, v in r.items()} for r in tr.to_dict('records')], open(OUT + '/tratti.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# celle di 100 m (solo con almeno 2 incidenti, per tenere il file piccolo): colonne
c = cells[cells.n >= 2]
json.dump({'cella_m': 100, 'n_celle_tutte': int(len(cells)), 'n_celle': int(len(c)), 'lon': c.lon.tolist(), 'lat': c.lat.tolist(), 'n': c.n.tolist(), 'ped': c.ped.tolist(), 'bici': c.bici.tolist(),
           'moto': c.moto.tolist(), 'p3': c.p3.tolist(), 'morti': c.morti.tolist(), 'max': int(cells.n.max()),
           'soglie': {k: [int(v) for v in np.unique(np.percentile(cells[k][cells[k] > 0], [50, 75, 90, 97.5]).round().astype(int))] for k in ('n', 'ped', 'bici', 'moto', 'p3')}},
          open(OUT + '/celle.json', 'w', encoding='utf-8'), separators=(',', ':'))

# riepilogo per i testi
keep = {k: R[k] for k in ('serie', 'totali', 'aggancio', 'incroci_osm', 'concentrazione', 'persistenza', 'zone30', 'aree', 'quando', 'mesi', 'comune_annuale', 'comune_mesi_covid', 'comune_2025',
                          'pedoni_dove', 'morti_dove', 'qualita', 'tratti', 'vie', 'interse_tutti')}
keep['zone30']['per_anno_zona'] = {k: v for k, v in keep['zone30']['per_anno_zona'].items() if int(k) >= 2010}
keep['zone30_finestre'] = pd.read_csv(S + '/pulito/zone30_prima_dopo.csv').to_dict('records')
json.dump(keep, open(OUT + '/riepilogo.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# file scaricabili (tabelle aggregate)
IC.drop(columns=['y']).assign(anni_con=IC.anni_con).to_csv(OUT + '/incroci_classifica.csv', index=False)
V.drop(columns=['key']).to_csv(OUT + '/vie_classifica.csv', index=False)
for f in ('serie_annuale.csv', 'quando_lombardia_2000_2011.csv', 'zone30_prima_dopo.csv', 'aree_b_c.csv', 'tratti_lontani_da_incroci.csv'):
    shutil.copy(S + '/pulito/' + f, OUT + '/' + f)
tot = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
print('docs/incroci/data:', round(tot / 1024), 'KB;', {f: os.path.getsize(os.path.join(OUT, f)) // 1024 for f in sorted(os.listdir(OUT))})
