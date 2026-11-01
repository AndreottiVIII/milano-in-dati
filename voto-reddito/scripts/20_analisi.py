"""Passo 2: voto e affluenza per sezione contro reddito del CAP (ecologico: nessun voto individuale e noto).

Unita: la sezione elettorale (1.238 sezioni col legame di ds939). Reddito della sezione = media dei redditi dei CAP
dei suoi civici, pesata per i civici (10_sezione_cap.py). Decili fissi: tagli sul reddito di sezione pesato per gli elettori
delle Comunali 2021 (stessi tagli per tutte le elezioni). Incertezza: bootstrap a grappoli, i grappoli sono i 38 CAP
(ogni sezione al suo CAP prevalente), 2.000 ripetizioni, intervallo 2,5-97,5 percentile.

Uso: python -I -X utf8 20_analisi.py <milano-in-dati> <voto-reddito>
"""
import sys, os, json, re
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

base, dest = sys.argv[1], sys.argv[2]
EL = os.path.join(base, 'elezioni')
OUT = os.path.join(dest, 'out')
NB = 2000
rng = np.random.default_rng(20261101)

cat = pd.read_csv(os.path.join(EL, 'pulito', 'elezioni.csv'), encoding='utf-8-sig')
ris = pd.read_csv(os.path.join(EL, 'pulito', 'risultati_sezione.csv'), encoding='utf-8-sig', low_memory=False)
voti = pd.read_csv(os.path.join(EL, 'pulito', 'voti_sezione.csv'), encoding='utf-8-sig', dtype={'lista': str}, low_memory=False)
fam = pd.read_csv(os.path.join(EL, 'famiglie_partiti.csv'), sep=';', encoding='utf-8-sig', dtype=str, keep_default_na=False)
W = pd.read_csv(os.path.join(OUT, 'sezione_cap.csv'))
CR = pd.read_csv(os.path.join(OUT, 'cap_reddito.csv')).set_index('cap')
WN = pd.read_csv(os.path.join(EL, 'pulito', 'sezione_nil.csv'), encoding='utf-8-sig')
NILR = pd.read_csv(os.path.join(OUT, 'nil_reddito.csv')).set_index('id_nil')
FRAG = pd.read_csv(os.path.join(EL, 'pulito', 'nil_controllo_popolazione.csv'), encoding='utf-8-sig')
FRAG_IDS = set(FRAG[FRAG.fragile == 1].id_nil.astype(int))
POPY = 2023
pop_c = pd.read_csv(os.path.join(base, 'popolazione', 'pulito', 'cittadinanze_nil_indicatori.csv'))
pop_e = pd.read_csv(os.path.join(base, 'popolazione', 'pulito', 'eta_nil_anno_indicatori.csv'))
POP = (pop_c[pop_c.anno == POPY].set_index('id_nil')[['residenti', 'quota_stranieri']]
       .join(pop_e[pop_e.anno == POPY].set_index('id_nil')[['q_65p', 'eta_media']]))

# ---- elezioni usate (anno >= 2016, nel sito; i file "candidati" e "presidente" non sono nel sito)
cat = cat[(cat.anno >= 2016) & (cat.nel_sito == 'si')].copy()
cat = cat[~cat.gruppo.isin(['municipali_consiglio'])]   # Municipi: stessa gente delle Comunali, pochi quesiti nuovi
ELE = cat.set_index('elezione_id')

SHORT_REF = {
    'ds1369': 'Trivellazioni 2016 (Si = fermare)', 'ds1370': 'Costituzionale Renzi-Boschi 2016 (Si = riforma)',
    'ds1371': 'Autonomia Lombardia 2017 (Si = piu autonomia)', 'ds1461': 'Taglio dei parlamentari 2020 (Si = taglio)',
    'ds1889': 'Giustizia 2022 - Incandidabilita', 'ds1890': 'Giustizia 2022 - Limitazione misure cautelari',
    'ds1891': 'Giustizia 2022 - Separazione funzioni', 'ds1892': 'Giustizia 2022 - Consigli giudiziari',
    'ds1893': 'Giustizia 2022 - Elezione CSM',
    'ds2930': 'Lavoro 2025 - Licenziamenti (Si = abrogare)', 'ds2931': 'Lavoro 2025 - Indennita licenziamento',
    'ds2932': 'Lavoro 2025 - Contratti a termine', 'ds2933': 'Lavoro 2025 - Sicurezza appalti',
    'ds2934': 'Cittadinanza 2025 (Si = 5 anni invece di 10)', 'ds2975': 'Giustizia 2026 (Si = separazione carriere)'}
GRP = {'comunali_consiglio': 'Comunali - Consiglio', 'comunali_sindaco': 'Comunali - Sindaco', 'comunali_ballottaggio': 'Comunali - Ballottaggio',
       'camera': 'Politiche - Camera', 'senato': 'Politiche - Senato', 'europee': 'Europee', 'regionali_consiglio': 'Regionali - Consiglio'}


def etich(r):
    if r.gruppo == 'referendum':
        return SHORT_REF[r.elezione_id.split('_')[-1]]
    return '%s %d' % (GRP[r.gruppo], r.anno)


ELE['etichetta2'] = [etich(r) for r in ELE.reset_index().itertuples()]

# ---- mappa lista -> famiglia (stessa regola di elezioni/scripts/16_aggrega.py)
rules = {}
for r in fam.itertuples():
    a = int(r.anno_da) if r.anno_da else -1
    b = int(r.anno_a) if r.anno_a else 9999
    rules.setdefault(r.lista, []).append((a, b, r.famiglia))


def fam_of(lista, anno):
    for a, b, f in rules.get(lista, []):
        if a <= anno <= b:
            return f
    return 'Altri'


voti = voti[voti.elezione_id.isin(ELE.index)].copy()
voti['anno'] = voti.elezione_id.map(ELE.anno)
ris = ris[ris.elezione_id.isin(ELE.index)].copy()
kk = voti[['lista', 'anno']].drop_duplicates()
kk['famiglia'] = [fam_of(l, a) for l, a in zip(kk.lista, kk.anno)]
voti = voti.merge(kk, on=['lista', 'anno'], how='left')

# ---- tabella sezioni: reddito, decile
inc_cap = CR.reddito_2019_22_euro2025
Wm = W.copy()
Wm['inc'] = Wm.cap.map(inc_cap)
sez = Wm.groupby('sezione').apply(lambda g: pd.Series({'inc': float((g.peso * g.inc).sum()),
                                                        'cap_prev': int(g.loc[g.prevalente == 1, 'cap'].iloc[0]),
                                                        'peso_prev': float(g.loc[g.prevalente == 1, 'peso'].iloc[0])}), include_groups=False)
sezioni = sez.index.values
SIDX = {s: i for i, s in enumerate(sezioni)}
S = len(sezioni)
inc_s = sez.inc.values
cap_list = sorted(CR.index)
CIDX = {c: i for i, c in enumerate(cap_list)}
cl = np.array([CIDX[c] for c in sez.cap_prev])          # grappolo (CAP prevalente) di ogni sezione
# matrice pesi sezione x CAP
WS = np.zeros((S, len(cap_list)))
for r in W.itertuples():
    WS[SIDX[r.sezione], CIDX[r.cap]] = r.peso
inc_c = np.array([inc_cap[c] for c in cap_list])
x_c = inc_c / 10000.0
lx_c = np.log2(inc_c)


def wquantile_cuts(x, w, qs):
    o = np.argsort(x, kind='stable')
    xs, ws = x[o], w[o]
    cw = np.cumsum(ws) / ws.sum()
    return [xs[np.searchsorted(cw, q)] for q in qs]


ref = ris[ris.elezione_id == 'comunali_consiglio_2021-10-03'].set_index('sezione')
el_ref = np.array([ref.elettori.get(s, 0) if s in ref.index else 0 for s in sezioni], dtype=float)
cuts = wquantile_cuts(inc_s, np.where(el_ref > 0, el_ref, 1e-9), [i / 10 for i in range(1, 10)])
dec = np.searchsorted(cuts, inc_s, side='left')        # 0..9
dec = np.minimum(dec, 9)
sez['decile'] = dec + 1
# colonna "income decile" per CAP prevalente: indicazione
D1H = np.zeros((S, 10))
D1H[np.arange(S), dec] = 1.0

# decili: chi c'e dentro
dec_tab = pd.DataFrame({'decile': np.arange(1, 11)})
dec_tab['sezioni'] = D1H.sum(0)
dec_tab['elettori_2021'] = D1H.T @ el_ref
dec_tab['quota_elettori_2021'] = dec_tab.elettori_2021 / el_ref.sum()
dec_tab['reddito_min'] = [inc_s[dec == d].min() for d in range(10)]
dec_tab['reddito_max'] = [inc_s[dec == d].max() for d in range(10)]
dec_tab['reddito_medio_pesato'] = [np.average(inc_s[dec == d], weights=np.maximum(el_ref[dec == d], 1e-9)) for d in range(10)]
dec_tab['n_cap_prevalenti'] = [len(set(cl[dec == d])) for d in range(10)]
dec_tab.to_csv(os.path.join(OUT, 'decili_definizione.csv'), index=False, encoding='utf-8-sig')


# ---- matrici dei voti per elezione
def sez_matrix(series_by_sez):
    a = np.zeros(S)
    for s, v in series_by_sez.items():
        i = SIDX.get(s)
        if i is not None:
            a[i] = v
    return a


BLOC = {'Sx (Sinistra+Centrosinistra)': ['Sinistra', 'Centrosinistra'],
        'Dx (Centrodestra+Lega+Destra)': ['Centrodestra', 'Lega', 'Destra'],
        'Sx+Centro (Sinistra+Centrosinistra+Centro)': ['Sinistra', 'Centrosinistra', 'Centro']}
FAMS = ['Centrosinistra', 'Sinistra', 'M5S', 'Centro', 'Centrodestra', 'Lega', 'Destra', 'Altri']
SOGLIA_LISTA = 0.025


def build(eid):
    """ritorna: nomi voci, matrice V (S x K) dei voti, vettore T (S) del denominatore, e metadati"""
    r = ELE.loc[eid]
    vv = voti[voti.elezione_id == eid]
    rr = ris[ris.elezione_id == eid].set_index('sezione')
    names, cols, tipo = [], [], []
    tot = vv.groupby('sezione').voti.sum()
    T = sez_matrix(tot)
    if r.gruppo == 'referendum':
        # Si e No dalla tabella risultati (campo si/no); la quota Si e su Si+No
        cols.append(sez_matrix(rr.si.fillna(0))); names.append('Si'); tipo.append('quesito')
        cols.append(sez_matrix(rr.no.fillna(0))); names.append('No'); tipo.append('quesito')
        T = cols[0] + cols[1]
    else:
        pf = vv.pivot_table(index='sezione', columns='famiglia', values='voti', aggfunc='sum', fill_value=0)
        for f in FAMS:
            if f in pf.columns and pf[f].sum() > 0:
                cols.append(sez_matrix(pf[f])); names.append(f); tipo.append('famiglia')
        fa = dict(zip(names, cols))
        for b, fs in BLOC.items():
            cols.append(sum(fa.get(f, np.zeros(S)) for f in fs)); names.append(b); tipo.append('blocco')
        if r.gruppo not in ('comunali_sindaco', 'comunali_ballottaggio'):
            pl = vv.groupby('lista').voti.sum()
            pl = pl[pl / pl.sum() >= SOGLIA_LISTA].sort_values(ascending=False)
            for l in pl.index:
                p2 = vv[vv.lista == l].groupby('sezione').voti.sum()
                cols.append(sez_matrix(p2)); names.append('lista: ' + l.strip()); tipo.append('lista')
        else:
            pl = vv.groupby('lista').voti.sum()
            pl = pl[pl / pl.sum() >= 0.03].sort_values(ascending=False)
            for l in pl.index:
                p2 = vv[vv.lista == l].groupby('sezione').voti.sum()
                cols.append(sez_matrix(p2)); names.append('candidato: ' + l.strip()); tipo.append('lista')
    V = np.column_stack(cols)
    # affluenza: solo sezioni "regolari" (elettori > 0 e votanti <= elettori)
    ele = sez_matrix(rr.elettori.fillna(0)); vot = sez_matrix(rr.votanti.fillna(0))
    ok = (ele > 0) & (vot <= ele)
    return names, tipo, V, T, np.where(ok, ele, 0.0), np.where(ok, vot, 0.0), ele, vot


# ---- funzioni di sintesi
def ratio_by(Mnum, Mden, G):
    """quote per gruppo G (S x g one-hot): (G'num)/(G'den)"""
    n = G.T @ Mnum
    d = G.T @ Mden
    with np.errstate(divide='ignore', invalid='ignore'):
        return n / d


def wls_slope(x, y, w):
    xm = np.average(x, weights=w); ym = np.average(y, weights=w)
    return np.sum(w * (x - xm) * (y - ym)) / np.sum(w * (x - xm) ** 2)


def boot_idx():
    return rng.integers(0, len(cap_list), size=(NB, len(cap_list)))


BI = boot_idx()    # stessi ricampionamenti di CAP per tutte le elezioni (confrontabili)
# conteggio per grappolo in ogni replica -> moltiplicatore per sezione
CNT = np.zeros((NB, len(cap_list)))
for b in range(NB):
    CNT[b] = np.bincount(BI[b], minlength=len(cap_list))
MULT = CNT[:, cl]            # NB x S


SEZ_VOCI = {'Sx (Sinistra+Centrosinistra)', 'Dx (Centrodestra+Lega+Destra)', 'Sx+Centro (Sinistra+Centrosinistra+Centro)', 'Centrosinistra',
            'Centro', 'M5S', 'Si', 'AFFLUENZA'}
SEZ_ALL = []


def analizza(eid):
    names, tipo, V, T, E, Vo, Eraw, Voraw = build(eid)
    K = V.shape[1]
    # --- numeratori/denominatori: voci (V/T) e affluenza (Vo/E)
    num = np.column_stack([V, Vo])
    den = np.column_stack([np.repeat(T[:, None], K, 1), E])
    nm = names + ['AFFLUENZA']
    tp = tipo + ['affluenza']
    # decili
    dsh = ratio_by(num, den, D1H)                         # 10 x (K+1)
    gap = (dsh[9] - dsh[0]) * 100
    gap9 = (dsh[8] - dsh[0]) * 100
    # bootstrap del gap D10-D1 (grappoli = CAP)
    Dn = np.einsum('sd,bs,sk->bdk', D1H, MULT, num, optimize=True)   # NB x 10 x K+1
    Dd = np.einsum('sd,bs,sk->bdk', D1H, MULT, den, optimize=True)
    with np.errstate(divide='ignore', invalid='ignore'):
        sb = Dn / Dd
    gapb = (sb[:, 9, :] - sb[:, 0, :]) * 100
    glo, ghi = np.nanpercentile(gapb, [2.5, 97.5], axis=0)
    dlo, dhi = np.nanpercentile(sb, [2.5, 97.5], axis=0)       # intervallo bootstrap di ogni quota di decile (10 x K+1)
    # --- livello CAP: voti divisi per peso, quote per CAP
    Cn = WS.T @ num; Cd = WS.T @ den
    with np.errstate(divide='ignore', invalid='ignore'):
        cshare = Cn / Cd
    wts = Cd                                              # pesi: denominatore di ogni voce
    slope = np.zeros(K + 1); rho = np.zeros(K + 1); slo = np.zeros(K + 1); shi = np.zeros(K + 1)
    rlo = np.zeros(K + 1); rhi = np.zeros(K + 1)
    lslope = np.zeros(K + 1); llo = np.zeros(K + 1); lhi = np.zeros(K + 1)
    for k in range(K + 1):
        y = cshare[:, k] * 100; w = wts[:, k]
        good = np.isfinite(y) & (w > 0)
        slope[k] = wls_slope(x_c[good], y[good], w[good])
        rho[k] = spearmanr(x_c[good], y[good]).statistic
        bs = np.empty(NB); br = np.empty(NB); bl = np.empty(NB)
        gi = np.where(good)[0]
        lslope[k] = wls_slope(lx_c[good], y[good], w[good])
        for b in range(NB):
            ii = BI[b][np.isin(BI[b], gi)]
            if len(ii) < 5 or np.ptp(x_c[ii]) == 0:
                bs[b] = np.nan; br[b] = np.nan; bl[b] = np.nan; continue
            bs[b] = wls_slope(x_c[ii], y[ii], w[ii])
            bl[b] = wls_slope(lx_c[ii], y[ii], w[ii])
            br[b] = spearmanr(x_c[ii], y[ii]).statistic
        slo[k], shi[k] = np.nanpercentile(bs, [2.5, 97.5])
        rlo[k], rhi[k] = np.nanpercentile(br, [2.5, 97.5])
        llo[k], lhi[k] = np.nanpercentile(bl, [2.5, 97.5])
    tot_num = num.sum(0); tot_den = den.sum(0)
    # città intera (tutte le sezioni con legame) e copertura
    ris_e = ris[ris.elezione_id == eid]
    vot_all = ris_e.votanti.sum()
    cov = Voraw.sum() / vot_all if vot_all > 0 else np.nan
    rows = []
    for k, n in enumerate(nm):
        rows.append(dict(elezione_id=eid, etichetta=ELE.loc[eid, 'etichetta2'], data=ELE.loc[eid, 'data'], gruppo=ELE.loc[eid, 'gruppo'],
                         voce=n, tipo=tp[k], quota_citta_pct=round(100 * tot_num[k] / tot_den[k], 2),
                         quota_D1_pct=round(100 * dsh[0, k], 2), quota_D10_pct=round(100 * dsh[9, k], 2),
                         gap_D10_D1_pp=round(gap[k], 2), gap_ic_lo=round(glo[k], 2), gap_ic_hi=round(ghi[k], 2), gap_D9_D1_pp=round(gap9[k], 2),
                         pend_per_raddoppio_pp=round(lslope[k], 3), pend_raddoppio_ic_lo=round(llo[k], 3), pend_raddoppio_ic_hi=round(lhi[k], 3),
                         pendenza_pp_per_10k=round(slope[k], 3), pend_ic_lo=round(slo[k], 3), pend_ic_hi=round(shi[k], 3),
                         spearman_cap=round(rho[k], 3), sp_ic_lo=round(rlo[k], 3), sp_ic_hi=round(rhi[k], 3),
                         copertura_votanti_pct=round(100 * cov, 2)))
    dec_rows = []
    for d in range(10):
        for k, n in enumerate(nm):
            dec_rows.append(dict(elezione_id=eid, voce=n, tipo=tp[k], decile=d + 1, quota_pct=round(100 * dsh[d, k], 2),
                                 ic_lo=round(100 * dlo[d, k], 2), ic_hi=round(100 * dhi[d, k], 2),
                                 num=round(float((D1H[:, d] @ num[:, k])), 1), den=round(float((D1H[:, d] @ den[:, k])), 1)))
    cap_rows = []
    for ci, c in enumerate(cap_list):
        for k, n in enumerate(nm):
            if tp[k] in ('famiglia', 'blocco', 'quesito', 'affluenza'):
                cap_rows.append(dict(elezione_id=eid, cap=c, voce=n, quota_pct=round(100 * cshare[ci, k], 2), den=round(float(Cd[ci, k]), 1)))
    sez_rows = []
    for k, n in enumerate(nm):
        if n in SEZ_VOCI:
            with np.errstate(divide='ignore', invalid='ignore'):
                qs = 100 * num[:, k] / den[:, k]
            for i in range(S):
                if den[i, k] > 0 and np.isfinite(qs[i]):
                    sez_rows.append((eid, int(sezioni[i]), n, round(float(qs[i]), 1), int(round(den[i, k]))))
    SEZ_ALL.extend(sez_rows)
    return rows, dec_rows, cap_rows, (names, tipo, V, T, E, Vo)


allrows, alldec, allcap = [], [], []
cache = {}
for eid in ELE.sort_values(['data']).index:
    rows, drows, crows, pack = analizza(eid)
    allrows += rows; alldec += drows; allcap += crows
    cache[eid] = pack
    print('ok', eid, len(rows), flush=True)

res = pd.DataFrame(allrows)
res.to_csv(os.path.join(OUT, 'gradiente_per_voce.csv'), index=False, encoding='utf-8-sig')
pd.DataFrame(alldec).to_csv(os.path.join(OUT, 'decili_per_voce.csv'), index=False, encoding='utf-8-sig')
pd.DataFrame(allcap).to_csv(os.path.join(OUT, 'cap_per_voce.csv'), index=False, encoding='utf-8-sig')
pd.DataFrame(SEZ_ALL, columns=['elezione_id', 'sezione', 'voce', 'quota_pct', 'den']).to_csv(
    os.path.join(OUT, 'sezioni_quote_voci_chiave.csv'), index=False, encoding='utf-8-sig')
sez.reset_index().to_csv(os.path.join(OUT, 'sezioni_reddito_decile.csv'), index=False, encoding='utf-8-sig')

# =============================== ROBUSTEZZA ===============================
KEYV = ['Sx (Sinistra+Centrosinistra)', 'Dx (Centrodestra+Lega+Destra)', 'Sx+Centro (Sinistra+Centrosinistra+Centro)', 'Centrosinistra', 'Centro', 'M5S', 'AFFLUENZA', 'Si']
YCOL = {2015: 'nom_2015', 2016: 'nom_2015', 2017: 'nom_2015', 2018: 'nom_2019', 2019: 'nom_2019', 2020: 'nom_2020', 2021: 'nom_2021',
        2022: 'nom_2022', 2023: 'nom_2023', 2024: 'nom_2024', 2025: 'nom_2024', 2026: 'nom_2024'}
rob = []
for eid, (names, tipo, V, T, E, Vo) in cache.items():
    num = np.column_stack([V, Vo]); den = np.column_stack([np.repeat(T[:, None], V.shape[1], 1), E])
    nm = names + ['AFFLUENZA']
    yr = int(ELE.loc[eid, 'anno'])
    variants = {
        'principale: reddito medio 2019-22 (euro 2025), pesi civici': inc_c,
        'reddito dell\'anno di imposta piu vicino all\'elezione': CR[YCOL[yr]].values.astype(float),
        'reddito 2024 (euro 2025)': CR['reddito_2024_euro2025'].values.astype(float),
        'reddito 2015 (euro correnti)': CR['nom_2015'].values.astype(float)}
    # (a) solo sezioni "pulite": peso del CAP prevalente >= 0,8, CAP assegnato per intero
    pure = sez.peso_prev.values >= 0.8
    for vn, vinc in variants.items():
        xc = vinc / 10000.0
        Cn = WS.T @ num; Cd = WS.T @ den
        for n in KEYV:
            if n not in nm:
                continue
            k = nm.index(n)
            y = 100 * Cn[:, k] / Cd[:, k]; w = Cd[:, k]
            g = np.isfinite(y) & (w > 0) & np.isfinite(xc)
            rob.append(dict(elezione_id=eid, etichetta=ELE.loc[eid, 'etichetta2'], voce=n, variante=vn, livello='CAP (voti divisi per peso)',
                            pendenza_pp_per_10k=round(wls_slope(xc[g], y[g], w[g]), 3), spearman=round(spearmanr(xc[g], y[g]).statistic, 3)))
            if vn.startswith('principale'):
                keep = np.array([c not in (20121, 20122, 20145) for c in cap_list])
                g2 = g & keep
                rob.append(dict(elezione_id=eid, etichetta=ELE.loc[eid, 'etichetta2'], voce=n, variante='senza i CAP 20121, 20122, 20145 (36 CAP)',
                                livello='CAP (voti divisi per peso)', pendenza_pp_per_10k=round(wls_slope(xc[g2], y[g2], w[g2]), 3),
                                spearman=round(spearmanr(xc[g2], y[g2]).statistic, 3)))
    # (b) sezione per sezione, solo sezioni con CAP prevalente >= 80% dei civici: ogni sezione al suo CAP
    for n in KEYV:
        if n not in nm:
            continue
        k = nm.index(n)
        xs = (inc_c[cl] / 10000.0)[pure]
        y = 100 * num[pure, k] / den[pure, k]; w = den[pure, k]
        g = np.isfinite(y) & (w > 0)
        rob.append(dict(elezione_id=eid, etichetta=ELE.loc[eid, 'etichetta2'], voce=n,
                        variante='sezioni con CAP prevalente >= 80%% dei civici (%d sezioni)' % int(pure.sum()), livello='sezione',
                        pendenza_pp_per_10k=round(wls_slope(xs[g], y[g], w[g]), 3), spearman=round(spearmanr(xs[g], y[g]).statistic, 3)))
    # (b2) sezione: quanta variabilita tra sezioni sta tra CAP (eta^2) e quanta e spiegata dal reddito (R^2), pesi = denominatore
    for n in KEYV:
        if n not in nm:
            continue
        k = nm.index(n)
        y = 100 * num[:, k] / den[:, k]; w = den[:, k]
        g = np.isfinite(y) & (w > 0)
        yg, wg, cg, xg = y[g], w[g], cl[g], (inc_s / 10000.0)[g]
        ym = np.average(yg, weights=wg)
        sst = np.sum(wg * (yg - ym) ** 2)
        ssb = sum(np.sum(wg[cg == c]) * (np.average(yg[cg == c], weights=wg[cg == c]) - ym) ** 2 for c in set(cg))
        bsl = wls_slope(xg, yg, wg)
        a0 = ym - bsl * np.average(xg, weights=wg)
        ssr = np.sum(wg * (yg - (a0 + bsl * xg)) ** 2)
        rob.append(dict(elezione_id=eid, etichetta=ELE.loc[eid, 'etichetta2'], voce=n, variante='varianza tra sezioni: quota tra CAP (eta2) e spiegata dal reddito (R2)',
                        livello='sezione', pendenza_pp_per_10k=round(bsl, 3), eta2_tra_cap=round(ssb / sst, 3), r2_reddito=round(1 - ssr / sst, 3)))
    # (c) livello NIL: voti divisi per i pesi sezione->NIL, reddito NIL = media CAP pesata per civici
    ids = sorted(set(WN.id_nil))
    NI = {n: i for i, n in enumerate(ids)}
    WSN = np.zeros((S, len(ids)))
    for r in WN.itertuples():
        i = SIDX.get(r.sezione)
        if i is not None:
            WSN[i, NI[r.id_nil]] = r.peso
    Nn = WSN.T @ num; Nd = WSN.T @ den
    xn = np.array([NILR.reddito_2019_22_euro2025.get(n, np.nan) for n in ids]) / 10000.0
    okn = np.array([(n not in FRAG_IDS) and np.isfinite(xn[i]) for i, n in enumerate(ids)])
    sq = POP.reindex(ids)
    for n in KEYV:
        if n not in nm:
            continue
        k = nm.index(n)
        y = 100 * Nn[:, k] / Nd[:, k]; w = Nd[:, k]
        g = okn & np.isfinite(y) & (w > 1000)
        yy, ww, xx = y[g], w[g], xn[g]
        b1 = wls_slope(xx, yy, ww)
        # regressione con controlli: quota di stranieri e quota 65+ (WLS)
        X = np.column_stack([np.ones(g.sum()), xx, sq.quota_stranieri.values[g] * 100, sq.q_65p.values[g] * 100])
        sw = np.sqrt(ww)
        beta = np.linalg.lstsq(X * sw[:, None], yy * sw, rcond=None)[0]
        # bootstrap sui NIL
        bs = []; bc = []
        gi = np.where(g)[0]
        for b in range(500):
            ii = rng.choice(len(yy), size=len(yy), replace=True)
            bs.append(wls_slope(xx[ii], yy[ii], ww[ii]))
            beta_b = np.linalg.lstsq(X[ii] * sw[ii, None], yy[ii] * sw[ii], rcond=None)[0]
            bc.append(beta_b[1])
        rob.append(dict(elezione_id=eid, etichetta=ELE.loc[eid, 'etichetta2'], voce=n,
                        variante='NIL (%d quartieri con >1.000 votanti, non fragili)' % int(g.sum()), livello='NIL',
                        pendenza_pp_per_10k=round(b1, 3), pend_ic_lo=round(np.percentile(bs, 2.5), 3), pend_ic_hi=round(np.percentile(bs, 97.5), 3),
                        spearman=round(spearmanr(xx, yy).statistic, 3),
                        pend_con_controlli=round(beta[1], 3), pend_con_controlli_ic_lo=round(np.percentile(bc, 2.5), 3),
                        pend_con_controlli_ic_hi=round(np.percentile(bc, 97.5), 3),
                        coef_stranieri_pp_per_pp=round(beta[2], 3), coef_over65_pp_per_pp=round(beta[3], 3)))
pd.DataFrame(rob).to_csv(os.path.join(OUT, 'robustezza.csv'), index=False, encoding='utf-8-sig')

# correlazioni tra le variabili esplicative a livello NIL (per capire cosa si confonde con il reddito)
ids = sorted(set(WN.id_nil))
nx = pd.DataFrame({'reddito_10k': [NILR.reddito_2019_22_euro2025.get(n, np.nan) / 10000.0 for n in ids]}, index=ids).join(POP)
nx = nx[[i not in FRAG_IDS for i in nx.index]]
cm = nx[['reddito_10k', 'quota_stranieri', 'q_65p']].corr(method='spearman').round(3)
cm.to_csv(os.path.join(OUT, 'correlazioni_nil_reddito_stranieri_eta.csv'), encoding='utf-8-sig')
json.dump({'cuts_reddito_sezione_euro2025': [float(c) for c in cuts], 'sezioni_con_legame': int(S), 'anno_popolazione': POPY,
           'nil_fragili_esclusi': sorted(FRAG_IDS)}, open(os.path.join(OUT, 'parametri.json'), 'w'), indent=1)
print('fine')
