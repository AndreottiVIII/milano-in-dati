"""PNRR (Italia Domani / ReGiS, open data CC-BY 4.0, estrazione 13/06/2026): progetti localizzati nel Comune di Milano.
Uso: python -I -X utf8 02_pnrr_milano.py <dir_raw_italiadomani> <out_csv>
- Localizzazione: righe con Descrizione Comune = MILANO e provincia 015 (un CUP puo' avere piu' righe: percentuale di localizzazione).
- Progetti e Pagamenti agganciati per CUP + Codice Locale Progetto (CLP) se presente, altrimenti per CUP.
Scrive un CSV con una riga per (CUP, CLP, localizzazione)."""
import sys, os, pandas as pd
R, out = sys.argv[1], sys.argv[2]
rd = lambda f: pd.read_csv(os.path.join(R, f), sep=";", dtype=str, encoding="utf-8-sig", keep_default_na=False)
loc = rd("PNRR_Localizzazione.csv")
print("localizzazione righe", len(loc), "estrazione", loc["Data di Estrazione"].iloc[0])
lm = loc[(loc["Descrizione Comune"].str.upper() == "MILANO") & (loc["Provincia"] == "015")].copy()
print("righe Milano", len(lm), "CUP", lm["CUP"].nunique())
pr = rd("PNRR_Progetti.csv")
pr = pr[pr["CUP"].isin(set(lm["CUP"]))]
print("progetti con CUP a Milano", len(pr))
pg = rd("PNRR_Pagamenti_di_Progetto.csv")
pg = pg[pg["CUP"].isin(set(lm["CUP"]))]
m = lm.merge(pr, on=["CUP", "Codice Locale Progetto"], how="left", suffixes=("", "_p"), indicator=True)
print("loc->progetti", m["_merge"].value_counts().to_dict())
m = m.drop(columns="_merge")
pgc = [c for c in pg.columns if c not in ("Codice Univoco Submisura", "Descrizione Submisura", "Data di Estrazione")]
pg = pg[pgc].add_prefix("PAG ").rename(columns={"PAG CUP": "CUP", "PAG Codice Locale Progetto": "Codice Locale Progetto"})
m = m.merge(pg, on=["CUP", "Codice Locale Progetto"], how="left")
m.to_csv(out, sep=";", index=False, encoding="utf-8")
print("scritto", out, len(m))
