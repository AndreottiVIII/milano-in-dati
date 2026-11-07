"""Scrive i file dati nuovi della pagina "Dove si costruisce" (versione 2): docs/costruzioni/data/titoli_trimestri_2021_2024.csv

Uso: python -I -X utf8 pagina_v2.py <costruzioni_dir> <docs_dir>
Conta i nuovi fabbricati (ogni uso) per trimestre dell'anno di ritiro e per tipo di titolo
(permesso di costruire, SCIA, SCIA alternativa). Controlla che i totali coincidano con trimestri_2021_2024.csv.
Nessun record singolo viene ripubblicato.
"""
import sys, os
import pandas as pd
K, DOCS = sys.argv[1], sys.argv[2]
t = pd.read_csv(os.path.join(K, "pulito", "titoli_edilizi.csv"), sep=";", dtype={"civico": str})
x = t[(t.intervento == "nuovo_fabbricato") & (t.flag_anno_fuori_serie == 0) & (t.anno >= 2021) & (t.anno <= 2024)].copy()
x["t"] = x.anno.astype(int).astype(str) + "-T" + (((x.mese.astype(int) - 1) // 3) + 1).astype(str)
x = x[x.tipo_titolo.notna()]
p = x.pivot_table(index="t", columns="tipo_titolo", values="id_modello", aggfunc="size", fill_value=0)
out = pd.DataFrame({"t": p.index, "permesso_di_costruire": p["Permesso di costruire"].values, "scia": p["SCIA"].values, "scia_alternativa": p["SCIA alternativa"].values})
out["totale_con_titolo"] = out.permesso_di_costruire + out.scia + out.scia_alternativa
ref = pd.read_csv(os.path.join(DOCS, "costruzioni", "data", "trimestri_2021_2024.csv"), sep=";").set_index("t")
for _, r in out.iterrows():
    print(r.t, int(r.totale_con_titolo), "atteso", int(ref.loc[r.t, "nuovi"]))
out.to_csv(os.path.join(DOCS, "costruzioni", "data", "titoli_trimestri_2021_2024.csv"), index=False, sep=";")
