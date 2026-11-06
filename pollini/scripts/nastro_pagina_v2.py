"""Prepara i dati della nuova pagina Pollini (nastri a decadi, giorni forti, ambrosia giorno per giorno).
Uso: python -I -X utf8 prepara_dati.py
Legge  pollini/pulito/concentrazioni_giornaliere.csv, pollini/pulito/stagioni_taxon_anno.csv, pollini/raw/ispra/pollini_spore.csv
Scrive bozze-grafici/pollini-v2/data/nastro.json  (solo valori aggregati)."""
import json, os
import numpy as np, pandas as pd
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(R, 'pollini'); OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
TAXA = [('Corylus','Nocciolo'),('Alnus','Ontano'),('Cupressaceae/Taxaceae','Cipressi e affini'),('Platanaceae','Platano'),
        ('Betula','Betulla'),('Fraxinus','Frassino'),('Quercus','Quercia'),('Gramineae','Graminacee'),
        ('Urticaceae','Parietaria (urticacee)'),('Artemisia','Artemisia'),('Ambrosia','Ambrosia')]
ref = pd.read_csv(os.path.join(P,'raw','ispra','pollini_spore.csv'))
SOG = {k: [float(x) for x in ref[ref.PART_NAME_I==k][['PART_LOW','PART_MIDDLE','PART_HIGH']].iloc[0]] for k,_ in TAXA}
d = pd.read_csv(os.path.join(P,'pulito','concentrazioni_giornaliere.csv'), sep=';', usecols=['data','codice_stazione','taxon','granuli_m3'])
d['data'] = pd.to_datetime(d.data); d['anno'] = d.data.dt.year
st = pd.read_csv(os.path.join(P,'pulito','stagioni_taxon_anno.csv'), sep=';')
valid = {(r.stazione, r.taxon, int(r.anno)) for r in st.itertuples() if r.valida}
d = d[d.taxon.isin([k for k,_ in TAXA])].copy()
d = d[[ (s,t,a) in valid for s,t,a in zip(d.codice_stazione,d.taxon,d.anno)]]
m = d.data.dt.month.values; dd = d.data.dt.day.values
d['dec'] = (m-1)*3 + np.minimum((dd-1)//10, 2)
out = {'taxa':[], 'tip':{}, 'anni':{}, 'alti':{}, 'ambrosia':{}}
LAST = d.groupby('anno').data.max()
for k,nome in TAXA:
    g = d[d.taxon==k]
    out['taxa'].append({'k':k,'nome':nome,'sog':SOG[k]})
    # massimo di ogni decade per stazione e anno (almeno 3 giorni con dato nella decade)
    a = g.groupby(['codice_stazione','anno','dec']).granuli_m3.agg(['max','count']).reset_index()
    a = a[a['count']>=3]
    tip = []
    for dec in range(36):
        v = a[(a.dec==dec)&(a.anno<2026)]['max']
        tip.append(round(float(v.median()),1) if len(v)>=5 else None)
    out['tip'][k] = tip
    yy = {}
    for y,gy in a.groupby('anno'):
        row = []
        for dec in range(36):
            v = gy[gy.dec==dec]['max']
            row.append(round(float(v.median()),1) if len(v) else None)
        yy[int(y)] = {'v':row, 'n':int(gy.codice_stazione.nunique())}
    out['anni'][k] = yy
    # giorni con valore alto (>= soglia alta) per anno, mediana tra le stazioni
    hi = SOG[k][2]
    z = g.groupby(['codice_stazione','anno']).granuli_m3.apply(lambda s:int((s>=hi).sum())).reset_index()
    z2 = z.groupby('anno').granuli_m3.median()
    out['alti'][k] = {int(y):float(v) for y,v in z2.items()}
# ambrosia giorno per giorno a Novara (giorno dell'anno 196-290), per anno valido
gn = d[(d.taxon=='Ambrosia')&(d.codice_stazione=='NO1')]
amb = {}
for y,gy in gn.groupby('anno'):
    doy = gy.data.dt.day_of_year.values; val = gy.granuli_m3.values
    arr = [None]*(290-196+1)
    for dy,v in zip(doy,val):
        if 196<=dy<=290: arr[dy-196]=float(v)
    amb[int(y)] = arr
out['ambrosia'] = amb
json.dump(out, open(os.path.join(OUT,'nastro.json'),'w',encoding='utf-8'), ensure_ascii=False, separators=(',',':'))
print(os.path.getsize(os.path.join(OUT,'nastro.json')))
for k,_ in TAXA: print(k, SOG[k], [None if v is None else round(v) for v in out['tip'][k]][:36], sorted(out['anni'][k])[:1], sorted(out['anni'][k])[-1])
