"""Rete della metropolitana per anno di apertura: scrive docs/metro/data/rete_segmenti_anno.json
Un tratto = due stazioni vicine della stessa linea; esiste dall'anno in cui sono aperte entrambe su quella linea.
L'ordine delle stazioni lungo ogni linea e' quello gia' usato dallo schema a 45 gradi (schema45.py).
Le lunghezze sono in linea d'aria tra stazioni vicine: sono una stima, non i chilometri ufficiali ATM.
Uso: python -I -X utf8 rete_anno.py <cartella milano-in-dati>"""
import ast, csv, json, math, re, sys
ROOT = sys.argv[1]
src = open(ROOT + "/metro/scripts/schema45.py", encoding="utf8").read()
m = re.search(r"^LINEE = (\{.*?^\})", src, re.S | re.M)
LINEE = ast.literal_eval(m.group(1))
ST = {}
for r in csv.DictReader(open(ROOT + "/docs/metro/data/stazioni_metro.csv", encoding="utf8")):
    ap = {}
    for p in r["apertura_per_linea (da it.wikipedia, CC BY-SA 4.0)"].split(";"):
        l, d = p.strip().split(":")
        ap[l] = int(d[:4])
    ST[r["stazione"]] = dict(lat=float(r["lat"]), lon=float(r["lon"]), ap=ap)
def km(a, b):
    R = 6371.0
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dl = math.radians(b["lon"] - a["lon"]); dp = p2 - p1
    h = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))
seg = []
for l, paths in LINEE.items():
    for path in paths:
        nomi = [x for x in path if isinstance(x, str)]
        for a, b in zip(nomi, nomi[1:]):
            y = max(ST[a]["ap"][l], ST[b]["ap"][l])
            seg.append(dict(l=l, a=a, b=b, y=y, km=round(km(ST[a], ST[b]), 3)))
anni = {}
for y in range(1964, 2026):
    d = {"km": {}, "stazioni": 0, "stazioni_linea": 0}
    for l in LINEE:
        d["km"][l] = round(sum(s["km"] for s in seg if s["l"] == l and s["y"] <= y), 1)
    d["km_tot"] = round(sum(d["km"].values()), 1)
    d["stazioni"] = sum(1 for s in ST.values() if min(s["ap"].values()) <= y)
    d["stazioni_linea"] = sum(1 for s in ST.values() for v in s["ap"].values() if v <= y)
    anni[y] = d
out = dict(
    nota="Tratti tra stazioni vicine, anno = apertura di entrambe le stazioni sulla linea; km in linea d'aria (stima). Stazioni: GTFS ATM/AMAT (CC BY) e date da Wikipedia (CC BY-SA 4.0).",
    stazioni={n: dict(lat=round(s["lat"], 5), lon=round(s["lon"], 5), ap=s["ap"]) for n, s in ST.items()},
    segmenti=seg, anni=anni)
open(ROOT + "/docs/metro/data/rete_segmenti_anno.json", "w", encoding="utf8").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
for y in (1964, 1990, 2015, 2019, 2022, 2023, 2024, 2025):
    print(y, anni[y]["km_tot"], anni[y]["stazioni"], anni[y]["stazioni_linea"], anni[y]["km"])
print(len(seg), "tratti")
