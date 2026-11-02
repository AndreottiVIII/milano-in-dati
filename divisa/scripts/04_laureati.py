"""04: quanto sono separati laureati e non laureati tra i 88 quartieri (NIL), censimenti 1991, 2001, 2011, 2021, 2023 (complemento al reddito).
Entrata: censimenti/pulito/indicatori_NIL.csv (campi grad = laureati, edu_base = popolazione di 6+ anni nel 1991-2011 e di 9+ nel 2021-2023);
         censimenti/pulito/variazioni_NIL_1991_2023.csv (campo robusto = 66 NIL con confini stabili tra 1991 e 2023).
Uscita in divisa/out/: laureati_serie.csv
Uso: python -I -X utf8 04_laureati.py <milano-in-dati assoluto> <divisa assoluto>
Misure: D laureati / non laureati; isolamento dei laureati; confronto su tutti i 88 NIL e sui 66 robusti. Intervalli: ricampionamento (200); valore a caso (50)."""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import misure as M

BASE, DIV = sys.argv[1], sys.argv[2]
d = pd.read_csv(os.path.join(BASE, 'censimenti', 'pulito', 'indicatori_NIL.csv'))
v = pd.read_csv(os.path.join(BASE, 'censimenti', 'pulito', 'variazioni_NIL_1991_2023.csv'))
rob = set(v.loc[v.robusto == True, 'nil'].astype(int))
rng = np.random.default_rng(91)
f = lambda R: M.dissimilarita(R[:, 0], R[:, 1])
rows = []
for anno, g in d.groupby('anno'):
    for nome, h in [('88 NIL', g), ('66 NIL con confini stabili', g[g.nil.astype(int).isin(rob)])]:
        h = h[h.edu_base > 0]
        C = np.column_stack([h.grad.to_numpy(float), (h.edu_base - h.grad).to_numpy(float)])
        _, lo, hi = M.bootstrap(C, f, 200, rng)
        rows.append(dict(anno=int(anno), insieme=nome, n_nil=len(h), laureati=int(C[:, 0].sum()), base=int(C.sum()), quota_laureati=C[:, 0].sum() / C.sum(),
                         d=f(C), d_lo=lo, d_hi=hi, d_base=M.basale(C, f, 50, rng)[0], iso_laureati=M.isolamento(C[:, 0], C.sum(1))))
S = pd.DataFrame(rows)
S.to_csv(os.path.join(DIV, 'out', 'laureati_serie.csv'), index=False, float_format='%.5f')
print(S.round(3).to_string())
