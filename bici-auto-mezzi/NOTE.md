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
