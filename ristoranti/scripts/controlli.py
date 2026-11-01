"""Controlli di robustezza sulla freschezza. Legge pulito/osm_poi.csv e pulito/registro.csv (prodotti da freshness.py) e raw/osm/osm_milano_food_chiusi.json.
Uso: python -I -X utf8 controlli.py <ristoranti_abs>
Scrive pulito/controlli.json"""
import sys, os, json
import numpy as np, pandas as pd, shapely
from shapely.strtree import STRtree
from pyproj import Transformer

D = sys.argv[1]
OUT = os.path.join(D, "pulito")
NOW = pd.Timestamp("2026-11-01", tz="UTC")
SIX = ["restaurant", "fast_food", "cafe", "bar", "pub", "ice_cream"]
R = {}
o = pd.read_csv(os.path.join(OUT, "osm_poi.csv"), sep=";", encoding="utf-8-sig", low_memory=False)
o["ts"] = pd.to_datetime(o.timestamp, utc=True)
reg = pd.read_csv(os.path.join(OUT, "registro.csv"), sep=";", encoding="utf-8-sig", low_memory=False)
reg = reg[reg.lon.notna()].reset_index(drop=True)
Tu = Transformer.from_crs(4326, 32632, always_xy=True)
def xy(lon, lat):
    x, y = Tu.transform(np.asarray(lon), np.asarray(lat)); return np.column_stack([x, y])
rxy = xy(reg.lon, reg.lat); rtree = STRtree(shapely.points(rxy))
s6 = o[o.amenity.isin(SIX)].reset_index(drop=True)
pxy = xy(s6.lon, s6.lat)

def dmin(points, tree, txy, radius):
    tp = shapely.points(points)
    res = []
    for k in range(len(points)):
        near = tree.query(tp[k].buffer(radius))
        res.append(min((float(np.hypot(*(txy[j] - points[k]))) for j in near), default=np.inf))
    return np.array(res)

# 1. concentrazione delle modifiche recenti (2025-2026): chi le ha fatte
rec = o[o.ts >= "2025-01-01"]
top = rec.uid.value_counts()
R["modifiche_2025_26"] = {"n": len(rec), "utenti_distinti": int(top.size), "top1_pct": round(100 * top.iloc[0] / len(rec), 1), "top5_pct": round(100 * top.iloc[:5].sum() / len(rec), 1), "top10_pct": round(100 * top.iloc[:10].sum() / len(rec), 1),
                       "changeset_distinti": int(rec.changeset.nunique()), "changeset_top5_pct": round(100 * rec.changeset.value_counts().iloc[:5].sum() / len(rec), 1)}
# quante modifiche 2025-26 sono "vere" (hanno tag di contenuto aggiornato)? proxy: check_date nel 2025-26
cd = pd.to_datetime(o.check_date, errors="coerce", utc=True)
R["check_date_per_anno"] = {int(k): int(v) for k, v in cd.dt.year.value_counts().sort_index().items() if k >= 2018}
R["check_date_ultimi_12_mesi_n"] = int(((NOW - cd).dt.days <= 365).sum())
# modifiche per mese ultimi 24 mesi
R["modifiche_per_mese_ultimi_24"] = {str(k): int(v) for k, v in o[o.ts >= "2024-11-01"].ts.dt.strftime("%Y-%m").value_counts().sort_index().items()}
# utenti con piu' modifiche in assoluto (mapping party / import?)
R["top_utenti_su_tutte_le_modifiche_pct"] = round(100 * o.uid.value_counts().iloc[:5].sum() / len(o), 1)

# 2. abbinamento a distanza: soglie e controllo nullo (stessi punti spostati di 150-400 m)
rng = np.random.default_rng(1101)
for rad in (15, 25, 50):
    d = dmin(pxy, rtree, rxy, rad)
    R[f"match_osm6_entro_{rad}m_pct"] = round(100 * np.mean(d <= rad), 1)
ang = rng.uniform(0, 2 * np.pi, len(pxy)); dist = rng.uniform(150, 400, len(pxy))
sh = pxy + np.column_stack([dist * np.cos(ang), dist * np.sin(ang)])
for rad in (25, 50):
    d = dmin(sh, rtree, rxy, rad)
    R[f"controllo_nullo_spostati_150_400m_entro_{rad}m_pct"] = round(100 * np.mean(d <= rad), 1)
# 3. con indirizzo: tra gli OSM con via+civico, quanti hanno via+civico uguale nel registro
wa = s6[s6.street.notna() & s6.housenumber.notna()]
R["osm6_con_indirizzo"] = {"n": len(wa), "indirizzo_trovato_nel_registro_pct": round(100 * wa.indirizzo_in_registro.mean(), 1), "entro_50m_pct": round(100 * wa.match_50m.mean(), 1)}

# 4. registro -> OSM, con soglia stretta e controllo nullo
oxy = xy(o.lon, o.lat); otree = STRtree(shapely.points(oxy))
r58 = reg[reg.registro == "ds58_in_piano"].reset_index(drop=True); r58xy = xy(r58.lon, r58.lat)
for rad in (25, 50):
    d = dmin(r58xy, otree, oxy, rad)
    R[f"registro_ds58_con_POI_OSM_entro_{rad}m_pct"] = round(100 * np.mean(d <= rad), 1)
ang = rng.uniform(0, 2 * np.pi, len(r58xy)); dist = rng.uniform(150, 400, len(r58xy))
sh2 = r58xy + np.column_stack([dist * np.cos(ang), dist * np.sin(ang)])
R["controllo_nullo_registro_spostato_entro_50m_pct"] = round(100 * np.mean(dmin(sh2, otree, oxy, 50) <= 50), 1)

# 5. copertura relativa per NIL: rapporto OSM/registro normalizzato sul rapporto di tutta la citta'
c = pd.read_csv(os.path.join(OUT, "confronto_nil.csv"), sep=";", encoding="utf-8-sig")
for k in ("reg_ds58", "reg_58_59"):
    ok = c[c[k] >= 20].copy()
    ratio = ok.osm_6tipi / ok[k]
    med = ratio.median(); glob = c.osm_6tipi.sum() / c[k].sum()
    rel = 100 * (ratio / glob - 1)
    R[f"NIL_rapporto_relativo_{k}"] = {"NIL_con_almeno_20_nel_registro": int(len(ok)), "rapporto_citta": round(float(glob), 3), "rapporto_mediano_NIL": round(float(med), 3),
                                        "entro_20pct_dal_rapporto_di_citta": int((rel.abs() <= 20).sum()), "entro_30pct": int((rel.abs() <= 30).sum()),
                                        "rapporto_min": round(float(ratio.min()), 3), "rapporto_max": round(float(ratio.max()), 3)}
    ok = ok.assign(rapporto=ratio.round(3))
    R[f"NIL_estremi_{k}"] = {"piu_bassi": ok.sort_values("rapporto").head(5)[["nil", "osm_6tipi", k, "rapporto"]].to_dict("records"), "piu_alti": ok.sort_values("rapporto").tail(5)[["nil", "osm_6tipi", k, "rapporto"]].to_dict("records")}

# 6. POI chiusi in OSM (disused:/was:/abandoned:) -> il registro li ha ancora?
cl = pd.DataFrame(json.load(open(os.path.join(D, "raw", "osm", "osm_milano_food_chiusi.json"), encoding="utf-8")))
cl["ts"] = pd.to_datetime(cl.timestamp, utc=True)
# escludi quelli dove oggi c'e' un POI food attivo a <20 m (cambio gestione, stesso locale)
cxy = xy(cl.lon, cl.lat)
d_act = dmin(cxy, otree, oxy, 20); d_reg = dmin(cxy, rtree, rxy, 25)
cl["food_attivo_osm_entro_20m"] = d_act <= 20
cl["registro_entro_25m"] = d_reg <= 25
solo = cl[~cl.food_attivo_osm_entro_20m]
R["osm_chiusi"] = {"n": len(cl), "senza_altro_food_attivo_entro_20m": len(solo), "di_cui_ancora_nel_registro_entro_25m": int(solo.registro_entro_25m.sum()),
                   "per_anno_ultima_modifica": {int(k): int(v) for k, v in cl.ts.dt.year.value_counts().sort_index().items()}}
rc = solo[solo.ts >= "2025-01-01"]
R["osm_chiusi_dal_2025"] = {"n": len(rc), "ancora_nel_registro_entro_25m": int(rc.registro_entro_25m.sum())}
cl.to_csv(os.path.join(OUT, "osm_chiusi_vs_registro.csv"), sep=";", index=False, encoding="utf-8-sig")

# 7. OSM attivi con ultima modifica 2026 ma NIENTE nel registro (aperture non ancora registrate, o fuori registro: circoli, mense, ecc.)
r26 = s6[s6.ts >= "2026-01-01"]
R["osm6_modificati_2026"] = {"n": len(r26), "senza_registro_entro_50m": int((~r26.match_50m).sum()), "senza_registro_pct": round(100 * (~r26.match_50m).mean(), 1)}
R["osm6_nuovi_2026_(versione_1)"] = {"n": int((r26.version == 1).sum()), "senza_registro_entro_50m": int(((r26.version == 1) & ~r26.match_50m).sum())}
r25n = s6[(s6.ts >= "2025-01-01") & (s6.version == 1)]
R["osm6_nuovi_2025_26_(versione_1_e_mai_modificati)"] = {"n": len(r25n), "con_registro_entro_50m_pct": round(100 * r25n.match_50m.mean(), 1)}
# 8. tag cuisine: copertura tra ristoranti per anzianita'
rr = s6[s6.amenity == "restaurant"]
R["ristoranti_con_cuisine_pct"] = round(100 * rr.cuisine.notna().mean(), 1)
R["cuisine_prime_20_(ristoranti+fast_food)"] = s6[s6.amenity.isin(["restaurant", "fast_food"])].cuisine.dropna().str.split(";").explode().str.strip().value_counts().head(25).to_dict()
json.dump(R, open(os.path.join(OUT, "controlli.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
