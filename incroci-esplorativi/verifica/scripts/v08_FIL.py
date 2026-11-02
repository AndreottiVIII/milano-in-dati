"""F Wikipedia febbraio 2026; I rottura maltrattamenti e stalking; L alberghi e aeroporti."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vc import *
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 60); pd.set_option('display.max_rows', 300); pd.set_option('display.max_colwidth', 40)
L = open(os.path.join(OUT, 'FIL.log'), 'w', encoding='utf8')
def say(*a):
    s = ' '.join(str(x) for x in a); print(s); L.write(s + '\n'); L.flush()
# ===== F
say('===== F')
lc = p('luoghi-cercati', 'pulito')
v = pd.read_csv(os.path.join(lc, 'views_mensili.csv'), sep=';')
lu = pd.read_csv(os.path.join(lc, 'luoghi.csv'), sep=';', low_memory=False)
say('categorie tipo', lu.tipo.value_counts().to_dict())
v = v.merge(lu[['qid', 'tipo', 'categoria', 'nil']], on='qid', how='left')
s0 = pd.read_csv(os.path.join(lc, 'serie_mensile_totale.csv'), sep=';')
luo = v[v.tipo == 'luogo']
chk = luo.groupby('mese').views.sum()
say('controllo serie: febbraio 2026 mio', chk.get('2026-02'), 'file', s0[s0.mese == '2026-02'].tot.values, ' febbraio 2025 mio', chk.get('2025-02'), 'file', s0[s0.mese == '2025-02'].tot.values)
den = pd.read_csv(os.path.join(lc, 'luoghi_vs_wikipedia_mensile.csv'), sep=';')
say('lingue denominatore', den.lingua.unique().tolist(), ' righe per lingua', den.groupby('lingua').size().iloc[0], 'ultimo', den.mese.max())
luo = luo.copy(); luo['gr'] = np.where(luo.lingua == 'it', 'it', 'estero')
M = luo.pivot_table(index='mese', columns='gr', values='views', aggfunc='sum')
M['tot'] = M.sum(axis=1)
den['gr'] = np.where(den.lingua == 'it', 'it', 'estero')
Dn = den.pivot_table(index='mese', columns='gr', values='wikipedia_totale', aggfunc='sum')
Ln = den.pivot_table(index='mese', columns='gr', values='luoghi_milano', aggfunc='sum')
say('luoghi_milano nel file denominatore vs mio feb 2026', Ln.loc['2026-02'].to_dict(), M.loc['2026-02'].to_dict())
Q = pd.DataFrame({c: M[c] / Dn[c] * 1e6 for c in ['it', 'estero']})
for c in ['it', 'estero', 'tot']:
    say(c, 'febbraio per anno:', {y: int(M.loc[f'{y}-02', c]) for y in range(2016, 2027)})
for c in ['it', 'estero']:
    say(c, 'per milione febbraio:', {y: round(Q.loc[f'{y}-02', c], 1) for y in range(2016, 2027)})
    say(c, 'denominatore febbraio (milioni):', {y: round(Dn.loc[f'{y}-02', c] / 1e6) for y in range(2016, 2027)})
def effetto(serie):
    base = np.mean([serie[f'{y}-02'] for y in (2023, 2024, 2025)])
    # differenza nelle differenze: rispetto a gen+mar stesso anno rispetto agli anni prima (scala log)
    r = {y: np.log(serie[f'{y}-02']) - np.log((serie[f'{y}-01'] + serie[f'{y}-03']) / 2) for y in range(2017, 2027) if y != 2020}
    bb = np.mean([r[y] for y in (2023, 2024, 2025)]); sd = np.std([r[y] for y in r if y != 2026], ddof=1)
    return dict(feb26_su_feb2325=round(serie['2026-02'] / base, 3), feb_vs_genmar_2026=round(np.exp(r[2026]) , 3), feb_vs_genmar_prima=round(np.exp(bb), 3), scarto_z=round((r[2026] - np.mean([r[y] for y in r if y != 2026])) / sd, 1))
for c in ['it', 'estero', 'tot']:
    say('grezzo', c, effetto(M[c]))
for c in ['it', 'estero']:
    say('per milione', c, effetto(Q[c]))
say('mesi 2025-10 .. 2026-10, rapporto con stesso mese medio 2023-25 (per milione)')
for c in ['it', 'estero']:
    say(c, {f'{m:02d}': round(Q.loc[f'2026-{m:02d}', c] / np.mean([Q.loc[f'{y}-{m:02d}', c] for y in (2023, 2024, 2025)]), 2) for m in range(1, 11)})
# Quante voci spiegano il salto
for gr in ['it', 'estero']:
    x = luo[luo.gr == gr]
    P = x.pivot_table(index=['qid', 'nome'], columns='mese', values='views', aggfunc='sum').fillna(0)
    P['base'] = P[['2023-02', '2024-02', '2025-02']].mean(axis=1); P['diff'] = P['2026-02'] - P['base']
    tot = P['diff'].sum()
    say(f'\n{gr}: salto totale {tot:.0f} su base {P.base.sum():.0f} = {tot / P.base.sum() * 100:+.1f}% voci {len(P)}; con salita {(P["diff"] > 0).sum()}, con discesa {(P["diff"] < 0).sum()}; rapporto mediano (voci con base>=100): {(P[P.base >= 100]["2026-02"] / P[P.base >= 100].base).median():.3f}')
    t = P.sort_values('diff', ascending=False)
    t['cum'] = t['diff'].cumsum() / tot * 100
    say(t[['base', '2026-02', 'diff', 'cum']].head(15).round(1).to_string())
    pos = P[P['diff'] > 0]['diff'].sort_values(ascending=False); say('voci per fare il 50%/80% del salto netto:', int((pos.cumsum() < .5 * tot).sum() + 1), int((pos.cumsum() < .8 * tot).sum() + 1))
    # togliendo le prime k
    for k in [1, 3, 5, 10, 20, 50]:
        idx = t.index[:k]; rest = P.drop(idx)
        say(f' senza le prime {k:2d}: {rest["diff"].sum() / rest.base.sum() * 100:+.1f}%')
    # voci nuove: nessuna lettura nel feb 2023
    nuove = P[(P['2023-02'] == 0)]
    say(' voci senza letture nel feb 2023:', len(nuove), 'contributo al salto', round(nuove['diff'].sum() / tot * 100, 1), '%')
    # per voci sempre presenti
    ok = P[(P['2023-02'] > 0) & (P['2024-02'] > 0) & (P['2025-02'] > 0)]
    say(' voci sempre presenti:', len(ok), f'{ok["diff"].sum() / ok.base.sum() * 100:+.1f}%')
    rng = np.random.default_rng(SEED); ar = P[['base', '2026-02']].values
    bs = [(lambda i: ar[i, 1].sum() / ar[i, 0].sum())(rng.integers(0, len(ar), len(ar))) for _ in range(2000)]
    say(' bootstrap per voce del rapporto 2026/base: IC', np.round(np.percentile(bs, [2.5, 97.5]), 3))
    # placebo: stesso calcolo per altri febbraio
    for y in [2019, 2023, 2024, 2025]:
        b_ = [f'{y - 3}-02', f'{y - 2}-02', f'{y - 1}-02']
        if all(c in P.columns for c in b_):
            say(f' placebo feb {y}: {P[f"{y}-02"].sum() / P[b_].mean(axis=1).sum() * 100 - 100:+.1f}%')
    if gr == 'it':
        Pi = P
    else:
        Pe = P
# Unipol Dome e altre voci nuove: effetto del titolo
for nome in ['Unipol Dome', 'Villaggio Olimpico', 'Stadio Giuseppe Meazza', 'Arco della Pace', 'Duomo di Milano']:
    x = luo[luo.nome.str.contains(nome, case=False, na=False)]
    if len(x):
        g = x.groupby('mese').views.sum()
        say(nome, {k: int(g.get(k, 0)) for k in ['2023-02', '2024-02', '2024-06', '2025-02', '2025-10', '2025-12', '2026-01', '2026-02', '2026-03', '2026-04']})
rd = pd.read_csv(os.path.join(lc, 'redirect_it_riepilogo.csv'), sep=';')
say('redirect, colonne', rd.columns.tolist()); say(rd[rd.iloc[:, 0].astype(str).str.contains('Unipol|Meazza', case=False) | rd.iloc[:, 1].astype(str).str.contains('Unipol|Meazza', case=False)].to_string())
# confronto con evento analogo: maggio 2015 non c'è; olimpiadi come articolo
n_ = v[v.nome.str.contains('Giochi olimpici', case=False, na=False)].groupby('mese').views.sum(); say('Articolo Giochi olimpici 2026 (non luogo):', {k: int(n_.get(k, 0)) for k in ['2025-12', '2026-01', '2026-02', '2026-03']})
ct = v[v.nome.eq('Milano')].groupby(['mese']).views.sum(); say('Articolo Milano:', {k: int(ct.get(k, 0)) for k in ['2023-02', '2024-02', '2025-02', '2026-01', '2026-02', '2026-03']})

# ===== I
say('\n===== I')
r = pd.read_csv(p('docs', 'reati-citta', 'data', 'famiglia_stalking_mensile.csv'))
say(r.groupby(['territorio', 'tipo_codice']).agg(n=('denunce', 'size'), inizio=('anno', 'min'), fine=('anno', 'max'), tot=('denunce', 'sum')).to_string())
def rottura(y, idx, trim=.15, cov=True, lags=6):
    """sup-F su log y: dummies mese + tendenza + gradino; costo: stessa tendenza."""
    n = len(y); t = np.arange(n); md = pd.get_dummies(idx.month, drop_first=True).values.astype(float)
    base = [np.ones(n), t, md]
    if cov:
        base.append(np.array([(i.year == 2020 and i.month in (3, 4, 5)) for i in idx]).astype(float))
    res = []
    for k in range(int(n * trim), int(n * (1 - trim))):
        st = (t >= k).astype(float)
        X = np.column_stack([st] + base)
        b, se, u = hac_ols(y, X, lags=lags)
        res.append((idx[k], b[0], se[0], b[0] / se[0]))
    return pd.DataFrame(res, columns=['mese', 'b', 'se', 't'])
def sup_perm(y, idx, B=300, seed=SEED):
    """Soglia per sup-t col bootstrap a blocchi dei residui del modello senza rottura."""
    n = len(y); t = np.arange(n); md = pd.get_dummies(idx.month, drop_first=True).values.astype(float)
    X0 = np.column_stack([np.ones(n), t, md, np.array([(i.year == 2020 and i.month in (3, 4, 5)) for i in idx]).astype(float)])
    b0 = np.linalg.lstsq(X0, y, rcond=None)[0]; u0 = y - X0 @ b0
    rng = np.random.default_rng(seed); out = []
    for _ in range(B):
        st_ = rng.integers(0, n - 6, n // 6 + 1); uu = np.concatenate([u0[s:s + 6] for s in st_])[:n]
        ys = X0 @ b0 + uu
        out.append(rottura(ys, idx).t.abs().max())
    return np.percentile(out, 95)
for tp, nm in [('CP572', 'Maltrattamenti'), ('CP612BIS', 'Stalking')]:
    sub = r[r.tipo_codice == tp]
    piv = sub.pivot_table(index=['anno', 'mese'], columns='territorio', values='denunce', aggfunc='sum')
    piv.index = pd.PeriodIndex([f'{a}-{m:02d}' for a, m in piv.index], freq='M').to_timestamp()
    say(f'\n{nm}: colonne {list(piv.columns)} n={len(piv)} {piv.index.min().date()} {piv.index.max().date()}')
    say(' annuo:', piv.groupby(piv.index.year).sum().round(0).astype(int).to_dict())
    mi = [c for c in piv.columns if 'ilano' in c][0]; it = [c for c in piv.columns if 'talia' in c][0]
    yy = {'Italia': np.log(piv[it].values), 'Milano': np.log(piv[mi].values), 'Milano-Italia': np.log(piv[mi].values) - np.log(piv[it].values)}
    for k, y in yy.items():
        R = rottura(y, piv.index)
        top = R.iloc[R.t.abs().argmax()]
        thr = sup_perm(y, piv.index, B=200)
        say(f' {k:14s} rottura {top.mese.date()} gradino {(np.exp(top.b) - 1) * 100:+.1f}% (t {top.t:.1f}), soglia 95% sup-t {thr:.1f}; altri picchi:', R.sort_values('t', key=abs, ascending=False).head(4)[['mese', 'b', 't']].assign(mese=lambda d: d.mese.dt.strftime('%Y-%m')).round(2).values.tolist())
    # Finestre fisse: prima/dopo agosto 2019, marzo 2020, gennaio 2023
    for dt in ['2019-08-01', '2020-03-01', '2023-01-01']:
        t0 = pd.Timestamp(dt)
        for k, y in yy.items():
            idx = piv.index; t = np.arange(len(y)); md = pd.get_dummies(idx.month, drop_first=True).values.astype(float); X = np.column_stack([(idx >= t0).astype(float), np.ones(len(y)), t, md, np.array([(i.year == 2020 and i.month in (3, 4, 5)) for i in idx]).astype(float)])
            b, se, u = hac_ols(y, X, lags=6); say(f'  gradino {dt} {k:14s} {(np.exp(b[0]) - 1) * 100:+.1f}% (t {b[0] / se[0]:.1f})')
    ri = piv[mi] / piv[it]; say(' quota Milano su Italia per anno %', (piv[mi].groupby(piv.index.year).sum() / piv[it].groupby(piv.index.year).sum() * 100).round(2).to_dict())
    # ottobre-novembre: mese per mese attorno
    say(' Mesi Italia 2019:', piv[it]['2019'].astype(int).tolist(), ' Milano 2019:', piv[mi]['2019'].astype(int).tolist())

# ===== L
say('\n===== L')
tur = pd.read_csv(p('turisti', 'pulito', 'milano_mensile_totale.csv'))
air = pd.read_csv(p('docs', 'aeroporti', 'data', 'mensile_tre_aeroporti.csv'), sep=';')
say(tur.groupby('anno').presenze.agg(['size', 'sum']).to_string())
say(air.pivot_table(index='anno', columns='aeroporto', values='passeggeri', aggfunc='sum').loc[2018:].to_string())
A = air.pivot_table(index=['anno', 'mese'], columns='aeroporto', values='passeggeri', aggfunc='sum')
T_ = tur.set_index(['anno', 'mese']).presenze
D = A.join(T_, how='inner'); D.index = pd.PeriodIndex([f'{a}-{m:02d}' for a, m in D.index], freq='M').to_timestamp()
say('colonne', list(D.columns), 'mesi', D.index.min().date(), D.index.max().date(), len(D))
say('Mesi con voli a Linate:', D['Linate'][D.index.year == 2019].astype(int).tolist() if 'Linate' in D else 'colonna diversa')
AER = [c for c in D.columns if c != 'presenze']
D['MXP+LIN'] = D['Malpensa'] + D['Linate']; D['Tutti'] = D[AER].sum(axis=1)
def resid(S, idx, covid_out, trend=True):
    """Toglie mese dell'anno e tendenza lineare sul log per regime."""
    m = ~covid_out
    y = np.log(S.values[m]); i = idx[m]; t = np.arange(len(S))[m]
    X = [np.ones(m.sum()), pd.get_dummies(i.month, drop_first=True).values.astype(float)]
    if trend:
        X += [t, t ** 2.]
    X = np.column_stack(X)
    return pd.Series(y - X @ np.linalg.lstsq(X, y, rcond=None)[0], index=i)
def rmix(a_, b_, k=4, B=4000, seed=SEED):
    a_, b_ = a_.align(b_, join='inner')
    r0 = np.corrcoef(a_, b_)[0, 1]; s0 = stats.spearmanr(a_, b_).statistic
    n = len(a_); rng = np.random.default_rng(seed); bs = []
    for _ in range(B):
        st_ = rng.integers(0, n - k + 1, n // k + 1); ii = np.concatenate([np.arange(s, s + k) for s in st_])[:n]
        bs.append(np.corrcoef(a_.values[ii], b_.values[ii])[0, 1])
    return r0, s0, np.percentile(bs, [2.5, 97.5]), n
regimi = {'senza Covid (2020-02..2022-03 fuori)': (D.index >= '2020-02-01') & (D.index <= '2022-03-01'),
          'come sopra e senza Linate chiuso lug-ott 2019': ((D.index >= '2020-02-01') & (D.index <= '2022-03-01')) | ((D.index >= '2019-07-01') & (D.index <= '2019-11-01')),
          'solo 2022-04..fine': D.index < '2022-04-01',
          'solo 2022-04..2024-12 (senza 2025)': (D.index < '2022-04-01') | (D.index >= '2025-01-01')}
rows = []
for k, out in regimi.items():
    say(f'\nRegime: {k}')
    rp = resid(D.presenze, D.index, out)
    say(' mesi usati', (~out).sum())
    for c in AER + ['MXP+LIN', 'Tutti']:
        ra = resid(D[c], D.index, out)
        r0, s0, ci, n_ = rmix(rp, ra)
        say(f'  {c:10s} n={n_} Pearson {r0:+.3f} [{ci[0]:+.3f},{ci[1]:+.3f}] Spearman {s0:+.3f}')
        rows.append(dict(regime=k, aer=c, n=n_, r=r0, lo=ci[0], hi=ci[1], sp=s0))
    # differenza appaiata
    ress = {c: resid(D[c], D.index, out) for c in AER}
    rng = np.random.default_rng(SEED); n_ = len(rp); k_ = 4
    names = AER; diffs = {f'{a_}-{b_}': [] for i, a_ in enumerate(names) for b_ in names[i + 1:]}
    for _ in range(4000):
        st_ = rng.integers(0, n_ - k_ + 1, n_ // k_ + 1); ii = np.concatenate([np.arange(s, s + k_) for s in st_])[:n_]
        rr = {c: np.corrcoef(rp.values[ii], ress[c].values[ii])[0, 1] for c in names}
        for kk in diffs:
            a_, b_ = kk.split('-'); diffs[kk].append(rr[a_] - rr[b_])
    for kk, vv in diffs.items():
        say(f'  differenza {kk}: IC', np.round(np.percentile(vv, [2.5, 97.5]), 3))
    # senza tendenza quadratica: variazione annua
yo = np.log(D[AER + ['presenze']]).diff(12).dropna()
yo = yo[(yo.index >= '2023-04-01')]
say('\nVariazione sullo stesso mese anno prima, dal 2023-04, n=', len(yo))
for c in AER:
    r0, s0, ci, n_ = rmix(yo.presenze, yo[c]); say(f'  {c:10s} Pearson {r0:+.3f} [{ci[0]:+.3f},{ci[1]:+.3f}] Spearman {s0:+.3f}')
# Salone/settimane moda: i residui più grandi
out = regimi['senza Covid (2020-02..2022-03 fuori)']; rp = resid(D.presenze, D.index, out)
say('Residui presenze più grandi:', rp.sort_values(key=abs, ascending=False).head(8).round(3).rename(lambda d: d.strftime('%Y-%m')).to_dict())
# Quante osservazioni servirebbero: ampiezza
say('Ampiezza IC con n=57 e r=0.5: circa +-', round(1.96 * (1 - .25) / np.sqrt(57), 2))
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'L_correlazioni.csv'), index=False)
L.close()
