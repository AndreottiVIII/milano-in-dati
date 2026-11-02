"""Mostra le righe di un foglio ACI che contengono una parola. Uso: esplora2.py <cartella auto> <anno> <file: pv|cop> <parte nome foglio> <parola>"""
import sys, glob, os, re
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(HERE)), "parcheggi", "scripts"))
from ods_lettore import fogli

A, y, which, part, word = sys.argv[1:6]
pat = "Parco_veicolare_%s.ods" if which == "pv" else "Circolante_Copert_%s.ods"
p = glob.glob(os.path.join(A, "raw", "aci", "x" + y, "**", pat % y), recursive=True)[0]
f = fogli(p)
for n, r in f.items():
    if part.lower() in n.lower().replace("_", " "):
        print("--", n, len(r))
        for x in r[:3]:
            print("   H", x[:16])
        for x in r:
            if any(word.lower() in c.lower() for c in x[:5]):
                print("   ", x[:16])
