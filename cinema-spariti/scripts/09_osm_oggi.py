import sys, csv, json, math, time, requests
base = sys.argv[1]
UA = {"User-Agent": "MilanoInDati/1.0 (davide.caniatti@gmail.com; progetto dati aperti)"}
rows = [r for r in csv.DictReader(open(f"{base}/pulito/cinema.csv", encoding="utf-8-sig")) if r["id"].startswith("SC") and r["lat"] and r["precisione_posizione"].startswith("civico")]
SKIP = {"bench", "parking", "waste_basket", "bicycle_parking", "parking_entrance", "parking_space", "recycling", "post_box", "vending_machine", "atm", "drinking_water", "bicycle_rental", "car_sharing", "charging_station", "motorcycle_parking", "waste_disposal", "shelter", "toilets", "telephone", "clock", "fountain", "cinema"}
def hav(a, b, c, d):
    p = math.pi / 180; x = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2; return 12742000 * math.asin(math.sqrt(x))
res = {}; raw = []
for i in range(0, len(rows), 40):
    chunk = rows[i:i + 40]
    q = "[out:json][timeout:120];(" + "".join(f'nwr(around:30,{r["lat"]},{r["lon"]})[~"^(shop|amenity|office|leisure|tourism|craft|healthcare)$"~"."];' for r in chunk) + ");out center tags;"
    for att in range(4):
        resp = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, headers=UA, timeout=180)
        print(i, resp.status_code, len(resp.content), flush=True)
        if resp.status_code == 200: break
        time.sleep(30 * (att + 1))
    els = resp.json()["elements"]; raw += els
    for r in chunk:
        found = []
        for e in els:
            t = e["tags"]; la = e.get("lat") or e.get("center", {}).get("lat"); lo = e.get("lon") or e.get("center", {}).get("lon")
            if la is None: continue
            d = hav(float(r["lat"]), float(r["lon"]), la, lo)
            if d > 30: continue
            kind = next((f"{k}={t[k]}" for k in ("shop", "amenity", "office", "leisure", "tourism", "craft", "healthcare") if k in t), "")
            if kind.split("=")[1] in SKIP: continue
            found.append((d, f'{t.get("name", "(senza nome)")} [{kind}]'))
        found.sort(); res[r["id"]] = [f for _, f in found]
    time.sleep(10)
json.dump(res, open(f"{base}/raw/osm/oggi_vicino.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(raw, open(f"{base}/raw/osm/oggi_vicino_grezzo.json", "w", encoding="utf-8"), ensure_ascii=False)
print(len(rows), "cinema interrogati;", sum(1 for v in res.values() if v), "con almeno un candidato")
