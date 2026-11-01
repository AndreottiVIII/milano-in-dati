"""Scarica da dati.comune.milano.it (CKAN) i dataset NIC, inflazione, redditi comunali, consumi. 
Uso: python -I -X utf8 scarica_comune.py <costo-vita assoluto>
Solo risorse CSV; metadati in _metadati.json; log in raw/download_log.csv. Pausa 1 s."""
import sys, os, re, json, urllib.request, urllib.parse, time, datetime, hashlib
base = sys.argv[1]
H = {"User-Agent": "Mozilla/5.0 (ricerca open data; davide.caniatti@gmail.com)"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=120).read()
# 1) elenco pacchetti: dalla ricerca gia' fatta + ricerca "irpef"
pk = json.load(open(os.path.join(base, "raw", "comune_search_all.json"), encoding="utf-8"))["pacchetti"]
for q in ["irpef", "redditi comunale", "spesa media mensile"]:
    start = 0
    while True:
        d = json.loads(get("https://dati.comune.milano.it/api/3/action/package_search?rows=100&start=%d&q=%s" % (start, urllib.parse.quote(q))))["result"]
        for p in d["results"]: pk[p["name"]] = p
        start += 100
        if start >= d["count"]: break
        time.sleep(1)
want = []
for n, p in pk.items():
    t = p["title"]
    num = int(re.match(r"ds(\d+)", n).group(1)) if re.match(r"ds(\d+)", n) else -1
    if re.search(r"indice NIC", t) and not re.search(r"Prezzi al consumo (gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre) 20", t):
        want.append(n)
    elif num in (1499, 1821, 120, 310, 531, 109, 110) or re.search(r"Redditi e (principali )?variabili Irpef su base comunale", t):
        want.append(n)
want = sorted(set(want))
print(len(want), "pacchetti")
log = open(os.path.join(base, "raw", "download_log.csv"), "a", encoding="utf-8")
for n in want:
    p = pk[n]
    sid = re.match(r"(ds\d+)", n).group(1)
    folder = os.path.join(base, "raw", "comune", sid); os.makedirs(folder, exist_ok=True)
    full = json.loads(get("https://dati.comune.milano.it/api/3/action/package_show?id=" + n))["result"]
    json.dump(full, open(os.path.join(folder, "_metadati.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for r in full["resources"]:
        if r["format"].upper() != "CSV": continue
        fn = r["url"].rsplit("/", 1)[-1]
        dst = os.path.join(folder, fn)
        if not os.path.exists(dst):
            data = get(r["url"]); open(dst, "wb").write(data); time.sleep(1)
        data = open(dst, "rb").read()
        log.write("%s;200;%s;%d;%s;%s;%s;%s\n" % (datetime.date.today(), r["url"], len(data), hashlib.sha256(data).hexdigest()[:16], dst, full.get("license_id"), r.get("last_modified"))); log.flush()
        print(sid, fn, len(data))
