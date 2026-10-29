# NOTE - Film e libri ambientati a Milano (fase 1: scarico e controllo)

Data di scarico: 29/10/2026. Nessuna pagina del sito, nessun git. Tutti i numeri vengono da `pulito/_statistiche.json` (costruito da `scripts/costruisci_pulito.py`).

## Risposta breve

- Film: **435** (in `pulito/film.csv`). Serie TV: 17 (`serie_tv.csv`). Libri: **280** righe (`libri.csv`: 125 da Wikidata/Wikipedia, 123 nuovi da Open Library, 32 nuovi da Library of Congress; 44 record LoC e 1 di Open Library erano gia fra i primi). Altro (videogiochi, quadri, opere liriche): 12 (`altro.csv`).
- Con un luogo **piu preciso di "Milano"**: solo **10 film** e **4 libri** (campo `ha_luogo_preciso`, tutti con coordinate). Per una mappa sono pochissimi. Gli altri dicono solo "Milano".
- Il collo di bottiglia e Wikidata: P840 (ambientazione) quasi sempre punta alla citta intera; solo 7 opere hanno un luogo interno (Teatro alla Scala, viale Bligny, Palazzo del Monte di Pietà, Mediolanum). P915 (luogo delle riprese) e piu preciso: 10 film su 83 hanno una piazza, una strada, una stazione o un teatro.
- Per mappare serve una fase 2 diversa (per esempio leggere le trame su Wikipedia o schedare a mano i casi famosi). Questo non e stato fatto.

## Film per decennio (campo `decennio`, da `anno` = prima data di P577; 12 film senza data)

1930: 5 - 1940: 14 - 1950: 38 - 1960: 43 - **1970: 95** - 1980: 64 - 1990: 37 - 2000: 43 - 2010: 54 - 2020: 30.
Il picco degli anni Settanta (poliziotteschi, commedie) e netto. Dopo il 1990 c'e un calo e poi una ripresa.

## Libri per decennio (242 con data su 280)

Prima del 1900: 25 - 1920: 1 - 1930: 2 - 1940: 8 - 1950: 4 - 1960: 12 - 1970: 17 - 1980: 17 - 1990: 34 - **2000: 58 - 2010: 55** - 2020: 9 (il decennio 2020 e ancora in corso).
Attenzione: i conteggi dei libri dipendono molto da chi ha schedato (Wikidata + Open Library), non misurano quanto si e scritto davvero.

## Fonti, una per una

### 1. Wikidata (SPARQL, CC0) - `raw/wikidata\`
- Endpoint `https://query.wikidata.org/sparql`. Filtro: opere con P840 o P915 che puntano a Milano (Q490) o a un luogo con P131* = Milano (6.486 luoghi in Milano su Wikidata).
- File: `luoghi_p840.json` (1,8 MB), `luoghi_p915.json` (0,4 MB), `opere_*.json` (titoli it/en, classi, anno, regia/autore, genere, IMDb id, link Wikipedia), `etichette_extra.json`. Totale 3,4 MB.
- Risultato: **393 opere** (339 con P840, 83 con P915; sovrapposte 29). Classi (campo `tipo_wikidata`): 291 film, 70 "opera letteraria", 11 serie TV, 2 miniserie, resto vario.
- Completezza: Wikidata e **incompleto**. Dei 484 articoli nelle categorie di it.wikipedia, 196 non hanno P840/P915 dentro Milano (116 non hanno P840 per niente, 80 lo hanno ma su altro luogo, es. Q220 Roma). Quindi Wikidata da solo perde circa un terzo.
- Licenza: CC0, si puo ripubblicare.
- Trappole: (a) un film con piu P31/piu luoghi genera piu righe: il file `luoghi_p840.json` ha 2.025 righe per 339 opere; si deduplica per QID (fatto). (b) Alcuni libri e film non hanno etichetta italiana/inglese (restano col QID come titolo). (c) Le serie TV non hanno P577 (hanno P580, data d'inizio, non scaricata): solo 3 su 17 hanno l'anno. (d) Il numero di "libri" in Wikidata e basso: i romanzi usano quasi sempre "opera letteraria" (Q7725634) e P840 e raro.
- Non usato: query con P31/P279* sulle classi (andava in timeout; basta P31 diretto, controllato).

### 2. Categorie di it.wikipedia (API MediaWiki) - `raw/wikipedia\`
- `categorie.json`: "Film ambientati a Milano" 351 pagine, "Film girati a Milano" 156, "Romanzi ambientati a Milano" 71, "Opere ambientate a Milano" (1 pagina + 4 sottocategorie), "Serie televisive ambientate a Milano" 2, "Opere teatrali ambientate a Milano" 9. La categoria "Opere letterarie ambientate a Milano" **non esiste** (0 pagine). Profondita 2: le sottocategorie non hanno altre sottocategorie. Totale 484 pagine uniche; una ("Rider (film)") senza QID.
- `pagine_qid.json` (QID Wikidata di ogni pagina), `mancanti_wikidata.json` (dati base delle 196 pagine fuori da Wikidata-Milano).
- Resa: film solo da categoria 142; da Wikidata e categoria insieme 256; solo Wikidata 37. Libri: solo categoria 46, entrambe 29, solo Wikidata 50.
- Licenza: i nomi delle pagine/categorie sono fatti; il testo di Wikipedia e CC BY-SA. Non abbiamo scaricato testi, solo titoli e appartenenza alle categorie.
- Trappola: "Film girati a Milano" contiene film girati a Milano ma ambientati altrove; la categoria dice dove si gira, non dove si svolge la storia. Nel CSV l'origine e nel campo `fonte_itwiki_categoria`.

### 3. Open Library - `raw/openlibrary\` (2,1 MB)
- API `https://openlibrary.org/search.json`, 1 richiesta ogni 2 s. Query: `place:"Milan (Italy)"` 2.738 libri; `subject:"Milan (Italy)"` 1.578; `place:"Milano"` 46; `subject:"Milano"` 710; `subject:"Milan (Italy) -- Fiction"` solo **2**; `place:"Milan (Italy)" AND subject:fiction` 82. Unione: **4.562 libri** (tutti in `pulito/openlibrary_tutti.csv`).
- Il soggetto esatto "Milan (Italy) -- Fiction" quasi non esiste su Open Library: i romanzi sono etichettati con soggetti separati (Fiction + luogo Milan). Ho preso come narrativa i libri con un soggetto che contiene fiction / narrativa / novel / romanz / racconti / detective / mystery: **124**, di cui 1 gia in Wikidata/Wikipedia (agganciati per titolo e cognome). 123 sono nuovi in `libri.csv`.
- Trappole: il luogo "Milan (Italy)" vale anche per "Ducato di Milano" (romanzi storici su Leonardo, Sforza), per libri di storia o per opere solo citate; non e sinonimo di "ambientato a Milano". Il controllo manuale e necessario. Molti libri sono inglesi di serie rosa (Harlequin) con un tocco milanese.
- Licenza: Open Library dichiara i metadati liberi (pubblico dominio/CC0); da verificare nei termini prima di ripubblicare.

### 4. Library of Congress - `raw/loc\` (0,2 MB)
- L'API `loc.gov/books` risponde 403 (Cloudflare "Just a moment"): **non aggirato**, come da regole. Usato invece il catalogo pubblico SRU `http://lx2.loc.gov:210/lcdb` (nessun login).
- `bath.subject="Milan (Italy)--Fiction"`: **76 record** (tutti scaricati, 2 file XML; 44 agganciati a libri gia presenti, 32 nuovi). `bath.subject="Milan (Italy)"` in generale: 4.830 (solo conteggio in `tutti_milan_italy_conteggio.xml`).
- Licenza: record bibliografici della LoC (opera del governo USA, pubblico dominio); la condizione esatta non e stata verificata.

### 5. SBN OPAC - `raw/sbn\` (0,2 MB, solo conteggi)
- Stessa interfaccia JSON della fase scala (`opac.sbn.it/opacmobilegw/search.json`, parametro `subject`), cliente educato (3 s). Conteggi in `raw/sbn/_conteggi.json`: "Milano - Narrativa" 6, "Milano - Romanzi" 3, "Milano - Racconti" 6, "Milano - Letteratura" 63, "Milano - Film" 29, "Milano - Cinema" 31, "Milano" 30.987.
- Fattibile ma inutile per i romanzi: i soggetti italiani per la narrativa non portano il luogo, quindi quasi nessun romanzo e indicizzato come "Milano - Narrativa". Il parametro `subject` sembra anche abbastanza largo (alcuni risultati non c'entrano: "romanzi cavallereschi"). Non entra in `libri.csv` (colonna `fonte_sbn` vuota). Utile al massimo per saggi su Milano e cinema.
- Licenza: non verificata (fase 1 solo conteggi).

### 6. Lombardia Film Commission e Comune di Milano
- Il sito vero e `https://www.filmcomlombardia.it` (i domini lombardiafilmcommission.* non esistono). Ha un database di location (oltre 25.000 foto secondo la stampa) e un elenco "produzioni", ma il suo `robots.txt` dice `User-agent: * Disallow: /`: **tutto vietato ai programmi**. Non scaricato (ho letto solo la home e il robots.txt). Nessun download aperto. Possibile contatto: filmcom@filmcomlombardia.it (da fare solo se Davide vuole).
- Portale open data del Comune (CKAN): ricerche "riprese", "set cinematografici", "film", "fiction", "audiovisivo" = 0 risultati; "cinema" 3 risultati non pertinenti (ingressi spettacoli, musei). Esistono solo "Occupazioni suolo temporanee straordinarie 2020 e 2021", che non riguardano le riprese. Elenco delle ricerche in `raw/altro/ckan_milano_ricerche.json`.
- dati.lombardia.it (Socrata): "film", "riprese", "audiovisivo" 0; "cinema" solo cinema di altri comuni.
- IMDb: non usato.

## Cosa manca

- Luoghi precisi: vedi sopra, 14 opere su circa 730.
- Serie TV: anno quasi sempre mancante; 17 sono poche (Wikipedia ne ha 2 in categoria).
- Non cercati: categorie di en.wikipedia (es. "Films set in Milan"), altri sottoinsiemi di Wikidata (P840 su luoghi senza P131 verso Milano, per esempio un quartiere o una via senza "comune"), cortometraggi e documentari fuori dalla classe film, fumetti, canzoni.
- Libri: nessun controllo se l'ambientazione e davvero Milano; la fonte forte e Wikidata/Wikipedia (125), Open Library e LoC sono rumorosi.
- Titoli senza etichetta: pochi (es. `Q17150542`, `Q18327213` rimasti col solo QID).

## File

- `pulito\film.csv`, `serie_tv.csv`, `libri.csv`, `altro.csv`: una riga per opera, colonne `fonte_wikidata_P840`, `fonte_wikidata_P915`, `fonte_itwiki_categoria`, `fonte_openlibrary`, `fonte_loc`, `fonte_sbn`, `imdb_id` (solo identificatore, nessun dato IMDb), `luogo_preciso`, `lat_lon_primo_luogo_preciso`.
- `pulito\openlibrary_tutti.csv` (4.562 righe, con colonna `narrativa_probabile`), `pulito\_statistiche.json`.
- Programmi in `scripts\`; `raw\` non va pubblicato intero (le parti Wikipedia/Open Library sono comunque ripubblicabili, vedi licenze sopra).

## Fase 2 - i luoghi dentro Milano (30/10/2026)

### Risultato in breve
- Prima (solo Wikidata): 10 film e 4 libri con un luogo piu preciso di "Milano" (`pulito/film.csv` e `libri.csv`, campo `ha_luogo_preciso`).
- Dopo: **185 opere** con almeno un luogo preciso (`pulito/luoghi.csv`, campo `id_opera`): **141 film** su 435, **3 serie TV** su 17, **37 libri** su 280, 4 opere "altro" su 12. Numeri in `pulito/_statistiche_luoghi.json`.
- `luoghi.csv`: 426 righe (opera + luogo + tipo), 179 luoghi diversi (punti a meno di 100 m contati come uno), 236 righe "riprese" e 190 "ambientazione", 393 con confidenza alta e 33 media (campo `confidence`). I 26 match a confidenza bassa non sono nel file.
- Luoghi piu raccontati (opere diverse): Stazione Centrale 26, Teatro alla Scala 26, Duomo 23, San Siro 13, San Vittore 12, San Babila 11, Piazza Fontana 7, Pirellone 7, Navigli 6, Giardini di Porta Venezia 5.
- Precisione, controllo a mano di 30 luoghi presi a caso: ultimo giro **28 giusti su 30 (93%)**; i quattro giri insieme 111 su 120 (92%). Registro in `pulito/_controllo_precisione.csv`.
- Pagina: `docs/film-e-libri/index.html` (mappa, elenchi per decennio, luoghi piu raccontati, fonti e limiti), dati in `docs/film-e-libri/data/`. Provata sul server "milano-in-dati" (porta 8796): nessun errore in console, nessuno scorrimento orizzontale su telefono.

### Come e stato fatto
1. **Testi di Wikipedia** (`scripts/20_scarica_wikitext.py`): 560 articoli it.wikipedia e 369 en.wikipedia, in blocchi da 40 con l'API MediaWiki (pausa 2 s), salvati in `raw/wikitext/` (8 MB). Sono tutte le opere che hanno un articolo.
2. **Luoghi con nome**: l'estratto OpenStreetMap della striscia 7 contiene solo le strade, non teatri o stazioni. Allora una sola richiesta a Overpass (`20b_overpass_luoghi.py`, `raw/osm/overpass_luoghi_milano.json`, 1,2 MB): 2.963 oggetti con nome (stazioni, teatri, musei, chiese, ospedali, universita, stadi, monumenti, quartieri) dentro il Comune.
3. **Elenco dei luoghi** (`21_gazetteer.py`, risultato `pulito/_gazetteer.csv`, 9.083 nomi): strade e piazze dal registro dei civici del Comune (4.246 nomi, piu 1.855 varianti col cognome, per esempio "corso Garibaldi"), 133 nomi di quartieri NIL, 2.648 nomi OSM, 201 nomi di luoghi famosi scritti a mano (Duomo, Pirellone, San Siro, Bovisa, Quarto Oggiaro...). Se lo stesso nome e in piu elenchi vince quello scritto a mano, poi i civici, poi i NIL, poi OSM.
4. **Link dentro il testo** (`22_link_coordinate.py`, `22b_link_wikidata.py`): i link delle sezioni utili puntano a 8.356 pagine; di ognuna si chiedono le coordinate a Wikipedia (1.298 pagine) e, se mancano, a Wikidata (P625, altre 306). Contano solo se cadono dentro il Comune.
5. **Estrazione** (`23_estrai_luoghi.py`): si leggono la parte iniziale, "Trama" (e simili: Plot, Synopsis, Contenuto, Personaggi), "Produzione", "Riprese" (Filming, Location...), "Curiosita". Si cercano i nomi dell'elenco nelle frasi; il nome piu lungo vince. Per ogni match: opera, luogo, tipo di luogo, coordinate, sezione, fonte, confidenza, tipo. Le frasi sono in `pulito/_frasi_locali.csv` (e `_match_tutti.json`): **solo in locale, mai sul sito**, perche il testo di Wikipedia e CC BY-SA e noi pubblichiamo solo fatti e link.
6. **Ambientazione o riprese**: conta la parola chiave piu vicina nella frase (ambientato, si svolge, set in... contro girato, riprese, filmed, location); se non c'e, vale la sezione (Trama = ambientazione, Riprese e Produzione = riprese). Per i libri e sempre ambientazione.
7. **Controllo a mano e regole** (4 giri da 30 luoghi a caso, vedi `_controllo_precisione.csv`). Falsi positivi trovati e regole:
   - "Adriano" (quartiere) = Adriano Celentano, "Buenos Aires" (quartiere) = un Gran Premio, "Villa San Giovanni" = Calabria, "Museo Egizio" = Torino: tolti dall'elenco o messi in lista nera.
   - Nomi di persona nei giardini e parchi OSM ("Parco Walter Chiari"): i nomi abbreviati si fanno solo per basilica, chiesa, stazione, castello, abbazia, santuario, cattedrale; mai "San X" da solo; alberghi solo se hanno un id Wikidata; monumenti solo di certi tipi.
   - "fa andare via Luciano": "via" scritto minuscolo conta solo dopo una preposizione o una virgola.
   - "Corso" come nome, Garibaldi persona o stazione: ogni nome deve avere almeno una parola con la maiuscola che non sia un articolo; non ci sono chiavi "Garibaldi" o "Corso" da soli, solo "corso Garibaldi", "stazione Garibaldi", "Porta Garibaldi". "Via Roma" non esiste nei civici di Milano, quindi la citta di Roma non genera luoghi.
   - Altra citta nella frase (Roma, Torino, Sesto San Giovanni, Forte dei Marmi...) senza "Milano": confidenza bassa; la parte del nome del luogo non conta, cosi "Porta Venezia" non e Venezia. Nomi di strade molto comuni (Mazzini, Garibaldi, Dante...) senza "Milano" nella frase: bassa.
   - Titoli e uscite: "San Babila ore 20", "Il ponte della Ghisolfa", frasi con "dal libro", "uscita in sala", "debutto", "prima rappresentazione": titolo cancellato o confidenza bassa.
   - Link a editori, eventi, Ducato di Milano, metropolitana in generale: esclusi.
   Errori che restano: frasi con due citta (un luogo di Torino letto come Milano), personaggi con nome di luogo ("l'investigatore Duomo"), attori o compagnie che "recitano al Piccolo Teatro" (non e l'ambientazione).
8. **Conteggi per decennio e pagina**: `24_luoghi_csv.py` produce `luoghi.csv` e `_statistiche_luoghi.json`; `26_dati_pagina.py` produce `docs/film-e-libri/data/` (`opere.json`, `luoghi.json`, `stats.json`, `luoghi.csv`): solo fatti e link.

### Copertura per decennio (film e serie TV, con luogo / totale)
1930: 1/5 - 1940: 5/14 - 1950: 10/38 - 1960: 16/43 - 1970: 30/95 - 1980: 24/64 - 1990: 17/38 - 2000: 16/43 - 2010: 13/54 - 2020: 9/30 (conteggi dei soli film, senza le 17 serie TV). Libri: 37 su 280 in tutto; la maggior parte dei libri viene da Open Library o dalla LoC, senza pagina Wikipedia da leggere. Tabella completa nella pagina e in `_statistiche_luoghi.json`, campo `per_decennio`.

### Limiti da ricordare
- Le trame di Wikipedia spesso dicono solo "a Milano": 141 film su 435 hanno un luogo. I conti per decennio dipendono da quanto e lunga e dettagliata la voce, non da quanto Milano compare nel film.
- Per le strade il punto sulla mappa e il civico centrale, non il tracciato. L'Idroscalo e fuori dal Comune ma e messo a Milano.
- Open Library ha qualche anno sbagliato (per esempio "I promessi sposi" con 1800): non corretto.
- Non cercate le categorie di en.wikipedia; le voci inglesi lette sono solo quelle di opere gia trovate. Database delle location della Lombardia Film Commission non usato (il robots.txt lo vieta).
- Licenze: testo di Wikipedia CC BY-SA (solo in locale), Wikidata CC0, civici e NIL CC BY, OpenStreetMap ODbL (da citare, scritto nel piede della pagina).
- `raw/wikitext/`, `pulito/_frasi_locali.csv` e `_match_tutti.json` non vanno pubblicati.

### Per rifare tutto
Dalla cartella `film-e-libri`: `python -I scripts/20_scarica_wikitext.py .`, `20b_overpass_luoghi.py .`, `21_gazetteer.py . ..`, `22_link_coordinate.py .`, `22b_link_wikidata.py .`, `23_estrai_luoghi.py . ..`, `24_luoghi_csv.py .`, `26_dati_pagina.py . ../docs/film-e-libri` (per prendere un campione da controllare: `25_campione.py . <seme> 30`).
