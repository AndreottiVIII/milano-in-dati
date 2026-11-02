import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 200)
b = base()
print(b.shape, 'NIL>=3000:', (b.residenti >= 3000).sum())
print(b[['id_nil','nil','residenti','dist_duomo','area_km2','area_geo','reddito_2024','eta_media','densita_ab_km2','laur_1991','laur_2023','municipio']].head(8))
print('NA in nil3000:'); print(nil3000(b)[['dist_duomo','reddito_2024','eta_media','densita_ab_km2','laur_2023','laur_1991']].isna().sum())
print('area scarto', ((b.area_geo-b.area_km2)/b.area_km2).describe())
idx = indice()
print(len(idx['elezioni']))
for eid in ELEZ_POL+['comunali_sindaco_2021-10-03','comunali_sindaco_2016-06-05','municipali_consiglio_2021-10-03']:
    meta=[x for x in idx['elezioni'] if x['id']==eid][0]
    print('==',eid,meta['fam'])
    d=json.load(open(p('docs','elezioni','data','nil',eid+'.json'),encoding='utf8'))
    totnil=sum(sum(v['v']) for v in d['p'].values())
    print(' par n',len(meta['par']),'city',sum(meta['city']['v']),'sum nil',round(totnil),'na',d['na'],'city e',meta['city'].get('e'),'vt',meta['city'].get('vt'))
    agg={}
    for (nome,fi),x in zip(meta['par'],meta['city']['v']):
        agg.setdefault(meta['fam'][fi],[]).append((nome,x))
    for f,l in agg.items():
        l=sorted(l,key=lambda t:-t[1])
        tot=sum(x for _,x in l)
        print(f'  {f:15s} {tot/sum(meta["city"]["v"])*100:5.1f}% ',', '.join(f'{n}({x})' for n,x in l[:8]))
sez=pd.read_csv(p('elezioni','pulito','risultati_sezione.csv'),nrows=5); print(sez.columns.tolist()); print(sez.head(2).to_string())
vot=pd.read_csv(p('elezioni','pulito','voti_sezione.csv'),nrows=5); print(vot.columns.tolist()); print(vot.head(2).to_string())
for f,sep in [('popolazione/pulito/residenti_nil_anno_eta_genere.csv',','),('popolazione/pulito/residenti_nil_anno_cittadinanza.csv',','),('popolazione/pulito/confronto_censimento_anagrafe_nil.csv',','),('popolazione/pulito/flussi_nil_anno.csv',','),('popolazione/pulito/censimenti_nil_eta_stranieri_1991_2023.csv',',')]:
    print(f, pd.read_csv(p(f),nrows=3,sep=sep).to_string())
