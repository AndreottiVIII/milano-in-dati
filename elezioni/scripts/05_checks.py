"""Controlli di fase 1 (solo osservazioni, nessuna pulizia): sezioni nel tempo, coerenza interna dei totali, stabilita' di municipio e sede."""
import sys, os, re, io, json
import pandas as pd
rawdir, outdir = sys.argv[1:3]
prof = pd.read_csv(os.path.join(outdir, 'profilo_csv.csv'))
inv = pd.read_csv(os.path.join(outdir, 'inventario_risorse.csv'), encoding='utf-8-sig')
invd = inv.drop_duplicates('dataset').set_index(inv.drop_duplicates('dataset')['dataset'].str.slice(0,80))
def load(rel):
    b = open(os.path.join(rawdir, rel), 'rb').read()
    try: t = b.decode('utf-8-sig')
    except UnicodeDecodeError: t = b.decode('cp1252')
    first = t.split('\n',1)[0]
    d = ';' if first.count(';') >= first.count(',') else ','
    return pd.read_csv(io.StringIO(t), sep=d, dtype=str, keep_default_na=False)
def num(s):
    return pd.to_numeric(s.str.replace(',', '.', regex=False), errors='coerce')
# 1. coerenza interna dei file "risultati/riepilogo"
rows = []
rs = prof[prof.dataset.map(lambda d: invd.loc[d,'kind']).isin(['risultati_sezione','riepilogo_sezione']) & prof.file.str.endswith('.csv')]
store = {}
for _, r in rs.iterrows():
    df = load(r.file); ds = r.dataset
    store[ds] = df
    c = {k.lower(): k for k in df.columns}
    E,V,Va,N = (num(df[c[k]]) for k in ('elettori','votanti','validi','non validi'))
    rec = dict(dataset=ds, title=invd.loc[ds,'title'], rows=len(df), elettori_tot=E.sum(), votanti_tot=V.sum(), validi_tot=Va.sum(), nonvalidi_tot=N.sum(),
               righe_votanti_ne_validi_piu_nonvalidi=int(((Va+N)!=V).sum()), righe_votanti_gt_elettori=int((V>E).sum()), righe_elettori_zero=int((E==0).sum()),
               sezioni_duplicate=int(df[c['sezione']].duplicated().sum()))
    if 'si' in c:
        S,No = num(df[c['si']]), num(df[c['no']])
        rec['righe_si_piu_no_ne_validi'] = int(((S+No)!=Va).sum()); rec['si_tot']=S.sum(); rec['no_tot']=No.sum()
        rec['si_ha_virgola_decimale'] = bool(df[c['si']].str.contains(',').any())
    for k in ('municipio','zona','circoscrizione'):
        if k in c: rec['terr_col']=k; rec['terr_n']=df[c[k]].nunique(); rec['terr_vals']=','.join(sorted(df[c[k]].unique(), key=lambda x: (len(x),x)))[:60]
    rows.append(rec)
pd.DataFrame(rows).to_csv(os.path.join(outdir,'controlli_coerenza_totali.csv'), index=False, encoding='utf-8-sig')
# 2. sezioni per elezione e sezioni fuori numerazione standard
rows2 = []
for ds, df in store.items():
    c = {k.lower(): k for k in df.columns}
    s = num(df[c['sezione']])
    big = sorted(s[s>2243].astype(int).tolist())
    rows2.append(dict(dataset=ds, n_sezioni=s.nunique(), min=s.min(), max=s.max(), oltre_2243=','.join(map(str,big))))
pd.DataFrame(rows2).to_csv(os.path.join(outdir,'sezioni_per_elezione.csv'), index=False, encoding='utf-8-sig')
# 3. stabilita' sezione -> territorio (zona/municipio) fra elezioni selezionate
def terr(ds):
    df = store[[k for k in store if k.startswith(ds)][0]]
    c = {k.lower(): k for k in df.columns}
    k = next(x for x in ('municipio','zona','circoscrizione') if x in c)
    return pd.Series(df[c[k]].values, index=num(df[c['sezione']]).astype(int)), k
picks = {'1980':'ds1198','1990':'ds1206','1997':'ds1219','2001':'ds1228','2006':'ds1235','2011':'ds1245','2016':'ds1255','2018':'ds1260','2021':'ds1624','2022':'ds1983','2024':'ds2746','2025':'ds2930','2026':'ds2975'}
T = {y: terr(d) for y,d in picks.items()}
out = []
ys = list(picks)
for i in range(len(ys)-1):
    a,ka = T[ys[i]]; b,kb = T[ys[i+1]]
    common = a.index.intersection(b.index)
    same = (a.loc[common].values == b.loc[common].values).sum()
    out.append(dict(da=ys[i], a=ys[i+1], col_a=ka, col_b=kb, n_a=len(a), n_b=len(b), comuni=len(common), stesso_territorio=int(same), solo_in_a=len(a.index.difference(b.index)), solo_in_b=len(b.index.difference(a.index))))
pd.DataFrame(out).to_csv(os.path.join(outdir,'stabilita_territorio.csv'), index=False, encoding='utf-8-sig')
# 4. stabilita' indirizzo sede per numero sezione (file Sezioni e sedi)
sede = {}
for _, r in prof[prof.file.str.endswith('.csv')].iterrows():
    ds = r.dataset; k = invd.loc[ds,'kind']
    if k != 'sezioni_sedi': continue
    df = load(r.file); c = {x.lower(): x for x in df.columns}
    ac = next(x for x in ('sede','indirizzo','indirizzo_sede') if x in c)
    s = num(df[c['sezione']]).astype(int)
    sede[ds] = pd.Series(df[c[ac]].str.upper().str.replace(r'[^A-Z0-9]','',regex=True).values, index=s)
    sede[ds] = sede[ds][~sede[ds].index.duplicated()]
names = sorted(sede, key=lambda d: str(invd.loc[d,'date_start']))
json.dump({n: invd.loc[n,'title'] for n in names}, open(os.path.join(outdir,'sedi_file_titoli.json'),'w'), ensure_ascii=False, indent=1)
M = []
for i in range(len(names)-1):
    a,b = sede[names[i]], sede[names[i+1]]
    common = a.index.intersection(b.index)
    same = (a.loc[common].values == b.loc[common].values).sum()
    M.append(dict(da=names[i][:7], data_a=str(invd.loc[names[i],'date_start']), a=names[i+1][:7], data_b=str(invd.loc[names[i+1],'date_start']), n_a=len(a), n_b=len(b), comuni=len(common), stesso_indirizzo=int(same)))
pd.DataFrame(M).to_csv(os.path.join(outdir,'stabilita_sedi_consecutive.csv'), index=False, encoding='utf-8-sig')
# primo vs ultimo
f,l = sede[names[0]], sede[names[-1]]
common = f.index.intersection(l.index)
print('primo/ultimo', names[0][:7], names[-1][:7], len(common), int((f.loc[common].values==l.loc[common].values).sum()))
print('ok')
