"""v1: confronto tra anagrafe del Comune (ds27, 31/12 anno Y) e ISTAT (POSAS/STRASA al 1 gennaio Y+1, popolazione 'censita' corretta col censimento permanente).
Uso: python -I -X utf8 v1_confronto_istat.py <popolazione assoluto> <milano-in-dati assoluto>   Scrive pulito/confronto_istat_comune.csv"""
import sys, os, zipfile
import pandas as pd
P, M = sys.argv[1], sys.argv[2]; out = os.path.join(P, "pulito")
src = os.path.join(M, "censimenti", "raw", "istat_demo")
g = pd.read_csv(os.path.join(out, "residenti_nil_anno_eta_genere.csv"))
cit = pd.read_csv(os.path.join(out, "residenti_comune_anno_cittadinanza.csv"))
rows = []
for y in range(2019, 2027):
    z = zipfile.ZipFile(os.path.join(src, f"POSAS_{y}_it_015_Milano.zip")); df = pd.read_csv(z.open(z.namelist()[0]), sep=";", skiprows=1, encoding="utf-8-sig", dtype={"Codice comune": str})
    df = df[df["Codice comune"] == "015146"]
    if "Totale" in df.columns:
        tot = df[df["Età"] == 999]["Totale"].iloc[0]; c100 = df[df["Età"] == 100]["Totale"].iloc[0]; c65 = df[(df["Età"] >= 65) & (df["Età"] < 999)]["Totale"].sum(); u15 = df[df["Età"] < 15]["Totale"].sum()
    else:
        cols = [c for c in df.columns if c.startswith("Totale")]
        tcol = [c for c in df.columns if c.lower() in ("totale", "totale ")]
        # formato 2019-2025: colonne per stato civile, uso la somma di maschi e femmine
        df = df.copy()
        num = df.drop(columns=["Codice comune", "Comune", "Età"]).apply(pd.to_numeric, errors="coerce")
        df["_t"] = num.sum(axis=1)
        eta = pd.to_numeric(df["Età"], errors="coerce")
        tot = df[eta == 999]["_t"].iloc[0] if (eta == 999).any() else df[eta < 999]["_t"].sum()
        c100 = df[eta == 100]["_t"].iloc[0]; c65 = df[(eta >= 65) & (eta < 999)]["_t"].sum(); u15 = df[eta < 15]["_t"].sum()
    z2 = zipfile.ZipFile(os.path.join(src, f"STRASA_{y}_it_015_Milano.zip")); d2 = pd.read_csv(z2.open(z2.namelist()[0]), sep=";", skiprows=1, encoding="utf-8-sig", dtype={"Codice comune": str})
    d2 = d2[d2["Codice comune"] == "015146"]
    num2 = d2.drop(columns=[c for c in ("Codice comune", "Comune", "Età") if c in d2.columns]).apply(pd.to_numeric, errors="coerce")
    et2 = pd.to_numeric(d2['Età'], errors='coerce')
    st_istat = (num2.sum(axis=1))[et2 < 999].sum()
    ya = y - 1
    gy = g[g.anno == ya]
    rows.append(dict(anno_comune_31dic=ya, comune_totale=int(gy.residenti.sum()), istat_1gen_totale=tot, comune_su_istat=gy.residenti.sum() / tot,
                     comune_100p=int(gy[gy.eta == 100].residenti.sum()), istat_100=c100, comune_65p=int(gy[gy.eta >= 65].residenti.sum()), istat_65p=c65,
                     comune_0_14=int(gy[gy.eta < 15].residenti.sum()), istat_0_14=u15,
                     comune_stranieri=int(cit[(cit.anno == ya) & (cit.cittadinanza != "Italia")].residenti.sum()), istat_stranieri=st_istat, strasa_colonne=";".join(d2.columns[:6])))
r = pd.DataFrame(rows); r.to_csv(os.path.join(out, "confronto_istat_comune.csv"), index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(r.drop(columns=["strasa_colonne"]).to_string()); print(r.strasa_colonne.iloc[0])
