import json, sys, os
import pandas as pd
R = sys.argv[1]
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60); pd.set_option('display.max_colwidth', 40)
def show(p, sep=',', n=3, **kw):
    fp = os.path.join(R, p)
    try:
        d = pd.read_csv(fp, sep=sep, nrows=2000, **kw)
    except Exception as e:
        print('ERR', p, e); return
    print('==', p, d.shape, list(d.columns)[:80])
    print(d.head(n).to_string()[:1800])
show('censimenti/pulito/indicatori_NIL.csv')
show('quartieri-che-cambiano/out/indicatori_nil.csv')
show('quartieri-che-cambiano/out/collegamento_cap_nil.csv')
show('speranza-vita/pulito/nil_smr_e0.csv')
show('speranza-vita/pulito/nil_bandiere_residenze.csv')
show('speranza-vita/pulito/decessi_nil_anno_genere.csv')
show('speranza-vita/pulito/residenti_nil_anno_cl_genere.csv')
show('elezioni/pulito/nil_info.csv')
show('elezioni/pulito/nil_controllo_popolazione.csv')
show('elezioni/pulito/sezione_nil.csv')
show('elezioni/famiglie_partiti.csv')
show('elezioni/pulito/nil_confronti.csv')
show('censimenti/pulito/raccordo_sezioni_1991.csv')
show('censimenti/pulito/raccordo_quote_area_1991.csv')
show('censimenti/pulito/sensibilita_ripartizione_area.csv')
show('popolazione/pulito/eta_nil_anno_indicatori.csv')
d = json.load(open(os.path.join(R,'docs/elezioni/data/nil/camera_2022-09-25.json'),encoding='utf8'))
print(type(d), list(d.keys())[:20] if isinstance(d,dict) else d[:2])
print(json.dumps(d)[:1800])
d = json.load(open(os.path.join(R,'docs/elezioni/data/nil/referendum_2020-09-20_ds1461.json'),encoding='utf8'))
print(json.dumps(d)[:800])
