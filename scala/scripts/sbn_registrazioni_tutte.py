"""Registrazioni sonore alla Scala (SBN): scarica la scheda completa di TUTTI i candidati (2.994) non ancora in cache.
Stesso cliente educato di sbn_lib (3 s, cache in raw/sbn/full, STOP su blocchi). UN SOLO PROCESSO. Riprendibile.
Uso (dalla cartella scala/): python -I -X utf8 scripts/sbn_registrazioni_tutte.py"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbn_lib as s
cand = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sbn", "_registrazioni_candidati.json"), encoding="utf8"))
print("candidati:", len(cand), flush=True)
n = 0
for i, r in enumerate(cand):
    try:
        d, cached = s.get("full", {"bid": r["codiceIdentificativo"]})
    except s.Blocked as e:
        print("BLOCCO, mi fermo:", e, flush=True); sys.exit(2)
    except Exception as e:
        print("ERR", r["codiceIdentificativo"], e, flush=True); continue
    if not cached:
        n += 1
        if n % 50 == 0: print(f"{i+1}/{len(cand)} scaricate {n}", flush=True)
print("FINE", n, flush=True)
