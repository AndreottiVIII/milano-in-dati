"""Prezzi dell'opera alla Scala, per anno: poltrona di platea e biglietto meno caro, in moneta dell'epoca e in euro del 2025.

Uso: python -I -X utf8 locandine_prezzi.py --cartella <risultati> --tavole <zip ISTAT> --lire <..._lire_letti.csv> --euro <..._euro_letti.csv>

I prezzi sono letti a vista sulle locandine: la lettura automatica sbaglia le colonne dei fogli vecchi e le cifre piccole di
quelli recenti. Campione: da 3 a 6 locandine per anno, titoli diversi, sera, sala principale, senza 7 dicembre e spettacoli
per bambini. Dal 1944 al 2001 un solo prezzo meno caro per poster quando si vede. Il valore dell'anno è la mediana.
In euro 2025: coefficienti ISTAT "Il valore della moneta in Italia dal 1861 al 2025", tavola 2025. Le lire si dividono per 1936,27.
"""
import argparse, collections as C, csv, io, json, os, statistics as ST, zipfile
import openpyxl


def coefficienti(zp):
    z = zipfile.ZipFile(zp)
    nome = [n for n in z.namelist() if n.endswith('2022-2024_25.xlsx')][0]
    ws = openpyxl.load_workbook(io.BytesIO(z.read(nome)), read_only=True, data_only=True)['2025']
    co = {}
    righe = list(ws.iter_rows(values_only=True))
    ini = next(i for i, r in enumerate(righe) if r and any(c == 1861 for c in r))
    cols = [(j, v) for j, v in enumerate(righe[ini]) if isinstance(v, int) and v in (1861, 1901, 1941, 1981, 2021)]
    for i in range(0, 40):
        if ini + i >= len(righe):
            break
        r = righe[ini + i]
        for j, base in cols:
            if j + 1 < len(r) and isinstance(r[j + 1], (int, float)):
                co[base + i] = float(r[j + 1])
    return co


def leggi(p, ca, cb):
    d = C.defaultdict(lambda: {'p': [], 'b': []})
    for x in csv.DictReader(open(p, encoding='utf-8-sig')):
        y = int(x['locandina'][:4])
        if x[ca]:
            d[y]['p'].append(float(x[ca]))
        if x[cb]:
            d[y]['b'].append(float(x[cb]))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cartella', required=True)
    ap.add_argument('--tavole', required=True)
    ap.add_argument('--lire', required=True)
    ap.add_argument('--euro', required=True)
    a = ap.parse_args()
    co = coefficienti(a.tavole)
    serie = []
    for moneta, d in (('L', leggi(a.lire, 'platea_lire', 'meno_caro_lire')), ('E', leggi(a.euro, 'platea_euro', 'meno_caro_euro'))):
        for y in sorted(d):
            v = d[y]
            if not v['p']:
                continue
            c = co.get(y, 1.0)  # per il 2026 ISTAT non dà ancora un coefficiente: il prezzo resta com'è
            f = (lambda q: q * c / 1936.27) if moneta == 'L' else (lambda q: q * c)
            p = ST.median(v['p'])
            b = ST.median(v['b']) if v['b'] else None
            serie.append({'y': y, 'm': moneta, 'p': p, 'b': b, 'p_lo': min(v['p']), 'p_hi': max(v['p']), 'n': len(v['p']),
                          'p25': round(f(p)), 'b25': round(f(b), 1) if b else None, 'lo25': round(f(min(v['p']))), 'hi25': round(f(max(v['p'])))})
    with open(os.path.join(a.cartella, 'prezzi_serie.csv'), 'w', encoding='utf-8-sig', newline='') as fh:
        w = csv.DictWriter(fh, fieldnames=list(serie[0]))
        w.writeheader()
        w.writerows(serie)
    json.dump(serie, open(os.path.join(a.cartella, 'prezzi_serie.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    for s in serie:
        print(s['y'], s['m'], s['p'], s['b'], f"[{s['p_lo']}-{s['p_hi']}]", 'n', s['n'], '| 2025:', s['p25'], s['b25'], f"({s['lo25']}-{s['hi25']})")


if __name__ == '__main__':
    main()
