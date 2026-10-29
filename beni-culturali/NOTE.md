# Beni culturali di Milano (Catalogo generale ICCD / ArCo) - note della fase 1

Data del lavoro: 2026-10-29. Fase 1 = solo scarico e controlli di completezza, nessuna analisi.

## In breve

- Fonte scelta: **dump ArCo 2.0 del 1 dicembre 2023** (grafo di conoscenza del Catalogo generale dei beni culturali, ICCD), scaricato da `http://arco.istc.cnr.it/arco-data/2.0/` (server del CNR-ISTC). E' l'ultima versione pubblica che ho trovato.
- Nel dump ci sono **2.640.709 schede** in tutta Italia (file `work/conteggi_nazionali.json`, campo `proprieta_nazionali_totale`).
- **Milano**: `beni_culturali_milano.csv` ha **30.721 schede**, divise in due gruppi (campo `ambito`):
  - **27.459 `sede_milano`**: il bene e' a Milano (campo riassuntivo `dc:coverage` = "Milano (MI)" e indirizzo del bene = Comune di Milano). E' il numero da usare come "schede di Milano".
  - **3.262 `solo_luogo_collegato`**: il bene NON e' a Milano, ma una sua localizzazione "altra" (luogo di fabbricazione, di ritrovamento, collocazione precedente o successiva) e' a Milano. Esempio: una coppa del Museo della Valle di Formazza fatta a Milano. Vanno tenute a parte.
- Il dato e' fermo al **2022-2023** (colonna `ultimo_aggiornamento`: 26.806 schede del 2022 e 653 del 2023 tra le `sede_milano`). Il catalogo vivo, oggi, e' piu' avanti e non si riesce a raggiungerlo (vedi "Cosa non ho potuto fare").
- Licenza: vedi sezione apposita. Sintesi: metadati CC BY 4.0 dichiarati dal catalogo, ma il grafo ArCo e' pubblicato altrove come CC BY-SA 4.0. Nessuna immagine scaricata.

## Fonti confrontate

| Fonte | Esito | Note |
|---|---|---|
| Endpoint SPARQL `dati.beniculturali.it/sparql` | **Non raggiungibile**: il nome non esiste piu' nel DNS (risposta NXDOMAIN da 8.8.8.8, 1.1.1.1 e Cloudflare, 2026-10-29) | Stessa cosa per `dati.cultura.gov.it`, `sparql.dati.cultura.gov.it`, `arco.beniculturali.it`. Quindi niente interrogazioni a pagine (LIMIT/OFFSET): non c'e' a chi farle. |
| Catalogo `catalogo.beniculturali.it` / `catalogo.cultura.gov.it` (con sezione OpenICCD `/opendata/`) | **Bloccato da un controllo anti-bot** (Anubis, "Making sure you're not a bot!", risposta HTTP 401/403) | Non ho aggirato il controllo (regola: niente bot-detection). Nessun download da qui. Non ho creato account e nessuno e' stato richiesto. |
| Zenodo, ArCo Knowledge Graph v1.0 (2019-04-05), record 3242580 | Non scaricato | 3,7 GB, licenza CC BY-SA 4.0. Obsoleto. |
| Zenodo, ArCo v0.1 (giugno 2020), record 3872004 | Non scaricato | 285,6 MB, CC BY-SA 4.0. Obsoleto. |
| CNR-ISTC `arco-data/1.1` (2020-10-29) | Non scaricato | un solo file di 5.121.864.209 byte (`Content-Length`) |
| CNR-ISTC `arco-data/1.2` (2021-01-10) | Non scaricato | circa 5,9 GB (43 parti) |
| **CNR-ISTC `arco-data/2.0` (2023-12-01)** | **SCARICATO** | 97 parti + indice. Il file unico `arco-knowledge-graph-2.0.nt.gz` da 13 GB non e' stato scaricato (stesso contenuto delle parti). |
| GitHub `ICCD-MiBACT/ArCo` | Solo lettura di testi | Il codice e' attivo (ultimi commit 2026-10-19), ma non ci sono release dati dopo il dump 2.0: `KG_release_notes.md` si ferma alla 1.1 e la cartella `release_notes` ha solo `1.1.md`. |

Conteggi per Milano per fonte: solo il dump 2.0 e' stato letto, quindi **30.721 (27.459 + 3.262)** e' l'unico conteggio. Le versioni 1.x e 0.x non le ho scaricate (piu' vecchie e piu' piccole: 5,1 e 5,9 GB contro 14,2 GB di oggi) e non ho un numero di Milano per loro. Per confronto: il lavoro scientifico del 2019 parla di circa 820.000 entita' nel grafo, il dump 2.0 ne ha 2.640.709.

## Cosa ho scaricato

Cartella `raw\arco-2.0\` (dati grezzi, non toccati):

- `arco-knowledge-graph-2.0_part_0.nt.gz` ... `_part_96.nt.gz`: 97 file, **14.236.239.680 byte (circa 13,3 GiB, 13.577 MB per `du`)**. Ogni file e' un pezzo di RDF in formato N-Triples compresso; le prime 96 parti hanno 10.000.000 di righe ciascuna, la parte 96 e' piu' piccola (96,9 MB). Righe totali lette: **966.591.725** (`logs/estrazione2.log`, seconda colonna).
- `index.txt` (3.773 byte): elenco dei file, copia dall'indice del server.
- Verifica: ogni parte ha la dimensione attesa (`Content-Length` del server, `logs/download.log`), tutte sono state lette per intero senza errori di compressione, SHA-256 in `logs/sha256_arco2.0.txt`.
- Non scaricato: `quarantine.nt.gz` (18 MB, triple scartate dal controllo di qualita' di ArCo): non serve.

Come: `scripts\01_download_arco20.sh` (una parte alla volta, pausa di 1 s, ripresa se interrotto), partito alle 15:24 e finito alle 16:30.

## File prodotti

| File | Cosa contiene |
|---|---|
| `beni_culturali_milano.csv` (18,3 MB, 30.721 righe, UTF-8) | una riga per scheda di Milano; colonne qui sotto |
| `controlli_completezza.txt` | tutti i conteggi di questa nota |
| `controllo_istituzioni.txt` | controllo: le istituzioni milanesi hanno schede fuori dall'elenco? |
| `work\conteggi_nazionali.json` | conteggi Italia per classe di bene |
| `work\tsv\` (6,9 GB, 97 file) | passaggio intermedio: solo i triple utili, riscrivibile in circa 10 minuti con `scripts\02_estrai_triple.py`; si puo' cancellare |
| `scripts\` | 01 scarico, 02 estrazione, 03 costruzione tabella, 04 controlli, 05 verifica istituzioni, 00 lancio automatico |
| `logs\` | log di scarico e di esecuzione, SHA-256 |

Colonne del CSV: `iri` (identificativo unico della scheda nel grafo, da usare come chiave), `id` (numero di catalogo generale, NON unico), `ambito`, `classe_bene`, `tipo_scheda`, `codice_catalogo` (ICCD...), `url_catalogo` (pagina della scheda), `titolo`, `tipo_oggetto`, `soggetto`, `autore`, `datazione`, `materia_tecnica`, `categoria_catalogazione`, `diritti` (proprieta' del bene, non licenza), `copertura_dc`, quattro colonne 0/1 per i criteri di Milano (`cov_milano`, `indirizzo_milano`, `loc_attuale_mi`, `loc_altra_mi`), `indirizzo_bene`, `localizzazione_attuale`, `altre_localizzazioni`, `istituzione`, `codice_sito`, `lat`, `long`, `ultimo_aggiornamento`, `ente_catalogatore` (codice, non nome).

### Come ho deciso che una scheda e' "di Milano"

Il dump e' un grafo: la localizzazione e' una catena (bene -> localizzazione nel tempo -> luogo o sito -> indirizzo -> comune). Ho seguito la catena con lo script `03_milano.py` e salvato quattro criteri separati:

1. `cov_milano`: il campo riassuntivo `dc:coverage` e' esattamente "Milano (MI)" (27.459 schede in tutta Italia, `logs\milano3.log`).
2. `indirizzo_milano`: l'indirizzo del bene (`hasCulturalPropertyAddress`) ha `clv:hasCity` = `City/milano`. Si usa il **comune** (City), non la provincia: i comuni della provincia di Milano (Sesto San Giovanni, Rho...) restano fuori.
3. `loc_attuale_mi`: la localizzazione fisica attuale (`CurrentPhysicalLocation`) porta a un indirizzo del Comune di Milano (15.788 schede).
4. `loc_altra_mi`: una localizzazione di altro tipo (precedente, ritrovamento, fabbricazione...) porta a Milano, sia da luoghi (`Feature`) sia da siti (`Site`).

`sede_milano` = almeno uno tra 1, 2, 3. Nei dati i tre criteri coincidono quasi sempre: tutte le schede con criterio 1 hanno anche il 2, e tutte quelle con criterio 3 hanno anche 1 e 2 (`controlli_completezza.txt`, righe "di cui ...").

Controllo "oggetti in musei milanesi ma venuti da fuori": `controllo_istituzioni.txt` mostra che le istituzioni milanesi (Brera, Castello Sforzesco, Poldi Pezzoli, Bertarelli, Villa Necchi, ecc.) hanno tutte le loro schede dentro l'elenco (fuori = 0). Le uniche eccezioni sono istituzioni che hanno sedi in piu' citta': Archivio Franca Rame Dario Fo (764 a Milano, 170 a Verona), Pinacoteca Civica Alberto Martini (261 a Milano, 216 a Oderzo). Quelle fuori Milano sono giustamente escluse.

## Conteggi (campo `tipo_scheda`, solo `sede_milano`, 27.459)

Il tipo di scheda e' preso dal nome della scheda collegata (`CatalogueRecordOA`, `...D`, ecc.) in `dc:source`; nelle 30.721 righe non e' mai vuoto.

| Tipo | Schede | | Tipo | Schede |
|---|---|---|---|---|
| OA (opere d'arte) | 17.292 | | OAC | 166 |
| D (disegni) | 4.464 | | MA | 38 |
| RA (reperti archeologici) | 2.204 | | F (fotografie) | 36 |
| S (stampe) | 1.578 | | NU (numismatica) | 16 |
| PST (strumenti scientifici) | 788 | | CA | 11 |
| A (architettura) | 665 | | PG | 2 |
| BDM (demoetnoantropologici) | 199 | | | |

Fonte: `controlli_completezza.txt`, sezione "SOLO sede_milano: PER TIPO DI SCHEDA". Il totale 27.459 e' la somma. Le sigle sono quelle delle schede ICCD: disegni `D` e stampe `S` sono schede a parte rispetto a OA.

Per classe del bene (percorso nell'IRI): HistoricOrArtisticProperty 23.500, ArchaeologicalProperty 2.253, ScientificOrTechnologicalHeritage 788, ArchitecturalOrLandscapeHeritage 667, DemoEthnoAnthropologicalHeritage 199, PhotographicHeritage 36, NumismaticProperty 16. (`controlli_completezza.txt`, sezione "SOLO sede_milano: PER CLASSE DEL BENE").

### Primi 20 detentori (campo `istituzione`, `sede_milano`)

| Istituzione | Schede |
|---|---|
| `CulturalInstituteOrSite/DBunicoCG106788` (nome non presente nel dump) | 3.195 |
| Raccolte storiche dell'Accademia di Brera | 1.593 |
| Civica Raccolta delle Stampe "Achille Bertarelli" | 1.256 |
| Raccolte Grafiche e Fotografiche del Castello Sforzesco | 1.137 |
| Raccolte Artistiche del Castello Sforzesco | 1.081 |
| Museo Poldi Pezzoli | 1.076 |
| Museo Archeologico | 636 |
| Villa Necchi Campiglio | 633 |
| Museo Teatrale alla Scala, medagliere Eisner von Eisenhof Angelo | 322 |
| Collezione Istituto dei Ciechi di Milano | 236 |
| Collezione Torno | 211 |
| Soprintendenza Archeologica | 206 |
| Museo Teatrale alla Scala | 93 |
| Polo del Novecento e Arte Contemporanea | 84 |
| `CulturalInstituteOrSite/ICCD_CG_7658429273461` (senza nome) | 67 |
| Pinacoteca di Brera Archivio Cagnola | 19 |
| Fondo Alfredo Coppola, scatola 2 | 11 |
| Pinacoteca di Brera Collezione Vitali | 5 |
| Collezione dell'Accademia di Belle Arti di Brera | 3 |
| Universita' degli Studi di Milano | 2 |

Fonte: `controlli_completezza.txt`, sezione "SOLO sede_milano: PRIMI 20 ISTITUZIONI". Attenzione: il nome e' il campo `istituzione`, una stessa raccolta puo' comparire con identificatori diversi, quindi alcune righe vanno unite.

### Campi mancanti (`sede_milano`, 27.459 schede)

| Campo | Mancano | % |
|---|---|---|
| titolo (`dc:title`) | 0 | 0,0 |
| datazione (`dc:date`) | 1.543 | 5,6 |
| autore (`dc:creator`/`pico:author`) | 14.565 | 53,0 |
| soggetto | 183 | 0,7 |
| materia/tecnica | 732 | 2,7 |
| localizzazione fisica attuale (`CurrentPhysicalLocation`) | 11.671 | 42,5 |
| coordinate (lat/long) | 14.265 | 52,0 |
| istituzione detentrice | 15.587 | 56,8 |
| link alla pagina del catalogo | 0 | 0,0 |

Fonte: `controlli_completezza.txt`, sezione "SOLO sede_milano: CAMPI MANCANTI". "Autore mancante" e' normale: molti beni (reperti, architetture, stampe anonime) non hanno autore.

## Licenza (cosa so e cosa no)

Trovati tre testi diversi:

1. **Pagina del catalogo** (`catalogo.cultura.gov.it`, letta solo tramite un motore di ricerca perche' il sito e' dietro il controllo anti-bot): "LICENZA METADATI CC-BY 4.0". Cioe' i metadati delle schede sono attribuzione semplice.
2. **Zenodo** (ArCo Knowledge Graph v1.0 2019 e v0.1 2020, record 3242580 e 3872004): licenza **CC BY-SA 4.0**. Un articolo del 2024 (GARR) dice lo stesso del nodo di grafo costruito sul dataset ICCD. La pagina del singolo record sul sito lodview dell'ICCD risulta anch'essa CC BY-SA 4.0, con "eccezioni".
3. **Ontologia ArCo** (file `arco.owl` nel repository GitHub, ultima modifica 2023-12-01 = data del dump): `dct:license` CC BY 4.0.

Il dump 2.0 in se' non contiene dichiarazioni di licenza (ho cercato "licen" e "creativecommons" nelle parti 0 e 3: nessun triple di licenza, solo parole italiane nei testi).

Quindi la sintesi onesta e': **metadati CC BY 4.0 secondo il catalogo; CC BY-SA 4.0 secondo la pubblicazione ArCo su Zenodo e sul sito ICCD**. Non l'ho risolto. Le immagini possono avere condizioni diverse (non le abbiamo scaricate; la colonna immagine non e' nel CSV).

Ripubblicare nel repo pubblico: i dati sono aperti e riusabili con **citazione della fonte** (ICCD - Catalogo generale dei beni culturali, ArCo). Per stare sul sicuro conviene ripubblicare **solo il CSV derivato** (non i 14 GB di grezzi), dichiarare **CC BY-SA 4.0** (la piu' restrittiva tra le due, compatibile con la CC BY) e linkare le pagine originali. Il testo preciso della licenza va confermato dall'ICCD (indirizzo indicato dal sito del Ministero: redazione.mic@cultura.gov.it) o aprendo a mano la pagina "Termini d'uso" del catalogo in un browser. **Questa decisione resta al coordinatore.**

## Trappole dei dati (tutte verificate)

1. **Gli indirizzi sono quasi sempre solo "Milano".** Tra le `sede_milano`, 12.845 + 10.456 + 2.158 + 199 hanno un indirizzo del bene fatto solo da "Italia, Lombardia, MI, Milano" (varianti di maiuscole); solo 1.745 contengono una via o piazza (`indirizzo_bene`, ricerca di via/piazza/corso). La piazza Castello (Castello Sforzesco) da sola vale 1.141 schede. Quindi niente mappa dettagliata dai soli indirizzi: gli indirizzi precisi sono nelle istituzioni, che nel dump hanno solo il nome (e a volte neppure quello).
2. **Il numero di catalogo `id` non e' unico**: 4.366 righe condividono l'`id` con un'altra (esempio: `0100127418-2`, `-21`, `-23`, `-24` sono parti dello stesso bene, tutte con `id` 0100127418). La chiave giusta e' `iri` (zero duplicati) oppure `codice_catalogo`/`url_catalogo` (zero duplicati).
3. **Il dump ha moltissime righe doppie**: 966.591.725 righe lette, ma dopo avere tolto le doppie nei triple che ci servono ne restano 83.583.345 (circa 850.000 per parte; somma della terza colonna di `logs/estrazione2.log`). Lo stesso fatto e' ripetuto decine di volte, quindi non si possono contare le righe grezze.
4. **Un bene e' sparso su piu' parti del dump**: i triple di una scheda stanno in file diversi. Non basta cercare "Milano" in una parte: serve leggere tutte le 97 e unire.
5. **`dc:coverage` e `localizzazione fisica attuale` non coincidono**: 11.671 schede `sede_milano` hanno `dc:coverage` Milano ma nessuna localizzazione attuale che arrivi a un indirizzo di Milano. Tutte e 11.671 hanno invece un "sito" con un codice numerico (colonna `codice_sito`) che nel dump non ha nome ne' indirizzo. Per questo ho usato `dc:coverage`+indirizzo come criterio principale e non la sola localizzazione.
6. **Istituzione senza nome**: 3.195 schede (la voce piu' grande) hanno come istituzione solo `CulturalInstituteOrSite/DBunicoCG106788`, senza etichetta nel dump. Sono 2.863 dipinti OA e 332 disegni D (ad esempio Hayez, Voghera), catalogati dall'ente `033c02867cc5...`: probabilmente raccolta di Brera, ma e' una mia ipotesi, non scritta nel dump. Idem `ICCD_CG_7658429273461` (67). In totale il 56,8% delle `sede_milano` non ha istituzione.
7. **Coordinate con latitudine e longitudine scambiate**: su 13.194 schede con coordinate, 2 sono fuori dal rettangolo di Milano perche' invertite (es. scheda 0300101865 Palazzo Gallarati Scotti: lat 9,19 e long 45,47). Le altre 13.192 cadono nel rettangolo 45,38-45,54 N / 9,04-9,28 E.
8. **Ente catalogatore e istituzioni: solo codici/hash** (`ente_catalogatore` e' un codice di 32 caratteri); i nomi stanno in altre parti del grafo che non ho estratto. Il piu' frequente (19.287 schede) ha come nome, nelle schede che ho visto a campione, la Soprintendenza per i beni storici artistici ed etnoantropologici per le province di Milano e di altre (scheda 0300004394).
9. **Titoli con aggiunte tra parentesi**: il titolo `dc:title` include la forma della catalogazione, es. "dipinto (opera isolata)", "capitello composito (serie)", oppure frasi molto lunghe. Per i nomi puliti usare `tipo_oggetto` e `categoria_catalogazione`.
10. **Tipo scheda `D`, `S`, `OAC`**: in ArCo sono tipi diversi da OA; se si vuole "opere d'arte" nel senso comune vanno sommati OA, D, S (circa 23.300). Decisione per la fase 2.
11. **Il sito DNS `dati.beniculturali.it` e' sparito**: tutti i link di vecchi articoli e README (`dati.beniculturali.it/arco`, `.../sparql`) sono morti. Nel dump restano migliaia di URI `http://dati.beniculturali.it/iccd/cf/resource/CulturalInstituteOrSite/<numero>` che non portano piu' a nulla.
12. **Link di catalogo**: `url_catalogo` e' del tipo `http://www.catalogo.beniculturali.it/sigecSSU_FE/dettaglioScheda.action?keycode=ICCD...` (indirizzo vecchio, per ora il nome esiste ancora nel DNS ma e' dietro il controllo anti-bot). Il nuovo sito e' `catalogo.cultura.gov.it`; il formato dei nuovi indirizzi di scheda non e' verificato.
13. **Le 3.262 `solo_luogo_collegato` sono beni di altre citta'**: per tipo sono OA 1.447, D 1.407, F 237, S 74, BDM 62, PST 16, RA 14, altri 5. Le fotografie (F) sono 237 di questo gruppo contro 36 di `sede_milano`: Milano e' spesso solo il luogo della ripresa. Non contarle come patrimonio "di Milano".
14. **Aggiornamento**: il dump e' del 2023-12-01 ma le schede sono state aggiornate l'ultima volta nel 2022 o 2023 (colonna `ultimo_aggiornamento`). Il catalogo di oggi ha certamente piu' schede.

## Cosa non ho potuto fare

- Nessun accesso all'endpoint SPARQL (non esiste piu' nel DNS) e nessun download diretto dal catalogo (controllo anti-bot Anubis, non aggirato). Quindi non so quante schede di Milano ci sono oggi nel catalogo vivo, solo nel dump di fine 2023. Se serve il dato piu' recente, un essere umano puo' aprire `catalogo.cultura.gov.it` nel browser, oppure scrivere a redazione.mic@cultura.gov.it chiedendo un dump piu' nuovo.
- Nessun conteggio per Milano delle versioni vecchie del grafo (non scaricate).
- Nessun nome per gli enti catalogatori e per alcuni istituti (mancano nel dump).
- Nessuna immagine scaricata (come richiesto).
- Nessun account creato; nessun sito ha chiesto registrazione.
- Nessun git, nessuna pubblicazione.

## Come rifare tutto

```
bash scripts/01_download_arco20.sh raw/arco-2.0
python -I scripts/02_estrai_triple.py raw/arco-2.0 work/tsv 8 logs/download.log
python -I scripts/03_milano.py work/tsv beni_culturali_milano.csv work/conteggi_nazionali.json
python -I scripts/04_controlli.py beni_culturali_milano.csv work/conteggi_nazionali.json controlli_completezza.txt
python -I scripts/05_verifica_istituzioni.py work/tsv beni_culturali_milano.csv controllo_istituzioni.txt
```

Tempi: scarico circa 66 minuti, estrazione circa 10 minuti, tabella Milano circa 10 minuti, 7-8 GB di RAM al massimo.

---

# Fase 2 (2026-10-29): pulizia e prima pagina

Licenza deciso da Davide: dati derivati ripubblicati con **CC BY-SA 4.0**, con citazione dell'ICCD (Istituto Centrale per il Catalogo e la Documentazione) e di ArCo 2.0 (CNR-ISTC, dump del 2023-12-01). Programmi: `scripts\06_pulisci.py` (pulizia), `scripts\07_pagina.py` + `scripts\pagina_template.html` (pagina). Nessun git, niente online: i file sono solo sul PC.

## Che cosa e' stato fatto

- **File pulito**: `pulito\beni_milano.csv`, 30.721 righe, una per scheda, chiave `iri` (mai `id`). Il file della fase 1 non e' stato toccato.
- **Righe doppie**: nessuna rimasta (`iri` e codice di catalogo sono unici). I doppioni veri erano nel dump e sono stati tolti in fase 1. Sono stati tolti solo i valori ripetuti dentro un campo (6 titoli, 7 date, 5 materie).
- **Problemi trovati**: tutti in `pulito\problemi.md` ("trappole dei dati", 34 punti con i numeri) e, come conteggi, in `pulito\problemi_conteggi.json`.
- **Pagina**: `..\docs\beni-culturali\index.html` con i dati in `..\docs\beni-culturali\data\` (`oggetti.json` 3,0 MB, `punti.json` 0,13 MB, `beni_milano.csv.gz` 1,4 MB, `numeri.json`, `problemi.md`).

## Che cosa c'e' nel file pulito

Per ogni scheda: tipo di scheda (sigla + nome in italiano), titolo pulito, soggetto, autori (nomi uniti e messi in ordine uguale; l'originale resta in `autore_originale`; le qualifiche tipo "attribuito" in `autore_qualifica`), data (testo + anno di inizio e di fine + secolo), materia e tecnica, detentore, luogo attuale e indirizzo, coordinate corrette e segnate se dentro il Comune, link al catalogo, e il segno `sede_milano` (1 = il bene e' a Milano, 0 = solo luogo collegato).

## Numeri principali (27.459 schede con sede a Milano)

Fonte: `..\docs\beni-culturali\data\numeri.json`, calcolati da `pulito\beni_milano.csv`.

| Cosa | Schede | Quota |
|---|---|---|
| autore indicato | 12.894 | 47,0% (manca nel 53,0%) |
| data indicata | 25.916 | 94,4% |
| detentore con nome | 8.610 | 31,4% (manca nel 68,6%) |
| luogo con nome o via | 5.945 | 21,7% |
| solo "Milano" come luogo | 10.799 | 39,3% |
| nessun luogo | 10.715 | 39,0% |
| coordinate dentro il Comune | 13.193 | 48,0% (mancano nel 52,0%) |

Tipi: OA 17.292, D 4.464, RA 2.204, S 1.578, PST 788, A 665, BDM 199, OAC 166, MA 38, F 36, NU 16, CA 11, PG 2. Autori distinti: 3.192. Punti sulla mappa: 769.

Rispetto alla fase 1: autore mancante 53,0% (uguale), coordinate mancanti 52,0% (uguale). La "localizzazione fisica attuale mancante 42,5%" della fase 1 qui non c'e': ora si guarda se il luogo e' piu' preciso di "Milano" (sito o via), che e' il 21,7% presente, perche' il campo della fase 1 era riempito anche con la sola scritta "Milano".

## Decisioni prese e cose da sapere

- **Detentore senza nome**: i 3.262 codici senza etichetta (3.195 + 67) sono stati cercati in tutte le 97 parti del dump: nessun nome. I 3.195 hanno tutti le coordinate di Brera, ma non e' scritto: nel file resta "non indicata" e il codice e' in `istituzione_iri`.
- **Coordinate**: le 2 con latitudine e longitudine scambiate sono state rimesse a posto. Controllo fatto sul confine vero del Comune (poligono in `..\citta-15-minuti\raw\comune_milano\confine_comune\`, non un rettangolo): 13.193 dentro, 1 fuori (Cascina Mirabello, scheda `ArchitecturalOrLandscapeHeritage/0300101875`, a circa 18 km: coordinata sbagliata, non disegnata).
- **Le coordinate sono del museo, non dell'oggetto**: 769 punti per 13.193 schede.
- **Link al catalogo**: nel file pulito `url_catalogo` e' `https://catalogo.beniculturali.it/detail/<iri>` (formato visto in un motore di ricerca per altre schede dello stesso catalogo; per le schede di Milano **non verificato** perche' il sito e' dietro il controllo anti-bot). Il vecchio indirizzo del dump e' in `url_catalogo_dump`.
- **Secolo**: e' quello del punto medio della data (non un dato del catalogo); le date oltre 300 anni di ampiezza non hanno secolo.
- **Titoli**: il 62,5% e' solo il tipo di oggetto ("dipinto"): la ricerca guarda anche il soggetto.
- La home `..\docs\index.html` dice ancora "Beni culturali: in arrivo": non e' stata toccata, il link va aggiunto dal coordinatore.

## Prova della pagina

Anteprima "milano-in-dati" (porta 8796): pagina, mappa (769 punti, clic con elenco a pagine di 20 e link alle schede), ricerca (es. "hayez": 32 schede) e filtro per tipo funzionano; nessun errore in console; a 375 px di larghezza non c'e' scorrimento orizzontale.

## Cosa non e' stato fatto

- Nessun nome per l'ente catalogatore (solo codici, non e' mostrato nella pagina).
- Il catalogo vivo non e' stato letto (anti-bot): il dato resta quello del 2022-2023.
- Il significato della sigla `VeAC` (1 scheda) non e' scritto nel dump: l'etichetta e' una nostra lettura.
- Nessun controllo a mano sul testo delle licenze dell'ICCD (vedi fase 1).

## Come rifare

```
python -I scripts/06_pulisci.py beni_culturali_milano.csv ../citta-15-minuti/raw/comune_milano/confine_comune/confine_comune_milano_layer_0_confine_comune_milano.geojson pulito
python -I scripts/07_pagina.py pulito/beni_milano.csv ../docs/beni-culturali pulito/problemi.md
```
(`problemi.md` e' scritto a mano con i conteggi di `problemi_conteggi.json`; se si rifa la pulizia vanno ricontrollati.)
