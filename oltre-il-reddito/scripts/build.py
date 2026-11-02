"""Oltre il reddito: genera docs/oltre-il-reddito/data/ dai file originali dei filoni.

Uso:  python -I -X utf8 C:\\Users\\davide\\Desktop\\ClaudeTower\\milano-in-dati\\oltre-il-reddito\\scripts\\build.py

Legge solo file locali del progetto (nessuna rete). Scrive:
  docs/oltre-il-reddito/data/riepilogo.json   tutti i numeri della pagina, con l'origine
  docs/oltre-il-reddito/data/quartieri.csv    una riga per quartiere (70), separatore ; e virgola decimale
  oltre-il-reddito/out/controlli.txt          log dei controlli contro i valori del rapporto

Il calcolo dell'indice, delle correlazioni parziali e dell'affluenza ripete quello di
incroci-esplorativi/verifica/scripts/ (vc.py, v06_D.py, v05_C.py), ma parte dai file originali dei filoni
(non dalle tabelle intermedie) e non usa le colonne con difetti noti elencate in testa a
incroci-esplorativi/RAPPORTO.md.
"""
import json
import math
import os
import sys

import numpy as np
import pandas as pd
from scipy import stats

R = r'C:\Users\davide\Desktop\ClaudeTower\milano-in-dati'
DATA = os.path.join(R, 'docs', 'oltre-il-reddito', 'data')
LOCAL = os.path.join(R, 'oltre-il-reddito', 'out')
os.makedirs(DATA, exist_ok=True)
os.makedirs(LOCAL, exist_ok=True)
SEED = 20261102
SOGLIA = 3000
DUOMO = (45.4642, 9.1900)
CTRL = ['dist_duomo', 'eta_media', 'densita_ab_km2']  # + reddito o indice, a seconda della domanda
LOG = open(os.path.join(LOCAL, 'controlli.txt'), 'w', encoding='utf8')


def say(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    LOG.write(s + '\n')
    LOG.flush()


def p(*a):
    return os.path.join(R, *a)


# ---------------------------------------------------------------- funzioni statistiche (come vc.py)
def rk(x):
    return pd.Series(x).rank(method='average').values


def _res(y, Z):
    if Z is None or Z.shape[1] == 0:
        return y - y.mean()
    A = np.column_stack([np.ones(len(y)), Z])
    b, *_ = np.linalg.lstsq(A, y, rcond=None)
    return y - A @ b


def parz(x, y, Z=None):
    """Correlazione parziale sui ranghi (Spearman a parità dei controlli Z)."""
    rx, ry = rk(x), rk(y)
    rz = np.column_stack([rk(Z[:, j]) for j in range(Z.shape[1])]) if Z is not None and Z.shape[1] > 0 else None
    ex, ey = _res(rx, rz), _res(ry, rz)
    d = np.sqrt((ex ** 2).sum() * (ey ** 2).sum())
    return float((ex * ey).sum() / d) if d > 0 else float('nan')


def parz_df(d, x, y, ctrl):
    dd = d.dropna(subset=[x, y] + list(ctrl))
    Z = dd[list(ctrl)].values.astype(float) if ctrl else None
    return parz(dd[x].values.astype(float), dd[y].values.astype(float), Z)


# ---------------------------------------------------------------- base: 70 quartieri
def geometrie():
    g = json.load(open(p('docs', 'elezioni', 'data', 'nil.geojson'), encoding='utf8'))
    kx = 111.32 * math.cos(math.radians(DUOMO[0]))
    ky = 110.57
    rows = []
    for f in g['features']:
        geom = f['geometry']
        polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
        sx = sy = sa = 0.0
        for poly in polys:
            ring = [((c[0] - DUOMO[1]) * kx, (c[1] - DUOMO[0]) * ky) for c in poly[0]]
            x = np.array([c[0] for c in ring])
            y = np.array([c[1] for c in ring])
            cr = x[:-1] * y[1:] - x[1:] * y[:-1]
            A = cr.sum() / 2
            if abs(A) < 1e-12:
                cx, cy, a = x.mean(), y.mean(), 0.0
            else:
                cx, cy, a = ((x[:-1] + x[1:]) * cr).sum() / (6 * A), ((y[:-1] + y[1:]) * cr).sum() / (6 * A), abs(A)
            sx += cx * a
            sy += cy * a
            sa += a
        rows.append(dict(id_nil=int(f['properties']['n']), dist_duomo=math.hypot(sx / sa, sy / sa)))
    return pd.DataFrame(rows)


e = pd.read_csv(p('popolazione', 'pulito', 'eta_nil_anno_indicatori.csv'))
b = e[e.anno == 2024][['id_nil', 'nil', 'residenti', 'eta_media', 'densita_ab_km2']].copy()
b = b.merge(geometrie(), on='id_nil', how='left')
q = pd.read_csv(p('quartieri-che-cambiano', 'out', 'indicatori_nil.csv'))
b = b.merge(q[['id_nil', 'reddito_2024', 'prezzo_2026_reale']], on='id_nil', how='left')
c = pd.read_csv(p('censimenti', 'pulito', 'indicatori_NIL.csv'))
for an in (2021, 2023):
    s = c[c.anno == an].set_index('nil')
    b[f'laur_{an}'] = b.id_nil.map(s.quota_laureati_su_residenti)
b['laur_oggi'] = b[['laur_2021', 'laur_2023']].mean(axis=1)
b = b[b.residenti >= SOGLIA].copy().reset_index(drop=True)
say('Quartieri con almeno', SOGLIA, 'residenti (2024):', len(b))

# lavoro 2011 (censimento)
lav = pd.read_csv(p('docs', 'lavoro', 'data', 'nil_lavoro.csv'))
b['occ_2011'] = b.id_nil.map(lav[lav.anno == 2011].set_index('nil').tasso_occ)
b['disocc_2011'] = b.id_nil.map(lav[lav.anno == 2011].set_index('nil').tasso_disocc)
# censimento 2011 per sezione: m2 a persona (A44/P1), quota proprieta' (A47 / (A46+A47+A48))
s = pd.read_csv(p('censimenti', 'pulito', 'sezioni_2011.csv'), low_memory=False)
keyc = [k for k in s.columns if k.upper().startswith('SEZ')][0]
s['sez'] = s[keyc].astype(str).str.replace(r'\.0$', '', regex=True).str[-7:].astype(int)
sa = pd.read_csv(p('censimenti', 'pulito', 'sezioni_armonizzate.csv'), usecols=['sez', 'anno', 'nil'], low_memory=False)
s = s.merge(sa[sa.anno == 2011], on='sez', how='inner')
g = s.groupby('nil')[['A44', 'A46', 'A47', 'A48', 'P1']].sum()
b['mq_persona_2011'] = b.id_nil.map(g.A44 / g.P1)
b['q_proprieta_2011'] = b.id_nil.map(g.A47 / (g.A46 + g.A47 + g.A48) * 100)
cp = pd.read_csv(p('docs', 'case-popolari', 'data', 'nil.csv'), sep=';')
b['aler'] = b.id_nil.map(cp.set_index('id_nil').canone_ALER_2016_per_abitazione_euro)

# affluenza
idx = json.load(open(p('docs', 'elezioni', 'data', 'index.json'), encoding='utf8'))


def elez(eid):
    d = json.load(open(p('docs', 'elezioni', 'data', 'nil', eid + '.json'), encoding='utf8'))
    return pd.DataFrame([dict(id_nil=int(k), e=v.get('e', np.nan), vt=v.get('vt', np.nan)) for k, v in d['p'].items()]).set_index('id_nil')


EL = {'cam22': 'camera_2022-09-25', 'com21': 'comunali_consiglio_2021-10-03', 'eur24': 'europee_2024-06-08'}
for k, eid in EL.items():
    x = elez(eid)
    b['e_' + k] = b.id_nil.map(x.e)
    b['vt_' + k] = b.id_nil.map(x.vt)
    b['aff_' + k] = b['vt_' + k] / b['e_' + k] * 100
# stessa sostituzione del ricontrollo: voti diviso gli elettori della Camera 2022 (senza residenti all'estero)
b['aff_com21_netta'] = b.vt_com21 / b.e_cam22 * 100
b['aff_eur24_netta'] = b.vt_eur24 / b.e_cam22 * 100

# mortalita': osservati e attesi 2022-2024, tutti i sessi (speranza-vita, standardizzazione indiretta)
sm = pd.read_csv(p('speranza-vita', 'pulito', 'nil_smr_e0.csv'))
for fin, tag in (('2022-2024', '2224'), ('2012-2019', '1219')):
    t = sm[(sm.finestra == fin) & (sm.sesso == 'T')].set_index('id_nil')
    b['O_' + tag] = b.id_nil.map(t.osservati)
    b['E_' + tag] = b.id_nil.map(t.attesi)
    b['smr_' + tag] = b.id_nil.map(t.smr)
bandiere = pd.read_csv(p('speranza-vita', 'pulito', 'nil_bandiere_residenze.csv')).set_index('id_nil')
smax = sm[(sm.finestra == '2012-2019') & (sm.sesso == 'T')].set_index('id_nil')
# stessa regola della pagina speranza-vita: cautela se i decessi delle donne superano di molto quelli degli uomini (Morivione)
b['cautela'] = b.nil.str.strip().eq('Morivione')
say('Controllo SMR: O/E coincide con smr?', bool(np.allclose(b.O_2224 / b.E_2224, b.smr_2224, rtol=1e-3)))

# ---------------------------------------------------------------- 1. affluenza e mortalita'
r1 = {}
r1['n'] = len(b)
r1['spearman_grezzo'] = float(stats.spearmanr(b.aff_cam22, b.smr_2224).statistic)
r1['parz_4controlli'] = parz_df(b, 'aff_cam22', 'smr_2224', CTRL + ['reddito_2024'])
r1['parz_con_laureati'] = parz_df(b, 'aff_cam22', 'smr_2224', CTRL + ['reddito_2024', 'laur_oggi'])
r1['parz_senza_morivione'] = parz_df(b[~b.cautela], 'aff_cam22', 'smr_2224', CTRL + ['reddito_2024'])
# dentro lo stesso CAP (CAP dominante del quartiere, solo CAP con almeno due quartieri)
cc = pd.read_csv(p('quartieri-che-cambiano', 'out', 'collegamento_cap_nil.csv')).dropna(subset=['ID_NIL'])
cc['id_nil'] = cc.ID_NIL.astype(int)
dom = cc.sort_values('quota_nil').groupby('id_nil').tail(1).set_index('id_nil')
b['cap_dom'] = b.id_nil.map(dom.CAP)
gg = b[b.groupby('cap_dom').cap_dom.transform('size') >= 2].copy()
ex = gg.aff_cam22 - gg.groupby('cap_dom').aff_cam22.transform('mean')
ey = gg.smr_2224 - gg.groupby('cap_dom').smr_2224.transform('mean')
r1['stesso_cap_n'] = int(len(gg))
r1['stesso_cap_pearson'] = float(np.corrcoef(ex, ey)[0, 1])
r1['stesso_cap_spearman'] = float(stats.spearmanr(ex, ey).statistic)
# misura piu' prudente: media di otto elezioni (come nel ricontrollo), contro la mortalita' 2012-2019
MAIN = ['comunali_consiglio_2016-06-05', 'camera_2018-03-04', 'regionali_consiglio_2018-03-04', 'europee_2019-05-26',
        'comunali_consiglio_2021-10-03', 'camera_2022-09-25', 'regionali_consiglio_2023-02-12', 'europee_2024-06-08']
zs = []
for eid in MAIN:
    x = elez(eid)
    a_ = b.id_nil.map(x.vt) / b.id_nil.map(x.e) * 100
    zs.append((a_ - a_.mean()) / a_.std())
b['aff_media8'] = pd.concat(zs, axis=1).mean(axis=1)
m8 = {}
for y, tag in (('smr_1219', '2012-2019'), ('smr_2224', '2022-2024')):
    m8[tag] = dict(a_parita=parz_df(b, 'aff_media8', y, CTRL + ['reddito_2024']), con_laureati=parz_df(b, 'aff_media8', y, CTRL + ['reddito_2024', 'laur_oggi']))
gg2 = b[b.groupby('cap_dom').cap_dom.transform('size') >= 2]
for y, tag in (('smr_1219', '2012-2019'), ('smr_2224', '2022-2024')):
    ex2 = gg2.aff_media8 - gg2.groupby('cap_dom').aff_media8.transform('mean')
    ey2 = gg2[y] - gg2.groupby('cap_dom')[y].transform('mean')
    m8[tag]['stesso_cap_pearson'] = float(np.corrcoef(ex2, ey2)[0, 1])
    m8[tag]['stesso_cap_spearman'] = float(stats.spearmanr(ex2, ey2).statistic)
r1['media_otto_elezioni'] = m8
say('   media di otto elezioni:', json.dumps(m8))
# residenti all'estero al denominatore: le Comunali 2021 e le Europee 2024 con e senza
r1['estero'] = {}
for k, kn in (('com21', 'aff_com21'), ('eur24', 'aff_eur24')):
    r1['estero'][k] = dict(con_estero=parz_df(b, kn, 'smr_2224', CTRL + ['reddito_2024']),
                           senza_estero=parz_df(b, kn + '_netta', 'smr_2224', CTRL + ['reddito_2024']))
say('1. affluenza-mortalita:', json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r1.items() if k != 'estero'}), json.dumps(r1['estero']))

# ---------------------------------------------------------------- 2. tre gruppi per affluenza
b['terzo'] = pd.qcut(b.aff_cam22, 3, labels=['bassa', 'media', 'alta'])
terzi = []
for nm in ('bassa', 'media', 'alta'):
    t = b[b.terzo == nm]
    terzi.append(dict(gruppo=nm, n=int(len(t)), aff_min=float(t.aff_cam22.min()), aff_max=float(t.aff_cam22.max()), aff_media=float(t.aff_cam22.mean()),
                      O=int(t.O_2224.sum()), E=float(t.E_2224.sum()), rapporto=float(t.O_2224.sum() / t.E_2224.sum())))
say('2. terzi:', [(t['gruppo'], t['n'], t['O'], round(t['E'], 3), round(t['rapporto'], 3)) for t in terzi])

# ---------------------------------------------------------------- 3. dentro le fasce di reddito
b['fascia_red'] = pd.qcut(b.reddito_2024, 3, labels=['basso', 'medio', 'alto'])
b['meta_aff'] = b.groupby('fascia_red', observed=True).aff_cam22.transform(lambda s_: pd.qcut(s_, 2, labels=['bassa', 'alta']))
fasce = []
for fr in ('basso', 'medio', 'alto'):
    for ma in ('bassa', 'alta'):
        t = b[(b.fascia_red == fr) & (b.meta_aff == ma)]
        fasce.append(dict(reddito=fr, affluenza=ma, n=int(len(t)), aff_media=float(t.aff_cam22.mean()), red_media=float(t.reddito_2024.mean()),
                          O=int(t.O_2224.sum()), E=float(t.E_2224.sum()), rapporto=float(t.O_2224.sum() / t.E_2224.sum()), media_dei_rapporti=float(t.smr_2224.mean())))
say('3. fasce:', [(f['reddito'], f['affluenza'], f['n'], round(f['rapporto'], 3), round(f['media_dei_rapporti'], 3)) for f in fasce])
red_cut = [float(x) for x in pd.qcut(b.reddito_2024, 3, retbins=True)[1]]

# ---------------------------------------------------------------- 4. indice senza reddito (come v06_D.py)
IND = {'laur_oggi': 1, 'occ_2011': 1, 'disocc_2011': -1, 'prezzo_2026_reale': 1, 'mq_persona_2011': 1, 'q_proprieta_2011': 1, 'aler': -1}
NOMI_IND = {'laur_oggi': 'laureati (media 2021-2023)', 'occ_2011': 'occupazione 2011', 'disocc_2011': 'disoccupazione 2011 (al contrario)',
            'prezzo_2026_reale': 'prezzo delle case (quotazioni OMI)', 'mq_persona_2011': 'metri quadri di casa a persona (2011)',
            'q_proprieta_2011': 'quota di case di proprietà (2011)', 'aler': 'canone medio delle case ALER (al contrario)'}
assert b[list(IND)].notna().all().all(), 'indicatori mancanti'
Rk = pd.DataFrame({k: v * b[k].rank().values for k, v in IND.items()}, index=b.index)
Z = (Rk - Rk.mean()) / Rk.std()
b['indice'] = Z.mean(axis=1)
b['r_ind'] = b.indice.rank()
b['r_red'] = b.reddito_2024.rank()
b['gap'] = b.r_ind - b.r_red
b['pos_red'] = len(b) + 1 - b.r_red   # 1 = reddito piu' alto
b['pos_ind'] = len(b) + 1 - b.r_ind   # 1 = indice piu' alto
r4 = dict(spearman_indice_reddito=float(stats.spearmanr(b.indice, b.reddito_2024).statistic))
say('4. Spearman indice-reddito', round(r4['spearman_indice_reddito'], 3))
# pesi casuali
rng = np.random.default_rng(SEED)
NP = 5000
W = rng.dirichlet(np.ones(len(IND)), NP)
ind_mc = Z.values @ W.T
ranks_mc = pd.DataFrame(ind_mc).rank(axis=0).values            # (70, 5000)
gaps = ranks_mc - b.r_red.values[:, None]
absrank = pd.DataFrame(np.abs(gaps)).rank(axis=0, ascending=False).values
b['freq_top10'] = (absrank <= 10).mean(axis=1)
b['gap_p5'] = np.percentile(gaps, 5, axis=1)
b['gap_p95'] = np.percentile(gaps, 95, axis=1)
pos_mc = len(b) + 1 - ranks_mc
b['pos_ind_p5'] = np.percentile(pos_mc, 5, axis=1)
b['pos_ind_p95'] = np.percentile(pos_mc, 95, axis=1)
b['stesso_segno'] = (np.sign(gaps) == np.sign(b.gap.values)[:, None]).mean(axis=1)
stab = b[b.freq_top10 >= 0.8].sort_values('gap')
altri = b[b.freq_top10 < 0.8]
r4['pesi_casuali'] = dict(n_estrazioni=NP, soglia='tra i 10 quartieri con scarto maggiore in almeno l\'80% delle estrazioni',
                          stabili=[dict(nome=r.nil.strip(), freq_top10=float(r.freq_top10), pos_red=float(r.pos_red), pos_ind=float(r.pos_ind),
                                        pos_ind_p5=float(r.pos_ind_p5), pos_ind_p95=float(r.pos_ind_p95), stesso_segno=float(r.stesso_segno)) for r in stab.itertuples()],
                          altri_freq_max=float(altri.freq_top10.max()), altri_freq_max_nome=altri.loc[altri.freq_top10.idxmax(), 'nil'].strip(),
                          altri_ampiezza_mediana=float((altri.pos_ind_p95 - altri.pos_ind_p5).median()),
                          altri_ampiezza_max=float((altri.pos_ind_p95 - altri.pos_ind_p5).max()))
say('   stabili con 5.000 pesi casuali:', [(s_['nome'], round(s_['freq_top10'], 3), s_['pos_red'], s_['pos_ind']) for s_ in r4['pesi_casuali']['stabili']],
    '| massimo degli altri', round(r4['pesi_casuali']['altri_freq_max'], 3), r4['pesi_casuali']['altri_freq_max_nome'],
    '| ampiezza mediana p5-p95 posizione, altri', r4['pesi_casuali']['altri_ampiezza_mediana'])

# indice contro mortalita' (indice e' costruito SENZA mortalita' e SENZA affluenza)
for y, tag in (('smr_2224', '2022-2024'), ('smr_1219', '2012-2019')):
    r4['indice_a_parita_reddito_' + tag] = parz_df(b, 'indice', y, CTRL + ['reddito_2024'])
    r4['reddito_a_parita_indice_' + tag] = parz_df(b, 'reddito_2024', y, CTRL + ['indice'])
r4['indice_senza_laureati_a_parita_reddito_2022-2024'] = parz_df(b.assign(ind_nl=Z.drop(columns=['laur_oggi']).mean(axis=1)), 'ind_nl', 'smr_2224', CTRL + ['reddito_2024'])
r4['indice_grezzo_2022-2024'] = float(stats.spearmanr(b.indice, b.smr_2224).statistic)
r4['reddito_grezzo_2022-2024'] = float(stats.spearmanr(b.reddito_2024, b.smr_2224).statistic)
r4['affluenza_grezzo_2022-2024'] = float(stats.spearmanr(b.aff_cam22, b.smr_2224).statistic)
say('4. indice|reddito', {k: round(v, 3) for k, v in r4.items() if isinstance(v, float)})

# controllo contro il ricontrollo: SMR proprio del ricontrollo (solo per verifica, non e' un input della pagina)
sp = os.path.join(R, 'incroci-esplorativi', 'verifica', 'out', 'smr_propri.csv')
if os.path.exists(sp):
    smp = pd.read_csv(sp)
    t = smp[(smp.finestra == '2022-2024') & (smp['pop'] == 'T') & (smp.sesso == 'T')].set_index('id_nil')
    bb = b.copy()
    bb['smr_2224'] = bb.id_nil.map(t.smr)
    say('   (controllo con gli SMR del ricontrollo) indice|reddito', round(parz_df(bb, 'indice', 'smr_2224', CTRL + ['reddito_2024']), 3),
        'reddito|indice', round(parz_df(bb, 'reddito_2024', 'smr_2224', CTRL + ['indice']), 3),
        '| differenza massima fra i due SMR', round(float((bb.smr_2224 - b.smr_2224).abs().max()), 4))

# ---------------------------------------------------------------- tabella dei quartieri
tab = b.copy()
tab['nome'] = tab.nil.str.strip().replace({'Pta Romana': 'Porta Romana', "Citta' studi": 'Città Studi', "Monlue' - Ponte Lambro": 'Monluè - Ponte Lambro'})
rows = []
for r in tab.sort_values('nome').itertuples():
    rows.append(dict(i=int(r.id_nil), n=r.nome, res=int(r.residenti), red=round(float(r.reddito_2024)), aff=round(float(r.aff_cam22), 2),
                     O=int(r.O_2224), E=round(float(r.E_2224), 1), smr=round(float(r.O_2224 / r.E_2224), 4),
                     pr=float(r.pos_red), pi=float(r.pos_ind), c=int(bool(r.cautela))))
out = dict(
    generato='2 novembre 2026',
    n_quartieri=len(b), soglia_residenti=SOGLIA,
    quartieri=rows,
    affluenza_mortalita=r1,
    terzi=terzi, fasce=fasce, fasce_soglie_reddito=red_cut,
    indice=dict(indicatori=[dict(k=k, nome=NOMI_IND[k], verso=v) for k, v in IND.items()], **r4),
    citta_aff_media=float(b.aff_cam22.mean()),
    tot_O=int(b.O_2224.sum()), tot_E=float(b.E_2224.sum()),
)
json.dump(out, open(os.path.join(DATA, 'riepilogo.json'), 'w', encoding='utf8'), ensure_ascii=False, separators=(',', ':'))

# CSV scaricabile (separatore ; e virgola decimale, come gli altri filoni)
cs = pd.DataFrame(dict(id_nil=tab.id_nil, quartiere=tab.nome, residenti_2024=tab.residenti, reddito_medio_cap_2024=tab.reddito_2024.round(0),
                       affluenza_camera_2022=tab.aff_cam22.round(2), morti_osservate_2022_2024=tab.O_2224, morti_attese_2022_2024=tab.E_2224.round(1),
                       osservate_su_attese=(tab.O_2224 / tab.E_2224).round(3), posizione_per_reddito=tab.pos_red, posizione_per_indice_senza_reddito=tab.pos_ind,
                       da_leggere_con_cautela=tab.cautela.astype(int)))
cs = cs.sort_values('quartiere')
cs.to_csv(os.path.join(DATA, 'quartieri.csv'), sep=';', decimal=',', index=False, encoding='utf-8-sig')

# ---------------------------------------------------------------- controlli contro i valori attesi dal rapporto
say('\n=== CONTROLLI CONTRO IL RAPPORTO ===')
att = {'terzo bassa: osservate': (16913, terzi[0]['O']), 'terzo bassa: attese': (15661, round(terzi[0]['E'])),
       'terzo alta: osservate': (13445, terzi[2]['O']), 'terzo alta: attese': (14665, round(terzi[2]['E'])),
       'terzo bassa: +%': (8, round((terzi[0]['rapporto'] - 1) * 100)), 'terzo alta: -%': (-8, round((terzi[2]['rapporto'] - 1) * 100))}
for k, (a, v) in att.items():
    say(f'  {k:28s} atteso {a:>8} mio {v:>8} {"OK" if a == v else "DIVERSO"}')
say('  reddito basso, affluenza bassa (rapporto 1,15):', round(fasce[0]['rapporto'], 3), '| media dei rapporti', round(fasce[0]['media_dei_rapporti'], 3))
say('  reddito basso, affluenza alta  (rapporto 0,98):', round(fasce[1]['rapporto'], 3), '| media dei rapporti', round(fasce[1]['media_dei_rapporti'], 3))
say('  affluenza a parita (-0,68):', round(r1['parz_4controlli'], 3), '| grezza (-0,80):', round(r1['spearman_grezzo'], 3))
say('  con laureati (-0,45):', round(r1['parz_con_laureati'], 3), '| stesso CAP (-0,42): Pearson', round(r1['stesso_cap_pearson'], 3), 'Spearman', round(r1['stesso_cap_spearman'], 3))
say('  indice a parita di reddito (-0,61):', round(r4['indice_a_parita_reddito_2022-2024'], 3), '| reddito a parita di indice (-0,03):', round(r4['reddito_a_parita_indice_2022-2024'], 3))
LOG.close()
print('ok')
