"""Approfondimenti sulle serie: pioggia e Area C (auto contro moto), Wikipedia e Olimpiadi, denunce da novembre 2023, inflazione e compravendite, giorni della settimana dei morti, Linate e presenze, esperimenti naturali con base pulita dal Covid, ipotesi attese che non reggono.
Stampare in out/log_08.txt"""
import json
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy import stats

from comune import OUT, SEED, bh, path, rd

pd.set_option("display.width", 220, "display.max_rows", 200)
rng = np.random.default_rng(SEED)
M = pd.read_csv(os.path.join(OUT, "tempo_mese.csv"), index_col=0)
M.index = pd.PeriodIndex(M.index, freq="M")
Y = pd.read_csv(os.path.join(OUT, "tempo_anno.csv"), index_col=0)
G = pd.read_csv(os.path.join(OUT, "tempo_giorno.csv"), index_col=0, parse_dates=True)
R = pd.read_csv(os.path.join(OUT, "tempo_mese_residui.csv"), index_col=0)
R.index = pd.PeriodIndex(R.index, freq="M")


def nw_ols(y, X, lag=7):
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b
    XtXi = np.linalg.pinv(X.T @ X)
    S0 = (X * e[:, None]).T @ (X * e[:, None])
    for l in range(1, lag + 1):
        w = 1 - l / (lag + 1)
        G_ = (X[l:] * e[l:, None]).T @ (X[:-l] * e[:-l, None])
        S0 += w * (G_ + G_.T)
    return b, np.sqrt(np.diag(XtXi @ S0 @ XtXi))


print("=== 1. PIOGGIA E INGRESSI IN AREA C")
ac = rd("docs/area-c/data/ingressi_giornalieri.csv")
ac["data"] = pd.to_datetime(ac.data)
ac = ac[ac.flag != "nessun_dato"].set_index("data")
print(ac[["totale", "tipo_moto", "tipo_auto", "veic_persone", "veic_merci", "res_residenti", "esenti_autorizzati"]].describe().T[["count", "mean"]].round(0).to_string())
d = ac.join(G[["pioggia_mm", "tmedia"]], how="inner")
d = d[(d.index.dayofweek < 5) & (d.index.month != 8) & ~((d.index >= "2020-02-20") & (d.index <= "2021-12-31")) & ~((d.index.month == 12) & (d.index.day >= 20)) & ~((d.index.month == 1) & (d.index.day <= 7))]
festivi = {(1, 1), (1, 6), (4, 25), (5, 1), (6, 2), (8, 15), (11, 1), (12, 7), (12, 8), (12, 25), (12, 26)}
d = d[[(a.month, a.day) not in festivi for a in d.index]]
d = d.dropna(subset=["pioggia_mm", "tmedia"])


def eff(col, mask=None, nome=None):
    q = d if mask is None else d[mask]
    q = q[q[col] > 0]
    doy = q.index.dayofyear.values / 365.25
    X = [np.ones(len(q)), (q.pioggia_mm.values >= 1).astype(float), (q.pioggia_mm.values >= 10).astype(float), q.tmedia.values]
    for k in (1, 2):
        X += [np.sin(2 * np.pi * k * doy), np.cos(2 * np.pi * k * doy)]
    for w in range(1, 5):
        X.append((q.index.dayofweek == w).astype(float))
    ys = sorted(set(q.index.year))
    for a in ys[1:]:
        X.append((q.index.year == a).astype(float))
    X = np.column_stack(X)
    b, se = nw_ols(np.log(q[col].values), X)
    return dict(serie=nome or col, n=len(q), pioggia_ge1mm_pct=(np.exp(b[1]) - 1) * 100, z1=b[1] / se[1], in_piu_oltre_10mm_pct=(np.exp(b[2]) - 1) * 100, z10=b[2] / se[2], per_grado_pct=(np.exp(b[3]) - 1) * 100, zt=b[3] / se[3])


rr = [eff(c) for c in ["totale", "tipo_auto", "tipo_moto", "veic_persone", "veic_merci", "res_residenti", "esenti_autorizzati", "classe_paganti_residenti", "classe_altri_paganti"] if c in d.columns]
PR = pd.DataFrame(rr)
PR.to_csv(os.path.join(OUT, "app_pioggia_areac.csv"), index=False, encoding="utf-8-sig")
print(PR.round(2).to_string())
for an in [(2016, 2019), (2022, 2024)]:
    m = (d.index.year >= an[0]) & (d.index.year <= an[1])
    print(an, pd.DataFrame([eff(c, m) for c in ["totale", "tipo_auto", "tipo_moto"]]).round(2).to_string())
# stagione: in estate la moto sostituisce di più?
print("per stagione moto:", {s: round(eff("tipo_moto", d.index.month.isin(ms))["pioggia_ge1mm_pct"], 1) for s, ms in {"inverno": [11, 12, 1, 2], "primavera": [3, 4, 5], "estate": [6, 7, 9], "autunno": [10]}.items()})
print("per stagione auto:", {s: round(eff("tipo_auto", d.index.month.isin(ms))["pioggia_ge1mm_pct"], 1) for s, ms in {"inverno": [11, 12, 1, 2], "primavera": [3, 4, 5], "estate": [6, 7, 9], "autunno": [10]}.items()})
# prova inversa: pioggia del giorno dopo non deve contare
d2 = d.copy()
d2["pioggia_mm"] = G.pioggia_mm.shift(-1).reindex(d2.index)
dd = d
d = d2.dropna(subset=["pioggia_mm"])
print("placebo pioggia di DOMANI:", pd.DataFrame([eff(c) for c in ["tipo_auto", "tipo_moto"]])[["serie", "pioggia_ge1mm_pct", "z1"]].round(2).to_string())
d = dd
# serie vecchia 2012-2015: contava cosa?
ao = rd("docs/area-c/data/ingressi_giornalieri_2012-2016_conteggio_diverso.csv")
print("colonne serie vecchia:", list(ao.columns)[:14])

print("\n=== 2. WIKIPEDIA E OLIMPIADI")
wm = pd.read_csv(path("luoghi-cercati", "pulito", "luoghi_vs_wikipedia_mensile.csv"), sep=";")
print(wm.columns.tolist())
wm["p"] = pd.PeriodIndex(wm.mese, freq="M")
tot = wm.groupby("p")[["wikipedia_totale", "luoghi_milano"]].sum()
it = wm[wm.lingua == "it"].set_index("p")
es = wm[wm.lingua != "it"].groupby("p")[["wikipedia_totale", "luoghi_milano"]].sum()
es["quota"] = es.luoghi_milano / es.wikipedia_totale * 1e6
it = it.assign(quota=it.luoghi_milano / it.wikipedia_totale * 1e6)
print(es.loc["2025-10":"2026-06"].round(1).to_string())
print(it.loc["2025-10":"2026-06"][["wikipedia_totale", "luoghi_milano", "quota"]].round(1).to_string())
for nm, q in [("estero", es.quota), ("italiano", it.quota)]:
    v = q["2026-02"]
    base = [q[pd.Period(f"{a}-02", "M")] for a in (2023, 2024, 2025)]
    tutti = np.log(q["2016-01":"2026-01"])
    print(nm, "feb 2026:", round(v, 1), "feb 23-25:", np.round(base, 1), "rapporto:", round(v / np.mean(base), 2), "| mesi con rapporto sullo stesso mese dei 3 anni prima superiore:", sum(1 for p in q["2019-01":"2026-01"].index if q[p] / np.mean([q[p - 12 * k] for k in (1, 2, 3)]) >= v / np.mean(base)), "su", len(q["2019-01":"2026-01"]))
vm = pd.read_csv(path("luoghi-cercati", "pulito", "views_mensili.csv"), nrows=3, sep=None, engine="python")
print(vm.columns.tolist())
try:
    vm = pd.read_csv(path("luoghi-cercati", "pulito", "views_mensili.csv"), sep=None, engine="python")
    vm["mese"] = vm[[c for c in vm.columns if "mese" in c.lower()][0]].astype(str)
    idc = [c for c in vm.columns if c in ("qid", "nome")][0]
    lang = [c for c in vm.columns if c in ("lingua", "lang")]
    val = [c for c in vm.columns if c in ("views", "letture", "visualizzazioni")][0]
    q = vm[vm.mese.str.startswith("2026-02")]
    if lang:
        q = q[q[lang[0]] != "it"]
    top = q.groupby(idc)[val].sum().sort_values(ascending=False).head(12)
    pr = vm[vm.mese.str.startswith("2025-02")]
    if lang:
        pr = pr[pr[lang[0]] != "it"]
    pr = pr.groupby(idc)[val].sum()
    lu = pd.read_csv(path("luoghi-cercati", "pulito", "totali_luogo.csv"), sep=None, engine="python").set_index("qid").nome
    print(pd.DataFrame({"feb26": top, "feb25": pr.reindex(top.index), "nome": lu.reindex(top.index)}).to_string())
except Exception as ex:
    print("dettaglio luoghi non letto", ex)

print("\n=== 3. DENUNCE: MALTRATTAMENTI E STALKING DA NOVEMBRE 2023")
fa = rd("docs/reati-citta/data/famiglia_stalking_mensile.csv")
fa["p"] = pd.PeriodIndex.from_fields(year=fa.anno.astype(int).values, month=fa.mese.astype(int).values, freq="M")
for k in ["Maltrattamenti", "stalking"]:
    x = fa[fa.tipo_delitto.astype(str).str.contains(k)]
    mi = x[x.territorio.astype(str).str.contains("Milano")].groupby("p").denunce.sum()
    itl = x[x.territorio == "Italia"].groupby("p").denunce.sum()
    print(k, "Milano medie:", {a: round(mi[str(a)].mean(), 1) for a in range(2019, 2025)}, "| Italia:", {a: round(itl[str(a)].mean(), 0) for a in range(2019, 2025)})
    for nome, s in [("Milano", mi), ("Italia", itl)]:
        pre = s["2022-11":"2023-10"]
        post = s["2023-11":"2024-10"]
        # placebo: stesso confronto 12 mesi prima
        pr2 = s["2021-11":"2022-10"]
        print("  ", nome, "12 mesi dopo nov 2023 contro 12 prima:", round(post.mean() / pre.mean() * 100 - 100, 1), "%  | anno prima:", round(pre.mean() / pr2.mean() * 100 - 100, 1), "%")
    rap = np.log(mi / itl).dropna()
    print("   rapporto Milano/Italia: prima", round(np.exp(rap["2022-01":"2023-10"].mean()) * 100, 2), "% dopo", round(np.exp(rap["2023-11":"2024-12"].mean()) * 100, 2), "%")
    print("   mese per mese Milano:", mi["2023-07":"2024-04"].astype(int).to_dict())

print("\n=== 4. INFLAZIONE E COMPRAVENDITE L'ANNO DOPO")
D_ = np.log(Y[["ipc_generale", "compravendite", "immatricolazioni", "ipc_affitti", "prezzo_case_reale"]]).diff()
for y_ in ["compravendite", "immatricolazioni", "prezzo_case_reale"]:
    for L in (0, 1, 2):
        d_ = pd.concat([D_.ipc_generale.shift(L), D_[y_]], axis=1, keys=["x", "y"]).dropna()
        d2 = d_[~d_.index.isin([2020, 2021, 2022]) & ~d_.index.isin([2020 + L, 2021 + L, 2022 + L])]
        r, p = stats.spearmanr(d2.x, d2.y) if len(d2) > 5 else (np.nan, np.nan)
        rt, pt = stats.spearmanr(d_.x, d_.y)
        # senza 2008-2009 e 2012-13 (crisi): togli gli anni peggiori
        d3 = d2[~d2.index.isin([2008, 2009, 2012, 2013])]
        r3 = stats.spearmanr(d3.x, d3.y)[0] if len(d3) > 5 else np.nan
        # pendenza: variazione y per +1 punto di inflazione
        sl = np.polyfit(d2.x * 100, d2.y * 100, 1)[0] if len(d2) > 5 else np.nan
        print(y_, "lag", L, "n", len(d2), "r senza covid", round(r, 2), "p", round(p, 4), "| con tutti", round(rt, 2), "| senza crisi", round(r3, 2), "| punti di y per punto di inflazione", round(sl, 1))
print(pd.concat([D_.ipc_generale.shift(1) * 100, D_.compravendite * 100], axis=1, keys=["infl_anno_prima", "var_comprav"]).dropna().round(1).T.to_string())

print("\n=== 5. MORTI: GIORNI DELLA SETTIMANA")
g = G.dropna(subset=["morti"])
g = g[~((g.index >= "2020-02-15") & (g.index <= "2021-12-31"))]
w = g.groupby(g.index.dayofweek).morti.agg(["mean", "size", "std"])
w["rapporto"] = w["mean"] / g.morti.mean()
w["z"] = (w["mean"] - g.morti.mean()) / (w["std"] / np.sqrt(w["size"]))
print(w.round(3).to_string())
by = g.groupby([g.index.year, g.index.dayofweek]).morti.mean().unstack()
print((by.div(by.mean(axis=1), axis=0)).round(3).to_string())
print("anni in cui domenica è sotto la media:", int((by[6] < by.mean(axis=1)).sum()), "su", len(by))
# è un giorno in cui si muore meno o si certifica meno? lunedì non compensa
tot_week = g.morti.resample("W").sum()
print("Domenica contro media feriali:", round((by[6] / by[[0, 1, 2, 3, 4]].mean(axis=1)).mean(), 3), " sabato:", round((by[5] / by[[0, 1, 2, 3, 4]].mean(axis=1)).mean(), 3))

print("\n=== 6. LINATE E PRESENZE")
for a in ["pax_linate", "pax_malpensa", "pax_bergamo"]:
    x = R[a]
    y = R["presenze"]
    d_ = pd.concat([x, y], axis=1, keys=["x", "y"]).dropna()
    d2 = d_[~((d_.index >= pd.Period("2020-03", "M")) & (d_.index <= pd.Period("2021-12", "M")))]
    print(a, "n", len(d2), "rho senza covid", round(stats.spearmanr(d2.x, d2.y)[0], 3), "| dal 2022-07:", round(stats.spearmanr(d2.x["2022-07":], d2.y["2022-07":])[0], 3), "n", len(d2.x["2022-07":]), "| 2019:", round(stats.spearmanr(d2.x["2019"], d2.y["2019"])[0], 3))
print("tolta anche la chiusura di Linate, senza il 2022 di ripresa")
d_ = pd.concat([R.pax_linate, R.presenze], axis=1, keys=["x", "y"]).dropna()
d2 = d_[(d_.index >= pd.Period("2023-01", "M")) | (d_.index < pd.Period("2020-03", "M"))]
print(len(d2), stats.spearmanr(d2.x, d2.y))
# residui grandi: quali mesi?
print(pd.concat([R.pax_linate, R.presenze], axis=1)["2022-07":].round(3).assign(prod=lambda t: t.pax_linate * t.presenze).sort_values("prod", ascending=False).head(6).to_string())

print("\n=== 7. ESPERIMENTI NATURALI CON BASE SENZA COVID")


def effetto(s, ini, fin, base_anni, log=True):
    s = M[s].dropna()
    s = np.log(s.where(s > 0)) if log else s
    pr = pd.period_range(ini, fin, freq="M")
    dif = []
    for p in pr:
        b = [s[pd.Period(f"{a}-{p.month:02d}", "M")] for a in base_anni if pd.Period(f"{a}-{p.month:02d}", "M") in s.index]
        if p in s.index and b:
            dif.append(s[p] - np.mean(b))
    return (np.exp(np.mean(dif)) - 1) * 100 if dif and log else (np.mean(dif) if dif else np.nan), len(dif)


E = [("Energia 2022: Area C", "areac", "2022-03", "2022-12", [2017, 2018, 2019], True),
     ("Stesso periodo, senza shock: Area C 2023", "areac", "2023-03", "2023-12", [2017, 2018, 2019], True),
     ("Stesso periodo Area C 2024", "areac", "2024-03", "2024-10", [2017, 2018, 2019], True),
     ("Energia 2022: prestiti", "prestiti", "2022-03", "2022-12", [2017, 2018, 2019], True),
     ("Prestiti 2023", "prestiti", "2023-03", "2023-12", [2017, 2018, 2019], True),
     ("Prestiti 2024", "prestiti", "2024-03", "2024-12", [2017, 2018, 2019], True),
     ("Prestiti 2025", "prestiti", "2025-03", "2025-12", [2017, 2018, 2019], True),
     ("Linate dopo M4 (2023-2)", "pax_linate", "2023-02", "2023-12", [2017, 2018], True),
     ("Linate 2024", "pax_linate", "2024-01", "2024-12", [2017, 2018], True),
     ("Linate dopo M4 completa (2025)", "pax_linate", "2025-01", "2025-12", [2017, 2018], True),
     ("Malpensa 2023", "pax_malpensa", "2023-02", "2023-12", [2017, 2018], True),
     ("Malpensa 2024", "pax_malpensa", "2024-01", "2024-12", [2017, 2018], True),
     ("Malpensa 2025", "pax_malpensa", "2025-01", "2025-12", [2017, 2018], True),
     ("Bergamo 2025", "pax_bergamo", "2025-01", "2025-12", [2017, 2018], True),
     ("Area C M4 dic22-nov24 sul 2017-19", "areac", "2022-12", "2024-10", [2017, 2018, 2019], True),
     ("Area C prima di M4 mar-nov 2022", "areac", "2022-03", "2022-11", [2017, 2018, 2019], True),
     ("NO2 Area B mar19-feb20 su 2016-18", "no2", "2019-03", "2020-02", [2016, 2017, 2018], True),
     ("PM10 Area B mar19-feb20 su 2016-18", "pm10", "2019-03", "2020-02", [2016, 2017, 2018], True),
     ("NO2 2018 placebo su 2015-17", "no2", "2018-03", "2019-02", [2015, 2016, 2017], True),
     ("Musei civici Expo mag-ott 2015 su 2012-14", "musei_civici", "2015-05", "2015-10", [2012, 2013, 2014], True),
     ("Musei civici mag-ott 2016 su 2012-14", "musei_civici", "2016-05", "2016-10", [2012, 2013, 2014], True),
     ("Musei civici mag-ott 2017 su 2012-14", "musei_civici", "2017-05", "2017-10", [2012, 2013, 2014], True),
     ("Prestiti Expo mag-ott 2015 su 2013-14", "prestiti", "2015-05", "2015-10", [2013, 2014], True),
     ]
print(pd.DataFrame([dict(evento=e[0], effetto_pct=effetto(*e[1:])[0], mesi=effetto(*e[1:])[1]) for e in E]).round(1).to_string())
print("Chiusura Linate: passeggeri totali 3 scali ago-ott 2019 su ago-ott 2018:")
tot3 = M[["pax_linate", "pax_malpensa", "pax_bergamo"]].sum(axis=1)
print(round(tot3["2019-08":"2019-10"].sum() / tot3["2018-08":"2018-10"].sum() * 100 - 100, 1), "%   Linate persi:", int(M.pax_linate["2018-08":"2018-10"].sum() - M.pax_linate["2019-08":"2019-10"].sum()), "Malpensa guadagnati:", int(M.pax_malpensa["2019-08":"2019-10"].sum() - M.pax_malpensa["2018-08":"2018-10"].sum()), "Bergamo guadagnati:", int(M.pax_bergamo["2019-08":"2019-10"].sum() - M.pax_bergamo["2018-08":"2018-10"].sum()))

print("\n=== 8. RELAZIONI ATTESE CHE NON SI VEDONO (residui mensili, senza Covid)")
ATT = [("benzina", "areac", "benzina cara, meno ingressi?"), ("benzina", "pax_linate", "benzina cara, meno voli?"), ("pioggia_mm", "prestiti", "più pioggia, più prestiti?"), ("giorni_pioggia", "prestiti", "più giorni di pioggia, più prestiti?"), ("pioggia_mm", "musei_civici", "più pioggia, più musei?"), ("giorni_pioggia", "musei_civici", "giorni di pioggia e musei"), ("tmedia", "morti", "mese più caldo del normale e morti"), ("pm10", "morti", "PM10 alto e morti"), ("no2", "morti", "NO2 alto e morti"), ("areac", "no2", "più ingressi, più NO2?"), ("areac", "pm10", "più ingressi, più PM10?"), ("presenze", "prestiti", "più turisti, meno prestiti?"), ("pax_malpensa", "presenze", "Malpensa e presenze"), ("wiki_estero", "presenze", "letture estere e presenze"), ("wiki_estero", "pax_malpensa", "letture estere e Malpensa"), ("tmedia", "denunce_maltrattamenti", "caldo e denunce di maltrattamenti"), ("tmedia", "denunce_stalking", "caldo e denunce di stalking"), ("ipc_generale_milano", "prestiti", "inflazione e prestiti"), ("presenze", "pm10", "turisti e PM10")]
righe = []
cov = (R.index >= pd.Period("2020-03", "M")) & (R.index <= pd.Period("2021-12", "M"))
for a, b, q_ in ATT:
    if a not in R or b not in R:
        righe.append(dict(domanda=q_, a=a, b=b))
        continue
    for L in (0, 1):
        x = R[a].shift(L)
        y = R[b]
        ok = x.notna() & y.notna() & ~cov
        if ok.sum() < 30:
            continue
        rr_, p_ = stats.spearmanr(x[ok], y[ok])
        righe.append(dict(domanda=q_, a=a, b=b, lag=L, n=int(ok.sum()), rho=rr_, p=p_))
AT = pd.DataFrame(righe)
AT["q"] = bh(AT.p.values)
AT.to_csv(os.path.join(OUT, "tempo_ipotesi_attese.csv"), index=False, encoding="utf-8-sig")
print(AT.round(3).to_string())
print("\n=== 9. MORTI E PM10 PER STAGIONE E RITARDO (giornaliero, senza Covid)")
