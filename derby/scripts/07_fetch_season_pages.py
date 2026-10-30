"""Fetch wikitext of the competition/season pages linked from the it.wiki derby table (non Serie A) + early seasons.
Usage: python -I 07_fetch_season_pages.py <derby_dir>"""
import sys, re, csv, json, os, time, requests
base = sys.argv[1]
UA = {"User-Agent": "MilanoInDati/1.0 (research; davide.caniatti@gmail.com)"}
rows = list(csv.DictReader(open(base + "/pulito/_itwiki_matches.csv", encoding="utf-8")))
pages = []
for x in rows:
    if x["competition"].startswith("Serie A"): continue
    m = re.match(r"\[\[([^\]|]+)", x["competition_raw"])
    if m and m.group(1) not in pages: pages.append(m.group(1))
for p in pages:
    dest = base + "/raw/wikipedia/seasons/" + re.sub(r"[^\w\-]", "_", p) + ".wiki"
    if os.path.exists(dest): continue
    r = requests.get("https://it.wikipedia.org/w/api.php", params={"action": "query", "prop": "revisions", "rvprop": "content|ids", "rvslots": "main", "titles": p, "format": "json", "formatversion": 2, "redirects": 1}, headers=UA, timeout=60)
    pg = r.json()["query"]["pages"][0]
    if "revisions" not in pg: print("missing", p); continue
    open(dest, "w", encoding="utf-8").write(pg["revisions"][0]["slots"]["main"]["content"])
    print("ok", p, pg["revisions"][0]["revid"])
    time.sleep(1.5)
