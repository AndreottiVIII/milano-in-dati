import sys, gzip, pandas as pd
f = sys.argv[1]
df = pd.read_csv(gzip.open(f,'rt'), header=None, names=['id','date','elem','val','mflag','qflag','sflag','obstime'], dtype={'date':str,'mflag':str,'qflag':str,'sflag':str,'obstime':str})
print(len(df), df.elem.value_counts().to_dict())
df['d']=pd.to_datetime(df.date)
for e,g in df.groupby('elem'):
    print(e, g.d.min().date(), g.d.max().date(), 'n=',len(g), 'expected days=',(g.d.max()-g.d.min()).days+1)
    print(' sflag', g.sflag.value_counts(dropna=False).to_dict())
    print(' qflag', g.qflag.value_counts(dropna=False).to_dict())
    print(' mflag', g.mflag.value_counts(dropna=False).to_dict())
    y=g.groupby(g.d.dt.year).size()
    full=y.reindex(range(g.d.dt.year.min(), g.d.dt.year.max()+1), fill_value=0)
    print(' years with <350 days:', full[full<350].to_dict())
    # first/last by sflag
    print(g.groupby('sflag').d.agg(['min','max','count']))
