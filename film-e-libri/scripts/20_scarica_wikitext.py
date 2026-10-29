"""Scarica il wikitext degli articoli it/en delle opere (film, serie, libri, altro). Cache in raw/wikitext/.
Uso: python -I 20_scarica_wikitext.py <cartella_strand>"""
import sys, os, csv, json, time, requests
base = sys.argv[1]
out = os.path.join(base, "raw", "wikitext"); os.makedirs(out, exist_ok=True)
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)"}
titoli = {"it": set(), "en": set()}
for f in ("film", "serie_tv", "libri", "altro"):
    for r in csv.DictReader(open(os.path.join(base, "pulito", f + ".csv"), encoding="utf8")):
        if r["itwiki"]: titoli["it"].add(r["itwiki"])
        if r["enwiki"]: titoli["en"].add(r["enwiki"])
for lang, ts in titoli.items():
    ts = sorted(ts)
    for i in range(0, len(ts), 40):
        fn = os.path.join(out, f"{lang}_{i:05d}.json")
        if os.path.exists(fn): continue
        for t in range(5):
            try:
                r = requests.get(f"https://{lang}.wikipedia.org/w/api.php", params={
                    "action": "query", "format": "json", "prop": "revisions", "rvprop": "content|ids", "rvslots": "main",
                    "redirects": 1, "titles": "|".join(ts[i:i+40]), "formatversion": 2}, headers=UA, timeout=90)
                if r.status_code in (429, 500, 502, 503, 504): time.sleep(30*(t+1)); continue
                r.raise_for_status()
                d = r.json(); d["_richiesti"] = ts[i:i+40]
                json.dump(d, open(fn, "w", encoding="utf8"), ensure_ascii=False)
                print(lang, i, len(d["query"]["pages"]), flush=True); break
            except requests.RequestException as e:
                print("errore", e, flush=True); time.sleep(20*(t+1))
        time.sleep(2)
print("fine")
