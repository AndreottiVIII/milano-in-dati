"""Per le pagine delle categorie it.wikipedia: QID Wikidata (pageprops) e, per quelle non gia in Wikidata-P840/P915-Milano, dati base via wbgetentities. Uso: python -I wp_qid.py <raw/wikipedia> <raw/wikidata>"""
import sys, os, json, time, requests
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)"}
wp, wd = sys.argv[1], sys.argv[2]
cat = json.load(open(os.path.join(wp, "categorie.json"), encoding="utf8"))
pages = {}
for root, tree in cat.items():
    for c, v in tree.items():
        for p in v.get("pages", []):
            pages.setdefault(p["title"], set()).add(c)
titles = sorted(pages)
out = os.path.join(wp, "pagine_qid.json")
if not os.path.exists(out):
    res = {}
    for i in range(0, len(titles), 50):
        time.sleep(1.2)
        r = requests.get("https://it.wikipedia.org/w/api.php", params={"action": "query", "prop": "pageprops", "ppprop": "wikibase_item", "titles": "|".join(titles[i:i+50]), "redirects": 1, "format": "json"}, headers=UA, timeout=60).json()
        red = {x["from"]: x["to"] for x in r["query"].get("redirects", [])}
        byt = {p["title"]: p.get("pageprops", {}).get("wikibase_item") for p in r["query"]["pages"].values()}
        for t in titles[i:i+50]:
            res[t] = byt.get(red.get(t, t))
    json.dump({"pagine": {t: {"qid": res[t], "categorie": sorted(pages[t])} for t in titles}}, open(out, "w", encoding="utf8"), ensure_ascii=False, indent=1)
d = json.load(open(out, encoding="utf8"))["pagine"]
known = {x["w"]["value"].split("/")[-1] for x in json.load(open(os.path.join(wd, "opere_base.json"), encoding="utf8"))["results"]["bindings"]}
miss = sorted({v["qid"] for v in d.values() if v["qid"] and v["qid"] not in known})
print("pagine", len(d), "senza qid", sum(1 for v in d.values() if not v["qid"]), "qid mancanti da WD-Milano", len(miss))
out2 = os.path.join(wp, "mancanti_wikidata.json")
if not os.path.exists(out2):
    ents = {}
    for i in range(0, len(miss), 50):
        time.sleep(1.5)
        r = requests.get("https://www.wikidata.org/w/api.php", params={"action": "wbgetentities", "ids": "|".join(miss[i:i+50]), "props": "labels|claims|sitelinks", "languages": "it|en", "format": "json"}, headers=UA, timeout=90).json()
        for q, e in r["entities"].items():
            def ids(p): return [c["mainsnak"]["datavalue"]["value"]["id"] for c in e.get("claims", {}).get(p, []) if c["mainsnak"].get("datavalue")]
            def times(p): return [c["mainsnak"]["datavalue"]["value"]["time"] for c in e.get("claims", {}).get(p, []) if c["mainsnak"].get("datavalue")]
            ents[q] = {"it": e.get("labels", {}).get("it", {}).get("value"), "en": e.get("labels", {}).get("en", {}).get("value"), "P31": ids("P31"), "P840": ids("P840"), "P915": ids("P915"), "P577": times("P577"), "P57": ids("P57"), "P50": ids("P50"), "P136": ids("P136"), "P345": [c["mainsnak"]["datavalue"]["value"] for c in e.get("claims", {}).get("P345", []) if c["mainsnak"].get("datavalue")], "itwiki": e.get("sitelinks", {}).get("itwiki", {}).get("title"), "enwiki": e.get("sitelinks", {}).get("enwiki", {}).get("title")}
    json.dump(ents, open(out2, "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("FINE")
