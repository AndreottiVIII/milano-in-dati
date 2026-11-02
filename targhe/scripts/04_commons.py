"""Wikimedia Commons: file nella categoria 'Plaques in Milan' e sottocategorie (profondita' 3), con coordinate se presenti.
Si salvano solo METADATI (titolo, categorie, coordinate, data, autore/licenza breve). Nessuna immagine.
Uso: python -I -X utf8 04_commons.py <uscita json assoluta>"""
import sys, json, time, urllib.request, urllib.parse
API="https://commons.wikimedia.org/w/api.php"
UA={"User-Agent":"milano-in-dati research (davide.caniatti@gmail.com)"}
def get(**p):
    p["format"]="json"
    r=urllib.request.urlopen(urllib.request.Request(API+"?"+urllib.parse.urlencode(p),headers=UA),timeout=60)
    time.sleep(0.5); return json.load(r)
def members(cat,typ):
    out=[];cont={}
    while True:
        d=get(action="query",list="categorymembers",cmtitle=cat,cmtype=typ,cmlimit=500,**cont)
        out+=[m["title"] for m in d["query"]["categorymembers"]]
        if "continue" in d: cont={"cmcontinue":d["continue"]["cmcontinue"]}
        else: return out
seen={};files={}
def walk(cat,depth):
    if cat in seen: return
    seen[cat]=depth
    for f in members(cat,"file"): files.setdefault(f,[]).append(cat)
    if depth<3:
        for c in members(cat,"subcat"):
            if "Stolperstein" in c: continue
            walk(c,depth+1)
walk("Category:Plaques in Milan",0)
print(len(seen),"categorie",len(files),"file")
titles=list(files); info={}
for i in range(0,len(titles),40):
    d=get(action="query",titles="|".join(titles[i:i+40]),prop="coordinates|imageinfo|categories",iiprop="extmetadata",iiextmetadatafilter="DateTimeOriginal|LicenseShortName|Artist|ImageDescription",cllimit="max",colimit="max")
    for pg in d["query"]["pages"].values():
        co=pg.get("coordinates",[{}])[0]
        em=(pg.get("imageinfo",[{}])[0]).get("extmetadata",{})
        info[pg["title"]]={"lat":co.get("lat"),"lon":co.get("lon"),"cats":[c["title"] for c in pg.get("categories",[])],
            "data":em.get("DateTimeOriginal",{}).get("value"),"licenza":em.get("LicenseShortName",{}).get("value"),
            "descr":em.get("ImageDescription",{}).get("value"),"cat_origine":files[pg["title"]]}
json.dump({"categorie":seen,"file":info},open(sys.argv[1],"w",encoding="utf8"),ensure_ascii=False)
print(sum(1 for v in info.values() if v["lat"]),"con coordinate")
