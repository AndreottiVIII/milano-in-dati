# Beni confiscati alla mafia a Milano - FASE 1 (fonti, scarico, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web. Ogni numero dice da quale file viene. Programmi in `scripts/` (si lanciano con `python -I -X utf8 <script> <percorso assoluto>`; vedi STATO.md), dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`, tutti i numeri sotto in `pulito/riepilogo.json`.
Regola di questa cartella: **mai nomi di persone** (da chi è stato confiscato) e **mai nomi di aziende**. Nei file puliti ci sono solo tipi di bene, indirizzi, quartieri, settori. I file grezzi dell'elenco del Comune (`raw/ds147/`) contengono i nomi di chi ha in uso i beni (fondazioni, cooperative, ma anche qualche negozio o privato): restano in `raw/`, non vanno pubblicati; nelle tabelle pulite c'è solo il tipo di ente.

## 1. In breve

1. **A Milano (solo il Comune) l'Agenzia nazionale (ANBSC) elenca 665 beni confiscati: 477 immobili e 188 aziende** (ANBSC, export del 1/11/2026). È l'1,4% dei 46.940 beni d'Italia; Milano è l'ottavo comune d'Italia per numero di beni, il primo del Nord (dopo Palermo, Roma, Bagheria, Napoli, Reggio Calabria, Termini Imerese, Caltanissetta). Per abitante ne ha meno di Roma e delle grandi città del Sud: 49 beni ogni 100.000 abitanti (Roma 78, Napoli 108, Catania 116, Palermo 645), più di Torino (26) e Genova (23).
2. **Immobili (477)**: 158 ancora in gestione all'Agenzia, 307 destinati (234 trasferiti agli enti territoriali, 73 tenuti dallo Stato per forze dell'ordine e uffici), 12 venduti. Per tipo: 251 abitazioni, 96 box/posti auto, 41 terreni, 23 negozi e laboratori, 19 magazzini, 31 pertinenze (cantine, solai), 16 altro.
3. **Aziende (188)**: 115 in gestione, 73 uscite (68 liquidate, 5 vendute). A livello nazionale le aziende uscite sono 1.790: 1.697 liquidate (94,8%), 89 vendute, **3 affittate, 1 ceduta gratuitamente**.
4. **L'elenco del Comune (giugno 2026) ha 274 unità** (146 abitazioni, 45 box, 39 negozi/locali, 13 magazzini...) in 157 indirizzi: **193 già in uso** (165 assegnate a terzi, 28 in gestione diretta del Comune), **47 in attesa di assegnazione**, 10 ferme per lavori o problemi, 24 senza informazioni. Tre palazzi (Via Vallazze 26, Via Sant'Arialdo 69, Via Carlo Torre 24) contengono 59 delle 274 unità.
5. **"Da quanto tempo"**: le date nei dati sono due: l'anno del decreto di destinazione e l'anno di apertura del procedimento. Non esiste l'anno di confisca. Per le 57 unità non assegnate con anno noto il decreto che le ha date al Comune ha una **mediana di 18 anni** dal decreto (decreti dal 2001 al 2023; 22 sono del 2008), ma 18 di queste sono i box di un solo palazzo (Via Carlo Torre 24, decreto 2008, "in attesa di prossimo bando").
6. **Le fonti non sono la stessa cosa**: ANBSC conta 215 immobili destinati al Comune, il Comune elenca 274 unità. I conti non tornano 1 a 1 (vedi "Limiti dei dati").

## 2. Fonti, una per una (anche in `raw/download_log.csv`, con sha256)

### 2.1 ANBSC - Infoweb / OpenRE.G.I.O. (la fonte principale)
- **Che cos'è**: l'export pubblico dei dati dell'Agenzia nazionale per l'amministrazione e la destinazione dei beni sequestrati e confiscati. Pagina `https://openregio.anbsc.it/statistiche` (con l'avviso "il servizio è stato spostato sulla nuova Piattaforma Unica delle Destinazioni", `benidestinati.anbsc.it`, ma i download sul vecchio indirizzo funzionano ancora). Il sito `benisequestraticonfiscati.it` non offre file: rimanda a questi.
- **File scaricati** (4, nazionali, CSV UTF-8, link pubblico di export della pagina, nessun login): `raw/anbsc_openregio/nazionale_{gestione,destinati}_{immobili,aziende}.csv`
  - **destinati_immobili** 20.013 righe, **destinati_aziende** 1.790 righe: m_bene, s_bene, regione, provincia, comune, indirizzo, ufficio e distretto giudiziario, numero di procedura, categoria e sottocategoria (catastale), tipologia di destinazione, destinatario, finalità, descrizione d'uso (`utilizzo`), decreto (numero, anno, data).
  - **gestione_immobili** 21.938 righe, **gestione_aziende** 3.199 righe: s_bene, regione, provincia, comune, categoria, sottocategoria, provvedimento (Confisca def./I/II...), quota confiscata, ufficio giudiziario, tipo di procedura. **Niente indirizzo, niente date.**
- **Licenza**: Italian Open Data License v2.0 (IODL 2.0), dichiarata sulla pagina stessa ("I dati e i testi presenti in questa sezione... sono rilasciati con la licenza Italian Open Data License v2.0"). Si può ripubblicare citando ANBSC.
- **Data**: dati "aggiornati in tempo reale" (testo della pagina); scaricati il 1/11/2026. La pagina avverte che "i dati relativi alle destinazioni dei beni potrebbero essere sottostimati" per il rinnovo della piattaforma.
- **Cosa manca**: data di confisca, data di inizio della gestione, indirizzo per i beni in gestione, coordinate, valore, metri quadri, nomi (giustamente).

### 2.2 Aziende Confiscate (Unioncamere + ANBSC) - JSON-LD
- `https://aziendeconfiscate.camcom.gov.it/odacWeb/opendata/download/` : catalogo + due file, `raw/aziende_confiscate_unioncamere/`. 3.422 aziende in confisca definitiva, dati al 1/10/2026 (catalogo `modified` 2026-10-01, aggiornamento trimestrale; la home dice "22/12/2024": è un testo non aggiornato).
  - `aziende-confiscate-anbsc.json`: stato amministrativo (3.104 in gestione, 318 fuori gestione).
  - `aziende-confiscate-unioncamere.json`: natura giuridica, stato di attività, codice e descrizione Ateco, sede legale (regione, provincia, comune). Nessun nome né partita IVA (gli id sono codici cifrati).
- **Licenza**: CC BY 4.0 (indicata nel catalogo `dct:license` / rightsHolder `creativecommons.org/licenses/by/4.0`).
- **Cosa manca**: copre solo le aziende in confisca definitiva (non quelle ancora in primo o secondo grado); le due liste non si agganciano per intero alle liste ANBSC (nell'export ANBSC le aziende in gestione a Milano sono 115, nel file Unioncamere 127 aziende con sede legale a Milano sono "in gestione": criteri diversi).

### 2.3 Comune di Milano - open data (ds147)
- Dataset CKAN `ds147-sociale-beni-immobili-confiscati-criminalita-organizzata`, "unità immobiliari confiscate trasferite al patrimonio del Comune di Milano ai sensi dell'art. 48 D.Lgs. 159/2011 e destinate a finalità sociali e/o istituzionali". `raw/ds147/` (CSV 150 KB, JSON, metadati CKAN).
- **274 unità**, aggiornamento giugno 2026 (colonna `periodo`; il file ha `metadata_modified` 18/6/2026), frequenza mensile dichiarata. Campi: unità, tipologia, consistenza, indirizzo, municipio, dati catastali, tipologia di destinazione (scopi sociali / fini istituzionali / "fini di lucro con reimpiego dei proventi per finalità sociali"), utilizzazione, **ente assegnatario**, estremi e durata del contratto, periodo del contratto, note.
- **Licenza**: CC-BY (campo CKAN `license_id`; la versione non è scritta). Si può ripubblicare citando "Comune di Milano - dati.comune.milano.it".
- **Altre ricerche sul portale**: la ricerca CKAN "confiscati" e "beni confiscati" trova solo questo dataset (`raw/sondaggi/comune_milano_ckan_ricerca_confiscati.json`). Non esiste un elenco separato dei beni "ancora da assegnare": è nella stessa tabella (colonna note, ente assegnatario vuoto).
- **Cosa manca**: la data di destinazione/acquisizione al patrimonio (la ricavo agganciando l'indirizzo all'elenco ANBSC), un identificativo che lo leghi ad ANBSC, i beni non ancora trasferiti. Alcune note si riferiscono a un'unica situazione per più righe.

### 2.4 Regione Lombardia - Open Data (krpf-yure)
- "Beni confiscati alla criminalità organizzata - Beni destinati": 1.331 righe lombarde (250 a Milano città), tratte da ANBSC e "arricchite dai comuni tramite il Viewer Beni"; data ultimo aggiornamento del portale 06/10/2026 (frequenza mensile), ma le righe di Milano sono state caricate il 17/9/2020 (214), 12/5/2022 (29), 8/3/2023 (7). `raw/regione_lombardia/`.
- I campi che dovrebbero dire come è usato il bene (`uso_str_u`, `scopo_u`, lavori, costi, finanziamenti) sono **tutti vuoti ("--") per Milano**. Aggiunge solo la categoria catastale. 225 dei 250 id di Milano si ritrovano nei 319 destinati ANBSC di oggi.
- **Licenza**: il portale (Socrata) non la scrive nei metadati (`license` vuoto). Non verificata: da non usare come fonte primaria. Non ne ho avuto bisogno. Gli altri risultati lombardi (Rho, San Donato Milanese, Zerbolò) sono elenchi dei singoli comuni, fuori Milano: non scaricati.

### 2.5 Confiscati Bene (Libera / onData) - spento, copie in archivio
- `confiscatibene.it` oggi risponde 403 con una pagina "Progetto in pensione... l'abbiamo spento" (`raw/sondaggi/confiscatibene_home_progetto_in_pensione.html`): non è un blocco anti-robot, il sito è chiuso. Non ho cercato di aggirare niente.
- Ho preso dalla **Wayback Machine** (archive.org, indirizzo `.../id_/...` del file originale) i file dati che il sito pubblicava: `raw/confiscatibene_wayback/`
  - `latest_bid / big / ad / aig` (6-8/8/2024): le copie ANBSC "destinati/in gestione, immobili/aziende" di agosto 2024 (con codici ISTAT aggiunti da onData). Servono per vedere cosa è cambiato in 27 mesi.
  - `immobili_anbsc_2014-09-20.csv`, `aziende_anbsc_2014-09-20.csv`: copie ANBSC di luglio 2014 (colonna `Stato`: in gestione / destinati consegnati / non consegnati / usciti).
  - `openregio_comuni_2018-02-26.csv`: conteggi per comune per sottocategoria (2018). Solo contesto, non usato nei numeri.
  - `Elenco beni confiscati destinati al patrimonio comunale e utilizzo` (2025): è un modulo di un altro comune (Palermo), non usato.
- **Licenza**: i metadati dei dataset (pagine archiviate 2019) dicono "Creative Commons Attribution"; il sito dichiara CC BY-SA 4.0 per i contenuti. I dati originali sono comunque ANBSC (IODL 2.0). Per cautela: citare ANBSC come fonte e Confiscati Bene come intermediario.
- **Limiti**: sono fotografie datate; non sono verificabili con una somma di controllo del sito originale. Le definizioni dei "stati" del 2014 sono diverse da quelle di oggi.

### 2.6 Altro
- **ISTAT** popolazione residente al 1/1/2025 per comune (`raw/istat_pop/POSAS_2025_it_Comuni.zip`, `demo.istat.it`): servono per i "per 100.000 abitanti". Licenza ISTAT CC BY 4.0. Milano 1.365.698.
- **Registro civici del Comune** (ds634, 1/10/2026, CC BY), già scaricato per altri filoni: `citta-15-minuti/raw/comune_milano/civici/estratto/ds634_civici_coordinategeografiche_20261001_final.csv` (letto da lì, non copiato). Usato per le coordinate e il NIL (campi `LONG_WGS84`, `LAT_WGS84`, `NIL`, `ID_NIL`).
- **Non fatto / non trovato**: nessuna fonte con la data di confisca o con il valore dei beni a Milano; nessun registro dei beni "venduti" con prezzo.
- **Nessuna registrazione, nessun login, nessun blocco anti-robot aggirato.** Per i filtri per comune di OpenRE.G.I.O. (elenco dei comuni nel menu) la richiesta semplice ha dato una risposta vuota; una seconda prova con intestazioni da browser (Referer) è stata fermata dai controlli di sicurezza e non l'ho ripetuta. Ho usato i quattro export nazionali (link di download pubblico previsto dalla pagina) e filtrato in locale.

## 3. Pulizia (`scripts/build.py`, `scripts/anbsc_parse.py`)

- **Il CSV ANBSC "destinati" è rotto**: il campo `utilizzo` ha virgolette dentro il testo e a-capo, quindi il modulo `csv` standard sbaglia (conta 20.019 righe invece di 20.013 e spezza 74 record). `anbsc_parse.py` divide il file in record dove inizia un identificativo e li divide su `","`. Risultato: 20.013 immobili + 1.790 aziende, 0 righe scartate.
- **Stato** (tabella `immobili_anbsc_milano.csv`): `in gestione` = file gestione; `destinato` = trasferimento agli enti territoriali o mantenimento allo Stato; `uscito` = vendita (nazionale anche liquidazione, demolizione, revoca). Per le aziende: `in gestione` o `uscita` (liquidazione/vendita/affitto).
- **Tipo**: abitazione (appartamento, villa, abitazione indipendente), box_posto_auto, negozio_laboratorio, magazzino, terreno (qualsiasi), altro_commerciale_industriale, altro_pertinenza (le "Altro" della categoria abitazione: cantine, solai), altro.
- **Destinatario**: Comune (ANBSC "Comune"/"Comuni"), Provincia/Città metropolitana, Forze dell'ordine e sicurezza (Carabinieri, GdF, Polizia, Forestale, Vigili del fuoco, Prefettura), Stato (ministeri e altre amministrazioni), Altro, ANBSC, non indicato.
- **Ente assegnatario del Comune** (ds147): tipo ricavato dal nome: fondazione, cooperativa/impresa sociale, associazione/volontariato, impresa/privato, gestione diretta del Comune, altro. Il nome non viene copiato.
- **Anni**: `anno_destinazione` = anno del decreto ANBSC; `anno_procedura` = anno dopo la barra del numero di procedura (es. "38/2005" = 2005): è l'anno di apertura del procedimento giudiziario, **non** l'anno di confisca.
- **Posizione** (solo con il registro civici del Comune, nessun geocoder esterno): indirizzo "pulito" (via, numero, lettera; sigle P.LE, V.LE, C.SO; iniziali e preposizioni tolte; numeri romani; refusi corretti con il vocabolario delle vie del Comune) e confrontato con le vie del registro. Esito:

| | civico esatto | civico senza lettera | civico più vicino | solo via | solo quartiere (testo) | totale |
|---|---|---|---|---|---|---|
| ANBSC destinati Milano | 288 | 2 | 6 | 13 | 10 | 319 |
| Elenco Comune ds147 | 270 | 0 | 1 | 2 | 1 | 274 |

  Nessun indirizzo senza posizione. I "solo quartiere" sono "Ronchetto sul Naviglio" (una località, non una via: quartiere del Comune "RONCHETTO SUL NAVIGLIO - Q.RE LODOVICO IL MORO"). I "solo via" hanno il punto medio della via e il quartiere più frequente sulla via; vanno mostrati con prudenza. Dei 477 immobili ANBSC, 158 (in gestione) non hanno indirizzo e quindi nessuna posizione.
- **Aggancio ANBSC - Comune**: per ogni unità del Comune, anno del decreto ANBSC dei beni destinati al Comune nello stesso civico (via + numero): 218 unità su 274 agganciate; 10 unità hanno più anni (si prende il più vecchio).
- Tabelle pulite in `pulito/`:
  - `immobili_anbsc_milano.csv` (477): id, fonte, stato, dettaglio, tipo, categoria, destinatario_tipo, finalità, anno_destinazione, anno_procedura, indirizzo, lon, lat, nil, id_nil, qualità posizione.
  - `comune_ds147_milano.csv` (274): tipo, municipio, finalità, stato d'uso, tipo di ente, anni contratto, anni dal decreto, indirizzo, lon, lat, nil.
  - `aziende_anbsc_milano.csv` (188): stato, esito, settore, forma giuridica, anni.
  - `aziende_unioncamere_sede_milano.csv` (153): stato amministrativo, stato di attività, natura giuridica, Ateco (sezione, codice, attività). Nessun nome.
  - `per_nil.csv` (60 NIL): unità per quartiere (Comune e ANBSC). `confronto_comuni.csv` (2.005 comuni), `confronto_province.csv` (110). `tutti_i_beni_per_comune.csv` (46.940 righe, nazionale, senza indirizzi). `riepilogo.json`, `controlli_build.json`.

## 4. Numeri principali (ogni numero: file e tabella)

### 4.1 Quanti e di che tipo (ANBSC, 1/11/2026; `immobili_anbsc_milano.csv`, `aziende_anbsc_milano.csv`)
| Stato | Abitaz. | Box | Terreni | Negozi/lab. | Magazz. | Altro* | Totale |
|---|---|---|---|---|---|---|---|
| In gestione | 75 | 36 | 9 | 11 | 14 | 13 | 158 |
| Destinati | 171 | 59 | 27 | 11 | 5 | 34 | 307 |
| Venduti | 5 | 1 | 5 | 1 | 0 | 0 | 12 |
| **Totale** | **251** | **96** | **41** | **23** | **19** | **47** | **477** |

*pertinenze (cantine, solai), fabbricati commerciali e industriali, altro. In gestione: 135 con confisca definitiva, 17 in primo o secondo grado di giudizio ("Confisca I", "Confisca II"), 3 definitiva parziale, 3 altro (revoca, rinvio); 13 con quota confiscata inferiore al 100%.
- **Destinatari** dei 319 destinati: Comune 215, forze dell'ordine e sicurezza 63, Provincia/Città metropolitana 18, Altro 14, Stato (ministeri) 6, ANBSC 2, non indicato 1. **Finalità** (per i 215 destinati al Comune): scopi sociali 154, fini istituzionali 10, non indicata 51.
- **Aziende** (188): per settore ANBSC, in gestione: attività immobiliari e servizi alle imprese 30, costruzioni 20, altri servizi 15, alberghi e ristoranti 13, commercio 13, attività finanziarie 11, trasporti 7, manifattura 3, sanità 2, agricoltura 1. Uscite (73): commercio 18, costruzioni 14, alberghi e ristoranti 13, immobiliare 12, altri servizi 7, trasporti 4, finanza 2... Forma giuridica: 147 srl, 14 sas, 11 spa, 7 imprese individuali, 3 snc.
- **Secondo Unioncamere (sede legale a Milano, confisca definitiva, 153)**: 127 in gestione, 26 fuori gestione; **46 attive**, 56 cessate, 30 con procedure concorsuali, 21 inattive; per sezione Ateco: attività immobiliari 36 (31 "compravendita di beni immobili su beni propri"), commercio 26, costruzioni 25, "non classificate" 17, alloggio e ristorazione 12, finanza e assicurazioni 10, professioni 7, noleggio e servizi alle imprese 6, trasporti 5; 132 società di capitali, 13 di persone, 8 imprese individuali.

### 4.2 Riuso sociale o ancora in attesa (elenco del Comune, giugno 2026; `comune_ds147_milano.csv`)
| Stato d'uso | Unità |
|---|---|
| Assegnate a terzi | 165 |
| In gestione diretta del Comune | 28 |
| In attesa di assegnazione (bando o nuovo avviso) | 47 (23 box, 14 abitazioni, 8 negozi/locali, 2 pertinenze) |
| Non assegnate: lavori o problemi | 10 |
| Non assegnate: nessuna informazione | 24 |
| **Totale** | **274** |

- Per finalità: 217 scopi sociali, 36 "fini di lucro con reimpiego dei proventi per finalità sociali", 21 finalità istituzionali. Enti assegnatari per tipo: fondazioni 68, cooperative/imprese sociali 53, associazioni/volontariato 35, gestione diretta 28, imprese/privati 6, altro 3, nessuno 81.
- Contratti: 165 assegnate; 13 con contratto già scaduto al 30/6/2026, 30 senza date. Anno di inizio del contratto: 32 nel 2026, 22 nel 2025, 20 nel 2023, 17 nel 2022, 19 nel 2016. Ricorda: è il contratto in corso, non la prima assegnazione.
- **Da quanto tempo** (anno del decreto ANBSC - 2026): le 57 unità non assegnate con anno noto hanno decreto mediano di **18 anni fa** (min 3, max 25; 55 su 57 oltre 5 anni, 42 oltre 10). Escludendo il palazzo di Via Carlo Torre 24: mediana 19 su 39. Per le 114 assegnate con anno noto, tra decreto e inizio del contratto in corso passano **13 anni** (mediana), ma è un'ipotesi alta: il contratto potrebbe essere un rinnovo. Le unità dichiarate "nuova acquisizione 2026" sono 8.
- Immobili destinati al Comune di Milano per anno del decreto (ANBSC, 215): 2008 70 (soprattutto 30/6/2008 e 13/10/2008), 2013 26, 2018 15, 2007 13, 2023 13, 2009 12, 2021 12, 2001-2005 32, altri anni 22 (`riepilogo.json` → destinati_al_comune_per_anno_decreto).

### 4.3 Per quartiere (NIL; `per_nil.csv`)
Elenco del Comune (274 unità): **Loreto-Casoretto-NoLo 31** (tra cui 9 in Via Padova), **Buenos Aires-Porta Venezia-Porta Monforte 30** (Via Vallazze), **Parco delle Abbazie 22** (18 in Via Sant'Arialdo 69, Chiaravalle), **Porta Ticinese-Conchetta 19** (Via Carlo Torre), Lodi-Corvetto 14, Bovisa 11, Dergano 9, Villapizzone-Cagnola-Boldinasco 9, Baggio 8, Farini 7. I primi tre quartieri hanno il 30% delle unità; 56 NIL (su 88-89) hanno almeno un bene del Comune. Per municipio: 9: 51, 3: 44, 2: 42, 5: 34, 6: 27, 8: 25, 4: 22, 7: 17, 1: 12 (campo `Municipio` del Comune).
- Concentrazione: in 157 indirizzi ci sono 274 unità; 5 palazzi con 5 o più unità ne contengono 75 (Via Vallazze 26: 23; Via Sant'Arialdo 69: 18; Via Carlo Torre 24: 18; Via Padova 80: 8; Via Mosso 4: 8). Nei 319 destinati ANBSC: 183 indirizzi distinti.

### 4.4 Milano nel confronto (ANBSC; `confronto_comuni.csv`, `confronto_province.csv`; popolazione ISTAT 1/1/2025)
| Comune | Abitanti | Beni (totale) | Immobili | Aziende | Beni ogni 100.000 ab. | Immobili ancora in gestione |
|---|---|---|---|---|---|---|
| Palermo | 628.693 | 4.054 | 3.593 | 461 | 645 | 36% |
| Roma | 2.747.290 | 2.150 | 1.609 | 541 | 78 | 79% |
| Napoli | 909.013 | 981 | 763 | 218 | 108 | 59% |
| **Milano** | **1.365.698** | **665** | **477** | **188** | **49** | **33%** |
| Catania | 298.054 | 345 | 242 | 103 | 116 | - |
| Bari | 315.831 | 286 | 244 | 42 | 91 | - |
| Torino | 853.196 | 220 | 185 | 35 | 26 | 74% |
| Genova | 564.080 | 127 | 115 | 12 | 23 | - |
| Brescia | 199.853 | 50 | 38 | 12 | 25 | - |
| Venezia | 249.490 | 50 | 39 | 11 | 20 | - |
| Bologna | 390.151 | 39 | 13 | 26 | 10 | - |
| Firenze | 361.705 | 22 | 8 | 14 | 6 | - |
(Resto della tabella in `confronto_comuni.csv`.) Italia: 41.951 immobili + 4.989 aziende = 46.940; in gestione il 52% degli immobili (Milano 33%).
- **Provincia/Città metropolitana di Milano**: 1.665 beni (544 immobili in gestione, 828 destinati, 48 venduti; 141 aziende in gestione, 104 uscite): ottava provincia d'Italia; Milano città è il 40%. Altri comuni: Cesano Boscone 62, Buccinasco 40, Cinisello Balsamo 38, Peschiera Borromeo 37, Cusago 37, San Donato Milanese 36, Sesto San Giovanni 34, Legnano 30. **Lombardia**: 3.444 beni (Milano 1.665, Monza e Brianza 458, Varese 233, Brescia 232, Pavia 167, Bergamo 153, Como 152...).
- Regioni: Sicilia 17.862, Campania 7.303, Calabria 5.484, Lazio 4.304, Lombardia 3.444, Puglia 2.870.
- **Tipi**: a livello nazionale i terreni sono il 39% degli immobili (16.306 su 41.951), a Milano il 9% (41/477): le abitazioni sono il 53% (251/477), in Italia il 30%.

### 4.5 Cosa è cambiato (Milano comune; `riepilogo.json` → serie_milano, movimenti)
| Quando | Immobili in gestione | Immobili destinati | Aziende in gestione | Aziende uscite/destinate |
|---|---|---|---|---|
| Set. 2014 (copia ANBSC) | 52 | 177 (171 consegnati + 6 non consegnati) | 55 | 55 |
| Ago. 2024 (copia ANBSC) | 210 | 258 | 126 | 43 |
| Nov. 2026 (ANBSC) | 158 | 319 | 115 | 73 |
Le definizioni di allora e di oggi non coincidono esattamente: confronto indicativo.
- Dei 210 immobili in gestione ad agosto 2024: **95 sono ancora in gestione** a novembre 2026 (stesso identificativo), almeno 50 sono stati destinati; gli altri 65 non compaiono più né tra i beni in gestione né tra i destinati con lo stesso identificativo (ipotesi non verificabile: molti sono tra i 61 nuovi destinati, che in parte non riportano l'identificativo di gestione). Gestione nuova: 63 immobili entrati dopo agosto 2024. I 258 destinati del 2024 ci sono tutti. Nuovi destinati dal 2024: 61, di cui 29 con decreto del 2021 e 14 del 2023.
- Aziende: 126 in gestione ad agosto 2024, 68 ancora a novembre 2026, 47 nuove.

## 5. La cosa più sorprendente

**Le aziende confiscate non sopravvivono.** Delle 1.790 aziende confiscate e destinate in tutta Italia, 1.697 (il 95%) sono state **liquidate**, 89 vendute, **3 affittate e 1 ceduta gratuitamente**. A Milano 68 su 73 sono state liquidate e 5 vendute: nessuna è stata assegnata a lavoratori o cooperative. Le case invece vengono riusate (193 unità su 274 dell'elenco del Comune sono in uso). Delle 153 aziende in confisca definitiva con sede a Milano (Unioncamere) solo 46 risultano ancora attive al registro imprese (56 cessate, 30 in procedure concorsuali, 21 inattive), e una su cinque (31) ha come attività la "compravendita di beni immobili su beni propri": più del mattone che della ristorazione.

Seconda cosa notevole: **il riuso si ferma sui garage**. 18 delle 47 unità in attesa sono i box di un unico palazzo (Via Carlo Torre 24), destinati al Comune nel 2008 e ancora "in attesa di prossimo bando", 18 anni dopo.

## 6. Limiti dei dati (da riportare in ogni pagina)

1. **Nessuna data di confisca.** Gli anni sono due altri: anno del decreto di destinazione (quando il bene passa a un ente) e anno di apertura del procedimento. Non dicono da quanto tempo il bene è sottratto, né quanto è rimasto vuoto.
2. **I beni in gestione (158 immobili, 115 aziende) non hanno indirizzo né data**: non si possono mettere sulla mappa né datare. La mappa per quartiere mostra solo i 319 destinati e le 274 unità del Comune.
3. **Il conteggio è per "unità", non per edifici o persone.** Un appartamento con la sua cantina e il suo box sono tre beni. Tre palazzi contengono da soli 59 delle 274 unità del Comune.
4. **ANBSC e Comune non coincidono**: ANBSC elenca 215 immobili destinati al Comune di Milano, il Comune ne elenca 274 (comprese 8 nuove acquisizioni 2026 e unità che ANBSC non ha ancora registrato o registra sotto altra forma). Per 56 unità del Comune non c'è un abbinamento per indirizzo con ANBSC. Non c'è un identificativo comune.
5. **ANBSC avverte che le destinazioni potrebbero essere sottostimate** (rinnovo della piattaforma). L'aumento dei destinati tra 2014, 2024 e 2026 può dipendere anche da registrazioni in ritardo.
6. **"In attesa" non vuol dire "mai usato"**: la riga può riguardare un bene già assegnato in passato e ora in attesa di un nuovo bando (le note dicono "in attesa di prossimo bando", "nuovo avviso"). Il tempo "dal decreto" è un massimo, non un tempo di inutilizzo. Anche "13 anni tra decreto e contratto" riguarda il contratto in corso, che può essere un rinnovo.
7. **Il perimetro è il luogo, non il tribunale**: ANBSC attribuisce ogni bene al comune dove si trova (immobili) o al comune indicato per l'azienda (probabile sede); un bene confiscato dal tribunale di Milano ma situato altrove non è a Milano. Per le aziende i conteggi cambiano con la fonte: 188 (ANBSC, gestione + uscite), 153 (Unioncamere, sede legale a Milano, solo confisca definitiva).
8. **Il file ANBSC ha il campo d'uso con virgolette rotte**: ho dovuto scrivere un lettore apposta. I dati sono stati controllati (0 righe scartate) ma ogni nuovo scarico va riletto con `anbsc_parse.py`.
9. **I nomi di vie** nei file ANBSC e del Comune sono scritti a mano (sigle, refusi); l'abbinamento ai civici è esatto per il 91% degli immobili ANBSC e il 99% di quelli del Comune. Le posizioni "solo via" o "civico vicino" (19 su 319 ANBSC, 3 su 274 Comune) vanno segnalate sulla mappa.
10. **Confronto tra comuni**: ANBSC attribuisce i beni al comune dove si trovano; la popolazione è quella al 1/1/2025. "Beni ogni 100.000 abitanti" conta unità, quindi un comune con tanti box o terreni frazionati pesa più di uno con pochi grandi immobili. I comuni con popolazione molto piccola hanno rapporti poco significativi (es. Furnari 8.874 ogni 100.000).
11. **Confiscati Bene** è spento: le copie 2014 e 2024 vengono dalla Wayback Machine, non sono verificabili sul sito originale, e la licenza dei dati è quella dell'originale ANBSC.
12. **Persone e aziende**: nei file ANBSC non ci sono nomi di chi ha subito la confisca; ds147 ha i nomi di chi usa i beni oggi (enti, qualche impresa): non vanno pubblicati; le aziende hanno codici cifrati.

## 7. Cosa potrebbe mostrare una pagina (non fatta)
- **Un numero grande**: 665 beni, 477 immobili e 188 aziende; Milano è il primo comune del Nord (ottavo in Italia) ma l'ultimo per abitante tra le grandi città del Sud e Roma.
- **Dove sono**: mappa dei 319 immobili destinati e dell'elenco del Comune per quartiere (NIL), con punto per edificio; i quartieri Loreto-NoLo, Porta Venezia-Buenos Aires (Via Vallazze 26), Parco delle Abbazie (Via Sant'Arialdo 69, Chiaravalle) e Porta Ticinese (Via Carlo Torre 24) concentrano più di un terzo delle unità del Comune (102 su 274).
- **Cosa ne è stato**: barra a stati (ANBSC: 158 in gestione, 307 destinati, 12 venduti; Comune: 193 in uso, 47 in attesa, 34 senza assegnazione per lavori o dati mancanti), per tipo (abitazioni, box, negozi, terreni).
- **Da quanto tempo**: istogramma degli anni di decreto (picco 2008) e l'età dei beni in attesa; avvertenza sui limiti.
- **Aziende**: sette settori e il destino (liquidazione quasi sempre); "compravendita di immobili" come attività prevalente.
- **Milano e le altre**: tabella a barre dei grandi comuni, beni per 100.000 abitanti e quota ancora in gestione (Milano 33%, Roma 79%, Torino 74%).
- **Nel tempo**: 2014 → 2024 → 2026 con le avvertenze di cui sopra.
- **Regole**: nessun nome di persona o azienda; "limiti dei dati" (non "trappole") in ogni pagina; citare ANBSC (IODL 2.0), Comune di Milano (CC-BY), Unioncamere/ANBSC (CC BY 4.0), ISTAT.
