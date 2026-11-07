"""Scrive docs/costruzioni/data/nil_anni.csv: abitazioni dei nuovi edifici per quartiere e per anno di ritiro del titolo, 2014-2024.
Uso: python -I -X utf8 pagina_v3_dati.py <costruzioni_dir> <docs_dir>
Valori aggregati per quartiere e anno (nessun modulo singolo). Controlla i totali con nil.csv e serie_annuale.csv."""
import sys, os
import pandas as pd
K, DOCS = sys.argv[1], sys.argv[2]
D = os.path.join(DOCS, "costruzioni", "data")
t = pd.read_csv(os.path.join(K, "pulito", "titoli_edilizi.csv"), sep=";", dtype={"civico": str}, low_memory=False)
x = t[(t.intervento == "nuovo_fabbricato") & (t.flag_anno_fuori_serie == 0) & t.anno.between(2014, 2024)].copy()
x["anno"] = x.anno.astype(int)
nil = pd.read_csv(os.path.join(D, "nil.csv"), sep=";")
y = x[x.id_nil.notna()].copy(); y["id_nil"] = y.id_nil.astype(int)
p = y.pivot_table(index="id_nil", columns="anno", values="abitazioni", aggfunc="sum", fill_value=0)
p = p.reindex(nil.id_nil, fill_value=0).reindex(columns=range(2014, 2025), fill_value=0).astype(int)
out = pd.DataFrame({"id_nil": nil.id_nil.values, "nil": nil.nil.values})
for a in range(2014, 2025): out["a%d" % a] = p[a].values
tot = out[[c for c in out.columns if c.startswith("a")]].sum(axis=1)
assert (tot.values == nil.nuove_abitazioni_2014_2024.values).all(), "totali per quartiere diversi da nil.csv"
sa = pd.read_csv(os.path.join(D, "serie_annuale.csv"), sep=";").set_index("anno")
senza = x[x.id_nil.isna()].groupby("anno").abitazioni.sum()
for a in range(2014, 2025):
    assert int(out["a%d" % a].sum() + senza.get(a, 0)) == int(sa.loc[a, "abitazioni"]), a
out.to_csv(os.path.join(D, "nil_anni.csv"), index=False, sep=";")
print("ok", len(out), int(tot.sum()), int(senza.sum()))
