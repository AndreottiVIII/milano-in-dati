"""Due tabelle in piu' per la pagina Redditi:
 - cap_nomi_zone.csv: per ogni CAP di Milano il quartiere in cui cadono piu' civici (da docs/citta-15-minuti/data/esagoni_cap.json)
 - cap_divario_citta_2011_2024.csv: divario tra CAP (rapporto tra CAP al 90 e al 10 per cento) per citta' con almeno 15 CAP
Uso: python -I -X utf8 dati_pagina_v2.py <ABS milano-in-dati>"""
import sys, json
import pandas as pd
R = sys.argv[1]
e = json.load(open(R + '/docs/citta-15-minuti/data/esagoni_cap.json', encoding='utf-8'))
pd.DataFrame({'cap': e['caps'], 'zona': e['zona']}).to_csv(R + '/docs/redditi/data/cap_nomi_zone.csv', index=False)
d = pd.read_csv(R + '/redditi/pulito/cap_divario_per_citta.csv')
d = d[(d.n_cap >= 15) & ~d.comune.str.contains('uniti')]
d = d.dropna(subset=['p90_su_p10'])
d = d[d.anno_imposta.isin([2011, 2024])][['comune', 'anno_imposta', 'n_cap', 'p90_su_p10']]
d['comune'] = d.comune.str.title()
d['p90_su_p10'] = d.p90_su_p10.round(3)
d.to_csv(R + '/docs/redditi/data/cap_divario_citta_2011_2024.csv', index=False)
print(d[d.anno_imposta == 2024].sort_values('p90_su_p10', ascending=False).to_string())
