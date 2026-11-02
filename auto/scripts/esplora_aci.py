"""Esplora i fogli dei file ACI Autoritratto di un anno (solo per capire la struttura).
Uso: python -I -X utf8 esplora_aci.py <cartella auto> <anno> [parola da cercare nel nome foglio]"""
import sys, glob, os
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "parcheggi", "scripts"))
from ods_lettore import fogli

A, y = sys.argv[1], sys.argv[2]
for pat in ("Parco_veicolare_%s.ods", "Circolante_Copert_%s.ods"):
    p = glob.glob(os.path.join(A, "raw", "aci", "x" + y, "**", pat % y), recursive=True)[0]
    f = fogli(p, max_righe=4)
    print("##", os.path.basename(p))
    for n, r in f.items():
        print("  ", n, "|", (r[0][0] if r and r[0] else "")[:100])
