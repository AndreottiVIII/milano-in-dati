"""Riepiloghi dai dati ISPRA per comune (edizione 2026): Milano, citta' di confronto, comuni della Citta' metropolitana.
Legge pulito/comuni_lungo.csv (da estrai_indicatori.py) e raw/snpa/consumo_suolo_2026_dati_principali.xlsx.
Scrive in pulito/: serie_citta.csv, confronto_citta_2025.csv, grandi_comuni_2025.csv, metro_comuni.csv, metro_top_recenti.csv,
 serie_milano.csv, edizioni_milano.csv, riepilogo.json
Uso: python -I -X utf8 analisi_indicatori.py <suolo assoluto>
"""
import sys, os, json
import pandas as pd, numpy as np, openpyxl

base = sys.argv[1]
P = os.path.join(base, "pulito")
d = pd.read_csv(os.path.join(P, "comuni_lungo.csv"), sep=";")

# serie scelta: fogli originali, tranne 2023 e 2024 dove usiamo i fogli "rev" (valori rivisti da ISPRA)
SERIE = {2006: "Comuni_2006", 2012: "Comuni_2012", 2015: "Comuni_2015", 2016: "Comuni_2016", 2017: "Comuni_2017", 2018: "Comuni_2018",
         2019: "Comuni_2019", 2020: "Comuni_2020", 2021: "Comuni_2021", 2022: "Comuni_2022", 2023: "Comuni_2023rev",
         2024: "Comuni_2024rev", 2025: "Comuni_2025"}
s = d[d.foglio.isin(SERIE.values())].copy()
s["anno"] = s.foglio.map({v: k for k, v in SERIE.items()})
s["m2_per_ab"] = s.csuolo1 * 10000 / s.clammi4
s = s.rename(columns={"csuolo1": "consumato_ha", "csuolo4": "consumato_pct", "clammi3": "superficie_ha", "clammi4": "popolazione"})

CITTA = {15146: "Milano", 58091: "Roma", 1272: "Torino", 63049: "Napoli", 37006: "Bologna", 48017: "Firenze", 10025: "Genova"}
keep = ["pro_com", "nome_comune", "anno", "foglio", "consumato_ha", "consumato_pct", "superficie_ha", "popolazione", "m2_per_ab", "csuolo9", "formet4"]
c = s[s.pro_com.isin(CITTA)][keep].sort_values(["pro_com", "anno"])
# incrementi netti da differenza di stock (serie coerente), per anno medio
c["consumato_ha_prec"] = c.groupby("pro_com").consumato_ha.shift()
c["anno_prec"] = c.groupby("pro_com").anno.shift()
c["incremento_netto_ha"] = c.consumato_ha - c.consumato_ha_prec
c["incremento_netto_ha_per_anno"] = c.incremento_netto_ha / (c.anno - c.anno_prec)
c.round(3).to_csv(os.path.join(P, "serie_citta.csv"), sep=";", index=False)
c[c.pro_com == 15146].round(3).to_csv(os.path.join(P, "serie_milano.csv"), sep=";", index=False)

# incrementi pubblicati da ISPRA (dati principali, per periodo)
wb = openpyxl.load_workbook(os.path.join(base, "raw", "snpa", "consumo_suolo_2026_dati_principali.xlsx"), read_only=True)
it = wb["Comuni_2006_2025"].iter_rows(values_only=True)
head = next(it)
inc = pd.DataFrame([r for r in it if r[0] is not None], columns=head)
inc = inc.rename(columns={"PRO_COM": "pro_com"})
periodi = ["2006-2012", "2012-2015", "2015-2016", "2016-2017", "2017-2018", "2018-2019", "2019-2020", "2020-2021", "2021-2022", "2022-2023", "2023-2024", "2024-2025"]
long = []
for p in periodi:
    t = inc[["pro_com", f"Incremento netto {p} [ettari]", f"Incremento lordo {p} [ettari]", f"Ripristino {p} [ettari]"]].copy()
    t.columns = ["pro_com", "netto_ha", "lordo_ha", "ripristino_ha"]
    t["periodo"] = p
    a, b = map(int, p.split("-"))
    t["anni"] = b - a
    long.append(t)
inc_long = pd.concat(long)
inc_long.to_csv(os.path.join(P, "incrementi_pubblicati_comuni_lungo.csv"), sep=";", index=False)
im = inc_long[inc_long.pro_com == 15146].copy()
im["netto_ha_per_anno"] = im.netto_ha / im.anni
im["lordo_ha_per_anno"] = im.lordo_ha / im.anni
im.round(3).to_csv(os.path.join(P, "incrementi_milano_periodi.csv"), sep=";", index=False)

# confronto citta' 2025 (+ incrementi pubblicati 2012-2025 e 2018-2025)
def somma(pc_df, periodi_sel, col):
    return pc_df[pc_df.periodo.isin(periodi_sel)].groupby("pro_com")[col].sum()

p1225 = periodi[1:]
p1825 = periodi[5:]  # 2018-2019 ... 2024-2025
n1225, l1225, r1225 = (somma(inc_long, p1225, k) for k in ["netto_ha", "lordo_ha", "ripristino_ha"])
n1825, l1825 = somma(inc_long, p1825, "netto_ha"), somma(inc_long, p1825, "lordo_ha")
n0612 = inc_long[inc_long.periodo == "2006-2012"].set_index("pro_com").netto_ha
n2425, l2425, r2425 = (inc_long[inc_long.periodo == "2024-2025"].set_index("pro_com")[k] for k in ["netto_ha", "lordo_ha", "ripristino_ha"])
a25 = s[s.anno == 2025].set_index("pro_com")
a06 = s[s.anno == 2006].set_index("pro_com")
a12 = s[s.anno == 2012].set_index("pro_com")
a18 = s[s.anno == 2018].set_index("pro_com")

def tabella(idx):
    t = pd.DataFrame(index=idx)
    t["comune"] = a25.loc[idx, "nome_comune"]
    t["provincia"] = a25.loc[idx, "nome_provincia"]
    t["superficie_ha"] = a25.loc[idx, "superficie_ha"]
    t["popolazione_2025"] = a25.loc[idx, "popolazione"]
    t["consumato_2006_ha"] = a06.loc[idx, "consumato_ha"]
    t["consumato_2012_ha"] = a12.loc[idx, "consumato_ha"]
    t["consumato_2018_ha"] = a18.loc[idx, "consumato_ha"]
    t["consumato_2025_ha"] = a25.loc[idx, "consumato_ha"]
    t["consumato_2006_pct"] = a06.loc[idx, "consumato_pct"]
    t["consumato_2025_pct"] = a25.loc[idx, "consumato_pct"]
    t["m2_per_abitante_2025"] = a25.loc[idx, "m2_per_ab"]
    t["m2_per_abitante_2006"] = a06.loc[idx, "m2_per_ab"]
    t["netto_2006_2012_ha"] = n0612.reindex(idx)
    t["netto_2012_2025_ha_pubblicato"] = n1225.reindex(idx)
    t["lordo_2012_2025_ha_pubblicato"] = l1225.reindex(idx)
    t["ripristino_2012_2025_ha_pubblicato"] = r1225.reindex(idx)
    t["netto_2018_2025_ha_pubblicato"] = n1825.reindex(idx)
    t["lordo_2018_2025_ha_pubblicato"] = l1825.reindex(idx)
    t["netto_2024_2025_ha"] = n2425.reindex(idx)
    t["lordo_2024_2025_ha"] = l2425.reindex(idx)
    t["ripristino_2024_2025_ha"] = r2425.reindex(idx)
    t["netto_2012_2025_ha_da_stock"] = t.consumato_2025_ha - t.consumato_2012_ha
    t["netto_2018_2025_ha_da_stock"] = t.consumato_2025_ha - t.consumato_2018_ha
    t["netto_2018_2025_per_100ha_comune"] = 100 * t.netto_2018_2025_ha_da_stock / t.superficie_ha
    t["isola_calore_2025_C"] = a25.loc[idx, "iscalo1"]
    t["densita_ab_per_ha"] = a25.loc[idx, "formet4"]
    return t

conf = tabella(list(CITTA)).reset_index().rename(columns={"index": "pro_com"})
conf.round(2).to_csv(os.path.join(P, "confronto_citta_2025.csv"), sep=";", index=False)

# grandi comuni (>= 100.000 abitanti)
tutti = tabella(a25.index.tolist())
grandi = tutti[tutti.popolazione_2025 >= 100000].sort_values("consumato_2025_pct", ascending=False)
grandi["rango_pct"] = range(1, len(grandi) + 1)
grandi.round(2).reset_index().rename(columns={"index": "pro_com"}).to_csv(os.path.join(P, "grandi_comuni_2025.csv"), sep=";", index=False)

# tutti i comuni: rango nazionale di Milano per % consumata
tutti["rango_pct_nazionale"] = tutti.consumato_2025_pct.rank(ascending=False, method="min")

# Citta' metropolitana di Milano (cod_prov 15)
mi_idx = a25[a25.cod_prov == 15].index
metro = tabella(list(mi_idx))
metro = metro.reset_index().rename(columns={"index": "pro_com"}).sort_values("consumato_2025_pct", ascending=False)
metro.round(2).to_csv(os.path.join(P, "metro_comuni.csv"), sep=";", index=False)
top = metro[metro.pro_com != 15146].sort_values("netto_2018_2025_ha_da_stock", ascending=False).head(25)
top.round(2).to_csv(os.path.join(P, "metro_top_recenti.csv"), sep=";", index=False)

# totali metro e Milano / resto
tm = metro.select_dtypes("number").sum()
tot_metro = {
    "comuni": int(len(metro)),
    "superficie_ha": float(metro.superficie_ha.sum()),
    "consumato_2006_ha": float(metro.consumato_2006_ha.sum()), "consumato_2012_ha": float(metro.consumato_2012_ha.sum()),
    "consumato_2018_ha": float(metro.consumato_2018_ha.sum()), "consumato_2025_ha": float(metro.consumato_2025_ha.sum()),
    "popolazione_2025": int(metro.popolazione_2025.sum()),
    "netto_2012_2025_ha_da_stock": float(metro.netto_2012_2025_ha_da_stock.sum()),
    "netto_2012_2025_ha_pubblicato": float(metro.netto_2012_2025_ha_pubblicato.sum()),
    "netto_2018_2025_ha_da_stock": float(metro.netto_2018_2025_ha_da_stock.sum()),
}
mil = metro[metro.pro_com == 15146].iloc[0]
resto = metro[metro.pro_com != 15146]
tot_metro["resto_senza_milano"] = {
    "consumato_2025_ha": float(resto.consumato_2025_ha.sum()), "superficie_ha": float(resto.superficie_ha.sum()),
    "netto_2012_2025_ha_da_stock": float(resto.netto_2012_2025_ha_da_stock.sum()),
    "netto_2018_2025_ha_da_stock": float(resto.netto_2018_2025_ha_da_stock.sum()),
    "popolazione_2025": int(resto.popolazione_2025.sum()),
}

# edizioni: quanto cambia il numero di Milano da un'edizione all'altra (2025 vs 2026), e foglio originale vs "rev"
ed = d[(d.pro_com == 15146)][["foglio", "anno", "revisione", "csuolo1", "csuolo4", "clammi4"]]
ed.to_csv(os.path.join(P, "edizioni_milano.csv"), sep=";", index=False)

riepilogo = {
    "milano_2025": {k: (float(mil[k]) if isinstance(mil[k], (int, float, np.floating, np.integer)) else str(mil[k])) for k in mil.index},
    "milano_rango_pct_nazionale": int(tutti.loc[15146, "rango_pct_nazionale"]), "n_comuni_italia": int(len(tutti)),
    "grandi_comuni_n": int(len(grandi)), "milano_rango_grandi": int(grandi.loc[15146, "rango_pct"]),
    "metro": tot_metro,
}
json.dump(riepilogo, open(os.path.join(P, "riepilogo_indicatori.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps(riepilogo, ensure_ascii=False, indent=1)[:4000])
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(conf[["comune", "superficie_ha", "popolazione_2025", "consumato_2006_pct", "consumato_2025_pct", "consumato_2025_ha", "m2_per_abitante_2006", "m2_per_abitante_2025", "netto_2012_2025_ha_pubblicato", "netto_2012_2025_ha_da_stock", "netto_2018_2025_ha_pubblicato", "netto_2024_2025_ha"]].round(1).to_string())
print(top[["comune", "superficie_ha", "consumato_2025_pct", "netto_2018_2025_ha_da_stock", "netto_2018_2025_ha_pubblicato", "lordo_2018_2025_ha_pubblicato", "netto_2018_2025_per_100ha_comune"]].round(1).to_string())
print(grandi[["comune", "consumato_2025_pct", "popolazione_2025", "rango_pct"]].head(15).round(1).to_string())
