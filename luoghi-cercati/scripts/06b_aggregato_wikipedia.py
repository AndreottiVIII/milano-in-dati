"""Passo 6b: totale mensile di TUTTE le visualizzazioni (agent=user, all-access) di ciascuna Wikipedia principale, come
riferimento per separare l'andamento dei luoghi di Milano da quello generale di Wikipedia.
Endpoint /metrics/pageviews/aggregate/<progetto>/all-access/user/monthly/2015070100/2026103100 -> raw/aggregato_wikipedia/<lingua>.json
Uso: python -I -X utf8 06b_aggregato_wikipedia.py <luoghi-cercati assoluto>"""
import sys, os, json, time
import requests

UA = "MilanoInDati/1.0 (https://github.com/AndreottiVIII/milano-in-dati)"
base = sys.argv[1]
d = os.path.join(base, "raw", "aggregato_wikipedia")
os.makedirs(d, exist_ok=True)
for lang in ["it", "en", "de", "fr", "es", "zh", "ja", "ru", "pt", "ar"]:
    f = os.path.join(d, lang + ".json")
    if os.path.exists(f):
        continue
    u = "https://wikimedia.org/api/rest_v1/metrics/pageviews/aggregate/%s.wikipedia/all-access/user/monthly/2015070100/2026103100" % lang
    for k in range(20):
        r = requests.get(u, headers={"User-Agent": UA}, timeout=60)
        if r.status_code == 200:
            json.dump({"progetto": lang + ".wikipedia", "scaricato": time.strftime("%Y-%m-%d"), "items": r.json()["items"]},
                      open(f, "w", encoding="utf8"))
            break
        time.sleep(float(r.headers.get("retry-after", 15)) + 2 if r.status_code == 429 else 5)
    time.sleep(1)
    print(lang, flush=True)
