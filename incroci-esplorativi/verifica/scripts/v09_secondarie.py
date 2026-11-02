"""G, H, M, N, O, P, Q (e L con i soli alberghi)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
from scipy.spatial import cKDTree
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 300)
L = open(os.path.join(OUT, 'secondarie.log'), 'w', encoding='utf8')
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); L.write(s + '\n'); L.flush()
n = pd.read_csv(os.path.join(OUT, 'nil_tabella_D.csv'))
c = pd.read_csv(p('censimenti', 'pulito', 'indicatori_NIL.csv'))
for an in [2011, 2021, 2023]:
    n[f'fam_{an}'] = n.id_nil.map(c[c.anno == an].set_index('nil').famiglie_comp_medio_approx)
    n[f'fame_{an}'] = n.id_nil.map(c[c.anno == an].set_index('nil').famiglie_comp_medio_esatto)
for eid in ELEZ_POL:
    t = eid.split('-')[0]; e = elezione(eid).set_index('id_nil')
    n[f'q_sx|{t}'] = n.id_nil.map(e.q_sx); n[f'q_pd|{t}'] = n.id_nil.map(e.q_Centrosinistra); n[f'q_si|{t}'] = n.id_nil.map(e.q_Sinistra); n[f'q_dx|{t}'] = n.id_nil.map(e.q_dx)
# ==== G
say('===== G')
rows = []
for eid in ELEZ_POL:
    t = eid.split('-')[0]
    y = f'q_sx|{t}'; fx = 'fam_2011' if eid < 'zz' and t.endswith(('2016', '2018', '2019')) else 'fam_2021'
    a = analisi(n, fx, y, CTRL, B=800); a0 = analisi(n, 'fam_2023', y, CTRL, B=300); a1 = analisi(n, fx, y, CTRL + ['laur_oggi', 'quota_stranieri'], B=300); s0 = stats.spearmanr(n[fx], n[y]).statistic
    rows.append(dict(el=t, fx=fx, sempl=round(s0, 3), **{k: a[k] for k in ['n', 'r', 'lo', 'hi', 'r_senza5', 'r_senza5_avverso']}, r_fam23=a0['r'], piu_laur_stran=a1['r'], q_pd=analisi(n, fx, f'q_pd|{t}', CTRL, B=50)['r'], q_si=analisi(n, fx, f'q_si|{t}', CTRL, B=50)['r']))
G = pd.DataFrame(rows); say(G.to_string()); G.to_csv(os.path.join(OUT, 'G.csv'), index=False)
say('Spearman ampiezza famiglie 2011-2021', round(stats.spearmanr(n.fam_2011, n.fam_2021).statistic, 3), '2011-2023', round(stats.spearmanr(n.fam_2011, n.fam_2023).statistic, 3), 'con stranieri', round(stats.spearmanr(n.fam_2023, n.quota_stranieri).statistic, 3), 'con laureati', round(stats.spearmanr(n.fam_2023, n.laur_oggi).statistic, 3))
# differenza 2021 contro 2024 appaiata
rng = np.random.default_rng(SEED); d = n
Zc = d[CTRL].values
for a_, b_ in [('comunali_consiglio_2021', 'camera_2022'), ('comunali_consiglio_2016', 'europee_2024'), ('camera_2018', 'camera_2022')]:
    df = []
    for _ in range(1000):
        i = rng.integers(0, len(d), len(d))
        df.append(parz(d.fam_2021.values[i], d[f'q_sx|{b_}'].values[i], Zc[i]) - parz(d.fam_2021.values[i], d[f'q_sx|{a_}'].values[i], Zc[i]))
    say(f'differenza {b_} - {a_} con famiglie 2021: {parz(d.fam_2021.values, d[f"q_sx|{b_}"].values, Zc) - parz(d.fam_2021.values, d[f"q_sx|{a_}"].values, Zc):+.3f} IC', np.round(np.percentile(df, [2.5, 97.5]), 3))
# ==== H
say('\n===== H')
lav = pd.read_csv(p('docs', 'lavoro', 'data', 'nil_lavoro.csv'))
for an in [2011, 2021, 2023]:
    n[f'gap_{an}'] = n.id_nil.map(lav[lav.anno == an].set_index('nil').gap_occ_mf)
for g_ in ['gap_2023', 'gap_2021', 'gap_2011']:
    for y in ['aff_netta', 'aff_cam22', 'aff_com21', 'aff_eur24']:
        a = analisi(n, g_, y, CTRL, B=800); say(f'{g_} {y:10s} sempl {stats.spearmanr(n[g_], n[y]).statistic:+.2f} parz {fmt(a)}')
    a = analisi(n, g_, 'aff_netta', CTRL + ['laur_oggi'], B=800); say(f'  + laureati {fmt(a)}')
    a = analisi(n, g_, 'aff_netta', CTRL + ['laur_oggi', 'quota_stranieri'], B=800); say(f'  + laureati + stranieri {fmt(a)}')
say('Spearman gap_2023 con laureati', round(stats.spearmanr(n.gap_2023, n.laur_oggi).statistic, 2), 'reddito', round(stats.spearmanr(n.gap_2023, n.reddito_2024).statistic, 2), 'stranieri', round(stats.spearmanr(n.gap_2023, n.quota_stranieri).statistic, 2), 'gap 2011-2023', round(stats.spearmanr(n.gap_2011, n.gap_2023).statistic, 2))
# ==== M
say('\n===== M')
pn = pd.read_csv(p('beni-confiscati', 'pulito', 'per_nil.csv'))
im = pd.read_csv(p('beni-confiscati', 'pulito', 'immobili_anbsc_milano.csv'), low_memory=False)
co = pd.read_csv(p('beni-confiscati', 'pulito', 'comune_ds147_milano.csv'), low_memory=False)
say('tipi Comune', co.tipo.value_counts().to_dict()); say('tipi ANBSC', im.tipo.value_counts().to_dict())
ed = json.load(open(p('docs', 'beni-confiscati', 'data', 'edifici.json'), encoding='utf8'))
ed = pd.DataFrame([dict(nil=e['nil'], cu=e.get('cu', 0), ad=e.get('ad', 0)) for e in ed])
nm = n.set_index('nil').id_nil
ed['id_nil'] = ed.nil.map(nm)
say('edifici', len(ed), 'senza NIL>=3000', int(ed.id_nil.isna().sum()))
def conta(s):
    return n.id_nil.map(s).fillna(0)
n['bc_comune'] = conta(co.groupby('id_nil').size()); n['bc_anbsc'] = conta(im.groupby('id_nil').size()); n['bc_edifici'] = conta(ed.groupby('id_nil').size())
n['bc_abitaz'] = conta(co[co.tipo == 'abitazione'].groupby('id_nil').size()) + 0
com_tipi = [t for t in co.tipo.unique() if 'negozio' in str(t) or 'commerc' in str(t) or 'laborator' in str(t)]; n['bc_negozi'] = conta(co[co.tipo.isin(com_tipi)].groupby('id_nil').size())
com2 = [t for t in im.tipo.unique() if 'negozio' in str(t) or 'commerc' in str(t) or 'laborator' in str(t)]; n['bc_negozi_anbsc'] = conta(im[im.tipo.isin(com2)].groupby('id_nil').size())
for k in ['bc_comune', 'bc_anbsc', 'bc_edifici', 'bc_abitaz', 'bc_negozi', 'bc_negozi_anbsc']:
    n[k + '_x1000'] = n[k] / n.residenti * 1000
    n[k + '_km2'] = n[k] / n.area_km2
    n[k + '_si'] = (n[k] > 0).astype(float)
ris = pd.read_csv(p('docs', 'ristoranti', 'data', 'nil.csv'), sep=';').set_index('id_nil')
for k in ['in_piano_per_1000ab', 'osm_per_1000ab', 'in_piano_per_km2']:
    n[k] = n.id_nil.map(ris[k])
say('NIL con zero beni:', {k: int((n[k] == 0).sum()) for k in ['bc_comune', 'bc_anbsc', 'bc_edifici', 'bc_negozi']})
rows = []
for x in ['bc_comune_x1000', 'bc_anbsc_x1000', 'bc_edifici_x1000', 'bc_edifici_km2', 'bc_comune_si', 'bc_edifici_si', 'bc_negozi_x1000', 'bc_negozi_anbsc_x1000', 'bc_abitaz_x1000']:
    for y in ['in_piano_per_1000ab', 'osm_per_1000ab', 'in_piano_per_km2']:
        a = analisi(n, x, y, CTRL, B=500)
        rows.append(dict(x=x, y=y, sempl=round(stats.spearmanr(n[x], n[y]).statistic, 3), **{k: a[k] for k in ['n', 'r', 'lo', 'hi', 'r_senza5', 'r_senza5_avverso']}))
M = pd.DataFrame(rows); say(M.to_string()); M.to_csv(os.path.join(OUT, 'M.csv'), index=False)
a = analisi(n, 'bc_edifici_x1000', 'in_piano_per_1000ab', CTRL + ['laur_oggi', 'q_aire'], B=500); say('Edifici, locali per 1000, + laureati, AIRE:', fmt(a))
# NIL grandi: i locali sono una funzione della densità di negozi
# ==== N
say('\n===== N')
ab = pd.read_csv(p('affitti-brevi', 'pulito', 'nil_riepilogo.csv'))
ver = pd.read_csv(p('docs', 'verde', 'data', 'nil_verde.csv'), sep=';').set_index('id_nil')
e24 = pd.read_csv(p('popolazione', 'pulito', 'eta_nil_anno_indicatori.csv')); e24 = e24[e24.anno == 2024].set_index('id_nil')
ab = ab.set_index('nil')
n['air100'] = n.id_nil.map(ab.annunci_per_100_abitazioni); n['air_int'] = n.id_nil.map(ab.case_intere_recensite_12m_per_100_abitazioni); n['air1000'] = n.id_nil.map(ab.annunci_per_1000_residenti); n['air_picc'] = n.id_nil.map(ab.piccolo_denominatore)
n['gioco_n'] = n.id_nil.map(ver.gioco_n); n['gioco_m2'] = n.id_nil.map(ver.gioco_m2); n['n014'] = n.id_nil.map(e24.n_0_14)
n['g_x1000'] = n.gioco_n / n.residenti * 1000; n['g_km2'] = n.gioco_n / n.area_km2; n['g_xb'] = n.gioco_n / n.n014 * 1000; n['gm2_xb'] = n.gioco_m2 / n.n014; n['gm2_ab'] = n.gioco_m2 / n.residenti
gg = json.load(open(p('verde', 'raw', 'comune_ds724', 'ds724_aree_gioco.geojson'), encoding='utf8'))
kx = 111.32 * np.cos(np.radians(45.46)) * 1000; ky = 110.57 * 1000
def verts(g):
    t = g['type']; co_ = g['coordinates']
    if t == 'Point': return [co_]
    if t == 'Polygon': return [q for r_ in co_ for q in r_]
    if t == 'MultiPolygon': return [q for po in co_ for r_ in po for q in r_]
    if t == 'LineString': return co_
    return []
vx = []
for f in gg['features']:
    if f.get('geometry'):
        vx += [(q[0] * kx, q[1] * ky) for q in verts(f['geometry'])]
vx = np.array(vx); say('vertici aree gioco', len(vx), 'poligoni', len(gg['features']))
cv = pd.read_csv(p('citta-15-minuti', 'out', 'civici_tempi.csv'), usecols=['RESIDENZIALE', 'ID_NIL', 'lon', 'lat'], low_memory=False)
say('RESIDENZIALE valori', cv.RESIDENZIALE.value_counts().head(4).to_dict())
rv = cv[cv.RESIDENZIALE.astype(str).str.upper().isin(['1', '1.0', 'S', 'SI', 'TRUE'])] if cv.RESIDENZIALE.astype(str).str.upper().isin(['1', '1.0', 'S', 'SI', 'TRUE']).sum() > 1000 else cv
tree = cKDTree(vx); dd_, _ = tree.query(np.column_stack([rv.lon * kx, rv.lat * ky]))
rv = rv.assign(dg=dd_)
g_ = rv.groupby('ID_NIL').dg
n['dg_med'] = n.id_nil.map(g_.median()); n['dg_300'] = n.id_nil.map(rv.assign(x=rv.dg <= 300).groupby('ID_NIL').x.mean() * 100)
for x in ['g_x1000', 'g_km2', 'g_xb', 'gm2_xb', 'gm2_ab', 'dg_med', 'dg_300']:
    for y in ['air100', 'air_int']:
        d = n[n.air_picc != True]
        a = analisi(d, y, x, CTRL, B=500); say(f'{x:8s} con {y:8s} sempl {stats.spearmanr(d[x], d[y], nan_policy="omit").statistic:+.2f} parz {fmt(a)}')
a = analisi(n[n.air_picc != True], 'air100', 'g_xb', CTRL + ['laur_oggi', 'q_aire'], B=500); say('per bambino + laureati, AIRE', fmt(a))
# per bambino è meccanico? i NIL con Airbnb hanno pochi bambini
say('Spearman air100 con quota 0-14', round(stats.spearmanr(n.air100, n.n014 / n.residenti, nan_policy='omit').statistic, 2), 'distanza', round(stats.spearmanr(n.air100, n.dist_duomo, nan_policy='omit').statistic, 2), 'densità', round(stats.spearmanr(n.air100, n.densita_ab_km2, nan_policy='omit').statistic, 2))
# ==== O
say('\n===== O')
e = pd.read_csv(p('popolazione', 'pulito', 'eta_nil_anno_indicatori.csv'))
Pi = e.pivot_table(index='id_nil', columns='anno', values='n_0_14')
for a_, b_ in [(2014, 2024), (2019, 2024), (2009, 2014), (2004, 2009), (2014, 2019)]:
    n[f'k_{a_}_{b_}'] = n.id_nil.map((Pi[b_] / Pi[a_] - 1) * 100)
n['q014_2014'] = n.id_nil.map(e[e.anno == 2014].set_index('id_nil').q_0_14 * 100)
sc = pd.read_csv(p('scuole', 'pulito', 'nil_iscritti_variazione_2015_2024.csv'), sep=';').dropna(subset=['id_nil']); sc['id_nil'] = sc.id_nil.astype(int)
sg = sc.groupby('id_nil')[['iscritti_2015', 'iscritti_2024']].sum(); sg = sg[sg.iscritti_2015 >= 100]
n['alunni'] = n.id_nil.map((sg.iscritti_2024 / sg.iscritti_2015 - 1) * 100)
cr = pd.read_csv(p('affitti-brevi', 'pulito', 'crescita_nil.csv')).set_index('nil_id')
n['air_r19'] = n.id_nil.map(cr.annunci_con_recensione_2019); n['air_r25'] = n.id_nil.map(cr.annunci_con_recensione_2025)
ab23 = ab.abitazioni_2023; n['abit'] = n.id_nil.map(ab23); n['air_cresc'] = (n.air_r25 - n.air_r19) / n.abit * 100
qq = pd.read_csv(p('quartieri-che-cambiano', 'out', 'indicatori_nil.csv')).set_index('id_nil'); n['costr'] = n.id_nil.map(qq.costruzioni_100)
n['resvar'] = n.id_nil.map((e.pivot_table(index='id_nil', columns='anno', values='residenti')[2024] / e.pivot_table(index='id_nil', columns='anno', values='residenti')[2014] - 1) * 100)
d = n[n.air_picc != True]
for y in ['k_2014_2024', 'k_2019_2024', 'k_2014_2019', 'alunni', 'k_2009_2014', 'k_2004_2009']:
    for x in ['air100', 'air_cresc']:
        cc = CTRL + ['q014_2014']
        a = analisi(d, x, y, cc, B=500); a2 = analisi(d, x, y, cc + ['costr'], B=300); a3 = analisi(d, x, y, cc + ['costr', 'quota_stranieri', 'laur_oggi'], B=300)
        say(f'{x:9s} {y:12s} sempl {stats.spearmanr(d[x], d[y], nan_policy="omit").statistic:+.2f} parz {fmt(a)} | +costruzioni {a2["r"]:+.2f} | +stran,laur {a3["r"]:+.2f}')
# ==== P
say('\n===== P')
n['air100f'] = n.air100
VAR = {'reddito_2024': 'reddito', 'laur_oggi': 'laureati', 'eta_media': 'età', 'quota_stranieri': 'stranieri (controllo)', 'smrTT|2012-2019': 'SMR', 'aff_netta': 'affluenza netta', 'aff_com21': 'aff comunali 21', 'q_sx|comunali_consiglio_2021': 'sx comunali 21', 'q_dx|camera_2022': 'dx camera 22', 'prezzo_2026_reale': 'prezzo', 'air100f': 'Airbnb', 'in_piano_per_1000ab': 'locali', 'densita_ab_km2': 'densità', 'indice': 'indice D', 'gap': 'scarto indice-reddito'}
XY = n[['cx', 'cy']].values
g = json.load(open(p('docs', 'elezioni', 'data', 'nil.geojson'), encoding='utf8'))
vt = {}
ckx = 111.32 * np.cos(np.radians(45.46)); cky = 110.57
for f in g['features']:
    co_ = f['geometry']['coordinates']; rings = co_ if f['geometry']['type'] == 'Polygon' else [r_ for po in co_ for r_ in po]
    vt[f['properties']['n']] = np.array([(q[0] * ckx, q[1] * cky) for r_ in rings for q in r_])
ids = n.id_nil.values; m_ = len(ids); adj = [[] for _ in range(m_)]
for i in range(m_):
    ti = cKDTree(vt[ids[i]])
    for j in range(i + 1, m_):
        dmin = ti.query(vt[ids[j]])[0].min()
        if dmin < .25:
            adj[i].append(j); adj[j].append(i)
say('grado medio adiacenza (entro 250 m)', round(np.mean([len(a_) for a_ in adj]), 1))
mun = n.municipio.astype(int).values; sizes = pd.Series(mun).value_counts().values; say('NIL per municipio', dict(pd.Series(mun).value_counts().sort_index()))
def eta2(v, lab):
    gm = v.mean(); ssb = sum(((lab == k).sum() * (v[lab == k].mean() - gm) ** 2) for k in np.unique(lab)); return ssb / ((v - gm) ** 2).sum()
rng = np.random.default_rng(SEED)
def casuale():
    lab = np.zeros(m_, int); perm = rng.permutation(m_); st = 0
    for k, s_ in enumerate(sizes):
        lab[perm[st:st + s_]] = k; st += s_
    return lab
def contigua():
    for _ in range(300):
        lab = -np.ones(m_, int); ok = True
        order = rng.permutation(len(sizes))
        for k in order:
            free = np.where(lab < 0)[0]
            if len(free) == 0:
                ok = False; break
            # seme: NIL libero con meno vicini liberi (evita isole)
            nf = [sum(lab[q] < 0 for q in adj[i]) for i in free]; s0 = free[int(np.argmin(np.array(nf) + rng.random(len(free))))]
            grp = [s0]; lab[s0] = k
            while len(grp) < sizes[k]:
                fr = list({q for i in grp for q in adj[i] if lab[q] < 0})
                if not fr:
                    break
                q = fr[rng.integers(len(fr))]; lab[q] = k; grp.append(q)
            if len(grp) < sizes[k]:
                ok = False; break
        if ok and (lab >= 0).all():
            return lab
    return None
CAS = [casuale() for _ in range(5000)]
CON = []
for _ in range(1500):
    l_ = contigua()
    if l_ is not None:
        CON.append(l_)
say('partizioni contigue trovate', len(CON))
rows = []
for k, nm_ in VAR.items():
    x = n[k]; m = x.notna().values
    v = x.rank().values[m] if False else x.rank().values
    vv = pd.Series(v)
    def e_(lab):
        return eta2(v[m], lab[m])
    e0 = e_(mun); ec = np.array([e_(l_) for l_ in CAS]); eg = np.array([e_(l_) for l_ in CON])
    rows.append(dict(var=nm_, n=int(m.sum()), eta2_municipi=round(e0, 3), casuali_media=round(ec.mean(), 3), p_cas=round((ec >= e0).mean(), 4), contigui_media=round(eg.mean(), 3), contigui_p95=round(np.percentile(eg, 95), 3), p_cont=round((eg >= e0).mean(), 3)))
P_ = pd.DataFrame(rows); say(P_.to_string()); P_.to_csv(os.path.join(OUT, 'P.csv'), index=False)
# ==== Q
say('\n===== Q')
a = pd.read_csv(os.path.join(OUT, 'ds27_cl.csv')); dec = pd.read_csv(p('speranza-vita', 'pulito', 'decessi_nil_anno_genere.csv')); ist = pd.read_csv(p('speranza-vita', 'pulito', 'decessi_citta_anno_cl_sesso.csv'))
a0 = a.groupby(['anno', 'id_nil', 'cl_eta', 'sesso']).res.sum().reset_index()
def py(y):
    c_ = a0[a0.anno == y].set_index(['id_nil', 'cl_eta', 'sesso']).res
    if y == 2012: return c_
    return c_.add(a0[a0.anno == y - 1].set_index(['id_nil', 'cl_eta', 'sesso']).res, fill_value=0) / 2
Em = {}; Em_std = {}; Ob = {}
base_rate = None
# tasso di riferimento fisso: 2016-2019 per l'eccesso assoluto
rr = []
for y in range(2016, 2020):
    Pp = py(y).groupby(['cl_eta', 'sesso']).sum(); rr.append((ist[ist.anno == y].set_index(['cl_eta', 'sesso']).decessi, Pp))
rate_ref = sum(d_ for d_, _ in rr) / sum(p_ for _, p_ in rr)
scale_ref = sum(dec[dec.anno.between(2016, 2019)].decessi) / sum((py(y).reset_index().merge(rate_ref.rename('r').reset_index(), on=['cl_eta', 'sesso']).eval('res*r').sum()) for y in range(2016, 2020))
for y in range(2013, 2025):
    Pu = py(y).reset_index()
    D_ = ist[ist.anno == y].set_index(['cl_eta', 'sesso']).decessi; city = py(y).groupby(['cl_eta', 'sesso']).sum(); rt = (D_ / city).rename('r').reset_index()
    x = Pu.merge(rt, on=['cl_eta', 'sesso']); x['e'] = x.res * x.r
    Oy = dec[dec.anno == y].groupby('id_nil').decessi.sum()
    E_ = x.groupby('id_nil').e.sum(); E_ *= Oy.sum() / E_.sum()
    Em[y] = E_; Ob[y] = Oy
    x2 = Pu.merge(rate_ref.rename('r').reset_index(), on=['cl_eta', 'sesso']); x2['e'] = x2.res * x2.r * scale_ref
    Em_std[y] = x2.groupby('id_nil').e.sum()
ids70 = n.id_nil.values
def eccesso(y, baseyrs):
    O = Ob[y].reindex(ids70).values.astype(float); E = Em[y].reindex(ids70).values
    Ob_b = sum(Ob[k].reindex(ids70).values for k in baseyrs).astype(float); Eb = sum(Em[k].reindex(ids70).values for k in baseyrs)
    smr_b = Ob_b / Eb; Ex = E * smr_b; Ex *= O.sum() / Ex.sum()   # chiude i totali: conta solo la differenza tra NIL
    var = Ex + Ex ** 2 / Ob_b
    z = (O - Ex) / np.sqrt(var); X2 = (z ** 2).sum()
    return dict(y=y, O=int(O.sum()), X2=round(X2, 1), df=len(O) - 1, phi=round(X2 / (len(O) - 1), 2), p=round(stats.chi2.sf(X2, len(O) - 1), 5), n_z2=int((np.abs(z) > 1.96).sum()), attese_z2=round(.05 * len(O), 1), sd_rapp=round(np.std(O / Ex), 3), sd_rumore=round(np.sqrt(np.mean(var / Ex ** 2)), 3), r_min=round((O / Ex).min(), 2), r_max=round((O / Ex).max(), 2)), z, O / Ex, Ex
res = []
for y, by in [(2017, [2013, 2014, 2015, 2016]), (2018, [2014, 2015, 2016, 2017]), (2019, [2015, 2016, 2017, 2018]), (2020, [2016, 2017, 2018, 2019]), (2021, [2016, 2017, 2018, 2019]), (2022, [2016, 2017, 2018, 2019]), (2023, [2016, 2017, 2018, 2019]), (2024, [2016, 2017, 2018, 2019])]:
    r_, z_, ra, Ex = eccesso(y, by); res.append(r_)
    if y == 2020:
        z20, ra20, Ex20 = z_, ra, Ex
Q_ = pd.DataFrame(res); say(Q_.to_string()); Q_.to_csv(os.path.join(OUT, 'Q.csv'), index=False)
# Assoluto: rispetto a 2016-2019 senza chiudere al totale
O20 = Ob[2020].reindex(ids70).values.astype(float); Eabs = Em_std[2020].reindex(ids70).values; Ob_b = sum(Ob[k].reindex(ids70).values for k in range(2016, 2020)).astype(float); Eb = sum(Em_std[k].reindex(ids70).values for k in range(2016, 2020)); sm = Ob_b / Eb
Ex_abs = Eabs * sm; ra_abs = O20 / Ex_abs
say('Eccesso assoluto per NIL: città', round(O20.sum() / Ex_abs.sum(), 3), 'quantili', np.round(np.percentile(ra_abs, [0, 10, 50, 90, 100]), 2), 'NIL con eccesso>0', int((ra_abs > 1).sum()), 'NIL con z>1.96 rispetto a nessun eccesso', int((((O20 - Ex_abs) / np.sqrt(Ex_abs + Ex_abs ** 2 / Ob_b)) > 1.96).sum()))
n['ecc20'] = ra20; n['z20'] = z20; n['ex20'] = Ex20
say('Più alti:', n.sort_values('ecc20', ascending=False)[['nil', 'ecc20', 'z20', 'ex20']].head(8).round(2).values.tolist())
say('Più bassi:', n.sort_values('ecc20')[['nil', 'ecc20', 'z20', 'ex20']].head(6).round(2).values.tolist())
# correzione per test multipli (Benjamini-Hochberg)
pv = 2 * stats.norm.sf(np.abs(z20)); o_ = np.argsort(pv); thr = .05 * (np.arange(len(pv)) + 1) / len(pv); ok = np.where(pv[o_] <= thr)[0]; say('Sopravvivono a BH 5%:', (len(ok) and ok.max() + 1), list(n.nil.values[o_][:(ok.max() + 1 if len(ok) else 0)]))
for x in ['ita_q85p', 'ita_q80p', 'rapp85', 'reddito_2024', 'laur_oggi', 'densita_ab_km2', 'dist_duomo', 'smrTT|2016-2019', 'aff_netta', 'quota_stranieri']:
    if x in n:
        say(f' ecc20 con {x:18s} Spearman {stats.spearmanr(n.ecc20, n[x], nan_policy="omit").statistic:+.2f}')
say(' ecc20, 85+ a parità:', fmt(analisi(n, 'ita_q85p', 'ecc20', ['dist_duomo', 'reddito_2024', 'densita_ab_km2'], B=800)))
say(' ecc20, senza i NIL con <300 attesi:', int((n.ex20 >= 300).sum()), 'sd rapporti', round(n[n.ex20 >= 300].ecc20.std(), 3))
XY2 = n[['cx', 'cy']].values; Dm = np.sqrt(((XY2[:, None] - XY2[None]) ** 2).sum(-1)); vv = z20 - z20.mean(); W = (Dm < 2.5) & (Dm > 0); I = (W * np.outer(vv, vv)).sum() / W.sum() / (vv ** 2).mean()
rng = np.random.default_rng(SEED); pm = []
for _ in range(2000):
    s_ = rng.permutation(vv); pm.append((W * np.outer(s_, s_)).sum() / W.sum() / (s_ ** 2).mean())
say(' Moran z20 entro 2,5 km', round(I, 3), 'p perm', round((np.array(pm) >= I).mean(), 3))
# Persistenza: 2020 e 2021
r21, z21, ra21, _ = eccesso(2021, [2016, 2017, 2018, 2019]); say(' Spearman ecc 2020-2021', round(stats.spearmanr(ra20, ra21).statistic, 3))
# ==== L alberghi
say('\n===== L, provincia, solo alberghi')
pm_ = pd.read_csv(p('turisti', 'pulito', 'provincia_mensile.csv'), low_memory=False)
al = pm_[(pm_.tipo_struttura == 'alberghiero') & pm_.tipo_provenienza.isin(['italia_regione', 'estero'])].groupby(['anno', 'mese']).presenze.sum()
to = pm_[(pm_.tipo_struttura == 'totale') & pm_.tipo_provenienza.isin(['italia_regione', 'estero'])].groupby(['anno', 'mese']).presenze.sum()
say('Alberghi provincia per anno', al.groupby('anno').sum().to_dict(), ' totale provincia', to.groupby('anno').sum().to_dict())
air = pd.read_csv(p('docs', 'aeroporti', 'data', 'mensile_tre_aeroporti.csv'), sep=';'); A = air.pivot_table(index=['anno', 'mese'], columns='aeroporto', values='passeggeri', aggfunc='sum')
tur = pd.read_csv(p('turisti', 'pulito', 'milano_mensile_totale.csv')).set_index(['anno', 'mese']).presenze
D = A.join(al.rename('alb'), how='inner').join(tur.rename('tot_comune')).join(to.rename('tot_prov')); D.index = pd.PeriodIndex([f'{a_}-{m:02d}' for a_, m in D.index], freq='M').to_timestamp()
say('mesi alberghi', D.alb.notna().sum(), D.alb.dropna().index.min().date(), D.alb.dropna().index.max().date())
def resid(S, idx, keep):
    y = np.log(S.values[keep]); i = idx[keep]; t = np.arange(len(S))[keep]
    X = np.column_stack([np.ones(keep.sum()), pd.get_dummies(i.month, drop_first=True).values.astype(float), t, t ** 2.])
    return pd.Series(y - X @ np.linalg.lstsq(X, y, rcond=None)[0], index=i)
def rmix(a_, b_, k=4, B=4000):
    a_, b_ = a_.align(b_, join='inner'); r0 = np.corrcoef(a_, b_)[0, 1]; n_ = len(a_); rng = np.random.default_rng(SEED); bs = []
    for _ in range(B):
        s_ = rng.integers(0, n_ - k + 1, n_ // k + 1); ii = np.concatenate([np.arange(q, q + k) for q in s_])[:n_]; bs.append(np.corrcoef(a_.values[ii], b_.values[ii])[0, 1])
    return r0, np.percentile(bs, [2.5, 97.5]), n_
for lab, keep in {'2022-04..2025-12': D.index >= '2022-04-01', '2022-04..2024-12': (D.index >= '2022-04-01') & (D.index <= '2024-12-01'), '2023-01..2025-12': D.index >= '2023-01-01', '2019-01..2019-06 + 2022-04..': (D.index >= '2022-04-01') | (D.index <= '2019-06-01')}.items():
    keep = np.asarray(keep) & D.alb.notna().values
    for ser in ['alb', 'tot_comune', 'tot_prov']:
        rp = resid(D[ser], D.index, keep)
        say(f'{lab:30s} {ser:10s} ' + ' | '.join(f"{c_} {rmix(rp, resid(D[c_], D.index, keep))[0]:+.2f} {np.round(rmix(rp, resid(D[c_], D.index, keep))[1], 2)}" for c_ in ['Linate', 'Bergamo', 'Malpensa']) + f' n={keep.sum()}')
n.to_csv(os.path.join(OUT, 'nil_tabella_finale.csv'), index=False)
L.close()
