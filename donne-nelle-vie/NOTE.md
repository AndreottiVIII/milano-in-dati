# Donne nelle vie — NOTE fase 1 (scarico + primo conteggio)

Data di scarico: 2026-10-29. Tutto in `milano-in-dati/donne-nelle-vie/`. Nulla è stato pubblicato, nessun git.
Programmi in `scripts/` (numerati 01-09, si rilanciano in ordine). I dati scaricati sono in `raw/` (copie originali, non modificate). I file ricavati sono in `out/` e nella cartella principale.

## 1. Fonti scaricate

### 1.1 OpenStreetMap (strade e tag `name:etymology:wikidata`)
- **Come:** una sola richiesta Overpass (`https://overpass-api.de/api/interpreter`) sull'area del Comune di Milano (relazione amministrativa con `admin_level=8` e `wikidata=Q490`, quindi solo il comune, non la città metropolitana). Contenuto: tutte le `way` con `highway=*` e `name`, più `place=square` e le aree pedonali con nome. Il testo della richiesta è in `scripts/01_overpass.py`.
- **File:** `raw/osm/overpass_milano.json`, 11,26 MB. 31.950 elementi (31.886 `way`, 64 `relation`). Campo `osm3s.timestamp_osm_base` = **2026-10-29T14:21:50Z** (questo è il momento dei dati OSM).
- **Completezza:** una sola richiesta, finita senza errori. Tag tenuti: `name`, `name:etymology`, `name:etymology:wikidata`, `subject:wikidata`, `old_name`, `highway`, `loc_ref`, id dell'elemento (nel JSON c'è tutto).
- **Licenza:** ODbL (OpenStreetMap contributors). Si può ripubblicare, ma con la citazione e con la stessa licenza per i database derivati (obbligo "share-alike"). Regola del JOURNAL: nel repo meglio solo risultati e programmi, non il JSON grezzo.
- **Aggregazione:** `scripts/03_aggregate_osm.py` → `out/osm_strade_aggregate.csv` (una riga per nome). Campi: `name`, `n_elementi`, `highway`, `etymology_wikidata`, `loc_ref_codes`.

### 1.2 Wikidata (chi è la persona)
- **Come:** query SPARQL a `https://query.wikidata.org/sparql` con User-Agent proprio, blocchi di 150 QID (8 blocchi, pausa di 5 s). Campi chiesti: tipo (P31), sesso (P21), professioni in italiano (P106), anno di nascita (P569), anno di morte (P570), cittadinanza (P27), etichetta e descrizione in italiano. Programma: `scripts/04_wikidata_fetch.py`; lettura: `scripts/07_parse_wikidata.py`.
- **File:** `raw/wikidata/osm_etymology_batches/batch_000.json … batch_007.json` (circa 1,2 MB in tutto) → `out/etimologie_wikidata.csv` (0,15 MB, una riga per QID).
- **Completezza:** chiesti 1.173 QID (tutti i QID unici trovati nel campo `name:etymology:wikidata`, separati da `;`), ricevuti 1.173, nessuno mancante.
- **Licenza:** CC0 (pubblico dominio). Si può ripubblicare liberamente.
- **Secondo scarico, per il matching:** `raw/wikidata/matching_untagged/search_results.json` (1,4 MB, ricerca `wbsearchentities` per 3.047 nomi) e `entities.json` (2,4 MB, dettagli `wbgetentities` di 10.307 candidati). Stessa licenza CC0.

### 1.3 Comune di Milano — registro dei numeri civici (la fonte ufficiale)
- **URL:** `https://dati.comune.milano.it/dataset/ds634-numeri-civici-coordinate` (CKAN, API `package_show`). Risorsa CSV zip: `…/ds634_civici_coordinategeografiche_20261001_final_csv.zip` (4,35 MB). Ultimo aggiornamento sul portale: 2026-10-04, frequenza mensile.
- **File:** `raw/comune/ds634/ds634_civici_coordinategeografiche_20261001_final.csv` (21,90 MB, 65.160 righe = civici, 41 colonne, separatore `;`) e lo zip originale.
- **Cosa contiene (importante):** una riga per civico, ma ogni via ha un `CODICE_VIA` (numero ufficiale). Vie uniche per `CODICE_VIA`: **4.030**. Colonne utili: `CODICE_VIA`, `TIPO` (Via, Piazza, Viale…), `DENOMINAZIONE` (formato "COGNOME NOME", es. "GENTILE GIOVANNI"), `DESCRITTIVO` (formato "NOME COGNOME"), **`DATA_INTITOLAZIONE`** (formato AAAAMMGG), `STATOVIA` (sempre "Intitolata"), `ANNO_SOPPRESSIONE`.
- **Licenza:** CC BY (campo `license_id` = `cc-by` nella scheda CKAN). Si può ripubblicare citando il Comune di Milano.
- **Limite:** contiene solo le vie che hanno civici. Vie senza civici (alcune piazze, giardini, sottopassi) possono mancare. Nella tabella dei campi non ho trovato la spiegazione ufficiale di `DATA_INTITOLAZIONE` (il "Data Dictionary" della pagina si carica con JavaScript e non l'ho letto): quello che scrivo sulla data è dedotto dai dati.

### 1.4 Comune di Milano — vie e nomi storici (mappe dal 1884)
- **URL:** `https://dati.comune.milano.it/dataset/ds2914-vie-di-milano-e-corrispondenza-toponomastica-nelle-mappe-storiche-dal-1884`. File: `raw/comune/ds2914/ds2914_vie.csv` (0,01 MB). Licenza CC BY.
- **Contenuto:** solo una selezione di vie (progetto LetMi), con il nome in 10 mappe storiche (1884-2012). Non ha date di intitolazione né codice via (solo un `identificativo` interno). Utile solo come curiosità sui cambi di nome; non per la data.

### 1.5 Mapping Diversity (OBC Transeuropa / EDJNet) — solo per controllo incrociato
- **URL:** `https://github.com/EDJNet/mapping_diversity` (file `street names aggregate results.xlsx`), pagina del dataset `https://www.europeandatajournalism.eu/cp_dataset/street-names-in-european-cities/`. Scaricato in `raw/altri/mapping_diversity/`: l'xlsx (0,08 MB), `README.md`, `LICENSE.md`. È un file di sole somme per città (non vie una per una). I dati via-per-via sono su Google Sheet (non scaricati).
- **Licenza:** il repository GitHub dichiara CC BY 4.0; il testo del README dice a un certo punto CC BY-SA (incoerenza interna); nomi delle vie e dati geografici sono © OpenStreetMap (ODbL), dati Wikidata CC0. Per un confronto basta citare la fonte.
- **Dato per Milano** (`street_names_aggregate_results.xlsx`, fogli `overview` e `gender gap`, riga "Milano", febbraio 2023): vie totali **4.480**; vie dedicate a persone **2.677**; a uomini **2.523**; a donne **135** (5,04%); genere misto/incerto **19**. Persone uniche con Wikidata: 2.426.

### 1.6 Toponomastica femminile (associazione)
- Nessun file aperto scaricabile trovato (solo censimenti nei comunicati). Cifra riportata da un articolo de Il Giorno (visto solo come risultato di ricerca, non scaricato né verificato): censimento 2019, 4.250 strade a Milano, 2.538 a uomini, 141 a donne. Licenza dei loro dati: non trovata, da chiedere se servisse.

### 1.7 Ricerca di altre fonti sulle date di intitolazione
Sul portale `dati.comune.milano.it` ho cercato `stradario`, `toponomastica`, `viario`, `intitolazione`, `denominazione`, `toponimi`, `grafo stradale`, `arco viario`: i risultati sono solo gli "stradari elettorali" (strade con sezioni elettorali, nessuna data), i civici (ds634) e le mappe storiche (ds2914). Nessun registro separato con delibere. Nessuna fonte ha richiesto registrazione.

## 2. Data di intitolazione: esiste?
**Sì, in parte.** Il campo `DATA_INTITOLAZIONE` di ds634 è compilato per **1.232 vie su 4.030 (30,6%)**; per le altre 2.798 è vuoto (file `raw/comune/ds634/…csv`, campo `DATA_INTITOLAZIONE`, righe uniche per `CODICE_VIA`). Mancano soprattutto le vie storiche (Manzoni, Dante, Garibaldi, Verdi non hanno data). Sono segnaposto 14 valori: `17000101` (Piazza del Duomo) e 13 valori `19000101` (= "prima del 1900", presumibilmente). Le date più comuni sono dal 1921 al 1930. Nel 2017 o dopo risultano 23 vie con data. **Chiave per unire con OSM:** il tag OSM `loc_ref` ha la forma `CODICE_VIA_progressivo` (es. `7238_35162`): la prima parte è il `CODICE_VIA` del Comune. Su 4.030 vie del Comune, 3.979 si agganciano al codice; 4.012 con codice o nome (18 non risultano in OSM). Lo scrive `out/strade_unite.csv` (campo `in_osm`).
Nel registro Comune le vie dedicate a donne (con la nostra classificazione) sono 104 e di queste solo 29 hanno la data (`strade_persone.csv`, campi `sesso` e `data_intitolazione`).

## 3. Copertura (primo conteggio grezzo)
Tutti i numeri vengono da `copertura.json` (calcolato da `scripts/09_coverage.py` sul file `strade_persone.csv`). Il file `out/strade_unite.csv` unisce registro Comune e OSM.

**Quante strade ci sono**
- Nomi unici in OSM (`out/osm_strade_aggregate.csv`, campo `name`): **5.168**. Includono anche sentieri, marciapiedi, banchine, ecc.
- Vie nel registro del Comune (ds634, `CODICE_VIA`): **4.030**.
- Nomi presenti solo in OSM: 1.061, ma solo 250 sono vere strade (residenziali, secondarie, piazze, pedonali); gli altri 811 sono soprattutto `footway` (560) e `platform` (141).
- **Universo di lavoro** ("core"): 4.030 + 250 = **4.280**.

**Con il tag OSM (`name:etymology:wikidata`)**
- Nomi unici OSM con il tag: **1.186** (`out/osm_strade_aggregate.csv`, campo `etymology_wikidata` non vuoto). Elementi con il tag: 10.846 su 31.950.
- Nell'universo di lavoro: **1.202 strade con tag (28,1%)**, 3.078 senza.
- Dei 1.202 tag: **882** puntano a una persona (Wikidata P31 = essere umano, più 4 "esistenza discussa" come Omero e Alberto da Giussano); **874** con sesso noto (`strade_persone.csv`, campo `sesso`); 8 con più persone di sesso diverso o sesso non indicato; **320** puntano a luoghi o altro (non persone: comuni, fiumi, quartieri, specie…).
- Sesso tra le 874: **28 donne**, **846 uomini**.
- Persone uniche nei tag: 826 QID umani su 1.173 QID unici (`out/etimologie_wikidata.csv`, campo `umano`): 30 donne, 796 uomini. (La differenza con le 28 strade deriva da donne con una sola strada o con più strade/tag.)

**Senza tag: 3.078 strade, primo giro di matching** (`matching_candidati.csv`, campi `categoria` e `confidenza`)
- **sicuro: 756** (un solo umano con nome identico o chiaramente prevalente): 33 donne, 722 uomini, 1 sesso non indicato.
- **incerto: 692** (omonimi, nome parziale, o legame con l'Italia non chiaro): sesso del primo candidato 53 donne, 632 uomini, 7 non indicato.
- **nessuno: 1.630**, di cui: 419 luoghi (comune, fiume…), 16 date/eventi, 404 altra cosa non umana su Wikidata, **791 senza alcun candidato** (non si sa se persone o luoghi).
- Quindi "chiaramente non persone" in tutto: 320 (tag) + 419 + 16 + 404 = **1.159** strade (l'ultimo gruppo di 404 è "altra cosa non umana", meno sicuro).

**Conta grezza donne/uomini** (solo tag + match "sicuro", senza gli incerti): **61 donne e 1.568 uomini**, cioè 3,7% donne su 1.629 persone trovate. Se si aggiungono i primi candidati degli "incerti": +53 donne, +632 uomini. Per confronto Mapping Diversity (feb 2023, controllo manuale): 135 donne su 2.677 vie dedicate a persone (5,04%) e il registro Comune ne conta 104 con la nostra classificazione: la nostra cifra è per ora **sicuramente troppo bassa** per le donne (vedi limiti).

## 4. Trappole dei dati (problemi trovati)
1. **Il tag OSM non è completo né sempre una persona.** Solo 28% delle strade ha il tag; di quelle che lo hanno, 27% (320/1.202) non punta a una persona. Un tag può contenere più QID: 149 strade ne hanno più di uno (es. "Gioacchino Murat" con due QID; "Della Scala" con due; "Sesto San Giovanni" due).
2. **Un nome OSM non è una strada.** 5.168 "nomi" ma 4.280 strade vere; la stessa via può avere più `way` e anche nomi leggermente diversi (es. "Via Johann Gutemberg" e "Via Johannes Gutenberg" compaiono insieme come strade separate solo in OSM). 704 nomi OSM hanno più di un codice `loc_ref`; ci sono codici non nel registro ufficiale (205 su 4.184 codici distinti, fra cui `-9999` e `100058`).
3. **Il registro del Comune ha due ordini del nome:** `DENOMINAZIONE` = "COGNOME NOME", `DESCRITTIVO` = "NOME COGNOME", e usa maiuscole, apostrofi al posto degli accenti ("NICCOLO'") e parentesi per particelle ("VIVARINI (F.LLI)"). Per cercare su Wikidata serve il `DESCRITTIVO`.
4. **Data di intitolazione presente solo per il 31% delle vie**, con 14 valori segnaposto (1700-01-01, 1900-01-01), vuota proprio per le vie storiche. Per le donne sono 29 su 104.
5. **Wikidata:** 5 elementi su 1.173 non hanno etichetta in italiano né in inglese (la query restituisce il codice QID come nome, es. Q7186 = Marie Curie); 12 persone senza anno di nascita, 10 senza anno di morte, 10 senza professione. Le professioni sono molte e disordinate (Santa Cecilia = "musicista"; Caterina Sforza = "scrittore, politico"). "Fratelli X" o famiglie (Della Scala, Visconti) non sono persone singole.
6. **Matching dei senza tag (primo giro):** funziona bene sui nomi completi (Nome Cognome), male su titoli e nomi parziali: "Via Don Carlo Porro", "Fra Giovanni Pantaleo", "Padre G.B. Martini", "Madre Cabrini" (trovata), "Via del Caravaggio", "Via Piermarini" ricadono in "nessuno" o in "incerto". I santi e le sante ("Santa Lucia", "San Clemente") sono difficili da distinguere da chiese e luoghi. Alcuni "sicuri" potrebbero comunque essere omonimi sbagliati: il controllo manuale resta da fare. Le strade intitolate a donne con ruolo religioso o titolo (Santa, Madre, Regina, Suor) sono quelle più perse.
7. **Mapping Diversity ha cifre diverse dalle nostre** (4.480 vie, 135 donne, febbraio 2023) perché usa altro metodo e altra data: confrontare con cautela. Il Giorno/Toponomastica femminile danno 141 donne su 4.250 (2019).
8. **Overpass:** il timestamp dei dati OSM è del 29/10/2026 14:21 UTC; tra qualche mese i conteggi dei tag cambieranno (OSM è modificato di continuo). Da citare sempre con la data.

## 5. File prodotti (cartella `donne-nelle-vie/`)
| File | Contenuto | MB |
|---|---|---|
| `raw/osm/overpass_milano.json` | risposta Overpass grezza | 11,26 |
| `raw/wikidata/osm_etymology_batches/` | 8 risposte SPARQL grezze | 1,2 |
| `raw/wikidata/matching_untagged/` | ricerca e dettagli per il matching | 3,7 |
| `raw/comune/ds634/` | civici Comune (CSV + zip) | 26,25 |
| `raw/comune/ds2914/ds2914_vie.csv` | vie e mappe storiche | 0,01 |
| `raw/altri/mapping_diversity/` | xlsx + README + licenza | 0,10 |
| `out/osm_strade_aggregate.csv` | 5.168 nomi unici OSM | 0,42 |
| `out/etimologie_wikidata.csv` | 1.173 QID: sesso, professioni, anni | 0,15 |
| `out/strade_unite.csv` | 5.091 righe: registro Comune + solo OSM | 0,45 |
| `matching_candidati.csv` | 3.078 strade senza tag: candidato, motivo, confidenza | 0,53 |
| `strade_persone.csv` | tabella unica: strada, persona, sesso, anni, data intitolazione, fonte | 0,69 |
| `copertura.json` | tutti i conteggi di questa nota | <0,01 |

## 6. Da decidere / prossimi passi suggeriti (non fatti)
- Secondo giro sul matching togliendo i titoli (Don, Fra, Padre, Madre, San/Santa, Beato) e provando le due varianti del nome.
- Controllo manuale degli incerti, partendo dai 53 con primo candidato donna, e delle 33+28 donne trovate.
- Per ogni donna: professione leggibile (le professioni Wikidata vanno raggruppate in poche categorie).
- Data di intitolazione solo dove c'è (30,6%): decidere se basta o se cercare le delibere altrove.
