import pandas as pd, glob, re, collections
fs=sorted(glob.glob('raw/ckan_ds*/*peg*.csv')+glob.glob('raw/ckan_ds39[67]/*.csv'))
for f in fs:
    for enc in ('utf-8','cp1252'):
        try: df=pd.read_csv(f,sep=';',encoding=enc,dtype=str,keep_default_na=False); break
        except: pass
    cols=df.columns[21:27]
    pats=collections.Counter()
    ex={}
    for c in cols:
        for v in df[c]:
            p=re.sub(r'\d','9',v)
            p=re.sub(r'9+','9',p)
            pats[p]+=1; ex.setdefault(p,v)
    print(f.split('/')[-1], dict(pats.most_common(12)))
    print('   ex',{k:ex[k] for k in list(ex)[:12]})
