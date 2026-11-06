"""Dati nuovi per la pagina Scuole di domani (versione 2). Rieseguibile.
Uso: python -I -X utf8 pagina_v2.py <percorso assoluto milano-in-dati> <percorso assoluto scuole-domani>
Scrive in docs/scuole-domani/data/ SOLO file con nomi nuovi: scuole_tre_ordini.json, prova_sul_passato.json.
Non tocca i file usati dalla pagina attuale."""
import json, sys
from pathlib import Path
import pandas as pd

base = Path(sys.argv[1]); O = Path(sys.argv[2]); out = O / "out"
dest = base / "docs" / "scuole-domani" / "data"
ORD = ["infanzia", "primaria", "sec1"]
GN = {"statale": 0, "comunale": 1, "privata_paritaria": 2, "privata_non_paritaria": 3}

def nz(x, d=None):
    return None if pd.isna(x) else x

ps = pd.read_csv(out / "proiezione_scuole.csv", sep=";")
tidy = pd.read_csv(base / "scuole" / "pulito" / "scuole_anno_tidy.csv", sep=";")
tidy = tidy[tidy.ordine.isin(ORD)]
sj = {s["id"]: s for s in json.load(open(base / "docs" / "scuole" / "data" / "scuole.json", encoding="utf-8"))}
pos = tidy.sort_values("anno_inizio").groupby("codice")[["lon", "lat", "denominazione"]].last()
anni = list(range(2009, 2025))
serie = tidy.pivot_table(index=["ordine", "codice"], columns="anno_inizio", values="iscritti", aggfunc="sum")

def nome(code, den):
    s = sj.get(code)
    if s and s.get("n"):
        return s["n"]
    return str(den).title()

res = []
for _, r in ps.iterrows():
    c = r.codice; o = ORD.index(r.ordine)
    s = sj.get(c, {})
    lon = s.get("x"); lat = s.get("y")
    if (lon is None or lat is None) and c in pos.index:
        lon, lat = pos.loc[c, "lon"], pos.loc[c, "lat"]
    if lon is None or pd.isna(lon):
        continue
    try:
        ser = [None if pd.isna(v) else int(v) for v in serie.loc[(r.ordine, c)].reindex(anni)]
    except KeyError:
        ser = [None] * len(anni)
    res.append({
        "id": c, "n": nome(c, r.denominazione), "a": s.get("a") or r.indirizzo, "o": o, "g": GN[r.gestione],
        "nil": int(r.id_nil), "x": round(float(lon), 5), "y": round(float(lat), 5), "cl": int(r.classi_2024) if not pd.isna(r.classi_2024) else None,
        "i": ser, "p": [round(float(r[f"p{y}"])) for y in range(2025, 2035)],
        "fb": round(float(r.fascia_bassa_2034)), "fa": round(float(r.fascia_alta_2034)),
        "i15": None if pd.isna(r.iscritti_2015) else int(r.iscritti_2015),
        "gs": bool(r.gia_sotto_70_nel_2024), "s34": bool(r.sotto_70_nel_2034),
        "ay": None if pd.isna(r.primo_anno_sotto_70) else int(r.primo_anno_sotto_70),
        "t": {"sopra 70% in tutte e 6 le varianti": 0, "sotto 70% in tutte e 6 le varianti": 2, "dipende dalla variante": 1}.get(r.tenuta_del_risultato, -1),
        "pc": bool(r.piccola_meno_50_alunni_2024),
    })
json.dump(res, open(dest / "scuole_tre_ordini.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("scuole", len(res), [sum(1 for x in res if x["o"] == k) for k in range(3)])

# ---- prova sul passato
bc = pd.read_csv(out / "backtest_citta.csv", sep=";")
bc = bc[bc.metodo == "centrale"]
prova = {"citta": {}, "scuole": [], "casi": []}
tid = tidy.groupby(["ordine", "anno_inizio"]).iscritti.sum()
for o in ORD:
    reale = {int(a): int(tid[(o, a)]) for a in anni}
    prova["citta"][o] = {"reale": [reale[a] for a in anni]}
    for t0 in (2014, 2019):
        sub = bc[(bc.ordine == o) & (bc["T0"] == t0)].sort_values("h")
        prova["citta"][o][f"da{t0}"] = [[t0 + int(h), round(float(p))] for h, p in zip(sub.h, sub.proiettati)]
bs = pd.read_csv(out / "backtest_scuole.csv", sep=";")
bs = bs[(bs.metodo == "centrale") & (bs["T0"] == 2019) & (bs.h == 5) & (bs.esiste_dopo == True)]
for _, r in bs.iterrows():
    prova["scuole"].append([r.codice, ORD.index(r.ordine), int(r.reali), round(float(r.proiettati), 1)])
casi = pd.read_csv(out / "backtest_casi.csv", sep=";")
casi = casi[casi.metodo.isin(["centrale", "centrale_nati_veri"])]
for _, r in casi.iterrows():
    prova["casi"].append({"m": r.metodo, "da": int(r.partenza), "a": int(r.arrivo), "o": ORD.index(r.ordine), "err": float(r.errore_citta_pct),
                          "mediana": float(r.mediana_err_scuola_pct), "e10": float(r.scuole_entro10_pct), "e20": float(r.scuole_entro20_pct), "n": int(r.n_scuole)})
json.dump(prova, open(dest / "prova_sul_passato.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("prova ok", len(prova["scuole"]))
