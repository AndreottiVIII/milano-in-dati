"""Costruisce le tabelle ordinate delle serie di città: giorno, mese, anno.
Uscite: out/tempo_giorno.csv, out/tempo_mese.csv, out/tempo_anno.csv e aggiunge le serie a out/dizionario_tempo.csv"""
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd

from comune import OUT, path, rd

DIZ = []


def reg(nome, freq, file, campo, gruppo, nota="", aff="alta"):
    DIZ.append(dict(serie=nome, frequenza=freq, file=file, campo=campo, gruppo=gruppo, affidabilita=aff, nota_limite=nota))


# ---------------- GIORNO
g = rd("docs/morti/data/milano_giorno.csv")
g["data"] = pd.to_datetime(g.data)
G = g.set_index("data")[["morti", "attesi", "tmax_brera"]]
reg("morti", "giorno", "docs/morti/data/milano_giorno.csv", "morti", "morti", "Residenza, non luogo; ultimi mesi si riempiono con ritardo")
reg("tmax_brera", "giorno", "docs/morti/data/milano_giorno.csv", "tmax_brera", "meteo", "Brera 2008-2016 circa 0,65 gradi troppo calda")
sens = pd.read_csv(path("pioggia-e-caldo", "pulito", "sensori_selezionati.csv"))
mil = sens[sens.nomestazione.str.contains("Milano") & ~sens.nomestazione.str.contains("Segrate")]
tg = pd.read_csv(path("pioggia-e-caldo", "pulito", "temp_giornaliera.csv.gz"))
tg = tg[tg.idsensore.isin(mil.idsensore) & (tg.n >= 20)]
tg["data"] = pd.to_datetime(tg.data)
G = G.join(tg.groupby("data").tmean.median().rename("tmedia"), how="outer")
reg("tmedia", "giorno", "pioggia-e-caldo/pulito/temp_giornaliera.csv.gz", "tmean, mediana sensori di Milano", "meteo", "Sensori ARPA, composizione variabile")
po = pd.read_parquet(path("pioggia-e-caldo", "pulito", "intermedi", "P_orario.parquet"))
po = po[po.idsensore.astype(str).isin(mil.idsensore.astype(str))]
po["data"] = pd.to_datetime(po.ora).dt.normalize()
pg = po.groupby(["idsensore", "data"]).mm.sum().reset_index()
G = G.join(pg.groupby("data").mm.median().rename("pioggia_mm"), how="outer")
reg("pioggia_mm", "giorno", "pioggia-e-caldo/pulito/intermedi/P_orario.parquet", "mm, mediana giornaliera sensori di Milano", "meteo", "Pluviometri con buchi 2011-2020")
ar = pd.read_csv(path("aria", "pulito", "aria_giornaliera.csv"), low_memory=False)
ar["data"] = pd.to_datetime(ar.data, errors="coerce")
ar = ar[ar.statistica.astype(str).str.contains("media") & ar.data.notna() & (ar.data >= "2005-01-01")]
for inq, nome in [("PM10", "pm10"), ("NO2", "no2"), ("O3", "o3"), ("PM25", "pm25")]:
    a = ar[ar.inquinante == inq]
    # panel bilanciato approssimato: si toglie a ogni stazione la sua media per non far entrare i cambi di stazione
    m = a.groupby("id_stazione").valore.transform("mean")
    z = a.assign(v=a.valore - m).groupby("data").v.mean() + a.valore.mean()
    G = G.join(z.rename(nome), how="outer")
    reg(nome, "giorno", "aria/pulito/aria_giornaliera.csv", f"valore {inq}, media scarti di stazione", "aria", "Cambi di stazione: tolta la media di ogni stazione")
ac = rd("docs/area-c/data/ingressi_giornalieri.csv")
ac["data"] = pd.to_datetime(ac.data)
acx = ac[ac.flag != "nessun_dato"].set_index("data")
G = G.join(acx.totale.rename("areac"), how="outer")
reg("areac", "giorno", "docs/area-c/data/ingressi_giornalieri.csv", "totale", "areac", "Dal 9/2016 al 11/2024; prima conteggio diverso (rottura)")
ao = rd("docs/area-c/data/ingressi_giornalieri_2012-2016_conteggio_diverso.csv")
ao["data"] = pd.to_datetime(ao.data)
ao = ao[(ao.data < "2016-01-01")].set_index("data")
G = G.join(ao.totale.rename("areac_vecchia"), how="outer")
reg("areac_vecchia", "giorno", "docs/area-c/data/ingressi_giornalieri_2012-2016_conteggio_diverso.csv", "totale", "areac", "2012-2015 con conteggio diverso: non si unisce alla serie nuova")
G = G[(G.index >= "2005-01-01") & (G.index <= "2026-10-31")]
G.to_csv(os.path.join(OUT, "tempo_giorno.csv"), encoding="utf-8-sig")

# ---------------- MESE
Gm = G.copy()
Gm["mese"] = Gm.index.to_period("M")
M = pd.DataFrame(index=pd.period_range("2004-01", "2026-10", freq="M"))
M.index.name = "mese"
cov = Gm.groupby("mese").size()
gm = Gm.groupby("mese")
M["morti"] = gm.morti.sum(min_count=25)
M["attesi_morti"] = gm.attesi.sum(min_count=25)
M["tmedia"] = gm.tmedia.mean()
M["tmax"] = gm.tmax_brera.mean()
M["pioggia_mm"] = gm.pioggia_mm.sum(min_count=25)
M["giorni_pioggia"] = gm.pioggia_mm.apply(lambda s: (s >= 1).sum() if s.notna().sum() >= 25 else np.nan)
for c in ["pm10", "no2", "o3"]:
    M[c] = gm[c].mean()
M["areac"] = gm.areac.mean().where(gm.areac.count() >= 20)
M["areac_vecchia"] = gm.areac_vecchia.mean().where(gm.areac_vecchia.count() >= 20)


def dasm(df, anno="anno", mese="mese"):
    return pd.PeriodIndex.from_fields(year=df[anno].astype(int).values, month=df[mese].astype(int).values, freq="M")


ae = rd("docs/aeroporti/data/mensile_tre_aeroporti.csv")
ae["p"] = dasm(ae)
for a in ["Linate", "Malpensa", "Bergamo"]:
    s = ae[ae.aeroporto == a].set_index("p").passeggeri
    M["pax_" + a.lower()] = s.reindex(M.index)
    reg("pax_" + a.lower(), "mese", "docs/aeroporti/data/mensile_tre_aeroporti.csv", "passeggeri", "aeroporti", "Nessuna origine dei passeggeri; 2026 fino a maggio; Linate chiuso 27/7-27/10/2019")
tu = pd.read_csv(path("turisti", "pulito", "milano_mensile_totale.csv"))
tu["p"] = dasm(tu)
M["presenze"] = tu.set_index("p").presenze.reindex(M.index)
M["arrivi"] = tu.set_index("p").arrivi.reindex(M.index)
reg("presenze", "mese", "turisti/pulito/milano_mensile_totale.csv", "presenze", "turisti", "Dal 2019; strutture ufficiali, non conta chi non dichiara")
tp = rd("docs/turisti/data/mensile_paese.csv")
tp["p"] = dasm(tp)
tpg = tp.groupby("p")[["arrivi", "presenze"]].sum()
M["presenze_estero_prov"] = tpg.presenze.reindex(M.index)
reg("presenze_estero_prov", "mese", "docs/turisti/data/mensile_paese.csv", "presenze, somma paesi", "turisti", "Dal 2015; stranieri", aff="media")
bi = rd("docs/biblioteche/data/mensile.csv")
bi = bi[bi.parziale.astype(str).str.lower() != "true"]
bi["p"] = pd.PeriodIndex(bi.mese, freq="M")
M["prestiti"] = bi.set_index("p").totale.reindex(M.index)
reg("prestiti", "mese", "docs/biblioteche/data/mensile.csv", "totale", "biblioteche", "Chiusure per lavori; prestiti non sono lettori")
mu = rd("docs/musei/data/civici_mensili.csv")
mu["p"] = dasm(mu)
mug = mu.groupby("p").visitatori.sum()
M["musei_civici"] = mug.reindex(M.index)
reg("musei_civici", "mese", "docs/musei/data/civici_mensili.csv", "visitatori somma", "musei", "2007-2017, musei che cambiano, mesi mancanti", aff="media")
ca = rd("docs/costo-vita/data/carburanti_milano_mensile.csv")
ca["p"] = pd.PeriodIndex(ca.mese, freq="M")
M["benzina"] = ca.set_index("p").benzina_self_eur_litro.reindex(M.index)
M["gasolio"] = ca.set_index("p").gasolio_self_eur_litro.reindex(M.index)
reg("benzina", "mese", "docs/costo-vita/data/carburanti_milano_mensile.csv", "benzina_self_eur_litro", "prezzi", "Quotazione media comunale")
en = rd("docs/costo-vita/data/serie_mensili_energia.csv")
en["p"] = pd.PeriodIndex(en.mese, freq="M")
for c in ["elettricita", "gas", "generale_milano"]:
    M["ipc_" + c] = en.set_index("p")[c].reindex(M.index)
    reg("ipc_" + c, "mese", "docs/costo-vita/data/serie_mensili_energia.csv", c, "prezzi", "Solo 2020-2026")
fa = rd("docs/reati-citta/data/famiglia_stalking_mensile.csv")
fa = fa[fa.territorio.astype(str).str.contains("Milano")]
fa["p"] = dasm(fa)
for k, n in [("Maltrattamenti", "denunce_maltrattamenti"), ("stalking", "denunce_stalking")]:
    s = fa[fa.tipo_delitto.astype(str).str.contains(k)].groupby("p").denunce.sum()
    M[n] = s.reindex(M.index)
    reg(n, "mese", "docs/reati-citta/data/famiglia_stalking_mensile.csv", "denunce", "reati", "Provincia; 2019-2024; denunciato non è commesso")
ca2 = rd("docs/carceri/data/istituti_lombardia_milano_mensile.csv")
ca2["p"] = pd.PeriodIndex(pd.to_datetime(ca2.data), freq="M")
M["detenuti_milano"] = ca2[ca2.istituto.astype(str).str.contains("Milano")].groupby("p").detenuti_presenti.sum().reindex(M.index)
reg("detenuti_milano", "mese", "docs/carceri/data/istituti_lombardia_milano_mensile.csv", "detenuti_presenti", "carceri", "Dal 2019", aff="media")
wk = pd.read_csv(path("luoghi-cercati", "pulito", "serie_mensile_totale.csv"), sep=";")
wk["p"] = pd.PeriodIndex(wk.mese, freq="M")
M["wiki_estero"] = wk.set_index("p").estero.reindex(M.index)
M["wiki_italiano"] = wk.set_index("p")["it"].reindex(M.index)
reg("wiki_estero", "mese", "luoghi-cercati/pulito/serie_mensile_totale.csv", "estero", "wiki", "Wikipedia nel suo insieme cala: confronto cauto; 2015-07/2026-10", aff="media")
reg("wiki_italiano", "mese", "luoghi-cercati/pulito/serie_mensile_totale.csv", "it", "wiki", "Wikipedia nel suo insieme cala", aff="media")
cv = rd("docs/prezzi-case/data/compravendite_milano.csv")
cv["p"] = pd.PeriodIndex.from_fields(year=cv.anno.astype(int).values, quarter=cv.trimestre.astype(int).values, freq="Q")
for per, v in zip(cv.p, cv.ntn_capoluogo):
    for mm in pd.period_range(per.asfreq("M", "s"), per.asfreq("M", "e"), freq="M"):
        if mm in M.index:
            M.loc[mm, "compravendite"] = v / 3
reg("compravendite", "mese", "docs/prezzi-case/data/compravendite_milano.csv", "ntn_capoluogo /3 per mese", "case", "Trimestrale spalmato: usare solo per rotture, non per lag; 2025-26 provvisorio", aff="media")
M = M.dropna(how="all")
M.to_csv(os.path.join(OUT, "tempo_mese.csv"), encoding="utf-8-sig")

# ---------------- ANNO
Y = pd.DataFrame(index=range(1990, 2027))
Y.index.name = "anno"
gy = G.groupby(G.index.year)
Y["morti"] = gy.morti.sum(min_count=330)
Y["tmedia"] = gy.tmedia.mean()
Y["pioggia_mm"] = gy.pioggia_mm.sum(min_count=300)
Y["pm10"] = gy.pm10.mean()
Y["no2"] = gy.no2.mean()
inc = rd("docs/incroci/data/serie_annuale.csv").set_index("anno")
for c, n in [("incidenti", "incidenti"), ("feriti", "feriti"), ("morti", "morti_strada"), ("ped_inc", "incidenti_pedoni"), ("bici_inc", "incidenti_bici"), ("moto_inc", "incidenti_moto")]:
    Y[n] = inc[c].reindex(Y.index)
    reg(n, "anno", "docs/incroci/data/serie_annuale.csv", c, "incidenti", "Solo con feriti, forze dell'ordine")
na = rd("docs/nascite/data/citta_anno.csv").set_index("anno")
Y["nati"] = na.nati_residenti.reindex(Y.index)
Y["nati_x1000_donne"] = na.nati_per_1000_donne_15_49.reindex(Y.index)
reg("nati", "anno", "docs/nascite/data/citta_anno.csv", "nati_residenti", "nascite", "Salti di registro 2002-03 e 2011-12")
ma = rd("docs/matrimoni/data/tassi_per_mille_milano.csv").set_index("anno")
Y["matrimoni"] = ma.totale.reindex(Y.index)
Y["quota_civili"] = ma.quota_civili_pct.reindex(Y.index)
reg("matrimoni", "anno", "docs/matrimoni/data/tassi_per_mille_milano.csv", "totale", "matrimoni", "Celebrati a Milano; 2010 ISTAT fuori traiettoria")
re_ = rd("docs/reati/data/milano_comune_ds564.csv")
for k, n in [("Totale", "denunce_totale"), ("Furti", "denunce_furti"), ("Rapine", "denunce_rapine"), ("Lesioni dolose", "denunce_lesioni"), ("Normativa sugli stupefacenti", "denunce_stupefacenti"), ("Truffe e frodi informatiche", "denunce_truffe"), ("Danneggiamenti", "denunce_danneggiamenti")]:
    s = re_[re_.tipo_delitto == k].set_index("anno").denunce_comune
    if len(s):
        Y[n] = pd.to_numeric(s, errors="coerce").reindex(Y.index)
        reg(n, "anno", "docs/reati/data/milano_comune_ds564.csv", "denunce_comune/" + k, "reati", "Denunciato non è commesso; 2004-2023")
ri = rd("docs/rifiuti/data/milano_serie.csv")
ri["anno"] = ri.anno.astype(int)
ri = ri.set_index("anno")
Y["rifiuti_t"] = ri.rifiuti_urbani_t.reindex(Y.index)
Y["rifiuti_kg_ab"] = ri.kg_per_abitante_RU.reindex(Y.index)
reg("rifiuti_t", "anno", "docs/rifiuti/data/milano_serie.csv", "rifiuti_urbani_t", "rifiuti", "ISPRA")
tu2 = rd("docs/turisti/data/serie_totale.csv")
tu2 = tu2[tu2.serie == "nuova"].set_index("anno") if (tu2.serie == "nuova").sum() >= 10 else tu2.drop_duplicates("anno", keep="last").set_index("anno")
Y["presenze_anno"] = tu2.presenze_totale.reindex(Y.index)
reg("presenze_anno", "anno", "docs/turisti/data/serie_totale.csv", "presenze_totale", "turisti", "Serie nuova e vecchia diverse")
for a in ["Linate", "Malpensa", "Bergamo"]:
    s = rd("docs/aeroporti/data/annuale_tre_aeroporti.csv")
    Y["pax_" + a.lower()] = s[s.aeroporto == a].set_index("anno").passeggeri.reindex(Y.index)
me = rd("docs/metro/data/rete_km_passeggeri.csv").set_index("anno")
Y["metro_pax"] = me.passeggeri_mln.reindex(Y.index)
reg("metro_pax", "anno", "docs/metro/data/rete_km_passeggeri.csv", "passeggeri_mln", "metro", "Solo 2016-2025, tornelli; serie corta", aff="media")
bk = rd("docs/bici/data/bikemi_serie.csv").set_index("anno")
Y["bici_noleggi"] = bk.noleggi_giorno_totale.reindex(Y.index)
reg("bici_noleggi", "anno", "docs/bici/data/bikemi_serie.csv", "noleggi_giorno_totale", "bici", "Medie del Comune; base non dichiarata; serie corta", aff="media")
bib = rd("docs/biblioteche/data/mensile.csv")
bib["anno"] = bib.mese.str[:4].astype(int)
bib = bib[bib.parziale.astype(str).str.lower() != "true"].groupby("anno").totale.agg(["sum", "size"])
Y["prestiti_anno"] = bib["sum"].where(bib["size"] == 12).reindex(Y.index)
mu2 = rd("docs/musei/data/statali_milano_1996_2024.csv").groupby("anno").totale.sum()
Y["musei_statali"] = mu2.reindex(Y.index)
reg("musei_statali", "anno", "docs/musei/data/statali_milano_1996_2024.csv", "totale", "musei", "Siti statali, biglietti emessi; Cenacolo e pochi altri")
mc = rd("docs/musei/data/civici_mensili.csv").groupby("anno").visitatori.sum()
Y["musei_civici"] = mc.reindex(Y.index)
ind = rd("docs/costo-vita/data/indici_annui_2005_100.csv")
ind["anno"] = ind.anno.astype(int)
ind = ind.set_index("anno")
Y["ipc_generale"] = ind.generale_milano.reindex(Y.index)
Y["ipc_affitti"] = ind.affitti.reindex(Y.index)
Y["ipc_ristoranti"] = ind.ristoranti.reindex(Y.index)
Y["ipc_alberghi"] = ind.alberghi.reindex(Y.index)
reg("ipc_generale", "anno", "docs/costo-vita/data/indici_annui_2005_100.csv", "generale_milano", "prezzi", "ISTAT")
pc = rd("docs/prezzi-case/data/serie_citta.csv")
pc = pc[pc.tipologia.astype(str).str.contains("Abitazioni civili")]
pc["anno"] = pc.semestre.str[:4].astype(int)
Y["prezzo_case_reale"] = pc.groupby("anno").prezzo_mediano_euro2025_m2.mean().reindex(Y.index)
Y["affitto_case_reale"] = pc.groupby("anno").affitto_mediano_euro2025_m2_mese.mean().reindex(Y.index)
reg("prezzo_case_reale", "anno", "docs/prezzi-case/data/serie_citta.csv", "prezzo_mediano_euro2025_m2", "case", "OMI stime; revisione zone 2014 e 2024", aff="media")
cv2 = cv.groupby("anno").ntn_capoluogo.agg(["sum", "size"])
Y["compravendite"] = cv2["sum"].where(cv2["size"] == 4).reindex(Y.index)
im = rd("docs/imprese/data/milano_annuale.csv").set_index("anno")
for c, n in [("attive", "imprese_attive"), ("iscrizioni", "imprese_iscrizioni"), ("cessazioni_non_ufficio", "imprese_cessazioni")]:
    Y[n] = im[c].reindex(Y.index)
reg("imprese_iscrizioni", "anno", "docs/imprese/data/milano_annuale.csv", "iscrizioni", "imprese", "Provincia; Monza dal 2007; ATECO 2025")
sf = rd("docs/sfratti/data/serie_unita.csv")
s_ = sf[sf.unita == "Comune di Milano"].set_index("anno")
Y["sfratti_emessi"] = s_.emessi.reindex(Y.index)
Y["sfratti_eseguiti"] = s_.eseguiti.reindex(Y.index)
reg("sfratti_emessi", "anno", "docs/sfratti/data/serie_unita.csv", "emessi", "sfratti", "Comune di Milano; blocco Covid 2020-21")
au = rd("docs/auto/data/serie_milano_comune.csv").set_index("anno")
Y["auto_x1000"] = au.per1000_auto.reindex(Y.index)
Y["moto_x1000"] = au.per1000_moto.reindex(Y.index)
Y["immatricolazioni"] = au.immatricolazioni.reindex(Y.index)
reg("auto_x1000", "anno", "docs/auto/data/serie_milano_comune.csv", "per1000_auto", "auto", "Iscritte al PRA a Milano (flotte, noleggi)")
Y = Y.dropna(how="all")
Y.to_csv(os.path.join(OUT, "tempo_anno.csv"), encoding="utf-8-sig")
pd.DataFrame(DIZ).to_csv(os.path.join(OUT, "dizionario_tempo.csv"), index=False, encoding="utf-8-sig")
pd.set_option("display.width", 200)
print("giorno", G.shape, G.notna().sum().to_dict())
print(M.apply(lambda c: f"{c.first_valid_index()}..{c.last_valid_index()} n={c.notna().sum()}").to_string())
print(Y.apply(lambda c: f"{c.first_valid_index()}..{c.last_valid_index()} n={c.notna().sum()}").to_string())
