# Il tuo anno: note

Pagina nuova (bozza in bozze-grafici/il-tuo-anno-v2/, dati in docs/il-tuo-anno/data/). Non pubblicata, non nel menu.

## Fonti e licenze
- Comune di Milano, dati.comune.milano.it, tutte CC BY 4.0 (scaricate il 9/11/2026):
  - ds1495 "Nati vivi - serie storica dal 1880" (nati vivi residenti)
  - ds1494 "Popolazione calcolata - serie storica dal 1880"
  - ds2918 "Tassi di natalità e mortalità - serie storica dal 1880"
  - ds223 "Popolazione: residenti per stato civile, genere, età e cittadinanza (2012-2025)"
- Residenti per età singola: docs/eta/data/eta_singola_citta.json (Comune, CC BY).

## Passi (il-tuo-anno/scripts/)
01_prepara.py legge i CSV in _esplorazione/dati/ckan/csv e scrive docs/il-tuo-anno/data/anno.json (15 KB). Python con -I -X utf8.

## Data dei residenti (correzione all'esplorazione)
- Ogni colonna di eta_singola_citta.json è la popolazione al 31 dicembre di quell'anno (come scrive popolazione/NOTE.md). Il totale della colonna 2025 (1.399.079) è uguale a quello di ds223 2025 e di ds1494 2025: stesso giorno, 31/12/2025. Anche ds223 2012 è al 31/12/2012.
- La pagina usa la colonna 2025, dichiarata "a fine 2025": nato nell'anno X, età compiuta 2025-X, rapporto con i nati dell'anno X. L'esplorazione (a7_coorti.py) abbinava invece l'età a all'anno 2024-a, sfasato di un anno rispetto alla colonna 2025 (rapporto massimo 2,14 nel 1987 nell'esplorazione; con la colonna 2025 è 2,09 per i nati nel 1991: 19.960 residenti contro 9.529 nati).
- Con la colonna 2024 ("inizio 2025", età a = 2024-X) si ottengono i numeri dell'esplorazione e di arrivi-partenze. Le due versioni non vanno mescolate.
- Le età del 2012 sono "alla stessa età", non le stesse persone.

## Limiti
- Confini del Comune cambiati nel 1923 (abitanti 697.368 nel 1922, 826.469 nel 1923).
- Stato civile: colonne "_stima" del Comune; "mai sposato" include i conviventi; "95 e più" è un solo gruppo; oltre i 99 anni nessun dato per età.
- Coetanei: non sono le stesse persone; oltre i 60 anni pesano i morti.
- Anagrafe: dal 2020 circa +3% rispetto alla popolazione ISTAT.
- I nati 2025 non sono ancora nella serie: chi è nato nel 2025 manca.
