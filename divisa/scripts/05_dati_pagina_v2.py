"""Prepara il file compatto per la nuova pagina 'Quanto è divisa Milano' (docs/divisa/data/quadro_v2.json).
Non rifà nessun conto: rimette in ordine i risultati già calcolati dai programmi 01-04 e i conteggi per quartiere.
Uso: python -I -X utf8 05_dati_pagina_v2.py <percorso assoluto di milano-in-dati>"""
import csv, json, os, sys
R = sys.argv[1]
DD = os.path.join(R, 'docs', 'divisa', 'data')

def rd(n):
    return list(csv.DictReader(open(os.path.join(DD, n), encoding='utf-8')))

m = json.load(open(os.path.join(DD, 'mappa.json'), encoding='utf-8'))
rj = json.load(open(os.path.join(DD, 'riepilogo.json'), encoding='utf-8'))
f = float

cs = rd('cittadinanza_serie.csv')
es = rd('eta_serie.csv')
ms = [r for r in rd('reddito_serie.csv') if r['citta'] == 'MILANO']
ls = [r for r in rd('laureati_serie.csv') if r['insieme'] == '88 NIL']
out = {
    'cittadinanza': [{'a': int(r['anno']), 'q': f(r['quota_stranieri']), 'd': f(r['d']), 'b': f(r['d_base'])} for r in cs],
    'eta': [{'a': int(r['anno']), 'q': f(r['quota_65p']), 'd': f(r['d']), 'b': f(r['d_base'])} for r in es],
    'reddito': [{'a': int(r['anno']), 'd': f(r['d']), 'b': f(r['d_base']), 'alto': f(r['quota_alto']), 'basso': f(r['quota_basso'])} for r in ms],
    'laureati': [{'a': int(r['anno']), 'q': f(r['quota_laureati']), 'd': f(r['d']), 'b': f(r['d_base'])} for r in ls],
}
# comunità: tutti gli anni disponibili (dal primo anno con almeno 2000 residenti)
com = {}
for r in rd('cittadinanza_comunita.csv'):
    if int(r['residenti']) >= 2000:
        com.setdefault(r['comunita'], []).append([int(r['anno']), round(f(r['d']), 4), int(r['residenti'])])
out['comunita'] = com
# città con almeno 10 CAP: 2011 e 2024
cit = {}
for r in rd('reddito_41_citta.csv'):
    if int(r['n_cap']) >= 10:
        cit.setdefault(r['citta'], {})[r['anno']] = {'d': round(f(r['d']), 4), 'n': int(r['n_cap'])}
out['citta'] = {k.title(): v for k, v in cit.items() if '2024' in v}
# quartieri: primo e ultimo anno
c, e, rr = m['cittadinanza'], m['eta'], m['reddito']
i0, i1 = 0, len(c['anni']) - 1
assert c['anni'][i0] == 1999 and c['anni'][i1] == 2025
nil = []
for k, n in enumerate(m['nomi']):
    nil.append({'i': m['nil'][k], 'n': n,
                'r99': c['res'][i0][k], 's99': c['stra'][i0][k], 'a99': e['a65'][i0][k], 'u99': e['u35'][i0][k],
                'r25': c['res'][i1][k], 's25': c['stra'][i1][k], 'a25': e['a65'][i1][k], 'u25': e['u35'][i1][k],
                'alto': rr['alto'][-1][k], 'basso': rr['basso'][-1][k]})
out['nil'] = nil
out['anni_reddito'] = rr['anni']
out['n'] = {'reddito_alto_2024': rj['numeri']['reddito_quota_alto_2024']}
json.dump(out, open(os.path.join(DD, 'quadro_v2.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('ok', os.path.getsize(os.path.join(DD, 'quadro_v2.json')))
