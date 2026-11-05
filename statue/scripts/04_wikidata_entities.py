"""Scarica da Wikidata (wbgetentities, CC0) le entita' necessarie, a giri, con cache.
Giro 1: gli elementi trovati dalle query SPARQL (A, B) + i QID 'wikidata' / 'subject:wikidata' dei tag OSM.
Giro 2: tutto cio' che i giri precedenti citano (P180 raffigura, P547 commemora, P921 soggetto, P138 intitolato a, P170 creatore, P31, P131, P106, P27, P135/P149 movimento/stile).
Uso: python -I -X utf8 04_wikidata_entities.py <raw/wikidata> <raw/osm/overpass_statue.json>"""
import sys, os, json, time, re, requests
W, OSM = sys.argv[1:3]
UA = {"User-Agent": "milano-in-dati/0.3 (milano-in-dati; research on statues and monuments in Milan)"}
cache_fn = os.path.join(W, "entities_cache.json")
cache = json.load(open(cache_fn, encoding="utf8")) if os.path.exists(cache_fn) else {}
def qid(u): return u.rsplit("/", 1)[-1]
def get(ids):
    for a in range(8):
        r = requests.get("https://www.wikidata.org/w/api.php", params=dict(action="wbgetentities", ids="|".join(ids), props="labels|descriptions|claims", languages="it|en", format="json"), headers=UA, timeout=90)
        j = r.json() if r.status_code == 200 else {}
        if "entities" in j: return j["entities"]
        time.sleep(min(90, 5 * 2 ** a))
    raise SystemExit("fallito " + str(ids[:3]))
def fetch(qs):
    qs = sorted({q for q in qs if re.fullmatch(r"Q\d+", q)} - set(cache), key=lambda x: int(x[1:]))
    print("da scaricare", len(qs), flush=True)
    for i in range(0, len(qs), 50):
        for q, e in get(qs[i:i + 50]).items():
            cache[q] = e
        time.sleep(1)
    json.dump(cache, open(cache_fn, "w", encoding="utf8"), ensure_ascii=False)
def refs(e):
    out = set()
    for p in ["P180", "P547", "P921", "P138", "P170", "P31", "P131", "P106", "P27", "P135", "P149", "P279", "P361", "P915", "P84", "P1435", "P276", "P7084", "P411"]:
        for c in e.get("claims", {}).get(p, []):
            v = c.get("mainsnak", {}).get("datavalue", {}).get("value")
            if isinstance(v, dict) and "id" in v: out.add(v["id"])
    return out
base = set()
for n in ["A_p131", "B_box"]:
    for r in json.load(open(os.path.join(W, n + ".json"), encoding="utf8"))["results"]["bindings"]:
        base.add(qid(r["item"]["value"]))
for e in json.load(open(OSM, encoding="utf8"))["elements"]:
    for k in ["wikidata", "subject:wikidata", "artist:wikidata", "memorial:subject:wikidata", "commemorates:wikidata", "buried:wikidata"]:
        for v in e["tags"].get(k, "").split(";"):
            if re.fullmatch(r"Q\d+", v.strip()): base.add(v.strip())
print("giro 1:", len(base))
fetch(base)
r2 = set()
for q in base:
    if q in cache: r2 |= refs(cache[q])
print("giro 2:", len(r2))
fetch(r2)
# giro 3: occupazioni e cittadinanze delle persone raffigurate (solo etichette servono, ma prendiamo comunque)
r3 = set()
for q in r2:
    if q in cache: r3 |= refs(cache[q])
print("giro 3:", len(r3))
fetch(r3)
print("entita' in cache:", len(cache))
