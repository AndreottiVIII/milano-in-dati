"""SBN OPAC: conteggi per soggetto (solo fattibilita). Cliente educato (3 s). Uso: python -I sbn_fattibilita.py"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.stdout.reconfigure(encoding="utf8")
import sbn_lib as s
Qs = ["Milano - Narrativa","Milano - Romanzi","Milano - Racconti","Milano - Letteratura","Milano - Romanzi gialli","Milano - Gialli","Milano - Film","Milano - Cinema","Milano - Narrativa italiana","Milano (Italia) - Narrativa","Milano <città> - Narrativa","Milano","Milano <città>","Milano - Opere narrative","Milano - Romanzi, racconti, novelle","Milano - Storia - Narrativa"]
res = {}
for q in Qs:
    d, c = s.get("search", {"subject": q, "rows": 100, "start": 0})
    n = d.get("numFound", 0); res[q] = n
    print(f"{q!r}: {n}  campione:", [r["titolo"][:50] for r in d.get("briefRecords", [])[:3]], flush=True)
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw", "sbn", "_conteggi.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
