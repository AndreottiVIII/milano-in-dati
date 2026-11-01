"""Passo 4: tabelle di sintesi (nel tempo) a partire da out/gradiente_per_voce.csv e out/robustezza.csv.
Uso: python -I -X utf8 31_sintesi.py <voto-reddito>"""
import sys, os
import pandas as pd
OUT = os.path.join(sys.argv[1], 'out')
r = pd.read_csv(os.path.join(OUT, 'gradiente_per_voce.csv'))
ELE = ['comunali_sindaco_2016-06-05', 'camera_2018-03-04', 'regionali_consiglio_2018-03-04', 'europee_2019-05-26', 'comunali_sindaco_2021-10-03',
       'camera_2022-09-25', 'regionali_consiglio_2023-02-12', 'europee_2024-06-08']
VOCI = {'Centrosinistra': 'PD e affini (Centrosinistra)', 'Sx (Sinistra+Centrosinistra)': 'Sx', 'Centro': 'Centro', 'Sx+Centro (Sinistra+Centrosinistra+Centro)': 'Sx+Centro',
        'Dx (Centrodestra+Lega+Destra)': 'Dx', 'M5S': 'M5S', 'AFFLUENZA': 'Affluenza'}
rows = []
for e in ELE:
    for v, lab in VOCI.items():
        k = r[(r.elezione_id == e) & (r.voce == v)]
        if len(k) == 0:
            continue
        k = k.iloc[0]
        rows.append(dict(elezione=k.etichetta, data=k.data, voce=lab, quota_citta=k.quota_citta_pct, D1=k.quota_D1_pct, D9=None, D10=k.quota_D10_pct,
                         gap_D10_D1=k.gap_D10_D1_pp, ic=f'{k.gap_ic_lo:+.1f}/{k.gap_ic_hi:+.1f}', gap_D9_D1=k.gap_D9_D1_pp,
                         spearman_cap=k.spearman_cap, sp_ic=f'{k.sp_ic_lo:+.2f}/{k.sp_ic_hi:+.2f}'))
t = pd.DataFrame(rows)
d = pd.read_csv(os.path.join(OUT, 'decili_per_voce.csv'))
t['D9'] = [d[(d.elezione_id == r[(r.etichetta == a)].elezione_id.iloc[0]) & (d.voce == [k for k, l in VOCI.items() if l == v][0]) & (d.decile == 9)].quota_pct.iloc[0]
           for a, v in zip(t.elezione, t.voce)]
t.to_csv(os.path.join(OUT, 'sintesi_nel_tempo.csv'), index=False, encoding='utf-8-sig')
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 300)
print(t.to_string())
