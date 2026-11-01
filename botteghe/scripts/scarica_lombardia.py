"""Scarica da dati.lombardia.it (Socrata) metadati e righe CSV dei dataset indicati.
Uso: python -I -X utf8 scarica_lombardia.py <cartella raw assoluta>"""
import sys, json, urllib.request, os, csv, datetime
raw = sys.argv[1]
ids = ["d5uj-xwht", "czq5-nkk7", "g4x3-hs9b", "pccq-vbbq", "x5us-52q8", "d62u-rncn", "t635-fygy", "xguy-ssff", "vp3x-pmp8", "z47y-7rbf", "iiqz-ri2e"]
log = []
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/1.0"}), timeout=120).read()
for i in ids:
    d = raw + "/lombardia/" + i
    os.makedirs(d, exist_ok=True)
    try:
        meta = get(f"https://www.dati.lombardia.it/api/views/{i}.json")
        open(d + "/_metadati.json", "wb").write(meta)
        m = json.loads(meta)
        print(i, m.get("name"), "| licenza:", m.get("license", {}).get("name") if isinstance(m.get("license"), dict) else m.get("licenseId"), "| righe:", m.get("columns", [{}])[0].get("cachedContents", {}).get("non_null"), "| rowsUpdatedAt:", datetime.datetime.utcfromtimestamp(m.get("rowsUpdatedAt", 0)).isoformat() if m.get("rowsUpdatedAt") else None, "| viewLastModified:", m.get("viewLastModified"))
        data = get(f"https://www.dati.lombardia.it/api/views/{i}/rows.csv?accessType=DOWNLOAD")
        open(d + f"/{i}.csv", "wb").write(data)
        log.append((i, m.get("name"), len(data), "ok"))
    except Exception as e:
        print(i, "ERR", e)
        log.append((i, "", 0, str(e)))
with open(raw + "/lombardia/download_log.csv", "w", newline="", encoding="utf8") as f:
    w = csv.writer(f); w.writerow(["id", "nome", "byte", "esito"]); w.writerows(log)
