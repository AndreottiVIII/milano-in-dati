"""Scrive i dati della pagina docs/scuole-domani/data/ (rieseguibile).

Uso: python -I -X utf8 pagina.py <percorso assoluto milano-in-dati> <percorso assoluto scuole-domani>
Legge: out/*.csv (da 02, 03, 04), scuole/pulito/scuole_anno_tidy.csv, docs/scuole/data/scuole.json (nomi puliti)
e docs/scuole/data/nil.geojson (sagome dei NIL). Non scrive il file index.html (e' scritto a mano).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

base = Path(sys.argv[1])
O = Path(sys.argv[2])
out = O / "out"
dest = base / "docs" / "scuole-domani" / "data"
dest.mkdir(parents=True, exist_ok=True)
ORD = ["infanzia", "primaria", "sec1"]
ANNI_P = list(range(2009, 2025))
ANNI_F = list(range(2025, 2035))


def rd(name):
    return pd.read_csv(out / name, sep=";")


def nz(x):
    return None if pd.isna(x) else x


tidy = pd.read_csv(base / "scuole" / "pulito" / "scuole_anno_tidy.csv", sep=";")
tidy = tidy[tidy.ordine.isin(ORD)]
pr_s = rd("proiezione_scuole.csv")
pr_n = rd("proiezione_nil.csv")
pr_r = rd("proiezione_residenti_nil.csv")
pr_c = rd("proiezione_citta.csv")
sens = rd("sensibilita_scenari.csv")
bande = rd("backtest_bande_errore.csv")
casi = rd("backtest_casi.csv")
soglia = rd("backtest_soglia_riepilogo.csv")
qvs = rd("sorpresa_quartiere_vs_scuola.csv")
gn = rd("sorpresa_gia_nati.csv")
sg = rd("sorpresa_soglie.csv")
rapp = rd("sorpresa_nil_rapporto_alunni_residenti.csv")
bt_riep = rd("backtest_riepilogo.csv")
bt_nil = rd("backtest_nil.csv")
bt_cit = rd("backtest_citta.csv")
sj = {s["id"]: s for s in json.load(open(base / "docs" / "scuole" / "data" / "scuole.json", encoding="utf-8"))}

# ---------------- citta': passato + scenari + bambini residenti
res_csv = pd.read_csv(base / "popolazione" / "pulito" / "residenti_nil_anno_eta_genere.csv")
BANDE = {"infanzia": (3, 5), "primaria": (6, 10), "sec1": (11, 13)}
citta = {}
for k, o in enumerate(ORD):
    past = tidy[tidy.ordine == o].groupby("anno_inizio").iscritti.sum().reindex(ANNI_P)
    lo, hi = BANDE[o]
    rp = res_csv[(res_csv.eta >= lo) & (res_csv.eta <= hi)].groupby("anno").residenti.sum()
    rf = pr_r[pr_r.ordine == o][[f"res{y}" for y in ANNI_F]].sum()
    c = pr_c[pr_c.ordine == o]

    def serie(comb):
        s = c[c.combinazione == comb].set_index("anno").alunni_proiettati
        return [round(float(s[y])) for y in ANNI_F]

    citta[o] = {
        "passato": [int(v) for v in past.values],
        "centrale": serie("centrale"), "nati_in_calo": serie("nati_in_calo"), "nati_in_risalita": serie("nati_in_risalita"),
        "con_migrazione": serie("con_migrazione"), "solo_citta": serie("solo_citta"),
        "residenti_passato": [int(rp[y]) for y in ANNI_P], "residenti_2025": int(rp[2025]),
        "residenti_futuro": [round(float(rf[f"res{y}"])) for y in ANNI_F[1:]],
    }
    cl = pr_c[(pr_c.ordine == o) & (pr_c.combinazione == "centrale") & (pr_c.anno == 2034)].iloc[0]
    citta[o]["classi_eq_2034"] = round(float(cl.classi_equivalenti))
    citta[o]["alunni_per_classe_2024"] = round(float(cl.alunni_per_classe_2024), 1)

# ---------------- NIL (geojson)
geo = json.load(open(base / "docs" / "scuole" / "data" / "nil.geojson", encoding="utf-8"))
nome_nil = {}
feats = []
for f in geo["features"]:
    i = int(f["properties"]["i"])
    nome_nil[i] = f["properties"]["n"]
    p = {"i": i, "n": f["properties"]["n"]}
    for k, o in enumerate(ORD):
        a = pr_n[(pr_n.ordine == o) & (pr_n.id_nil == i)]
        r = pr_r[(pr_r.ordine == o) & (pr_r.id_nil == i)]
        if len(a):
            a = a.iloc[0]
            p[f"a24_{k}"] = int(a.iscritti_2024)
            p[f"a29_{k}"] = round(float(a.p2029))
            p[f"a34_{k}"] = round(float(a.p2034))
            p[f"ns_{k}"] = int(a.n_scuole)
            p[f"av_{k}"] = round(float(a.var_pct_2034_su_2024), 1) if a.iscritti_2024 >= 200 else None
        else:
            p[f"a24_{k}"] = 0
            p[f"av_{k}"] = None
        if len(r):
            r = r.iloc[0]
            p[f"r24_{k}"] = int(r.residenti_fascia_2024)
            p[f"r34_{k}"] = round(float(r.res2034))
            p[f"rv_{k}"] = round(100 * (float(r.res2034) / float(r.residenti_fascia_2024) - 1), 1) if r.residenti_fascia_2024 >= 200 else None
        else:
            p[f"r24_{k}"] = 0
            p[f"rv_{k}"] = None
    feats.append({"type": "Feature", "properties": p, "geometry": f["geometry"]})
json.dump({"type": "FeatureCollection", "features": feats}, open(dest / "nil.geojson", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ---------------- scuole (solo infanzia e primaria)
GEST = {"statale": 0, "comunale": 1, "privata_paritaria": 2, "privata_non_paritaria": 3}
rows = []
for _, r in pr_s[pr_s.ordine.isin(["infanzia", "primaria"])].iterrows():
    s = sj.get(r.codice, {})
    serie = s.get("i") or []
    ser = [None if v is None else int(v) for v in serie]
    # salto improvviso o buchi: puo' essere un cambio di codice (fusione, trasloco), non un calo vero
    salto = False
    prev = None
    for v in ser:
        if v is not None and v > 0 and prev is not None and prev > 0 and max(v, prev) >= 40 and abs(v - prev) / max(v, prev) > 0.4:
            salto = True
        prev = v
    vals = [v for v in ser if v]
    buchi = bool(vals) and any((not v) for v in ser[ser.index(vals[0]):]) and ser[-1]
    # tenuta: 0 sopra in tutte, 1 dipende, 2 sotto in tutte, None senza riferimento
    t = r.tenuta_del_risultato
    tc = None if t.startswith("senza") else (2 if t.startswith("sotto") else (0 if t.startswith("sopra") else 1))
    rows.append({
        "id": r.codice, "n": s.get("n") or r.denominazione.title(), "a": s.get("a") or r.indirizzo, "o": 0 if r.ordine == "infanzia" else 1,
        "g": GEST.get(r.gestione, 3), "nil": int(r.id_nil), "cl": nz(r.classi_2024),
        "i": ser, "p": [round(float(r[f"p{y}"])) for y in ANNI_F],
        "i15": None if pd.isna(r.iscritti_2015) else int(r.iscritti_2015),
        "gs": bool(r.gia_sotto_70_nel_2024) if not pd.isna(r.iscritti_2015) else None,
        "s34": bool(r.sotto_70_nel_2034) if not pd.isna(r.iscritti_2015) else None,
        "t": tc, "ay": None if pd.isna(r.primo_anno_sotto_70) else int(r.primo_anno_sotto_70),
        "v": [round(float(r[f"p2034_{k}"])) for k in ["nati_in_calo", "nati_in_risalita", "solo_citta", "solo_nil", "con_migrazione"]],
        "pc": bool(r.piccola_meno_50_alunni_2024), "cod": bool(salto or buchi),
    })
sc_json = rows
json.dump(sc_json, open(dest / "scuole.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ---------------- riepilogo
def rec(df):
    return json.loads(df.to_json(orient="records"))

bt_pool5 = bt_riep[(bt_riep.h == 5) & bt_riep.metodo.isin(["centrale", "fermo"])]
sogl = soglia[(soglia.soglia == 0.7) & soglia.metodo.isin(["centrale", "fermo"])]
errcit5 = bt_cit[(bt_cit.h == 5) & bt_cit.metodo.isin(["centrale", "fermo"])].groupby(["metodo", "ordine"]).err_citta.agg(lambda x: x.abs().mean()).reset_index()
nil5 = bt_nil[(bt_nil.h == 5) & bt_nil.metodo.isin(["centrale", "fermo"])].groupby(["metodo", "ordine"]).WAPE_nil.mean().reset_index()
conteggi = []
for o in ["infanzia", "primaria"]:
    s = [x for x in rows if x["o"] == (0 if o == "infanzia" else 1) and x["i15"] is not None]
    conteggi.append({"ordine": o, "con_rif": len(s), "gia": sum(1 for x in s if x["gs"]), "sotto34": sum(1 for x in s if x["s34"]),
                     "robuste": sum(1 for x in s if x["t"] == 2), "dipende": sum(1 for x in s if x["t"] == 1 and x["s34"]),
                     "tot": sum(1 for x in rows if x["o"] == (0 if o == "infanzia" else 1))})
s1 = pr_n[pr_n.ordine == "sec1"]
riepilogo = {
    "anni_passati": ANNI_P, "anni_futuri": ANNI_F, "citta": citta,
    "bande": {o: {int(r.h): [round(float(r.q10), 3), round(float(r.q90), 3)] for r in bande[bande.ordine == o].itertuples()} for o in ORD},
    "casi": rec(casi[casi.metodo.isin(["centrale", "fermo"])]),
    "pool5": rec(bt_pool5), "err_citta5": rec(errcit5), "err_nil5": rec(nil5), "soglia": rec(sogl),
    "quartiere_vs_scuola": rec(qvs), "gia_nati": rec(gn), "soglie": rec(sg), "sensibilita": rec(sens),
    "conteggi": conteggi,
    "rapporto": json.load(open(out / "sorpresa_riepilogo.json", encoding="utf-8"))["rapporto_alunni_residenti"],
    "tasso_nati_pct": -1.76,
}
json.dump(riepilogo, open(dest / "riepilogo.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"), default=float)

# ---------------- file scaricabili (sottoinsieme di out/, solo infanzia e primaria per le scuole)
import csv
pr_s[pr_s.ordine.isin(["infanzia", "primaria"])].to_csv(dest / "proiezione_scuole_infanzia_primaria.csv", sep=";", index=False, float_format="%.3f")
pr_n.to_csv(dest / "proiezione_nil.csv", sep=";", index=False, float_format="%.2f")
pr_r.to_csv(dest / "proiezione_residenti_nil.csv", sep=";", index=False, float_format="%.2f")
pr_c.to_csv(dest / "proiezione_citta.csv", sep=";", index=False, float_format="%.1f")
casi.to_csv(dest / "backtest_casi.csv", sep=";", index=False, float_format="%.2f")
sens.to_csv(dest / "sensibilita_scenari.csv", sep=";", index=False, float_format="%.2f")
print("scritto", dest, "scuole:", len(rows), "con salto/buchi:", sum(r["cod"] for r in rows), "piccole:", sum(r["pc"] for r in rows))
print(conteggi)
