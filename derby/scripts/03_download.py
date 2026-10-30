"""Download football-data (via footballcsv cache, CC0) + football-data.co.uk (last seasons) + openfootball/italy. Resumable.
Usage: python -I 03_download.py <raw_dir>"""
import sys, os, time, requests
raw = sys.argv[1]
UA = {"User-Agent": "MilanoInDati/1.0 (research; davide.caniatti@gmail.com)"}
def get(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    for k in range(4):
        r = requests.get(url, headers=UA, timeout=60)
        if r.status_code == 200:
            open(dest, "wb").write(r.content); print("ok", url, len(r.content)); break
        if r.status_code in (429, 503): time.sleep(20 * (k + 1)); continue
        print("skip", r.status_code, url); break
    time.sleep(1.0)
# football-data cache
for y in range(1993, 2024):
    s = "%d-%02d" % (y, (y + 1) % 100)
    get(f"https://raw.githubusercontent.com/footballcsv/cache.footballdata/master/{s}/it.1.csv", f"{raw}/footballdata/cache_{s}_it.1.csv")
for code in ("2425", "2526", "2627"):
    get(f"https://www.football-data.co.uk/mmz4281/{code}/I1.csv", f"{raw}/footballdata/fd_{code}_I1.csv")
# openfootball
import json
for y in range(2013, 2027):
    s = "%d-%02d" % (y, (y + 1) % 100)
    r = requests.get(f"https://api.github.com/repos/openfootball/italy/contents/{s}", headers=UA, timeout=60)
    time.sleep(1)
    if r.status_code != 200: print("no", s); continue
    for f in r.json():
        if f["name"].endswith(".txt"):
            get(f["download_url"], f"{raw}/openfootball/{s}_{f['name']}")
