"""Confronta il 2026 di Brera con le stazioni vicine: medie mensili dei soli valori :00 (come in RAPPORTO.md).
uso: python -I verifica_2026.py RAW_ARPA RAW_ARPA_ALTRE RAW_ARPA_ALTRE_2026 OUTDIR
Scrive OUTDIR/verifica_2026_mensili.csv, verifica_2026_estate.csv, verifica_2026_anomalie.csv"""
import sys, os, glob, pandas as pd
ra, rb, rc, od = sys.argv[1:5]
NOMI = {'5897': 'Brera', '5909': 'Juvara', '5911': 'Marche', '5920': 'Zavattari', '2001': 'Lambrate'}
fr = {}
for d in (ra, rb, rc):
    for p in glob.glob(os.path.join(d, '*.csv')):
        b = os.path.basename(p)
        if b.startswith('nf78'): continue
        s = b.split('_')[1] if b.startswith('sens_') else b.split('_')[1]   # brera_5897_x / sens_5909_x
        if s not in NOMI: continue
        df = pd.read_csv(p, usecols=['data', 'valore', 'stato'], dtype=str)
        df = df[df.stato == 'VA']
        t = pd.to_datetime(df.data, errors='coerce')
        v = pd.to_numeric(df.valore, errors='coerce')
        m = (t.dt.minute == 0) & v.between(-30, 50)
        fr.setdefault(s, []).append(pd.DataFrame({'t': t[m], 'v': v[m]}))
S = {}
for s, l in fr.items():
    x = pd.concat(l).drop_duplicates('t').set_index('t').v.sort_index()
    S[NOMI[s]] = x
    print(NOMI[s], x.index.min(), x.index.max(), len(x))
# solo mesi con copertura >= 80% delle ore, e solo ore in cui TUTTE le stazioni hanno il dato (confronto alla pari)
H = pd.DataFrame(S)
H = H[H.index.year >= 2019]
H = H[[c for c in H.columns if H[c].index[H[c].notna()].year.max() >= 2026 and (H[c].index[H[c].notna()].year <= 2025).any()]]   # solo stazioni con dati 2019-2026
print('stazioni usate', list(H.columns))
com = H.dropna()                                  # ore comuni a tutte
print('ore comuni', len(com), 'su', len(H))
M = com.groupby([com.index.year.rename('anno'), com.index.month.rename('mese')]).agg(['mean', 'count'])
n = com.groupby([com.index.year, com.index.month]).size()
mm = com.groupby([com.index.year.rename('anno'), com.index.month.rename('mese')]).mean()
mm['ore'] = n.values
mm = mm[mm.ore >= 0.8 * mm.index.map(lambda im: pd.Period(f'{im[0]}-{im[1]:02d}').days_in_month * 24)]
mm.round(2).to_csv(os.path.join(od, 'verifica_2026_mensili.csv'))
# anomalie: 2026 e 2022 meno media 2019-2025 dello stesso mese (stesse stazioni)
st = [c for c in mm.columns if c != 'ore']
base = mm[(mm.index.get_level_values(0) >= 2019) & (mm.index.get_level_values(0) <= 2025)][st].groupby(level=1).mean()
mesi26 = mm.loc[2026].index
r = []
for y in (2022, 2026):
    d = mm.loc[y][st].reindex(mesi26) - base.reindex(mesi26)
    d.index = [f'{y}-{m:02d}' for m in d.index]
    r.append(d)
A = pd.concat(r)
A.round(2).to_csv(os.path.join(od, 'verifica_2026_anomalie.csv'))
print(mm.round(2).to_string()); print(A.round(2).to_string())
# estate (giu-ago) per anno: media delle tre medie mensili, solo se i tre mesi sono completi (>=80% delle ore)
rows = {}
for y in sorted(set(mm.index.get_level_values(0))):
    if all((y, m) in mm.index for m in (6, 7, 8)):
        rows[y] = mm.loc[[(y, 6), (y, 7), (y, 8)], st].mean()
E_ = pd.DataFrame(rows).T
vic = [c for c in st if c != 'Brera']
E_['media_vicine'] = E_[vic].mean(axis=1)
E_['Brera_meno_vicine'] = E_.Brera - E_.media_vicine
E_.round(2).to_csv(os.path.join(od, 'verifica_2026_estate.csv')); print(E_.round(2).to_string())
# 2026 meno 2022 e meno media 2019-2025, per stazione (estate) e per mese
print('estate 2026-2022', (E_.loc[2026] - E_.loc[2022]).round(2).to_dict())
b = E_.loc[[y for y in E_.index if y <= 2025]].mean()
print('estate 2026-media2019-25', (E_.loc[2026] - b).round(2).to_dict())
A['media_vicine'] = A[vic].mean(axis=1)
A['Brera_meno_vicine'] = A.Brera - A.media_vicine
A.round(2).to_csv(os.path.join(od, 'verifica_2026_anomalie.csv'))
print(A.round(2).to_string())
print('media mesi 2026 Brera_meno_vicine', A.loc[[i for i in A.index if i.startswith('2026')], 'Brera_meno_vicine'].mean().round(2),
      '2022', A.loc[[i for i in A.index if i.startswith('2022')], 'Brera_meno_vicine'].mean().round(2))
# stessi mesi di tutti gli anni: Brera meno media vicine, media annua
mm['vic'] = mm[vic].mean(axis=1); mm['d'] = mm.Brera - mm.vic
print(mm[mm.index.get_level_values(1).isin(mesi26)].groupby(level=0).d.mean().round(2).to_string())
