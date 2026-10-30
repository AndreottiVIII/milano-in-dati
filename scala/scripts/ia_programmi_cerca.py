"""Internet Archive: cerca TUTTI i programmi di sala "Teatro alla Scala" 2002-2011 (aperti, con testo). 3 s tra richieste, cache in raw/ia_programmi/ricerche.
Uso (dalla cartella scala/): python -I -X utf8 scripts/ia_programmi_cerca.py"""
import sys, os, json, urllib.parse, time, urllib.request
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ia_cerca as ia
ROOT = ia.ROOT
OUT = os.path.join(ROOT, "raw", "ia_programmi", "ricerche"); os.makedirs(OUT, exist_ok=True)
ia.OUT = OUT
QS = {
 "tas_titolo": 'title:("teatro alla scala") AND mediatype:texts AND date:[2000-01-01 TO 2012-12-31]',
 "tas_stagione": 'title:("teatro alla scala") AND title:(stagione) AND mediatype:texts',
 "tas_qualsiasi": '(identifier:teatro-alla-scala*) AND mediatype:texts',
 "tas_filarmonica": 'title:("filarmonica della scala") AND mediatype:texts',
 "tas_direttore": 'title:("teatro alla scala") AND title:(direttore) AND mediatype:texts',
 "tas_di_stagione": 'title:("teatro alla scala") AND (title:(opera) OR title:(balletto) OR title:(concerto) OR title:(recital)) AND mediatype:texts',
}
tutti = {}
for k, q in QS.items():
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode({"q": q, "fl[]": ["identifier", "title", "creator", "year", "date", "mediatype", "access-restricted-item", "language", "downloads"], "rows": 500, "output": "json"}, doseq=True)
    d = ia.get(url, k + ".json")
    docs = d["response"]["docs"]
    print(k, d["response"]["numFound"], flush=True)
    for x in docs: tutti[x["identifier"]] = x
json.dump(tutti, open(os.path.join(ROOT, "raw", "ia_programmi", "tutti.json"), "w", encoding="utf8"), ensure_ascii=False)
print("unici", len(tutti))
