# Fase 3: scarica il testo (con numero di versione) delle voci it usate dagli eventi aggiunti.
import sys, json
sys.path.insert(0, sys.argv[1]); import wpx
raw = sys.argv[2]
titles = ['Volante Rossa "Martiri Partigiani"', "Giorgio Ambrosoli", "Danilo Abbruciati", "Pasqua Rossa", "Caserma Santa Barbara", "Terrorismo in Italia", "Rapimento di Carlo Saronio", "Strage del Diana"]
out = {}
d = wpx.api("it", action="query", titles="|".join(titles), prop="revisions|info|coordinates|pageprops", rvprop="content|ids|timestamp", rvslots="main", inprop="url", redirects="1", colimit="max", ppprop="wikibase_item")
for p in d["query"]["pages"]:
    if p.get("missing"): print("MISSING", p["title"]); continue
    r = p["revisions"][0]
    out[p["title"]] = {"text": r["slots"]["main"]["content"], "revid": r["revid"], "ts": r["timestamp"], "url": p["fullurl"], "coords": p.get("coordinates", []), "qid": p.get("pageprops", {}).get("wikibase_item")}
json.dump(out, open(raw + "/wikitext_fase3.json", "w", encoding="utf-8"), ensure_ascii=False)
print({k: (v["revid"], v["ts"][:10]) for k, v in out.items()})
