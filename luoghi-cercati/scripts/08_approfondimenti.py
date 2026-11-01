"""Passo 8: approfondimenti citati in NOTE.md -> pulito/approfondimenti.json + redirect_it_riepilogo.csv + serie_top10_mensile.csv
 - effetto Notre-Dame (aprile 2019) sul Duomo; - Covid 2020 e ripresa; - andamento senza lo stadio; - stagionalita';
 - luoghi piu' "stranieri" / piu' "italiani" (almeno 200.000 views); - controllo redirect it.wikipedia.
Uso: python -I -X utf8 08_approfondimenti.py <luoghi-cercati assoluto>"""
import sys, os, json, glob
import pandas as pd
import numpy as np

base = sys.argv[1]
P = os.path.join(base, "pulito")
vm = pd.read_csv(os.path.join(P, "views_mensili.csv"), sep=";")
lu = pd.read_csv(os.path.join(P, "luoghi.csv"), sep=";")
tl = pd.read_csv(os.path.join(P, "totali_luogo.csv"), sep=";")
luogo = set(lu[lu.tipo == "luogo"].qid)
v = vm[vm.qid.isin(luogo)].copy()
v["it"] = np.where(v.lingua == "it", "it", "estero")
R = {}
# --- Notre-Dame: Duomo di Milano (Q18068), mesi attorno ad aprile 2019
d = vm[vm.qid == "Q18068"].pivot_table(index="mese", columns="lingua", values="views", aggfunc="sum", fill_value=0)
d["tot"] = d.sum(axis=1)
R["duomo_mesi_2019"] = {m: {"tot": int(d.loc[m, "tot"]), "it": int(d.loc[m].get("it", 0)), "en": int(d.loc[m].get("en", 0))} for m in ["2019-02", "2019-03", "2019-04", "2019-05", "2019-06"]}
R["duomo_mesi_2018"] = {m: int(d.loc[m, "tot"]) for m in ["2018-03", "2018-04", "2018-05"]}
# --- Covid: totale luoghi, mesi 2019 vs 2020
sm = v.groupby(["mese", "it"]).views.sum().unstack(fill_value=0)
sm["tot"] = sm.sum(axis=1)
cov = {}
for m in ["03", "04", "05", "06", "07", "08"]:
    a, b = sm.loc["2019-" + m], sm.loc["2020-" + m]
    cov[m] = {"tot_2019": int(a.tot), "tot_2020": int(b.tot), "var_%": round(100 * (b.tot / a.tot - 1), 1),
              "it_var_%": round(100 * (b["it"] / a["it"] - 1), 1), "estero_var_%": round(100 * (b["estero"] / a["estero"] - 1), 1)}
R["covid_2020_vs_2019_per_mese"] = cov
# ripresa: primo mese (da marzo 2020) in cui il totale e' >= stesso mese del 2019 per 3 mesi di fila (2019 = ultimo anno "normale")
def ripresa(col):
    mm = [m for m in sorted(sm.index) if m >= "2020-03" and m <= "2026-10"]
    ok = {}
    for m in mm:
        ref = "2019" + m[4:]
        ok[m] = sm.loc[m, col] >= sm.loc[ref, col]
    for i, m in enumerate(mm[:-2]):
        if ok[m] and ok[mm[i + 1]] and ok[mm[i + 2]]:
            return m
    return None
R["ripresa_primo_mese_3_di_fila_>=_stesso_mese_2019"] = {"tot": ripresa("tot"), "it": ripresa("it"), "estero": ripresa("estero")}
R["rapporto_su_2019_mesi_selezionati"] = {m: round(float(sm.loc[m, "tot"] / sm.loc["2019" + m[4:], "tot"]), 2) for m in ["2020-03", "2020-06", "2020-12", "2021-06", "2021-12", "2022-06", "2022-12", "2023-06", "2023-12", "2024-06", "2024-12", "2025-06", "2025-12", "2026-06", "2026-10"] if m in sm.index}
# Notre-Dame: eccesso giornaliero sul Duomo (it, en) 15-21 aprile 2019 sopra la mediana 1-14 aprile
ex = {}
for lang in ("it", "en"):
    dd = json.load(open(os.path.join(base, "raw", "pageviews_giornalieri", lang, "Q18068.json"), encoding="utf8"))
    sd = {i["timestamp"][:8]: i["views"] for i in dd["items"]}
    bs = float(np.median([x for k, x in sd.items() if "20190401" <= k <= "20190414"]))
    ex[lang] = {"mediana_1_14_aprile": bs, "15_aprile": sd["20190415"], "16_aprile": sd["20190416"],
                "eccesso_15_21_aprile": int(sum(max(0, x - bs) for k, x in sd.items() if "20190415" <= k <= "20190421"))}
R["notre_dame_duomo_giornaliero"] = ex
# --- senza stadio (Q133566)
s2 = v[v.qid != "Q133566"].groupby("anno" if "anno" in v else v.mese.str[:4]).views.sum()
s1 = v[v.qid == "Q133566"].groupby(v.mese.str[:4]).views.sum()
R["serie_annuale_senza_meazza"] = {k: int(x) for k, x in s2.items()}
R["serie_annuale_meazza"] = {k: int(x) for k, x in s1.items()}
# --- estero/it per luogo (>=200.000)
t = tl[(tl.tipo == "luogo") & (tl.views_totali >= 200000)].sort_values("quota_italiano_%")
R["piu_stranieri_>=200k"] = t.head(12)[["nome", "views_totali", "quota_italiano_%"]].to_dict("records")
R["piu_italiani_>=200k"] = t.tail(12)[["nome", "views_totali", "quota_italiano_%"]].to_dict("records")
# --- stagionalita' (primi 20 luoghi, anni 2016-2019, quota per mese di calendario)
top20 = tl[tl.tipo == "luogo"].head(20).qid
x = vm[vm.qid.isin(top20) & vm.mese.str[:4].isin(["2016", "2017", "2018", "2019"])].copy()
x["m"] = x.mese.str[5:]
sea = x.groupby("m").views.sum()
R["stagionalita_top20_2016_2019_quota_%"] = {k: round(100 * s / sea.sum(), 2) for k, s in sea.items()}
x2 = x[x.qid != "Q133566"]
sea2 = x2.groupby("m").views.sum()
R["stagionalita_top20_senza_stadio_2016_2019_quota_%"] = {k: round(100 * s_ / sea2.sum(), 2) for k, s_ in sea2.items()}
# --- serie mensile dei primi 10 luoghi
top10 = tl[tl.tipo == "luogo"].head(10)
vm[vm.qid.isin(top10.qid)].groupby(["mese", "nome"]).views.sum().unstack(fill_value=0).to_csv(os.path.join(P, "serie_top10_mensile.csv"), sep=";")
# --- redirect
rows = []
tt = tl.set_index("qid")
for f in glob.glob(os.path.join(base, "raw", "redirect_it", "*.json")):
    dd = json.load(open(f, encoding="utf8"))
    q = dd["qid"]
    rv = sum(r["views_totali"] for r in dd["redirect"])
    itv = int(tt.loc[q, "views_it"])
    top = sorted(dd["redirect"], key=lambda r: -r["views_totali"])[:1]
    rows.append({"qid": q, "nome": tt.loc[q, "nome"], "titolo_attuale": dd["titolo"], "views_it_titolo_attuale": itv, "n_redirect": len(dd["redirect"]),
                 "views_it_redirect": rv, "redirect_su_titolo_%": round(100 * rv / max(itv, 1), 1), "redirect_principale": top[0]["titolo"] if top else "",
                 "views_redirect_principale": top[0]["views_totali"] if top else 0})
rd = pd.DataFrame(rows).sort_values("redirect_su_titolo_%", ascending=False)
rd.to_csv(os.path.join(P, "redirect_it_riepilogo.csv"), sep=";", index=False)
R["redirect_it_controllati"] = int(len(rd))
R["redirect_it_mediana_%"] = float(rd["redirect_su_titolo_%"].median())
R["redirect_it_totale_%"] = round(100 * rd.views_it_redirect.sum() / rd.views_it_titolo_attuale.sum(), 2)
json.dump(R, open(os.path.join(P, "approfondimenti.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps(R, ensure_ascii=False, indent=1))
