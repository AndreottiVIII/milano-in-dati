"""Internet Archive: cerca annuari/libri/riviste sulla Scala (advancedsearch + metadata API, niente login). 3 s tra richieste, cache in raw/ia_scala.
Uso: python -I -X utf8 scripts/ia_cerca.py"""
import sys, os, json, time, urllib.request, urllib.parse, hashlib, csv
sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = os.path.join(ROOT, "raw", "ia_scala", "ricerche"); os.makedirs(OUT, exist_ok=True)
UA = "milano-in-dati research project (davide.caniatti@gmail.com; ricerca bibliografica, 1 richiesta ogni 3 s)"
last = [0.0]
def get(url, nome):
    p = os.path.join(OUT, nome)
    if os.path.exists(p): return json.load(open(p, encoding="utf8"))
    w = 3 - (time.time() - last[0])
    if w > 0: time.sleep(w)
    last[0] = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as f: d = json.loads(f.read().decode("utf8"))
    json.dump(d, open(p, "w", encoding="utf8"), ensure_ascii=False)
    return d
QS = {
 "scala_titolo": 'title:("teatro alla scala" OR "la scala" OR "scala di milano") AND (mediatype:texts)',
 "annuario": '(title:annuario OR title:"stagione") AND (title:"scala")',
 "rivista_la_scala": 'title:("la scala" rivista) OR (title:"la scala" AND subject:opera)',
 "musica_doggi": 'title:"musica d\'oggi"',
 "tintori": 'creator:tintori AND (scala OR cronologia)',
 "duecento": 'title:("duecento anni" OR "200 anni" OR "due secoli") AND scala',
 "cronologia": 'title:cronologia AND (scala OR milano)',
 "scala_testo": 'scala AND milano AND (stagione OR opere OR cartellone OR cronologia) AND mediatype:texts',
 "programma_di_sala": '"programma di sala" AND scala',
 "gatti": 'creator:gatti AND scala',
 "cambiasi": 'creator:cambiasi',
 "libretti": 'title:("teatro alla scala") AND subject:(libretto OR libretti)',
}
righe = {}
for k, q in QS.items():
    url = "https://archive.org/advancedsearch.php?" + urllib.parse.urlencode({"q": q, "fl[]": ["identifier", "title", "creator", "year", "date", "mediatype", "access-restricted-item", "language", "downloads"], "rows": 100, "output": "json"}, doseq=True)
    try:
        d = get(url, k + ".json")
    except Exception as e:
        print(k, "ERR", e); continue
    docs = d["response"]["docs"]
    print(f"{k}: {d['response']['numFound']} risultati", flush=True)
    for x in docs:
        righe.setdefault(x["identifier"], dict(x, trovato_con=[]))["trovato_con"].append(k)
json.dump(righe, open(os.path.join(ROOT, "raw", "ia_scala", "tutti.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("unici", len(righe))
