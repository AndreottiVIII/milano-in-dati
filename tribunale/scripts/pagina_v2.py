"""Prepara i file nuovi della pagina "Il tribunale di Milano" (versione 2).
Legge le tabelle già pulite (tribunale/pulito/) e i file della pagina attuale (docs/tribunale/data/), senza modificarli.
Scrive in docs/tribunale/data/: durata_per_tribunale_2025.csv e pagina_v2.json.
Uso: python -I -X utf8 pagina_v2.py <cartella del progetto milano-in-dati>"""
import csv, json, os, sys
R = sys.argv[1]
P = os.path.join(R, 'tribunale', 'pulito'); D = os.path.join(R, 'docs', 'tribunale', 'data')
def key(s): return s.strip().lower()
PICCOLE = {'Della', 'Di', 'Del', 'Dei', 'Delle', 'Dello', 'Sul', 'Sulla', 'Su', 'In', 'Sotto', 'Sopra', 'Nel'}
def bello(n):  # nomi in maiuscoletto del Ministero: 'Vallo Della Lucania' -> 'Vallo della Lucania'
    return ' '.join(w.lower() if (i and w in PICCOLE) else w for i, w in enumerate(n.split(' ')))
dur = list(csv.DictReader(open(os.path.join(P, 'durata_effettiva.csv'), encoding='utf-8')))
def d(tipo, liv, mat, anno):
    return {key(r['sede']): (float(r['durata_giorni']), int(r['definiti'])) for r in dur
            if r['tipo'] == tipo and r['livello'] == liv and r['materia'] == mat and r['anno'] == anno}
S = json.load(open(os.path.join(D, 'serie.json'), encoding='utf-8'))
def ult(k, anno='2025'):
    v = S[k]; i = v['x'].index(anno)
    return {key(n): x[i] for n, x in v['uffici'].items()}, v['milano'][i], v['italia'][i]
def num(x): return None if x is None or x == '' else float(x)
# tribunali
nomi = {}
for r in csv.DictReader(open(os.path.join(D, 'tribunali_2025.csv'), encoding='utf-8'), delimiter=';'):
    nomi[key(r['ufficio'])] = (r['ufficio'], r['distretto'])
co25 = d('tribunale', 'ufficio', 'Civile ordinario', '2025'); co19 = d('tribunale', 'ufficio', 'Civile ordinario', '2019')
lav = d('tribunale', 'ufficio', 'Lavoro', '2025'); tot = d('tribunale', 'ufficio', 'Totale delle materie', '2025')
dtc, _, _ = ult('civile_tribunale_dt'); dtp, _, _ = ult('penale_tribunale_dt'); pend, _, _ = ult('civile_tribunale_pend')
trib = []
for k, (n, dist) in sorted(nomi.items(), key=lambda x: x[1][0]):
    g = lambda m: round(m[k][0]) if k in m else None
    trib.append({'n': bello(n), 'd': dist, 'o': g(co25), 'o19': g(co19), 'l': g(lav), 't': g(tot),
                 'dc': round(dtc[k]) if dtc.get(k) is not None else None, 'dp': round(dtp[k]) if dtp.get(k) is not None else None,
                 'pe': int(pend[k]) if pend.get(k) is not None else None, 'do': co25[k][1] if k in co25 else None})
# corti d'appello
c25 = d('corte_appello', 'distretto', 'Civile ordinario', '2025'); cl = d('corte_appello', 'distretto', 'Lavoro', '2025')
cdc, _, _ = ult('civile_corte_appello_dt'); cdp, _, _ = ult('penale_corte_appello_dt')
corti = []
for k, (v, nd) in sorted(c25.items()):
    corti.append({'n': k.title() if k != 'reggio calabria' else 'Reggio Calabria', 'o': round(v), 'l': round(cl[k][0]) if k in cl else None,
                  'dc': round(cdc[k]) if cdc.get(k) is not None else None, 'dp': round(cdp[k]) if cdp.get(k) is not None else None})
def nz(tipo, mat, anno='2025'):
    return round(d(tipo, 'nazionale', mat, anno)['totale'][0])
ita = {'trib': {'o': nz('tribunale', 'Civile ordinario'), 'o19': nz('tribunale', 'Civile ordinario', '2019'), 'l': nz('tribunale', 'Lavoro'), 't': nz('tribunale', 'Totale delle materie')},
       'corte': {'o': nz('corte_appello', 'Civile ordinario'), 'l': nz('corte_appello', 'Lavoro'), 't': nz('corte_appello', 'Totale delle materie')}}
for sez, k in [('tc', 'civile_tribunale_dt'), ('tp', 'penale_tribunale_dt'), ('cc', 'civile_corte_appello_dt'), ('cp', 'penale_corte_appello_dt')]:
    _, m, i = ult(k); ita[sez] = round(i, 1)
    ita['m' + sez] = round(m, 1)
ser = {}
for sez, k in [('tc', 'civile_tribunale_dt'), ('tp', 'penale_tribunale_dt')]:
    v = S[k]; ser[sez] = {'x': v['x'], 'mi': v['milano'], 'it': v['italia']}
for sez, k in [('pc', 'civile_tribunale_pend'), ('cpc', 'civile_corte_appello_pend')]:
    v = S[k]; ser[sez] = {'x': v['x'], 'mi': v['milano'], 'it': v['italia']}
asilo = [{'a': int(r['anno']), 'tot': int(r['cause_civili_aperte_tempo_smaltimento']), 'asilo': int(r['di_cui_protezione_internazionale']), 'altre': int(r['altre_cause'])}
         for r in csv.DictReader(open(os.path.join(D, 'pendenti_milano_protezione_internazionale.csv'), encoding='utf-8-sig'), delimiter=';')]
json.dump({'trib': trib, 'corti': corti, 'ita': ita, 'serie': ser, 'asilo': asilo,
           'fonte': 'Ministero della Giustizia: durata effettiva dei procedimenti civili (Durata_SICID_20142025), Monitoraggio PNRR; elaborazione nostra'},
          open(os.path.join(D, 'pagina_v2.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
with open(os.path.join(D, 'durata_per_tribunale_2025.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['tribunale', 'distretto', 'durata_cause_ordinarie_giorni_2025', 'durata_cause_ordinarie_giorni_2019', 'durata_cause_lavoro_giorni_2025', 'durata_tutte_le_materie_giorni_2025',
                'cause_ordinarie_chiuse_2025', 'tempo_smaltimento_civile_giorni_2025', 'tempo_smaltimento_penale_giorni_2025', 'cause_civili_aperte_2025'])
    for t in trib: w.writerow([t['n'], t['d'], t['o'], t['o19'], t['l'], t['t'], t['do'], t['dc'], t['dp'], t['pe']])
print(len(trib), len(corti), ita)
print([t for t in trib if t['n'] == 'Milano'], [c for c in corti if c['n'] == 'Milano'])
print(sum(1 for t in trib if t['o'] is None), asilo[-1])
