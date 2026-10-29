import sys, os, pickle
import pandas as pd
work = sys.argv[1]
out = pickle.load(open(os.path.join(work, 'carica.pkl'), 'rb'))
rows = []
for ds, o in sorted(out.items()):
    d = o['df']
    ses = d.sessione.unique().tolist()
    nonnum = int(d.sezione.isna().sum())
    t = d.territorio
    key = ['sezione'] + (['lista'] if 'lista' in d else [])
    dup = int(d.duplicated(key).sum())
    rows.append(dict(ds=ds, kind=o['kind'][:4], sess=ses[:3], tcol=o['tcol'], tmin=t.min(), tmax=t.max(), tna=int(t.isna().sum()),
                     nsez=d.sezione.nunique(), sezNaN=nonnum, dup=dup, n=len(d), title=o['title'][:60]))
df = pd.DataFrame(rows)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500); pd.set_option('display.max_colwidth', 60)
print(df.to_string())
