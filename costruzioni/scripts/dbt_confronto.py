"""Confronto tra il Database Topografico (DBT) 2012 e 2020 del Comune di Milano: unita' volumetriche fuori terra.
Per ogni unita' 2020: quota dell'impronta che copre un'unita' del 2012 -> 'nuova' se < 20%; per ogni unita' 2012: quota coperta dal 2020 -> 'sparita' se < 20%.
Unita' presenti in entrambi (copertura >= 80% e partner prevalente): sopraelevazione se l'altezza cresce di >= 3 m, riduzione se cala di >= 3 m.
Uso: python -I -X utf8 dbt_confronto.py <costruzioni (assoluto)> <milano-in-dati (assoluto)>
Richiede in raw/dbt2012/x e raw/dbt2020/x i file estratti (vedi STATO.md). Scrive pulito/dbt_unita_*.csv, pulito/dbt_nil.csv, pulito/dbt_controlli.json
"""
import sys, os, json
import numpy as np, pandas as pd, shapely
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.strtree import STRtree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import shp

C, P = sys.argv[1], sys.argv[2]
log = {}
MIN_AREA = 20.0   # m2: sotto questa soglia l'unita' e' ignorata (tettoie, chioschi, rumore)

def ring_area(r):
    a = 0.0
    for i in range(len(r) - 1): a += r[i][0] * r[i+1][1] - r[i+1][0] * r[i][1]
    return a / 2

def build(rings):
    polys = []
    for r in rings:
        if len(r) < 4: continue
        if ring_area(r) < 0 or not polys: polys.append([r, []])   # senso orario = esterno
        else: polys[-1][1].append(r)
    gs = []
    for o, h in polys:
        try: gs.append(Polygon(o, h))
        except Exception: pass
    if not gs: return None
    g = gs[0] if len(gs) == 1 else MultiPolygon(gs)
    if not g.is_valid: g = shapely.make_valid(g)
    return g

def load(dbf, shpf, filtro, hfield, extra=None):
    rows = list(shp.dbf_rows(dbf)); geoms = []
    for rings in shp.shp_polys(shpf): geoms.append(build(rings) if rings else None)
    assert len(rows) == len(geoms), (len(rows), len(geoms))
    keep = [i for i, r in enumerate(rows) if geoms[i] is not None and not r["_del"]]
    g = np.array([geoms[i] for i in keep], dtype=object)
    h = np.array([float(rows[i][hfield] or 0) for i in keep])
    ft = np.array([bool(filtro(rows[i])) for i in keep])
    return g, h, ft, (np.array([rows[i][extra] for i in keep]) if extra else None)

D12 = os.path.join(C, "raw", "dbt2012", "x"); D20 = os.path.join(C, "raw", "dbt2020", "x", "DBT 2020 - SHAPE")
g12, h12, ft12, z12 = load(os.path.join(D12, "A020101.Dbf"), os.path.join(D12, "A020101.Shp"), lambda r: r["UN_VOL_POR"] == "0301", "UN_VOL_AV", "ID_ZRIL")
g20, h20, ft20, _ = load(os.path.join(D20, "UN_VOL.dbf"), os.path.join(D20, "UN_VOL.shp"), lambda r: r["UN_VOL_POR"] == "01", "UN_VOL_AV")
log["origine_unita_2012_per_ID_ZRIL"] = pd.Series([v[:7] for v in z12]).value_counts().to_dict()
log["unita_2012_tutti_i_tipi"] = int(len(g12)); log["unita_2012_fuori_terra_0301"] = int(ft12.sum()); log["unita_2020_tutti_i_tipi"] = int(len(g20)); log["unita_2020_fuori_terra_01"] = int(ft20.sum())
a12 = shapely.area(g12); a20 = shapely.area(g20)
k12 = a12 >= MIN_AREA; k20 = a20 >= MIN_AREA
z12 = z12[k12]
g12, h12, a12, ft12 = g12[k12], h12[k12], a12[k12], ft12[k12]; g20, h20, a20, ft20 = g20[k20], h20[k20], a20[k20], ft20[k20]
# tutte le unita' (anche interrate/altri tipi) servono come bersaglio della copertura; le statistiche usano solo le fuori terra
T12, T20 = g12, g20; H12_all = np.where(h12 < 2.5, 2.5, h12); FT12_all = ft12.copy()
log["unita_2012_tutti_i_tipi_dopo_soglia"] = int(len(g12)); log["unita_2020_tutti_i_tipi_dopo_soglia"] = int(len(g20))
z12 = z12[ft12]
g12, h12, a12 = g12[ft12], h12[ft12], a12[ft12]; g20, h20, a20 = g20[ft20], h20[ft20], a20[ft20]
h12 = np.where(h12 < 2.5, 2.5, h12); h20 = np.where(h20 < 2.5, 2.5, h20)   # altezze nulle/negative -> 2,5 m minimo (segnalato)
log["soglia_area_m2"] = MIN_AREA; log["unita_2012_dopo_soglia"] = int(len(g12)); log["unita_2020_dopo_soglia"] = int(len(g20))
log["area_impronta_totale_km2"] = {"2012": round(float(a12.sum()) / 1e6, 3), "2020": round(float(a20.sum()) / 1e6, 3)}
log["volume_totale_milioni_m3"] = {"2012": round(float((a12 * h12).sum()) / 1e6, 2), "2020": round(float((a20 * h20).sum()) / 1e6, 2)}

def coverage(src, tgt, a_src, tgt_h=None):
    """quota dell'area di src coperta da tgt + indice del partner con maggiore sovrapposizione"""
    tree = STRtree(tgt)
    si, ti = tree.query(src, predicate="intersects")
    inter = shapely.area(shapely.intersection(src[si], tgt[ti]))
    cov = np.zeros(len(src)); best = np.full(len(src), -1); bestv = np.zeros(len(src))
    np.add.at(cov, si, inter)
    for s, t_, v in zip(si, ti, inter):
        if v > bestv[s]: bestv[s] = v; best[s] = t_
    return np.minimum(cov / a_src, 1.0), best

cov20, best20 = coverage(g20, T12, a20)     # quanto delle unita' 2020 esisteva nel 2012 (qualunque tipo)
cov12, best12 = coverage(g12, T20, a12)     # quanto delle unita' 2012 esiste ancora nel 2020 (qualunque tipo)
# NIL del centroide
gj = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
from pyproj import Transformer
tr = Transformer.from_crs(4326, 7791, always_xy=True)
nilp = [shapely.transform(shape(f["geometry"]), lambda c: np.column_stack(tr.transform(c[:, 0], c[:, 1]))) for f in gj["features"]]
nid = [int(f["properties"]["ID_NIL"]) for f in gj["features"]]; nnm = [f["properties"]["NIL"] for f in gj["features"]]
nt = STRtree(nilp)
def nil_of(g):
    c = shapely.centroid(g); pi, gi = nt.query(c, predicate="within")
    out = np.full(len(g), -1)
    for a, b in zip(pi, gi): out[a] = b
    # fuori: piu' vicino
    miss = np.where(out < 0)[0]
    if len(miss):
        ni, dm = nt.query_nearest(c[miss], return_distance=True)
        for a, j, d_ in zip(ni[0], ni[1], dm): out[miss[a]] = j
    return out
n20 = nil_of(g20); n12 = nil_of(g12)

u20 = pd.DataFrame({"area_m2": a20, "altezza_m": h20, "volume_m3": a20 * h20, "copertura_2012": cov20, "nil_idx": n20})
u12 = pd.DataFrame({"area_m2": a12, "altezza_m": h12, "volume_m3": a12 * h12, "copertura_2020": cov12, "nil_idx": n12})
# esito
u20["esito"] = np.where(u20.copertura_2012 < 0.2, "nuova", np.where(u20.copertura_2012 < 0.8, "ampliata_o_cambiata", "gia_presente"))
u12["esito"] = np.where(u12.copertura_2020 < 0.2, "sparita", np.where(u12.copertura_2020 < 0.8, "ridotta_o_cambiata", "ancora_presente"))
dh = np.where((best20 >= 0) & FT12_all[np.clip(best20, 0, None)], h20 - H12_all[np.clip(best20, 0, None)], np.nan)
u20["delta_altezza_m"] = dh
u20.loc[(u20.esito == "gia_presente") & (u20.delta_altezza_m >= 3), "esito"] = "sopraelevata"
u20.loc[(u20.esito == "gia_presente") & (u20.delta_altezza_m <= -3), "esito"] = "abbassata"
pers = u20[(u20.copertura_2012 >= 0.8)].delta_altezza_m.dropna()
log["delta_altezza_unita_presenti_percentili_1_10_25_50_75_90_99"] = [round(float(x), 2) for x in np.percentile(pers, [1, 10, 25, 50, 75, 90, 99])]
log["esiti_2020"] = u20.esito.value_counts().to_dict(); log["esiti_2012"] = u12.esito.value_counts().to_dict()

# volume aggiunto da sopraelevazione = area x delta altezza; da nuove = volume
u20["vol_netto_m3"] = np.where(u20.esito == "nuova", u20.volume_m3, np.where(u20.esito.isin(["sopraelevata", "abbassata"]), u20.area_m2 * u20.delta_altezza_m.fillna(0), 0))
rows = []
for i in range(len(nid)):
    a = u20[u20.nil_idx == i]; b = u12[u12.nil_idx == i]
    nuova = a[a.esito == "nuova"]; sop = a[a.esito == "sopraelevata"]; sparita = b[b.esito == "sparita"]
    gn = nuova[nuova.area_m2 >= 300]; gs = sparita[sparita.area_m2 >= 300]
    rows.append({"id_nil": nid[i], "nil": nnm[i], "grandi_nuove_n": len(gn), "grandi_nuove_volume_m3": round(gn.volume_m3.sum()), "grandi_sparite_n": len(gs), "grandi_sparite_volume_m3": round(gs.volume_m3.sum()),
                 "unita_nuove": len(nuova), "area_nuove_m2": round(nuova.area_m2.sum()), "volume_nuove_m3": round(nuova.volume_m3.sum()),
                 "unita_sopraelevate": len(sop), "volume_sopraelevazioni_m3": round((sop.area_m2 * sop.delta_altezza_m).sum()),
                 "unita_sparite": len(sparita), "area_sparite_m2": round(sparita.area_m2.sum()), "volume_sparite_m3": round(sparita.volume_m3.sum()),
                 "volume_2012_m3": round(b.volume_m3.sum()), "volume_2020_m3": round(a.volume_m3.sum())})
res = pd.DataFrame(rows)
res["grandi_volume_netto_m3"] = res.grandi_nuove_volume_m3 - res.grandi_sparite_volume_m3
res["volume_netto_m3"] = res.volume_nuove_m3 + res.volume_sopraelevazioni_m3 - res.volume_sparite_m3
res["variazione_volume_2012_2020_m3"] = res.volume_2020_m3 - res.volume_2012_m3
res["variazione_volume_pct"] = (100 * res.variazione_volume_2012_2020_m3 / res.volume_2012_m3).round(2)
res.to_csv(os.path.join(C, "pulito", "dbt_nil.csv"), index=False, sep=";", encoding="utf-8")
# le unita' nuove e sparite, con centroide WGS84, per eventuale mappa
tr2 = Transformer.from_crs(7791, 4326, always_xy=True)
def dump(g, df, name, sel):
    s = df[sel].copy(); c = shapely.centroid(g[sel.values])
    x, y = tr2.transform(shapely.get_x(c), shapely.get_y(c))
    s["lon"] = np.round(x, 6); s["lat"] = np.round(y, 6); s["id_nil"] = [nid[i] if i >= 0 else None for i in s.nil_idx]
    s.drop(columns=["nil_idx"]).round(2).to_csv(os.path.join(C, "pulito", name), index=False, sep=";", encoding="utf-8")
dump(g20, u20, "dbt_unita_nuove_2020.csv", u20.esito.isin(["nuova", "sopraelevata"]))
dump(g12, u12, "dbt_unita_sparite_2012.csv", u12.esito == "sparita")
gN = u20[(u20.esito == "nuova") & (u20.area_m2 >= 300)]; gS = u12[(u12.esito == "sparita") & (u12.area_m2 >= 300)]
log["unita_grandi_oltre_300m2"] = {"nuove_n": int(len(gN)), "nuove_volume_milioni_m3": round(float(gN.volume_m3.sum()) / 1e6, 2), "sparite_n": int(len(gS)), "sparite_volume_milioni_m3": round(float(gS.volume_m3.sum()) / 1e6, 2)}
log["totali"] = {"nuove_n": int((u20.esito == "nuova").sum()), "nuove_volume_milioni_m3": round(float(u20[u20.esito == "nuova"].volume_m3.sum()) / 1e6, 2),
                 "sopraelevate_n": int((u20.esito == "sopraelevata").sum()), "sopraelevate_volume_aggiunto_milioni_m3": round(float((u20[u20.esito == "sopraelevata"].area_m2 * u20[u20.esito == "sopraelevata"].delta_altezza_m).sum()) / 1e6, 2),
                 "sparite_n": int((u12.esito == "sparita").sum()), "sparite_volume_milioni_m3": round(float(u12[u12.esito == "sparita"].volume_m3.sum()) / 1e6, 2)}
json.dump(log, open(os.path.join(C, "pulito", "dbt_controlli.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(log, ensure_ascii=False, indent=1))
