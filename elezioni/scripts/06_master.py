"""Tabella per dataset (inventario_dataset.csv) e riepiloghi per tipo di elezione."""
import sys, os, pandas as pd
base = sys.argv[1]
meta = os.path.join(base, 'meta')
inv = pd.read_csv(os.path.join(meta,'inventario_risorse.csv'), encoding='utf-8-sig')
prof = pd.read_csv(os.path.join(meta,'profilo_csv.csv'))
dl = pd.read_csv(os.path.join(meta,'download_log.csv'), encoding='utf-8-sig')
inv['key'] = inv.dataset.str.slice(0,80)
prof = prof[prof.file.str.endswith('.csv')]
rows=[]
for d, g in inv.groupby('dataset', sort=False):
    k = d[:80]
    pr = prof[prof.dataset==k]
    first = g.iloc[0]
    csvr = g[g.format.isin(['CSV','SHP'])]
    dd = dl[dl.dataset.str.slice(0,80)==k]
    r = dict(dataset=d, ds=first.ds, title=first.title, kind=first['kind'], election_type=first.election_type, year=first.year, date_start=first.date_start, date_end=first.date_end, level=first.level,
             license=first.license, dataset_modified=first.dataset_modified, formati=','.join(sorted(set(g.format))),
             scaricato=('si' if len(dd) and (dd.status=='ok').all() else ('NO' if len(dd) else 'no (solo link/JSON)')),
             byte_scaricati=int(dd.size_bytes.sum()) if len(dd) else 0)
    if len(pr):
        p0 = pr.iloc[0]
        r.update(csv_file=p0.file, righe=int(p0.rows), sezioni_distinte=p0.sez_distinct, codifica=p0.encoding, separatore=p0.delimiter, intestazione=p0.header)
    rows.append(r)
m = pd.DataFrame(rows)
m.to_csv(os.path.join(base,'inventario_dataset.csv'), index=False, encoding='utf-8-sig')
inv.drop(columns=['key']).to_csv(os.path.join(base,'inventario_risorse.csv'), index=False, encoding='utf-8-sig')
print(len(m), 'dataset;', m.scaricato.value_counts().to_dict())
res = m[m['kind'].isin(['risultati_sezione','riepilogo_sezione'])]
vot = m[m['kind']=='voti_lista_sezione']
for et, g in m.groupby('election_type'):
    print(et, 'dataset', len(g), 'risultati', (g['kind'].isin(['risultati_sezione','riepilogo_sezione'])).sum(), 'voti', (g['kind']=='voti_lista_sezione').sum(), 'anni', sorted(set(g.year.astype(str)))) 
print('righe totali risultati', res.righe.sum(), 'voti', vot.righe.sum())
print(m['kind'].value_counts().to_dict())
