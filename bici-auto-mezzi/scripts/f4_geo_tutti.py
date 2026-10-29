"""Fase 4 (incidenti), passo 2: geocodifica TUTTE le righe dei microdati Lombardia/ISTAT di Milano 2010-2024 (131.435) in locale
(civici del Comune ds634 + nomi strade OSM). Salva out/f4_incidenti_geo.pkl e out/f4_geo_qualita.json.
Uso: python -I f4_geo_tutti.py <ABS strand>  (dopo f4_carica.py)"""
import sys, os, pickle, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from f4_geocode import Geocoder4
S = sys.argv[1]
df = pickle.load(open(S + '/out/f4_incidenti_raw.pkl', 'rb'))
t0 = time.time(); g = Geocoder4(S)
uniq = df.nome_strada.unique(); res = {}
for s in uniq:
    r, lv, mo, fz = g.indirizzo4(s)
    res[s] = (r[0] if r else np.nan, r[1] if r else np.nan, lv, mo, fz, g.multi, g.vie(s))
print('geocodificate', len(uniq), 'stringhe in', round(time.time() - t0), 's')
df['lon'] = df.nome_strada.map(lambda s: res[s][0]); df['lat'] = df.nome_strada.map(lambda s: res[s][1])
df['livello'] = df.nome_strada.map(lambda s: res[s][2]); df['motivo'] = df.nome_strada.map(lambda s: res[s][3])
df['fuzzy'] = df.nome_strada.map(lambda s: res[s][4]); df['multi'] = df.nome_strada.map(lambda s: res[s][5])
def vk(s, i):
    v = res[s][6]
    return v[i] if len(v) > i else (None, None)
df['via1_k'] = df.nome_strada.map(lambda s: vk(s, 0)[0]); df['via1'] = df.nome_strada.map(lambda s: vk(s, 0)[1])
df['via2_k'] = df.nome_strada.map(lambda s: vk(s, 1)[0]); df['via2'] = df.nome_strada.map(lambda s: vk(s, 1)[1])
# controllo: dentro Milano (rettangolo largo)
inb = df.lon.between(9.04, 9.28) & df.lat.between(45.38, 45.54)
df.loc[df.lon.notna() & ~inb, ['lon', 'lat']] = np.nan
df.loc[df.lon.isna() & (df.livello != 'nessuna'), 'livello'] = 'nessuna'
pickle.dump(df, open(S + '/out/f4_incidenti_geo.pkl', 'wb'), protocol=4)
q = {'righe': len(df), 'livelli': df.livello.value_counts().to_dict(), 'livelli_pct': (100 * df.livello.value_counts(normalize=True)).round(1).to_dict(),
     'motivi': df.motivo.value_counts().head(15).to_dict(), 'ricerca_approssimata_usata': int(df.fuzzy.sum()),
     'incroci_con_piu_nodi_lontani': int(df.multi.sum()),
     'per_anno_pct_posizione_buona': {int(a): round(100 * v, 1) for a, v in (df.livello.isin(['civico', 'civico_approx', 'incrocio', 'incrocio_approx']).groupby(df.anno).mean()).items()}}
json.dump(q, open(S + '/out/f4_geo_qualita.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(q, indent=1, ensure_ascii=False))
