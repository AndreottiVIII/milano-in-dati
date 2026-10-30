"""Scarica in blocco i file ISD (annuali, per stazione) e GSOD (annuali) per Linate, Malpensa (e Milano/Linate 160810).
Riprendibile: salta i file gia' presenti. Uso: python -I scarica_isd_gsod.py <cartella_raw>"""
import sys, os, time, requests
raw = sys.argv[1]
UA = {"User-Agent": "milano-in-dati research (davide.caniatti@gmail.com)"}
stazioni = {"160800-99999": (1931, 2025), "160660-99999": (1965, 2025), "160810-99999": (2005, 2018)}
s = requests.Session(); s.headers.update(UA)
def get(url, dest):
    if os.path.exists(dest): return "gia"
    for t in range(4):
        try:
            r = s.get(url, timeout=60)
            if r.status_code == 404: return "404"
            if r.status_code == 429: time.sleep(30*(t+1)); continue
            r.raise_for_status()
            open(dest, "wb").write(r.content); return "ok %d" % len(r.content)
        except Exception as e:
            time.sleep(5*(t+1)); err = str(e)
    return "ERR " + err
log = open(os.path.join(raw, "log_download.txt"), "a")
for st, (a, b) in stazioni.items():
    for kind, base, ext, sub in (("isd", "https://www.ncei.noaa.gov/pub/data/noaa/%d/%s-%d.gz", ".gz", "isd"),):
        d = os.path.join(raw, sub, st); os.makedirs(d, exist_ok=True)
        for y in range(a, b+1):
            res = get(base % (y, st, y), os.path.join(d, "%s-%d.gz" % (st, y)))
            log.write("%s %s %d %s\n" % (kind, st, y, res)); log.flush()
            if res.startswith("ok"): time.sleep(0.7)
            if res == "404":
                try: os.remove(os.path.join(d, "%s-%d.gz" % (st, y)))
                except: pass
    sid = st.replace("-", "")
    d = os.path.join(raw, "gsod", sid); os.makedirs(d, exist_ok=True)
    for y in range(a, b+1):
        res = get("https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/%d/%s.csv" % (y, sid), os.path.join(d, "%s_%d.csv" % (sid, y)))
        log.write("gsod %s %d %s\n" % (sid, y, res)); log.flush()
        if res.startswith("ok"): time.sleep(0.7)
log.write("FINE\n"); log.close()
