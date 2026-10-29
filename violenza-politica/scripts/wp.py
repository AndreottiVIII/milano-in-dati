import requests, time
UA = {"User-Agent": "milano-in-dati/1.0 (davide.caniatti@gmail.com; research)"}
API = "https://it.wikipedia.org/w/api.php"
def api(**p):
    p["format"] = "json"; p.setdefault("formatversion", "2")
    for i in range(5):
        t0=time.time()
        try: r = requests.get(API, params=p, headers=UA, timeout=40)
        except Exception as e:
            print('EXC', e, flush=True); time.sleep(3); continue
        if time.time()-t0>8 or r.status_code!=200: print('slow/err', r.status_code, round(time.time()-t0,1), flush=True)
        if r.status_code == 200: return r.json()
        time.sleep(5*(i+1))
    raise RuntimeError(r.status_code)
def members(cat, typ):
    out = []; cont = {}
    while True:
        d = api(action="query", list="categorymembers", cmtitle=cat, cmtype=typ, cmlimit="500", **cont)
        out += [m["title"] for m in d["query"]["categorymembers"]]
        if "continue" in d: cont = d["continue"]
        else: return out
