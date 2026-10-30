"""Internet Archive, secondo giro: programmi/riviste/annuari 1945-2025 e metadati degli elementi utili (stesse regole di ia_cerca.py)."""
import sys, os, json, re, time, urllib.parse
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ia_cerca as ia   # esegue le ricerche del primo giro (in cache) e riusa get()
QS = {
 "ts_titolo_dopo1945": 'title:("teatro alla scala") AND mediatype:texts AND year:[1945 TO 2026]',
 "ts_stagione": 'title:("teatro alla scala" AND stagione) AND mediatype:texts',
 "scala_rivista": '(title:"la scala" OR title:"rivista mensile") AND (subject:musica OR subject:opera OR description:rivista) AND mediatype:texts',
 "scala_collection": 'collection:(teatroallascala) OR creator:"teatro alla scala"',
 "musica_oggi": 'title:("musica d\'oggi" OR "musica doggi") OR title:"rassegna musicale"',
 "tintori_giampiero": 'creator:"tintori, giampiero" OR title:"quattro secoli di" OR title:"duecento anni di storia"',
 "la_scala_programma": 'title:"programma" AND title:"scala" AND mediatype:texts',
 "annuario_scala": 'title:("annuario" AND "scala") OR title:"almanacco" AND title:"scala"',
 "scala_1950": 'subject:"Teatro alla Scala" AND mediatype:texts',
 "scala_stagione_ts": 'title:"scala" AND (title:"stagione lirica" OR title:"stagione d\'opera" OR title:"stagione 19")',
}
nuovi = {}
for k, q in QS.items():
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode({"q": q, "fl[]": ["identifier", "title", "creator", "year", "mediatype", "access-restricted-item", "downloads"], "rows": 100, "output": "json"}, doseq=True)
    try: d = ia.get(url, k + ".json")
    except Exception as e: print(k, "ERR", e); continue
    print(f"{k}: {d['response']['numFound']}", flush=True)
    for x in d["response"]["docs"]: nuovi.setdefault(x["identifier"], dict(x, trovato_con=[]))["trovato_con"].append(k)
json.dump(nuovi, open(os.path.join(ia.ROOT, "raw", "ia_scala", "tutti2.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
