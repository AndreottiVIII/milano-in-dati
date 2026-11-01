"""Tabella per zona OMI (2026/1): servizi, reddito, distanza dal Duomo, prezzi OMI abitazioni civili.
Uso: python -I -X utf8 02_tabella_zone.py <ABS milano-in-dati> <ABS case-servizi-reddito>
Entrate: out/civici_zone.csv, out/zone_geom_utm.geojson (da 01), prezzi-case/pulito/prezzi_zona_semestre_prevalente.csv (sola lettura).
Uscita: out/zone_tabella.csv, out/log_02.json
ATTENZIONE: i prezzi OMI sono STIME dell'Agenzia delle Entrate (intervalli min-max, centro = (min+max)/2), non prezzi di vendita reali.
Pesi: 'peso' = residenti 2025 del NIL distribuiti in parti uguali sui civici residenziali del NIL (stessa ipotesi di citta-15-minuti).
"""
import sys, json
import numpy as np, pandas as pd
from pyproj import Transformer
from shapely.geometry import shape, Point

def P(a): return a.replace(chr(92), '/').rstrip('/')
R, O = P(sys.argv[1]), P(sys.argv[2])
LOG = {}
tr = Transformer.from_crs(4326, 32632, always_xy=True)
# Piazza del Duomo (centro della piazza), WGS84
DUOMO_LAT, DUOMO_LON = 45.46427, 9.19192
dx, dy = tr.transform(DUOMO_LON, DUOMO_LAT)
LOG['duomo_lat_lon'] = [DUOMO_LAT, DUOMO_LON]

c = pd.read_csv(O + '/out/civici_zone.csv')
c['d_duomo_m'] = np.hypot(c.x - dx, c.y - dy)
gj = json.load(open(O + '/out/zone_geom_utm.geojson'))
geo = {f['properties']['zona']: shape(f['geometry']) for f in gj['features']}

def wavg(g, col, w='peso'):
    ww = g[w]
    return float((g[col] * ww).sum() / ww.sum()) if ww.sum() > 0 else np.nan

rows = []
for z, g in c.groupby('zona'):
    r = g[g.RESIDENZIALE == 1]
    cen = geo[z].centroid
    rows.append(dict(
        zona=z,
        n_civici_tutti=len(g), n_civici_residenziali=len(r), residenti_stimati=round(float(g.peso.sum())),
        area_km2=round(geo[z].area / 1e6, 3),
        servizi10_pesato=wavg(g, 'punteggio'), servizi20_pesato=wavg(g, 'punteggio_20'),
        servizi10_civici_tutti=g.punteggio.mean(), servizi20_civici_tutti=g.punteggio_20.mean(),
        servizi_extra_pesato=wavg(g, 'punteggio_extra'),
        quota_premium_pesata=wavg(g.assign(prem=(g.punteggio_20 == 20).astype(float)), 'prem'),
        quota_premium_civici_tutti=float((g.punteggio_20 == 20).mean()),
        quota_10su10_pesata=wavg(g.assign(t=(g.punteggio == 10).astype(float)), 't'),
        reddito_imponibile_medio_2024_pesato=wavg(g, 'imponibile_medio_2024'),
        reddito_min_cap=g.imponibile_medio_2024.min(), reddito_max_cap=g.imponibile_medio_2024.max(),
        n_cap=g.CAP.nunique(),
        dist_duomo_centroide_m=float(np.hypot(cen.x - dx, cen.y - dy)),
        dist_duomo_media_civici_m=wavg(g, 'd_duomo_m'),
    ))
t = pd.DataFrame(rows)

# prezzi OMI: abitazioni civili, 2026/1, stato prevalente (colonna prevalente = True)
p = pd.read_csv(R + '/prezzi-case/pulito/prezzi_zona_semestre_prevalente.csv')
p = p[(p.semestre == '2026-S1') & (p.tipologia == 'Abitazioni civili') & (p.prevalente == True)]
assert p.zona.is_unique
p = p[['zona', 'stato', 'fascia', 'compr_min', 'compr_max', 'compr_centro', 'loc_centro']].rename(
    columns={'stato': 'stato_prevalente', 'compr_centro': 'prezzo_eur_m2', 'loc_centro': 'affitto_eur_m2_mese',
             'compr_min': 'prezzo_min', 'compr_max': 'prezzo_max'})
t = t.merge(p, on='zona', how='left')
# nomi dal file del sito (sola lettura)
nm = pd.read_csv(R + '/docs/prezzi-case/data/zone_ultimo_semestre.csv', usecols=['zona', 'nome'])
t = t.merge(nm, on='zona', how='left')
LOG['zone_senza_prezzo'] = t[t.prezzo_eur_m2.isna()].zona.tolist()
LOG['zone_con_prezzo'] = int(t.prezzo_eur_m2.notna().sum())
# controllo contro il file del sito
chk = pd.read_csv(R + '/docs/prezzi-case/data/zone_ultimo_semestre.csv').set_index('zona')
m = t.dropna(subset=['prezzo_eur_m2']).set_index('zona')
LOG['controllo_prezzo_vs_docs_max_scarto'] = float((m.prezzo_eur_m2 - chk.loc[m.index, 'compr_centro']).abs().max())
LOG['stato_prevalente'] = t.stato_prevalente.value_counts().to_dict()
t.sort_values('prezzo_eur_m2', ascending=False).to_csv(O + '/out/zone_tabella.csv', index=False, float_format='%.4f')
json.dump(LOG, open(O + '/out/log_02.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(LOG, indent=1, ensure_ascii=False))
pd.set_option('display.width', 250)
print(t.sort_values('prezzo_eur_m2', ascending=False)[['zona', 'n_civici_tutti', 'n_civici_residenziali', 'servizi10_pesato', 'servizi20_pesato', 'quota_premium_pesata', 'reddito_imponibile_medio_2024_pesato', 'dist_duomo_centroide_m', 'prezzo_eur_m2', 'affitto_eur_m2_mese', 'stato_prevalente']].round(2).to_string())
