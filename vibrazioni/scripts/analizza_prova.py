# Confronta i periodi di prova a partire dal file orario.
# Uso: python analizza_prova.py <prova_oraria.csv>
import csv, statistics as st, sys
import datetime as dt

PERIODI = {
    'normale_2019': ('2019-03-25', 7),
    'prima_2020': ('2020-02-17', 7),
    'lockdown_2020': ('2020-03-23', 7),
}


def carica(p):
    with open(p, encoding='utf-8') as f:
        return [dict(t=dt.datetime.fromisoformat(r['ora_locale']), c=float(r['citta_nm_s']), k=float(r['controllo_nm_s']), n=int(r['finestre'])) for r in csv.DictReader(f)]


def med(righe, campo='c'):
    return round(st.median(r[campo] for r in righe), 2) if righe else None


def main(p):
    R = carica(p)
    print('ore totali', len(R), 'ore incomplete', sum(r['n'] < 6 for r in R))
    ris = {}
    for nome, (ini, n) in PERIODI.items():
        a = dt.date.fromisoformat(ini)
        b = a + dt.timedelta(days=n)
        Q = [r for r in R if a <= r['t'].date() < b]
        feriali = [r for r in Q if r['t'].weekday() < 5]
        giorno = [r for r in feriali if 8 <= r['t'].hour < 19]
        notte = [r for r in feriali if 1 <= r['t'].hour < 5]
        domenica = [r for r in Q if r['t'].weekday() == 6 and 8 <= r['t'].hour < 19]
        ris[nome] = dict(ore=len(Q), giorno=med(giorno), notte=med(notte), domenica=med(domenica), controllo=med(Q, 'k'))
        print(nome, ris[nome], 'giorno/notte', round(med(giorno) / med(notte), 2))
        print('  per ora, feriali:', [med([r for r in feriali if r['t'].hour == h]) for h in range(24)])
    for base in ('normale_2019', 'prima_2020'):
        for k in ('giorno', 'notte', 'domenica', 'controllo'):
            print('lockdown rispetto a', base, k, '%+.0f%%' % (100 * (ris['lockdown_2020'][k] / ris[base][k] - 1)))
    print('--- Capodanno, ora per ora')
    for r in R:
        if dt.datetime(2023, 12, 30, 20) <= r['t'].replace(tzinfo=None) < dt.datetime(2023, 12, 31, 4) or dt.datetime(2023, 12, 31, 20) <= r['t'].replace(tzinfo=None) < dt.datetime(2024, 1, 1, 4):
            print(r['t'].strftime('%d/%m %H'), r['c'], r['k'], r['n'])
    g = [r for r in R if r['t'].date() in (dt.date(2023, 12, 30), dt.date(2024, 1, 1))]
    print('30/12 giorno', med([r for r in g if r['t'].date() == dt.date(2023, 12, 30) and 8 <= r['t'].hour < 19]), '1/1 giorno', med([r for r in g if r['t'].date() == dt.date(2024, 1, 1) and 8 <= r['t'].hour < 19]))


if __name__ == '__main__':
    main(sys.argv[1])
