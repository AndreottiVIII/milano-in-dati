"""Verde pubblico per quartiere (NIL): calcola le tabelle in verde/pulito/.

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 build.py <verde_dir> <milano_in_dati_dir>

Legge: verde/raw (ds89 parchi, ds339 e ds1323/ds2926/ds2927 da alberi/raw, aree gioco/cani/condivisi/orti, ds2811 calore, OSM),
alberi/pulito (alberi.csv 2025 per localizzare le aree del 2014, nil_alberi.csv), suolo/pulito/nil_suolo.csv,
citta-15-minuti/out/civici_tempi.csv (minuti a piedi dal parco piu' vicino) e il file dei poligoni dei NIL.
Scrive verde/pulito/: nil_verde.csv, parchi_ds89.csv, aree_ds339_localizzate.csv, serie_citta.csv, schede_per_anno.csv,
confronti.json (correlazioni), controlli.json (controlli e numeri della citta'), osm_controllo.csv.

Due misure del verde per quartiere:
  A = "poligoni": parchi e giardini disegnati dal Comune (ds89), uniti (le sovrapposizioni contano una volta). Esatta ma incompleta.
  B = "completo": A + le aree di ds339 (elenco 2014) classificate ISTAT 1 (verde attrezzato), 2 (parchi urbani), 3 (verde storico)
      che non sono in ds89, localizzate con gli alberi del censimento 2025 (id_area = zona_area): la superficie 2014 e' divisa fra i
      quartieri in proporzione agli alberi; se non ci sono alberi, si usa un poligono (aree gioco/cani/orti/condivisi) con lo stesso id_area.
Escluse da entrambe: aree di arredo urbano (filari, aiuole stradali), giardini scolastici, cimiteri, centri sportivi, edifici pubblici.
"""
import sys, os, json, csv, io, warnings
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, Point
from shapely.ops import unary_union, polygonize, linemerge
from shapely import make_valid
from pyproj import Transformer
from scipy.stats import spearmanr

warnings.filterwarnings("ignore")
V, P = sys.argv[1], sys.argv[2]
RAW, PU = os.path.join(V, "raw"), os.path.join(V, "pulito")
AL = os.path.join(P, "alberi")
os.makedirs(PU, exist_ok=True)
TR = Transformer.from_crs(4326, 32632, always_xy=True)
CTRL = {}


def utm(g):
    return shapely.transform(g, lambda c: np.column_stack(TR.transform(c[:, 0], c[:, 1])))


def gj(path):
    return json.load(open(path, encoding="utf8"))


def spear(x, y, nb=5000, seed=1):
    x, y = np.asarray(x, float), np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y)); x, y = x[ok], y[ok]
    r = spearmanr(x, y)[0]
    rng = np.random.default_rng(seed); n = len(x); bs = []
    for _ in range(nb):
        i = rng.integers(0, n, n)
        if len(set(x[i])) > 1 and len(set(y[i])) > 1:
            bs.append(spearmanr(x[i], y[i])[0])
    return {"rho": round(float(r), 2), "ic95": [round(float(np.percentile(bs, 2.5)), 2), round(float(np.percentile(bs, 97.5)), 2)], "n": int(n)}


# ------------------------------------------------------------------ NIL
nil = pd.read_csv(os.path.join(AL, "pulito", "nil_alberi.csv"), sep=";")
ana = pd.read_csv(os.path.join(P, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
nomi = dict(zip(ana.nil, ana.nil_nome))
nil["nome"] = [nomi.get(int(i)) or str(n).title() for i, n in zip(nil.id_nil, nil.nil)]
assert len(nil) == 88
nilgeo = gj(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"))
NG = {int(f["properties"]["ID_NIL"]): make_valid(utm(shape(f["geometry"]))) for f in nilgeo["features"]}
assert set(NG) == set(int(i) for i in nil.id_nil)
for i, g in NG.items():  # controllo: area poligoni = area_km2 di alberi/
    a = nil.loc[nil.id_nil == i, "area_km2"].iloc[0]
    assert abs(g.area / 1e6 - a) < 0.01, (i, g.area / 1e6, a)
ID = list(NG)
nil = nil.set_index("id_nil")
nil["area_m2"] = pd.Series({i: NG[i].area for i in ID})
POP = nil.abitanti_2024
CITTA_POP = int(POP.sum()); CITTA_AREA = float(nil.area_m2.sum())
CTRL["popolazione_2024_ds205"] = CITTA_POP
CTRL["area_citta_km2_poligoni_nil"] = round(CITTA_AREA / 1e6, 2)
tree = shapely.STRtree([NG[i] for i in ID])


def nil_of_point(x, y):
    """NIL (id) che contiene il punto UTM, altrimenti None"""
    p = Point(x, y)
    for k in tree.query(p, predicate="intersects"):
        return ID[k]
    return None


def per_nil(geom):
    """area (m2) di una geometria UTM in ogni NIL"""
    out = {}
    if geom is None or geom.is_empty:
        return out
    for k in tree.query(geom, predicate="intersects"):
        a = geom.intersection(NG[ID[k]]).area
        if a > 0:
            out[ID[k]] = a
    return out


# ------------------------------------------------------------------ A: ds89
d89 = gj(os.path.join(RAW, "comune_ds89", "parchi.geojson"))
pieces = []
for f in d89["features"]:
    p = f["properties"]
    pieces.append({"key": f"{p['ZONA']}_{str(p['CODICE_ARE']).zfill(3)}", "nome": p["PARCO"], "g": make_valid(utm(shape(f["geometry"])))})
P89 = pd.DataFrame(pieces)
CTRL["ds89_pezzi"] = len(P89)
CTRL["ds89_parchi_con_nome"] = int(P89.key.nunique())
CTRL["ds89_somma_pezzi_km2"] = round(sum(g.area for g in P89.g) / 1e6, 3)
parch = {}
for k, gr in P89.groupby("key"):
    parch[k] = {"nome": gr.nome.iloc[0], "g": unary_union(list(gr.g)), "pezzi": len(gr)}
UNI89 = unary_union([v["g"] for v in parch.values()])
CTRL["ds89_unione_km2"] = round(UNI89.area / 1e6, 3)
A_nil = per_nil(UNI89)
CTRL["ds89_unione_dentro_comune_km2"] = round(sum(A_nil.values()) / 1e6, 3)
rows = []
for k, v in parch.items():
    pn = per_nil(v["g"])
    n_main = max(pn, key=pn.get) if pn else None
    rows.append({"chiave": k, "parco": v["nome"].title(), "pezzi": v["pezzi"], "area_m2": round(v["g"].area), "area_ha": round(v["g"].area / 1e4, 1),
                 "id_nil_prevalente": n_main, "nil_prevalente": nil.nome.get(n_main, "") if n_main else "",
                 "quota_nel_nil_prevalente_pct": round(100 * pn[n_main] / v["g"].area, 1) if n_main else None, "n_nil": len(pn)})
pd.DataFrame(rows).sort_values("area_m2", ascending=False).to_csv(os.path.join(PU, "parchi_ds89.csv"), index=False, sep=";")
GRANDI = {k for k, v in parch.items() if v["g"].area >= 400000}  # 40 ha
CTRL["parchi_oltre_40ha"] = sorted(parch[k]["nome"].title() for k in GRANDI)
A_nil_senza = per_nil(unary_union([v["g"] for k, v in parch.items() if k not in GRANDI]))

# ------------------------------------------------------------------ B: ds339
t339 = pd.read_csv(os.path.join(AL, "raw", "comune_ds339", "ds339_territorioambiente_aree-verdi-zona-superficie_2014.csv"), sep=";", encoding="latin-1",
                   decimal=",", dtype={"Area": str, "Zona": str})
t339["key"] = t339.Zona + "_" + t339.Area.str.zfill(3)
t339["mq"] = t339["Superficie totale in mq"]
CTRL["ds339_senza_superficie"] = t339[t339.mq.isna()][["Zona", "Area", "Nome località"]].to_dict("records")  # 1 area senza superficie: conta 0
t339["mq"] = t339.mq.fillna(0)
t339["cls"] = t339["Classificazione ISTAT"].str[:2].str.strip()
t339 = t339.rename(columns={"Nome località": "nome_loc", "Classificazione ISTAT": "classe_istat"})
assert t339.key.is_unique
CTRL["ds339_aree"] = len(t339); CTRL["ds339_totale_km2"] = round(t339.mq.sum() / 1e6, 3)
CTRL["ds339_per_classe_km2"] = {k: round(v / 1e6, 3) for k, v in t339.groupby("classe_istat").mq.sum().items()}
AB = t339[t339.cls.isin(["1", "2", "3"])].copy()
CTRL["ds339_classi_1_2_3_aree"] = len(AB); CTRL["ds339_classi_1_2_3_km2"] = round(AB.mq.sum() / 1e6, 3)
in89 = AB.key.isin(parch.keys())
CTRL["ds339_cl123_in_ds89_aree"] = int(in89.sum()); CTRL["ds339_cl123_in_ds89_km2_secondo_ds339"] = round(AB[in89].mq.sum() / 1e6, 3)
CTRL["ds89_chiavi_non_in_cl123"] = sorted(set(parch) - set(AB.key))

al = pd.read_csv(os.path.join(AL, "pulito", "alberi.csv"), sep=";", usecols=["edizione", "id_area", "id_nil"], dtype=str)
al = al[al.edizione == "2025-03-31"]
al = al[al.id_nil.notna()]
al["id_nil"] = al.id_nil.astype(float).astype(int)
tn = al.groupby(["id_area", "id_nil"]).size().rename("n").reset_index()
tot = tn.groupby("id_area").n.transform("sum"); tn["q"] = tn.n / tot
TREE_SHARE = {k: dict(zip(g.id_nil, g.q)) for k, g in tn.groupby("id_area")}
CTRL["alberi_2025_con_nil"] = int(len(al))

# poligoni di gioco/cani/condivisi/orti: servono come fallback di localizzazione e per le "schede per anno"
EXTRA = {}
for nm, f in [("gioco", "comune_ds724/ds724_aree_gioco.geojson"), ("cani", "comune_ds52/ds52_aree_fruizione_cani.geojson"),
              ("condivisi", "comune_ds2187/ds2187_giardini_condivisi.geojson"), ("orti", "comune_ds2186/ds2186_aree_orti_comunali.geojson")]:
    rr = []
    for ft in gj(os.path.join(RAW, f))["features"]:
        p = ft["properties"]
        g = make_valid(utm(shape(ft["geometry"])))
        c = g.representative_point()
        rr.append({"id_area": p["id_area"], "anno": (int(str(p["data_ini"])[:4]) if p.get("data_ini") else np.nan), "area_m2": g.area, "nil": nil_of_point(c.x, c.y), "geom": g})
    EXTRA[nm] = pd.DataFrame(rr)
poly_by_area = {}
for nm, df in EXTRA.items():
    for r in df.itertuples():
        poly_by_area.setdefault(r.id_area, []).append(r.nil)

B_extra = {}  # nil -> m2 (aree ds339 non in ds89)
B_extra_senza = {}
loc_rows = []
for r in AB.itertuples():
    if r.key in parch:
        continue
    grande = r.mq >= 400000
    metodo, shares = None, None
    if r.key in TREE_SHARE:
        metodo, shares = "alberi", TREE_SHARE[r.key]
    elif r.key in poly_by_area and any(n is not None for n in poly_by_area[r.key]):
        ns = [n for n in poly_by_area[r.key] if n is not None]
        metodo, shares = "poligono_gioco_cani_orti", {n: ns.count(n) / len(ns) for n in set(ns)}
    if shares is None:
        loc_rows.append({"chiave": r.key, "nome": r.nome_loc, "classe": r.classe_istat, "affidatario": r.AFFIDATARIO, "mq_2014": round(r.mq), "metodo": "non localizzata", "id_nil": "", "n_nil": 0, "n_alberi": 0})
        continue
    for n, q in shares.items():
        B_extra[n] = B_extra.get(n, 0) + q * r.mq
        if not grande:
            B_extra_senza[n] = B_extra_senza.get(n, 0) + q * r.mq
    main = max(shares, key=shares.get)
    loc_rows.append({"chiave": r.key, "nome": r.nome_loc, "classe": r.classe_istat, "affidatario": r.AFFIDATARIO, "mq_2014": round(r.mq), "metodo": metodo, "id_nil": main,
                     "n_nil": len(shares), "n_alberi": int(tn[tn.id_area == r.key].n.sum()) if metodo == "alberi" else 0})
LOC = pd.DataFrame(loc_rows)
LOC.to_csv(os.path.join(PU, "aree_ds339_localizzate.csv"), index=False, sep=";")
nonloc = LOC[LOC.metodo == "non localizzata"]
CTRL["ds339_non_in_ds89_aree"] = int((~in89).sum()); CTRL["ds339_non_in_ds89_km2"] = round(AB[~in89].mq.sum() / 1e6, 3)
CTRL["non_localizzate_aree"] = len(nonloc); CTRL["non_localizzate_km2"] = round(nonloc.mq_2014.sum() / 1e6, 3)
CTRL["non_localizzate_top"] = nonloc.sort_values("mq_2014", ascending=False).head(8)[["chiave", "nome", "affidatario", "mq_2014"]].to_dict("records")
CTRL["localizzate_con_alberi_aree"] = int((LOC.metodo == "alberi").sum()); CTRL["localizzate_con_alberi_km2"] = round(LOC[LOC.metodo == "alberi"].mq_2014.sum() / 1e6, 3)
CTRL["localizzate_con_poligono_aree"] = int((LOC.metodo == "poligono_gioco_cani_orti").sum())
CTRL["localizzate_su_piu_nil_aree"] = int((LOC.n_nil > 1).sum())

# convalida del metodo "alberi": per le aree che hanno sia poligono (ds89) sia alberi, quanta superficie finirebbe nel NIL giusto?
ok_m2 = tot_m2 = 0.0
for k, v in parch.items():
    if k in TREE_SHARE:
        pn = per_nil(v["g"]); s = sum(pn.values())
        for n in set(pn) | set(TREE_SHARE[k]):
            ok_m2 += min(pn.get(n, 0) / s, TREE_SHARE[k].get(n, 0)) * s
        tot_m2 += s
CTRL["convalida_alberi_su_ds89"] = {"aree": sum(1 for k in parch if k in TREE_SHARE), "superficie_nel_nil_giusto_pct": round(100 * ok_m2 / tot_m2, 1), "superficie_km2": round(tot_m2 / 1e6, 2)}

# ------------------------------------------------------------------ tabella per NIL
nil["verde_A_m2"] = pd.Series(A_nil).reindex(ID).fillna(0)
nil["verde_B_m2"] = nil.verde_A_m2 + pd.Series(B_extra).reindex(ID).fillna(0)
nil["verde_A_senza_grandi_m2"] = pd.Series(A_nil_senza).reindex(ID).fillna(0)
nil["verde_B_senza_grandi_m2"] = nil.verde_A_senza_grandi_m2 + pd.Series(B_extra_senza).reindex(ID).fillna(0)
nil["in_classifica"] = (nil.abitanti_2024 >= 5000).astype(int)
for s in "AB":
    nil[f"m2_ab_{s}"] = np.where(nil.abitanti_2024 > 0, nil[f"verde_{s}_m2"] / nil.abitanti_2024.replace(0, np.nan), np.nan)
    nil[f"pct_area_{s}"] = 100 * nil[f"verde_{s}_m2"] / nil.area_m2
    nil[f"m2_ab_{s}_senza_grandi"] = nil[f"verde_{s}_senza_grandi_m2"] / nil.abitanti_2024.replace(0, np.nan)
# parco piu' grande e sua quota
quota_main, nome_main = {}, {}
for k, v in parch.items():
    pn = per_nil(v["g"])
    for n, a in pn.items():
        if a > quota_main.get(n, 0):
            quota_main[n] = a; nome_main[n] = v["nome"].title()
nil["parco_piu_grande"] = pd.Series(nome_main).reindex(ID).fillna("")
nil["parco_piu_grande_m2"] = pd.Series(quota_main).reindex(ID).fillna(0)
nil["parco_piu_grande_quota_A_pct"] = np.where(nil.verde_A_m2 > 0, 100 * nil.parco_piu_grande_m2 / nil.verde_A_m2.replace(0, np.nan), np.nan)

# ------------------------------------------------------------------ distanza dal parco piu' vicino (minuti a piedi, da citta-15-minuti)
ct = pd.read_csv(os.path.join(P, "citta-15-minuti", "out", "civici_tempi.csv"), usecols=["RESIDENZIALE", "ID_NIL", "min_parchi"])
ct = ct[ct.RESIDENZIALE == 1].copy()
CTRL["civici_residenziali_senza_nil"] = int(ct.ID_NIL.isna().sum())
ct = ct[ct.ID_NIL.notna()].copy(); ct["ID_NIL"] = ct.ID_NIL.astype(int)
CTRL["civici_residenziali"] = len(ct); CTRL["civici_residenziali_senza_tempo_parco"] = int(ct.min_parchi.isna().sum())
ct["m"] = ct.min_parchi.fillna(99.0)  # oltre il limite del calcolo (43 minuti): conta come "non raggiunto"
w_nil = (POP / ct.groupby("ID_NIL").size()).rename("w")
ct = ct.join(w_nil, on="ID_NIL")
ct["w"] = ct.w.fillna(0)


def wmed(x, w):
    o = np.argsort(x); x, w = np.asarray(x)[o], np.asarray(w)[o]
    c = np.cumsum(w); return float(x[np.searchsorted(c, c[-1] / 2)]) if c[-1] > 0 else np.nan


mp, q5, q10, q15 = {}, {}, {}, {}
for n, g in ct.groupby("ID_NIL"):
    mp[n] = float(g.m.median()); q5[n] = 100 * float((g.m <= 5).mean()); q10[n] = 100 * float((g.m <= 10).mean()); q15[n] = 100 * float((g.m <= 15).mean())
nil["min_parco_mediana"] = pd.Series(mp).reindex(ID)
nil["quota_entro5min_pct"] = pd.Series(q5).reindex(ID); nil["quota_entro10min_pct"] = pd.Series(q10).reindex(ID); nil["quota_entro15min_pct"] = pd.Series(q15).reindex(ID)
nil["metri_parco_circa"] = (nil.min_parco_mediana * 75).round(-1)  # 4,5 km/h = 75 m al minuto
CTRL["distanza_citta"] = {"minuti_mediana_residenti": round(wmed(ct.m, ct.w), 1), "entro5_pct": round(100 * float((ct.w * (ct.m <= 5)).sum() / ct.w.sum()), 1),
                          "entro10_pct": round(100 * float((ct.w * (ct.m <= 10)).sum() / ct.w.sum()), 1), "entro15_pct": round(100 * float((ct.w * (ct.m <= 15)).sum() / ct.w.sum()), 1),
                          "oltre15_residenti": int(round(float((ct.w * (ct.m > 15)).sum()))), "residenti_pesati": int(round(float(ct.w.sum())))}

# ------------------------------------------------------------------ confronti: alberi, suolo, calore, indice di verde
suolo = pd.read_csv(os.path.join(P, "suolo", "pulito", "nil_suolo.csv"), sep=";").set_index("id_nil")
nil["suolo_consumato_2025_pct"] = suolo.pct_2025.reindex(ID).values
calore = pd.read_csv(os.path.join(RAW, "comune_ds2811", [f for f in os.listdir(os.path.join(RAW, "comune_ds2811")) if f.endswith(".csv")][0]), sep=";").set_index("ID_NIL")
nil["calore_esposizione"] = calore.value.reindex(ID).values
nil["indice_verde_spotted"] = nil.indice_verde  # gia' in alberi/pulito/nil_alberi.csv (ds2813, luglio 2024)
nil["alberi_per_1000ab"] = nil.alberi_per_1000ab_2025
nil["alberi_per_km2"] = nil.alberi_per_km2_2025
nil["abitanti_per_km2"] = nil.abitanti_2024 / (nil.area_m2 / 1e6)
rk = nil[nil.in_classifica == 1]
CONF = {"n_nil_classifica": int(len(rk)), "note": "Spearman fra i NIL con almeno 5.000 residenti; IC 95% da 5.000 ricampionamenti dei NIL"}
for s in "AB":
    CONF[s] = {
        "m2_ab_vs_densita_abitanti": spear(rk[f"m2_ab_{s}"], rk.abitanti_per_km2),
        "m2_ab_vs_alberi_per_1000ab": spear(rk[f"m2_ab_{s}"], rk.alberi_per_1000ab),
        "pct_area_vs_alberi_per_km2": spear(nil[f"pct_area_{s}"], nil.alberi_per_km2),
        "pct_area_vs_suolo_consumato_2025": spear(nil[f"pct_area_{s}"], nil.suolo_consumato_2025_pct),
        "m2_ab_vs_suolo_consumato_2025": spear(rk[f"m2_ab_{s}"], rk.suolo_consumato_2025_pct),
        "pct_area_vs_calore_esposizione": spear(nil[f"pct_area_{s}"], nil.calore_esposizione),
        "m2_ab_vs_calore_esposizione": spear(rk[f"m2_ab_{s}"], rk.calore_esposizione),
        "pct_area_vs_indice_verde_spotted": spear(nil[f"pct_area_{s}"], nil.indice_verde_spotted),
        "m2_ab_vs_minuti_parco": spear(rk[f"m2_ab_{s}"], rk.min_parco_mediana),
    }
CONF["minuti_parco_vs_densita"] = spear(rk.min_parco_mediana, rk.abitanti_per_km2)
CONF["minuti_parco_vs_suolo_consumato"] = spear(nil.min_parco_mediana, nil.suolo_consumato_2025_pct)
# NIL con piu' del 70% di suolo consumato e meno di 3 m2 per abitante, ecc.
json.dump(CONF, open(os.path.join(PU, "confronti.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

# ------------------------------------------------------------------ standard 9 m2
STD = 9.0
for s in "AB":
    r = nil[nil.in_classifica == 1]
    CTRL[f"standard9_{s}"] = {
        "nil_classifica": int(len(r)), "sotto_9": int((r[f"m2_ab_{s}"] < STD).sum()), "sopra_9": int((r[f"m2_ab_{s}"] >= STD).sum()),
        "residenti_in_nil_sotto_9": int(r[r[f"m2_ab_{s}"] < STD].abitanti_2024.sum()), "residenti_classifica": int(r.abitanti_2024.sum()),
        "quota_residenti_in_nil_sotto_9_pct": round(100 * r[r[f"m2_ab_{s}"] < STD].abitanti_2024.sum() / r.abitanti_2024.sum(), 1),
        "mediana_nil": round(float(r[f"m2_ab_{s}"].median()), 1), "minimo": round(float(r[f"m2_ab_{s}"].min()), 2), "massimo": round(float(r[f"m2_ab_{s}"].max()), 1),
        "sotto_3": int((r[f"m2_ab_{s}"] < 3).sum()),
        "citta_m2_ab": round(float(nil[f"verde_{s}_m2"].sum() / CITTA_POP), 2), "citta_pct_area": round(float(100 * nil[f"verde_{s}_m2"].sum() / CITTA_AREA), 2),
        "citta_km2": round(float(nil[f"verde_{s}_m2"].sum() / 1e6), 3),
        "citta_senza_grandi_m2_ab": round(float(nil[f"verde_{s}_senza_grandi_m2"].sum() / CITTA_POP), 2),
        "nil_sotto_9_senza_grandi": int((r[f"m2_ab_{s}_senza_grandi"] < STD).sum()),
        "rapporto_max_min_classifica": (round(float(r[f"m2_ab_{s}"].max() / r[f"m2_ab_{s}"].min()), 1) if r[f"m2_ab_{s}"].min() > 0 else None)}
# quanto del verde dei NIL con pochi residenti
poco = nil[nil.in_classifica == 0]
CTRL["nil_sotto_5000_ab"] = {"n": int(len(poco)), "residenti": int(poco.abitanti_2024.sum()), "verde_A_km2": round(float(poco.verde_A_m2.sum() / 1e6), 3), "verde_B_km2": round(float(poco.verde_B_m2.sum() / 1e6), 3),
                             "quota_verde_A_pct": round(100 * float(poco.verde_A_m2.sum() / nil.verde_A_m2.sum()), 1), "quota_verde_B_pct": round(100 * float(poco.verde_B_m2.sum() / nil.verde_B_m2.sum()), 1)}
CTRL["nil_senza_verde_A"] = int((nil.verde_A_m2 == 0).sum()); CTRL["nil_senza_verde_B"] = int((nil.verde_B_m2 == 0).sum())

# ------------------------------------------------------------------ serie della citta' (ds1323, ds2926, ds2927)
ser = []
for ln in open(os.path.join(AL, "raw", "comune_ds1323", "ds1323_verde-urbano.csv"), encoding="utf8"):
    f = ln.rstrip("\r\n").split(";")
    if f[0] == "Anno":
        continue
    note = ""
    if len(f) == 5:  # riga 2018 "Verde attrezzato;6534108;972": valore con campo in piu', segnalato
        note = f"riga con 5 campi nel file ({';'.join(f)}): letto il primo valore, 972 ignorato"; f = f[:4]
    val = f[3].strip()
    ser.append({"anno": int(f[0]), "gestione": f[1], "tipo": f[2].strip(), "mq": float(val) if val else np.nan, "nota": note})
S = pd.DataFrame(ser)
CTRL["ds1323_righe"] = len(S); CTRL["ds1323_righe_anomale"] = S[S.nota != ""].to_dict("records"); CTRL["ds1323_valori_vuoti"] = S[S.mq.isna()][["anno", "gestione", "tipo"]].to_dict("records")
S.drop(columns="nota").to_csv(os.path.join(PU, "ds1323_pulito.csv"), index=False, sep=";")
pivot = S.pivot_table(index="anno", columns="tipo", values="mq", aggfunc="sum")
tipi_parco = ["Parchi (giardini e ville) urbani", "Ville giardini e parchi", "Verde attrezzato", "Aree naturali protette", "Forestazione urbana"]
ISTAT_M2 = pd.read_csv(os.path.join(AL, "raw", "comune_ds2926", "mq_verde_urbano_per_abitante_milano.csv"), sep=";").set_index("Anno").Mq_verde_urbano_per_abitante
ISTAT_PCT = pd.read_csv(os.path.join(AL, "raw", "comune_ds2927", "incidenza_percentuale_milano.csv"), sep=";").set_index("Anno").Incidenza_percentuale
tot_anno = S.groupby("anno").mq.sum()
serie = pd.DataFrame({"anno": tot_anno.index, "ds1323_totale_mq": tot_anno.values})
serie["ds1323_parchi_attrezzato_mq"] = [S[(S.anno == a) & S.tipo.isin(tipi_parco)].mq.sum() for a in serie.anno]
serie["istat_mq_per_abitante"] = serie.anno.map(ISTAT_M2); serie["istat_pct_superficie"] = serie.anno.map(ISTAT_PCT)
serie.to_csv(os.path.join(PU, "serie_citta.csv"), index=False, sep=";")
CTRL["serie_citta"] = serie.round(1).to_dict("records")

# ------------------------------------------------------------------ schede per anno (aree gioco, cani, giardini condivisi, orti)
sp = []
for nm, df in EXTRA.items():
    g = df.groupby("anno").agg(schede=("id_area", "size"), area_m2=("area_m2", "sum")).reset_index(); g["tipo"] = nm; sp.append(g)
SPA = pd.concat(sp)[["tipo", "anno", "schede", "area_m2"]]
SPA["area_m2"] = SPA.area_m2.round()
SPA.to_csv(os.path.join(PU, "schede_per_anno.csv"), index=False, sep=";")
CTRL["schede_totali"] = {nm: {"schede": int(len(df)), "id_area_distinti": int(df.id_area.nunique()), "ha": round(df.area_m2.sum() / 1e4, 1),
                             "anno_2003_pct": round(100 * float((df.anno == 2003).mean()), 1)} for nm, df in EXTRA.items()}
for nm, df in EXTRA.items():  # per NIL
    c = df[df.nil.notna()].groupby("nil").agg(n=("id_area", "size"), m2=("area_m2", "sum"))
    nil[f"{nm}_n"] = c.n.reindex(ID).fillna(0).astype(int).values
    nil[f"{nm}_m2"] = c.m2.reindex(ID).fillna(0).round().values
rec = pd.concat([df.assign(tipo=nm) for nm, df in EXTRA.items()])
rec = rec[rec.nil.notna()]
rec["periodo"] = pd.cut(rec.anno, [0, 2005, 2015, 2025], labels=["fino_2005", "2006_2015", "2016_2024"])
pp = rec.groupby(["nil", "periodo"], observed=False).size().unstack(fill_value=0)
for c in pp.columns:
    nil[f"schede_{c}"] = pp[c].reindex(ID).fillna(0).astype(int).values
nil["schede_dal_2016"] = nil.schede_2016_2024
nil["gioco_per_1000_bambini_non_calcolato"] = ""  # nessuna stima dei bambini: non calcolato di proposito

# ------------------------------------------------------------------ controllo OSM
os_path = os.path.join(RAW, "osm", "overpass_verde_milano.json")
OSM = {}
if os.path.exists(os_path):
    el = json.load(open(os_path, encoding="utf8"))["elements"]
    polys = {"park": [], "garden": [], "playground": [], "dog_park": []}
    nout = 0
    for e in el:
        lei = e["tags"].get("leisure")
        if lei not in polys:
            continue
        try:
            if e["type"] == "way":
                c = [(p["lon"], p["lat"]) for p in e.get("geometry", [])]
                if len(c) >= 4 and c[0] == c[-1]:
                    polys[lei].append(make_valid(shapely.Polygon(c)))
            else:
                outer = [shapely.LineString([(p["lon"], p["lat"]) for p in m["geometry"]]) for m in e.get("members", []) if m.get("role") == "outer" and m.get("geometry")]
                inner = [shapely.LineString([(p["lon"], p["lat"]) for p in m["geometry"]]) for m in e.get("members", []) if m.get("role") == "inner" and m.get("geometry")]
                if not outer:
                    continue
                po = list(polygonize(linemerge(outer))); pi = list(polygonize(linemerge(inner))) if inner else []
                if not po:
                    nout += 1; continue
                g = unary_union(po)
                if pi:
                    g = g.difference(unary_union(pi))
                polys[lei].append(make_valid(g))
        except Exception:
            nout += 1
    OSM["scartati_non_ricostruibili"] = nout
    OSM["elementi"] = {k: len(v) for k, v in polys.items()}
    comune = unary_union(list(NG.values()))
    U = {}
    for k, v in polys.items():
        if v:
            U[k] = unary_union([utm(g) for g in v]).intersection(comune)
    U["park+garden"] = unary_union([U["park"], U["garden"]]); U["park"] = U["park"]
    OSM["km2_dentro_comune"] = {k: round(g.area / 1e6, 3) for k, g in U.items()}
    OSM["km2_park_meno_garden_privati_non_noto"] = "leisure=garden include giardini privati e aiuole: non e' verde pubblico"
    for k in ["park", "park+garden"]:
        pn = per_nil(U[k]); nil[f"osm_{k.replace('+', '_')}_m2"] = pd.Series(pn).reindex(ID).fillna(0).values
    nil["osm_park_m2_ab"] = nil.osm_park_m2 / nil.abitanti_2024.replace(0, np.nan)
    rk = nil[nil.in_classifica == 1]
    OSM["spearman_m2_ab_A_vs_osm_park"] = spear(rk.m2_ab_A, rk.osm_park_m2_ab)
    OSM["spearman_m2_ab_B_vs_osm_park"] = spear(rk.m2_ab_B, rk.osm_park_m2_ab)
    OSM["osm_park_m2_ab_citta"] = round(float(nil.osm_park_m2.sum() / CITTA_POP), 2)
    OSM["osm_park_garden_m2_ab_citta"] = round(float(nil.osm_park_garden_m2.sum() / CITTA_POP), 2)
    # quanto di A e B e' coperto da OSM (park+garden)
    # Bosco in citta' (ds339 7_402, Italia Nostra, 118 ha, non localizzabile con gli alberi): dove lo mette OSM?
    bic = [make_valid(utm(g)) for g in [shapely.Polygon([(p["lon"], p["lat"]) for p in e["geometry"]]) for e in el
           if e["type"] == "way" and e["tags"].get("leisure") == "park" and e["tags"].get("name", "").replace(" ", "").lower() in ("boscoincittà", "boscoincitta")]]
    if bic:
        bu = unary_union(bic).intersection(comune); pb = per_nil(bu)
        OSM["bosco_in_citta_osm"] = {"km2": round(bu.area / 1e6, 3), "per_nil_m2": {nil.nome.get(n, str(n)): round(a) for n, a in sorted(pb.items(), key=lambda x: -x[1])}}
    OSM["A_coperta_da_osm_park_garden_pct"] = round(100 * UNI89.intersection(U["park+garden"]).area / UNI89.area, 1)
CTRL["osm"] = OSM

# ------------------------------------------------------------------ uscita
keep = ["nome", "area_m2", "abitanti_2024", "abitanti_per_km2", "in_classifica", "verde_A_m2", "m2_ab_A", "pct_area_A", "verde_B_m2", "m2_ab_B", "pct_area_B",
        "verde_A_senza_grandi_m2", "m2_ab_A_senza_grandi", "verde_B_senza_grandi_m2", "m2_ab_B_senza_grandi", "parco_piu_grande", "parco_piu_grande_m2", "parco_piu_grande_quota_A_pct",
        "min_parco_mediana", "metri_parco_circa", "quota_entro5min_pct", "quota_entro10min_pct", "quota_entro15min_pct",
        "alberi_per_1000ab", "alberi_per_km2", "suolo_consumato_2025_pct", "calore_esposizione", "indice_verde_spotted",
        "gioco_n", "gioco_m2", "cani_n", "cani_m2", "condivisi_n", "condivisi_m2", "orti_n", "orti_m2", "schede_fino_2005", "schede_2006_2015", "schede_2016_2024"] \
       + [c for c in nil.columns if c.startswith("osm_")]
out = nil[keep].copy()
out.insert(0, "id_nil", out.index)
for c in out.columns:
    if out[c].dtype.kind == "f":
        out[c] = out[c].round(2)
out.to_csv(os.path.join(PU, "nil_verde.csv"), index=False, sep=";")
json.dump(CTRL, open(os.path.join(PU, "controlli.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, default=float)
print(json.dumps({k: CTRL[k] for k in ["ds89_unione_km2", "ds339_classi_1_2_3_km2", "non_localizzate_km2", "convalida_alberi_su_ds89", "standard9_A", "standard9_B", "distanza_citta"]}, ensure_ascii=False, indent=1, default=float))
print(json.dumps(CONF, ensure_ascii=False, indent=1))
print(json.dumps(OSM, ensure_ascii=False, indent=1))
