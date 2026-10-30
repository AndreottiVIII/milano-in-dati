"""Fase 2, passo 5: graduatorie dei NIL, cittadinanze, controlli. Uso: python -I h8_risultati.py <cartella censimenti>
Output (pulito/): variazioni_NIL_1991_2023.csv, variazioni_municipi_1991_2023.csv, cittadinanze_comune.csv, controllo_ds205_2023.csv"""
import sys
import numpy as np
import pandas as pd
root = sys.argv[1]; P = root + "/pulito/"; C = root + "/raw/comune_ckan/"
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
n = pd.read_csv(P + "indicatori_NIL.csv")
sens = pd.read_csv(P + "sensibilita_ripartizione_area.csv")
cols = ["pop", "quota_0_14", "quota_65p", "quota_75p", "indice_vecchiaia", "eta_media_classi", "quota_stranieri", "stran",
        "quota_laureati_su_base", "quota_laureati_su_residenti", "famiglie_comp_medio_approx", "quota_famiglie_1_comp",
        "quota_abit_non_occ_da_residenti", "tasso_occupazione_15_64_approx", "area_km2"]
w = {y: n[n.anno == y].set_index("nil")[cols + ["nil_nome", "municipio_prevalente"]] for y in (1991, 2001, 2011, 2021, 2023)}
out = pd.DataFrame(index=w[1991].index)
out["nil_nome"] = w[1991].nil_nome; out["municipio"] = w[1991].municipio_prevalente
for y in w:
    out[f"pop_{y}"] = w[y]["pop"]
out["var_pop_pct_1991_2023"] = 100 * (out.pop_2023 / out.pop_1991 - 1)
out["var_pop_pct_1991_2011"] = 100 * (out.pop_2011 / out.pop_1991 - 1)
out["var_pop_pct_2011_2023"] = 100 * (out.pop_2023 / out.pop_2011 - 1)
out["var_pop_ass_1991_2023"] = out.pop_2023 - out.pop_1991
for k, lab in [("eta_media_classi", "eta_media"), ("indice_vecchiaia", "ind_vecchiaia"), ("quota_65p", "q65"), ("quota_0_14", "q0_14"),
               ("quota_stranieri", "q_stran"), ("quota_laureati_su_base", "q_laur"), ("quota_famiglie_1_comp", "q_fam1")]:
    for y in (1991, 2011, 2023):
        out[f"{lab}_{y}"] = w[y][k]
    out[f"{lab}_delta_1991_2023"] = out[f"{lab}_2023"] - out[f"{lab}_1991"]
out["stran_2023"] = w[2023]["stran"]
# robustezza: NIL con almeno 2000 residenti nel 1991 e nel 2023 e differenza <5% tra assegnazione intera e ripartizione per area nel 1991 e 2001
s91 = sens[sens.anno == 1991].set_index("nil").diff_pop_pct.abs(); s01 = sens[sens.anno == 2001].set_index("nil").diff_pop_pct.abs()
out["diff_area_1991_pct"] = s91; out["diff_area_2001_pct"] = s01
out["robusto"] = (out.pop_1991 >= 2000) & (out.pop_2023 >= 2000) & (out.diff_area_1991_pct < 5) & (out.diff_area_2001_pct < 5)
out.round(3).reset_index().to_csv(P + "variazioni_NIL_1991_2023.csv", index=False)
r = out[out.robusto]
print("NIL robusti:", len(r), "su", len(out), "; popolazione 1991 dei NIL non robusti:", int(out[~out.robusto].pop_1991.sum()), "2023:", int(out[~out.robusto].pop_2023.sum()))
print(out[~out.robusto][["nil_nome", "pop_1991", "pop_2023", "diff_area_1991_pct"]].round(1).to_string())


def top(col, k=5, asc=False):
    t = r.sort_values(col, ascending=asc).head(k)
    return t[["nil_nome", "pop_1991", "pop_2023", col]].round(2)


for c in ["var_pop_pct_1991_2023", "var_pop_ass_1991_2023"]:
    print("\nPIU' ALTO", c); print(top(c)); print("PIU' BASSO"); print(top(c, asc=True))
for c in ["eta_media_delta_1991_2023", "ind_vecchiaia_delta_1991_2023", "q65_delta_1991_2023", "q_stran_delta_1991_2023", "q_laur_delta_1991_2023", "q_fam1_delta_1991_2023"]:
    t = r.sort_values(c, ascending=False)
    print("\n", c, "ALTO:", t[["nil_nome", c]].head(4).round(1).values.tolist(), "\n   BASSO:", t[["nil_nome", c]].tail(4).round(1).values.tolist())
print("\nPiu' vecchi 2023 (eta media):", r.sort_values("eta_media_2023", ascending=False)[["nil_nome", "eta_media_2023", "ind_vecchiaia_2023", "q65_2023"]].head(5).round(1).values.tolist())
print("Piu' giovani 2023:", r.sort_values("eta_media_2023")[["nil_nome", "eta_media_2023", "ind_vecchiaia_2023", "q65_2023"]].head(5).round(1).values.tolist())
print("Stranieri 2023 max:", r.sort_values("q_stran_2023", ascending=False)[["nil_nome", "q_stran_1991", "q_stran_2023"]].head(5).round(1).values.tolist())
print("Laureati 2023 max:", r.sort_values("q_laur_2023", ascending=False)[["nil_nome", "q_laur_1991", "q_laur_2023"]].head(4).round(1).values.tolist(), "min:", r.sort_values("q_laur_2023")[["nil_nome", "q_laur_1991", "q_laur_2023"]].head(4).round(1).values.tolist())
print("\nNIL con eta' media in calo 1991->2023:", int((r.eta_media_delta_1991_2023 < 0).sum()), "su", len(r))
print(r[r.eta_media_delta_1991_2023 < 0.5][["nil_nome", "eta_media_1991", "eta_media_2023", "eta_media_delta_1991_2023", "var_pop_pct_1991_2023"]].round(2).to_string())
print("Correlazione (NIL robusti) var pop 1991-2023 vs delta eta media:", round(r.var_pop_pct_1991_2023.corr(r.eta_media_delta_1991_2023), 2),
      "| vs delta quota stranieri", round(r.var_pop_pct_1991_2023.corr(r.q_stran_delta_1991_2023), 2))

# ---- municipi
m = pd.read_csv(P + "indicatori_municipi.csv")
mw = m.pivot(index="mun", columns="anno", values="pop"); mw["var_9123_pct"] = 100 * (mw[2023] / mw[1991] - 1)
mm = m[m.anno.isin([1991, 2023])].pivot(index="mun", columns="anno", values=["eta_media_classi", "quota_stranieri", "quota_laureati_su_base", "quota_65p"])
mm.columns = [f"{a}_{b}" for a, b in mm.columns]
mout = mw.join(mm); mout.round(2).reset_index().to_csv(P + "variazioni_municipi_1991_2023.csv", index=False)
print("\nMUNICIPI\n", mout.round(1).to_string())

# ---- cittadinanze (comune)
nz = pd.read_csv(P + "micro_codici_nazione.csv")
rows = []
for y in (1991, 2001):
    ci = pd.read_csv(P + f"micro_cittadinanza_{y}.csv").groupby("Nazione").persone.sum().reset_index()
    nm = nz[nz.anno == y].drop_duplicates("nazione_cod").set_index("nazione_cod").nome
    ci["nome"] = ci.Nazione.map(nm); tot = ci.persone.sum()
    ci = ci.sort_values("persone", ascending=False)
    for _, x in ci.head(10).iterrows():
        rows.append(dict(anno=y, cittadinanza=x.nome, persone=int(x.persone), quota_su_stranieri=round(100 * x.persone / tot, 1), fonte="record individuali Comune (micro_cittadinanza)"))
d = pd.read_csv(C + "ds386-censimento-2011-stranieri/00_ds386_popolazione_struttura_demografica_stranieri_10_cittadinanza_2011c.csv", sep=";")
d.columns = ["cit", "eta", "gen", "n"]
d["n"] = pd.to_numeric(d.n.astype(str).str.replace(".", "", regex=False), errors="coerce")
g = d.groupby("cit").n.sum().sort_values(ascending=False)
print("\nds386 2011 (10 cittadinanze), somma", int(g.sum()), "di", 176303)
for k, v in g.items():
    rows.append(dict(anno=2011, cittadinanza=k, persone=int(v), quota_su_stranieri=round(100 * v / 176303, 1), fonte="Comune ds386 (solo le 10 principali; somma sulle eta')"))
s23 = pd.read_csv(P + "sezioni_2023.csv", low_memory=False)
cit = {c: int(s23[c].sum()) for c in s23.columns if c.startswith("CIT_")}
nm23 = {"EGY": "Egitto", "PHL": "Filippine", "CHN": "Cina", "PER": "Peru'", "LKA": "Sri Lanka", "ROU": "Romania", "BGD": "Bangladesh", "UKR": "Ucraina", "MAR": "Marocco", "ECU": "Ecuador"}
for k, v in sorted(cit.items(), key=lambda x: -x[1]):
    rows.append(dict(anno=2023, cittadinanza=nm23[k.split("_")[-1]], persone=v, quota_su_stranieri=round(100 * v / 269397, 1), fonte="ISTAT Comuni_2023 colonne CIT_* (sezioni_2023.csv)"))
cz = pd.DataFrame(rows); cz.to_csv(P + "cittadinanze_comune.csv", index=False)
print(cz.to_string())

# ---- controllo ds205 (anagrafe) vs censimento 2023
d5 = pd.read_csv(root + "/raw/comune_annuale_nil/ds205_dati_quartieri_2011_2024_.csv", sep=";")
a = d5[d5.Anno == 2023].set_index("NIL")
cmp = pd.DataFrame({"anagrafe_2023": a.Totale, "censimento_2023": out.pop_2023, "nome": out.nil_nome})
cmp["diff_pct"] = 100 * (cmp.anagrafe_2023 / cmp.censimento_2023 - 1)
cmp.round(2).reset_index().rename(columns={"NIL": "nil"}).to_csv(P + "controllo_ds205_2023.csv", index=False)
print("\nds205 anagrafe 2023 vs censimento 2023: totale %d vs %d; corr NIL %.4f; diff %% mediana %.1f, min %.1f, max %.1f" % (
    cmp.anagrafe_2023.sum(), cmp.censimento_2023.sum(), cmp.anagrafe_2023.corr(cmp.censimento_2023), cmp.diff_pct.median(), cmp.diff_pct.min(), cmp.diff_pct.max()))
print(cmp.sort_values("diff_pct").iloc[[0, 1, 2, -3, -2, -1]].round(1))
