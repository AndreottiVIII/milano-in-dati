# Dove si costruisce - FASE 1 (fonti, scaricamento, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Nessuna pagina web, nessun giudizio. Ogni numero dice file e campo. Programmi in `scripts/` (comandi in `STATO.md`), dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`. Nessun account creato, nessun login, nessun anti-bot aggirato.

## 1. In breve

1. **Il portale del Comune ha solo 5 dataset sull'edilizia privata, tutti sui "nuovi fabbricati" e sugli "ampliamenti" (modello ISTAT dei permessi di costruire, un record per fabbricato, con indirizzo e NIL), anni 2014-2024.** Non esiste nessun dataset aperto su SCIA, CILA, ristrutturazioni, demolizioni o cantieri: ho scorso tutto il catalogo (2.611 dataset) e le 20 parole chiave. **Quindi "nuovo contro ristrutturazione" non si può misurare**: le ristrutturazioni senza aumento di volume non sono nei dati.
2. **ISTAT non dà il comune di Milano**: i permessi di costruire sono pubblicati al massimo per provincia (la nota dell'ISTAT lo dice: "analisi territoriale fino al livello provinciale"). Per Milano ci sono la Città metropolitana (ITC45) e la classe "capoluoghi sopra 500.000 abitanti" (6 città). Per il solo comune vale la serie del Comune (che deriva dallo stesso modello ISTAT).
3. **Il Comune pubblica due versioni del Database Topografico (DBT 2012 e 2020), scaricabili senza login**: servono per vedere dall'alto dove sono comparsi e spariti edifici. Il "2012" in realtà è per il 96% una restituzione del 2006 (campo `ID_ZRIL`): è un confronto 2006-2020.
4. Il geoportale `geoportale.comune.milano.it` **non esiste più come indirizzo** (il nome non si risolve: provato con due DNS). I file stanno su `gisportal.comune.milano.it` (area download).
5. **Numeri chiave** (serie 2014-2024, sezione 4): 725 nuovi fabbricati residenziali e 210 non residenziali, 26.174 abitazioni in nuovi fabbricati contro +56.364 residenti (ds205); il 2022 è l'anno più alto (127 nuovi fabbricati, 3.917 abitazioni), il 2024 il più basso (33 e 1.059).
6. **La cosa più sorprendente** (sezione 6): dal 2022 (anno in cui il campo "abbattimento e ricostruzione" è sempre compilato) **1 nuovo edificio residenziale su 2 (92 su 185) sostituisce un edificio demolito**, e due su tre di queste ricostruzioni (61 su 92) passano con la SCIA alternativa.

## 2. Fonti, una per una (anche in `pulito/inventario.csv`, con sha256)

Licenza dei dataset del Comune: nel catalogo CKAN `license_id = cc-by` ("Creative Commons Attribution"); la versione non è scritta. Si possono ripubblicare citando "Comune di Milano - dati.comune.milano.it".

### 2.1 Cinque dataset "Edilizia" del Comune (CKAN, CSV, separatore `;`, UTF-8 con testo a volte salvato due volte: "SocietÃ " -> "Società", sistemato in pulizia)
| ID | Cosa | Righe | Anni (campo `Anno Ritiro`) | Senza coordinate |
|---|---|---|---|---|
| ds270 | nuovi fabbricati residenziali | 728 | 2014-2024 (+3 record 2011-2012) | 66 |
| ds2984 | nuovi fabbricati non residenziali | 214 | 2014-2024 (+4 record 2010-2012) | 28 |
| ds271 | ampliamenti residenziali (solo la parte ampliata) | 204 | 2014-2024 | 6 |
| ds2985 | ampliamenti non residenziali | 150 | 2012, 2014-2024 | 2 |
| ds2983 | fabbricati per collettività (nuovi e ampliamenti) | 19 | 2014-2023 | 2 |

- Definizione del Comune (campo `notes`): fabbricati "per i quali è stato presentato un permesso di costruire, una SCIA, una SCIA alternativa, o che rientrano in interventi di edilizia pubblica (DPR 380/2001, art. 7)"; residenziale = più del 50% della superficie è abitativa; **i nuovi fabbricati comprendono quelli ricostruiti dopo completa demolizione**.
- Campi utili: titolo (Permesso di costruire / SCIA / SCIA alternativa), mese e anno di "ritiro", indirizzo, civico, municipio, NIL, numero di abitazioni, stanze, piani, volume (V/p, m³), superficie, abbattimento e ricostruzione (sì/no), categoria del titolare (Impresa/Società, Persona fisica, Cooperativa, Ente pubblico, Altro), piano casa, impianti. **Non ci sono nomi di persone** né nomi di progetto; il campo "Specifica altro titolare" può contenere nomi e **non è stato copiato** nelle tabelle pulite.
- Aggiornamento dichiarato: annuale / semestrale; `metadata_modified` tra l'1 e l'8/9/2026; copertura dichiarata 2014-2024.
- Cosa manca: il numero del titolo, il nome del progetto, la data di fine lavori, le ristrutturazioni e le demolizioni senza ricostruzione, il 2025. "Anno Ritiro" = anno di ritiro del titolo (è il campo che ho usato come anno; il significato esatto non è spiegato).
- Scaricati con `scripts/download_comune.py` (log `raw/download_log.csv`: URL, byte, sha256).

### 2.2 Database Topografico (DBT) 2012 e 2020 (Comune, CKAN ds2892 e ds2889; file su `gisportal.comune.milano.it/download/area_download/SIT/...`)
- DBT 2020: volo marzo-aprile 2020, scala 1:1.000, RDN2008 UTM 32N, 596.533.009 byte; DBT 2012: 590.476.659 byte. Scaricati l'1/11/2026 con una sola richiesta ciascuno, senza login; `robots.txt` del gisportal non vieta `area_download`. Licenza CC-BY (CKAN).
- Strato usato: unità volumetriche (2020 `UN_VOL`: 237.743 oggetti di cui 214.233 fuori terra; 2012 `A020101`: 213.076 di cui 206.783 fuori terra) con altezza (`UN_VOL_AV`, m). Gli altri strati (strade, verde, ecc.) non sono stati usati.
- **Limite grosso**: nel DBT 2012 il campo `ID_ZRIL` vale `MI_2006` per 203.745 unità su 213.076 e `MI_2012` solo per 9.331. Il confronto vero è 2006-2020 (14 anni), non 2012-2020.
- Manca: anno di costruzione, uso, numero di abitazioni.

### 2.3 ISTAT (IstatData / esploradati, SDMX)
- Dataflow `11_111_DF_DCSC_RESID_CONSTR_1` (fabbricati residenziali nuovi e abitazioni) e `22_222_DF_DCSC_NONRESID_CONSTR_1` (non residenziali): annuale 2010-2025. Territorio disponibile: Italia, ripartizioni, regioni, province, classi di comune; per Milano `ITC45` (Città metropolitana), `INH_GE500001_CAP` (capoluoghi oltre 500.000 ab.) e altri raggruppamenti che non ho decodificato (`PROVCAPM`, `NPROVCAPM`). File: `raw/istat/resid_constr_1_milano.csv`, `nonresid_constr_1_milano.csv`.
- Licenza: ISTAT dichiara CC BY 4.0 per IstatData; la pagina delle tavole dei permessi 2025 non riporta licenza e io non l'ho ricontrollata nel file SDMX.
- Scaricati con 3 richieste di vincoli (availableconstraint) e 2 di dati, pausa 20-25 s (limite ISTAT: 5 richieste al minuto). Un tentativo di richiesta è finito in errore 422 (chiave sbagliata) e un altro dataflow (ampliamenti, `RESID_CONSTR_2`) non è stato riprovato.
- Pagina dei dati: https://www.istat.it/tavole-di-dati/statistiche-sui-permessi-di-costruire-anno-2025/ (annuale 2025, pubblicata il 17/6/2026; ultimo trimestre uscito: II 2026, 9/10/2026).
- Manca: il comune di Milano da solo; le ristrutturazioni; i permessi per titolo a livello comunale.

### 2.4 Già su disco, usati solo come contesto
- Popolazione per NIL, ds205 (`citta-15-minuti/raw/comune_milano/pop_caratteristiche_quartiere/`), 88 NIL per anno 2011-2024 (+1 riga "N.D."); confini dei 88 NIL, ds964 (`citta-15-minuti/raw/comune_milano/nil_vigenti/`).
- Compravendite (NTN) di Milano comune, trimestrali, e quotazioni OMI in euro 2025 (`prezzi-case/pulito/ntn_milano_trimestrale.csv`, `prezzi_citta_mediana_zone.csv`, solo "abitazioni civili"; media annuale delle mediane semestrali: è un indicatore grezzo).
- Una cartella "case popolari" non esiste in `milano-in-dati`: non ho fatto confronti con quel filone.

### 2.5 Altro sondato
- Edifici degradati, abbandonati o dismessi 2014-2017 (ds503, CC-BY): 174 immobili privati con indirizzo e NIL, scaricato in `raw/comune_ds503/`, **non usato** (indirizzi di proprietà private).
- Catalogo completo del portale: `raw/catalogo_completo.json` (2.611 dataset); ricerca per parole chiave: `raw/search_all.json` (200 dataset unici trovati con le 20 parole chiave). Dataset trovati sul Censimento 2001/2011 (edifici e abitazioni per NIL: ds1524, ds1522, ds1457) e sui certificati energetici (CENED, ds604/ds623): non scaricati.
- Sportello Unico Edilizia: le pratiche passano dalla piattaforma "OnlyOne-Pratiche Edilizie"; il Garante per la privacy ha dichiarato riservati i dati personali nei fascicoli SCIA/CILA (BibLus, 2018): è una spiegazione plausibile dell'assenza di dati aperti, ma è una mia lettura. Conteggi annuali di CILA/SCIA per Milano: non trovati.

## 3. Pulizia

`scripts/build_titoli.py` -> `pulito/titoli_edilizi.csv` (1.315 righe, separatore `;`) e `pulito/controlli_titoli.json`.
- Una tabella sola per i 5 dataset (colonne `uso`, `intervento`, `tipo_titolo`, `titolare_categoria`, `abitazioni`, `volume_m3`, `superficie_m2`, indirizzo, NIL, coordinate, flag). Nessun valore è stato cancellato.
- **NIL**: punto in poligono con i 88 NIL vigenti. Confronto con il NIL scritto nel file: 1.211 su 1.211 record uguali (100%). 104 record non hanno coordinate: ne ho recuperati 50 dall'indirizzo con i civici del Comune (4 al civico, 46 solo alla via, se almeno l'80% dei civici della via sta in un NIL: colonna `geo_metodo`, da leggere come approssimato); **54 restano senza NIL** (4,1%).
- **Flag**: anno fuori serie 9 record (2010-2012, ritardi); titolo mancante 4; più di 300 abitazioni 3; volume zero o mancante 7; stessa via/civico/anno/uso/intervento di un altro record 307 (cantieri con più edifici).
- `indirizzo_pubblicabile = 0` per 310 record (titolare "Persona fisica" o piccolo ampliamento residenziale): **in una pagina non vanno mostrati indirizzi di questi record**, perché potrebbero identificare privati. `id_modello` è il codice del modello, non una persona.
- Il campo "Abbattimento e ricostruzione" è vuoto prima del 2021 (3 sole eccezioni), nel 2021 è compilato per 35 nuovi residenziali su 68 (33 a vuoto) e dal 2022 per tutti (185 su 185).
- "SCIA" e "SCIA alternativa" si scambiano di ruolo nel tempo (la SCIA alternativa è il 37-49% fino al 2017, l'1-2% nel 2018-2019, poi 60-71% nel 2021-2022): sembra una differenza di compilazione, non di comportamento. **Per i confronti nel tempo ho sommato le due.**

`scripts/dbt_confronto.py` -> `pulito/dbt_nil.csv`, `dbt_unita_nuove_2020.csv` (nuove + sopraelevate, centroide), `dbt_unita_sparite_2012.csv`, `dbt_controlli.json`.
- Solo unità fuori terra (2012: codice `0301`; 2020: `01`) e almeno 20 m² di impronta; ogni unità del 2020 è "nuova" se meno del 20% della sua impronta era coperta da una unità 2012 di qualunque tipo, "sparita" l'analoga del 2012 rispetto al 2020, "sopraelevata" se già presente (copertura >= 80%) e più alta di almeno 3 m. Altezze sotto 2,5 m portate a 2,5 m.
- La differenza di altezza sulle unità rimaste ha mediana 0,0 m (1° e 99° percentile -4,3 e +5,4): nessuna distorsione sistematica evidente.
- Soglie e regole sono scelte mie (non verificate contro i permessi): sono una stima.

## 4. Riepilogo (tutti i numeri in `pulito/riepilogo.json` e nelle tabelle; `scripts/analisi.py`)

### 4.1 Per anno (serie 2014-2024, `pulito/serie_annuale.csv`)
- Totali 2014-2024: **725 nuovi fabbricati residenziali, 210 non residenziali, 14 per collettività; 204 ampliamenti residenziali, 148 non residenziali, 5 collettività**. 26.174 abitazioni nei nuovi fabbricati (26.106 nei residenziali), 322 negli ampliamenti. Volume dei nuovi fabbricati 19,88 milioni di m³; ampliamenti 0,46 milioni di m³.
- Nuovi fabbricati (tutti gli usi) per anno: 79, 62, 70, 92, 97, 122, 105, 89, **127** (2022), 73, **33** (2024). Abitazioni: 1.880, 1.006, 1.409, 3.072, 2.938, 3.421, 3.080, 2.639, **3.917**, 1.753, **1.059**.
- Tipo di titolo, nuovi fabbricati (`pulito/nuovi_per_tipo_titolo_anno.csv`): quota di SCIA (semplice più alternativa) 49% nel 2014, 34% nel 2018, 51% nel 2020, **62% nel 2021, 72% nel 2022**, 51% nel 2023, 35% nel 2024. Permesso di costruire: 63 nel 2018, 73 nel 2019, 35 nel 2022, 10 nel 2024.
- **Nuovo contro ristrutturazione**: non misurabile (sezione 1, punto 1). Gli ampliamenti (volume aggiunto) sono 357 in 11 anni, 0,46 milioni di m³ in totale.
- Abbattimento e ricostruzione (campo completo solo dal 2022): nuovi residenziali 2022-2024 = 185, di cui **92 ricostruzioni (50%)**: 45 su 103 (2022), 38 su 58 (2023), 9 su 24 (2024); nel 2021 sono 4 su 35 compilati (68 totali). Le 92 ricostruzioni hanno 2.859 abitazioni e 1,59 milioni di m³; i 93 edifici non sostitutivi 3.867 abitazioni e 1,28 milioni di m³.

### 4.2 Abitazioni nuove contro popolazione (`serie_annuale.csv`)
- Popolazione del comune (somma dei NIL, ds205): 1.350.680 (2014), 1.407.044 (2024): **+56.364**. Le abitazioni in nuovi fabbricati nello stesso periodo (2014-2024): 26.174, cioè 46 ogni 100 residenti in più (una abitazione ogni 2,2 residenti in più). Le demolizioni non sono sottratte (non ci sono nei dati): è un conteggio lordo.
- Anno per anno la popolazione sale e scende (2020 -11.929, 2021 -6.217, 2022 +10.388, 2023 +20.924, 2024 -10.553 secondo ds205); il rapporto tra nuove abitazioni e nuovi residenti non è stabile (da 8 a 38 ogni 100 negli anni con crescita positiva): non c'è una relazione annuale leggibile.
- Confronto con ISTAT (provincia di Milano, `NUMDW` = abitazioni in fabbricati residenziali nuovi): 2022 6.257, 2023 3.946, 2024 3.552, 2025 3.241. Il comune pesa tra il 34% (2015) e l'83% (2020) delle abitazioni della Città metropolitana (`quota_comune_su_provincia_abitazioni_pct`): serie molto variabile.
- Contesto (prezzi-case): compravendite NTN del comune 28.617 (2022), 24.848 (2023), 24.003 (2024); prezzo OMI "abitazioni civili" in euro 2025: 3.128 (2014), 3.410 (2022), 3.840 (2024) (media di mediane per zona).

### 4.3 Dove (NIL) (`pulito/nil_costruzioni.csv`)
- Abitazioni nuove 2014-2024 assegnate a un NIL: 25.005 (su 26.174; le altre 1.169 stanno nei 47 nuovi fabbricati senza NIL). I **primi 5 NIL hanno il 28,8% delle abitazioni, i primi 10 il 43,2%; 14 NIL su 88 non ne hanno nessuna**.
- Primi NIL per abitazioni nuove: Maggiore-Musocco-Certosa 1.954 (7,8%; popolazione 4.921 -> 9.930), Lorenteggio 1.459, Lambrate-Ortica 1.422, Gorla-Precotto 1.384, Bovisa 989, Adriano 944, Vigentino-Q.re Fatima 837, Moncucco-San Cristoforo 615, Porta Ticinese-Conca del Naviglio 611, Porta Ticinese-Conchetta 593.
- Per volume dei nuovi fabbricati (anche non residenziali): Maggiore-Musocco-Certosa 2,62 milioni di m³, Scalo Romana 1,52, Tre Torri 1,11, Lorenteggio 0,94, Lambrate-Ortica 0,73; i primi 5 NIL hanno il 38,0% del volume.
- Correlazioni tra NIL (Spearman, n = 88): abitazioni nuove dei permessi contro variazione di popolazione 2014-2024 **rho = 0,48**; contro il volume nuovo del confronto DBT **rho = 0,40**; volume netto DBT contro popolazione 0,27. Sono associazioni medio-deboli, non prove.
- Dal confronto DBT (per NIL, `dbt_nil.csv`): nuove unità sopra 300 m² di impronta, volume netto (nuove meno sparite) più alto a Cascina Merlata (+0,33 milioni di m³), Porta Vigentina-Porta Lodovica (+0,29), Lorenteggio (+0,29), Ortomercato (+0,26), Bovisa (+0,25), Maggiore-Musocco-Certosa (+0,23). **Il valore più basso, Stadio-Ippodromi (-1,97 milioni di m³), è quasi certamente un errore del metodo**: sono le tribune dello stadio, alte 54 m, segnate come "sparite" perché nel 2020 sono codificate altrove; altre negative (Bovisasca -0,46, Farini -0,17) non le ho verificate.
- Totali DBT: 12.289 unità nuove (13,83 milioni di m³), 4.102 sopraelevate (+5,92 milioni di m³), 10.523 sparite (12,28 milioni di m³); sopra 300 m²: 1.053 nuove (8,95 milioni di m³) e 952 sparite (8,28). Il volume totale delle unità fuori terra passa da 451,2 a 442,0 milioni di m³ (-2%) e l'impronta da 31,52 a 31,04 km²: **entro il rumore del metodo, non dice che Milano ha costruito meno**; il volume sopra 300 m² nuovo e sparito sono quasi pari.

### 4.4 Grandi interventi (`pulito/grandi_interventi_top60_volume.csv`; solo indirizzi con `indirizzo_pubblicabile = 1`)
I dati danno l'indirizzo e la categoria del titolare, **non il nome del progetto**: i nomi noti (Expo, Scalo Romana, Tre Torri, Santa Giulia, ecc.) sono mie letture degli indirizzi, da verificare con una fonte prima di scriverli.
- Per volume (nuovi fabbricati, anno del titolo, imprese/società o altro): via Pasolini (Maggiore-Musocco-Certosa) 2018, non residenziale, 1,48 milioni di m³; "Area ex Expo 2015 - via Belgioioso" 2018, 0,87 milioni (nella voce destinazione "Sanità"); viale Domodossola (Tre Torri) 2023, 0,60; viale Ortles 36 (Scalo Romana) 2019, 0,59; via Bonfadini (Rogoredo-Santa Giulia) 2023, SCIA alternativa, 0,51; via Calvino 11 (Tre Torri) 2022, 39 abitazioni, 0,32 milioni, SCIA alternativa; via Gargano-via Ortles (Scalo Romana) 2023, 0,29.
- Per abitazioni: via Frigia 19 (Gorla-Precotto) 2020, 695 abitazioni (SCIA); via Bisceglie (Lorenteggio) 2022, 11 edifici, 607; via Gassman (Adriano) 2022, 3 edifici, 502 (SCIA alternativa); via Giovenale 15 (Porta Ticinese-Conca del Naviglio) 2019, 498; via Calchi Taeggi (Lorenteggio) 2019, 19 edifici, 489; via Durando 7 (Bovisa) 2024, 317.
- **Segnalo che 3 edifici (via Giovenale, via Durando 2021 e 2024) hanno tra 76 e 98 m³ per abitazione**: sono probabilmente residenze studentesche o appartamenti piccolissimi contati come abitazioni (1.084 abitazioni, 4,1% del totale). Il 28% delle abitazioni sta in soli 49 edifici con almeno 100 abitazioni. I primi 10 interventi pesano il 26,9% del volume, l'1% dei più grandi il 23,5%.

### 4.5 Il periodo dell'inchiesta (2022-2025): cronologia dai dati, non una prova
Dati: `pulito/nuovi_per_trimestre_2021_2024.csv`, `titoli_per_mese_2021_2024.csv`. Nuovi fabbricati per trimestre (tutti gli usi): 2021: 28, 23, 25, 13; 2022: 29, **61**, 19, 18; 2023: 14, 21, 16, 22; **2024: 12, 10, 6, 5**. Abitazioni: 2022-T2 = 2.558 (65% di tutto il 2022); 2024-T4 = 68.
- Giugno 2022: 29 nuovi fabbricati con SCIA alternativa e 1 permesso di costruire (aprile 8 e 5, maggio 16 e 2): da aprile a giugno 2022, 53 SCIA alternative contro 8 permessi.
- Per i fatti pubblici ho solo titoli di giornale (da verificare con le fonti primarie): l'esposto che ha dato avvio al filone (13/7/2022, Il Giorno); il tentativo di inserire la norma nel decreto "Salva-casa" ritirato a luglio 2024 (ediltecnico.it, 25/7/2024); sequestri di cantieri in novembre 2024 (didascalia ANSA in Il Post 5/3/2025); primo arresto nell'inchiesta il 5/3/2025 (Il Post); il 6/3/2025 il Comune dichiara di non sostenere più la norma "Salva Milano" (Il Post); 17/7/2025 una nuova inchiesta; 2/8/2025 il Comune chiede alla prefettura aiuto per i cantieri sotto sequestro (Il Post). Cifre sul numero di cantieri fermi variano tra le fonti (circa 150 secondo alcune): non le uso.
- **Effetto del blocco: si vede qualcosa, ma non si può dire che sia l'effetto.** Nei dati del Comune i nuovi fabbricati residenziali scendono del 59% dal 2023 al 2024 e del 77% dal 2022 (abitazioni -40% e -73%). Nello stesso periodo l'ISTAT dà per la Città metropolitana abitazioni -10% (2023->2024) e -43% (2022->2024), fabbricati residenziali -7% e -25%; i capoluoghi sopra 500.000 abitanti +30% (2023->2024) e -33% (2022->2024). Nel 2025 l'ISTAT dà per la provincia 3.241 abitazioni (-9% sul 2024) e 344 fabbricati (+2%); i capoluoghi >500.000 scendono a 1.900 abitazioni (-64%): non so quali città. Il calo di Milano comune nel 2024 è quindi più forte di quello provinciale, ma il 2022 era un picco (ondata di SCIA alternative in aprile-giugno) e il 2024 può essere incompleto (il Comune pubblica i dati con ritardo e nei dataset ci sono record 2010-2012 arrivati in ritardo). **Sono confronti, non prove.**

## 5. Limiti dei dati (da riportare in una pagina)

1. Sono "permessi", non cantieri: l'anno è quello del ritiro del titolo; non sappiamo se e quando l'edificio è stato costruito (fine lavori), né se il titolo è stato poi sospeso o sequestrato.
2. Sono solo nuovi fabbricati e ampliamenti: ristrutturazioni, CILA, cambi d'uso, demolizioni senza ricostruzione non ci sono.
3. Poche centinaia di record: il rumore statistico è alto; un solo intervento da 695 abitazioni sposta un anno intero.
4. Nei "nuovi fabbricati" le ricostruzioni dopo demolizione sono incluse, ma il campo che le identifica esiste solo dal 2021.
5. Le etichette "SCIA" e "SCIA alternativa" cambiano uso tra il 2017 e il 2020: ho sommato le due.
6. Le abitazioni sono lorde: nessuna sottrazione delle abitazioni demolite; alcune unità sono micro-appartamenti.
7. NIL: 54 record senza NIL (4,1%); 46 localizzati solo alla via.
8. Il confronto DBT è 2006-2020 per la maggior parte, ha regole scelte da me e un errore noto (Stadio-Ippodromi); non conta le ristrutturazioni né i cambi d'uso.
9. ISTAT: solo provincia/classi, non il comune; il 2025 solo lì.
10. Gli indirizzi dei record con titolare "Persona fisica" o di piccoli ampliamenti non vanno mostrati.
11. Le coincidenze tra picchi, inchiesta e calo sono confronti: gli eventi sono tre fonti giornalistiche non verificate.

## 6. La cosa più sorprendente

**Dal 2022, 92 dei 185 nuovi edifici residenziali del Comune di Milano (50%) sostituiscono un edificio demolito: portano 2.859 abitazioni e 1,59 milioni di m³ (più volume dei 93 edifici costruiti dove non c'era un edificio demolito: 3.867 abitazioni e 1,28 milioni di m³); e 61 di queste 92 ricostruzioni (66%) sono passate con la SCIA alternativa, contro il 43% degli edifici non sostitutivi (40 su 93).** Nel 2022 erano 45 su 103; in giugno 2022 si sono concentrate 29 SCIA alternative sui nuovi fabbricati. Limiti: il campo esiste solo dal 2021 (e nel 2021 è compilato per metà), la risposta è dichiarata dal compilatore, il numero di abitazioni è quello del nuovo edificio senza sottrarre le demolite. "Nuovo" nei dati non vuol dire "su terreno libero": non si può dire quanto suolo nuovo sia stato occupato.

## 7. Che cosa potrebbe mostrare una pagina

- Una linea 2014-2024 di nuovi fabbricati e abitazioni (non residenziale a parte), con il picco 2022 e il 2024 più basso, e a lato la popolazione del comune (ds205) e le abitazioni nuove dell'ISTAT per la provincia.
- Una striscia "chi lo autorizza": quota di SCIA contro permesso di costruire per anno, con le due etichette sommate (e la nota sul cambio di compilazione).
- Una mappa dei 88 NIL: abitazioni nuove per NIL e per 1.000 abitanti, con le cinque aree dove si concentra il 29% delle nuove abitazioni; secondo livello, i nuovi volumi dal confronto con il DBT 2012-2020 (con le avvertenze).
- Un elenco dei dieci interventi più grandi (solo indirizzi pubblicabili, nomi di progetto solo con una fonte) e una nota di cronologia 2022-2025 con il grafico dei trimestri.
- "Le ricostruzioni dopo demolizione" come numero grande: metà dei nuovi edifici residenziali dal 2022 (92 su 185).
- Non si può mostrare: nuovo contro ristrutturazione; singoli indirizzi di privati; l'effetto del blocco come causa.

## 8. Domande aperte (non fatte)
- Chiedere al Comune (accesso civico / SUE) i conteggi annuali di CILA, SCIA, permessi e demolizioni per municipio: non risultano aperti.
- Scaricare dall'ISTAT il dataflow "ampliamenti" (RESID_CONSTR_2) e quello per titolo (RESID_CONSTR_4) per la provincia, e i trimestrali nazionali.
- Scaricare Censimento 2011 (edifici per epoca di costruzione per NIL) e CENED (certificati energetici con anno di costruzione) per l'età del patrimonio edilizio per NIL.
- Verificare con il Comune il significato di "Anno Ritiro" e se i record 2024 sono completi.
- Rifare il confronto DBT per i grandi edifici verificando a mano 50 casi con un'ortofoto.
