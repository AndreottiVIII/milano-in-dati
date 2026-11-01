"""Costruisce i dati della pagina "Il tuo quartiere" (docs/quartiere/).

Uso:  python -I -X utf8 pagina.py <percorso assoluto di milano-in-dati>

Legge SOLO docs/*/data/ (i file delle altre pagine) e scrive:
  docs/quartiere/data/schede.json   un record per quartiere (NIL) con i valori di tutti gli indicatori,
                                    il valore della citta, il posto in classifica, i flag, le "cose che
                                    saltano all'occhio" e, per ogni numero, file e campo di origine;
  docs/quartiere/data/nil.geojson   i 88 confini (presi da comunita/data/nil.geojson, gia semplificati);
  quartiere/mismatch.json           (fuori da docs) nomi di NIL che non corrispondono tra le pagine.
Non inventa e non stima: dove il dato manca scrive null e il motivo. Si puo rilanciare quando vuole.
"""
import csv
import gzip
import json
import math
import os
import re
import statistics
import sys
import unicodedata
from collections import defaultdict

BASE = sys.argv[1]
DOCS = os.path.join(BASE, 'docs')
OUT = os.path.join(DOCS, 'quartiere', 'data')
os.makedirs(OUT, exist_ok=True)

# ------------------------------------------------------------------ utilita


def P(*a):
    return os.path.join(DOCS, *a)


def read_csv(rel):
    path = P(*rel.split('/'))
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8-sig', newline='') as fh:
        txt = fh.read().splitlines()
    d = ';' if txt[0].count(';') > txt[0].count(',') else ','
    return list(csv.DictReader(txt, delimiter=d))


def read_json(rel):
    with open(P(*rel.split('/')), encoding='utf-8') as fh:
        return json.load(fh)


def num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return None if (isinstance(x, float) and math.isnan(x)) else x
    s = str(x).strip()
    if s.count(',') == 1 and '.' not in s:
        s = s.replace(',', '.')
    if s == '' or s.lower() in ('nan', 'none', 'null', 'na'):
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    return int(v) if v == int(v) and '.' not in s else v


def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r"[^a-z0-9]+", ' ', s)
    s = re.sub(r'\bq re\b', 'quartiere', s)
    s = re.sub(r'\bp?ta\b', 'porta', s)
    s = re.sub(r'\bs\b', 'san', s)
    s = re.sub(r'\bqt 8\b', 'qt8', s)
    return re.sub(r'\s+', ' ', s).strip()


# ------------------------------------------------------------------ elenco ufficiale dei 88 NIL
MASTER = {}
for r in read_csv('quartieri-che-cambiano/data/nil.csv'):
    MASTER[int(r['id_nil'])] = {'nome': r['nil'], 'municipio': int(r['municipio'])}
assert sorted(MASTER) == list(range(1, 89)), 'attesi 88 NIL con id 1..88'
BYNORM = {norm(v['nome']): k for k, v in MASTER.items()}
MISMATCH = defaultdict(list)


def nil_by_name(name, fonte):
    if not name:
        return None
    k = BYNORM.get(norm(name))
    if k is None and name not in MISMATCH[fonte]:
        MISMATCH[fonte].append(name)
    return k


# ------------------------------------------------------------------ residenti di riferimento (per i flag "quartiere piccolo")
RES25 = {int(r['id_nil']): num(r['residenti_2025']) for r in read_csv('eta/data/nil_eta_centenari.csv')}

# ------------------------------------------------------------------ registro degli indicatori
TEMI = ['Chi ci abita', 'Case e soldi', 'Servizi e scuole', 'Verde e clima', 'Vita in strada', 'Storia e memoria', 'Voto']
IND = []        # definizioni
VAL = {}        # id_indicatore -> {nil: {v, f, m, ...}}


def add(id, tema, et, pagina, file, campo, anno, unita, fmt, citta, dati, alto=None, basso=None,
        evid=False, tipo='num', nota=None, stima=None, csv_file=None, dec=1, ref='città', origine_citta=None, ftxt=None):
    """dati: dict nil -> (valore, flag, motivo[, extra]).  citta: valore di riferimento (numero/testo/None)."""
    IND.append(dict(id=id, tema=tema, et=et, pagina=pagina, file=file, campo=campo, anno=anno, unita=unita,
                    fmt=fmt, dec=dec, tipo=tipo, alto=alto, basso=basso, evid=evid, nota=nota, stima=stima,
                    csv=csv_file or file, citta=citta, ref=ref, origine_citta=origine_citta, ftxt=ftxt))
    VAL[id] = dati


def cells(rows, idkey, valkey, flagfn=None, scale=1.0, nullreason='dato mancante nella fonte', cast=num):
    out = {}
    for r in rows:
        i = int(r[idkey])
        v = cast(r[valkey])
        if v is not None and scale != 1.0:
            v = v * scale
        f = flagfn(r, i) if flagfn else None
        out[i] = (v, f, None if v is not None else nullreason)
    return out


def full(d, reason='il quartiere non compare nella fonte'):
    """Completa con i NIL mancanti (valore null + motivo)."""
    for i in MASTER:
        if i not in d:
            d[i] = (None, None, reason)
    return d


def small(th, key='residenti'):
    return lambda r, i: 'piccolo' if (RES25.get(i) is not None and RES25[i] < th) else None


def weighted_city(rows, idkey, valkey, wkey):
    s = w = 0.0
    for r in rows:
        v, x = num(r[valkey]), num(r[wkey])
        if v is not None and x:
            s += v * x
            w += x
    return s / w if w else None


# ================================================================== CHI CI ABITA
eta = read_csv('eta/data/nil_eta_centenari.csv')
eta_city = {r['anno']: r for r in read_csv('eta/data/citta_eta_centenari.csv')}['2025']
add('residenti', 'Chi ci abita', 'Residenti (31 dicembre)', 'eta', 'eta/data/nil_eta_centenari.csv', 'residenti_2025', 2025,
    'persone', 'int', None, full(cells(eta, 'id_nil', 'residenti_2025')), tipo='conto',
    nota='Anagrafe del Comune: sono più dei residenti ISTAT (+2,7% a fine 2025).', ref='mediana dei quartieri')
add('eta_media', 'Chi ci abita', 'Età media', 'eta', 'eta/data/nil_eta_centenari.csv', 'eta_media_2025', 2025, 'anni', 'num',
    num(eta_city['eta_media']), full(cells(eta, 'id_nil', 'eta_media_2025', small(3000))),
    alto="l'età media più alta", basso="l'età media più bassa", evid=True,
    nota='Età in anni compiuti. Sotto i 3.000 residenti il valore oscilla (case di riposo, centri di accoglienza).',
    origine_citta='eta/data/citta_eta_centenari.csv, anno 2025, campo eta_media', dec=1)
add('quota_65', 'Chi ci abita', 'Residenti di 65 anni e più', 'eta', 'eta/data/nil_eta_centenari.csv', 'quota_65_2025', 2025, '%', 'pct',
    num(eta_city['quota_65_pct']), full(cells(eta, 'id_nil', 'quota_65_2025', small(3000))),
    alto='più residenti di 65 anni e più', basso='meno residenti di 65 anni e più', evid=True,
    origine_citta='eta/data/citta_eta_centenari.csv, anno 2025, campo quota_65_pct')
add('quota_80', 'Chi ci abita', 'Residenti di 80 anni e più', 'eta', 'eta/data/nil_eta_centenari.csv', 'quota_80_2025', 2025, '%', 'pct',
    num(eta_city['quota_80_pct']), full(cells(eta, 'id_nil', 'quota_80_2025', small(3000))),
    alto='più residenti di 80 anni e più', basso='meno residenti di 80 anni e più', evid=True,
    origine_citta='eta/data/citta_eta_centenari.csv, anno 2025, campo quota_80_pct')

# stranieri (comunita): solo quartieri con almeno 3.000 residenti e 500 stranieri
div = [r for r in read_csv('comunita/data/diversita_nil.csv') if r['anno'] == '2025']
div_ids = {}
for r in div:
    k = nil_by_name(r['nil'], 'comunita/data/diversita_nil.csv')
    if k:
        div_ids[k] = r
dstr = {k: (num(r['quota_stranieri_pct']), None, None) for k, r in div_ids.items()}
for k in MASTER:
    dstr.setdefault(k, (None, None, 'la pagina non lo mostra: meno di 3.000 residenti o di 500 stranieri'))
tot_res = sum(num(r['residenti']) for r in div_ids.values())
tot_str = sum(num(r['stranieri']) for r in div_ids.values())
add('stranieri', 'Chi ci abita', 'Residenti con cittadinanza non italiana', 'comunita', 'comunita/data/diversita_nil.csv', 'quota_stranieri_pct', 2025,
    '%', 'pct', round(100 * tot_str / tot_res, 1), dstr,
    alto='più residenti con cittadinanza non italiana', basso='meno residenti con cittadinanza non italiana', evid=True,
    nota='Cittadinanza, non origine: chi ha preso la cittadinanza italiana conta come italiano. Registro del Comune.',
    origine_citta='calcolato: somma dei campi stranieri / somma dei campi residenti dei quartieri presenti in comunita/data/diversita_nil.csv (anno 2025)')
prima = {}
for k, r in div_ids.items():
    prima[k] = (r['prima_cittadinanza'], None, None, {'s': num(r['quota_prima_su_stranieri_pct'])})
for k in MASTER:
    prima.setdefault(k, (None, None, 'la pagina non lo mostra: meno di 3.000 residenti o di 500 stranieri'))
cit25 = [r for r in read_csv('comunita/data/residenti_per_cittadinanza_citta.csv') if r['anno'] == '2025']
cit25.sort(key=lambda r: -num(r['residenti']))
add('prima_cittadinanza', 'Chi ci abita', 'Cittadinanza straniera più numerosa', 'comunita', 'comunita/data/diversita_nil.csv', 'prima_cittadinanza',
    2025, '', 'testo', cit25[0]['cittadinanza'], prima, tipo='testo',
    nota='Tra i residenti con cittadinanza non italiana. Percentuale = quota sugli stranieri del quartiere.',
    origine_citta='comunita/data/residenti_per_cittadinanza_citta.csv, anno 2025, cittadinanza con più residenti')

cen = read_json('censimenti/data/dati.json')
cenn = {}
for e in cen['nil']:
    cenn[e['i']] = e
lau_city = cen['comune']['lau'][-1]
f1_city = cen['comune']['f1'][-1]
dlau, df1 = {}, {}
for i in MASTER:
    e = cenn.get(i)
    if not e:
        dlau[i] = df1[i] = (None, None, 'il quartiere non compare nella fonte')
        continue
    lau, f1 = e['v']['lau'][-1], e['v']['f1'][-1]
    pop = e['v']['pop'][-1]
    fl = 'piccolo' if (pop is not None and pop < 3000) else None
    dlau[i] = (lau, fl, None if lau is not None else 'dato mancante nella fonte')
    df1[i] = (f1, fl, None if f1 is not None else 'dato mancante nella fonte')
add('laureati', 'Chi ci abita', 'Residenti con un titolo universitario', 'censimenti', 'censimenti/data/dati.json', 'nil[].v.lau (ultimo anno: 2023)', 2023,
    '%', 'pct', lau_city, dlau, alto='più residenti con titolo universitario', basso='meno residenti con titolo universitario', evid=True,
    nota='Titoli terziari su residenti di 9 anni e più (censimento permanente 2023).', csv_file='censimenti/data/dati.json',
    origine_citta='censimenti/data/dati.json, comune.lau (ultimo anno)')
add('famiglie_sole', 'Chi ci abita', 'Famiglie di una sola persona', 'censimenti', 'censimenti/data/dati.json', 'nil[].v.f1 (ultimo anno: 2023)', 2023,
    '%', 'pct', f1_city, df1, alto='più famiglie di una sola persona', basso='meno famiglie di una sola persona', evid=True,
    csv_file='censimenti/data/dati.json', origine_citta='censimenti/data/dati.json, comune.f1 (ultimo anno)')

arr = read_csv('arrivi-partenze/data/nil_saldi.csv')
arr_city = weighted_city(arr, 'id_nil', 'saldo_totale_x1000_anno_2020_2024', 'residenti_medi_2020_2024')
darr = {}
for r in arr:
    i = int(r['id_nil'])
    v = num(r['saldo_totale_x1000_anno_2020_2024'])
    fl = 'piccolo' if (num(r['residenti_medi_2020_2024']) or 0) < 3000 else None
    darr[i] = (v, fl, None if v is not None else 'la pagina non lo mostra: meno di 3.000 residenti')
add('saldo_migratorio', 'Chi ci abita', 'Saldo di residenti: iscritti meno cancellati, ogni 1.000 residenti l\'anno', 'arrivi-partenze',
    'arrivi-partenze/data/nil_saldi.csv', 'saldo_totale_x1000_anno_2020_2024', '2020–2024', 'per 1.000 residenti', 'num', round(arr_city, 1), full(darr),
    alto='il saldo di residenti più favorevole', basso='il saldo di residenti meno favorevole', evid=True,
    nota='Cambi di residenza registrati (con altri comuni italiani e con l\'estero), non persone che ci sono davvero.',
    origine_citta='calcolato: media dei saldi dei quartieri pesata con residenti_medi_2020_2024 (nil_saldi.csv)')

# ================================================================== CASE E SOLDI (via quartieri-che-cambiano)
qg = read_json('quartieri-che-cambiano/data/nil.geojson')
QG = {f['properties']['i']: f['properties'] for f in qg['features']}
qc = {int(r['id_nil']): r for r in read_csv('quartieri-che-cambiano/data/nil.csv')}
qri = read_json('quartieri-che-cambiano/data/riepilogo.json')
red_city = read_json('redditi/data/riepilogo.json')['serie']['Milano']['media_euro2025'][-1]
pre_city = read_json('prezzi-case/data/riepilogo.json')['abitazioni'][-1]['reale']
dred, dpre = {}, {}
for i in MASTER:
    lv = QG.get(i, {}).get('liv_v') or {}
    dred[i] = (lv.get('red'), 'piccolo' if (RES25.get(i) or 0) < 1000 else None, 'non calcolato: più della metà delle case è in CAP con sede fiscale instabile (o quartiere senza residenti)' if lv.get('red') is None else None)
    dpre[i] = (lv.get('pre'), 'piccolo' if (RES25.get(i) or 0) < 1000 else None, 'dato mancante nella fonte' if lv.get('pre') is None else None)
add('reddito', 'Case e soldi', 'Reddito medio per contribuente (stima dai CAP)', 'redditi', 'quartieri-che-cambiano/data/nil.geojson', 'liv_v.red', 2024,
    '€ (euro 2025)', 'eur', red_city, dred, alto='il reddito medio per contribuente più alto', basso='il reddito medio per contribuente più basso', evid=False,
    nota='Il Comune pubblica i redditi solo per CAP (38 zone): il valore del quartiere è la media dei CAP dei suoi civici residenziali. Contribuenti, non tutti i residenti.',
    stima='cap', csv_file='quartieri-che-cambiano/data/nil.geojson', origine_citta='redditi/data/riepilogo.json, serie.Milano.media_euro2025 (ultimo anno, 2024)')
add('prezzo_vendita', 'Case e soldi', 'Prezzo di vendita delle case (stima OMI)', 'prezzi-case', 'quartieri-che-cambiano/data/nil.geojson', 'liv_v.pre', '2026 (1° semestre)',
    '€ al m² (euro 2025)', 'eur', pre_city, dpre, alto='i prezzi di vendita più alti', basso='i prezzi di vendita più bassi', evid=False,
    nota='Quotazioni OMI dell\'Agenzia delle Entrate (abitazioni civili): stime per zona, portate al quartiere con i civici.',
    stima='omi', csv_file='quartieri-che-cambiano/data/nil.geojson', origine_citta='prezzi-case/data/riepilogo.json, abitazioni[ultimo semestre 2026/1].reale')
med = lambda key: qri['mediane'][key]
for iid, key, et, anno, hi, lo in [
    ('var_reddito', 'reddito_var', 'Reddito reale: variazione', '2011→2024', None, None),
    ('var_prezzo', 'prezzo_var', 'Prezzo di vendita OMI reale: variazione', '2014→2026', None, None),
    ('var_affitto', 'affitto_var', 'Affitto OMI reale: variazione', '2014→2026', None, None)]:
    d = {}
    for i in MASTER:
        r = qc.get(i)
        v = num(r[key]) if r else None
        fuori = 'piccolo' if (r and r.get('in_classifica') != '1') else None
        d[i] = (v, fuori, None if v is not None else ('non calcolato: reddito instabile per CAP' if key == 'reddito_var' else 'dato mancante nella fonte'))
    add(iid, 'Case e soldi', et, 'quartieri-che-cambiano', 'quartieri-che-cambiano/data/nil.csv', key, anno, '%', 'pct', med(key), d,
        stima='cap' if key == 'reddito_var' else 'omi', ref='mediana dei quartieri in classifica',
        origine_citta='quartieri-che-cambiano/data/riepilogo.json, mediane.' + key,
        nota='Variazione in termini reali (euro 2025), dato di zona OMI o di CAP portato al quartiere.')

dq = {}
for i in MASTER:
    r = qc.get(i)
    if r and r.get('in_classifica') == '1' and num(r['rango']) is not None:
        dq[i] = (num(r['rango']), None, None, {'min': num(r['rango_min_varianti']), 'max': num(r['rango_max_varianti']), 'tip': r['tipologia']})
    else:
        dq[i] = (None, None, 'fuori classifica: meno di 2.000 residenti')
add('cambiamento', 'Case e soldi', 'Posto nella classifica dei quartieri che cambiano (1° = cambia di più)', 'quartieri-che-cambiano',
    'quartieri-che-cambiano/data/nil.csv', 'rango (e rango_min_varianti, rango_max_varianti)', '2011–2026', 'posto su 73', 'rango', None, dq, tipo='rango',
    nota='Indice di sette segnali (redditi, prezzi, affitti, affitti brevi, locali, giovani adulti, laureati). Confronto tra quartieri, non misura chi se ne va o chi arriva.')

ab = read_csv('affitti-brevi/data/nil.csv')
dab = {}
for r in ab:
    i = int(r['nil'])
    v = num(r['annunci_per_100_abitazioni'])
    fl = 'piccolo' if r['piccolo_denominatore'] == 'True' else None
    dab[i] = (v, fl, None if v is not None else 'dato mancante nella fonte')
add('airbnb', 'Case e soldi', 'Annunci di affitto breve ogni 100 abitazioni', 'affitti-brevi', 'affitti-brevi/data/nil.csv', 'annunci_per_100_abitazioni', '19/9/2026',
    'ogni 100 abitazioni', 'num', read_json('affitti-brevi/data/riepilogo.json')['citta']['annunci_per_100'], full(dab),
    alto='più annunci di affitto breve ogni 100 abitazioni', basso='meno annunci di affitto breve ogni 100 abitazioni', evid=True,
    nota='Annunci Airbnb (Inside Airbnb) su abitazioni del censimento 2023. Sotto 2.000 abitazioni o residenti il rapporto non è affidabile.',
    origine_citta='affitti-brevi/data/riepilogo.json, citta.annunci_per_100')
dpr = {}
for r in ab:
    i = int(r['nil'])
    v = num(r['prezzo_mediano_case_intere'])
    n = num(r['n_prezzi_case_intere']) or 0
    fl = 'piccolo' if (n < 30 or r['piccolo_denominatore'] == 'True') else None
    dpr[i] = (v, fl, None if v is not None else 'meno di 30 annunci con prezzo')
pr_city = [x for x in read_json('affitti-brevi/data/riepilogo.json')['prezzi'] if x['snapshot'] == '2026-09-19' and x['gruppo'].startswith('case intere, notti 1-7')][0]['mediana']
add('prezzo_notte', 'Case e soldi', 'Prezzo mediano a notte, case intere in affitto breve', 'affitti-brevi', 'affitti-brevi/data/nil.csv', 'prezzo_mediano_case_intere', '19/9/2026',
    '€ a notte', 'eur', pr_city, full(dpr), alto='il prezzo mediano a notte più alto', basso='il prezzo mediano a notte più basso', evid=False,
    nota='Prezzo richiesto dall\'host (1–7 notti), non prezzo pagato. Servono almeno 30 annunci con prezzo nel quartiere.',
    origine_citta='affitti-brevi/data/riepilogo.json, prezzi (snapshot 2026-09-19, case intere, notti 1-7)')

cp = read_csv('case-popolari/data/nil.csv')
cp_sum_c = sum(num(r['canone_fatturato_ALER_2016_milioni_euro']) or 0 for r in cp) * 1e6
cp_sum_a = sum(num(r['abitazioni_2023']) or 0 for r in cp)
dcp = cells(cp, 'id_nil', 'canone_ALER_2016_per_abitazione_euro', lambda r, i: 'piccolo' if (num(r['abitazioni_2023']) or 0) < 1000 else None)
add('aler', 'Case e soldi', 'Canone ALER fatturato per abitazione del quartiere', 'case-popolari', 'case-popolari/data/nil.csv', 'canone_ALER_2016_per_abitazione_euro', 2016,
    '€ l\'anno per abitazione', 'eur', round(cp_sum_c / cp_sum_a), full(dcp),
    nota='Solo ALER, canone fatturato nel 2016 (anche negozi e box): mancano gli alloggi del Comune (MM). Misura la presenza di ALER, non quante case sono vuote.',
    evid=False, origine_citta='calcolato: somma canone_fatturato_ALER_2016_milioni_euro / somma abitazioni_2023 (case-popolari/data/nil.csv)', dec=0)

co = read_csv('costruzioni/data/nil.csv')
co_city = sum(num(r['nuove_abitazioni_2014_2024']) or 0 for r in co) / sum(num(r['abitanti_2024']) or 0 for r in co) * 1000
dco = cells(co, 'id_nil', 'nuove_abitazioni_ogni_1000_abitanti_2024', lambda r, i: 'piccolo' if r['in_classifica_almeno_5000_abitanti'] != '1' else None)
add('nuove_case', 'Case e soldi', 'Nuove abitazioni costruite ogni 1.000 abitanti', 'costruzioni', 'costruzioni/data/nil.csv', 'nuove_abitazioni_ogni_1000_abitanti_2024', '2014–2024',
    'ogni 1.000 abitanti', 'num', round(co_city, 1), full(dco), alto='più nuove abitazioni ogni 1.000 abitanti', basso='meno nuove abitazioni ogni 1.000 abitanti', evid=True,
    nota='Abitazioni dei nuovi fabbricati con titolo edilizio (tolte le demolizioni solo nel dato sul volume). Quartieri con almeno 5.000 abitanti.',
    origine_citta='calcolato: somma nuove_abitazioni_2014_2024 / somma abitanti_2024 × 1000 (costruzioni/data/nil.csv)')

# ================================================================== SERVIZI E SCUOLE
c15 = read_csv('citta-15-minuti/data/nil_punteggi.csv')
c15e = read_csv('citta-15-minuti/data/nil_punteggi_extra.csv')
c15r = read_json('citta-15-minuti/data/riepilogo.json')['citta']
c15x = read_json('citta-15-minuti/data/extra.json')['citta']


def f15(r, i):
    return 'piccolo' if r['stato'] != 'in classifica' else None


def r15(rows, key):
    d = cells(rows, 'ID_NIL', key, f15)
    for r in rows:
        if r['stato'] == 'dato non affidabile':
            i = int(r['ID_NIL'])
            d[i] = (d[i][0], 'piccolo', None)
    return full(d, 'il quartiere non compare nella fonte (nessun civico residenziale)')


add('c15_10', 'Servizi e scuole', 'Servizi raggiungibili a piedi in 15 minuti (punteggio su 10)', 'citta-15-minuti', 'citta-15-minuti/data/nil_punteggi.csv', 'punteggio_su_10', '2025',
    'su 10', 'num', c15r['p'], r15(c15, 'punteggio_su_10'), alto='più servizi raggiungibili a piedi in 15 minuti', basso='meno servizi raggiungibili a piedi in 15 minuti', evid=True,
    nota='Farmacia, medico, nido, scuola, biblioteca, mercato, parco, sport, posta, alimentari: un punto ciascuno. Residenti distribuiti in parti uguali sui civici (stima).',
    origine_citta='citta-15-minuti/data/riepilogo.json, citta.p')
add('c15_20', 'Servizi e scuole', 'Punteggio con i dieci servizi extra (su 20)', 'citta-15-minuti', 'citta-15-minuti/data/nil_punteggi_extra.csv', 'punteggio_totale_su_20', '2025',
    'su 20', 'num', c15x['p20'], r15(c15e, 'punteggio_totale_su_20'), alto='più servizi (essenziali ed extra) a 15 minuti a piedi', basso='meno servizi (essenziali ed extra) a 15 minuti a piedi', evid=True,
    nota='Aggiunge cinema, teatri e musei, aree gioco, piscine, aree cani, metro, BikeMi, supermercati, ospedali, librerie.',
    origine_citta='citta-15-minuti/data/extra.json, citta.p20')
tipi15 = {t['t']: t for t in read_json('citta-15-minuti/data/riepilogo.json')['tipi']}
add('c15_metro', 'Servizi e scuole', 'Residenti con una fermata della metropolitana a 15 minuti a piedi', 'citta-15-minuti', 'citta-15-minuti/data/nil_punteggi_extra.csv', 'quota_entro15_metro', '2025',
    '%', 'pct', round(100 * [t for t in read_json('citta-15-minuti/data/extra.json')['tipi'] if t['t'] == 'metro'][0]['q'], 1),
    full({int(r['ID_NIL']): (None if num(r['quota_entro15_metro']) is None else round(100 * num(r['quota_entro15_metro']), 1), f15(r, int(r['ID_NIL'])), None) for r in c15e}, 'il quartiere non compare nella fonte'),
    alto='più residenti vicini a una fermata della metropolitana', basso='meno residenti vicini a una fermata della metropolitana', evid=True,
    origine_citta='citta-15-minuti/data/extra.json, tipi[t=metro].q')

sc = read_csv('scuole/data/nil_scuole.csv')
sc_tot = {k: sum(num(r[k]) or 0 for r in sc) for k in ('I15', 'I24', 'R15', 'R24')}
scv = lambda k15, k24: round(100 * (sc_tot[k24] / sc_tot[k15] - 1), 1)
add('alunni_var', 'Servizi e scuole', 'Alunni nelle scuole del quartiere: variazione (infanzia, primaria, media)', 'scuole', 'scuole/data/nil_scuole.csv', 'Iv', '2015/16→2024/25',
    '%', 'pct', scv('I15', 'I24'), full(cells(sc, 'id_nil', 'Iv', nullreason='meno di 200 alunni nel 2015 o nessuna scuola nel quartiere')),
    alto='una crescita maggiore degli alunni nelle scuole del quartiere', basso='un calo maggiore degli alunni nelle scuole del quartiere', evid=True,
    nota='Alunni contati dove sta la scuola, non dove abitano. In grigio nella pagina i quartieri con meno di 200 alunni nel 2015.',
    origine_citta='calcolato: somma I24 / somma I15 − 1 (scuole/data/nil_scuole.csv)')
add('bambini_var', 'Servizi e scuole', 'Bambini residenti di 3–13 anni: variazione', 'scuole', 'scuole/data/nil_scuole.csv', 'Rv', '2015→2024',
    '%', 'pct', scv('R15', 'R24'), full(cells(sc, 'id_nil', 'Rv', nullreason='meno di 200 bambini nel 2015')),
    alto='una crescita maggiore dei bambini di 3–13 anni', basso='un calo maggiore dei bambini di 3–13 anni', evid=True,
    origine_citta='calcolato: somma R24 / somma R15 − 1 (scuole/data/nil_scuole.csv)')

pn = read_csv('scuole-domani/data/proiezione_nil.csv')
agg = defaultdict(lambda: [0.0, 0.0])
for r in pn:
    i = int(r['id_nil'])
    a24, p34 = num(r['iscritti_2024']), num(r['p2034'])
    if a24 is not None and p34 is not None:
        agg[i][0] += a24
        agg[i][1] += p34
dpn = {}
for i, (a, p) in agg.items():
    dpn[i] = (round(100 * (p / a - 1), 1) if a >= 200 else None, None, None if a >= 200 else 'meno di 200 alunni nel 2024')
ta, tp = sum(a for a, p in agg.values()), sum(p for a, p in agg.values())
add('alunni_2034', 'Servizi e scuole', 'Alunni previsti nel 2034 rispetto al 2024 (proiezione, scenario centrale)', 'scuole-domani', 'scuole-domani/data/proiezione_nil.csv', 'iscritti_2024 e p2034 (somma dei tre ordini)', '2024→2034',
    '%', 'pct', round(100 * (tp / ta - 1), 1), full(dpn), tipo='num', evid=False,
    nota='È una proiezione (bambini già nati, nascite future stabili), non un dato: la pagina ne mostra il margine d\'errore.',
    stima='proiezione', origine_citta='calcolato: somma p2034 / somma iscritti_2024 − 1 su tutti i quartieri (scuole-domani/data/proiezione_nil.csv)')

bib = read_csv('biblioteche/data/biblioteche_posizione.csv')
cb = defaultdict(int)
for r in bib:
    cb[int(r['id_nil'])] += 1
add('biblioteche', 'Servizi e scuole', 'Biblioteche del Sistema bibliotecario nel quartiere', 'biblioteche', 'biblioteche/data/biblioteche_posizione.csv', 'conteggio delle righe per id_nil', 'elenco attuale',
    'biblioteche', 'int', None, {i: (cb.get(i, 0), None, None) for i in MASTER}, tipo='conto', ref='sul totale: %d biblioteche' % len(bib))

an = read_csv('antenne/data/nil.csv')
an_city = read_json('antenne/data/riepilogo.json')['citta']['per_1000']
dan = cells(an, 'id_nil', 'mobile_per_1000_ab', lambda r, i: 'piccolo' if (num(r['abitanti_2024']) or 0) < 1000 else None)
add('antenne', 'Servizi e scuole', 'Impianti di telefonia mobile accesi ogni 1.000 abitanti', 'antenne', 'antenne/data/nil.csv', 'mobile_per_1000_ab', '8/6/2025',
    'ogni 1.000 abitanti', 'num', an_city, full(dan, 'il quartiere non compare nella fonte'),
    alto='più impianti di telefonia mobile per abitante', basso='meno impianti di telefonia mobile per abitante', evid=False, dec=2,
    nota='Catasto CASTEL (ARPA Lombardia): conta gli impianti, non la potenza né l\'esposizione. Tolti i quartieri con meno di 1.000 abitanti.',
    origine_citta='antenne/data/riepilogo.json, citta.per_1000')

# ================================================================== VERDE E CLIMA
al = read_csv('alberi/data/nil.csv')
al_c = read_json('alberi/data/riepilogo.json')['citta']
dal = cells(al, 'id_nil', 'alberi_per_1000_abitanti_2025', lambda r, i: 'piccolo' if r['in_classifica_almeno_5000_abitanti'] != '1' else None)
add('alberi', 'Verde e clima', 'Alberi gestiti dal Comune ogni 1.000 abitanti', 'alberi', 'alberi/data/nil.csv', 'alberi_per_1000_abitanti_2025', '31/3/2025',
    'ogni 1.000 abitanti', 'num', al_c['per_1000_abitanti'], full(dal), alto='più alberi del Comune per abitante', basso='meno alberi del Comune per abitante', evid=True, dec=0,
    nota='Solo gli alberi schedati dal Comune (strade, parchi pubblici, cimiteri): mancano i giardini privati. Quartieri con almeno 5.000 abitanti.',
    origine_citta='alberi/data/riepilogo.json, citta.per_1000_abitanti')
al_tot = al_c['alberi']
dalv = cells(al, 'id_nil', 'variazione_pct_2023_2025', lambda r, i: 'piccolo' if r['in_classifica_almeno_5000_abitanti'] != '1' else None)
add('alberi_var', 'Verde e clima', 'Alberi gestiti dal Comune: variazione', 'alberi', 'alberi/data/nil.csv', 'variazione_pct_2023_2025', '2023→2025',
    '%', 'pct', round(100 * (al_tot['2025'] / al_tot['2023'] - 1), 1), full(dalv), evid=False,
    nota='Il dato non dice se un albero è stato tagliato, è morto o è uscito dall\'elenco: tra le edizioni il Comune può cambiare il perimetro.',
    origine_citta='alberi/data/riepilogo.json, citta.alberi (2025 su 2023)')
add('c15_parchi', 'Verde e clima', 'Residenti con un parco (almeno 5.000 m²) a 15 minuti a piedi', 'citta-15-minuti', 'citta-15-minuti/data/nil_punteggi.csv', 'quota_entro15_parchi', '2025',
    '%', 'pct', round(100 * tipi15['parchi']['q'], 1),
    full({int(r['ID_NIL']): (None if num(r['quota_entro15_parchi']) is None else round(100 * num(r['quota_entro15_parchi']), 1), f15(r, int(r['ID_NIL'])), None) for r in c15}, 'il quartiere non compare nella fonte'),
    alto='più residenti con un parco a 15 minuti', basso='meno residenti con un parco a 15 minuti', evid=True,
    nota='Il Parco Agricolo Sud non è nei dati dei parchi del Comune: nelle periferie del sud i parchi risultano più lontani di quanto siano.',
    origine_citta='citta-15-minuti/data/riepilogo.json, tipi[t=parchi].q')
su = read_csv('suolo/data/nil_suolo.csv')
su_c = [x for x in read_json('suolo/data/riepilogo.json')['milano']['serie'] if x['anno'] == 2025][0]['consumato_pct']
add('suolo', 'Verde e clima', 'Suolo consumato (non più naturale o agricolo)', 'suolo', 'suolo/data/nil_suolo.csv', 'pct_2025', 2025,
    '% della superficie', 'pct', su_c, full(cells(su, 'id_nil', 'pct_2025')), alto='più suolo consumato', basso='meno suolo consumato', evid=True,
    nota='Carta del consumo di suolo ISPRA/SNPA. Per i parchi e i quartieri agricoli la quota bassa è attesa.',
    origine_citta='suolo/data/riepilogo.json, milano.serie[anno 2025].consumato_pct')

cal = [r for r in read_csv('caldo/data/stazioni.csv') if r['classe'] == 'urbana']
calg = defaultdict(list)
for r in cal:
    k = nil_by_name(r['nil'], 'caldo/data/stazioni.csv')
    if k:
        calg[k].append(num(r['notte']))
dcal = {k: (round(statistics.mean(v), 2), 'stazione', None) for k, v in calg.items()}
cal_med = round(statistics.mean(num(r['notte']) for r in cal), 2)
add('notte_calda', 'Verde e clima', 'Notti più calde della campagna (stazione ARPA nel quartiere)', 'caldo', 'caldo/data/stazioni.csv', 'notte', 'estati 2017–2025',
    '°C in più', 'num', cal_med, full(dcal, 'nessuna stazione di misura nel quartiere'), dec=2, tipo='num', ref='media delle stazioni urbane',
    nota='Differenza con la campagna nelle ore notturne (estati giugno-agosto). Dove le stazioni sono due, media delle due.',
    ftxt='Misura il punto in cui sta la stazione, non tutto il quartiere: non entra nelle classifiche.',
    origine_citta='calcolato: media del campo notte delle %d stazioni urbane (caldo/data/stazioni.csv)' % len(cal))

# ================================================================== VITA IN STRADA
ri = read_csv('ristoranti/data/nil.csv')
ri_c = read_json('ristoranti/data/riepilogo.json')['citta']
dri = cells(ri, 'id_nil', 'in_piano_per_1000ab', lambda r, i: 'piccolo' if r['piccolo'] == '1' else None)
add('locali', 'Vita in strada', 'Bar, ristoranti e locali ogni 1.000 abitanti', 'ristoranti', 'ristoranti/data/nil.csv', 'in_piano_per_1000ab', 2026,
    'ogni 1.000 abitanti', 'num', ri_c['in_piano_per_1000'], full(dri), alto='più bar, ristoranti e locali per abitante', basso='meno bar, ristoranti e locali per abitante', evid=True,
    nota='Pratiche del registro del Comune per i pubblici esercizi di somministrazione. Sotto 3.000 residenti dividere non ha senso.',
    origine_citta='ristoranti/data/riepilogo.json, citta.in_piano_per_1000')
pr19 = read_csv('ristoranti/data/pratiche_2019_2026_nil.csv')
pr_t = sum(num(r['registro_2026']) or 0 for r in pr19) / sum(num(r['registro_2019']) or 0 for r in pr19)
dpr19 = cells(pr19, 'id_nil', 'variazione_pct', lambda r, i: 'piccolo' if (num(r['registro_2019']) or 0) < 40 else None)
add('locali_var', 'Vita in strada', 'Bar, ristoranti e locali: variazione', 'ristoranti', 'ristoranti/data/pratiche_2019_2026_nil.csv', 'variazione_pct', '2019→2026',
    '%', 'pct', round(100 * (pr_t - 1), 1), full(dpr19), alto='una crescita maggiore dei locali', basso='un calo maggiore dei locali', evid=True,
    nota='Pratiche del registro 2026 su quelle del 2019. Servono almeno 40 pratiche nel 2019.',
    origine_citta='calcolato: somma registro_2026 / somma registro_2019 − 1 (ristoranti/data/pratiche_2019_2026_nil.csv)')
ca = read_csv('cani/data/aree_cani_per_nil.csv')
add('aree_cani', 'Vita in strada', 'Aree per i cani ogni 100.000 abitanti', 'cani', 'cani/data/aree_cani_per_nil.csv', 'aree_cani_per_100mila_ab', '2024',
    'ogni 100.000 abitanti', 'num', read_json('cani/data/riepilogo.json')['comune']['per100k'],
    full(cells(ca, 'id_nil', 'aree_cani_per_100mila_ab', lambda r, i: 'piccolo' if r['in_classifica_almeno_5000_abitanti'] != '1' else None,
               nullreason='senza aree cani, o meno di 5.000 residenti: la pagina non calcola il rapporto')),
    alto='più aree cani per abitante', basso='meno aree cani per abitante', evid=True,
    nota='Aree recintate e prati del Comune. Quartieri con almeno 5.000 residenti.', origine_citta='cani/data/riepilogo.json, comune.per100k')
bc = read_json('beni-confiscati/data/nil.geojson')
BC = {f['properties']['i']: f['properties'] for f in bc['features']}
cu_med = statistics.median(p['cu'] for p in BC.values())
add('confiscati', 'Vita in strada', 'Unità confiscate alla mafia nell\'elenco del Comune', 'beni-confiscati', 'beni-confiscati/data/nil.geojson', 'cu', 'giugno 2026',
    'unità', 'int', cu_med, {i: ((BC[i]['cu'] if i in BC else None), None, None if i in BC else 'il quartiere non compare nella fonte') for i in MASTER}, tipo='conto',
    ref='mediana dei quartieri', origine_citta='calcolato: mediana del campo cu dei 88 quartieri (beni-confiscati/data/nil.geojson)',
    nota='Si contano beni, non persone: case, box, negozi, terreni.')

bo = read_csv('botteghe/data/botteghe.csv')
cbo = defaultdict(int)
for r in bo:
    if r['stato'].startswith(('attiva', 'probabile')) and r['nil']:
        k = nil_by_name(r['nil'], 'botteghe/data/botteghe.csv')
        if k:
            cbo[k] += 1
bo_med = statistics.median(cbo.get(i, 0) for i in MASTER)
add('botteghe', 'Storia e memoria', 'Botteghe storiche ancora attive o probabili', 'botteghe', 'botteghe/data/botteghe.csv', 'conteggio di stato = attiva/probabile per nil', 'elenchi 2024–2026',
    'botteghe', 'int', bo_med, {i: (cbo.get(i, 0), None, None) for i in MASTER}, tipo='conto', ref='mediana dei quartieri',
    nota='Albo del Comune e elenco della Regione. «Probabile» = solo negli elenchi, senza prova indipendente.',
    origine_citta='calcolato: mediana dei conteggi per quartiere (botteghe/data/botteghe.csv)')

# ================================================================== STORIA E MEMORIA
pi = read_csv('pietre-inciampo/data/nil.csv')


def pietre_cells(rows):
    """per10mila e vuoto nel file dove le pietre sono 0: lo zero si calcola (0 / abitanti), non si inventa."""
    d = {}
    for r in rows:
        i = int(r['id'])
        ab, n = num(r['abitanti']), num(r['pietre'])
        v = num(r['per10mila'])
        if v is None and n == 0 and ab:
            v = 0.0
        d[i] = (v, 'piccolo' if (ab or 0) < 3000 else None, None if v is not None else 'quartiere senza abitanti nei dati')
    return d

pi_c = sum(num(r['pietre']) for r in pi) / sum(num(r['abitanti']) or 0 for r in pi) * 1e4
add('pietre', 'Storia e memoria', 'Pietre d\'inciampo ogni 10.000 abitanti', 'pietre-inciampo', 'pietre-inciampo/data/nil.csv', 'per10mila', 2026,
    'ogni 10.000 abitanti', 'num', round(pi_c, 2),
    full(pietre_cells(pi)),
    alto='più pietre d\'inciampo per abitante', basso='meno pietre d\'inciampo per abitante', evid=True, dec=2,
    nota='Una pietra è posata davanti all\'ultima abitazione scelta di una persona deportata: dice dove abitavano, non quanto il quartiere ricorda.',
    origine_citta='calcolato: somma pietre / somma abitanti × 10.000 (pietre-inciampo/data/nil.csv)')
st = read_csv('statue/data/per_nil.csv')
st_c = sum(num(r['opere']) for r in st) / sum(num(r['area_kmq']) for r in st)
add('opere', 'Storia e memoria', 'Statue, lapidi e murali per km²', 'statue', 'statue/data/per_nil.csv', 'opere_per_kmq', 2026,
    'per km²', 'num', round(st_c, 1), full(cells(st, 'id_nil', 'opere_per_kmq')),
    alto='più statue, lapidi e murali per km²', basso='meno statue, lapidi e murali per km²', evid=False,
    nota='Opere trovate in Wikidata, OpenStreetMap e catalogo ICCD: non è un censimento completo.',
    origine_citta='calcolato: somma opere / somma area_kmq (statue/data/per_nil.csv)')

# ================================================================== VOTO
EIDX = read_json('elezioni/data/index.json')
EL = {e['id']: e for e in EIDX['elezioni']}
INFO = read_json('elezioni/data/nil_info.json')


def affl(eid, fname):
    n = read_json('elezioni/data/nil/%s.json' % fname)
    city = EL[eid]['city']
    d = {}
    for i in MASTER:
        p = n['p'].get(str(i))
        if not p or not p.get('e'):
            d[i] = (None, None, 'il quartiere non compare nella fonte')
            continue
        weak = p['vt'] < 1000 or INFO.get(str(i), {}).get('x')
        d[i] = (round(100 * p['vt'] / p['e'], 1), 'piccolo' if weak else None, None)
    return d, round(100 * city['vt'] / city['e'], 1)


d21, c21 = affl('comunali_sindaco_2021-10-03', 'comunali_sindaco_2021-10-03')
add('affluenza21', 'Voto', 'Affluenza alle comunali (sindaco, primo turno)', 'elezioni', 'elezioni/data/nil/comunali_sindaco_2021-10-03.json', 'p[nil].vt / p[nil].e', 2021,
    '% degli elettori', 'pct', c21, d21, alto='una maggiore affluenza alle comunali 2021', basso='una minore affluenza alle comunali 2021', evid=True,
    nota='I risultati per quartiere sono ricostruiti dalle sezioni elettorali: dove una sezione sta in più quartieri è una stima.',
    stima='sezioni', origine_citta='elezioni/data/index.json, elezioni[comunali_sindaco_2021-10-03].city (vt / e)')
d22, c22 = affl('camera_2022-09-25', 'camera_2022-09-25')
add('affluenza22', 'Voto', 'Affluenza alle politiche (Camera)', 'elezioni', 'elezioni/data/nil/camera_2022-09-25.json', 'p[nil].vt / p[nil].e', 2022,
    '% degli elettori', 'pct', c22, d22, alto='una maggiore affluenza alle politiche 2022', basso='una minore affluenza alle politiche 2022', evid=True,
    nota='Dati ufficiosi del Comune. Come sopra, per quartiere è una stima dalle sezioni.', stima='sezioni',
    origine_citta='elezioni/data/index.json, elezioni[camera_2022-09-25].city (vt / e)')
cam = EL['camera_2022-09-25']
camn = read_json('elezioni/data/nil/camera_2022-09-25.json')
fams = cam['fam']


def fam_shares(v):
    s = [0.0] * len(fams)
    for (nome, fi), x in zip(cam['par'], v):
        s[fi] += x
    t = sum(s)
    return [100 * x / t for x in s] if t else None


city_sh = fam_shares(cam['city']['v'])
dfam = {}
for i in MASTER:
    p = camn['p'].get(str(i))
    if not p or not p.get('vt'):
        dfam[i] = (None, None, 'il quartiere non compare nella fonte')
        continue
    sh = fam_shares(p['v'])
    if not sh:
        dfam[i] = (None, None, 'nessun voto di lista')
        continue
    k = max(range(len(sh)), key=lambda j: sh[j])
    weak = p['vt'] < 1000 or INFO.get(str(i), {}).get('x')
    dfam[i] = (fams[k], 'piccolo' if weak else None, None, {'s': round(sh[k], 1), 'c': round(city_sh[k], 1)})
add('famiglia', 'Voto', 'Schieramento con più voti di lista alle politiche (Camera)', 'elezioni', 'elezioni/data/nil/camera_2022-09-25.json', 'p[nil].v raggruppato con elezioni/data/index.json (par, fam)', 2022,
    '% dei voti di lista', 'testo', fams[max(range(len(city_sh)), key=lambda j: city_sh[j])], dfam, tipo='testo_voto',
    nota='Gli schieramenti sono raggruppamenti nostri dei partiti («famiglie», da rivedere), dati ufficiosi. Accanto la quota in città della stessa famiglia.',
    stima='sezioni', origine_citta='elezioni/data/index.json, elezioni[camera_2022-09-25].city.v raggruppato per famiglia')

# ================================================================== testi dei flag, per indicatore (soglie delle pagine di origine)
FTXT = {
    'eta_media': 'Meno di 3.000 residenti: il valore oscilla (residenze collettive).',
    'quota_65': 'Meno di 3.000 residenti: la percentuale oscilla.',
    'quota_80': 'Meno di 3.000 residenti: la percentuale oscilla.',
    'laureati': 'Meno di 3.000 residenti: la percentuale oscilla.',
    'famiglie_sole': 'Meno di 3.000 residenti: la percentuale oscilla.',
    'saldo_migratorio': 'Meno di 3.000 residenti: il saldo ogni 1.000 abitanti è instabile.',
    'reddito': 'Quartiere con meno di 1.000 residenti: stima non affidabile.',
    'prezzo_vendita': 'Quartiere con meno di 1.000 residenti: stima non affidabile.',
    'var_reddito': 'Quartiere fuori dalla classifica della pagina (meno di 2.000 residenti).',
    'var_prezzo': 'Quartiere fuori dalla classifica della pagina (meno di 2.000 residenti).',
    'var_affitto': 'Quartiere fuori dalla classifica della pagina (meno di 2.000 residenti).',
    'airbnb': 'Meno di 2.000 abitazioni o residenti: il rapporto non è affidabile.',
    'prezzo_notte': 'Meno di 30 annunci con prezzo (o quartiere piccolo): mediana non affidabile.',
    'aler': 'Meno di 1.000 abitazioni: il rapporto non è affidabile.',
    'nuove_case': 'Meno di 5.000 abitanti: la pagina non lo mette in classifica.',
    'c15_10': 'Fuori classifica nella pagina (meno di 30 civici o 1.000 residenti) o dato non affidabile.',
    'c15_20': 'Fuori classifica nella pagina (meno di 30 civici o 1.000 residenti) o dato non affidabile.',
    'c15_metro': 'Fuori classifica nella pagina (meno di 30 civici o 1.000 residenti) o dato non affidabile.',
    'c15_parchi': 'Fuori classifica nella pagina (meno di 30 civici o 1.000 residenti) o dato non affidabile.',
    'antenne': 'Meno di 1.000 abitanti: la pagina non lo mette in classifica.',
    'alberi': 'Meno di 5.000 abitanti: la pagina non lo mette in classifica.',
    'alberi_var': 'Meno di 5.000 abitanti: la pagina non lo mette in classifica.',
    'locali': 'Meno di 3.000 residenti: dividere non ha senso.',
    'locali_var': 'Meno di 40 pratiche nel 2019: la percentuale ballerebbe troppo.',
    'aree_cani': 'Meno di 5.000 abitanti: la pagina non lo mette in classifica.',
    'pietre': 'Meno di 3.000 abitanti: il rapporto non è affidabile.',
    'affluenza21': 'Meno di 1.000 votanti, oppure quartiere piccolo o poco coperto dallo stradario 2020.',
    'affluenza22': 'Meno di 1.000 votanti, oppure quartiere piccolo o poco coperto dallo stradario 2020.',
    'famiglia': 'Meno di 1.000 votanti, oppure quartiere piccolo o poco coperto dallo stradario 2020.',
}
for _x in IND:
    if _x['id'] in FTXT and not _x.get('ftxt'):
        _x['ftxt'] = FTXT[_x['id']]

# ================================================================== classifiche, flag, salienti
NN = len(MASTER)
for ind in IND:
    id = ind['id']
    cs = VAL[id]
    out = {}
    elig = [(i, c[0]) for i, c in cs.items() if c[0] is not None and c[1] is None and ind['tipo'] in ('num', 'conto', 'rango')]
    vals = sorted(v for _, v in elig)
    ind['n'] = len(elig)
    ind['_vals'] = vals
    if vals:
        ind['min'], ind['max'] = vals[0], vals[-1]
        if ind['tipo'] == 'conto' and ind['citta'] is None:
            pass
        if ind['ref'].startswith('mediana') and ind['citta'] is None:
            ind['citta'] = statistics.median(vals)
    for i in MASTER:
        c = cs[i]
        cell = {'v': c[0]}
        if c[1]:
            cell['f'] = c[1]
        if c[0] is None:
            cell['m'] = c[2] or 'dato mancante nella fonte'
        if len(c) > 3:
            cell['x'] = c[3]
        if c[0] is not None and c[1] is None and ind['tipo'] in ('num', 'conto'):
            cell['r'] = 1 + sum(1 for x in vals if x > c[0])
        elif c[0] is not None and c[1] is None and ind['tipo'] == 'rango':
            cell['r'] = int(c[0])
        out[i] = cell
    VAL[id] = out
IMAP = {x['id']: x for x in IND}

SAL = {}
for i in MASTER:
    cand = []
    for ind in IND:
        if not ind['evid']:
            continue
        cell = VAL[ind['id']][i]
        if cell.get('r') is None or cell.get('f'):
            continue
        v = cell['v']
        vs = ind['_vals']
        cge = sum(1 for x in vs if x >= v)   # quanti quartieri hanno almeno questo valore (pareggi compresi)
        cle = sum(1 for x in vs if x <= v)
        if cge <= 5:
            cand.append((cge, ind['id'], 'alto'))
        elif cle <= 5:
            cand.append((cle, ind['id'], 'basso'))
    # cambiamento: solo se l'intervallo di robustezza sta tutto in testa (primi 12) o in coda (ultimi 12)
    q = VAL['cambiamento'][i]
    if q.get('r') is not None:
        mn, mx = q['x']['min'], q['x']['max']
        n = IMAP['cambiamento']['n']
        if q['r'] <= 5 and mx is not None and mx <= 12:
            cand.append((q['r'], 'cambiamento', 'alto'))
        elif q['r'] >= n - 6 and mn is not None and mn >= n - 11:
            cand.append((n - q['r'] + 1, 'cambiamento', 'basso'))
    cand.sort()
    pick, temi = [], defaultdict(int)
    for k, iid, verso in cand:
        t = IMAP[iid]['tema']
        if temi[t] >= 2:
            continue
        temi[t] += 1
        pick.append({'i': iid, 'verso': verso, 'k': k, 'r': VAL[iid][i]['r'], 'n': IMAP[iid]['n']})
        if len(pick) == 5:
            break
    SAL[i] = pick

# ------------------------------------------------------------------ scrittura
FLAGS = {
    'piccolo': 'Pochi residenti o pochi dati: il valore oscilla e non entra nel posto in classifica.',
    'stazione': 'Una sola stazione di misura: vale per il punto, non per tutto il quartiere.',
}
STIME = {
    'cap': 'Stimato dai CAP (il Comune pubblica i redditi solo per CAP)',
    'omi': 'Stimato dalle zone OMI dell\'Agenzia delle Entrate',
    'sezioni': 'Stimato dalle sezioni elettorali',
    'proiezione': 'Proiezione, non dato',
}
nil_list = []
for i in sorted(MASTER):
    nil_list.append({'id': i, 'nome': MASTER[i]['nome'], 'municipio': MASTER[i]['municipio'], 'residenti': RES25.get(i),
                     'piccolo': (RES25.get(i) or 0) < 3000,
                     'quasi_vuoto': (RES25.get(i) or 0) < 1000})
ind_out = []
for ind in IND:
    d = {k: ind[k] for k in ('id', 'tema', 'et', 'pagina', 'file', 'campo', 'anno', 'unita', 'fmt', 'dec', 'tipo', 'alto', 'basso', 'evid', 'nota', 'stima', 'csv', 'ref', 'origine_citta', 'n', 'ftxt')}
    if 'min' in ind:
        d['min'], d['max'] = ind['min'], ind['max']
    d['citta'] = ind['citta']
    ind_out.append(d)

res = {
    'generato': '2026-11-01',
    'n_nil': NN,
    'temi': TEMI,
    'flags': FLAGS,
    'stime': STIME,
    'nil': nil_list,
    'indicatori': ind_out,
    'valori': {str(i): {iid: VAL[iid][i] for iid in VAL} for i in MASTER},
    'salienti': {str(i): SAL[i] for i in MASTER},
    'origine': {x['id']: {'file': x['file'], 'campo': x['campo'], 'citta': x['origine_citta']} for x in IND},
}
with open(os.path.join(OUT, 'schede.json'), 'w', encoding='utf-8') as fh:
    json.dump(res, fh, ensure_ascii=False, separators=(',', ':'))

geo = read_json('comunita/data/nil.geojson')
feats = []
for f in geo['features']:
    i = f['properties']['i']
    feats.append({'type': 'Feature', 'properties': {'i': i, 'n': MASTER[i]['nome']}, 'geometry': f['geometry']})
assert sorted(f['properties']['i'] for f in feats) == list(range(1, 89))
with open(os.path.join(OUT, 'nil.geojson'), 'w', encoding='utf-8') as fh:
    json.dump({'type': 'FeatureCollection', 'features': feats}, fh, ensure_ascii=False, separators=(',', ':'))

with open(os.path.join(BASE, 'quartiere', 'mismatch.json'), 'w', encoding='utf-8') as fh:
    json.dump(MISMATCH, fh, ensure_ascii=False, indent=1)

print('indicatori:', len(IND), '- quartieri:', NN)
for ind in IND:
    nmiss = sum(1 for i in MASTER if VAL[ind['id']][i]['v'] is None)
    nflag = sum(1 for i in MASTER if VAL[ind['id']][i].get('f'))
    print('  %-18s n=%-3s mancanti=%-3s flag=%-3s citta=%s' % (ind['id'], ind['n'], nmiss, nflag, ind['citta']))
print('mismatch nomi:', {k: len(v) for k, v in MISMATCH.items()})
print('salienti per quartiere (min/med/max):', min(len(v) for v in SAL.values()), statistics.median(len(v) for v in SAL.values()), max(len(v) for v in SAL.values()))
