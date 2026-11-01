"""Interroga l'indice CDX di web.archive.org (URL pubblici) per copie dei file di ds612/ds290/ds2858 e dei file Socrata.
Salva l'elenco in raw/wayback/cdx_*.txt. Uso: python -I -X utf8 wayback_cdx.py <raw assoluta>"""
import sys, os, time, urllib.request, urllib.parse
raw = sys.argv[1]; os.makedirs(raw + "/wayback", exist_ok=True)
pats = {
 "ds612_download": "dati.comune.milano.it/dataset/*/resource/*/download/ds612*",
 "ds612_download_old": "dati.comune.milano.it/dataset/ds612*/resource/*/download/*",
 "ds290_download": "dati.comune.milano.it/dataset/*/resource/*/download/ds290*",
 "ds2858_download": "dati.comune.milano.it/dataset/*/resource/*/download/*botteghe*",
 "ds612_ids": "dati.comune.milano.it/dataset/624e5fff-9e40-4adc-9b82-a5d06fa95a26/*",
 "socrata_g4x3": "dati.lombardia.it/api/views/g4x3-hs9b/*",
 "socrata_pccq": "dati.lombardia.it/api/views/pccq-vbbq/*",
 "socrata_czq5": "dati.lombardia.it/api/views/czq5-nkk7/*",
 "socrata_resource": "dati.lombardia.it/resource/g4x3-hs9b*",
 "socrata_resource2": "dati.lombardia.it/resource/pccq-vbbq*",
 "socrata_resource3": "dati.lombardia.it/resource/czq5-nkk7*",
 "socrata_d5uj": "dati.lombardia.it/api/views/d5uj-xwht/*",
}
for k, p in pats.items():
    url = "http://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode({"url": p, "output": "txt", "fl": "timestamp,original,mimetype,statuscode,digest,length", "limit": 400})
    for t in range(4):
        try:
            b = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "milano-in-dati/1.0"}), timeout=100).read()
            if b.startswith(b"<html"): raise RuntimeError("503/offline")
            open(f"{raw}/wayback/cdx_{k}.txt", "wb").write(b)
            print(k, len(b.splitlines()), "righe"); break
        except Exception as e:
            print(k, "tentativo", t, e); time.sleep(8)
    time.sleep(2)
