"""Copia in occupazione/dati_grezzi/ i file già scaricati (nessun nuovo scaricamento) che servono alla pagina «Il lavoro che c'è».
Uso: python -I -X utf8 occupazione/scripts/01_prepara.py
Origine: _esplorazione/aree/lavoro/ (scaricati il 10/11/2026 con _esplorazione/aree/scripts/: User-Agent «milano-in-dati/1.0», senza login).
Il file ISTAT dei settori è grande (24 MB): qui si tengono solo le righe della Città metropolitana di Milano (ITC45) e dell'Italia (IT), ultima edizione (2025M12)."""
import csv, glob, os, shutil
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
A = os.path.join(R, '_esplorazione', 'aree', 'lavoro')
G = os.path.join(R, 'occupazione', 'dati_grezzi')
os.makedirs(G, exist_ok=True)
COPIE = [
    ('ds109*/*.csv', 'comune_ds109_condizione_lavorativa_15piu.csv'),
    ('ds114*/*.csv', 'comune_ds114_confronti_territoriali.csv'),
    ('ds113*/*.csv', 'comune_ds113_giovani_15_24.csv'),
    ('ds112*/*.csv', 'comune_ds112_indicatori_15_64.csv'),
    ('ds1497*/*.csv', 'comune_ds1497_occupazione_serie.csv'),
    ('ds1498*/*.csv', 'comune_ds1498_disoccupazione_serie.csv'),
    ('lombardia_p9wf-dh6p/rows.csv', 'lombardia_p9wf_durata_per_tipo.csv'),
    ('lombardia_x54h-y9u7/rows.csv', 'lombardia_x54h_durata_eta_sesso.csv'),
    ('istat_DF_DCSS_LCAS_FRISC_1.csv', 'istat_lavoro_da_casa.csv'),
]
for pat, dest in COPIE:
    src = glob.glob(os.path.join(A, pat))[0]
    shutil.copyfile(src, os.path.join(G, dest))
    print(dest, os.path.getsize(os.path.join(G, dest)))
src = os.path.join(A, 'istat_93_379_DF_DCCN_OCCTSEC2010_2.csv')
n = 0
with open(src, encoding='utf-8', newline='') as f, open(os.path.join(G, 'istat_settori_milano_italia.csv'), 'w', encoding='utf-8', newline='') as o:
    r = csv.reader(f); w = csv.writer(o)
    h = next(r); w.writerow(h)
    ia, ie, iv = h.index('REF_AREA'), h.index('EDITION'), h.index('EMPLOYMENT_STATUS')
    for row in r:
        if row[ia] in ('ITC45', 'IT') and row[ie] == '2025M12' and row[iv] == '9':
            w.writerow(row); n += 1
print('istat_settori_milano_italia.csv', n, 'righe')
