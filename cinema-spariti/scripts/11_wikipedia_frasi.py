import sys, json, re, csv
base = sys.argv[1]
d = json.load(open(f"{base}/raw/wikipedia/wikitext.json", encoding="utf-8"))
rows = []
for t, p in d.items():
    w = re.sub(r"<ref[^>]*?/>|<ref.*?</ref>", "", p["wikitext"], flags=re.S)
    w = re.sub(r"\{\{[^{}]*\}\}", "", w); w = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", w); w = re.sub(r"'{2,}", "", w)
    for s in re.split(r"(?<=[.!?])\s+|\n", w):
        if re.search(r"cinema", s, re.I) and re.search(r"\b(1[89]\d\d|20[0-2]\d)\b", s) and len(s) < 500:
            rows.append([t, p["pageid"], p.get("wikibase") or "", s.strip()])
with open(f"{base}/pulito/wikipedia_frasi_cinema.csv", "w", newline="", encoding="utf-8") as f:
    wr = csv.writer(f); wr.writerow(["pagina_it_wikipedia", "pageid", "wikidata", "frase"]); wr.writerows(rows)
print(len(rows), len({r[0] for r in rows}), "pagine")
