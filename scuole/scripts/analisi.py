"""Riepiloghi filone Scuole (fase 1). Uso: python -I -X utf8 analisi.py <abs scuole> <abs milano-in-dati>
Legge pulito/*.csv, scrive altre tabelle in pulito/ e pulito/riepilogo.json. Nessun giudizio: solo confronti."""
import sys, json, os
import pandas as pd, numpy as np
S, P = sys.argv[1], sys.argv[2]
OUT = f"{S}/pulito"
RJ = {}
C = pd.read_csv(f"{OUT}/comune_scuole_anno.csv", sep=";", dtype={"codice_comune": str})
M = pd.read_csv(f"{OUT}/miur_scuole_anno.csv", sep=";", dtype={"codice_mecc": str})
G = pd.read_csv(f"{OUT}/miur_scuole_anagrafica.csv", sep=";", dtype=str)
SL = pd.read_csv(f"{OUT}/serie_lunga_ordine_gestione.csv", sep=";")
RN = pd.read_csv(f"{OUT}/residenti_nil_fascia_cittadinanza_ds27.csv", sep=";")
R223 = pd.read_csv(f"{OUT}/residenti_per_eta_ds223.csv", sep=";")
BN = pd.read_csv(f"{P}/nomi-bambini/pulito/nascite_milano_ds289.csv")
ORD = ["infanzia", "primaria", "sec1", "sec2"]
BAND = {"infanzia": ["3-5"], "primaria": ["6-10"], "sec1": ["11-13"], "sec2": ["14-18"]}
rnd = lambda x, n=1: None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), n)

# 1. Iscritti nel tempo per ordine e gruppo di gestione ----------------------------------------------------------
a = C.groupby(["anno_scolastico", "anno_inizio", "ordine", "gruppo_gestione"]).agg(scuole=("iscritti", "size"), classi=("classi", "sum"), iscritti=("iscritti", "sum"),
    cittadinanza_non_italiana=("cittadinanza_non_italiana", "sum")).reset_index()
a["fonte"] = "Comune ANASCO ds224/225/226"
b = M[M.ordine == "sec2"].groupby(["anno_scolastico", "anno_inizio", "ordine", "tipo"]).agg(scuole=("iscritti", "size"), classi=("classi", "sum"), iscritti=("iscritti", "sum"),
    cittadinanza_non_italiana=("cittadinanza_non_italiana", "sum")).reset_index().rename(columns={"tipo": "gruppo_gestione"})
b["fonte"] = "MIM open data (solo statali e paritarie)"
ISC = pd.concat([a, b], ignore_index=True)
ISC["quota_non_italiana_pct"] = (100 * ISC.cittadinanza_non_italiana / ISC.iscritti).round(2)
ISC.sort_values(["ordine", "anno_inizio", "gruppo_gestione"]).to_csv(f"{OUT}/iscritti_per_ordine_gruppo_anno.csv", index=False, sep=";")
tot = ISC.groupby(["anno_inizio", "ordine"]).iscritti.sum().unstack()
RJ["iscritti_totali_comune_2009_2024"] = {o: {int(y): int(v) for y, v in tot[o].dropna().items()} for o in ["infanzia", "primaria", "sec1"]}
RJ["iscritti_sec2_miur_2015_2024"] = {int(y): int(v) for y, v in tot["sec2"].dropna().items()}
# serie lunga (somma dei municipi) per sec2 e per tutti (2002-)
SL["pubblico"] = SL.gestione.str.lower().isin(["pubblica (statale+comunale)", "statale"])
lung = SL.groupby(["anno_inizio", "ordine"]).alunni.sum().unstack()
RJ["serie_lunga_ds102_105"] = {o: {int(y): int(v) for y, v in lung[o].dropna().items()} for o in ORD}
for o in ORD:
    s = lung[o].dropna()
    RJ[f"picco_{o}"] = {"anno": int(s.idxmax()), "iscritti": int(s.max()), "ultimo_anno": int(s.index.max()), "ultimo": int(s.iloc[-1]), "var_pct_dal_picco": rnd(100 * (s.iloc[-1] / s.max() - 1))}

# statale vs paritaria: quote nel tempo (Comune, 3 ordini; sec2 da MIM)
q = ISC.pivot_table(index=["ordine", "anno_inizio"], columns="gruppo_gestione", values="iscritti", aggfunc="sum").fillna(0)
q["totale"] = q.sum(axis=1)
for c_ in [c for c in q.columns if c != "totale"]: q[f"quota_{c_}_pct"] = (100 * q[c_] / q.totale).round(2)
q.reset_index().to_csv(f"{OUT}/quote_statale_paritaria.csv", index=False, sep=";")
RJ["quota_statale_pct"] = {o: {int(y): rnd(q.loc[(o, y), "quota_statale_pct"]) for y in sorted(q.loc[o].index)} for o in ORD}
# dettaglio gestione per le 3 scuole del Comune
g3 = C.groupby(["ordine", "anno_inizio", "gestione"]).iscritti.sum().unstack().fillna(0)
g3.reset_index().to_csv(f"{OUT}/iscritti_per_gestione_dettaglio.csv", index=False, sep=";")

# 2. Stranieri (cittadinanza non italiana) nel tempo: Comune, MIM, residenti ------------------------------------------
cc = C.groupby(["anno_inizio", "ordine"]).agg(iscritti=("iscritti", "sum"), non_it=("cittadinanza_non_italiana", "sum"), nd=("cittadinanza_nd", "sum"), nati_estero=("nati_estero_aree_note", "sum"), nati_altro_nd=("nati_altro_o_nd", "sum"), nati_italia=("nati_italia", "sum")).reset_index()
cc["quota_non_italiana_comune_pct"] = (100 * cc.non_it / cc.iscritti).round(2)
cc["quota_nati_fuori_italia_pct"] = (100 * cc.nati_estero / cc.iscritti).round(2)
mm = M.groupby(["anno_inizio", "ordine"]).agg(iscritti_mim=("iscritti", "sum"), non_it_mim=("cittadinanza_non_italiana", "sum"), tot_cit=("tot_cittadinanza", "sum")).reset_index()
mm["quota_non_italiana_mim_pct"] = (100 * mm.non_it_mim / mm.tot_cit).round(2)
sc = cc.merge(mm, on=["anno_inizio", "ordine"], how="outer")
res = RN.groupby(["anno", "fascia_eta"])[["stranieri", "italiani"]].sum().reset_index()
res["quota_non_italiana_residenti_pct"] = (100 * res.stranieri / (res.stranieri + res.italiani)).round(2)
inv = {v[0]: k for k, v in BAND.items()}
res["ordine"] = res.fascia_eta.map(inv)
sc = sc.merge(res[res.ordine.notna()][["anno", "ordine", "quota_non_italiana_residenti_pct", "stranieri", "italiani"]].rename(columns={"anno": "anno_inizio", "stranieri": "residenti_fascia_non_italiani", "italiani": "residenti_fascia_italiani"}), on=["anno_inizio", "ordine"], how="left")
sc.to_csv(f"{OUT}/stranieri_serie_per_ordine.csv", index=False, sep=";")
y = 2024
RJ["stranieri_2024"] = {r.ordine: {"comune": rnd(r.quota_non_italiana_comune_pct), "mim": rnd(r.quota_non_italiana_mim_pct), "residenti_fascia": rnd(r.quota_non_italiana_residenti_pct), "nati_fuori_italia_comune": rnd(r.quota_nati_fuori_italia_pct)} for r in sc[sc.anno_inizio == y].itertuples()}
# confronto statali MIM vs Comune (stessa scuola agganciata per indirizzo)
mg = M.merge(G[["codice_mecc", "ordine", "codice_comune_corrispondente"]], on=["codice_mecc", "ordine"])
cmp_ = []
for yy in sorted(M.anno_inizio.unique()):
    for o in ["infanzia", "primaria", "sec1"]:
        x = mg[(mg.anno_inizio == yy) & (mg.ordine == o) & (mg.tipo == "statale")].merge(C[(C.anno_inizio == yy) & (C.ordine == o)], left_on="codice_comune_corrispondente", right_on="codice_comune", suffixes=("_m", "_c"))
        if len(x): cmp_.append(dict(anno_inizio=yy, ordine=o, scuole_agganciate=len(x), iscritti_mim=int(x.iscritti_m.sum()), iscritti_comune=int(x.iscritti_c.sum()), non_it_mim=int(x.cittadinanza_non_italiana_m.sum()), non_it_comune=int(x.cittadinanza_non_italiana_c.sum()),
                                      quota_mim=rnd(100 * x.cittadinanza_non_italiana_m.sum() / x.tot_cittadinanza.sum(), 2), quota_comune=rnd(100 * x.cittadinanza_non_italiana_c.sum() / x.iscritti_c.sum(), 2)))
CM = pd.DataFrame(cmp_); CM.to_csv(f"{OUT}/confronto_MIM_Comune_statali_agganciate.csv", index=False, sep=";")
RJ["confronto_MIM_Comune_statali_agganciate_2024_solo_primaria_affidabile"] = CM[(CM.anno_inizio == 2024) & (CM.ordine == "primaria")].to_dict("records")
# confronto sui totali (senza aggancio scuola per scuola): quota di cittadinanza non italiana, per ordine e statale/paritaria
rows = []
cm_ = C.copy(); cm_["tipo"] = np.where(cm_.gestione == "statale", "statale", np.where(cm_.gestione == "privata_non_paritaria", "privata_non_paritaria_(solo_Comune)", "paritaria"))
for (yy, o, tp), g in cm_.groupby(["anno_inizio", "ordine", "tipo"]):
    mm2 = M[(M.anno_inizio == yy) & (M.ordine == o) & (M.tipo == tp)]
    rows.append(dict(anno_inizio=yy, ordine=o, tipo=tp, iscritti_comune=int(g.iscritti.sum()), quota_comune_pct=rnd(100 * g.cittadinanza_non_italiana.sum() / g.iscritti.sum(), 2),
                     iscritti_mim=int(mm2.iscritti.sum()) if len(mm2) else None, quota_mim_pct=rnd(100 * mm2.cittadinanza_non_italiana.sum() / mm2.tot_cittadinanza.sum(), 2) if len(mm2) and mm2.tot_cittadinanza.sum() else None))
CQ = pd.DataFrame(rows); CQ["differenza_pp_mim_meno_comune"] = (CQ.quota_mim_pct - CQ.quota_comune_pct).round(2)
CQ.to_csv(f"{OUT}/confronto_quota_stranieri_MIM_vs_Comune_totali.csv", index=False, sep=";")
RJ["confronto_quota_MIM_vs_Comune_2024"] = CQ[CQ.anno_inizio == 2024].to_dict("records")
RJ["confronto_quota_MIM_vs_Comune_2018"] = CQ[CQ.anno_inizio == 2018].to_dict("records")

# 3. Nascite -> prima classe primaria; residenti per eta' -> iscritti -------------------------------------------------
p1 = M[M.ordine == "primaria"].groupby("anno_inizio").iscritti_anno_corso_1.sum()
rr = R223.pivot_table(index="anno", columns="eta", values="residenti", aggfunc="sum")
nati = BN.set_index("anno")
rows = []
for bcoh in range(2003, 2021):
    r = dict(coorte=bcoh, nati_avvenuti_a_milano=int(nati.loc[bcoh, "nati_avvenuti_a_milano"]), di_cui_entrambi_genitori_stranieri=int(nati.loc[bcoh, "di_cui_entrambi_genitori_stranieri"]))
    r["residenti_eta0_a_fine_anno"] = int(rr.loc[bcoh, 0]) if bcoh in rr.index else None
    r["prima_primaria_a_s_coorte_piu_6"] = int(p1[bcoh + 6]) if (bcoh + 6) in p1.index else None
    r["residenti_eta5_a_fine_coorte_piu_5"] = int(rr.loc[bcoh + 5, 5]) if (bcoh + 5) in rr.index else None
    rows.append(r)
NB = pd.DataFrame(rows)
NB["prima_primaria_su_nati"] = (NB.prima_primaria_a_s_coorte_piu_6 / NB.nati_avvenuti_a_milano).round(3)
NB["prima_primaria_su_residenti_eta5"] = (NB.prima_primaria_a_s_coorte_piu_6 / NB.residenti_eta5_a_fine_coorte_piu_5).round(3)
NB.to_csv(f"{OUT}/nascite_e_prima_primaria.csv", index=False, sep=";")
RJ["nascite_milano"] = {int(r.coorte): int(r.nati_avvenuti_a_milano) for r in NB.itertuples()}
RJ["rapporto_prima_primaria_su_residenti_eta5"] = {int(r.coorte): r.prima_primaria_su_residenti_eta5 for r in NB.itertuples() if pd.notna(r.prima_primaria_su_residenti_eta5)}
RJ["rapporto_prima_primaria_su_nati"] = {int(r.coorte): r.prima_primaria_su_nati for r in NB.itertuples() if pd.notna(r.prima_primaria_su_nati)}
# iscritti / residenti nella fascia (tutta la citta')
rows = []
for yy in sorted(RN.anno.unique()):
    for o in ORD:
        f = RN[(RN.anno == yy) & (RN.fascia_eta.isin(BAND[o]))]
        rs = int((f.stranieri + f.italiani).sum())
        isc = ISC[(ISC.anno_inizio == yy) & (ISC.ordine == o)].iscritti.sum()
        rows.append(dict(anno=yy, ordine=o, residenti_fascia=rs, iscritti=int(isc) if isc else None, rapporto=rnd(isc / rs, 3) if isc and rs else None))
RI = pd.DataFrame(rows); RI.to_csv(f"{OUT}/iscritti_su_residenti_fascia.csv", index=False, sep=";")
RJ["residenti_fascia_eta_citta"] = {o: {int(r.anno): r.residenti_fascia for r in RI[RI.ordine == o].itertuples() if r.anno in (2012, 2015, 2018, 2021, 2024, 2025)} for o in ORD}
RJ["rapporto_iscritti_su_residenti_2024"] = {r.ordine: r.rapporto for r in RI[RI.anno == 2024].itertuples()}

# 4. Scuole che si svuotano / si riempiono (Comune, 2015/16 -> 2024/25) ---------------------------------------------
a0 = C[C.anno_inizio == 2015][["ordine", "codice_comune", "denominazione", "indirizzo", "gestione", "gruppo_gestione", "id_nil", "nil", "iscritti"]]
a1 = C[C.anno_inizio == 2024][["ordine", "codice_comune", "iscritti", "classi", "cittadinanza_non_italiana", "capienza"]]
mm_ = a0.merge(a1, on=["ordine", "codice_comune"], how="outer", suffixes=("_2015", "_2024"), indicator=True)
last_den = C.sort_values("anno_inizio").groupby(["ordine", "codice_comune"]).denominazione.last().rename("den_ultima")
mm_ = mm_.merge(last_den, on=["ordine", "codice_comune"], how="left")
mm_["situazione"] = mm_._merge.map({"both": "presente_in_entrambi", "left_only": "non_piu_presente_2024", "right_only": "nuova_o_riaperta_2024"}).astype(str)
mm_["variazione"] = mm_.iscritti_2024 - mm_.iscritti_2015
mm_["variazione_pct"] = (100 * mm_.variazione / mm_.iscritti_2015).round(1)
def cls(r):
    if r.situazione != "presente_in_entrambi": return r.situazione
    if r.variazione_pct <= -20: return "si_svuota_oltre_20pct"
    if r.variazione_pct <= -10: return "cala_10_20pct"
    if r.variazione_pct < 10: return "stabile_entro_10pct"
    if r.variazione_pct < 20: return "cresce_10_20pct"
    return "si_riempie_oltre_20pct"
mm_["classe_variazione"] = mm_.apply(cls, axis=1)
mm_["piccola_2015_sotto_30"] = mm_.iscritti_2015 < 30
mm_.drop(columns="_merge").to_csv(f"{OUT}/scuole_variazione_2015_2024.csv", index=False, sep=";")
vv = mm_[mm_.situazione == "presente_in_entrambi"]
RJ["variazione_scuole_2015_2024"] = {o: vv[vv.ordine == o].classe_variazione.value_counts().to_dict() for o in ["infanzia", "primaria", "sec1"]}
RJ["scuole_non_piu_presenti_o_nuove"] = {o: {"non_piu": int((mm_[(mm_.ordine == o)].situazione == "non_piu_presente_2024").sum()), "nuove": int((mm_[(mm_.ordine == o)].situazione == "nuova_o_riaperta_2024").sum())} for o in ["infanzia", "primaria", "sec1"]}
gv = vv.groupby(["ordine", "gruppo_gestione"]).agg(scuole=("variazione", "size"), isc2015=("iscritti_2015", "sum"), isc2024=("iscritti_2024", "sum")).reset_index()
gv["variazione_pct"] = (100 * (gv.isc2024 / gv.isc2015 - 1)).round(1)
gv.to_csv(f"{OUT}/variazione_per_ordine_gruppo_2015_2024_stessi_codici.csv", index=False, sep=";")
RJ["variazione_2015_2024_stessi_codici"] = gv.to_dict("records")
# massimi cali / crescite in valore assoluto (scuole con almeno 100 iscritti nel 2015)
big = vv[vv.iscritti_2015 >= 100].sort_values("variazione")
RJ["scuole_maggiori_cali_assoluti"] = big.head(8)[["ordine", "den_ultima", "gruppo_gestione", "nil", "iscritti_2015", "iscritti_2024", "variazione"]].to_dict("records")
RJ["scuole_maggiori_crescite_assolute"] = big.tail(8)[["ordine", "den_ultima", "gruppo_gestione", "nil", "iscritti_2015", "iscritti_2024", "variazione"]].to_dict("records")
# occupazione statali (iscritti / capienza dichiarata), primaria e sec1
occ = C[(C.anno_inizio == 2024) & (C.gestione == "statale") & (C.ordine.isin(["primaria", "sec1"])) & (C.capienza > 0)].copy()
occ["occupazione"] = occ.iscritti / occ.capienza
RJ["occupazione_statali_2024"] = {o: {"scuole": int((occ.ordine == o).sum()), "mediana": rnd(occ[occ.ordine == o].occupazione.median(), 2), "sopra_100pct": int((occ[occ.ordine == o].occupazione > 1).sum()), "sotto_70pct": int((occ[occ.ordine == o].occupazione < 0.7).sum())} for o in ["primaria", "sec1"]}
# per NIL (sede della scuola): iscritti 2015 e 2024 e variazione, per ordine
nl = C[C.anno_inizio.isin([2015, 2024])].groupby(["id_nil", "nil", "ordine", "anno_inizio"]).iscritti.sum().unstack().reset_index().rename(columns={2015: "iscritti_2015", 2024: "iscritti_2024"})
nl["variazione_pct"] = (100 * (nl.iscritti_2024 / nl.iscritti_2015 - 1)).round(1)
nl.to_csv(f"{OUT}/nil_iscritti_variazione_2015_2024.csv", index=False, sep=";")
nlt = C[C.anno_inizio.isin([2015, 2024])].groupby(["id_nil", "nil", "anno_inizio"]).iscritti.sum().unstack().reset_index().rename(columns={2015: "iscritti_2015", 2024: "iscritti_2024"})
nlt["variazione_pct"] = (100 * (nlt.iscritti_2024 / nlt.iscritti_2015 - 1)).round(1)
RJ["nil_con_piu_calo_totale_3ordini"] = nlt[nlt.iscritti_2015 >= 500].sort_values("variazione_pct").head(5).to_dict("records")
RJ["nil_con_piu_crescita_totale_3ordini"] = nlt[nlt.iscritti_2015 >= 500].sort_values("variazione_pct").tail(5).to_dict("records")
RJ["nil_con_iscritti_in_calo_su_nil_con_iscritti"] = {"in_calo": int((nlt.variazione_pct < 0).sum()), "totale": int(nlt.variazione_pct.notna().sum())}

# 5. Concentrazione degli stranieri: scuole vs quartiere ---------------------------------------------------------------
def D(af, it):
    af = np.asarray(af, float); it = np.asarray(it, float)
    return float(0.5 * np.abs(af / af.sum() - it / it.sum()).sum())
rows = []
for yy in [2012, 2015, 2018, 2021, 2024]:
    for o in ["infanzia", "primaria", "sec1"]:
        c = C[(C.anno_inizio == yy) & (C.ordine == o) & (C.iscritti > 0)]
        r = RN[(RN.anno == yy) & (RN.fascia_eta.isin(BAND[o]))].groupby("id_nil")[["stranieri", "italiani"]].sum()
        gnil = c.groupby("id_nil")[["cittadinanza_non_italiana", "cittadinanza_italiana"]].sum()
        sh = c.cittadinanza_non_italiana / c.iscritti
        pub = c[c.gestione.isin(["statale", "comunale"])]
        rows.append(dict(anno_inizio=yy, ordine=o, scuole=len(c), quota_pupilli_pct=rnd(100 * c.cittadinanza_non_italiana.sum() / c.iscritti.sum()),
                         quota_residenti_fascia_pct=rnd(100 * r.stranieri.sum() / (r.stranieri.sum() + r.italiani.sum())),
                         D_tra_scuole=rnd(D(c.cittadinanza_non_italiana, c.cittadinanza_italiana), 3),
                         D_tra_scuole_solo_pubbliche=rnd(D(pub.cittadinanza_non_italiana, pub.cittadinanza_italiana), 3),
                         D_tra_gestioni=rnd(D(c.groupby("gestione").cittadinanza_non_italiana.sum(), c.groupby("gestione").cittadinanza_italiana.sum()), 3),
                         D_tra_NIL_per_sede_scuola=rnd(D(gnil.cittadinanza_non_italiana, gnil.cittadinanza_italiana), 3),
                         D_tra_NIL_residenti_fascia=rnd(D(r.stranieri, r.italiani), 3),
                         scuole_oltre_50pct=int((sh > .5).sum()), quota_stranieri_in_scuole_oltre_50pct=rnd(100 * c.cittadinanza_non_italiana[sh > .5].sum() / c.cittadinanza_non_italiana.sum()),
                         scuole_sotto_10pct=int((sh < .1).sum()), quota_italiani_in_scuole_sotto_10pct=rnd(100 * c.cittadinanza_italiana[sh < .1].sum() / c.cittadinanza_italiana.sum())))
CI = pd.DataFrame(rows); CI.to_csv(f"{OUT}/concentrazione_indici.csv", index=False, sep=";")
RJ["concentrazione_2024"] = CI[CI.anno_inizio == 2024].to_dict("records")
RJ["concentrazione_2012"] = CI[CI.anno_inizio == 2012].to_dict("records")
# quota stranieri per gestione 2024 (Comune)
gg = C[C.anno_inizio == 2024].groupby(["ordine", "gestione"]).agg(scuole=("iscritti", "size"), iscritti=("iscritti", "sum"), non_it=("cittadinanza_non_italiana", "sum")).reset_index()
gg["quota_non_italiana_pct"] = (100 * gg.non_it / gg.iscritti).round(1)
gg.to_csv(f"{OUT}/stranieri_per_gestione_2024.csv", index=False, sep=";")
RJ["stranieri_per_gestione_2024"] = gg.to_dict("records")
# per scuola vs media del quartiere (2024): tre riferimenti
rows = []
c24 = C[(C.anno_inizio == 2024) & (C.iscritti > 0)].copy()
for o in ["infanzia", "primaria", "sec1"]:
    c = c24[c24.ordine == o].copy()
    r = RN[(RN.anno == 2024) & (RN.fascia_eta.isin(BAND[o]))].groupby("id_nil")[["stranieri", "italiani"]].sum()
    r["quota_residenti_fascia_pct"] = 100 * r.stranieri / (r.stranieri + r.italiani)
    gnil = c.groupby("id_nil").agg(isc_nil=("iscritti", "sum"), non_nil=("cittadinanza_non_italiana", "sum"), n_nil=("iscritti", "size"))
    c = c.merge(gnil, left_on="id_nil", right_index=True, how="left").merge(r[["quota_residenti_fascia_pct"]], left_on="id_nil", right_index=True, how="left")
    c["quota_scuola_pct"] = 100 * c.cittadinanza_non_italiana / c.iscritti
    # media delle ALTRE scuole dello stesso ordine nello stesso NIL
    c["quota_altre_scuole_nil_pct"] = np.where(c.n_nil > 1, 100 * (c.non_nil - c.cittadinanza_non_italiana) / (c.isc_nil - c.iscritti), np.nan)
    quota_citta = 100 * c.cittadinanza_non_italiana.sum() / c.iscritti.sum()
    c["quota_citta_ordine_pct"] = quota_citta
    c["diff_vs_residenti_nil_pp"] = c.quota_scuola_pct - c.quota_residenti_fascia_pct
    c["diff_vs_altre_scuole_nil_pp"] = c.quota_scuola_pct - c.quota_altre_scuole_nil_pct
    rows.append(c[["anno_scolastico", "ordine", "codice_comune", "denominazione", "indirizzo", "gestione", "id_nil", "nil", "iscritti", "cittadinanza_non_italiana", "quota_scuola_pct", "quota_residenti_fascia_pct", "quota_altre_scuole_nil_pct", "quota_citta_ordine_pct", "diff_vs_residenti_nil_pp", "diff_vs_altre_scuole_nil_pp", "n_nil"]].rename(columns={"n_nil": "scuole_stesso_ordine_nel_nil"}))
SQ = pd.concat(rows); SQ = SQ.round(2)
SQ.to_csv(f"{OUT}/stranieri_scuole_vs_nil_2024.csv", index=False, sep=";")
def pc(s, p): return rnd(np.nanpercentile(s, p))
RJ["scuole_vs_residenti_nil_2024"] = {}
for o in ["infanzia", "primaria", "sec1"]:
    x = SQ[SQ.ordine == o]
    big_ = x[x.iscritti >= 50]
    RJ["scuole_vs_residenti_nil_2024"][o] = {"scuole": len(x), "scuole_50plus_iscritti": len(big_),
        "diff_vs_residenti_nil_pp_p10_p50_p90": [pc(big_.diff_vs_residenti_nil_pp, 10), pc(big_.diff_vs_residenti_nil_pp, 50), pc(big_.diff_vs_residenti_nil_pp, 90)],
        "scuole_50plus_con_oltre_20pp_sopra_residenti": int((big_.diff_vs_residenti_nil_pp > 20).sum()), "scuole_50plus_con_oltre_20pp_sotto_residenti": int((big_.diff_vs_residenti_nil_pp < -20).sum()),
        "corr_scuola_vs_residenti_nil": rnd(big_[["quota_scuola_pct", "quota_residenti_fascia_pct"]].corr().iloc[0, 1], 2)}
# stesso NIL: scuole vicine con quote molto diverse (stesso ordine, statali+comunali)
dif = []
for (o, nid), g in c24[c24.gestione.isin(["statale", "comunale"])].groupby(["ordine", "id_nil"]):
    g = g[g.iscritti >= 50]
    if len(g) >= 2:
        q_ = 100 * g.cittadinanza_non_italiana / g.iscritti
        dif.append(dict(ordine=o, id_nil=nid, nil=g.nil.iloc[0], scuole=len(g), quota_min=rnd(q_.min()), quota_max=rnd(q_.max()), divario_pp=rnd(q_.max() - q_.min())))
DF = pd.DataFrame(dif); DF.to_csv(f"{OUT}/nil_divario_tra_scuole_pubbliche_2024.csv", index=False, sep=";")
RJ["nil_divario_tra_scuole_pubbliche_2024"] = {o: {"nil_con_2plus_scuole": int((DF.ordine == o).sum()), "divario_mediano_pp": rnd(DF[DF.ordine == o].divario_pp.median()), "nil_con_divario_oltre_30pp": int((DF[DF.ordine == o].divario_pp > 30).sum())} for o in ["infanzia", "primaria", "sec1"]}
# per NIL: quota 2024 pupilli (sede scuola) e residenti
nilq = []
for o in ["infanzia", "primaria", "sec1"]:
    c = c24[c24.ordine == o].groupby(["id_nil", "nil"], as_index=False).agg(scuole=("iscritti", "size"), iscritti=("iscritti", "sum"), non_it=("cittadinanza_non_italiana", "sum"))
    c["quota_pupilli_pct"] = (100 * c.non_it / c.iscritti).round(1)
    r = RN[(RN.anno == 2024) & (RN.fascia_eta.isin(BAND[o]))].groupby("id_nil")[["stranieri", "italiani"]].sum().reset_index()
    r["quota_residenti_fascia_pct"] = (100 * r.stranieri / (r.stranieri + r.italiani)).round(1)
    r["residenti_fascia"] = r.stranieri + r.italiani
    c = c.merge(r[["id_nil", "quota_residenti_fascia_pct", "residenti_fascia"]], on="id_nil", how="outer"); c["ordine"] = o
    nilq.append(c)
pd.concat(nilq).to_csv(f"{OUT}/nil_stranieri_2024.csv", index=False, sep=";")

# 6. Secondaria II grado per tipo (solo statali, dalla tipologia dell'anagrafe MIM) + stranieri -----------------------------
s2 = M[(M.ordine == "sec2")].copy()
def tipo2(r):
    t = str(r.tipologia).upper()
    if r.tipo != "statale": return "paritarie (tipo non indicato)"
    if t.startswith("LICEO") or "MAGISTRALE" in t: return "licei e magistrali"
    if "TECNICO" in t or t.startswith("IST TEC"): return "istituti tecnici"
    if t.startswith("IST PROF"): return "istituti professionali"
    return "altro/istituti superiori misti"
s2["tipo_sec2"] = s2.apply(tipo2, axis=1)
t2 = s2.groupby(["anno_inizio", "tipo_sec2"]).agg(iscritti=("iscritti", "sum"), non_it=("cittadinanza_non_italiana", "sum"), scuole=("iscritti", "size")).reset_index()
t2["quota_non_italiana_pct"] = (100 * t2.non_it / t2.iscritti).round(1)
t2.to_csv(f"{OUT}/sec2_per_tipo_stranieri.csv", index=False, sep=";")
RJ["sec2_per_tipo_2024"] = t2[t2.anno_inizio == 2024].to_dict("records")
RJ["sec2_per_tipo_2015"] = t2[t2.anno_inizio == 2015].to_dict("records")

json.dump(RJ, open(f"{OUT}/riepilogo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
print(json.dumps(RJ, ensure_ascii=False, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
