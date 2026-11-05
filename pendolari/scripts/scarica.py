"""Scarica i file grezzi del filone "Pendolari" in raw/ (salta quelli gia' presenti) e scrive raw/download_log.csv.

Uso: python -I -X utf8 scarica.py <cartella pendolari, percorso assoluto>
Poi decomprimere (nomi delle cartelle attesi dagli altri programmi):
  istat_1991/x, istat_2001/x, istat_2011/x, istat_2021/x_LAVORO, istat_2021/x_STUDIO, istat_codici/x (Limiti2021_g.zip),
  lombardia_od2016/x (matrice_od_2016_passeggeri.zip; il csv pesa 2,8 GB). Lombardia.zip delle distanze si legge direttamente dallo zip.
Solo file pubblici, nessuna registrazione, nessun accesso protetto. Licenze: ISTAT CC BY 4.0; Regione Lombardia CC0.
File non fidati: restano in raw/, non si eseguono mai.
"""
import sys, csv, time, urllib.request
from pathlib import Path

P = Path(sys.argv[1])
RAW = P / 'raw'
UA = {'User-Agent': 'milano-in-dati/1.0'}
FILES = [
    ('istat_1991/matrici_pendolarismo_1991.zip', 'http://www.istat.it/storage/cartografia/matrici_pendolarismo/matrici_pendolarismo_1991.zip'),
    ('istat_2001/matrici_pendolarismo_2001.zip', 'http://www.istat.it/storage/cartografia/matrici_pendolarismo/matrici_pendolarismo_2001.zip'),
    ('istat_2011/matrici_pendolarismo_2011.zip', 'http://www.istat.it/storage/cartografia/matrici_pendolarismo/matrici_pendolarismo_2011.zip'),
    ('istat_2021/matrix_pendoLAVORO_2021.zip', 'https://esploradati.istat.it/databrowser/DWL/PERMPOP/MATPEN/matrix_pendoLAVORO_2021.zip'),
    ('istat_2021/matrix_pendoSTUDIO_2021.zip', 'https://esploradati.istat.it/databrowser/DWL/PERMPOP/MATPEN/matrix_pendoSTUDIO_2021.zip'),
    ('istat_2021/leggimi_pendoLAVORO_2021.doc', 'https://esploradati.istat.it/databrowser/DWL/PERMPOP/MATPEN/leggimi_file_matrix_pendoLAVORO_2021.doc'),
    ('istat_2021/leggimi_pendoSTUDIO_2021.doc', 'https://esploradati.istat.it/databrowser/DWL/PERMPOP/MATPEN/leggimi_file_matrix_pendoSTUDIO_2021.doc'),
    ('istat_2021/nota_lavoro.pdf', 'https://www.istat.it/wp-content/uploads/2025/10/Nota-metodologica-Pendolarismo-per-lavoro-2021_1.pdf'),
    ('istat_2021/nota_studio.pdf', 'https://www.istat.it/wp-content/uploads/2026/09/Nota-metodologica-Pendolarismo-per-studio-2021-.pdf'),
    ('istat_distanze/Lombardia.zip', 'https://www.istat.it/storage/cartografia/matrici_distanze/Lombardia.zip'),
    ('istat_distanze/nota-tecnica-matrici-distanze-maggio2023.pdf', 'https://www.istat.it/wp-content/uploads/2015/04/nota-tecnica-matrici-distanze-maggio2023.pdf'),
    ('istat_codici/Limiti2021_g.zip', 'https://www.istat.it/storage/cartografia/confini_amministrativi/generalizzati/Limiti2021_g.zip'),
    ('istat_codici/Elenco-comuni-italiani.xlsx', 'https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.xlsx'),
    ('lombardia_od2016/matrice_od_2016_passeggeri.zip', 'https://dati.lombardia.it/api/views/64n7-bhkf/files/d096c86f-dc58-466d-ab10-2814709e6e13?download=true&filename=matrice_od_2016_passeggeri.zip'),
    ('lombardia_od2016/nota_metodologica.pdf', 'https://dati.lombardia.it/api/views/tezw-ewgk/files/1587b018-1407-4a03-a8b3-0a91561b102d?download=true&filename=nota_metodologica.pdf'),
    ('lombardia_od2016/descrizione_campi.pdf', 'https://dati.lombardia.it/api/views/tezw-ewgk/files/bd747487-d932-4634-be8f-53a79a3f9bd9?download=true&filename=descrizione_campi.pdf'),
]
log = []
for rel, url in FILES:
    dest = RAW / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        log.append((rel, url, dest.stat().st_size, 'gia presente'))
        continue
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=600) as r, open(dest, 'wb') as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    log.append((rel, url, dest.stat().st_size, time.strftime('%Y-%m-%d')))
    print('scaricato', rel, dest.stat().st_size)
    time.sleep(2)
with open(RAW / 'download_log.csv', 'w', newline='', encoding='utf8') as f:
    w = csv.writer(f)
    w.writerow(['file', 'url', 'byte', 'data_o_nota'])
    w.writerows(log)
