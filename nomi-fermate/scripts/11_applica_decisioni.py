"""Applica le decisioni di Davide (29-30/10/2026) alle 27 stazioni metro incerte.
Legge pulito/fermate_metro_nomi.csv (output di 06) + pulito/decisioni_davide.csv.
Scrive pulito/fermate_metro_nomi_finale.csv e pulito/da_verificare_finale.csv (residui).
Mai modificare gli output a mano: si cambia decisioni_davide.csv e si rilancia (dopo 06)."""
import csv, sys
base = list(csv.DictReader(open('pulito/fermate_metro_nomi.csv', encoding='utf-8-sig')))
dec = {r['stazione']: r for r in csv.DictReader(open('pulito/decisioni_davide.csv', encoding='utf-8-sig'))}
dubbi = {r['stazione'] for r in csv.DictReader(open('pulito/da_verificare.csv', encoding='utf-8-sig'))}
errori = []
mancanti = dubbi - set(dec)
extra = set(dec) - {r['stazione'] for r in base}
if mancanti: errori.append('dubbi senza decisione: ' + ', '.join(sorted(mancanti)))
if extra: errori.append('decisioni per stazioni inesistenti: ' + ', '.join(sorted(extra)))
if errori:
    sys.exit('ERRORE: ' + ' | '.join(errori))
cols = list(base[0].keys()) + ['decisione_davide', 'categoria_prima']
out, cambi = [], []
for r in base:
    r = dict(r); r['decisione_davide'] = ''; r['categoria_prima'] = ''
    d = dec.get(r['stazione'])
    if d:
        r['categoria_prima'] = r['categoria']
        for k in ('categoria', 'sottocategoria', 'sesso', 'persona', 'intitolato_a'):
            if d[k]:
                r[k] = d[k]
        if r['categoria'] not in ('persona', 'persona leggendaria', 'santo/santa'):
            r['sesso'] = ''  # il sesso conta solo per le persone
        r['decisione_davide'] = d['nota_decisione']
        r['da_verificare'] = ''
        r['confidenza'] = 'decisa da Davide'
        if r['categoria_prima'] != r['categoria']:
            cambi.append(f"{r['stazione']}: {r['categoria_prima']} -> {r['categoria']}")
    out.append(r)
with open('pulito/fermate_metro_nomi_finale.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(out)
res = [r for r in out if r['da_verificare']]
with open('pulito/da_verificare_finale.csv', 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=['stazione', 'categoria', 'da_verificare']); w.writeheader()
    for r in res:
        w.writerow({k: r[k] for k in ('stazione', 'categoria', 'da_verificare')})
print(len(out), 'stazioni;', len(dec), 'decisioni applicate;', len(res), 'dubbi residui')
print('cambi di categoria:', '; '.join(cambi))
