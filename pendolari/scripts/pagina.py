"""Scrive i file dati della pagina "Pendolari" (docs/pendolari/data/).

Uso (percorsi assoluti, si puo' rilanciare):
  python -I -X utf8 pagina.py <cartella pendolari> <cartella docs>

Legge pendolari/pulito/*.csv e riepilogo.json (prodotti da analisi.py) e i confini dei comuni ISTAT 2021
(raw/istat_codici/x/Limiti2021_g/Com2021_g/Com2021_g.shp, generalizzati, CC BY 4.0).
Scrive in <docs>/pendolari/data/: riepilogo.json (tutte le tabelle usate dalla pagina), comuni.geojson (1.506 comuni
lombardi, semplificati, con i valori), e i csv scaricabili. Sono tutti valori aggregati per comune o per fascia: nessun
dato individuale (i file ISTAT non ne contengono).
"""
import sys, json, shutil
from pathlib import Path
import numpy as np
import pandas as pd
import pyogrio, pyogrio.raw
import shapely, shapely.ops
from shapely.geometry import mapping

P = Path(sys.argv[1])
DOCS = Path(sys.argv[2])
PU = P / 'pulito'
OUT = DOCS / 'pendolari' / 'data'
OUT.mkdir(parents=True, exist_ok=True)
AVV = []


def check(nome, calc, atteso, tol=0):
    ok = abs(calc - atteso) <= tol
    print(('ok  ' if ok else '!!  ') + f'{nome}: {calc} (atteso {atteso})')
    if not ok:
        AVV.append(nome)


R = json.load(open(PU / 'riepilogo.json', encoding='utf8'))
CTRL = json.load(open(PU / 'controlli_parse.json', encoding='utf8'))
com = pd.read_csv(PU / 'comuni_2021.csv').set_index('pro_com')
serie = pd.read_csv(PU / 'serie_totali.csv')
grp = pd.read_csv(PU / 'origini_gruppi.csv')
top = pd.read_csv(PU / 'top_comuni.csv')
bande = pd.read_csv(PU / 'bande_distanza.csv')
modi = pd.read_csv(PU / 'modi_per_banda.csv')
tempi = pd.read_csv(PU / 'tempi_per_banda.csv', dtype={'tempo': str})
orari = pd.read_csv(PU / 'orari_entrata.csv', dtype={'orario': str})
usc = pd.read_csv(PU / 'uscite_top.csv')
sca = pd.read_csv(PU / 'scambi_vicini.csv')
mp = pd.read_csv(PU / 'mappa_comuni.csv')
odb = pd.read_csv(PU / 'od2016_bande_modi.csv')
fl = pd.read_csv(PU / 'flussi_milano.csv')

# ------------------------------------------------ controlli di coerenza con i totali dichiarati da ISTAT
check('2001 totale file = dichiarato', CTRL['2001_totale_file_tutti_i_record'], CTRL['2001_dichiarato_ISTAT'])
check('2011 totale record S = dichiarato', CTRL['2011']['S_cnt_tot'], CTRL['2011_dichiarato_ISTAT'])
check('2021 lavoro', CTRL['2021_lavoro_totale_file'], CTRL['2021_dichiarato_ISTAT']['lavoro'])
check('2021 studio', CTRL['2021_studio_totale_file'], CTRL['2021_dichiarato_ISTAT']['studio'])
tm = fl[fl.direzione == 'entra'].groupby('anno')['n'].sum()
mm = modi[(modi.direzione == 'entra')].groupby('anno')['n'].sum()
for y in (1991, 2001, 2011):
    check(f'{y} entrata: somma dettaglio (mezzo noto) vs totale', round(float(mm[y])), round(float(tm[y])), tol=0.04 * float(tm[y]))

# ------------------------------------------------ riepilogo per la pagina
J = {'anni': [1991, 2001, 2011, 2021]}
J['totali'] = R['totali']
J['totali_per_motivo'] = R['totali_per_motivo']
J['quota_di_fuori_lavoro'] = R['quota_di_fuori_lavoro']
J['quota_milanesi_fuori_lavoro'] = R['quota_milanesi_fuori_lavoro']
J['serie'] = serie.round(4).to_dict('records')
J['gruppi'] = grp.round(0).to_dict('records')
J['top'] = [{'id': int(r.pro_com), 'nome': r.nome, 'uts': r.uts, 'km': None if pd.isna(r.km) else float(r.km),
             'min': None if pd.isna(r.min_strada) else float(r.min_strada), 'pop': None if pd.isna(r.pop_2021) else int(r.pop_2021),
             'n': {y: int(getattr(r, f'n_{y}')) for y in (1991, 2001, 2011, 2021)}, 'lav21': int(r.lavoro_2021), 'stu21': int(r.studio_2021)} for r in top.itertuples()]
J['bande'] = bande.round(0).to_dict('records')
J['distanze'] = R['distanze']
J['modi'] = modi[modi.direzione.isin(['entra', 'interno'])].round(0).to_dict('records')
J['tempi'] = tempi[tempi.direzione.isin(['entra', 'interno'])].round(0).to_dict('records')
J['orari'] = orari.round(0).to_dict('records')
J['uscite'] = [{'id': int(r.pro_com), 'nome': r.nome, 'uts': r.uts, 'n': {y: int(getattr(r, f'n_{y}')) for y in (1991, 2001, 2011, 2021)}} for r in usc.itertuples()]
J['scambi'] = [{'id': int(r.pro_com), 'nome': r.nome, 'entra': {y: int(getattr(r, f'entra_{y}')) for y in (1991, 2001, 2011, 2021)},
                'esce': {y: int(getattr(r, f'esce_{y}')) for y in (1991, 2001, 2011, 2021)}} for r in sca.itertuples()]
J['assago'] = R['comuni_che_ricevono_piu_di_quanti_mandano']
J['od2016'] = {'tot': R['od2016'], 'righe': odb.to_dict('records'), 'quote': R['od2016_modi_entrata']}
J['mezzo_non_indicato_quota'] = R['mezzo_non_indicato_quota']
J['non_agganciato_quota'] = R['non_agganciato_quota']
J['controlli'] = {'2001_solo_spostati_mercoledi': CTRL['2001_totale_solo_spostati_mercoledi'], '2001_tutti': CTRL['2001_totale_file_tutti_i_record'],
                  '2011_estero_S': CTRL['2011']['S_cnt_estero'], '2011_tot': CTRL['2011']['S_cnt_tot']}
J['comuni_lombardi'] = R['comuni_lombardi']
J['comuni_lombardi_con_flussi_2021'] = R['comuni_lombardi_con_flussi_2021']
json.dump(J, open(OUT / 'riepilogo.json', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'), default=float)

# ------------------------------------------------ poligoni dei comuni lombardi
meta, fids, geoms, fields = pyogrio.raw.read(P / 'raw/istat_codici/x/Limiti2021_g/Com2021_g/Com2021_g.shp')
g = pd.DataFrame({k: v for k, v in zip(meta['fields'], fields)})
g['geometry'] = shapely.from_wkb(geoms)
g = g[g['COD_REG'] == 3].copy()
g['pro_com'] = g['PRO_COM_T'].astype(int)
from pyproj import Transformer
_tr = Transformer.from_crs('EPSG:32632', 'EPSG:4326', always_xy=True)
g['geometry'] = [shapely.ops.transform(_tr.transform, x).simplify(0.0004, preserve_topology=True) for x in g['geometry']]
mpi = mp.set_index('pro_com')
feats = []
for r in g.itertuples():
    if r.pro_com not in mpi.index:
        continue
    m = mpi.loc[r.pro_com]
    geom = shapely.set_precision(r.geometry, 0.0001)
    if geom.is_empty:
        continue
    q = [None if pd.isna(m[f'quota_{y}']) else round(float(m[f'quota_{y}']) * 100, 1) for y in (1991, 2001, 2011, 2021)]
    e = [int(m[f'entra_{y}']) for y in (1991, 2001, 2011, 2021)]
    t = [None if pd.isna(m[f'tot_{y}']) else int(round(m[f'tot_{y}'])) for y in (1991, 2001, 2011, 2021)]
    props = {'i': int(r.pro_com), 'n': m['nome'], 'u': m['sigla'], 'p': int(m['pop_2021']), 'e': e, 'q': q, 't': t,
             'k': None if pd.isna(m['km']) else float(m['km']), 'm': None if pd.isna(m['min']) else float(m['min'])}
    feats.append({'type': 'Feature', 'properties': props, 'geometry': mapping(geom)})
gj = {'type': 'FeatureCollection', 'features': feats}


def rnd(o):
    if isinstance(o, float):
        return round(o, 4)
    if isinstance(o, (list, tuple)):
        return [rnd(x) for x in o]
    if isinstance(o, dict):
        return {k: rnd(v) for k, v in o.items()}
    return o


for f in gj['features']:
    f['geometry']['coordinates'] = rnd(f['geometry']['coordinates'])
json.dump(gj, open(OUT / 'comuni.geojson', 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))
check('comuni lombardi nel geojson', len(feats), 1506)

# ------------------------------------------------ csv scaricabili
for nome in ('serie_totali', 'origini_gruppi', 'top_comuni', 'bande_distanza', 'modi_per_banda', 'tempi_per_banda', 'orari_entrata',
             'uscite_top', 'scambi_vicini', 'od2016_bande_modi'):
    shutil.copy(PU / f'{nome}.csv', OUT / f'{nome}.csv')
mp.to_csv(OUT / 'comuni_lombardia.csv', index=False)
f2 = fl.copy()
f2['comune'] = f2['altro'].map(lambda c: com['nome'].get(c) if c in com.index else ('non agganciato' if c == -1 else ''))
f2 = f2.rename(columns={'altro': 'pro_com_2021'})[['anno', 'motivo', 'direzione', 'pro_com_2021', 'comune', 'n']]
f2 = f2.groupby(['anno', 'motivo', 'direzione', 'pro_com_2021', 'comune'], as_index=False)['n'].sum()
f2['n'] = f2['n'].round(0).astype(int)
f2.to_csv(OUT / 'flussi_milano.csv', index=False)
tot = sum(p.stat().st_size for p in OUT.iterdir())
print('dimensione cartella data:', round(tot / 1e6, 2), 'MB', {p.name: round(p.stat().st_size / 1e3) for p in OUT.iterdir()})
if AVV:
    print('AVVISI:', AVV)
