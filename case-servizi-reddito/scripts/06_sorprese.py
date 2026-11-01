"""Zone in cui prezzo e servizi non vanno d'accordo: residui dei modelli e scarto fra posizione in classifica servizi e posizione in classifica prezzo.
Uso: python -I -X utf8 06_sorprese.py <ABS case-servizi-reddito>
Entrata: out/zone_tabella.csv. Uscita: out/sorprese_zone.csv
Prezzi = stime OMI (Agenzia delle Entrate), non prezzi di vendita. Campione: 41 zone (senza D39 e R2).
Residuo A: ln(prezzo) rispetto a quello 'atteso' dai soli servizi su 20. Residuo B: rispetto al modello servizi + ln(distanza) + ln(reddito).
Un residuo di +0,20 vuol dire circa +22% sopra l'atteso.
"""
import sys
import numpy as np, pandas as pd

O = sys.argv[1].replace(chr(92), '/').rstrip('/')
t = pd.read_csv(O + '/out/zone_tabella.csv')
t = t[(t.prezzo_eur_m2.notna()) & (t.zona != 'D39')].copy()
t['lnP'] = np.log(t.prezzo_eur_m2)
t['lnD'] = np.log(t.dist_duomo_centroide_m / 1000)
t['lnY'] = np.log(t.reddito_imponibile_medio_2024_pesato)

def resid(cols):
    X = np.column_stack([np.ones(len(t)), t[cols].values])
    b = np.linalg.lstsq(X, t.lnP.values, rcond=None)[0]
    return t.lnP.values - X @ b, np.exp(X @ b)

t['residuo_A_solo_servizi'], t['prezzo_atteso_A'] = resid(['servizio20'] if False else ['servizi20_pesato'])
t['residuo_B_con_distanza_reddito'], t['prezzo_atteso_B'] = resid(['servizi20_pesato', 'lnD', 'lnY'])
t['residuo_C_distanza_reddito_senza_servizi'], t['prezzo_atteso_C'] = resid(['lnD', 'lnY'])
t['rango_servizi20'] = t.servizi20_pesato.rank(ascending=False)
t['rango_servizi10'] = t.servizi10_pesato.rank(ascending=False)
t['rango_prezzo'] = t.prezzo_eur_m2.rank(ascending=False)
t['rango_reddito'] = t.reddito_imponibile_medio_2024_pesato.rank(ascending=False)
t['scarto_rango_servizi10_meno_prezzo'] = t.rango_prezzo - t.rango_servizi10
t['scarto_rango_servizi20_meno_prezzo'] = t.rango_prezzo - t.rango_servizi20
cols = ['zona', 'nome', 'n_civici_residenziali', 'servizi10_pesato', 'servizi20_pesato', 'reddito_imponibile_medio_2024_pesato',
        'dist_duomo_centroide_m', 'prezzo_eur_m2', 'prezzo_atteso_A', 'residuo_A_solo_servizi', 'prezzo_atteso_B', 'residuo_B_con_distanza_reddito',
        'rango_servizi10', 'rango_servizi20', 'rango_prezzo', 'scarto_rango_servizi10_meno_prezzo', 'scarto_rango_servizi20_meno_prezzo']
t[cols].sort_values('residuo_B_con_distanza_reddito').to_csv(O + '/out/sorprese_zone.csv', index=False, float_format='%.4f')
pd.set_option('display.width', 250)
pd.set_option('display.max_colwidth', 40)
v = t[cols].round(3)
print('--- servizi 10: piu alti nei primi posti ma prezzo basso (rango prezzo - rango servizi10 grande = servito ma economico)')
print(v.sort_values('scarto_rango_servizi10_meno_prezzo', ascending=False)[['zona', 'nome', 'servizi10_pesato', 'rango_servizi10', 'rango_prezzo', 'prezzo_eur_m2', 'reddito_imponibile_medio_2024_pesato']].head(8).to_string())
print('--- servizi 10: caro con pochi servizi')
print(v.sort_values('scarto_rango_servizi10_meno_prezzo')[['zona', 'nome', 'servizi10_pesato', 'rango_servizi10', 'rango_prezzo', 'prezzo_eur_m2']].head(8).to_string())
print('--- servizi 20: servito ma economico')
print(v.sort_values('scarto_rango_servizi20_meno_prezzo', ascending=False)[['zona', 'nome', 'servizi20_pesato', 'rango_servizi20', 'rango_prezzo', 'prezzo_eur_m2']].head(8).to_string())
print('--- servizi 20: caro con pochi')
print(v.sort_values('scarto_rango_servizi20_meno_prezzo')[['zona', 'nome', 'servizi20_pesato', 'rango_servizi20', 'rango_prezzo', 'prezzo_eur_m2']].head(8).to_string())
print('--- residuo B (modello con controlli): piu cari / piu economici del previsto')
print(v.sort_values('residuo_B_con_distanza_reddito')[['zona', 'nome', 'prezzo_eur_m2', 'prezzo_atteso_B', 'residuo_B_con_distanza_reddito']].head(6).to_string())
print(v.sort_values('residuo_B_con_distanza_reddito', ascending=False)[['zona', 'nome', 'prezzo_eur_m2', 'prezzo_atteso_B', 'residuo_B_con_distanza_reddito']].head(6).to_string())
print('--- residuo A (solo servizi)')
print(v.sort_values('residuo_A_solo_servizi')[['zona', 'nome', 'servizi20_pesato', 'prezzo_eur_m2', 'prezzo_atteso_A', 'residuo_A_solo_servizi']].head(6).to_string())
print(v.sort_values('residuo_A_solo_servizi', ascending=False)[['zona', 'nome', 'servizi20_pesato', 'prezzo_eur_m2', 'prezzo_atteso_A', 'residuo_A_solo_servizi']].head(6).to_string())
