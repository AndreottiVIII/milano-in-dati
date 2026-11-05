"""Scarica (se mancano) i file ISTAT del Bes dei territori in raw/ e scrive raw/download_log.csv (url, file, byte, sha256).
Non fa login, non aggira nulla: sono link pubblici dalle pagine ISTAT (vedi NOTE.md, punto 2).
Uso: python -I -X utf8 scarica.py <benessere assoluto>"""
import sys, csv, hashlib, pathlib, datetime, urllib.request

base = pathlib.Path(sys.argv[1]); raw = base / 'raw'
U = 'https://www.istat.it/wp-content/uploads/'
FILES = [  # (cartella, url)
    ('ed2025', U + '2025/06/Bes_dei_territori_edizione_2025.zip'),
    ('ed2025', U + '2025/06/Quadro-di-corrispondenza-Bes_BesT_2025.pdf'),
    ('ed2024', U + '2024/07/Bes_dei_territori_edizione_2024_18122024_IT_EC.zip'),
    ('ed2023', U + '2023/06/Bes-territori-2023.zip'),
    ('ed2022', U + '2022/10/Bes_dei_territori_edizione_03102022.zip'),
    ('ed2022', U + '2022/10/NOTA-STAMPA-_BES_TERRITORI_2022.pdf'),
    ('ed2021', U + '2024/02/Bes_dei_territori_edizione_2021.zip'),
    ('ed2020', U + '2024/02/Bes_dei_territori_edizione_102020.zip'),
    ('ed2019', U + '2019/05/tavole-bes-2018.zip'),
    ('ed2019', U + '2019/05/Glossario-1.pdf'),
    ('ed2019', U + '2019/05/Nota-metodologica.pdf'),
    ('ed2018', U + '2018/06/Tavole.zip'),
    ('ed2018', U + '2018/06/MBT_Glossario.pdf'),
    ('ed2018', U + '2018/06/Nota-metodologica.pdf'),
    ('ed2018', U + '2018/06/Indice-delle-tavole-statistiche.pdf'),
    ('extra', U + '2026/02/Ballabio_BesT_VA_0326.pdf'),
    ('report_cm2024', U + '2024/11/BesT_CM_2024_VSP.pdf'),
    ('report_cm2024', U + '2024/11/Appendice_citta_metropolitane_VSP.xlsx'),
    ('report_cm2024', U + '2024/11/Notastampa-BesTcitta-metropolitane.pdf'),
]
righe = []
for d, url in FILES:
    p = raw / d / url.rsplit('/', 1)[1]
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        req = urllib.request.Request(url, headers={'User-Agent': 'milano-in-dati/1.0'})
        with urllib.request.urlopen(req, timeout=300) as r:
            p.write_bytes(r.read())
    b = p.read_bytes()
    righe.append(dict(cartella=d, file=p.name, url=url, byte=len(b), sha256=hashlib.sha256(b).hexdigest(),
                      verificato_il=datetime.date.today().isoformat()))
with open(raw / 'download_log.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=list(righe[0])); w.writeheader(); w.writerows(righe)
print(len(righe), 'file in raw/')
