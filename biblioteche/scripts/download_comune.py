"""Scarica da dati.comune.milano.it i dataset sulle biblioteche (CKAN). 
Uso: python -I -X utf8 download_comune.py <biblioteche_abs> 
Legge raw/search_all.json, salva in raw/comune_<dsNNN>/ (file originali + _metadati.json con package_show), log in raw/download_log.csv.
Salta il JSON quando c'è il CSV (copia identica). Non riscarica file già presenti."""
import sys, os, re, json, time, csv, urllib.request, urllib.parse, datetime
base = sys.argv[1]
raw = os.path.join(base, "raw")
d = json.load(open(os.path.join(raw, "search_all.json"), encoding="utf-8"))
sel = [k for k, v in d.items() if re.search(r"bibliot|prestit|sormani|braidense", (k + v["title"]).lower()) and not k.startswith(("ds21", "ds51")) or k.startswith(("ds2493",))]
sel = sorted(set(k for k in d if re.search(r"biblio|prestit", k.lower())))
print(len(sel), "dataset")
logp = os.path.join(raw, "download_log.csv")
done = set()
rows = []
if os.path.exists(logp):
    rows = list(csv.reader(open(logp, encoding="utf-8")))
    done = {r[0] + "/" + r[2] for r in rows[1:] if r[4] == "ok"}
else:
    rows = [["dataset", "titolo", "file", "url", "stato", "byte", "scaricato_il", "licenza"]]
def get(url, retries=3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 milano-in-dati research"})
            return urllib.request.urlopen(req, timeout=180).read()
        except Exception as e:
            err = e; time.sleep(3)
    raise err
for k in sel:
    v = d[k]
    m = re.match(r"(ds\d+)", k)
    dsid = m.group(1)
    ddir = os.path.join(raw, "comune_" + dsid)
    os.makedirs(ddir, exist_ok=True)
    mp = os.path.join(ddir, "_metadati.json")
    if not os.path.exists(mp):
        pj = json.loads(get("https://dati.comune.milano.it/api/3/action/package_show?id=" + v["id"]))
        json.dump(pj["result"], open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    pj = json.load(open(mp, encoding="utf-8"))
    for r in pj["resources"]:
        fmt = (r.get("format") or "").upper()
        if fmt in ("JSON", "GEOJSON", "SHP") and any(x["format"].upper() in ("CSV",) for x in pj["resources"]):
            continue
        fn = urllib.parse.unquote(r["url"].rsplit("/", 1)[-1])
        key = dsid + "/" + fn
        if key in done: continue
        try:
            b = get(r["url"])
            open(os.path.join(ddir, fn), "wb").write(b)
            rows.append([dsid, v["title"], fn, r["url"], "ok", len(b), datetime.date.today().isoformat(), pj.get("license_id")])
        except Exception as e:
            rows.append([dsid, v["title"], fn, r["url"], "ERR " + str(e)[:80], 0, datetime.date.today().isoformat(), pj.get("license_id")])
        csv.writer(open(logp, "w", encoding="utf-8", newline="")).writerows(rows)
        time.sleep(0.3)
print("fine")
