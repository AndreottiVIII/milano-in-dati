"""A: laureati contro reddito sul voto; stessa grana. B: laureati 1991."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 300)
L = open(os.path.join(OUT, 'A_B.log'), 'w', encoding='utf8')
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); L.write(s + '\n'); L.flush()

b = base()
red = pd.read_csv(p('voto-reddito', 'out', 'nil_reddito.csv'), encoding='utf-8-sig')
b = b.merge(red[['id_nil', 'reddito_2019_22_euro2025', 'n_cap', 'quota_cap_dominante']], on='id_nil', how='left')
b['laur_oggi'] = b[['laur_2021', 'laur_2023']].mean(axis=1)
for eid in ELEZ_POL:
    e = elezione(eid)
    t = eid.split('-')[0]
    for c in ['q_sx', 'q_dx', 'q_ce', 'q_m5', 'aff']:
        b[f'{c}|{t}'] = b.id_nil.map(e.set_index('id_nil')[c])
    b[f'q_sxce|{t}'] = b[f'q_sx|{t}'] + b[f'q_ce|{t}'].fillna(0)
    b[f'q_pd|{t}'] = b.id_nil.map((e.set_index('id_nil')['q_Centrosinistra']))
    b[f'q_dest|{t}'] = b.id_nil.map((e.set_index('id_nil')['q_Destra']))
    b[f'q_csx_sx|{t}'] = b.id_nil.map((e.set_index('id_nil')['q_Sinistra']))
    b[f'q_lega|{t}'] = b.id_nil.map((e.set_index('id_nil')['q_Lega']))
    b[f'q_cdx|{t}'] = b.id_nil.map((e.set_index('id_nil')['q_Centrodestra']))
n = nil3000(b)
say('NIL >=3000:', len(n))
C0 = ['dist_duomo', 'eta_media', 'densita_ab_km2']
rows = []
def corsa(n, xL, xR, etich, vars_=('q_sx', 'q_dx'), B=1000, extra=None):
    for eid in ELEZ_POL:
        t = eid.split('-')[0]
        for v in vars_:
            y = f'{v}|{t}'
            if y not in n or n[y].isna().all():
                continue
            cc = C0 + (extra or [])
            aL = analisi(n, xL, y, cc + [xR], B=B)
            aR = analisi(n, xR, y, cc + [xL], B=B)
            # differenza appaiata con bootstrap
            d = n.dropna(subset=[xL, xR, y] + cc)
            rng = np.random.default_rng(SEED)
            diff = []
            X = d[[xL, xR, y] + cc].values.astype(float)
            for _ in range(B):
                i = rng.integers(0, len(d), len(d)); x = X[i]
                diff.append(abs(parz(x[:, 0], x[:, 2], x[:, [1] + list(range(3, x.shape[1]))])) - abs(parz(x[:, 1], x[:, 2], x[:, [0] + list(range(3, x.shape[1]))])))
            lo, hi = np.percentile(diff, [2.5, 97.5])
            rows.append(dict(variante=etich, voto=v, elezione=t, n=aL['n'], r_laur=aL['r'], l_lo=aL['lo'], l_hi=aL['hi'], l_s5=aL['r_senza5'], l_s5a=aL['r_senza5_avverso'],
                             r_redd=aR['r'], r_lo=aR['lo'], r_hi=aR['hi'], r_s5=aR['r_senza5'], r_s5a=aR['r_senza5_avverso'], diff_abs=round(abs(aL['r']) - abs(aR['r']), 3), d_lo=round(lo, 3), d_hi=round(hi, 3)))

# semplici e combinati
say('\n--- correlazioni semplici (ranghi), laureati e reddito')
say(' laur-reddito', stats.spearmanr(n.laur_oggi, n.reddito_2024).statistic, ' laur-reddito 2019-22', stats.spearmanr(n.laur_oggi, n.reddito_2019_22_euro2025, nan_policy='omit').statistic, ' redd2024-redd1922', stats.spearmanr(n.reddito_2024, n.reddito_2019_22_euro2025, nan_policy='omit').statistic)
for eid in ELEZ_MAIN:
    t = eid.split('-')[0]
    say(t, 'sx~laur %.2f sx~redd %.2f | dx~laur %.2f dx~redd %.2f | ce~laur %.2f ce~redd %.2f | m5~laur %.2f m5~redd %.2f' % tuple(
        stats.spearmanr(n[a], n[f'{v}|{t}'], nan_policy='omit').statistic for v in ['q_sx', 'q_dx', 'q_ce', 'q_m5'] for a in ['laur_oggi', 'reddito_2024']))

corsa(n, 'laur_oggi', 'reddito_2024', 'base')
corsa(n, 'laur_oggi', 'reddito_2019_22_euro2025', 'reddito 2019-22')
corsa(n, 'laur_oggi', 'reddito_2024', 'con stranieri', extra=['quota_stranieri'])
corsa(n, 'laur_oggi', 'reddito_2024', 'famiglie alternative', vars_=('q_sxce', 'q_pd', 'q_dest', 'q_ce', 'q_m5'), B=500)
A = pd.DataFrame(rows); A.to_csv(os.path.join(OUT, 'A_confronto.csv'), index=False)
say(A[(A.variante == 'base')].drop(columns=['variante']).to_string())
say(A.groupby(['variante', 'voto'])[['r_laur', 'r_redd', 'diff_abs']].mean().round(3).to_string())

# ---- Stessa grana: laureati portati a CAP con la stessa matrice del reddito
cap = pd.read_csv(p('quartieri-che-cambiano', 'out', 'collegamento_cap_nil.csv'))
cap = cap.dropna(subset=['ID_NIL']); cap['id_nil'] = cap.ID_NIL.astype(int)
cap = cap.merge(b[['id_nil', 'residenti', 'laur_oggi', 'laur_1991']], on='id_nil')
cap['pes'] = cap.quota_nil * cap.residenti
capL = cap.groupby('CAP').apply(lambda g: pd.Series({'L_cap': np.average(g.laur_oggi, weights=g.pes), 'L91_cap': np.average(g.laur_1991, weights=g.pes), 'pes': g.pes.sum()}), include_groups=False).reset_index()
c2 = cap.merge(capL[['CAP', 'L_cap', 'L91_cap']], on='CAP')
sm = c2.groupby('id_nil').apply(lambda g: pd.Series({'laur_cap': np.average(g.L_cap, weights=g.quota_nil), 'laur91_cap': np.average(g.L91_cap, weights=g.quota_nil)}), include_groups=False).reset_index()
b2 = b.merge(sm, on='id_nil', how='left')
n2 = nil3000(b2)
say('\nRiduzione di grana: Spearman laureati NIL vs laureati sfocati su CAP', stats.spearmanr(n2.laur_oggi, n2.laur_cap, nan_policy='omit').statistic)
# controllo: la stessa sfocatura applicata a un reddito "vero" è impossibile; misuriamo quanto perde laureati
rows = []
corsa(n2, 'laur_cap', 'reddito_2024', 'laureati sfocati su CAP (n NIL)', B=500)
G = pd.DataFrame(rows); G.to_csv(os.path.join(OUT, 'A_grana_nil.csv'), index=False)
say(G.drop(columns=['variante']).to_string())
say(G.groupby('voto')[['r_laur', 'r_redd', 'diff_abs']].mean().round(3).to_string())
say('Laureati solo, senza reddito, perdita di capacità per sfocatura:')
for eid in ELEZ_MAIN:
    t = eid.split('-')[0]
    say(t, ' '.join(f"{v}: fine {stats.spearmanr(n2.laur_oggi, n2[f'{v}|{t}'], nan_policy='omit').statistic:+.2f} sfocato {stats.spearmanr(n2.laur_cap, n2[f'{v}|{t}'], nan_policy='omit').statistic:+.2f} reddito {stats.spearmanr(n2.reddito_2024, n2[f'{v}|{t}'], nan_policy='omit').statistic:+.2f}" for v in ['q_sx', 'q_dx']))

# ---- Livello CAP vero: voti dalle sezioni verso i CAP
vs = pd.read_csv(p('elezioni', 'pulito', 'voti_sezione.csv'), usecols=['elezione_id', 'sezione', 'lista', 'voti'], low_memory=False)
vs = vs[vs.elezione_id.isin(ELEZ_POL)]
fam = pd.read_csv(p('elezioni', 'famiglie_partiti.csv'), sep=';', engine='python', on_bad_lines='skip')
say('\nRighe famiglie', len(fam), 'colonne', list(fam.columns))
fam['anno_da'] = pd.to_numeric(fam.anno_da, errors='coerce'); fam['anno_a'] = pd.to_numeric(fam.anno_a, errors='coerce')
def famiglia(lista, anno):
    x = fam[fam.lista == lista]
    if len(x) == 0:
        return 'Altri'
    for r in x.itertuples():
        if (np.isnan(r.anno_da) or anno >= r.anno_da) and (np.isnan(r.anno_a) or anno <= r.anno_a):
            return r.famiglia
    return x.iloc[0].famiglia
vs['anno'] = vs.elezione_id.str.extract(r'_(\d{4})-')[0].astype(int)
mp = {(l, a): famiglia(l, a) for l, a in vs[['lista', 'anno']].drop_duplicates().itertuples(index=False)}
vs['fam'] = [mp[(l, a)] for l, a in zip(vs.lista, vs.anno)]
# controllo contro il JSON
idx = indice()
for eid in ['camera_2022-09-25', 'comunali_consiglio_2021-10-03', 'europee_2019-05-26']:
    j = [x for x in idx['elezioni'] if x['id'] == eid][0]
    agg = {}
    for (nm, fi), v in zip(j['par'], j['city']['v']):
        agg[j['fam'][fi]] = agg.get(j['fam'][fi], 0) + v
    mine = vs[vs.elezione_id == eid].groupby('fam').voti.sum().to_dict()
    say(eid, {k: (agg.get(k, 0), int(mine.get(k, 0))) for k in sorted(set(agg) | set(mine))})
sc = pd.read_csv(p('voto-reddito', 'out', 'sezione_cap.csv'), encoding='utf-8-sig')
capred = pd.read_csv(p('voto-reddito', 'out', 'cap_reddito.csv'), encoding='utf-8-sig')
capL = capL.rename(columns={'CAP': 'cap'})
capT = capred[['cap', 'reddito_2019_22_euro2025', 'reddito_2024_euro2025', 'contribuenti_2024']].merge(capL, on='cap', how='left')
# età e controlli al CAP con la stessa matrice
cc2 = pd.read_csv(p('quartieri-che-cambiano', 'out', 'collegamento_cap_nil.csv')).dropna(subset=['ID_NIL'])
cc2['id_nil'] = cc2.ID_NIL.astype(int)
cc2 = cc2.merge(b[['id_nil', 'residenti', 'eta_media', 'dist_duomo', 'densita_ab_km2']], on='id_nil'); cc2['pes'] = cc2.quota_nil * cc2.residenti
ctr = cc2.groupby('CAP').apply(lambda g: pd.Series({k: np.average(g[k], weights=g.pes) for k in ['eta_media', 'dist_duomo', 'densita_ab_km2']}), include_groups=False).reset_index().rename(columns={'CAP': 'cap'})
capT = capT.merge(ctr, on='cap', how='left').dropna()
say('CAP utilizzabili', len(capT))
rows = []
for eid in ELEZ_POL:
    t = eid.split('-')[0]
    x = vs[vs.elezione_id == eid].merge(sc[['sezione', 'cap', 'peso']], on='sezione')
    x['vp'] = x.voti * x.peso
    pv = x.pivot_table(index='cap', columns='fam', values='vp', aggfunc='sum').fillna(0)
    tot = pv.sum(axis=1)
    q = pd.DataFrame({'q_sx': sum(pv[c] for c in SX if c in pv) / tot * 100, 'q_dx': sum(pv[c] for c in DX if c in pv) / tot * 100}).reset_index()
    d = capT.merge(q, on='cap')
    d['nil'] = d.cap
    for v in ['q_sx', 'q_dx']:
        for lab, dd, xR in [('38cap', d, 'reddito_2024_euro2025'), ('38cap_r1922', d, 'reddito_2019_22_euro2025'), ('senza instabili', d[~d.cap.isin([20121, 20122, 20145])], 'reddito_2019_22_euro2025')]:
            cc = ['eta_media', 'dist_duomo']  # densità al CAP: pochi punti, due controlli
            aL = analisi(dd, 'L_cap', v, cc + [xR], B=500); aR = analisi(dd, xR, v, cc + ['L_cap'], B=500)
            rows.append(dict(el=t, voto=v, var=lab, n=aL['n'], r_laur=aL['r'], l_lo=aL['lo'], l_hi=aL['hi'], l_s5=aL['r_senza5'], r_redd=aR['r'], r_lo=aR['lo'], r_hi=aR['hi'], r_s5=aR['r_senza5'],
                             sp_laur=round(stats.spearmanr(dd.L_cap, dd[v]).statistic, 3), sp_red=round(stats.spearmanr(dd[xR], dd[v]).statistic, 3)))
CC = pd.DataFrame(rows); CC.to_csv(os.path.join(OUT, 'A_livello_CAP.csv'), index=False)
say(CC.to_string())
say(CC.groupby(['var', 'voto'])[['r_laur', 'r_redd', 'sp_laur', 'sp_red']].mean().round(3).to_string())

# ---- Dentro lo stesso CAP dominante: il reddito è costante per costruzione
cc3 = pd.read_csv(p('quartieri-che-cambiano', 'out', 'collegamento_cap_nil.csv')).dropna(subset=['ID_NIL'])
cc3['id_nil'] = cc3.ID_NIL.astype(int)
dom = cc3.sort_values('quota_nil').groupby('id_nil').tail(1)[['id_nil', 'CAP', 'quota_nil']].rename(columns={'CAP': 'cap_dom', 'quota_nil': 'q_dom'})
n3 = nil3000(b.merge(dom, on='id_nil', how='left'))
say('\nNIL con CAP dominante >=0.9:', (n3.q_dom >= .9).sum(), ' NIL per CAP dominante:', n3.groupby('cap_dom').size().describe().round(1).to_dict())
for eid in ELEZ_MAIN:
    t = eid.split('-')[0]
    out = []
    for v in ['q_sx', 'q_dx']:
        y = f'{v}|{t}'
        g = n3.dropna(subset=[y, 'laur_oggi'])
        g = g[g.groupby('cap_dom').cap_dom.transform('size') >= 2]
        ex = g.laur_oggi - g.groupby('cap_dom').laur_oggi.transform('mean'); ey = g[y] - g.groupby('cap_dom')[y].transform('mean')
        out.append(f"{v}: n={len(g)} r_entro_cap={np.corrcoef(ex, ey)[0, 1]:+.2f} spearman={stats.spearmanr(ex, ey).statistic:+.2f}")
    say(t, ' | '.join(out))

# ==== B
say('\n===== B: laureati 1991 a parità di laureati oggi')
# ricostruzioni del 1991
sa = pd.read_csv(p('censimenti', 'pulito', 'sezioni_armonizzate.csv'), low_memory=False)
s91 = sa[sa.anno == 1991][['sez', 'grad', 'edu_base', 'pop', 'a65p', 'a75p', 'nil', 'purezza_nil']].copy()
ass = s91.groupby('nil').agg(g=('grad', 'sum'), p=('pop', 'sum'), eb=('edu_base', 'sum')); ass['laur91_chk'] = ass.g / ass.p * 100
qa = pd.read_csv(p('censimenti', 'pulito', 'raccordo_quote_area_1991.csv')).rename(columns={'sezione': 'sez', 'nil': 'nil_a'})
m = s91.merge(qa, on='sez', how='left')
m['g_a'] = m.grad * m.quota_area; m['p_a'] = m['pop'] * m.quota_area; m['eb_a'] = m.edu_base * m.quota_area
ar = m.groupby('nil_a')[['g_a', 'p_a', 'eb_a']].sum(); ar['laur91_area'] = ar.g_a / ar.p_a * 100; ar['laurb91_area'] = ar.g_a / ar.eb_a * 100
s91['p90'] = s91['pop'] * (s91.purezza_nil < .9)
pur = s91.groupby('nil').agg(p90=('p90', 'sum'), p=('pop', 'sum')); pur['q_impuro'] = pur.p90 / pur.p
b['laur91_chk'] = b.id_nil.map(ass.laur91_chk); b['laur91_area'] = b.id_nil.map(ar.laur91_area); b['laurb91_area'] = b.id_nil.map(ar.laurb91_area); b['q_impuro91'] = b.id_nil.map(pur.q_impuro)
b['pop91_area'] = b.id_nil.map(ar.p_a)
var = pd.read_csv(p('censimenti', 'pulito', 'variazioni_NIL_1991_2023.csv'))
rcol = [c for c in var.columns if 'robust' in c.lower()][0]; ncol = [c for c in var.columns if c in ('nil', 'id_nil')][0]
b['robusto'] = b.id_nil.map(var.set_index(ncol)[rcol])
# età 1991 per controllo coorte
n = nil3000(b)
say('n', len(n), 'controllo: laur_1991 file vs ricalcolo', round((n.laur_1991 - n.laur91_chk).abs().max(), 4), ' vs per area Spearman', round(stats.spearmanr(n.laur_1991, n.laur91_area).statistic, 4),
    'scarto ass mediano', round((n.laur_1991 - n.laur91_area).abs().median(), 3), 'max', round((n.laur_1991 - n.laur91_area).abs().max(), 3))
say('NIL con >10% popolazione 1991 in sezioni impure:', (n.q_impuro91 > .1).sum(), ' robusti', int(n.robusto.sum()))
say('Spearman laur 1991-2001-2011-2021-2023:'); say(n[['laur_1991', 'laur_2001', 'laur_2011', 'laur_2021', 'laur_2023']].corr(method='spearman').round(3).to_string())
sens = [('reddito', CTRL), ]
rows = []
for eid in ELEZ_POL:
    t = eid.split('-')[0]
    for v in ['q_sx', 'q_dx', 'q_ce', 'aff']:
        y = f'{v}|{t}'
        if n[y].isna().all() or (v == 'q_ce' and 'comunali' in t):
            continue
        C = CTRL + ['laur_oggi']
        r0 = analisi(n, 'laur_1991', y, C, B=500)
        r1 = analisi(n, 'laur91_area', y, C, B=300)
        r2 = analisi(n[n.robusto == True], 'laur_1991', y, C, B=300)
        r3 = analisi(n[n.q_impuro91 <= .1], 'laur_1991', y, C, B=300)
        r4 = analisi(n, 'laur_1991', y, CTRL + ['laur_oggi', 'laur_2011'], B=300)
        r5 = analisi(n, 'laur_2001', y, C, B=300)
        r5b = analisi(n, 'laur_2011', y, C, B=300)
        r6 = analisi(n, 'laurb_1991', y, CTRL + ['laurb_2023'], B=300)
        r7 = analisi(n, 'laur_1991', y, CTRL + ['laur_oggi', 'quota_stranieri'], B=300)
        r8 = analisi(n, 'laur_1991', y, CTRL + ['laur_oggi', 'laur_2011', 'laur_2001'], B=300)
        rows.append(dict(el=t, voto=v, n=r0['n'], r=r0['r'], lo=r0['lo'], hi=r0['hi'], s5=r0['r_senza5'], s5a=r0['r_senza5_avverso'], top5=r0['top5'], area=r1['r'], robusti=r2['r'], n_rob=r2['n'], puri=r3['r'], n_puri=r3['n'], piu_2011=r4['r'], l2001=r5['r'], l2011=r5b['r'], su_base=r6['r'], c_stran=r7['r'], piu_2011_2001=r8['r']))
B_ = pd.DataFrame(rows); B_.to_csv(os.path.join(OUT, 'B_1991.csv'), index=False)
say(B_.drop(columns=['top5']).to_string())
say(B_.groupby('voto').mean(numeric_only=True).round(3).to_string())
# prova del rumore: se il 1991 fosse solo un proxy di "laureati oggi misurati male"
rng = np.random.default_rng(SEED)
y = 'q_sx|camera_2022'
say('\nProva di errore di misura (camera 2022): r parziale di laur_1991 se a laur_oggi si aggiunge rumore crescente')
sd = n.laur_oggi.std()
for fr in [0, .05, .1, .2, .3, .5]:
    rs = [parz(n.laur_1991.values, n[y].values, np.column_stack([n[c].values for c in CTRL] + [n.laur_oggi.values + rng.normal(0, fr * sd, len(n))])) for _ in range(200)]
    say(f' rumore {fr:.2f}sd r={np.mean(rs):+.3f}')
say('\nInversa: effetto di laureati oggi a parità di 1991 (stesse elezioni)')
for eid in ELEZ_MAIN:
    t = eid.split('-')[0]
    say(t, 'sx', fmt(analisi(n, 'laur_oggi', f'q_sx|{t}', CTRL + ['laur_1991'], B=300)), '| dx', fmt(analisi(n, 'laur_oggi', f'q_dx|{t}', CTRL + ['laur_1991'], B=300)))
n.to_csv(os.path.join(OUT, 'nil_tabella_AB.csv'), index=False)
L.close()
