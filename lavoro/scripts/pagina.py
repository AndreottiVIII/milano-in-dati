"""Lavoro, passo 4: costruisce i dati della pagina docs/lavoro/ (ripetibile).
Uso: python -I -X utf8 pagina.py <milano-in-dati> <docs>/lavoro
Input : lavoro/out/lavoro_NIL.csv, lavoro_comune.csv, analisi.json (passi 2 e 3)
        docs/censimenti/data/nil.geojson (confini dei NIL gia' semplificati dal filone censimenti)
        quartieri-che-cambiano/out/indicatori_nil.csv (reddito_2024, quota_civici_cap_instabili)
        censimenti/pulito/nil_2021_anagrafica.csv (nomi dei NIL)
Output: <docs>/lavoro/data/dati.json, nil.geojson, riepilogo.json, nil_lavoro.csv, comune_lavoro.csv
        <docs>/lavoro/index.html (copia di scripts/pagina_template.html: il testo non contiene numeri scritti a mano, li legge dai json)
"""
import sys, os, json, shutil
import numpy as np
import pandas as pd

root, dst = sys.argv[1], sys.argv[2]
O = root + "/lavoro/out/"
YEARS = [1991, 2001, 2011, 2021, 2023]
os.makedirs(dst + "/data", exist_ok=True)

n = pd.read_csv(O + "lavoro_NIL.csv")
c = pd.read_csv(O + "lavoro_comune.csv")
ana = pd.read_csv(root + "/censimenti/pulito/nil_2021_anagrafica.csv")
inc = pd.read_csv(root + "/quartieri-che-cambiano/out/indicatori_nil.csv")[["id_nil", "reddito_2024", "quota_civici_cap_instabili"]].rename(columns={"id_nil": "nil"})
inc["nil"] = inc.nil.astype(int)
R = json.load(open(O + "analisi.json", encoding="utf-8"))


def r1(v, d=1):
    return None if v is None or (isinstance(v, float) and np.isnan(v)) else round(float(v), d)


def series(g, col, d=1):
    s = g.set_index("anno")[col]
    return [r1(s.get(y), d) for y in YEARS]


MAPC = dict(occ="tasso_occ", occ_f="tasso_occ_f", occ_m="tasso_occ_m", gap="gap_occ_mf", dis="tasso_disocc", dis_f="tasso_disocc_f", dis_m="tasso_disocc_m",
            stu="studenti_100", pen="pensionati_100", cas="casalinghe_100_donne", alt="altri_100")
rows = []
for nid, g in n.groupby("nil"):
    g = g.sort_values("anno")
    first = g.iloc[0]
    o = dict(i=int(nid), n=str(first.nil_nome), mun=int(first.municipio_prevalente), rob=bool(first.robusto),
             pop=[int(g.set_index("anno")["pop"][y]) for y in YEARS], p=[int(g.set_index("anno")["p1564"][y]) for y in YEARS])
    for k, col in MAPC.items():
        o[k] = series(g, col)
    s = g.set_index("anno")
    for k, col in [("d_occ_f", "tasso_occ_f"), ("d_occ", "tasso_occ"), ("d_occ_m", "tasso_occ_m"), ("d_dis", "tasso_disocc")]:
        a, b = s[col].get(1991), s[col].get(2011)
        o[k] = r1(b - a) if o["rob"] and pd.notna(a) and pd.notna(b) else None
    rd = inc[inc.nil == nid]
    o["rd"] = r1(rd.reddito_2024.iloc[0], 0) if len(rd) else None
    o["inst"] = bool(rd.quota_civici_cap_instabili.iloc[0] > 0.5) if len(rd) else None
    rows.append(o)

cm = {}
for _, r in c.iterrows():
    y = int(r.anno)
    cm[y] = {k: (None if pd.isna(r[k]) else (int(r[k]) if k in ("pop", "p1564", "occ", "occ_m", "occ_f", "fl", "cerca", "stu", "rit", "cas", "pop_f") else round(float(r[k]), 2)))
             for k in ["pop", "pop_f", "p1564", "occ", "occ_m", "occ_f", "fl", "cerca", "stu", "rit", "cas", "tasso_occ", "tasso_occ_m", "tasso_occ_f", "gap_occ_mf",
                       "tasso_disocc", "tasso_disocc_m", "tasso_disocc_f", "studenti_100", "pensionati_100", "casalinghe_100", "casalinghe_100_donne", "altri_100", "occupati_100"]}
dati = dict(anni=YEARS, comune=cm, nil=rows)
json.dump(dati, open(dst + "/data/dati.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# confini: dal filone censimenti (stesse geometrie), con nome
gj = json.load(open(root + "/docs/censimenti/data/nil.geojson", encoding="utf-8"))
nm = dict(zip(ana.nil, ana.nil_nome))
assert len(gj["features"]) == 88
for f in gj["features"]:
    i = int(f["properties"]["i"])
    f["properties"] = dict(i=i, n=nm[i])
json.dump(gj, open(dst + "/data/nil.geojson", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

R["generato_da"] = "lavoro/scripts/pagina.py"
json.dump(R, open(dst + "/data/riepilogo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

cols = ["anno", "nil", "nil_nome", "municipio_prevalente", "robusto", "pop", "p1564", "occ", "occ_m", "occ_f", "fl", "cerca", "stu", "rit", "cas",
        "tasso_occ", "tasso_occ_m", "tasso_occ_f", "gap_occ_mf", "tasso_disocc", "tasso_disocc_m", "tasso_disocc_f", "studenti_100", "pensionati_100", "casalinghe_100_donne", "altri_100"]
out = n[cols].merge(inc.rename(columns={"reddito_2024": "reddito_medio_2024_euro2025"}), on="nil", how="left")
out.round(2).to_csv(dst + "/data/nil_lavoro.csv", index=False)
c.round(2).to_csv(dst + "/data/comune_lavoro.csv", index=False)
shutil.copyfile(root + "/lavoro/scripts/pagina_template.html", dst + "/index.html")
for f in sorted(os.listdir(dst + "/data")):
    print(f, os.path.getsize(dst + "/data/" + f))
