"""Scarica l'intero catalogo (titoli, descrizioni) di dati.lombardia.it dall'API pubblica Socrata e cerca parole chiave.
Uso: python -I -X utf8 catalogo_lombardia.py <out_json>"""
import sys, json, urllib.request, re
out = sys.argv[1]
res = []
off = 0
while True:
    url = f"https://api.eu.socrata.com/api/catalog/v1?domains=www.dati.lombardia.it&limit=100&offset={off}&only=datasets"
    req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/antenne (ricerca open data)"})
    j = json.load(urllib.request.urlopen(req, timeout=60))
    r = j.get("results", [])
    if not r: break
    for x in r:
        rs = x["resource"]
        res.append({"id": rs["id"], "name": rs["name"], "desc": (rs.get("description") or "")[:400], "updated": rs.get("data_updated_at"), "cat": x.get("classification", {}).get("domain_category")})
    off += 100
    if off > 20000: break
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False)
print(len(res))
pat = re.compile(r"elettromagn|radiofrequen|\bcem\b|telefon|castel|radiobase|radio base|antenn|telecomun|ripetitor|v/m|5g|emf|radiotelev|inquinamento", re.I)
for x in res:
    if pat.search(x["name"] + " " + x["desc"]):
        print(x["id"], "|", x["name"][:90], "|", (x["updated"] or "")[:10], "|", x["cat"])
