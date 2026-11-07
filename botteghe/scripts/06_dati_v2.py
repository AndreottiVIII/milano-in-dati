"""Dati della pagina rifatta: docs/botteghe/data/v2_*.  Solo nomi nuovi, non tocca i file della pagina attuale.
Uso: python -I -X utf8 06_dati_v2.py <progetto abs>      (rilanciabile)
Legge botteghe/pulito/botteghe.csv, docs/medici-farmacie/data/nil.geojson (confini e residenti 2025), docs/botteghe/data/riepilogo.json (campione di controllo, OSM, Regione).
Scrive v2_botteghe.json (742 punti con via e quartiere), v2_nil.geojson (confini con conteggi), v2_riepilogo.json."""
import sys, os, re, json, unicodedata, collections
import pandas as pd
P = sys.argv[1]
D = P + "/docs/botteghe/data"
b = pd.read_csv(P + "/botteghe/pulito/botteghe.csv", dtype=str, keep_default_na=False)
b["anno"] = pd.to_numeric(b.anno_fondazione, errors="coerce")
b["disc"] = pd.to_numeric(b.discordanza_albo2024_m, errors="coerce")
b["inc"] = b.disc > 1000
old = json.load(open(D + "/riepilogo.json", encoding="utf-8"))
TIPO = json.load(open(D + "/botteghe.json", encoding="utf-8"))["tipi"]
STAT = {"si": "A", "probabile": "P", "cessata": "C", "contraddittoria": "D", "non_verificabile": "D", "cessata_probabile": "D"}
b["st"] = b.ancora_attiva.map(STAT)
b["chiusa"] = (b.stato_albo_2024 == "cessata")           # cessata secondo l'Albo 2024


def nz(s):
    s = unicodedata.normalize("NFD", str(s).lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", s)


geo = json.load(open(P + "/docs/medici-farmacie/data/nil.geojson", encoding="utf-8"))
GN = {nz(f["properties"]["n"]): f["properties"] for f in geo["features"]}
b["nilid"] = b.nil.map(lambda n: GN[nz(n)]["i"])
b["mu"] = b.nil.map(lambda n: GN[nz(n)]["mu"])
# --- vie
PART = {"di", "del", "dello", "della", "dei", "degli", "delle", "da", "de", "e", "ai", "al", "alla", "sul", "sulla", "la", "il", "lo", "le", "in", "d"}


def via_di(ind):
    v = ind.split(",")[0].strip()
    v = re.sub(r"\s+\d+[A-Za-z]?(\s*[-/].*)?$", "", v).strip()
    return v


def bella(v):
    if not v.isupper():
        return v
    out = []
    for i, w in enumerate(v.lower().split()):
        if "'" in w:
            a, c = w.split("'", 1)
            w = a + "'" + c[:1].upper() + c[1:]
            out.append(w if i else w[:1].upper() + w[1:])
            continue
        out.append(w if (w in PART and i) else w[:1].upper() + w[1:])
    return " ".join(out)


b["via"] = b.indirizzo.map(via_di)
form = collections.defaultdict(collections.Counter)
for v in b.via:
    form[nz(v)][bella(v)] += 1
VIA = {k: c.most_common(1)[0][0] for k, c in form.items()}
vkeys = sorted(VIA, key=lambda k: VIA[k].lower())
vidx = {k: i for i, k in enumerate(vkeys)}
# --- punti
pts = []
for r in b.itertuples():
    if r.inc or not r.lon:
        continue
    parts = r.indirizzo.split(",")
    ind = bella(" ".join(w if not (w.isupper() and len(w) > 2 and not w[0].isdigit()) else bella(w) for w in parts[0].split())) + ("," + ",".join(parts[1:]) if len(parts) > 1 else "")
    pts.append({"n": bella(r.nome_insegna), "ind": ind, "a": int(r.anno), "t": r.settore, "c": int(r.chiusa), "s": r.st,
                "x": round(float(r.lon), 5), "y": round(float(r.lat), 5), "q": int(r.nilid), "v": vidx[nz(r.via)]})
pts.sort(key=lambda p: (p["a"], p["n"]))
vcount = collections.Counter(p["v"] for p in pts)
vie = [{"n": VIA[k], "k": k, "m": vcount.get(i, 0)} for i, k in enumerate(vkeys)]
json.dump({"tipi": TIPO, "vie": vie, "punti": pts}, open(D + "/v2_botteghe.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
# --- confini con conteggi
cnt = collections.Counter(p["q"] for p in pts)
cc = collections.Counter(p["q"] for p in pts if p["c"])
feats = []
for f in geo["features"]:
    p = f["properties"]
    feats.append({"type": "Feature", "properties": {"i": p["i"], "n": p["n"], "mu": p["mu"], "ab": p["ab"], "b": cnt.get(p["i"], 0), "c": cc.get(p["i"], 0)}, "geometry": f["geometry"]})
json.dump({"type": "FeatureCollection", "features": feats}, open(D + "/v2_nil.geojson", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
# --- riepilogo
R = {}
R["tot"] = len(b)
R["sulla_mappa"] = len(pts)
R["incerte"] = int(b.inc.sum())
a24 = b[b.in_albo_2024 == "sì"]
R["albo24"] = {"n": len(a24), "cessate": int(a24.chiusa.sum()), "pct": round(a24.chiusa.mean() * 100, 1)}


def blocco(sub):
    s = sub.sort_values("anno")
    return {"n": len(sub), "cess": int(sub.chiusa.sum()),
            "vecchie": [{"n": bella(r.nome_insegna), "a": int(r.anno), "c": int(r.chiusa)} for r in s.head(3).itertuples()]}


dec = []
bb = b.dropna(subset=["anno"])
sp = [("1800-1899", 1800, 1899)] + [("%d-%s" % (d, ("%02d" % (d % 100 + 9)) if d < 1980 else "86"), d, d + 9) for d in range(1900, 1990, 10)]
for lab, lo, hi in sp:
    sub = bb[(bb.anno >= lo) & (bb.anno <= hi)]
    x = blocco(sub)
    x["lab"] = lab
    dec.append(x)
R["decenni"] = dec
sing = bb[bb.anno < 1800].sort_values("anno")
R["prima_1800"] = [{"n": bella(r.nome_insegna), "a": int(r.anno), "c": int(r.chiusa)} for r in sing.itertuples()]
R["cento_anni"] = int((2026 - bb.anno >= 100).sum())
R["anno_mediano"] = float(bb.anno.median())
c17 = b[b.in_albo_2017 == "sì"]
R["coorte17"] = {"n": len(c17), "attive_2024": int((c17.stato_albo_2024 == "attiva").sum()), "cessate_2024": int((c17.stato_albo_2024 == "cessata").sum()), "assenti_2024": int((c17.in_albo_2024 != "sì").sum())}
g = c17.groupby("settore").agg(n=("id", "size"), att=("stato_albo_2024", lambda x: int((x == "attiva").sum()))).reset_index()
g = g[g.n >= 10].copy()
g["perse"] = g.n - g.att
g["pct"] = (g.perse / g.n * 100).round(1)
g["tipo"] = g.settore.map(TIPO)
g = g.sort_values("n", ascending=False)
R["coorte_per_tipo"] = g[["settore", "tipo", "n", "att", "perse", "pct"]].to_dict("records")
a = a24.copy()
a["epoca"] = pd.cut(a.anno, [0, 1919, 1944, 1959, 1969, 2100], labels=["fino al 1919", "1920-44", "1945-59", "1960-69", "dal 1970"])
ep = a.groupby("epoca", observed=True).agg(n=("id", "size"), cessate=("chiusa", "sum")).reset_index()
ep["pct"] = (ep.cessate / ep.n * 100).round(1)
ep["epoca"] = ep.epoca.astype(str)
R["per_epoca"] = ep.to_dict("records")
m1 = a24[a24.mu == 1]
R["centro"] = {"n": len(m1), "cessate": int(m1.chiusa.sum())}
r_ = a24[a24.mu != 1]
R["resto"] = {"n": len(r_), "cessate": int(r_.chiusa.sum())}
R["mun1_tot"] = int(sum(cnt[f["properties"]["i"]] for f in geo["features"] if f["properties"]["mu"] == 1))
R["quartieri_zero"] = sum(1 for f in geo["features"] if cnt.get(f["properties"]["i"], 0) == 0)
R["quartieri_tot"] = len(geo["features"])
ab = sum(f["properties"]["ab"] for f in geo["features"])
R["per_10000_citta"] = round(len(pts) / ab * 1e4, 1)
R["vie_con_botteghe"] = int(sum(1 for v in vie if v["m"] > 0))
for k in ("campione", "osm_attive_pct", "osm_cessate_pct", "albo2024_indirizzo_discordante", "lombardia", "righe_edizioni", "coord_ok50",
          "regione_uscite_2019", "regione_uscite_stato_albo24", "regione26_cessata_albo", "edizioni_regione", "in_albo17", "in_albo24", "in_reg26", "in_entrambi"):
    R[k] = old[k]
json.dump(R, open(D + "/v2_riepilogo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: R[k] for k in ("tot", "sulla_mappa", "albo24", "centro", "resto", "mun1_tot", "quartieri_zero", "per_10000_citta", "vie_con_botteghe", "coorte17", "per_epoca")}, ensure_ascii=False))
print(R["prima_1800"])
print([(d["lab"], d["n"], d["cess"]) for d in dec])
print(len(vie), sorted(cnt.values())[-8:])
