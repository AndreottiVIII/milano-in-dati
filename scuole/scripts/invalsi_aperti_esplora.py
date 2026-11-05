"""Guarda i file aperti INVALSI: colonne e presenza di Milano e della gestione (statale, paritaria)."""
import csv, glob, os, sys
D = sys.argv[1]
for f in sorted(glob.glob(os.path.join(D, '*.csv'))):
    n = os.path.basename(f)
    if n.startswith('TRACCIATO') or n.startswith('_'):
        continue
    try:
        testo = open(f, encoding='utf-8-sig', errors='replace').read(60000000)
    except Exception as e:
        print(n, e)
        continue
    righe = testo.splitlines()
    sep = ';' if righe[0].count(';') > righe[0].count(',') else ','
    t = list(csv.reader(righe, delimiter=sep))
    h = t[0]
    mil = [r for r in t[1:] if any(c.strip().upper() == 'MILANO' for c in r)]
    gest = sorted({c for r in t[1:3000] for c in r if c.strip().lower() in ('statale', 'paritaria', 'non statale', 'statali', 'paritarie', 'non statali')})
    print(n, 'righe', len(t) - 1, 'Milano', len(mil), 'gestione', gest)
    print('  ', h[:16])
    if mil:
        print('  es', mil[0][:16])
