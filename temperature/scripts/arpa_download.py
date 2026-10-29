"""Scarica da dati.lombardia.it (Socrata) le righe di un sensore da un dataset, a pagine.
uso: python -I arpa_download.py DATASET_ID IDSENSORE OUTFILE"""
import sys, requests, time
ds, sens, out = sys.argv[1:4]
url=f'https://www.dati.lombardia.it/resource/{ds}.csv'
n=0; off=0; page=50000
with open(out,'w',encoding='utf-8',newline='') as f:
    first=True
    while True:
        for t in range(5):
            try:
                r=requests.get(url, params={'$where':f"idsensore='{sens}'",'$order':'data','$limit':page,'$offset':off}, timeout=180); r.raise_for_status(); break
            except Exception as e:
                print('retry',e); time.sleep(5)
        lines=r.text.splitlines()
        if len(lines)<=1: break
        f.write('\n'.join(lines if first else lines[1:])+'\n'); first=False
        n+=len(lines)-1; off+=page; print(ds,'righe',n,flush=True)
        if len(lines)-1<page: break
print('FINE',ds,n)
