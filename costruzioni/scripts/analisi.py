"""Riepiloghi del filone 'Dove si costruisce'. Uso: python -I -X utf8 analisi.py <costruzioni (assoluto)> <milano-in-dati (assoluto)>
Legge pulito/titoli_edilizi.csv, pulito/dbt_nil.csv (se c'e'), raw/istat/*.csv, ds205 (popolazione per NIL), prezzi-case/pulito (NTN, prezzi).
Scrive tabelle in pulito/ e pulito/riepilogo.json
"""
import sys, os, json
import numpy as np, pandas as pd
from scipy.stats import spearmanr

C, P = sys.argv[1], sys.argv[2]
pul = lambda f: os.path.join(C, "pulito", f)
R = {}
t = pd.read_csv(pul("titoli_edilizi.csv"), sep=";", encoding="utf-8", dtype={"civico": str})
t["anno"] = t.anno.astype("Int64")
tt = t[t.flag_anno_fuori_serie == 0].copy()          # serie 2014-2024 (i 9 record 2010-2012 sono ritardi, fuori dalle serie)
R["righe_totali"] = int(len(t)); R["righe_serie_2014_2024"] = int(len(tt))

# ---------------- A. titoli per anno
g = tt.groupby(["anno", "uso", "intervento", "tipo_titolo"], dropna=False).agg(n=("id_modello", "size"), abitazioni=("abitazioni", "sum"),
        volume_m3=("volume_m3", "sum"), superficie_m2=("superficie_m2", "sum")).reset_index()
g.to_csv(pul("titoli_per_anno_tipo.csv"), index=False, sep=";")
nuovi = tt[tt.intervento == "nuovo_fabbricato"]
amp = tt[tt.intervento == "ampliamento"]
y = pd.DataFrame({"anno": range(2014, 2025)}).set_index("anno")
y["nuovi_fabbricati_res"] = nuovi[nuovi.uso == "residenziale"].groupby("anno").size()
y["nuovi_fabbricati_nonres"] = nuovi[nuovi.uso == "non_residenziale"].groupby("anno").size()
y["nuovi_fabbricati_collettivita"] = nuovi[nuovi.uso == "collettivita"].groupby("anno").size()
y["ampliamenti_res"] = amp[amp.uso == "residenziale"].groupby("anno").size()
y["ampliamenti_nonres"] = amp[amp.uso == "non_residenziale"].groupby("anno").size()
y["ampliamenti_collettivita"] = amp[amp.uso == "collettivita"].groupby("anno").size()
for tipo, nm in [("Permesso di costruire", "pdc"), ("SCIA", "scia"), ("SCIA alternativa", "scia_alt")]:
    y[f"nuovi_fabbricati_{nm}"] = nuovi[nuovi.tipo_titolo == tipo].groupby("anno").size()
y["nuove_abitazioni_in_nuovi_fabbricati"] = nuovi.groupby("anno").abitazioni.sum()
y["nuove_abitazioni_nuovi_res"] = nuovi[nuovi.uso == "residenziale"].groupby("anno").abitazioni.sum()
y["abitazioni_da_ampliamenti"] = amp.groupby("anno").abitazioni.sum()
y["volume_nuovi_fabbricati_m3"] = nuovi.groupby("anno").volume_m3.sum()
y["volume_ampliamenti_m3"] = amp.groupby("anno").volume_m3.sum()
y["nuovi_con_abbattimento_ricostruzione"] = nuovi[nuovi.abbattimento_ricostruzione == "si"].groupby("anno").size()
y["nuovi_res_con_abbattimento_ricostruzione"] = nuovi[(nuovi.uso == "residenziale") & (nuovi.abbattimento_ricostruzione == "si")].groupby("anno").size()
y["nuove_abitazioni_con_abbattimento"] = nuovi[nuovi.abbattimento_ricostruzione == "si"].groupby("anno").abitazioni.sum()
y = y.fillna(0)

# ---------------- popolazione (ds205, somma dei NIL)
d205 = pd.read_csv(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "pop_caratteristiche_quartiere", "ds205_dati_quartieri_2011_2024_.csv"), sep=None, engine="python", dtype=str)
d205["Anno"] = d205.Anno.astype(int); d205["Totale"] = pd.to_numeric(d205.Totale, errors="coerce"); d205["id_nil"] = pd.to_numeric(d205.NIL, errors="coerce")
pop = d205.groupby("Anno").agg(pop=("Totale", "sum"), nil=("id_nil", "nunique"))
R["ds205_nil_per_anno"] = pop.nil.to_dict()
y["popolazione"] = pop["pop"]
y["var_popolazione"] = y.popolazione.diff()
y["nuove_abitazioni_per_100_nuovi_residenti"] = (100 * y.nuove_abitazioni_in_nuovi_fabbricati / y.var_popolazione).where(y.var_popolazione > 0).round(1)
# ---------------- ISTAT provincia (esploradati)
rc = pd.read_csv(os.path.join(C, "raw", "istat", "resid_constr_1_milano.csv"), dtype=str)
nr = pd.read_csv(os.path.join(C, "raw", "istat", "nonresid_constr_1_milano.csv"), dtype=str)
def ist(df, area, dt):
    s = df[(df.REF_AREA == area) & (df.DATA_TYPE == dt)].set_index("TIME_PERIOD").OBS_VALUE.astype(float); s.index = s.index.astype(int); return s
y["istat_prov_MI_nuovi_fabbricati_res"] = ist(rc, "ITC45", "NRB_NUM")
y["istat_prov_MI_abitazioni_nuovi_res"] = ist(rc, "ITC45", "NUMDW")
y["istat_prov_MI_volume_nuovi_res_m3"] = ist(rc, "ITC45", "NRB_VOL")
y["istat_prov_MI_nuovi_fabbricati_nonres"] = ist(nr, "ITC45", "NNRB_NUM")
y["istat_capoluoghi_oltre500k_abitazioni_nuovi_res"] = ist(rc, "INH_GE500001_CAP", "NUMDW")
y["quota_comune_su_provincia_abitazioni_pct"] = (100 * y.nuove_abitazioni_nuovi_res / y.istat_prov_MI_abitazioni_nuovi_res).round(1)
y["quota_comune_su_provincia_fabbricati_res_pct"] = (100 * y.nuovi_fabbricati_res / y.istat_prov_MI_nuovi_fabbricati_res).round(1)
# ---------------- contesto prezzi-case: NTN e prezzi
ntn = pd.read_csv(os.path.join(P, "prezzi-case", "pulito", "ntn_milano_trimestrale.csv"))
y["ntn_capoluogo"] = ntn.groupby("anno").ntn_capoluogo.sum().round(0)
n4 = ntn.groupby("anno").trimestre.nunique(); y["ntn_trimestri_presenti"] = n4
pr = pd.read_csv(os.path.join(P, "prezzi-case", "pulito", "prezzi_citta_mediana_zone.csv"))
pr = pr[pr.tipologia.str.contains("civili", case=False, na=False)]
y["prezzo_omi_abitazioni_civili_reale_2025_eur_m2"] = pr.groupby("anno").compr_mediana_zone_reale_2025.mean().round(0)
y.reset_index().to_csv(pul("serie_annuale.csv"), index=False, sep=";")
R["serie_annuale"] = y.reset_index().round(1).to_dict("records")

# ---------------- B. per NIL
n = nuovi.dropna(subset=["id_nil"]).copy(); n["id_nil"] = n.id_nil.astype(int)
nilname = t.dropna(subset=["id_nil"]).drop_duplicates("id_nil").set_index(t.dropna(subset=["id_nil"]).drop_duplicates("id_nil").id_nil.astype(int)).nil
gj = json.load(open(os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "nil_vigenti", "ds964_nil_wm.geojson"), encoding="utf-8"))
nl = pd.DataFrame([{"id_nil": int(f["properties"]["ID_NIL"]), "nil": f["properties"]["NIL"]} for f in gj["features"]]).set_index("id_nil")
nl["nuovi_fabbricati_res"] = n[n.uso == "residenziale"].groupby("id_nil").size()
nl["nuovi_fabbricati_nonres"] = n[n.uso == "non_residenziale"].groupby("id_nil").size()
nl["nuove_abitazioni_2014_2024"] = n.groupby("id_nil").abitazioni.sum()
nl["nuove_abitazioni_2014_2019"] = n[n.anno <= 2019].groupby("id_nil").abitazioni.sum()
nl["nuove_abitazioni_2020_2024"] = n[n.anno >= 2020].groupby("id_nil").abitazioni.sum()
nl["volume_nuovi_m3"] = n.groupby("id_nil").volume_m3.sum()
a_ = amp.dropna(subset=["id_nil"]).copy(); a_["id_nil"] = a_.id_nil.astype(int)
nl["ampliamenti"] = a_.groupby("id_nil").size(); nl["volume_ampliamenti_m3"] = a_.groupby("id_nil").volume_m3.sum()
nl["titoli_totali"] = tt.dropna(subset=["id_nil"]).assign(id_nil=lambda d: d.id_nil.astype(int)).groupby("id_nil").size()
nl = nl.fillna(0)
p14 = d205[d205.Anno == 2014].set_index("id_nil").Totale; p24 = d205[d205.Anno == 2024].set_index("id_nil").Totale
nl["pop_2014"] = p14; nl["pop_2024"] = p24; nl["var_pop_2014_2024"] = nl.pop_2024 - nl.pop_2014
nl["var_pop_pct"] = (100 * nl.var_pop_2014_2024 / nl.pop_2014).round(1)
nl["abitazioni_nuove_per_1000_ab_2024"] = (1000 * nl.nuove_abitazioni_2014_2024 / nl.pop_2024).round(1)
tot_ab = nl.nuove_abitazioni_2014_2024.sum()
nl["quota_abitazioni_nuove_pct"] = (100 * nl.nuove_abitazioni_2014_2024 / tot_ab).round(2)
nl["senza_nil_abitazioni"] = np.nan
R["abitazioni_nuove_assegnate_a_NIL"] = int(tot_ab); R["abitazioni_nuove_totali_serie"] = int(nuovi.abitazioni.sum())
srt = nl.sort_values("nuove_abitazioni_2014_2024", ascending=False)
R["top10_nil_abitazioni"] = srt.head(10)[["nil", "nuove_abitazioni_2014_2024", "quota_abitazioni_nuove_pct", "abitazioni_nuove_per_1000_ab_2024", "var_pop_pct"]].reset_index().to_dict("records")
R["quota_top5_nil_pct"] = round(float(srt.head(5).nuove_abitazioni_2014_2024.sum() / tot_ab * 100), 1)
R["quota_top10_nil_pct"] = round(float(srt.head(10).nuove_abitazioni_2014_2024.sum() / tot_ab * 100), 1)
R["nil_con_zero_abitazioni_nuove"] = int((nl.nuove_abitazioni_2014_2024 == 0).sum())
rho = spearmanr(nl.nuove_abitazioni_2014_2024, nl.var_pop_2014_2024, nan_policy="omit")
R["spearman_abitazioni_nuove_vs_var_popolazione_per_NIL"] = {"rho": round(float(rho.statistic), 2), "p": float(rho.pvalue), "n": int(nl.var_pop_2014_2024.notna().sum())}

# DBT (se presente)
if os.path.exists(pul("dbt_nil.csv")):
    d = pd.read_csv(pul("dbt_nil.csv"), sep=";").set_index("id_nil")
    for c in ["grandi_nuove_n", "grandi_nuove_volume_m3", "grandi_sparite_n", "grandi_sparite_volume_m3", "grandi_volume_netto_m3", "volume_nuove_m3", "volume_sopraelevazioni_m3", "volume_sparite_m3", "volume_netto_m3", "variazione_volume_pct", "volume_2012_m3", "volume_2020_m3"]:
        nl["dbt_" + c] = d[c]
    r2 = spearmanr(nl.nuove_abitazioni_2014_2024, nl.dbt_volume_nuove_m3, nan_policy="omit")
    R["spearman_abitazioni_permessi_vs_volume_nuovo_DBT_per_NIL"] = {"rho": round(float(r2.statistic), 2), "p": float(r2.pvalue)}
    r3 = spearmanr(nl.dbt_volume_netto_m3, nl.var_pop_2014_2024, nan_policy="omit")
    R["spearman_volume_netto_DBT_vs_var_popolazione"] = {"rho": round(float(r3.statistic), 2), "p": float(r3.pvalue)}
    s2 = nl.sort_values("dbt_volume_netto_m3", ascending=False)
    R["top10_nil_volume_netto_dbt"] = s2.head(10)[["nil", "dbt_volume_nuove_m3", "dbt_volume_sparite_m3", "dbt_volume_netto_m3", "dbt_variazione_volume_pct", "nuove_abitazioni_2014_2024"]].reset_index().to_dict("records")
nl["volume_nuovi_totale_m3"] = nl.volume_nuovi_m3
R["top10_nil_volume_nuovi_permessi"] = nl.sort_values("volume_nuovi_m3", ascending=False).head(10)[["nil", "volume_nuovi_m3", "nuove_abitazioni_2014_2024"]].reset_index().to_dict("records")
R["quota_volume_nuovi_top5_nil_pct"] = round(float(100 * nl.sort_values("volume_nuovi_m3", ascending=False).head(5).volume_nuovi_m3.sum() / nl.volume_nuovi_m3.sum()), 1)
if "dbt_grandi_volume_netto_m3" in nl:
    R["top10_nil_grandi_volume_netto_dbt"] = nl.sort_values("dbt_grandi_volume_netto_m3", ascending=False).head(10)[["nil", "dbt_grandi_nuove_n", "dbt_grandi_nuove_volume_m3", "dbt_grandi_sparite_volume_m3", "dbt_grandi_volume_netto_m3"]].reset_index().to_dict("records")
    R["bottom5_nil_grandi_volume_netto_dbt"] = nl.sort_values("dbt_grandi_volume_netto_m3").head(5)[["nil", "dbt_grandi_nuove_volume_m3", "dbt_grandi_sparite_volume_m3", "dbt_grandi_volume_netto_m3"]].reset_index().to_dict("records")
    R["nil_con_volume_2020_minore_2012"] = int((nl.dbt_variazione_volume_pct < 0).sum())
nl.drop(columns=["senza_nil_abitazioni", "volume_nuovi_totale_m3"]).reset_index().to_csv(pul("nil_costruzioni.csv"), index=False, sep=";")

# ---------------- C. grandi interventi (solo indirizzi pubblicabili: non persone fisiche)
tt["cluster"] = tt.indirizzo.str.lower().str.replace(r"[^a-z0-9 ]", " ", regex=True).str.split().str.join(" ")
big = tt[(tt.intervento == "nuovo_fabbricato")].groupby(["cluster", "anno"]).agg(indirizzo=("indirizzo", "first"), civico=("civico", "first"), nil=("nil", "first"),
        edifici=("id_modello", "size"), abitazioni=("abitazioni", "sum"), volume_m3=("volume_m3", "sum"), superficie_m2=("superficie_m2", "sum"),
        uso=("uso", "first"), tipo_titolo=("tipo_titolo", "first"), titolare=("titolare_categoria", "first"), pubblicabile=("indirizzo_pubblicabile", "min"),
        destinazione=("destinazione_economica", "first")).reset_index().drop(columns="cluster")
big = big.sort_values("volume_m3", ascending=False)
big.head(60).to_csv(pul("grandi_interventi_top60_volume.csv"), index=False, sep=";")
R["top15_interventi_per_volume"] = big[big.pubblicabile == 1].head(15)[["anno", "indirizzo", "civico", "nil", "uso", "edifici", "abitazioni", "volume_m3", "tipo_titolo", "titolare"]].to_dict("records")
R["top10_per_abitazioni"] = big[big.pubblicabile == 1].sort_values("abitazioni", ascending=False).head(10)[["anno", "indirizzo", "civico", "nil", "edifici", "abitazioni", "volume_m3", "tipo_titolo", "titolare"]].to_dict("records")
top10share = big.head(10).volume_m3.sum() / big.volume_m3.sum()
R["quota_volume_top10_interventi_pct"] = round(float(100 * top10share), 1)
R["quota_volume_top_1pct_interventi_pct"] = round(float(100 * big.head(max(1, len(big)//100)).volume_m3.sum() / big.volume_m3.sum()), 1)

# ---------------- D. periodo 2022-2024: mesi e semestri (nota di cronologia, non prova)
per = t[(t.anno >= 2021) & (t.anno <= 2024) & (t.intervento == "nuovo_fabbricato")].copy()
per["trim"] = per.anno.astype(str) + "-T" + ((per.mese - 1) // 3 + 1).astype(str)
tq = per.groupby("trim").agg(nuovi_fabbricati=("id_modello", "size"), abitazioni=("abitazioni", "sum"), volume_m3=("volume_m3", "sum"))
tq.reset_index().to_csv(pul("nuovi_per_trimestre_2021_2024.csv"), index=False, sep=";")
R["trimestri_2021_2024"] = tq.reset_index().to_dict("records")
mm = t[(t.anno >= 2021) & (t.anno <= 2024)].groupby(["anno", "mese"]).size().unstack(fill_value=0)
mm.to_csv(pul("titoli_per_mese_2021_2024.csv"), sep=";")
R["mesi_con_zero_titoli_2024"] = [int(m) for m in range(1, 13) if m not in mm.loc[2024].index or mm.loc[2024].get(m, 0) == 0]
# tipo titolo per anno (nuovi fabbricati): quota SCIA alternativa
q = nuovi.groupby(["anno", "tipo_titolo"]).size().unstack(fill_value=0)
tot_ = q.sum(axis=1)
q["quota_scia_alt_pct"] = (100 * q.get("SCIA alternativa", 0) / tot_).round(1)
q["quota_scia_tutte_pct"] = (100 * (q.get("SCIA alternativa", 0) + q.get("SCIA", 0)) / tot_).round(1)   # 'SCIA' e 'SCIA alternativa' si scambiano nel 2018-2020: vanno sommate
q.reset_index().to_csv(pul("nuovi_per_tipo_titolo_anno.csv"), index=False, sep=";")
R["nuovi_per_tipo_titolo_anno"] = q.reset_index().to_dict("records")
# confronto 2022/2023 -> 2024 Comune vs ISTAT provincia
cmp = {}
for a, b in [(2022, 2024), (2023, 2024)]:
    cmp[f"{a}->{b}"] = {"comune_nuovi_fabbricati_res_var_pct": round(100 * (y.loc[b, "nuovi_fabbricati_res"] / y.loc[a, "nuovi_fabbricati_res"] - 1), 1),
                         "comune_nuove_abitazioni_var_pct": round(100 * (y.loc[b, "nuove_abitazioni_in_nuovi_fabbricati"] / y.loc[a, "nuove_abitazioni_in_nuovi_fabbricati"] - 1), 1),
                         "istat_provincia_abitazioni_var_pct": round(100 * (y.loc[b, "istat_prov_MI_abitazioni_nuovi_res"] / y.loc[a, "istat_prov_MI_abitazioni_nuovi_res"] - 1), 1),
                         "istat_provincia_fabbricati_var_pct": round(100 * (y.loc[b, "istat_prov_MI_nuovi_fabbricati_res"] / y.loc[a, "istat_prov_MI_nuovi_fabbricati_res"] - 1), 1),
                         "istat_capoluoghi_oltre500k_abitazioni_var_pct": round(100 * (y.loc[b, "istat_capoluoghi_oltre500k_abitazioni_nuovi_res"] / y.loc[a, "istat_capoluoghi_oltre500k_abitazioni_nuovi_res"] - 1), 1)}
R["confronto_2024_comune_vs_istat"] = cmp
# ISTAT 2025 (solo provincia)
R["istat_2025_provincia_MI"] = {"abitazioni_nuovi_res": float(y.loc[2024:2024, "istat_prov_MI_abitazioni_nuovi_res"].iloc[0]) if False else float(ist(rc, "ITC45", "NUMDW").get(2025)),
                                "fabbricati_res": float(ist(rc, "ITC45", "NRB_NUM").get(2025)), "abitazioni_2024": float(ist(rc, "ITC45", "NUMDW").get(2024))}
# anno medio per mese: titolari
R["titolare_categoria_nuovi"] = nuovi.titolare_categoria.value_counts().to_dict()
r22 = nuovi[(nuovi.uso == "residenziale") & (nuovi.anno >= 2022)]
R["ricostruzioni_nuovi_res_2022_2024"] = {"edifici": int(len(r22)), "con_campo_compilato": int(r22.abbattimento_ricostruzione.notna().sum()),
    "ricostruzioni": int((r22.abbattimento_ricostruzione == "si").sum()),
    "quota_pct": round(float(100 * (r22.abbattimento_ricostruzione == "si").sum() / r22.abbattimento_ricostruzione.notna().sum()), 1),
    "abitazioni_ricostruzioni": float(r22[r22.abbattimento_ricostruzione == "si"].abitazioni.sum()), "volume_ricostruzioni_m3": float(r22[r22.abbattimento_ricostruzione == "si"].volume_m3.sum()),
    "abitazioni_non_sostitutivi": float(r22[r22.abbattimento_ricostruzione == "no"].abitazioni.sum()), "volume_non_sostitutivi_m3": float(r22[r22.abbattimento_ricostruzione == "no"].volume_m3.sum()),
    "scia_alt_tra_ricostruzioni": int(((r22.abbattimento_ricostruzione == "si") & (r22.tipo_titolo == "SCIA alternativa")).sum()),
    "scia_alt_tra_non_sostitutivi": int(((r22.abbattimento_ricostruzione == "no") & (r22.tipo_titolo == "SCIA alternativa")).sum())}
r21 = nuovi[(nuovi.uso == "residenziale") & (nuovi.anno == 2021)]
R["campo_abbattimento_2021"] = {"edifici": int(len(r21)), "compilati": int(r21.abbattimento_ricostruzione.notna().sum()), "si": int((r21.abbattimento_ricostruzione == "si").sum())}
R["tipo_titolo_nuovi_res"] = nuovi[nuovi.uso == "residenziale"].tipo_titolo.value_counts(dropna=False).to_dict()
R["piani_nuovi_res_mediana"] = float(nuovi[nuovi.uso == "residenziale"].piani.median())
R["abitazioni_per_edificio_mediana"] = float(nuovi[nuovi.uso == "residenziale"].abitazioni.median())

json.dump(R, open(pul("riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print(json.dumps(R, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))[:14000])
