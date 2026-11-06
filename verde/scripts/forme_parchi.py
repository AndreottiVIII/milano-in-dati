"""Due file nuovi per la pagina "Parchi e verde" (docs/verde/data/), solo nomi nuovi.

Uso (percorsi assoluti):
  python -I -X utf8 forme_parchi.py <milano_in_dati_dir>

1) parchi_grandi_forma.json: i 12 parchi disegnati piu' grandi (ds89, uniti per parco), contorni in metri
   (proiezione UTM 32N, semplificati a 6 m), per disegnarli con la stessa scala uno accanto all'altro.
2) nil_parco_vicino.csv: per ogni quartiere, il parco (ds89, almeno 5.000 m2) piu' vicino in linea d'aria
   alla maggior parte dei civici residenziali (civici_tempi.csv della pagina citta-15-minuti), con la distanza mediana in linea d'aria.
Licenza dei dati: Comune di Milano, CC BY.
"""
import sys, os, json, csv, re
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import shape, Point
from shapely.ops import transform, unary_union
from shapely.strtree import STRtree

R = sys.argv[1]
DOCS = os.path.join(R, "docs", "verde", "data")
tr = Transformer.from_crs(4326, 32632, always_xy=True).transform

BREVI = {
    "Parco Delle Cave": "Cave", "Parco Lambro": "Lambro", "Parco Di Trenno": "Trenno",
    "Parco Enrico Forlanini": "Forlanini", "Parco Sempione": "Sempione", "Parco Monte Stella": "Monte Stella",
    "Giardini Pubblici Indro Montanelli": "Giardini Montanelli", "Parco Della Cava Di Muggiano": "Cava di Muggiano",
    "Parco Di Villa Scheibler": "Villa Scheibler", "Parco Gino Cassinis": "Gino Cassinis", "Parco Adriano": "Adriano",
    "Bosco Di Bruzzano": "Bosco di Bruzzano",
    "Parco Martiri Della Liberta' Iracheni Vittime Del Terrorismo": "Martiri della Libertà",
    "Parco Dell'Acqua": "Parco dell'Acqua", "Parco Monlue'": "Monluè", "Parco Teramo Barona": "Teramo Barona",
}


def breve(n):
    if n in BREVI:
        return BREVI[n]
    m = re.sub(r"^(Parco|Giardini Pubblici|Giardino|Giardini)\s+(?:(?:Di|Del|Della|Delle|Dei|Dell')\s*)?", "", n).strip()
    m = m.replace("'", "’")
    m = re.sub(r"\bIi\b", "II", m)
    m = re.sub(r"(?<=\S )(Di|Del|Della|Delle|Dei|Degli|E|Da)(?= )", lambda x: x.group(1).lower(), m)
    return m[:1].upper() + m[1:] if m else n


P = json.load(open(os.path.join(DOCS, "parchi.geojson"), encoding="utf8"))
parchi = []
for f in P["features"]:
    g = transform(tr, shape(f["geometry"]))
    parchi.append((f["properties"]["n"], g))
assert len(parchi) == 74

# --- 1) forme dei 12 piu' grandi
top = sorted(parchi, key=lambda t: -t[1].area)[:12]
out = []
for n, g in top:
    gs = g.simplify(6, preserve_topology=True)
    x0, y0, x1, y1 = gs.bounds
    polys = list(gs.geoms) if gs.geom_type == "MultiPolygon" else [gs]
    d = ""
    for pg in polys:
        if pg.area < 400:
            continue
        for ring in [pg.exterior] + list(pg.interiors):
            c = list(ring.coords)
            d += "M" + "L".join("%d %d" % (round(x - x0), round(y1 - y)) for x, y in c) + "Z"
    out.append({"nome": n, "breve": breve(n), "ha": round(g.area / 1e4, 1), "w": round(x1 - x0), "h": round(y1 - y0), "d": d})
json.dump(out, open(os.path.join(DOCS, "parchi_grandi_forma.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
print("forme:", [(o["breve"], o["ha"]) for o in out])

# --- 2) parco piu' vicino per quartiere
big = [(n, g) for n, g in parchi if g.area >= 5000]
tree = STRtree([g for _, g in big])
cv = pd.read_csv(os.path.join(R, "citta-15-minuti", "out", "civici_tempi.csv"), usecols=["RESIDENZIALE", "ID_NIL", "x", "y"])
cv = cv[(cv.RESIDENZIALE > 0) & cv.ID_NIL.notna()].copy()
cv["ID_NIL"] = cv.ID_NIL.astype(int)
pts = [Point(x, y) for x, y in zip(cv.x, cv.y)]
idx = tree.query_nearest(pts, all_matches=False)
near = np.full(len(pts), -1)
near[idx[0]] = idx[1]
dist = np.array([big[j][1].distance(p) if j >= 0 else np.nan for j, p in zip(near, pts)])
cv["par"] = near
cv["dist"] = dist
rows = []
for nid, gr in cv.groupby("ID_NIL"):
    vc = gr.par.value_counts()
    j = int(vc.index[0])
    sub = gr[gr.par == j]
    rows.append({"id_nil": nid, "parco": big[j][0], "parco_breve": breve(big[j][0]), "parco_ha": round(big[j][1].area / 1e4, 1),
                 "quota_civici_pct": round(100 * len(sub) / len(gr)), "distanza_linea_aria_m_mediana": int(round(float(np.nanmedian(gr.dist))))})
w = csv.DictWriter(open(os.path.join(DOCS, "nil_parco_vicino.csv"), "w", encoding="utf8", newline=""), fieldnames=list(rows[0].keys()), delimiter=";")
w.writeheader(); w.writerows(rows)
print("nil con parco vicino:", len(rows))
