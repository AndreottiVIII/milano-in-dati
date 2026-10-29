import sys, json, os, time
sys.path.insert(0, sys.argv[1]); import wp
raw = sys.argv[2]
pages = list(json.load(open(raw+"/pagine_categorie.json", encoding="utf-8")).keys())
import os as _o
if _o.path.exists(raw+"/ricerche.json"): pages += list(json.load(open(raw+"/ricerche.json", encoding="utf-8")).keys())
pages = list(dict.fromkeys(pages))
pages = [p for p in pages if not p.startswith(("Categoria:", "Template:", "Wikipedia:", "Portale:", "File:", "Aiuto:"))]
outf = raw+"/info_pagine.jsonl"
done = set()
if os.path.exists(outf):
    for l in open(outf, encoding="utf-8"): done.add(json.loads(l)["title"])
todo = [p for p in pages if p not in done]
print(len(pages), "pagine,", len(todo), "da fare", flush=True)
with open(outf, "a", encoding="utf-8") as f:
    for i in range(0, len(todo), 20):
        b = todo[i:i+20]
        d = wp.api(action="query", titles="|".join(b), prop="extracts|coordinates|pageprops|categories", exintro="1", explaintext="1", exlimit="20",
                   colimit="max", cllimit="max", ppprop="wikibase_item|disambiguation", redirects="1")
        for pg in d["query"]["pages"]:
            if pg.get("missing"): continue
            f.write(json.dumps({"title": pg["title"], "pageid": pg.get("pageid"), "extract": pg.get("extract", ""), "coords": pg.get("coordinates", []),
                "qid": pg.get("pageprops", {}).get("wikibase_item"), "disamb": "disambiguation" in pg.get("pageprops", {}),
                "cats": [c["title"] for c in pg.get("categories", [])]}, ensure_ascii=False) + "\n")
        f.flush()
        if i % 400 == 0: print(i, flush=True)
        time.sleep(0.2)
