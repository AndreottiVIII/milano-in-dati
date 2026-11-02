"""01: quanto sono separati ricchi e poveri tra i CAP (MEF, redditi per CAP, anni d'imposta 2011, 2015, 2019-2024).
Entrate: redditi/pulito/cap_redditi_tutte_le_citta.csv (41 citta'); quartieri-che-cambiano/out/collegamento_cap_nil.csv.
Uscite in divisa/out/: reddito_serie.csv (citta' x anno), reddito_varianti_milano.csv, reddito_41_citta.csv, reddito_cap_milano.csv, reddito_nil_milano.csv, reddito_log.json
Uso: python -I -X utf8 01_reddito.py <milano-in-dati assoluto> <divisa assoluto>
Classi MEF del reddito complessivo: <=0 | 0-10k | 10-15k | 15-26k | 26-55k | 55-75k | 75-120k | >120k (euro correnti dell'anno d'imposta).
Si usano 7 classi: <=0 e 0-10k sono unite (dal 2019 il MEF svuota la classe <=0: con p quasi 0 il rumore di poche decine di persone gonfiava l'indice a ordine di rango, +33% 2011-2024 invece di +12%).
Indici: hr = entropia a ordine di rango; d = D tra quarto piu' povero e quarto piu' ricco; iso = isolamento del quarto piu' ricco; d_soglie = D tra <=15k e >55k (soglie fisse in euro, non confrontabile nel tempo).
Celle mancanti: la classe >120k (e a volte <=0) manca in 11-18 CAP di Milano nel 2023-24 (segreto statistico); si ricostruisce dalla somma
(reddito_complessivo_n = somma delle 8 classi, verificato su 591 righe complete: differenza 0). Il residuo (<=0 piu' >120k) va tutto in >120k (errore <= 25 persone per CAP)."""
import sys, os, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import misure as M

BASE, DIV = sys.argv[1], sys.argv[2]
OUT = os.path.join(DIV, 'out')
os.makedirs(OUT, exist_ok=True)
CL = ['cl0_le0', 'cl1_0_10k', 'cl2_10_15k', 'cl3_15_26k', 'cl4_26_55k', 'cl5_55_75k', 'cl6_75_120k', 'cl7_oltre120k']
N = [c + '_n' for c in CL]
d = pd.read_csv(os.path.join(BASE, 'redditi', 'pulito', 'cap_redditi_tutte_le_citta.csv'), dtype={'cap': str})
log = dict(righe=len(d))

# --- ricostruzione celle mancanti
# 1) classe >120k mancante ma "reddito_complessivo_n" presente (2023-24): per differenza (la somma delle 8 classi e' uguale a reddito_complessivo_n)
# 2) altre celle mancanti (segreto statistico, soprattutto CAP piccoli di altre citta'): quota mediana della classe nel CAP negli altri anni
X = d[N].copy()
mid = X[N[1:7]].sum(axis=1, min_count=6)
res = d.reddito_complessivo_n - mid - X.cl0_le0_n.fillna(0)
fix = X.cl7_oltre120k_n.isna() & res.notna() & (res >= 0)
log['imputati_per_differenza'] = int(fix.sum())
X.loc[fix, 'cl7_oltre120k_n'] = res[fix]
X['cl0_le0_n'] = X.cl0_le0_n.fillna(0)
d = d.assign(**{c: X[c] for c in N})
comp = d[N].notna().all(axis=1)
sh = d[comp].copy()
sh[N] = sh[N].div(sh[N].sum(axis=1), axis=0)
med = sh.groupby(['comune', 'cap'])[N].median()
nfix = 0; drop = []
rows_fix = d.index[~comp]
for i in rows_fix:
    r = d.loc[i]
    key = (r.comune, r.cap)
    if key not in med.index:
        drop.append(i); continue
    m = r[N].isna().to_numpy()
    sm = med.loc[key].to_numpy()
    obs = r[N].to_numpy(float)
    if (~m).sum() == 0 or sm[~m].sum() <= 0:
        drop.append(i); continue
    k = np.nansum(obs) / sm[~m].sum()
    d.loc[i, np.array(N)[m]] = sm[m] * k
    nfix += 1
log['imputati_per_quota_mediana'] = nfix
log['righe_scartate_senza_anni_completi'] = [d.loc[i, ['comune', 'anno', 'cap']].astype(str).tolist() for i in drop][:60]
d = d.drop(index=drop)
# classi usate: 7 (la classe <=0 e' unita a 0-10k: dal 2019 il MEF la svuota e un'ondata di rumore a p quasi 0 gonfiava l'indice)
d['c0'] = d.cl0_le0_n + d.cl1_0_10k_n
C7 = ['c0', 'cl2_10_15k_n', 'cl3_15_26k_n', 'cl4_26_55k_n', 'cl5_55_75k_n', 'cl6_75_120k_n', 'cl7_oltre120k_n']
N = C7
d['tot'] = d[N].sum(axis=1)
# unita' troppo piccole (meno di 500 contribuenti) fuori
log['cap_sotto_500_scartati'] = int((d.tot < 500).sum())
d = d[d.tot >= 500].copy()


def matrice(g):
    return g[N].to_numpy(float)


def quartili(Cm, q=0.25):
    """quota di ogni unita' nel quarto piu' povero e nel quarto piu' ricco dei contribuenti della citta' (classe di confine divisa in proporzione)."""
    T = Cm.sum(0); tot = T.sum()
    def prendi(ordine):
        w = np.zeros(len(T)); resto = q * tot
        for k in ordine:
            u = min(T[k], resto); w[k] = u / T[k] if T[k] > 0 else 0; resto -= u
            if resto <= 0: break
        return Cm @ w
    return prendi(range(len(T))), prendi(range(len(T) - 1, -1, -1))


def dq(R):
    lo, hi = quartili(R); return M.dissimilarita(lo, hi)


def dsoglie(R):
    return M.dissimilarita(R[:, 4:].sum(1), R[:, :2].sum(1))


def misure(Cm, B, rng):
    """Cm: unita' x 7 classi. Indice a ordine di rango, D tra quarto ricco e quarto povero, isolamento del quarto ricco, D a soglie fisse (+ intervalli e valore a caso)."""
    lo, hi = quartili(Cm); t = Cm.sum(1)
    out = {'hr': M.rank_order_H(Cm), 'd': M.dissimilarita(lo, hi), 'iso': M.isolamento(hi, t), 'iso_basso': M.isolamento(lo, t),
           'd_soglie': dsoglie(Cm), 'quota_alto': Cm[:, 4:].sum() / t.sum(), 'quota_basso': Cm[:, :2].sum() / t.sum()}
    if B:
        _, out['hr_lo'], out['hr_hi'] = M.bootstrap(Cm, M.rank_order_H, B, rng)
        _, out['d_lo'], out['d_hi'] = M.bootstrap(Cm, dq, B, rng)
        out['hr_base'] = M.basale(Cm, M.rank_order_H, max(B // 4, 10), rng)[0]
        out['d_base'] = M.basale(Cm, dq, max(B // 4, 10), rng)[0]
    return out


rng = np.random.default_rng(2026)
GRANDI = ['MILANO', 'ROMA', 'TORINO', 'NAPOLI', 'BOLOGNA']
rows = []
for (cit, anno), g in d.groupby(['comune', 'anno']):
    if cit not in GRANDI:
        continue
    Cm = matrice(g)
    r = misure(Cm, 300, rng)
    r.update(citta=cit, anno=int(anno), n_cap=len(g), contribuenti=int(Cm.sum()), per_cap=Cm.sum() / len(g))
    rows.append(r)
S = pd.DataFrame(rows)
S.to_csv(os.path.join(OUT, 'reddito_serie.csv'), index=False, float_format='%.5f')
print(S[S.citta == 'MILANO'][['anno', 'n_cap', 'hr', 'hr_lo', 'hr_hi', 'hr_base', 'd', 'd_lo', 'd_hi', 'iso', 'quota_alto']].round(3).to_string())
print(S.pivot(index='anno', columns='citta', values='hr').round(3))

# --- varianti Milano: CAP 20121+20122 uniti; senza 20121 e 20122
rows = []
mi = d[d.comune == 'MILANO']
for anno, g in mi.groupby('anno'):
    due = g[g.cap.isin(['20121', '20122'])][N].sum().to_frame().T
    for nome, Cm in [('tutti i 38 CAP', matrice(g)),
                     ('20121 e 20122 uniti', np.vstack([matrice(g[~g.cap.isin(['20121', '20122'])]), due.to_numpy(float)])),
                     ('senza 20121 e 20122', matrice(g[~g.cap.isin(['20121', '20122'])]))]:
        rows.append(dict(variante=nome, anno=int(anno), n_cap=len(Cm), hr=M.rank_order_H(Cm), d=dq(Cm),
                         iso=M.isolamento(quartili(Cm)[1], Cm.sum(1))))
V = pd.DataFrame(rows)
V.to_csv(os.path.join(OUT, 'reddito_varianti_milano.csv'), index=False, float_format='%.5f')
print(V.pivot(index='anno', columns='variante', values='hr').round(3))

# --- tutte le 41 citta', solo 2011 e 2024
rows = []
for (cit, anno), g in d[d.anno.isin([2011, 2024])].groupby(['comune', 'anno']):
    Cm = matrice(g)
    if len(g) < 5:
        continue
    r = misure(Cm, 100, rng)
    r.update(citta=cit, anno=int(anno), n_cap=len(g), contribuenti=int(Cm.sum()), per_cap=Cm.sum() / len(g))
    rows.append(r)
A = pd.DataFrame(rows)
A.to_csv(os.path.join(OUT, 'reddito_41_citta.csv'), index=False, float_format='%.5f')
print(A[A.anno == 2024].sort_values('hr', ascending=False)[['citta', 'n_cap', 'per_cap', 'hr', 'hr_lo', 'hr_hi', 'd']].round(3).head(15).to_string())

# --- CAP di Milano e NIL
mi = mi.copy()
mi['alto'] = mi[N[4:]].sum(axis=1) / mi.tot
mi['basso'] = mi[N[:2]].sum(axis=1) / mi.tot
mi[['anno', 'cap', 'tot', 'alto', 'basso', 'media_euro2025'] + N].to_csv(os.path.join(OUT, 'reddito_cap_milano.csv'), index=False, float_format='%.5f')
cn = pd.read_csv(os.path.join(BASE, 'quartieri-che-cambiano', 'out', 'collegamento_cap_nil.csv'), dtype={'CAP': str})
cn['ID_NIL'] = cn.ID_NIL.astype(int)
s = cn.groupby('ID_NIL').quota_nil.sum()
log['quota_nil_somma_min_max'] = [float(s.min()), float(s.max())]
rows = []
for anno, g in mi.groupby('anno'):
    gg = g.set_index('cap')
    for nil, h in cn.groupby('ID_NIL'):
        h = h[h.CAP.isin(gg.index)]
        if h.empty:
            continue
        w = h.quota_nil.to_numpy() / h.quota_nil.sum()
        rows.append(dict(anno=int(anno), id_nil=int(nil), alto=float((w * gg.loc[h.CAP, 'alto'].to_numpy()).sum()),
                         basso=float((w * gg.loc[h.CAP, 'basso'].to_numpy()).sum()),
                         media=float((w * gg.loc[h.CAP, 'media_euro2025'].to_numpy()).sum()), n_cap=len(h)))
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'reddito_nil_milano.csv'), index=False, float_format='%.5f')
json.dump(log, open(os.path.join(OUT, 'reddito_log.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print({k: (v if not isinstance(v, list) or len(v) < 5 else len(v)) for k, v in log.items()})
