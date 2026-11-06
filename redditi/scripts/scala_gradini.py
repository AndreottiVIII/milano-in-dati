"""Gradini di reddito a soglie costanti in euro di oggi, Milano, 2000-2024.
Le 8 classi MEF hanno soglie fisse in euro correnti; qui le soglie del 2000 (10.000, 15.000, 26.000, 55.000 euro)
sono spostate con l'inflazione (FOI) e le quote si ricavano per interpolazione lineare dentro la classe
(contribuenti spalmati in modo uniforme nella classe; soldi in proporzione al punto medio).
Uso: python -I -X utf8 scala_gradini.py <ABS milano-in-dati>
Scrive docs/redditi/data/scala_gradini_milano.csv"""
import sys
import numpy as np, pandas as pd
R = sys.argv[1]
cl = pd.read_csv(R + '/redditi/pulito/mef_comuni_2000_2024.csv', dtype={'catastale': str}, low_memory=False)
m = cl[(cl.comune.str.upper() == 'MILANO') & (cl.prov == 'MI')].sort_values('anno')
foi = pd.read_csv(R + '/prezzi-case/pulito/foi_annuale.csv').set_index('anno').indice_raccordato_2025_100
cols = ['cl1_0_10k', 'cl2_10_15k', 'cl3_15_26k', 'cl4_26_55k', 'cl5_55_75k', 'cl6_75_120k', 'cl7_oltre120k']
edges = [0, 10000, 15000, 26000, 55000, 75000, 120000]
TH = [10000, 15000, 26000, 55000]  # soglie del 2000, in euro del 2000
rows = []
for _, r in m.iterrows():
    y = int(r.anno)
    k = foi[y] / foi[2000]                      # euro dell'anno per ogni euro del 2000
    n = [r['cl0_le0_n']] + [r[c + '_n'] for c in cols]
    e = [r['cl0_le0_eur']] + [r[c + '_eur'] for c in cols]
    n = np.array(n, float); e = np.array(e, float)
    totn = n.sum(); tote = e.sum()
    lo = [None] + edges  # inizio classi (classe 0 = <=0)
    def cum(x):
        """contribuenti e soldi con reddito < x (euro dell'anno), x <= 120000"""
        cn = n[0]; ce = e[0]
        for i, c in enumerate(cols):
            a = edges[i]; b = edges[i + 1] if i + 1 < len(edges) else None
            if b is None: break
            if x >= b: cn += n[i + 1]; ce += e[i + 1]
            elif x > a:
                f = (x - a) / (b - a); mid_part = (a + x) / 2; mid_all = (a + b) / 2
                cn += n[i + 1] * f
                ce += e[i + 1] * f * mid_part / mid_all
                break
            else: break
        return cn, ce
    pts = [(0, 0)] + [cum(t * k) for t in TH] + [(totn, tote)]
    for g in range(5):
        dn = pts[g + 1][0] - pts[g][0]; de = pts[g + 1][1] - pts[g][1]
        rows.append({'anno_imposta': y, 'gradino': g + 1, 'quota_contribuenti': round(dn / totn, 5), 'quota_reddito': round(de / tote, 5),
                     'da_euro_2025': round(([0] + TH)[g] * foi[2000] and ([0] + TH)[g] * 100 / foi[2000]) if g else 0})
df = pd.DataFrame(rows)
df.to_csv(R + '/docs/redditi/data/scala_gradini_milano.csv', index=False)
print(df[df.anno_imposta.isin([2000, 2006, 2024])].to_string())
print(100 / foi[2000])
