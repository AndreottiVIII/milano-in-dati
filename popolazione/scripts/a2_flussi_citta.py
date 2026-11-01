"""a2: serie dei flussi migratori di Milano citta', tre fonti confrontate. Uso: python -I -X utf8 a2_flussi_citta.py <popolazione assoluto>
Fonti: (1) ISTAT bilancio demografico/ricostruzione intercensuaria (data di registrazione): interno (altri comuni) ed estero, 2001-2025;
(2) Comune ds71 (immigrati/emigrati totali dal 1880, non separa Italia/estero); (3) Comune ds1595-1600 e ds1953-1956 (per data dell'EVENTO, 2004-2024, con tipo di provvedimento).
Scrive pulito/flussi_citta_anno.csv"""
import sys, os, io, zipfile
import pandas as pd
P = sys.argv[1]; out = os.path.join(P, "pulito"); raw = os.path.join(P, "raw")
# ISTAT 2001-2018
r = pd.read_csv(os.path.join(out, "istat_bilancio_milano_2001_2018.csv"))
r = r[(r.Cittadinanza == "Tutte") & (r.Sesso == "Maschi e femmine")]
a = pd.DataFrame({"anno": r.Anno, "istat_isc_interno": r["Iscritti dall'interno"], "istat_canc_interno": r["Cancellati per l'interno"], "istat_isc_estero": r["Iscritti dall'estero"],
                  "istat_canc_estero": r["Cancellati per l'estero"], "istat_nati": r["Nati"], "istat_morti": r["Morti"], "istat_pop_fine": r["Popolazione fine periodo"], "istat_pop_inizio": r["Popolazione inizio periodo"]})
for cit, tag in (("Italiana", "ita"), ("Straniera", "str")):
    q = pd.read_csv(os.path.join(out, "istat_bilancio_milano_2001_2018.csv"))
    q = q[(q.Cittadinanza == cit) & (q.Sesso == "Maschi e femmine")].set_index("Anno")
    a["istat_isc_estero_" + tag] = a.anno.map(q["Iscritti dall'estero"]); a["istat_canc_estero_" + tag] = a.anno.map(q["Cancellati per l'estero"])
    a["istat_isc_interno_" + tag] = a.anno.map(q["Iscritti dall'interno"]); a["istat_canc_interno_" + tag] = a.anno.map(q["Cancellati per l'interno"])
# 2019-2024 mensile
d = pd.read_csv(os.path.join(out, "istat_bilancio_milano_2019_2024_mensile.csv"), dtype={"Codice comune": str})
d = d[d.Sesso == "Totale"].groupby("Anno")[["Nati vivi", "Morti", "Immigrati da altro comune", "Emigrati per altro comune", "Immigrati dall'estero", "Emigrati per l'estero", "Unità in più/meno dovute a variazioni territoriali"]].sum()
b = pd.DataFrame({"anno": d.index, "istat_isc_interno": d["Immigrati da altro comune"].values, "istat_canc_interno": d["Emigrati per altro comune"].values, "istat_isc_estero": d["Immigrati dall'estero"].values,
                  "istat_canc_estero": d["Emigrati per l'estero"].values, "istat_nati": d["Nati vivi"].values, "istat_morti": d["Morti"].values})
# 2025 da P2
p2 = pd.read_csv(os.path.join(raw, "istat_demo", "P2_2025_unzip", "P2_2025_it_015_Milano.csv"), sep=";", skiprows=1, encoding="utf-8-sig", dtype={"Codice comune": str})
p2 = p2[p2["Codice comune"] == "015146"].iloc[0]
c25 = dict(anno=2025, istat_isc_interno=p2["Immigrati da altro comune - Totale"], istat_canc_interno=p2["Emigrati per altro comune - Totale"], istat_isc_estero=p2["Immigrati dall'estero - Totale"],
           istat_canc_estero=p2["Emigrati per l'estero - Totale"], istat_nati=p2["Nati vivi - Totale"], istat_morti=p2["Morti - Totale"])
print(p2["Comune"], {k: p2[k] for k in p2.index if "Totale" in k})
istat = pd.concat([a, b, pd.DataFrame([c25])], ignore_index=True)
# ds71
m = pd.read_csv(os.path.join(raw, "comune_ds71", "ds71_mov_pop-1880-2024.csv"), sep=";")
m.columns = ["anno", "ds71_nati", "ds71_morti", "ds71_immigrati", "ds71_emigrati", "ds71_saldo_censuario_aggiust", "ds71_pop_fine"]
# Comune per evento
def ev(files, col, tag):
    fr = []
    for f in files:
        x = pd.read_csv(f, sep=";"); x.columns = ["anno", "quartiere", "prov", "genere", "cit", "n"]; fr.append(x)
    x = pd.concat(fr)
    return x
I = ev([os.path.join(raw, "comune_ds1596", "ds1596-popolazione-iscrizioni-evento-quartiere.csv"), os.path.join(raw, "comune_ds1954", "ds1954_popolazione_iscrizioni_evento_quartiere.csv")], "", "")
C = ev([os.path.join(raw, "comune_ds1600", "ds1600-popolazione-cancellazioni-evento-quartiere.csv"), os.path.join(raw, "comune_ds1956", "ds1956_popolazione_cancellazioni_evento_quartiere.csv")], "", "")
ti = I.pivot_table(index="anno", columns="prov", values="n", aggfunc="sum").rename(columns={"Altro": "ev_isc_altro", "Da altro Comune italiano": "ev_isc_italia", "Dall'estero": "ev_isc_estero"})
tc = C.pivot_table(index="anno", columns="prov", values="n", aggfunc="sum").rename(columns={"Altro": "ev_canc_altro", "Per altro comune italiano": "ev_canc_italia", "Per estero": "ev_canc_estero"})
ev_ = ti.join(tc).reset_index()
# per cittadinanza (evento)
for nm, X, tcol in (("isc", I, "Dall'estero"), ("canc", C, "Per estero")):
    for cit, tag in (("Italiana", "ita"), ("Straniera", "str")):
        s = X[(X.prov == tcol) & (X.cit == cit)].groupby("anno").n.sum()
        ev_[f"ev_{nm}_estero_{tag}"] = ev_.anno.map(s)
full = pd.DataFrame({"anno": range(1999, 2026)}).merge(m, on="anno", how="left").merge(istat, on="anno", how="left").merge(ev_, on="anno", how="left")
full["istat_saldo_interno"] = full.istat_isc_interno - full.istat_canc_interno
full["istat_saldo_estero"] = full.istat_isc_estero - full.istat_canc_estero
full["ev_saldo_italia"] = full.ev_isc_italia - full.ev_canc_italia
full["ev_saldo_estero"] = full.ev_isc_estero - full.ev_canc_estero
full.to_csv(os.path.join(out, "flussi_citta_anno.csv"), index=False)
pd.set_option("display.width", 300); pd.set_option("display.max_columns", 50)
print(full[["anno", "ds71_immigrati", "ds71_emigrati", "istat_isc_interno", "istat_canc_interno", "istat_isc_estero", "istat_canc_estero", "ev_isc_italia", "ev_canc_italia", "ev_isc_estero", "ev_canc_estero", "ev_isc_altro", "ev_canc_altro"]].to_string())
