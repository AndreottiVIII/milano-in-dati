"""Fase 2, passo 4: popolazione residente annuale di Milano 2018-2025 (31.12 di ogni anno = 1 gennaio dopo), da demo.istat.it (open).
Uso: python -I h7_annuale.py <cartella censimenti>
Input: raw/istat_demo/POSAS_<anno>_it_015_Milano.zip (residenti per eta' al 1 gennaio), STRASA_* (stranieri per eta'), D7B<anno>.csv.zip (bilancio mensile, tutti i comuni)
Output: pulito/annuale_milano_2018_2025.csv
"""
import sys, zipfile, io
import numpy as np
import pandas as pd
root = sys.argv[1]; R = root + "/raw/istat_demo/"; P = root + "/pulito/"
rows = []
for y in range(2019, 2027):
    z = zipfile.ZipFile(R + f"POSAS_{y}_it_015_Milano.zip")
    t = z.open(z.namelist()[0]).read().decode("cp1252").splitlines()
    d = pd.read_csv(io.StringIO("\n".join(t[1:])), sep=";", dtype=str)
    d = d[d["Codice comune"] == "015146"].copy()
    d["eta"] = pd.to_numeric(d.iloc[:, 2]); 
    for c in ["Totale maschi", "Totale femmine", "Totale"]:
        d[c] = pd.to_numeric(d[c])
    tot = d[d.eta == 999].iloc[0]
    d = d[d.eta != 999]
    z2 = zipfile.ZipFile(R + f"STRASA_{y}_it_015_Milano.zip")
    t2 = z2.open(z2.namelist()[0]).read().decode("cp1252").splitlines()
    s = pd.read_csv(io.StringIO("\n".join(t2[1:])), sep=";", dtype=str)
    s = s[s["Codice comune"] == "015146"].copy()
    s["eta"] = pd.to_numeric(s.iloc[:, 2]); s["str"] = pd.to_numeric(s.Maschi) + pd.to_numeric(s.Femmine)
    st_tot = s[s.eta == 999].str.iloc[0]; s = s[s.eta != 999]
    n = d.Totale.sum()
    rows.append(dict(data_riferimento=f"{y}-01-01", anno_fine_periodo=y - 1,
                     popolazione=int(tot.Totale), controllo_somma_eta=int(n), maschi=int(tot["Totale maschi"]), femmine=int(tot["Totale femmine"]),
                     stranieri=int(st_tot), quota_stranieri=round(100 * st_tot / tot.Totale, 2),
                     quota_0_14=round(100 * d[d.eta <= 14].Totale.sum() / n, 2), quota_65p=round(100 * d[d.eta >= 65].Totale.sum() / n, 2),
                     quota_75p=round(100 * d[d.eta >= 75].Totale.sum() / n, 2), quota_80p=round(100 * d[d.eta >= 80].Totale.sum() / n, 2),
                     eta_media=round((d.eta * d.Totale).sum() / n, 2),
                     indice_vecchiaia=round(100 * d[d.eta >= 65].Totale.sum() / d[d.eta <= 14].Totale.sum(), 1),
                     stranieri_0_14=int(s[s.eta <= 14].str.sum()), stranieri_65p=int(s[s.eta >= 65].str.sum()),
                     eta_media_stranieri=round((s.eta * s.str).sum() / s.str.sum(), 2)))
a = pd.DataFrame(rows)
# bilancio demografico
bil = []
for y in range(2019, 2025):
    z = zipfile.ZipFile(R + f"D7B{y}.csv.zip")
    d = pd.read_csv(z.open(z.namelist()[0]), sep=";", dtype=str, encoding="cp1252")
    d = d[(d["Codice comune"] == "015146") & (d.Sesso == "Totale")].copy()
    for c in d.columns:
        if c not in ("Nome mese", "Sesso", "Comune", "Provincia", "Regione", "Ripartizione", "Nazione", "Codice nazione", "Codice comune", "Codice provincia", "Codice regione", "Codice ripartizione"):
            d[c] = pd.to_numeric(d[c])
    d["Mese"] = d["Mese"].astype(int)
    d = d.sort_values("Mese")
    f = d[d.Mese <= 12]
    adj = d[d["Nome mese"].str.contains("Aggiust", na=False)]["Popolazione fine periodo"].sum()
    cens = d[d["Nome mese"].str.contains("censita", na=False)]["Popolazione fine periodo"]
    bil.append(dict(anno_fine_periodo=y, mesi_flussi=len(f), pop_inizio=int(f.iloc[0]["Popolazione inizio periodo"]), pop_fine_anagrafe_prima_aggiustamento=int(f.iloc[-1]["Popolazione fine periodo"]),
                    aggiustamento_statistico=int(adj), pop_censita_31dic=int(cens.iloc[0]) if len(cens) else None,
                    nati=int(f["Nati vivi"].sum()), morti=int(f["Morti"].sum()), saldo_naturale=int(f["Saldo naturale"].sum()),
                    iscritti_da_altro_comune=int(f["Immigrati da altro comune"].sum()), cancellati_per_altro_comune=int(f["Emigrati per altro comune"].sum()),
                    iscritti_dall_estero=int(f["Immigrati dall'estero"].sum()), cancellati_per_estero=int(f["Emigrati per l'estero"].sum())))
b = pd.DataFrame(bil)
b["saldo_migratorio_totale"] = b.iscritti_da_altro_comune - b.cancellati_per_altro_comune + b.iscritti_dall_estero - b.cancellati_per_estero
b["saldo_totale_flussi"] = b.saldo_naturale + b.saldo_migratorio_totale
b["controllo_flussi_vs_anagrafe"] = b.pop_fine_anagrafe_prima_aggiustamento - b.pop_inizio - b.saldo_totale_flussi
m = a.merge(b, on="anno_fine_periodo", how="left")
m.to_csv(P + "annuale_milano_2018_2025.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(m.T)
