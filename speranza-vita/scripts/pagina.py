"""Scrive i file dati della pagina "Quanto si vive" (docs/speranza-vita/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <speranza-vita_dir> <progetto_milano_in_dati_dir> <docs_dir>

Legge (fase 1): speranza-vita/pulito/*.csv, *.json (prodotti da build.py, analisi.py, sensibilita.py, municipi.py),
e dai poligoni dei NIL gia' semplificati di docs/alberi/data/nil.geojson (solo la geometria, letta senza modificarla).
Scrive in <docs_dir>/speranza-vita/data/: riepilogo.json, nil.geojson, nil.csv, nil_finestre.csv, gruppi_reddito.csv, citta_anno.csv,
municipi.csv, decessi_nil_anno_sesso.csv, correlazione_reddito.csv.
Dati aggregati per quartiere (NIL) e per anno: nessun dato individuale.
"""
import sys, os, json, math
import numpy as np, pandas as pd

SV, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(SV, "pulito")
OUT = os.path.join(DOCS, "speranza-vita", "data")
os.makedirs(OUT, exist_ok=True)
AVVISI = []
def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok: AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")
def r(x, d=3):
    return None if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))) else round(float(x), d)

R = pd.read_csv(os.path.join(PU, "nil_smr_e0.csv"))
G = pd.read_csv(os.path.join(PU, "gruppi_reddito.csv"))
Y = pd.read_csv(os.path.join(PU, "citta_e0_annuale.csv"))
CF = pd.read_csv(os.path.join(PU, "citta_e0_finestre.csv"))
MU = pd.read_csv(os.path.join(PU, "municipi_smr_e0.csv"))
COR = pd.read_csv(os.path.join(PU, "correlazione_reddito_smr.csv"))
BES = pd.read_csv(os.path.join(PU, "bes_e0_milano_lombardia_italia.csv"))
SENS = json.load(open(os.path.join(PU, "sensibilita.json"), encoding="utf8"))
CB = json.load(open(os.path.join(PU, "controlli_build.json"), encoding="utf8"))
FL = pd.read_csv(os.path.join(PU, "nil_bandiere_residenze.csv"))
QU = pd.read_csv(os.path.join(PU, "quintili_reddito_nil.csv"))
DN = pd.read_csv(os.path.join(PU, "decessi_nil_anno_genere.csv"))
ana = pd.read_csv(os.path.join(P, "popolazione", "pulito", "nil_anagrafica.csv"))

WIN_FULL = ["2012-2019", "2022-2024"]
WIN_T = ["2012-2015", "2016-2019", "2020", "2021"]
# ---------------------------------------------------------------- controlli sui dati
check("decessi NIL 2012-2019 (somma anni, Comune)", int(DN[DN.anno.between(2012, 2019)].decessi.sum()), 110284)
check("decessi osservati nella finestra 2012-2019 = decessi Comune", int(R[(R.finestra == "2012-2019") & (R.sesso == "T")].osservati.sum()), 110284)
check("attesi = osservati (finestra 2022-2024)", round(R[(R.finestra == "2022-2024") & (R.sesso == "T")].attesi.sum()), 43270, 1)
check("NIL con dati", R.id_nil.nunique(), 88)
_m = R[(R.finestra == "2012-2019") & (R.sesso == "T")].set_index("nil")
check("Muggiano: SMR sotto 0,9 e intervallo sotto 1 (testo della pagina)", int(_m.loc["Muggiano"].smr < 0.9 and _m.loc["Muggiano"].smr_hi < 1), 1)
check("Lambrate-Ortica: SMR sopra 1,15 e intervallo sopra 1 (testo della pagina)", int(_m.loc["Lambrate - Ortica"].smr > 1.15 and _m.loc["Lambrate - Ortica"].smr_lo > 1), 1)
check("Morivione: SMR donne 1,68 / uomini 1,30 (testo della pagina)", int(round(R[(R.finestra == "2012-2019") & (R.nil == "Morivione") & (R.sesso == "F")].smr.iloc[0], 2) == 1.68 and round(R[(R.finestra == "2012-2019") & (R.nil == "Morivione") & (R.sesso == "M")].smr.iloc[0], 2) == 1.30), 1)
check("decessi 2021-2024 ds1938 = NIL (2022)", CB["ds1938_totale_per_anno"]["2022"], CB["decessi_NIL_per_anno"]["2022"])

# ---------------------------------------------------------------- NIL: tabella e geojson
geo = json.load(open(os.path.join(DOCS, "alberi", "data", "nil.geojson"), encoding="utf8"))
geom = {f["properties"]["i"]: f["geometry"] for f in geo["features"]}
check("poligoni NIL", len(geom), 88)
ana_ix = ana.set_index("id_nil")
Qd = dict(zip(QU.id_nil, QU.quintile))
FLd = FL.set_index("id_nil")
def cell(g, w, s):
    x = g[(g.finestra == w) & (g.sesso == s)]
    if x.empty: return None
    x = x.iloc[0]
    return [r(x.smr), r(x.smr_lo), r(x.smr_hi), r(x.e0, 2), r(x.e0_lo, 2), r(x.e0_hi, 2), int(x.osservati), r(x.attesi, 1), r(x.smr_shrunk)]
feats = []; rows_csv = []
for i, g in R.groupby("id_nil"):
    a = ana_ix.loc[i]; f = FLd.loc[i]
    ab = float(f.residenti_2024)
    pr = {"i": int(i), "n": a.nil, "mu": int(a.municipio_prevalente), "ab": int(round(ab)), "ab24": int(f.residenti_2024),
          "red": r(g.reddito_2024.iloc[0], 0), "q": int(Qd[i]) if i in Qd else None,
          "cl": 0 if bool(f.piccolo_sotto_3000) else 1, "v85": r(f.rapporto_85piu_2024, 2), "q85": r(f.quota_85piu_2024 * 100, 1)}
    pr["w"] = {w: {s: cell(g, w, s) for s in "TMF"} for w in WIN_FULL}
    for w in WIN_T: pr["w"][w] = {"T": cell(g, w, "T")}
    mm = g[(g.finestra == "2012-2019")]
    pr["fm"] = r(mm[mm.sesso == "F"].smr.iloc[0] / mm[mm.sesso == "M"].smr.iloc[0], 2) if (mm.sesso == "M").any() and mm[mm.sesso == "M"].smr.iloc[0] > 0 else None
    if i == 8: pr["w"] = {w: {s: None for s in "TMF"} for w in WIN_FULL}
    feats.append({"type": "Feature", "properties": pr, "geometry": geom[int(i)]})
geo_out = {"type": "FeatureCollection", "features": sorted(feats, key=lambda f: f["properties"]["i"])}
json.dump(geo_out, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))

# CSV larghi per NIL
T = R[R.sesso == "T"]
for i, g in R.groupby("id_nil"):
    a = ana_ix.loc[i]; f = FLd.loc[i]; row = {"id_nil": i, "nil": a.nil, "municipio_prevalente": int(a.municipio_prevalente),
        "residenti_2024": int(f.residenti_2024), "meno_di_3000_residenti": int(bool(f.piccolo_sotto_3000)),
        "quota_85piu_2024_pct": r(f.quota_85piu_2024 * 100, 2), "rapporto_85piu_su_citta": r(f.rapporto_85piu_2024, 2),
        "reddito_medio_2024_euro_per_CAP": r(g.reddito_2024.iloc[0], 0), "quintile_reddito_1povero_5ricco": Qd.get(i)}
    for w in WIN_FULL + WIN_T:
        for s in ("TMF" if w in WIN_FULL else "T"):
            x = g[(g.finestra == w) & (g.sesso == s)]
            if x.empty: continue
            x = x.iloc[0]; k = f"{w}_{ {'T':'tutti','M':'uomini','F':'donne'}[s] }".replace(" ", "")
            row[k + "_decessi"] = int(x.osservati); row[k + "_attesi"] = r(x.attesi, 1); row[k + "_SMR"] = r(x.smr)
            row[k + "_SMR_lo95"] = r(x.smr_lo); row[k + "_SMR_hi95"] = r(x.smr_hi)
            if w in WIN_FULL:
                row[k + "_e0_stimata"] = r(x.e0, 2); row[k + "_e0_lo95"] = r(x.e0_lo, 2); row[k + "_e0_hi95"] = r(x.e0_hi, 2)
    rows_csv.append(row)
pd.DataFrame(rows_csv).to_csv(os.path.join(OUT, "nil.csv"), index=False, sep=";", decimal=",", encoding="utf-8")
R.drop(columns=["quota_civici_cap_instabili"]).to_csv(os.path.join(OUT, "nil_finestre.csv"), index=False, sep=";", decimal=",", float_format="%.5g")
G.to_csv(os.path.join(OUT, "gruppi_reddito.csv"), index=False, sep=";", decimal=",", float_format="%.5g")
DN.to_csv(os.path.join(OUT, "decessi_nil_anno_sesso.csv"), index=False, sep=";")
MU.to_csv(os.path.join(OUT, "municipi.csv"), index=False, sep=";", decimal=",", float_format="%.5g")
COR.to_csv(os.path.join(OUT, "correlazione_reddito.csv"), index=False, sep=";", decimal=",", float_format="%.4g")
Y.to_csv(os.path.join(OUT, "citta_anno.csv"), index=False, sep=";", decimal=",", float_format="%.5g")

# ---------------------------------------------------------------- riepilogo
def grp(w, s):
    out = {}
    for q in range(1, 6):
        x = G[(G.finestra == w) & (G.sesso == s) & (G.quintile == q)].iloc[0]
        out[q] = dict(e0=r(x.e0, 2), e0_lo=r(x.e0_lo, 2), e0_hi=r(x.e0_hi, 2), smr=r(x.smr), smr_lo=r(x.smr_lo), smr_hi=r(x.smr_hi),
                      n_nil=int(x.n_nil), residenti=int(round(x.residenti)), red_min=r(x.reddito_min, 0), red_max=r(x.reddito_max, 0), osservati=int(x.osservati))
    a, b = out[1], out[5]
    se = math.sqrt(1 / G[(G.finestra == w) & (G.sesso == s) & (G.quintile == 1)].osservati.iloc[0] + 1 / G[(G.finestra == w) & (G.sesso == s) & (G.quintile == 5)].osservati.iloc[0])
    rat = a["smr"] / b["smr"]
    out["gap_e0"] = r(b["e0"] - a["e0"], 2); out["rapporto_smr_1su5"] = r(rat); out["rapporto_lo"] = r(rat * math.exp(-1.96 * se)); out["rapporto_hi"] = r(rat * math.exp(1.96 * se))
    return out
RIEP = {
    "scaricato": "2026-11-01",
    "finestre": {"2012-2019": "2012-2019 (prima del Covid)", "2022-2024": "2022-2024 (dopo il Covid)"},
    "citta": {w: {s: r(CF[(CF.finestra == w) & (CF.sesso == s)].e0_citta.iloc[0], 2) for s in "TMF"} for w in WIN_FULL + ["2012-2015", "2016-2019", "2020", "2021"]},
    "citta_decessi": {w: int(CF[(CF.finestra == w) & (CF.sesso == "T")].decessi.iloc[0]) for w in WIN_FULL},
    "quintili": {w: {s: grp(w, s) for s in "TMF"} for w in ["2012-2015", "2016-2019", "2012-2019", "2022-2024", "2020"]},
    "correlazione_reddito_smr": {f"{x.finestra}|{x.sesso}": dict(rho=r(x.spearman, 3), lo=r(x.lo, 3), hi=r(x.hi, 3), n=int(x.n_nil)) for x in COR.itertuples()},
    "sensibilita": SENS,
    "annuale": [{k: (None if pd.isna(v) else r(v, 2) if k not in ("anno",) else int(v)) for k, v in row.items()} for row in Y.to_dict("records")],
    "bes_serie": [{k: (None if pd.isna(v) else (int(v) if k == "anno" else r(v, 1))) for k, v in row.items()} for row in BES.to_dict("records")],
    "municipi": [{k: (None if pd.isna(v) else (v if isinstance(v, str) else r(v, 3))) for k, v in row.items()} for row in MU.to_dict("records")],
    "controlli": {"decessi_NIL_per_anno": CB["decessi_NIL_per_anno"], "decessi_istat_per_anno": CB["istat_totale_per_anno"], "avvisi": AVVISI},
    "origine": {
        "e0 e SMR per NIL": "speranza-vita/pulito/nil_smr_e0.csv (scripts/analisi.py)",
        "gruppi di reddito": "speranza-vita/pulito/gruppi_reddito.csv; reddito per NIL da quartieri-che-cambiano/out/indicatori_nil.csv (reddito_2024)",
        "citta anno per anno": "speranza-vita/pulito/citta_e0_annuale.csv; BES: benessere/pulito/bes_lungo.csv (01SAL001)",
        "robustezza": "speranza-vita/pulito/sensibilita.json (scripts/sensibilita.py)",
        "municipi": "speranza-vita/pulito/municipi_smr_e0.csv (scripts/municipi.py)",
    },
}
json.dump(RIEP, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
for k in ("2012-2019", "2022-2024"):
    print(k, "città", RIEP["citta"][k], "gap quintili T", RIEP["quintili"][k]["T"]["gap_e0"], "M", RIEP["quintili"][k]["M"]["gap_e0"], "F", RIEP["quintili"][k]["F"]["gap_e0"])
print("AVVISI:", AVVISI or "nessuno")
for f in sorted(os.listdir(OUT)): print(f, os.path.getsize(os.path.join(OUT, f)))
