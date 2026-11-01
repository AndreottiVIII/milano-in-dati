"""Quanto cambia il numero di Milano e delle citta' di confronto fra edizione 2025 (anni 2006-2024) e edizione 2026 (2006-2025), file SNPA 'dati principali'.
Uso: python -I -X utf8 confronto_edizioni.py <suolo assoluto>
Scrive pulito/confronto_edizioni_2025_2026.csv
"""
import sys, os
import pandas as pd, openpyxl
base = sys.argv[1]
def leggi(f, foglio):
    wb = openpyxl.load_workbook(os.path.join(base, "raw", "snpa", f), read_only=True)
    it = wb[foglio].iter_rows(values_only=True); h = next(it)
    return pd.DataFrame([r for r in it if r[0] is not None], columns=h)
a = leggi("consumo_di_suolo_estratto_dati_2025_anni_2006_2024.xlsx", "Comuni_2006_2024")
b = leggi("consumo_suolo_2026_dati_principali.xlsx", "Comuni_2006_2025")
CITTA = {15146: "Milano", 58091: "Roma", 1272: "Torino", 63049: "Napoli", 37006: "Bologna", 48017: "Firenze", 10025: "Genova"}
rows = []
for pc, n in CITTA.items():
    ra, rb = a[a.PRO_COM == pc].iloc[0], b[b.PRO_COM == pc].iloc[0]
    for p in ["2006-2012", "2012-2015", "2015-2016", "2016-2017", "2017-2018", "2018-2019", "2019-2020", "2020-2021", "2021-2022", "2022-2023", "2023-2024"]:
        k = f"Incremento netto {p} [ettari]"
        rows.append({"comune": n, "periodo": p, "netto_ed2025_ha": ra[k], "netto_ed2026_ha": rb[k], "differenza_ha": rb[k] - ra[k]})
    rows.append({"comune": n, "periodo": "stock 2024 (ha)", "netto_ed2025_ha": ra["Suolo consumato 2024 [ettari]"], "netto_ed2026_ha": None, "differenza_ha": None})
d = pd.DataFrame(rows)
d.round(2).to_csv(os.path.join(base, "pulito", "confronto_edizioni_2025_2026.csv"), sep=";", index=False)
print(d[d.comune == "Milano"].round(2).to_string())
t = d[d.periodo.str.contains("-")].groupby("comune")[["netto_ed2025_ha", "netto_ed2026_ha"]].sum().round(1); print(t)
