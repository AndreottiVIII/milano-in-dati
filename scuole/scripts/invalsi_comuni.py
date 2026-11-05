"""Report generale INVALSI (popolazione, open data): Milano come comune, per origine, e confronto tra comuni.

Uso: python -I -X utf8 invalsi_comuni.py <zip report generale> <cartella scuole>
Legge il CSV dentro lo zip senza estrarlo. Quota di cittadinanza non italiana per comune dal MIM.
"""
import glob
import os
import sys
import zipfile

import numpy as np
import pandas as pd

ZIP, BASE = sys.argv[1], sys.argv[2]
z = zipfile.ZipFile(ZIP)
nome = z.namelist()[0]
with z.open(nome) as f:
    testa = f.readline().decode("latin1")
sep = ";" if testa.count(";") > testa.count(",") else ","
with z.open(nome) as f:
    d = pd.read_csv(f, sep=sep, encoding="latin1", dtype=str, keep_default_na=False)
print(list(d.columns))
print(d.Aggregato_territoriale.value_counts().to_dict())
print("anni", sorted(d.Anno.unique()))
agg = d.aggregazione.str.strip()
print("aggregazioni comune plesso:", d[d.Aggregato_territoriale == "Comune plesso"].aggregazione.str.strip().value_counts().head(12).to_dict())
print("esempi denominazione:", d[d.Aggregato_territoriale == "Comune plesso"].Denominazione.head(5).tolist())
for c in ["Punteggio_wle_medio", "media_ESCS", "Percentuale_partecipazione", "Dev_Std_Punteggio_wle"]:
    d[c] = pd.to_numeric(d[c].str.replace(",", ".", regex=False), errors="coerce")
    d.loc[d[c].isin([888, 999]), c] = np.nan
d["agg"] = agg
d["den"] = d.Denominazione.str.strip().str.upper()
CITTA = ["MILANO", "TORINO", "BOLOGNA", "FIRENZE", "ROMA", "GENOVA", "VENEZIA", "NAPOLI", "BRESCIA", "BERGAMO", "MONZA"]
pd.set_option("display.width", 220, "display.max_rows", 300, "display.max_columns", 30)

print("\n=== MILANO (Comune plesso), punteggio WLE ed ESCS per origine, gradi 5 e 8")
m = d[(d.Aggregato_territoriale == "Comune plesso") & (d.den == "MILANO") & d.Materia.isin(["Italiano", "Matematica"]) & d.Grado.isin(["5", "8"]) & d["agg"].isin(["", "Totale", "Nativo", "Straniero I generazione", "Straniero II generazione"])]
print(sorted(m["agg"].unique()))
print(m[m.Anno.isin(["2018-19", "2022-23", "2023-24", "2024-25"])].sort_values(["Grado", "Materia", "Anno", "agg"])[["Grado", "Materia", "Anno", "agg", "Punteggio_wle_medio", "media_ESCS", "Percentuale_partecipazione"]].round(2).to_string(index=False))

print("\n=== STESSE RIGHE: Lombardia, Italia, provincia di Milano (2024-25)")
for tipo, den in (("Regione", "LOMBARDIA"), ("Provincia", "MILANO"), ("Italia", "ITALIA")):
    x = d[(d.Aggregato_territoriale == tipo) & (d.den == den) & d.Materia.isin(["Italiano", "Matematica"]) & d.Grado.isin(["5", "8"]) & (d.Anno == "2024-25") & d["agg"].isin(["", "Nativo", "Straniero I generazione", "Straniero II generazione"])]
    print(tipo, den)
    print(x.sort_values(["Grado", "Materia", "agg"])[["Grado", "Materia", "agg", "Punteggio_wle_medio", "media_ESCS"]].round(2).to_string(index=False))

print("\n=== CITTA 2024-25: nativi, grado 5 e 8")
x = d[(d.Aggregato_territoriale == "Comune plesso") & d.den.isin(CITTA) & d.Materia.isin(["Italiano", "Matematica"]) & d.Grado.isin(["5", "8"]) & (d.Anno == "2024-25") & d["agg"].isin(["Nativo", "Straniero I generazione", "Straniero II generazione"])]
print(x.pivot_table(index=["Grado", "Materia", "den"], columns="agg", values="Punteggio_wle_medio").round(1).to_string())

# quota cittadinanza non italiana per comune: MIM 2024/25, statali + paritarie
print("\n=== COMUNI: quota MIM di non italiani in primaria e sec. I contro punteggio dei nativi (2024-25)")
ang = []
for f in ["SCUANAGRAFESTAT20242520250831.csv", "SCUANAGRAFEPAR20242520250831.csv"]:
    p = os.path.join(BASE, "raw", "miur", f)
    a = pd.read_csv(p, dtype=str, keep_default_na=False)
    a.columns = [c.strip() for c in a.columns]
    ang.append(a[["CODICESCUOLA", "DESCRIZIONECOMUNE", "REGIONE", "AREAGEOGRAFICA"]])
ang = pd.concat(ang).drop_duplicates("CODICESCUOLA")
cit = []
for f in ["ALUITASTRACITSTA20242520250831.csv", "ALUITASTRACITPAR20242520250831.csv"]:
    p = os.path.join(BASE, "raw", "miur", f)
    a = pd.read_csv(p, dtype=str, keep_default_na=False)
    a.columns = [c.strip() for c in a.columns]
    cit.append(a)
cit = pd.concat(cit)
print("colonne cittadinanza:", list(cit.columns))
tot = "ALUNNI" if "ALUNNI" in cit.columns else [c for c in cit.columns if c.startswith("ALUNNI") and "CITT" not in c][0]
non = [c for c in cit.columns if "NONITALIANA" in c and "UE" not in c.replace("CITTADINANZA", "").replace("NONITALIANA", "")]
non = non[0] if non else [c for c in cit.columns if "NONITAL" in c][0]
ita = [c for c in cit.columns if "CITTADINANZAITALIANA" in c][0]
for c in (non, ita):
    cit[c] = pd.to_numeric(cit[c], errors="coerce")
cit = cit.merge(ang, on="CODICESCUOLA", how="inner")
print("ordini MIM:", cit.ORDINESCUOLA.value_counts().to_dict())
ORD = {"5": "SCUOLA PRIMARIA", "8": "SCUOLA SECONDARIA I GRADO"}
for gr, o in ORD.items():
    c = cit[cit.ORDINESCUOLA == o].groupby(["DESCRIZIONECOMUNE", "REGIONE", "AREAGEOGRAFICA"]).agg(non=(non, "sum"), ita=(ita, "sum")).reset_index()
    c["alunni"] = c.non + c.ita
    c["quota"] = c.non / c.alunni * 100
    c["den"] = c.DESCRIZIONECOMUNE.str.strip().str.upper()
    for mat in ("Italiano", "Matematica"):
        v = d[(d.Aggregato_territoriale == "Comune plesso") & (d.Grado == gr) & (d.Materia == mat) & (d.Anno == "2024-25")]
        nat = v[v["agg"] == "Nativo"].set_index("den")["Punteggio_wle_medio"]
        tuttiv = v[v["agg"] == ""].set_index("den")
        k = c.merge(nat.rename("nativi"), left_on="den", right_index=True, how="inner")
        for regione, q in (("LOMBARDIA", k[k.REGIONE == "LOMBARDIA"]), ("NORD", k[k.AREAGEOGRAFICA.isin(["NORD OVEST", "NORD EST"])])):
            for soglia in (0, 300, 1000):
                w = q[(q.alunni >= soglia) & q.nativi.notna()]
                if len(w) < 8:
                    continue
                print(f"G{gr} {mat} {regione}, comuni con almeno {soglia} alunni: n={len(w)}, Spearman quota-punteggio nativi {w.quota.corr(w.nativi, method='spearman'):+.2f}, Pearson pesato n.d.; Milano quota {c[c.den=='MILANO'].quota.iloc[0]:.1f}, nativi Milano {nat.get('MILANO', float('nan')):.1f}")
    print(c[c.den.isin(CITTA)][["den", "alunni", "quota"]].round(1).to_string(index=False))
