"""Dati per due grafici della pagina scuole: (1) stranieri tra i residenti e tra gli alunni, per quartiere;
(2) punteggi INVALSI e quota di stranieri in classe. Scrive in docs/scuole/data/.

Uso: python -I -X utf8 web_stranieri_invalsi.py <cartella milano-in-dati> [scripts]
Il divario tra stranieri e italiani e lo scarto tipico non stanno nei csv: si ricalcolano dai microdati
(scuole/raw/invalsi_campione) con le funzioni di invalsi_stranieri.py. Con l'opzione --no-raw si salta il ricalcolo
e si tengono i valori gia' scritti in invalsi_stranieri.json.
"""
import csv, json, os, runpy, sys, collections

ROOT = sys.argv[1]
SCR = os.path.join(ROOT, "scuole", "scripts")
PUL = os.path.join(ROOT, "scuole", "pulito")
OUT = os.path.join(ROOT, "docs", "scuole", "data")
SOGLIA = 200


def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8-sig"), delimiter=";"))


def fl(v):
    return float(v.replace(",", ".")) if v not in ("", None) else None


# ---------- 1. quartieri ----------
nil = [r for r in rd(os.path.join(PUL, "nil_stranieri_2024.csv")) if r["ordine"] == "primaria"]
sc = [r for r in rd(os.path.join(PUL, "stranieri_scuole_vs_nil_2024.csv")) if r["ordine"] == "primaria"]
ges = collections.defaultdict(lambda: collections.Counter())
for r in sc:
    ges[int(float(r["id_nil"]))][r["gestione"]] += int(float(r["iscritti"]))
punti, esclusi = [], 0
for r in nil:
    isc, res = fl(r["iscritti"]), fl(r["residenti_fascia"])
    qa, qr = fl(r["quota_pupilli_pct"]), fl(r["quota_residenti_fascia_pct"])
    if not (isc and res and qa is not None and qr is not None):
        continue
    if isc < SOGLIA or res < SOGLIA:
        esclusi += 1
        continue
    i = int(float(r["id_nil"]))
    g = ges[i]
    par = (g["privata_paritaria"] + g["privata_non_paritaria"]) / sum(g.values()) * 100
    punti.append(dict(i=i, n=r["nil"], alunni=int(isc), stranieri=int(fl(r["non_it"])), qa=qa, qr=qr, res=int(res),
                      scuole=int(float(r["scuole"])), priv=round(par, 1)))
for p in punti:
    p["d"] = round(p["qa"] - p["qr"], 1)
sotto = [p for p in punti if p["d"] < 0]
sopra = [p for p in punti if p["d"] > 0]
forte = [p for p in punti if p["d"] <= -10]
resto = [p for p in punti if p["d"] > -10]
mm = lambda L: round(sum(p["priv"] for p in L) / len(L), 1) if L else None
quart = dict(anno="2024/25", soglia=SOGLIA, n_quartieri=len(punti), esclusi_piccoli=esclusi,
             sopra=len(sopra), sotto=len(sotto), n_forte=len(forte), priv_forte=mm(forte), priv_resto=mm(resto),
             punti=punti)
json.dump(quart, open(os.path.join(OUT, "stranieri_quartieri.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print("quartieri", len(punti), "sopra", len(sopra), "sotto", len(sotto), "esclusi", esclusi)
print("sotto di 10+ punti:", len(forte), "quota priv media", mm(forte), "contro", mm(resto), "n", len(resto))
for p in sorted(punti, key=lambda p: p["d"])[:6] + sorted(punti, key=lambda p: -p["d"])[:4]:
    print(" ", p["n"], p["alunni"], p["qa"], p["qr"], p["d"], "scuole", p["scuole"], "priv%", p["priv"])

# ---------- 2. INVALSI ----------
fasce = rd(os.path.join(PUL, "invalsi_stranieri_fasce.csv"))
mod = rd(os.path.join(PUL, "invalsi_stranieri_modelli.csv"))
BINS = ["0-5%", "5-10%", "10-20%", "20-30%", "30-50%", ">50%"]
out = dict(fasce={}, modelli={}, divario={})
for area in ("Nord", "Lombardia"):
    out["fasce"][area] = [dict(f=r["fascia"], classi=int(r["n_classi"]), alunni=int(r["n_studenti"]), media=fl(r["media_pesata"]),
                               d=fl(r["diff_escs_ind_classe"]), se=fl(r["se_escs_ind_classe"]))
                          for b in BINS for r in fasce if r["grado"] == "5" and r["materia"] == "ita" and r["area"] == area
                          and r["gruppo"] == "nativi" and r["fascia"] == b]
    for mat in ("ita", "mat"):
        for tag, nome in (("C", "C ESCS individuale + classe"), ("F", "F stessa scuola, ESCS ind. + classe")):
            r = [x for x in mod if x["grado"] == "5" and x["materia"] == mat and x["area"] == area and x["gruppo"] == "nativi" and x["modello"] == nome][0]
            out["modelli"][f"{area}|{mat}|{tag}"] = dict(b=fl(r["coef_per_10pp"]), lo=fl(r["ci95_basso"]), hi=fl(r["ci95_alto"]),
                                                          classi=int(r["n_classi"]), scuole=int(r["n_scuole"]), alunni=int(r["n_studenti"]))
# divario e scarto tipico dai microdati
import numpy as np
RAW = os.path.join(ROOT, "scuole", "raw", "invalsi_campione")
vecchio = os.path.join(OUT, "invalsi_stranieri.json")
if "--no-raw" in sys.argv and os.path.exists(vecchio):
    out["divario"] = json.load(open(vecchio, encoding="utf-8"))["divario"]
else:
    sys.argv = ["x", RAW, PUL]
    m = runpy.run_path(os.path.join(SCR, "invalsi_stranieri.py"), run_name="lib")
    d, conta = m["tutto"]()
    conta["ok"] = (conta.noti >= 10) & (conta.quota_mancante <= 0.25)
    d = d.merge(conta[["id_classe", "ok"]], on="id_classe", how="left")
    d["quota_ok"] = d.ok
    d = d[d.punteggio.notna() & d.peso.notna()]
    wls, GEO, dummies = m["wls_cl"], m["GEO"], m["dummies"]
    for geo in ("Lombardia", "Nord"):
        s = d[(d.grado == 5) & (d.materia == "ita") & GEO[geo](d) & d.origine.isin([1, 2, 3]) & d.quota_ok].copy()
        mu = np.average(s.punteggio, weights=s.peso)
        sd = float(np.sqrt(np.average((s.punteggio - mu) ** 2, weights=s.peso)))
        s["st"] = s.origine.isin([2, 3]).astype(float)
        ya = dummies(s, "anno")
        ra = dummies(s, "cod_reg") if geo != "Lombardia" else []
        r0 = wls(s, "punteggio", ["st"] + ya + ra)
        r1 = wls(s, "punteggio", ["st", "escs"] + ya + ra)
        out["divario"][geo] = dict(media=round(float(mu), 1), sd=round(sd, 1), grezzo=round(float(r0["b"][0]), 1), se_grezzo=round(float(r0["se_id_scuola"][0]), 1),
                                   parita=round(float(r1["b"][0]), 1), se_parita=round(float(r1["se_id_scuola"][0]), 1), alunni=int(r0["n"]),
                                   stranieri=int(s.st.sum()))
out["fonte"] = "INVALSI, microdati del campione, 5a primaria, anni scolastici 2023/24, 2024/25, 2025/26, CC BY 4.0"
json.dump(out, open(vecchio, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(json.dumps(out["divario"]))
for k, v in out["modelli"].items():
    if k.startswith("Nord"):
        print(k, v)
