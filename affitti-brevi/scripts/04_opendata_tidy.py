r"""Fase 1 - tabelle ordinate dai dati aperti ufficiali (PoliS-Lombardia/ISTAT e Comune di Milano).
Uso: python -I -X utf8 04_opendata_tidy.py <cartella affitti-brevi (assoluta)>
Scrive in pulito\ : ufficiale_strutture_milano.csv (lunga: fonte, serie, periodo, tipo, strutture, posti_letto)
                    ufficiale_flussi_milano.csv   (PoliS/ISTAT: anno, tipo struttura, cittadinanza, arrivi, presenze)
"""
import sys, csv
from pathlib import Path
import pandas as pd

base = Path(sys.argv[1]); od = base/'raw/opendata'
rows = []
# 1) PoliS-Lombardia / ISTAT: strutture e letti, Milano (id 2724-d4dt)
p = pd.read_csv(od/'lombardia/2724-d4dt_milano.csv')
for _, r in p.iterrows():
    t = r['tipo_struttura'].strip()
    if t.upper() == 'TOTALE': t = 'Totale'
    rows.append(dict(fonte='PoliS-Lombardia/ISTAT dataset 2724-d4dt', serie='esercizi ricettivi ISTAT (comune di Milano)', periodo=str(r['anno']),
                     tipo=t, strutture=r['numero_strutture'], posti_letto=r['numero_letti']))
# 2) Comune di Milano ds2955: strutture attive e posti letto per tipologia
c = pd.read_csv(od/'comune_milano/ds2955.csv', sep=';', encoding='utf-8-sig')
for _, r in c.iterrows():
    rows.append(dict(fonte='Comune di Milano dataset ds2955', serie='strutture attive per tipologia (serie storica)', periodo=str(r['ANNO']),
                     tipo=f"{r['COD_Struttura']} - {r['Struttura']}", strutture=r['Esercizi_attivi'], posti_letto=r['Posti_letto']))
# 3) Comune: strutture accreditate nel sistema imposta di soggiorno
for _, r in pd.read_csv(od/'comune_milano/ds477.csv', sep=';', encoding='utf-8-sig').iterrows():
    mesi = ['Gennaio','Febbraio','Marzo','Aprile','Maggio','Giugno','Luglio','Agosto','Settembre','Ottobre','Novembre','Dicembre']
    rows.append(dict(fonte='Comune di Milano dataset ds477', serie='strutture accreditate imposta di soggiorno (mensile)',
                     periodo=f"{r['Anno']}-{mesi.index(r['Mese'])+1:02d}", tipo='Totale accreditate', strutture=r['Numero strutture ricettive'], posti_letto=None))
for _, r in pd.read_csv(od/'comune_milano/ds500.csv', sep=';', encoding='utf-8-sig').iterrows():
    for q in range(1, 5):
        rows.append(dict(fonte='Comune di Milano dataset ds500', serie='strutture accreditate imposta di soggiorno (trimestrale)',
                         periodo=f"{r['anno']}-T{q}", tipo='Totale accreditate', strutture=r[f'strutture al {q} trimestre'], posti_letto=None))
t = pd.DataFrame(rows)
(base/'pulito').mkdir(exist_ok=True)
t.to_csv(base/'pulito/ufficiale_strutture_milano.csv', index=False)
print('ufficiale_strutture_milano.csv', len(t))

# flussi
f = pd.read_csv(od/'lombardia/vyxt-7jdx_milano.csv', dtype=str)
def num(s): return pd.to_numeric(s.str.replace(',', '', regex=False), errors='coerce')
f['cittadinanza_turisti'] = f['cittadinanza_turisti'].str.capitalize()
f['tipo_struttura'] = f['tipo_struttura'].str.strip()
out = pd.DataFrame({'anno': f['anno'].astype(int), 'tipo_struttura': f['tipo_struttura'], 'cittadinanza': f['cittadinanza_turisti'],
                    'arrivi': num(f['arrivi']), 'presenze': num(f['presenze']), 'permanenza_media': pd.to_numeric(f['permanenza_media'], errors='coerce')})
out['fonte'] = 'PoliS-Lombardia/ISTAT dataset vyxt-7jdx'
out.sort_values(['anno', 'tipo_struttura', 'cittadinanza']).to_csv(base/'pulito/ufficiale_flussi_milano.csv', index=False)
print('ufficiale_flussi_milano.csv', len(out))
