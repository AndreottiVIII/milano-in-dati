"""Aggiunge i "servizi in piu" alla pagina "Il mio quartiere ideale" (docs/quartiere-ideale/).

Uso:  python -I -X utf8 servizi.py <percorso assoluto di milano-in-dati>

Prima si lancia pagina.py (i 9 criteri di base), poi questo programma. Legge docs/quartiere-ideale/data/criteri.json,
toglie gli eventuali servizi gia aggiunti in un lancio precedente (si puo rilanciare quando si vuole) e aggiunge
i servizi extra, leggendo i valori dai file delle altre pagine (docs/<pagina>/data/). I percentili si ricalcolano
qui, con la stessa regola di pagina.py: posto tra i quartieri ammessi che hanno il dato, a meta dei pareggi
(0 = valore piu basso, 1 = piu alto; il verso lo applica la pagina).

Regole:
  - i quartieri ammessi sono quelli gia scelti da pagina.py (almeno 3.000 residenti, non parchi).
  - i rapporti "per abitante" (aree gioco, aree cani, impianti, palestre, posti auto) valgono solo per i quartieri con almeno
    5.000 abitanti, come alberi, aree gioco e aree cani nelle pagine di origine: sotto quella soglia un centro sportivo
    o un'area cani che serve tutta la citta falsa il rapporto (esempio: QT8). Gli altri sono "dato mancante".
  - niente di cio che descrive le persone (reddito, cittadinanza, titolo di studio, voto, reati) e mai un criterio.
Non inventa niente: ogni valore viene dal file indicato in "file" e "campo".
"""
import csv
import json
import os
import sys

BASE = sys.argv[1]
DOCS = os.path.join(BASE, 'docs')
PATH = os.path.join(DOCS, 'quartiere-ideale', 'data', 'criteri.json')

with open(PATH, encoding='utf-8') as fh:
    C = json.load(fh)

# via i servizi di un lancio precedente
C['criteri'] = [c for c in C['criteri'] if not c.get('extra')]
extra_ids = set()
for n in C['nil']:
    n['d'] = {k: v for k, v in n['d'].items() if k in {c['id'] for c in C['criteri']}}
ammessi = [n['id'] for n in C['nil'] if n['ok']]
AM = set(ammessi)


def righe(rel):
    with open(os.path.join(DOCS, rel), encoding='utf-8-sig', newline='') as fh:
        head = fh.readline()
        fh.seek(0)
        d = ';' if head.count(';') > head.count(',') else ','
        return list(csv.DictReader(fh, delimiter=d))


def num(x):
    if x in (None, ''):
        return None
    try:
        return float(str(x).strip())
    except ValueError:
        return None


def flag(x):
    return str(x).strip() in ('1', 'True', 'true')


# --- letture --------------------------------------------------------------
verde = {int(r['id_nil']): r for r in righe('verde/data/nil_verde.csv')}
cani = {int(r['id_nil']): r for r in righe('cani/data/aree_cani_per_nil.csv')}
park = {int(r['id_nil']): r for r in righe('parcheggi/data/nil.csv')}
sport = {int(r['ID_NIL']): r for r in righe('sport/data/nil_sport.csv')}
c15x = {int(r['ID_NIL']): r for r in righe('citta-15-minuti/data/nil_punteggi_extra.csv')}
aff = {int(r['id_nil']): r for r in righe('permettersi/data/nil_affitti_redditi.csv') if r['anno'] == '2024'}
with open(os.path.join(DOCS, 'medici-farmacie', 'data', 'nil.geojson'), encoding='utf-8') as fh:
    med = {f['properties']['i']: f['properties'] for f in json.load(fh)['features']}

# quartieri con almeno 5.000 abitanti (stesso insieme delle pagine verde, cani e parcheggi)
GRANDI = {i for i in AM if i in verde and flag(verde[i]['in_classifica'])}


def solo_grandi(v):
    return {i: x for i, x in v.items() if i in GRANDI}


V = {}
V['affitto'] = {i: num(r['affitto_60mq_mese_eur']) for i, r in aff.items()}
V['farmacia'] = {i: p['fmin'] for i, p in med.items()}
V['pediatri'] = {i: p['p1000'] for i, p in med.items()}
V['gioco'] = solo_grandi({i: num(r['gioco_n']) / num(r['abitanti_2024']) * 10000 for i, r in verde.items()
                          if num(r['abitanti_2024'])})
V['cani'] = solo_grandi({i: num(r['aree_cani_per_100mila_ab']) for i, r in cani.items()})
V['piscine'] = {i: num(r['quota_entro15_piscine']) * 100 for i, r in c15x.items() if num(r['quota_entro15_piscine']) is not None}
V['caldo'] = {i: num(r['calore_esposizione']) for i, r in verde.items()}
V['parcheggi'] = solo_grandi({i: num(r['STIMA_posti_su_strada']) / num(r['abitanti_2024']) * 1000 for i, r in park.items()
                              if num(r['abitanti_2024'])})
V['palestre'] = solo_grandi({i: num(r['per10k_palestre']) for i, r in sport.items()})
V['impianti'] = solo_grandi({i: num(r['per10k_tutti']) for i, r in sport.items()})

# id, etichetta, verso, spiegazione, fmt, dec, unita, suffisso (None = come fmt), anno, stima, pagina, nome pagina,
# file, campo, limite (frase per "Limiti dei dati")
EXTRA = [
    ('affitto', 'Affitto basso', -1,
     'Affitto di un appartamento di 60 m² in un mese, stima dalle quotazioni dell’Agenzia delle Entrate (OMI). Meno è, meglio è.',
     'eur', 0, 'al mese', 'al mese (60 m²)', '2024', 'omi', 'permettersi', 'Chi può permettersi di vivere dove',
     'permettersi/data/nil_affitti_redditi.csv', 'affitto_60mq_mese_eur (anno 2024)',
     'È una stima per zona, portata al quartiere, non il canone degli annunci. È più vecchia di un anno e mezzo del prezzo di vendita e i due si muovono insieme: alzarli tutti e due conta due volte la stessa cosa.'),
    ('farmacia', 'Farmacia vicina', -1,
     'Minuti a piedi fino alla farmacia più vicina: la mediana dei residenti del quartiere. Meno minuti, meglio è.',
     'dec', 1, 'minuti a piedi', None, '2025-26', None, 'medici-farmacie', 'Medici e farmacie',
     'medici-farmacie/data/nil.geojson', 'fmin',
     'I minuti sono calcolati sulla rete dei marciapiedi di OpenStreetMap, a 4,5 km/h; l’elenco delle farmacie è quello regionale di ottobre 2026.'),
    ('pediatri', 'Pediatri nel quartiere', 1,
     'Pediatri con ambulatorio nel quartiere ogni 1.000 bambini da 0 a 13 anni. Più è, meglio è.',
     'dec', 2, 'ogni 1.000 bambini', None, '2026', None, 'medici-farmacie', 'Medici e farmacie',
     'medici-farmacie/data/nil.geojson', 'p1000',
     'Conta gli ambulatori nel quartiere, non i pediatri che lo servono: in molti quartieri il valore è zero e i bambini vanno dal pediatra di un quartiere vicino. In città i pediatri nell’elenco del Comune sembrano troppo pochi, quindi l’elenco può essere incompleto.'),
    ('gioco', 'Aree gioco', 1,
     'Aree gioco per bambini ogni 10.000 abitanti. Più è, meglio è.',
     'dec', 1, 'ogni 10.000 abitanti', None, '2024', None, 'verde', 'Parchi e verde',
     'verde/data/nil_verde.csv', 'gioco_n / abitanti_2024 (solo quartieri con almeno 5.000 abitanti)',
     'Conta le aree, non la loro grandezza né se sono tenute bene. Per i sei quartieri con meno di 5.000 abitanti il dato non c’è.'),
    ('cani', 'Aree per i cani', 1,
     'Aree recintate per i cani ogni 100.000 abitanti. Più è, meglio è.',
     'dec', 1, 'ogni 100.000 abitanti', None, '2024', None, 'cani', 'Cani di Milano',
     'cani/data/aree_cani_per_nil.csv', 'aree_cani_per_100mila_ab',
     'Conta le aree recintate, non i parchi dove i cani sono ammessi. Per i sei quartieri con meno di 5.000 abitanti il dato non c’è.'),
    ('piscine', 'Piscina a 15 minuti', 1,
     'Quanti residenti hanno una piscina a 15 minuti a piedi. Più è, meglio è.',
     'pct', 0, '%', None, '2020-2026', None, 'citta-15-minuti', 'La città dei 15 minuti',
     'citta-15-minuti/data/nil_punteggi_extra.csv', 'quota_entro15_piscine (frazione 0-1, qui in %)',
     'L’elenco delle piscine del Comune è del 2019-2020 e quello di OpenStreetMap del 2026: può mancare qualche piscina nuova o privata. In 16 quartieri nessun residente arriva a una piscina in 15 minuti.'),
    ('caldo', 'Poco caldo d’estate', -1,
     'Indice di esposizione al calore da satellite (da 0 a 1), luglio 2024. Meno è, meglio è.',
     'dec', 2, '', '(indice da 0 a 1)', '2024', None, 'verde', 'Parchi e verde',
     'verde/data/nil_verde.csv', 'calore_esposizione (SPOTTED, ds2811)',
     'È un indice da satellite del Comune, non una temperatura misurata, e fotografa un solo mese di un solo anno. Le differenze tra quartieri sono piccole (da 0,33 a 0,62).'),
    ('parcheggi', 'Posti auto in strada', 1,
     'Posti auto in strada ogni 1.000 abitanti: una stima, perché il Comune non pubblica i posti. Più è, meglio è.',
     'int', 0, 'ogni 1.000 abitanti', None, '2025', 'posti', 'parcheggi', 'Parcheggi: quanto spazio alle auto',
     'parcheggi/data/nil.csv', 'STIMA_posti_su_strada / abitanti_2024 * 1000 (solo quartieri con almeno 5.000 abitanti)',
     'Il totale della città (circa 297.000 posti) viene da una presentazione del Comune riportata dalla stampa e non è stato verificato sul documento; la divisione tra i quartieri è nostra e dà lo stesso numero di posti per ogni chilometro di strada: quindi misura soprattutto quanta strada c’è per abitante, non i posti veri. Non dice se i posti sono liberi, a pagamento o riservati ai residenti. Tienilo come un’indicazione larga.'),
    ('palestre', 'Palestre', 1,
     'Palestre e centri fitness ogni 10.000 abitanti, pubblici e privati. Più è, meglio è.',
     'dec', 1, 'ogni 10.000 abitanti', None, '2011-2026', None, 'sport', 'Impianti sportivi',
     'sport/data/nil_sport.csv', 'per10k_palestre (solo quartieri con almeno 5.000 abitanti)',
     'Gli elenchi di partenza sono di anni diversi (dal 2011 al 2026) e non dicono se una palestra è aperta a tutti né quanto costa. Per i sei quartieri con meno di 5.000 abitanti il dato non c’è.'),
    ('impianti', 'Impianti sportivi', 1,
     'Impianti sportivi di ogni tipo (piscine, palestre, campi, centri sportivi) ogni 10.000 abitanti. Più è, meglio è.',
     'dec', 1, 'ogni 10.000 abitanti', None, '2011-2026', None, 'sport', 'Impianti sportivi',
     'sport/data/nil_sport.csv', 'per10k_tutti (solo quartieri con almeno 5.000 abitanti)',
     'Mette insieme cinque elenchi che non coincidono (quasi la metà degli impianti compare in uno solo) e non sa se un impianto è aperto a tutti. Comprende anche le palestre delle scuole. Per i sei quartieri con meno di 5.000 abitanti il dato non c’è.'),
]

byid = {n['id']: n for n in C['nil']}
for (cid, et, verso, spieg, fmt, dec, unita, suf, anno, stima, pagina, nome_pag, file, campo, limite) in EXTRA:
    vals = {i: v for i, v in V[cid].items() if i in AM and v is not None}
    allv = sorted(vals.values())
    N = len(allv)
    for i, v in vals.items():
        less = sum(1 for x in allv if x < v)
        eq = sum(1 for x in allv if x == v)
        p = (less + (eq - 1) / 2) / (N - 1)
        byid[i]['d'][cid] = [round(v, 4), round(p, 4)]
    top = max(allv.count(x) for x in set(allv))
    C['criteri'].append({'id': cid, 'extra': True, 'verso': verso, 'et': et, 'spieg': spieg, 'gruppo': None,
                         'fmt': fmt, 'dec': dec, 'unita': unita, 'suf': suf, 'citta': None, 'anno': anno,
                         'stima': stima, 'pagina': pagina, 'pagina_nome': nome_pag, 'n': N, 'file': file,
                         'campo': campo, 'limite': limite})
    print('%-10s n=%d  min=%s max=%s  valore piu ripetuto: %d quartieri' % (cid, N, allv[0], allv[-1], top))

C['generato_servizi'] = '2026-11-05'
with open(PATH, 'w', encoding='utf-8') as fh:
    json.dump(C, fh, ensure_ascii=False, separators=(',', ':'))
print('criteri:', len(C['criteri']), '->', PATH)
