import sys, json, urllib.request
pid, out = sys.argv[1], sys.argv[2]
req = urllib.request.Request("https://dati.comune.milano.it/api/3/action/package_show?id="+pid, headers={"User-Agent":"Mozilla/5.0 (milano-in-dati research)"})
d = json.load(urllib.request.urlopen(req, timeout=60))
json.dump(d, open(out,"w",encoding="utf8"), ensure_ascii=False, indent=1)
r = d["result"]
print(r["title"], r.get("license_id"), r.get("metadata_modified"), r.get("frequency"))
print(r.get("notes"))
for x in r["resources"]: print(x["format"], x["url"], x.get("last_modified"))
