"""Raccoglie i link delle sezioni utili e chiede a Wikipedia (GeoData) + Wikidata (P625) le coordinate di ogni pagina collegata.
Cache in raw/wikitext/link_*.json e raw/wikitext/_link_coordinate.json.  Uso: python -I 22_link_coordinate.py <strand>"""
import sys, os, re, json, time, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_wikitext import *
base = sys.argv[1]
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)"}
art = carica_articoli(base)
targets = {"it": set(), "en": set()}
for (lang, rich), (tit, w) in art.items():
    ered = {1: None}
    for liv, titolo, testo in sezioni(w):
        kind = classifica_sezione(titolo, ered.get(liv-1) if liv > 2 else None)
        ered[liv] = kind
        if not kind: continue
        for piano, spans in paragrafi(pulisci(testo)):
            for s, e, t in spans:
                if ":" in t.split(" ")[0] and t.split(":")[0].lower() in ("wikipedia", "file", "categoria", "category", "template"): continue
                targets[lang].add(t[:1].upper() + t[1:])
print({k: len(v) for k, v in targets.items()}, flush=True)
res_fn = os.path.join(base, "raw", "wikitext", "_link_coordinate.json")
res = json.load(open(res_fn, encoding="utf8")) if os.path.exists(res_fn) else {}
for lang, ts in targets.items():
    ts = sorted(t for t in ts if f"{lang}:{t}" not in res)
    for i in range(0, len(ts), 50):
        batch = ts[i:i+50]
        for tr in range(5):
            try:
                r = requests.get(f"https://{lang}.wikipedia.org/w/api.php", params={
                    "action": "query", "format": "json", "formatversion": 2, "prop": "coordinates|pageprops", "ppprop": "wikibase_item",
                    "coprimary": "primary", "colimit": "max", "redirects": 1, "titles": "|".join(batch)}, headers=UA, timeout=60)
                if r.status_code in (429, 500, 502, 503, 504): time.sleep(20*(tr+1)); continue
                r.raise_for_status(); d = r.json()["query"]; break
            except requests.RequestException as e:
                print("errore", e, flush=True); time.sleep(15*(tr+1)); d = None
        if d is None: continue
        norm_ = {n["from"]: n["to"] for n in d.get("normalized", [])}
        red = {x["from"]: x["to"] for x in d.get("redirects", [])}
        pag = {p["title"]: p for p in d["pages"]}
        for t in batch:
            tt = norm_.get(t, t); tt = red.get(tt, tt)
            p = pag.get(tt)
            if not p or p.get("missing"): res[f"{lang}:{t}"] = None; continue
            c = p.get("coordinates", [{}])[0] if p.get("coordinates") else {}
            res[f"{lang}:{t}"] = {"titolo": tt, "lat": c.get("lat"), "lon": c.get("lon"), "qid": p.get("pageprops", {}).get("wikibase_item", "")}
        if (i // 50) % 20 == 0:
            json.dump(res, open(res_fn, "w", encoding="utf8"), ensure_ascii=False); print(lang, i, len(ts), flush=True)
        time.sleep(1)
json.dump(res, open(res_fn, "w", encoding="utf8"), ensure_ascii=False)
print("fine", len(res), "con coordinate:", sum(1 for v in res.values() if v and v["lat"]), "con qid senza coordinate:", sum(1 for v in res.values() if v and not v["lat"] and v["qid"]))
