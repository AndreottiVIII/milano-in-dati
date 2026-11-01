"""Confronto (solo confronto) fra nuovo suolo consumato per NIL (pulito/nil_suolo.csv) e il filone costruzioni (costruzioni/pulito/nil_costruzioni.csv).
Uso: python -I -X utf8 confronto_costruzioni.py <suolo assoluto> <costruzioni/pulito assoluto>
"""
import sys, os
import pandas as pd
from scipy.stats import spearmanr
base, cos = sys.argv[1], sys.argv[2]
a = pd.read_csv(os.path.join(base, "pulito", "nil_suolo.csv"), sep=";")
b = pd.read_csv(os.path.join(cos, "nil_costruzioni.csv"), sep=";")
m = a.merge(b, on="id_nil", suffixes=("", "_c"))
cols = ["id_nil", "nil", "area_ha", "pct_2025", "nuovo_2012_2025_ha", "ripristino_2012_2025_ha", "nuove_abitazioni_2014_2024", "volume_nuovi_m3", "dbt_volume_nuove_m3",
        "dbt_volume_sparite_m3", "dbt_volume_netto_m3", "dbt_volume_2012_m3", "dbt_volume_2020_m3", "var_pop_2014_2024"]
m = m[cols]
m["volume_nuovo_dbt_per_ha_nuovo_suolo"] = m.dbt_volume_nuove_m3 / m.nuovo_2012_2025_ha.where(m.nuovo_2012_2025_ha > 0)
m.round(2).to_csv(os.path.join(base, "pulito", "confronto_costruzioni_nil.csv"), sep=";", index=False)
for c in ["nuove_abitazioni_2014_2024", "volume_nuovi_m3", "dbt_volume_nuove_m3", "dbt_volume_netto_m3", "var_pop_2014_2024"]:
    r = spearmanr(m.nuovo_2012_2025_ha, m[c], nan_policy="omit")
    print(c, "spearman con nuovo suolo 2012-25 (ha):", round(r.statistic, 2), "p=", round(r.pvalue, 4), "n=", m[c].notna().sum())
tot = m[["nuovo_2012_2025_ha", "dbt_volume_nuove_m3", "dbt_volume_sparite_m3", "dbt_volume_netto_m3", "nuove_abitazioni_2014_2024"]].sum()
print(tot)
top = m.sort_values("nuovo_2012_2025_ha", ascending=False).head(8)
print("quota del nuovo suolo nei primi 8 NIL:", round(100 * top.nuovo_2012_2025_ha.sum() / m.nuovo_2012_2025_ha.sum(), 1), "% ; quota volume nuovo DBT:", round(100 * top.dbt_volume_nuove_m3.sum() / m.dbt_volume_nuove_m3.sum(), 1), "% ; quota abitazioni nuove:", round(100 * top.nuove_abitazioni_2014_2024.sum() / m.nuove_abitazioni_2014_2024.sum(), 1), "%")
print(top[["nil", "nuovo_2012_2025_ha", "dbt_volume_nuove_m3", "nuove_abitazioni_2014_2024"]].to_string())
