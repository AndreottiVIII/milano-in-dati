# Uso: python analizza_ferragosto_sansiro.py <cartella_out>
import collections, csv, math, os, statistics as st, sys
import datetime as dt


def carica(p):
    with open(p, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def ferragosto(out):
    blocchi = collections.defaultdict(list)
    for r in carica(os.path.join(out, 'minuti_ferragosto.csv')):
        t = dt.datetime.fromisoformat(r['minuto'])
        blocchi[t.replace(minute=t.minute - t.minute % 10, second=0, microsecond=0)].append((float(r['citta']), float(r['controllo'])))
    ore = collections.defaultdict(list)
    for t, v in blocchi.items():
        if len(v) >= 8:
            ore[t.replace(minute=0)].append((math.sqrt(st.mean(a * a for a, _ in v)), math.sqrt(st.mean(b * b for _, b in v))))
    oraria = {t: (st.median(a for a, _ in v), st.median(b for _, b in v)) for t, v in ore.items()}
    print('=== Ferragosto 2019, ora per ora (fascia citta), mediana')
    for g in range(11, 20):
        d = dt.date(2019, 8, g)
        giorno = [v[0] for t, v in oraria.items() if t.date() == d and 8 <= t.hour < 19]
        notte = [v[0] for t, v in oraria.items() if t.date() == d and 1 <= t.hour < 5]
        ctrl = [v[1] for t, v in oraria.items() if t.date() == d]
        if giorno:
            print(d, d.strftime('%a'), 'giorno', round(st.median(giorno)), 'notte', round(st.median(notte)) if notte else None, 'controllo', round(st.median(ctrl)), 'ore', len(giorno))
    sett = [(t, v) for t, v in oraria.items() if dt.date(2019, 8, 12) <= t.date() <= dt.date(2019, 8, 18)]
    fer = [v[0] for t, v in sett if t.weekday() < 5 and 8 <= t.hour < 19]
    no = [v[0] for t, v in sett if t.weekday() < 5 and 1 <= t.hour < 5]
    dom = [v[0] for t, v in sett if t.weekday() == 6 and 8 <= t.hour < 19]
    print('settimana feriali giorno', round(st.median(fer)), 'notte', round(st.median(no)), 'domenica', round(st.median(dom)))
    print('rispetto a marzo 2019 (604, 223, 431): %+.0f%% %+.0f%% %+.0f%%' % (100 * (st.median(fer) / 604 - 1), 100 * (st.median(no) / 223 - 1), 100 * (st.median(dom) / 431 - 1)))


GOL = {
    '2023-05-10': [('Dzeko 8', 21, 8), ('Mkhitaryan 11', 21, 11)],
    '2023-05-16': [('Lautaro 74', 22, 32)],
    '2025-05-06': [('Lautaro 21', 21, 21), ('Calhanoglu 45+1', 21, 46), ('Acerbi 90+3', 22, 51), ('Frattesi 99', 23, 7)],
}
# Il 3/5/2023 scartato: quella sera Milan-Cremonese si giocava a San Siro.
CONFRONTI = {'2023-05-10': ['2023-05-17'], '2023-05-16': ['2023-05-09', '2023-05-23'], '2025-05-06': ['2025-04-29', '2025-05-13']}


def partite(out):
    D = collections.defaultdict(dict)
    for r in carica(os.path.join(out, 'minuti_partite.csv')):
        t = dt.datetime.fromisoformat(r['minuto'])
        D[r['giorno']][(t.hour, t.minute)] = (float(r['folla']), float(r['citta']), float(r['controllo']))
    fascia = lambda g, a, b, i: [v[i] for (h, m), v in D[g].items() if a <= h * 60 + m < b]
    for g, conf in CONFRONTI.items():
        print('===', g, 'confronti', conf)
        for nome, a, b in (('18-19.30', 1080, 1170), ('19.30-21 arrivo', 1170, 1260), ('21-23 partita', 1260, 1380), ('23-24 uscita', 1380, 1440)):
            for i, banda in ((0, 'folla 1,5-4 Hz'), (1, 'citta 2-20 Hz')):
                x = st.median(fascia(g, a, b, i))
                c = [st.median(fascia(z, a, b, i)) for z in conf]
                print('%-18s %-15s partita %6.0f confronti %s  %+.0f%%' % (nome, banda, x, [round(z) for z in c], 100 * (x / st.mean(c) - 1)))
        serie = sorted((h * 60 + m, v[0]) for (h, m), v in D[g].items() if 1245 <= h * 60 + m < 1440)
        vals = [v for _, v in serie]
        finestre = [max(vals[i:i + 7]) for i in range(len(vals) - 6)]
        for nome, h, m in GOL[g]:
            c = h * 60 + m
            w = [v for t, v in serie if abs(t - c) <= 3]
            if w:
                print('gol %-16s max finestra %6.0f, piu alta del %.0f%% delle finestre della serata' % (nome, max(w), 100 * sum(x < max(w) for x in finestre) / len(finestre)))
        top = sorted(serie, key=lambda a: -a[1])[:8]
        print('minuti piu forti:', [('%02d:%02d' % (t // 60, t % 60), round(v)) for t, v in top])
        for z in conf:
            s = sorted(((h * 60 + m), v[0]) for (h, m), v in D[z].items() if 1245 <= h * 60 + m < 1440)
            print('  confronto', z, 'massimo', round(max(v for _, v in s)), 'mediana', round(st.median(v for _, v in s)))
        print('  questa serata massimo', round(max(vals)), 'mediana', round(st.median(vals)))


if __name__ == '__main__':
    ferragosto(sys.argv[1])
    partite(sys.argv[1])
