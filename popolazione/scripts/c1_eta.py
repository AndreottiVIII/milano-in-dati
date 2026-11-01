"""c1: storia C - eta' e centenari per NIL. Legge pulito/eta_nil_anno_indicatori.csv e centenari_*.csv (da b1).
Uso: python -I -X utf8 c1_eta.py <popolazione assoluto>  Scrive pulito/eta_nil_classifiche.csv, pulito/eta_dispersione_nil.csv, pulito/riepilogo_C.json
Regola per le classifiche: solo NIL con almeno 3.000 residenti nell'anno considerato (i NIL piccoli oscillano di anno in anno)."""
import sys, os, json
import numpy as np, pandas as pd
P = sys.argv[1]; out = os.path.join(P, "pulito")
i = pd.read_csv(os.path.join(out, "eta_nil_anno_indicatori.csv"))
c = pd.read_csv(os.path.join(out, "eta_comune_anno_indicatori.csv"))
cen = pd.read_csv(os.path.join(out, "centenari_comune_anno_genere.csv"))
res = {}
rows = []
for y in (1999, 2005, 2011, 2019, 2025):
    q = i[(i.anno == y) & (i.residenti >= 3000)].copy()
    q["rango_eta_media"] = q.eta_media.rank(ascending=False, method="first").astype(int)  # 1 = piu' anziano
    q["rango_mediana"] = q.eta_mediana.rank(ascending=False, method="first").astype(int)
    rows.append(q[["anno", "id_nil", "nil", "residenti", "eta_media", "eta_mediana", "q_0_14", "q_65p", "q_80p", "q_90p", "n_100p", "indice_vecchiaia", "rango_eta_media", "rango_mediana"]])
    res[f"estremi_{y}"] = dict(
        piu_anziani=q.sort_values("eta_media", ascending=False).head(5)[["nil", "residenti", "eta_media", "eta_mediana", "q_65p", "q_80p"]].round(3).to_dict("records"),
        piu_giovani=q.sort_values("eta_media").head(5)[["nil", "residenti", "eta_media", "eta_mediana", "q_0_14", "q_65p"]].round(3).to_dict("records"),
        n_nil=int(len(q)))
pd.concat(rows).to_csv(os.path.join(out, "eta_nil_classifiche.csv"), index=False, float_format="%.6g")
# dispersione tra NIL (>=3000 res) per anno
disp = []
for y, g in i[i.residenti >= 3000].groupby("anno"):
    w = g.residenti
    m = np.average(g.eta_media, weights=w)
    disp.append(dict(anno=y, n_nil=len(g), media_pesata=m, dev_std_pesata=float(np.sqrt(np.average((g.eta_media - m) ** 2, weights=w))), min=g.eta_media.min(), max=g.eta_media.max(), range=g.eta_media.max() - g.eta_media.min(),
                     q_65p_min=g.q_65p.min(), q_65p_max=g.q_65p.max(), q_0_14_min=g.q_0_14.min(), q_0_14_max=g.q_0_14.max()))
disp = pd.DataFrame(disp); disp.to_csv(os.path.join(out, "eta_dispersione_nil.csv"), index=False, float_format="%.6g")
res["dispersione"] = disp[disp.anno.isin([1999, 2011, 2019, 2025])].round(3).to_dict("records")
# cambiamenti 1999->2025 e 2011->2025 (NIL con >=3000 in entrambi)
a = i[(i.anno == 1999)].set_index("id_nil"); b = i[(i.anno == 2025)].set_index("id_nil"); m = i[(i.anno == 2011)].set_index("id_nil")
ok = a.index[(a.residenti >= 3000) & (b.reindex(a.index).residenti >= 3000)]
d = pd.DataFrame({"nil": a.loc[ok, "nil"], "res1999": a.loc[ok, "residenti"], "res2025": b.loc[ok, "residenti"], "eta1999": a.loc[ok, "eta_media"], "eta2025": b.loc[ok, "eta_media"]})
d["delta"] = d.eta2025 - d.eta1999
res["cambio_eta_media_1999_2025"] = dict(n=int(len(d)), invecchiati=d.sort_values("delta", ascending=False).head(5).round(2).to_dict("records"), ringiovaniti=d.sort_values("delta").head(6).round(2).to_dict("records"),
                                        mediana_delta=float(d.delta.median()))
ok2 = m.index[(m.residenti >= 3000) & (b.reindex(m.index).residenti >= 3000)]
d2 = pd.DataFrame({"nil": m.loc[ok2, "nil"], "eta2011": m.loc[ok2, "eta_media"], "eta2025": b.loc[ok2, "eta_media"], "q65_2011": m.loc[ok2, "q_65p"], "q65_2025": b.loc[ok2, "q_65p"]})
d2["delta"] = d2.eta2025 - d2.eta2011; d2["dq65"] = d2.q65_2025 - d2.q65_2011
res["cambio_2011_2025"] = dict(n=int(len(d2)), invecchiati=d2.sort_values("delta", ascending=False).head(5).round(3).to_dict("records"), ringiovaniti=d2.sort_values("delta").head(6).round(3).to_dict("records"))
# citta'
cc = c.set_index("anno")
res["citta"] = {int(y): dict(residenti=int(cc.loc[y, "residenti"]), eta_media=round(cc.loc[y, "eta_media"], 2), eta_mediana=round(cc.loc[y, "eta_mediana"], 2), q_0_14=round(cc.loc[y, "q_0_14"], 4),
                          q_65p=round(cc.loc[y, "q_65p"], 4), q_80p=round(cc.loc[y, "q_80p"], 4), q_90p=round(cc.loc[y, "q_90p"], 4), n_100p=int(cc.loc[y, "n_100p"])) for y in cc.index}
res["picco_q65"] = dict(anno=int(cc.q_65p.idxmax()), valore=round(cc.q_65p.max(), 4), minimo_dopo=dict(anno=int(cc.loc[2008:].q_65p.idxmin()), valore=round(cc.loc[2008:].q_65p.min(), 4)))
# centenari
cen = cen.set_index("anno"); cen["rapporto_F_M"] = cen.Femmine / cen.Maschi
cen["per_100mila"] = 1e5 * cen.totale / cc.residenti
res["centenari"] = {int(y): dict(F=int(r.Femmine), M=int(r.Maschi), tot=int(r.totale), FperM=round(r.rapporto_F_M, 2), per100mila=round(r.per_100mila, 1)) for y, r in cen.iterrows()}
cn = pd.read_csv(os.path.join(out, "centenari_nil_anno.csv"))
for y in (2011, 2025):
    q = cn[cn.anno == y].merge(i[i.anno == y][["id_nil", "residenti", "n_90p", "n_80p"]], on="id_nil")
    q = q[q.residenti >= 3000]
    q["per_10mila_res"] = 1e4 * q.centenari / q.residenti
    q["per_1000_90p"] = 1e3 * q.centenari / q.n_90p
    res[f"centenari_nil_{y}"] = dict(piu_numerosi=q.sort_values("centenari", ascending=False).head(6)[["nil", "centenari", "residenti"]].to_dict("records"),
                                    per_10mila=q.sort_values("per_10mila_res", ascending=False).head(5)[["nil", "centenari", "residenti", "per_10mila_res"]].round(2).to_dict("records"),
                                    nil_senza_centenari=int((cn[cn.anno == y].set_index("id_nil").centenari.reindex(range(1, 89)).fillna(0) == 0).sum()))
json.dump(res, open(os.path.join(out, "riepilogo_C.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(res, ensure_ascii=False, indent=0)[:9000])
