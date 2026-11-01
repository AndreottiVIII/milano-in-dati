"""Scrive i file dati della pagina "Morti giorno per giorno" (docs/morti/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <morti_dir> <docs_dir>

Legge (fase 1): morti/pulito/{milano,lombardia,italia}_{giorno,settimana}.csv, annuale_confronto.csv, finestre_covid.csv, picco_2020.csv,
milano_eta_sesso_finestre.csv, milano_tassi_eta_sesso.csv, milano_composizione_per_anno.csv, ondate_caldo.csv, ondate_freddo.csv,
estati_confronto.csv, estati_pct_per_area.csv, estate_rapporto_per_tmax3.csv, inverni_confronto.csv, revisioni_release.csv, riepilogo.json.
Scrive in <docs_dir>/morti/data/: *.json per la pagina e alcuni *.csv da scaricare.
Dati aggregati (Milano, Lombardia, Italia; per giorno o settimana): nessuna riga per comune, il file ISTAT da 827 MB non viene copiato.
Baseline di riferimento = B (ultimi 5 anni senza 2020 e 2021); A solo nell'annuale per le note di metodo.
"""
import sys, os, json, shutil
import numpy as np, pandas as pd

M, DOCS = sys.argv[1], sys.argv[2]
PU = os.path.join(M, "pulito")
OUT = os.path.join(DOCS, "morti", "data")
os.makedirs(OUT, exist_ok=True)
AVVISI = []


def check(nome, calcolato, atteso, tol=0):
    ok = abs(calcolato - atteso) <= tol
    if not ok:
        AVVISI.append(f"DIVERSO {nome}: calcolato {calcolato} atteso {atteso}")
    print(("ok  " if ok else "!!  ") + f"{nome}: {calcolato} (atteso {atteso})")


def rd(n, **kw):
    return pd.read_csv(os.path.join(PU, n), **kw)


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating, float)):
        return None if (o != o) else round(float(o), 3)
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return o


def dump(nome, obj):
    with open(os.path.join(OUT, nome), "w", encoding="utf8") as f:
        json.dump(clean(obj), f, ensure_ascii=False, separators=(",", ":"))


def recs(df):
    return clean(df.to_dict("records"))


RIEP = json.load(open(os.path.join(PU, "riepilogo.json"), encoding="utf8"))

# ---------------------------------------------------------------- Milano giorno per giorno
g = rd("milano_giorno.csv", parse_dates=["data"])
assert g.attesi_B.notna().all()
NTX = int(g.TX.isna().sum())  # giorni senza temperatura (2026): restano null
dump("milano_giorno.json", {"inizio": str(g.data.min().date()), "fine": str(g.data.max().date()),
                            "morti": g.morti.astype(int).tolist(), "attesi": g.attesi_B.round(1).tolist(), "tx": g.TX.round(1).tolist()})  # clean() trasforma i NaN in null
g[["data", "morti", "attesi_B", "TX"]].rename(columns={"attesi_B": "attesi", "TX": "tmax_brera"}).round(2).to_csv(
    os.path.join(OUT, "milano_giorno.csv"), index=False)
check("Milano morti 2020", int(g[g.data.dt.year == 2020].morti.sum()), 18487)
check("Milano morti 3/4/2020", int(g[g.data == "2020-04-03"].morti.iloc[0]), 137)
check("Milano giorni", len(g), (pd.Timestamp("2026-06-30") - pd.Timestamp("2014-01-01")).days + 1)

# ---------------------------------------------------------------- settimane (complete)
sett = {}
for k in ("milano", "lombardia", "italia"):
    s = rd(f"{k}_settimana.csv", parse_dates=["lunedi"])
    s = s[s.completa]
    sett[k.capitalize()] = [[str(r.lunedi.date()), int(r.morti), round(float(r.attesi_B), 1)] for r in s.itertuples()]
    s[["lunedi", "morti", "attesi_B"]].rename(columns={"attesi_B": "attesi"}).round(1).to_csv(os.path.join(OUT, f"{k}_settimana.csv"), index=False)
dump("settimane.json", {"nota": "settimane ISO complete (7 giorni); [lunedi, morti, attesi B]", **sett})

# ---------------------------------------------------------------- primavera 2020 giorno per giorno (3 aree)
cov = {"inizio": "2020-02-01", "fine": "2020-06-30"}
for k in ("milano", "lombardia", "italia"):
    d = rd(f"{k}_giorno.csv", parse_dates=["data"]).set_index("data").loc["2020-02-01":"2020-06-30"]
    cov[k.capitalize()] = {"morti": d.morti.astype(int).tolist(), "attesi": d.attesi_B.round(1).tolist()}
cov["picco"] = recs(rd("picco_2020.csv"))
dump("covid2020.json", cov)

# ---------------------------------------------------------------- annuale
A = rd("annuale_confronto.csv")
comp = rd("milano_composizione_per_anno.csv")
mil = A[A.scope == "Milano"]
dump("annuale.json", {
    "milano": recs(mil[["anno", "giorni", "morti", "attesi_A", "attesi_B", "attesi_eta", "eccesso_B", "pct_B", "eccesso_eta", "pct_eta", "pct_A"]]),
    "morti_2011_2025": recs(comp[["anno", "morti", "maschi", "femmine"]]),
    "pct_B_aree": {s: recs(A[A.scope == s][["anno", "morti", "attesi_B", "pct_B"]]) for s in ("Lombardia", "Italia", "Lombardia_senza_Milano", "Italia_senza_Lombardia")},
})
A.round(2).to_csv(os.path.join(OUT, "annuale.csv"), index=False)
check("Milano 2025", int(comp[comp.anno == 2025].morti.iloc[0]), 13639)

# ---------------------------------------------------------------- finestre Covid
W = rd("finestre_covid.csv")
keep = ["scope", "finestra", "da", "a", "giorni", "morti", "attesi_B", "eccesso_B", "pct_B", "attesi_eta", "eccesso_eta", "pct_eta"]
dump("finestre.json", recs(W[keep]))
W[keep].round(2).to_csv(os.path.join(OUT, "finestre_covid.csv"), index=False)
mm = W[(W.scope == "Milano") & (W.finestra == "primavera 2020")].iloc[0]
check("Milano primavera 2020 eccesso", round(mm.eccesso_B), 2934, 1)
mens = rd("mensile_confronto.csv")
dump("mensile.json", recs(mens[mens.anno.isin([2020, 2021, 2022])][["scope", "anno", "mese", "morti", "attesi_B", "pct_B"]]))

# ---------------------------------------------------------------- eta e sesso
es = rd("milano_eta_sesso_finestre.csv")
tassi = rd("milano_tassi_eta_sesso.csv")
dump("eta_sesso.json", {"finestre": recs(es), "composizione": recs(comp), "tassi": recs(tassi)})
es.to_csv(os.path.join(OUT, "milano_eta_sesso_finestre.csv"), index=False)
comp.to_csv(os.path.join(OUT, "milano_composizione_per_anno.csv"), index=False)
tassi.to_csv(os.path.join(OUT, "milano_tassi_eta_sesso.csv"), index=False)
check("quota 85+ 2025", float(comp[comp.anno == 2025].quota_85p.iloc[0]), 55.5, 0.05)

# ---------------------------------------------------------------- caldo e freddo
hot = rd("ondate_caldo.csv")
est = rd("estati_confronto.csv")
area = rd("estati_pct_per_area.csv")
bins = rd("estate_rapporto_per_tmax3.csv")
dump("caldo.json", {"soglia_tx": 33, "coda_giorni": 3, "minimo_giorni": 3, "ondate": recs(hot), "estati": recs(est),
                    "estati_per_area": recs(area), "classi_tmax3": recs(bins)})
hot.to_csv(os.path.join(OUT, "ondate_caldo.csv"), index=False)
est.to_csv(os.path.join(OUT, "estati_confronto.csv"), index=False)
check("ondate di caldo", len(hot), 39)
cold = rd("ondate_freddo.csv")
inv = rd("inverni_confronto.csv")
dump("freddo.json", {"coda_giorni": 7, "ondate": recs(cold), "inverni": recs(inv)})
cold.to_csv(os.path.join(OUT, "ondate_freddo.csv"), index=False)
inv.to_csv(os.path.join(OUT, "inverni_confronto.csv"), index=False)

# ---------------------------------------------------------------- revisioni (dati provvisori)
rv = rd("revisioni_release.csv")
rv = rv[rv.scope.isin(["Milano", "Italia"]) & rv.periodo.str.match(r"^2025-0[1-6]$")]
dump("revisioni.json", recs(rv[["scope", "periodo", "2025-08-05", "2026-03-31", "2026-08-25", "var_ago25_a_ago26_pct"]]))
j = rv[(rv.scope == "Milano") & (rv.periodo == "2025-06")].iloc[0]
check("giugno 2025 Milano release agosto 2025", int(j["2025-08-05"]), 1032)

# ---------------------------------------------------------------- riepilogo
tot = rd("annuale_confronto.csv")
dump("riepilogo.json", {
    "fonte": {"nome": "ISTAT, Decessi e cause di morte: dati giornalieri comunali (decessi comunali giornalieri provvisori)",
              "pagina": "https://www.istat.it/it/archivio/240401",
              "release": "25 agosto 2026", "scaricato": "2026-11-01", "periodo": "2011-01-01 / 2026-06-30",
              "file": "comuni_giornaliero_30giugno26.csv (zip 51.592.163 byte)",
              "licenza": "Creative Commons Attribuzione 4.0 (note legali ISTAT, https://www.istat.it/note-legali/)",
              "temperature": "Milano Brera, serie giornaliera del filone temperature (massima TX), fino al 28/10/2026",
              "popolazione": "ISTAT demo.istat.it, POSAS al 1 gennaio 2019-2026"},
    "origine": "morti/pulito/*.csv (fase 1: morti/NOTE.md); questi file sono copie aggregate (Milano, Lombardia, Italia)",
    "ultimo_giorno": "2026-06-30", "giorni_senza_tmax": NTX,
    "controlli": AVVISI,
})
print("AVVISI:", AVVISI or "nessuno")
if AVVISI:
    sys.exit(1)
