"""Categorie it.wikipedia (API MediaWiki): pagine, profondita 2. Uso: python -I wp_categorie.py <raw/wikipedia>"""
import sys, os, json, time, requests
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)"}
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
API = "https://it.wikipedia.org/w/api.php"
ROOTS = ["Film ambientati a Milano", "Film girati a Milano", "Romanzi ambientati a Milano", "Opere letterarie ambientate a Milano", "Opere ambientate a Milano", "Serie televisive ambientate a Milano", "Opere teatrali ambientate a Milano"]
def api(params):
    for t in range(5):
        time.sleep(1.2)
        r = requests.get(API, params={**params, "format": "json"}, headers=UA, timeout=60)
        if r.status_code in (429, 503): time.sleep(30*(t+1)); continue
        r.raise_for_status(); return r.json()
    raise RuntimeError("api")
def members(cat):
    res = []; cont = {}
    while True:
        d = api({"action": "query", "list": "categorymembers", "cmtitle": "Categoria:" + cat, "cmlimit": 500, "cmprop": "title|type|ids", **cont})
        if "error" in d: return None
        res += d["query"]["categorymembers"]
        if "continue" in d: cont = d["continue"]
        else: return res
p = os.path.join(out, "categorie.json")
if os.path.exists(p): print("gia fatto"); sys.exit()
result = {}  # root -> {cat: {pages:[], subcats:[]}}
for root in ROOTS:
    tree = {}; frontier = [(root, 0)]; seen = {root}
    while frontier:
        c, depth = frontier.pop(0)
        m = members(c)
        if m is None: tree[c] = {"errore": "non esiste", "depth": depth}; print(root, "->", c, "NON ESISTE"); continue
        pages = [x for x in m if x["type"] == "page"]
        subs = [x["title"].split(":", 1)[1] for x in m if x["type"] == "subcat"]
        tree[c] = {"depth": depth, "pages": [{"title": x["title"], "pageid": x["pageid"]} for x in pages], "subcats": subs}
        print(root, "|", c, "d", depth, "pagine", len(pages), "sub", len(subs), flush=True)
        if depth < 2:
            for s in subs:
                if s not in seen: seen.add(s); frontier.append((s, depth + 1))
    result[root] = tree
json.dump(result, open(p, "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("FINE")
