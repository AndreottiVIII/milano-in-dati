"""b1: legge ds27 (residenti per NIL, eta singola, genere, cittadinanza, 31/12 di ogni anno 1999-2025) e produce le tabelle pulite
per le storie B (cittadinanze) e C (eta, centenari).
Uso: python -I -X utf8 b1_ds27.py <popolazione assoluto> <milano-in-dati assoluto>
Nessun valore del file originale e' cancellato o corretto; il codice 'n.d.' e le 'Nil' vuote sono tenute e contate in controlli_ds27.json."""
import sys, os, json
import numpy as np, pandas as pd
P, M = sys.argv[1], sys.argv[2]
src = os.path.join(P, "raw", "comune_ds27", "unzip", "ds27_pop_sto_quartiere.csv")
out = os.path.join(P, "pulito")
os.makedirs(out, exist_ok=True)
df = pd.read_csv(src, sep=";", dtype={"Eta": str, "Cittadinanza": str, "Nil": str})
chk = {"righe": int(len(df)), "residenti_totali_somma_anni": int(df.Residenti.sum())}
df["Nil"] = df["Nil"].str.strip()
# eta: '100 e piu' -> 100
df["eta"] = df.Eta.str.replace("100 e più", "100").astype(int)
df = df.rename(columns={"Anno": "anno", "IdNil": "id_nil", "Nil": "nil", "Genere": "genere", "Cittadinanza": "cittadinanza", "Residenti": "residenti"})
chk["id_nil_distinti"] = int(df.id_nil.nunique())
chk["nomi_per_id"] = int(df.groupby("id_nil").nil.nunique().max())
chk["valori_nulli"] = {c: int(df[c].isna().sum()) for c in df.columns}
chk["residenti_zero_o_negativi"] = int((df.residenti <= 0).sum())
chk["cittadinanze_distinte"] = int(df.cittadinanza.nunique())
# tot per anno
tot = df.groupby("anno").residenti.sum()
chk["totale_per_anno"] = {int(k): int(v) for k, v in tot.items()}
# anagrafica NIL
ana = df[["id_nil", "nil"]].drop_duplicates().sort_values("id_nil")
cens = pd.read_csv(os.path.join(M, "censimenti", "pulito", "nil_2021_anagrafica.csv"))
ana = ana.merge(cens[["nil", "municipio_prevalente", "area_km2"]].rename(columns={"nil": "id_nil"}), on="id_nil", how="left")
ana.to_csv(os.path.join(out, "nil_anagrafica.csv"), index=False)
chk["nil_senza_area"] = int(ana.area_km2.isna().sum())

# 1) residenti per anno, nil, eta, genere (somma sulle cittadinanze) + stranieri
df["straniero"] = df.cittadinanza != "Italia"
g = df.groupby(["anno", "id_nil", "genere", "eta"]).residenti.sum().reset_index()
g.to_csv(os.path.join(out, "residenti_nil_anno_eta_genere.csv"), index=False)
gs = df[df.straniero].groupby(["anno", "id_nil", "eta"]).residenti.sum().reset_index().rename(columns={"residenti": "stranieri"})
# 2) per cittadinanza
c = df.groupby(["anno", "id_nil", "cittadinanza"]).residenti.sum().reset_index()
c.to_csv(os.path.join(out, "residenti_nil_anno_cittadinanza.csv"), index=False)
cc = df.groupby(["anno", "cittadinanza"]).residenti.sum().reset_index()
cc.to_csv(os.path.join(out, "residenti_comune_anno_cittadinanza.csv"), index=False)

# 3) indicatori di eta per nil-anno
def indic(gr):
    ages = gr.groupby("eta").residenti.sum().reindex(range(0, 101), fill_value=0).values.astype(float)
    n = ages.sum()
    if n == 0:
        return pd.Series(dtype=float)
    a = np.arange(101)
    mean = (a * ages).sum() / n       # eta compiuta; l'eta media esatta e' circa +0,5
    cum = ages.cumsum()
    k = int(np.searchsorted(cum, n / 2))
    prev = cum[k - 1] if k > 0 else 0
    med = k + (n / 2 - prev) / ages[k]   # interpolazione dentro l'anno di eta k
    r = dict(residenti=n, eta_media=mean, eta_mediana=med,
             q_0_14=ages[:15].sum() / n, q_15_64=ages[15:65].sum() / n, q_65p=ages[65:].sum() / n, q_80p=ages[80:].sum() / n, q_90p=ages[90:].sum() / n,
             n_0_14=ages[:15].sum(), n_65p=ages[65:].sum(), n_80p=ages[80:].sum(), n_90p=ages[90:].sum(), n_100p=ages[100], n_20_34=ages[20:35].sum(), n_25_34=ages[25:35].sum())
    r["indice_vecchiaia"] = 100 * ages[65:].sum() / ages[:15].sum() if ages[:15].sum() else np.nan
    return pd.Series(r)
ind = g.groupby(["anno", "id_nil"]).apply(indic, include_groups=False).reset_index()
# stranieri per nil-anno
st = gs.groupby(["anno", "id_nil"]).stranieri.sum().reset_index()
ind = ind.merge(st, on=["anno", "id_nil"], how="left")
ind["stranieri"] = ind.stranieri.fillna(0)
ind["quota_stranieri"] = ind.stranieri / ind.residenti
ind = ind.merge(ana[["id_nil", "nil", "area_km2"]], on="id_nil", how="left")
ind["densita_ab_km2"] = ind.residenti / ind.area_km2
ind.to_csv(os.path.join(out, "eta_nil_anno_indicatori.csv"), index=False, float_format="%.6g")
# comune intero
gc = g.groupby(["anno", "genere", "eta"]).residenti.sum().reset_index()
gc.to_csv(os.path.join(out, "residenti_comune_anno_eta_genere.csv"), index=False)
indc = gc.groupby("anno").apply(indic, include_groups=False).reset_index()
indc.to_csv(os.path.join(out, "eta_comune_anno_indicatori.csv"), index=False, float_format="%.6g")
# centenari per anno e genere (comune) e per nil
cen = g[g.eta == 100].groupby(["anno", "genere"]).residenti.sum().unstack().fillna(0).astype(int)
cen["totale"] = cen.sum(axis=1)
cen.to_csv(os.path.join(out, "centenari_comune_anno_genere.csv"))
cn = g[g.eta == 100].groupby(["anno", "id_nil"]).residenti.sum().reset_index().rename(columns={"residenti": "centenari"})
cn = cn.merge(ana[["id_nil", "nil"]], on="id_nil")
cn.to_csv(os.path.join(out, "centenari_nil_anno.csv"), index=False)
json.dump(chk, open(os.path.join(out, "controlli_ds27.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(chk, ensure_ascii=False)[:1500])
