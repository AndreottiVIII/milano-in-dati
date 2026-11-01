"""Riepiloghi della fase 1: serie armonizzata degli alloggi ALER vuoti, quote sul totale delle abitazioni, domande/assegnazioni, Municipi e NIL.
Uso: python -I -X utf8 09_riepilogo.py <case-popolari> <milano-in-dati>   (percorsi assoluti)
Scrive in pulito/: aler_vuoti_serie_armonizzata.csv, quote_su_abitazioni.csv, domande_per_alloggio.csv, aler_stabili_per_municipio.csv, nil_ald.csv, riepilogo.json"""
import sys, os, json
import pandas as pd

base, root = sys.argv[1], sys.argv[2]
P = os.path.join(base, "pulito")
R = {}

# 1. ALER: serie armonizzata dei vuoti. Dal 2022 ALER espone "demolizione", "vendita", "valorizzazione" come voci a parte, fuori dal totale "sfitti";
#    fino al 2021 la vendita (e nel 2021 la valorizzazione) stava dentro "sfitti". Controllo: contratto + piani valorizzazione + senza contratto + tutti i vuoti = totale ALER.
s = pd.read_csv(os.path.join(P, "aler_sfitti_serie.csv"))
w = s.pivot_table(index="anno", columns="voce", values="n_alloggi", aggfunc="first")
g = lambda c: w[c].fillna(0) if c in w.columns else 0
out = pd.DataFrame(index=w.index)
out["totale_ALER_canone_sociale"] = w["totale ALER a canone sociale"]
out["con_contratto"] = g("canone sociale con contratto") + g("canone sociale con contratto (piani di valorizzazione)")
out["occupati_senza_titolo"] = w["senza contratto (occupati senza titolo)"]
out["sfitti_come_scritti_da_ALER"] = w["sfitti (totale)"]
out["extra_fuori_da_sfitti_demolizione"] = g("sfitti: in fase di demolizione").where(out.index >= 2022, 0)
extra_v = g("sfitti: destinati a piani di vendita").where(out.index >= 2022, 0)
extra_val = g("sfitti: destinati a piani di valorizzazione").where(out.index >= 2022, 0)
out["extra_fuori_da_sfitti_vendita"] = extra_v
out["extra_fuori_da_sfitti_valorizzazione"] = extra_val
out["vuoti_totali_armonizzati"] = out.sfitti_come_scritti_da_ALER + out.extra_fuori_da_sfitti_demolizione + extra_v + extra_val
out["controllo_somma"] = out.con_contratto + out.occupati_senza_titolo + out.vuoti_totali_armonizzati
out["scarto_su_totale"] = out.controllo_somma - out.totale_ALER_canone_sociale
out["vuoti_%_del_totale"] = (100 * out.vuoti_totali_armonizzati / out.totale_ALER_canone_sociale).round(1)
out["sfitti_ALER_%_del_totale"] = (100 * out.sfitti_come_scritti_da_ALER / out.totale_ALER_canone_sociale).round(1)
out["in_ristrutturazione"] = w["sfitti: in corso di ristrutturazione"]
out["in_riassegnazione"] = w["sfitti: in corso di riassegnazione"]
out = out.reset_index()
out.to_csv(os.path.join(P, "aler_vuoti_serie_armonizzata.csv"), index=False, encoding="utf-8")
print(out.T.to_string())
R["aler_scarti_somma_max"] = int(out.scarto_su_totale.abs().max())
a21, a25 = out[out.anno == 2021].iloc[0], out[out.anno == 2025].iloc[0]
R["aler_sfitti_2021"] = int(a21.sfitti_come_scritti_da_ALER)
R["aler_sfitti_2025"] = int(a25.sfitti_come_scritti_da_ALER)
R["aler_sfitti_var_%"] = round(100 * (a25.sfitti_come_scritti_da_ALER / a21.sfitti_come_scritti_da_ALER - 1), 1)
R["aler_vuoti_armonizzati_2021"] = int(a21.vuoti_totali_armonizzati)
R["aler_vuoti_armonizzati_2025"] = int(a25.vuoti_totali_armonizzati)
R["aler_vuoti_armonizzati_var_%"] = round(100 * (a25.vuoti_totali_armonizzati / a21.vuoti_totali_armonizzati - 1), 1)

# 2. Quota del patrimonio SAP sul totale delle abitazioni di Milano
pat = pd.read_csv(os.path.join(P, "patrimonio_sap_milano_serie.csv"))
ult = pat.iloc[-1]
ind = pd.read_csv(os.path.join(root, "censimenti", "pulito", "indicatori_comune.csv")).set_index("anno")
rows = []
for anno, campo in ((2011, "abit_tot"), (2021, "abit_tot"), (2023, "abit_tot"), (2011, "abit_occ"), (2021, "abit_occ"), (2023, "abit_occ")):
    den = float(ind.loc[anno, campo])
    rows.append(dict(numeratore=f"SAP Milano citta' {ult.data_riferimento} (Regione)", n=int(ult.totale_Milano_citta), denominatore=f"{campo} censimento/registri {anno}", d=int(den),
                     quota_pct=round(100 * ult.totale_Milano_citta / den, 2),
                     avvertenza="2011 = censimento 2011; 2021 e 2023 = conteggio da registri/censimento permanente (salto da 643.053 a 809.990 non e' edilizia)"))
pd.DataFrame(rows).to_csv(os.path.join(P, "quote_su_abitazioni.csv"), index=False, encoding="utf-8")
R["sap_milano_2026"] = int(ult.totale_Milano_citta)
R["quota_su_abitazioni_2023_%"] = round(100 * ult.totale_Milano_citta / float(ind.loc[2023, "abit_tot"]), 1)
R["quota_su_abitazioni_2021_%"] = round(100 * ult.totale_Milano_citta / float(ind.loc[2021, "abit_tot"]), 1)
R["quota_su_abitazioni_occupate_2023_%"] = round(100 * ult.totale_Milano_citta / float(ind.loc[2023, "abit_occ"]), 1)
R["quota_su_abitazioni_2011_%"] = round(100 * ult.totale_Milano_citta / float(ind.loc[2011, "abit_tot"]), 1)

# 3. Domande / alloggi in avviso / assegnati
av = pd.read_csv(os.path.join(P, "avvisi_milano.csv"))
y = av.groupby("anno_avvisi").agg(avvisi=("avviso_n", "count"), alloggi_in_avviso=("alloggi_pubblicati_in_avviso", "sum"), domande_somma_avvisi=("domande", "sum"), assegnati=("alloggi_assegnati", "sum")).reset_index()
y["domande_per_alloggio_in_avviso"] = (y.domande_somma_avvisi / y.alloggi_in_avviso).round(1)
y["assegnati_%_degli_in_avviso"] = (100 * y.assegnati / y.alloggi_in_avviso).round(1)
y["nota"] = "domande sommate sugli avvisi dell'anno: lo stesso nucleo puo' comparire in piu' avvisi (la Regione stima ~10% in meno a livello regionale)"
y.to_csv(os.path.join(P, "domande_per_alloggio.csv"), index=False, encoding="utf-8")
print(y.to_string())

# 4. ALER: fabbricati (2016) per Municipio, a confronto con gli alloggi ALER assegnabili 2026 per Municipio (slide Piano 2026)
nilm = pd.read_csv(os.path.join(root, "censimenti", "pulito", "nil_2021_anagrafica.csv"))[["nil", "municipio_prevalente"]]
st = pd.read_csv(os.path.join(P, "aler_stabili_per_nil.csv")).merge(nilm, left_on="ID_NIL", right_on="nil", how="left")
mun = st.groupby("municipio_prevalente").agg(fabbricati_ALER_2016=("fabbricati_2016", "sum"), canone_fatturato_2016=("canone_fatturato_2016", "sum")).reset_index()
mun["quota_canone_%"] = (100 * mun.canone_fatturato_2016 / mun.canone_fatturato_2016.sum()).round(1)
pm = pd.read_csv(os.path.join(P, "piano_annuale_2026_per_municipio.csv"))
tot = pm[pm.voce.str.startswith("g)") & pm.municipio.str.startswith("Municipio")].copy()
tot["municipio_prevalente"] = tot.municipio.str.extract(r"(\d+)")[0].astype(int)
mun = mun.merge(tot[["municipio_prevalente", "alloggi_ALER", "alloggi_Comune_MM"]].rename(columns={"alloggi_ALER": "ALER_assegnabili_2026", "alloggi_Comune_MM": "Comune_assegnabili_2026"}), on="municipio_prevalente", how="left")
cm = pm[pm.voce.str.startswith("b)") & pm.municipio.str.startswith("Municipio")].copy()
cm["municipio_prevalente"] = cm.municipio.str.extract(r"(\d+)")[0].astype(int)
mun = mun.merge(cm[["municipio_prevalente", "alloggi_ALER", "alloggi_Comune_MM"]].rename(columns={"alloggi_ALER": "ALER_carenza_manutentiva_assegnabili_2026", "alloggi_Comune_MM": "Comune_carenza_manutentiva_assegnabili_2026"}), on="municipio_prevalente", how="left")
rc = pm[pm.voce.str.startswith("c)") & pm.municipio.str.startswith("Municipio")].copy()
rc["municipio_prevalente"] = rc.municipio.str.extract(r"(\d+)")[0].astype(int)
mun = mun.merge(rc[["municipio_prevalente", "alloggi_ALER", "alloggi_Comune_MM"]].rename(columns={"alloggi_ALER": "ALER_da_ristrutturazione_assegnabili_2026", "alloggi_Comune_MM": "Comune_da_ristrutturazione_assegnabili_2026"}), on="municipio_prevalente", how="left")
mun.to_csv(os.path.join(P, "aler_stabili_per_municipio.csv"), index=False, encoding="utf-8")
print(mun.to_string())

# 5. NIL: fabbricati ALER 2016 + abitazioni (indicatori NIL 2023) - solo descrittivo
ind_nil = pd.read_csv(os.path.join(root, "censimenti", "pulito", "indicatori_NIL.csv"))
ind_nil = ind_nil[ind_nil.anno == 2023][["nil", "pop", "abit_tot"]].rename(columns={"nil": "ID_NIL", "pop": "pop_2023", "abit_tot": "abitazioni_2023"})
nn = st.merge(ind_nil, on="ID_NIL", how="left")
nn["canone_ALER_2016_per_abitazione_eur"] = (nn.canone_fatturato_2016 / nn.abitazioni_2023).round(0)
nn = nn[["ID_NIL", "NIL", "municipio_prevalente", "fabbricati_2013", "fabbricati_2015", "fabbricati_2016", "canone_fatturato_2013", "canone_fatturato_2016", "quota_canone_2016_%", "pop_2023", "abitazioni_2023", "canone_ALER_2016_per_abitazione_eur"]]
nn.to_csv(os.path.join(P, "nil_aler_stabili_abitazioni.csv"), index=False, encoding="utf-8")
R["nil_con_fabbricati_ALER"] = int(len(nn))
R["quota_canone_top5_nil_%"] = round(float(nn.head(5)["quota_canone_2016_%"].sum()), 1)
R["top5_nil"] = nn.head(5)["NIL"].tolist()
json.dump(R, open(os.path.join(P, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(R, ensure_ascii=False, indent=1))
