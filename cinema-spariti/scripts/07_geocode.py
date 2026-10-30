import sys, csv, json, os, time, re, requests
src, cache_fn = sys.argv[1], sys.argv[2]
UA = {"User-Agent": "MilanoInDati/1.0 (davide.caniatti@gmail.com; progetto dati aperti)"}
cache = json.load(open(cache_fn, encoding="utf-8")) if os.path.exists(cache_fn) else {}
rows = list(csv.DictReader(open(src, encoding="utf-8")))
def pulisci(a):
    a = a.split(" / ")[0]
    a = re.sub(r",? poi \d+.*", "", a)
    a = re.sub(r"^(.*?)\s*-\s*largo.*", r"\1", a)
    a = re.sub(r"/\s*v\..*", "", a)
    a = re.sub(r"\b(\d+)/(\d+)\b", r"\1", a)   # 15/17 -> 15 (primo civico)
    a = re.sub(r"(\d+)[a-z]\b", r"\1", a)
    return a.strip()
n = 0
for r in rows:
    q = pulisci(r["indirizzo_elenco"])
    if q in cache: continue
    for att in range(3):
        resp = requests.get("https://nominatim.openstreetmap.org/search", params={"q": q + ", Milano, Italia", "format": "jsonv2", "limit": 1, "addressdetails": 1, "viewbox": "9.04,45.58,9.32,45.37", "bounded": 1, "countrycodes": "it"}, headers=UA, timeout=60)
        if resp.status_code == 200: break
        time.sleep(15 * (att + 1))
    j = resp.json() if resp.status_code == 200 else []
    cache[q] = j[0] if j else None
    n += 1
    time.sleep(1.2)
    if n % 20 == 0:
        json.dump(cache, open(cache_fn, "w", encoding="utf-8"), ensure_ascii=False); print(n, flush=True)
json.dump(cache, open(cache_fn, "w", encoding="utf-8"), ensure_ascii=False)
print("fatto", n, "nuove query;", sum(1 for v in cache.values() if v is None), "senza risultato")
