"""b2: storia B - comunita' per cittadinanza, citta' e NIL. Legge pulito/residenti_nil_anno_cittadinanza.csv (da b1).
Uso: python -I -X utf8 b2_cittadinanze.py <popolazione assoluto>
Scrive in pulito/: cittadinanze_nil_indicatori.csv, cittadinanze_top3_nil.csv, cittadinanze_concentrazione.csv, cittadinanze_citta_top.csv, riepilogo_B.json
'cittadinanza' = cittadinanza del registro anagrafico (Italia = chi ha la cittadinanza italiana, anche se nato altrove); non e' il luogo di nascita ne' l'origine."""
import sys, os, json
import numpy as np, pandas as pd
P = sys.argv[1]; out = os.path.join(P, "pulito")
d = pd.read_csv(os.path.join(out, "residenti_nil_anno_cittadinanza.csv"))
ana = pd.read_csv(os.path.join(out, "nil_anagrafica.csv"))
nm = dict(zip(ana.id_nil, ana.nil))
tot = d.groupby(["anno", "id_nil"]).residenti.sum().rename("residenti")
s = d[d.cittadinanza != "Italia"].copy()
stt = s.groupby(["anno", "id_nil"]).residenti.sum().rename("stranieri")
s = s.merge(stt.reset_index(), on=["anno", "id_nil"], suffixes=("", "_tot"))
s["sh"] = s.residenti / s.residenti_tot if "residenti_tot" in s else None
s["sh"] = s.residenti / s.stranieri
agg = s.groupby(["anno", "id_nil"]).agg(n_cittadinanze=("cittadinanza", "nunique"), hhi=("sh", lambda x: float((x ** 2).sum())))
agg["n_effettivo"] = 1 / agg.hhi
top = s.sort_values(["anno", "id_nil", "residenti"], ascending=[True, True, False]).groupby(["anno", "id_nil"]).head(1).set_index(["anno", "id_nil"])
agg["cit_top1"] = top.cittadinanza; agg["top1_n"] = top.residenti
r = pd.concat([tot, stt], axis=1).join(agg).reset_index()
r["stranieri"] = r.stranieri.fillna(0)
r["quota_stranieri"] = r.stranieri / r.residenti
r["top1_quota_su_stranieri"] = r.top1_n / r.stranieri
r["top1_quota_su_residenti"] = r.top1_n / r.residenti
r["nil"] = r.id_nil.map(nm)
r.to_csv(os.path.join(out, "cittadinanze_nil_indicatori.csv"), index=False, float_format="%.6g")

# top3 per nil-anno (anni scelti)
rows = []
for y in (1999, 2005, 2011, 2019, 2025):
    ss = s[s.anno == y].merge(tot.reset_index(), on=["anno", "id_nil"], suffixes=("", "_c"))
    ss = ss.sort_values(["id_nil", "residenti"], ascending=[True, False])
    ss["rango"] = ss.groupby("id_nil").cumcount() + 1
    ss = ss[ss.rango <= 3]
    ss["quota_su_residenti"] = ss.residenti / ss.residenti_c if "residenti_c" in ss else np.nan
    ss["nil"] = ss.id_nil.map(nm)
    rows.append(ss[["anno", "id_nil", "nil", "rango", "cittadinanza", "residenti", "quota_su_residenti"]])
pd.concat(rows).to_csv(os.path.join(out, "cittadinanze_top3_nil.csv"), index=False, float_format="%.6g")

# concentrazione di ogni cittadinanza sui NIL
cres = d.merge(tot.reset_index(), on=["anno", "id_nil"], suffixes=("", "_nil"))
conc = []
for y in (1999, 2005, 2011, 2019, 2025):
    dy = cres[cres.anno == y]
    T = dy.groupby("id_nil").residenti.sum()
    Ttot = T.sum()
    gtop = dy[dy.cittadinanza != "Italia"].groupby("cittadinanza").residenti.sum().sort_values(ascending=False).head(25).index
    for g in gtop:
        a = dy[dy.cittadinanza == g].groupby("id_nil").residenti.sum().reindex(T.index, fill_value=0)
        n = a.sum()
        share_group = a / n                       # dove vive il gruppo
        share_rest = (T - a) / (Ttot - n)          # dove vive il resto
        D = 0.5 * (share_group - share_rest).abs().sum()   # indice di dissimilarita' di Duncan
        lq = (a / T) / (n / Ttot)
        big = T[T >= 3000].index
        lqb = lq[big]
        k5 = share_group.sort_values(ascending=False).head(5)
        conc.append(dict(anno=y, cittadinanza=g, residenti=int(n), quota_citta=n / Ttot, dissimilarita=D, quota_nei_5_nil_top=k5.sum(),
                         nil_1=nm[k5.index[0]], nil_1_n=int(a[k5.index[0]]), nil_1_quota_su_residenti_nil=a[k5.index[0]] / T[k5.index[0]],
                         nil_lq_max=nm[lqb.idxmax()], lq_max=lqb.max(), nil_lq_max_n=int(a[lqb.idxmax()]), nil_lq_max_quota=a[lqb.idxmax()] / T[lqb.idxmax()]))
conc = pd.DataFrame(conc)
conc.to_csv(os.path.join(out, "cittadinanze_concentrazione.csv"), index=False, float_format="%.6g")

# citta: top 15 per anno e rango del 2025
cc = pd.read_csv(os.path.join(out, "residenti_comune_anno_cittadinanza.csv"))
ci = cc[cc.cittadinanza != "Italia"]
rk = ci.assign(rango=ci.groupby("anno").residenti.rank(ascending=False, method="first"))
rk[rk.rango <= 15].to_csv(os.path.join(out, "cittadinanze_citta_top.csv"), index=False)
piv = ci.pivot(index="anno", columns="cittadinanza", values="residenti").fillna(0)
first = piv.idxmax(axis=1)
# anno di sorpasso Egitto-Filippine
sorp = piv[["Egitto", "Filippine"]]
res = dict(primo_per_anno={int(k): v for k, v in first.items()},
           egitto_filippine={int(k): [int(a), int(b)] for k, (a, b) in zip(sorp.index, sorp.values)})
# diversita': NIL con >=3000 residenti e >=500 stranieri
for y in (1999, 2011, 2019, 2025):
    q = r[(r.anno == y) & (r.residenti >= 3000) & (r.stranieri >= 500)].sort_values("n_effettivo")
    res[f"diversita_{y}"] = dict(meno_diversi=q.head(5)[["nil", "n_effettivo", "quota_stranieri", "cit_top1", "top1_quota_su_stranieri"]].round(3).to_dict("records"),
                                 piu_diversi=q.tail(5)[["nil", "n_effettivo", "quota_stranieri", "cit_top1", "top1_quota_su_stranieri"]].round(3).to_dict("records"))
    q2 = r[(r.anno == y) & (r.residenti >= 3000)].sort_values("quota_stranieri")
    res[f"quota_stranieri_{y}"] = dict(min=q2.head(5)[["nil", "quota_stranieri", "residenti"]].round(3).to_dict("records"), max=q2.tail(5)[["nil", "quota_stranieri", "residenti"]].round(3).to_dict("records"))
json.dump(res, open(os.path.join(out, "riepilogo_B.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(conc[conc.anno == 2025].sort_values("residenti", ascending=False).head(14).to_string())
print(conc[(conc.anno == 1999)].sort_values("residenti", ascending=False).head(8).to_string())
print(json.dumps({k: v for k, v in res.items() if k.startswith("quota") or k.startswith("divers")}, ensure_ascii=False, indent=0)[:3500])
print({k: v for k, v in res["primo_per_anno"].items()})
print(res["egitto_filippine"])
