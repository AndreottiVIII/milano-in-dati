import sys, pandas as pd
df = pd.read_csv(sys.argv[1], sep=';', dtype=str)
print(df.shape)
v = df.drop_duplicates('CODICE_VIA')
print('vie uniche CODICE_VIA', len(v))
for c in ['STATOVIA','TIPO','STATOCIVICO']:
    print(v[c].value_counts(dropna=False).head(20) if c!='STATOCIVICO' else df[c].value_counts(dropna=False))
print(v['DATA_INTITOLAZIONE'].str[:4].value_counts().sort_index().head(60))
print((v['DATA_INTITOLAZIONE']=='17000101').sum(), v['DATA_INTITOLAZIONE'].isna().sum())
print(v[['CODICE_VIA','TIPO','DENOMINAZIONE','DATA_INTITOLAZIONE','ANNO_SOPPRESSIONE','DESCRITTIVO','ANNCSU','OPENSTREETMAP']].sample(15, random_state=1).to_string())
print(v['DENOMINAZIONE'].nunique())
