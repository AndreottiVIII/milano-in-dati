"""Passo 1 - collegamenti civico -> NIL, CAP, zona OMI.

Idea: i civici (punti) sono il ponte. Ogni civico residenziale ha gia' NIL e CAP (CAP stimato: punto con CAP noto piu'
vicino, vedi citta-15-minuti/NOTE.md) e qui riceve anche la zona OMI del 2014/2 e quella del 2026/1 (punto-in-poligono,
con i perimetri di ciascun semestre, cosi' i cambi di zonizzazione non contano: ogni civico confronta la zona che aveva
nel 2014/2 con la zona che ha nel 2026/1).
Il valore di un NIL = media sui civici residenziali del NIL (stessi pesi di citta-15-minuti: gli abitanti del NIL sono
distribuiti in parti uguali sui civici residenziali, quindi la media semplice e' la media pesata con i residenti stimati).

Entrate: citta-15-minuti/out/civici_tempi.csv, prezzi-case/raw/geopoi/F205_20142.json e F205_20261.json,
         prezzi-case/pulito/prezzi_zona_semestre_prevalente.csv
Uscite (out/): civici_collegamenti.csv, collegamento_cap_nil.csv, collegamento_omi_nil.csv, collegamenti_log.json
Uso: python -I -X utf8 01_collegamenti.py <milano-in-dati> <quartieri-che-cambiano>
"""
import sys, os, json
from functools import reduce
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Polygon, Point
from shapely.strtree import STRtree
from shapely.validation import make_valid
import shapely

BASE = sys.argv[1]
OUT = os.path.join(sys.argv[2], 'out')
os.makedirs(OUT, exist_ok=True)
TR = Transformer.from_crs(4326, 32632, always_xy=True)
log = {}


def geom_feature(feat):
    """Perimetro in metri. Anelli con OR esclusivo (regola pari/dispari, vedi prezzi-case/scripts/05_zone_corrispondenza.py)."""
    ps = []
    for ring in feat['geometry']['coordinates']:
        a = np.array(ring, dtype=float)
        x, y = TR.transform(a[:, 0], a[:, 1])
        ps.append(make_valid(Polygon(np.column_stack([x, y]))))
    return reduce(lambda p, q: p.symmetric_difference(q), ps)


def carica_zone(path):
    d = json.load(open(path, encoding='utf-8'))
    z = {}
    for f in d['dat']['features']:
        cod = f['properties']['zona']
        g = geom_feature(f)
        z[cod] = z[cod].union(g) if cod in z else g
    return z


def assegna(punti, zone):
    codici = list(zone.keys())
    tree = STRtree([zone[c] for c in codici])
    pi, gi = tree.query(punti, predicate='within')
    res = np.full(len(punti), None, dtype=object)
    molteplici = 0
    visti = set()
    for p, g in zip(pi, gi):
        if p in visti:
            molteplici += 1
            continue
        visti.add(p)
        res[p] = codici[g]
    return res, molteplici


civ = pd.read_csv(os.path.join(BASE, 'citta-15-minuti', 'out', 'civici_tempi.csv'),
                  usecols=['IDMASTER', 'RESIDENZIALE', 'ID_NIL', 'NIL', 'lon', 'lat', 'CAP', 'CAP_dist_m'])
log['civici_totali'] = int(len(civ))
log['civici_residenziali'] = int((civ.RESIDENZIALE == 1).sum())
log['civici_senza_CAP'] = int(civ.CAP.isna().sum())
x, y = TR.transform(civ.lon.values, civ.lat.values)
pts = shapely.points(x, y)

geo = os.path.join(BASE, 'prezzi-case', 'raw', 'geopoi')
z0 = carica_zone(os.path.join(geo, 'F205_20142.json'))
z1 = carica_zone(os.path.join(geo, 'F205_20261.json'))
log['aree_km2'] = {'2014_2': round(sum(g.area for g in z0.values()) / 1e6, 2),
                   '2026_1': round(sum(g.area for g in z1.values()) / 1e6, 2)}
civ['zona_2014_2'], m0 = assegna(pts, z0)
civ['zona_2026_1'], m1 = assegna(pts, z1)
log['civici_in_piu_zone'] = {'2014_2': int(m0), '2026_1': int(m1)}
log['civici_senza_zona'] = {'2014_2': int(civ.zona_2014_2.isna().sum()), '2026_1': int(civ.zona_2026_1.isna().sum())}

# valori OMI: abitazioni civili, stato prevalente
p = pd.read_csv(os.path.join(BASE, 'prezzi-case', 'pulito', 'prezzi_zona_semestre_prevalente.csv'))
p = p[(p.tipologia == 'Abitazioni civili') & (p.prevalente == True)]
assert p.groupby(['semestre', 'zona']).size().max() == 1


def val(sem, col):
    s = p[p.semestre == sem].set_index('zona')[col]
    return s


for nome, sem, zc in [('0', '2014-S2', 'zona_2014_2'), ('1', '2026-S1', 'zona_2026_1')]:
    civ['prezzo_reale_' + nome] = civ[zc].map(val(sem, 'compr_centro_reale_2025'))
    civ['affitto_reale_' + nome] = civ[zc].map(val(sem, 'loc_centro_reale_2025'))
civ['crescita_prezzo'] = civ.prezzo_reale_1 / civ.prezzo_reale_0 - 1
civ['crescita_affitto'] = civ.affitto_reale_1 / civ.affitto_reale_0 - 1
civ.to_csv(os.path.join(OUT, 'civici_collegamenti.csv'), index=False)

res = civ[civ.RESIDENZIALE == 1]
log['residenziali_con_valore_omi'] = {'prezzo_cresc': int(res.crescita_prezzo.notna().sum()),
                                      'affitto_cresc': int(res.crescita_affitto.notna().sum()),
                                      'prezzo_2026': int(res.prezzo_reale_1.notna().sum())}

# tabelle del collegamento (documentazione)
cn = res.groupby(['ID_NIL', 'CAP']).size().rename('civici_res').reset_index()
cn['quota_nil'] = cn.civici_res / cn.groupby('ID_NIL').civici_res.transform('sum')
cn.to_csv(os.path.join(OUT, 'collegamento_cap_nil.csv'), index=False)
zn = res.groupby(['ID_NIL', 'zona_2026_1']).size().rename('civici_res').reset_index()
zn['quota_nil'] = zn.civici_res / zn.groupby('ID_NIL').civici_res.transform('sum')
zn.to_csv(os.path.join(OUT, 'collegamento_omi_nil.csv'), index=False)

dom = cn.sort_values('quota_nil', ascending=False).groupby('ID_NIL').head(1)
log['NIL_con_CAP_dominante_ge_90pct'] = int((dom.quota_nil >= 0.9).sum())
log['NIL_con_CAP_dominante_lt_60pct'] = int((dom.quota_nil < 0.6).sum())
log['NIL_con_civici_residenziali'] = int(res.ID_NIL.nunique())
log['civici_res_per_nil_min_mediana_max'] = [int(v) for v in
                                             [res.groupby('ID_NIL').size().min(), res.groupby('ID_NIL').size().median(), res.groupby('ID_NIL').size().max()]]
json.dump(log, open(os.path.join(OUT, 'collegamenti_log.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(json.dumps(log, ensure_ascii=False, indent=1))
