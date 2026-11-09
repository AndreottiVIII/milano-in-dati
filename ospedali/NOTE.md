# Ospedali di Milano: note

Bozza: `bozze-grafici/ospedali-v2/index.html`. Dati della pagina: `docs/ospedali/data/` (tutti sotto 2 MB). Programmi in `scripts/`, da lanciare in ordine con `python -I -X utf8`, User-Agent `milano-in-dati/1.0`.

## Fonti e licenze (in `dati_grezzi/`)
| Fonte | File | Licenza |
|---|---|---|
| Comune di Milano DS683, posti letto strutture ospedaliere e case di cura 2010-2023 (file del 1/9/2025, copia dei dati del Ministero, con indirizzo, NIL, coordinate) | `ds683.csv`, `ds683.geojson` | IODL 2.0 (scheda: "Italian Open Data License v2.0"; il campo licenza CKAN dice "Other (Attribution)") |
| Ministero della Salute, posti letto per Regione e disciplina 2010-2023 | `min_regione_*.csv` | IODL 2.0 |
| Ministero della Salute, posti letto per struttura ospedaliera 2010-2023 (con comune) | `min_struttura_*.csv` | IODL 2.0 |
| Eurostat demo_r_d2jan, popolazione 1 gennaio Italia e Lombardia | `eurostat_demo_r_d2jan_IT_ITC4.json` | CC BY 4.0 |
| OpenStreetMap (Overpass, 9/11/2026): ospedali e pronto soccorso | `osm_ospedali_milano.json` | ODbL |
| ISTAT, abitanti delle città: da `docs/auto/data/confronto_citta.csv` e `popolazione/pulito/` (non copiati) | | CC BY 4.0 |
| Rete pedonale e civici: da `citta-15-minuti/out/` (sola lettura, non copiata) | | OSM ODbL, Comune CC BY |
| Confini NIL e residenti: da `docs/medici-farmacie/data/nil.geojson` (ridotti) | | Comune CC BY |

Passi: 01 scarica, 02 OSM, 03 Eurostat, 04 punti (ospedali e pronto soccorso), 05 minuti a piedi, 06 dati della pagina.

## robots.txt
- dati.salute.gov.it: consente tutto. dati.lombardia.it: crawl-delay 1 (rispettato, solo API di catalogo).
- dati.comune.milano.it: `robots.txt` risponde 403 (pagina "accesso non consentito"). Scaricato solo il file indicato dall'API pubblica CKAN, una volta. Da segnalare a Davide.
- Il sito del Ministero chiude le connessioni di urllib: i download usano curl.

## Scelte e limiti
- Pubblico = "Ospedale a gestione diretta" + "IRCCS fondazione"; privato accreditato = IRCCS privato, casa di cura, ospedale classificato (San Giuseppe). Scelta nostra.
- Gruppi storici: Galeazzi = 30946-0/-1 + Sant'Ambrogio 30112; San Siro 30119 + 30946-2; Turro 30104+30950; Riabilitazione 30373+30949; Capitanio 30118+30389+30936-3; Policlinico 30925-1/-2. Controllo: la somma dei gruppi uguale al totale di Milano ogni anno.
- Abitanti di Milano prima del 2019 non confrontabili (ISTAT ricostruita 2010 1,25 M, anagrafe 1,32 M): niente serie per abitante nel tempo, indice 2010=100. Per il 2023 ISTAT 1.371.499 (con l'anagrafe 1.417.597: 6,4 invece di 6,6 per 1.000).
- Pronto soccorso: nessun elenco aperto ufficiale. Lista a mano da OSM (22 punti: 11 generali a Milano, 5 specialistici, 6 fuori comune). Generale/specialistico deciso da noi dai nomi. Melloni e Città Studi dipendono dal tag OSM.
- Minuti a piedi: rete pedonale di citta-15-minuti, 4,5 km/h, mediana dei civici residenziali per quartiere (equi-peso), tetto 9.000 m. Un solo punto per ospedale.
- Non trovati dati aperti su: accessi e attese al pronto soccorso (Regione Lombardia: solo "Paziente cronico", "Ricoveri per ospedale" 2010-2016 senza residenza); pazienti da fuori Milano (nessun dato aperto con la residenza di chi si ricovera).
- Nel 2021-2022 letti Covid (+448 infettive e +467 medicina generale tra 2019 e 2021).
- Posizione mancante per Tumori, Besta, Casa di cura Policlinico dal 2021: presa da anni precedenti.
