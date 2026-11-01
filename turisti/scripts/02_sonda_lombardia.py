"""Sonda i dataset Socrata di dati.lombardia.it: metadati e 3 righe. Pausa 2 s.
uso: python -I -X utf8 02_sonda_lombardia.py <cartella raw/lombardia_meta assoluta> id1 id2 ..."""
import sys, json, time, os, urllib.request
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "milano-in-dati research (turisti fase 1)"}
def get(u):
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as f:
            return f.read().decode("utf-8")
    except Exception as e:
        return "ERRORE " + str(e)
for i in sys.argv[2:]:
    m = get(f"https://dati.lombardia.it/api/views/{i}.json")
    open(os.path.join(out, i + ".json"), "w", encoding="utf-8").write(m)
    if m.startswith("ERRORE"): print(i, m); continue
    j = json.loads(m)
    print("==", i, j.get("name"), "| attr:", j.get("attribution"), "| licenza:", j.get("license"), j.get("licenseId"))
    print("  ", (j.get("description") or "")[:300].replace("\n", " "))
    print("   campi:", [c["fieldName"] for c in j.get("columns", [])])
    s = get(f"https://dati.lombardia.it/resource/{i}.json?$limit=2")
    print("   righe:", s[:400])
    time.sleep(2)
