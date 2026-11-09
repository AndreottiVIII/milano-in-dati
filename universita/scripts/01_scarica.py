"""Scarica gli archivi interi in universita/dati_grezzi/ (Comune di Milano DS752 e MUR iscritti).
Uso: python -I -X utf8 universita/scripts/01_scarica.py
MUR: robots.txt chiede 10 secondi tra una richiesta e l'altra (e vieta /api/): si scarica solo /download/."""
import os, time, urllib.request
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(R, 'dati_grezzi')
os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'milano-in-dati/1.0'}
B = 'https://dati.comune.milano.it/dataset/b0d96b3a-b1d3-4583-8a4d-d33571903c99/resource/'
COMUNE = {
 'comune_2017-18.csv': '089e741f-131f-4660-95f8-dade36d89ece/download/ds752_iscritti_anno_accademico_2017-18.csv',
 'comune_2018-19.csv': 'cd5c2ee7-eaab-4f01-8b8b-aaf2a818fa86/download/ds752_iscritti_anno_accademico_2018-19_no_dupl.csv',
 'comune_2019-20.csv': '5d382842-eb99-42a9-990b-cde2a3ae1c74/download/ds752_iscritti_anno_accademico_2019-20_no_dupl.csv',
 'comune_2020-21.csv': 'ee1ef286-4d60-4c75-83a7-bc3d51f6da7d/download/ds752_iscritti_anno_accademico_2020-21.csv',
 'comune_2021-22.csv': 'e043f6d5-a1ba-44dc-8657-5c68b73efbbf/download/ds752_iscriti_anno_accademico_2021-22.csv',
 'comune_2022-23.csv': '12fca3b5-85d2-4ce3-aaaf-b785944a9a00/download/ds752_iscritti_anno_accademico_2022-23.csv',
 'comune_2023-24.csv': 'd2b50a8e-2c63-47c3-b150-0747f34faad8/download/ds752_iscritti_anno_accademico_2023-24.csv',
 'comune_2024-25.csv': '288a03b7-2bf9-42db-9e3d-81250f152ff4/download/ds752_iscritti_anno_accademico_2024-25.csv',
}
M = 'https://dati-ustat.mur.gov.it/dataset/3dd9ca7f-9cc9-4a1a-915c-e569b181dbd5/resource/'
MUR = {
 'mur_01_iscritti_per_anno.csv': 'e76fcb62-22c5-4ff9-a425-e06f3d6f8330/download/01_iscrittixanno.csv',
 'mur_02_iscritti_per_ateneo.csv': '32d26e28-a0b5-45f3-9152-6072164f3e63/download/02_iscrittixateneo.csv',
 'mur_10_internazionali_per_ateneo.csv': '27ba8d3b-9a54-4a75-8798-2010bc7c205a/download/10_iscrittiinternazionalixateneo.csv',
 'mur_14c_in_sede_fuori_sede.csv': '349e58d7-6ea6-4b99-99cb-b8748fccbaf6/download/14c_iscrittixsedescuolasecondariasedecorso.csv',
 'mur_18_ateneo_e_gruppo.csv': '2020e61d-40d1-4465-bd67-aa748d5b7c76/download/18_iscrittixgruppoateneo.csv',
 'mur_14a_residenza_sede_gruppo.csv': 'b270ef1a-c219-48b1-8399-b1458e225d39/download/14a_iscrittixresidenzasedecorsogruppo.csv',
}
def get(nome, url, pausa):
    p = os.path.join(OUT, nome)
    if os.path.exists(p): return
    d = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()
    open(p, 'wb').write(d); print(nome, len(d)); time.sleep(pausa)
for n, u in COMUNE.items(): get(n, B + u, 1)
for n, u in MUR.items(): get(n, M + u, 11)
