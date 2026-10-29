"""Scarica wikitesto (+ id revisione) di pagine Wikipedia sulla Scala via API MediaWiki (CC BY-SA). Uso: python -I wikipedia_scala.py <cartella_raw_wikipedia>"""
import sys, os, json, time, requests
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)"}
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
pages = ["Stagioni liriche del Teatro alla Scala", "Prime stagionali al Teatro alla Scala", "Stagioni di balletto del Teatro alla Scala", "Teatro alla Scala"]
for t in pages:
    p = os.path.join(out, t.replace(" ", "_") + ".json")
    if os.path.exists(p): continue
    r = requests.get("https://it.wikipedia.org/w/api.php", headers=UA, timeout=60, params={
        "action": "query", "prop": "revisions", "rvprop": "ids|timestamp|content", "rvslots": "main", "titles": t, "format": "json", "formatversion": 2})
    r.raise_for_status(); open(p, "w", encoding="utf8").write(r.text); print(t, len(r.text)); time.sleep(3)
