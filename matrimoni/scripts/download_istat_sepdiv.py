"""Scarica le tavole ISTAT 'Separazioni e divorzi' (serie storiche 2007-2024 + distretto 2011/2012) da demo.istat.it in raw/istat_sepdiv.
Uso: python -I -X utf8 download_istat_sepdiv.py <raw_dir>"""
import sys, os, urllib.request, urllib.parse, datetime, hashlib, time
raw = os.path.join(sys.argv[1], "istat_sepdiv"); os.makedirs(raw, exist_ok=True)
base = "https://demo.istat.it/data/sepdiv/"
files = [("seriestoriche/" + n) for n in ["tavola 1.1.xls","tavola 1.2.xlsx","tavola 1.3.xlsx","tavola 1.4.xls","tavola 1.5.xlsx","tavola 2.1.xls","tavola 2.2.xls","tavola 2.3.xlsx","tavola 2.4.xls","tavola 2.5.xlsx"]]
files += ["2012/Tav1_1.xls","2012/Tav2_1.xls","2011/Tav1_1.xls","2011/Tav2_1.xls"]
log = open(os.path.join(sys.argv[1], "download_log.csv"), "a", encoding="utf-8")
for f in files:
    dst = os.path.join(raw, f.replace("/", "__").replace(" ", "_"))
    url = base + urllib.parse.quote(f)
    if not os.path.exists(dst):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        open(dst, "wb").write(urllib.request.urlopen(req, timeout=90).read()); time.sleep(1)
    h = hashlib.sha256(open(dst, "rb").read()).hexdigest()[:16]
    log.write(f"{datetime.date.today()};istat_sepdiv;xls;{url};{os.path.getsize(dst)};{h};;CC-BY 4.0 (note legali Istat)\n"); log.flush()
    print(f, os.path.getsize(dst))
