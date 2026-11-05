"""Scrive i file dati della pagina "Le case vuote" (docs/case-vuote/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <case-vuote_dir> <progetto_milano_in_dati_dir> <docs_dir>

Prima va lanciato 03_costruisci.py (scrive case-vuote/pulito/). Legge:
  case-vuote/pulito/{citta_anni,municipi_anni,fasce_distanza_anni,nil_anni,nil_confronti,confronto_territori,agenzia_entrate_utilizzo_milano}.csv, correlazioni.json
  citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson   (confini NIL, semplificati per la mappa)
Scrive in <docs_dir>/case-vuote/data/:
  riepilogo.json (tutti i numeri della pagina, con l'origine), nil.geojson, nil.csv, citta_anni.csv, municipi_anni.csv, fasce_distanza_anni.csv, confronto_territori.csv
Solo valori aggregati: nessun annuncio Airbnb singolo, nessun file del volume MEF/Agenzia Entrate ripubblicato (solo una manciata di numeri citati con la fonte).
"""
import sys, os, json
import numpy as np, pandas as pd
from shapely.geometry import shape, mapping

CV, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(CV, "pulito")
OUT = os.path.join(DOCS, "case-vuote", "data"); os.makedirs(OUT, exist_ok=True)
YEARS = [1991, 2001, 2011, 2021, 2023]
AVVISI = []
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    print(("OK      " if ok else "DIVERSO ") + f"{nome}: {calcolato} / {atteso}")
    if not ok: AVVISI.append(nome)
def R(x, d=1):
    return None if x is None or (isinstance(x, (float, np.floating)) and not np.isfinite(x)) else round(float(x), d)

cit = pd.read_csv(os.path.join(PU, "citta_anni.csv")).set_index("anno")
mun = pd.read_csv(os.path.join(PU, "municipi_anni.csv"))
fas = pd.read_csv(os.path.join(PU, "fasce_distanza_anni.csv"))
nil = pd.read_csv(os.path.join(PU, "nil_confronti.csv"))
nilanni = pd.read_csv(os.path.join(PU, "nil_anni.csv"))
ter = pd.read_csv(os.path.join(PU, "confronto_territori.csv"))
ae = pd.read_csv(os.path.join(PU, "agenzia_entrate_utilizzo_milano.csv"))
cor = json.load(open(os.path.join(PU, "correlazioni.json"), encoding="utf8"))

# ------------------------------------------------------------ geojson dei quartieri
geo = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
geom = {int(f["properties"]["ID_NIL"]): shape(f["geometry"]) for f in geo["features"]}
fasce_lab = ["0-2 km", "2-4 km", "4-6 km", "oltre 6 km"]
fascia_of = nilanni.drop_duplicates("nil").set_index("nil").fascia.to_dict()
feats, rows = [], []
for _, r in nil.sort_values("nome").iterrows():
    i = int(r.nil)
    a = [int(r[f"abitazioni_{y}"]) for y in YEARS]
    o = [int(r[f"non_occupate_{y}"]) for y in YEARS]
    q = [R(r[f"quota_{y}"], 1) for y in YEARS]
    pr = {"i": i, "n": r.nome, "mu": int(r.municipio), "d": R(r.dist_duomo_km, 1), "f": fasce_lab.index(fascia_of[i]), "a": a, "o": o, "q": q,
          "res": int(r.residenti_2023), "an": int(r.annunci), "ci": int(r.case_intere), "ci12": int(r.case_intere_con_recensione_12m), "anr": R(r.annunci_per_1000_residenti, 1),
          "p": None if np.isnan(r.prezzo_compravendita_eur_m2) or r.copertura_zone_omi < .7 else int(round(r.prezzo_compravendita_eur_m2, -1)),
          "cl": 1 if (not r.piccolo_denominatore) and r.abitazioni_2011 >= 500 and r.abitazioni_1991 >= 500 else 0}
    g = geom[i].simplify(0.00003, preserve_topology=True)
    feats.append({"type": "Feature", "properties": pr, "geometry": mapping(g)})
    rows.append({"id_nil": i, "quartiere": r.nome, "municipio_prevalente": int(r.municipio), "distanza_duomo_km": R(r.dist_duomo_km, 2), "fascia_distanza": fascia_of[i],
                 **{f"abitazioni_{y}": int(r[f"abitazioni_{y}"]) for y in YEARS}, **{f"non_occupate_da_residenti_{y}": int(r[f"non_occupate_{y}"]) for y in YEARS},
                 **{f"quota_non_occupate_pct_{y}": R(r[f"quota_{y}"], 2) for y in YEARS},
                 "residenti_2023": int(r.residenti_2023), "annunci_airbnb_2026_09": int(r.annunci), "case_intere_airbnb_2026_09": int(r.case_intere),
                 "annunci_airbnb_ogni_1000_residenti": R(r.annunci_per_1000_residenti, 2),
                 "prezzo_compravendita_eur_m2_2025_zone_omi": pr["p"], "abbastanza_abitazioni_per_confronti": pr["cl"]})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"), allow_nan=False)
pd.DataFrame(rows).to_csv(os.path.join(OUT, "nil.csv"), index=False, sep=";")
cit.reset_index().drop(columns=["fonte_campi"]).assign(fonte_campi=cit.fonte_campi.values).to_csv(os.path.join(OUT, "citta_anni.csv"), index=False, sep=";")
mun.to_csv(os.path.join(OUT, "municipi_anni.csv"), index=False, sep=";")
fas.rename(columns={"fascia": "fascia_distanza_dal_Duomo_centroide_quartiere"}).to_csv(os.path.join(OUT, "fasce_distanza_anni.csv"), index=False, sep=";")
ter.to_csv(os.path.join(OUT, "confronto_territori.csv"), index=False, sep=";")

# ------------------------------------------------------------ riepilogo.json
def cy(y, c): return cit.loc[y, c]
anni = {str(y): {"abitazioni": int(cy(y, "abitazioni")), "occupate": int(cy(y, "occupate_da_residenti")), "non_occupate": int(cy(y, "non_occupate_da_residenti")),
                 "quota": R(cy(y, "quota_non_occupate"), 2), "residenti": int(cy(y, "residenti")), "famiglie": int(cy(y, "famiglie"))} for y in YEARS}
split = {"2001": {"vuote": int(cy(2001, "vuote")), "solo_non_residenti": int(cy(2001, "solo_non_residenti")), "totale": int(cy(2001, "non_occupate_da_residenti"))},
         "2011": {"vuote": int(cy(2011, "vuote")), "solo_non_residenti": int(cy(2011, "solo_non_residenti")), "totale": int(cy(2011, "non_occupate_da_residenti"))}}
mu = {str(m): {str(y): {"quota": R(r.quota_non_occupate, 1), "non_occ": int(r.non_occupate_da_residenti), "abit": int(r.abitazioni)} for y, r in g.set_index("anno").iterrows()} for m, g in mun.groupby("municipio")}
fa = {f: {str(y): {"quota": R(r.quota_non_occupate, 1), "non_occ": int(r.non_occupate_da_residenti), "abit": int(r.abitazioni)} for y, r in g.set_index("anno").iterrows()} for f, g in fas.groupby("fascia")}
t = {r.territorio: {"q2011": R(r.quota_2011, 1), "q2021": R(r.quota_2021, 1), "abit2011": int(r.abitazioni_2011), "abit2021": int(r.abitazioni_2021), "no2011": int(r.non_occupate_2011), "no2021": int(r.non_occupate_2021)} for _, r in ter.iterrows()}
aeD = {}
for ed, g in ae.groupby("edizione_volume"):
    g = g.set_index("voce")
    aeD[str(ed)] = {"anno_dati": int(g.anno_dati.iloc[0]), "a_disposizione": int(g.loc["a disposizione", "abitazioni"]), "a_disposizione_pct": float(g.loc["a disposizione", "quota_pct"]),
                    "locate_pct": float(g.loc["locate", "quota_pct"]), "principali_pct": float(g.loc["abitazioni principali", "quota_pct"]), "totale_pf": int(g.loc["totale", "abitazioni"])}
ab_tot = nil.annunci.sum(); ci_tot = nil.case_intere.sum(); ci12 = nil.case_intere_con_recensione_12m.sum()
no23 = int(cy(2023, "non_occupate_da_residenti")); no21 = int(cy(2021, "non_occupate_da_residenti")); no11 = int(cy(2011, "non_occupate_da_residenti"))
m1_21 = mu["1"]["2021"]; m1_23 = mu["1"]["2023"]
f_cent = fa["0-2 km"]; f_2_4 = fa["2-4 km"]
cl = nil[(nil.piccolo_denominatore == False) & (nil.abitazioni_2011 >= 500) & (nil.abitazioni_1991 >= 500)]
top = cl.sort_values("quota_2023", ascending=False).iloc[0]; bot = cl.sort_values("quota_2023").iloc[0]
n05 = lambda f, y: sum(v[str(y)]["non_occ"] for k, v in fa.items() if k in f)
RIEP = {
 "anni": anni, "split": split, "municipi": mu, "fasce": fa, "territori": t, "agenzia_entrate": aeD, "correlazioni": cor,
 "polimi": {"cifra": 109000, "data": "2026-04-29", "link_comunicato": "https://www.polimi.it/fileadmin/user_upload/comunicati_stampa/ComSt_260429_dashboard_Milano_def.pdf",
            "link_pagina": "https://www.polimi.it/ricerca/news-e-comunicati/dettaglio/mappare-dinamiche-spaziali-abitative-milano"},
 "istat_citta_metropolitana_2021": {"occupate": 1512673, "non_occupate": 214674, "totale": 1727347, "quota": R(100 * 214674 / 1727347, 1)},
 "istat_italia_2021": {"totale": 35271829, "occupate": 25690057, "non_occupate": 9581772, "quota": R(100 * 9581772 / 35271829, 1)},
 "istat_italia_2023": {"totale": 35610473, "occupate": 26051682, "non_occupate": 9558791, "quota": R(100 * 9558791 / 35610473, 1)},
 "variazioni": {
   "non_occ_2011_2021_x": R(no21 / no11, 2), "quota_pp_milano_2011_2021": R(t["Comune di Milano"]["q2021"] - t["Comune di Milano"]["q2011"], 1),
   "quota_pp_altri_comuni_2011_2021": R(t["Altri comuni della citta' metropolitana"]["q2021"] - t["Altri comuni della citta' metropolitana"]["q2011"], 1),
   "quota_pp_lombardia_2011_2021": R(t["Lombardia"]["q2021"] - t["Lombardia"]["q2011"], 1),
   "non_occ_2021_2023_pct": R(100 * (no23 / no21 - 1), 1), "abitazioni_2011_2021_pct": R(100 * (cy(2021, "abitazioni") / cy(2011, "abitazioni") - 1), 1),
   "famiglie_2011_2021_pct": R(100 * (cy(2021, "famiglie") / cy(2011, "famiglie") - 1), 1),
   "m1_quota_x_2011_2021": R(mu["1"]["2021"]["quota"] / mu["1"]["2011"]["quota"], 1),
   "m1_abit_2011_2021_pct": R(100 * (mu["1"]["2021"]["abit"] / mu["1"]["2011"]["abit"] - 1), 0),
   "m1_quota_resto_2011": R(100 * (no11 - mu["1"]["2011"]["non_occ"]) / (cy(2011, "abitazioni") - mu["1"]["2011"]["abit"]), 1),
   "m1_quota_resto_2021": R(100 * (no21 - m1_21["non_occ"]) / (cy(2021, "abitazioni") - m1_21["abit"]), 1),
   "m1_quota_di_non_occ_2021_pct": R(100 * m1_21["non_occ"] / no21, 1), "m1_quota_di_abit_2021_pct": R(100 * m1_21["abit"] / cy(2021, "abitazioni"), 1),
   "m1_quota_di_non_occ_2023_pct": R(100 * m1_23["non_occ"] / no23, 1), "m1_quota_di_abit_2023_pct": R(100 * m1_23["abit"] / cy(2023, "abitazioni"), 1),
   "entro4km_quota_di_non_occ_2021_pct": R(100 * (f_cent["2021"]["non_occ"] + f_2_4["2021"]["non_occ"]) / no21, 1),
   "entro4km_quota_di_abit_2021_pct": R(100 * (f_cent["2021"]["abit"] + f_2_4["2021"]["abit"]) / cy(2021, "abitazioni"), 1),
   "entro4km_quota_di_non_occ_2023_pct": R(100 * (f_cent["2023"]["non_occ"] + f_2_4["2023"]["non_occ"]) / no23, 1),
   "entro4km_quota_di_abit_2023_pct": R(100 * (f_cent["2023"]["abit"] + f_2_4["2023"]["abit"]) / cy(2023, "abitazioni"), 1),
   "entro2km_quota_di_non_occ_2023_pct": R(100 * f_cent["2023"]["non_occ"] / no23, 1), "entro2km_quota_di_abit_2023_pct": R(100 * f_cent["2023"]["abit"] / cy(2023, "abitazioni"), 1),
 },
 "airbnb": {"annunci": int(ab_tot), "case_intere": int(ci_tot), "case_intere_con_recensione_12m": int(ci12), "case_intere_su_non_occupate_2023_pct": R(100 * ci_tot / no23, 0),
            "case_intere_12m_su_non_occupate_2023_pct": R(100 * ci12 / no23, 0)},
 "estremi_2023": {"max": {"nome": top.nome, "quota": R(top.quota_2023, 1), "non_occ": int(top.non_occupate_2023), "abit": int(top.abitazioni_2023)},
                  "min": {"nome": bot.nome, "quota": R(bot.quota_2023, 1), "non_occ": int(bot.non_occupate_2023), "abit": int(bot.abitazioni_2023)}},
 "n_quartieri_confronti": int(len(cl)),
 "origine": {
   "anni": "ISTAT, sezioni di censimento 1991, 2001, 2011, 2021, 2023 (censimenti/pulito/sezioni_<anno>.csv): totale e occupate da residenti, vedi citta_anni.csv colonna fonte_campi",
   "quartieri": "sezioni -> 88 NIL 2021 con il raccordo della pagina censimenti (censimenti/pulito/indicatori_NIL.csv)",
   "territori": "ISTAT, file regionali Lombardia 2011 (CPA) e 2021: somma delle sezioni, case-vuote/pulito/confronto_territori.csv",
   "airbnb": "Inside Airbnb, Milano, snapshot 19/9/2026, aggregato per NIL dalla pagina affitti-brevi (affitti-brevi/pulito/nil_riepilogo.csv)",
   "prezzi": "Agenzia delle Entrate - OMI, valore centrale di compravendita (abitazioni civili) dell'ultimo semestre in euro 2025, media delle zone pesata per area dentro il NIL (docs/prezzi-case/data/zone.geojson)",
   "agenzia_entrate": "MEF-Dipartimento delle Finanze e Agenzia delle Entrate-OMI, Gli immobili in Italia, edizioni 2019, 2023, 2026, Tabella 1.10 (Milano)",
   "correlazioni": "Spearman sui quartieri con almeno 2.000 abitazioni e 2.000 residenti nel 2023 e almeno 500 abitazioni nel 1991 e nel 2011; intervalli di confidenza al 95% con 5.000 ricampionamenti (seme fisso)"}
}
# controlli incrociati con la fase di raccolta
check("non occupate 2021", no21, 109404); check("non occupate 2011", no11, 38546); check("non occupate 2023", no23, 105375)
check("somma NIL non occupate 2021", int(nil.non_occupate_2021.sum()), no21)
check("annunci", int(ab_tot), 25338); check("case intere", int(ci_tot), 22309)
check("59.021 a disposizione 2023", aeD["2026"]["a_disposizione"], 59021)
check("istat italia 2021 quota", RIEP["istat_italia_2021"]["quota"], 27.2, 0.05)
json.dump(RIEP, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1, allow_nan=False)
print("file scritti in", OUT, os.listdir(OUT))
if AVVISI:
    print("ATTENZIONE, controlli falliti:", AVVISI); sys.exit(1)
