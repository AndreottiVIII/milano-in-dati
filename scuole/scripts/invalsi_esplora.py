"""Prima occhiata ai microdati campione INVALSI: righe, codici, mancanti, regioni.

Uso: python -I -X utf8 invalsi_esplora.py <cartella raw/invalsi_campione>
"""
import os
import sys

import numpy as np
import pandas as pd

RAW = sys.argv[1]
FILES = {
    "G05 ITA 2025-26": "g05_2025-26/2026_matrice_campione_ita_05_0_1_wle_anonima.csv",
    "G05 MAT 2025-26": "g05_2025-26/2026_matrice_campione_mat_05_0_1_wle_anonima.csv",
    "G08 ITA 2024-25": "g08_2024-25/2025_matrice_campione_ita_08_0_1_wle_anonima.csv",
    "G08 MAT 2024-25": "g08_2024-25/2025_matrice_campione_mat_08_0_1_wle_anonima.csv",
}

for nome, rel in FILES.items():
    p = os.path.join(RAW, rel)
    with open(p, "rb") as f:
        testa = f.read(400)
    sep = ";" if testa.count(b";") > testa.count(b",") else ","
    d = pd.read_csv(p, sep=sep, encoding="latin1", low_memory=False, decimal=",")
    d.columns = [c.strip().lower() for c in d.columns]
    print("=" * 70)
    print(nome, "| sep", repr(sep), "| righe", len(d), "| colonne", d.shape[1])
    meta = [c for c in d.columns if not (c[0] in "abcdefghij" and c[1:2].isdigit())]
    print("colonne non-item:", meta)
    print(d[[c for c in meta if c.startswith(("peso", "wle", "escs", "pu_"))]].head(3).to_string())
    print(d[[c for c in meta if c.startswith(("peso", "wle", "escs", "pu_"))]].dtypes.to_string())
    scuola, classe, stud = "scuola_anonimo", "classe_anonimo", "studente_anonimo"
    print("scuole", d[scuola].nunique(), "| classi (id puro)", d[classe].nunique(), "| coppie scuola-classe", d[[scuola, classe]].drop_duplicates().shape[0])
    print("duplicati studente", d.duplicated([scuola, classe, stud]).sum())
    cs = d.groupby(scuola)[classe].nunique()
    print("classi per scuola:", cs.value_counts().sort_index().to_dict())
    print("regioni:", d["cod_reg"].value_counts().sort_index().to_dict())
    print("aree:", d["areageo_5"].value_counts().sort_index().to_dict())
    print("origine:", d["origine"].value_counts(dropna=False).sort_index().to_dict())
    lo = d[d["cod_reg"] == 4]
    print("Lombardia: studenti", len(lo), "scuole", lo[scuola].nunique(), "classi", lo[[scuola, classe]].drop_duplicates().shape[0])
    print("origine Lombardia:", lo["origine"].value_counts(dropna=False).sort_index().to_dict())
    for c in ["peso_studente", "peso_classe", "peso_scuola", "escs_studente", "escs_classe", "wle_ita_200", "wle_mat_200"]:
        if c in d:
            v = pd.to_numeric(d[c], errors="coerce")
            print(f"  {c}: mancanti {v.isna().mean():.3f} | media {v.mean():.3f} | sd {v.std():.3f} | min {v.min():.3f} | max {v.max():.3f}")
    d["_m"] = pd.to_numeric(d.get("escs_studente"), errors="coerce").isna()
    print("  mancanti ESCS per origine:", d.groupby("origine")["_m"].mean().round(3).to_dict())
    print("  media peso per regione 4:", pd.to_numeric(lo["peso_studente"], errors="coerce").sum())
