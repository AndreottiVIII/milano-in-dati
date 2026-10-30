import sys, os, time, json, requests
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "MilanoInDati/1.0 (davide.caniatti@gmail.com; progetto dati aperti)"}
API = "https://it.wikipedia.org/w/api.php"
def get(params):
    for a in range(4):
        r = requests.get(API, params={**params, "format":"json","formatversion":2}, headers=UA, timeout=60)
        if r.status_code == 200: time.sleep(1); return r.json()
        time.sleep(10*(a+1))
    raise SystemExit("fail")
def members(cat):
    res=[]; cont={}
    while True:
        d=get({"action":"query","list":"categorymembers","cmtitle":cat,"cmlimit":500,"cmtype":"page|subcat",**cont})
        res+=d["query"]["categorymembers"]
        if "continue" in d: cont=d["continue"]
        else: break
    return res
roots=["Categoria:Cinema di Milano","Categoria:Sale cinematografiche di Milano","Categoria:Teatri di Milano","Categoria:Sale cinematografiche della Lombardia","Categoria:Cinema scomparsi di Milano","Categoria:Sale cinematografiche scomparse"]
seen={}; cats={}
queue=[(c,0) for c in roots]
while queue:
    c,dep=queue.pop(0)
    if c in cats: continue
    try: m=members(c)
    except SystemExit: continue
    cats[c]=[x["title"] for x in m]
    print(c,len(m))
    for x in m:
        if x["ns"]==14 and dep<2 and any(k in x["title"] for k in ("Milano","milanes")): queue.append((x["title"],dep+1))
        elif x["ns"]==0: seen[x["title"]]=x["pageid"]
json.dump({"categorie":cats,"pagine":seen}, open(os.path.join(out,"categorie.json"),"w",encoding="utf8"), ensure_ascii=False, indent=1)
print("pagine",len(seen))
# wikitext di ogni pagina (batch da 20 titoli, rvslots)
titles=list(seen)
pages={}
fn=os.path.join(out,"wikitext.json")
for i in range(0,len(titles),20):
    d=get({"action":"query","prop":"revisions|coordinates|pageprops","rvprop":"content","rvslots":"main","titles":"|".join(titles[i:i+20]),"colimit":50,"ppprop":"wikibase_item"})
    for p in d["query"]["pages"]:
        if "revisions" in p:
            pages[p["title"]]={"pageid":p["pageid"],"wikitext":p["revisions"][0]["slots"]["main"]["content"],"coords":p.get("coordinates"),"wikibase":p.get("pageprops",{}).get("wikibase_item")}
json.dump(pages, open(fn,"w",encoding="utf8"), ensure_ascii=False)
print("wikitext",len(pages), os.path.getsize(fn))
