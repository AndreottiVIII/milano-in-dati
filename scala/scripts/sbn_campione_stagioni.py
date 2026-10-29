"""Campione SBN: per alcuni anni scarica i record 'teatro alla scala AAAA' (pagine da 100, pausa 3 s),
tiene quelli con editore/luogo che nomina la Scala e l'anno, e li salva in CSV + JSON grezzo."""
import json, sys, time, urllib.request, urllib.parse, csv, re, os
UA = "MilanoInDati-research/0.1 (davide.caniatti@gmail.com; small samples)"
out = sys.argv[1]; years = [int(a) for a in sys.argv[2:]]
os.makedirs(out, exist_ok=True)
def get(q, start):
    u = "https://opac.sbn.it/opacmobilegw/search.json?" + urllib.parse.urlencode({"any": q, "rows": 100, "start": start})
    with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": UA}), timeout=60) as f:
        return json.load(f)
for y in years:
    recs = []; start = 0
    while True:
        d = get(f"teatro alla scala {y}", start); time.sleep(3)
        recs += d.get("briefRecords", [])
        start += 100
        if start >= d.get("numFound", 0) or start >= 400: break
    json.dump(recs, open(f"{out}/q_{y}.json", "w", encoding="utf8"), ensure_ascii=False)
    keep = []
    for r in recs:
        pub = r.get("pubblicazione", "") or ""
        if re.search(r"scala", pub + (r.get("autorePrincipale") or ""), re.I) and re.search(rf"\b({y}|{y+1})\b", pub):
            keep.append(r)
    with open(f"{out}/campione_{y}.csv", "w", newline="", encoding="utf8") as f:
        w = csv.writer(f); w.writerow(["id", "titolo", "pubblicazione"])
        for r in keep: w.writerow([r["codiceIdentificativo"], r["titolo"], r.get("pubblicazione", "")])
    print(y, "trovati", len(recs), "tenuti", len(keep), flush=True)
