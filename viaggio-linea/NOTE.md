# NOTE - Un viaggio in tram (e in metro) (filone viaggio-linea)

Data: 1 novembre 2026. Pagina `docs\viaggio-linea\index.html` (dati in `docs\viaggio-linea\data\`, circa 395 KB). Nessun git; JOURNAL.md, docs\index.html, menu.js e MENU_README.md non toccati: il coordinatore deve aggiungere la sezione al menu e alla home.

## Idea
Scegli una linea, la percorri fermata per fermata e vedi come cambia la citta': reddito, prezzo delle case, eta media, % stranieri, alberi, Airbnb, punteggio "15 minuti", scuole, voto (centrosinistra e centrodestra). Idea dal racconto della linea M29 di Berlino (Berliner Morgenpost).

## Linee (9) e come sono prese - `scripts\01_linee.py`
Fonte: GTFS ATM/AMAT in `..\bici-auto-mezzi\raw\gtfs\ext_comune_new\` (versione 425, validita' 26/10-30/11/2026, CC-BY). Per ogni linea si fissa il percorso (`shape_id`) e si prende la corsa con piu' fermate; ordine e coordinate da stop_times/stops.
- M1 (Rho Fiera - Sesto 1 Maggio, 31 fermate; senza ramo Bisceglie), M2 (Abbiategrasso - Gessate, 30; senza ramo Assago), M3 (21), M4 (21), M5 (19), tram 9 (Porta Genova - Centrale, 26), tram 15 (Duomo - Rozzano, 32), filobus 90 e 91 (63 e 64 fermate).
- **Il tram 9 non e' circolare** (lo e' solo il 90/91): la pagina lo dice. Nel feed il giro del 90 e del 91 e' spezzato in due meta' (Lodi-Lotto e Lotto-Lodi, 24+40 e 40+25 fermate); le meta' sono attaccate togliendo il capolinea doppio (Lotto). I tracciati sono quelli degli orari di ottobre-novembre 2026 con i lavori in corso (i service_id dei filobus dicono "lavori"): possono non coincidere col percorso consueto.
- Fuori dal Comune: M1 5 fermate, M2 10, M4 1 (Linate), tram 15 8 (Rozzano). Restano senza valori.

## Fermata -> quartiere/zona - `scripts\pagina.py`
- NIL: punto-in-poligono sui confini ds964 (`citta-15-minuti\raw\comune_milano\nil_vigenti\ds964_nil_wm.geojson`, in WGS84 nonostante "wm" nel nome); anelli con OR esclusivo come in quartieri-che-cambiano. Fuori poligono ma entro 40 m: poligono piu' vicino (successo per 1 fermata del tram 15).
- Zona OMI: stessa cosa con i perimetri 2026/1 (`prezzi-case\raw\geopoi\F205_20261.json`). Il prezzo e' `compr_centro` (abitazioni civili, valore centrale dell'intervallo, euro/m2) da `docs\prezzi-case\data\zone_ultimo_semestre.csv`.
- Tutte le fermate dentro Milano hanno NIL e zona OMI.

## Indicatori (letti da file gia' sul disco, mai ricalcolati; fonte e anno anche in `data\riepilogo.json`)
| id | valore | file | anno | livello |
|---|---|---|---|---|
| reddito | reddito medio per contribuente, euro 2025 (`reddito_2024`) | quartieri-che-cambiano\out\indicatori_nil.csv (CAP -> NIL con i civici) | imposta 2024 | NIL |
| prezzo | OMI abitazioni civili euro/m2 | docs\prezzi-case\data\zone_ultimo_semestre.csv | 2026/1 | zona OMI |
| eta | eta media | docs\eta\data\nil_eta_centenari.csv | 31/12/2025 | NIL |
| stranieri | % residenti stranieri (`stranieri_2025`) | quartieri-che-cambiano\out\indicatori_nil.csv (da ds27) | 31/12/2025 | NIL |
| alberi | alberi ogni 1.000 abitanti | docs\alberi\data\nil.csv | 31/3/2025 | NIL |
| airbnb | annunci ogni 100 abitazioni | docs\affitti-brevi\data\nil.csv | 19/9/2026 | NIL |
| servizi | punteggio 15 minuti su 10 | docs\citta-15-minuti\data\nil_punteggi.csv (solo "in classifica") | 2025 | NIL |
| scuole | scuole infanzia+primaria+media ogni 10.000 residenti = (s24_0+s24_1+s24_2)/residenti 2024 | docs\scuole\data\nil_scuole.csv + docs\alberi\data\nil.csv (residenti ds205) | a.s. 2024/25 | NIL |
| voto_sx, voto_dx | quota di Sala e di Bernardo sui voti ai candidati sindaco | docs\elezioni\data\nil\comunali_sindaco_2021-10-03.json + index.json (famiglie) | 3/10/2021 | NIL |

Voto di citta' (da index.json, 480.608 voti ai candidati): affluenza 47,7%, centrosinistra 57,7%, centrodestra 32,0%, sinistra 1,6%, altri 8,7%.

Soglie (in `pagina.py`): niente valori di quartiere sotto 1.000 residenti (2025); niente valori per abitante (alberi, scuole) sotto 5.000 residenti (come la pagina Alberi); niente voto sotto 500 voti validi; Airbnb vuoto dove la pagina Affitti brevi segna "piccolo denominatore". Scelta: i quartieri sotto 5.000 residenti restano sul grafico come pallino vuoto ma NON entrano nei testi automatici ne' nei salti (San Donato M3, in Triulzo Superiore, ha il 62,9% di stranieri e si prenderebbe tutte le frasi).

## Testi e "cosa sorprende"
- Testi automatici per linea e per verso (andata e ritorno calcolati a parte): frasi su reddito, prezzo, stranieri = punto piu' basso e piu' alto lungo la linea, nel verso di marcia, e rapporto tra i due ("raddoppia" / "si dimezza" solo se il rapporto e' tra 1,9 e 2,1). Piu' il salto piu' brusco della linea.
- Salto tra due fermate vicine = differenza di posizione (percentile) nella classifica dei NIL (88) o delle zone OMI (42): 0 uguale, 1 dal minimo al massimo. Contano coppie in due unita' diverse, entrambe con almeno 5.000 residenti. Stessa coppia di quartieri su piu' linee: una volta sola. Scelta fatta dopo aver visto che lo scarto in deviazioni standard premiava gli indicatori con code lunghe (alberi, Airbnb a Duomo).
- Nei titoli in alto non compaiono scuole e alberi (rapporti per abitante instabili), ma restano nella tabella dei dieci indicatori.
- Salti piu' grandi: tra i titoli Airbnb tra Famagosta e Romolo (M2), da 0,7 a 7,1 annunci ogni 100 abitazioni (Barona -> Porta Ticinese - Conchetta), 83 su 100; poi voto al centrosinistra nella stessa coppia 50,0% -> 68,4% (81), eta media tra Ca' Granda e Bicocca (M5) 47,3 -> 42,9 (79), voto al centrodestra (75). In tabella anche scuole tra Segesta e Lotto (M5) 13,7 -> 2,8 (86) e stranieri tra Bolivar e Tolstoj (M4) 9,9% -> 24,9% (73).
- Il reddito, tra fermate vicine, non fa salti enormi (massimo 59 su 100: Famagosta -> Romolo, 27.893 -> 43.458 euro): il divario sta tra i capi opposti (M1 da Pagano 92.141 a Turro 29.098 euro, 3,2 volte; M3 da Missori 80.589 ad Affori Centro 27.603; M4 da Sant'Ambrogio 84.621 a Repetti 28.532).

## Limiti dichiarati in pagina (mai "trappole")
Valore del NIL/zona, non della fermata; anni diversi (2021-2026); reddito per CAP portato al NIL; OMI = quotazione, zone ampie; quartieri piccoli; stranieri = cittadinanza; voto = una elezione, non il voto degli abitanti della fermata; Airbnb su abitazioni del censimento 2023; scuole = sede nel quartiere; percorsi con lavori e rami non coperti (M1 Bisceglie, M2 Assago); fermate a distanze uguali nel grafico; nessuna causa.

## Pagina
Stile come `docs\alberi\index.html` (CSS, Leaflet 1.9.4 con tessere OSM in grigio, `../menu.js`, `fetch(..., {cache:'no-cache'})`). Selettori di linea e indicatore, verso opposto, mappa con fermate colorate in quinti (soglie dagli 88 NIL, o dalle 42 zone per il prezzo), profilo in SVG con bande dei quartieri e mediana della citta', scheda della fermata (clic su grafico, mappa o elenco dei quartieri), elenco dei quartieri attraversati. Indirizzo `#M3&i=prezzo` per linkare linea e indicatore. Verificato nel browser (server `python -m http.server 8850` da docs\, poi fermato): nessun errore in console, nessuno scorrimento orizzontale a 375 px, 90 combinazioni linea x indicatore e i due versi provate da script.

## File prodotti
`docs\viaggio-linea\data\`: linee.json (usato dalla pagina), nil_linee.geojson (confini semplificati a 15 m dei NIL toccati), fermate_indicatori.csv (307 righe), nil_indicatori.csv (88), salti.csv (300), riepilogo.json. In `out\`: linee_gtfs.json (grezzo da GTFS), fermate_indicatori.csv.

## Idee non fatte
Ramo Bisceglie della M1 e ramo Assago della M2; altre linee tram (1, 3, 19, 24); distanza reale in km tra le fermate sull'asse del grafico; reddito per CAP della fermata (dal civico piu' vicino) invece che per NIL; voto di altre elezioni (europee 2024, politiche 2022).
