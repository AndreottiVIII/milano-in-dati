"""Confronta le tre release ISTAT (5/8/2025, 31/3/2026, 25/8/2026): quanto cambiano i dati provvisori.
Uso: python -I -X utf8 revisioni.py <cartella pulito assoluta>"""
import sys, os
import pandas as pd
P = sys.argv[1]
files = {'2025-08-05': 'rev_20250805_decessi.csv', '2026-03-31': 'rev_20260331_decessi.csv', '2026-08-25': 'decessi_giorno_eta_sesso.csv'}
D = {}
for r, f in files.items():
    x = pd.read_csv(os.path.join(P, f), parse_dates=['data'])
    D[r] = x
rows = []
for scope in ('Milano', 'Lombardia', 'Italia'):
    # per anno (anni completi in tutte le release disponibili)
    for r, x in D.items():
        x = x[x.scope == scope]
        by = x.groupby(x.data.dt.year)['T'].sum()
        for y, v in by.items():
            rows.append(dict(scope=scope, release=r, periodo=str(y), morti=int(v)))
        # mesi 2025
        m = x[x.data.dt.year == 2025].groupby(x.data.dt.month)['T'].sum()
        for mm, v in m.items():
            rows.append(dict(scope=scope, release=r, periodo=f'2025-{mm:02d}', morti=int(v)))
        m = x[x.data.dt.year == 2026].groupby(x.data.dt.month)['T'].sum()
        for mm, v in m.items():
            rows.append(dict(scope=scope, release=r, periodo=f'2026-{mm:02d}', morti=int(v)))
Rv = pd.DataFrame(rows).pivot_table(index=['scope', 'periodo'], columns='release', values='morti').reset_index()
Rv['var_ago25_a_ago26_pct'] = 100 * (Rv['2026-08-25'] / Rv['2025-08-05'] - 1)
Rv['var_mar26_a_ago26_pct'] = 100 * (Rv['2026-08-25'] / Rv['2026-03-31'] - 1)
Rv.round(2).to_csv(os.path.join(P, 'revisioni_release.csv'), index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 300)
print(Rv.round(2).to_string())
