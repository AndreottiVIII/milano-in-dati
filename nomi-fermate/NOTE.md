# NOTE - A chi sono intitolate le fermate (filone 16)

Data del lavoro: 30/10/2026. FASE 1: raccolta e classificazione, nessun grafico, nessuna pagina.

## Fonti usate

1. **Orari ATM (GTFS), gia' scaricati dal filone bici-auto-mezzi**
   File: `..\bici-auto-mezzi\raw\gtfs\ext_comune_new\` (stops.txt, routes.txt, trips.txt, stop_times.txt). Versione feed 425, dal 26/10/2026.
   Metro = route_type 1 (M1-M5), tram = route_type 0 (17 linee). Le fermate sono quelle servite da almeno una corsa.
   Risultati: `raw\metro_stops_gtfs.csv` (130 fermate fisiche -> 125 stazioni, perche' Duomo, Cadorna, Loreto, Lotto e Sant'Ambrogio hanno due fermate), `raw\tram_stops_gtfs.csv` (724 fermate, 341 nomi diversi).
   Licenza: dati del Comune/ATM, gia' valutata dal filone bici-auto-mezzi; qui non si ripubblica il file grezzo.
2. **Wikidata (SPARQL, query.wikidata.org), 30/10/2026**
   Stazioni metro nel riquadro di Milano con la proprieta' "intitolato a" (P138): `raw\wd_metro_stations.csv` (250 KB). Poi due-tre salti lungo la catena stazione -> via/piazza -> persona/luogo: `raw\wd_hop2.csv`. Mestieri delle persone: `raw\wd_persone.csv`. Santi: `raw\wd_santi.csv`.
   Licenza: CC0 (si puo' ripubblicare).
3. **donne-nelle-vie (filone 2)**, solo lettura: `strade_classificate_arricchite_v2.csv` (4.278 vie, categoria uomo/donna/non_persona, mestieri, anni) e `decisioni_davide.csv`. Serve per controllare le persone delle stazioni e per classificare i tram.
4. **OpenStreetMap (Overpass)**: provato due volte, il server ha risposto 502 e poi e' andato in timeout. Saltato. Non cambia molto: il filone 2 usa gia' i tag OSM "name:etymology:wikidata" per le vie (campo `fonte` = tag_osm).

## Come ho classificato (metro) - script `scripts\06_build_metro.py`

- Il nome della stazione si collega, con Wikidata, alla via/piazza/luogo da cui prende il nome. Da li si scende fino alla persona (es. Pasteur: stazione -> via Luigi Pasteur -> Louis Pasteur).
- Si scende solo attraverso vie, piazze, porte e stazioni ferroviarie. Non si scende da quartieri, comuni, edifici (Duomo resta "edificio", non diventa "festa dell'Assunta").
- Categorie: persona (uomo/donna, mestiere, anni), santo/santa, luogo (comune, quartiere, citta', regione/stato, natura), evento/data, edificio/istituzione, altro.
- Il mestiere e il gruppo di mestiere vengono da donne-nelle-vie quando la via c'e', altrimenti da Wikidata. Il "gruppo di mestiere" e' una regola a parole chiave sulla descrizione (la prima professione citata).
- Pochi casi a mano, tutti in `scripts\override_metro.json` e tutti segnalati: santi (Wikidata non ha la persona), stazioni senza dati Wikidata (Comasina, Cassina de' Pecchi, Cascina Burrona, ecc.), nomi doppi (Lodi T.I.B.B., Sforza-Policlinico, Sesto 1 Maggio).
- Ogni dubbio e' in `pulito\da_verificare.csv` (27 stazioni). Niente e' stato deciso in silenzio.

## Come ho classificato (tram) - script `scripts\09_build_tram.py`

- Le fermate tram sono incroci ("via Farini v.le Stelvio"): ho separato le strade e abbreviazioni (v.le, p.za, s., l.go...). Ogni strada e' una riga (375 denominazioni). `n_fermate` = quante fermate fisiche la contengono.
- Abbinamento col registro vie del filone 2: nome uguale (con iniziali), poi parte finale del nome ("via meda" = Giuseppe Meda), poi parte iniziale solo se unica. Il metodo usato e' scritto in `registro_via`.
- Per i "non persona" uso il motivo scritto dal filone 2 (luogo su Wikidata, data/evento, parola chiave): quindi "luogo/altro" e' una categoria larga, non distingue edifici da luoghi.
- Nomi senza tipo di via (Teatro alla Scala, Stazione Centrale, ecc.): stessa classificazione della stazione metro con lo stesso nome oppure parola chiave.
- Fermate nei comuni vicini (Rozzano, Cinisello, Sesto) non sono nel registro di Milano: restano "fuori Milano (non classificato)".
- Dubbi in `pulito\da_verificare_tram.csv` (79 righe).

## Trappole dei dati

- Le fermate GTFS delle stazioni hanno nomi doppi (DUOMO M1 / DUOMO M3) e sigle (P.TA GENOVA F.S., VILLA S.G.): ho unito le fermate della stessa stazione. Una stazione serve piu' linee: la colonna `linee` le elenca.
- La stazione e' intitolata a una via/piazza, che e' a sua volta intitolata a qualcuno. "Cadorna" = piazzale Luigi Cadorna = il generale (persona), non un luogo.
- Wikidata sbaglia o e' incerto in alcuni punti: Dateo ha la data di morte 878 (dubbia), Romolo e' una figura leggendaria, la via della Moscova e' collegata al fiume ma ricorda la battaglia, le descrizioni in italiano mancano spesso.
- **Il filone 2 ha tre vie che non risultano persona ma lo sono**: piazza Simone Bolivar (Simon Bolivar), piazzale Dateo (arcivescovo), viale Romolo (leggendario, dubbio). Segnalo per eventuale correzione di donne-nelle-vie (non l'ho toccato).
- Santa Sofia: potrebbe essere la martire romana oppure la Sapienza divina; sesso e identita' da confermare.
- Ogni fermata "da santo" ma che indica un quartiere (San Siro, San Leonardo, San Donato, Villa San Giovanni) l'ho messa in "luogo" e non in "santo", con nota.
- Sul tram il registro vie ha anche vie con "cognome" (es. Cusani, Tibaldi, Negroli): probabili persone, ma non identificate. Sono in "non classificato".
- I conteggi per "persona" contano le stazioni, non i passeggeri.

## File prodotti (cartella `pulito\`)

- `fermate_metro_nomi.csv` - 125 stazioni (stazione, linee, categoria, sottocategoria, riferimento diretto, intitolato a, persona, sesso, mestiere, gruppo di mestiere, nascita-morte, QID, fonte, confidenza, controllo con filone 2, note, da verificare)
- `da_verificare.csv` - 27 stazioni dubbie
- `fermate_tram_nomi.csv` - 375 denominazioni di strade/luoghi sulle fermate tram
- `da_verificare_tram.csv` - 79 righe dubbie
- `riepilogo.json` - conteggi

## Come rifare tutto

`cd nomi-fermate` poi `python -I scripts\01_metro.py raw\metro_stops_gtfs.csv` (come da STATO.md), poi 02, 03, 03b, 05, 07 (Wikidata), poi `06_build_metro.py`, `08_tram_stops.py raw\tram_stops_gtfs.csv`, `09_build_tram.py`, `10_riepilogo.py`.
