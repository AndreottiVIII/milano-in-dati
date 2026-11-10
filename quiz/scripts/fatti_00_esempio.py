"""Domande di esempio (modello per gli altri moduli)."""
from mazzo import Prove, piuomeno, vf, anno_q, serie_da, primo_sorpasso


def domande():
    out = []

    p = Prove()
    auto = p.v('auto/data/riepilogo.json', 'serie', '[a=2025]', 'auto')
    alb = p.v('alberi/data/riepilogo.json', 'citta', 'alberi', '2025')
    out.append(piuomeno(p, id='auto-o-alberi', pagina='auto', diff='facile',
        domanda='A Milano ci sono più auto dei residenti o più alberi curati dal Comune?',
        a=('auto dei residenti, fine 2025', auto, ''), b=('alberi del Comune, marzo 2025', alb, ''),
        spiega='Le auto sono quasi tre volte gli alberi schedati dal Comune. E gli alberi dei giardini privati non sono contati.',
        anno='2025', fonte='Comune di Milano, auto iscritte al PRA; alberi: Comune di Milano', licenza='CC BY 4.0'))

    p = Prove()
    n24 = p.v('nascite/data/serie_1880_2024.csv', '[anno=2024]', 'nati')
    n1880 = p.v('nascite/data/serie_1880_2024.csv', '[anno=1880]', 'nati')
    ab1880 = p.v('nascite/data/serie_1880_2024.csv', '[anno=1880]', 'abitanti')
    out.append(vf(p, id='nati-1880', pagina='nascite', diff='media',
        affermazione='Nel 2024 a Milano sono nati meno bambini che nel 1880, quando la città aveva 305 mila abitanti.',
        vero=n24 < n1880, confronto=[('1880', n1880, 'nati'), ('2024', n24, 'nati')],
        spiega='9.147 nati nel 2024 contro 9.739 nel 1880. Oggi gli abitanti sono più di quattro volte tanti.',
        anno='2024', fonte='Comune di Milano, nati e morti dal 1880', licenza='CC BY 4.0'))
    return out
