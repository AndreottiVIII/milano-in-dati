"""Cliente educato per SBN OPAC (opacmobilegw): 1 richiesta alla volta, >=3 s, cache su raw/sbn, backoff, STOP su blocchi."""
import json, os, time, hashlib, urllib.request, urllib.parse, urllib.error, sys
UA = "milano-in-dati research project (davide.caniatti@gmail.com; catalogo SBN, fatti bibliografici, 1 richiesta ogni 3 s)"
BASE = "https://opac.sbn.it/opacmobilegw/"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw", "sbn")
os.makedirs(ROOT, exist_ok=True)
_last = [0.0]
class Blocked(Exception): pass
def _path(kind, params):
    s = urllib.parse.urlencode(sorted(params.items()))
    h = hashlib.md5(s.encode()).hexdigest()[:10]
    label = "".join(c if c.isalnum() else "_" for c in "_".join(str(v) for k, v in sorted(params.items())))[:60]
    return os.path.join(ROOT, kind, f"{label}_{h}.json")
def get(kind, params):
    """kind = 'search' o 'full'. Restituisce (dati, dalla_cache)."""
    p = _path(kind, params)
    if os.path.exists(p):
        return json.load(open(p, encoding="utf8")), True
    os.makedirs(os.path.dirname(p), exist_ok=True)
    url = BASE + kind + ".json?" + urllib.parse.urlencode(params)
    for attempt in range(5):
        wait = 3 - (time.time() - _last[0])
        if wait > 0: time.sleep(wait)
        _last[0] = time.time()
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as f:
                raw = f.read()
            try:
                d = json.loads(raw.decode("utf8"))
            except Exception:
                txt = raw[:300].decode("utf8", "replace")
                if any(w in txt.lower() for w in ("captcha", "robot", "denied", "blocked", "<html")):
                    raise Blocked("risposta non JSON, possibile blocco: " + txt)
                raise
            json.dump(d, open(p, "w", encoding="utf8"), ensure_ascii=False)
            return d, False
        except urllib.error.HTTPError as e:
            if e.code in (403, 429, 503) and attempt >= 2:
                raise Blocked(f"HTTP {e.code} ripetuto su {url}")
            if e.code in (401, 403):
                raise Blocked(f"HTTP {e.code} su {url}")
            print("HTTP", e.code, "backoff", flush=True)
            time.sleep(30 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError) as e:
            print("errore rete", e, "backoff", flush=True)
            time.sleep(30 * (attempt + 1))
    raise RuntimeError("troppi errori su " + url)
