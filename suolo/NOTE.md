# Quanto suolo si consuma - FASE 1 (raccolta, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web, nessun giudizio. Ogni numero dice file e campo. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di suolo> [altri percorsi assoluti]` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`.

## 1. In breve

1. **Fonte unica e ufficiale: ISPRA / SNPA, rapporto "Consumo di suolo, ecosistemi urbani e stato del territorio. Edizione 2026" (SNPA 50/2026, pubblicato in ottobre 2026), dati del 27/10/2026.** Serie annuale comune per comune completa: 2006, 2012, 2015, 2016 ... 2025 (13 fotografie; fra il 2006 e il 2012 e fra il 2012 e il 2015 non ci sono anni intermedi). Anche le carte raster a 10 m si scaricano senza registrazione.
2. **Milano 2025: 10.678,98 ettari di suolo consumato su 18.157,72 = 58,81%** (`csuolo1`, `csuolo4`, foglio `Comuni_2025`). Terza fra i 44 comuni sopra i 100.000 abitanti, dopo Torino (65,3%) e Napoli (63,8%); 45a su 7.896 comuni italiani; l'Italia è al 7,19%.
3. **Cresce poco**: 10.364,99 ettari nel 2006, +314 ettari in 19 anni (+3,0%). Media netta 18,9 ettari/anno nel 2006-2012, 15,4 ettari/anno nel 2012-2025. Ultimo anno (2024-2025): +35,07 lordi, -7,00 ripristinati, **+28,07 netti**.
4. **Per abitante Milano è tra le più "compatte"**: 78,2 m2 di suolo consumato per residente (82,1 nel 2006), contro Roma 110,9, Bologna 123,6, Firenze 119,0, Genova 103,0, Torino 99,5; solo Napoli è vicina (83,2). Popolazione +8,2% dal 2006, suolo consumato +3,0%.
5. **Città metropolitana (133 comuni): 50.481 ettari consumati, 32,07%**; senza Milano 28,6% e 212 m2 per abitante. Dal 2012 al 2025 la città metropolitana ha aggiunto 1.633 ettari netti (dato ISPRA): **Milano ne fa 203 (12%)**, gli altri 132 comuni 1.430.
6. **Raster ritagliati su Milano**: il nuovo consumo 2012-2025 (terreno libero diventato consumato) è 244 ettari lordi nei NIL (250 con i confini ISTAT del comune), 44 ettari sono tornati liberi: **netto 200,5 ettari, identico alla cifra ISPRA** (10.678,98 - 10.478,46). Il totale di ogni carta ritagliata su Milano coincide con il dato ISPRA entro lo 0,04% (vedi 6).
7. **Il dato più sorprendente** (dettaglio al punto 5): le grandi trasformazioni degli ultimi quindici anni (Porta Nuova, CityLife, Portello, Scalo Romana, Farini) **non compaiono quasi per nulla nel "nuovo consumo"** perché erano già classificate come suolo consumato (ex scali, ex Fiera, cantieri): nei NIL Porta Garibaldi-Porta Nuova e Tre Torri il suolo consumato è addirittura **diminuito** di 4,3 e 4,5 ettari (parchi). Entro 3 km dal Duomo il saldo è -8,4 ettari. Il suolo "nuovo" è stato consumato quasi tutto fra 4 e 9 km dal Duomo (84%) e per un terzo (36%) è terra battuta di cantiere, non edifici.

## 2. Fonti, una per una (anche in `pulito/inventario_fonti.csv`, con byte e sha256)

| Fonte | Cosa | Dove | Licenza scritta dalla fonte | Dimensione |
|---|---|---|---|---|
| Indicatori comuni/province/regioni/Italia | 109 campi, fogli `Comuni_2006` ... `Comuni_2025` (anche `2023rev`, `2024rev`) | groupware.sinanet.isprambiente.it/uso-copertura-e-consumo-di-suolo/library/consumo-di-suolo/indicatori (file `consumo_suolo_2026_Com_Prov_Reg_Naz_v1.0.xlsx`) | foglio Info: "Creative Commons Attribution 4.0 - https://creativecommons.org/licenses/by/4.0/" | 82 MB |
| "Dati principali" SNPA | incrementi netto, lordo, ripristino per periodo (12 periodi), suolo consumato 2025, 7.896 comuni | snpambiente.it, pagina dell'edizione 2026 | foglio Descrizione_campi: "Creative Commons Atttribution 4.0 - https://creativecommons.org/licenses/by/4.0/" | 1,7 MB |
| Edizione 2025 (2006-2024) | per misurare quanto cambiano i numeri da un'edizione all'altra | snpambiente.it, edizione 2025 | non scritta nel foglio | 1,7 MB |
| Carte nazionali del consumo di suolo | 10 m, EPSG:7794 (RDN2008 Italia), 2006, 2012, 2015, 2018 (v6), 2024, 2025 (v8); cambiamenti 2024-2025 | library/consumo-di-suolo/carta-nazionale-consumo-suolo-AAAA | `licenza.txt`: "Licenza Attribuzione 3.0 Italia (CC BY 4.0 IT)" con link creativecommons.org/licenses/by/4.0/it/legalcode. **L'etichetta è incoerente (3.0 o 4.0?); il link punta alla 4.0.** I file 2006-2018 dichiarano nel testo "v.5.0" mentre i nomi dicono v6 | 255-268 MB l'una |
| Logistica in Italia | centroidi (8.309 + 327 punti) delle aree di cambiamento 2006-2023, classi 1 grande distribuzione/commerciale, 2 produttivo/industriale, 3 e-commerce; EPSG:3035 | library/consumo-di-suolo/logistica/centroidi | `Licenza.txt`: stessa formula "Licenza Attribuzione 3.0 Italia (CC BY 4.0 IT)". Chiede di citare: "SNPA, Consumo di suolo, dinamiche territoriali e servizi ecosistemici. Edizione 2024, Report ambientali SNPA, 43/2024" | 190 KB |
| Potenziale di recupero 2026 | spazi verdi, copertura arborea, tetti per fotovoltaico potenziali per comune | snpambiente.it, edizione 2026 | non scritta nel file | 0,8 MB |

**Citazione richiesta dall'edizione 2026** (foglio Info): Munafò M. (a cura di), 2026, *Consumo di suolo, ecosistemi urbani e stato del territorio. Edizione 2026*, Report ambientali SNPA, 50/2026. Per una pagina: citare così, dire che i dati sono ISPRA/SNPA, licenza CC BY 4.0, e dire cosa è stato calcolato da noi (NIL, anelli, confronto fra carte).

**Accesso**: nessuna registrazione, nessun login, nessuna protezione anti-bot. Il server del repository ISPRA ha risposto con errori 500 per alcuni minuti dopo una raffica di richieste mie (non l'ho aggirato: ho aspettato e riprovato più lentamente). Il sito consumosuolo.it è una web app (JavaScript) senza file da scaricare: non l'ho usato.

**Cosa NON ho preso**: le carte 2016, 2017, 2019-2023 (si scaricano allo stesso modo; per i NIL bastano le sei che ho), le carte LAEA (stesse ma in altra proiezione), le carte di frammentazione e permeabilità, il file `stato_del_territorio_2026` (CORINE ecc.; scaricato, non usato), i poligoni della logistica (la pagina `logistica/poligoni` rispondeva 500; esistono solo "Centroidi" scaricati).

## 3. Pulizia (`scripts/estrai_indicatori.py` e gli altri)

- `pulito/comuni_lungo.csv`: tutti i 7.896 comuni x 15 fogli (118.440 righe) con 35 campi chiave (suolo consumato ha e %, incrementi, per abitante e popolazione, superficie, densità, isola di calore, verde...). `pulito/milano_area_completo.csv`: tutti i 109 campi per Milano, le sei città di confronto e i 133 comuni della Città metropolitana. `campi.csv` = dizionario ufficiale dei campi. `province_lungo.csv`, `regioni_lungo.csv`, `nazionale_lungo.csv`.
- **Quale foglio uso per ogni anno**: i fogli originali, tranne 2023 e 2024 dove uso `Comuni_2023rev` e `Comuni_2024rev` (valori rivisti da ISPRA con la v8 delle carte; i fogli `rev` non hanno gli incrementi). Per Milano il cambio è piccolo ma visibile: 2023 10.661,23 -> 10.669,90 (rev); 2024 10.662,09 -> 10.650,91 (rev).
- **Popolazione** (`clammi4`): è la popolazione ISTAT "da rilevamento intercensuario"; ha un salto al 2021 (Milano 1.406.242 nel 2020 -> 1.374.582 nel 2021) dovuto al censimento permanente. I m2 per abitante nel 2021 risentono del salto.
- **Confini**: i comuni sono quelli ISTAT di ISPRA (`clammi3`, superficie in ettari: Milano 18.157,72). Per ritagliare le carte su Milano uso i 88 NIL vigenti (`citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson`): la loro unione fa 18.157,68 ettari, praticamente uguale. Per i 133 comuni della Città metropolitana uso i confini delle sezioni di censimento ISTAT 2021 (filone censimenti, `R03_21_WGS84.shp`) unite per comune (EPSG:32632, convertiti in 7794). Vermezzo con Zelo (15251) c'è.
- **Classi delle carte** (legenda `Legenda_QGIS_2025_v8.qml`): consumato = 1, 11, 12 e 111-126; non consumato = 2 e 201-206; 255 = nessun dato (1 pixel a Milano). Classe 1 è "Consumo di suolo" generico (2.275 ettari a Milano nel 2025): la legenda non dice cosa contenga, la tratto come consumato. **Classe 122 = "cantieri e altre aree in terra battuta (piazzali, parcheggi, cortili, campi sportivi, depositi permanenti di materiale)": conta come consumato.**
- Ogni pixel vale 10 m x 10 m = 100 m2 = 0,01 ettari.

## 4. I numeri (tutti riproducibili con gli script)

### 4.1 Milano nel tempo (`pulito/serie_milano.csv`, `incrementi_milano_periodi.csv`)

| Anno | Suolo consumato ha | % | Popolazione | m2/abitante |
|---|---|---|---|---|
| 2006 | 10.364,99 | 57,08 | 1.262.198 | 82,1 |
| 2012 | 10.478,46 | 57,71 | 1.279.948 | 81,9 |
| 2015 | 10.540,36 | 58,05 | 1.339.812 | 78,7 |
| 2018 | 10.588,15 | 58,31 | 1.380.995 | 76,7 |
| 2021 | 10.624,87 | 58,51 | 1.374.582 | 77,3 |
| 2023 (rev) | 10.669,90 | 58,76 | 1.358.420 | 78,5 |
| 2024 (rev) | 10.650,91 | 58,66 | 1.371.499 | 77,7 |
| 2025 | 10.678,98 | 58,81 | 1.365.698 | 78,2 |

Incrementi pubblicati (netto = lordo - ripristino, ettari): 2006-12 113,47 (18,9/anno); 2012-15 61,90 (20,6/anno); 2015-16 2,05; 2016-17 20,74; 2017-18 25,00; 2018-19 -1,39; 2019-20 10,86; 2020-21 27,25; 2021-22 21,61; 2022-23 14,75; 2023-24 -7,81 (lordo 13,11, ripristino 20,92); 2024-25 +28,07 (lordo 35,07, ripristino 7,00). Totale 2012-2025: netto 203,03, lordo 275,66, ripristino 72,63. **Confermato dal rapporto SNPA 2026 (testo, Tabella 30): "Milano (+35 ettari)" nell'ultimo anno.** Il rapporto (Tabella 32) dà Milano al 59,28% perché divide per la superficie "al netto dei corpi idrici permanenti"; il campo `diseco11` del file dà 59,03%.

### 4.2 Milano e le altre grandi città (`pulito/confronto_citta_2025.csv`, `serie_citta.csv`)

| Città | % consumato 2025 | ettari | m2/ab 2006 -> 2025 | consumato 2006-2025 | popolazione 2006-2025 | netto 2012-2025 (ettari, pubblicato) | ultimo anno (netto) |
|---|---|---|---|---|---|---|---|
| Milano | 58,8 | 10.679 | 82 -> 78 | +3,0% | +8,2% | 203 | 28 |
| Torino | 65,3 | 8.488 | 95 -> 100 | +1,6% | -2,5% | 102 | 7 |
| Napoli | 63,8 | 7.565 | 76 -> 83 | +2,4% | -7,1% | 112 | 14 |
| Bologna | 34,3 | 4.823 | 127 -> 124 | +3,6% | +6,2% | 125 | 2 |
| Firenze | 42,2 | 4.303 | 119 -> 119 | +1,7% | +1,5% | 64 | 15 |
| Genova | 24,2 | 5.810 | 95 -> 103 | +1,3% | -6,9% | 53 | 6 |
| Roma | 23,7 | 30.463 | 112 -> 111 | +5,7% | +7,1% | 1.067 | 74 |

Classifica dei 44 comuni con almeno 100.000 abitanti per % consumata (`grandi_comuni_2025.csv`): Torino, Napoli, **Milano**, Pescara 51,7, Padova 49,9, Monza 49,6, Bergamo 45,7, Brescia 44,2, Bari 43,7, Firenze 42,2.

### 4.3 Città metropolitana (`metro_comuni.csv`, `metro_top_recenti.csv`, `riepilogo_indicatori.json`)

- 133 comuni (cod_prov 15), 157.401 ettari, 3.246.455 residenti, 50.481 ettari consumati (32,07%). Milano è **13a** della città metropolitana per % consumata: più alti Sesto San Giovanni 69,2, Cusano Milanino 66,0, Corsico 65,8, Pero 64,8, Baranzate 63,7, Cologno Monzese 63,0, San Giorgio su Legnano 62,9, Paderno Dugnano 62,2.
- **Dove si è consumato di più dal 2012** (lordo pubblicato 2012-2025, ettari): Milano 275,7; Pozzuolo Martesana 67,9; Segrate 63,3; Gessate 45,0; Pioltello 43,2; Bollate 42,5; Cassano d'Adda 41,0; Lainate 39,6; Paullo 39,3; Nerviano 37,3; Vizzolo Predabissi 36,1; Senago 31,2.
- **Ultimi sette anni (netto 2018-2025, ettari)**: Segrate 27,5; Bollate 21,7; Pioltello 21,6; Senago 20,1; Lainate 19,3; Noviglio 18,1; Magenta 17,0; Settala 16,4; Paullo 15,1.
- **Cosa c'è dentro questo "nuovo consumo" dei comuni intorno a Milano** (da carta 2025, `metro_nuovo_per_classe.csv`, 1.522 ettari fuori Milano): cantieri e terra battuta 29%, edifici 22%, strade pavimentate 16%, altre aree pavimentate 12%, classe 1 generica 11%, **cave 7,9% (123+124)**, fotovoltaico a terra 0,8%. Le tre macchie più grandi di nuovo consumo dell'intera area (esclusa la distinzione dei comuni) sono cave: cava in falda a Pozzuolo Martesana (20,7 ettari), area estrattiva a Vizzolo Predabissi (17,3), cava in falda a Cassano d'Adda (16,8) (`metro_patch_grandi_2012_2025.csv`).
- **Logistica** (livello ISPRA, `logistica_metro_*.csv`): nel territorio della città metropolitana le aree classificate "logistica" sono 250 ettari dal 2006 al 2023 (su 6.478 in tutta Italia); **dal 2012 sono 151 ettari: circa l'8% del nuovo consumo 2012-2025 dell'area (1.771 ettari lordi dalla carta, 1.934 dal file ISPRA)**. Per comune (tutto il periodo): Pozzuolo Martesana 30,0 ettari, Milano 24,1, Vignate 24,1, Pioltello 20,7, Peschiera Borromeo 20,0, Segrate 15,9, Truccazzano 14,9, Settala 9,3, Basiano 8,9, Mesero 8,7. Dal 2018: Milano 11,9, Pioltello 8,8, Mesero 8,7, Segrate 6,8, Settala 4,3, Basiano 4,3. Il livello contiene solo le aree che ISPRA ha classificato come logistica (centroidi di aree di cambiamento): può sottostimare; ma **l'ipotesi "è tutta colpa dei magazzini" non è sostenuta da questo dato**.

### 4.4 Dentro Milano, per NIL (carte raster; `nil_suolo.csv`, `nil_suolo_serie.csv`, `nil_suolo_classi_2025.csv`)

- **Nuovo consumo 2012-2025 (terreno libero -> consumato, ettari)**: Cascina Merlata 30,7 (è la zona dell'ex Expo/MIND-Cascina Merlata, 84% consumata nel 2025: **30,5 ettari fra il 2012 e il 2015, poi quasi zero**); Maggiore-Musocco-Certosa 25,1; Lorenteggio 23,0; Stadio-Ippodromi 20,0; Adriano 12,6; Parco dei Navigli 12,6; Bovisa 10,2; Rogoredo-Santa Giulia 8,5 (4,4 tornati liberi, netto 4,1); Parco delle Abbazie 7,6; Ronchetto sul Naviglio 7,6; Parco Forlanini-Cavriano 7,1; Taliedo-Morsenchio 7,0; Lambrate-Ortica 6,8. **Questi primi 8 NIL fanno il 58,5% del nuovo consumo di Milano.** 43 NIL su 88 hanno più di 0,5 ettari di nuovo consumo, 28 meno di 0,1.
- **Nell'ultimo anno (2024-2025, carta dei cambiamenti)**: nuovo consumo 35,1 ettari, ripristino 6,9 (come l'ISPRA: 35,07 e 7,00). Adriano 8,0; Lorenteggio 5,9; Stadio-Ippodromi 4,5; Taliedo-Morsenchio-Forlanini 4,0; Bovisa 2,1.
- **Tempi per NIL** (variazioni nette dello stock, `nil_suolo_serie.csv`; carte 2006/2012/2015/2018 v6 e 2024/2025 v8): Maggiore-Musocco-Certosa +17,5 ettari nel 2012-2015, poi +5,4 nel 2018-24; Lorenteggio +12,4 nel 2015-2018; Stadio-Ippodromi +13,9 nel 2018-2024; Bovisa +7,4 nel 2018-24; Parco dei Navigli +14,9 nel 2015-2018 (poi -4,8); Adriano +13,2 nel 2006-12.
- **Per distanza dal Duomo** (`anelli_duomo.csv`): 0-3 km: nuovo 2,6, ripristino 11,0 ettari (saldo -8,4; già consumato al 85-93%); 3-4 km +12,8/-10,0; 4-5 km +39,3/-8,4; 5-6 km +62,5/-5,9; 6-7 km +43,0/-5,2; 7-8 km +21,8; 8-9 km +39,3; 9-10 km +21,9; oltre 10 km +1,0. **Fra 4 e 9 km passa l'84% del nuovo consumo** (206 su 244 ettari). Oltre i 10 km (la parte nord-ovest e sud del comune) resta poco da consumare.
- **Da che cosa si arriva** (`transizioni_classi_2012_2025.csv`, nuovo consumo 2012-2025): 89,3 ettari sono diventati cantiere/terra battuta (122), 53,7 edifici, 38,7 piazzali e parcheggi pavimentati, 38,0 classe 1 generica, 18,5 strade, 5,1 ferrovia. In senso inverso 32,6 ettari di "cantiere" 2012 sono tornati terreno libero e 51,9 sono diventati edifici/strade/piazzali: **i cantieri di Milano sono ancora in gran parte cantieri (92,9 ettari su 177 restano tali)**; lo stock di classe 122 è 177 ettari nel 2012 e 201 nel 2025.
- **Zone delle grandi trasformazioni** (NIL, nuovo / tornati liberi, ettari): Scalo Romana 0,8/0,6; Farini 0,9/1,3; Portello 0,0/0,0; Porta Genova 0,0/0,1; Isola 0,0/1,7; **Tre Torri (CityLife) 0,0/4,5; Porta Garibaldi-Porta Nuova 0,0/4,3**. Sono già "consumate" nel 2012 (ex scali, ex Fiera): i parchi nuovi le fanno scendere.
- **Confronto col filone costruzioni** (solo confronto, `confronto_costruzioni_nil.csv`): fra il nuovo consumo di suolo per NIL e il volume dei nuovi edifici (DBT 2012-2020) la correlazione di rango è 0,47; con le nuove abitazioni 2014-2024 0,21 (debole). I primi 8 NIL per nuovo suolo hanno il 58,5% del nuovo suolo ma solo il 24% del volume nuovo e il 23% delle abitazioni nuove: **la maggior parte di ciò che si costruisce a Milano si costruisce su suolo già consumato** (demolizione e ricostruzione, cantieri, ex aree industriali). Cascina Merlata ha 819.000 m3 di edifici nuovi (DBT) ma 0 abitazioni nel registro titoli 2014-2024.

### 4.5 Altro che l'ISPRA dà per Milano 2025 (`milano_area_completo.csv`, foglio `Comuni_2025`)

Isola di calore urbana (`iscalo1`) 7,1 gradi C (differenza media estiva diurna 2020-2025 della temperatura al suolo fra aree urbane e rurali, con la densità di superfici artificiali nel raggio di 300 m); densità 75,2 abitanti per ettaro; vegetazione 7.108 ettari (`cover10`), area urbana e suburbana 16.544 (`cover11`), verde su urbanizzato 33,9% (`cover12`), incidenza aree verdi 39,1% (`cover13`). Dal file `potenziale_recupero_2026.xlsx`: spazi verdi potenziali 1.675,6 ettari (795,5 prevalentemente pubblici, 685,8 privati, 194,2 altre aree interne al perimetro urbano), copertura arborea potenziale 3.194,5 ettari, tetti per fotovoltaico 731-955 ettari. Sono stime ISPRA, non le ho controllate.

## 5. La cosa più sorprendente (due versioni, la prima è la mia scelta)

1. **"Milano costruisce su ciò che è già consumato."** La carta registra come consumo il passaggio terreno libero -> artificiale, ma gli scali ferroviari, l'ex Fiera, i cantieri e le aree industriali dismesse sono già artificiali. Quindi le trasformazioni più famose (Porta Nuova, CityLife, Portello, Scalo Romana, Farini) hanno **zero** nuovo consumo, e dove sono nati i parchi (Tre Torri, Porta Nuova) il suolo consumato scende di 4 ettari. Il suolo "nuovo" è altrove: Cascina Merlata/ex Expo (30,5 ettari in tre anni, 2012-2015, 12% del totale), poi le fasce esterne fra 4 e 9 km dal Duomo; e un terzo è terra battuta di cantieri (122), non edifici.
2. In alternativa, per la metropoli: **le cave e i cantieri pesano più dei magazzini**. Le tre macchie più grandi di nuovo consumo nei comuni intorno a Milano sono cave (Pozzuolo Martesana, Vizzolo Predabissi, Cassano d'Adda); la logistica classificata da ISPRA è l'8% del nuovo consumo dal 2012.

## 6. Controlli fatti

- **Carte vs ISPRA**: il totale ritagliato sui NIL coincide con il dato ISPRA in tutti i sei anni, con scarto costante -4,4 / -4,7 ettari (-0,04%): 2006 10.360,58 vs 10.364,99; 2012 10.473,92 vs 10.478,46; 2015 10.535,79 vs 10.540,36; 2018 10.583,56 vs 10.588,15; 2024 10.646,18 vs 10.650,91 (rev); 2025 10.674,42 vs 10.678,98 (`controllo_raster_vs_ispra_milano.csv`). Netto 2012-2025 raster = 200,5 ettari = ISPRA (da stock).
- **Rapporto SNPA 2026 (pdf in `raw/snpa/`, letto per testo)**: conferma Milano 10.679 ettari, +35 ettari nell'ultimo anno, 59,28% netto acque.
- **Città metropolitana, carta vs file**: lordo 2012-2025 dalle carte 1.771 ettari, dal file ISPRA 1.934 (-8%); i comuni con scarti grandi sono Gessate (28 vs 45) e Pessano con Bornago (18 vs 27); Nerviano ha 22 ettari di ripristino pubblicati (lordo 37,3, netto 14,8). Per il netto Milano combacia (206 vs 203). Per la classifica dei comuni è meglio il dato ISPRA; le carte servono per dire *dove* e *di che tipo*.
- Milano, confini diversi: 244,2 ettari di nuovo consumo con i NIL, 249,9 con i confini ISTAT del comune (differenza di bordo: 6 ettari).

## 7. Limiti dei dati

1. **"Suolo consumato" non vuol dire "costruito".** È la superficie artificiale (edifici, strade, piazzali, ferrovie, cantieri, cave, ecc.). Il 58,8% di Milano non è 58,8% di cemento: i giardini e i parchi dentro la città non sono consumati, ma strade e parcheggi sì. I **cantieri e la terra battuta (classe 122, 201 ettari nel 2025) contano come consumato** e sono la prima voce del "nuovo" consumo.
2. **I numeri si rivedono a ogni edizione.** Milano 2012-2015: +66,91 ettari nell'edizione 2025, +61,90 nella 2026; stock 2024: 10.667,5 (ed. 2025), 10.662,09 (ed. 2026 originale), 10.650,91 (ed. 2026 rivista). Nel foglio 2023 e 2024 ci sono due versioni (originale e `rev`). Gli incrementi pubblicati (che sommano periodi calcolati su versioni diverse) non coincidono con le differenze fra gli stock: 2012-2025 203,03 vs 200,52; 2018-2025 93,3 vs 90,8. Per l'Italia la revisione 2024 è -2.600 ettari. **Citare sempre l'edizione.**
3. **Carte di versioni diverse.** 2006-2018 sono v6, 2024-2025 v8: i confronti 2018-2024 fra le due versioni possono contenere piccole differenze di interpretazione; ho verificato che i totali combaciano con ISPRA.
4. **Sei punti nel tempo, non venti**: 2006, 2012, 2015, poi annuale. Il "per anno" del periodo 2006-2012 è una media.
5. **"Ripristino" non vuol dire parco**: l'ISPRA lo definisce "ripristino di superfici precedentemente consumate". Il -7,81 del 2023-2024 viene da 20,92 ettari di ripristino contro 13,11 di nuovo consumo. A Milano, 2012-2025, 32,6 ettari di classe 122 (cantiere/terra battuta) sono tornati terreno libero: possono essere cantieri chiusi, non per forza verde.
6. **Popolazione**: residenti ISTAT, con il salto del censimento 2021; non conta i pendolari né gli utenti della città, quindi i m2 per abitante vanno letti come "per residente".
7. **Risoluzione 10 m**: elementi piccoli (alberate, giardini interni, singoli edifici piccoli) si perdono nella classificazione.
8. **Quale classe sia "1"** non è spiegato nella legenda che ho (2.275 ettari a Milano, il 21% del consumato).
9. **Logistica**: solo centroidi di aree di cambiamento classificate da ISPRA (le aree nuove, non i magazzini già esistenti nel 2006); i poligoni non si sono potuti scaricare; i punti sono attribuiti ai comuni da me (punto in poligono con i confini ISTAT 2021); la classificazione per tipologia (GDO, produttivo, e-commerce) è dell'ISPRA e non l'ho controllata.
10. **Coordinate di riferimento (MIND, Santa Giulia, scali ecc.)** nel file `patch_nuovo_consumo_2012_2025.csv` (colonna `riferimento_vicino_indicativo`) sono punti che ho messo io a memoria con 500 m di tolleranza: non sono una fonte. Usare solo il NIL.
11. **I NIL** sono i 88 vigenti del PGT 2030; i poligoni NIL e i confini ISTAT non coincidono al bordo (6 ettari su 244).

## 8. Cosa può mostrare una pagina (idee, non fatte)

- Una linea del suolo consumato 2006-2025 per Milano accanto alla popolazione: la popolazione cresce 8%, il suolo 3%; con le città di confronto (m2 per abitante: Milano più compatta di Roma, Bologna, Firenze).
- La classifica: Milano è la terza grande città italiana per suolo consumato (58,8%). Crescita relativa 2012-2025 (da stock): Roma +3,5%, Bologna +2,8%, Milano +1,9%, Napoli +1,6%, Firenze +1,4%, Torino +1,2%, Genova +0,9%.
- Una mappa a pixel (10 m) del nuovo consumo 2012-2025 per NIL con i colori dei tre periodi (Expo 2012-15; periferia nord-ovest 2015-2018; Stadio-Ippodromi 2018-24), più gli anelli dal Duomo.
- "Dove il suolo è tornato libero": Tre Torri, Porta Nuova, Isola, Rogoredo (parchi su ex scali), con le 43,7 ettari di ripristino 2012-2025.
- La città metropolitana in una tabella ordinabile: percentuale e metri quadrati per abitante dei 133 comuni, con cave, cantieri e logistica separati.
- Un quadro "dove potrebbe tornare il verde" con il potenziale di recupero ISPRA (1.676 ettari di spazi verdi potenziali).
