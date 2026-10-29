"""Fase 1: interroga SBN OPAC (search.json) per anno e per stagione. Riprendibile (cache in raw/sbn/search)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbn_lib as s
def season(y):
    return f"{y}-{str(y+1)[2:]}"
queries = []
for y in range(1963, 2025):
    queries.append(f"teatro alla scala {y}")
for y in range(1963, 2024):
    queries.append(f"rappresentazioni teatro alla scala {season(y)}")
    queries.append(f"teatro alla scala stagione {season(y)}")
for y in range(1963, 2012):
    queries.append(f"piccola scala {y}")
queries += ["arcimboldi teatro alla scala", "teatro alla scala arcimboldi 2003", "teatro alla scala arcimboldi 2004", "teatro alla scala tournée"]
for q in queries:
    start = 0
    while True:
        d, cached = s.get("search", {"any": q, "rows": 100, "start": start})
        n = d.get("numFound", 0)
        if start == 0: print(f"{q!r}: numFound={n}{' (cache)' if cached else ''}", flush=True)
        got = len(d.get("briefRecords", []))
        start += 100
        if start >= n or got == 0: break
print("FINE", flush=True)
