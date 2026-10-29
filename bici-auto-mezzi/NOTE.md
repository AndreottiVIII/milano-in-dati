# NOTE - filone 7: bici contro auto contro mezzi pubblici (fase 1, solo scarico)

Scaricato il 29 ottobre 2026. Nessuna analisi fatta. Scripts in `scripts\`, dati in `raw\`.

## 1. Rete stradale OpenStreetMap
- **Fonte**: estratto della Lombardia di openstreetmap.fr, `https://download.openstreetmap.fr/extracts/europe/italy/lombardia-latest.osm.pbf` (340 MB). Dati OSM aggiornati al **29/10/2026 ore 01:08 UTC** (file `lombardia.state.txt`, sequenza 7349062).
- **Perche' questa strada**: Overpass (tutti i server provati) rispondeva "pieno/timeout"; Geofabrik "nord-ovest" (594 MB, 28/10/2026) funzionava ma e' piu' grande. Nessun programma di ritaglio (osmium) sul PC, quindi ho scritto un ritagliatore in Python (`scripts\clip_pbf.py`, usa solo numpy).
- **Ritaglio**: rettangolo lat 45.350-45.572, lon 8.990-9.330 (Comune di Milano piu' circa 4 km intorno). File `raw\osm_milano\milano_buffer.osm.gz` (17,9 MB compresso, XML OSM standard, anche letto da molti programmi). Statistiche con `scripts\osm_stats.py`.
- **Contenuto** (conteggi dal file, tag `highway`, `oneway`, `maxspeed`, ecc.): 181.476 strade/percorsi con tag `highway` (73.376 footway, 33.415 service, 24.802 residential, 9.519 tertiary, 6.716 cycleway, 2.838 pedestrian, ecc.); 779.196 nodi; `oneway=yes` su 39.964 strade, `oneway:bicycle` su 939 (no=469, yes=467, -1=3); `maxspeed` su 18.433 strade; 4.072 semafori (`highway=traffic_signals`), 40.175 attraversamenti pedonali (`highway=crossing`), 3.426 stop, 4.524 dare-precedenza. Relazioni: 4.380 divieti di svolta (`type=restriction`), 61 itinerari (`route=bicycle`), 28 multipoligoni stradali.
- **Piste ciclabili**: `highway=cycleway` 6.716 strade; il conteggio "ciclabile" che esce dallo script (15.712) e' troppo largo perche' conta anche `cycleway:*=no`. Da rifare con regole precise in fase 2.
- **Licenza**: ODbL 1.0, (c) contributori OpenStreetMap. Si puo' ripubblicare citando la fonte; chi ripubblica una versione modificata deve usare la stessa licenza.
- **Trappole**: i nodi con tag sono tenuti solo se `highway`, `crossing`, `barrier`, `traffic_calming`; le strade sono troncate al rettangolo (nessun nodo fuori). Nel file ci sono anche strade `proposed`/`construction` (298) e `platform`/`corridor`: da scartare in fase 2. Il tag `maxspeed` c'e' solo su ~10% delle strade: per le altre servono velocita' tipiche per tipo di strada.

## 2. GTFS (orari mezzi pubblici)
Nessun account, chiave o clic di accettazione necessari.
- **ATM / Comune di Milano (AMAT)**: `https://dati.comune.milano.it/gtfs.zip` (scheda `ds929-orari-del-trasporto-pubblico-locale-nel-comune-di-milano-in-formato-gtfs`, mantenuto da AMAT, aggiornato ogni 2-4 settimane). File `raw\gtfs\gtfs_comune_milano_amat.zip`, 25,4 MB (la scheda dichiara 60 MB, errata). Estratto in `raw\gtfs\ext_comune\`.
  - `feed_info.txt`: versione 424, inizio 16/10/2026. **Validita': 16/10/2026 - 20/11/2026** (`calendar_dates.txt`, 36 giorni; `calendar.txt` e' vuoto, tutto e' per data). Oggi (29/10) e' coperto, ma scade tra tre settimane: va riscaricato.
  - Un solo ente (`agency.txt`: ATM). `routes.txt`: 169 linee = 5 metro (M1-M5, `route_type` 1), 17 tram (`route_type` 0), 147 bus/filobus (`route_type` 3). `stops.txt`: 4.915 fermate. `trips.txt`: 124.020 corse. `stop_times.txt`: 2.900.116 righe (307 MB estratto). Ha anche `shapes.txt`. Tutte le fermate sono dentro il rettangolo di Milano.
  - **Non ci sono** treni suburbani/Passante, ne' linee extraurbane ATM: sono nell'altro file.
  - Licenza: CC-BY (scheda CKAN "Creative Commons Attribution"): ripubblicabile citando Comune di Milano / AMAT.
- **Trenord (treni regionali, S, RE, R)**: portale Regione Lombardia, scheda `3z4k-mxz9` "Orario Ferroviario Regionale Gtfs", `https://www.dati.lombardia.it/api/views/3z4k-mxz9/files/d893b62a-6f97-44fc-b31b-e92a9c37b057?download=true&filename=trenord_gtfs.zip`. File `raw\gtfs\trenord_gtfs.zip`, 1,66 MB, estratto in `ext_trenord\`.
  - File datato 03/08/2026; **validita' fino al 12/12/2026** (`calendar_dates.txt`: 140 date da 26/07 al 12/12/2026, include oggi). Un ente (Trenord). 63 linee (60 `route_type` 2, 3 di tipo bus), 566 stazioni (38 nel rettangolo di Milano), 8.470 corse, 90.553 righe di `stop_times` (circa 10,7 fermate per corsa).
  - Ci sono le S (S1-S13, S19, S30-S50), RE, R e RE51/RE54 per Malpensa. Non ho verificato se il Malpensa Express e' completo.
  - Licenza: CC BY 4.0 (Trenord, via PoliS-Lombardia/Regione): ripubblicabile citando.
- **Trappole**: il feed ATM non ha `calendar.txt` (solo date); il feed Trenord non ha ne' `calendar.txt` ne' `shapes`, ogni corsa ha un suo `service_id`. Le due fonti hanno ID fermate diversi: i trasferimenti metro-treno vanno costruiti a mano (distanza a piedi). Nessun orario in tempo reale. Le corse Trenord hanno poche fermate per corsa (mediana 10): da controllare in fase 2 che i tempi di percorrenza bastino.

## 3. BikeMi e incidenti
### BikeMi
- Scheda `ds65_infogeo_aree_sosta_bike_sharing_localizzazione_` (Stazioni BikeMi). File `raw\bikemi\bikemi_stazioni.csv` (61 KB, separatore `;`) e `.geojson` (127 KB). Campi: `id_amat, stato, numero, nome, tipo, stalli, sede, indirizzo, zd_attuale, anno, LONG_X_4326, LAT_Y_4326`.
- 325 stazioni, tutte `attiva` (264 monofacciali, 58 bifacciali, 3 virtuali), 9.452 stalli in totale; anno di installazione fino al **2021**. **Trappola**: i file risalgono a settembre 2022 (il Comune ha toccato la scheda il 08/05/2026 ma non i file): il numero attuale di stazioni potrebbe essere diverso. Niente disponibilita' in tempo reale (non richiesta). Licenza CC-BY.

### Incidenti stradali
Nessuna fonte aperta con le coordinate di ogni incidente a Milano: ISTAT non le pubblica nei file aperti; il Comune pubblica solo conteggi mensili.
- **Migliore con luogo (strada/civico)**: Regione Lombardia / PoliS-Lombardia, "Incidenti Stradali - Microdati - Anno AAAA" (dati ISTAT, rilevazione IST-00142, incidenti con lesioni a persone). Un file per anno, schede Socrata su dati.lombardia.it (ID in `scripts\incidenti_ids.json`; per es. 2024 = `san9-3hvn`). Scaricato solo il Comune di Milano (`denominazione_comune = MILANO`) per **2010-2024**: `raw\incidenti\lombardia_microdati\incidenti_microdati_lombardia_AAAA_MILANO.json`, 15 file, ~66 MB. Righe per anno: 12.085 (2010), 8.263 (2019), 4.856 (2020), 7.743 (2024). Script: `scripts\scarica_incidenti.py`. Il 2025 non c'e' ancora.
  - Campi: anno, mese (niente giorno ne' ora), `nome_strada` (testo libero: "via Monte Rosa, 57", "via Padova, palo luce 124", "via Valtellina incrocio viale Jenner"), `tipo_strada`, `localizzazione_incidente`, `intersezione_nonintersezione`, `natura_incidente`, tipo veicolo A/B/(C), eta' conducenti, pedoni morti/feriti, morti entro 24 ore/30 giorni, feriti. **Niente coordinate**: per metterli su mappa serve geocodificare `nome_strada` (circa 46% ha civico o palo luce, 49% e' un incrocio). Granularita': via/incrocio.
  - Licenza: CC BY 4.0 (PoliS-Lombardia - ISTAT). Ripubblicabile citando.
- **Conteggi del Comune** (totali mensili, senza luogo preciso): `raw\incidenti\comune_milano\` - `ds175` per mese 2001-2025 (300 righe; campi `Anno, Mese, IncidentiMortali, IncidentiSoliFeriti, Morti, Feriti`), `ds176` per natura dell'incidente (2.698 righe), `ds177` per municipio 2020-2025 (703 righe), `ds179` per numero di veicoli (300 righe). Dati Polizia Locale; licenza CC-BY. Il 2025 e' completo fino a dicembre.
- **Trappola dei numeri**: i due archivi non coincidono. 2024: Comune `ds175` 7.602 incidenti (IncidentiMortali + IncidentiSoliFeriti), 9.384 feriti; microdati 7.743 righe, 9.585 feriti. Il 2020 (Covid) ha circa meta' dei casi. I morti nei microdati vanno letti da `tot_morti_a_24ore_incidente` o `..._30gg`, che sono due definizioni diverse.

## 4. Strumenti di calcolo percorsi su questo PC (non installato nulla)
PC: Intel i5-12600K (10 core, 16 thread), 31,8 GB RAM, 78 GB liberi su disco, Windows 11.
- **Presenti**: Python 3.12.10 con numpy 2.5, scipy 1.18, networkx 3.6, pandas 3.1, numba 0.67, scikit-learn, matplotlib, lxml, requests; Git Bash con `pdftotext`.
- **Assenti**: Java (`java -version` non trovato), Docker (non trovato), WSL (non installato); anche igraph, osmium, shapely, pyproj, geopandas, pyarrow, r5py, osmnx, pyrosm.
- **Installabili da pip** (esistono pacchetti per Windows, non installati): r5py 1.1.7, pyvalhalla 3.9.1, igraph 1.0.0, osmium 4.3.2, shapely 2.2.0, pyproj 3.8.0, pandana 0.8, pyarrow 26.0.
- **Valutazione**:
  - r5py e OpenTripPlanner: vanno bene su carta (bici, piedi, GTFS insieme), ma servono Java (JDK 21 o simile) che qui non c'e'; l'OSM va in formato `.pbf` (si converte con osmium da pip). Pro: motore completo, mappe di tempi gia' pronte. Contro: installare Java, 4-8 GB RAM, poco controllo sulle ipotesi (semafori, auto).
  - OSRM/Valhalla: OSRM ha bisogno di Docker (assente). Valhalla ha pacchetto pip per Windows (pyvalhalla), ma e' solo strade (bici/auto/piedi), non i mezzi pubblici.
  - **Consigliato: approccio in Python puro** con `scipy.sparse.csgraph` (Dijkstra veloce) sui grafi bici, auto e piedi costruiti dal file OSM, piu' un percorso mezzi pubblici di tipo "connection scan / RAPTOR" scritto con numba sul GTFS, con camminata fino alla fermata e attesa. Pro: nessuna installazione grossa, tutte le ipotesi (velocita' per tipo di strada, semafori, sensi unici per bici, Area C, tempo di parcheggio) in chiaro e modificabili, mappe a colori per punto di partenza con un solo calcolo da un punto verso tutti. Contro: da scrivere e collaudare (alcune settimane di lavoro in piu'), serve `shapely/pyproj` o equivalenti per le coordinate (si possono evitare con formule semplici su Milano).
  - Piano B se il Python puro e' troppo lento o impreciso: installare un JDK e usare r5py solo per i mezzi pubblici + piedi, tenendo bici e auto in Python.

## 5. Area C: tariffa e orari
- **Tariffe**: PDF ufficiale del Comune "Area C: ticket in vigore dal 30 ottobre 2023", `https://www.comune.milano.it/documents/20118/35188/Area+C+nuove+tariffe+dal+2023+Area+C.pdf/5ee21a73-7301-60c7-d2fe-5e2f77e8a158?version=1.0&t=1746021538283&download=true`, salvato in `raw\areac\area_c_tariffe_2023.pdf` (45 KB). Valori: tutti i veicoli **7,50 euro**; residenti (e assimilati) con veicolo registrato **3,00 euro dal 51° accesso/anno**; veicoli "di servizio" 4,50; veicoli in sosta in autorimesse in Area C 4,50; pagamento tardivo (entro 7 giorni) 22,50; NCC oltre nove posti 60 / 97,50 / 150 secondo la lunghezza. Il PDF e' versione 1.0 caricata ad aprile 2025.
- **Orari**: lunedi'-venerdi' 7:30-19:30, festivi esclusi; nel fine settimana non e' attiva. Un biglietto vale per tutti i passaggi dello stesso veicolo nel giorno. Fonte: riassunto dei risultati di ricerca sulle pagine FAQ ufficiali del Comune (`https://servizicrm.comune.milano.it/centro-supporto/KA-01151/Orari-di-attivazione-Area-C`, "Quando e' attiva Area C?"; `.../KA-01642/Costo-accesso-giornaliero-Area-C`; `.../KA-01156/Ingressi-gratuiti-residenti-Area-C`). **Non ho potuto leggere le pagine ufficiali**: il sito del Comune risponde "403 Forbidden" a qualsiasi programma (curl, WebFetch, anche la copia di web.archive.org). Gli orari vanno quindi verificati a mano su `https://www.comune.milano.it/aree-tematiche/mobilita/area-c` prima di usarli. Alcuni siti terzi indicano 5 euro: sono vecchi o sbagliati, vale il PDF.
- Il confine di Area C (poligono) non e' scaricato qui: probabilmente e' nei dati del filone `area-c`.
- Licenza del PDF: non indicata, non ripubblicare il file; i valori sono un fatto pubblico e si possono citare.

## Cosa manca / bloccato
- Orari e regole Area C da pagina ufficiale (sito del Comune blocca i programmi); il poligono di Area C.
- Incidenti con coordinate: non esiste in forma aperta; serve geocodificare le strade (fase 2).
- Stazioni BikeMi aggiornate a oggi (file del 2022).
- Velocita' reali del traffico auto: nessun dato aperto, come previsto.

---

## Fase 2 - motore bici / auto / mezzi (29 ottobre 2026, nessuna pagina del sito, nessun git)

Tutto e' Python puro (numpy, scipy, numba, pyproj, shapely, matplotlib): niente Java, niente Docker, niente servizi a pagamento o con chiave. Script in `scripts\f2_*.py`, dati intermedi in `out\`, tutte le ipotesi in `scripts\f2_parametri.py`. Comandi per rifare tutto in `STATO.md`.

### 1. Orari dei mezzi aggiornati
- ATM/AMAT, riscaricato il 29/10/2026: `raw\gtfs\gtfs_comune_milano_amat_new.zip` (25,5 MB, estratto in `ext_comune_new\`). **Versione 425, validita' 26/10/2026 - 30/11/2026** (file `feed_info.txt` e `calendar_dates.txt`, 36 giorni). Il vecchio file (versione 424, fino al 20/11) resta in `raw\gtfs\`. Da riscaricare dopo il 30/11.
- Trenord: file invariato (validita' fino al 12/12/2026, vedi fase 1).
- Giorno usato nel calcolo: **martedi' 3 novembre 2026** (giorno feriale normale). Corse attive quel giorno: ATM 25.133 (116.218 collegamenti tram, 61.672 metro, 385.902 bus/filobus), Trenord 2.893 (30.363 collegamenti treno, piu' i bus sostitutivi). In tutto 594.155 collegamenti tra fermate vicine e 5.485 fermate (`out\gtfs_info.json`).

### 2. Come e' fatto il motore
- **Reti**: dal ritaglio OSM del 29/10/2026 (`out\osm_parsed.pkl`) si costruiscono tre grafi (`out\g_walk.npz`, `g_bike.npz`, `g_car.npz`), tenendo solo la parte connessa piu' grande: piedi 647.424 nodi e 24.597 km di archi, bici 384.345 nodi e 12.674 km (9.824 km veloci come una ciclabile: `highway=cycleway`, sentieri `bicycle=designated`, strade con corsia/pista scritta), auto 294.350 nodi e 8.819 km (sensi unici rispettati).
- **Percorsi**: Dijkstra di scipy da un punto verso tutti (bici, auto, piedi). Per l'auto, lungo l'albero dei percorsi si calcolano anche i km percorsi e se il percorso passa dentro Area C.
- **Mezzi pubblici**: algoritmo "Connection Scan" (scritto con numba) sul GTFS del giorno: a piedi dall'origine alle fermate entro 800 m, attesa dall'orario vero, cambi con margine di 45 secondi e a piedi fino a 300 m (21.294 collegamenti pedonali tra fermate, calcolati sulla rete pedonale, tra ATM e Trenord compresi), a piedi dall'ultima fermata alla meta entro 800 m. Si fa la **media di 6 partenze** (ora, +2, +4, +6, +8, +10 minuti) per non dipendere da un orario fortunato. Massimo 2 ore di viaggio.
- **Celle**: 2.915 celle di 250 m con il centro dentro il confine del Comune (181,8 km2). Di queste, 124 sono in Area C, 492 nel "semicentro" (entro 3,5 km dal Duomo), 2.299 in periferia. 423 celle (14,5%) non hanno nessuna fermata entro 800 m (parchi, campagna del sud, zone industriali): per i mezzi risultano irraggiungibili.
- **Tempi di calcolo** (PC con i5-12600K): caricare il motore 1 s, preparare le 2.915 destinazioni 2 s (una volta sola), **una partenza verso tutte le celle: 0,1-0,3 s per fascia oraria** (l'obiettivo era 30 s). 300 partenze x 2.915 celle x 3 fasce (2,6 milioni di coppie) in circa 105 secondi.
- **Fuori rete**: se l'origine o la meta sono lontane dalla strada piu' vicina, il tratto si fa a piedi in linea retta (a 5 km/h per la bici, a 4,5 km/h per le altre); fino a 727 m per l'auto (parchi).

### 3. Tabella delle ipotesi (tutte da tarare con i 20 tragitti)
| Cosa | Valore usato | Da dove viene |
|---|---|---|
| Velocita' a piedi | 4,5 km/h | mandato |
| Attesa semaforo, a piedi | 10 s | ipotesi mia |
| Bici su pista ciclabile (e strade con corsia/pista) | 15 km/h | mandato |
| Bici su strada normale | 13 km/h | mandato |
| Bici su strada di servizio / living street | 12 km/h | ipotesi mia |
| Bici su area pedonale con `bicycle=yes/designated` | 10 km/h | ipotesi mia |
| Bici a mano (area pedonale, `bicycle=dismount`) | 5 km/h | mandato |
| Bici su sterrato (`track`) | 10 km/h; fondo non asfaltato x0,8; pave' x0,85 | ipotesi mia |
| Attesa media a un semaforo, bici | 15 s | mandato |
| Attraversamento senza semaforo di una strada primary/secondary/trunk | 8 s | ipotesi mia |
| Semafori sulle ciclabili e marciapiedi | i gruppi di semafori entro 30 m (incrocio piu' attraversamenti) pesano 1/radice(n) ciascuno; sulle strade contano solo i semafori d'incrocio e gli attraversamenti semaforici isolati (nessun incrocio entro 40 m, deduplicati) | mia scelta, per non contare 4 volte lo stesso incrocio |
| Sensi unici per la bici | rispettati, tranne `oneway:bicycle=no` o corsie contromano (`cycleway=opposite*`, `cycleway:*:oneway=-1/no`) | mandato |
| Vietato alla bici | autostrade, `trunk` (salvo `bicycle=yes/designated`), `bicycle=no`, accesso privato, scale, `footway` senza `bicycle` | mandato + mia scelta |
| Bici: aprire e chiudere il lucchetto | 60 s in totale | ipotesi mia |
| Auto: velocita' di marcia tra un semaforo e l'altro, 08:00 / 12:00 / 21:00 (km/h, PRIMA della taratura) | autostrada 45/70/90; svincoli 30/40/50; trunk 35/45/60; primary 26/34/40; secondary 23/30/36; tertiary 21/27/32; unclassified 20/24/28; residential 18/22/25; servizio 12/14/15; living street 10 | ipotesi mia (valori tipici) |
| Auto: limite scritto in OSM (`maxspeed`) | velocita' mai oltre l'85% del limite | ipotesi mia |
| Auto: attesa media a un semaforo | 20 s (08:00), 15 s (12:00), 10 s (21:00) | ipotesi mia |
| Auto: taratura | un fattore per fascia, 0,916 (08:00), 1,056 (12:00), 1,158 (21:00): il tempo medio ogni 10 km sul percorso, per viaggi di 6-14 km, esce uguale all'obiettivo | `scripts\f2_taratura.py` |
| Auto: obiettivo 08:00 | **38 min 43 s ogni 10 km** (15,5 km/h) | TomTom Traffic Index, pagina Milano, dati 2025, ora di punta mattina (https://www.tomtom.com/traffic-index/milan-traffic/). Stesso sito: media sull'anno 31 min 35 s ogni 10 km; 2022: 27 min 30 s |
| Auto: obiettivi 12:00 e 21:00 | 27 min e 21 min ogni 10 km (22 e 29 km/h) | **ipotesi mia**, non c'e' un dato libero per le due fasce: da tarare con Google Maps |
| A piedi fino all'auto e dal parcheggio alla meta | 2 min + 2 min | mandato (letto come 2 min per parte) |
| Ricerca parcheggio alla meta | Area C 12 min, semicentro (entro 3,5 km dal Duomo) 8 min, periferia 4 min | mandato (valori), raggio del semicentro scelto da me |
| Area C | si paga 7,50 euro se la meta e' dentro o il percorso passa dentro (non conta se si parte da dentro), lun-ven 7:30-19:30; alle 21:00 non si paga. Il costo non e' nei tempi | tariffa dal PDF del Comune; **orari ancora da verificare** (sezione 5 sopra); poligono: `area-c\raw\ds51_aree-pedonali-e-ztl\disciplina_aree.geojson` (tipo `AREA_C`) |
| Mezzi: a piedi alla fermata | massimo 800 m (rete pedonale vera, 4,5 km/h), fermata agganciata alla rete entro 150 m | mandato |
| Mezzi: cambi a piedi | massimo 300 m di rete pedonale; margine minimo 45 s per cambiare mezzo | mandato + ipotesi mia (45 s) |
| Mezzi: partenze | martedi' 3/11/2026 alle 08:00, 12:00, 21:00, media di 6 partenze nei 10 minuti dopo | mia scelta |
| Mezzi: dati usati | ATM versione 425 (metro, tram, bus, filobus) + Trenord (S, RE, R e bus sostitutivi); niente tempo reale, niente ritardi, niente biglietti | fase 1 |

### 4. Primi risultati: chi arriva prima (300 partenze a caso x 2.915 celle, martedi' 3/11/2026)
Confronto "porta a porta": bici (con 1 min di lucchetto), auto (guida + 2 + 2 min a piedi + ricerca del parcheggio), mezzi (a piedi, attesa, viaggio, a piedi). Non conta il costo (Area C 7,50 euro, biglietti, carburante). Le celle senza fermate entro 800 m (14,5%) non permettono ai mezzi di vincere. La coppia con origine e destinazione nella stessa cella e' esclusa. "Vittoria netta" = il primo batte il secondo di almeno il 10%. File: `out\quote_vittorie.csv`, `out\tempi_mediani.csv`.

**Ore 08:00**
| Distanza in linea retta | coppie | bici % | auto % | mezzi % | vittoria netta (>=10%) % | mezzi non raggiungibili % |
|---|---|---|---|---|---|---|
| 0-1 km | 12003 | 92.1 | 2.9 | 5.0 | 92.6 | 18.1 |
| 1-2 km | 36825 | 92.6 | 5.2 | 2.2 | 90.8 | 17.7 |
| 2-4 km | 128702 | 78.1 | 14.8 | 7.1 | 65.0 | 17.7 |
| 4-6 km | 172253 | 44.3 | 38.8 | 17.0 | 44.1 | 20.3 |
| 6-8 km | 179786 | 18.5 | 55.0 | 26.5 | 48.8 | 23.2 |
| 8-12 km | 261254 | 4.6 | 68.2 | 27.2 | 60.5 | 33.7 |
| oltre 12 km | 83377 | 0.3 | 90.8 | 8.9 | 81.3 | 57.3 |
| tutte | 874200 | 30.6 | 50.4 | 19.0 | 59.3 | 27.9 |

**Ore 12:00**

| Distanza in linea retta | coppie | bici % | auto % | mezzi % | vittoria netta (>=10%) % | mezzi non raggiungibili % |
|---|---|---|---|---|---|---|
| 0-1 km | 12003 | 89.8 | 5.6 | 4.6 | 90.4 | 18.1 |
| 1-2 km | 36825 | 82.1 | 16.3 | 1.5 | 76.3 | 17.7 |
| 2-4 km | 128702 | 33.6 | 61.5 | 4.9 | 60.3 | 17.7 |
| 4-6 km | 172253 | 5.5 | 86.9 | 7.6 | 78.8 | 20.3 |
| 6-8 km | 179786 | 0.8 | 92.6 | 6.7 | 87.8 | 23.2 |
| 8-12 km | 261254 | 0.0 | 97.5 | 2.5 | 94.4 | 33.7 |
| oltre 12 km | 83377 | 0.0 | 100.0 | 0.0 | 99.7 | 57.3 |
| tutte | 874200 | 10.9 | 84.7 | 4.4 | 84.6 | 27.9 |

**Ore 21:00**

| Distanza in linea retta | coppie | bici % | auto % | mezzi % | vittoria netta (>=10%) % | mezzi non raggiungibili % |
|---|---|---|---|---|---|---|
| 0-1 km | 12003 | 87.4 | 8.2 | 4.3 | 88.8 | 18.1 |
| 1-2 km | 36825 | 67.3 | 31.7 | 1.0 | 68.6 | 17.7 |
| 2-4 km | 128702 | 15.8 | 81.5 | 2.7 | 76.5 | 17.7 |
| 4-6 km | 172253 | 0.9 | 96.8 | 2.4 | 93.4 | 20.3 |
| 6-8 km | 179786 | 0.0 | 98.8 | 1.1 | 97.5 | 23.2 |
| 8-12 km | 261254 | 0.0 | 99.9 | 0.1 | 99.4 | 33.7 |
| oltre 12 km | 83377 | 0.0 | 100.0 | 0.0 | 100.0 | 57.3 |
| tutte | 874200 | 6.5 | 92.2 | 1.2 | 93.1 | 27.9 |

Tempi mediani in minuti, ore 08:00 (`out\tempi_mediani.csv` ha anche le altre fasce):
| Distanza | bici | auto (solo guida) | auto (porta a porta) | mezzi | a piedi |
|---|---|---|---|---|---|
| 0-1 km | 8.5 | 6.9 | 16.4 | 13.2 | 14.0 |
| 1-2 km | 14.7 | 11.8 | 21.3 | 23.0 | 28.4 |
| 2-4 km | 25.2 | 19.6 | 29.0 | 33.6 | 53.2 |
| 4-6 km | 37.3 | 28.7 | 38.1 | 42.8 | 78.6 |
| 6-8 km | 49.5 | 37.7 | 46.9 | 50.1 | 89.5 |
| 8-12 km | 66.4 | 48.7 | 57.4 | 60.4 | - |
| oltre 12 km | 87.0 | 58.8 | 66.9 | 76.7 | - |
| tutte | 49.8 | 37.2 | 46.5 | 48.6 | 62.8 |

Cose da notare (non sono risultati finali, i numeri vanno prima tarati):
- La bici vince nei viaggi corti (fino a 2 km circa) in tutte le fasce; a 4-6 km vince ancora il 44% alle 08:00 (auto lenta e 4-12 min di parcheggio), poi sempre meno. L'auto vince sempre di piu' con la distanza, e a mezzogiorno e di sera molto di piu' che alle 08:00.
- Con i valori del mandato la bici risulta lenta: circa 12 km/h in media, comprese le attese ai semafori (percorso viale Sarca - via Giambellino: 11,6 km in 58 minuti, 8 dei quali di attese). Se Google dara' tempi molto piu' bassi, i primi parametri da cambiare sono l'attesa ai semafori (15 s) e la velocita' sulle strade normali (13 km/h).
- I mezzi sono penalizzati dal fatto che le coppie sono celle a caso (non case e uffici vicini alle fermate) e dalla media su 6 partenze (attesa vera). Vincono nelle zone vicine alle linee: nelle mappe si vedono le linee M1-M5 (`out\mappa_citta_08.png`).
- Alle 21:00 le linee hanno poche corse e si perdono molte coincidenze.
- Alle 08:00 l'auto prende a volte la Tangenziale per attraversare la citta' (autostrada tarata a 45 km/h x 0,916): da guardare nel confronto con Google.

Mappe di prova (PNG in `out\`): `mappa_<nome>_<ora>.png` per Duomo (08:00 e 21:00), Niguarda, Gratosoglio, Cordusio: ogni cella e' colorata col mezzo che arriva prima. `mappa_citta_08|12|21.png`: per ogni cella di arrivo, la quota di partenze (delle 300 a caso) da cui vince bici, auto, mezzi. Si rifanno con `scripts\f2_mappa.py <strand> <lon> <lat> <fascia> <nome>` e `scripts\f2_analisi.py <strand>`.

### 5. 20 tragitti di prova per Davide
`tragitti_prova.csv` (separatore `;`, aprire con Excel) e `COME_CONTROLLARE.md`. 20 tragitti da 0,7 a 11 km in linea retta: 5 con meta in Area C, 9 nel semicentro, 6 in periferia; alcuni con partenza o arrivo a meno di 100 m da una fermata della metro, altri a oltre 1 km (colonne `metro_vicino_*`); 8 con percorso in auto dentro Area C. Giorno martedi' 3/11/2026, ore 08:00 (9 tragitti), 12:00 (6), 21:00 (5). Gli indirizzi vengono dal registro dei civici del Comune. Colonne: i tempi stimati (bici = solo pedalata; auto = solo guida e anche porta a porta; mezzi = con attesa), tre colonne vuote per Google Maps e le note.

### 6. Incidenti: quanti si possono mettere su mappa
Fonte: microdati Lombardia 2010-2024, 131.435 righe di Milano (`raw\incidenti\lombardia_microdati`, campo `nome_strada`). Tipi di indirizzo sull'insieme (`out\incidenti_geo_stima.json`):
- incrocio: 67839 righe (51.6%)
- civico: 43830 righe (33.3%)
- palo_luce: 13957 righe (10.6%)
- solo_via_o_altro: 2936 righe (2.2%)
- autostrada_statale: 2554 righe (1.9%)
- vuoto: 319 righe (0.2%)

Nota: per alcuni anni il campo ha un formato vecchio "Via - Via - civico" (`Majno Luigi -  - 14`), per altri il formato "via X, 57" / "via X incrocio via Y" / "via X, palo luce 12": il programma legge entrambi.

**Come si geocodifica gratis in locale** (`scripts\f2_geocode.py`):
1. civico: registro dei civici del Comune (`citta-15-minuti\raw\comune_milano\civici`, ds634, 57.405 civici applicati con coordinate); nome strada normalizzato (senza articoli, abbreviazioni sciolte, ordine delle parole indifferente: "Pagano Mario" = "Mario Pagano"), civico esatto, altrimenti il piu' vicino della stessa parita' entro 20 numeri.
2. incrocio: nomi delle strade in OSM (7.129 strade con nome): nodo in comune fra le due strade, altrimenti il punto piu' vicino se entro 80 m.
3. solo via (palo luce, civico non trovato, incrocio non trovato): punto mediano della via, posizione solo approssimata.
Non servono servizi esterni.

**Stima su 500 righe a caso** (seme 11, `out\incidenti_geo_campione500.csv`): civico esatto **28.6%**, incrocio **45.4%**, civico approssimato 0.6%, solo la via 17.4%, nessuna posizione 8.0% (autostrade/tangenziali, nomi non riconosciuti). Posizione buona (civico esatto + incrocio): **74.0% dei casi**. Tutte le coordinate trovate cadono dentro Milano. Non verificato: l'esattezza dei punti (non c'e' una verita' di confronto); l'incrocio e' il nodo OSM comune alle due strade. I non agganciati sono in gran parte nomi particolari ("Sempione -  - 41", "via X in prossimita di ...").

Per la fase dopo: geocodificare tutte le 131.435 righe richiede pochi minuti con lo stesso programma. BikeMi (325 stazioni, file del 2022): serve ancora un controllo sulle stazioni attuali.

### 7. Limiti noti
- Divieti di svolta (4.380 in OSM) e tempi dei semafori veri non usati; ZTL e corsie preferenziali non modellate; niente pendenze (Milano e' piana); lavori in corso, parcheggi pieni, ritardi non considerati.
- Le piste ciclabili sono quelle scritte in OSM; la rete ciclabile reale puo' differire.
- Il tempo di ricerca del parcheggio e' lo stesso in tutte le fasce orarie (di sera in realta' si trova prima).
- Le velocita' dell'auto per 12:00 e 21:00 sono ipotesi; quella delle 08:00 e' ancorata a TomTom, che e' una media di tutta la citta' nel 2025.
- Il programma sceglie sempre il percorso piu' veloce: Google a volte consiglia percorsi piu' tranquilli per le bici.

---

<!-- FASE3 -->
## Fase 3 - taratura con Google Maps e risultati (29 ottobre 2026; riscritta da `scripts\f3_note.py`)

Taratura fatta con i tragitti di prova che hanno i tempi di Google Maps letti il 29/10/2026 per martedi 3/11/2026 (file: `tragitti_prova.csv`, `tragitti_prova_2.csv`). Tragitti usati: **120** (con valore Google: bici 120, auto 120, mezzi 120); ore 08:00 = 42, 12:00 = 39, 21:00 = 39. Divisione 70/30 per ora e distanza: **84 di taratura** (scelta dei parametri) e **36 di controllo** (solo per misurare l'errore, non toccati dalla taratura). Google e' un riferimento, non la verita': i suoi tempi di auto sono intervalli ("tipicamente X-Y min", usato il valore di mezzo), la bici e' un percorso consigliato, i mezzi sono il primo percorso proposto. I tempi di Google non sono pubblicati, solo i nostri errori in percentuale.

### Cosa e' cambiato (valore vecchio -> valore nuovo, perche)
| Parametro | Prima | Dopo | Perche |
|---|---|---|---|
| Bici su strada normale (km/h) | 13 | 17 | la nostra bici era sempre piu lenta di Google (rapporto mediano 1,403). Velocita su strada cercata tra 14 e 18 km/h: la prima per cui il rapporto mediano sui tragitti di taratura sta tra 0,95 e 1,05 (regola in `f3_calibra.py`) |
| Bici su ciclabile o corsia (km/h) | 15 | 19 | strada + 2 km/h |
| Bici su strada di servizio (km/h) | 12 | 16 | strada - 1 km/h |
| Attesa media a un semaforo, bici (s) | 15 | 6 | la bici supera spesso le code e prende scorciatoie; si prova prima 6 s, poi 4 s, poi 2 s se la velocita da sola non basta |
| Attraversamento senza semaforo di strada grande, bici (s) | 8 | 3 | meta dell'attesa al semaforo |
| Bici: pedonale pedalabile, a mano, sterrato (km/h) | 10, 5, 10 | 10, 5, 10 | invariati (pochi tratti) |
| Bici: lucchetto | 60 s | 60 s | invariato (Google non lo conta, il confronto con Google e' sulla sola pedalata) |
| Auto: fattore di velocita ore 08:00 | 0,916 | 0,916 | invariato: ancorato a TomTom (38 min 43 s ogni 10 km) |
| Auto: fattore di velocita ore 12:00 | 1,056 | 0,77 | prima era un'ipotesi (27 min ogni 10 km). Un moltiplicatore comune alle ore 12 e 21 portato a rapporto mediano 1 sui tragitti di taratura (esclusi quelli con meta a meno di 1 km, dove Google gira largo per le zone chiuse) |
| Auto: fattore di velocita ore 21:00 | 1,158 | 0,845 | idem |
| Mezzi: margine per cambiare mezzo (s) | 45 | 180 | i nostri mezzi erano ottimisti (Google propone il primo percorso, non il piu veloce in assoluto) |
| Mezzi: tempo per scendere/salire al binario di metro e treno (s, all'inizio e alla fine) | 0 | 60 | la fermata del GTFS e' il binario, ma si parte dalla strada. Scelto con una griglia (margine 45-180 s x accesso 0-120 s) minimizzando errore medio + distorsione |
| Mezzi: velocita a piedi, distanza massima a piedi | 4,5 km/h; 800 m / 300 m (400 m tra due stazioni, vedi correzioni mezzi) | invariati | non modificati: cambiano poco il risultato e sono scelte di principio |

### Errori prima e dopo (nostra stima / Google: 1,00 = uguale; errore in % del tempo Google)
| Mezzo | Gruppo | N | Rapporto mediano prima | dopo | Errore mediano prima | dopo | Errore medio prima | dopo |
|---|---|---|---|---|---|---|---|---|
| Bici | taratura | 84 | 1,414 | 1,028 | 41,4% | 7,6% | 46,6% | 15,1% |
| Bici | controllo | 36 | 1,382 | 1,013 | 38,2% | 6,4% | 44,8% | 11,8% |
| Bici | tutti | 120 | 1,403 | 1,02 | 40,3% | 7,4% | 46,1% | 14,1% |
| Auto (solo guida) | taratura | 84 | 0,913 | 1,024 | 16,4% | 11,4% | 18% | 14,8% |
| Auto (solo guida) | controllo | 36 | 0,875 | 1,024 | 17,4% | 9,9% | 17,7% | 14,4% |
| Auto (solo guida) | tutti | 120 | 0,905 | 1,024 | 16,5% | 10,9% | 17,9% | 14,7% |
| Mezzi | taratura | 84 | 0,91 | 1 | 10,4% | 6,9% | 10,7% | 8,7% |
| Mezzi | controllo | 36 | 0,891 | 1,001 | 13,4% | 7,5% | 13,3% | 11,1% |
| Mezzi | tutti | 120 | 0,906 | 1 | 11,5% | 7% | 11,5% | 9,4% |

Auto per ora di partenza (tutti i tragitti), rapporto mediano prima -> dopo: 08:00 = 1,058 -> 1,058 (N=42); 12:00 = 0,872 -> 1,096 (N=39); 21:00 = 0,727 -> 0,914 (N=39).

Attenzione: con pochi tragitti per ora (vedi N) l'errore sul gruppo di controllo e' molto incerto. Nella taratura 12:00 e 21:00 l'auto diventa lenta quasi quanto alle 08:00 sulle strade principali: probabilmente il valore di mezzo dell'intervallo di Google e' pessimista per le ore tranquille; con il valore basso l'auto vincerebbe di piu.

### Risultati generali dopo la taratura (tutte le coppie cella-cella: 2.915 x 2.915 celle da 250 m, martedi 3/11/2026)
Chi arriva prima porta a porta (bici con 1 min di lucchetto; auto con 2+2 min a piedi e ricerca del parcheggio; mezzi con attesa vera). Non conta il costo. Le celle senza fermate entro 800 m non danno vittorie ai mezzi.

**Ore 08:00**
| Distanza in linea retta | coppie | bici % | auto % | mezzi % | vittoria netta (>=10%) % | a piedi batte tutti % | mezzi non raggiungibili % |
|---|---|---|---|---|---|---|---|
| 0-1 km | 117938 | 96,5 | 1,9 | 1,7 | 97,2 | 3,4 | 18,4 |
| 1-2 km | 361252 | 98,3 | 1,6 | 0,1 | 97,8 | 0,2 | 18,5 |
| 2-4 km | 1245542 | 97,4 | 2,4 | 0,2 | 95,6 | 0 | 17,8 |
| 4-6 km | 1642070 | 94,5 | 4,8 | 0,7 | 90,2 | 0 | 19,5 |
| 6-8 km | 1725316 | 91,1 | 7,6 | 1,3 | 84,5 | 0 | 22,5 |
| 8-12 km | 2570844 | 84,3 | 14 | 1,7 | 75,5 | 0 | 32,5 |
| oltre 12 km | 831348 | 57 | 42,2 | 0,9 | 51,9 | 0 | 57,4 |
| tutte | 8494310 | 87,7 | 11,3 | 1,1 | 82,1 | 0,1 | 27,5 |

**Ore 12:00**
| Distanza in linea retta | coppie | bici % | auto % | mezzi % | vittoria netta (>=10%) % | a piedi batte tutti % | mezzi non raggiungibili % |
|---|---|---|---|---|---|---|---|
| 0-1 km | 117938 | 96,4 | 2 | 1,6 | 97,1 | 3,4 | 18,4 |
| 1-2 km | 361252 | 98 | 1,9 | 0,1 | 97,5 | 0,2 | 18,5 |
| 2-4 km | 1245542 | 96,4 | 3,4 | 0,2 | 94 | 0 | 17,8 |
| 4-6 km | 1642070 | 91,4 | 8 | 0,6 | 85 | 0 | 19,5 |
| 6-8 km | 1725316 | 84,6 | 14,2 | 1,2 | 73,9 | 0 | 22,5 |
| 8-12 km | 2570844 | 69,6 | 29 | 1,4 | 56,8 | 0 | 32,5 |
| oltre 12 km | 831348 | 23,5 | 76,2 | 0,3 | 58,4 | 0 | 57,5 |
| tutte | 8494310 | 77,9 | 21,3 | 0,9 | 73,6 | 0,1 | 27,4 |

**Ore 21:00**
| Distanza in linea retta | coppie | bici % | auto % | mezzi % | vittoria netta (>=10%) % | a piedi batte tutti % | mezzi non raggiungibili % |
|---|---|---|---|---|---|---|---|
| 0-1 km | 117938 | 95,9 | 2,6 | 1,6 | 96,5 | 3,4 | 19,1 |
| 1-2 km | 361252 | 96,3 | 3,7 | 0,1 | 95,2 | 0,2 | 19,8 |
| 2-4 km | 1245542 | 89,4 | 10,5 | 0,1 | 80,5 | 0 | 19,4 |
| 4-6 km | 1642070 | 66,4 | 33,1 | 0,4 | 53,4 | 0 | 21,6 |
| 6-8 km | 1725316 | 37,6 | 61,7 | 0,7 | 47,3 | 0 | 25,5 |
| 8-12 km | 2570844 | 10,8 | 88,8 | 0,4 | 64,8 | 0 | 37,1 |
| oltre 12 km | 831348 | 0,3 | 99,7 | 0 | 94,3 | 0 | 63,7 |
| tutte | 8494310 | 42,3 | 57,3 | 0,4 | 66 | 0,1 | 30,8 |

### Sensibilita alla velocita della bici (tutte le coppie; auto e mezzi invariati)
Il risultato dipende molto dalla velocita della bici: la taratura su Google porta a circa 17-18 km/h su strada (veloce per una bici normale). Quote di vittoria su tutte le coppie:
| Bici | ore | bici % | auto % | mezzi % |
|---|---|---|---|---|
| come tarata (17 km/h su strada, semaforo 6 s) | 08:00 | 87,7 | 11,3 | 1,1 |
| come tarata (17 km/h su strada, semaforo 6 s) | 12:00 | 77,9 | 21,3 | 0,9 |
| come tarata (17 km/h su strada, semaforo 6 s) | 21:00 | 42,3 | 57,3 | 0,4 |
| bici 15 km/h su strada, 17 su ciclabile, semaforo 8 s | 08:00 | 71,4 | 24,7 | 3,9 |
| bici 15 km/h su strada, 17 su ciclabile, semaforo 8 s | 12:00 | 55,5 | 41,7 | 2,8 |
| bici 15 km/h su strada, 17 su ciclabile, semaforo 8 s | 21:00 | 24,6 | 74,5 | 0,9 |
| bici 13 km/h su strada, 15 su ciclabile, semaforo 15 s (le ipotesi iniziali, prima della taratura) | 08:00 | 33,2 | 56,1 | 10,7 |
| bici 13 km/h su strada, 15 su ciclabile, semaforo 15 s (le ipotesi iniziali, prima della taratura) | 12:00 | 23,6 | 70,3 | 6,2 |
| bici 13 km/h su strada, 15 su ciclabile, semaforo 15 s (le ipotesi iniziali, prima della taratura) | 21:00 | 11,1 | 87,3 | 1,6 |

I risultati della "Fase 2" in questo file (sezione 4) sono i primi, prima della taratura: valgono questi.

Come rifare tutto: `STATO.md` (una riga: `scripts\f3_rifai.py`). Dati della pagina: `docs\bici-auto-mezzi\data\`.
<!-- /FASE3 -->

## Fase 3 - correzioni mezzi (29 ottobre 2026; scritta a mano, fuori dal blocco riscritto da `f3_note.py`)
Rapporto completo con tabelle prima/dopo e prove: `out\verifica_mezzi.md`.
- **Il 20% "mezzi non raggiungibili" non e' un errore**: sono le coppie in cui partenza o arrivo non ha nessuna fermata entro 800 m a piedi. 423 quadrati su 2.915 (14,5%), quasi tutti parchi, campagna, scali ferroviari e bordi della periferia (mappa `out\mappa_irraggiungibili.png`, numeri `out\irraggiungibili.json`). Se entrambi i quadrati hanno una fermata la coppia e' sempre raggiungibile. La pagina ora mostra anche le quote solo tra coppie servite (73% delle coppie).
- **Errore 1 (corretto)**: in `f2_motore.py` le fermate "stazione" (tempo extra per il binario) erano `rtype >= 1`, cioe' anche tutti i bus. Ora solo metro (1) e treno (2): 573 fermate invece di 4.725.
- **Errore 2 (corretto)**: mancavano i cambi tra stazioni oltre i 300 m (Loreto M1-M2, Centrale M2-treni, Porta Venezia M1-Passante). Ora: cambi ufficiali ATM (`transfers.txt`) sempre ammessi, e 400 m (`STATION_TRANSFER_M` in `f2_parametri.py`) tra due stazioni metro/treno. `f2_gtfs.py` salva anche `stop_gid`; `out\footpaths.npz` ha una versione (`FP_VERSION` in `f2_motore.py`) e si ricalcola da solo se cambia.
- Effetto delle sole correzioni: piccolo (tempo mediano mezzi 53,7 -> 52,6 min su 120 partenze a caso alle 8). Il grosso della variazione nelle quote viene dalla nuova taratura con 56 tragitti Google (prima 20): bici 17 km/h e semaforo 6 s, auto 0,739 (12:00) e 0,81 (21:00), margine di cambio 180 s (bordo della griglia), tempo binario 0 s.
- Quote 08:00 su tutte le coppie, prima -> dopo (bici/auto/mezzi): 91,2/8,3/0,6 -> 87,1/11,3/1,6. 21:00: 67,0/32,7/0,3 -> 46,6/52,7/0,7. Solo coppie servite 08:00: 91,7/6,2/2,2.
- Prove di buon senso (`scripts\f3_verifica.py`, 10 tragitti, risultati in `out\f3_verifica_prima.json` e `out\f3_verifica_dopo.json`): tutte dentro l'intervallo atteso. Da stazione a stazione i mezzi battono la bici; sui tragitti solo bus in periferia la bici vince largamente.
- Pagina: aggiunta la frase "solo coppie servite" sotto la tabella, frase "i mezzi vincono poco" scritta dai dati, nota sui cambi a 400 m, nota "nessun tempo in piu' per il binario" quando il valore e' 0. Testata con la preview "milano-in-dati" porta 8796 (`/bici-auto-mezzi/`): nessun errore, larghezza 375 px ok.
- Da rifare con `f3_rifai.py` quando `tragitti_prova_2.csv` e' completo.
