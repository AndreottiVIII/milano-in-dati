"""Controlla copertura e buchi dei file scaricati. uso: python -I check_coverage.py RAWDIR"""
import sys, os, glob, io, gzip, pandas as pd
raw=sys.argv[1]
def read_ecad(p):
    lines=open(p,encoding='latin-1').read().splitlines()
    i=[k for k,l in enumerate(lines) if l.strip().startswith('STAID')][0]
    df=pd.read_csv(io.StringIO('\n'.join(lines[i:])),skipinitialspace=True)
    df.columns=[c.strip() for c in df.columns]
    df['d']=pd.to_datetime(df.DATE.astype(str),format='%Y%m%d')
    el=[c for c in df.columns if c in('TX','TN','TG')][0]
    df['v']=df[el].where((df['Q_'+el]!=9)&(df[el]!=-9999))  # 9 o -9999 = mancante
    df['q']=df['Q_'+el]
    return df,el
def rep(name,df,el):
    ok=df.dropna(subset=['v'])
    print(f'\n## {name}: righe {len(df)}, valide {len(ok)}, da {df.d.min().date()} a {df.d.max().date()}, prima valida {ok.d.min().date()}, ultima valida {ok.d.max().date()}')
    print('   qualita:',df.q.value_counts().to_dict())
    full=pd.date_range(ok.d.min(),ok.d.max()); miss=full.difference(ok.d)
    print(f'   giorni mancanti tra prima e ultima valida: {len(miss)} su {len(full)}')
    # buchi lunghi (>=10 giorni)
    if len(miss):
        s=pd.Series(miss); grp=(s.diff()!=pd.Timedelta('1D')).cumsum()
        gg=s.groupby(grp).agg(['min','max','count']); gg=gg[gg['count']>=10]
        print('   buchi >=10 giorni:',[(a.date().isoformat(),b.date().isoformat(),int(c)) for a,b,c in gg.values][:25])
    if 'SOUID' in df.columns:
        sg=df.dropna(subset=['v']).groupby('SOUID').d.agg(['min','max','count'])
        print('   fonti (SOUID) nel file:'); print(sg.to_string())
    return ok
for p in sorted(glob.glob(os.path.join(raw,'ecad','*','[TX][XNG]_*.txt'))):
    df,el=read_ecad(p); rep(os.path.relpath(p,raw),df,el)

# --- ARPA ---
print('######## ARPA Lombardia sensore 5897 (Milano v.Brera, temperatura) ########')
parts=[]
for p in sorted(glob.glob(os.path.join(raw,'arpa','brera_5897_*.csv'))):
    a=pd.read_csv(p,dtype={'stato':str}); a['file']=os.path.basename(p); parts.append(a)
    print(os.path.basename(p),len(a),'righe;',a.data.min(),'->',a.data.max(),'; stato:',a.stato.value_counts(dropna=False).to_dict(),'; valore NaN:',a.valore.isna().sum(),'; min/max valore',a.valore.min(),a.valore.max())
A=pd.concat(parts); A['t']=pd.to_datetime(A.data)
print('righe totali',len(A),'duplicati su (data):',A.duplicated('t').sum())
# overlap tra file
for x,y in [(0,1),(1,2),(2,3)]:
    if y<len(parts):
        ov=set(pd.to_datetime(parts[x].data))&set(pd.to_datetime(parts[y].data)); print('timestamp in comune file',x,y,len(ov))
# passo temporale
A=A.drop_duplicates('t').sort_values('t'); A['dt']=A.t.diff()
print('passi piu frequenti:',A.dt.value_counts().head(5).to_dict())
# giorni con dati validi
V=A[(A.stato=='VA')&A.valore.notna()].copy(); V['day']=(V.t-pd.Timedelta('1s')).dt.floor('D')
dd=V.groupby('day').valore.agg(['count','min','max','mean'])
print('giorni con almeno 1 dato valido:',len(dd),'da',dd.index.min().date(),'a',dd.index.max().date())
alld=pd.date_range(dd.index.min(),dd.index.max()); print('giorni senza nessun dato valido:',len(alld.difference(dd.index)))
by=dd.groupby(dd.index.year)['count'].agg(['count','mean']); 
ann=pd.DataFrame({'giorni_validi':dd.groupby(dd.index.year).size()}); ann['giorni_con_>=20_ore(o>=120 dieci-min)']=dd[dd['count']>=20].groupby(dd[dd['count']>=20].index.year).size()
print(ann.to_string())
s=pd.Series(alld.difference(dd.index)); 
if len(s):
    g=(s.diff()!=pd.Timedelta('1D')).cumsum(); gg=s.groupby(g).agg(['min','max','count']); print('buchi >=3 giorni senza dati:',[(a.date().isoformat(),b.date().isoformat(),int(c)) for a,b,c in gg.values if c>=3])
