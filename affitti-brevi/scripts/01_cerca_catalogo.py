import sys, json, urllib.request, urllib.parse, time
# uso: python -I -X utf8 01_cerca_catalogo.py <dominio> <query>...
dom=sys.argv[1]
for q in sys.argv[2:]:
    u=f"https://{dom}/api/catalog/v1?"+urllib.parse.urlencode({"q":q,"limit":30,"only":"datasets"})
    req=urllib.request.Request(u,headers={"User-Agent":"milano-in-dati research"})
    d=json.load(urllib.request.urlopen(req,timeout=60))
    print("==",q,d.get("resultSetSize"))
    for r in d["results"]:
        m=r["resource"]; print(m["id"],"|",m["name"],"|",(m.get("updatedAt") or "")[:10],"|",m.get("type"))
    time.sleep(2)
