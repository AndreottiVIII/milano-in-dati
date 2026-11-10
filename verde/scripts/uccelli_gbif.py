"""Uccelli segnalati a Milano (GBIF): quota del parrocchetto dal collare sul totale degli uccelli, per anno, e specie piu' segnalate.
Scrive docs/verde/data/uccelli.json. Solo record con licenza CC0 o CC BY 4.0 (esclusi CC BY-NC).
Uso, dalla cartella del progetto:  python -I -X utf8 verde/scripts/uccelli_gbif.py
Le richieste sono conteggi (limit=0, nessun record scaricato): non serve registrazione e non esiste un DOI di scarico."""
import json, os, urllib.request, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(ROOT), 'docs', 'verde', 'data', 'uccelli.json')
RAW = os.path.join(ROOT, 'raw')
os.makedirs(RAW, exist_ok=True)
H = {'User-Agent': 'milano-in-dati (dati aperti)'}
BASE = ('https://api.gbif.org/v1/occurrence/search?decimalLatitude=45.386,45.536&decimalLongitude=9.04,9.28'
        '&license=CC0_1_0&license=CC_BY_4_0&limit=0')
AVES, PARR = 212, 2479226


def g(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=60))


def facet(extra, nome, n=200):
    r = g(BASE + extra + '&facet=%s&facetLimit=%d' % (nome, n))
    return r['count'], {c['name']: c['count'] for c in r['facets'][0]['counts']}


tot_n, tot_y = facet('&taxonKey=%d' % AVES, 'year')
par_n, par_y = facet('&taxonKey=%d' % PARR, 'year')
_, sp = facet('&taxonKey=%d' % AVES, 'speciesKey', 25)
_, ds = facet('&taxonKey=%d' % AVES, 'datasetKey', 5)
json.dump({'tot': tot_y, 'parr': par_y, 'sp': sp, 'ds': ds}, open(os.path.join(RAW, 'gbif_conteggi.json'), 'w', encoding='utf-8'))

IT = {'Corvus cornix': 'Cornacchia grigia', 'Turdus merula': 'Merlo', 'Columba livia': 'Piccione', 'Columba palumbus': 'Colombaccio',
      'Sturnus vulgaris': 'Storno', 'Parus major': 'Cinciallegra', 'Psittacula krameri': 'Parrocchetto dal collare', 'Anas platyrhynchos': 'Germano reale',
      'Fringilla coelebs': 'Fringuello', 'Gallinula chloropus': 'Gallinella d’acqua', 'Pica pica': 'Gazza', 'Erithacus rubecula': 'Pettirosso'}
specie = []
for k, n in list(sp.items())[:12]:
    sci = g('https://api.gbif.org/v1/species/' + k)['canonicalName']
    specie.append({'nome': IT[sci], 'sci': sci, 'n': n, 'parr': sci == 'Psittacula krameri'})

anni = list(range(2018, 2026))
dsinfo = []
for k, n in ds.items():
    d = g('https://api.gbif.org/v1/dataset/' + k)
    dsinfo.append({'titolo': d['title'], 'doi': d.get('doi'), 'n': n})

out = {
    'meta': {'scaricato': datetime.date.today().isoformat(), 'rettangolo': 'latitudine 45,386-45,536, longitudine 9,04-9,28', 'licenze': 'CC0 1.0 e CC BY 4.0',
             'totale_uccelli': tot_n, 'totale_parrocchetto': par_n, 'primo_anno_mostrato': anni[0], 'ultimo_anno_completo': 2025},
    'anni': anni,
    'totali': [tot_y.get(str(a), 0) for a in anni],
    'parrocchetto': [par_y.get(str(a), 0) for a in anni],
    'specie': specie,
    'rango_parrocchetto': [i + 1 for i, s in enumerate(specie) if s['parr']][0],
    'dataset': dsinfo,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(out['meta'], out['totali'], out['parrocchetto'], [round(100 * p / t, 2) for p, t in zip(out['parrocchetto'], out['totali'])], out['rango_parrocchetto'])
print(dsinfo)
