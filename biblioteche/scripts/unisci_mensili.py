"""Unisce gli aggregati mensili in pulito/cubo_prestiti_completo.parquet e pulito/titoli_anno_completo.parquet.
Uso: python -I -X utf8 unisci_mensili.py <biblioteche_abs>   (dopo build_mensili.py)"""
import sys, os, glob
import pandas as pd
O = os.path.join(sys.argv[1], "pulito")
c = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(O, "mensili_parquet", "cubo_*.parquet")))])
c.to_parquet(os.path.join(O, "cubo_prestiti_completo.parquet"), index=False)
t = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(O, "mensili_parquet", "titoli_*.parquet")))])
t["anno"] = t.mese_inizio.str[:4]
y = t.groupby(["anno", "titolo", "autore", "media", "supporto", "lingua", "eta_fascia"], as_index=False).n.sum()
y.to_parquet(os.path.join(O, "titoli_anno_completo.parquet"), index=False)
print(len(c), c.n.sum(), len(y), y.n.sum())
