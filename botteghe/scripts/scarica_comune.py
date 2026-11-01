"""Scarica da dati.comune.milano.it (CKAN) i dataset indicati: metadati, risorse e attività.
Uso: python -I -X utf8 scarica_comune.py <cartella raw assoluta>"""
import sys, json, urllib.request, os, csv, datetime, hashlib
raw = sys.argv[1]
nomi = ["ds290-economia-botteghe-storiche-2017", "ds2858-economia-botteghe-storiche-2024", "ds612_elenco_attivita_storiche_e_di_tradizione_nel_comune_di_milano", "ds588_imprese_artigiane_certificate_artis_nel_comune_di_milano"]
H = {"User-Agent": "milano-in-dati/1.0"}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=180).read()
log = []
for n in nomi:
    d = f"{raw}/comune/{n.split('-')[0].split('_')[0]}"
    os.makedirs(d, exist_ok=True)
    pk = json.loads(get(f"https://dati.comune.milano.it/api/3/action/package_show?id={n}"))["result"]
    json.dump(pk, open(d + "/_metadati.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
    try:
        act = json.loads(get(f"https://dati.comune.milano.it/api/3/action/package_activity_list?id={pk['id']}&limit=200"))["result"]
        json.dump(act, open(d + "/_activity.json", "w", encoding="utf8"), ensure_ascii=False)
    except Exception as e:
        print("activity ERR", e)
    print(n, pk["title"], "| mod", pk["metadata_modified"][:10], "|", pk["license_id"], "| freq", pk.get("frequency"))
    for r in pk["resources"]:
        fn = r["url"].rsplit("/", 1)[-1]
        if r["format"].upper() not in ("CSV", "GEOJSON", "JSON", "ZIP", "XLSX", "XLS"): 
            print("  salto", r["format"], fn); continue
        if r["format"].upper()=="JSON": continue
        b = get(r["url"])
        open(f"{d}/{fn}", "wb").write(b)
        log.append((n, fn, r["format"], r.get("last_modified"), len(b), hashlib.sha256(b).hexdigest()[:16], datetime.date.today().isoformat()))
        print("  ", fn, r["format"], len(b), r.get("last_modified"))
with open(raw + "/comune/download_log.csv", "w", newline="", encoding="utf8") as f:
    w = csv.writer(f); w.writerow(["dataset", "file", "formato", "last_modified_ckan", "byte", "sha256_16", "scaricato"]); w.writerows(log)
