# Costruisce i dati della pagina "Il respiro di Milano" a partire dai file in vibrazioni/out/.
# Ricalcola i numeri come fanno analizza_prova.py e analizza_ferragosto_sansiro.py e li confronta con
# quelli scritti in NOTE.md: se anche uno solo non coincide, il programma si ferma senza scrivere nulla.
# Uso: python -I -X utf8 build.py <radice del progetto>
# Scrive: docs/vibrazioni/data/pagina.json e docs/vibrazioni/data/vibrazioni_orarie.csv
import collections, csv, json, math, os, statistics as st, sys
import datetime as dt

DATA_SCARICO = '2026-11-03'
STAZIONE = {'codice': 'IV.MILN', 'canale': 'HHZ', 'lat': 45.4803, 'lon': 9.2321}
# Coordinate dello stadio: Wikipedia in italiano (voce "Stadio Giuseppe Meazza", API, 3/11/2026)
# e OpenStreetMap (way 218520505, Nominatim, 3/11/2026). Servono solo per la distanza in linea d'aria.
STADIO_WIKIPEDIA = (45.478056, 9.123889)
STADIO_OSM = (45.4782003, 9.1239640)

PERIODI = [
    ('marzo2019', 'Marzo 2019', '2019-03-25', 7),
    ('febbraio2020', 'Febbraio 2020', '2020-02-17', 7),
    ('lockdown2020', 'Lockdown, marzo 2020', '2020-03-23', 7),
]
GIORNI = ['lun', 'mar', 'mer', 'gio', 'ven', 'sab', 'dom']

# (partita, data, giocatore, minuto scritto, ora, minuto dell'ora, orario stimato?)
# Gli orari del secondo tempo e dei supplementari sono stimati dal minuto di gioco.
PARTITE = [
    ('2023-05-10', 'Milan-Inter', ['2023-05-17']),
    ('2023-05-16', 'Inter-Milan', ['2023-05-09', '2023-05-23']),
    ('2025-05-06', 'Inter-Barcellona', ['2025-04-29', '2025-05-13']),
]
GOL = {
    '2023-05-10': [('Dzeko', "8'", 21, 8, False), ('Mkhitaryan', "11'", 21, 11, False)],
    '2023-05-16': [('Lautaro', "74'", 22, 32, True)],
    '2025-05-06': [('Lautaro', "21'", 21, 21, False), ('Calhanoglu', "45'+1", 21, 46, False),
                   ('Acerbi', "90'+3", 22, 51, True), ('Frattesi', "99'", 23, 7, True)],
}
# Il 3/5/2023 non e' tra i confronti: quella sera Milan-Cremonese si giocava a San Siro.

ERRORI = []


def verifica(nome, calcolato, atteso):
    ok = calcolato == atteso
    print(('OK      ' if ok else 'ERRORE  ') + nome + ': calcolato ' + repr(calcolato) + ', atteso ' + repr(atteso))
    if not ok:
        ERRORI.append(nome)


def pct(a, b):
    return int(round(100 * (a / b - 1)))


def carica(p):
    with open(p, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def med(v):
    return round(st.median(v), 2)


# ---------- 1. curva sulle 24 ore e settimane di confronto ----------
def oraria(out):
    R = []
    for r in carica(os.path.join(out, 'prova_oraria.csv')):
        R.append(dict(t=dt.datetime.fromisoformat(r['ora_locale']), c=float(r['citta_nm_s']), k=float(r['controllo_nm_s']), n=int(r['finestre'])))
    return R


def giornata(R):
    ris = {}
    periodi = []
    for pid, nome, ini, n in PERIODI:
        a = dt.date.fromisoformat(ini)
        b = a + dt.timedelta(days=n)
        Q = [r for r in R if a <= r['t'].date() < b]
        fer = [r for r in Q if r['t'].weekday() < 5]
        giorno = med([r['c'] for r in fer if 8 <= r['t'].hour < 19])
        notte = med([r['c'] for r in fer if 1 <= r['t'].hour < 5])
        dom = med([r['c'] for r in Q if r['t'].weekday() == 6 and 8 <= r['t'].hour < 19])
        ctrl = med([r['k'] for r in Q])
        ore = [med([r['c'] for r in fer if r['t'].hour == h]) for h in range(24)]
        ris[pid] = dict(giorno=giorno, notte=notte, domenica=dom, controllo=ctrl)
        periodi.append(dict(id=pid, nome=nome, dal=a.isoformat(), al=(b - dt.timedelta(days=1)).isoformat(), ore=ore, **ris[pid]))
    var = {}
    for base, chiave in (('marzo2019', 'rispetto_marzo2019'), ('febbraio2020', 'rispetto_febbraio2020')):
        var[chiave] = {k: pct(ris['lockdown2020'][k], ris[base][k]) for k in ('giorno', 'notte', 'domenica', 'controllo')}
    return periodi, ris, var


# ---------- 2. Ferragosto ----------
def ferragosto(out):
    blocchi = collections.defaultdict(list)
    for r in carica(os.path.join(out, 'minuti_ferragosto.csv')):
        t = dt.datetime.fromisoformat(r['minuto'])
        blocchi[t.replace(minute=t.minute - t.minute % 10, second=0, microsecond=0)].append((float(r['citta']), float(r['controllo'])))
    ore = collections.defaultdict(list)
    for t, v in blocchi.items():
        if len(v) >= 8:
            ore[t.replace(minute=0)].append((math.sqrt(st.mean(a * a for a, _ in v)), math.sqrt(st.mean(b * b for _, b in v))))
    orarie = {t: (st.median(a for a, _ in v), st.median(b for _, b in v), len(v)) for t, v in ore.items()}
    giorni = []
    for g in range(11, 20):
        d = dt.date(2019, 8, g)
        gi = [v[0] for t, v in orarie.items() if t.date() == d and 8 <= t.hour < 19]
        no = [v[0] for t, v in orarie.items() if t.date() == d and 1 <= t.hour < 5]
        giorni.append(dict(data=d.isoformat(), sett=GIORNI[d.weekday()], valore=round(st.median(gi)), notte=round(st.median(no)) if no else None, ore=len(gi)))
    sett = [(t, v) for t, v in orarie.items() if dt.date(2019, 8, 12) <= t.date() <= dt.date(2019, 8, 18)]
    fer = round(st.median([v[0] for t, v in sett if t.weekday() < 5 and 8 <= t.hour < 19]))
    no = round(st.median([v[0] for t, v in sett if t.weekday() < 5 and 1 <= t.hour < 5]))
    dom = round(st.median([v[0] for t, v in sett if t.weekday() == 6 and 8 <= t.hour < 19]))
    return giorni, dict(feriali=fer, notte=no, domenica=dom), orarie


# ---------- 3. San Siro ----------
def distanza_km(a, b):
    R = 6371.0088
    p = math.radians
    x = math.sin(p(b[0] - a[0]) / 2) ** 2 + math.cos(p(a[0])) * math.cos(p(b[0])) * math.sin(p(b[1] - a[1]) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(x))


def sansiro(out):
    D = collections.defaultdict(dict)
    for r in carica(os.path.join(out, 'minuti_partite.csv')):
        t = dt.datetime.fromisoformat(r['minuto'])
        D[r['giorno']][(t.hour, t.minute)] = (float(r['folla']), float(r['citta']), float(r['controllo']))
    fascia = lambda g, a, b, i: [v[i] for (h, m), v in D[g].items() if a <= h * 60 + m < b]
    risultati = []
    for g, nome, conf in PARTITE:
        for z in conf:
            if z not in D:
                raise SystemExit('serata di confronto mancante: ' + z)
        diff = {}
        for chiave, a, b in (('partita', 1260, 1380), ('uscita', 1380, 1440)):
            for i, banda in ((0, 'folla'), (1, 'citta')):
                x = st.median(fascia(g, a, b, i))
                c = [st.median(fascia(z, a, b, i)) for z in conf]
                diff[chiave + '_' + banda] = pct(x, st.mean(c))
        serie = sorted((h * 60 + m, v[0]) for (h, m), v in D[g].items() if 1245 <= h * 60 + m < 1440)
        vals = [v for _, v in serie]
        finestre = [max(vals[i:i + 7]) for i in range(len(vals) - 6)]
        gol = []
        for chi, minuto, h, m, stimato in GOL[g]:
            c = h * 60 + m
            w = [v for t, v in serie if abs(t - c) <= 3]
            gol.append(dict(chi=chi, minuto=minuto, ora='%02d:%02d' % (h, m), stimato=stimato, posto=int(round(100 * sum(x < max(w) for x in finestre) / len(finestre)))))
        top = max(serie, key=lambda a: a[1])
        dentro = any(abs(top[0] - (h * 60 + m)) <= 3 for _, _, h, m, _ in GOL[g])
        massimi_conf = []
        for z in conf:
            s = [v[0] for (h, m), v in D[z].items() if 1245 <= h * 60 + m < 1440]
            massimi_conf.append(round(max(s)))
        risultati.append(dict(
            data=g, nome=nome, ora_inizio='21:00', confronti=conf, differenza=diff, gol=gol,
            minuto_piu_forte=dict(ora='%02d:%02d' % (top[0] // 60, top[0] % 60), valore=round(top[1]), vicino_a_un_gol=dentro),
            massimo_serata=round(max(vals)), massimi_confronti=massimi_conf))
    return risultati


# ---------- 4. giorni campione (salto di livello) ----------
def livello(out):
    P = []
    for r in carica(os.path.join(out, 'livello_campione.csv')):
        def num(x):
            try:
                v = float(x)
            except ValueError:
                return None
            return None if math.isnan(v) else round(v, 1)
        P.append(dict(data=r['data'], giorno=num(r['giorno_8_19_nm_s']), notte=num(r['notte_1_5_nm_s']), controllo=num(r['controllo_nm_s'])))
    return P


def main(radice):
    out = os.path.join(radice, 'vibrazioni', 'out')
    dest = os.path.join(radice, 'docs', 'vibrazioni', 'data')
    R = oraria(out)
    periodi, ris, var = giornata(R)
    fgiorni, fsett, forarie = ferragosto(out)
    partite = sansiro(out)
    punti = livello(out)

    # --- controlli contro NOTE.md ---
    print('--- controlli contro NOTE.md')
    ore_tot = len(R)
    incomplete = sum(r['n'] < 6 for r in R)
    verifica('ore totali', ore_tot, 771)
    verifica('ore incomplete', incomplete, 42)
    for pid, g, n, d, c in (('marzo2019', 604, 223, 431, 98), ('febbraio2020', 588, 222, 443, 276), ('lockdown2020', 442, 172, 344, 121)):
        r = ris[pid]
        verifica('tabella ' + pid, (round(r['giorno']), round(r['notte']), round(r['domenica']), round(r['controllo'])), (g, n, d, c))
    verifica('lockdown su marzo 2019', var['rispetto_marzo2019'], dict(giorno=-27, notte=-23, domenica=-20, controllo=24))
    verifica('lockdown su febbraio 2020', var['rispetto_febbraio2020'], dict(giorno=-25, notte=-23, domenica=-22, controllo=-56))
    h19 = periodi[0]['ore']
    verifica('ritmo 2019: minimo tra le 2 e le 3', h19.index(min(h19)) in (2, 3), True)
    verifica('ritmo 2019: minimo circa 175', round(min(h19)), 175)
    verifica('ritmo 2019: ore 4, 5, 6', (round(h19[4]), round(h19[5]), round(h19[6])), (269, 488, 607))

    verifica('Ferragosto: giorni 12-19', [g['valore'] for g in fgiorni[1:]], [514, 501, 506, 402, 447, 432, 418, 512])
    verifica('Ferragosto: ore per giorno', [g['ore'] for g in fgiorni], [11] * 9)
    verifica('Ferragosto: settimana', (fsett['feriali'], fsett['notte'], fsett['domenica']), (490, 204, 418))
    fvar = dict(feriali=pct(fsett['feriali'], 604), notte=pct(fsett['notte'], 223), domenica=pct(fsett['domenica'], 431))
    verifica('Ferragosto su marzo 2019', fvar, dict(feriali=-19, notte=-9, domenica=-3))
    verifica('Ferragosto: feriali piu del lockdown', fsett['feriali'] > round(ris['lockdown2020']['giorno']), True)
    verifica('riferimento marzo 2019 = 604', round(ris['marzo2019']['giorno']), 604)

    verifica('San Siro: differenze 21-23 (1,5-4 Hz e 2-20 Hz)', [(p['differenza']['partita_folla'], p['differenza']['partita_citta']) for p in partite], [(-3, 0), (-2, 5), (0, 1)])
    verifica('San Siro: uscita 23-24, fascia 2-20 Hz', [p['differenza']['uscita_citta'] for p in partite], [5, 14, -11])
    posti = [g['posto'] for p in partite for g in p['gol']]
    verifica('gol: posti tra 46 e 88', (min(posti), max(posti)), (46, 88))
    verifica('gol: Lautaro 2023 al 63', partite[1]['gol'][0]['posto'], 63)
    verifica('minuto piu forte mai vicino a un gol', [p['minuto_piu_forte']['vicino_a_un_gol'] for p in partite], [False, False, False])
    verifica('6/5/2025: minuto piu forte 20:49, 1955', (partite[2]['minuto_piu_forte']['ora'], partite[2]['minuto_piu_forte']['valore']), ('20:49', 1955))
    verifica('serate di confronto: stesso giorno della settimana, +/- 7 giorni', all(dt.date.fromisoformat(z).weekday() == dt.date.fromisoformat(p['data']).weekday() and abs((dt.date.fromisoformat(z) - dt.date.fromisoformat(p['data'])).days) == 7 for p in partite for z in p['confronti']), True)
    verifica('3/5/2023 non e un confronto', any('2023-05-03' in p['confronti'] for p in partite), False)

    d_wiki = distanza_km(( STAZIONE['lat'], STAZIONE['lon']), STADIO_WIKIPEDIA)
    d_osm = distanza_km((STAZIONE['lat'], STAZIONE['lon']), STADIO_OSM)
    verifica('distanza Wikipedia e OpenStreetMap entro 0,1 km', abs(d_wiki - d_osm) < 0.1, True)
    verifica('distanza circa 8 km (tra 8 e 9)', 8 <= d_wiki < 9, True)

    D = {p['data']: p for p in punti}
    verifica('livello 17/3/2021 = 644', round(D['2021-03-17']['giorno']), 644)
    verifica('livello 15/12/2021 = 1953', round(D['2021-12-15']['giorno']), 1953)
    verifica('livello 16/12/2020 = 782', round(D['2020-12-16']['giorno']), 782)
    dopo = [p['giorno'] for p in punti if p['data'] >= '2021-12-15']
    verifica('dopo il salto: da 1.860 a 2.200', (round(min(dopo), -1), round(max(dopo), -2)), (1860, 2200))
    verifica('tutti i giorni campione sono mercoledi', all(dt.date.fromisoformat(p['data']).weekday() == 2 for p in punti), True)
    verifica('11/12/2019 senza dati di notte', D['2019-12-11']['notte'], None)

    # Capodanno 2023-24: confronto ora per ora tra la notte del 31/12 e quella del 1/1
    per_ora = {r['t'].replace(tzinfo=None): r['c'] for r in R}
    cap = {}
    for h in (1, 2, 3):
        cap[h] = pct(per_ora[dt.datetime(2024, 1, 1, h)], per_ora[dt.datetime(2023, 12, 31, h)])
    verifica('Capodanno: dopo l\'una +18%, +41%, +27%', [cap[1], cap[2], cap[3]], [18, 41, 27])
    mezzanotte = dict(capodanno=round(per_ora[dt.datetime(2024, 1, 1, 0)]), notte_prima=round(per_ora[dt.datetime(2023, 12, 31, 0)]))
    verifica('Capodanno: mezzanotte senza scatto (entro 5%)', abs(pct(mezzanotte['capodanno'], mezzanotte['notte_prima'])) <= 5, True)

    if ERRORI:
        print('\nFALLITO: %d controlli non tornano (%s). Non scrivo nulla.' % (len(ERRORI), ', '.join(ERRORI)))
        sys.exit(1)

    # --- scrittura ---
    pagina = dict(
        data_scarico=DATA_SCARICO,
        stazione=STAZIONE,
        giornata=dict(
            periodi=[{**p, 'ore': [round(x, 1) for x in p['ore']]} for p in periodi],
            rispetto_marzo2019=var['rispetto_marzo2019'],
            rispetto_febbraio2020=var['rispetto_febbraio2020'],
            ore_minimo=[h for h in (2, 3)]),
        ferragosto=dict(giorni=fgiorni, riferimento_marzo2019=round(ris['marzo2019']['giorno']), riferimento_lockdown=round(ris['lockdown2020']['giorno']),
                        settimana=fsett, rispetto_marzo2019=fvar),
        sansiro=dict(
            distanza_km=round(d_wiki, 1),
            stadio=dict(wikipedia=list(STADIO_WIKIPEDIA), openstreetmap=list(STADIO_OSM), distanza_osm_km=round(d_osm, 1)),
            partite=partite,
            posto_gol_min=min(posti), posto_gol_max=max(posti)),
        livello=dict(punti=punti, dopo_min=min(dopo), dopo_max=max(dopo)),
        limiti=dict(ore_totali=ore_tot, ore_incomplete=incomplete,
                    capodanno=dict(dopo_l_una={str(h): cap[h] for h in (1, 2, 3)}, mezzanotte=mezzanotte)),
        csv=dict(nome='vibrazioni_orarie.csv'))

    def serie_di(t):
        d = t.date()
        if dt.date(2019, 3, 1) <= d <= dt.date(2019, 4, 30):
            return 'marzo_2019'
        if dt.date(2020, 2, 1) <= d <= dt.date(2020, 2, 29):
            return 'febbraio_2020'
        if dt.date(2020, 3, 1) <= d <= dt.date(2020, 3, 31):
            return 'marzo_2020'
        return 'capodanno_2023_24'

    righe = [(r['t'], r['c'], r['k'], r['n'], serie_di(r['t'])) for r in R]
    righe += [(t, v[0], v[1], v[2], 'agosto_2019') for t, v in forarie.items()]
    righe.sort(key=lambda a: a[0])
    os.makedirs(dest, exist_ok=True)
    tmp = os.path.join(dest, 'vibrazioni_orarie.csv.tmp')
    with open(tmp, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['ora_locale', 'fascia_citta_nm_s', 'fascia_controllo_nm_s', 'finestre_10min', 'periodo'])
        for t, c, k, n, s in righe:
            w.writerow([t.isoformat(), round(c, 1), round(k, 1), n, s])
    os.replace(tmp, os.path.join(dest, 'vibrazioni_orarie.csv'))
    pagina['csv']['righe'] = len(righe)
    tmp = os.path.join(dest, 'pagina.json.tmp')
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(pagina, f, ensure_ascii=False, indent=1)
    os.replace(tmp, os.path.join(dest, 'pagina.json'))
    print('\nTutti i controlli tornano. Scritti pagina.json e vibrazioni_orarie.csv (%d righe) in %s' % (len(righe), dest))
    print('Distanza stazione-stadio: %.2f km (Wikipedia), %.2f km (OpenStreetMap)' % (d_wiki, d_osm))


if __name__ == '__main__':
    main(os.path.abspath(sys.argv[1]))
