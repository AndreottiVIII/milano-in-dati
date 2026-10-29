# Aiuto per l'API MediaWiki in più lingue (it, en, de). Solo lettura.
import requests, time
UA = {"User-Agent": "milano-in-dati/1.0 (davide.caniatti@gmail.com; research)"}
def api(lang="it", **p):
    p["format"] = "json"; p.setdefault("formatversion", "2")
    url = f"https://{lang}.wikipedia.org/w/api.php"
    for i in range(5):
        try: r = requests.get(url, params=p, headers=UA, timeout=40)
        except Exception as e: print("EXC", e, flush=True); time.sleep(3); continue
        if r.status_code == 200: return r.json()
        time.sleep(4 * (i + 1))
    raise RuntimeError(r.status_code)
def members(cat, typ="page", lang="it"):
    out = []; cont = {}
    while True:
        d = api(lang, action="query", list="categorymembers", cmtitle=cat, cmtype=typ, cmlimit="500", **cont)
        out += [m["title"] for m in d["query"]["categorymembers"]]
        if "continue" in d: cont = d["continue"]
        else: return out
def search(q, lang="it", n=50):
    d = api(lang, action="query", list="search", srsearch=q, srlimit=str(n), srprop="snippet")
    return [(x["title"], x["snippet"]) for x in d["query"]["search"]]
def intro(titles, lang="it", full=False):
    out = {}
    for i in range(0, len(titles), 20):
        b = titles[i:i+20]
        kw = dict(action="query", titles="|".join(b), prop="extracts|info|pageprops|coordinates", exintro="1" if not full else None, explaintext="1", exlimit="max", redirects="1", inprop="url", ppprop="wikibase_item", colimit="max")
        kw = {k: v for k, v in kw.items() if v is not None}
        d = api(lang, **kw)
        for p in d["query"]["pages"]:
            out[p["title"]] = p
    return out
