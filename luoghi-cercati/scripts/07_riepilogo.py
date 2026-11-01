"""Passo 7: riepiloghi -> pulito/*.csv, pulito/riepilogo.json, pulito/mappa_nil.png (controllo, non e' la pagina).
Uso: python -I -X utf8 07_riepilogo.py <luoghi-cercati assoluto> <milano-in-dati assoluto>
Dati: Wikimedia REST pageviews per-article (all-access, agent=user, mensili e giornalieri), CC0; Wikidata CC0."""
import sys, os, json, glob, csv
import numpy as np
import pandas as pd

base, mid = sys.argv[1], sys.argv[2]
P = os.path.join(base, "pulito")
NONLUOGO = {"non_luogo", "altro", "senza_classe"}
MAIN = ["it", "en", "de", "fr", "es", "zh", "ja", "ru", "pt", "ar"]
vm = pd.read_csv(os.path.join(P, "views_mensili.csv"), sep=";")
lu = pd.read_csv(os.path.join(P, "luoghi.csv"), sep=";", dtype={"id_nil": "Int64"})
lu["luogo"] = lu.tipo == "luogo"
vm = vm.merge(lu[["qid", "tipo", "categoria", "luogo", "id_nil", "nil"]], on="qid")
vm["anno"] = vm.mese.str[:4].astype(int)
R = {}
ULT = vm.mese.max()
R["mese_ultimo"] = ULT
R["mese_primo"] = vm.mese.min()

# ---- totali
tot = vm.groupby("qid").views.sum().rename("tot").reset_index().merge(lu, on="qid").sort_values("tot", ascending=False)
L = tot[tot.luogo]
R["views_totali_luoghi"] = int(L.tot.sum())
R["views_totali_tutti_gli_elementi"] = int(tot.tot.sum())
R["n_luoghi_con_dati"] = int(len(L))
byl = vm[vm.luogo].groupby(["qid", "lingua"]).views.sum().unstack(fill_value=0)
top = L.head(100).merge(byl, left_on="qid", right_index=True, how="left")
top["tot_it"] = top["it"]
top["quota_it_%"] = (100 * top["it"] / top.tot).round(1)
cols = ["qid", "nome", "categoria", "nil", "tot", "quota_it_%"] + [c for c in MAIN if c in top.columns]
top[cols].to_csv(os.path.join(P, "top100_luoghi.csv"), sep=";", index=False)
R["views_per_tipo"] = {k: int(v) for k, v in tot.groupby("tipo").tot.sum().items()}
tot[tot.tipo != "luogo"].head(60)[["qid", "nome", "tipo", "categoria", "tot"]].to_csv(os.path.join(P, "top60_non_luoghi.csv"), sep=";", index=False)
# per lingua
rows = []
for l in MAIN:
    s = vm[(vm.luogo) & (vm.lingua == l)].groupby("qid").views.sum().sort_values(ascending=False).head(20)
    for i, (q, v) in enumerate(s.items(), 1):
        rows.append({"lingua": l, "rango": i, "qid": q, "nome": lu.set_index("qid").nome[q], "categoria": lu.set_index("qid").categoria[q], "views": int(v)})
pd.DataFrame(rows).to_csv(os.path.join(P, "top20_per_lingua.csv"), sep=";", index=False)
# per categoria
cat = vm[vm.luogo].groupby("categoria").views.sum().sort_values(ascending=False)
catn = lu[lu.luogo].groupby("categoria").size()
pd.DataFrame({"views": cat, "n_luoghi": catn, "quota_%": (100 * cat / cat.sum()).round(2)}).to_csv(os.path.join(P, "per_categoria.csv"), sep=";")
# quota lingue
ll = vm[vm.luogo].groupby("lingua").views.sum().sort_values(ascending=False)
R["quota_lingua_%"] = {k: round(100 * v / ll.sum(), 2) for k, v in ll.head(15).items()}
R["quota_it_%"] = round(100 * ll.get("it", 0) / ll.sum(), 2)
R["quota_it_en_%"] = round(100 * (ll.get("it", 0) + ll.get("en", 0)) / ll.sum(), 2)
R["quota_prime10_lingue_%"] = round(100 * ll[ll.index.isin(MAIN)].sum() / ll.sum(), 2)

# ---- it vs estero per categoria e luogo
vm["it_flag"] = np.where(vm.lingua == "it", "it", "estero")
cc = vm[vm.luogo].pivot_table(index="categoria", columns="it_flag", values="views", aggfunc="sum", fill_value=0)
cc["quota_it_%"] = (100 * cc["it"] / (cc["it"] + cc["estero"])).round(1)
cc.to_csv(os.path.join(P, "it_vs_estero_per_categoria.csv"), sep=";")
pl = vm[vm.luogo].pivot_table(index="qid", columns="it_flag", values="views", aggfunc="sum", fill_value=0)
pl["tot"] = pl["it"] + pl["estero"]
pl["quota_it_%"] = (100 * pl["it"] / pl.tot).round(1)
pl = pl.merge(lu[["qid", "nome", "categoria"]], left_index=True, right_on="qid").sort_values("tot", ascending=False)
pl.head(300).to_csv(os.path.join(P, "it_vs_estero_top300.csv"), sep=";", index=False)

# ---- serie mensile e annuale
sm = vm[vm.luogo].groupby(["mese", "it_flag"]).views.sum().unstack(fill_value=0)
sm["tot"] = sm.sum(axis=1)
sm.to_csv(os.path.join(P, "serie_mensile_totale.csv"), sep=";")
sa = vm[vm.luogo].groupby(["anno", "it_flag"]).views.sum().unstack(fill_value=0)
sa["tot"] = sa.sum(axis=1)
sa["mesi_nei_dati"] = vm[vm.luogo].groupby("anno").mese.nunique()
sa["indice_2019=100"] = (100 * sa.tot / sa.loc[2019, "tot"]).round(1)
sa["it_indice_2019=100"] = (100 * sa["it"] / sa.loc[2019, "it"]).round(1)
sa["estero_indice_2019=100"] = (100 * sa["estero"] / sa.loc[2019, "estero"]).round(1)
sa.to_csv(os.path.join(P, "serie_annuale_totale.csv"), sep=";")
# riferimento: tutta Wikipedia per lingua (se scaricato)
agg = {}
for f in glob.glob(os.path.join(base, "raw", "aggregato_wikipedia", "*.json")):
    d = json.load(open(f))
    agg[d["progetto"].split(".")[0]] = {i["timestamp"][:4] + "-" + i["timestamp"][4:6]: i["views"] for i in d["items"]}
if agg:
    rows = []
    for l, s in agg.items():
        m = vm[(vm.luogo) & (vm.lingua == l)].groupby("mese").views.sum()
        for mese_, v in s.items():
            rows.append({"lingua": l, "mese": mese_, "wikipedia_totale": v, "luoghi_milano": int(m.get(mese_, 0))})
    ag = pd.DataFrame(rows)
    ag["anno"] = ag.mese.str[:4].astype(int)
    ag["quota_per_milione"] = 1e6 * ag.luoghi_milano / ag.wikipedia_totale
    ag.to_csv(os.path.join(P, "luoghi_vs_wikipedia_mensile.csv"), sep=";", index=False)
    ya = ag.groupby(["lingua", "anno"]).agg(w=("wikipedia_totale", "sum"), m=("luoghi_milano", "sum")).reset_index()
    ya["per_milione"] = (1e6 * ya.m / ya.w).round(2)
    ya.to_csv(os.path.join(P, "luoghi_vs_wikipedia_annuale.csv"), sep=";", index=False)

# ---- picchi mensili: totale (tutte le lingue) mese vs mediana dei 12 mesi attorno (+-6, escluso il mese)
mp = vm[vm.luogo].groupby(["qid", "mese"]).views.sum().unstack(fill_value=0)
allm = sorted(vm.mese.unique())
mp = mp.reindex(columns=allm, fill_value=0)
pk = []
arr = mp.values
for i, q in enumerate(mp.index):
    a = arr[i]
    for j in range(len(allm)):
        lo, hi = max(0, j - 6), min(len(allm), j + 7)
        ctx = np.concatenate([a[lo:j], a[j + 1:hi]])
        med = np.median(ctx) if len(ctx) else 0
        if a[j] >= 5000 and a[j] >= 3 * max(med, 1):
            pk.append({"qid": q, "mese": allm[j], "views": int(a[j]), "mediana_6+6_mesi": float(med), "eccesso": int(a[j] - med), "rapporto": round(a[j] / max(med, 1), 1)})
pk = pd.DataFrame(pk).merge(lu[["qid", "nome", "categoria"]], on="qid").sort_values("eccesso", ascending=False)
pk.to_csv(os.path.join(P, "picchi_mensili.csv"), sep=";", index=False)

# ---- picchi giornalieri (top luoghi, it/en)
dp = []
for f in glob.glob(os.path.join(base, "raw", "pageviews_giornalieri", "*", "*.json")):
    d = json.load(open(f, encoding="utf8"))
    if not d["items"]:
        continue
    s = pd.Series({i["timestamp"][:8]: i["views"] for i in d["items"]})
    s.index = pd.to_datetime(s.index, format="%Y%m%d")
    s = s.asfreq("D", fill_value=0)
    med = s.shift(1).rolling(28, min_periods=14).median()
    ok = (s >= 2000) & (s >= 4 * med.clip(lower=1))
    for dt in s[ok].index:
        dp.append({"qid": d["qid"], "lingua": d["progetto"].split(".")[0], "data": dt.strftime("%Y-%m-%d"), "views": int(s[dt]), "mediana_28g_prima": float(med[dt]), "eccesso": int(s[dt] - med[dt])})
if dp:
    dp = pd.DataFrame(dp).merge(lu[["qid", "nome"]], on="qid").sort_values("eccesso", ascending=False)
    dp.to_csv(os.path.join(P, "picchi_giornalieri.csv"), sep=";", index=False)

# ---- NIL
vn = vm[vm.luogo & vm.id_nil.notna()].groupby(["id_nil", "nil"]).views.sum().rename("views").reset_index()
nl = lu[lu.luogo & lu.id_nil.notna()].groupby("id_nil").size().rename("n_luoghi")
topn = tot[tot.luogo & tot.id_nil.notna()].sort_values("tot", ascending=False).groupby("id_nil").head(1).set_index("id_nil").nome.rename("luogo_piu_visto")
vn = vn.merge(nl, left_on="id_nil", right_index=True).merge(topn, left_on="id_nil", right_index=True)
g = json.load(open(os.path.join(mid, "citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson"), encoding="utf8"))
ar = {f["properties"]["ID_NIL"]: f["properties"]["Shape_Area"] / 1e6 for f in g["features"]}
vn["km2"] = vn.id_nil.map(ar).round(3)
vn["quota_%"] = (100 * vn.views / vn.views.sum()).round(2)
vn = vn.sort_values("views", ascending=False)
vn.to_csv(os.path.join(P, "views_per_nil.csv"), sep=";", index=False)
R["nil_top5"] = vn.head(5)[["nil", "views", "quota_%"]].to_dict("records")
R["nil_senza_assegnazione_luoghi"] = int((lu.luogo & lu.id_nil.isna()).sum())
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP
    from matplotlib.collections import PatchCollection
    fig, ax = plt.subplots(figsize=(8, 9))
    val = vn.set_index("id_nil").views
    mx = np.log10(val.max())
    for f in g["features"]:
        i = f["properties"]["ID_NIL"]
        v = val.get(i, 0)
        c = plt.cm.viridis(np.log10(v + 1) / mx) if v else (0.9, 0.9, 0.9, 1)
        geoms = f["geometry"]["coordinates"] if f["geometry"]["type"] == "MultiPolygon" else [f["geometry"]["coordinates"]]
        for poly in geoms:
            ax.add_patch(MP(np.array(poly[0]), closed=True, fc=c, ec="white", lw=0.4))
    ax.autoscale_view()
    ax.set_aspect(1 / np.cos(np.radians(45.46)))
    ax.set_title("Visualizzazioni Wikipedia dei luoghi, per NIL (scala log), lug 2015 - %s" % ULT)
    ax.axis("off")
    fig.savefig(os.path.join(P, "mappa_nil.png"), dpi=110, bbox_inches="tight")
except Exception as e:
    R["mappa_errore"] = str(e)
json.dump(R, open(os.path.join(P, "riepilogo.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps(R, ensure_ascii=False, indent=1))
