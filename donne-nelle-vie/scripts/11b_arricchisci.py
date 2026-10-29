"""Fase 2: per le donne (sicure e incerte) completa le professioni in italiano (etichette Wikidata delle occupazioni P106) dove mancano.
Scrive anche da_verificare_donne.csv (tutti i casi incerti in cui una donna e candidata).
Uso: python -I 11b_arricchisci.py strade_classificate_v2.csv strade_classificate_arricchite_v2.csv cache_json da_verificare_donne.csv"""
import sys, json, os, time, requests
import pandas as pd

inp, outp, cache, verif = sys.argv[1:5]
d = pd.read_csv(inp, dtype=str).fillna('')
UA = {"User-Agent": "milano-in-dati/0.2 (davide.caniatti@gmail.com; street-name research, polite)"}
labels = json.load(open(cache, encoding='utf8')) if os.path.exists(cache) else {}
W = d[d.categoria == 'donna']
need = sorted({q for s in W.occupazioni_qid for q in s.split(';') if q} - set(labels), key=lambda q: int(q[1:]))
print(len(need), 'etichette di occupazioni da scaricare')


def get(params):
    for a in range(8):
        r = requests.get("https://www.wikidata.org/w/api.php", params=params, headers=UA, timeout=60)
        j = r.json() if r.status_code == 200 else {}
        if 'error' in j or r.status_code != 200:
            time.sleep(min(90, 6 * 2 ** a)); continue
        return j
    return {}


for i in range(0, len(need), 50):
    j = get(dict(action='wbgetentities', ids='|'.join(need[i:i + 50]), props='labels', languages='it|en', format='json'))
    for q, e in j.get('entities', {}).items():
        labels[q] = (e.get('labels', {}).get('it') or e.get('labels', {}).get('en') or {}).get('value', q)
    time.sleep(1)
json.dump(labels, open(cache, 'w', encoding='utf8'), ensure_ascii=False)


def prof(r):
    if r.professioni:
        return r.professioni
    qs = [q for q in r.occupazioni_qid.split(';') if q]
    return ', '.join(labels.get(q, q) for q in qs)


d['professioni'] = [prof(r) for r in d.itertuples()]
d.to_csv(outp, index=False, encoding='utf-8-sig')
w = d[d.categoria == 'donna']
print('donne:', len(w), '| senza professione:', int((w.professioni == '').sum()))

dv = d[(d.confidenza == 'incerto') & ((d.categoria == 'donna') | d.candidati.str.contains(r'\|donna\|', regex=True))].copy()
dv['classificata_ora_come'] = dv.categoria
dv['wikidata'] = dv.qid.apply(lambda x: ' '.join('https://www.wikidata.org/wiki/' + q for q in x.split(';') if q))
dv['tipo_di_dubbio'] = dv.fonte.map({'titolo': 'santa/titolo senza persona trovata (chiesa?)', 'nome': 'solo nome di battesimo femminile, nessuna persona trovata', 'wikidata': 'omonimi o nome parziale su Wikidata'}).fillna('altro')
dv['tua_decisione (donna / non donna / altro)'] = ''
dv['note_tue'] = ''
dv = dv.sort_values(['tipo_di_dubbio', 'nome'])
dv[['nome', 'codice_via', 'classificata_ora_come', 'tipo_di_dubbio', 'motivo', 'santa', 'persona', 'nascita', 'morte', 'professioni', 'descrizione', 'candidati', 'wikidata', 'data_intitolazione',
    'tua_decisione (donna / non donna / altro)', 'note_tue']].to_csv(verif, index=False, encoding='utf-8-sig')
print('da verificare:', len(dv), dv.tipo_di_dubbio.value_counts().to_dict())
