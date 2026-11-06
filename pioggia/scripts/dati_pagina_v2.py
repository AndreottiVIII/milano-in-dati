"""Costruisce i file dati della pagina Pioggia (bozza v2).
Uso: python -I -X utf8 genera_dati.py <pioggia-e-caldo_dir> <uscita_data_dir>
Legge: raw/ecad_rr/blend_rr/RR_STAID000173.txt (ECA&D Milano 1858-2008), pulito/intermedi/P_orario.parquet (ARPA, CC0),
pulito/pioggia_giorni_ge40mm_verifica.csv, pulito/sensori_selezionati.csv, pulito/pioggia_anno_sensore.csv.
Scrive: meta.json, annuale.json, barcode.json, records.json, calendario/MM-DD.json, sensori/AAAA.json, stazioni.json
"""
import sys, os, json
import numpy as np, pandas as pd

B, OUT = sys.argv[1], sys.argv[2]
PU = os.path.join(B, 'pulito')
os.makedirs(os.path.join(OUT, 'calendario'), exist_ok=True)
os.makedirs(os.path.join(OUT, 'sensori'), exist_ok=True)


def js(path, obj):
    with open(path, 'w', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))


# ---------------- ECA&D Milano 1858-2008
e = pd.read_csv(os.path.join(B, 'raw/ecad_rr/blend_rr/RR_STAID000173.txt'), skiprows=20, skipinitialspace=True)
e.columns = [c.strip() for c in e.columns]
e['data'] = pd.to_datetime(e.DATE.astype(str), format='%Y%m%d')
e = e[e.data <= '2008-12-31']
e['mm'] = np.where((e.RR == -9999) | (e.Q_RR == 9), np.nan, e.RR / 10.0)
e['sosp'] = (e.Q_RR == 1)
print('ECA', e.data.min().date(), e.data.max().date(), 'mancanti', int(e.mm.isna().sum()), 'sospetti', int(e.sosp.sum()), 'valori', int(e.mm.notna().sum()))
eca = e.set_index('data').mm

# ---------------- ARPA: giornaliero per pluviometro
sel = pd.read_csv(os.path.join(PU, 'sensori_selezionati.csv'), dtype=str)
sel = sel[sel.tipologia == 'Precipitazione'].copy()
sel['km'] = sel.dist_duomo_km.astype(float)
nome = dict(zip(sel.idsensore, sel.nomestazione))
P = pd.read_parquet(os.path.join(PU, 'intermedi/P_orario.parquet'))
print('ARPA orario fino a', P.ora.max())
P['giorno'] = (P.ora - pd.Timedelta(minutes=10)).dt.floor('D')
D = P.groupby(['idsensore', 'giorno']).agg(mm=('mm', 'sum'), n=('mm', 'size')).reset_index()
D = D[D.n >= 20]
ver = pd.read_csv(os.path.join(PU, 'pioggia_giorni_ge40mm_verifica.csv'), dtype={'idsensore': str})
ver['giorno'] = pd.to_datetime(ver.giorno)
nc = ver[ver.stato == 'NON_CONFERMATO'][['idsensore', 'giorno']].assign(nc=1)
D = D.merge(nc, how='left', on=['idsensore', 'giorno'])
D['nc'] = D.nc.fillna(0).astype(int)
print('giorni-sensore', len(D), 'non confermati', int(D.nc.sum()))

MIL = ['5908', '8149', '14121', '9341', '2006', '5902', '4065', '19373']
Dm = D[D.idsensore.isin(MIL) & (D.nc == 0)]
comp = Dm.groupby('giorno').agg(mm=('mm', 'median'), n=('mm', 'size'))
comp = comp[comp.index >= '2009-01-01']
LAST = pd.Timestamp('2026-03-01')
comp = comp[comp.index < LAST]
print('composito', comp.index.min().date(), comp.index.max().date(), 'n giorni', len(comp), 'con <3 pluviometri', int((comp.n < 3).sum()), 'con 1', int((comp.n == 1).sum()))

# serie unica giornaliera: ECA fino al 2008, ARPA (mediana) dal 2009
idx = pd.date_range('1858-01-01', comp.index.max().normalize(), freq='D')
serie = pd.Series(np.nan, index=idx)
serie.loc[eca.index] = eca.values
serie.loc[comp.index] = comp.mm.values
fonte = pd.Series(0, index=idx)
fonte.loc[idx >= '2009-01-01'] = 1
nn = pd.Series(0, index=idx)
nn.loc[comp.index] = comp.n.values
sosp = pd.Series(False, index=idx)
sosp.loc[e.data.values] = e.sosp.values

# ---------------- annuale
FIN = 2025
ann = []
for y in range(1858, FIN + 1):
    s = serie[serie.index.year == y]
    val = s.dropna()
    ok = len(val) >= 330
    ann.append(dict(a=y, v=int(len(val)), ok=bool(ok), f=int(fonte[s.index[0]])))
    if len(val) == 0:
        continue
    imax = val.idxmax()
    ann[-1].update(tot=round(float(val.sum()), 1), g1=int((val >= 1).sum()), g10=int((val >= 10).sum()), g30=int((val >= 30).sum()),
                   mx=round(float(val.max()), 1), mxg=imax.strftime('%m-%d'))
okE = [a for a in ann if a['ok'] and a['a'] <= 2008]
media_eca = sum(a['tot'] for a in okE) / len(okE)
print('anni ok ECA', len(okE), 'media', round(media_eca, 1))
okAll = [a for a in ann if a['ok']]
print('anni non ok', [(a['a'], a['v']) for a in ann if not a['ok']])


# ---------------- barcode: una riga per anno, un carattere per giorno
def cls(v):
    if np.isnan(v):
        return '_'
    if v < 1:
        return '0'
    if v < 5:
        return '1'
    if v < 10:
        return '2'
    if v < 20:
        return '3'
    if v < 30:
        return '4'
    if v < 50:
        return '5'
    return '6'


bc = {}
for y in range(1858, FIN + 1):
    s = serie[serie.index.year == y]
    bc[str(y)] = ''.join(cls(v) for v in s.values)
js(os.path.join(OUT, 'barcode.json'), dict(legenda='_ manca; 0 meno di 1 mm; 1 da 1 a 5; 2 da 5 a 10; 3 da 10 a 20; 4 da 20 a 30; 5 da 30 a 50; 6 da 50', anni=bc))

# ---------------- siccita (giorni consecutivi con meno di 1 mm, senza buchi)
runs = []
cur = None
vals = serie.values
dates = serie.index
for i, v in enumerate(vals):
    if (not np.isnan(v)) and v < 1:
        if cur is None:
            cur = i
    else:
        if cur is not None:
            runs.append((cur, i - 1))
            cur = None
if cur is not None:
    runs.append((cur, len(vals) - 1))
runs = [r for r in runs if dates[r[1]] <= pd.Timestamp('2025-12-31')]
runs.sort(key=lambda r: r[1] - r[0], reverse=True)
secchi = [dict(da=dates[a].strftime('%Y-%m-%d'), a=dates[b].strftime('%Y-%m-%d'), g=int(b - a + 1)) for a, b in runs[:12]]
print('siccita', secchi[:8])

# ---------------- giorni piu piovosi (serie unica, 1858-2025)
sv = serie[serie.index <= '2025-12-31'].dropna().sort_values(ascending=False)
top = []
for d, v in sv.head(40).items():
    top.append(dict(g=d.strftime('%Y-%m-%d'), mm=round(float(v), 1), f=int(fonte[d]), n=int(nn[d]), s=bool(sosp[d])))
for t in top[:15]:
    print('top', t)

# ---------------- pluviometri entro 15 km dal Duomo (mappa e controlli)
vic = sel[(sel.km <= 15)].sort_values('km')
st = [dict(id=r.idsensore, nome=r.nomestazione, lat=float(r.lat), lng=float(r.lng), km=r.km, da=r.datastart[:10],
           a=(r.datastop[:10] if isinstance(r.datastop, str) else None)) for r in vic.itertuples()]
js(os.path.join(OUT, 'stazioni.json'), st)
ids = list(vic.idsensore)
Dv = D[D.idsensore.isin(ids)].copy()
Dv['y'] = Dv.giorno.dt.year
Dv['doy'] = Dv.giorno.dt.day_of_year - 1
for y, g in Dv.groupby('y'):
    if y < 1990:
        continue
    have = set(g.idsensore)
    sens = [i for i in ids if i in have]
    ndays = 366 if (y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)) else 365
    rows = []
    for i in sens:
        arr = [None] * ndays
        flag = []
        gi = g[g.idsensore == i]
        for r in gi.itertuples():
            arr[r.doy] = round(r.mm, 1)
            if r.nc:
                flag.append(int(r.doy))
        rows.append(dict(i=i, v=arr, x=flag))
    js(os.path.join(OUT, 'sensori', '%d.json' % y), dict(y=int(y), s=rows))
print('file sensori', len(os.listdir(os.path.join(OUT, 'sensori'))))

# ---------------- un file per anno: i millimetri di ogni giorno
os.makedirs(os.path.join(OUT, 'anni'), exist_ok=True)
for y in range(1858, FIN + 1):
    sy = serie[serie.index.year == y]
    js(os.path.join(OUT, 'anni', '%d.json' % y), dict(v=[None if np.isnan(x) else round(float(x), 1) for x in sy.values]))

# ---------------- calendario: un file per giorno del calendario
dd = serie[serie.index <= '2025-12-31']
for mm_ in range(1, 13):
    for d_ in range(1, 32):
        try:
            pd.Timestamp(2000, mm_, d_)
        except Exception:
            continue
        sub = dd[(dd.index.month == mm_) & (dd.index.day == d_)]
        js(os.path.join(OUT, 'calendario', '%02d-%02d.json' % (mm_, d_)),
           dict(y=[int(x) for x in sub.index.year], v=[None if np.isnan(x) else round(float(x), 1) for x in sub.values]))
print('calendario', len(os.listdir(os.path.join(OUT, 'calendario'))))

# ---------------- quota nelle 88 ore piu piovose (ARPA, pluviometri di Milano, anni completi)
A = pd.read_csv(os.path.join(PU, 'pioggia_anno_sensore.csv'), dtype={'idsensore': str})
Am = A[A.idsensore.isin(MIL) & A.anno_completo]
quota = dict(media=round(float(Am.quota_top1pct_ore.mean()), 3), min=round(float(Am.quota_top1pct_ore.min()), 3),
             max=round(float(Am.quota_top1pct_ore.max()), 3), n=int(len(Am)))
print('quota', quota)
c = Am[Am.anno.isin([2022, 2024])].pivot_table(index='idsensore', columns='anno', values='tot_mm').dropna()
conf = [dict(nome=nome[i], t22=round(float(r[2022])), t24=round(float(r[2024]))) for i, r in c.iterrows()]

casi = ['1999-10-21', '2000-03-22', '2007-09-26', '2009-07-07', '2018-05-16', '2024-09-05']

okx = okAll
secco = min(okx, key=lambda a: a['tot'])
umido = max(okx, key=lambda a: a['tot'])
dec = {}
for a in okx:
    dec.setdefault(a['a'] // 10 * 10, []).append(a)
decen = [dict(d=k, anni=len(v), tot=round(sum(x['tot'] for x in v) / len(v)), g1=round(sum(x['g1'] for x in v) / len(v), 1)) for k, v in sorted(dec.items())]
riep = dict(media_eca=round(media_eca, 1), anni_ok=len(okx), secco=dict(a=secco['a'], mm=secco['tot']), umido=dict(a=umido['a'], mm=umido['tot']),
            quota=quota, decenni=decen, conf=conf, secchi=secchi, top=top, casi=casi,
            tendenza_g1=dict(pend=-1.14, lo=-1.70, hi=-0.56, anni=151, da=1858, a=2008),
            ore=dict(anno=8760, top=88),
            # riferimenti indipendenti per i giorni della mappa: ECA&D Milano e NOAA GSOD Linate (pioggia-e-caldo/pulito/pioggia_ore_estreme_non_confermate.csv e docs/pioggia/data/riepilogo.json, casi)
            ref={'1999-10-21': dict(eca=68.0, linate=71.9), '2000-03-22': dict(eca=0.0, linate=0.0), '2007-09-26': dict(eca=15.4, linate=34.8), '2018-05-16': dict(eca=None, linate=20.1)})
js(os.path.join(OUT, 'records.json'), riep)
js(os.path.join(OUT, 'annuale.json'), dict(anni=ann))
js(os.path.join(OUT, 'meta.json'), dict(primo='1858-01-01', ultimo='2025-12-31', ultimo_anno=FIN, scaricato='2026-11-01', ecad_fino='2008-12-31',
                                         arpa_da='2009-01-01', giorni_ecad_sospetti=int(e.sosp.sum()), giorni_ecad_mancanti=int(e.mm.isna().sum()), arpa_nc=int(D.nc.sum())))


# ---------------- mappa: Milano (quartieri), comune e comuni vicini, in km dal Duomo
from shapely.geometry import shape, box, mapping
from shapely.ops import unary_union
DOCS = os.path.normpath(os.path.join(B, '..', 'docs'))
LAT0, LON0 = 45.46419, 9.19192
KX = 111.32 * np.cos(np.radians(LAT0)); KY = 110.57
def proj(geom):
    from shapely.ops import transform
    return transform(lambda x, y, z=None: ((np.array(x) - LON0) * KX, (np.array(y) - LAT0) * KY), geom)
def path(geom, tol):
    g = proj(geom).simplify(tol)
    polys = [g] if g.geom_type == 'Polygon' else list(g.geoms)
    out = []
    for p in polys:
        for ring in [p.exterior] + list(p.interiors):
            c = list(ring.coords)
            out.append('M' + 'L'.join('%.2f %.2f' % (x, -y) for x, y in c) + 'Z')
    return ''.join(out)
BOX = box(-17, -17, 17, 17)
nil = json.load(open(os.path.join(DOCS, 'medici-farmacie/data/nil.geojson'), encoding='utf8'))
com = json.load(open(os.path.join(DOCS, 'hinterland/data/comuni.geojson'), encoding='utf8'))
quartieri = [dict(n=f['properties']['n'], d=path(shape(f['geometry']), 0.03)) for f in nil['features']]
altri = []
mil = None
for f in com['features']:
    g = shape(f['geometry'])
    pg = proj(g)
    if f['properties'].get('g') == 'MILANO':
        mil = path(g, 0.03); continue
    if pg.intersects(BOX):
        altri.append(dict(n=f['properties']['n'], d=path(g, 0.06)))
js(os.path.join(OUT, 'mappa.json'), dict(note='km dal Duomo; x verso est, y verso sud (y gia invertito); Milano = confine del comune', milano=mil, quartieri=quartieri, comuni=altri,
   stazioni=[dict(id=x['id'], x=round((x['lng'] - LON0) * KX, 2), y=round(-(x['lat'] - LAT0) * KY, 2)) for x in st]))
print('mappa', len(quartieri), len(altri), os.path.getsize(os.path.join(OUT, 'mappa.json')))
