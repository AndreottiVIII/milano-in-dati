r"""Fase 1 - recensioni Inside Airbnb come indicatore indiretto della crescita nel tempo.
Uso: python -I -X utf8 03_recensioni.py <cartella affitti-brevi (assoluta)>
Legge solo id, listing_id e date (NON legge reviewer_name, comments). Scrive in pulito\ :
 recensioni_per_annuncio.csv  (unione dei 4 snapshot: listing_id, prima/ultima recensione, n recensioni, in_ultimo_snapshot)
 recensioni_anno.csv          (anno: ultimo snapshot e UNIONE dei 4 snapshot, + conteggi di ogni snapshot)
 recensioni_mese.csv          (mese, recensioni: ultimo snapshot e unione)
 recensioni_nil_anno.csv      (nil_id, nil_nome, anno, recensioni, annunci_con_recensione) con UNIONE e NIL piu' recente noto
Perche' l'unione: le recensioni di un annuncio sparito dal sito spariscono dal file; unendo gli snapshot si
recupera in parte quanto e' sparito tra dicembre 2025 e settembre 2026 (ma non quanto sparito prima).
"""
import sys
from pathlib import Path
import pandas as pd

base = Path(sys.argv[1])
SNAP = ['2025-12-26', '2026-03-27', '2026-06-25', '2026-09-19']
frames, per_snap_year, per_snap_lst = [], {}, {}
for d in SNAP:
    r = pd.read_csv(base/f'raw/insideairbnb/{d}/reviews.csv.gz', usecols=['listing_id', 'id', 'date'], parse_dates=['date'])
    r['snap'] = d
    per_snap_year[d] = r.groupby(r['date'].dt.year).size()
    per_snap_lst[d] = r.groupby(r['date'].dt.year)['listing_id'].nunique()
    print(d, len(r), r['date'].min().date(), r['date'].max().date(), 'annunci distinti', r['listing_id'].nunique(), 'id recensione distinti', r['id'].nunique(), flush=True)
    frames.append(r)
allr = pd.concat(frames, ignore_index=True)
last = allr[allr.snap == SNAP[-1]].copy()
uni = allr.drop_duplicates('id').copy()
print('recensioni: ultimo snapshot', len(last), '| unione', len(uni))
for df in (last, uni):
    df['anno'] = df['date'].dt.year; df['mese'] = df['date'].dt.to_period('M').astype(str)

(base/'pulito').mkdir(exist_ok=True)
pa = uni.groupby('listing_id')['date'].agg(prima_recensione='min', ultima_recensione='max', n_recensioni='size').reset_index()
pa['in_ultimo_snapshot_reviews'] = pa['listing_id'].isin(set(last['listing_id']))
pa.to_csv(base/'pulito/recensioni_per_annuncio.csv', index=False)

anni = pd.DataFrame({
    'recensioni_ultimo': last.groupby('anno').size(),
    'annunci_con_recensione_ultimo': last.groupby('anno')['listing_id'].nunique(),
    'recensioni_unione': uni.groupby('anno').size(),
    'annunci_con_recensione_unione': uni.groupby('anno')['listing_id'].nunique()})
pa['anno_prima'] = pa['prima_recensione'].dt.year
anni['annunci_prima_recensione_unione'] = pa.groupby('anno_prima').size()
for d, s in per_snap_year.items(): anni[f'recensioni_nel_file_{d}'] = s
for d, s in per_snap_lst.items(): anni[f'annunci_con_recensione_nel_file_{d}'] = s
anni.index.name = 'anno'
anni = anni.fillna(0).astype(int).reset_index()
anni.to_csv(base/'pulito/recensioni_anno.csv', index=False)

mm = pd.DataFrame({'recensioni_ultimo': last.groupby('mese').size(), 'recensioni_unione': uni.groupby('mese').size()}).fillna(0).astype(int)
mm.index.name = 'mese'; mm.reset_index().to_csv(base/'pulito/recensioni_mese.csv', index=False)

an = pd.read_csv(base/'pulito/annunci_snapshot.csv', usecols=['snapshot', 'id', 'nil_id', 'nil_nome']).sort_values('snapshot')
an = an.drop_duplicates('id', keep='last').rename(columns={'id': 'listing_id'})   # NIL dell'ultimo snapshot in cui l'annuncio compare
m = uni.merge(an[['listing_id', 'nil_id', 'nil_nome']], on='listing_id', how='left')
print('recensioni dell''unione con annuncio mai visto nei file listings:', int(m['nil_id'].isna().sum()))
g = m.dropna(subset=['nil_id']).groupby(['nil_id', 'nil_nome', 'anno']).agg(recensioni=('listing_id', 'size'), annunci_con_recensione=('listing_id', 'nunique')).reset_index()
g['nil_id'] = g['nil_id'].astype(int)
g.to_csv(base/'pulito/recensioni_nil_anno.csv', index=False)
print(anni.to_string())
