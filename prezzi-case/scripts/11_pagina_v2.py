r"""Dati per la pagina rifatta docs\prezzi-case (stile nuovo, 7/11/2026).
Entrata (sola lettura): docs\prezzi-case\data\riepilogo.json, serie_zone.json, zone.geojson; docs\redditi\data\riepilogo.json
Uscita: docs\prezzi-case\data\pagina_v2.json  (nome nuovo: non tocca i file della pagina attuale)
  citta   serie semestrale della mediana (euro di allora e euro 2025, prezzo e affitto)
  reddito reddito medio dichiarato di un contribuente di Milano per anno d'imposta (MEF, CC BY 3.0), euro 2025 e correnti
  zone    per ogni zona dell'ultimo semestre: nome, fascia, serie (prezzo e affitto, euro di allora e euro 2025)
L'affitto "di allora" = affitto in euro 2025 x (prezzo di allora / prezzo in euro 2025): lo stesso deflatore del semestre.
Uso: python -I -X utf8 11_pagina_v2.py <cartella milano-in-dati>
"""
import sys, os, json
R = sys.argv[1]
D = os.path.join(R, 'docs', 'prezzi-case', 'data')
riep = json.load(open(os.path.join(D, 'riepilogo.json'), encoding='utf-8'))
sz = json.load(open(os.path.join(D, 'serie_zone.json'), encoding='utf-8'))
geo = json.load(open(os.path.join(D, 'zone.geojson'), encoding='utf-8'))
red = json.load(open(os.path.join(R, 'docs', 'redditi', 'data', 'riepilogo.json'), encoding='utf-8'))

ab = riep['abitazioni']
citta = {'s': [x['s'] for x in ab], 'nom': [x['nom'] for x in ab], 'reale': [x['reale'] for x in ab],
         'aff_nom': [x['aff_nom'] for x in ab], 'aff_reale': [x['aff_reale'] for x in ab], 'n': [x['n'] for x in ab]}
anni = red['anni']; m = red['serie']['Milano']
reddito = {'anni': anni, 'euro2025': m['media_euro2025'], 'nominale': m['media_nominale']}
zone = []
for f in geo['features']:
    p = f['properties']; s = sz[p['zona']]
    affn = [round(a * n / rl, 2) for a, n, rl in zip(s['aff_reale'], s['nom'], s['reale'])]
    zone.append({'z': p['zona'], 'nome': p['nome'], 'breve': p['nome_breve'], 'fascia': p['fascia'],
                 's': s['s'], 'nom': s['nom'], 'reale': s['reale'], 'aff_nom': affn, 'aff_reale': s['aff_reale']})
out = {'meta': {'ultimo': riep['meta']['ultimo'], 'data_scarico': riep['meta']['data_scarico'],
                'nota': 'aff_nom ricavato con il deflatore del prezzo dello stesso semestre'},
       'citta': citta, 'reddito': reddito, 'zone': zone}
json.dump(out, open(os.path.join(D, 'pagina_v2.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('ok', len(zone), 'zone', os.path.getsize(os.path.join(D, 'pagina_v2.json')), 'byte')
