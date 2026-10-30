# NOTE - cinema scomparsi di Milano (fase 1)
Data: 30/10/2026. Cartella: milano-in-dati\cinema-spariti. Nessun grafico, nessuna pagina.

## Risultato in due righe
Abbiamo un elenco di 170 cinema milanesi chiusi (anni di apertura e chiusura, indirizzo) più 29 cinema aperti oggi (OpenStreetMap). Mancano i cinema che erano attivi nel passato e sono ancora aperti, le sale parrocchiali e il numero di sale dei cinema chiusi.

## Fonti
1. **Elenco spazioCinema (Anteo)**. Pagina: https://www.spaziocinema.info/cinema/notizie/scegli-il-nome-delle-nuove-sale-di-anteo-tra-le-insegne-di-storici-cinema-milanesi ; PDF alla stessa pagina, link "at_download/programma". Scaricato 30/10/2026. File: raw\storiche\spaziocinema\programma.pdf (251 KB), tabella_grezza.csv (170 righe: campi sala, periodo, indirizzo). Periodo coperto: 1896-2017. Licenza: copyright Anteo, nessuna licenza aperta: il PDF non va ripubblicato. Trappola: il testo estratto "a righe" mescola le colonne, si legge bene solo con l'estrazione per tabella (script 05).
2. **OpenStreetMap (Overpass)**, estrazione del 29/10/2026 23:28 UTC, area del comune di Milano. File: raw\osm\cinema_attuali_e_storici.json (15 KB, 37 elementi), raw\osm\teatri.json (26 KB), raw\osm\oggi_vicino.json e oggi_vicino_grezzo.json (negozi e locali entro 30 m dai cinema chiusi). Campi: amenity, disused:amenity, screen (numero schermi), start_date. Trappola: solo 2 cinema "disused" e nessun "was:": OSM non ha la storia. Licenza ODbL (ripubblicabile citando OSM). Il file del settore 7 (bici-auto-mezzi) ha solo strade, quindi non usato.
3. **Wikidata (SPARQL)**, 30/10/2026. File: raw\wikidata\a_cinema_inMilano_P131.json (76 KB, 59 cinema), b_cinema_box.json (stessi 59), c_teatri_box.json (136 KB, 90 teatri). Campi: inception P571, dissolved P576, coordinate P625, indirizzo P6375. Trappola: l'anno di chiusura c'è per 1 cinema, l'apertura per 6. Licenza CC0.
4. **Wikipedia italiana (API)**, 30/10/2026. File: raw\wikipedia\categorie.json, wikitext.json (413 KB, 37 voci della categoria "Teatri di Milano"). Trappola: le categorie sui cinema di Milano non esistono. Licenza CC BY-SA.
5. **Comune di Milano, dati aperti (CKAN)**, 30/10/2026. File in raw\comune: ds157 (ingressi e spettacoli per tipo, 1995-2010, CSV 2 KB), ds252 (295 locali di pubblico spettacolo, CSV 62 KB, nessun cinema), ds59 (pubblici esercizi fuori piano, CSV 845 KB, non rilevante), _metadati.json. Licenza CC-BY. Trappola in ds157: anni 2004-2005 con campi vuoti.
6. **Nominatim (OSM)** per le coordinate: raw\storiche\geocode_nominatim.json (163 indirizzi, 12 senza risultato).
7. **Archive.org**: le guide "Milano Scelta" 1905 e 1907 (raw\storiche\archive_org, circa 2 MB l'una) quasi non parlano di cinema. Google Books: quota esaurita.

## File puliti (cartella pulito)
- `cinema.csv` (203 righe): 170 dall'elenco, 29 cinema aperti solo da OSM, 4 solo da Wikidata. Campi: id, nome, altri_nomi, indirizzo, lat, lon, precisione_posizione, fonte_posizione, anno_apertura, anno_chiusura, apertura_incerta e chiusura_incerta (1 = data "circa"), periodi_attivita, periodo_testo_originale, n_sale (solo 15 cinema aperti con tag screen), stato_2026, wikidata, osm_id, cosa_c_ora, fonti.
- `elenco_spaziocinema_parsed.csv`, `conteggi_decenni_preliminari.csv`, `wikipedia_frasi_cinema.csv` (30 frasi), `fonti_valutate.md`.
- Posizione dei 170 cinema dell'elenco: 42 con coordinate Wikidata, 70 Nominatim con civico (da controllare), 46 solo via, 12 senza.
- `cosa_c_ora`: 93 candidati OSM (negozi o locali entro 30 m), da confermare a mano; mancano per gli altri.

## Conteggi preliminari (cinema dell'elenco attivi a gennaio dell'anno; file conteggi_decenni_preliminari.csv)
1910: 23; 1920: 52; 1930: 82; 1940: 82; 1950: 98; 1960: 118; 1970: 110; 1980: 101; 1990: 50; 2000: 35; 2010: 4. Sono solo sale poi chiuse: vanno aggiunte quelle ancora aperte. Oggi (OSM 2026): 29 cinema.
Chiusure per decennio (fine dell'ultimo periodo): 1930: 20; 1940: 7; 1950: 3; 1960: 11; 1970: 21; 1980: 50; 1990: 17; 2000: 31; 2010: 4.

## Cosa manca
- Cinema attivi nel passato e ancora aperti nel 2017; sale parrocchiali, arene, cinema a luci rosse non elencati; numero di sale storico.
- "Cosa c'è ora" confermato; coordinate esatte per 58 cinema.
- Verifica indipendente delle date (Wikidata deriva forse dalla stessa lista). Possibili aggiunte: CineMi (Roaro, fino al 1955), dati Anec, Google Books.


## Fase 2 (30/10/2026): la pagina
Pagina: docs\cinema-spariti\index.html (+ data\cinema.json, data\serie.json). Costruita da scripts\pagina_dati.py con scripts\pagina_template.html; Leaflet 1.9.4, tessere OSM in grigio, un colore (arancio), mappa con cursore per decennio (1890-2010 e "oggi") e tasto Avvia, grafico a aree delle sale attive per anno, istogramma di aperture e chiusure per decennio, elenco ricercabile, sezione "Fonti e limiti".

Cosa è stato deciso o trovato:
- **Licenza**: dall'elenco spazioCinema 2017 si pubblicano solo nome, altri nomi, indirizzo e anni; niente testo originale (campo periodo_testo_originale escluso), niente PDF, niente CSV scaricabile. Resta da chiedere ad Anteo il permesso. Rischio da tenere presente: pubblicare tutte le 170 righe potrebbe contare come estrazione sostanziale di una banca dati; per questo la richiesta ad Anteo resta aperta.
- **Posizioni**: Wikidata e OSM = esatte (43 chiusi); Nominatim = "posizione approssimata" (116, cerchio vuoto sulla mappa); 12 senza posizione, fuori mappa.
- **Cinema ancora aperti con anno di apertura** (da Wikidata, Wikipedia, OSM): Cinema Centrale via Torino 1907 (tag OSM start_date, non verificato), Odeon 1929, Ducale 1938 (Wikidata P1619), Ariosto 1948 (ex sala parrocchiale anni '30), Beltrade circa 1925 ("anni venti"), Plinius 1967 (da allora solo cinema, prima teatro), Anteo 1979, Anteo CityLife 2017. Per gli altri 20 aperti oggi l'anno non si trova: compaiono solo nel passo "oggi". Wikidata ha una sola data di apertura utile (Ducale); le altre vengono da Wikipedia (CC BY-SA).
- **Odeon**: OSM lo segnala attivo, ma è chiuso dal 31/07/2023 (riconversione, 5 schermi e galleria commerciale; lo dice anche la descrizione OSM). Spostato tra le sale chiuse (171 in tutto) e tolto dagli aperti (28). UCI Certosa ha chiuso il 5/5/2024 ma è stata rilevata da Cinelandia: tenuta tra gli aperti.
- **Esclusi** 4 luoghi solo Wikidata senza date: Cinema Prada (probabile doppione del Cinema Godard di Fondazione Prada), Pussycat, Teatro Trianon, Teatro Ciak.
- **Numeri**: massimo di sale attive nel 1960 = 119 poi chiuse + 4 aperte con anno noto = 123 (la stampa dice circa 160 negli anni Settanta; il nostro 1970 è 111+5). Chiusure per decennio: 1980: 50, 2000: 31, 1970: 21, 1930: 20. Riferimenti stampa sul grafico etichettati come stime: 110 nel 1950 (VareseNews 2019), circa 160 anni Settanta e 29 nel 2022 (Il Giorno).
- **Trappola grafica**: la curva delle sale poi chiuse scende per forza vicino al presente (si vedono solo le chiuse): la pagina lo dice sotto il grafico.
- Trappola tecnica: con python -I il terminale Windows stampa in cp1252; per stampare accenti usare sys.stdout.reconfigure(encoding="utf-8").
