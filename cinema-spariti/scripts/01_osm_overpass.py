import sys, os, time, json, requests
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "MilanoInDati/1.0 (davide.caniatti@gmail.com; progetto dati aperti)"}
AREA = 'area["name"="Milano"]["boundary"="administrative"]["admin_level"="8"]->.a;'
queries = {
 "cinema_attuali_e_storici": AREA + '''
(
 nwr(area.a)["amenity"="cinema"];
 nwr(area.a)["building"="cinema"];
 nwr(area.a)["historic"="cinema"];
 nwr(area.a)["theatre:genre"~"cinema"];
 nwr(area.a)[~"^(disused|was|abandoned|removed|demolished|razed|former|old|historic|ruins|destroyed|lifecycle)(:.*)?$"~"^cinema$"];
 nwr(area.a)["old_name"~"[Cc]ine"];
 nwr(area.a)["name"~"[Cc]inema|[Cc]inematograf|[Cc]ine[ -]?[Tt]eatro|Odeon|Excelsior|Cinecittà"]["shop"]; 
 nwr(area.a)["name"~"[Cc]inema|[Cc]inematograf"]["disused"];
 nwr(area.a)["cinema:3d"];
 nwr(area.a)["screen"]["amenity"];
);
out center tags;''',
 "teatri": AREA + '''
(
 nwr(area.a)["amenity"="theatre"];
 nwr(area.a)["building"="theatre"];
);
out center tags;''',
}
for name, q in queries.items():
    fn = os.path.join(out, name + ".json")
    if os.path.exists(fn) and os.path.getsize(fn) > 100:
        print("skip", fn); continue
    for att in range(5):
        r = requests.post("https://overpass-api.de/api/interpreter", data={"data": "[out:json][timeout:180];" + q}, headers=UA, timeout=240)
        print(name, r.status_code, len(r.content))
        if r.status_code == 200:
            open(fn, "wb").write(r.content); break
        time.sleep(30 * (att + 1))
    time.sleep(10)
