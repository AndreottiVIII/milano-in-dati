import pandas as pd, glob, os, sys
fs=sorted(glob.glob('raw/ckan_ds*/*peg*.csv')+glob.glob('raw/ckan_ds39[67]/*.csv'))
for f in fs:
    for enc in ('utf-8','cp1252','latin-1'):
        try:
            df=pd.read_csv(f,sep=';',encoding=enc,dtype=str); break
        except Exception as e: pass
    print('=====',f,enc,df.shape)
    print(list(df.columns))
    t=df.columns[0]
    print(df[t].value_counts().to_dict())
    print('sample numeric:',df.iloc[3,19:26].tolist())
