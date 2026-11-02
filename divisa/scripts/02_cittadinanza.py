"""02: quanto sono separati italiani e cittadini stranieri (e le comunita' principali) tra i 88 quartieri (NIL), 1999-2025.
Entrata: popolazione/pulito/residenti_nil_anno_cittadinanza.csv (ds27 del Comune: residenti al 31/12 per NIL x cittadinanza).
Uscite in divisa/out/: cittadinanza_serie.csv (anno), cittadinanza_comunita.csv (anno x comunita'), cittadinanza_nil.csv (anno x NIL x gruppo), cittadinanza_log.json
Uso: python -I -X utf8 02_cittadinanza.py <milano-in-dati assoluto> <divisa assoluto>
'Cittadinanza' = quella scritta in anagrafe (chi l'ha acquisita e' 'Italia'): non e' origine ne' luogo di nascita.
Misure: D italiani/stranieri; isolamento degli stranieri; indice di entropia (Theil) tra tutte le cittadinanze raggruppate (Italia + 10 comunita' + altre) e solo tra stranieri;
D di ogni comunita' contro tutti gli altri residenti. Intervalli: ricampionamento multinomiale (200). Valore a caso: 50 riallocazioni."""
import sys, os, json
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import misure as M

BASE, DIV = sys.argv[1], sys.argv[2]
OUT = os.path.join(DIV, 'out')
os.makedirs(OUT, exist_ok=True)
c = pd.read_csv(os.path.join(BASE, 'popolazione', 'pulito', 'residenti_nil_anno_cittadinanza.csv'))
ana = pd.read_csv(os.path.join(BASE, 'popolazione', 'pulito', 'nil_anagrafica.csv'))
ids = ana.id_nil.tolist()
TOP = ['Egitto', 'Cinese, Rep. Popolare', 'Filippine', 'Perù', 'Sri Lanka (ex Ceylon)', 'Romania', 'Bangladesh', 'Ucraina', 'Ecuador', 'Marocco']
ETI = {'Cinese, Rep. Popolare': 'Cina', 'Sri Lanka (ex Ceylon)': 'Sri Lanka'}
GR = ['Italia'] + TOP + ['altre']
c['g'] = np.where(c.cittadinanza.isin(GR), c.cittadinanza, 'altre')
P = c.groupby(['anno', 'id_nil', 'g']).residenti.sum().unstack('g').reindex(columns=GR).fillna(0)
rng = np.random.default_rng(1999)
log = {}


def mat(anno):
    p = P.loc[anno].reindex(ids).fillna(0)
    return p


def dit(R):
    return M.dissimilarita(R[:, 0], R[:, 1:].sum(1))


rows = []; com = []; nilrows = []
for anno in sorted(P.index.get_level_values(0).unique()):
    p = mat(anno)
    Cm = p.to_numpy(float)
    keep = Cm.sum(1) > 0
    Cm = Cm[keep]
    ita = Cm[:, 0]; stra = Cm[:, 1:].sum(1); t = Cm.sum(1)
    # due gruppi: italiani / stranieri
    C2 = np.column_stack([ita, stra])
    r = dict(anno=int(anno), residenti=int(t.sum()), stranieri=int(stra.sum()), quota_stranieri=stra.sum() / t.sum(), n_nil=int(keep.sum()))
    r['d'] = M.dissimilarita(ita, stra)
    _, r['d_lo'], r['d_hi'] = M.bootstrap(C2, lambda R: M.dissimilarita(R[:, 0], R[:, 1]), 200, rng)
    r['d_base'] = M.basale(C2, lambda R: M.dissimilarita(R[:, 0], R[:, 1]), 50, rng)[0]
    r['iso_stranieri'] = M.isolamento(stra, t)          # quota media di stranieri tra i residenti del NIL di uno straniero
    r['esposizione_a_italiani'] = 1 - r['iso_stranieri']
    # entropia multigruppo
    r['h_tutte'] = M.theil_H(Cm)
    _, r['h_tutte_lo'], r['h_tutte_hi'] = M.bootstrap(Cm, M.theil_H, 200, rng)
    r['h_tutte_base'] = M.basale(Cm, M.theil_H, 50, rng)[0]
    Cs = Cm[:, 1:]
    Cs = Cs[Cs.sum(1) > 0]
    r['h_stranieri'] = M.theil_H(Cs)
    _, r['h_stranieri_lo'], r['h_stranieri_hi'] = M.bootstrap(Cs, M.theil_H, 200, rng)
    r['h_stranieri_base'] = M.basale(Cs, M.theil_H, 50, rng)[0]
    rows.append(r)
    # comunita'
    for j, g in enumerate(TOP, start=1):
        a = Cm[:, j]; b = t - a
        C2g = np.column_stack([a, b])
        f = lambda R: M.dissimilarita(R[:, 0], R[:, 1])
        d0 = M.dissimilarita(a, b) if a.sum() > 0 else np.nan
        if a.sum() >= 50:
            _, lo, hi = M.bootstrap(C2g, f, 100, rng)
            base = M.basale(C2g, f, 30, rng)[0]
        else:
            lo = hi = base = np.nan
        com.append(dict(anno=int(anno), comunita=ETI.get(g, g), residenti=int(a.sum()), quota_citta=a.sum() / t.sum(), d=d0, d_lo=lo, d_hi=hi, d_base=base,
                        iso=M.isolamento(a, t) if a.sum() > 0 else np.nan))
    # per NIL (mappe)
    for i, nid in enumerate(p.index):
        row = p.loc[nid]
        nilrows.append(dict(anno=int(anno), id_nil=int(nid), residenti=int(row.sum()), stranieri=int(row.sum() - row['Italia']),
                            **{('c_' + ETI.get(g, g)): int(row[g]) for g in TOP}))
    print(anno, round(r['d'], 3), round(r['d_base'], 3), round(r['h_tutte'], 3), round(r['h_stranieri'], 3), flush=True)
S = pd.DataFrame(rows); S.to_csv(os.path.join(OUT, 'cittadinanza_serie.csv'), index=False, float_format='%.5f')
K = pd.DataFrame(com); K.to_csv(os.path.join(OUT, 'cittadinanza_comunita.csv'), index=False, float_format='%.5f')
pd.DataFrame(nilrows).to_csv(os.path.join(OUT, 'cittadinanza_nil.csv'), index=False)
log['gruppi'] = GR
json.dump(log, open(os.path.join(OUT, 'cittadinanza_log.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(K[K.anno.isin([1999, 2011, 2025])].pivot(index='comunita', columns='anno', values='d').round(3))
print(K[K.anno.isin([1999, 2011, 2025])].pivot(index='comunita', columns='anno', values='d_base').round(3))
