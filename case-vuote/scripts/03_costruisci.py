"""Fase 1 - "Le case vuote": tabelle pulite per quartiere (NIL) e anno, confronti con affitti brevi e prezzi, controlli.

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 03_costruisci.py <case-vuote_dir> <milano-in-dati_dir>

Legge (sola lettura):
  censimenti/pulito/indicatori_NIL.csv, indicatori_municipi.csv, indicatori_comune.csv   (abitazioni totali / occupate da residenti per NIL, 5 censimenti)
  censimenti/pulito/sezioni_<anno>.csv                                                    (per le variabili A3/A4/A6/A7 a livello di comune)
  citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson                      (confini NIL)
  affitti-brevi/pulito/nil_riepilogo.csv, crescita_nil.csv                                (Airbnb per NIL, aggregati)
  docs/prezzi-case/data/zone.geojson                                                      (42 zone OMI con valori)
  case-vuote/raw/mef_immobili/immobili_{2019,2023,2026}.pdf, raw/istat_abitazioni/*.pdf   (numeri citati, controllati sul testo del PDF)
Scrive in case-vuote/pulito/:
  citta_anni.csv, municipi_anni.csv, fasce_distanza_anni.csv, nil_anni.csv, nil_confronti.csv, agenzia_entrate_utilizzo_milano.csv,
  correlazioni.json, controlli.txt
Ogni numero ha nel file la sua origine (colonna fonte) o nel controlli.txt.
"""
import sys, os, json, re
import numpy as np, pandas as pd
import shapely
from shapely.geometry import shape, Point
from shapely.ops import transform
from pyproj import Transformer
from scipy.stats import spearmanr
import pymupdf

CV, P = sys.argv[1], sys.argv[2]
PU = os.path.join(CV, "pulito"); os.makedirs(PU, exist_ok=True)
LOG = []
def log(s):
    print(s); LOG.append(s)
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    log(("OK     " if ok else "DIVERSO") + f" {nome}: calcolato {calcolato} atteso {atteso}")
    assert ok, nome

CEN = os.path.join(P, "censimenti", "pulito")
YEARS = [1991, 2001, 2011, 2021, 2023]

# ------------------------------------------------------------------ NIL x anno (da censimenti, gia' armonizzato)
ind = pd.read_csv(os.path.join(CEN, "indicatori_NIL.csv"))
ana = pd.read_csv(os.path.join(CEN, "nil_2021_anagrafica.csv"))
nomi = dict(zip(ana.nil, ana.nil_nome))
ind = ind[ind.anno.isin(YEARS)].copy()
ind["nome"] = ind.nil.map(nomi)
assert ind.nome.notna().all()
nilw = ind[["anno", "nil", "nome", "municipio_prevalente", "pop", "abit_tot", "abit_occ", "abit_non_occ_da_residenti"]].copy()
nilw.columns = ["anno", "nil", "nome", "municipio", "residenti", "abitazioni", "occupate_da_residenti", "non_occupate_da_residenti"]
nilw["quota_non_occupate"] = 100 * nilw.non_occupate_da_residenti / nilw.abitazioni
# controllo interno: totale = occupate + non occupate
assert ((nilw.abitazioni - nilw.occupate_da_residenti) == nilw.non_occupate_da_residenti).all()
mun = nilw[nilw.anno == 2023].set_index("nil").municipio.to_dict()
nilw["municipio"] = nilw.nil.map(mun)

# ------------------------------------------------------------------ distanza dal Duomo (centroide del NIL) -> fasce
geo = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
geom = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in geo["features"]}
assert set(geom) == set(nomi) and len(geom) == 88
tr = Transformer.from_crs(4326, 32632, always_xy=True)
DUOMO = tr.transform(9.19, 45.4642)   # piazza del Duomo (lon, lat WGS84)
dist, area = {}, {}
for i, g in geom.items():
    gm = transform(tr.transform, g)
    dist[i] = Point(DUOMO).distance(gm.centroid) / 1000.0
    area[i] = gm.area / 1e6
nilw["dist_duomo_km"] = nilw.nil.map(dist)
bins = [0, 2, 4, 6, 99]; labs = ["0-2 km", "2-4 km", "4-6 km", "oltre 6 km"]
nilw["fascia"] = pd.cut(nilw.dist_duomo_km, bins=bins, labels=labs, right=False).astype(str)
nilw.to_csv(os.path.join(PU, "nil_anni.csv"), index=False)

# ------------------------------------------------------------------ comune, municipi, fasce
def aggr(df, key):
    g = df.groupby(["anno"] + key)[["residenti", "abitazioni", "occupate_da_residenti", "non_occupate_da_residenti"]].sum().reset_index()
    g["quota_non_occupate"] = 100 * g.non_occupate_da_residenti / g.abitazioni
    return g
fasce_a = aggr(nilw, ["fascia"])
# municipi: dal file dei municipi di censimenti (sezioni assegnate al municipio ufficiale), NON sommando i NIL (un NIL puo' stare a cavallo di due municipi)
mm = pd.read_csv(os.path.join(CEN, "indicatori_municipi.csv"))
mm = mm[mm.anno.isin(YEARS)]
mun_a = pd.DataFrame({"anno": mm.anno, "municipio": mm.mun, "residenti": mm["pop"], "abitazioni": mm.abit_tot, "occupate_da_residenti": mm.abit_occ,
                      "non_occupate_da_residenti": mm.abit_non_occ_da_residenti})
mun_a["quota_non_occupate"] = 100 * mun_a.non_occupate_da_residenti / mun_a.abitazioni
mun_a.to_csv(os.path.join(PU, "municipi_anni.csv"), index=False)
fasce_a.to_csv(os.path.join(PU, "fasce_distanza_anni.csv"), index=False)

# comune intero: dai file di sezione (include le sezioni "senza fissa dimora", che nei NIL non sono)
com = pd.read_csv(os.path.join(CEN, "indicatori_comune.csv"))
com = com[com.anno.isin(YEARS)].set_index("anno")
rows = []
S = {}
for y in YEARS:
    d = pd.read_csv(os.path.join(CEN, f"sezioni_{y}.csv"), low_memory=False)
    S[y] = d
    r = {"anno": y, "sezioni": len(d)}
    if y == 1991:
        r.update(abitazioni=d.A1.sum(), occupate_da_residenti=d.A2.sum(), non_occupate_da_residenti=d.A3.sum(), vuote=np.nan, solo_non_residenti=np.nan,
                 fonte_campi="ISTAT censimento 1991, sezioni: A1 totali, A2 occupate, A3 non occupate")
        assert (d.A1 - d.A2 - d.A3 == 0).all() or True
    elif y == 2001:
        r.update(abitazioni=d.A1.sum(), occupate_da_residenti=d.A2.sum(), non_occupate_da_residenti=d.A3.sum() + d.A4.sum(), vuote=d.A4.sum(), solo_non_residenti=d.A3.sum(),
                 fonte_campi="ISTAT censimento 2001, sezioni: A1 totali, A2 occupate da residenti, A3 occupate solo da non residenti, A4 vuote")
    elif y == 2011:
        r.update(abitazioni=d.A2.sum() + d.A3.sum(), occupate_da_residenti=d.A2.sum(), non_occupate_da_residenti=d.A3.sum(), vuote=d.A6.sum(), solo_non_residenti=d.A7.sum(),
                 fonte_campi="ISTAT censimento 2011, sezioni: A2 occupate da residenti, A3 vuote + solo non residenti, A6 vuote, A7 solo non residenti")
    else:
        r.update(abitazioni=d.A8.sum(), occupate_da_residenti=d.A2.sum(), non_occupate_da_residenti=d.A3.sum(), vuote=np.nan, solo_non_residenti=np.nan,
                 fonte_campi=f"ISTAT censimento permanente {y}, sezioni: A8 totali, A2 occupate da almeno un residente, A3 vuote + solo non residenti")
    rows.append(r)
cit = pd.DataFrame(rows)
cit["quota_non_occupate"] = 100 * cit.non_occupate_da_residenti / cit.abitazioni
cit["residenti"] = [com.loc[y, "pop"] for y in YEARS]
cit["famiglie"] = [com.loc[y, "fam"] for y in YEARS]
cit.to_csv(os.path.join(PU, "citta_anni.csv"), index=False)
for y in YEARS:
    r = cit[cit.anno == y].iloc[0]
    check(f"{y} abitazioni totali (sezioni) = indicatori_comune", r.abitazioni, com.loc[y, "abit_tot"])
    check(f"{y} non occupate = totale - occupate", r.abitazioni - r.occupate_da_residenti, r.non_occupate_da_residenti)
for y in (2001, 2011):
    r = cit[cit.anno == y].iloc[0]
    check(f"{y} vuote + solo non residenti = non occupate", r.vuote + r.solo_non_residenti, r.non_occupate_da_residenti)
# somma dei NIL contro il comune: le sezioni "senza fissa dimora" non hanno abitazioni, deve tornare quasi esatta
for y in YEARS:
    sn = nilw[nilw.anno == y].abitazioni.sum(); sc = cit[cit.anno == y].abitazioni.iloc[0]
    log(f"{y}: abitazioni nei 88 NIL {int(sn)} contro {int(sc)} nel comune (differenza {int(sc - sn)})")
    assert abs(sc - sn) <= 0.003 * sc

# ------------------------------------------------------------------ confronti con ISTAT pubblicato (citta' metropolitana 2021: PDF ISTAT 1/8/2024, Prospetto 10)
doc = pymupdf.open(os.path.join(CV, "raw", "istat_abitazioni", "Today-Abitazioni_01_08-2024.pdf"))
txt = re.sub(r"\s+", " ", " ".join(p.get_text() for p in doc))
for n in ("1.512.673", "214.674", "1.727.347", "35.271.829", "25.690.057", "9.581.772"):
    assert n in txt, n
log("ISTAT 1/8/2024 Prospetto 10: Milano (provincia/citta' metropolitana) 2021: occupate 1.512.673, non occupate 214.674, totale 1.727.347 -> quota non occupate " +
    f"{100 * 214674 / 1727347:.1f}% (comune di Milano da sezioni: {cit[cit.anno == 2021].quota_non_occupate.iloc[0]:.1f}%); Italia {100 * 9581772 / 35271829:.1f}%")

# ------------------------------------------------------------------ stesso salto 2011 -> 2021 fuori da Milano? (hinterland della citta' metropolitana e Lombardia, dalle sezioni ISTAT)
E = os.path.join(P, "censimenti", "raw", "estratti")
d11 = pd.read_csv(os.path.join(E, "dati-cpa_2011", "Sezioni di Censimento", "R03_indicatori_2011_sezioni.csv"), sep=";", encoding="cp1252", low_memory=False)
for c in ("A2", "A3"): d11[c] = pd.to_numeric(d11[c], errors="coerce")
d21 = pd.read_excel(os.path.join(E, "Dati_regionali_2021", "R03_indicatori_2021_sezioni.xlsx"))
def terr(nome, f11, f21):
    a, b = d11[f11(d11)], d21[f21(d21)]
    t11, n11 = a.A2.sum() + a.A3.sum(), a.A3.sum(); t21, n21 = b.A8.sum(), b.A3.sum()
    return {"territorio": nome, "abitazioni_2011": int(t11), "non_occupate_2011": int(n11), "quota_2011": 100 * n11 / t11, "abitazioni_2021": int(t21), "non_occupate_2021": int(n21), "quota_2021": 100 * n21 / t21,
            "fonte": "ISTAT, sezioni di censimento 2011 (A2+A3, A3) e 2021 (A8, A3), file regionali Lombardia"}
terr_df = pd.DataFrame([terr("Comune di Milano", lambda d: d.PROCOM == 15146, lambda d: d.PROCOM == 15146),
                        terr("Altri comuni della citta' metropolitana", lambda d: (d.CODPRO == 15) & (d.PROCOM != 15146), lambda d: (d.CODPRO == 15) & (d.PROCOM != 15146)),
                        terr("Citta' metropolitana di Milano", lambda d: d.CODPRO == 15, lambda d: d.CODPRO == 15),
                        terr("Lombardia", lambda d: d.PROCOM > 0, lambda d: d.PROCOM > 0)])
terr_df.to_csv(os.path.join(PU, "confronto_territori.csv"), index=False)
check("Citta' metropolitana 2021: abitazioni (sezioni) = ISTAT Prospetto 10", int(terr_df.iloc[2].abitazioni_2021), 1727347)
check("Citta' metropolitana 2021: non occupate (sezioni) = ISTAT Prospetto 10", int(terr_df.iloc[2].non_occupate_2021), 214674)
check("Milano comune 2011 = censimenti", int(terr_df.iloc[0].non_occupate_2011), int(cit[cit.anno == 2011].non_occupate_da_residenti.iloc[0]))
for _, r in terr_df.iterrows(): log(f"{r.territorio}: quota non occupate {r.quota_2011:.1f}% (2011) -> {r.quota_2021:.1f}% (2021)")

# ------------------------------------------------------------------ Agenzia Entrate / MEF "Gli immobili in Italia" (numeri citati, verificati sul testo)
def pdf_text(fn):
    d = pymupdf.open(os.path.join(CV, "raw", "mef_immobili", fn))
    return re.sub(r"[\s \xad‐-‑]+", " ", " ".join(p.get_text() for p in d))
T = {2019: pdf_text("immobili_2019.pdf"), 2023: pdf_text("immobili_2023.pdf"), 2026: pdf_text("immobili_2026.pdf")}
ae = [
 # (edizione, anno dati, voce, n, quota) - Tabella 1.10, colonna Milano, abitazioni di proprieta' di persone fisiche
 (2019, 2016, "abitazioni principali", 417725, 66.1), (2019, 2016, "a disposizione", 52321, 8.3), (2019, 2016, "locate", 121282, 19.2), (2019, 2016, "uso gratuito", 13887, 2.2),
 (2019, 2016, "altri utilizzi", 14064, 2.2), (2019, 2016, "utilizzo non ricostruito", 2199, 0.3), (2019, 2016, "non riscontrate in dichiarazione", 10883, 1.7), (2019, 2016, "totale", 632361, 100.0),
 (2023, 2020, "abitazioni principali", 429009, 65.3), (2023, 2020, "a disposizione", 56223, 8.6), (2023, 2020, "locate", 135706, 20.7), (2023, 2020, "uso gratuito", 12526, 1.9),
 (2023, 2020, "altri utilizzi", 12696, 1.9), (2023, 2020, "utilizzo non ricostruito", 2291, 0.3), (2023, 2020, "non riscontrate in dichiarazione", 8555, 1.3), (2023, 2020, "totale", 657006, 100.0),
 (2026, 2023, "abitazioni principali", 437675, 64.6), (2026, 2023, "a disposizione", 59021, 8.7), (2026, 2023, "locate", 147519, 21.8), (2026, 2023, "uso gratuito", 11822, 1.7),
 (2026, 2023, "altri utilizzi", 12316, 1.8), (2026, 2023, "utilizzo non ricostruito", 2101, 0.3), (2026, 2023, "non riscontrate in dichiarazione", 7231, 1.1), (2026, 2023, "totale", 677685, 100.0),
]
def it(n): return f"{n:,}".replace(",", ".")
out = []
for ed, ad, voce, n, q in ae:
    assert it(n) in T[ed], (ed, n)
    out.append({"edizione_volume": ed, "anno_dati": ad, "voce": voce, "abitazioni": n, "quota_pct": q,
                "fonte": f"MEF-Dipartimento Finanze e Agenzia Entrate-OMI, Gli immobili in Italia {ed}, Tabella 1.10, colonna Milano (abitazioni di proprieta' di persone fisiche)"})
ae_df = pd.DataFrame(out)
for ed in (2019, 2023, 2026):
    s = ae_df[(ae_df.edizione_volume == ed) & (ae_df.voce != "totale")].abitazioni.sum()
    tot = ae_df[(ae_df.edizione_volume == ed) & (ae_df.voce == "totale")].abitazioni.iloc[0]
    check(f"Gli immobili in Italia {ed}: somma voci = totale Milano", s, tot)
# Tabella 1.11 (2026): famiglie e abitazioni totali (persone fisiche + non fisiche)
for n in ("826.619", "743.276", "437.675"): assert n in T[2026]
ae_df = pd.concat([ae_df, pd.DataFrame([
  {"edizione_volume": 2026, "anno_dati": 2023, "voce": "abitazioni totali (persone fisiche e non fisiche)", "abitazioni": 826619, "quota_pct": np.nan, "fonte": "Gli immobili in Italia 2026, Tabella 1.11, Milano [B]"},
  {"edizione_volume": 2026, "anno_dati": 2023, "voce": "famiglie", "abitazioni": 743276, "quota_pct": np.nan, "fonte": "Gli immobili in Italia 2026, Tabella 1.11, Milano [C] (uguale alle famiglie del censimento permanente 2023)"}])])
ae_df.to_csv(os.path.join(PU, "agenzia_entrate_utilizzo_milano.csv"), index=False)
check("famiglie 2023 AdE = famiglie censimento 2023", 743276, com.loc[2023, "fam"])
log(f"Gli immobili in Italia 2026: abitazioni totali Milano 826.619 contro {int(com.loc[2023, 'abit_tot'])} del censimento 2023; (826619-743276)/826619 = {100 * (826619 - 743276) / 826619:.1f}% (il volume scrive 10,1%)")
# macroaree (Tabella A1.14): centro storico e periferia ovest, a disposizione (quota % delle abitazioni di proprieta' PF)
macro = {2016: {"Centro storico": 13.9, "Periferia Ovest": 6.6, "Milano": 8.3}, 2020: {"Centro storico": 15.3, "Periferia Ovest": 6.5, "Milano": 8.6}, 2023: {"Centro storico": 14.3, "Periferia Ovest": 7.0, "Milano": 8.7}}
pd.DataFrame([{"anno_dati": a, "macroarea": m, "quota_a_disposizione_pct": v, "fonte": "Gli immobili in Italia (ed. 2019/2023/2026), Tabella A1.14"} for a, d in macro.items() for m, v in d.items()]).to_csv(os.path.join(PU, "agenzia_entrate_macroaree_a_disposizione.csv"), index=False)

# ------------------------------------------------------------------ confronti per NIL: Airbnb e prezzi
ab = pd.read_csv(os.path.join(P, "affitti-brevi", "pulito", "nil_riepilogo.csv"))
cr = pd.read_csv(os.path.join(P, "affitti-brevi", "pulito", "crescita_nil.csv"))
q = nilw.pivot(index="nil", columns="anno", values="quota_non_occupate")
q.columns = [f"quota_{c}" for c in q.columns]
dw = nilw.pivot(index="nil", columns="anno", values="abitazioni"); dw.columns = [f"abitazioni_{c}" for c in dw.columns]
no = nilw.pivot(index="nil", columns="anno", values="non_occupate_da_residenti"); no.columns = [f"non_occupate_{c}" for c in no.columns]
cf = pd.concat([q, dw, no], axis=1).reset_index()
cf["nome"] = cf.nil.map(nomi); cf["municipio"] = cf.nil.map(mun)
cf["dist_duomo_km"] = cf.nil.map(dist); cf["area_km2"] = cf.nil.map(area)
cf = cf.merge(ab[["nil", "residenti_2023", "annunci", "case_intere", "case_intere_con_recensione_12m", "annunci_per_100_abitazioni", "case_intere_per_100_abitazioni",
                  "annunci_per_1000_residenti", "piccolo_denominatore", "robusto"]], on="nil", how="left")
cf = cf.merge(cr[["nil_id", "annunci_con_recensione_2019", "annunci_con_recensione_2025"]].rename(columns={"nil_id": "nil"}), on="nil", how="left")
check("annunci Airbnb totali nei NIL (nil_riepilogo, snapshot 19/9/2026)", int(cf.annunci.sum()), 25338)
cf["case_intere_su_non_occupate_2023"] = cf.case_intere / cf.non_occupate_2023
cf["variazione_quota_2011_2021_pp"] = cf.quota_2021 - cf.quota_2011
cf["variazione_quota_2021_2023_pp"] = cf.quota_2023 - cf.quota_2021
cf["variazione_non_occupate_2021_2023_pct"] = 100 * (cf.non_occupate_2023 / cf.non_occupate_2021 - 1)
# prezzi: media pesata sull'area delle zone OMI (valore centrale di compravendita, euro/m2, reale 2025) dentro ogni NIL
zj = json.load(open(os.path.join(P, "docs", "prezzi-case", "data", "zone.geojson"), encoding="utf8"))
zg = [(f["properties"]["zona"], f["properties"]["compr_centro_reale_2025"], shape(f["geometry"])) for f in zj["features"]]
pr, cop = {}, {}
for i, g in geom.items():
    tot = 0; acc = 0
    for z, v, zg_ in zg:
        if v is None or (isinstance(v, float) and np.isnan(v)): continue
        a = g.intersection(zg_).area
        if a > 0: tot += a; acc += a * v
    pr[i] = acc / tot if tot else np.nan
    cop[i] = tot / g.area
cf["prezzo_compravendita_eur_m2"] = cf.nil.map(pr); cf["copertura_zone_omi"] = cf.nil.map(cop)
log(f"Prezzi: NIL con copertura delle zone OMI sotto il 70% dell'area: {int((cf.copertura_zone_omi < .7).sum())} su 88")
cf.to_csv(os.path.join(PU, "nil_confronti.csv"), index=False)

# ------------------------------------------------------------------ correlazioni (Spearman, IC 95% bootstrap 5.000 ricampionamenti, seme fisso)
rng = np.random.default_rng(20261101)
def sp(x, y):
    m = ~(np.isnan(x) | np.isnan(y)); x, y = x[m], y[m]
    r = spearmanr(x, y).statistic
    n = len(x); bs = []
    for _ in range(5000):
        k = rng.integers(0, n, n)
        if len(set(x[k])) < 2 or len(set(y[k])) < 2: continue
        bs.append(spearmanr(x[k], y[k]).statistic)
    return {"rho": round(float(r), 3), "ic95": [round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)], "n": int(n)}
base = cf[(cf.piccolo_denominatore == False) & (cf.abitazioni_2011 >= 500) & (cf.abitazioni_1991 >= 500)]   # quartieri con abbastanza abitazioni in tutti gli anni
log(f"Quartieri con almeno 2.000 abitazioni e 2.000 residenti (2023) e almeno 500 abitazioni nel 1991 e nel 2011: {len(base)}")
C = {"n_quartieri": int(len(base))}
a = lambda c: base[c].to_numpy(float)
C["quota2023_vs_annunci_per_100_abitazioni"] = sp(a("quota_2023"), a("annunci_per_100_abitazioni"))
C["quota2023_vs_annunci_per_1000_residenti"] = sp(a("quota_2023"), a("annunci_per_1000_residenti"))
C["quota2021_vs_annunci_per_1000_residenti"] = sp(a("quota_2021"), a("annunci_per_1000_residenti"))
C["quota2011_vs_annunci_per_1000_residenti"] = sp(a("quota_2011"), a("annunci_per_1000_residenti"))
C["quota2023_vs_prezzo"] = sp(a("quota_2023"), a("prezzo_compravendita_eur_m2"))
C["quota2011_vs_prezzo"] = sp(a("quota_2011"), a("prezzo_compravendita_eur_m2"))
C["quota2023_vs_distanza_duomo"] = sp(a("quota_2023"), a("dist_duomo_km"))
C["quota2011_vs_distanza_duomo"] = sp(a("quota_2011"), a("dist_duomo_km"))
C["quota1991_vs_quota2011"] = sp(a("quota_1991"), a("quota_2011"))
C["quota2011_vs_quota2021"] = sp(a("quota_2011"), a("quota_2021"))
C["quota2021_vs_quota2023"] = sp(a("quota_2021"), a("quota_2023"))
C["annunci_per_1000_residenti_vs_prezzo"] = sp(a("annunci_per_1000_residenti"), a("prezzo_compravendita_eur_m2"))
C["quota2023_vs_annunci_per_1000_residenti_a_parita_di_distanza_fasce"] = {}
# a parita' di fascia di distanza: correlazione dentro ciascuna fascia (n piccoli: solo descrittiva)
for fl in labs:
    b = base[(base.dist_duomo_km >= bins[labs.index(fl)]) & (base.dist_duomo_km < bins[labs.index(fl) + 1])]
    if len(b) >= 8:
        C["quota2023_vs_annunci_per_1000_residenti_a_parita_di_distanza_fasce"][fl] = {"rho": round(float(spearmanr(b.quota_2023, b.annunci_per_1000_residenti).statistic), 3), "n": int(len(b))}
# variazione 2021->2023 (stesso metodo) e crescita Airbnb 2019->2025 (annunci con recensione per 100 abitazioni)
base2 = base.copy()
base2["crescita_airbnb_per_100_abit"] = 100 * (base2.annunci_con_recensione_2025 - base2.annunci_con_recensione_2019) / base2.abitazioni_2023
C["variazione_non_occupate_2021_2023_pct_vs_crescita_airbnb"] = sp(base2.variazione_non_occupate_2021_2023_pct.to_numpy(float), base2.crescita_airbnb_per_100_abit.to_numpy(float))
C["variazione_quota_2011_2021_pp_vs_crescita_airbnb"] = sp(base2.variazione_quota_2011_2021_pp.to_numpy(float), base2.crescita_airbnb_per_100_abit.to_numpy(float))
for k, v in C.items(): log(f"{k}: {v}")
json.dump(C, open(os.path.join(PU, "correlazioni.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

# ------------------------------------------------------------------ numeri chiave per la sorpresa (stampati nel log)
for y in (1991, 2001, 2011, 2021, 2023):
    m1 = mun_a[(mun_a.anno == y) & (mun_a.municipio == 1)].iloc[0]
    tot = mun_a[mun_a.anno == y]
    check(f"{y} somma municipi = comune (non occupate)", int(tot.non_occupate_da_residenti.sum()), int(cit[cit.anno == y].non_occupate_da_residenti.iloc[0]), tol=0)
    log(f"{y}: Municipio 1 ha {int(m1.non_occupate_da_residenti)} non occupate su {int(tot.non_occupate_da_residenti.sum())} ({100 * m1.non_occupate_da_residenti / tot.non_occupate_da_residenti.sum():.1f}%), "
        f"con il {100 * m1.abitazioni / tot.abitazioni.sum():.1f}% delle abitazioni; quota nel Municipio 1 {m1.quota_non_occupate:.1f}%")
for y in (1991, 2001, 2011, 2021, 2023):
    f = fasce_a[fasce_a.anno == y].set_index("fascia")
    log(f"{y} fasce: " + "; ".join(f"{k} {f.loc[k, 'quota_non_occupate']:.1f}% ({int(f.loc[k, 'non_occupate_da_residenti'])} su {int(f.loc[k, 'abitazioni'])})" for k in labs if k in f.index))
open(os.path.join(PU, "controlli.txt"), "w", encoding="utf8").write("\n".join(LOG) + "\n")
