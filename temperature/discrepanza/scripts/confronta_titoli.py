"""Confronta i numeri principali del sito tra due versioni dei dati (prima/dopo una correzione).
uso: python -I confronta_titoli.py DATI_A DATI_B OUTCSV
  DATI_A, DATI_B  cartelle con i JSON di statistiche.py (A = attuale, B = con correzione)
Scrive una tabella: voce, A, B, B-A. Voci: normali 1961-90 / 1991-2020 / 1981-2010 (media, massime, minime), tendenze
dal 1980 (C/secolo), 10 anni piu' caldi, mesi/estati piu' caldi, record giornalieri del calendario (quanti dal 2008 in poi,
quanti nel 2008-2016), record per mese del calendario, giorno piu' caldo, 2026 'finora', ultimi 20 anni."""
import sys, json, os
import pandas as pd

a, b, out = sys.argv[1:4]
L = lambda d, n: json.load(open(os.path.join(d, n), encoding='utf-8'))
rows = []


def add(voce, va, vb):
    try:
        diff = round(vb - va, 2)
    except TypeError:
        diff = '' if va == vb else 'cambia'
    rows.append({'voce': voce, 'attuale': va, 'corretta': vb, 'differenza': diff})


ca, cb = L(a, 'clima.json'), L(b, 'clima.json')
for na, nb in zip(ca['normali'], cb['normali']):
    for k in ('tmedia', 'tmax_media', 'tmin_media', 'gg_caldi', 'notti_tropicali', 'gg_gelo'):
        add(f"normale {na['periodo']} {k}", round(na[k], 2), round(nb[k], 2))
for ta, tb in zip(ca['tendenze'], cb['tendenze']):
    if ta['dal'] in (1950, 1980):
        add(f"tendenza dal {ta['dal']} {ta['variabile']} (C/secolo)", round(ta['pend_secolo'], 2), round(tb['pend_secolo'], 2))
        if ta['dal'] == 1980:
            add(f"  errore standard dal 1980 {ta['variabile']}", round(ta['se_secolo'], 2), round(tb['se_secolo'], 2))
ra, rb = L(a, 'records.json'), L(b, 'records.json')
for k in ('anni_caldi', 'estati_calde', 'mesi_caldi', 'inverni_caldi'):
    fa = lambda o: f"{o['anno']}" + (f"-{o['mese']:02d}" if 'mese' in o else '') + f" ({o['tmedia']:.2f})"
    add(f'{k} (primi 10)', ', '.join(fa(o) for o in ra[k][:10]), ', '.join(fa(o) for o in rb[k][:10]))
for k in ('tmax_alta', 'tmin_alta', 'tmedia_alta'):
    fa = lambda o: f"{o['data']} ({o['valore']})"
    add(f'giorni_estremi {k} (primi 5)', ', '.join(fa(o) for o in ra['giorni_estremi'][k][:5]), ', '.join(fa(o) for o in rb['giorni_estremi'][k][:5]))
ga, gb = L(a, 'giorni.json'), L(b, 'giorni.json')
c = ga['campi']
for nome, col in (('massima piu alta', 'tx_rec_anno'), ('minima piu bassa', 'tn_rec_anno')):
    i = c.index(col)
    ya = [r[i] for r in ga['righe']]; yb = [r[i] for r in gb['righe']]
    add(f'record giornalieri del calendario ({nome}) dal 2008', sum(y >= 2008 for y in ya), sum(y >= 2008 for y in yb))
    add(f'record giornalieri del calendario ({nome}) 2008-2016', sum(2008 <= y <= 2016 for y in ya), sum(2008 <= y <= 2016 for y in yb))
    add(f'record giornalieri del calendario ({nome}) 2017 e dopo', sum(y >= 2017 for y in ya), sum(y >= 2017 for y in yb))
for ma, mb in zip(ca['clima_mensile'], cb['clima_mensile']):
    add(f"record mese {ma['mese']:02d} massima", f"{ma['record_max']['data']} {ma['record_max']['valore']}", f"{mb['record_max']['data']} {mb['record_max']['valore']}")
    add(f"mese {ma['mese']:02d} piu caldo", f"{ma['mese_piu_caldo']['anno']} {ma['mese_piu_caldo']['tmedia']:.2f}", f"{mb['mese_piu_caldo']['anno']} {mb['mese_piu_caldo']['tmedia']:.2f}")
fa_, fb_ = L(a, 'finora.json'), L(b, 'finora.json')
for x, y in zip(fa_['righe'], fb_['righe']):
    add(f"2026 finora {x['var']}: posto (dal piu alto) su {x['n']}", x['rank_alto'], y['rank_alto'])
    add(f"2026 finora {x['var']}: media degli altri anni", round(x['media_altri'], 2), round(y['media_altri'], 2))
add('2026 finora: primi 5', ', '.join(f"{o['anno']} ({o['tmedia']:.2f})" for o in fa_['classifica_tmedia_caldi'][:5]),
    ', '.join(f"{o['anno']} ({o['tmedia']:.2f})" for o in fb_['classifica_tmedia_caldi'][:5]))
aa, ab = L(a, 'annuale.json')['anni'], L(b, 'annuale.json')['anni']
for x, y in zip(aa, ab):
    if 2006 <= x['anno'] <= 2018 and x['ok']:
        add(f"anno {x['anno']} media annua", round(x['tmedia'], 2), round(y['tmedia'], 2))
R = pd.DataFrame(rows); R.to_csv(out, index=False)
pd.set_option('display.width', 300); pd.set_option('display.max_colwidth', 140); pd.set_option('display.max_rows', 300)
print(R.to_string())
