"""Dati in piu' per la pagina antenne rifatta: per ogni quartiere, distanza dei numeri civici residenziali dall'impianto
di telefonia mobile acceso piu' vicino e numero di impianti per gestore. Scrive docs/antenne/data/nil_vicinanza_gestori.csv
Uso: python -I -X utf8 pagina_v2_dati.py <antenne_dir> <milano_in_dati_dir>"""
import sys, os
import numpy as np, pandas as pd
from scipy.spatial import cKDTree
from pyproj import Transformer
A, P = sys.argv[1], sys.argv[2]
t = pd.read_csv(os.path.join(A, "pulito", "impianti.csv"), sep=";", dtype={"id_nil": "Int64"})
t["acceso"] = t.acceso.astype(str) == "True"
mob = t[t.acceso & t.tipo.isin(["Telefonia", "Microcella"]) & t.gruppo_gestore.isin(
    ["TIM", "Vodafone", "WindTre", "Iliad", "CommsCon", "Cellnex", "INWIT", "OpNet", "Hightel", "TowerCo"])].dropna(subset=["lon", "lat"])
tr = Transformer.from_crs(4326, 32632, always_xy=True)
def xy(lon, lat):
    X, Y = tr.transform(np.asarray(lon, float), np.asarray(lat, float)); return np.column_stack([X, Y])
tree = cKDTree(xy(mob.lon, mob.lat))
civ = pd.read_csv(os.path.join(P, "citta-15-minuti", "out", "civici_tempi.csv"), usecols=["RESIDENZIALE", "ID_NIL", "lon", "lat"])
civ = civ[civ.RESIDENZIALE == 1.0].dropna()
d, _ = tree.query(xy(civ.lon, civ.lat))
civ["d"] = d
g = civ.groupby("ID_NIL").d
out = pd.DataFrame({"civici": g.size(), "dist_mediana_m": g.median().round(0),
                    "entro_100m_pct": g.apply(lambda s: round(100 * (s <= 100).mean(), 1)),
                    "entro_200m_pct": g.apply(lambda s: round(100 * (s <= 200).mean(), 1))})
out.index = out.index.astype(int); out.index.name = "id_nil"
ge = mob.assign(gr=np.where(mob.gruppo_gestore.isin(["TIM", "Vodafone", "WindTre", "Iliad", "CommsCon", "Cellnex"]), mob.gruppo_gestore, "Altre societa")) \
        .groupby(["id_nil", "gr"]).size().unstack(fill_value=0)
ge.index = ge.index.astype(int)
for c in ["TIM", "Vodafone", "WindTre", "Iliad", "CommsCon", "Cellnex", "Altre societa"]:
    if c not in ge: ge[c] = 0
out = out.join(ge[["TIM", "Vodafone", "WindTre", "Iliad", "CommsCon", "Cellnex", "Altre societa"]], how="outer").fillna(0)
for c in out.columns:
    if c not in ("dist_mediana_m", "entro_100m_pct", "entro_200m_pct"): out[c] = out[c].astype(int)
dst = os.path.join(P, "docs", "antenne", "data", "nil_vicinanza_gestori.csv")
out.reset_index().to_csv(dst, sep=";", index=False, encoding="utf-8")
print(len(out), out.sum(numeric_only=True)[["TIM","Vodafone","WindTre","Iliad","CommsCon","Cellnex","Altre societa"]].to_dict(), civ.d.median(), (civ.d<=100).mean())
