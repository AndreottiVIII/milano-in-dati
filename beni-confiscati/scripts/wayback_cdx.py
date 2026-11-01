# Cerca nella Wayback Machine le risorse dati di confiscatibene.it (sito spento). Uso: python -I -X utf8 wayback_cdx.py <cartella_output_assoluta>
import sys, time, urllib.request, urllib.parse, json, os
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
queries = ["confiscatibene.it/dataset/*", "confiscatibene.it/sites/default/files/*", "confiscatibene.it/*.csv"]
for i, q in enumerate(queries):
    url = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode({"url": q, "output": "json", "fl": "timestamp,original,mimetype,statuscode", "filter": "statuscode:200", "collapse": "urlkey", "limit": "800"})
    for t in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "milano-in-dati-research/1.0"})
            data = urllib.request.urlopen(req, timeout=120).read()
            open(os.path.join(out, f"cdx_{i}.json"), "wb").write(data)
            print(q, "ok", len(data)); break
        except Exception as e:
            print(q, "tentativo", t, e); time.sleep(30)
