"""Costruisce i dati della pagina in ../docs/ospedali/data/ (tutti i file sotto 2 MB).
Uso: python -I -X utf8 06_dati_pagina.py"""
import json, pathlib, csv
import numpy as np, pandas as pd
B = pathlib.Path(__file__).resolve().parent.parent
R = B.parent
OUT = R / 'docs' / 'ospedali' / 'data'; OUT.mkdir(parents=True, exist_ok=True)
GR = B / 'dati_grezzi'
ANNI = list(range(2010, 2024))
PUBBLICI = {'Ospedale a gestione diretta', 'IRCCS fondazione'}
# tipi di struttura del file nazionale che contano come pubblici (aziende ospedaliere, IRCCS pubblici, ecc.)
PUBBLICI_IT = PUBBLICI | {'Azienda Ospedaliera', "Azienda Ospedaliera integrata con l'Università",
    'Azienda Ospedaliera universitaria integrata con il Servizio Sanitario Nazionale', 'IRCCS pubblico',
    'Istituto qualificato presidio della U.S.L.', 'Ente di ricerca'}

# ---------- ds683 (Comune di Milano, copia dei dati del Ministero) ----------
d = pd.read_csv(GR/'ds683.csv', sep=';', encoding='utf-8-sig')
d['sub'] = d['Subcodice'].fillna(0).astype(int)
d['pub'] = d['Descrizione tipo struttura'].isin(PUBBLICI)
tot = d.groupby('Anno')['Totale posti letto'].sum()
pubb = d[d.pub].groupby('Anno')['Totale posti letto'].sum(); priv = d[~d.pub].groupby('Anno')['Totale posti letto'].sum()
tipodisc = d.pivot_table(index='Anno', columns='Tipo di Disciplina', values='Totale posti letto', aggfunc='sum').fillna(0)
nstr = d.groupby('Anno')['Codice struttura'].nunique()

# ---------- popolazione ISTAT al 1 gennaio ----------
bil = pd.read_csv(R/'popolazione/pulito/istat_bilancio_milano_2001_2018.csv')
bil = bil[(bil.Sesso == 'Maschi e femmine') & (bil.Cittadinanza == 'Tutte')].set_index('Anno')['Popolazione fine periodo']
conf = pd.read_csv(R/'popolazione/pulito/confronto_istat_comune.csv').set_index('anno_comune_31dic')['istat_1gen_totale']
popMI = {}
for a in ANNI:
    popMI[a] = int(bil[a-1]) if a <= 2018 else int(conf[a])
ec = json.load(open(GR/'eurostat_demo_r_d2jan_IT_ITC4.json'))
anni_e = list(range(2010, 2026)); vals = [ec['value'][str(i)] for i in range(32)]
popIT = dict(zip(anni_e, vals[:16])); popLO = dict(zip(anni_e, vals[16:]))

# ---------- Ministero: regioni ----------
fs = ['min_regione_2010_2019','min_regione_2020','min_regione_2021','min_regione_2022','min_regione_2023']
RG = pd.concat([pd.read_csv(GR/f'{f}.csv', sep=';', encoding='latin-1') for f in fs])
RG['reg'] = RG['Descrizione Regione'].str.strip()
it_tot = RG.groupby('Anno')['Totale posti letto'].sum()
lo_tot = RG[RG.reg == 'LOMBARDIA'].groupby('Anno')['Totale posti letto'].sum()

serie = []
for a in ANNI:
    serie.append(dict(anno=a, milano=int(tot[a]), pubblici=int(pubb[a]), privati=int(priv[a]), acuti=int(tipodisc.loc[a].get('ACUTI',0)),
        riab=int(tipodisc.loc[a].get('RIABILITAZIONE',0)), lungo=int(tipodisc.loc[a].get('LUNGODEGENZA',0)), strutture=int(nstr[a]),
        pop_milano=popMI[a], m1000=round(tot[a]/popMI[a]*1000, 3),
        lombardia=int(lo_tot[a]), pop_lombardia=int(popLO[a]), l1000=round(lo_tot[a]/popLO[a]*1000, 3),
        italia=int(it_tot[a]), pop_italia=int(popIT[a]), i1000=round(it_tot[a]/popIT[a]*1000, 3)))

# ---------- Ministero: strutture, confronto tra citta 2023 ----------
ms = pd.read_csv(GR/'min_struttura_2023.csv', sep=';', encoding='latin-1')
ms['Comune'] = ms['Comune'].str.strip()
cc = pd.read_csv(R/'docs/auto/data/confronto_citta.csv', sep=';')
cc = cc[(cc.anno == 2023) & (cc.tipo == 'comune')].set_index('territorio')['popolazione']
nomi = {'MILANO':'Milano','ROMA':'Roma','TORINO':'Torino','NAPOLI':'Napoli','BOLOGNA':'Bologna','FIRENZE':'Firenze','GENOVA':'Genova','VERONA':'Verona','BARI':'Bari','PALERMO':'Palermo'}
citta = []
for k, n in nomi.items():
    x = ms[ms.Comune == k]
    letti = int(x['Totale posti letto'].sum()); pop = int(cc[n])
    pub = int(x[x['Descrizione tipo struttura'].isin(PUBBLICI_IT)]['Totale posti letto'].sum())
    citta.append(dict(nome=n, letti=letti, pop=pop, per1000=round(letti/pop*1000, 2), pubblici=pub, strutture=int(x['Codice struttura'].nunique())))
citta.sort(key=lambda r: -r['per1000'])
assert [c for c in citta if c['nome']=='Milano'][0]['letti'] == int(tot[2023])

# ---------- specialita: Milano / Italia, 2023 ----------
a23 = RG[RG.Anno == 2023]
it_d = a23.groupby('Codice disciplina')['Totale posti letto'].sum()
mi_d = d[d.Anno == 2023].groupby('Codice disciplina')['Totale posti letto'].sum()
nm = d.groupby('Codice disciplina')['Descrizione disciplina'].first().str.strip()
ESCLUDI = {2, 98, 67, 60}  # day hospital, day surgery, pensionanti (letti a pagamento), lungodegenti
spec = []
for c, v in mi_d.items():
    if c in ESCLUDI: continue
    i_ = float(it_d.get(c, 0))
    if v < 40 or i_ == 0: continue
    spec.append(dict(cod=int(c), nome=nm[c], milano=int(v), italia=int(i_), m1000=round(v/popMI[2023]*1000, 3), i1000=round(i_/popIT[2023]*1000, 3), rapporto=round((v/popMI[2023])/(i_/popIT[2023]), 2)))
spec.sort(key=lambda r: -r['rapporto'])

# ---------- ospedali (2023) con serie dei letti ----------
P = json.load(open(B/'pulito/punti.json', encoding='utf-8'))
GRUPPO = {'30946-0':'30946-1','30112-0':'30946-1','30119-0':'30946-2','30104-0':'30950-0','30373-0':'30949-0',
          '30118-0':'30936-3','30389-0':'30936-3','30925-1':'30925-0','30925-2':'30925-0'}
d['k'] = d['Codice struttura'].astype(str) + '-' + d['sub'].astype(str)
d['g'] = d['k'].map(lambda k: GRUPPO.get(k, k))
pv = d.pivot_table(index='g', columns='Anno', values='Totale posti letto', aggfunc='sum').fillna(0)
for o in P['ospedali']:
    o['serie'] = [int(pv.loc[o['id'], a]) if o['id'] in pv.index else 0 for a in ANNI]
assert sum(o['serie'][0] for o in P['ospedali']) == int(tot[2010]), 'i gruppi non coprono il 2010'
assert all(sum(o['serie'][i] for o in P['ospedali']) == int(tot[a]) for i, a in enumerate(ANNI)), 'i gruppi non coprono tutti gli anni'
M = pd.read_csv(B/'pulito/minuti_nil.csv')
riep_min = json.load(open(B/'pulito/minuti_riepilogo.json'))

# ---------- quartieri ----------
gj = json.load(open(R/'docs/medici-farmacie/data/nil.geojson', encoding='utf-8'))
H_nil = pd.DataFrame(P['ospedali']).groupby('idnil').agg(letti=('letti','sum'), n=('id','count'))
def rnd(c):
    return [round(c[0], 5), round(c[1], 5)] if isinstance(c[0], (int, float)) else [rnd(x) for x in c]
feat = []
for f in gj['features']:
    p = f['properties']; i = p['i']
    m = M[M.id == i]
    o = dict(i=i, n=p['n'], mu=p['mu'], ab=p['ab'])
    o['le'] = int(H_nil.letti.get(i, 0)); o['no'] = int(H_nil.n.get(i, 0))
    if len(m) and not np.isnan(m.min_ps_g.iloc[0]):
        r = m.iloc[0]
        o.update(mo=float(r.min_osp), po=r.p_osp, mp=float(r.min_ps_g), pp=r.p_ps_g, mt=float(r.min_ps_tutti), pt=r.p_ps_tutti)
    feat.append(dict(type='Feature', properties=o, geometry=dict(type=f['geometry']['type'], coordinates=rnd(f['geometry']['coordinates']))))
json.dump(dict(type='FeatureCollection', features=feat), open(OUT/'nil_quartieri.geojson', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---------- riepilogo ----------
riep = dict(serie=serie, citta=citta, specialita=spec, ospedali=P['ospedali'], ps=P['ps'], minuti=riep_min, anno=2023)
json.dump(riep, open(OUT/'riepilogo.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))

# ---------- csv per chi scarica ----------
def w(nome, rows, cols):
    with open(OUT/nome, 'w', encoding='utf-8', newline='') as f:
        wr = csv.writer(f, delimiter=';'); wr.writerow(cols)
        for r in rows: wr.writerow([r.get(c, '') for c in cols])
w('letti_milano_per_anno.csv', serie, ['anno','milano','pubblici','privati','acuti','riab','lungo','strutture','pop_milano','m1000','lombardia','pop_lombardia','l1000','italia','pop_italia','i1000'])
w('confronto_citta_2023.csv', citta, ['nome','letti','pop','per1000','strutture'])
w('specialita_2023.csv', spec, ['cod','nome','milano','italia','m1000','i1000','rapporto'])
w('ospedali_2023.csv', [dict(o, serie_2010=o['serie'][0]) for o in P['ospedali']], ['id','nome','indirizzo','tipo_ds','pubblico','nil','letti','ordinari','pagamento','dh','ds','lat','lon','serie_2010'])
w('pronto_soccorso.csv', P['ps'], ['nome','tipo','fuori','lat','lon','osm'])
w('minuti_quartieri.csv', M.fillna('').to_dict('records'), ['id','quartiere_nil','residenti_2025','min_osp','p_osp','min_ps_g','p_ps_g','min_ps_tutti','p_ps_tutti'])
for f in OUT.iterdir(): print(f.name, f.stat().st_size)
print(json.dumps(serie[0]), json.dumps(serie[-1]))
for c in citta: print(c)
for s in spec: print(s)
