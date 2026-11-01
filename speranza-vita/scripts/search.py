"""Cerca nel CKAN del Comune di Milano. Uso: python -I -X utf8 search.py <raw_dir>"""
import sys, os, json, urllib.request, urllib.parse
raw = sys.argv[1]
terms = ["speranza di vita","mortalità","decessi","morti","deceduti","mortality","aspettativa di vita","cause di morte","tavole di mortalità","decessi per età","decessi NIL","salute","sanitari","ATS","epidemiologico","longevità","anni di vita"]
seen = {}
for t in terms:
    url = "https://dati.comune.milano.it/api/3/action/package_search?rows=100&q=" + urllib.parse.quote(t)
    req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/1.0 (ricerca open data)"})
    try:
        d = json.load(urllib.request.urlopen(req, timeout=60))["result"]
    except Exception as e:
        print("ERR", t, e); continue
    print(t, d["count"])
    for p in d["results"]:
        seen[p["name"]] = {"title": p["title"], "notes": (p.get("notes") or "")[:300], "modified": p.get("metadata_modified"), "res": [(r["format"], r["url"]) for r in p["resources"]], "terms": seen.get(p["name"], {}).get("terms", []) + [t]}
json.dump(seen, open(os.path.join(raw, "search_all.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(seen))
