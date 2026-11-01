"""Passo 6 (dopo 05): per i primi N luoghi (per views totali, solo categorie "luogo"):
 (a) visualizzazioni GIORNALIERE in it e en (raw/pageviews_giornalieri/<lingua>/<qid>.json);
 (b) controllo redirect e rinominazioni su it.wikipedia: redirect che puntano al titolo attuale (MediaWiki API list=backlinks)
     e visualizzazioni mensili totali di quei redirect; spostamenti di pagina nel registro (list=logevents, letype=move)
     -> raw/redirect_it/<qid>.json
Rate: 3 richieste/s, pausa su 429. Riprendibile.
Uso: python -I -X utf8 06_giornalieri_redirect.py <luoghi-cercati assoluto> [N=40]"""
import sys, os, json, csv, time, urllib.parse
import requests

UA = "MilanoInDati/1.0 (https://github.com/AndreottiVIII/milano-in-dati)"
base = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 40
NONLUOGO = {"non_luogo", "altro", "senza_classe"}
S = requests.Session()
S.headers["User-Agent"] = UA
last = [0.0]


def get(url, params=None):
    for k in range(30):
        dt = time.time() - last[0]
        if dt < 0.33:
            time.sleep(0.33 - dt)
        last[0] = time.time()
        try:
            r = S.get(url, params=params, timeout=60)
        except Exception:
            time.sleep(5)
            continue
        if r.status_code in (200, 404):
            return r
        if r.status_code == 429:
            time.sleep(float(r.headers.get("retry-after", 15)) + 2)
        else:
            time.sleep(3 * (k + 1))
    raise SystemExit("richiesta fallita " + url)


tot = [r for r in csv.DictReader(open(os.path.join(base, "pulito", "totali_luogo.csv"), encoding="utf8"), delimiter=";")
       if r["tipo"] in ("luogo", "opera")][:N]
tit = {}
for r in csv.DictReader(open(os.path.join(base, "pulito", "titoli_wikipedia.csv"), encoding="utf8"), delimiter=";"):
    tit[(r["qid"], r["lingua"])] = r["titolo"]
END_D = "2026103100"
for r in tot:
    q = r["qid"]
    for lang in ("it", "en"):
        t = tit.get((q, lang))
        if not t:
            continue
        f = os.path.join(base, "raw", "pageviews_giornalieri", lang, q + ".json")
        if os.path.exists(f):
            continue
        os.makedirs(os.path.dirname(f), exist_ok=True)
        u = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/%s.wikipedia/all-access/user/%s/daily/2015070100/%s" % (
            lang, urllib.parse.quote(t, safe=""), END_D)
        resp = get(u)
        json.dump({"qid": q, "progetto": lang + ".wikipedia", "titolo": t, "http": resp.status_code, "scaricato": time.strftime("%Y-%m-%d"),
                   "items": resp.json().get("items", []) if resp.status_code == 200 else []},
                  open(f, "w", encoding="utf8"), ensure_ascii=False)
    # redirect it
    t = tit.get((q, "it"))
    f = os.path.join(base, "raw", "redirect_it", q + ".json")
    if t and not os.path.exists(f):
        os.makedirs(os.path.dirname(f), exist_ok=True)
        api = "https://it.wikipedia.org/w/api.php"
        red = get(api, {"action": "query", "list": "backlinks", "bltitle": t.replace("_", " "), "blfilterredir": "redirects",
                        "bllimit": "100", "blnamespace": "0", "format": "json"}).json().get("query", {}).get("backlinks", [])
        mv = get(api, {"action": "query", "list": "logevents", "letype": "move", "letitle": t.replace("_", " "),
                       "lelimit": "50", "format": "json"}).json().get("query", {}).get("logevents", [])
        mv2 = get(api, {"action": "query", "list": "logevents", "letype": "move", "lelimit": "50", "format": "json",
                        "leprop": "title|timestamp|details"}).json() if False else None
        out = {"qid": q, "titolo": t, "scaricato": time.strftime("%Y-%m-%d"), "redirect": [], "spostamenti": [
            {"titolo": e.get("title"), "verso": e.get("params", {}).get("target_title"), "data": e.get("timestamp")} for e in mv]}
        for b in red:
            rt = b["title"].replace(" ", "_")
            u = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/it.wikipedia/all-access/user/%s/monthly/2015070100/%s" % (
                urllib.parse.quote(rt, safe=""), END_D)
            resp = get(u)
            v = sum(i["views"] for i in resp.json().get("items", [])) if resp.status_code == 200 else 0
            out["redirect"].append({"titolo": rt, "views_totali": v})
        json.dump(out, open(f, "w", encoding="utf8"), ensure_ascii=False)
    print(q, r["nome"], flush=True)
print("fine")
