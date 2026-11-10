"""Domande "quale quartiere?": tra tre quartieri, chi ha di più (o di meno) di una misura.

I valori sono quelli delle schede dei quartieri (pagina "Il tuo quartiere"), solo per quartieri in classifica
per quella misura e con almeno 10.000 residenti (nomi conosciuti, numeri stabili). Le terne si scelgono con un
seme fisso, così il mazzo è sempre lo stesso; i tre valori devono distare almeno il 12% l'uno dall'altro.
"""
import random
from mazzo import Prove, quartiere, carica
from quartieri_gioco import IND

# misura: (domanda col verso massimo, domanda col verso minimo, anno nel testo)
TESTI = {
    'reddito': ('ha il reddito medio per contribuente più alto?', 'ha il reddito medio per contribuente più basso?'),
    'prezzo_vendita': ('ha le case più care al metro quadro?', 'ha le case meno care al metro quadro?'),
    'eta_media': ('ha i residenti più anziani, in media?', 'ha i residenti più giovani, in media?'),
    'stranieri': ('ha la quota più alta di residenti con cittadinanza straniera?', None),
    'laureati': ('ha più laureati, in proporzione?', 'ha meno laureati, in proporzione?'),
    'famiglie_sole': ('ha più famiglie di una persona sola, in proporzione?', None),
    'alberi': ('ha più alberi del Comune per abitante?', 'ha meno alberi del Comune per abitante?'),
    'airbnb': ('ha più annunci di affitto breve ogni 100 case?', None),
    'locali': ('ha più bar e ristoranti per abitante?', None),
    'affluenza21': ('è andato di più a votare alle comunali?', 'è andato di meno a votare alle comunali?'),
    'suolo': ('ha la quota più alta di suolo consumato?', 'ha la quota più bassa di suolo consumato?'),
    'aree_cani': ('ha più aree cani per abitante?', None),
    'c15_metro': ('ha più residenti con il metrò a 15 minuti a piedi?', None),
    'nuove_case': ('ha costruito più case nuove per abitante?', None),
    'quota_65': ('ha la quota più alta di over 65?', None),
}


def domande():
    S = carica('quartiere/data/schede.json')
    I = {i['id']: i for i in S['indicatori']}
    nomi = {str(n['id']): n for n in S['nil']}
    rnd = random.Random(20261110)
    out = []
    for k, (tmax, tmin) in TESTI.items():
        cosa, breve, u, dec, fonte, lic, verso = IND[k]
        cand = [sid for sid, n in nomi.items() if n['residenti'] >= 10000 and (S['valori'][sid].get(k) or {}).get('r') is not None]
        for verso_q, testo in (('max', tmax), ('min', tmin)):
            if not testo:
                continue
            for tent in range(500):
                tre = rnd.sample(cand, 3)
                v = [S['valori'][s][k]['v'] for s in tre]
                vs = sorted(v)
                if _distanti(vs[0], vs[1], u) and _distanti(vs[1], vs[2], u):
                    break
            else:
                raise RuntimeError('nessuna terna per ' + k)
            p = Prove()
            vals = [p.v('quartiere/data/schede.json', 'valori', s, k, 'v') for s in tre]
            citta = p.v('quartiere/data/schede.json', 'indicatori', '[id=%s]' % k, 'citta')
            anno = I[k]['anno']
            ratio = vs[2] / vs[0] if vs[0] else 99
            if u in ('%', 'anni'):
                gap = vs[2] - vs[0]
                diff = 'facile' if gap >= (6 if u == 'anni' else 25) else 'media' if gap >= (4 if u == 'anni' else 12) else 'difficile'
            else:
                diff = 'facile' if ratio >= 2.2 else 'media' if ratio >= 1.45 else 'difficile'
            best = max(vals) if verso_q == 'max' else min(vals)
            chi = nomi[tre[vals.index(best)]]['nome']
            rel = 'sopra' if best > citta * 1.02 else 'sotto' if best < citta * 0.98 else 'in linea con'
            spiega = '%s: %s, %s il valore di tutta Milano (%s).' % (chi, _f(best, dec, u, k), rel, _f(citta, dec, u, k))
            out.append(quartiere(p, id='q-%s-%s' % (k, verso_q), pagina=I[k]['pagina'], diff=diff,
                                 domanda='%s Quale di questi tre quartieri %s' % (_quando(k, anno), testo),
                                 opzioni=[(nomi[s]['nome'], x) for s, x in zip(tre, vals)], verso=verso_q, unita=u,
                                 spiega=spiega, anno=anno, fonte=fonte, licenza=lic, dec=dec, citta=citta, misura=breve))
    return out


def _distanti(a, b, u):
    """Valori abbastanza lontani da non essere un testa a testa."""
    if u == 'anni':
        return b - a >= 1.5
    if u == '%':
        return b - a >= 4
    return a > 0 and b / a >= 1.12


def _quando(k, anno):
    if k == 'affluenza21':
        return 'Comunali del 2021.'
    if k == 'airbnb':
        return 'Settembre 2026.'
    if k == 'nuove_case':
        return 'Dal 2014 al 2024.'
    if k == 'prezzo_vendita':
        return 'Primo semestre 2026.'
    if k == 'alberi':
        return 'Marzo 2025.'
    return 'Nel %s.' % anno


LUNGA = {'alberi': 'alberi ogni 1.000 abitanti', 'airbnb': 'annunci ogni 100 case', 'locali': 'locali ogni 1.000 abitanti',
         'aree_cani': 'aree ogni 100.000 abitanti', 'nuove_case': 'case nuove ogni 1.000 abitanti'}


def _f(x, dec, u, k=None):
    s = ('{:,.%df}' % dec).format(x).replace(',', 'X').replace('.', ',').replace('X', '.')
    if u == '%':
        return s + '%'
    if not u and k in LUNGA:
        return s + ' ' + LUNGA[k]
    return s + (' ' + u if u else '')
