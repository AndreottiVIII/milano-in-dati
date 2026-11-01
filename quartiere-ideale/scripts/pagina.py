"""Costruisce i dati della pagina "Il mio quartiere ideale" (docs/quartiere-ideale/).

Uso:  python -I -X utf8 pagina.py <percorso assoluto di milano-in-dati>

Legge SOLO docs/quartiere/data/schede.json (costruito dalla pagina "Il tuo quartiere") e scrive
  docs/quartiere-ideale/data/criteri.json
con, per ciascuno dei criteri scelti, il valore di ogni quartiere e il suo percentile (0 = valore piu basso
tra i quartieri ammessi, 1 = piu alto). Il verso (piu e meglio / meno e meglio) lo applica la pagina.

Regole:
  - Ammessi: quartieri con almeno 3.000 residenti e che non sono parchi/aree verdi (quasi senza abitanti).
    Gli altri restano sulla mappa, grigi, con il motivo.
  - Si usano solo valori affidabili: se la scheda segna un valore come "poco affidabile" (flag) o manca,
    il criterio per quel quartiere e "dato mancante" (la pagina calcola il punteggio sugli altri criteri e lo dice).
  - Percentile = posto tra i quartieri ammessi con dato affidabile, a meta dei pareggi.
Non inventa niente. Si puo rilanciare quando si vuole.
"""
import json
import os
import sys
from datetime import date

BASE = sys.argv[1]
SRC = os.path.join(BASE, 'docs', 'quartiere', 'data', 'schede.json')
OUTD = os.path.join(BASE, 'docs', 'quartiere-ideale', 'data')
os.makedirs(OUTD, exist_ok=True)

with open(SRC, encoding='utf-8') as fh:
    S = json.load(fh)

IND = {i['id']: i for i in S['indicatori']}
MIN_RES = 3000

# id criterio, indicatore, verso (+1: valore alto = meglio; -1: valore basso = meglio), etichetta, spiegazione breve,
# gruppo di esclusione reciproca (due slider opposti sullo stesso dato)
CRITERI = [
    ('parchi', 'c15_parchi', 1, 'Parchi vicini', 'Quanti residenti hanno un parco (almeno 5.000 m²) a 15 minuti a piedi.', None),
    ('alberi', 'alberi', 1, 'Tanti alberi', 'Alberi gestiti dal Comune ogni 1.000 abitanti (mancano i giardini privati).', None),
    ('cemento', 'suolo', -1, 'Poco cemento', 'Quota di suolo consumato: meno è, meglio è.', None),
    ('prezzo', 'prezzo_vendita', -1, 'Case a prezzo basso', 'Prezzo di vendita al m², stima dalle quotazioni OMI.', None),
    ('servizi', 'c15_10', 1, 'Servizi a 15 minuti', 'Farmacia, medico, scuola, mercato, parco… raggiungibili a piedi (punteggio su 10).', None),
    ('metro', 'c15_metro', 1, 'Metropolitana vicina', 'Quanti residenti hanno una fermata del metrò a 15 minuti a piedi.', None),
    ('calmo', 'locali', -1, 'Tranquillità', 'Pochi bar, ristoranti e locali per abitante.', 'locali'),
    ('vivo', 'locali', 1, 'Vita in strada', 'Tanti bar, ristoranti e locali per abitante.', 'locali'),
    ('giovani', 'eta_media', -1, 'Residenti più giovani', 'Età media bassa.', None),
]


def ammesso(n):
    if n['quasi_vuoto']:
        return 'parco o area verde, quasi senza residenti'
    if n['piccolo'] or (n['residenti'] or 0) < MIN_RES:
        return 'meno di 3.000 residenti'
    return None


nil = []
for n in S['nil']:
    m = ammesso(n)
    nil.append({'id': n['id'], 'nome': n['nome'], 'municipio': n['municipio'], 'residenti': n['residenti'],
                'ok': m is None, 'motivo': m, 'd': {}})
byid = {n['id']: n for n in nil}
ammessi = [n for n in nil if n['ok']]

criteri_out = []
for cid, iid, verso, et, spieg, grp in CRITERI:
    ind = IND[iid]
    vals = []
    for n in ammessi:
        c = S['valori'][str(n['id'])][iid]
        if c.get('v') is not None and not c.get('f'):
            vals.append((n['id'], c['v']))
    allv = sorted(v for _, v in vals)
    N = len(allv)
    for i, v in vals:
        less = sum(1 for x in allv if x < v)
        eq = sum(1 for x in allv if x == v)
        p = (less + (eq - 1) / 2) / (N - 1)
        byid[i]['d'][cid] = [v, round(p, 4)]
    criteri_out.append({'id': cid, 'ind': iid, 'verso': verso, 'et': et, 'spieg': spieg, 'gruppo': grp,
                        'fmt': ind['fmt'], 'dec': ind['dec'], 'unita': ind['unita'], 'citta': ind['citta'],
                        'ref': ind['ref'], 'anno': ind['anno'], 'stima': ind.get('stima'), 'pagina': ind['pagina'],
                        'n': N, 'file': S['origine'][iid]['file'], 'campo': S['origine'][iid]['campo']})
    print('%-8s %-15s n=%d  (mancanti tra gli ammessi: %d)' % (cid, iid, N, len(ammessi) - N))

out = {'generato': date.today().isoformat(), 'fonte': 'docs/quartiere/data/schede.json (generato %s)' % S.get('generato'),
       'min_residenti': MIN_RES, 'stime': S['stime'], 'n_ammessi': len(ammessi), 'criteri': criteri_out, 'nil': nil}
with open(os.path.join(OUTD, 'criteri.json'), 'w', encoding='utf-8') as fh:
    json.dump(out, fh, ensure_ascii=False, separators=(',', ':'))
print('quartieri ammessi:', len(ammessi), 'su', len(nil), '->', os.path.join(OUTD, 'criteri.json'))
