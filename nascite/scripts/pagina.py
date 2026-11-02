"""Scrive i file dati della pagina "Nascite e mamme" (docs/nascite/data/). Si puo' rilanciare.
Uso: python -I -X utf8 pagina.py <nascite_dir> <milano_in_dati_dir> <docs_dir>        (percorsi assoluti)

Prima va lanciato 01_pulisci.py (scrive nascite/pulito/). Legge pulito/*.csv e i confini dei NIL di citta-15-minuti (ds964).
Scrive in <docs_dir>/nascite/data/:
  riepilogo.json, nil.geojson (confini semplificati + serie 2003-2024 per quartiere), nil_anno.csv, citta_anno.csv,
  eta_madre_citta_2021_2024.csv, tfr_eta_madre_istat.csv, tfr_citta_2021_2024.csv, nil_2022_2024.csv
Dati aggregati (per quartiere e per anno): nessun dato individuale. I numeri dei fatti sono ricalcolati e confrontati (check) con i controlli di pulito/.
"""
import sys, os, json
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, mapping

N, M, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(N, "pulito")
OUT = os.path.join(DOCS, "nascite", "data")
os.makedirs(OUT, exist_ok=True)
AVVISI = []

def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok:
        AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")

def R(x, d=1):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), d)

ANNI = list(range(2003, 2025))
ana = pd.read_csv(os.path.join(M, "censimenti", "pulito", "nil_2021_anagrafica.csv")).rename(columns={"nil": "id_nil", "nil_nome": "nome"})
nomi = dict(zip(ana.id_nil, ana.nome))
tassi = pd.read_csv(os.path.join(PU, "tassi_nil_anno.csv"))
den = pd.read_csv(os.path.join(PU, "denominatori_nil_anno.csv"))
nasc = pd.read_csv(os.path.join(PU, "nascite_nil_anno.csv"))
citta = pd.read_csv(os.path.join(PU, "citta_anno.csv"))
eta = pd.read_csv(os.path.join(PU, "eta_madre_citta.csv"))
tfrc = pd.read_csv(os.path.join(PU, "tfr_citta_2021_2024.csv"))
ist = pd.read_csv(os.path.join(PU, "istat_tfr_eta_madre.csv"))
chk = json.load(open(os.path.join(PU, "controlli.json"), encoding="utf8"))

# ------------------------------------------------------------------ NIL: serie per anno
res24 = den[den.anno == 2024].set_index("id_nil").residenti.reindex(sorted(int(i) for i in ana.id_nil), fill_value=0)   # Parco Sempione (8): nessun residente in ds27
tt = tassi.set_index(["id_nil", "anno"])
nilgeo = json.load(open(os.path.join(M, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
geom = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in nilgeo["features"]}
assert set(geom) == set(int(i) for i in ana.id_nil) and len(geom) == 88

def serie(i, col, d=0):
    out = []
    for y in ANNI:
        out.append(R(tt.loc[(i, y), col], d) if (i, y) in tt.index else None)
    return out

feats, nil_rows = [], []
for i in sorted(ana.id_nil, key=lambda k: nomi[k]):
    i = int(i)
    p = {"i": i, "n": nomi[i], "ab": int(res24[i]), "cl": 1 if res24[i] >= 3000 else 0,
         "b": [int(x or 0) for x in serie(i, "nati")],                      # nati (residenti) 2003..2024
         "w": serie(i, "donne_15_49_medie", 0),                       # donne 15-49 (media 31/12 anno prima e anno)
         "p": serie(i, "residenti_medi", 0),                           # residenti (stessa media)
         "s": [int(x or 0) for x in serie(i, "madre_straniera")],           # nati con madre di cittadinanza straniera
         "t": [int(x or 0) for x in serie(i, "madre_italiana")]}           # nati con madre di cittadinanza italiana
    g = geom[i].simplify(0.00003, preserve_topology=True)
    gj = mapping(g)
    def rnd(c):
        return [rnd(x) for x in c] if isinstance(c[0], (list, tuple)) else [round(c[0], 5), round(c[1], 5)]
    feats.append({"type": "Feature", "properties": p, "geometry": {"type": gj["type"], "coordinates": rnd(gj["coordinates"])}})
json.dump({"type": "FeatureCollection", "anni": ANNI, "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

t2 = tassi.copy()
t2.insert(1, "nil", t2.id_nil.map(nomi))
t2.to_csv(os.path.join(OUT, "nil_anno.csv"), index=False, sep=";")

# aggregazione 2022-2024 e 2003-2005 (somma di nati e di esposizione)
def per(y0, y1):
    x = tassi[tassi.anno.between(y0, y1)].groupby("id_nil").agg(nati=("nati", "sum"), w=("donne_15_49_medie", "sum"), p=("residenti_medi", "sum"),
                                                                ms=("madre_straniera", "sum"), mi=("madre_italiana", "sum"))
    x["r"] = 1000 * x.nati / x.w
    x["rp"] = 1000 * x.nati / x.p
    x["qs"] = 100 * x.ms / (x.ms + x.mi)
    return x
a1, a0 = per(2022, 2024), per(2003, 2005)
a1["nil"] = a1.index.map(nomi)
a1["r_2003_2005"] = a0.r
a1["nati_2003_2005"] = a0.nati
a1["residenti_2024"] = a1.index.map(res24)
a1["classifica"] = (a1.residenti_2024 >= 3000).astype(int)
out = a1.reset_index()[["id_nil", "nil", "residenti_2024", "classifica", "nati", "w", "r", "rp", "qs", "nati_2003_2005", "r_2003_2005"]]
out.columns = ["id_nil", "nil", "residenti_2024", "in_classifica_almeno_3000_residenti", "nati_2022_2024", "donne_15_49_anni_persona_2022_2024",
               "nati_per_1000_donne_15_49_2022_2024", "nati_per_1000_residenti_2022_2024", "quota_madre_straniera_pct_2022_2024",
               "nati_2003_2005", "nati_per_1000_donne_15_49_2003_2005"]
out.round(2).to_csv(os.path.join(OUT, "nil_2022_2024.csv"), index=False, sep=";")

cl = a1[a1.classifica == 1]
check("quartieri in classifica (>= 3.000 residenti nel 2024)", len(cl), int((res24 >= 3000).sum()))
cl_ok = cl[(cl.nati >= 100)]
def rows(df, col, n, asc):
    d = df.sort_values(col, ascending=asc).head(n)
    return [{"n": r.nil, "v": R(r[col], 1), "nati": int(r.nati), "ab": int(r.residenti_2024)} for _, r in d.iterrows()]
mm = cl["r"].median()
# variazione tra 2003-05 e 2022-24 (quartieri in classifica)
cl = cl.assign(var=cl.r - cl.r_2003_2005, varp=100 * (cl.r / cl.r_2003_2005 - 1))
n_calo = int((cl["var"] < 0).sum())
rank = {
    "mediana_r": R(mm, 1), "min_r": R(cl.r.min(), 1), "max_r": R(cl.r.max(), 1), "n_classifica": int(len(cl)),
    "top_r": rows(cl, "r", 10, False), "bot_r": rows(cl, "r", 10, True),
    "top_straniera": rows(cl, "qs", 10, False), "bot_straniera": rows(cl, "qs", 10, True),
    "mediana_qs": R(cl.qs.median(), 1),
    "n_calo_dal_2003_05": n_calo, "mediana_var_pct": R(cl.varp.median(), 1),
    "max_calo": [{"n": r.nil, "a": R(r.r_2003_2005, 1), "b": R(r.r, 1)} for _, r in cl.sort_values("var").head(5).iterrows()],
    "aumenti": [{"n": r.nil, "a": R(r.r_2003_2005, 1), "b": R(r.r, 1)} for _, r in cl[cl["var"] > 0].sort_values("var", ascending=False).iterrows()],
}

# ------------------------------------------------------------------ citta'
c = citta.set_index("anno")
cols = {k: [None if pd.isna(c.loc[y, k]) else (int(c.loc[y, k]) if float(c.loc[y, k]).is_integer() else R(c.loc[y, k], 2)) for y in ANNI]
        for k in ["nati_residenti", "nati_avvenuti_a_milano", "nati_in_citta_da_genitori_residenti", "residenti_nati_altrove_stima", "nati_istat_bilancio",
                  "madre_straniera", "madre_italiana", "madre_nd", "residenti_medi", "donne_15_49_medie", "donne_15_49_straniere_medie",
                  "donne_15_49_italiane_medie", "nati_per_1000_residenti", "nati_per_1000_donne_15_49", "nati_per_1000_donne_straniere",
                  "nati_per_1000_donne_italiane", "quota_madre_straniera_pct"]}
def v(k, y): return c.loc[y, k]
check("nati 2008", int(v("nati_residenti", 2008)), 12467)
check("nati 2024", int(v("nati_residenti", 2024)), 9147)
check("nati 2006 (massimo)", int(c.nati_residenti.max()), 12518)
check("anno del massimo", int(c.nati_residenti.idxmax()), 2006)
check("tasso 2008", float(v("nati_per_1000_donne_15_49", 2008)), 43.28, 0.01)
check("tasso 2024", float(v("nati_per_1000_donne_15_49", 2024)), 30.49, 0.01)
nati_somma = int(tassi.groupby("anno").nati.sum()[2024] + nasc[(nasc.anno == 2024) & (nasc.id_nil == -1)].nati.sum())
check("somma nati dei quartieri 2024 = totale citta'", nati_somma, 9147)
calo_08 = 100 * (v("nati_residenti", 2024) / v("nati_residenti", 2008) - 1)
calo_14 = int(v("nati_residenti", 2024) - v("nati_residenti", 2014))
calo_14_str = int(v("madre_straniera", 2024) - v("madre_straniera", 2014))
calo_14_ita = int(v("madre_italiana", 2024) - v("madre_italiana", 2014))
check("calo 2014->2024 = straniere + italiane + n.d.", calo_14_str + calo_14_ita + int(v("madre_nd", 2024) - v("madre_nd", 2014)), calo_14)

# eta' della madre
em = eta.copy()
classi = sorted(em.classe.unique())
eta_c = {str(y): {int(cl_): int(em[(em.anno == y) & (em.classe == cl_)].n.sum()) for cl_ in classi} for y in (2021, 2022, 2023, 2024)}
em.rename(columns={"madre_eta": "classe_eta_madre", "n": "nati", "classe": "eta_inizio_classe"}).drop(columns=["medio"]).to_csv(
    os.path.join(OUT, "eta_madre_citta_2021_2024.csv"), index=False)
tfrc.to_csv(os.path.join(OUT, "tfr_citta_2021_2024.csv"), index=False)
check("quota madre 35+ nel 2024 (%)", float(tfrc[tfrc.anno == 2024].quota_madre_35_piu_pct.iloc[0]), 49.4, 0.05)

# ISTAT
ist.rename(columns={"tfr": "tasso_fecondita_totale", "eta_media_madre": "eta_media_madri_al_parto"}).to_csv(
    os.path.join(OUT, "tfr_eta_madre_istat.csv"), index=False)
def ser(area, cit, col, y0=2000, y1=2025):
    s = ist[(ist.area == area) & (ist.cittadinanza == cit)].set_index("anno")[col]
    return [R(s.get(y), 2) for y in range(y0, y1 + 1)]
istj = {a: {cz: {"tfr": ser(a, cz, "tfr"), "eta": ser(a, cz, "eta_media_madre")} for cz in ("tutte", "italiana", "straniera")}
        for a in ("Italia", "Lombardia", "Provincia di Milano")}
check("TFR Provincia di Milano 2024", istj["Provincia di Milano"]["tutte"]["tfr"][2024 - 2000], 1.13, 0.001)
check("TFR Italia 2024", istj["Italia"]["tutte"]["tfr"][2024 - 2000], 1.18, 0.001)

# ------------------------------------------------------------------ riepilogo
cc = c.loc[ANNI]
fatti = {
    "anno_max": int(c.nati_residenti.idxmax()), "nati_max": int(c.nati_residenti.max()), "nati_2008": int(v("nati_residenti", 2008)),
    "nati_2014": int(v("nati_residenti", 2014)), "nati_2024": int(v("nati_residenti", 2024)), "nati_2003": int(v("nati_residenti", 2003)),
    "calo_2008_2024_pct": R(calo_08, 1), "calo_2014_2024": calo_14, "calo_2014_2024_madri_straniere": calo_14_str, "calo_2014_2024_madri_italiane": calo_14_ita,
    "quota_straniere_su_calo_pct": R(100 * calo_14_str / calo_14, 0),
    "donne_2008": int(v("donne_15_49_medie", 2008)), "donne_2024": int(v("donne_15_49_medie", 2024)),
    "tasso_2008": R(v("nati_per_1000_donne_15_49", 2008), 1), "tasso_2024": R(v("nati_per_1000_donne_15_49", 2024), 1), "tasso_2003": R(v("nati_per_1000_donne_15_49", 2003), 1),
    "tasso_ab_2008": R(v("nati_per_1000_residenti", 2008), 1), "tasso_ab_2024": R(v("nati_per_1000_residenti", 2024), 1),
    "quota_str_2013": R(v("quota_madre_straniera_pct", 2013), 1), "quota_str_2024": R(v("quota_madre_straniera_pct", 2024), 1), "quota_str_2003": R(v("quota_madre_straniera_pct", 2003), 1),
    "tasso_str_2003": R(v("nati_per_1000_donne_straniere", 2003), 1), "tasso_ita_2003": R(v("nati_per_1000_donne_italiane", 2003), 1),
    "tasso_str_2024": R(v("nati_per_1000_donne_straniere", 2024), 1), "tasso_ita_2024": R(v("nati_per_1000_donne_italiane", 2024), 1),
    "mmc_residenti_2011": int(den[(den.id_nil == 72) & (den.anno == 2011)].residenti.iloc[0]), "mmc_residenti_2024": int(den[(den.id_nil == 72) & (den.anno == 2024)].residenti.iloc[0]),
    "nati_senza_quartiere_totale": int(sum(chk["nati_senza_quartiere"].values())),
    "nati_senza_quartiere_2011": chk["nati_senza_quartiere"]["2011"], "nati_senza_quartiere_2012": chk["nati_senza_quartiere"]["2012"],
    "avvenuti_vs_residenti_2024": [int(v("nati_avvenuti_a_milano", 2024)), int(v("nati_residenti", 2024))],
    "residenti_in_citta_pct_2024": R(v("nati_in_citta_da_genitori_residenti_pct", 2024), 1),
    "residenti_in_citta_pct_2019": R(v("nati_in_citta_da_genitori_residenti_pct", 2019), 1),
}
riep = {
    "anni": ANNI, "citta": cols, "fatti": fatti, "nil": rank, "eta": {"classi": [int(x) for x in classi], "conteggi": eta_c,
                                                                       "tfr_citta": tfrc.round(3).to_dict(orient="records")},
    "istat": istj, "controlli": {k: chk[k] for k in ("nati_senza_quartiere", "ds1944_senza_eta_madre", "ds1945_senza_eta_madre", "nati_istat_bilancio",
                                                       "ds1946_totale_avvenuti")},
}
json.dump(riep, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
citta.round(3).to_csv(os.path.join(OUT, "citta_anno.csv"), index=False, sep=";")
print("\nAVVISI:", AVVISI if AVVISI else "nessuno")
if AVVISI:
    sys.exit(1)
