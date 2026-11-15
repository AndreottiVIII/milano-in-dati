"""Scarica da Open Data Lombardia l'elenco delle RSA (export completo) e i metadati del dataset.
Rispetta robots.txt (Crawl-delay 1). Uso: python -I -X utf8 anz_01_scarica.py <cartella progetto>"""
import sys, os, time, urllib.request
R = sys.argv[1]
raw = os.path.join(R, 'anziani', 'raw'); os.makedirs(raw, exist_ok=True)
UA = {'User-Agent': 'milano-in-dati/1.0'}
URL = {
  'rsa.csv': 'https://hub.dati.lombardia.it/api/views/jyyh-hybn/rows.csv?accessType=DOWNLOAD',
  'rsa_meta.json': 'https://hub.dati.lombardia.it/api/views/jyyh-hybn.json',
  'adi.csv': 'https://dati.comune.milano.it/dataset/507044d0-1cf4-4e44-aa71-aacc25164d7d/resource/bd828e95-9fa1-47eb-9cdb-300f66b70b3d/download/ds618_assistenza_domiciliare_i_bkdm-d8re_final.csv',
}
for nome, u in URL.items():
    d = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()
    open(os.path.join(raw, nome), 'wb').write(d); print(nome, len(d)); time.sleep(2)
