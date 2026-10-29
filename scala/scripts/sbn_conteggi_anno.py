"""Conta i record SBN per anno (solo numFound, rows=1) per due ricerche. Piccolo campione, pausa 3 s."""
import json, sys, time, urllib.request, urllib.parse, csv
UA = "MilanoInDati-research/0.1 (davide.caniatti@gmail.com; small samples)"
out = sys.argv[1]
def n(q):
    u = "https://opac.sbn.it/opacmobilegw/search.json?" + urllib.parse.urlencode({"any": q, "rows": 1})
    r = urllib.request.Request(u, headers={"User-Agent": UA})
    with urllib.request.urlopen(r, timeout=40) as f:
        return json.load(f).get("numFound", -1)
rows = []
for y in range(1964, 2024):
    a = n(f"teatro alla scala {y}"); time.sleep(3)
    b = n(f"edizioni della scala {y}"); time.sleep(3)
    rows.append((y, a, b)); print(y, a, b, flush=True)
with open(out, "w", newline="", encoding="utf8") as f:
    w = csv.writer(f); w.writerow(["anno", "teatro_alla_scala_anno", "edizioni_della_scala_anno"]); w.writerows(rows)
