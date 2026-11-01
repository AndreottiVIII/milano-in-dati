"""Riepiloghi da pulito/botteghe.csv, entita_record.csv e edizioni_lunga.csv: per edizione, settore, decennio, NIL, chiusure, incroci tra fonti.
Scrive pulito/*.csv e pulito/riepilogo.json (ogni numero con la fonte nel nome della chiave).
Uso: python -I -X utf8 04_riepilogo.py <botteghe abs> <milano-in-dati abs>"""
import sys, os, json, collections, statistics
import pandas as pd
B, P = sys.argv[1:3]
b = pd.read_csv(B + "/pulito/botteghe.csv", dtype=str, keep_default_na=False)
rec = pd.read_csv(B + "/pulito/entita_record.csv", dtype=str, keep_default_na=False)
ed = pd.read_csv(B + "/pulito/edizioni_lunga.csv", dtype=str, keep_default_na=False)
R = {}
b["anno"] = pd.to_numeric(b.anno_fondazione, errors="coerce")
R["attivita_totali_unite"] = len(b)
R["righe_totali_tutte_le_edizioni"] = len(ed)
# --- 1. edizioni
e = ed.groupby(["elenco", "edizione", "data_edizione"]).size().reset_index(name="righe")
e.loc[e.elenco == "A_albo", "descrizione"] = "Albo Botteghe Storiche del Comune (>=50 anni)"
e.loc[e.elenco == "B_regione", "descrizione"] = "Negozi e Locali Storici, Regione Lombardia (>=40 anni), copia in data"
e.to_csv(B + "/pulito/edizioni_conteggi.csv", index=False)
# --- 2. composizione per presenza nelle liste
b["albo17"] = b.in_albo_2017 == "sì"
b["albo24"] = b.in_albo_2024 == "sì"
b["reg26"] = b.in_regione_2026 == "sì"
comb = b.groupby(["albo17", "albo24", "reg26"]).size().reset_index(name="n")
comb.to_csv(B + "/pulito/combinazioni_liste.csv", index=False)
R["in_albo_2017"] = int(b.albo17.sum())
R["in_albo_2024"] = int(b.albo24.sum())
R["in_regione_2026"] = int(b.reg26.sum())
R["in_albo_e_regione_2026"] = int((b.albo24 & b.reg26).sum())
R["solo_regione_2026_non_in_albo_2024"] = int((b.reg26 & ~b.albo24).sum())
R["solo_albo_2024_non_in_regione_2026"] = int((b.albo24 & ~b.reg26).sum())
# --- 3. settori
vivi = b[b.ancora_attiva.isin(["si", "probabile", "contraddittoria", "non_verificabile"])]
sett = b.groupby("settore").agg(totale=("id", "size"), cessata_albo=("stato_albo_2024", lambda s: (s == "cessata").sum()), albo24=("in_albo_2024", lambda s: (s == "sì").sum()),
                                anno_mediano=("anno", "median"), anno_min=("anno", "min")).reset_index()
sett["quota_cessata_su_albo24_%"] = (sett.cessata_albo / sett.albo24 * 100).round(1)
sett = sett.sort_values("totale", ascending=False)
sett.to_csv(B + "/pulito/per_settore.csv", index=False)
# --- 4. decenni e anni
b["decennio"] = (b.anno // 10 * 10).astype("Int64")
dec = b.groupby("decennio").size().reset_index(name="n")
dec.loc[dec.decennio < 1900, "decennio"] = 1800
dec = dec.groupby("decennio").n.sum().reset_index()
dec.to_csv(B + "/pulito/per_decennio_fondazione.csv", index=False)
R["anno_fondazione_mediano"] = float(b.anno.median())
R["anno_fondazione_min"] = int(b.anno.min())
R["prima_del_1900"] = int((b.anno < 1900).sum())
R["fondate_1945_1975"] = int(((b.anno >= 1945) & (b.anno <= 1975)).sum())
R["fondate_dopo_1975"] = int((b.anno > 1975).sum())
R["fondate_prima_del_1945"] = int((b.anno < 1945).sum())
R["anno_dubbio_fonti_discordanti"] = int((b.anno_dubbio == "sì").sum())
piu = b.sort_values("anno").head(25)[["id", "nome_insegna", "anno_fondazione", "settore", "indirizzo", "nil", "ancora_attiva", "in_albo_2024", "in_regione_2026"]]
piu.to_csv(B + "/pulito/piu_antiche.csv", index=False)
# --- 5. NIL
pop = pd.read_csv(P + "/ristoranti/pulito/nil_locali_per_1000ab.csv", sep=";", encoding="utf-8-sig", dtype=str)
pop = pop[["id_nil", "nil", "abitanti_2024", "area_km2"]]
pop["abitanti_2024"] = pop.abitanti_2024.astype(float)
n = b[b.nil_id != ""].groupby("nil_id").agg(n_attivita=("id", "size"), n_albo24=("in_albo_2024", lambda s: (s == "sì").sum()), n_reg26=("in_regione_2026", lambda s: (s == "sì").sum()),
                                           n_cessate=("ancora_attiva", lambda s: s.isin(["cessata", "cessata_probabile"]).sum())).reset_index()
n = n.merge(pop, left_on="nil_id", right_on="id_nil", how="outer").drop(columns=["id_nil"])
n["nil"] = n.nil.fillna("")
n["n_attivita"] = n.n_attivita.fillna(0).astype(int)
n["per_10000_abitanti"] = (n.n_attivita / n.abitanti_2024 * 10000).round(2)
n = n.sort_values("n_attivita", ascending=False)
n.to_csv(B + "/pulito/per_nil.csv", index=False)
mun = b.copy()
# municipio dal record sorgente (Albo/Regione); vedi riepilogo
mm = rec[rec.municipio != ""].groupby("ent_id").municipio.agg(lambda s: s.iloc[-1])
b["municipio"] = b.id.map(mm).fillna("")
R["per_municipio"] = b.municipio.value_counts().to_dict()
R["municipio1_quota_%"] = round((b.municipio == "1").mean() * 100, 1)
R["tre_nil_centro_duomo_brera_guastalla_ecc"] = n.head(8)[["nil", "n_attivita"]].values.tolist()
# NIL centro storico: Duomo, Brera, Guastalla, Magenta-San Vittore, Porta Ticinese, Porta Romana... uso Municipio 1 come "centro"
R["centro_municipio1_n"] = int((b.municipio == "1").sum())
R["resto_n"] = int((b.municipio != "1").sum())
# --- 6. chiusure: Albo 2017 -> 2024
a17 = b[b.albo17]
R["albo17_n"] = len(a17)
R["albo17_ancora_in_albo24_attiva"] = int(((a17.stato_albo_2024) == "attiva").sum())
R["albo17_in_albo24_cessata"] = int(((a17.stato_albo_2024) == "cessata").sum())
R["albo17_assenti_da_albo24"] = int((~a17.albo24).sum())
R["albo24_totale"] = int(b.albo24.sum())
R["albo24_attiva"] = int((b.stato_albo_2024 == "attiva").sum())
R["albo24_cessata"] = int((b.stato_albo_2024 == "cessata").sum())
a24 = b[b.albo24]
R["albo24_cessata_%"] = round((a24.stato_albo_2024 == "cessata").mean() * 100, 1)
nuove = a24[~a24.albo17]
R["albo24_nuove_rispetto_2017"] = len(nuove)
R["albo24_nuove_cessate"] = int((nuove.stato_albo_2024 == "cessata").sum())
vecchie = a24[a24.albo17]
R["albo24_gia_in_2017_cessate"] = int((vecchie.stato_albo_2024 == "cessata").sum())
R["albo24_gia_in_2017_n"] = len(vecchie)
# per settore e per centro/resto
ch = a24.assign(cess=(a24.stato_albo_2024 == "cessata"))
ch["centro"] = ch.municipio == "1"
R["cessate_centro_%"] = round(ch[ch.centro].cess.mean() * 100, 1)
R["cessate_resto_%"] = round(ch[~ch.centro].cess.mean() * 100, 1)
R["albo24_centro_n"] = int(ch.centro.sum())
R["albo24_resto_n"] = int((~ch.centro).sum())
ch["epoca"] = pd.cut(ch.anno, [0, 1919, 1944, 1959, 1969, 1979, 2100], labels=["<1920", "1920-44", "1945-59", "1960-69", "1970-79", "1980+"])
ep = ch.groupby("epoca", observed=True).agg(n=("id", "size"), cessate=("cess", "sum")).reset_index()
ep["quota_%"] = (ep.cessate / ep.n * 100).round(1)
ep.to_csv(B + "/pulito/cessate_per_epoca_fondazione.csv", index=False)
ss = ch.groupby("settore").agg(n=("id", "size"), cessate=("cess", "sum")).reset_index()
ss["quota_%"] = (ss.cessate / ss.n * 100).round(1)
ss.sort_values("n", ascending=False).to_csv(B + "/pulito/cessate_per_settore_albo24.csv", index=False)
cn = ch.groupby("nil").agg(n=("id", "size"), cessate=("cess", "sum")).reset_index()
cn["quota_%"] = (cn.cessate / cn.n * 100).round(1)
cn.sort_values("n", ascending=False).to_csv(B + "/pulito/cessate_per_nil_albo24.csv", index=False)
b[b.ancora_attiva.isin(["cessata", "cessata_probabile", "contraddittoria"])].drop(columns=["anno"]).to_csv(B + "/pulito/botteghe_cessate_o_dubbie.csv", index=False)
# --- 7. verifica dell'etichetta "cessata" con OSM e registri
R["osm_trova_%_delle_attive_albo24"] = round((a24[a24.stato_albo_2024 == "attiva"].osm_trovata == "sì").mean() * 100, 1)
R["osm_trova_%_delle_cessate_albo24"] = round((a24[a24.stato_albo_2024 == "cessata"].osm_trovata == "sì").mean() * 100, 1)
R["registro_forte_%_delle_attive_albo24"] = round((a24[a24.stato_albo_2024 == "attiva"].registro_2026 == "forte").mean() * 100, 1)
R["registro_forte_%_delle_cessate_albo24"] = round((a24[a24.stato_albo_2024 == "cessata"].registro_2026 == "forte").mean() * 100, 1)
R["regione26_con_stato_cessata_albo"] = int(((b.reg26) & (b.stato_albo_2024 == "cessata")).sum())
R["regione26_con_stato_cessata_albo_ma_osm_la_trova"] = int(((b.reg26) & (b.stato_albo_2024 == "cessata") & (b.osm_trovata == "sì")).sum())
# --- 8. elenco Regione: uscite
bc = ed[ed.elenco == "B_regione"]
eds = sorted(bc.edizione.unique())
sets = {x: set(rec[(rec.elenco == "B_regione") & (rec.edizione == x)].ent_id) for x in eds}
usc = []
for i in range(1, len(eds)):
    usc.append(dict(da=eds[i - 1], a=eds[i], uscite=len(sets[eds[i - 1]] - sets[eds[i]]), entrate=len(sets[eds[i]] - sets[eds[i - 1]]), righe_a=len(sets[eds[i]])))
pd.DataFrame(usc).to_csv(B + "/pulito/regione_uscite_entrate.csv", index=False)
uscite_tot = set().union(*sets.values()) - sets["20261019"]
R["regione_attivita_viste_in_qualche_copia"] = len(set().union(*sets.values()))
R["regione_uscite_dal_2019_non_piu_nel_2026"] = len(uscite_tot)
u = b[b.id.isin(uscite_tot)]
R["regione_uscite_stato_albo24"] = u.stato_albo_2024.replace("", "non in Albo 2024").value_counts().to_dict()
R["regione_uscite_osm_trovata"] = u.osm_trovata.value_counts().to_dict()
R["regione_uscite_ancora_attiva"] = u.ancora_attiva.value_counts().to_dict()
R["regione_uscite_luglio_agosto_2019"] = int(len(sets["20190723"] - sets["20190823"]))
# --- 9. giudizio complessivo
R["ancora_attiva_conteggi"] = b.ancora_attiva.value_counts().to_dict()
R["ancora_attiva_per_fonte_prove_osm_o_registro_forte"] = int(((b.osm_trovata == "sì") & (b.osm_chiusa != "sì") | (b.registro_2026 == "forte")).sum())
# --- 10. qualita' dati
R["coordinate_da_fonte"] = int((b.coord_da == "fonte").sum())
R["coordinate_da_civici"] = int((b.coord_da == "civici").sum())
R["indirizzo_discordante_albo24"] = int((b.indirizzo_discordante != "").sum())
R["nome_rovinato_albo24"] = int((b.nome_rovinato == "sì").sum())
R["senza_nil"] = int((b.nil == "").sum())
gl = json.load(open(B + "/pulito/geocodifica_log.json", encoding="utf-8"))
R["geocodifica_esiti_righe"] = gl["esiti_geocodifica_per_riga"]
R["coord_fonte_vs_civici_oltre_200m_righe"] = len(gl["coord_fonte_vs_civici_oltre_200m"])
R["unioni_per_nome_con_indirizzo_diverso"] = len(gl["legami_albo2024_indirizzo_diverso"])
R["unioni_per_nome_oltre_1km"] = sum(1 for x in gl["legami_albo2024_indirizzo_diverso"] if x[3] > 1000)
json.dump(R, open(B + "/pulito/riepilogo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(R, ensure_ascii=False, indent=1, default=str))
