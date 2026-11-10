"""Dati del gioco per quartiere: docs/quiz/data/quartieri.json.

Prende i valori dalle schede dei quartieri (docs/quartiere/data/schede.json, gli stessi numeri della pagina
"Il tuo quartiere") e conta bambini, over 65, donne e uomini dalle età per quartiere della pagina Età
(docs/eta/data/eta_singola_nil_2025.json). Il gioco costruisce le domande nel browser da questi numeri.

Controlli:
- età: la somma delle età di ogni quartiere deve dare i residenti 2025 della pagina Età (nil_eta_centenari.csv);
- residenti, età media e quota di over 65 delle schede devono essere uguali a quelli della pagina Età;
- quota di stranieri delle schede uguale a quella della pagina Le comunità (diversita_nil.csv, 2025);
- ogni indicatore usato esiste nelle schede, con anno, valore di Milano e numero di quartieri in classifica.
Si usa un valore solo se il quartiere è in classifica per quella misura (r non vuoto): fuori classifica le schede
dicono che il valore oscilla.
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mazzo import DOCS, carica  # noqa: E402

# id: (cosa — per "è più alto/basso di Milano", breve, unità, decimali, fonte, licenza, verso della classifica in parole)
IND = {
    'eta_media':    ('l’età media dei residenti', 'età media', 'anni', 1, 'Comune di Milano, residenti per età e quartiere', 'CC BY 4.0', 'più anziano'),
    'quota_65':     ('la quota di residenti con 65 anni o più', 'residenti over 65', '%', 1, 'Comune di Milano, residenti per età e quartiere', 'CC BY 4.0', 'con più over 65'),
    'stranieri':    ('la quota di residenti con cittadinanza straniera', 'residenti stranieri', '%', 1, 'Comune di Milano, residenti per cittadinanza e quartiere', 'CC BY 4.0', 'con più stranieri'),
    'laureati':     ('la quota di residenti con un titolo universitario', 'residenti laureati', '%', 1, 'ISTAT, censimento permanente 2023', 'CC BY 4.0', 'con più laureati'),
    'famiglie_sole': ('la quota di famiglie di una sola persona', 'famiglie di una persona', '%', 1, 'ISTAT, censimento permanente 2023', 'CC BY 4.0', 'con più persone che vivono da sole'),
    'reddito':      ('il reddito medio per contribuente', 'reddito medio', '€', 0, 'MEF e Comune di Milano, redditi per CAP portati al quartiere', 'CC BY', 'più ricco'),
    'prezzo_vendita': ('il prezzo delle case in vendita al metro quadro', 'prezzo delle case', '€/m²', 0, 'Agenzia delle Entrate, quotazioni OMI', 'CC BY 4.0', 'più caro'),
    'airbnb':       ('il numero di annunci di affitto breve ogni 100 case', 'affitti brevi ogni 100 case', '', 1, 'Inside Airbnb, annunci del 19 settembre 2026', 'CC BY 4.0', 'con più affitti brevi'),
    'alberi':       ('il numero di alberi del Comune ogni 1.000 abitanti', 'alberi ogni 1.000 abitanti', '', 0, 'Comune di Milano, alberi gestiti dal Comune', 'CC BY 4.0', 'con più alberi per abitante'),
    'suolo':        ('la quota di suolo consumato (asfalto, edifici)', 'suolo consumato', '%', 1, 'ISPRA e SNPA, carta del consumo di suolo', 'CC BY 4.0', 'più cementificato'),
    'locali':       ('il numero di bar e ristoranti ogni 1.000 abitanti', 'bar e ristoranti ogni 1.000 abitanti', '', 1, 'Comune di Milano, registro dei pubblici esercizi', 'CC BY 4.0', 'con più locali per abitante'),
    'c15_metro':    ('la quota di residenti con il metrò a 15 minuti a piedi', 'residenti col metrò a 15 minuti', '%', 0, 'Comune di Milano e OpenStreetMap', 'CC BY 4.0 e ODbL', 'più vicino al metrò'),
    'c15_parchi':   ('la quota di residenti con un parco a 15 minuti a piedi', 'residenti con un parco a 15 minuti', '%', 0, 'Comune di Milano e OpenStreetMap', 'CC BY 4.0 e ODbL', 'più vicino a un parco'),
    'aree_cani':    ('il numero di aree cani ogni 100.000 abitanti', 'aree cani ogni 100.000 abitanti', '', 1, 'Comune di Milano, aree cani', 'CC BY 4.0', 'con più aree cani per abitante'),
    'affluenza21':  ('l’affluenza alle comunali del 2021', 'affluenza alle comunali 2021', '%', 1, 'Comune di Milano, risultati elettorali per sezione', 'CC BY 4.0', 'che vota di più'),
    'nuove_case':   ('il numero di case nuove costruite ogni 1.000 abitanti', 'case nuove ogni 1.000 abitanti', '', 1, 'Comune di Milano, titoli edilizi', 'CC BY 4.0', 'dove si costruisce di più'),
    'antenne':      ('il numero di antenne dei cellulari ogni 1.000 abitanti', 'antenne ogni 1.000 abitanti', '', 2, 'Comune di Milano, catasto degli impianti', 'CC BY 4.0', 'con più antenne per abitante'),
}
# confronto con Milano: solo dove il riferimento delle schede è il valore della città
CONTA = {  # conteggi su tutti gli 88 quartieri (riferimento: mediana dei quartieri)
    'residenti': ('residenti', 'persone', 0, 'Comune di Milano, anagrafe', 'CC BY 4.0'),
    'botteghe':  ('botteghe storiche', 'botteghe', 0, 'Comune di Milano e Regione Lombardia, elenchi delle botteghe storiche', 'CC BY 4.0 e CC0'),
}


def scrivi():
    S = carica('quartiere/data/schede.json')
    I = {i['id']: i for i in S['indicatori']}
    eta = carica('eta/data/eta_singola_nil_2025.json')['nil']
    nec = {r['id_nil']: r for r in carica('eta/data/nil_eta_centenari.csv')}
    div = {r['nil']: r for r in carica('comunita/data/diversita_nil.csv') if r['anno'] == 2025}
    ce = [r for r in carica('eta/data/citta_eta_centenari.csv') if r['anno'] == 2025][0]
    problemi = []

    ind_out = []
    for k, (cosa, breve, u, dec, fonte, lic, verso) in IND.items():
        i = I[k]
        assert i['ref'] == 'città' and i['citta'] is not None, k
        ind_out.append({'id': k, 'et': i['et'], 'cosa': cosa, 'breve': breve, 'u': u, 'dec': dec, 'anno': str(i['anno']),
                        'citta': i['citta'], 'n': i['n'], 'pagina': i['pagina'], 'fonte': fonte, 'licenza': lic, 'verso': verso,
                        'nota': i.get('nota') or ''})
    for k, (breve, u, dec, fonte, lic) in CONTA.items():
        i = I[k]
        ind_out.append({'id': k, 'et': i['et'], 'cosa': breve, 'breve': breve, 'u': u, 'dec': dec, 'anno': str(i['anno']),
                        'citta': i['citta'], 'ref': 'mediana', 'n': i['n'], 'pagina': i['pagina'], 'fonte': fonte, 'licenza': lic,
                        'verso': 'con più ' + breve, 'nota': i.get('nota') or ''})

    nil_out = []
    for n in S['nil']:
        sid = str(n['id'])
        V = S['valori'][sid]
        e = eta.get(sid) or {'F': [0] * 101, 'M': [0] * 101}
        F, M = e['F'], e['M']
        tot = sum(F) + sum(M)
        rif = nec.get(n['id']) or {'residenti_2025': 0, 'eta_media_2025': None, 'quota_65_2025': None}
        if tot != rif['residenti_2025']:
            problemi.append('%s: età sommate %d, residenti %d' % (n['nome'], tot, rif['residenti_2025']))
        if V['residenti']['v'] != rif['residenti_2025']:
            problemi.append('%s: residenti schede %s contro età %s' % (n['nome'], V['residenti']['v'], rif['residenti_2025']))
        if V['eta_media']['v'] is not None and rif['eta_media_2025'] is not None and abs(V['eta_media']['v'] - rif['eta_media_2025']) > 1e-9:
            problemi.append('%s: età media diversa' % n['nome'])
        if V['quota_65']['v'] is not None and rif['quota_65_2025'] is not None and abs(V['quota_65']['v'] - rif['quota_65_2025']) > 1e-9:
            problemi.append('%s: quota 65 diversa' % n['nome'])
        dn = div.get(n['nome']) or next((r for r in div.values() if r['residenti'] == n['residenti']), None)  # nomi scritti in modo diverso
        if V['stranieri'].get('r') is not None:
            if dn is None or abs(dn['quota_stranieri_pct'] - V['stranieri']['v']) > 1e-9:
                problemi.append('%s: stranieri diversi da Le comunità' % n['nome'])
        vals = {}
        for k in list(IND) + list(CONTA):
            x = V.get(k) or {}
            if isinstance(x.get('v'), (int, float)) and x.get('r') is not None:
                vals[k] = [x['v'], x['r']]
        q = {'id': n['id'], 'nome': n['nome'], 'mun': n['municipio'], 'res': n['residenti'], 'piccolo': n['piccolo'],
             'vuoto': n['quasi_vuoto'], 'v': vals,
             'eta': {'bambini': sum(F[:15]) + sum(M[:15]), 'over65': sum(F[65:]) + sum(M[65:]), 'donne': sum(F), 'uomini': sum(M)}}
        pc = V.get('prima_cittadinanza') or {}
        if isinstance(pc.get('v'), str) and V['stranieri'].get('r') is not None:
            q['prima'] = [pc['v'], (pc.get('x') or {}).get('s')]
        nil_out.append(q)
    if problemi:
        print('\n'.join(problemi))
        raise SystemExit('quartieri: %d problemi' % len(problemi))
    out = {'anno_eta': 2025, 'citta': {'quota_0_14': ce['quota_0_14_pct'], 'quota_65': ce['quota_65_pct']},
           'indicatori': ind_out, 'quartieri': nil_out,
           'fonte_eta': 'Comune di Milano, residenti per età e quartiere al 31 dicembre', 'licenza_eta': 'CC BY 4.0'}
    s = json.dumps(out, ensure_ascii=False, separators=(',', ':'))
    open(os.path.join(DOCS, 'quiz', 'data', 'quartieri.json'), 'w', encoding='utf-8').write(s)
    print('scritto quartieri: %.1f KB, %d quartieri, %d misure' % (len(s.encode()) / 1024, len(nil_out), len(ind_out)))
    # controllo licenze sulle pagine
    lic = {}
    for f in carica('fonti/data/fonti.json')['fonti']:
        lic.setdefault(f['pagina'], set()).add(f['licenza_tipo'].lower())
    for d in ind_out:
        pg = d['pagina']
        assert os.path.exists(os.path.join(DOCS, pg, 'index.html')), pg
        primo = d['licenza'].lower().split(' e ')[0]
        assert any(t.split(' (')[0] in primo or primo.startswith(t.split(' (')[0]) for t in lic.get(pg, [])), (d['id'], pg, lic.get(pg))


if __name__ == '__main__':
    scrivi()
