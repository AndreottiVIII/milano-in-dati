# Il lavoro che c'è: note

Pagina nuova (bozza in bozze-grafici/occupazione-v2/, dati in docs/occupazione/data/). Non pubblicata, non nel menu. Anteprima: `python -I -X utf8 bozze-grafici/anteprima.py occupazione`.
Parte del rapporto FONTI_AREE_NUOVE_2026-11-10.md, area 1 «Lavoro vero». Non ripete `docs/lavoro/` (censimento per quartiere 1991-2021).

## Fonti e licenze
- Comune di Milano, dati.comune.milano.it, licenza **Creative Commons Attribuzione (CC BY)** (dalla scheda del catalogo; la versione non è indicata, il sito scrive «CC BY»):
  - ds109 condizione lavorativa dei residenti di 15 anni e più per genere (occupati e in cerca, 2004-2024);
  - ds114 confronti territoriali (tassi 15-64 anni: comune, provincia, Lombardia, Nord-Ovest, Italia);
  - ds112 indicatori 15-64 anni del comune (usato per correggere il 2019);
  - ds113 occupazione giovanile 15-24 anni;
  - ds1497 serie storica del tasso di occupazione (usato solo per il 2019 della Lombardia).
  Tutte vengono dall'indagine ISTAT sulle forze di lavoro (campione).
- Regione Lombardia, dati.lombardia.it, **CC0** (dedica al pubblico dominio, verificato il 10/11/2026 sulla scheda API di ogni dataset):
  - p9wf-dh6p «Durata contratti di lavoro per tipologia» (provincia 015 = Milano, anni 2013-2025);
  - x54h-y9u7 «Durata contratti per tipologia, genere ed età» (fasce 15-34 e 35 e oltre, 2013 e 2024).
  robots.txt: Crawl-delay 1, nessuna regola sui file usati. Nessun nuovo scaricamento: i file erano già in `_esplorazione/aree/lavoro/`.
- ISTAT esploradati (SDMX, nessun login), **CC BY 4.0** (note legali di istat.it, lette il 10/11/2026). Il rapporto di area scriveva CC BY 3.0 IT: le note legali attuali dicono Creative Commons Attribuzione 4.0.
  - DF_DCSS_LCAS_FRISC_1 occupati che lavorano da casa nei grandi comuni, 2023-2024 (Milano 015146, Roma 058091, Torino 001272, Napoli 063049, Bologna 037006, Genova 010025, Firenze 048017, Palermo 082053, Italia);
  - 93_379_DF_DCCN_OCCTSEC2010_2 occupati per settore e provincia (ITC45 = Milano), edizione 2025M12, posizioni di lavoro (JB), anni 2018-2023.

### Fonte senza licenza dichiarata: NON usata
- Regione Lombardia 8su3-rqhi «Movimento lavoratori per tipo contratto e regime orario» (avviamenti 2013-2025): la scheda API non dichiara la licenza (`license: null`). Il rapporto di area la usava per «854.218 avviamenti nel 2025, 60,3% a tempo determinato». Sulla pagina non compare nessun numero da questo file. La quota dei contratti a termine per anno viene invece da p9wf (CC0): 49% nel 2013, 60% nel 2025 (il file 8su3 dà 49,0% e 60,3%: stessa storia). Se Davide vuole i numeri 8su3, serve prima chiedere alla Regione.

## Passi (occupazione/scripts/)
1. `01_prepara.py`: copia in `dati_grezzi/` i file già scaricati; del file ISTAT dei settori (24 MB) tiene solo ITC45 e Italia, edizione 2025M12, totale occupati (stato 9).
2. `02_elabora.py`: scrive in `docs/occupazione/data/` `riepilogo.json` (letto dalla pagina) e 7 CSV da scaricare (separatore `;`, punto decimale). Il file più grande è tassi_territori.csv (44 KB).
Esecuzione: `python -I -X utf8 occupazione/scripts/01_prepara.py` poi `02_elabora.py`.

## Numeri in alto (tutti ricalcolati e verificati nello script)
- 73,9% (Milano) contro 62,2% (Italia), 2024, tasso di occupazione 15-64 anni (ds114).
- Divario uomini-donne 14,7 punti (2004) → 3,9 (2024): 74,8-60,1 e 75,8-71,9 (ds114).
- Occupati residenti 562.757 → 683.910 (+21,5%), 15 anni e più (ds109).
- 58% dei contratti a termine 2024 sotto il mese: 412.615 su 712.891 (p9wf). Controllo: la stessa quota è 57,7% nel 2013, picco 63,6% nel 2016, minimo 48,7% nel 2020, 57,9% nel 2024: non cresce.
- Disoccupazione giovanile 15-24: 17,0% (2024), massimo 38,2% (2014) (ds113).
- Lavoro da casa a Milano 2024: (102.166 + 162.404) / 677.666 = 39,0% (ISTAT; nel 2023 38,3%).

## Difetti trovati nei dati (nuovi, oltre a quelli del rapporto)
- **ds114, colonna 2019 = colonna 2021** per tutti i territori (Milano 70,4 invece di 72,7; disoccupazione 6,8 invece di 5,1). Verificato con ds112 e ds1497. Per Milano il 2019 viene da ds112 (uguale a ds114 in tutti gli altri anni); per la Lombardia solo l'occupazione totale da ds1497 (anch'essa uguale a ds114 negli altri anni); per provincia, Nord-Ovest, Italia il 2019 è vuoto e la linea è tratteggiata. La disoccupazione lombarda di ds1498 differisce da ds114 quasi ovunque: non mescolata, 2019 vuoto.
- **ds109, 2017**: occupati maschi 341.737 = quelli del 2018, e maschi + femmine non fanno il totale (-1.477). Usati i totali; uomini e donne separati solo per 2004 e 2024.
- **ds109** usa etichette diverse da un anno all'altro («Popolazione di riferim (15 e +)», «Forze Lavoro»): lette per prefisso.
- **p9wf e x54h non coincidono**: nel 2024 x54h conta 978.375 contratti, p9wf 1.225.297 (a termine 483.547 contro 712.891). In x54h il 31-36% dei contratti a termine dura sotto il mese, in p9wf il 58%. Non usata la durata di x54h; di x54h solo le quote per tipo dentro lo stesso file (15-34 anni: 50,2% a termine, 29,3% indeterminato; 35+: 48,6% e 40,5%).
- p9wf prima del 2013 è incompleto (2012: 288 mila contratti, 2011: 123 mila): i grafici sui contratti partono dal 2013.
- La durata è calcolata alla data di estrazione (nov. 2026): per il 2025 i contratti lunghi possono apparire più corti.
- ISTAT settori: tre edizioni sovrapposte (2025M1, M6, M12): usata la più recente, che per Milano arriva al 2023. I dieci gruppi (A, B-E, F, G-I, J, K, L, M-N, O-Q, R-U) sommano al totale (controllato con tolleranza 0,35 per gli arrotondamenti).

## Limiti già scritti nella pagina
Campione (giovani e lavoro da casa ballano), residenti e non posti di lavoro, tassi 15-64 e numeri 15+, anni sbagliati nel file del Comune, contratti non persone e provincia non città, durata alla data di estrazione, due file contratti diversi, «Altro» non spiegato, settori in posizioni di lavoro, città scelte da noi, niente cause (correlazione), stipendi e NEET non disponibili.

## Cosa non c'è
- Stipendi per settore: INPS solo in PDF. NEET: solo Lombardia. Avviati al lavoro (ds597) e disponibili (ds621): fermi al 2018, non usati. Infortuni INAIL (ds518): fuori tema.
- Il Covid 2020 è solo richiamato con link alla pagina «L'anno del Covid».

## Controlli sulla bozza (10/11/2026)
A 375 e 1000 px con Edge: nessun errore in console, nessun testo fuori dagli svg, nessun scorrimento laterale, nessun testo sotto i 12 px, nessun testo sovrapposto a un altro negli svg.
