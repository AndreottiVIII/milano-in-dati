"""Download RSSSF Italian championship season pages (resumable, polite). Usage: python -I 06_download_rsssf.py <raw/rsssf>"""
import sys, os, time, requests
d = sys.argv[1]
UA = {"User-Agent": "MilanoInDati/1.0 (research; davide.caniatti@gmail.com)"}
names = ["ital%02d" % y for y in range(26, 100)] + ["ital%02d" % y for y in range(0, 10)] + ["ital%d" % y for y in range(2010, 2027)] + ["ital-sic45", "ital-sicily20", "italhist98-25", "ital24", "ital25"]
for n in names:
    dest = f"{d}/{n}.html"
    if os.path.exists(dest) and os.path.getsize(dest) > 500: continue
    for k in range(4):
        r = requests.get(f"https://www.rsssf.org/tablesi/{n}.html", headers=UA, timeout=60)
        if r.status_code == 200:
            open(dest, "wb").write(r.content); print("ok", n, len(r.content)); break
        if r.status_code in (429, 503): time.sleep(30 * (k + 1)); continue
        print("skip", r.status_code, n); break
    time.sleep(2)
print("DONE")
