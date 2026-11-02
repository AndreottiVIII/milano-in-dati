"""Scrive i file dati della pagina "Quanto sono vecchi i palazzi" (docs/palazzi/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <progetto_milano_in_dati_dir> <docs_dir>

Legge (tutto gia' sul disco, niente scaricamenti):
  censimenti/pulito/sezioni_2011.csv          edifici residenziali per epoca di costruzione (ISTAT, variabili E3, E8-E16) e abitazioni occupate (A2)
  censimenti/pulito/raccordo_sezioni_2011.csv sezione -> NIL (sovrapposizione geometrica, area massima)
  censimenti/pulito/raccordo_quote_area_2011.csv  quote di area di ogni sezione in ogni NIL (per la prova di sensibilita')
  censimenti/pulito/sezioni_1991.csv + raccordo_sezioni_1991.csv   abitazioni occupate per epoca (A11-A16, 1991)
  censimenti/pulito/sezioni_2001.csv          edifici per epoca (E9-E15, 2001): solo controllo sul totale della citta'
  censimenti/pulito/sezioni_2021.csv          edifici residenziali 2021 (E3): solo controllo, il 2021 non ha l'epoca
  censimenti/raw/comune_ckan/ds1456*/         abitazioni occupate per epoca dell'edificio, per municipio (Comune, censimento 2011)
  censimenti/pulito/geometrie/sezioni_2011_Milano.geojson   poligoni delle sezioni 2011 (EPSG:32632)
  censimenti/pulito/nil_2021_anagrafica.csv, indicatori_NIL.csv   nomi e residenti dei NIL
  docs/censimenti/data/nil.geojson            poligoni dei 88 NIL (gia' semplificati, WGS84)
  docs/prezzi-case/data/zone.geojson + zone_ultimo_semestre.csv   zone OMI e prezzi dell'ultimo semestre
  costruzioni/pulito/nil_costruzioni.csv      nuove abitazioni dei permessi 2014-2024 per NIL
Scrive in <docs_dir>/palazzi/data/: riepilogo.json, nil.geojson, nil.csv, epoche_citta_municipi.csv.
Dati aggregati (per NIL, municipio, citta'): nessun edificio singolo.
"""
import sys, os, json, glob, math
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, mapping, box
from shapely.strtree import STRtree
from pyproj import Transformer
from scipy.stats import spearmanr

P, DOCS = sys.argv[1], sys.argv[2]
CP = os.path.join(P, "censimenti", "pulito")
OUT = os.path.join(DOCS, "palazzi", "data")
os.makedirs(OUT, exist_ok=True)
assert int(shapely.__version__.split(".")[0]) >= 2

AVVISI = []
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok:
        AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")

EP = ["E8", "E9", "E10", "E11", "E12", "E13", "E14", "E15", "E16"]
EP_ETI = ["prima del 1919", "1919-1945", "1946-1960", "1961-1970", "1971-1980", "1981-1990", "1991-2000", "2001-2005", "dopo il 2005"]
EP_ETI_COMUNE = ["Prima del 1919", "Dal 1919 al 1945", "Dal 1946 al 1960", "Dal 1961 al 1970", "Dal 1971 al 1980",
                 "Dal 1981 al 1990", "Dal 1991 al 2000", "Dal 2001 al 2005", "Dopo il 2005"]
SOGLIA_EDIFICI = 100  # sotto questa soglia le quote per NIL non sono colorate sulla mappa
SOGLIA_CLASSIFICA = 200  # per le classifiche: almeno 200 edifici residenziali (62 NIL)

def num(x, d=1):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), d)

# ---------------------------------------------------------------- 2011: edifici per sezione -> NIL
s11 = pd.read_csv(os.path.join(CP, "sezioni_2011.csv"), low_memory=False)
rac = pd.read_csv(os.path.join(CP, "raccordo_sezioni_2011.csv")).drop_duplicates("sezione")
ana = pd.read_csv(os.path.join(CP, "nil_2021_anagrafica.csv")).set_index("nil")
ind = pd.read_csv(os.path.join(CP, "indicatori_NIL.csv"))
pop11 = ind[ind.anno == 2011].set_index("nil")["pop"]
m = s11.merge(rac[["sezione", "nil", "municipio", "purezza_nil"]], left_on="NSEZ", right_on="sezione", how="left", validate="1:1")
assert m.nil.notna().all()
check("sezioni 2011 con dati", len(m), 6017)
check("edifici residenziali 2011 (E3)", int(m.E3.sum()), 42980)
check("E8..E16 sommano a E3 in ogni sezione", int((m[EP].sum(axis=1) - m.E3).abs().sum()), 0)
check("abitazioni occupate 2011 (A2)", int(m.A2.sum()), 604507)

g = m.groupby("nil")[["E3"] + EP + ["A2", "E21", "E22", "E23", "E24", "E25", "E26", "E27"]].sum()
assert len(g) == 88 and set(g.index) == set(ana.index)
for c in g.columns:
    g[c] = g[c].astype(int)
check("somma NIL = totale citta'", int(g.E3.sum()), 42980)

# citta'
C = g[EP].sum()
cit_ed = [int(x) for x in C]
cit_ed_pct = [100 * x / sum(cit_ed) for x in cit_ed]

# ---------------------------------------------------------------- prova di sensibilita': ripartizione per quota di area
qa = pd.read_csv(os.path.join(CP, "raccordo_quote_area_2011.csv"))
qa = qa[qa.anno == 2011]
mm = qa.merge(m[["NSEZ"] + EP + ["E3"]], left_on="sezione", right_on="NSEZ", how="inner")
alt = pd.DataFrame({e: (mm[e] * mm.quota_area).groupby(mm.nil).sum() for e in EP}).reindex(g.index).fillna(0)
alt_tot = alt.sum(axis=1)
robust = g.E3 >= SOGLIA_EDIFICI
diff_pts = pd.DataFrame({e: 100 * (alt[e] / alt_tot - g[e] / g.E3) for e in EP}).abs().max(axis=1)[robust]
dom_main = (g[EP].div(g.E3, axis=0)).idxmax(axis=1)
dom_alt = (alt.div(alt_tot, axis=0)).idxmax(axis=1)
SENS = {"differenza_max_mediana_punti": num(diff_pts.median(), 1), "differenza_max_massima_punti": num(diff_pts.max(), 1),
        "nil_con_epoca_dominante_diversa": int((dom_main[robust] != dom_alt[robust]).sum()), "nil_robusti": int(robust.sum()),
        "edifici_totali_ripartiti": num(alt_tot.sum(), 0)}
print("sensibilita'", SENS)

# ---------------------------------------------------------------- abitazioni 2011 per epoca, per municipio (Comune ds1456)
righe = []
for f in sorted(glob.glob(os.path.join(P, "censimenti", "raw", "comune_ckan", "ds1456*", "0[0-8]_ds1456_cens2011_occupati_municipio_*.csv"))):
    righe.append(pd.read_csv(f, sep=";"))
assert len(righe) == 9
d1456 = pd.concat(righe)
d1456 = d1456[d1456["Edificio"].str.startswith("Epoca")]
mun_ab = {}
for mun, dd in d1456.groupby("Municipio"):
    k = int(mun.split()[-1])
    v = dict(zip(dd["Caratteristiche dell'edificio"], dd["Numero di abitazioni"]))
    mun_ab[k] = [int(v[e]) for e in EP_ETI_COMUNE]
    mun_ab[k].append(int(v["Edificio non residenziale"]))
assert sorted(mun_ab) == list(range(1, 10))
cit_ab = [sum(mun_ab[k][i] for k in mun_ab) for i in range(9)]
cit_ab_nonres = sum(mun_ab[k][9] for k in mun_ab)
check("abitazioni per epoca (Comune ds1456) + non residenziali = A2 delle sezioni", sum(cit_ab) + cit_ab_nonres, int(m.A2.sum()), tol=10)
cit_ab_pct = [100 * x / sum(cit_ab) for x in cit_ab]

# edifici per municipio (sezioni 2011 + raccordo)
mun_ed = {}
for k, dd in m.groupby("municipio"):
    mun_ed[int(k)] = [int(dd[e].sum()) for e in EP]
check("edifici per municipio sommano alla citta'", sum(sum(v) for v in mun_ed.values()), 42980)

# ---------------------------------------------------------------- 1991: abitazioni occupate per epoca -> NIL
s91 = pd.read_csv(os.path.join(CP, "sezioni_1991.csv"), low_memory=False)
r91 = pd.read_csv(os.path.join(CP, "raccordo_sezioni_1991.csv")).drop_duplicates("sezione")
m91 = s91.merge(r91[["sezione", "nil"]], left_on="SEZIONE", right_on="sezione", how="left", validate="1:1")
assert m91.nil.notna().all()
A91 = ["A11", "A12", "A13", "A14", "A15", "A16"]
check("abitazioni occupate 1991 = somma A11..A16", int(m91[A91].sum().sum()), int(m91.A2.sum()))
g91 = m91.groupby("nil")[A91 + ["A2"]].sum().reindex(g.index).fillna(0).astype(int)
check("abitazioni occupate 1991 (A2)", int(g91.A2.sum()), 576777)

# controlli sui totali di altri censimenti
s01 = pd.read_csv(os.path.join(CP, "sezioni_2001.csv"), low_memory=False)
s21 = pd.read_csv(os.path.join(CP, "sezioni_2021.csv"), low_memory=False)
E01 = [int(s01[c].sum()) for c in ["E9", "E10", "E11", "E12", "E13", "E14", "E15"]]
c2001 = {"edifici_residenziali": int(s01.E3.sum()), "per_epoca_1": E01,
         "epoche": ["prima del 1919", "1919-1945", "1946-1961", "1962-1971", "1972-1981", "1982-1991", "dopo il 1991"]}
check("somma epoche 2001 = E3 2001", sum(E01), c2001["edifici_residenziali"])
c2021 = {"edifici_residenziali": int(s21.E3.sum())}

# ---------------------------------------------------------------- prezzi OMI per NIL (via sezioni 2011)
tr = Transformer.from_crs(4326, 32632, always_xy=True)
zg = json.load(open(os.path.join(DOCS, "prezzi-case", "data", "zone.geojson"), encoding="utf8"))
zp = pd.read_csv(os.path.join(DOCS, "prezzi-case", "data", "zone_ultimo_semestre.csv")).set_index("zona")
zgeom, zval = [], []
for f in zg["features"]:
    z = f["properties"]["zona"]
    gg = shapely.transform(shape(f["geometry"]), lambda a: np.column_stack(tr.transform(a[:, 0], a[:, 1])))
    zgeom.append(gg)
    zval.append(float(zp.loc[z, "compr_centro"]))
zval = np.array(zval)
print("zone OMI", len(zgeom), "prezzi", zval.min(), zval.max())
tree = STRtree(zgeom)
sg = json.load(open(os.path.join(CP, "geometrie", "sezioni_2011_Milano.geojson"), encoding="utf8"))
prez = {}
for f in sg["features"]:
    nsez = int(round(float(f["properties"]["SEZ"])))
    gs = shape(f["geometry"])
    if not gs.is_valid:
        gs = gs.buffer(0)
    area = gs.area
    if area <= 0:
        continue
    tot = 0.0; acc = 0.0
    for i in tree.query(gs):
        a = gs.intersection(zgeom[i]).area
        if a > 0:
            tot += a; acc += a * zval[i]
    prez[nsez] = (acc / tot if tot > 0 else None, tot / area)
m = m.assign(pz=m.NSEZ.map(lambda k: prez.get(int(k), (None, 0))[0]),
             pz_cop=m.NSEZ.map(lambda k: prez.get(int(k), (None, 0))[1]))
mp = m[(m.A2 > 0)]
def nil_price(dd):
    ok = dd[dd.pz.notna()]
    w = ok.A2 * ok.pz_cop.clip(upper=1)
    return pd.Series({"pz": (ok.pz * w).sum() / w.sum() if w.sum() > 0 else np.nan,
                      "cop": ok.A2.sum() / dd.A2.sum() if dd.A2.sum() > 0 else np.nan})
npz = mp.groupby("nil").apply(nil_price, include_groups=False).reindex(g.index)

# ---------------------------------------------------------------- permessi 2014-2024
nc = pd.read_csv(os.path.join(P, "costruzioni", "pulito", "nil_costruzioni.csv"), sep=";").set_index("id_nil").reindex(g.index)
check("abitazioni nuove 2014-2024 assegnate a un NIL", int(nc.nuove_abitazioni_2014_2024.sum()), 25005)

# ---------------------------------------------------------------- tabella NIL
nil = pd.DataFrame(index=g.index)
nil["nome"] = ana.nil_nome
nil["municipio"] = ana.municipio_prevalente.astype(int)
nil["residenti_2011"] = pop11.reindex(g.index).astype(int)
nil["edifici"] = g.E3
for i, e in enumerate(EP):
    nil[f"n{i}"] = g[e]
nil["robusto"] = robust
sh = g[EP].div(g.E3, axis=0) * 100
sh = sh.fillna(0)
nil["pre46"] = sh["E8"] + sh["E9"]
nil["boom4670"] = sh["E10"] + sh["E11"]
nil["post80"] = sh[["E13", "E14", "E15", "E16"]].sum(axis=1)
nil["post00"] = sh[["E15", "E16"]].sum(axis=1)
dom = sh.idxmax(axis=1).map({e: i for i, e in enumerate(EP)})
nil["dominante"] = dom
cum = sh.cumsum(axis=1)
nil["epoca_mediana"] = (cum >= 50).idxmax(axis=1).map({e: i for i, e in enumerate(EP)})
nil["ab_2011"] = g.A2
nil["interni_per_edificio"] = (g.E27 / g.E3).replace([np.inf], np.nan)
nil["grandi_9piu"] = 100 * (g.E25 + g.E26) / g.E3
for i, a in enumerate(A91):
    nil[f"a91_{i}"] = g91[a]
nil["a91_tot"] = g91.A2
nil["a91_pre46"] = 100 * (g91.A11 + g91.A12) / g91.A2.replace(0, np.nan)
nil["prezzo"] = npz.pz.round(0)
nil["prezzo_cop"] = (100 * npz.cop).round(0)
nil["nuove_ab_14_24"] = nc.nuove_abitazioni_2014_2024.fillna(0).astype(int)
nil["nuove_per_100_ab"] = 100 * nil.nuove_ab_14_24 / nil.ab_2011.replace(0, np.nan)
nil["pre46_robusto"] = nil.pre46.where(nil.robusto)

# accordo tra edifici 2011 e abitazioni 1991 (stessa idea: quanto e' antico)
both = nil[nil.robusto & (nil.a91_tot >= 1000)]
rho_91 = spearmanr(both.pre46, both.a91_pre46)
print("Spearman pre46 edifici 2011 vs abitazioni 1991:", rho_91, len(both))

# ---------------------------------------------------------------- confronto con i prezzi
rng = np.random.default_rng(30102026)
def spear(x, y):
    r = spearmanr(x, y)[0]
    n = len(x); b = []
    xs, ys = np.asarray(x), np.asarray(y)
    for _ in range(5000):
        ix = rng.integers(0, n, n)
        b.append(spearmanr(xs[ix], ys[ix])[0])
    return [num(r, 3), [num(np.percentile(b, 2.5), 3), num(np.percentile(b, 97.5), 3)], n]
pr = nil[nil.robusto & nil.prezzo.notna() & (nil.prezzo_cop >= 80)]
conf = {"n_nil": int(len(pr)),
        "spearman_pre46": spear(pr.pre46, pr.prezzo),
        "spearman_boom4670": spear(pr.boom4670, pr.prezzo),
        "spearman_post80": spear(pr.post80, pr.prezzo)}
gr = []
for d, dd in pr.groupby("dominante"):
    gr.append({"epoca": int(d), "n": int(len(dd)), "prezzo_mediano": num(dd.prezzo.median(), 0),
               "min": num(dd.prezzo.min(), 0), "max": num(dd.prezzo.max(), 0)})
conf["per_epoca_dominante"] = gr
# confronto a pari "centralita'": solo NIL con la stessa fascia di prezzo non e' possibile; cittadino semplice: coppie di tipologie
conf["prezzo_mediano_nil_robusti"] = num(pr.prezzo.median(), 0)
print("confronto prezzi", json.dumps(conf, ensure_ascii=False))

# ---------------------------------------------------------------- numeri della citta' e classifiche
rob = nil[nil.robusto]
rk = nil[nil.edifici >= SOGLIA_CLASSIFICA]
def top(col, n=8, asc=False):
    d = rk.sort_values(col, ascending=asc).head(n)
    return [[int(i), r.nome, num(r[col], 1), int(r.edifici)] for i, r in d.iterrows()]

cit = {
    "edifici": int(g.E3.sum()), "per_epoca": cit_ed, "per_epoca_pct": [num(x, 1) for x in cit_ed_pct],
    "abitazioni_occupate": int(sum(cit_ab)), "abitazioni_per_epoca": cit_ab, "abitazioni_per_epoca_pct": [num(x, 1) for x in cit_ab_pct],
    "abitazioni_non_in_edifici_residenziali": int(cit_ab_nonres),
    "edifici_pre46_pct": num(cit_ed_pct[0] + cit_ed_pct[1], 1), "edifici_4670_pct": num(cit_ed_pct[2] + cit_ed_pct[3], 1),
    "edifici_dopo80_pct": num(sum(cit_ed_pct[5:]), 1), "edifici_dopo90_pct": num(sum(cit_ed_pct[6:]), 1),
    "abitazioni_pre46_pct": num(cit_ab_pct[0] + cit_ab_pct[1], 1), "abitazioni_4670_pct": num(cit_ab_pct[2] + cit_ab_pct[3], 1),
    "abitazioni_fino80_pct": num(sum(cit_ab_pct[:5]), 1), "abitazioni_dopo80_pct": num(sum(cit_ab_pct[5:]), 1),
    "abitazioni_dopo90_pct": num(sum(cit_ab_pct[6:]), 1),
    "interni_per_edificio": num(g.E27.sum() / g.E3.sum(), 1),
    "edifici_1_2_interni_pct": num(100 * (g.E21.sum() + g.E22.sum()) / g.E3.sum(), 1),
    "edifici_9piu_interni_pct": num(100 * (g.E25.sum() + g.E26.sum()) / g.E3.sum(), 1),
    "edifici_16piu_interni": int(g.E26.sum()),
}
# epoca dominante: conteggio NIL
dc = rob.dominante.value_counts().sort_index()
cit["nil_per_epoca_dominante"] = {int(k): int(v) for k, v in dc.items()}
cit["nil_robusti"] = int(len(rob)); cit["nil_non_robusti"] = int((~nil.robusto).sum())

# nuove abitazioni dopo il censimento
nuove = nil.sort_values("nuove_ab_14_24", ascending=False)
cit_nuove = {
    "abitazioni_nuove_2014_2024": int(nil.nuove_ab_14_24.sum()),
    "senza_nil": int(26174 - nil.nuove_ab_14_24.sum()),
    "top": [[int(i), r.nome, int(r.nuove_ab_14_24), num(r.nuove_per_100_ab, 1)] for i, r in nuove.head(8).iterrows()],
    "top_per_100": [[int(i), r.nome, int(r.nuove_ab_14_24), num(r.nuove_per_100_ab, 1)]
                    for i, r in nil[nil.ab_2011 >= 2000].sort_values("nuove_per_100_ab", ascending=False).head(8).iterrows()],
    "nil_senza_nuove": int((nil.nuove_ab_14_24 == 0).sum()),
}
check("abitazioni nuove totali 2014-2024 (costruzioni)", cit_nuove["abitazioni_nuove_2014_2024"] + cit_nuove["senza_nil"], 26174)

riep = {
    "meta": {"anno_dati": 2011, "soglia_edifici": SOGLIA_EDIFICI, "epoche": EP_ETI, "generato_da": "palazzi/scripts/pagina.py",
             "soglia_classifiche": SOGLIA_CLASSIFICA, "nil_in_classifica": int(len(nil[nil.edifici >= SOGLIA_CLASSIFICA])), "nil": 88, "data_dati": "2 novembre 2026", "nil_con_pochi_edifici": int((~nil.robusto).sum())},
    "citta": cit, "municipi": {"edifici": {str(k): v for k, v in mun_ed.items()}, "abitazioni": {str(k): v for k, v in mun_ab.items()}},
    "classifiche": {"piu_vecchi": top("pre46", 8), "piu_nuovi": top("post80", 8, False), "boom": top("boom4670", 8), "meno_boom": top("boom4670", 8, True),
                    "piu_ottocento": top("n0", 0) if False else [[int(i), r.nome, num(100 * r.n0 / r.edifici, 1), int(r.edifici)]
                                                          for i, r in rk.assign(x=100 * rk.n0 / rk.edifici).sort_values("x", ascending=False).head(8).iterrows()]},
    "dopo_il_2011": cit_nuove, "prezzi": conf,
    "controlli": {"censimento_2001": c2001, "censimento_2021": c2021, "sensibilita_area": SENS,
                  "spearman_edifici_2011_vs_abitazioni_1991_pre46": [num(rho_91[0], 3), int(len(both))],
                  "sezioni_con_dati": 6017, "purezza_nil_min_sezioni_con_edifici": num(m[m.E3 > 0].purezza_nil.min(), 2),
                  "avvisi": AVVISI},
    "origine": {
        "edifici": "ISTAT, censimento 2011, basi territoriali per sezione (variabili E3, E8-E16), file censimenti/pulito/sezioni_2011.csv; sezione -> NIL: censimenti/pulito/raccordo_sezioni_2011.csv",
        "abitazioni_2011": "Comune di Milano ds1456 (Censimento 2011: caratteristiche degli edifici occupati, per municipio): abitazioni occupate da residenti per epoca di costruzione dell'edificio",
        "abitazioni_1991": "ISTAT, censimento 1991 per sezione (A11-A16, abitazioni occupate per epoca); sezione -> NIL per sovrapposizione geometrica (censimenti/pulito/raccordo_sezioni_1991.csv)",
        "prezzi": "OMI (Agenzia delle Entrate) abitazioni civili stato prevalente, centro di min-max, 1 semestre 2026 (docs/prezzi-case/data/zone_ultimo_semestre.csv); zone docs/prezzi-case/data/zone.geojson; sovrapposizione con le sezioni 2011",
        "nuove_abitazioni": "Comune di Milano, nuovi fabbricati 2014-2024 (ds270, ds2984, ds2983): costruzioni/pulito/nil_costruzioni.csv",
        "interni": "ISTAT 2011, E21-E27 (edifici residenziali per numero di interni; E27 totale interni)"},
}
json.dump(riep, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- geometrie + proprieta' compatte
nf = json.load(open(os.path.join(DOCS, "censimenti", "data", "nil.geojson"), encoding="utf8"))
assert sorted(f["properties"]["i"] for f in nf["features"]) == list(range(1, 89))
feats = []
for f in nf["features"]:
    i = f["properties"]["i"]
    r = nil.loc[i]
    pr_ = {"i": i, "n": r.nome, "m": int(r.municipio), "r": int(r.residenti_2011), "T": int(r.edifici), "E": [int(r[f"n{k}"]) for k in range(9)],
           "rb": 1 if r.robusto else 0, "d": int(r.dominante), "em": int(r.epoca_mediana),
           "p46": num(r.pre46, 1), "b": num(r.boom4670, 1), "p80": num(r.post80, 1), "p00": num(r.post00, 1),
           "ab": int(r.ab_2011), "ipe": num(r.interni_per_edificio, 1), "g9": num(r.grandi_9piu, 1),
           "a91": [int(r[f"a91_{k}"]) for k in range(6)], "a91t": int(r.a91_tot), "a91p46": num(r.a91_pre46, 1),
           "pz": num(r.prezzo, 0), "pzc": num(r.prezzo_cop, 0), "nw": int(r.nuove_ab_14_24), "nw100": num(r.nuove_per_100_ab, 1)}
    feats.append({"type": "Feature", "properties": pr_, "geometry": f["geometry"]})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# csv leggibile
out = pd.DataFrame({"id_nil": nil.index, "nil": nil.nome, "municipio": nil.municipio, "residenti_2011": nil.residenti_2011, "edifici_residenziali_2011": nil.edifici})
for k, e in enumerate(EP_ETI):
    out[f"edifici_{e.replace(' ', '_')}"] = nil[f"n{k}"].values
for k, e in enumerate(EP_ETI):
    out[f"quota_{e.replace(' ', '_')}_pct"] = (100 * nil[f"n{k}"] / nil.edifici).round(1).values
out["quota_prima_del_1946_pct"] = nil.pre46.round(1).values
out["quota_1946_1970_pct"] = nil.boom4670.round(1).values
out["quota_dopo_il_1980_pct"] = nil.post80.round(1).values
out["epoca_dominante"] = [EP_ETI[int(k)] for k in nil.dominante]
out["epoca_mediana"] = [EP_ETI[int(k)] for k in nil.epoca_mediana]
out["quote_affidabili_(almeno_100_edifici)"] = nil.robusto.map({True: "si", False: "no"}).values
out["abitazioni_occupate_2011"] = nil.ab_2011.values
out["interni_per_edificio"] = nil.interni_per_edificio.round(1).values
out["abitazioni_occupate_1991"] = nil.a91_tot.values
out["quota_abitazioni_1991_costruite_prima_del_1946_pct"] = nil.a91_pre46.round(1).values
out["prezzo_omi_eur_m2_2026S1"] = nil.prezzo.values
out["copertura_prezzo_pct"] = nil.prezzo_cop.values
out["abitazioni_nuove_2014_2024_permessi"] = nil.nuove_ab_14_24.values
out.to_csv(os.path.join(OUT, "nil.csv"), index=False, encoding="utf-8", lineterminator="\n")

rows = []
rows.append(["Milano (edifici residenziali)", "citta"] + cit_ed + [sum(cit_ed)])
rows.append(["Milano (abitazioni occupate)", "citta"] + cit_ab + [sum(cit_ab)])
for k in range(1, 10):
    rows.append([f"Municipio {k} (edifici residenziali)", "municipio"] + mun_ed[k] + [sum(mun_ed[k])])
    rows.append([f"Municipio {k} (abitazioni occupate)", "municipio"] + mun_ab[k][:9] + [sum(mun_ab[k][:9])])
pd.DataFrame(rows, columns=["territorio", "livello"] + EP_ETI + ["totale"]).to_csv(
    os.path.join(OUT, "epoche_citta_municipi.csv"), index=False, encoding="utf-8", lineterminator="\n")

print("\nFATTO. Avvisi:", AVVISI or "nessuno")
if AVVISI:
    sys.exit(1)
