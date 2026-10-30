"""Fase 4 (servizi extra), passo 3: dati per la pagina (docs/citta-15-minuti/data/extra.json + due CSV). Non tocca i file di dati della fase 3.
Uso: python -I f4_dati.py <ABS strand citta-15-minuti> <ABS docs/citta-15-minuti>
Regole della fase 3 mantenute: Cascina Merlata (ID_NIL 73) senza punteggio, fuori da classifiche e dal confronto con i redditi; classifica solo NIL con >=30 civici e >=1.000 residenti."""
import sys, json, os
import numpy as np, pandas as pd
from scipy.stats import spearmanr
S = sys.argv[1]; D = sys.argv[2]; O = S + '/out/'; DD = D + '/data/'
CM = 73; SOGLIA = 15.0
EX = ['cinema', 'teatri_musei', 'giochi', 'piscine', 'cani', 'metro', 'bikemi', 'supermercati', 'ospedali', 'librerie']
ETI = {'cinema': 'Cinema (aperti oggi)', 'teatri_musei': 'Teatri e musei', 'giochi': 'Aree gioco per bambini', 'piscine': 'Piscine', 'cani': 'Aree cani',
       'metro': 'Fermate della metropolitana', 'bikemi': 'Stazioni BikeMi (dato 2022)', 'supermercati': 'Supermercati', 'ospedali': 'Ospedali', 'librerie': 'Librerie'}
R = json.load(open(O + 'f4_risultati.json', encoding='utf-8')); L = json.load(open(O + 'f4_servizi_log.json', encoding='utf-8'))['servizi']
nilg = json.load(open(DD + 'nil.geojson', encoding='utf-8'))
NS = {int(f['properties']['i']): f['properties'] for f in nilg['features']}
ne = pd.read_csv(O + 'nil_punteggi_extra.csv'); ne = ne[ne.ID_NIL != CM]
c = pd.read_csv(O + 'civici_tempi_extra.csv', dtype={'CAP': str})
# ---------- NIL
nil = {}
for _, r in ne.iterrows():
    i = int(r.ID_NIL)
    if i not in NS: continue
    nil[i] = [round(float(r.punteggio_medio_extra), 2), round(float(r.punteggio_medio_20), 2), round(float(r.tutti20), 3)] + [round(float(r['in_' + t]), 3) for t in EX]
# ---------- esagoni (stessi, nello stesso ordine, di esagoni.json)
H = pd.read_csv(O + 'hex100_extra.csv'); HX = json.load(open(DD + 'esagoni.json'))
assert len(H) == len(HX['x']), 'esagoni diversi dalla fase 3'
hexe = {'pe': [int(round(v * 10)) for v in H.pe], 'p20': [int(round(v * 10)) for v in (H.p20)],
        't': {t: [(-1 if v >= 99 else int(round(v * 10))) for v in H['m_' + t]] for t in EX}}
# ---------- tabella dei tipi
sv = pd.read_csv(O + 'extra_servizi_puliti.csv')
tipi = []
for t in EX:
    l = L[t]; tipi.append({'t': t, 'nome': ETI[t], 'q': R['quota_residenti_entro15'][t], 'med': R['minuti_mediani_pesati'][t], 'n': int(l['finali']), 'fonte': l['fonte'], 'anno': l['anno'], 'nota': l['note']})
tipi.sort(key=lambda z: -z['q'])
# ---------- classifica con extra (solo NIL 'ok')
ok = [i for i, p in NS.items() if p['s'] == 'ok' and i in nil]
d10 = {i: NS[i]['p'] for i in ok}; d20 = {i: nil[i][1] for i in ok}
o10 = sorted(ok, key=lambda i: -d10[i]); o20 = sorted(ok, key=lambda i: -d20[i])
p10 = {i: k + 1 for k, i in enumerate(o10)}; p20 = {i: k + 1 for k, i in enumerate(o20)}
def riga(i): return {'i': i, 'n': NS[i]['n'], 'p10': round(d10[i], 2), 'pe': nil[i][0], 'p20': nil[i][1], 'pos10': p10[i], 'pos20': p20[i]}
salto = sorted(ok, key=lambda i: p10[i] - p20[i])
# ---------- CAP senza Cascina Merlata, punteggio esteso
res = c[(c.RESIDENZIALE == 1) & c.ID_NIL.notna()].copy()
nilc = pd.read_csv(O + 'nil_punteggi.csv'); pop = nilc.set_index('ID_NIL').residenti_2025
cnt = res.groupby('ID_NIL').size(); res['peso'] = res.ID_NIL.map(pop) / res.ID_NIL.map(cnt); res = res[res.peso.notna() & (res.ID_NIL != CM)].copy()
for t in EX: res['in_' + t] = res['min_' + t] <= SOGLIA
def wavg(g, col): return float((g[col].astype(float) * g.peso).sum() / g.peso.sum())
rows = []
for k, g in res.groupby('CAP'):
    rows.append({'CAP': k, 'p10': wavg(g, 'punteggio'), 'pe': wavg(g, 'punteggio_extra'), 'p20': wavg(g, 'punteggio_20'), **{t: wavg(g, 'in_' + t) for t in EX}})
cp = pd.DataFrame(rows).merge(pd.read_csv(O + 'cap_redditi_servizi.csv', dtype={'CAP': str})[['CAP', 'imponibile_medio_2024']], on='CAP')
def sp_ci(a, b, nb=5000, seed=7):
    rho = spearmanr(a, b)[0]; rng = np.random.default_rng(seed); n = len(a); bs = []
    for _ in range(nb):
        ix = rng.integers(0, n, n)
        if len(np.unique(a[ix])) < 2 or len(np.unique(b[ix])) < 2: continue
        bs.append(spearmanr(a[ix], b[ix])[0])
    return [round(float(rho), 2), round(float(np.percentile(bs, 2.5)), 2), round(float(np.percentile(bs, 97.5)), 2)]
inc = cp.imponibile_medio_2024.values
cap = {'n': int(len(cp)), 'rho_10': sp_ci(cp.p10.values, inc), 'rho_extra': sp_ci(cp.pe.values, inc), 'rho_20': sp_ci(cp.p20.values, inc),
       'cor_tipo': {t: round(float(spearmanr(cp[t], inc)[0]), 2) for t in EX}}
q33 = np.quantile(inc, 1 / 3); q67 = np.quantile(inc, 2 / 3)
cp['terzo'] = np.where(inc <= q33, 'basso', np.where(inc >= q67, 'alto', 'medio'))
cap['terzi'] = {k: {'p10': round(float(g.p10.mean()), 2), 'pe': round(float(g.pe.mean()), 2)} for k, g in cp.groupby('terzo')}
# ---------- citta (senza Cascina Merlata: i numeri della citta sono quelli della fase 2, con tutti i residenti)
out = {'ordine': EX, 'etichette': ETI, 'tipi': tipi,
       'ps': {'q': R['quota_residenti_entro15']['ospedali_con_pronto_soccorso'], 'n': L['ospedali']['con_pronto_soccorso'], 'med': R['minuti_mediani_pesati']['ospedali_ps']},
       'tm': {'teatri': L['teatri_musei']['teatri'], 'musei': L['teatri_musei']['musei'], 'q_teatri': R['quota_residenti_entro15']['solo_teatri'], 'q_musei': R['quota_residenti_entro15']['solo_musei']},
       'citta': {'pe': R['punteggio_medio']['extra_0_10'], 'p20': R['punteggio_medio']['totale_0_20'], 'tutti_extra': R['quota_con_tutti']['10_extra'], 'tutti20': R['quota_con_tutti']['tutti_20'],
                 'dist_extra': R['distribuzione_punteggio_extra'], 'rho_civici': R['spearman_civici_10_vs_extra'], 'rho_classifica_nil': R['spearman_classifica_NIL_10_vs_20']},
       'nil': nil, 'hex': hexe, 'cap': cap, 'rank_n': len(ok),
       'top20': [riga(i) for i in o20[:5]], 'bottom20': [riga(i) for i in o20[::-1][:5]],
       'salgono': [riga(i) for i in salto[::-1][:5]], 'scendono': [riga(i) for i in salto[:5]]}
json.dump(out, open(DD + 'extra.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
# ---------- CSV scaricabili (con i nomi dei NIL come nel CSV della fase 3)
n3 = pd.read_csv(DD + 'nil_punteggi.csv')
ex = ne.rename(columns={'punteggio_medio_extra': 'punteggio_extra_su_10', 'punteggio_medio_20': 'punteggio_totale_su_20', 'tutti20': 'quota_residenti_con_tutti_i_20_servizi'})
ex = ex[['ID_NIL', 'punteggio_extra_su_10', 'punteggio_totale_su_20', 'quota_residenti_con_tutti_i_20_servizi'] + ['in_' + t for t in EX]]
ex = ex.rename(columns={'in_' + t: 'quota_entro15_' + t for t in EX})
m = n3[['ID_NIL', 'NIL', 'residenti_2025', 'stato']].merge(ex, on='ID_NIL', how='left')
m.loc[m.ID_NIL == CM, [c_ for c_ in m.columns if c_.startswith(('punteggio', 'quota'))]] = np.nan
m.round(4).to_csv(DD + 'nil_punteggi_extra.csv', index=False, encoding='utf-8')
cc = cp.rename(columns={'p10': 'punteggio_essenziali_su_10', 'pe': 'punteggio_extra_su_10', 'p20': 'punteggio_totale_su_20', 'imponibile_medio_2024': 'imponibile_medio_2024'}).drop(columns='terzo')
cc = cc.rename(columns={t: 'quota_entro15_' + t for t in EX})
cc.round(4).to_csv(DD + 'cap_punteggi_extra.csv', index=False, encoding='utf-8')
for f in ['extra.json', 'nil_punteggi_extra.csv', 'cap_punteggi_extra.csv']: print(f, os.path.getsize(DD + f))
print(json.dumps({k: out[k] for k in ['citta', 'cap', 'top20', 'bottom20', 'salgono', 'scendono']}, ensure_ascii=False, indent=1)[:5000])
