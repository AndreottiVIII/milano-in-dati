"""Cliente Wikidata SPARQL educato: cache su disco, pause, backoff."""
import os, json, time, hashlib, requests
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)", "Accept": "application/sparql-results+json"}
_last = [0.0]
def sparql(name, query, outdir, tries=5):
    p = os.path.join(outdir, name + ".json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf8"))["results"]["bindings"]
    for t in range(tries):
        w = 6 - (time.time() - _last[0])
        if w > 0: time.sleep(w)
        _last[0] = time.time()
        try:
            r = requests.post("https://query.wikidata.org/sparql", data={"query": query, "format": "json"}, headers=UA, timeout=170)
        except requests.RequestException as e:
            print(name, "errore rete", e, flush=True); time.sleep(30*(t+1)); continue
        if r.status_code in (429, 500, 502, 503, 504):
            print(name, "HTTP", r.status_code, "backoff", flush=True); time.sleep(40*(t+1)); continue
        r.raise_for_status()
        open(p, "w", encoding="utf8").write(r.text)
        b = r.json()["results"]["bindings"]
        print(name, len(b), "righe", flush=True)
        return b
    print(name, "FALLITA", flush=True)
    return None
