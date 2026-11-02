"""Lavoro, passo 3: analisi (confronti tra anni, stabilita' della geografia, legame con il reddito).
Uso: python -I -X utf8 03_analisi.py <milano-in-dati>
Input : lavoro/out/lavoro_NIL.csv, lavoro_comune.csv (passo 2), micro_condizione_1991_2001.csv (passo 1),
        censimenti/pulito/indicatori_NIL.csv, quartieri-che-cambiano/out/indicatori_nil.csv (reddito_2024, quota_civici_cap_instabili)
Output: lavoro/out/analisi.json (tutti i numeri usati dalla pagina e dalle NOTE, con la loro origine)
        lavoro/out/analisi.txt  (stessa cosa, leggibile)
"""
import sys, json
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

root = sys.argv[1]
O = root + "/lavoro/out/"
n = pd.read_csv(O + "lavoro_NIL.csv")
c = pd.read_csv(O + "lavoro_comune.csv").set_index("anno")
mic = pd.read_csv(O + "micro_condizione_1991_2001.csv")
ind = pd.read_csv(root + "/censimenti/pulito/indicatori_NIL.csv")[["anno", "nil", "quota_65p", "quota_laureati_su_residenti", "quota_stranieri"]]
inc = pd.read_csv(root + "/quartieri-che-cambiano/out/indicatori_nil.csv")[["id_nil", "reddito_2024", "quota_civici_cap_instabili"]].rename(columns={"id_nil": "nil"})
inc["nil"] = inc.nil.astype(int)
n = n.merge(ind, on=["anno", "nil"], how="left").merge(inc, on="nil", how="left")
R = {}
T = []


def P(s=""):
    print(s); T.append(str(s))


def rho(a, b):
    x = pd.concat([a, b], axis=1).dropna()
    if len(x) < 8:
        return None
    r, p = spearmanr(x.iloc[:, 0], x.iloc[:, 1])
    return dict(rho=round(float(r), 3), n=int(len(x)))


# ---------------- comune
R["comune"] = {int(y): {k: (None if pd.isna(v) else round(float(v), 3)) for k, v in row.items()} for y, row in c.iterrows()}
P("COMUNE")
P(f"occupati 1991 {int(c.loc[1991,'occ'])}, 2011 {int(c.loc[2011,'occ'])}; uomini {int(c.loc[1991,'occ_m'])} -> {int(c.loc[2011,'occ_m'])} ({int(c.loc[2011,'occ_m']-c.loc[1991,'occ_m']):+d}); "
  f"donne {int(c.loc[1991,'occ_f'])} -> {int(c.loc[2011,'occ_f'])} ({int(c.loc[2011,'occ_f']-c.loc[1991,'occ_f']):+d}); residenti {int(c.loc[1991,'pop'])} -> {int(c.loc[2011,'pop'])} ({int(c.loc[2011,'pop']-c.loc[1991,'pop']):+d})")
P(f"casalinghe/i {int(c.loc[1991,'cas'])} -> {int(c.loc[2011,'cas'])} ({int(c.loc[2011,'cas']-c.loc[1991,'cas']):+d}); pensionati {int(c.loc[1991,'rit'])} -> {int(c.loc[2011,'rit'])} ({int(c.loc[2011,'rit']-c.loc[1991,'rit']):+d})")
R["comune_differenze_1991_2011"] = dict(
    occ=int(c.loc[2011, "occ"] - c.loc[1991, "occ"]), occ_m=int(c.loc[2011, "occ_m"] - c.loc[1991, "occ_m"]), occ_f=int(c.loc[2011, "occ_f"] - c.loc[1991, "occ_f"]),
    pop=int(c.loc[2011, "pop"] - c.loc[1991, "pop"]), cas=int(c.loc[2011, "cas"] - c.loc[1991, "cas"]), rit=int(c.loc[2011, "rit"] - c.loc[1991, "rit"]),
    stu=int(c.loc[2011, "stu"] - c.loc[1991, "stu"]), p1564=int(c.loc[2011, "p1564"] - c.loc[1991, "p1564"]))

# ---------------- record individuali: quanto sovrastima il tasso 15-64 il fatto di contare anche gli occupati 65+
mm = {}
for y in (1991, 2001):
    x = mic[mic.anno == y]
    occ = x[x.CondProf == 1]
    tot = x.n.sum()
    mm[y] = dict(occupati=int(occ.n.sum()), occupati_65p=int(occ[occ.fascia == "65+"].n.sum()), quota_occupati_65p=round(float(occ[occ.fascia == "65+"].n.sum() / occ.n.sum() * 100), 2),
                 pop1564=int(x[x.fascia == "15-64"].n.sum()), occupati_1564=int(occ[occ.fascia == "15-64"].n.sum()),
                 tasso_occ_1564_esatto=round(float(occ[occ.fascia == "15-64"].n.sum() / x[x.fascia == "15-64"].n.sum() * 100), 2),
                 tasso_occ_tabelle_ISTAT=round(float(c.loc[y, "tasso_occ"]), 2))
    st = x[x.CondProf == 5]
    mm[y]["studenti_dichiarati"] = int(st.n.sum())
    if y == 1991:
        mm[y]["studenti_14anni"] = int(st[st.fascia == "14"].n.sum())
        mm[y]["quota_studenti_14anni"] = round(float(st[st.fascia == "14"].n.sum() / st.n.sum() * 100), 1)
        # casalinghe per sesso (Sesso: 1 = maschio, 2 = femmina)
        ca = x[x.CondProf == 4]
        mm[y]["casalinghe_uomini"] = int(ca[ca.Sesso == 1].n.sum()); mm[y]["casalinghe_donne"] = int(ca[ca.Sesso == 2].n.sum())
R["record_individuali"] = mm
P("RECORD INDIVIDUALI " + json.dumps(mm))

# ---------------- NIL: geografia stabile?
rob = n[n.anno == 2011].set_index("nil").robusto
tab = lambda col: n.pivot(index="nil", columns="anno", values=col)
occ, occf, occm, dis = tab("tasso_occ"), tab("tasso_occ_f"), tab("tasso_occ_m"), tab("tasso_disocc")
st = {}
for a, b in [(1991, 2001), (2001, 2011), (2011, 2021), (2021, 2023), (2011, 2023)]:
    for nm, t in [("tot", occ), ("donne", occf), ("uomini", occm)]:
        x = t[[a, b]].dropna()
        r = spearmanr(x[a], x[b])[0]
        st[f"{nm}_{a}_{b}"] = dict(rho=round(float(r), 3), n=int(len(x)), diff_media=round(float((x[b] - x[a]).mean()), 2), diff_sd=round(float((x[b] - x[a]).std()), 2))
R["stabilita_rank_occupazione"] = st
P("STABILITA' (Spearman tra anni, tasso di occupazione 15-64)")
for k, v in st.items():
    P(f"  {k}: rho {v['rho']} su {v['n']} NIL; differenza media {v['diff_media']}, sd {v['diff_sd']}")

# diagnosi della rottura 2011 -> 2021: chi perde e' chi ha piu' laureati?
q11 = n[n.anno == 2011].set_index("nil")
d = (occ[2021] - occ[2011]).rename("d")
rr = rob[rob.fillna(False)].index
x = pd.concat([d, q11.quota_laureati_su_residenti, q11.quota_65p, q11.quota_stranieri], axis=1).loc[lambda t: t.index.isin(rr)].dropna()
R["rottura_2011_2021"] = dict(
    n=int(len(x)), media_variazione_punti=round(float(x.d.mean()), 2),
    rho_variazione_vs_laureati_2011=round(float(spearmanr(x.d, x.quota_laureati_su_residenti)[0]), 3),
    rho_variazione_vs_over65_2011=round(float(spearmanr(x.d, x.quota_65p)[0]), 3),
    rho_variazione_vs_stranieri_2011=round(float(spearmanr(x.d, x.quota_stranieri)[0]), 3))
P("ROTTURA 2011->2021 (NIL robusti) " + json.dumps(R["rottura_2011_2021"]))
x2 = x.copy(); x2["terzile_laureati"] = pd.qcut(x2.quota_laureati_su_residenti, 3, labels=["meno laureati", "medio", "piu' laureati"])
R["rottura_2011_2021"]["variazione_media_per_terzile_laureati"] = {str(k): round(float(v), 2) for k, v in x2.groupby("terzile_laureati", observed=True).d.mean().items()}
P("  variazione media per terzile di laureati " + json.dumps(R["rottura_2011_2021"]["variazione_media_per_terzile_laureati"]))
# stesso calcolo 1991 -> 2011 (serie omogenea): dipende dai laureati?
q91 = n[n.anno == 1991].set_index("nil")
d2 = (occ[2011] - occ[1991]).rename("d")
x = pd.concat([d2, q91.quota_laureati_su_residenti], axis=1).loc[lambda t: t.index.isin(rr)].dropna()
R["serie_1991_2011"] = dict(n=int(len(x)), rho_variazione_vs_laureati_1991=round(float(spearmanr(x.d, x.quota_laureati_su_residenti)[0]), 3), media=round(float(x.d.mean()), 2))
P("1991->2011 " + json.dumps(R["serie_1991_2011"]))

# ---------------- donne: aumento in ogni NIL robusto?
dd = (occf[2011] - occf[1991]).rename("d").to_frame().join(q11.nil_nome)
dd = dd[dd.index.isin(rr)].dropna()
R["donne_1991_2011"] = dict(n=int(len(dd)), min=round(float(dd.d.min()), 1), max=round(float(dd.d.max()), 1), mediana=round(float(dd.d.median()), 1),
                             nil_min=int(dd.d.idxmin()), nome_min=dd.nil_nome.loc[dd.d.idxmin()], nil_max=int(dd.d.idxmax()), nome_max=dd.nil_nome.loc[dd.d.idxmax()])
P("DONNE 1991->2011 " + json.dumps(R["donne_1991_2011"], ensure_ascii=False))
g = n[n.anno == 2011].set_index("nil")
R["gap_2011"] = dict(nil_donne_ge_uomini=int((g.tasso_occ_f >= g.tasso_occ_m).sum()),
                     n_calcolabili=int(g.tasso_occ_f.notna().sum()))
for y in (1991, 2001, 2011, 2023):
    z = n[n.anno == y]
    R["gap_2011"][f"nil_donne_ge_uomini_{y}"] = int((z.tasso_occ_f >= z.tasso_occ_m).sum())
    R["gap_2011"][f"gap_min_max_{y}"] = [round(float(z.gap_occ_mf.min()), 1), round(float(z.gap_occ_mf.max()), 1)]
P("GAP " + json.dumps(R["gap_2011"]))

# ---------------- reddito
sub = n.copy()
sub["stabile"] = sub.quota_civici_cap_instabili <= 0.5
corr = {}
for y in (1991, 2001, 2011, 2021, 2023):
    z = sub[sub.anno == y].set_index("nil")
    row = {}
    for col in ["tasso_occ", "tasso_occ_f", "tasso_occ_m", "gap_occ_mf", "tasso_disocc", "studenti_100", "pensionati_100", "casalinghe_100_donne", "altri_100"]:
        if z[col].notna().sum() < 8:
            continue
        row[col] = dict(tutti=rho(z[col], z.reddito_2024), solo_cap_stabili=rho(z[col][z.stabile], z.reddito_2024[z.stabile]))
    corr[y] = row
R["reddito_spearman"] = corr
P("REDDITO 2024 (Spearman con il livello dei NIL)")
for y, row in corr.items():
    P(f"  {y}: " + "; ".join(f"{k} {v['tutti']['rho']:+.2f} (n={v['tutti']['n']}) / cap stabili {v['solo_cap_stabili']['rho']:+.2f}" for k, v in row.items() if v['tutti'] and v['solo_cap_stabili']))

# gruppi per reddito (terzili di NIL con tassi calcolabili e CAP stabili): tassi aggregati dai conteggi
grp = {}
base = sub[(sub.anno == 2011) & sub.tassi_ok & sub.stabile].set_index("nil")
cut = pd.qcut(base.reddito_2024, 3, labels=["terzo con reddito piu' basso", "terzo di mezzo", "terzo con reddito piu' alto"])
for y in (1991, 2001, 2011, 2023):
    z = sub[sub.anno == y].set_index("nil").loc[cut.index]
    z["gr"] = cut
    s = z.groupby("gr", observed=True)[["pop", "p1564", "p1564_m", "p1564_f", "occ", "occ_m", "occ_f", "fl", "cerca", "stu", "rit", "cas", "pop_f"]].sum()
    grp[y] = {str(k): dict(nil=int((cut == k).sum()), residenti=int(r["pop"]),
                          tasso_occ=round(float(100 * r.occ / r.p1564), 1), tasso_occ_f=round(float(100 * r.occ_f / r.p1564_f), 1), tasso_occ_m=round(float(100 * r.occ_m / r.p1564_m), 1),
                          tasso_disocc=(None if y >= 2021 else round(float(100 * r.cerca / r.fl), 1)),
                          pensionati_100=(None if y >= 2021 else round(float(100 * r.rit / r["pop"]), 1)),
                          casalinghe_100_donne=(None if y >= 2021 else round(float(100 * r.cas / r.pop_f), 1)))
              for k, r in s.iterrows()}
R["gruppi_reddito"] = dict(soglie_reddito_euro=[round(float(v)) for v in pd.qcut(base.reddito_2024, 3, retbins=True)[1]], gruppi=grp, nil_nel_gruppo=int(len(cut)))
P("GRUPPI PER REDDITO " + json.dumps(R["gruppi_reddito"], ensure_ascii=False))

# ---------------- classifiche (solo NIL con tassi calcolabili; robusti per i cambiamenti)
def top(y, col, k=5, asc=False, need_rob=False):
    z = n[(n.anno == y)].dropna(subset=[col])
    if need_rob:
        z = z[z.robusto == True]
    z = z.sort_values(col, ascending=asc).head(k)
    return [[int(r.nil), r.nil_nome, round(float(r[col]), 1), int(r["pop"])] for _, r in z.iterrows()]
R["classifiche"] = {f"{col}_{y}_{o}": top(y, col, 5, asc=(o == "min"), need_rob=True) for y, col in [(2011, "tasso_occ"), (2011, "tasso_occ_f"), (2011, "tasso_disocc"), (2011, "pensionati_100"), (1991, "casalinghe_100_donne"), (2011, "casalinghe_100_donne"), (2011, "gap_occ_mf"), (2023, "tasso_occ"), (2023, "tasso_occ_f")] for o in ("max", "min")}
for k, v in R["classifiche"].items():
    P(f"  {k}: " + "; ".join(f"{a[1]} {a[2]}" for a in v))


# ---------------- casalinghi uomini (per differenza) nei file per sezione
cm_ = {}
d01 = pd.read_csv(root + "/censimenti/pulito/sezioni_2001.csv", low_memory=False)
d11 = pd.read_csv(root + "/censimenti/pulito/sezioni_2011.csv", low_memory=False)
cm_["2001"] = int((d01.P129 - d01.P132 - d01.P134 - d01.P136).sum())
cm_["2011"] = int((d11.P129 - d11.P132 - d11.P136 - d11.P140).sum())
R["casalinghi_uomini_per_differenza"] = cm_
P("CASALINGHI UOMINI per differenza (non forze lavoro maschi - studenti - ritirati - altra condizione) " + json.dumps(cm_))

# quanti NIL affidabili
R["copertura_nil"] = {int(y): dict(tassi=int(g_.tassi_ok.sum()), disocc=int(g_.disocc_ok.sum()), robusti=int((g_.robusto == True).sum())) for y, g_ in n.groupby("anno")}
json.dump(R, open(O + "analisi.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=lambda o: None if o is None else str(o))
open(O + "analisi.txt", "w", encoding="utf-8").write("\n".join(T))
