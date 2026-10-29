"""Confronta le serie giornaliere pubblicate (ds1072, ds1085) con la somma dei file mensili per varco. Uso: 04 <raw> <out>"""
import sys,glob,zipfile,re,pandas as pd,os
raw,out=sys.argv[1:3]
parts=[]
for z in sorted(glob.glob(os.path.join(raw,'*','*ingressi_areac_20*.zip'))):
    zf=zipfile.ZipFile(z)
    for n in zf.namelist():
        df=pd.read_csv(zf.open(n),usecols=['dataora','moto','areac','numero_transiti','id_varco'],dtype=str)
        df['d']=df.dataora.str[:10]; df['n']=pd.to_numeric(df.numero_transiti); df['moto']=df.moto.astype(int)
        g=df.groupby(['d']).apply(lambda x:pd.Series({'tot':x.n.sum(),'moto':x.n[x.moto==1].sum(),'auto':x.n[x.moto==0].sum()}),include_groups=False)
        parts.append(g)
m=pd.concat(parts); m.index=pd.to_datetime(m.index.str.replace('/','-')); m=m.sort_index()
m.to_csv(os.path.join(out,'giornaliero_da_mensili.csv'),sep=';')
a=pd.read_csv(glob.glob(os.path.join(raw,'ds1085*','*.csv'))[0],sep=';',quotechar='"'); a['t']=pd.to_datetime(a.data_giorno.str[:10]); a=a.set_index('t').numero_transiti_giornalieri
o=pd.read_csv(glob.glob(os.path.join(raw,'ds1072*','*no_dic.csv'))[0],sep=';'); o['t']=pd.to_datetime(o.data_giorno.str[:10]); o=o.set_index('t').numero_transiti_giornalieri
n=pd.read_csv(glob.glob(os.path.join(raw,'ds1072*','*2025-01-17.csv'))[0],sep=';'); n['t']=pd.to_datetime(n.data_giorno.str[:10]); n=n.set_index('t')
for nome,s in [('ds1085 2016-2018',a),('ds1072 vecchio 2019-2023',o),('ds1072 nuovo h24 2023-12..2024-11',n.totale_transiti_giornalieri_h24)]:
    j=pd.concat([s.rename('pub'),m.tot.rename('mens')],axis=1,join='inner')
    j['r']=j.pub/j.mens
    print(nome,'giorni in comune',len(j),'rapporto pubblicato/mensile: min %.3f mediana %.3f max %.3f'%(j.r.min(),j.r.median(),j.r.max()),'| giorni con scarto >1%%: %d'%((j.r-1).abs().gt(.01).sum()))
    bad=j[(j.r-1).abs()>.01]; print(bad.head(8).to_string())
j=pd.concat([n.totale_transiti_giornalieri_h24.rename('pub'),m.auto.rename('auto'),m.tot.rename('tot')],axis=1,join='inner'); print((j.pub/j.tot).describe())
# giorni nei mensili assenti nel pubblicato
for nome,s in [('ds1085',a),('ds1072 vecchio',o),('ds1072 nuovo',n)]:
    rng=m.index[(m.index>=s.index.min())&(m.index<=s.index.max())]
    print(nome,'giorni presenti nei mensili ma non nella serie giornaliera:',len(set(rng)-set(s.index)), [str(x.date()) for x in sorted(set(rng)-set(s.index))][:70])
