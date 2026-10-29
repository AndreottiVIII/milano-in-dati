"""Scarica NOAA GSOD (Global Summary of the Day) per una stazione, anno per anno.
uso: python -I gsod_download.py STAZIONE ANNO_DA ANNO_A OUTDIR   (es. 16080099999 1985 2012 raw/gsod_linate)"""
import sys, os, requests
st, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
os.makedirs(out, exist_ok=True)
for y in range(a, b+1):
    u=f'https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/{y}/{st}.csv'
    r=requests.get(u, timeout=120)
    if r.status_code==200:
        open(f'{out}/{st}_{y}.csv','wb').write(r.content); print(y, len(r.content))
    else: print(y, 'HTTP', r.status_code)
