# Costruisce i dati della pagina "Quanta corrente, quanta acqua" a partire dai file in consumi/out/
# (prodotti da prepara.py). Ricalcola i numeri e li confronta con quelli scritti in consumi/NOTE.md:
# se anche uno solo non coincide, il programma si ferma senza scrivere nulla.
# Uso: python -I -X utf8 build.py <radice del progetto>        (il bootstrap, qualche secondo, e' sempre rifatto: seme fisso)
# Scrive: docs/consumi/data/pagina.json e docs/consumi/data/consumi_giornalieri.csv
# Da novembre 2026: anche gas (ds1573), settori Terna dal 2000 (solo somme annue, licenza non indicata) e lampade LED (ds1576).
import csv, datetime as dt, json, math, os, statistics as st, sys
import numpy as np

DATA_SCARICO = '2026-11-03'
DATA_SCARICO_NUOVI = '2026-11-04'     # gas (ds1573), lampade (ds1576), Terna per settore
TEP_PER_GWH = 86.0            # Istat, glossario del report sui consumi elettrici delle citta' capoluogo (anno 2024)
TEP_PER_KM3 = 0.819           # tep per 1.000 m3 di gas naturale (stesso glossario)
KWH_PER_TEP = 1e6 / TEP_PER_GWH
GRANDI = ['Torino', 'Genova', 'Milano', 'Venezia', 'Bologna', 'Firenze', 'Roma', 'Napoli', 'Bari',
          'Reggio di Calabria', 'Palermo', 'Messina', 'Catania', 'Cagliari']
D = dt.date.fromisoformat
SEME = 20261103
N_BOOT = 1000
SEME_GAS = 20261104
N_BOOT_GAS = 1000
GAS_GRIGLIA = np.arange(8.0, 26.5, 0.5)       # soglie provate per il gas (temperatura sotto la quale sale)

# Festivita' nazionali + 7 dicembre (Sant'Ambrogio, patrono di Milano). Pasqua 21/4/2019 e 12/4/2020.
FESTE = {
    '2019-01-01', '2019-01-06', '2019-04-21', '2019-04-22', '2019-04-25', '2019-05-01', '2019-06-02', '2019-08-15',
    '2019-11-01', '2019-12-07', '2019-12-08', '2019-12-25', '2019-12-26',
    '2020-01-01', '2020-01-06', '2020-04-12', '2020-04-13', '2020-04-25', '2020-05-01', '2020-06-02', '2020-08-15',
    '2020-11-01', '2020-12-07', '2020-12-08', '2020-12-25', '2020-12-26'}
LOCK_DAL, LOCK_AL = '2020-02-24', '2020-06-30'          # lockdown e riaperture (principale)
AGO_DAL, AGO_AL = '08-05', '08-25'                       # pausa di agosto
GIORNI = ['lun', 'mar', 'mer', 'gio', 'ven', 'sab', 'dom']
ERRORI = []


def verifica(nome, calcolato, atteso):
    ok = calcolato == atteso
    print(('OK      ' if ok else 'ERRORE  ') + nome + ': calcolato ' + repr(calcolato) + ', atteso ' + repr(atteso))
    if not ok:
        ERRORI.append(nome)


def pct(a, b):
    return int(round(100 * (a / b - 1)))


def r1(x):
    return round(float(x), 1)


# ---------------------------------------------------------------- dati giornalieri
def carica_giornaliero(out):
    R = []
    with open(os.path.join(out, 'giornaliero.csv'), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            d = D(r['data'])
            R.append(dict(data=r['data'], d=d, wd=d.weekday(), gwh=float(r['gwh']), tmin=float(r['tmin']), tmax=float(r['tmax']),
                          tmean=float(r['tmean']), fonte=r['fonte_temperatura'], gas=float(r['gas_smc']) / 1e6))
    # media di oggi e ieri (il primo giorno non ha "ieri")
    for i, r in enumerate(R):
        r['tmax2'] = (r['tmax'] + R[i - 1]['tmax']) / 2 if i else r['tmax']
    for r in R:
        mmdd = r['data'][5:]
        r['festa'] = r['data'] in FESTE
        r['natale'] = mmdd >= '12-24' or mmdd <= '01-06'
        r['lock'] = LOCK_DAL <= r['data'] <= LOCK_AL
        r['ago'] = AGO_DAL <= mmdd <= AGO_AL
        r['feriale'] = r['wd'] < 5 and not r['festa']
        r['anno'] = r['d'].year
        r['sett'] = r['d'].isocalendar()[:2]
        r['tipo'] = 'festivo' if r['festa'] else (['feriale'] * 5 + ['sabato', 'domenica'])[r['wd']]
        # motivo di esclusione dal confronto sul caldo (solo per i feriali)
        if not r['feriale']:
            r['escl'] = 'non feriale'
        elif r['lock']:
            r['escl'] = 'lockdown e riaperture 2020'
        elif r['ago']:
            r['escl'] = 'pausa di agosto'
        elif r['natale']:
            r['escl'] = 'feste di fine anno'
        else:
            r['escl'] = ''
    return R


def ok_base(r):
    return r['escl'] == ''


# ---------------------------------------------------------------- modello del caldo
def disegno(rows, col, T0, T1):
    n = len(rows)
    t = np.array([r[col] for r in rows])
    cols = [np.ones(n), np.maximum(0.0, t - T0)]
    if T1 is not None:
        cols.append(np.maximum(0.0, T1 - t))
    cols.append(np.array([1.0 if r['anno'] == 2020 else 0.0 for r in rows]))
    for d in range(1, 5):
        cols.append(np.array([1.0 if r['wd'] == d else 0.0 for r in rows]))
    return np.column_stack(cols)


def adatta(rows, col, T0, T1):
    X = disegno(rows, col, T0, T1)
    y = np.array([r['gwh'] for r in rows])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    res = y - X @ b
    return b, float((res ** 2).sum())


def griglie(col):
    if col == 'tmean':
        T0s = np.arange(14.0, 28.5, 0.5)
    else:
        T0s = np.arange(20.0, 32.5, 0.5)
    return T0s


def migliore(rows, col, solo_caldo=False, passo=0.5, T1_max_dist=3.0):
    best = None
    T0s = griglie(col)
    if passo != 0.5:
        T0s = T0s[::int(round(passo / 0.5))]
    for T0 in T0s:
        T1s = [None] if solo_caldo else [None] + [float(x) for x in np.arange(2.0, T0 - T1_max_dist + 0.01, 1.0)]
        for T1 in T1s:
            b, sse = adatta(rows, col, T0, T1)
            if best is None or sse < best['sse']:
                best = dict(sse=sse, T0=float(T0), T1=T1, b=b)
    b = best['b']
    best['caldo'] = float(b[1])
    best['freddo'] = float(b[2]) if best['T1'] is not None else None
    return best


def r2(rows, col, best):
    y = np.array([r['gwh'] for r in rows])
    return 1 - best['sse'] / float(((y - y.mean()) ** 2).sum())


def bootstrap(rows, col):
    rng = np.random.default_rng(SEME)
    sett = {}
    for r in rows:
        sett.setdefault(r['sett'], []).append(r)
    chiavi = list(sett)
    ris = []
    for _ in range(N_BOOT):
        camp = []
        for k in rng.integers(0, len(chiavi), len(chiavi)):
            camp.extend(sett[chiavi[k]])
        b = migliore(camp, col, passo=1.0)
        ris.append((b['T0'], b['caldo'], b['T1'], b['freddo']))
    return np.array([[x if x is not None else np.nan for x in r] for r in ris], dtype=float)


def pc(a, p):
    a = a[~np.isnan(a)]
    return float(np.percentile(a, p))


# ---------------------------------------------------------------- calcoli principali
def calcola_caldo(R):
    base = [r for r in R if ok_base(r)]
    out = dict(n_base=len(base), n_2019=sum(r['anno'] == 2019 for r in base), n_2020=sum(r['anno'] == 2020 for r in base))
    out['n_feriali_totali'] = sum(r['feriale'] for r in R)
    out['esclusi'] = {k: sum(1 for r in R if r['escl'] == k) for k in ('lockdown e riaperture 2020', 'pausa di agosto', 'feste di fine anno')}
    out['n_vicine'] = sum(1 for r in base if r['fonte'] != 'BRERA_H')
    mod = {}
    for col in ('tmax', 'tmean', 'tmax2'):
        b = migliore(base, col)
        mod[col] = dict(T0=b['T0'], T1=b['T1'], caldo=b['caldo'], freddo=b['freddo'], r2=r2(base, col, b),
                        a=float(b['b'][0]), anno2020=float(b['b'][-5]),
                        dow=[0.0] + [float(x) for x in b['b'][-4:]])
        c = migliore(base, col, solo_caldo=True)
        mod[col]['solo_caldo'] = dict(T0=c['T0'], caldo=c['caldo'])
    out['modelli'] = mod
    # piatto: modello senza temperatura (solo giorno della settimana e anno) per dire quanto spiega la temperatura
    y = np.array([r['gwh'] for r in base])
    X = np.column_stack([np.ones(len(base)), [1.0 if r['anno'] == 2020 else 0.0 for r in base]] + [[1.0 if r['wd'] == d else 0.0 for r in base] for d in range(1, 5)])
    bb = np.linalg.lstsq(X, y, rcond=None)[0]
    out['r2_senza_temperatura'] = 1 - float(((y - X @ bb) ** 2).sum()) / float(((y - y.mean()) ** 2).sum())
    # correlazione semplice
    t = np.array([r['tmax'] for r in base])
    out['corr_tmax'] = float(np.corrcoef(t, y)[0, 1])
    out['corr_tmax_sopra_soglia'] = float(np.corrcoef(t[t >= mod['tmax']['T0']], y[t >= mod['tmax']['T0']])[0, 1])
    # sensibilita'
    def scen(nome, rows, col='tmax'):
        b = migliore(rows, col)
        return dict(nome=nome, n=len(rows), col=col, T0=b['T0'], T1=b['T1'], caldo=b['caldo'], freddo=b['freddo'])
    S = []
    def f(r, **kw):
        return r['feriale']
    for col in ('tmax', 'tmean'):
        S.append(scen('Scelta principale', base, col))
        S.append(scen('Solo il 2019', [r for r in base if r['anno'] == 2019], col))
        S.append(scen('2019 e 2020 solo prima del 24 febbraio', [r for r in base if r['anno'] == 2019 or r['data'] < LOCK_DAL], col))
        S.append(scen('2019 e 2020 da settembre', [r for r in base if r['anno'] == 2019 or r['data'] >= '2020-09-01'], col))
        for fine in ('2020-05-31', '2020-07-31'):
            S.append(scen('Lockdown e riaperture fino al ' + fine[8:].lstrip('0') + '/' + fine[5:7].lstrip('0') + '/2020',
                          [r for r in R if r['feriale'] and not r['natale'] and not r['ago'] and not (LOCK_DAL <= r['data'] <= fine)], col))
        S.append(scen('Con le feste di fine anno', [r for r in R if r['feriale'] and not r['lock'] and not r['ago']], col))
        S.append(scen('Con la pausa di agosto', [r for r in R if r['feriale'] and not r['natale'] and not r['lock']], col))
        S.append(scen('Senza tutto agosto', [r for r in R if r['feriale'] and not r['natale'] and not r['lock'] and r['data'][5:7] != '08'], col))
        S.append(scen('Senza i giorni con temperatura da stazioni vicine', [r for r in base if r['fonte'] == 'BRERA_H'], col))
    out['sensibilita'] = S
    # fasce di temperatura massima
    fasce = [(-99, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 30), (30, 35), (35, 99)]
    tab = []
    for a, b in fasce:
        v = [r for r in base if a <= r['tmax'] < b]
        v19 = [r['gwh'] for r in v if r['anno'] == 2019]
        tab.append(dict(da=None if a < -90 else a, a=None if b > 90 else b, n=len(v), n2019=len(v19),
                        mediana=r1(st.median([r['gwh'] for r in v])) if v else None,
                        mediana2019=r1(st.median(v19)) if v19 else None,
                        minimo=r1(min(r['gwh'] for r in v)) if v else None, massimo=r1(max(r['gwh'] for r in v)) if v else None))
    out['fasce'] = tab
    # domeniche e festivi non natalizi
    dom = [r for r in R if r['wd'] == 6 and not r['festa'] and not r['natale'] and not r['lock'] and not r['ago']]
    tabd = []
    for a, b in ((-99, 20), (20, 28), (28, 99)):
        v = [r['gwh'] for r in dom if a <= r['tmax'] < b]
        tabd.append(dict(da=None if a < -90 else a, a=None if b > 90 else b, n=len(v), mediana=r1(st.median(v)) if v else None))
    out['domeniche'] = dict(n=len(dom), fasce=tabd)
    return out, base


def curva_modello(c, base):
    m = c['modelli']['tmax']
    dow = float(np.mean(m['dow']))
    pts = []
    for t in np.arange(0.0, 38.5, 0.5):
        y = m['a'] + dow + m['caldo'] * max(0.0, t - m['T0']) + (m['freddo'] * max(0.0, m['T1'] - t) if m['T1'] is not None else 0.0)
        pts.append([float(t), round(float(y), 2)])
    return pts


def calcola_giorni(R):
    def fer(a, b):
        return [r['gwh'] for r in R if a <= r['data'] <= b and r['wd'] < 5 and not r['festa']]
    def dom(a, b):
        return [r['gwh'] for r in R if a <= r['data'] <= b and r['wd'] == 6]
    o = {}
    o['feriali_marzo2019'] = st.median(fer('2019-03-01', '2019-03-31'))
    o['n_marzo2019'] = len(fer('2019-03-01', '2019-03-31'))
    o['feriali_feb2020'] = st.median(fer('2020-02-01', '2020-02-21'))
    o['n_feb2020'] = len(fer('2020-02-01', '2020-02-21'))
    o['feriali_lock'] = st.median(fer('2020-03-23', '2020-03-27'))
    o['dom_marzo2019'] = st.median(dom('2019-03-01', '2019-03-31'))
    o['dom_lock'] = dom('2020-03-29', '2020-03-29')[0]
    o['feriali_lug2019'] = st.median(fer('2019-07-01', '2019-07-31'))
    o['feriali_gen2019'] = st.median(fer('2019-01-07', '2019-01-31'))
    o['feriali_lug2020'] = st.median(fer('2020-07-01', '2020-07-31'))
    o['feriali_gen2020'] = st.median(fer('2020-01-07', '2020-01-31'))
    o['feriali_apr_lock'] = st.median(fer('2020-04-14', '2020-04-17'))
    G = {r['data']: r for r in R}
    o['ferragosto'] = [dict(data='2019-08-%02d' % g, sett=GIORNI[D('2019-08-%02d' % g).weekday()], gwh=G['2019-08-%02d' % g]['gwh'], tmax=G['2019-08-%02d' % g]['tmax']) for g in range(11, 20)]
    o['ferragosto_sett'] = st.median(G['2019-08-%02d' % g]['gwh'] for g in range(12, 17))
    o['ferragosto_sett_var'] = pct(o['ferragosto_sett'], o['feriali_marzo2019'])
    o['ferragosto_tmax_media'] = round(st.mean(G['2019-08-%02d' % g]['tmax'] for g in range(11, 20)), 1)
    mx = max(R, key=lambda r: r['gwh'])
    mn = min(R, key=lambda r: r['gwh'])
    o['massimo'] = dict(data=mx['data'], gwh=mx['gwh'], tmax=mx['tmax'], tmean=mx['tmean'])
    o['minimo'] = dict(data=mn['data'], gwh=mn['gwh'], tmax=mn['tmax'], vicini=[G['2020-04-15']['gwh'], G['2020-04-17']['gwh']])
    ordine = sorted(R, key=lambda r: -r['tmax'])
    o['posto_tmax_massimo'] = [i + 1 for i, r in enumerate(ordine) if r['data'] == mx['data']][0]
    o['top10'] = [dict(data=r['data'], gwh=r['gwh'], tmax=r['tmax']) for r in sorted(R, key=lambda r: -r['gwh'])[:10]]
    o['somma'] = {str(a): round(sum(r['gwh'] for r in R if r['anno'] == a), 1) for a in (2019, 2020)}
    return o


# ---------------------------------------------------------------- annuale e citta'
def calcola_energia(C):
    E = C['energia']
    anni = [str(a) for a in range(2015, 2025)]
    M = E['Milano']
    ann = []
    for a in anni:
        gwh = M['tep'][a] / TEP_PER_GWH
        gas = M['gas_tep'][a] / TEP_PER_KM3 / 1000.0
        ann.append(dict(anno=int(a), gwh=round(gwh, 1), kwh_ab=round(M['tep100'][a] * KWH_PER_TEP / 100.0), gas_mm3=round(gas, 1),
                        dom_gwh=round(M['dom_tep'][a] / TEP_PER_GWH, 1), nondom_gwh=round(M['nondom_tep'][a] / TEP_PER_GWH, 1)))
    citta = []
    for c in GRANDI:
        e = E[c]
        k15 = e['tep100']['2015'] * KWH_PER_TEP / 100.0
        k24 = e['tep100']['2024'] * KWH_PER_TEP / 100.0
        k19 = e['tep100']['2019'] * KWH_PER_TEP / 100.0
        citta.append(dict(nome=c, kwh_ab_2015=round(k15), kwh_ab_2019=round(k19), kwh_ab_2024=round(k24), var=round(100 * (k24 / k15 - 1), 1), var_2019=round(100 * (k24 / k19 - 1), 1),
                          gwh_2024=round(e['tep']['2024'] / TEP_PER_GWH)))
    return ann, citta


def calcola_acqua(C):
    A = C['acqua']
    anni = ['2018', '2020', '2022', '2024']
    mil = []
    for a in anni:
        v = A['Milano'][a]
        pop = v['immessa_vol'] * 1e6 / (366 if a == '2020' else 365) / v['immessa_pc']          # abitanti impliciti (solo per controllo)
        mil.append(dict(anno=int(a), immessa_vol=v['immessa_vol'], immessa_pc=v['immessa_pc'], erogata_vol=v['erogata_vol'], erogata_pc=v['erogata_pc'],
                        perdite_pct=v['perdite_pct'], fatturata_pc=v.get('fatturata_pc'), domestica_pc=v.get('domestica_pc'), domestica_vol=v.get('domestica_vol'),
                        perdite_calc=round(100 * (1 - v['erogata_vol'] / v['immessa_vol']), 1), abitanti_impliciti=round(pop / 1000.0)))
    citta = []
    for c in GRANDI:
        a18, a24 = A[c]['2018'], A[c]['2024']
        citta.append(dict(nome=c, immessa_2018=a18['immessa_pc'], immessa_2024=a24['immessa_pc'], erogata_2018=a18['erogata_pc'], erogata_2024=a24['erogata_pc'],
                          perdite_2018=a18['perdite_pct'], perdite_2024=a24['perdite_pct'], domestica_2024=a24['domestica_pc']))
    return mil, citta


# ---------------------------------------------------------------- gas e freddo (ds1573, milioni di Smc al giorno)
def gas_fit(rows, col, T1, tipi=False):
    t = np.array([r[col] for r in rows])
    y = np.array([r['gas'] for r in rows])
    cols = [np.ones(len(rows)), np.maximum(0.0, T1 - t)]
    if tipi:
        cols += [np.array([1.0 if r['tipo'] == 'sabato' else 0.0 for r in rows]), np.array([1.0 if r['tipo'] in ('domenica', 'festivo') else 0.0 for r in rows])]
    X = np.column_stack(cols)
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    return b, float(((y - X @ b) ** 2).sum())


def gas_migliore(rows, col='tmean', tipi=False):
    best = None
    for T1 in GAS_GRIGLIA:
        b, sse = gas_fit(rows, col, float(T1), tipi)
        if best is None or sse < best[2]:
            best = (float(T1), b, sse)
    y = np.array([r['gas'] for r in rows])
    return dict(T1=best[0], base=float(best[1][0]), per_grado=float(best[1][1]), sse=best[2], r2=1 - best[2] / float(((y - y.mean()) ** 2).sum()), n=len(rows), b=best[1])


def calcola_gas(R):
    fer = [r for r in R if r['tipo'] == 'feriale']
    lock = lambda r: LOCK_DAL <= r['data'] <= LOCK_AL
    out = dict(n_feriali=len(fer))
    m = gas_migliore(fer)
    # bootstrap per settimane intere (stesso metodo del caldo), seme proprio
    rng = np.random.default_rng(SEME_GAS)
    sett = {}
    for r in fer:
        sett.setdefault(r['sett'], []).append(r)
    chiavi = list(sett)
    ris = []
    for _ in range(N_BOOT_GAS):
        camp = []
        for k in rng.integers(0, len(chiavi), len(chiavi)):
            camp.extend(sett[chiavi[k]])
        bb = gas_migliore(camp)
        ris.append((bb['T1'], bb['per_grado']))
    ris = np.array(ris)
    m['boot_per_grado'] = [float(np.percentile(ris[:, 1], 2.5)), float(np.percentile(ris[:, 1], 97.5))]
    m['boot_soglia'] = [float(np.percentile(ris[:, 0], 2.5)), float(np.percentile(ris[:, 0], 97.5))]
    out['principale'] = m
    def scen(nome, rows, col='tmean', tipi=False):
        b = gas_migliore(rows, col, tipi)
        return dict(nome=nome, n=len(rows), col=col, T1=b['T1'], base=b['base'], per_grado=b['per_grado'])
    out['sensibilita'] = [
        scen('Scelta principale: giorni feriali', fer),
        scen('Solo i feriali del 2019', [r for r in fer if r['anno'] == 2019]),
        scen('Solo i feriali del 2020', [r for r in fer if r['anno'] == 2020]),
        scen('Feriali senza lockdown e riaperture', [r for r in fer if not lock(r)]),
        scen('Feriali senza i giorni con temperatura da stazioni vicine', [r for r in fer if r['fonte'] == 'BRERA_H']),
        scen('Feriali, con la temperatura massima invece della media', fer, 'tmax'),
        scen('Solo i sabati', [r for r in R if r['tipo'] == 'sabato']),
        scen('Solo domeniche e feste', [r for r in R if r['tipo'] in ('domenica', 'festivo')]),
        scen('Tutti i 731 giorni, con una base diversa per tipo di giorno', R, 'tmean', True)]
    # fasce di temperatura media (feriali)
    tab = []
    for a, b in ((-99, 5), (5, 10), (10, 15), (15, 20), (20, 99)):
        v = [r['gas'] for r in fer if a <= r['tmean'] < b]
        tab.append(dict(da=None if a < -90 else a, a=None if b > 90 else b, n=len(v), mediana=round(st.median(v), 2), minimo=round(min(v), 2), massimo=round(max(v), 2)))
    out['fasce'] = tab
    # confronto tra tipi di giorno alla stessa soglia: base estiva (>= soglia) e mediane nel freddo (temperatura media sotto 8 gradi)
    out['mediane_freddo'] = {n: round(st.median([r['gas'] for r in R if r['tipo'] in t and r['tmean'] < 8]), 2) for n, t in (('feriale', ('feriale',)), ('sabato', ('sabato',)), ('domenica', ('domenica', 'festivo')))}
    out['curva'] = [[float(t), round(m['base'] + m['per_grado'] * max(0.0, m['T1'] - t), 3)] for t in np.arange(-4.0, 30.5, 0.5)]
    out['somma'] = {str(a): round(sum(r['gas'] for r in R if r['anno'] == a), 1) for a in (2019, 2020)}
    out['minimo'] = min(R, key=lambda r: r['gas'])['data']
    out['massimo'] = max(R, key=lambda r: r['gas'])['data']
    out['n_mezzi'] = sum(1 for r in R if abs(r['gas'] * 1e6 - round(r['gas'] * 1e6)) > 0.01)
    return out


# ---------------------------------------------------------------- settori Terna dal 2000 (provincia di Milano + Monza e Brianza)
def calcola_settori(C):
    T = C['terna']
    serie = []
    for a in sorted(int(x) for x in T):
        t = T[str(a)]
        def s(sett, prov=('Milano', 'Monza e della Brianza')):
            return sum(t.get(p, {}).get(sett, 0.0) for p in prov)
        tot = sum(sum(t.get(p, {}).values()) for p in ('Milano', 'Monza e della Brianza'))
        serie.append(dict(anno=a, totale=round(tot, 1), industria=round(s('Industria'), 1), servizi=round(s('Servizi'), 1), domestico=round(s('Domestico'), 1), agricoltura=round(s('Agricoltura'), 1),
                          milano=round(sum(t.get('Milano', {}).values()), 1), monza=round(sum(t.get('Monza e della Brianza', {}).values()), 1)))
    return serie


def calcola_led(C):
    L = C['led']
    return [dict(anno=int(a), tradizionali=v[0], led=v[1], totale=v[0] + v[1]) for a, v in sorted(L.items())]


# ---------------------------------------------------------------- cache del bootstrap (seme fisso: il risultato non cambia)
def bootstrap_cache(out, base):
    p = os.path.join(out, 'bootstrap.json')
    chiave = dict(seme=SEME, n=N_BOOT, righe=len(base), somma=round(sum(r['gwh'] for r in base), 1))
    if os.path.exists(p):
        c = json.load(open(p, encoding='utf-8'))
        if c.get('chiave') == chiave:
            return {k: np.array(v, dtype=float) for k, v in c['boot'].items()}
    boot = {col: bootstrap(base, col) for col in ('tmax', 'tmean')}
    json.dump(dict(chiave=chiave, boot={k: [[None if math.isnan(x) else x for x in r] for r in v.tolist()] for k, v in boot.items()}), open(p, 'w', encoding='utf-8'))
    return {k: np.nan_to_num(v, nan=np.nan) for k, v in boot.items()}


def previsto_agosto(caldo, R):
    """Quanto prevede il modello (adattato fuori dalle pause) per i giorni di lavoro del 12-16 agosto 2019, con la loro temperatura."""
    m = caldo['modelli']['tmax']
    G = {r['data']: r for r in R}
    righe = []
    for g in (12, 13, 14, 16):
        r = G['2019-08-%02d' % g]
        y = m['a'] + m['dow'][r['wd']] + m['caldo'] * max(0.0, r['tmax'] - m['T0']) + (m['freddo'] * max(0.0, m['T1'] - r['tmax']) if m['T1'] is not None else 0.0)
        righe.append(dict(data=r['data'], gwh=r['gwh'], tmax=r1(r['tmax']), previsto=round(y, 1)))
    mis = st.median(x['gwh'] for x in righe)
    prev = st.median(x['previsto'] for x in righe)
    return righe, round(mis, 2), round(prev, 2), pct(mis, prev)


def main(radice):
    out = os.path.join(radice, 'consumi', 'out')
    dest = os.path.join(radice, 'docs', 'consumi', 'data')
    R = carica_giornaliero(out)
    C = json.load(open(os.path.join(out, 'citta.json'), encoding='utf-8'))
    caldo, base = calcola_caldo(R)
    giorni = calcola_giorni(R)
    ann, citta_e = calcola_energia(C)
    mil, citta_a = calcola_acqua(C)
    boot = bootstrap_cache(out, base)
    for col in boot:
        b = boot[col]
        caldo['modelli'][col]['boot'] = dict(caldo=[pc(b[:, 1], 2.5), pc(b[:, 1], 97.5)], T0=[pc(b[:, 0], 2.5), pc(b[:, 0], 97.5)],
                                             freddo=[pc(b[:, 3], 2.5), pc(b[:, 3], 97.5)], T1=[pc(b[:, 2], 2.5), pc(b[:, 2], 97.5)],
                                             caldo_mediana=pc(b[:, 1], 50))
    caldo['curva'] = curva_modello(caldo, base)
    ago_righe, ago_mis, ago_prev, ago_diff = previsto_agosto(caldo, R)
    vib = json.load(open(os.path.join(radice, 'docs', 'vibrazioni', 'data', 'pagina.json'), encoding='utf-8'))
    nuovi = dict(gas=calcola_gas(R), settori=calcola_settori(C), led=calcola_led(C))
    stampa_e_verifica(R, C, caldo, giorni, ann, citta_e, mil, citta_a, (ago_righe, ago_mis, ago_prev, ago_diff), vib, nuovi)
    if ERRORI:
        print('FALLITO: %d controlli non tornano (%s). Non scrivo nulla.' % (len(ERRORI), ', '.join(ERRORI)))
        sys.exit(1)
    scrivi(dest, R, C, caldo, giorni, ann, citta_e, mil, citta_a, (ago_righe, ago_mis, ago_prev, ago_diff), vib, nuovi)


def valori_da_controllare(R, C, caldo, giorni, ann, citta_e, mil, citta_a, ago, vib, nuovi):
    """Elenco (nome, valore calcolato) dei numeri scritti in NOTE.md."""
    m = caldo['modelli']['tmax']
    mm = caldo['modelli']['tmean']
    A = {a['anno']: a for a in ann}
    ce = {c['nome']: c for c in citta_e}
    ca = {c['nome']: c for c in citta_a}
    M = {x['anno']: x for x in mil}
    V = []
    add = lambda n, v: V.append((n, v))
    # --- dati giornalieri
    add('giorni nel file', len(R))
    add('somma 2019 e 2020 (GWh)', (giorni['somma']['2019'], giorni['somma']['2020']))
    add('massimo: data, GWh, tmax', (giorni['massimo']['data'], giorni['massimo']['gwh'], r1(giorni['massimo']['tmax'])))
    add('il massimo e il 2o giorno piu caldo su 731', giorni['posto_tmax_massimo'])
    add('minimo: data, GWh, vicini', (giorni['minimo']['data'], giorni['minimo']['gwh'], giorni['minimo']['vicini']))
    add('festivi nazionali + 7/12 nei due anni', len(FESTE))
    # --- lockdown e Ferragosto
    add('feriali marzo 2019 (n giorni)', (giorni['feriali_marzo2019'], giorni['n_marzo2019']))
    add('feriali 1-21 febbraio 2020 (n giorni)', (giorni['feriali_feb2020'], giorni['n_feb2020']))
    add('feriali 23-27 marzo 2020', giorni['feriali_lock'])
    add('lockdown su marzo 2019 e su febbraio 2020 (%)', (pct(giorni['feriali_lock'], giorni['feriali_marzo2019']), pct(giorni['feriali_lock'], giorni['feriali_feb2020'])))
    add('domeniche: marzo 2019 e 29/3/2020', (giorni['dom_marzo2019'], giorni['dom_lock']))
    add('domenica lockdown su marzo 2019 (%)', pct(giorni['dom_lock'], giorni['dom_marzo2019']))
    add('feriali luglio 2019 e gennaio 2019 (dal 7)', (giorni['feriali_lug2019'], giorni['feriali_gen2019']))
    add('Ferragosto 11-19 agosto', [x['gwh'] for x in giorni['ferragosto']])
    add('Ferragosto: temperatura massima media 11-19 agosto', giorni['ferragosto_tmax_media'])
    add('Ferragosto: feriali 12-16 agosto (mediana) e su marzo 2019 (%)', (giorni['ferragosto_sett'], giorni['ferragosto_sett_var']))
    add('Ferragosto: misurato, previsto (mediana 12, 13, 14, 16), differenza %', (ago[1], ago[2], ago[3]))
    # --- caldo
    add('giorni feriali (totali) / usati nel confronto', (caldo['n_feriali_totali'], caldo['n_base']))
    add('usati 2019 / 2020', (caldo['n_2019'], caldo['n_2020']))
    add('esclusi per motivo (lockdown, agosto, fine anno)', tuple(caldo['esclusi'].values()))
    add('giorni usati con temperatura da stazioni vicine', caldo['n_vicine'])
    add('tmax: soglia caldo, soglia freddo', (m['T0'], m['T1']))
    add('tmax: GWh per grado sopra soglia (2 decimali), freddo', (round(m['caldo'], 2), round(m['freddo'], 2)))
    add('tmax: intervallo bootstrap caldo (2 decimali)', tuple(round(x, 2) for x in m['boot']['caldo']))
    add('tmax: intervallo bootstrap soglia caldo', tuple(m['boot']['T0']))
    add('tmax: intervallo bootstrap freddo (2 decimali)', tuple(round(x, 2) for x in m['boot']['freddo']))
    add('tmean: soglie, caldo, freddo', (mm['T0'], mm['T1'], round(mm['caldo'], 2), round(mm['freddo'], 2)))
    add('tmean: intervallo bootstrap caldo', tuple(round(x, 2) for x in mm['boot']['caldo']))
    add('R2 con e senza temperatura (2 decimali)', (round(m['r2'], 2), round(caldo['r2_senza_temperatura'], 2)))
    add('correlazione tmax-GWh (tutti, sopra soglia)', (round(caldo['corr_tmax'], 2), round(caldo['corr_tmax_sopra_soglia'], 2)))
    add('effetto 2020 (GWh a parita di tutto)', round(m['anno2020'], 2))
    add('giorno della settimana (mar, mer, gio, ven rispetto a lun)', tuple(round(x, 2) for x in m['dow'][1:]))
    add('sensibilita: minimo e massimo GWh/grado (tmax)', (round(min(x['caldo'] for x in caldo['sensibilita'] if x['col'] == 'tmax'), 2), round(max(x['caldo'] for x in caldo['sensibilita'] if x['col'] == 'tmax'), 2)))
    add('sensibilita: minimo e massimo GWh/grado (tmean)', (round(min(x['caldo'] for x in caldo['sensibilita'] if x['col'] == 'tmean'), 2), round(max(x['caldo'] for x in caldo['sensibilita'] if x['col'] == 'tmean'), 2)))
    add('fasce di tmax: n', [f['n'] for f in caldo['fasce']])
    add('fasce di tmax: mediana', [f['mediana'] for f in caldo['fasce']])
    add('domeniche: n e (n, mediana) per meno di 20, 20-28, 28 e oltre', (caldo['domeniche']['n'], [(f['n'], f['mediana']) for f in caldo['domeniche']['fasce']]))
    # --- anni
    add('ISTAT GWh 2015-2024', [A[a]['gwh'] for a in range(2015, 2025)])
    add('ISTAT kWh per abitante 2015-2024', [A[a]['kwh_ab'] for a in range(2015, 2025)])
    add('gas milioni di m3 2015-2024', [A[a]['gas_mm3'] for a in range(2015, 2025)])
    add('ISTAT (GWh da tep/86) uguale a Tav 6.3 GWh 2018-2024 (tolleranza 0,05)', all(abs(A[int(y)]['gwh'] - v) < 0.05 for y, v in C['gwh_diretti_milano'].items()))
    add('ISTAT (gas da tep) uguale a Tav 6.4 2018-2024 (tolleranza 0,05)', all(abs(A[int(y)]['gas_mm3'] - v) < 0.05 for y, v in C['gas_milioni_m3_milano'].items()))
    add('ISTAT uguale al dataset del Comune ds1537 2015-2018 (tolleranza 0,05)', all(abs(A[int(y)]['gwh'] - v) < 0.05 for y, v in C['ds1537'].items() if y != '2014'))
    add('ds1537 2014 contro ISTAT attuale', (C['ds1537']['2014'], round(C['energia']['Milano']['tep']['2014'] / TEP_PER_GWH, 1)))
    EM = C['energia']['Milano']
    add('salto 2009-2010 Milano: elettricita (%), gas (%), domestico (%)',
        (pct(EM['tep']['2010'], EM['tep']['2009']), pct(EM['gas_tep']['2010'], EM['gas_tep']['2009']), pct(EM['dom_tep']['2010'], EM['dom_tep']['2009'])))
    add('salto 2009-2010 in tutti i capoluoghi: numero confrontato, calo elettricita >= 10% e gas >= +20%', (C['salto_2009_2010_comuni']['n_comuni'], C['salto_2009_2010_comuni']['el_meno10_gas_piu20']))
    add('A2A su ISTAT (%): 2019, 2020', (round(100 * (giorni['somma']['2019'] / A[2019]['gwh'] - 1), 1), round(100 * (giorni['somma']['2020'] / A[2020]['gwh'] - 1), 1)))
    add('ISTAT 2020 su 2019 (%) e A2A 2020 su 2019 (%)', (round(100 * (A[2020]['gwh'] / A[2019]['gwh'] - 1), 1), round(100 * (giorni['somma']['2020'] / giorni['somma']['2019'] - 1), 1)))
    add('Milano kWh per abitante 2015-2024: variazione %', ce['Milano']['var'])
    add('Milano: posto per kWh per abitante nel 2024 tra le 14', 1 + sum(c['kwh_ab_2024'] > ce['Milano']['kwh_ab_2024'] for c in citta_e))
    add('Milano: quota non domestico 2022 (%)', round(100 * A[2022]['nondom_gwh'] / A[2022]['gwh']))
    add('ds523 2011: elettricita domestica kWh, acqua domestica m3, litri al giorno', (C['ds523']['2011']['Energia elettrica per uso domestico'], C['ds523']['2011']['Acqua fatturata per uso domestico'], round(C['ds523']['2011']['Acqua fatturata per uso domestico'] * 1000 / 365)))
    # --- acqua
    add('acqua Milano 2018, 2020, 2022, 2024: immessa l/ab/g', [M[a]['immessa_pc'] for a in (2018, 2020, 2022, 2024)])
    add('acqua Milano: erogata l/ab/g', [M[a]['erogata_pc'] for a in (2018, 2020, 2022, 2024)])
    add('acqua Milano: perdite % dichiarate', [M[a]['perdite_pct'] for a in (2018, 2020, 2022, 2024)])
    add('acqua Milano: perdite % ricalcolate da immessa ed erogata', [M[a]['perdite_calc'] for a in (2018, 2020, 2022, 2024)])
    add('acqua Milano: domestica l/ab/g 2020, 2022, 2024', [M[a]['domestica_pc'] for a in (2020, 2022, 2024)])
    add('acqua Milano 2024: immessa, erogata, domestica (migliaia di m3)', (M[2024]['immessa_vol'], M[2024]['erogata_vol'], M[2024]['domestica_vol']))
    add('acqua Milano 2018: dataset del Comune ds1571 uguale a Istat', C['ds1571'] == [M[2018]['immessa_vol'], M[2018]['immessa_pc'], M[2018]['erogata_vol'], M[2018]['erogata_pc'], M[2018]['perdite_pct']])
    add('acqua: perdite 2024 Milano contro mediana delle altre 13', (ca['Milano']['perdite_2024'], round(st.median(c['perdite_2024'] for c in citta_a if c['nome'] != 'Milano'), 1)))
    add('acqua: domestica 2024, Milano contro mediana delle altre 13', (ca['Milano']['domestica_2024'], st.median(c['domestica_2024'] for c in citta_a if c['nome'] != 'Milano')))
    add('acqua: citta con la perdita piu bassa nel 2018 e nel 2024', (min(citta_a, key=lambda c: c['perdite_2018'])['nome'], min(citta_a, key=lambda c: c['perdite_2024'])['nome']))
    add('acqua: citta (su 14) con perdite in calo 2018-2024', sum(c['perdite_2024'] < c['perdite_2018'] for c in citta_a))
    # --- altre pagine
    add('vibrazioni: lockdown giorno su marzo 2019 e Ferragosto feriali su marzo 2019 (%)', (vib['giornata']['rispetto_marzo2019']['giorno'], vib['ferragosto']['rispetto_marzo2019']['feriali']))
    # --- gas (ds1573)
    G = nuovi['gas']
    gm = G['principale']
    add('gas: feriali usati, soglia (C), base estiva (Mmc/giorno), Mmc per grado (3 decimali)', (G['n_feriali'], gm['T1'], round(gm['base'], 2), round(gm['per_grado'], 3)))
    add('gas: R2 (2 decimali)', round(gm['r2'], 2))
    add('gas: intervallo bootstrap Mmc per grado (3 decimali) e soglia', (tuple(round(x, 3) for x in gm['boot_per_grado']), tuple(gm['boot_soglia'])))
    add('gas: stabilita, soglia e Mmc per grado di ogni scelta', [(x['n'], x['T1'], round(x['per_grado'], 3)) for x in G['sensibilita']])
    add('gas: basi (Mmc) feriali, sabati, domeniche e feste', tuple(round(x['base'], 2) for x in G['sensibilita'] if x['nome'] in ('Scelta principale: giorni feriali', 'Solo i sabati', 'Solo domeniche e feste')))
    add('gas: fasce di temperatura media dei feriali, n e mediana (Mmc)', [(f['n'], f['mediana']) for f in G['fasce']])
    add('gas: mediane con temperatura media sotto 8 gradi: feriali, sabati, domeniche e feste', (G['mediane_freddo']['feriale'], G['mediane_freddo']['sabato'], G['mediane_freddo']['domenica']))
    add('gas: somme annue A2A (milioni di Smc)', (G['somma']['2019'], G['somma']['2020']))
    add('gas: A2A su ISTAT (%), 2019 e 2020', (round(100 * (G['somma']['2019'] / A[2019]['gas_mm3'] - 1), 1), round(100 * (G['somma']['2020'] / A[2020]['gas_mm3'] - 1), 1)))
    add('gas: 2020 su 2019 (%), A2A e ISTAT', (round(100 * (G['somma']['2020'] / G['somma']['2019'] - 1), 1), round(100 * (A[2020]['gas_mm3'] / A[2019]['gas_mm3'] - 1), 1)))
    add('gas: giorno piu basso e piu alto', (G['minimo'], G['massimo']))
    add('gas: righe con mezzi Smc (16-19 aprile 2020)', G['n_mezzi'])
    # --- settori Terna, provincia di Milano + Monza e Brianza
    SE = {x['anno']: x for x in nuovi['settori']}
    add('Terna: anni 2000-2024 senza buchi', [x['anno'] for x in nuovi['settori']] == list(range(2000, 2025)))
    add('Terna: totale Milano+Monza 2000, 2008, 2024 (GWh)', (round(SE[2000]['totale']), round(SE[2008]['totale']), round(SE[2024]['totale'])))
    add('Terna: anno del massimo', max(SE, key=lambda a: SE[a]['totale']))
    add('Terna: 2009 Milano (che comprende Monza); 2010 Milano e Monza', (round(SE[2009]['milano']), round(SE[2010]['milano']), round(SE[2010]['monza'])))
    add('Terna: 2000 industria, servizi, case', (round(SE[2000]['industria']), round(SE[2000]['servizi']), round(SE[2000]['domestico'])))
    add('Terna: 2018 industria, servizi, case', (round(SE[2018]['industria']), round(SE[2018]['servizi']), round(SE[2018]['domestico'])))
    add('Terna: 2019 industria, servizi, case', (round(SE[2019]['industria']), round(SE[2019]['servizi']), round(SE[2019]['domestico'])))
    add('Terna: variazione 2018-2019 servizi, industria, case, totale (%)', (pct(SE[2019]['servizi'], SE[2018]['servizi']), pct(SE[2019]['industria'], SE[2018]['industria']), pct(SE[2019]['domestico'], SE[2018]['domestico']), pct(SE[2019]['totale'], SE[2018]['totale'])))
    add('Terna: 2020 e 2024 totale (GWh)', (round(SE[2020]['totale']), round(SE[2024]['totale'])))
    I91 = C['istat_tav91_provincia_milano']
    dif = {int(a): SE[int(a)]['milano'] - v for a, v in I91.items()}
    add('Terna provincia di Milano uguale a ISTAT Tav 9.1: 2017-2024 entro 0,5 GWh, 2018-2024 entro 0,05', (all(abs(d) < 0.5 for d in dif.values()), all(abs(d) < 0.05 for a, d in dif.items() if a >= 2018)))
    add('Terna contro ISTAT Tav 9.1: 2017 e 2024 (GWh)', (round(SE[2017]['milano'], 1), I91['2017'], round(SE[2024]['milano'], 1), I91['2024']))
    # --- lampade (ds1576)
    LE = {x['anno']: x for x in nuovi['led']}
    add('LED: anni 2002-2020 senza buchi', [x['anno'] for x in nuovi['led']] == list(range(2002, 2021)))
    add('LED: 2002, 2013, 2014, 2020 (tradizionali, LED)', [(LE[a]['tradizionali'], LE[a]['led']) for a in (2002, 2013, 2014, 2020)])
    add('LED: totale lampade 2002, 2013, 2014, 2020', [LE[a]['totale'] for a in (2002, 2013, 2014, 2020)])
    add('LED: il totale non scende mai, i LED non scendono mai', (all(LE[a]['totale'] >= LE[a - 1]['totale'] for a in range(2003, 2021)), all(LE[a]['led'] >= LE[a - 1]['led'] for a in range(2003, 2021))))
    add('LED: quota LED 2014 e 2020 (%)', (round(100 * LE[2014]['led'] / LE[2014]['totale'], 1), round(100 * LE[2020]['led'] / LE[2020]['totale'], 1)))
    add('LED: variazione annua massima del totale (lampade) e anno', max((LE[a]['totale'] - LE[a - 1]['totale'], a) for a in range(2003, 2021)))
    return V


def stampa_e_verifica(R, C, caldo, giorni, ann, citta_e, mil, citta_a, ago, vib, nuovi):
    print('--- controlli contro NOTE.md')
    for nome, v in valori_da_controllare(R, C, caldo, giorni, ann, citta_e, mil, citta_a, ago, vib, nuovi):
        if nome in ATTESI:
            verifica(nome, v, ATTESI[nome])
        else:
            print('DA SCRIVERE ' + nome + ': ' + repr(v))
            ERRORI.append(nome)


ATTESI = {
    'salto 2009-2010 in tutti i capoluoghi: numero confrontato, calo elettricita >= 10% e gas >= +20%': (103, ['milano']),
    'Ferragosto: feriali 12-16 agosto (mediana) e su marzo 2019 (%)': (16.9, -10),
    'giorni nel file': 731,
    'somma 2019 e 2020 (GWh)': (7116.7, 6399.3),
    'massimo: data, GWh, tmax': ('2019-06-27', 30.9, 36.9),
    'il massimo e il 2o giorno piu caldo su 731': 2,
    'minimo: data, GWh, vicini': ('2020-04-16', 12.3, [14.2, 14.1]),
    'festivi nazionali + 7/12 nei due anni': 26,
    'feriali marzo 2019 (n giorni)': (18.7, 21),
    'feriali 1-21 febbraio 2020 (n giorni)': (19.8, 15),
    'feriali 23-27 marzo 2020': 15.0,
    'lockdown su marzo 2019 e su febbraio 2020 (%)': (-20, -24),
    'domeniche: marzo 2019 e 29/3/2020': (15.5, 13.1),
    'domenica lockdown su marzo 2019 (%)': -15,
    'feriali luglio 2019 e gennaio 2019 (dal 7)': (25.2, 21.7),
    'Ferragosto 11-19 agosto': [18.0, 19.3, 17.7, 16.9, 15.5, 16.2, 15.8, 16.0, 18.5],
    'Ferragosto: temperatura massima media 11-19 agosto': 30.1,
    'Ferragosto: misurato, previsto (mediana 12, 13, 14, 16), differenza %': (17.3, 21.55, -20),
    'giorni feriali (totali) / usati nel confronto': (507, 375),
    'usati 2019 / 2020': (232, 143),
    'esclusi per motivo (lockdown, agosto, fine anno)': (89, 29, 14),
    'giorni usati con temperatura da stazioni vicine': 17,
    'tmax: soglia caldo, soglia freddo': (26.0, 18.0),
    'tmax: GWh per grado sopra soglia (2 decimali), freddo': (0.78, 0.2),
    'tmax: intervallo bootstrap caldo (2 decimali)': (0.5, 1.1),
    'tmax: intervallo bootstrap soglia caldo': (24.0, 28.0),
    'tmax: intervallo bootstrap freddo (2 decimali)': (0.16, 0.33),
    'tmean: soglie, caldo, freddo': (21.0, 14.0, 0.88, 0.26),
    'tmean: intervallo bootstrap caldo': (0.53, 1.11),
    'R2 con e senza temperatura (2 decimali)': (0.78, 0.07),
    'correlazione tmax-GWh (tutti, sopra soglia)': (0.4, 0.83),
    'effetto 2020 (GWh a parita di tutto)': -1.19,
    'giorno della settimana (mar, mer, gio, ven rispetto a lun)': (0.18, 0.25, 0.2, 0.04),
    'sensibilita: minimo e massimo GWh/grado (tmax)': (0.71, 1.06),
    'sensibilita: minimo e massimo GWh/grado (tmean)': (0.79, 0.96),
    'fasce di tmax: n': [10, 54, 70, 83, 53, 50, 44, 11],
    'fasce di tmax: mediana': [21.6, 20.6, 19.9, 18.6, 18.5, 20.0, 22.1, 28.4],
    'domeniche: n e (n, mediana) per meno di 20, 20-28, 28 e oltre': (72, [(44, 16.4), (13, 16.0), (15, 17.9)]),
    'ISTAT GWh 2015-2024': [6824.3, 6643.5, 6732.4, 6750.1, 6677.7, 6105.6, 6253.0, 6416.1, 6271.4, 6396.1],
    'ISTAT kWh per abitante 2015-2024': [5070, 4892, 4906, 4862, 4766, 4391, 4590, 4738, 4595, 4673],
    'gas milioni di m3 2015-2024': [1030.3, 1029.7, 1024.9, 1036.3, 1007.5, 996.9, 1063.1, 921.8, 837.8, 882.4],
    'ISTAT (GWh da tep/86) uguale a Tav 6.3 GWh 2018-2024 (tolleranza 0,05)': True,
    'ISTAT (gas da tep) uguale a Tav 6.4 2018-2024 (tolleranza 0,05)': True,
    'ISTAT uguale al dataset del Comune ds1537 2015-2018 (tolleranza 0,05)': True,
    'ds1537 2014 contro ISTAT attuale': (6500.8, 6522.2),
    'salto 2009-2010 Milano: elettricita (%), gas (%), domestico (%)': (-13, 41, 0),
    'A2A su ISTAT (%): 2019, 2020': (6.6, 4.8),
    'ISTAT 2020 su 2019 (%) e A2A 2020 su 2019 (%)': (-8.6, -10.1),
    'Milano kWh per abitante 2015-2024: variazione %': -7.8,
    'Milano: posto per kWh per abitante nel 2024 tra le 14': 3,
    'Milano: quota non domestico 2022 (%)': 74,
    'ds523 2011: elettricita domestica kWh, acqua domestica m3, litri al giorno': (1196.1, 83.1, 228),
    'acqua Milano 2018, 2020, 2022, 2024: immessa l/ab/g': [426.0, 399.0, 413.0, 403.0],
    'acqua Milano: erogata l/ab/g': [365.0, 346.0, 358.0, 358.0],
    'acqua Milano: perdite % dichiarate': [14.3, 13.5, 13.4, 11.1],
    'acqua Milano: perdite % ricalcolate da immessa ed erogata': [14.3, 13.5, 13.4, 11.1],
    'acqua Milano: domestica l/ab/g 2020, 2022, 2024': [265.0, 274.0, 272.0],
    'acqua Milano 2024: immessa, erogata, domestica (migliaia di m3)': (201950.0, 179603.0, 136157.0),
    'acqua Milano 2018: dataset del Comune ds1571 uguale a Istat': True,
    'acqua: perdite 2024 Milano contro mediana delle altre 13': (11.1, 38.0),
    'acqua: domestica 2024, Milano contro mediana delle altre 13': (272.0, 143.0),
    'acqua: citta con la perdita piu bassa nel 2018 e nel 2024': ('Milano', 'Milano'),
    'acqua: citta (su 14) con perdite in calo 2018-2024': 11,
    'vibrazioni: lockdown giorno su marzo 2019 e Ferragosto feriali su marzo 2019 (%)': (-27, -19),
    # --- novembre 2026: gas, settori Terna, lampade
    'gas: feriali usati, soglia (C), base estiva (Mmc/giorno), Mmc per grado (3 decimali)': (507, 19.0, 0.8, 0.443),
    'gas: R2 (2 decimali)': 0.92,
    'gas: intervallo bootstrap Mmc per grado (3 decimali) e soglia': ((0.407, 0.474), (18.5, 20.0)),
    'gas: stabilita, soglia e Mmc per grado di ogni scelta': [(507, 19.0, 0.443), (253, 19.0, 0.448), (254, 19.0, 0.439), (418, 19.5, 0.432), (490, 19.0, 0.443), (507, 25.5, 0.341), (100, 19.0, 0.433), (124, 19.0, 0.41), (731, 19.0, 0.436)],
    'gas: basi (Mmc) feriali, sabati, domeniche e feste': (0.8, 0.76, 0.7),
    'gas: fasce di temperatura media dei feriali, n e mediana (Mmc)': [(46, 7.47), (98, 6.07), (117, 3.99), (88, 1.12), (158, 0.77)],
    'gas: mediane con temperatura media sotto 8 gradi: feriali, sabati, domeniche e feste': (6.71, 6.32, 6.3),
    'gas: somme annue A2A (milioni di Smc)': (1150.4, 1146.7),
    'gas: A2A su ISTAT (%), 2019 e 2020': (14.2, 15.0),
    'gas: 2020 su 2019 (%), A2A e ISTAT': (-0.3, -1.1),
    'gas: giorno piu basso e piu alto': ('2020-08-15', '2019-02-01'),
    'gas: righe con mezzi Smc (16-19 aprile 2020)': 4,
    'Terna: anni 2000-2024 senza buchi': True,
    'Terna: totale Milano+Monza 2000, 2008, 2024 (GWh)': (19448, 21977, 20182),
    'Terna: anno del massimo': 2008,
    'Terna: 2009 Milano (che comprende Monza); 2010 Milano e Monza': (21132, 17257, 4259),
    'Terna: 2000 industria, servizi, case': (8782, 6202, 4414),
    'Terna: 2018 industria, servizi, case': (6478, 9818, 4786),
    'Terna: 2019 industria, servizi, case': (6961, 9091, 4848),
    'Terna: variazione 2018-2019 servizi, industria, case, totale (%)': (-7, 7, 1, -1),
    'Terna: 2020 e 2024 totale (GWh)': (19644, 20182),
    'Terna provincia di Milano uguale a ISTAT Tav 9.1: 2017-2024 entro 0,5 GWh, 2018-2024 entro 0,05': (True, True),
    'Terna contro ISTAT Tav 9.1: 2017 e 2024 (GWh)': (16686.8, 16687.2, 15971.3, 15971.3),
    'LED: anni 2002-2020 senza buchi': True,
    'LED: 2002, 2013, 2014, 2020 (tradizionali, LED)': [(113277, 0), (141963, 0), (65503, 77774), (1557, 151409)],
    'LED: totale lampade 2002, 2013, 2014, 2020': [113277, 141963, 143277, 152966],
    'LED: il totale non scende mai, i LED non scendono mai': (True, True),
    'LED: quota LED 2014 e 2020 (%)': (54.3, 99.0),
    'LED: variazione annua massima del totale (lampade) e anno': (4460, 2003),
}


def scrivi(dest, R, C, caldo, giorni, ann, citta_e, mil, citta_a, ago, vib, nuovi):
    scatter = []
    for i, r in enumerate(R):
        if not r['feriale']:
            continue
        if r['escl'] == '':
            c = 0 if r['anno'] == 2019 else 1
        else:
            c = {'pausa di agosto': 2, 'lockdown e riaperture 2020': 3, 'feste di fine anno': 4}[r['escl']]
        scatter.append([i, c])
    ago_righe, ago_mis, ago_prev, ago_diff = ago
    E = C['energia']
    pop = {a: E['Milano']['tep'][str(a)] / (E['Milano']['tep100'][str(a)] / 100.0) for a in range(2015, 2025)}      # abitanti impliciti
    for x in ann:
        x['dom_kwh_ab'] = round(x['dom_gwh'] * 1e6 / pop[x['anno']])
    A = {x['anno']: x for x in ann}
    m = caldo['modelli']['tmax']
    mm = caldo['modelli']['tmean']
    pagina = dict(
        data_scarico=DATA_SCARICO,
        data_scarico_nuovi=DATA_SCARICO_NUOVI,
        tep_per_gwh=TEP_PER_GWH,
        giornaliero=dict(
            inizio=R[0]['data'], gwh=[r['gwh'] for r in R], gas=[round(r['gas'], 3) for r in R], tmax=[r1(r['tmax']) for r in R], tmean=[r1(r['tmean']) for r in R],
            tipo=''.join({'feriale': 'f', 'sabato': 's', 'domenica': 'd', 'festivo': 'h'}[r['tipo']] for r in R),
            somma=giorni['somma'], massimo=giorni['massimo'], minimo=giorni['minimo'], posto_tmax_massimo=giorni['posto_tmax_massimo'], n_giorni=len(R),
            lockdown=[LOCK_DAL, LOCK_AL], agosto=['2019-' + AGO_DAL, '2019-' + AGO_AL, '2020-' + AGO_DAL, '2020-' + AGO_AL],
            feriali_lug2019=giorni['feriali_lug2019'], feriali_gen2019=giorni['feriali_gen2019'], feriali_lug2020=giorni['feriali_lug2020'], feriali_gen2020=giorni['feriali_gen2020'], top10=giorni['top10']),
        caldo=dict(
            n_feriali=caldo['n_feriali_totali'], n_base=caldo['n_base'], n_2019=caldo['n_2019'], n_2020=caldo['n_2020'], esclusi=caldo['esclusi'], n_vicine=caldo['n_vicine'],
            tmax=dict(soglia_caldo=m['T0'], soglia_freddo=m['T1'], per_grado_caldo=round(m['caldo'], 2), per_grado_freddo=round(m['freddo'], 2),
                      boot_caldo=[round(x, 2) for x in m['boot']['caldo']], boot_soglia_caldo=m['boot']['T0'], boot_freddo=[round(x, 2) for x in m['boot']['freddo']],
                      boot_soglia_freddo=m['boot']['T1'], r2=round(m['r2'], 2)),
            tmean=dict(soglia_caldo=mm['T0'], soglia_freddo=mm['T1'], per_grado_caldo=round(mm['caldo'], 2), per_grado_freddo=round(mm['freddo'], 2),
                       boot_caldo=[round(x, 2) for x in mm['boot']['caldo']], r2=round(mm['r2'], 2)),
            r2_senza_temperatura=round(caldo['r2_senza_temperatura'], 2), corr=round(caldo['corr_tmax'], 2), corr_sopra_soglia=round(caldo['corr_tmax_sopra_soglia'], 2),
            anno2020=round(m['anno2020'], 2), curva=caldo['curva'], scatter=scatter, fasce=caldo['fasce'], domeniche=caldo['domeniche'],
            sensibilita=[dict(nome=x['nome'], col=x['col'], n=x['n'], soglia=x['T0'], per_grado=round(x['caldo'], 2)) for x in caldo['sensibilita']]),
        lockdown=dict(
            feriali_marzo2019=giorni['feriali_marzo2019'], n_marzo2019=giorni['n_marzo2019'], feriali_feb2020=giorni['feriali_feb2020'], n_feb2020=giorni['n_feb2020'],
            feriali_lock=giorni['feriali_lock'], dom_marzo2019=giorni['dom_marzo2019'], dom_lock=giorni['dom_lock'],
            var_marzo2019=pct(giorni['feriali_lock'], giorni['feriali_marzo2019']), var_feb2020=pct(giorni['feriali_lock'], giorni['feriali_feb2020']),
            var_dom=pct(giorni['dom_lock'], giorni['dom_marzo2019']),
            vibrazioni_giorno=vib['giornata']['rispetto_marzo2019']['giorno'], vibrazioni_ferragosto=vib['ferragosto']['rispetto_marzo2019']['feriali']),
        ferragosto=dict(giorni=giorni['ferragosto'], tmax_media=giorni['ferragosto_tmax_media'], previsto=ago_righe, misurato_mediana=ago_mis, previsto_mediana=ago_prev, differenza=ago_diff,
                        feriali_marzo2019=giorni['feriali_marzo2019'], dom_marzo2019=giorni['dom_marzo2019'], sett_feriali=giorni['ferragosto_sett'], sett_var=giorni['ferragosto_sett_var']),
        annuale=dict(serie=ann, citta=citta_e, gwh_2014_istat=round(E['Milano']['tep']['2014'] / TEP_PER_GWH, 1), gwh_2014_comune=C['ds1537']['2014'],
                     a2a_su_istat={'2019': round(100 * (giorni['somma']['2019'] / A[2019]['gwh'] - 1), 1), '2020': round(100 * (giorni['somma']['2020'] / A[2020]['gwh'] - 1), 1)},
                     var_2020_istat=round(100 * (A[2020]['gwh'] / A[2019]['gwh'] - 1), 1), var_2020_a2a=round(100 * (giorni['somma']['2020'] / giorni['somma']['2019'] - 1), 1),
                     salto_2009_2010=dict(elettricita=pct(E['Milano']['tep']['2010'], E['Milano']['tep']['2009']), gas=pct(E['Milano']['gas_tep']['2010'], E['Milano']['gas_tep']['2009']),
                                          domestico=pct(E['Milano']['dom_tep']['2010'], E['Milano']['dom_tep']['2009']), non_domestico=pct(E['Milano']['nondom_tep']['2010'], E['Milano']['nondom_tep']['2009']),
                                          n_comuni_confrontati=C['salto_2009_2010_comuni']['n_comuni'], altri_con_lo_stesso_salto=len(C['salto_2009_2010_comuni']['el_meno10_gas_piu20']) - 1),
                     ds523=dict(anno=2011, kwh_domestico=C['ds523']['2011']['Energia elettrica per uso domestico'], acqua_m3=C['ds523']['2011']['Acqua fatturata per uso domestico'],
                                acqua_litri_giorno=round(C['ds523']['2011']['Acqua fatturata per uso domestico'] * 1000 / 365)),
                     quota_non_domestico_2022=round(100 * A[2022]['nondom_gwh'] / A[2022]['gwh'])),
        acqua=dict(milano=mil, citta=citta_a),
        gas=dict(n_feriali=nuovi['gas']['n_feriali'], soglia=nuovi['gas']['principale']['T1'], base=round(nuovi['gas']['principale']['base'], 3),
                 per_grado=round(nuovi['gas']['principale']['per_grado'], 3), boot_per_grado=[round(x, 3) for x in nuovi['gas']['principale']['boot_per_grado']],
                 boot_soglia=nuovi['gas']['principale']['boot_soglia'], r2=round(nuovi['gas']['principale']['r2'], 2), curva=nuovi['gas']['curva'],
                 sensibilita=[dict(nome=x['nome'], n=x['n'], col=x['col'], soglia=x['T1'], base=round(x['base'], 3), per_grado=round(x['per_grado'], 3)) for x in nuovi['gas']['sensibilita']],
                 fasce=nuovi['gas']['fasce'], mediane_freddo=nuovi['gas']['mediane_freddo'], somma=nuovi['gas']['somma'],
                 istat={'2019': A[2019]['gas_mm3'], '2020': A[2020]['gas_mm3']},
                 a2a_su_istat={a: round(100 * (nuovi['gas']['somma'][a] / A[int(a)]['gas_mm3'] - 1), 1) for a in ('2019', '2020')},
                 var_2020_a2a=round(100 * (nuovi['gas']['somma']['2020'] / nuovi['gas']['somma']['2019'] - 1), 1), var_2020_istat=round(100 * (A[2020]['gas_mm3'] / A[2019]['gas_mm3'] - 1), 1)),
        settori=dict(serie=nuovi['settori'], rottura=[2018, 2019]),
        led=nuovi['led'],
        csv=dict(nome='consumi_giornalieri.csv', righe=len(R)))
    os.makedirs(dest, exist_ok=True)
    tmp = os.path.join(dest, 'consumi_giornalieri.csv.tmp')
    with open(tmp, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['data', 'giorno', 'gwh_a2a', 'tmin_c', 'tmax_c', 'tmedia_c', 'fonte_temperatura', 'tipo_giorno', 'usato_per_il_caldo', 'motivo_esclusione', 'gas_smc_a2a'])
        for r in R:
            w.writerow([r['data'], ['lunedi', 'martedi', 'mercoledi', 'giovedi', 'venerdi', 'sabato', 'domenica'][r['wd']], r['gwh'], r['tmin'], r['tmax'], r['tmean'], r['fonte'],
                        r['tipo'], 1 if r['escl'] == '' else 0, r['escl'], (lambda v: int(v) if v == int(v) else v)(round(r['gas'] * 1e6, 1))])
    os.replace(tmp, os.path.join(dest, 'consumi_giornalieri.csv'))
    tmp = os.path.join(dest, 'pagina.json.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(pagina, f, ensure_ascii=False, separators=(',', ':'), default=float)
    os.replace(tmp, os.path.join(dest, 'pagina.json'))
    print('Tutti i controlli tornano. Scritti pagina.json e consumi_giornalieri.csv (%d righe) in %s' % (len(R), dest))


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]))
