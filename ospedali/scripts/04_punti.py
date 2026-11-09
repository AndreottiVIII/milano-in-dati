"""Elenco pulito di ospedali (da ds683, anno 2023) e pronto soccorso (da OpenStreetMap) -> pulito/punti.json
Uso: python -I -X utf8 04_punti.py"""
import json, pathlib
import pandas as pd
B = pathlib.Path(__file__).resolve().parent.parent
d = pd.read_csv(B/'dati_grezzi/ds683.csv', sep=';', encoding='utf-8-sig')
# nome pulito (a mano, per codice struttura e sottocodice) - 2023
NOMI = {
 (30056,0):'Buzzi (ospedale dei bambini)',(30057,0):'Melloni',(30096,0):'Casa di cura del Policlinico',
 (30097,0):'Istituto Clinico Città Studi',(30100,0):'Casa di cura Igea',(30103,0):'Casa di cura Palazzolo (Don Gnocchi)',
 (30110,0):'Casa di cura San Giovanni',(30121,0):'Casa di cura San Pio X',(30124,0):'Istituto Stomatologico Italiano',
 (30367,0):'San Giuseppe',(30378,0):'Centro clinico Nemo',(30910,0):'Fatebenefratelli e Oftalmico',
 (30911,0):'Gaetano Pini',(30912,0):'CTO (traumatologico e ortopedico)',(30913,0):'Niguarda',(30914,0):'San Paolo',
 (30915,0):'San Carlo Borromeo',(30916,0):'Sacco',(30922,0):'Istituto dei Tumori',(30923,0):'Istituto Besta (neurologico)',
 (30925,0):'Policlinico (Ospedale Maggiore)',(30934,0):'Centro Cardiologico Monzino',(30935,0):'San Raffaele',
 (30936,1):'Auxologico San Luca',(30936,2):'Auxologico San Michele',(30937,0):'Santa Maria Nascente (Don Gnocchi)',
 (30941,0):'Istituto Europeo di Oncologia',(30946,1):'Galeazzi Sant\'Ambrogio',(30946,2):'Istituto Clinico San Siro',
 (30949,0):'Istituto di Riabilitazione (Camaldoli)',(30950,0):'San Raffaele Turro',(30389,0):'Capitanio (ex San Carlo)',
 (30936,3):'Ospedale Capitanio',
}
PUBBLICI = {'Ospedale a gestione diretta','IRCCS fondazione'}
d['sub'] = d['Subcodice'].fillna(0).astype(int)
d['key'] = d['Codice struttura'].astype(str) + '-' + d['sub'].astype(str)
# coordinate: la prima disponibile in qualunque anno, per struttura
pos = d.dropna(subset=['LAT_Y_4326']).groupby('key').agg(lat=('LAT_Y_4326','last'), lon=('LONG_X_4326','last'),
        nil=('NIL','last'), idnil=('ID_NIL','last'))
x = d[d.Anno == 2023]
rows = []
for k, g in x.groupby('key'):
    p = pos.loc[k]; kk = tuple(int(v) for v in k.split('-'))
    tp = g['Descrizione tipo struttura'].iloc[0]
    disc = g.groupby('Descrizione disciplina')['Totale posti letto'].sum().sort_values(ascending=False)
    rows.append(dict(id=k, nome=NOMI[kk], indirizzo=g['Indirizzo'].iloc[0].title().replace('Via G.Dezza','Via Dezza'),
        tipo_ds=tp, pubblico=bool(tp in PUBBLICI), lat=round(float(p.lat),6), lon=round(float(p.lon),6),
        nil=p.nil, idnil=int(p.idnil), letti=int(g['Totale posti letto'].sum()),
        ordinari=int(g['Posti letto degenza ordinaria'].sum()), pagamento=int(g['Posti letto degenza a pagamento'].sum()),
        dh=int(g['Posti letto Day Hospital'].sum()), ds=int(g['Posti letto Day Surgery'].sum()),
        top=[[a.title(), int(b)] for a, b in disc.head(3).items()]))
ospedali = sorted(rows, key=lambda r: -r['letti'])
# pronto soccorso: punti da OpenStreetMap (ingresso del pronto soccorso se c'e', altrimenti centro dell'ospedale)
osm = {(e['type'], e['id']): e for e in json.load(open(B/'dati_grezzi/osm_ospedali_milano.json', encoding='utf-8'))['elements']}
def pt(t, i):
    e = osm[(t, i)]; c = e.get('center') or e; return round(c['lat'], 6), round(c['lon'], 6)
PS = [  # nome, tipo (g = generale, s = specialistico), fuori Milano?, (tipo osm, id)
 ('Niguarda','g',0,('node',257541827)),('Sacco','g',0,('node',6133388341)),('San Carlo Borromeo','g',0,('way',23801230)),
 ('San Paolo','g',0,('node',6165413772)),('Fatebenefratelli','g',0,('relation',4777470)),
 ('Policlinico','g',0,('node',6148419438)),('San Raffaele','g',0,('node',6133410550)),
 ('San Giuseppe','g',0,('node',6165355216)),('Galeazzi Sant\'Ambrogio','g',0,('way',1096964539)),
 ('Istituto Clinico Città Studi','g',0,('way',1510671203)),('Melloni','g',0,('node',6148368094)),
 ('Buzzi (bambini)','s',0,('node',6133448377)),('Gaetano Pini (ortopedico)','s',0,('node',13226903701)),
 ('CTO (ortopedico)','s',0,('node',14137944728)),('Monzino (cuore)','s',0,('node',13786079782)),
 ('Auxologico San Luca','s',0,('node',6165363171)),
 ('Humanitas (Rozzano)','g',1,('way',59465363)),('San Donato (Policlinico San Donato)','g',1,('node',3951766272)),
 ('Bassini (Cinisello)','g',1,('node',6126685488)),('Rho','g',1,('node',6126656355)),('Bollate','g',1,('way',198313143)),
 ('Città di Sesto','g',1,('node',6131322634)),
]
ps = []
for n, t, f, k in PS:
    la, lo = pt(*k); ps.append(dict(nome=n, tipo=t, fuori=f, lat=la, lon=lo, osm=f'{k[0]}/{k[1]}'))
json.dump(dict(ospedali=ospedali, ps=ps), open(B/'pulito/punti.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(ospedali), sum(o['letti'] for o in ospedali), len(ps))
for o in ospedali: print(o['id'], o['nome'], o['letti'], o['pubblico'], o['nil'])
