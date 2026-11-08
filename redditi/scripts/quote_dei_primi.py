"""Quota dei redditi dichiarati che va al primo X% dei contribuenti milanesi (X = 1..50), anno per anno.

Dati: docs/redditi/data/classi_milano.csv (quote per classe MEF) e serie_citta.csv (reddito medio nominale).
Metodo:
- si sommano le classi dall'alto;
- nella classe piu' alta (oltre 120.000 euro nominali) si usa una coda di Pareto: alpha = media/(media-120.000),
  con la media della classe ricavata da quota di reddito, quota di contribuenti e reddito medio;
- nelle altre classi, se il taglio cade dentro, la parte proporzionale (redditi uguali dentro la classe).
Scrive docs/redditi/data/quote_dei_primi.json.
"""
import csv, json, os
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(R, 'docs', 'redditi', 'data')
media = {int(r['anno_imposta']): float(r['media_nominale']) for r in csv.DictReader(open(os.path.join(D, 'serie_citta.csv'), encoding='utf8')) if r['unita'] == 'Milano'}
out = {}
for r in csv.DictReader(open(os.path.join(D, 'classi_milano.csv'), encoding='utf8')):
    a = int(r['anno_imposta'])
    qc = [float(r[k]) for k in r if k.startswith('quota_contribuenti')]
    qr = [float(r[k]) for k in r if k.startswith('quota_reddito')]
    m_top = qr[-1] / qc[-1] * media[a]
    alpha = m_top / (m_top - 120000)
    def quota(p):
        if p <= qc[-1]:
            return qr[-1] * (p / qc[-1]) ** (1 - 1 / alpha)
        tot, need = qr[-1], p - qc[-1]
        for c, y in zip(reversed(qc[:-1]), reversed(qr[:-1])):
            if c >= need:
                return tot + y * need / c
            tot += y; need -= c
        return tot
    out[a] = {'alpha': round(alpha, 3), 'quote': [round(quota(x / 100) * 100, 2) for x in range(1, 51)]}
json.dump({'nota': 'quote[i] = % dei redditi dichiarati che va al primo (i+1)% dei contribuenti', 'anni': out},
          open(os.path.join(D, 'quote_dei_primi.json'), 'w', encoding='utf8'), ensure_ascii=False)
for a in (2000, 2010, 2024):
    q = out[a]['quote']; print(a, 'alpha', out[a]['alpha'], '1%', q[0], '5%', q[4], '10%', q[9], '20%', q[19], '50%', q[49])
