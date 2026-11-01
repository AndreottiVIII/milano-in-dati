# Le case vuote - fase 1 (dati) e pagina

Data: 1 novembre 2026. Cartella `case-vuote/`: `raw/` (file scaricati, non fidati, mai eseguiti), `pulito/` (tabelle), `scripts/`. Pagina: `docs/case-vuote/index.html` + `docs/case-vuote/data/`. Niente git, JOURNAL.md / docs/index.html / docs/menu.js / MENU_README.md non toccati.
Ogni numero dice file e campo. Controlli automatici stampati da `scripts/03_costruisci.py` e salvati in `pulito/controlli.txt`.

## In breve

1. **Il numero del Politecnico (oltre 109.000) e' il censimento permanente 2021: 109.404 abitazioni non occupate da residenti** (A3 nei file ISTAT di sezione, somma delle 6.055 sezioni di Milano; 13,5% di 809.990). Il comunicato del 29/4/2026 (letto, `raw/polimi/ComSt_260429_dashboard_Milano_def.pdf`) parla di "unita' vuote o occupate da non residenti ... localizzate nelle zone centrali"; non cita la fonte, ma il numero coincide. La dashboard Tableau non e' stata consultata.
2. **Non e' un'esplosione: e' soprattutto il cambio di metodo.** 2011: 38.546 (6,0%); 2021: 109.404 (13,5%); 2023: 105.375 (12,7%). Lo stesso scatto 2011-2021 c'e' fuori da Milano (da sezioni ISTAT, `pulito/confronto_territori.csv`): altri comuni della citta' metropolitana 6,4% -> 11,5% (+5,1 punti), Lombardia 15,2% -> 21,2% (+6,0), Milano 6,0% -> 13,5% (+7,5). Il totale della citta' metropolitana 2021 (214.674 non occupate su 1.727.347) coincide esattamente con la tavola ISTAT (comunicato 1/8/2024, Prospetto 10). Con lo stesso metodo 2021 -> 2023: -3,7%.
3. **Le case dichiarate "a disposizione" dai proprietari (persone fisiche) sono quasi ferme**: 8,3% (2016), 8,6% (2020), 8,7% (2023), cioe' 52.321, 56.223, 59.021 (MEF/Agenzia Entrate, "Gli immobili in Italia" 2019, 2023, 2026, Tabella 1.10, Milano; somme delle voci = totali, controllato).
4. **Dove:** quartiere Duomo 39,0% nel 2023 (5.732 su 14.679), Porta Ticinese-Conca del Naviglio 29,9%, Brera 29,8%; piu' bassi Comasina 0,9%, Bovisasca 2,2%. Municipio 1: 28,2% (2023), ma contiene solo il 19,4% delle non occupate (8,8% delle abitazioni). Entro 4 km dal Duomo (centroide del quartiere) il 74,6% delle non occupate, in una zona con il 53,5% delle abitazioni.
5. **Centro e periferia c'erano gia'**: nel 1991 Municipio 1 15,0% contro 7,8-11,6% negli altri; dal 1991 al 2011 la quota in citta' scende da 10,0% a 6,0%. Nel 2021 il Municipio 1 triplica (9,8% -> 29,9%), il resto della citta' raddoppia (5,7% -> 11,9%): quanto sia reale e quanto metodo non e' stabilito.
6. **Airbnb e prezzi (69 quartieri con almeno 2.000 abitazioni e 2.000 residenti)**: Spearman quota 2023 vs annunci ogni 1.000 residenti +0,79 (IC 95% +0,66/+0,88); vs prezzo di vendita OMI +0,81; vs distanza dal Duomo -0,84; annunci vs prezzo +0,86: sono tre misure del centro. Nella fascia 4-6 km (21 quartieri) la correlazione quota-annunci scende a +0,19. Il pattern 2011 (pre-boom) correla +0,58 con gli annunci 2026. Variazione 2021-2023 contro crescita Airbnb 2019-2025: -0,18 (IC -0,41/+0,06), nessun legame. Tutto e' confronto, non causa.
7. **Quante sono davvero seconde case / di non residenti: nessuna fonte lo dice.** Il censimento distingueva solo nel 2001 (vuote 35.152 = 70,6%; solo non residenti 14.658 = 29,4%) e nel 2011 (vuote 37.073 = 96,2%; solo non residenti 1.473 = 3,8%): i due risultati sono incompatibili (cambio di rilevazione, non verificato). Pezzi non sommabili: a disposizione 59.021 (2023, solo persone fisiche); case intere Airbnb 22.309 (19/9/2026) = 21% delle 105.375 non occupate (16.177 con recensione negli ultimi 12 mesi = 15%); case popolari vuote 8.420 su 58.506 (marzo 2023, dal filone case-popolari).

**La cosa piu' sorprendente:** la cifra che fa titolo (109.000, "vuote") quasi triplica rispetto al 2011 ma lo stesso salto c'e' fuori da Milano: e' lo strumento, non (solo) la citta'. E non e' tutta nel centro: 4 su 5 stanno fuori dal Municipio 1.

## Fonti, licenze, date

| Fonte | Che cosa | Licenza | Scaricato / letto |
|---|---|---|---|
| ISTAT, censimenti 1991, 2001, 2011, 2021, 2023, dati per sezione | abitazioni totali e occupate da residenti per sezione, Milano (da filone `censimenti/`, file `censimenti/pulito/sezioni_<anno>.csv`, `indicatori_NIL.csv`, `indicatori_municipi.csv`) | CC BY 4.0 (ISTAT, note legali, letta il 30/10/2026) | 30/10/2026 |
| ISTAT, file regionali Lombardia 2011 (CPA) e 2021 | A2, A3, A8 per tutte le sezioni della Lombardia (`censimenti/raw/estratti/dati-cpa_2011/.../R03_indicatori_2011_sezioni.csv`, `Dati_regionali_2021/R03_indicatori_2021_sezioni.xlsx`) | CC BY 4.0 | 30/10/2026 |
| ISTAT, comunicato "Quasi un'abitazione su tre non e' occupata" | Italia 2021: 35.271.829 abitazioni, 9.581.772 non occupate (27,2%); citta' metropolitana di Milano 214.674 su 1.727.347 (Prospetto 10) | CC BY 4.0 | scaricato 1/11/2026 (`raw/istat_abitazioni/Today-Abitazioni_01_08-2024.pdf`) |
| ISTAT, "Aumentano le abitazioni occupate da residenti" (11/2/2026) | Italia 2023 e nota metodologica (RBI, ANPR, RSBL, AIDA; abitazioni = registro EUA, fonte primaria il catasto dei fabbricati; occupata/non occupata = collegamento famiglie-abitazioni) | CC BY 4.0 | 1/11/2026 (`raw/istat_abitazioni/Abitazioni-occupate-Anni-2021-2023.pdf`) |
| MEF-Dipartimento delle Finanze e Agenzia delle Entrate-OMI, "Gli immobili in Italia" 2019 (dati 2016), 2023 (dati 2020), 2026 (dati 2023) | uso delle abitazioni di proprieta' di persone fisiche, Milano: Tabella 1.10, Tabella 1.11 (2026), Tabella A1.14 (macroaree) | **nessuna licenza aperta**: il sito finanze.gov.it/it/copyright dice contenuti protetti, "autorizzati soltanto gli usi liberi consentiti dalla legge" (letto 1/11/2026). Nella pagina solo pochi numeri citati con la fonte; nessuna tabella copiata intera | 1/11/2026 (`raw/mef_immobili/`) |
| Agenzia delle Entrate, "Gli immobili in Italia" nota "L'utilizzo delle abitazioni in Italia" | non usata nei numeri | - | 1/11/2026 (`raw/agenzia_entrate/`) |
| Agenzia delle Entrate, Osservatorio Mercato Immobiliare, Rapporto residenziale 2024 | scaricato, **non usato** (e' sul mercato, non sull'uso) | - | 1/11/2026 |
| Comune di Milano, portale CKAN | ricerca con 11 parole chiave (`scripts/01_cerca_ckan.py`, `raw/ckan_ricerca.json`): **nessun dataset su case vuote / alloggi non occupati**; ci sono solo i censimenti (ds1522, ds1523, ds1639 record 1991/2001; ds362, ds384, ds385 indicatori 2011) gia' nel filone censimenti. ds964 (confini NIL) | CC BY | 1/11/2026 |
| Inside Airbnb, Milano, snapshot 19/9/2026 | solo aggregati per NIL dal filone `affitti-brevi/` (`pulito/nil_riepilogo.csv`, `crescita_nil.csv`) | CC BY 4.0, ma "Do not republish the data": nella pagina solo conteggi per quartiere | 1/11/2026 |
| Agenzia delle Entrate-OMI, quotazioni di compravendita, ultimo semestre | `docs/prezzi-case/data/zone.geojson` (42 zone), campo `compr_centro_reale_2025` | CC BY 4.0 (dal filone prezzi-case) | dal filone prezzi-case |
| Politecnico di Milano, comunicato stampa 29/4/2026 | contesto: "oltre 109.000 unita' ... vuote o occupate da non residenti" | non applicabile: solo citato (parafrasi) | 1/11/2026 |
| OpenStreetMap | sfondo mappa | ODbL | - |

## Cosa e' stato fatto (programmi, `python -I -X utf8 ... <percorsi assoluti>`)

- `scripts/01_cerca_ckan.py <file.json>`: cerca nel catalogo CKAN del Comune.
- `scripts/02_scarica_documenti.py <case-vuote>`: scarica i PDF pubblici (ISTAT, MEF/AdE, Politecnico) in `raw/` con User-Agent dichiarato e 3 s di pausa; log in `raw/download_log.csv`.
- `scripts/03_costruisci.py <case-vuote> <milano-in-dati>`: tabelle in `pulito/`: `citta_anni.csv` (con A3/A4/A6/A7 per 2001 e 2011), `nil_anni.csv` (88 NIL x 5 anni, distanza dal Duomo), `municipi_anni.csv`, `fasce_distanza_anni.csv`, `confronto_territori.csv`, `nil_confronti.csv` (Airbnb e prezzi per NIL), `agenzia_entrate_utilizzo_milano.csv` (24 numeri verificati sul testo dei PDF), `agenzia_entrate_macroaree_a_disposizione.csv`, `correlazioni.json`, `controlli.txt`. Si ferma se un controllo fallisce.
- `scripts/pagina.py <case-vuote> <milano-in-dati> <docs>`: scrive `docs/case-vuote/data/` (riepilogo.json con l'origine di ogni numero, nil.geojson, nil.csv, csv aggregati). Rilanciabile.
- Ordine: 01, 02, 03, pagina. Dipendenze: pandas, numpy, shapely 2, pyproj, scipy, PyMuPDF (pymupdf), openpyxl (per l'xlsx 2021).

## Controlli fatti (tutti in `pulito/controlli.txt`)

- Abitazioni per anno (somma delle sezioni) = `censimenti/pulito/indicatori_comune.csv`; non occupate = totale - occupate; 2001/2011: vuote + solo non residenti = non occupate; somma dei 88 NIL = totale del comune in tutti e 5 gli anni (differenza 0); somma dei 9 municipi = totale (non occupate) in tutti gli anni.
- Citta' metropolitana 2021 da sezioni (1.727.347 / 214.674) = ISTAT Prospetto 10; citta' metropolitana 2011 da sezioni: 1.440.651 abitazioni, 6,2% non occupate (non c'e' un numero ISTAT con cui confrontarla nei PDF letti).
- Numeri del volume MEF: ognuno cercato nel testo del PDF; somma delle voci = totale (632.361, 657.006, 677.685); famiglie Milano 2023 (743.276) = famiglie del censimento 2023; abitazioni totali 826.619 contro 827.648 del censimento (diff 1.029); (826.619-743.276)/826.619 = 10,1% come scritto nel volume.
- Annunci Airbnb: somma per NIL = 25.338 (snapshot 19/9/2026), case intere 22.309.

## Limiti dei dati (anche nella pagina)

1. Cambio di metodo nel 2021 (registri/catasto): 2011 e 2021 non si confrontano come aumento. Totale abitazioni +26% 2011-2021 contro famiglie +16,5%. Municipio 1: abitazioni +49%, Duomo +65% (8.745 -> 14.418): **ipotesi non verificata** che il catasto conti come abitazioni anche studi e uffici in edifici residenziali.
2. 2021 e 2023 sono stime del censimento permanente, non conteggi. Nei file 2021 e 2023 i due motivi (vuota / solo non residenti) non sono separati.
3. 2001 vs 2011: stessa distinzione, risultati molto diversi (29% vs 4% di "solo non residenti"): rilevazione instabile.
4. Quartieri: 1991 meno preciso (5,8% degli abitanti in sezioni con meno del 90% dell'area in un solo NIL; 2001 0,4%; 2011 0,1%). NIL con meno di 1.000 abitazioni in grigio sulla mappa; per correlazioni e classifiche solo 69 quartieri con almeno 2.000 abitazioni e 2.000 residenti (e almeno 500 abitazioni nel 1991 e 2011).
5. Distanza dal Duomo = in linea d'aria dal centroide del NIL; non e' la circonvallazione 90-91 del Politecnico ne' il Municipio 1.
6. Anni diversi: censimento 31/12; Airbnb 19/9/2026; AdE anno d'imposta 2023; prezzi ultimo semestre OMI. Airbnb: solo una piattaforma, posizione spostata fino a ~150 m, annuncio != casa.
7. MEF/AdE: solo abitazioni di persone fisiche (circa 678.000 nel 2023); uso da dichiarazioni dei redditi; no licenza aperta.
8. Correlazioni: Spearman su 69 quartieri, IC 95% con 5.000 ricampionamenti (seme 20261101). Dentro le fasce di distanza i quartieri sono pochi (8, 25, 21, 15).
9. Il numero "109.404" e' quello del comunicato Politecnico solo per coincidenza di cifra: il Politecnico non dichiara la fonte (non ho letto la dashboard Tableau).
10. Prezzo per NIL: media pesata sull'area delle zone OMI; 4 NIL con copertura OMI sotto il 70% non hanno prezzo.

## Non fatto / da decidere

- Dashboard Tableau del Politecnico non letta (nessun accesso programmatico, non aggirato).
- Nessuna fonte per distinguere seconde case da case di non residenti dopo il 2011; i dati IMU comunali (seconde case dichiarate) non cercati oltre una ricerca sul web (nessuna tabella per Milano trovata).
- Verificare con ISTAT/Catasto l'ipotesi "studi e uffici contati come abitazioni" nel centro.
- Stima 2021 -> 2023 per NIL con intervalli: la differenza e' piccola, non fatta.
- Licenza del volume MEF: chiedere conferma al Dipartimento se si volesse pubblicare di piu' (ora: pochi numeri citati).
