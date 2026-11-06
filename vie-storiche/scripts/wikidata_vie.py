# -*- coding: utf-8 -*-
"""Elenca le strade/piazze di Milano su Wikidata (API normale, non SPARQL che il robots.txt vieta) e scarica le voci in raw/wikidata/.
Uso: python -I -X utf8 wikidata_vie.py"""
import json, os, time, urllib.request, urllib.parse
QUI = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(os.path.dirname(QUI), "raw", "wikidata")
os.makedirs(RAW, exist_ok=True)
UA = {"User-Agent": "milano-in-dati/1.0"}
def get(p):
    for t in range(6):
        time.sleep(4 + 20 * t)
        try:
            with urllib.request.urlopen(urllib.request.Request("https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode(p), headers=UA), timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
    raise SystemExit("429 persistente")
ids = set()
for cls in ["Q79007", "Q174782", "Q34442", "Q787113"]:
    off = 0
    while True:
        d = get({"action": "query", "list": "search", "srsearch": f"haswbstatement:P131=Q490 haswbstatement:P31={cls}", "srlimit": 50, "sroffset": off, "format": "json"})
        for s in d["query"]["search"]: ids.add(s["title"])
        if "continue" not in d: break
        off = d["continue"]["sroffset"]
ids = sorted(ids); print(len(ids), "voci")
ent = {}
for i in range(0, len(ids), 50):
    d = get({"action": "wbgetentities", "ids": "|".join(ids[i:i+50]), "props": "labels|claims", "format": "json"})
    ent.update(d["entities"])
json.dump(ent, open(os.path.join(RAW, "strade_milano.json"), "w", encoding="utf-8"), ensure_ascii=False)
