"""Esegue in ordine tutta la pipeline dei prezzi OMI, con i file di Davide in omi_da_davide\\quotazioni\\.
Uso: python -I esegui_pipeline.py <cartella prezzi-case>
Passi: 03 indice ISTAT -> 04 NTN -> 05 corrispondenza zone -> 06 lettura OMI -> 07 prezzi.
Si ferma con un messaggio chiaro se mancano i file di Davide. Non scarica nulla.
"""
import os, sys, subprocess, glob

base = os.path.abspath(sys.argv[1])
S = os.path.join(base, 'scripts')
pulito = os.path.join(base, 'pulito')
quot = os.path.join(base, 'omi_da_davide', 'quotazioni')


def run(*args):
    cmd = [sys.executable, '-I', '-W', 'ignore'] + list(args)
    print('\n$', ' '.join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        raise SystemExit(f'ERRORE nel passo {args[0]}')


files = [f for f in glob.glob(os.path.join(quot, '**', '*'), recursive=True) if os.path.isfile(f)]
if not files:
    raise SystemExit(f'Nella cartella {quot} non ci sono file: prima vanno scaricati (vedi COSA_SCARICARE.md).')
run(os.path.join(S, '03_istat_foi.py'), os.path.join(base, 'raw', 'istat'), pulito)
run(os.path.join(S, '04_ntn_milano.py'), os.path.join(base, 'raw'), pulito)
run(os.path.join(S, '05_zone_corrispondenza.py'), os.path.join(base, 'raw', 'geopoi'), pulito, 'F205')
run(os.path.join(S, '06_leggi_omi.py'), quot, pulito)
run(os.path.join(S, '07_prezzi.py'), pulito)
print('\nFatto. Leggere pulito\\omi_controlli.txt prima di fidarsi dei numeri.')
