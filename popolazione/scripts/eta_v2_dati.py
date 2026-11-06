"""Pagina Età e centenari (versione 2): scrive due file nuovi in docs/eta/data/.
 - eta_singola_citta.json : residenti di Milano per anno (1999-2025), sesso ed età singola (0-100, 100 = "100 e più")
 - eta_singola_nil_2025.json : residenti al 31/12/2025 per quartiere, sesso ed età singola
Uso: python -I -X utf8 eta_v2_dati.py <percorso assoluto di popolazione> <percorso assoluto di milano-in-dati>"""
import csv, json, os, sys
P, R = sys.argv[1], sys.argv[2]
pul = os.path.join(P, 'pulito')
out = os.path.join(R, 'docs', 'eta', 'data')
anni = list(range(1999, 2026))
c = {a: {'F': [0]*101, 'M': [0]*101} for a in anni}
for r in csv.DictReader(open(os.path.join(pul, 'residenti_comune_anno_eta_genere.csv'), encoding='utf-8')):
    c[int(r['anno'])]['F' if r['genere'].startswith('F') else 'M'][int(r['eta'])] += int(r['residenti'])
json.dump({'anni': anni, 'F': [c[a]['F'] for a in anni], 'M': [c[a]['M'] for a in anni]},
          open(os.path.join(out, 'eta_singola_citta.json'), 'w'), separators=(',', ':'))
nome = {r['id_nil']: r['nil'] for r in csv.DictReader(open(os.path.join(pul, 'nil_anagrafica.csv'), encoding='utf-8'))}
n = {}
for r in csv.DictReader(open(os.path.join(pul, 'residenti_nil_anno_eta_genere.csv'), encoding='utf-8')):
    if r['anno'] != '2025': continue
    d = n.setdefault(r['id_nil'], {'n': nome[r['id_nil']], 'F': [0]*101, 'M': [0]*101})
    d['F' if r['genere'].startswith('F') else 'M'][int(r['eta'])] += int(r['residenti'])
json.dump({'anno': 2025, 'nil': n}, open(os.path.join(out, 'eta_singola_nil_2025.json'), 'w'), separators=(',', ':'), ensure_ascii=False)
print(len(n), 'quartieri;', sum(sum(d['F'])+sum(d['M']) for d in n.values()), 'residenti 2025;', sum(c[2025]['F'])+sum(c[2025]['M']))
