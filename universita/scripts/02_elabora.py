"""Elabora i dati scaricati e scrive i file della pagina «Una città di studenti» in docs/universita/data/.
Uso: python -I -X utf8 universita/scripts/02_elabora.py
Letture: universita/dati_grezzi/ (MUR e Comune di Milano) e docs/eta/data/eta.json (residenti di Milano).
Il MUR conta gli iscritti per ateneo; «atenei milanesi» = i sette con Milano nel nome. Humanitas (Rozzano) e le università telematiche sono fuori."""
import csv, io, json, os, collections
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
G = os.path.join(R, 'universita', 'dati_grezzi')
OUT = os.path.join(R, 'docs', 'universita', 'data')
os.makedirs(OUT, exist_ok=True)

def rd(f):
    b = open(os.path.join(G, f), 'rb').read()
    try: t = b.decode('utf-8-sig')
    except UnicodeDecodeError: t = b.decode('cp1252')
    return list(csv.DictReader(io.StringIO(t), delimiter=';'))
def y0(s): return int(s[:4])
def pct(a, b): return round(100.0 * a / b, 1) if b else None

ATE = [  # nome nel MUR, id, nome breve, nome esteso
    ('Milano', 'statale', 'Statale', 'Università degli Studi di Milano (la Statale)'),
    ('Milano Politecnico', 'poli', 'Politecnico', 'Politecnico di Milano'),
    ('Milano Cattolica', 'cattolica', 'Cattolica', 'Università Cattolica del Sacro Cuore'),
    ('Milano Bicocca', 'bicocca', 'Bicocca', 'Università di Milano-Bicocca'),
    ('Milano Bocconi', 'bocconi', 'Bocconi', 'Università Bocconi'),
    ('Milano IULM', 'iulm', 'IULM', 'Libera Università di Lingue e Comunicazione IULM'),
    ('Milano San Raffaele', 'sanraf', 'San Raffaele', 'Università Vita-Salute San Raffaele'),
]
MUR2ID = {a[0]: a[1] for a in ATE}
ISEF = ('Milano ISEF', 'Milano ISEF Lombardia')   # scuole di scienze motorie, solo nei primi anni: contano nel totale di Milano
def is_mi(n): return n in MUR2ID or n in ISEF
def tel(n): return 'telematica' in n

# ---------- 1. serie per ateneo (MUR 02) ----------
m02 = rd('mur_02_iscritti_per_ateneo.csv')
anni = sorted({y0(r['AnnoA']) for r in m02 if y0(r['AnnoA']) <= 2024})
ser = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))   # id -> anno -> [F,M]
ita = collections.defaultdict(lambda: [0, 0]); ita_tel = collections.defaultdict(lambda: [0, 0])
city_tot = collections.defaultdict(lambda: collections.defaultdict(int))
SPEC = [("Ca' Foscari Venezia", 'Venezia'), ('Venezia Iuav', 'Venezia'), ('Chieti e Pescara', 'Chieti-Pescara'), ('Modena e Reggio Emilia', 'Modena-Reggio'),
        ('Piemonte Orientale', 'Piemonte Orientale'), ('Perugia Stranieri', 'Perugia'), ('Siena Stranieri', 'Siena'), ('Reggio Calabria', 'Reggio Calabria'),
        ('Castellanza', 'Varese'), ('Casamassima', 'Bari'), ('Rozzano', 'Rozzano'), ('Torrevecchia', 'Chieti-Pescara'), ('Bra ', 'Cuneo'), ('Novedrate', 'Como'),
        ('Benevento', 'Benevento'), ('Enna', 'Enna'), ('Marche', 'Ancona'), ('Calabria', 'Cosenza'), ('Basilicata', 'Potenza'), ('Molise', 'Campobasso'),
        ('Insubria', 'Varese'), ('Salento', 'Lecce'), ('Sannio', 'Benevento'), ('Tuscia', 'Viterbo'), ('Teramo', 'Teramo'), ('Foggia', 'Foggia'),
        ('Catanzaro', 'Catanzaro'), ('Milano', 'Milano')]
def citta_di(n):
    s = n.replace('–', '-')
    for k, v in SPEC:
        if s.startswith(k): return v
    return s.split()[0]
for r in m02:
    a = y0(r['AnnoA']); n = r['AteneoNOME']; v = int(r['Iscritti']); k = 0 if r['SESSO'] == 'F' else 1
    if a > 2024: continue
    if is_mi(n):
        ser[MUR2ID.get(n, 'isef')][a][k] += v
        ser['_milano'][a][k] += v
    if not tel(n):
        ita[a][k] += v
        city_tot[citta_di(n)][a] += v
    else:
        ita_tel[a][k] += v
def tot(x): return x[0] + x[1]

# ---------- 2. Italia (MUR 01) ----------
m01 = rd('mur_01_iscritti_per_anno.csv')
italia_tot = {y0(r['AnnoA']): int(r['Iscritti'].replace('.', '')) for r in m01}

# ---------- 3. internazionali (MUR 10): diploma di scuola superiore preso all'estero ----------
m10 = rd('mur_10_internazionali_per_ateneo.csv')
intl = collections.defaultdict(dict); intl_ita = collections.defaultdict(int)
for r in m10:
    a = y0(r['AnnoA']); n = r['AteneoNOME']
    if a > 2024: continue
    v = int(r['Iscritti_Internazionali'])
    if n in MUR2ID: intl[MUR2ID[n]][a] = v
    if is_mi(n): intl['_milano'][a] = intl['_milano'].get(a, 0) + v
    if not tel(n) and not is_mi(n): intl_ita[a] += v

# ---------- 4. provenienza (MUR 14a, corsi nella provincia di Milano = codice sede 215) ----------
REG = {'EMILIA ROMAGNA': 'Emilia-Romagna', "VALLE D'AOSTA": "Valle d'Aosta", 'FRIULI VENEZIA GIULIA': 'Friuli-Venezia Giulia',
       'Provincia autonoma di TRENTO': 'Trentino-Alto Adige', 'Provincia autonoma di BOLZANO': 'Trentino-Alto Adige'}
def regione(s):
    s = s.strip()
    if s in REG: return REG[s]
    if 'ESTERA' in s.upper(): return 'Estero'
    return s.capitalize() if s.upper() == s else s
m14 = rd('mur_14a_residenza_sede_gruppo.csv')
prov = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.Counter()))  # id -> anno -> classe
regioni_mi = collections.defaultdict(collections.Counter)    # anno -> regione -> n
for r in m14:
    a = y0(r['AnnoA']); n = r['AteneoNOME']
    if a > 2024 or r['SedeP'] != '215' or n not in MUR2ID: continue
    v = int(r['Iscritti']); reg = regione(r['ResidenzaR'])
    cl = 'mi' if r['ResidenzaP'] == 'Milano' else 'lomb' if reg == 'Lombardia' else 'estero' if reg == 'Estero' else 'altre'
    for key in (MUR2ID[n], '_milano'):
        prov[key][a][cl] += v
    regioni_mi[a][reg] += v
    if a == 2024: regioni_mi['ate_' + MUR2ID[n]][reg] += v

# ---------- 5. aree di studio (MUR 18) ----------
m18 = rd('mur_18_ateneo_e_gruppo.csv')
aree = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))   # (id|'_milano'|'_italia') -> area -> [F,M]  (2024/25)
aree10 = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))  # anni scelti, solo Milano
for r in m18:
    a = y0(r['AnnoA']); n = r['AteneoNOME']; gr = r['Nome Gruppo Disciplinare'].strip(); v = int(r['Isc']); k = 0 if r['SESSO'] == 'F' else 1
    if a == 2024:
        if n in MUR2ID: aree[MUR2ID[n]][gr][k] += v
        if is_mi(n): aree['_milano'][gr][k] += v
        elif not tel(n): aree['_italia'][gr][k] += v
    if a in (2000, 2010, 2024) and is_mi(n):
        aree10[a][gr][k] += v

# ---------- 6. corsi (Comune di Milano DS752, 2024/25) ----------
com = rd('comune_2024-25.csv')
import re
def pulisci(t):
    # nel file del Comune le lettere accentate e gli apostrofi sono rovinati (U+FFFD): davanti a una lettera era un apostrofo, altrimenti una «à»
    t = re.sub('�(?=[A-Za-z])', "'", t).replace('�', 'à')
    return re.sub(r'\s+', ' ', t).strip()
corsi = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0]))
nome_corso = {}
sede_mi = [0, 0]   # corsi con sede nel comune di Milano / altrove
for r in com:
    n = r['AteneoNOME']; v = int(r['Isc']); k = 0 if r['Sesso'] == 'F' else 1
    i = MUR2ID.get(n)
    if not i: continue
    nm = pulisci(r['CorsoNOME']); kk = nm.casefold()
    nome_corso.setdefault((i, kk), nm)
    corsi[i][kk][k] += v
    sede_mi[0 if r['SedeC'] == '15146' else 1] += v
cm_tot = {}
for y in ['2017-18', '2018-19', '2019-20', '2020-21', '2021-22', '2022-23', '2023-24', '2024-25']:
    cm_tot[int(y[:4])] = sum(int(r['Isc']) for r in rd('comune_%s.csv' % y))

# ---------- residenti ----------
eta = json.load(open(os.path.join(R, 'docs', 'eta', 'data', 'eta.json'), encoding='utf-8'))
res = dict(zip(eta['anni'], eta['citta']['r']))

# ---------- confezione ----------
def serie(d):
    return [[a, d[a][0], d[a][1]] for a in anni if a in d]
out = {'meta': {'anno_ultimo': 2024, 'anni': anni, 'anno_mancante': 2009, 'residenti_milano_2024': res[2024]}}
atenei = []
for nome, i, breve, esteso in ATE:
    s = ser[i]
    d = {'id': i, 'nome': breve, 'esteso': esteso, 'serie': serie(s)}
    d['isc'] = tot(s[2024]); d['donne_pct'] = pct(s[2024][0], tot(s[2024]))
    d['intl'] = [[a, intl[i][a]] for a in sorted(intl[i])]
    d['intl_pct'] = pct(intl[i][2024], tot(s[2024]))
    pv = prov[i]
    d['prov'] = [[a, pv[a]['mi'], pv[a]['lomb'], pv[a]['altre'], pv[a]['estero']] for a in sorted(pv)]
    d['aree'] = sorted([[g, v[0], v[1]] for g, v in aree[i].items()], key=lambda x: -(x[1] + x[2]))
    cs = sorted([[nome_corso[(i, c)], v[0] + v[1], v[0]] for c, v in corsi[i].items()], key=lambda x: -x[1])
    d['corsi'] = cs[:8]
    atenei.append(d)
out['atenei'] = atenei
mi_s = ser['_milano']
out['milano'] = {'serie': serie(mi_s), 'isc': tot(mi_s[2024]), 'donne_pct': pct(mi_s[2024][0], tot(mi_s[2024])),
                 'intl': [[a, intl['_milano'][a]] for a in sorted(intl['_milano'])],
                 'prov': [[a, prov['_milano'][a]['mi'], prov['_milano'][a]['lomb'], prov['_milano'][a]['altre'], prov['_milano'][a]['estero']] for a in sorted(prov['_milano'])],
                 'aree': sorted([[g, v[0], v[1]] for g, v in aree['_milano'].items()], key=lambda x: -(x[1] + x[2])),
                 'aree_anni': {str(a): sorted([[g, v[0], v[1]] for g, v in aree10[a].items()]) for a in aree10},
                 'regioni': sorted([[k, v] for k, v in regioni_mi[2024].items()], key=lambda x: -x[1]),
                 'regioni_2010': sorted([[k, v] for k, v in regioni_mi[2010].items()], key=lambda x: -x[1]),
                 'regioni_ate': {i: sorted([[k, v] for k, v in regioni_mi['ate_' + i].items()], key=lambda x: -x[1]) for _, i, _, _ in ATE},
                 'sede_milano_citta': sede_mi[0], 'sede_altrove': sede_mi[1]}
out['italia'] = {'serie_senza_telematiche': serie(ita), 'telematiche': serie(ita_tel),
                 'totale': [[a, italia_tot[a]] for a in sorted(italia_tot) if 1998 <= a <= 2024],
                 'aree': sorted([[g, v[0], v[1]] for g, v in aree['_italia'].items()], key=lambda x: -(x[1] + x[2])),
                 'intl_senza_milano': [[a, intl_ita[a]] for a in sorted(intl_ita)],
                 'senza_milano': [[a, tot(ita[a]) - tot(mi_s[a])] for a in anni]}
cit = []
for c, d in city_tot.items():
    if 2024 in d: cit.append({'citta': c, 'isc': d[2024], 'isc2010': d.get(2010), 'isc2000': d.get(2000)})
cit.sort(key=lambda x: -x['isc'])
out['citta'] = cit[:12]
out['controllo'] = {'comune_totali': cm_tot, 'mur_milano_totali': {a: tot(mi_s[a]) for a in range(2017, 2025)}}
json.dump(out, open(os.path.join(OUT, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(os.path.getsize(os.path.join(OUT, 'riepilogo.json')))

# ---------- csv per chi vuole scaricare ----------
def w(nome, head, rows):
    with open(os.path.join(OUT, nome), 'w', encoding='utf-8', newline='') as f:
        c = csv.writer(f, delimiter=';'); c.writerow(head); c.writerows(rows)
w('iscritti_per_ateneo.csv', ['anno_accademico', 'ateneo', 'donne', 'uomini', 'totale'],
  [['%d/%d' % (a, a + 1), d['nome'], f, m, f + m] for d in atenei for a, f, m in d['serie']])
w('iscritti_milano_italia.csv', ['anno_accademico', 'milano', 'italia_senza_telematiche', 'telematiche'],
  [['%d/%d' % (a, a + 1), tot(mi_s[a]), tot(ita[a]), tot(ita_tel[a])] for a in anni])
w('citta_2024.csv', ['citta', 'iscritti_2024_25', 'iscritti_2010_11', 'iscritti_2000_01'], [[c['citta'], c['isc'], c['isc2010'], c['isc2000']] for c in cit])
w('aree_di_studio_2024.csv', ['area', 'donne', 'uomini', 'totale', 'donne_pct'], [[g, f, m, f + m, pct(f, f + m)] for g, f, m in out['milano']['aree']])
w('provenienza_2024.csv', ['regione_di_residenza', 'iscritti_con_corso_a_milano'], out['milano']['regioni'])
w('internazionali.csv', ['anno_accademico', 'ateneo', 'iscritti_con_diploma_estero'], [['%d/%d' % (a, a + 1), d['nome'], v] for d in atenei for a, v in d['intl']])
w('corsi_2024.csv', ['ateneo', 'corso', 'iscritti', 'donne'], [[d['nome'], c, n, f] for d in atenei for c, n, f in d['corsi']])
print('ok')
