"""Scrive i file dati della pagina "I soldi per i quartieri popolari" (docs/fondi-quartieri/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <fondi_quartieri_dir> <milano_in_dati_dir> <docs_dir>

Legge solo le tabelle pulite (fondi-quartieri/pulito/*.csv, riepilogo.json) e i poligoni dei NIL di citta-15-minuti.
Scrive in <docs_dir>/fondi-quartieri/data/: riepilogo.json, progetti.json, nil.geojson, progetti_perimetro.csv, aree.csv, bilancio_missione8_erp.csv, opencup_per_ente.csv.
Aggregati e titoli di progetti pubblici (CUP, titolo come nella fonte, ente pubblico, importi): nessuna persona, nessuna impresa privata.
Ogni numero importante e' confrontato con il valore atteso (controlli stampati; se uno e' diverso lo script si ferma)."""
import sys, os, json
import pandas as pd

F, P, DOCS = sys.argv[1], sys.argv[2], sys.argv[3]
PU = os.path.join(F, "pulito")
OUT = os.path.join(DOCS, "fondi-quartieri", "data")
os.makedirs(OUT, exist_ok=True)
BAD = []


def check(nome, calc, atteso, tol=0.5):
    ok = abs(calc - atteso) <= tol
    print(("ok  " if ok else "!!  ") + f"{nome}: {calc} (atteso {atteso})")
    if not ok:
        BAD.append(nome)


R = json.load(open(os.path.join(PU, "riepilogo.json"), encoding="utf-8"))
d = pd.read_csv(os.path.join(PU, "progetti_perimetro.csv"), sep=";", dtype=str, keep_default_na=False)
for c in ["importo", "pagato", "pagato_pct", "quota_pnrr", "ritardo_giorni", "nucleo"]:
    d[c] = pd.to_numeric(d[c], errors="coerce")

# ------------------------------------------------------------------ controlli sui numeri-chiave
T = R["totali"]
check("nucleo: progetti", T["nucleo_progetti"], 47, 0)
check("nucleo: finanziato (M)", round(T["nucleo_finanziato"] / 1e6, 1), 240.7, 0.05)
check("nucleo: pagato % ", T["nucleo_pagato_pct"], 61.0, 0.05)
pin = R["avanzamento_pnrr"]["PINQuA"]
check("PINQuA finanziato (M)", round(pin["finanziato"] / 1e6, 1), 223.7, 0.05)
check("PINQuA pagato %", pin["pagato_pct"], 55.0, 0.05)
check("PINQuA case popolari % del totale", R["pinqua_split"]["case_pct"], 57.2, 0.05)
check("PINQuA dopo 30/6/2026 (M)", round(pin["fine_dopo_30_6_2026"]["finanziato"] / 1e6, 1), 103.1, 0.05)
check("PUI pagato %", R["avanzamento_pnrr"]["Piani urbani integrati"]["pagato_pct"], 32.9, 0.05)
check("OpenCUP: CUP enti pubblici", R["opencup"]["cup_enti_pubblici"], 891, 0)
check("OpenCUP attivi dal 2020 (M)", round(R["opencup"]["attivi_dal_2020"]["costo"] / 1e6, 0), 1982, 0.5)
gg = d[d.cup == "J42C21002820004"].iloc[0]
check("Giaggioli finanziato (M)", round(gg.importo / 1e6, 2), 57.58, 0.01)
check("Giaggioli quota PNRR (M)", round(gg.quota_pnrr / 1e6, 2), 47.98, 0.01)
nucs = d[(d.nucleo == 1) & (~d.fonte.str.startswith("PNC"))]
check("somma progetti nucleo = riepilogo", nucs.importo.sum(), T["nucleo_finanziato"], 1)

# ------------------------------------------------------------------ progetti (tabella e download)
d["ambito_txt"] = d.ambito.map({"ERP": "Case popolari", "ABIT": "Emergenza abitativa e servizi per l'abitare", "QUART": "Spazi e servizi nei quartieri", "MOB": "Mobilita' (proposta PINQuA ID 94)"})
cols = ["fonte", "cup", "titolo", "programma", "ciclo", "ambito", "ambito_txt", "nucleo", "tipo_ente", "ente_attuatore", "ente_ruolo", "quartiere", "metodo_quartiere", "importo", "pagato", "pagato_pct",
        "quota_pnrr", "misura_importo", "stato", "fase", "fine_prevista_iso", "fine_effettiva_iso", "ritardo_giorni", "data_aggiornamento", "proposta_pinqua_id", "motivo_perimetro", "url"]
pj = d[cols].copy()
pj["titolo"] = pj.titolo.str.replace(r"\s+", " ", regex=True).str.strip()
pj.to_csv(os.path.join(OUT, "progetti_perimetro.csv"), sep=";", index=False, encoding="utf-8")
recs = json.loads(pj.drop(columns=["motivo_perimetro", "url"]).to_json(orient="records", force_ascii=False))
for r in recs:
    for k in ("importo", "pagato", "quota_pnrr"):
        if r[k] is not None:
            r[k] = round(r[k], 0)
    if r["pagato_pct"] is not None:
        r["pagato_pct"] = round(r["pagato_pct"], 1)
json.dump(recs, open(os.path.join(OUT, "progetti.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ------------------------------------------------------------------ aree e mappa (NIL)
ar = pd.read_csv(os.path.join(PU, "riep_per_quartiere.csv"), sep=";", dtype=str)
for c in ["progetti", "finanziato", "pagato", "pagato_pct"]:
    ar[c] = pd.to_numeric(ar[c])
qp = pd.read_csv(os.path.join(PU, "riep_quartiere_progetti.csv"), sep=";", dtype=str)
qp["importo"] = pd.to_numeric(qp.importo)
areas = []
for _, r in ar.iterrows():
    sub = qp[qp.area == r.area].sort_values("importo", ascending=False)
    areas.append({"area": r.area, "nil": [int(x) for x in r.nil_ids.split(";")], "progetti": int(r.progetti), "finanziato": round(r.finanziato), "pagato": round(r.pagato), "pagato_pct": r.pagato_pct,
                  "lista": [{"cup": a.cup, "titolo": a.titolo[:90], "importo": round(a.importo)} for a in sub.itertuples()]})
check("aree: somma finanziato", sum(a["finanziato"] for a in areas) + round(R["non_localizzati"]["finanziato"]), round(T["nucleo_finanziato"]), 3)
nilg = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf8"))
nil2area = {}
for a in areas:
    for i in a["nil"]:
        nil2area[i] = a


def rnd(c, n=5):
    if isinstance(c[0], (int, float)):
        return [round(c[0], n), round(c[1], n)]
    return [rnd(x, n) for x in c]


feats = []
for f in nilg["features"]:
    p = f["properties"]
    i = int(p["ID_NIL"])
    a = nil2area.get(i)
    pr = {"i": i, "n": p["NIL"].title().replace("Q.Re", "Q.re"), "a": a["area"] if a else "", "f": a["finanziato"] if a else 0, "p": a["pagato"] if a else 0, "np": a["progetti"] if a else 0}
    feats.append({"type": "Feature", "properties": pr, "geometry": {"type": f["geometry"]["type"], "coordinates": rnd(f["geometry"]["coordinates"])}})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nil.geojson"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
pd.DataFrame([{k: v for k, v in a.items() if k not in ("lista", "nil")} | {"nil_ids": ";".join(map(str, a["nil"]))} for a in areas]).to_csv(os.path.join(OUT, "aree.csv"), sep=";", index=False)

# ------------------------------------------------------------------ riepilogo per la pagina
pub_small = {k: R[k] for k in ("totali", "per_programma", "per_ente", "per_ambito", "non_localizzati", "metodo_quartiere", "avanzamento_pnrr", "pinqua_split", "opencoesione", "bilancio_m8_erp",
                               "bilancio_m8_erp_capitale_2021_2025", "opencup")}
pub_small["aree"] = areas
pub_small["meta"] = {"scarico": "2026-11-01", "oc_riferimento": "2026-06-30", "pnrr_estrazione": "2026-06-13", "opencup_aggiornamento": "2026-10-01", "pnc_estrazione": "2024-03-07"}
# ente del singolo progetto grande: solo enti pubblici
pub_small["opencup"]["top"] = [t for t in R["opencup"]["top"]]
json.dump(pub_small, open(os.path.join(OUT, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"), default=float)
pd.read_csv(os.path.join(PU, "riep_bilancio_missione8_erp.csv"), sep=";").to_csv(os.path.join(OUT, "bilancio_missione8_erp.csv"), sep=";", index=False)
pd.read_csv(os.path.join(PU, "riep_opencup_per_ente.csv"), sep=";").to_csv(os.path.join(OUT, "opencup_per_ente.csv"), sep=";", index=False)

tot = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
print("dimensione cartella data:", round(tot / 1e6, 2), "MB")
if BAD:
    print("CONTROLLI FALLITI:", BAD)
    sys.exit(1)
print("tutti i controlli ok")
