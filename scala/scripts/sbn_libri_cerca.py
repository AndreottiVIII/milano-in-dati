"""Ricerca di libri e locandine sulla Scala in SBN. Usa sbn_lib (3 s tra richieste, STOP su blocco) con cache in raw/sbn_libri.
Uso: python -I -X utf8 scripts/sbn_libri_cerca.py "query1" "query2" ...   [--pagine N]"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbn_lib
sbn_lib.ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw", "sbn_libri")
args = [a for a in sys.argv[1:] if not a.startswith("--")]
maxp = 2
if "--pagine" in sys.argv: maxp = int(sys.argv[sys.argv.index("--pagine") + 1]); args = [a for a in args if a != str(maxp)]
out = {}
for q in args:
    recs = []; start = 0
    while True:
        try:
            d, cached = sbn_lib.get("search", {"any": q, "rows": 100, "start": start})
        except sbn_lib.Blocked as e:
            print("BLOCCO, mi fermo:", e); sys.exit(2)
        recs += d.get("briefRecords", [])
        start += 100
        if start >= d.get("numFound", 0) or start >= 100 * maxp: break
    out[q] = {"numFound": d.get("numFound"), "recs": [{"id": r["codiceIdentificativo"], "t": r["titolo"], "p": r.get("pubblicazione"), "tipo": r.get("tipo"), "liv": r.get("livello"), "a": r.get("autorePrincipale"), "n": r.get("note")} for r in recs]}
    print(f"{q!r}: trovati {d.get('numFound')}, letti {len(recs)}", flush=True)
json.dump(out, open(os.path.join(sbn_lib.ROOT, "_ultima_ricerca.json"), "w", encoding="utf8"), ensure_ascii=False, indent=0)
