"""Download the archived (web.archive.org, snapshot Feb 2017) interfc.it 'Almanacco nerazzurro' match pages linked from it.wikipedia's derby table.
Resumable, polite (3 s). Usage: python -I 11_download_interfc.py <derby_dir>"""
import sys, csv, re, os, time, requests
base = sys.argv[1]
UA = {"User-Agent": "MilanoInDati/1.0 (research; davide.caniatti@gmail.com)"}
rows = list(csv.DictReader(open(base + "/pulito/derby.csv", encoding="utf-8")))
for x in rows:
    u = x["report_url"]
    if "interfc.it/Tabellino.asp" not in u: continue
    dest = f"{base}/raw/interfc_archive/{x['match_id']}.html"
    if os.path.exists(dest) and os.path.getsize(dest) > 2000: continue
    for k in range(4):
        try:
            r = requests.get(u, headers=UA, timeout=60)
        except Exception as e:
            print("err", x["match_id"], e); time.sleep(20); continue
        if r.status_code == 200:
            open(dest, "wb").write(r.content); print("ok", x["match_id"], len(r.content), flush=True); break
        if r.status_code in (429, 503, 502): time.sleep(30 * (k + 1)); continue
        print("skip", r.status_code, x["match_id"], flush=True); break
    time.sleep(3)
print("DONE", flush=True)
