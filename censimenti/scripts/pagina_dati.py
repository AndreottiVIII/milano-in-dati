"""Fase 3: costruisce la pagina docs/censimenti/ (index.html + data/) dai file ripuliti in pulito/.
Uso: python -I scripts\\pagina_dati.py
Input : pulito/*.csv (fase 1 e 2), pulito/geometrie/sezioni_2021_Milano.geojson, scripts/pagina_template.html
Output: docs/censimenti/index.html, docs/censimenti/data/nil.geojson, docs/censimenti/data/dati.json
Tutti i numeri della pagina escono da questi file: nessun numero e' scritto a mano nel modello,
tranne la data delle fonti e le cifre dei decreti (verificate su Normattiva il 30/10/2026).
"""
import json
import math
import os
import sys

import pandas as pd
from pyproj import Transformer
from shapely.geometry import mapping, shape
import numpy as np
import shapely
from shapely.ops import unary_union

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                       # .../censimenti
P = os.path.join(ROOT, "pulito")
OUT = os.path.join(os.path.dirname(os.path.dirname(ROOT)), "milano-in-dati", "docs", "censimenti") \
    if False else os.path.join(os.path.dirname(ROOT), "docs", "censimenti")
OUTD = os.path.join(OUT, "data")
os.makedirs(OUTD, exist_ok=True)

YEARS = [1991, 2001, 2011, 2021, 2023]


def rd(name):
    return pd.read_csv(os.path.join(P, name), encoding="utf-8")


# ---------- formattazione italiana ----------
def sw(s):
    return s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def n0(x):
    return sw(f"{x:,.0f}")


def n1(x):
    return sw(f"{x:,.1f}")


def n2(x):
    return sw(f"{x:,.2f}")


def s1(x):
    return ("+" if x > 0 else "−" if x < 0 else "") + n1(abs(x))


def s0(x):
    return ("+" if x > 0 else "−" if x < 0 else "") + n0(abs(x))


def r(x, d=2):
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), d)


# ---------- 1. geometria dei NIL (unione delle sezioni 2021) ----------
ana = rd("nil_2021_anagrafica.csv")
tr = Transformer.from_crs(32632, 4326, always_xy=True).transform
feats = json.load(open(os.path.join(P, "geometrie", "sezioni_2021_Milano.geojson"), encoding="utf-8"))["features"]
by = {}
for f in feats:
    k = int(f["properties"]["COM_ASC2"])
    if k == 0:
        continue
    by.setdefault(k, []).append(shape(f["geometry"]).buffer(0))
gj = {"type": "FeatureCollection", "features": []}
for nil in ana.nil:
    g = unary_union(by[15146000 + int(nil)]).simplify(4, preserve_topology=True)
    g = shapely.transform(g, lambda c: np.column_stack(tr(c[:, 0], c[:, 1])))
    m = mapping(g)

    def rc(c):
        return [round(c[0], 5), round(c[1], 5)] if isinstance(c[0], float) else [rc(x) for x in c]
    m = {"type": m["type"], "coordinates": rc(m["coordinates"])}
    gj["features"].append({"type": "Feature", "properties": {"i": int(nil)}, "geometry": m})
json.dump(gj, open(os.path.join(OUTD, "nil.geojson"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ---------- 2. indicatori per NIL ----------
ind = rd("indicatori_NIL.csv")
var = rd("variazioni_NIL_1991_2023.csv")
rob = dict(zip(var.nil, var.robusto))
d91 = dict(zip(var.nil, var.diff_area_1991_pct))
d01 = dict(zip(var.nil, var.diff_area_2001_pct))
COLS = {"pop": "pop", "eta": "eta_media_classi", "p65": "quota_65p", "str": "quota_stranieri",
        "lau": "quota_laureati_su_base", "f1": "quota_famiglie_1_comp", "fm": "famiglie_comp_medio_approx"}
DEC = {"pop": 0, "eta": 2, "p65": 2, "str": 2, "lau": 2, "f1": 2, "fm": 3}
nil_out = []
for _, a in ana.iterrows():
    n = int(a.nil)
    sub = ind[ind.nil == n].set_index("anno")
    v = {}
    for k, c in COLS.items():
        v[k] = [r(sub.loc[y, c], DEC[k]) for y in YEARS]
    p0 = v["pop"][0]
    v["var"] = [0.0 if y == 1991 else (r((v["pop"][i] / p0 - 1) * 100, 2) if p0 else None) for i, y in enumerate(YEARS)]
    mot = []
    if v["pop"][0] < 2000 or v["pop"][4] < 2000:
        mot.append("ha meno di 2.000 residenti nel 1991 o nel 2023")
    if d91[n] >= 5 or d01[n] >= 5:
        mot.append("il suo perimetro nei censimenti 1991 e 2001 si ricostruisce in modo incerto "
                   "(assegnare le sezioni intere o ripartirle per area cambia la popolazione di oltre il 5%)")
    ok = bool(rob[n])
    assert ok == (not mot), n
    nil_out.append({"i": n, "n": a.nil_nome, "m": int(a.municipio_prevalente), "a": r(a.area_km2, 2),
                    "ok": ok, "mot": "; ".join(mot), "v": v})
byid = {x["i"]: x for x in nil_out}
good = [x for x in nil_out if x["ok"]]
bad = [x for x in nil_out if not x["ok"]]

# ---------- 3. comune ----------
com = rd("indicatori_comune.csv").set_index("anno")
CO = {k: [r(com.loc[y, c], DEC[k]) for y in YEARS] for k, c in COLS.items()}
CO["var"] = [r((p / CO["pop"][0] - 1) * 100, 2) for p in CO["pop"]]
CO["iv"] = [r(com.loc[y, "indice_vecchiaia"], 1) for y in YEARS]
CO["stran_n"] = [int(com.loc[y, "stran"]) for y in YEARS]
CO["fam_n"] = [int(com.loc[y, "fam"]) for y in YEARS]
CO["fam1_n"] = [int(com.loc[y, "fam1"]) for y in YEARS]
CO["ita_n"] = [int(com.loc[y, "pop"] - com.loc[y, "stran"]) for y in YEARS]

# ---------- 4. classifiche ----------
def rank(key, f, rev=True, n=10, pool=None):
    pool = pool or good
    out = sorted(pool, key=f, reverse=rev)[:n]
    return [{"i": x["i"]} for x in out]


delta_eta = lambda x: x["v"]["eta"][4] - x["v"]["eta"][0]
delta_str = lambda x: x["v"]["str"][4] - x["v"]["str"][0]
R = {
    "invecchiano": [x["i"] for x in sorted(good, key=delta_eta, reverse=True)[:10]],
    "ringiovaniscono": [x["i"] for x in sorted(good, key=delta_eta) if delta_eta(x) < 0],
    "str_top": [x["i"] for x in sorted(good, key=lambda x: x["v"]["str"][4], reverse=True)[:10]],
    "str_aumento": [x["i"] for x in sorted(good, key=delta_str, reverse=True)[:10]],
    "str_min": [x["i"] for x in sorted(good, key=lambda x: x["v"]["str"][4])[:5]],
}
n_ring = len(R["ringiovaniscono"])
str23 = [x["v"]["str"][4] for x in good]
str91 = [x["v"]["str"][0] for x in good]

# ---------- 5. cittadinanze ----------
cit = rd("cittadinanze_comune.csv")
RENAME = {"Cinese, Repubblica Popolare": "Cina", "Jugoslavia, Rep. Federale": "Jugoslavia", "Sri Lanka (Ceylon)": "Sri Lanka",
          "Peru'": "Perù"}
CIT = {}
for y, g in cit.groupby("anno"):
    CIT[int(y)] = [{"n": RENAME.get(c, c), "p": int(p), "q": float(q)} for c, p, q in zip(g.cittadinanza, g.persone, g.quota_su_stranieri)]

# ---------- 6. storia e annuale ----------
ser = rd("serie_milano_1861_2023.csv")
STORIA = []
for _, s in ser.iterrows():
    STORIA.append({"y": int(s.anno), "e": r(s.pop_confini_epoca, 0), "k": r(s.superficie_km2_epoca, 1),
                   "r": r(s.pop_confini_1991_ricostruita_ISTAT, 0), "a": r(s.pop_confini_attuali_somma_sezioni, 0)})
ann = rd("annuale_milano_2018_2025.csv")
ANN = []
for _, a in ann.iterrows():
    ANN.append({"y": int(a.anno_fine_periodo), "pop": int(a.popolazione), "str": r(a.quota_stranieri, 2),
                "eta": r(a.eta_media, 2), "iv": r(a.indice_vecchiaia, 1),
                "nati": r(a.nati, 0), "morti": r(a.morti, 0), "nat": r(a.saldo_naturale, 0),
                "mig": r(a.saldo_migratorio_totale, 0), "agg": r(a.aggiustamento_statistico, 0),
                "ini": r(a.pop_inizio, 0)})
for a in ANN:                                 # controllo: inizio + naturale + migratorio + aggiustamento = fine
    if a["agg"] is not None and a["ini"] is not None:
        assert abs(a["ini"] + a["nat"] + a["mig"] + a["agg"] - a["pop"]) < 1, a
ser_ann = rd("serie_annuale_milano_1880_2025_flag.csv").set_index("anno")
salto23 = {"da": int(ser_ann.loc[1922, "popolazione_calcolata"]), "a": int(ser_ann.loc[1923, "popolazione_calcolata"]),
           "d": int(ser_ann.loc[1923, "var_assoluta"]), "p": float(ser_ann.loc[1923, "var_pct"])}
assert salto23["d"] == salto23["a"] - salto23["da"]
conf = rd("variazioni_confini_milano.csv")
COPERT = rd("copertura_raccordo.csv")

# ---------- 7. cifre del testo ----------
c = CO
T = {}
T["POP91"], T["POP23"] = n0(c["pop"][0]), n0(c["pop"][4])
T["POPVAR"] = n1(c["var"][4]).replace("−", "-")
T["ITA_MENO"] = n0(c["ita_n"][0] - c["ita_n"][4])
T["STR_PIU"] = n0(c["stran_n"][4] - c["stran_n"][0])
T["STR91"], T["STR23"] = n0(c["stran_n"][0]), n0(c["stran_n"][4])
T["QSTR91"], T["QSTR23"] = n1(c["str"][0]), n1(c["str"][4])
T["FAM_PIU"] = n0(c["fam_n"][4] - c["fam_n"][0])
T["FAM91"], T["FAM23"] = n0(c["fam_n"][0]), n0(c["fam_n"][4])
T["F1_91"], T["F1_23"] = n1(c["f1"][0]), n1(c["f1"][4])
T["FM91"], T["FM23"] = n2(c["fm"][0]), n2(c["fm"][4])
T["SENZA_DIMORA23"] = n0(float(COPERT[COPERT.anno == 2023].pop_sezioni_speciali.iloc[0]))
T["N_BUONI"], T["N_ESCLUSI"] = str(len(good)), str(len(bad))
T["POP_ESCL91"] = n0(sum(x["v"]["pop"][0] for x in bad))
T["POP_ESCL23"] = n0(sum(x["v"]["pop"][4] for x in bad))
T["ETA_91"], T["ETA_01"], T["ETA_11"], T["ETA_21"], T["ETA_23"] = [n1(x) for x in c["eta"]]
T["IV_91"], T["IV_01"], T["IV_11"], T["IV_21"], T["IV_23"] = [n0(x) for x in c["iv"]]
a25 = [a for a in ANN if a["y"] == 2024][0]       # 31 dicembre 2024 (= 1 gennaio 2025)
a26 = [a for a in ANN if a["y"] == 2025][0]       # 31 dicembre 2025 (= 1 gennaio 2026)
T["IV_25"], T["IV_26"] = n1(a25["iv"]), n1(a26["iv"])
T["Q65_91"], T["Q65_01"], T["Q65_11"], T["Q65_23"] = n1(c["p65"][0]), n1(c["p65"][1]), n1(c["p65"][2]), n1(c["p65"][4])


def nm(i):
    return byid[i]["n"]


def eta_txt(i):
    x = byid[i]
    return f"<b>{nm(i)}</b> da {n1(x['v']['eta'][0])} a {n1(x['v']['eta'][4])} anni ({s1(delta_eta(x))})"


inv = R["invecchiano"]
T["INV_TXT"] = "; ".join(eta_txt(i) for i in inv[:4])
T["RING_N"] = str(n_ring)
T["RING_TXT"] = "; ".join(eta_txt(i) for i in R["ringiovaniscono"])
vecchio = max(good, key=lambda x: x["v"]["eta"][4])
giovane = min(good, key=lambda x: x["v"]["eta"][4])
T["VECCHIO"] = f"<b>{vecchio['n']}</b> ({n1(vecchio['v']['eta'][4])} anni, indice di vecchiaia {n0(ind[(ind.nil==vecchio['i'])&(ind.anno==2023)].indice_vecchiaia.iloc[0])})"
T["GIOVANE"] = f"<b>{giovane['n']}</b> ({n1(giovane['v']['eta'][4])} anni, indice di vecchiaia {n0(ind[(ind.nil==giovane['i'])&(ind.anno==2023)].indice_vecchiaia.iloc[0])})"
T["N_SOPRA25"] = str(sum(1 for v in str23 if v > 25))
T["N_SOTTO10"] = str(sum(1 for v in str23 if v < 10))
T["MAX_STR91"] = n1(max(str91))
top = byid[R["str_top"][0]]
T["STR_TOP_TXT"] = ", ".join(f"<b>{byid[i]['n']}</b> {n1(byid[i]['v']['str'][4])}%" for i in R["str_top"][:5])
aum = byid[R["str_aumento"][0]]
T["STR_AUM_TXT"] = f"<b>{aum['n']}</b> dal {n1(aum['v']['str'][0])}% al {n1(aum['v']['str'][4])}% ({s1(delta_str(aum))} punti)"
mn = byid[R["str_min"][0]]
T["STR_MIN_TXT"] = f"<b>{mn['n']}</b> (dal {n1(mn['v']['str'][0])}% al {n1(mn['v']['str'][4])}%)"
eg91 = [x for x in CIT[1991] if x["n"] == "Egitto"][0]
eg23 = [x for x in CIT[2023] if x["n"] == "Egitto"][0]
ph11 = [x for x in CIT[2011] if x["n"] == "Filippine"][0]
ph23 = [x for x in CIT[2023] if x["n"] == "Filippine"][0]
T["EG_VOLTE"] = n0(round(eg23["p"] / eg91["p"]))
T["EG91"], T["EG23"], T["EGQ23"] = n0(eg91["p"]), n0(eg23["p"]), n1(eg23["q"])
T["PH_VAR"] = n0(round((ph23["p"] / ph11["p"] - 1) * 100))
T["PH11"], T["PH23"] = n0(ph11["p"]), n0(ph23["p"])
T["STR26"] = n1(a26["str"])
st = {s["y"]: s for s in STORIA}
T["POP1861"] = n0(st[1861]["e"])
T["POP1971"] = n0(st[1971]["e"])
T["POP2011"] = n0(st[2011]["e"])
T["PERSI_71_11"] = n0(st[1971]["e"] - st[2011]["e"])
T["PERSI_71_11P"] = n1((1 - st[2011]["e"] / st[1971]["e"]) * 100)
T["RECUP_11_23"] = n0(c["pop"][4] - st[2011]["e"])
T["RECUP_11_23P"] = n1((c["pop"][4] / st[2011]["e"] - 1) * 100)
T["IDX23"] = n0(round(c["pop"][4] / st[1861]["r"] * 100))
T["IDX71"] = n0(round(st[1971]["r"] / st[1861]["r"] * 100))
T["R1861"] = n0(st[1861]["r"])
T["R1921"], T["E1921"] = n0(st[1921]["r"]), n0(st[1921]["e"])
T["DIFF1921"] = n0(st[1921]["r"] - st[1921]["e"])
T["S1871"], T["S1881"] = n1(st[1871]["k"]), n1(st[1881]["k"])
T["S1921"], T["S1931"] = n1(st[1921]["k"]), n1(st[1931]["k"])
T["E1871"], T["E1881"], T["E1931"] = n0(st[1871]["e"]), n0(st[1881]["e"]), n0(st[1931]["e"])
T["SALTO23_DA"], T["SALTO23_A"] = n0(salto23["da"]), n0(salto23["a"])
T["SALTO23_D"], T["SALTO23_P"] = n0(salto23["d"]), n1(salto23["p"])
adj = {a["y"]: a for a in ANN}
T["AGG2020"], T["AGG2021"] = n0(-adj[2020]["agg"]), n0(-adj[2021]["agg"])
tot_calo = adj[2019]["pop"] - adj[2021]["pop"]
real = (adj[2020]["nat"] + adj[2020]["mig"]) + (adj[2021]["nat"] + adj[2021]["mig"])
T["POP2019"], T["POP2021"] = n0(adj[2019]["pop"]), n0(adj[2021]["pop"])
T["CALO_1921"] = n0(tot_calo)
T["REALI_1921"] = s0(real)
T["AGG_1921"] = n0(-(adj[2020]["agg"] + adj[2021]["agg"]))
d5 = pd.read_csv(os.path.join(ROOT, "raw", "comune_annuale_nil", "ds205_dati_quartieri_2011_2024_.csv"), sep=";", encoding="utf-8")
tot5 = d5.groupby("Anno")["Totale"].sum()
T["DS205_2011"], T["DS205_2023"] = n1((tot5[2011] / c["pop"][2] - 1) * 100), n1((tot5[2023] / c["pop"][4] - 1) * 100)
# righe della tabella di copertura
rows = []
for _, q in COPERT.iterrows():
    rows.append(f"<tr><td>{int(q.anno)}</td><td class=\"r\">{n0(q.sezioni)}</td><td class=\"r\">{n2(q.quota_collocata*100)}%</td>"
                f"<td class=\"r\">{n0(q.pop_sezioni_speciali)}</td><td class=\"r\">{n1(q.quota_pop_purezza_lt_90*100)}%</td></tr>")
T["TAB_COPERTURA"] = "\n".join(rows)

# ---------- 8. dati.json ----------
dati = {"anni": YEARS, "nil": nil_out, "comune": CO, "rank": R, "cit": {str(k): v for k, v in CIT.items()},
        "storia": STORIA, "annuale": ANN, "salto23": salto23}
json.dump(dati, open(os.path.join(OUTD, "dati.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# ---------- 9. html ----------
html = open(os.path.join(HERE, "pagina_template.html"), encoding="utf-8").read()
for k, v in T.items():
    html = html.replace("{{" + k + "}}", v)
left = [w for w in __import__("re").findall(r"\{\{[A-Z0-9_]+\}\}", html)]
assert not left, left
open(os.path.join(OUT, "index.html"), "w", encoding="utf-8").write(html)
sz = sum(os.path.getsize(os.path.join(OUTD, f)) for f in os.listdir(OUTD))
print("ok: NIL", len(nil_out), "buoni", len(good), "esclusi", len(bad), "| dati", sz, "byte")
