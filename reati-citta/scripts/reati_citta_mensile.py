"""Crea docs/reati-citta/data/mensile_provincia.json dal file mensile (delitti per mese, provincia di Milano e Italia)."""
import csv, json, os
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = os.path.join(R, 'docs', 'reati-citta', 'data', 'famiglia_stalking_mensile.csv')
out = {}
for r in csv.DictReader(open(src, encoding='utf-8')):
    t, a, y, m = r['tipo_codice'], r['codice_istat'], r['anno'], int(r['mese'])
    arr = out.setdefault(t, {}).setdefault(a, {}).setdefault(y, [None] * 12)
    arr[m - 1] = int(r['denunce'])
dst = os.path.join(R, 'docs', 'reati-citta', 'data', 'mensile_provincia.json')
json.dump(out, open(dst, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
for t in []:
    for a in out[t]:
        pass

# Dettaglio delle risposte "camminando al buio" per comune e anno: [sicuro, poco (non per niente), per niente, non esce mai, altre]
b = {}
src2 = os.path.join(R, 'docs', 'reati-citta', 'data', 'percezione_sicurezza_buio.csv')
for r in csv.DictReader(open(src2, encoding='utf-8')):
    sic = float(r['pct_molto_o_abbastanza_sicuro']); pn = float(r['pct_poco_o_per_niente_sicuro'])
    pxn = float(r['pct_per_niente_sicuro']); ne = float(r['pct_non_esce_mai_o_mai_da_solo'])
    b.setdefault(r['comune'], {})[r['anno']] = [sic, round(pn - pxn, 1), pxn, ne, round(max(0, 100 - sic - pn - ne), 1)]
json.dump(b, open(os.path.join(R, 'docs', 'reati-citta', 'data', 'buio_dettaglio.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(b), b['Milano'])
