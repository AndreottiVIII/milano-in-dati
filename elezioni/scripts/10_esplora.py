import sys, pandas as pd, os
base = sys.argv[1]
d = pd.read_csv(os.path.join(base, 'inventario_dataset.csv'), encoding='utf-8-sig')
for ds in [int(x) for x in sys.argv[2:]]:
    r = d[d.ds == ds].iloc[0]
    p = os.path.join(base, 'raw', r.csv_file)
    enc = 'cp1252' if 'cp1252' in str(r.codifica) else 'utf-8'
    df = pd.read_csv(p, sep=';', encoding=enc, dtype=str)
    print('==', ds, r.title[:80], df.shape)
    print(df.head(3).to_string())
    for c in ['Elezione', 'Nome_Elezione', 'Sessione']:
        if c in df:
            print(c, df[c].unique()[:5])
    if 'Lista' in df:
        print(df.Lista.nunique(), list(df.Lista.unique()[:15]))
