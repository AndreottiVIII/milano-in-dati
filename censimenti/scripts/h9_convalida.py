"""Fase 2: confronta i nostri indicatori di comune con quelli pubblicati dal Comune (ds361, ds363, ds365, ds366) per 1991, 2001, 2011.
Uso: python -I h9_convalida.py <cartella censimenti>   Output: pulito/convalida_indicatori_Comune.csv"""
import sys, glob
import pandas as pd
root = sys.argv[1]; P = root + "/pulito/"; C = root + "/raw/comune_ckan/"
ours = pd.read_csv(P + "indicatori_comune.csv").set_index("anno")
ex = pd.read_csv(P + "eta_storica_milano_1881_2011.csv").set_index("anno")


def com(ds, ind):
    f = glob.glob(C + ds + "*/00*.csv")[0]
    x = pd.read_csv(f, sep=";", encoding="cp1252")
    x = x[(x.Territorio == "Milano") & (x.Indicatore == ind)]
    return {int(a): float(str(v).replace(".", "").replace(",", ".")) for a, v in zip(x.Anno, x["Valore indicatore"]) if str(v).strip() not in ("-", "nan")}


rows = []
def add(nome, ds, ind, col, src=ours):
    c = com(ds, ind)
    for y in (1991, 2001, 2011):
        rows.append(dict(indicatore=nome, anno=y, valore_nostro=round(float(src.loc[y, col]), 2), valore_Comune=c.get(y),
                         fonte_Comune=f"{ds} '{ind}'", campo_nostro=col))
add("Eta' media (da classi quinquennali)", "ds363", "Età media della popolazione", "eta_media_classi")
add("Famiglie di una persona %", "ds361", "Famiglie di un solo componente ogni 100 famiglie", "quota_famiglie_1_comp")
add("Stranieri ogni 100 residenti", "ds366", "Stranieri ogni 100 residenti", "quota_stranieri")
add("Componenti medi per famiglia", "ds361", "Numero medio di componenti per famiglia", "famiglie_comp_medio_esatto")
add("Tasso di occupazione (15 anni e piu')", "ds365", "Tasso di occupazione", "tasso_occupazione_15piu")
for y in (1991, 2001, 2011):   # eta' media esatta da ds300 contro classi
    rows.append(dict(indicatore="Eta' media: classi (nostro) contro eta' singola ds300", anno=y, valore_nostro=round(float(ours.loc[y, "eta_media_classi"]), 2),
                     valore_Comune=float(ex.loc[y, "eta_media"]), fonte_Comune="ds300 eta' singola (calcolo nostro)", campo_nostro="eta_media_classi"))
v = pd.DataFrame(rows); v["differenza"] = (v.valore_nostro - v.valore_Comune).round(2)
v.to_csv(P + "convalida_indicatori_Comune.csv", index=False)
pd.set_option("display.width", 250)
print(v.drop(columns=["fonte_Comune", "campo_nostro"]).to_string())
