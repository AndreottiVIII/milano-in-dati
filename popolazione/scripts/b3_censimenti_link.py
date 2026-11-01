"""b3: riuso dei censimenti (filone censimenti/) per tornare prima del 1999 a livello di NIL: eta' e stranieri per NIL nei censimenti 1991 e 2001 (+2011, 2021, 2023),
confrontati con l'anagrafe del Comune (ds27) negli anni 2001 e 2011. Aggiunge la serie citta' degli stranieri per cittadinanza dal 1979 (ds74).
Uso: python -I -X utf8 b3_censimenti_link.py <popolazione assoluto> <milano-in-dati assoluto>"""
import sys, os
import numpy as np, pandas as pd
P, M = sys.argv[1], sys.argv[2]; out = os.path.join(P, "pulito")
c = pd.read_csv(os.path.join(M, "censimenti", "pulito", "indicatori_NIL.csv"))
keep = ["anno", "nil", "nil_nome", "pop", "quota_0_14", "quota_65p", "quota_75p", "indice_vecchiaia", "eta_media_classi", "stran", "quota_stranieri"]
c[keep].rename(columns={"nil": "id_nil", "pop": "residenti_censimento", "stran": "stranieri_censimento", "quota_0_14": "q_0_14_pct", "quota_65p": "q_65p_pct", "quota_75p": "q_75p_pct", "eta_media_classi": "eta_media_classi_75p_82", "quota_stranieri": "quota_stranieri_pct"}).to_csv(os.path.join(out, "censimenti_nil_eta_stranieri_1991_2023.csv"), index=False, float_format="%.5g")
i = pd.read_csv(os.path.join(out, "eta_nil_anno_indicatori.csv"))
rows = []
for y in (2001, 2011):
    a = c[c.anno == y].set_index("nil")[["pop", "quota_65p", "quota_stranieri"]].rename(columns={"pop": "pop_cens", "quota_65p": "q65_cens", "quota_stranieri": "str_cens"})
    b = i[i.anno == y].set_index("id_nil")[["residenti", "q_65p", "quota_stranieri"]].rename(columns={"q_65p": "q65_an", "quota_stranieri": "str_an"})
    j = a.join(b, how="inner"); j = j[j.residenti >= 3000]
    rows.append(dict(anno=y, n_nil=len(j), corr_q65=np.corrcoef(j.q65_cens, j.q65_an * 100)[0, 1], diff_q65_punti_medio=float((j.q65_cens - j.q65_an * 100).mean()),
                     corr_stranieri=np.corrcoef(j.str_cens, j.str_an * 100)[0, 1], diff_stranieri_punti_medio=float((j.str_cens - j.str_an * 100).mean()),
                     diff_pop_pct_medio=float(((j.pop_cens - j.residenti) / j.residenti * 100).mean())))
print(pd.DataFrame(rows).round(3).to_string())
pd.DataFrame(rows).to_csv(os.path.join(out, "confronto_censimento_anagrafe_nil.csv"), index=False, float_format="%.4g")
# serie citta' stranieri per cittadinanza dal 1979 (ds74)
a = pd.read_csv(os.path.join(P, "raw", "comune_ds74", "ds74_stranieri_citt.csv"), sep=";")
a.columns = ["anno", "cittadinanza", "residenti"]
a.to_csv(os.path.join(out, "stranieri_citta_cittadinanza_1979_2025.csv"), index=False)
t = a.groupby("anno").residenti.sum(); print(t.loc[[1979, 1990, 1998]].to_dict())
