"""Elabora i dati e scrive i file della pagina «Il lavoro che c'è» in docs/occupazione/data/.
Uso: python -I -X utf8 occupazione/scripts/02_elabora.py
Legge occupazione/dati_grezzi/ (prodotto da 01_prepara.py). Ogni numero della pagina viene da qui."""
import csv, io, json, os, collections
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
G = os.path.join(R, 'occupazione', 'dati_grezzi')
OUT = os.path.join(R, 'docs', 'occupazione', 'data')
os.makedirs(OUT, exist_ok=True)

def txt(f): return open(os.path.join(G, f), 'rb').read().decode('utf-8-sig')
def rd(f, delim=','): return list(csv.reader(io.StringIO(txt(f)), delimiter=delim))
def dr(f): return csv.DictReader(io.StringIO(txt(f)))
def num(s): return float(s.replace(',', '.')) if s.strip() != '' else None
def wcsv(name, head, rows):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='') as o:
        w = csv.writer(o, delimiter=';', lineterminator='\n')
        w.writerow(head)
        for r in rows: w.writerow(['' if v is None else v for v in r])

ANNI = list(range(2004, 2025))
SEX = {'maschi': 'm', 'femmine': 'f', 'totale': 't'}

# ---- 1. tassi per territorio, 15-64 anni (Comune di Milano, ds114) ----
rows = rd('comune_ds114_confronti_territoriali.csv', ';')
h = rows[0]
assert h[3] == '2004' and h[-1] == '2024'
TER = {'Comune di Milano': 'Milano', 'Provincia di Milano': 'Provincia', 'Lombardia': 'Lombardia', 'Nord-Ovest': 'Nord-Ovest', 'Italia': 'Italia'}
tassi = {}
csv_tassi = []
for r in rows[1:]:
    ind = r[0].strip()
    ter = TER[r[1].strip()]
    sx = SEX[r[2].strip()]
    k = {'Tasso di occupazione': 'occ', 'Tasso di disoccupazione': 'dis', 'Tasso di attivita': 'att'}[ind]
    v = [num(x) for x in r[3:]]
    assert len(v) == 21
    tassi.setdefault(ter, {}).setdefault(k, {})[sx] = v
    for a, x in zip(ANNI, v):
        csv_tassi.append((a, ter, r[2].strip(), ind, x))
# Difetto del file ds114: la colonna 2019 è una copia della colonna 2021 (per tutti i territori).
# Per Milano si usa il file ds112 (stessi indicatori, 15-64 anni); per la Lombardia il totale dell'occupazione dalla serie storica ds1497;
# per provincia, Nord-Ovest e Italia il 2019 resta vuoto.
Y19 = 2019 - 2004
d112 = {}
for r in rd('comune_ds112_indicatori_15_64.csv', ';')[1:]:
    k = {'Tasso di occupazione': 'occ', 'Tasso di disoccupazione': 'dis', 'Tasso di attivita': 'att'}[r[1].strip()]
    d112[(int(r[0]), k, SEX[r[2].strip()])] = num(r[3])
for k in ('occ', 'dis', 'att'):
    for sx in 'tmf':
        for a in ANNI:
            if a != 2019 and abs(tassi['Milano'][k][sx][a - 2004] - d112[(a, k, sx)]) > 0.05:
                print('ATTENZIONE: ds114 e ds112 differiscono', a, k, sx)
        tassi['Milano'][k][sx][Y19] = d112[(2019, k, sx)]
def serie(f):
    return {int(r[0]): (num(r[2]) if r[2] else None) for r in rd(f, ';')[1:]}
# (la serie ds1498 della disoccupazione lombarda differisce da ds114 in quasi tutti gli anni: non si mescola, il 2019 resta vuoto)
for k, f in (('occ', 'comune_ds1497_occupazione_serie.csv'),):
    sr = serie(f)
    for a in ANNI:
        if a != 2019 and abs(tassi['Lombardia'][k]['t'][a - 2004] - sr[a]) > 0.05:
            print('ATTENZIONE: ds114 e serie storica differiscono (Lombardia)', a, k)
    tassi['Lombardia'][k]['t'][Y19] = sr[2019]
for k in ('occ', 'dis', 'att'):
    for sx in 'tmf':
        for t in ('Provincia', 'Nord-Ovest', 'Italia'):
            tassi[t][k][sx][Y19] = None
        if not (k == 'occ' and sx == 't'):
            tassi['Lombardia'][k][sx][Y19] = None
csv_tassi = [(a, ter, g, ind, tassi[ter][k][sx][a - 2004]) for ter in tassi for k, ind in (('occ', 'Tasso di occupazione'), ('dis', 'Tasso di disoccupazione'), ('att', 'Tasso di attivita')) for sx, g in (('m', 'maschi'), ('f', 'femmine'), ('t', 'totale')) for a in ANNI]
wcsv('tassi_territori.csv', ['anno', 'territorio', 'genere', 'indicatore', 'valore_percento'], csv_tassi)

# ---- 2. occupati e persone in cerca di lavoro, 15 anni e oltre (ds109) ----
rows = rd('comune_ds109_condizione_lavorativa_15piu.csv', ';')[1:]
occ = collections.defaultdict(dict)
for a, c, g, v in rows:
    c = c.strip()
    g = g.strip()
    cl = c.lower()
    k = 'occ' if cl.startswith('occupati') else 'cerca' if cl.startswith('in cerca') else 'pop' if cl.startswith('popolazione') else 'inatt' if cl.startswith('inattivi') else 'fl'
    occ[k][(int(a), SEX[g])] = int(v)
occupati = {k: {s: [occ[k][(a, s)] for a in ANNI] for s in 'tmf'} for k in ('occ', 'cerca', 'pop')}
for a in ANNI:  # controllo: maschi + femmine = totale (tolleranza 2 per gli arrotondamenti)
    for k in ('occ', 'cerca'):
        d = occ[k][(a, 'm')] + occ[k][(a, 'f')] - occ[k][(a, 't')]
        if abs(d) > 2:
            print('ATTENZIONE: nel file del Comune maschi + femmine non fanno il totale:', a, k, d)
wcsv('occupati_milano.csv', ['anno', 'occupati_totale', 'occupati_maschi', 'occupati_femmine', 'in_cerca_totale', 'in_cerca_maschi', 'in_cerca_femmine', 'popolazione_15_piu'],
     [(a, occ['occ'][(a, 't')], occ['occ'][(a, 'm')], occ['occ'][(a, 'f')], occ['cerca'][(a, 't')], occ['cerca'][(a, 'm')], occ['cerca'][(a, 'f')], occ['pop'][(a, 't')]) for a in ANNI])

# ---- 3. giovani 15-24 (ds113) ----
rows = rd('comune_ds113_giovani_15_24.csv', ';')
assert rows[0][2] == '2004'
giov = {}
for r in rows[1:]:
    ind = r[0].strip()
    sx = SEX[r[1].strip()]
    k = 'att' if 'attivita' in ind else 'occ' if 'occupazione giovanile' in ind and 'disoccupazione' not in ind else 'dis'
    giov.setdefault(k, {})[sx] = [num(x) for x in r[2:]]
wcsv('giovani_15_24.csv', ['anno', 'occupazione_totale', 'occupazione_maschi', 'occupazione_femmine', 'disoccupazione_totale', 'attivita_totale'],
     [(a, giov['occ']['t'][i], giov['occ']['m'][i], giov['occ']['f'][i], giov['dis']['t'][i], giov['att']['t'][i]) for i, a in enumerate(ANNI)])

# ---- 4. contratti per tipo e durata, provincia di Milano (Comunicazioni obbligatorie, p9wf) ----
DUR = [('Minore di 1 mese', 'meno di 1 mese'), ('Tra 1 e 3 mesi', '1-3 mesi'), ('Tra 4 e 6 mesi', '4-6 mesi'), ('Tra 7 e 12 mesi', '7-12 mesi'), ('Maggiore di 12 mesi', 'oltre 12 mesi')]
DI = {a: i for i, (a, b) in enumerate(DUR)}
TIPI = ['Tempo determinato', 'Tempo indeterminato', 'Apprendistato', 'Tirocinio', 'Altro']
CA = list(range(2013, 2026))
cd = collections.defaultdict(lambda: [0] * 5)
for r in dr('lombardia_p9wf_durata_per_tipo.csv'):
    if r['COD_PROVINCIA'] != '015':
        continue
    p = int(r['PERIODO'])
    if p < 2013 or p > 2025:
        continue
    cd[(p, r['TIPO_CONTRATTO'])][DI[r['DURATA_GIORNI_TODAY_FASCIA']]] += int(r['CNT_DURATA_FASCIA'])
contratti = {'anni': CA, 'tipi': TIPI, 'durate': [b for a, b in DUR], 'dati': {t: {str(p): cd[(p, t)] for p in CA} for t in TIPI}}
wcsv('contratti_tipo_durata.csv', ['anno_inizio', 'tipo_contratto', 'durata', 'contratti'],
     [(p, t, DUR[i][1], cd[(p, t)][i]) for p in CA for t in TIPI for i in range(5)])
assert sum(cd[(2024, 'Tempo determinato')]) == 712891 and cd[(2024, 'Tempo determinato')][0] == 412615

# ---- 5. giovani e contratti (Comunicazioni obbligatorie, x54h): fasce 15-34 e 35 e oltre ----
gc = collections.defaultdict(lambda: [0] * 5)
for r in dr('lombardia_x54h_durata_eta_sesso.csv'):
    if r['PROVINCIA'] != '015':
        continue
    p = int(r['PERIODO'])
    if p not in (2013, 2024):
        continue
    gc[(p, r['FASCIA_ETA'], r['TIPO_CONTRATTO'])][DI[r['DURATA_GIORNI_TODAY_FASCIA']]] += int(r['N_CONTRATTI'])
giov_contr = {str(p): {f: {t: gc[(p, f, t)] for t in TIPI} for f in ('15-34', '35-')} for p in (2013, 2024)}
wcsv('contratti_giovani.csv', ['anno_inizio', 'eta', 'tipo_contratto', 'durata', 'contratti'],
     [(p, 'da 15 a 34 anni' if f == '15-34' else '35 anni e oltre', t, DUR[i][1], gc[(p, f, t)][i]) for p in (2013, 2024) for f in ('15-34', '35-') for t in TIPI for i in range(5)])

# ---- 6. lavoro da casa (ISTAT, occupati 15+, 2023 e 2024) ----
CITTA = [('015146', 'Milano'), ('058091', 'Roma'), ('001272', 'Torino'), ('063049', 'Napoli'), ('037006', 'Bologna'), ('010025', 'Genova'), ('048017', 'Firenze'), ('082053', 'Palermo'), ('IT', 'Italia')]
CN = dict(CITTA)
cs = collections.defaultdict(dict)
for r in dr('istat_lavoro_da_casa.csv'):
    if r['REF_AREA'] in CN:
        cs[(r['REF_AREA'], r['GENDER'], r['TIME_PERIOD'])][r['WORK_HOME']] = float(r['OBS_VALUE'])
casa = {'citta': []}
csv_casa = []
for cod, nome in CITTA:
    e = {'nome': nome}
    for y in ('2023', '2024'):
        for g in 'TMF':
            d = cs[(cod, g, y)]
            e[y + g] = {'tot': round(d['TOTAL']), 'mai': round(d['NEV']), 'meno': round(d['LESSHDAY']), 'meta': round(d['ATLHDAY'])}
            csv_casa.append((y, nome, {'T': 'totale', 'M': 'maschi', 'F': 'femmine'}[g], round(d['TOTAL']), round(d['NEV']), round(d['LESSHDAY']), round(d['ATLHDAY'])))
    casa['citta'].append(e)
wcsv('lavoro_da_casa.csv', ['anno', 'citta', 'genere', 'occupati', 'mai', 'meno_della_meta_del_tempo', 'meta_del_tempo_o_piu'], csv_casa)

# ---- 7. posizioni di lavoro per settore, provincia di Milano (ISTAT conti nazionali, edizione dicembre 2025) ----
SET = [('F', 'Costruzioni'), ('J', 'Informatica e comunicazione'), ('M_N', 'Professioni e servizi alle imprese'), ('GTI', 'Commercio, trasporti, alberghi, ristoranti'),
       ('OTQ', 'Pubblica amministrazione, scuola, sanità'), ('K', 'Banche e assicurazioni'), ('L', 'Immobiliare'), ('BTE', 'Industria'), ('A', 'Agricoltura'), ('RTU', 'Arte, sport, altri servizi')]
sv = collections.defaultdict(dict)
for r in dr('istat_settori_milano_italia.csv'):
    if r['DATA_TYPE_AGGR'] == 'JB' and r['REF_AREA'] == 'ITC45':
        sv[r['BRKDW_INDUSTRY_NACE_REV2']][int(r['TIME_PERIOD'])] = float(r['OBS_VALUE'])
SA = list(range(2018, 2024))
settori = {'anni': SA, 'totale': [sv['_T'][a] for a in SA], 'voci': [{'cod': c, 'nome': n, 'v': [sv[c][a] for a in SA]} for c, n in SET]}
for a in SA:
    assert abs(sum(sv[c][a] for c, n in SET) - sv['_T'][a]) < 0.35, a   # i 10 gruppi sommano al totale
wcsv('settori_posizioni_lavoro.csv', ['anno', 'settore', 'posizioni_di_lavoro_migliaia'], [(a, n, sv[c][a]) for c, n in SET for a in SA] + [(a, 'Totale', sv['_T'][a]) for a in SA])

# ---- riepilogo ----
J = {'anni': ANNI, 'tassi': tassi, 'occupati': occupati, 'giovani': giov, 'contratti': contratti, 'giovani_contratti': giov_contr, 'casa': casa, 'settori': settori}
json.dump(J, open(os.path.join(OUT, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
for f in sorted(os.listdir(OUT)):
    print(f, os.path.getsize(os.path.join(OUT, f)))
# controlli sui numeri citati
m = tassi['Milano']['occ']
print('divario', round(m['m'][0] - m['f'][0], 1), round(m['m'][-1] - m['f'][-1], 1), '| Milano/Italia 2024', m['t'][-1], tassi['Italia']['occ']['t'][-1])
print('occupati', occupati['occ']['t'][0], occupati['occ']['t'][-1], round(100 * (occupati['occ']['t'][-1] / occupati['occ']['t'][0] - 1), 1))
c0 = casa['citta'][0]['2024T']
print('casa Milano 2024', c0, round(100 * (c0['meno'] + c0['meta']) / c0['tot'], 1))
print('giovani', giov['dis']['t'][-1], max(giov['dis']['t']), giov['occ']['t'][-1])
