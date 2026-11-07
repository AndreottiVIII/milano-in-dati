"""Paniere di prezzi di Milano 2005-2026, in euro di quell'anno e in euro di oggi, per la pagina 'Quanto costa vivere' (versione 2).
Uso: python -I -X utf8 build_paniere_v2.py <costo-vita assoluto> <prezzi-case assoluto> <cartella data di destinazione>
Scrive nella cartella di destinazione SOLO file nuovi: paniere_v2.json e prezzi_2005_oggi.csv.

Metodo (stesso principio per tutti gli oggetti):
 - "euro di quell'anno" = prezzo pagato in quell'anno. Dove c'e' un prezzo vero (Osservatorio MIMIT dal 2021, archivio carburanti dal 2015,
   tariffe ATM, quotazioni OMI degli affitti dal 2006) si usa quello. Prima, il prezzo e' STIMATO riportando indietro il primo prezzo vero
   con l'indice ISTAT di Milano della voce (rapporto tra le medie annue).
 - "euro di oggi" = euro di quell'anno x (indice generale di Milano a settembre 2026 / indice generale di Milano di quell'anno).
 - 2026 = settembre 2026 (ultimo mese disponibile) per prezzi e indice generale.
 - luce: non ci sono euro; si usa "100 euro di luce nel 2005" e l'indice dell'elettricita' ISTAT di Milano.
Fonti: indici NIC Milano (Comune di Milano / ISTAT, CC BY), Osservatorio prezzi MIMIT, carburanti MIMIT (IODL 2.0), ATM, OMI (CC BY 4.0)."""
import sys, os, csv, json, datetime, collections
C, P, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
YEARS = list(range(2005, 2027))

def rd(p, delim=';'):
    return list(csv.DictReader(open(p, encoding='utf-8'), delimiter=delim))

# ---------- indici
voci = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rd(os.path.join(C, 'pulito', 'nic_milano_voci_base2015.csv')):
    voci[r['voce']][r['periodo']].append(float(r['indice_base2015_100']))
def vm(voce):  # periodo -> indice (uno per mese)
    return {k: sum(v) / len(v) for k, v in voci[voce].items()}
def annuale(voce):
    m = vm(voce); out = {}
    for y in range(2005, 2026):
        xs = [v for k, v in m.items() if k.startswith(str(y))]
        if len(xs) >= 11: out[y] = sum(xs) / len(xs)
    sep = m.get('2026-09')
    if sep is not None: out[2026] = sep
    return out
div = collections.defaultdict(list)
for r in rd(os.path.join(C, 'pulito', 'nic_milano_divisioni_base2015.csv')):
    if r['divisione'] in ('0', '00'): div[r['periodo']].append(float(r['indice_base2015_100']))
gm = {k: sum(v) / len(v) for k, v in div.items()}
g25 = sum(gm['2025-%02d' % m] for m in range(1, 13)) / 12
g_sep26 = gm['2026-09']
# indice generale annuo 2005=100 (file gia' pubblicato nella pagina attuale, 2005-2010 ricostruito dai tassi annui)
gen = {int(r['anno']): float(r['generale_milano']) for r in rd(os.path.join(C, '..', 'docs', 'costo-vita', 'data', 'indici_annui_2005_100.csv'))}
gen[2026] = gen[2025] * g_sep26 / g25
I_oggi = gen[2026]
def a_oggi(v, y): return v * I_oggi / gen[y]

# ---------- indici delle voci per le stime
A = {k: annuale(k) for k in ('bar', 'ristoranti', 'pane', 'affitti', 'elettricita', 'benzina')}
# caffe' al bar: 'bar' fino al 2015, poi 'ristoranti' (dal 2016 il bar e' dentro la voce unica; la rottura e' raccordata sulla media 2015)
caf_idx = {y: A['bar'][y] for y in range(2005, 2016)}
for y in range(2016, 2027): caf_idx[y] = caf_idx[2015] * A['ristoranti'][y] / A['ristoranti'][2015]

# ---------- prezzi veri MIMIT
mim = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rd(os.path.join(C, 'pulito', 'prezzi_medi_milano_mimit.csv')):
    mim[r['prodotto']][(int(r['anno']), int(r['mese']))].append(float(r['prezzo_medio_eur']))
def mimit_annuo(nome, extra=None, da=2021):
    out = {}
    for y in range(da, 2026):
        xs = [sum(v) / len(v) for k, v in mim[nome].items() if k[0] == y]
        out[y] = sum(xs) / len(xs)
    nm = extra or nome
    v = mim[nm][(2026, 9)]; out[2026] = sum(v) / len(v)
    return out

def indietro(ancora_anno, vero, idx, fine=2005):
    """Dal primo prezzo vero (anno ancora) si va indietro con l'indice; ritorna anno -> (prezzo, 'stimato'|'misurato')."""
    out = {y: (p, 'misurato') for y, p in vero.items()}
    for y in range(fine, ancora_anno):
        out[y] = (vero[ancora_anno] * idx[y] / idx[ancora_anno], 'stimato')
    return out

items = {}
# caffe'
items['caffe'] = indietro(2021, mimit_annuo('Caffè Espresso Al Bar'), caf_idx)
# pizzeria
items['pizza'] = indietro(2021, mimit_annuo('Pasto In Pizzeria'), A['ristoranti'])
# pane (1 kg): 'Pane Fresco' c'e' solo nel 2021, 'Pane Fresco Con Farina Di Grano' dal 2022: si usa il secondo (prezzo vero dal 2022)
items['pane'] = indietro(2022, mimit_annuo('Pane Fresco Con Farina Di Grano', None, 2022), A['pane'])
# benzina: pieno da 40 litri, self, prezzo vero dal 2015
carb = collections.defaultdict(list)
for r in rd(os.path.join(C, 'pulito', 'carburanti_milano_mensile.csv')):
    if r['carburante'] == 'Benzina' and r['self_service'] == 'si':
        carb[r['mese']].append(float(r['prezzo_mediano_eur_litro_media_mensile']))
bz = {}
for y in range(2015, 2026):
    xs = [carb['%d-%02d' % (y, m)][0] for m in range(1, 13) if '%d-%02d' % (y, m) in carb]
    bz[y] = sum(xs) / len(xs)
bz[2026] = carb['2026-09'][0]
picco22 = max(carb['2022-%02d' % m][0] for m in range(1, 13))
items['benzina'] = {y: (p * 40, t) for y, (p, t) in indietro(2015, bz, A['benzina']).items()}
# biglietto ATM: media dell'anno pesata sui giorni, gradini da biglietto_atm.csv
gr = [(datetime.date(2002, 1, 1), 1.0), (datetime.date(2011, 9, 1), 1.5), (datetime.date(2019, 7, 15), 2.0), (datetime.date(2023, 1, 9), 2.2)]
def prezzo_il(d):
    p = gr[0][1]
    for dd, pp in gr:
        if d >= dd: p = pp
    return p
bt = {}
for y in range(2005, 2026):
    d0, d1 = datetime.date(y, 1, 1), datetime.date(y + 1, 1, 1)
    n = (d1 - d0).days
    bt[y] = sum(prezzo_il(d0 + datetime.timedelta(i)) for i in range(n)) / n
bt[2026] = 2.2
items['biglietto'] = {y: (p, 'misurato') for y, p in bt.items()}
# luce: 100 euro di luce nel 2005 (indice)
el = A['elettricita']
items['luce'] = {y: (100 * el[y] / el[2005], 'indice') for y in YEARS}
# affitto 60 m2, OMI, abitazioni civili, mediana delle zone, media dei semestri
om = collections.defaultdict(list)
for r in rd(os.path.join(P, 'pulito', 'prezzi_citta_mediana_zone.csv'), ','):
    if r['categoria'] == 'residenziale' and r['tipologia'] == 'Abitazioni civili':
        om[int(r['anno'])].append(float(r['loc_mediana_zone']))
items['affitto'] = {y: (60 * sum(v) / len(v), 'misurato') for y, v in sorted(om.items())}

META = [
    ('caffe',     'Un caffè al bar',          'un espresso',                     'M1', 2),
    ('pane',      'Il pane',                  '1 chilo di pane fresco',          'M3', 2),
    ('pizza',     'Una pizza fuori',          'un pasto in pizzeria',            'M2', 2),
    ('biglietto', 'Il biglietto del tram',    'biglietto ordinario ATM',         'M4', 2),
    ('benzina',   'Un pieno di benzina',      '40 litri, self',                  'M5', 2),
    ('luce',      'La luce di casa',          '100 € di bolletta del 2005',      'AR', 0),
    ('affitto',   'Un affitto',               '60 m², un mese, zona mediana',    'MG', 0),
]
res = []
for k, nome, unita, col, dec in META:
    ser = []
    for y in YEARS:
        if y not in items[k]: continue
        p, t = items[k][y]
        ser.append({'anno': y, 'euro_allora': round(p, 3), 'euro_oggi': round(a_oggi(p, y), 3), 'tipo': t})
    res.append({'id': k, 'nome': nome, 'unita': unita, 'colore': col, 'decimali': dec, 'serie': ser})

# dumbbell: variazione 2005 -> 2025 delle voci ISTAT di Milano (dal riepilogo della raccolta)
rie = rd(os.path.join(C, 'pulito', 'riepilogo_indici_voci.csv'))
SCELTE = ['elettricita', 'gas', 'alberghi', 'acqua', 'treno', 'sigarette', 'uova', 'taxi', 'pane', 'ristoranti', 'benzina', 'cinema_teatri',
          'affitti', 'bus_tram_metro', 'assic_auto', 'rifiuti', 'medicinali', 'telefonia_mobile']
NOMI = {'elettricita': 'Luce', 'gas': 'Gas', 'alberghi': 'Alberghi', 'acqua': 'Acqua', 'treno': 'Treno', 'sigarette': 'Sigarette', 'uova': 'Uova',
        'taxi': 'Taxi', 'pane': 'Pane', 'ristoranti': 'Ristoranti e pizzerie', 'benzina': 'Benzina', 'cinema_teatri': 'Cinema e teatri',
        'affitti': 'Affitti (contratti in corso)', 'bus_tram_metro': 'Trasporto urbano (indice)', 'assic_auto': 'Assicurazione auto',
        'rifiuti': 'Tassa rifiuti', 'medicinali': 'Medicinali', 'telefonia_mobile': 'Telefono'}
dum = []
for r in rie:
    if r['tipo'] == 'voce Milano' and r['chiave'] in SCELTE and r['var_pct_2005_2025']:
        dum.append({'id': r['chiave'], 'nome': NOMI[r['chiave']], 'var_pct': float(r['var_pct_2005_2025'])})
dum.sort(key=lambda x: -x['var_pct'])

# affitto e lavoro (file gia' pubblicato)
av = rd(os.path.join(C, '..', 'docs', 'costo-vita', 'data', 'affitto_vs_reddito.csv'))
ore = [{'anno': int(r['anno']), 'ore': float(r['ore_di_lavoro_per_un_affitto']), 'quota': float(r['quota_affitto_su_reddito_pct']),
        'affitto': float(r['affitto_60m2_mese_eur_stima_OMI']), 'reddito': float(r['reddito_mensile_mediano_interpolato_eur'])} for r in av]

out = {
    'generato_da': 'costo-vita/scripts/build_paniere_v2.py', 'oggi': 'settembre 2026',
    'indice_generale_2005_100': {str(y): round(v, 2) for y, v in gen.items()},
    'cento_euro_2005_oggi': round(100 * I_oggi / gen[2005], 1),
    'inflazione_2005_oggi_pct': round((I_oggi / gen[2005] - 1) * 100, 1),
    'inflazione_2021_oggi_pct': round((I_oggi / gen[2021] - 1) * 100, 1),
    'inflazione_2005_2025_pct': round((gen[2025] / gen[2005] - 1) * 100, 1),
    'benzina_picco_2022_litro': round(picco22, 3), 'benzina_set2026_litro': round(bz[2026], 3),
    'oggetti': res, 'voci_2005_2025': dum, 'affitto_lavoro': ore,
}
os.makedirs(OUT, exist_ok=True)
json.dump(out, open(os.path.join(OUT, 'paniere_v2.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
with open(os.path.join(OUT, 'prezzi_2005_oggi.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['oggetto', 'unita', 'anno', 'euro_di_quell_anno', 'euro_di_oggi_set2026', 'tipo_dato'])
    for o in res:
        for s in o['serie']: w.writerow([o['nome'], o['unita'], s['anno'], s['euro_allora'], s['euro_oggi'], s['tipo']])
print('oggi=I', round(I_oggi, 2), '100 euro 2005 ->', out['cento_euro_2005_oggi'], 'infl 2005-oggi', out['inflazione_2005_oggi_pct'], '2021-oggi', out['inflazione_2021_oggi_pct'])
for o in res:
    s = o['serie']; print(o['id'], s[0], s[-1])
print([d['nome'] + ' ' + str(d['var_pct']) for d in dum])
print('picco22', picco22, bz[2026])
