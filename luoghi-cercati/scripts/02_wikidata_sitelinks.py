"""Passo 2: sitelink Wikipedia (tutte le lingue) degli elementi di Milano, via API wbgetentities (50 per chiamata;
la query SPARQL sui sitelink va in timeout), + controllo di completezza: elementi entro 12 km dal Duomo con articolo
in it.wikipedia ma senza catena P131 fino a Milano (Q490).
Uso: python -I -X utf8 02_wikidata_sitelinks.py <luoghi-cercati assoluto>
Scrive raw/wikidata_sitelinks.json e raw/wikidata_raggio12km.json. Fonte: wikidata.org (API e SPARQL), dati CC0."""
import sys, os, json, time, requests
UA="MilanoInDati/1.0 (https://github.com/AndreottiVIII/milano-in-dati)"
base=sys.argv[1]; raw=os.path.join(base,"raw")
H={"User-Agent":UA}
def sparql(q):
    for i in range(5):
        try:
            r=requests.post("https://query.wikidata.org/sparql",data={"query":q},headers={**H,"Accept":"application/sparql-results+json"},timeout=100)
        except Exception as e:
            print("errore",e,flush=True); time.sleep(10); continue
        if r.ok: return [{k:v["value"] for k,v in b.items()} for b in r.json()["results"]["bindings"]]
        print("retry",r.status_code,r.text[:150],flush=True); time.sleep(20*(i+1))
    raise SystemExit("sparql fallita")
def api(ids):
    for i in range(5):
        r=requests.get("https://www.wikidata.org/w/api.php",params={"action":"wbgetentities","ids":"|".join(ids),"props":"sitelinks","format":"json","maxlag":5},headers=H,timeout=60)
        if r.ok and "entities" in r.json(): return r.json()["entities"]
        print("retry api",r.status_code,r.text[:150],flush=True); time.sleep(5*(i+1))
    raise SystemExit("api fallita")
items=sorted({r["item"].split("/")[-1] for r in json.load(open(os.path.join(raw,"wikidata_items_classi.json"),encoding="utf8"))["righe"]})
q2="""SELECT ?item ?coord ?itemLabel_it ?itemLabel_en ?cls ?clsLabel_en ?title WHERE {
  SERVICE wikibase:around { ?item wdt:P625 ?coord . bd:serviceParam wikibase:center "Point(9.19 45.4642)"^^geo:wktLiteral . bd:serviceParam wikibase:radius "12" . }
  ?art schema:about ?item ; schema:isPartOf <https://it.wikipedia.org/> ; schema:name ?title .
  FILTER NOT EXISTS { ?item wdt:P131* wd:Q490 }
  OPTIONAL { ?item wdt:P31 ?cls . OPTIONAL { ?cls rdfs:label ?clsLabel_en FILTER(lang(?clsLabel_en)="en") } }
  OPTIONAL { ?item rdfs:label ?itemLabel_it FILTER(lang(?itemLabel_it)="it") }
  OPTIONAL { ?item rdfs:label ?itemLabel_en FILTER(lang(?itemLabel_en)="en") }
}"""
rows2=sparql(q2)
json.dump({"scaricato":time.strftime("%Y-%m-%d"),"query":q2,"righe":rows2},open(os.path.join(raw,"wikidata_raggio12km.json"),"w",encoding="utf8"),ensure_ascii=False)
print("raggio",len(rows2),"elementi",len({r['item'] for r in rows2}),flush=True)
items=sorted(set(items)|{r["item"].split("/")[-1] for r in rows2})
cd=os.path.join(raw,"sitelinks_blocchi"); os.makedirs(cd,exist_ok=True)
ent={}
for i in range(0,len(items),50):
    cf=os.path.join(cd,f"{i:05d}_{len(items)}.json")
    if os.path.exists(cf): ent.update(json.load(open(cf,encoding="utf8"))); continue
    e=api(items[i:i+50]); json.dump(e,open(cf,"w",encoding="utf8"),ensure_ascii=False); ent.update(e); time.sleep(0.5)
rows=[]
for q,e in ent.items():
    for k,v in e.get("sitelinks",{}).items():
        rows.append({"item":q,"sitekey":k,"title":v["title"]})
json.dump({"scaricato":time.strftime("%Y-%m-%d"),"nota":"API wbgetentities props=sitelinks; sitekey tipo itwiki, commonswiki, itwikiquote...; include anche gli elementi del raggio 12 km","righe":rows},open(os.path.join(raw,"wikidata_sitelinks.json"),"w",encoding="utf8"),ensure_ascii=False)
print("sitelink",len(rows),"elementi",len(ent),flush=True)
