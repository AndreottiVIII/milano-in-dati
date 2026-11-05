"""Statali contro paritarie a Milano sui punteggi INVALSI 2024/25, dalle pagine pubbliche.
Uso: python -I -X utf8 invalsi_paritarie_confronto.py <cartella scuole>
Confronta punteggio rispetto alla Lombardia e differenza da scuole con contesto simile, prova per prova.
"""
import glob, json, os, sys
import numpy as np
import pandas as pd

B = sys.argv[1]
pd.set_option('display.width', 200, 'display.max_columns', 20, 'display.max_rows', 200, 'display.max_colwidth', 44)
P = os.path.join(B, 'pulito')
tot = []
for f in glob.glob(os.path.join(B, 'raw', 'invalsi_rav_par', '*.json')):
    d = json.load(open(f, encoding='utf8'))
    tot.append(dict(ist=d['istituto'], tipo=d['tipo'], http=d.get('http'), righe=len(d['righe']), anni=';'.join(d['anni']), punt=sum(r.get('punteggio') is not None for r in d['righe'])))
T = pd.DataFrame(tot)
print('paritarie provate', len(T))
print(T.assign(pag=T.http == 200, con=T.punt > 0).groupby('tipo')[['pag', 'con']].agg(['size', 'sum']).to_string())
print(T[T.punt > 0].anni.value_counts().to_dict())


def n(d):
    d = d.copy()
    for c in ('punteggio', 'lombardia', 'diff_escs', 'partecipazione', 'copertura_background'):
        d[c] = pd.to_numeric(d.get(c), errors='coerce')
    d['scarto'] = d.punteggio - d.lombardia
    return d


par = n(pd.read_csv(os.path.join(P, 'invalsi_paritarie.csv'), sep=';', encoding='utf-8-sig', dtype={'istituto': str}))
par = par[par.anni.str.contains('2024/2025', na=False) & par.scarto.notna()]
pc = n(pd.read_csv(os.path.join(P, 'invalsi_istituti.csv'), sep=';', encoding='utf-8-sig', dtype={'istituto': str}))
pc = pc[pc.anni.astype(str).str.contains('2024/2025') & pc.scarto.notna()]
su = n(pd.read_csv(os.path.join(P, 'invalsi_superiori.csv'), sep=';', encoding='utf-8-sig', dtype={'istituto': str}))
su = su[su.scarto.notna()]
st = pd.concat([pc.assign(gest='statale'), su.assign(gest='statale')], ignore_index=True)
par = par.assign(gest='paritaria')
tutti = pd.concat([st, par], ignore_index=True)
tutti = tutti[tutti.materia.isin(['Italiano', 'Matematica'])]


def boot(s, r=2000):
    v = s.dropna().values
    if len(v) < 3:
        return (np.nan, np.nan)
    rng = np.random.default_rng(1)
    m = [rng.choice(v, len(v)).mean() for _ in range(r)]
    return tuple(np.percentile(m, [2.5, 97.5]))


righe = []
for (gr, mat), x in tutti.groupby(['grado', 'materia']):
    a, b = x[x.gest == 'statale'], x[x.gest == 'paritaria']
    if len(b) < 3 or len(a) < 3:
        continue
    d = lambda col: (b[col].mean() - a[col].mean())
    righe.append(dict(prova=gr[:58], materia=mat[:3], stat=a.istituto.nunique(), par=b.istituto.nunique(), stat_sc=a.scarto.mean(), par_sc=b.scarto.mean(), diff_sc=d('scarto'), stat_ct=a.diff_escs.mean(), par_ct=b.diff_escs.mean(), diff_ct=d('diff_escs'), part_st=a.partecipazione.mean(), part_par=b.partecipazione.mean()))
R = pd.DataFrame(righe).round(1)
print(R.to_string(index=False))
R.to_csv(os.path.join(P, 'invalsi_statali_paritarie.csv'), sep=';', index=False, encoding='utf-8-sig')
print('\nParitarie con punteggi, per istituto (5a primaria e 3a media e licei): prime e ultime')
x = par[par.materia == 'Italiano']
for gr, s in x.groupby('grado'):
    if s.istituto.nunique() >= 5:
        s = s.sort_values('scarto', ascending=False)
        print(gr[:60], len(s))
        print(s[['nome', 'punteggio', 'lombardia', 'scarto', 'diff_escs', 'partecipazione']].round(1).head(4).to_string(index=False, header=False))
        print(s[['nome', 'punteggio', 'lombardia', 'scarto', 'diff_escs', 'partecipazione']].round(1).tail(2).to_string(index=False, header=False))
