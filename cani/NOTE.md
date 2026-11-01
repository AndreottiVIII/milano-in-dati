# Cani di Milano - FASE 1 (raccolta, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto>` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`.

## 1. In breve

1. **Il dato che serve (quanti cani, di che razza, in che quartiere, anno per anno) NON è aperto.** L'anagrafe canina è della Regione Lombardia (banca dati SINAC, gestita dalle ATS: per Milano ATS Milano). La pagina della Regione dice che si può solo cercare un singolo animale per microchip; nessuna statistica, nessun file. Il portale del Comune ha un solo dataset sui cani (aree cani, ds52). dati.lombardia.it non ha nulla sull'anagrafe animali (solo aree di sgambatura di altri comuni). dati.gov.it ha "cani residenti per comune" solo per il Veneto (2012). **Non esiste quindi nessuna tabella (anno, zona, razza, n) per Milano, e non l'ho inventata.** Per averla bisognerebbe chiederla ad ATS Milano (accesso civico generalizzato): decisione di Davide.
2. **Quello che esiste in modo aperto sono le aree cani**: ds52 del Comune, CC-BY, 423 aree (297 parchi o giardini), 679.861 m2, con quartiere (NIL) e municipio. Più il controllo con OpenStreetMap (ODbL).
3. **Totali di cani, solo da stampa** (non sono dati aperti, non verificati alla fonte): Comune di Milano **104.067 cani** (7giorni.info, 27/11/2018, anno dei dati non dichiarato) e **118.292** (2020, Il Giorno 17/1/2022 su Legambiente X rapporto; l'articolo scrive "animali registrati" ma il numero sta nel passaggio sui cani: l'ho letto come cani). Per 100 abitanti (ds205): 7,46 (pop. 2018) e 8,49 (pop. 2020). Sono due punti, non una serie.
4. **Niente razze**: nessuna fonte con le razze di Milano. Le uniche razze pubblicate per comune in Lombardia che ho trovato sono quelle di ATS Insubria per la provincia di Varese (SaronnoNews, 19/9/2024, circa 134.000 cani), fornite al giornale, senza licenza, senza Milano.

## 2. Fonti, una per una

| Fonte | Contenuto | Anni | Righe | Dimensione | Licenza (esatta) | Scaricato | Cosa manca |
|---|---|---|---|---|---|---|---|
| **ds52 - Territorio: localizzazione delle aree cani** (dati.comune.milano.it, `ds52_infogeo_aree_cani_localizzazione`) | aree di fruizione per i cani: id_area, municipio, località, obj_id, data_ini, area_mq, perimetro, centroide; poligoni nel GeoJSON | schede dal 1983 al 20/9/2024; CKAN `metadata_modified` 8/5/2026, risorse modificate 21/11/2024; frequenza dichiarata ANNUAL | 423 | CSV 73.867 B, JSON 177.216 B, GeoJSON 1.406.935 B | CKAN `license_id = cc-by`, titolo "Creative Commons Attribution", link http://www.opendefinition.org/licenses/cc-by (la versione, es. 4.0, non è scritta) | 1/11/2026, `raw/comune_ds52/` (sha256 in `raw/download_log.csv`) | tipo di area (recintata, con giochi), apertura/chiusura, aree dismesse, cani che le usano; la data è quella della scheda, non dell'apertura |
| **OpenStreetMap `leisure=dog_park`** (Overpass API, rettangolo 45,36-45,56 / 9,00-9,32) | 415 elementi (398 aree, 15 punti, 2 relazioni); 259 dentro i confini di Milano | stato OSM al 1/11/2026 (timestamp base 18:23 UTC) | 415 | 73.772 B | ODbL ("The data is made available under ODbL", campo copyright della risposta) | 1/11/2026, `raw/osm/dog_park.json` (primo tentativo 502, secondo andato) | mappatura volontaria; serve solo come controllo |
| **Legambiente, XV rapporto "Animali in Città"** (PDF 22/7/2026, 2.616.865 B) + pagine web edizioni XIII e XV | analisi nazionale; nessun dato per razza o quartiere; nessuna tabella dei cani di Milano (cercata nel testo) | edizioni 2012-2026 | - | - | nessuna licenza dichiarata: **non ripubblicare** | 1/11/2026, `raw/legambiente/` | dati per città (stanno nei questionari, non pubblicati) |
| Articoli di stampa (Il Giorno 17/1/2022 su Legambiente X; 7giorni.info 27/11/2018; SaronnoNews 19/9/2024) | solo i numeri citati qui | 2018, 2020, 2024 | - | - | diritti riservati: si citano i fatti, non i testi | 1/11/2026 (lettura) | fonti primarie |
| Regione Lombardia, pagina "Banca dati regionale animali d'affezione" | descrive SINAC; nessun dato | - | - | - | - | 1/11/2026 (lettura) | tutto |
| dati.gov.it (CKAN) "anagrafe canina", "cani" | Veneto 2012 (cani per comune e per razza) e Oria; aree cani di Torino, Roma, ecc. | - | - | - | CC BY 4.0 | solo ricerca, non scaricato (non è Milano) | Milano |

Ricerche fatte (`raw/search_comune.json`, `raw/search_lombardia.json`): dati.comune.milano.it package_search con 16 parole (cani, cane, anagrafe canina, animali, razze, aree cani, animali d'affezione, gatti, pet, microchip, canile, sgambatura, zoofilia, veterinari, tutela animali, fauna): solo ds52 (e due dataset sui farmaci veterinari, irrilevanti). Catalogo dati.lombardia.it (Socrata, 18 parole): 40 risultati, tutti aree di sgambatura di altri comuni, aree verdi, inseminazione artificiale, o altre regioni (il catalogo senza filtro di dominio mischia anche la Catalogna). **Gatti e altri animali**: nessun dataset aperto. Dalla stampa (Il Giorno, 17/1/2022, dati 2020): 43.327 gatti registrati nel Comune, 1.320 colonie feline con circa 20.000 gatti; 82.251 gatti nell'ATS.

## 3. Pulizia (`scripts/build.py`, risultati in `pulito/riepilogo.json`)

Nessun valore corretto o cancellato; solo colonne aggiunte e flag.
- `pulito/aree_cani.csv` (423 righe, separatore `;`): `obj_id` (unico), `id_area` (identificativo del parco o giardino: 297 distinti, più aree cani nello stesso parco, fino a 12 nel Parco Nord `9_505`), `municipio`, `localita`, `data_scheda` (ISO), `anno_scheda`, `flag_data_convenzionale`, `area_mq`, `perim_m`, `lon`, `lat`, `id_nil`, `nil`, `nil_per_vicinanza`, `dist_nil_m`.
- **NIL**: centroide in poligono con gli 88 NIL (`citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson`, EPSG:4326 poi UTM 32N). 423 su 423 cadono dentro un NIL (0 per vicinanza). Controllo: un solo centroide CSV cade fuori dal proprio poligono GeoJSON (a più di 5 m; area a più parti).
- **Municipio**: preso dal file (1-9). 15 NIL hanno aree cani in più di un municipio (un NIL può stare a cavallo di due municipi): per questo i raggruppamenti per NIL e per municipio non si sommano tra loro.
- Date: 1 riga senza data; 47 con data convenzionale (1/1/1983 12 righe; 1/7/2009 34 righe; la riga senza data). Il 2003 raccoglie 77 schede su molte date vicine.
- Aree molto piccole (sotto 100 m2): 3; molto grandi (sopra 10.000 m2): 9 (Parco Forlanini 41.584 m2, Parco Nord 28.666). Media 1.607 m2, mediana 871.
- **OpenStreetMap**: `pulito/osm_dog_park.csv`. Dei 259 elementi dentro Milano, **250 stanno entro 50 m da un poligono ds52**; 9 no. Dall'altro lato, 261 delle 423 aree ds52 hanno un elemento OSM vicino: OSM è un sottoinsieme, ds52 è più completo.
- `pulito/totali_pubblicati.csv`: i totali di stampa con fonte; `pulito/serie_aree_cani_per_anno_scheda.csv`; `pulito/aree_cani_per_nil.csv`; `pulito/aree_cani_per_municipio.csv`.

## 4. Riepilogo (tutti i numeri sono nelle tabelle csv e in `riepilogo.json`)

### 4.1 Aree cani oggi (ds52, scaricato 1/11/2026; abitanti ds205 campo `Totale`, 2024 = 1.407.044)
- **423 aree, 679.861 m2, 0,48 m2 per abitante, 30,1 aree ogni 100.000 abitanti, 1 area ogni 3.326 abitanti.**
- Legambiente (X rapporto, dati 2020): 403 aree cani, 1 ogni 3.411 abitanti. Il ds52 con scheda fino al 2020 ne conta 383 (e 423 oggi): le cifre non coincidono e il perimetro del conteggio non è dichiarato.

### 4.2 Per municipio (`aree_cani_per_municipio.csv`; abitanti = censimento permanente 2023, `censimenti/pulito/indicatori_municipi.csv`, campo `pop`, che esclude le sezioni "senza dimora")
| Municipio | Aree | m2 | Abitanti | Aree per 100.000 ab. | m2 per abitante |
|---|---|---|---|---|---|
| 1 | 22 | 46.592 | 97.591 | 22,5 | 0,48 |
| 2 | 39 | 48.868 | 151.112 | 25,8 | 0,32 |
| 3 | 40 | 33.486 | 142.501 | 28,1 | 0,23 |
| 4 | 52 | 114.772 | 159.311 | 32,6 | 0,72 |
| 5 | 47 | 55.323 | 123.239 | 38,1 | 0,45 |
| 6 | 65 | 70.139 | 150.078 | 43,3 | 0,47 |
| 7 | 44 | 50.292 | 169.031 | 26,0 | 0,30 |
| 8 | 48 | 55.143 | 188.850 | 25,4 | 0,29 |
| 9 | 66 | 205.247 | 179.748 | 36,7 | 1,14 |

Il municipio 6 ha quasi il doppio di aree per abitante del municipio 1 (43,3 contro 22,5); il 9 ha cinque volte i m2 per abitante del 3 (1,14 contro 0,23), ma per il Parco Nord e Forlanini.

### 4.3 Per NIL (`aree_cani_per_nil.csv`; abitanti ds205 2024; rapporti solo per i 64 NIL con almeno 5.000 abitanti)
- 12 NIL senza nessuna area cani (tutti con meno di 5.000 abitanti: parchi e zone quasi senza residenti).
- **Meno aree per abitante**: De Angeli-Monte Rosa 4,6 per 100.000 ab. (1 area, 21.552 ab.), Stazione Centrale-Ponte Seveso 5,7, Duomo 6,2 (1 area, 16.226 ab.), Sarpi 6,5, Loreto-Casoretto-Nolo 9,2 (4 aree, 43.513 ab.), Brera 10,9.
- **Più aree per abitante**: Lorenteggio 79,2 (12 aree, 15.152 ab.), Barona 60,3, Bicocca 57,4, Taliedo-Morsenchio-Forlanini 55,9, Vigentino 55,8. Più aree in assoluto: Niguarda-Cà Granda-Prato Centenaro-Fulvio Testi 19 (52,3 per 100.000; 2,04 m2 per abitante), Gorla-Precotto 14, Gallaratese-San Leonardo-Lampugnano 13.
- **Rapporto massimo/minimo: 17 volte** (79,2 / 4,6) tra i NIL con almeno 5.000 abitanti; i sei NIL con meno aree per abitante sono tutti centrali o semicentrali (De Angeli, Centrale, Duomo, Sarpi, Loreto, Brera).

### 4.4 Nel tempo (`serie_aree_cani_per_anno_scheda.csv`)
Conta le aree con `data_ini` fino all'anno (non le aree aperte in quell'anno, vedi trappole): **200 (2011) -> 422 (2024); per 100.000 abitanti 14,9 -> 30,0**. Nuove schede per anno: 17 (2011), 26, 28, 22, 29, 17, 14, 16, 26 (2019), 5 (2020), 13, 13, 6 (2023), 7 (2024). Le aree si raddoppiano in 13 anni, i residenti ds205 crescono del 4,9% (1.341.830 -> 1.407.044).

### 4.5 Cani (solo stampa)
- Comune di Milano: 104.067 cani (7giorni, 27/11/2018) -> 118.292 (2020, Legambiente via Il Giorno): +13,7% in due anni; 7,46 e 8,49 cani ogni 100 abitanti (ds205 2018: 1.395.274; 2020: 1.392.502). Un salto di 14.000 cani in due anni non è credibile come aumento reale: è più probabilmente registrazione che cresce (in Italia i cani in anagrafe passano da 12,5 a 14,9 milioni tra 2020 e 2025, XV rapporto).
- ATS Milano (area metropolitana): 351.311 cani (2018) -> 375.887 (2020).
- Lombardia: 1.768.444 cani (2020), 1 ogni 5,6 abitanti = 17,9 per 100; **Milano 1 ogni 11, circa 9 per 100: la metà della media regionale.**
- Altro (Legambiente X, 2020): cani "di quartiere" 1.640; 1 cane in canile ogni 10.190 abitanti.

## 5. La cosa più sorprendente

**Milano ha 423 aree cani mappate al metro, ma nessun dato aperto su quanti cani ci siano**, né per razza né per quartiere, nella città che Legambiente mette prima tra le metropoli per gestione degli animali. E l'unico confronto che si può fare dice che Milano ha la metà dei cani registrati per abitante della Lombardia (circa 9 contro 18 ogni 100), mentre le aree cani sono raddoppiate in 13 anni. Senza i cani non si può dire se le aree sono molte o poche.

## 6. Trappole

1. **`data_ini` non è la data di apertura**: 47 righe hanno data convenzionale (1/1/1983, 1/7/2009), 77 sono del 2003. La serie "aree per anno" misura quando sono state schedate; le aree chiuse non compaiono (il file è l'elenco attuale). Presentarla come "aree oggi in elenco con scheda fino all'anno X".
2. **Conteggi diversi per le stesse aree**: 403 (Legambiente 2020), 383 (ds52 con scheda fino al 2020), 423 (ds52 2024). Una riga di ds52 è un'area (poligono), non un parco: 297 parchi o giardini ne contengono 423.
3. **"Animali registrati" non è "cani"**: il 118.292 del 2020 sta nell'articolo accanto ai cani, ma il testo dice "animali"; i gatti registrati nel Comune sono 43.327. Il 104.067 del 2018 è scritto "cani".
4. **Anagrafe non è cani reali**: Legambiente stessa dice che solo il 41% dei Comuni sa quanti cani ha in anagrafe (316 su 771, XV rapporto); gli iscritti includono cani morti non cancellati e non includono quelli non iscritti. Il totale nazionale in anagrafe (14,9 milioni nel 2025) supera di molto le stime sulla popolazione canina reale (circa 10 milioni, Focus).
5. **Iscrizione non è residenza del cane**: l'anagrafe segue il proprietario; un cane iscritto a Milano può vivere altrove e viceversa.
6. **ds205 e superfici**: per 3 NIL le superfici di ds205 sono scambiate (`alberi/NOTE.md` punto 6.5); qui uso `area_km2` di `alberi/pulito/nil_alberi.csv` (da poligono). Gli abitanti (`Totale`) non sono toccati. ds205 è registro anagrafico, 3,4% sopra il censimento nel 2023: per i municipi uso il censimento (ds205 non ha il municipio), per i NIL ds205; i due insiemi non sono confrontabili tra loro.
7. **ds205 ha una riga "N.D."** senza NIL ogni anno: esclusa (2011-2016 vale 0; dal 2019 è vuota).
8. **Overpass è instabile** (502 al primo tentativo): ripetere con pausa.
9. **Patentino**: nessun dato aperto sui cani con "patentino speciale" (27 razze e incroci, obbligatorio dal febbraio 2020 per regolamento comunale); è un elenco di razze per regola, non un censimento.

## 7. Cosa potrebbe mostrare una pagina (da decidere)

- **Mappa delle 423 aree cani** con filtro per municipio e NIL, dimensione, anno di scheda; accanto "aree cani per 100.000 abitanti" per quartiere (da 5 a 79: i quartieri centrali in fondo).
- **La crescita delle aree**: 200 -> 422 (2011-2024) contro residenti +5%, con l'avvertenza sulla data di scheda.
- **Cani a Milano: i due totali di stampa** (104 mila nel 2018, 118 mila nel 2020), il confronto con la Lombardia (1 ogni 11 contro 1 ogni 5,6), con l'avvertenza chiara che non sono dati aperti.
- **Il "non sappiamo"**: un riquadro che spiega perché mancano razze e quartieri (anagrafe regionale chiusa) e che cosa si potrebbe chiedere ad ATS Milano (cani per CAP, razza, anno).
- Estensioni da decidere: richiesta di accesso civico ad ATS Milano (la decide e la invia Davide, io non la invio); confronto con altri comuni lombardi che pubblicano le aree cani; gatti (colonie feline del Comune, nessun file aperto).

## 8. Cosa non ho fatto

Nessuna pagina, nessun grafico. Nessuna richiesta di accesso agli atti. Nessun account, nessun bypass. Non ho scaricato altre edizioni del rapporto Legambiente (nelle pagine delle edizioni XIII e XV e nel PDF XV non ho trovato dati per Milano; X solo via articoli). Nessuna verifica dei totali di stampa a una fonte primaria.
