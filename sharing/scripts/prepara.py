"""Pulisce la serie ds574 (sharing a Milano) e scrive i dati piccoli della pagina.
Uso: python -I -X utf8 sharing/scripts/prepara.py
Legge sharing/raw/ds574.csv (scaricato dal portale del Comune) e, per gli incidenti con monopattini,
docs/bici-auto-mezzi/data/incidenti.json (stessa fonte ISTAT già usata da quella pagina).
Scrive docs/sharing/data/*.csv e riepilogo.json. Ogni scelta è spiegata in sharing/NOTE.md."""
import csv, json, os, collections

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(R, 'sharing', 'raw', 'ds574.csv')
OUT = os.path.join(R, 'docs', 'sharing', 'data')
os.makedirs(OUT, exist_ok=True)

# ---- lettura: (servizio, tipologia in minuscolo, indicatore in minuscolo) -> {anno: valore}
v = collections.defaultdict(dict)
note = collections.defaultdict(list)
for x in csv.DictReader(open(RAW, encoding='utf-8'), delimiter=';'):
    k = (x['sharing_veicoli'].strip().lower(), x['sharing_veicoli_tipologia'].strip().lower(),
         x['sharing_veicoli_indicatori'].strip().lower())
    a = int(x['anno'])
    val = float(x['sharing_veicoli_valore'])
    if a in v[k] and v[k][a] != val:
        raise SystemExit('valori diversi per la stessa riga: %s %s' % (k, a))
    v[k][a] = val
    if x['note'].strip():
        note[(k, a)].append(x['note'].strip())

def g(servizio, tip, ind):
    return v.get((servizio, tip, ind), {})

# righe scritte in due modi (maiuscole diverse) o con due nomi: unite
scooter_tot = dict(g('scooter sharing', 'free floating', 'scooter totale'))  # 2017-2025 (e 2015-16 con altro nome)
for a, x in g('scooter sharing', 'free floating', 'scooter elettrici').items():
    pass
# veicoli scooter: 2015-2016 riga "scooter totale" (150), dal 2017 riga "Scooter totale" (stessa dicitura): già unite dal minuscolo

ANNI = list(range(2011, 2026))

bici_sb = g('bike sharing', 'station based', 'noleggi medi giornalieri totale')
bici_ff = g('bike sharing', 'free floating', 'noleggi medi giornalieri totale')
auto_ff = g('car sharing', 'free floating', 'noleggi medi giornalieri totale')
auto_sb = g('car sharing', 'station based', 'noleggi medi giornalieri totale')   # solo 2018-2023, da 108 a 11
scoot = g('scooter sharing', 'free floating', 'noleggi medi giornalieri totale')
monop = g('monopattini', 'free floating', 'noleggi medi giornalieri totale')

def riga(a):
    return {
        'anno': a,
        'bici_stazione': bici_sb.get(a),
        'bici_libere': bici_ff.get(a),
        'monopattini': monop.get(a),
        'scooter': scoot.get(a),
        'auto_libere': auto_ff.get(a),
    }

serie = [riga(a) for a in ANNI]
with open(os.path.join(OUT, 'noleggi_giorno.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['anno', 'bici_a_stazione', 'bici_senza_stazione', 'monopattini', 'scooter', 'auto_senza_stazione', 'totale'])
    for r in serie:
        tot = sum(r[k] for k in ('bici_stazione', 'bici_libere', 'monopattini', 'scooter', 'auto_libere') if r[k] is not None)
        r['totale'] = tot
        w.writerow([r['anno']] + [('' if r[k] is None else int(r[k])) for k in ('bici_stazione', 'bici_libere', 'monopattini', 'scooter', 'auto_libere')] + [int(tot)])

# ---- mezzi in strada
bici_veic_sb = g('bike sharing', 'station based', 'biciclette totale')
bici_veic_ff = g('bike sharing', 'free floating', 'biciclette totale')
mon_veic = g('monopattini', 'free floating', 'monopattini totale')
sc_veic = g('scooter sharing', 'free floating', 'scooter totale')   # 2015-16 e 2017-25
auto_veic_ff = g('car sharing', 'free floating', 'autovetture totale')

def veic(a, k):
    if k == 'bici':
        return (bici_veic_sb.get(a, 0) + bici_veic_ff.get(a, 0)) or None
    return {'monopattini': mon_veic, 'scooter': sc_veic, 'auto_libere': auto_veic_ff}[k].get(a)

# ---- chilometri
km_bici = g('bike sharing', 'free floating+station based', 'percorrenze annue')
km_mon = dict(g('monopattini', 'free floating', 'percorrenze annue'))
km_sc = g('scooter sharing', 'free floating', 'percorrenze annue')
km_auto = dict(g('car sharing', 'free floating', 'percorrenze annue'))
km_auto.update(g('car sharing', 'free floating+station based', 'percorrenze annue'))  # 2018-23 anche a stazione

# ---- 2020 -> 2025: mezzi e noleggi (auto: solo libere, per avere lo stesso perimetro nei due anni)
traccia = {}
for k, nome, ser in [('bici', 'Bici (con e senza stazione)', None), ('monopattini', 'Monopattini', monop),
                     ('scooter', 'Scooter', scoot), ('auto_libere', 'Auto senza stazione', auto_ff)]:
    pts = []
    for a in range(2020, 2026):
        if k == 'bici':
            n = (bici_sb.get(a) or 0) + (bici_ff.get(a) or 0)
        else:
            n = ser.get(a)
        pts.append({'anno': a, 'mezzi': veic(a, k), 'noleggi': n})
    traccia[k] = {'nome': nome, 'punti': pts}

# ---- 2025: noleggi per mezzo e km per mezzo
a = 2025
mezzi25 = {}
for k, nome, nol, km in [
        ('bici', 'Bici', (bici_sb[a] + bici_ff[a]), km_bici[a]),
        ('monopattini', 'Monopattini', monop[a], km_mon[a]),
        ('scooter', 'Scooter', scoot[a], km_sc[a]),
        ('auto_libere', 'Auto senza stazione', auto_ff[a], km_auto[a])]:
    n = veic(a, k)
    mezzi25[k] = {'nome': nome, 'mezzi': n, 'noleggi_giorno': nol, 'km_anno': km,
                  'noleggi_per_mezzo_giorno': round(nol / n, 2), 'km_per_mezzo_anno': round(km / n),
                  'km_per_noleggio': round(km / (nol * 365), 1)}
with open(os.path.join(OUT, 'mezzi_2025.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['mezzo', 'mezzi_in_strada', 'noleggi_medi_al_giorno', 'chilometri_anno', 'noleggi_per_mezzo_al_giorno', 'chilometri_per_mezzo_anno', 'chilometri_per_noleggio'])
    for k, m in mezzi25.items():
        w.writerow([m['nome'], int(m['mezzi']), int(m['noleggi_giorno']), int(m['km_anno']), str(m['noleggi_per_mezzo_giorno']).replace('.', ','), m['km_per_mezzo_anno'], str(m['km_per_noleggio']).replace('.', ',')])

# ---- incidenti con monopattini (ISTAT, già elaborati per la pagina Bici, auto e mezzi)
inc = json.load(open(os.path.join(R, 'docs', 'bici-auto-mezzi', 'data', 'incidenti.json'), encoding='utf-8'))['serie']
incid = []
for i, an in enumerate(inc['anno']):
    if an >= 2020:
        gg = 366 if an % 4 == 0 else 365
        noleggi_anno = monop[an] * gg
        incid.append({'anno': an, 'incidenti': inc['monop'][i], 'feriti': inc['monop_feriti'][i], 'morti': inc['monop_morti'][i],
                      'noleggi_anno_stima': round(noleggi_anno),
                      'incidenti_per_milione_noleggi': round(inc['monop'][i] / noleggi_anno * 1e6, 1),
                      'incidenti_totali': inc['tutti'][i], 'quota_pct': round(100 * inc['monop'][i] / inc['tutti'][i], 1)})
with open(os.path.join(OUT, 'incidenti_monopattini.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['anno', 'incidenti_con_feriti', 'feriti', 'morti', 'noleggi_sharing_stimati', 'incidenti_ogni_milione_di_noleggi', 'incidenti_in_tutto', 'quota_sul_totale_pct'])
    for r in incid:
        w.writerow([r['anno'], r['incidenti'], r['feriti'], r['morti'], r['noleggi_anno_stima'], str(r['incidenti_per_milione_noleggi']).replace('.', ','), r['incidenti_totali'], str(r['quota_pct']).replace('.', ',')])

# ---- controllo con ds179 (incidenti in tutto per anno, per capire se gli ISTAT tornano)
tot179 = collections.Counter()
p = os.path.join(R, 'sharing', 'raw', 'ds179.csv')
if os.path.exists(p):
    for x in csv.DictReader(open(p, encoding='utf-8'), delimiter=';'):
        tot179[int(x['Anno'])] += sum(int(x[c] or 0) for c in x if c.startswith('incidenti'))
ctrl179 = {a: tot179[a] for a in range(2020, 2025)}

# ---- classifica per anno (2017-2025, quando esistono tutti i servizi)
classifica = []
for r in serie:
    if r['anno'] >= 2017:
        c = [(k, r[k]) for k in ('bici_stazione', 'bici_libere', 'monopattini', 'scooter', 'auto_libere') if r[k] is not None]
        c.sort(key=lambda t: -t[1])
        classifica.append({'anno': r['anno'], 'ordine': [t[0] for t in c], 'valori': {t[0]: t[1] for t in c}})

# ---- numeri in alto
tot = {r['anno']: r['totale'] for r in serie}
picco_auto = max(auto_ff, key=auto_ff.get)
riep = {
    'serie': serie,
    'totale_2011': tot[2011], 'totale_2025': tot[2025], 'volte_2011_2025': round(tot[2025] / tot[2011], 1),
    'traccia': traccia,
    'mezzi25': mezzi25,
    'incidenti': incid,
    'controllo_ds179_incidenti_totali': ctrl179,
    'classifica': classifica,
    'picco_auto': {'anno': picco_auto, 'noleggi': auto_ff[picco_auto], 'noleggi_2025': auto_ff[2025],
                   'calo_pct': round(100 * (auto_ff[2025] / auto_ff[picco_auto] - 1))},
    'scooter': {'picco_anno': max(scoot, key=scoot.get), 'picco': max(scoot.values()), 'noleggi_2025': scoot[2025],
                'km_2023': km_sc[2023], 'km_2024': km_sc[2024]},
    'auto_stazione': auto_sb,
    'km_auto': km_auto, 'km_scooter': km_sc, 'km_bici': km_bici, 'km_monopattini': km_mon,
}
json.dump(riep, open(os.path.join(OUT, 'riepilogo.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('totale 2011', tot[2011], '2025', tot[2025], 'x', riep['volte_2011_2025'])
print('2025 noleggi/mezzo', {k: m['noleggi_per_mezzo_giorno'] for k, m in mezzi25.items()})
print('2025 km/mezzo', {k: m['km_per_mezzo_anno'] for k, m in mezzi25.items()})
print('auto picco', riep['picco_auto'])
print('incidenti', [(r['anno'], r['incidenti'], r['incidenti_per_milione_noleggi']) for r in incid])
print('ds179 totali', ctrl179, 'ISTAT', dict(zip(inc['anno'], inc['tutti'])))
for c in classifica: print(c['anno'], c['ordine'])
