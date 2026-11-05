"""Scarica i dataset del Comune di Milano sugli esercizi pubblici. Uso: python -I -X utf8 download_comune.py <raw_dir>"""
import sys, os, json, urllib.request, time, hashlib, csv
raw = sys.argv[1]
DS = ["ds58_economia_pubblici_esercizi_in_piano","ds59-economia-pubblici-esercizi-fuori-piano","ds250-economia-artigianato-settore-alimentare","ds251-economia-panificatori","ds252-economia-locali-pubblico-spettacolo","ds202-aperture-chiusure-attivita-2018","ds2954-attivita-commerciali-serie-storica","ds612_elenco_attivita_storiche_e_di_tradizione_nel_comune_di_milano"]
log = []
for n in DS:
    p = json.load(urllib.request.urlopen("https://dati.comune.milano.it/api/3/action/package_show?id=" + n, timeout=60))["result"]
    short = n.split("_")[0].split("-")[0]
    d = os.path.join(raw, "comune_" + short); os.makedirs(d, exist_ok=True)
    json.dump(p, open(os.path.join(d, "_metadati.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in p["resources"]:
        if r["format"] not in ("CSV", "GeoJSON"): continue
        fn = r["url"].rsplit("/", 1)[1]
        path = os.path.join(d, fn)
        if not os.path.exists(path):
            data = urllib.request.urlopen(urllib.request.Request(r["url"], headers={"User-Agent": "milano-in-dati research"}), timeout=180).read()
            open(path, "wb").write(data); time.sleep(1)
        b = open(path, "rb").read()
        log.append([n, r["format"], fn, len(b), hashlib.sha256(b).hexdigest()[:16], r.get("last_modified"), time.strftime("%Y-%m-%d")])
        print(log[-1])
csv.writer(open(os.path.join(raw, "download_log.csv"), "w", newline="", encoding="utf-8")).writerows([["dataset","formato","file","byte","sha256_16","last_modified_ckan","scaricato"]] + log)
