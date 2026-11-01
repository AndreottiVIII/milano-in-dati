# Il metrò - FASE 1 (raccolta, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web, nessun giudizio. Ogni numero dice file e campo. Programmi in `scripts/` (numerati nell'ordine in cui si lanciano), `python -I -X utf8 <script> <percorsi assoluti>` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`. Registro dei download: `raw/download_log.csv` e `raw/download_log_comune.csv`.

## 1. In breve

1. **Il dato che serviva non è pubblico: nessun ingresso per stazione e per giorno della metropolitana di Milano esiste in open data.** Né nel portale del Comune (16 parole chiave, 813 dataset toccati, 115 con titolo/descrizione sul trasporto: nessuno ha ingressi, tornelli o validazioni), né in ATM, né in AMAT, né in Regione Lombardia (catalogo API), né in ISTAT (solo passeggeri per abitante, 2013-2018). ATM i tornelli li conta (il Report della Mobilità 2024 scrive "conteggiati dai tornelli", p. 94 stampata) ma non li pubblica. Quindi **la tabella `data, stazione, linea, ingressi` non si può fare**. Restano: passeggeri per anno e per linea, un grafico mensile del solo Linate M4, stazioni e orari (GTFS), e - come controllo, per le stazioni dove si cambia per la metro - la frequentazione per stazione delle **stazioni ferroviarie** di Milano (Trenord, CC0).
2. **Passeggeri della metro, per linea e per anno, 2016-2025** (`pulito/metro_passeggeri_linea_anno.csv`): 2016-2024 letti dal grafico vettoriale del Report della Mobilità 2024 di AMAT (precisione ±0,5 mln; la somma 2024 viene 340,6 contro "oltre 341" nel testo; il 2019 viene 384,9 contro 386,8 della stampa); 2025 citato da Wikipedia che rimanda al Report 2025 di AMAT (che non ho ottenuto).
3. **Il Covid è stato -56,6% nel 2020** (M1+M2+M3+M5: 384,9 → 167,0 mln) **e nel 2025 le linee del 2019 sono ancora al -17,4%** (317,9 mln). Con la M4 la rete 2025 fa 352,4 mln, -8,4% sul 2019.
4. **La cosa più sorprendente**: la rete è più lunga e ha una linea in più, ma porta meno gente. 96,8 km e 113 stazioni-linea nel 2019, 111,3 km e 134 nel 2025 (+15% di chilometri); passeggeri 384,9 → 352,4 mln (-8%). Passeggeri per km di rete: **3,98 mln/km nel 2019, 3,17 nel 2025 (-20%)**. E dal 2024 al 2025 la M4 passa da 13,4 a 34,5 mln (+21,1) mentre M1+M2+M3 scendono da 297,7 a 288,0 (M2 -6,2; M1 -3,2): la rete nel complesso cresce solo di 11,8 mln. È un confronto, non una prova (2024 letto da grafico, 2025 da fonte secondaria, definizioni non garantite uguali).
5. **Stazioni mai riprese (solo treno, Trenord, saliti in un feriale di novembre, 2025 su 2019)**: Porta Garibaldi superficie 70%, Repubblica 71%, Porta Garibaldi Passante 72%, Cadorna 73%, Porta Venezia 74%, Bovisa (Politecnico) 74%. Centrale 92%, Lambrate 91%. La teoria "non tornano le stazioni dove si arriva al mattino" (uffici, università) **non regge sui dati**: correlazione tra "arrivi/partenze 7-9 nel 2019" e "ripresa 2025/2019" = -0,10 su 24 stazioni.
6. **Giorni di evento, Olimpiadi, scioperi, partite e concerti a San Siro: nessun dato giornaliero della metro.** Solo cose qualitative (ATM Carta della Mobilità 2026, pagine stampate 26-29, piano di potenziamento per i Giochi: ultima corsa alle 2:00 su tutte le linee, ecc.) e un comunicato Trenord sulla rete ferroviaria (secondario, non scaricato).
7. **Licenze**: dataset del Comune CC-BY (3.0 IT o 4.0 a seconda della scheda); Regione Lombardia CC0; Wikipedia CC BY-SA 4.0; **Report della Mobilità AMAT: "Tutti i diritti riservati"; PDF di ATM: nessuna licenza dichiarata**. Dei PDF si citano i numeri, non si ripubblicano i file né i grafici (vedi punto 5.5).

## 2. Fonti, una per una

Elenco completo con URL, dimensione, hash e data: `raw/download_log.csv`.

### 2.1 Comune di Milano - dati.comune.milano.it (CKAN) - CC-BY
Ricerca: `scripts/01_search.py` -> `raw/search_all.json` (18 parole: metropolitana, metro, ingressi, tornelli (0 risultati), passeggeri, ATM, validazioni, trasporto pubblico, frequentazione, viaggiatori (0), TPL, mobilita, linea M1, affluenza, titoli di viaggio, abbonamenti, bigliett, stazioni metropolitana; 813 dataset distinti, perché la ricerca è per testo libero). Scaricati il 1/11/2026 (`scripts/02_download_comune.py`):

| Dataset | Contenuto | Periodo | Granularità | Righe | Cosa manca |
|---|---|---|---|---|---|
| ds2952 TPL dati sul servizio (da Carta della Mobilità ATM) | linee, lunghezza rete km, parco veicoli | 2005-2025 | anno, per rete | 78 | passeggeri. Errore evidente: tram 2025 = 38,8 km (copia della filovia) |
| ds1547 domanda TPL, passeggeri annui per abitante (ISTAT Mobilità urbana, tav. 2.1) | 474,2 (2013), 428,8, 442,6, 420,9, 480,1, 499,2 (2018) | 2013-2018 | anno, tutto il TPL | 6 | metro separata, dopo il 2018 |
| ds528 TPL entro i confini comunali | fermate, km, veicoli per tipo rete | 2008-2013 | anno | 24 | passeggeri |
| ds1551, ds1550, ds1566, ds1567 | km di metro, densità, convogli disponibili/utilizzati (ISTAT) | 2013-2018 | anno | 6 ciascuno | passeggeri |
| ds535 fermate metro, ds533 sequenza fermate nei percorsi, ds537 orari, ds539 percorsi | anagrafica ATM | aggiornata 24/7/2026 | fermata / percorso | 130 / 650 / 83 / 31 | niente storico, niente passeggeri |

Licenza: nel catalogo `license_id = cc-by`. Citare "Comune di Milano - dati.comune.milano.it". Nessuno dei dataset ha passeggeri per stazione.

### 2.2 AMAT - Report della Mobilità (Comune di Milano) - **tutti i diritti riservati**
- Edizioni: 2022 (1ª), 2023 (2ª, presentata 26/11/2024), 2024 (3ª, presentata 29/11/2025), **2025 (4ª, presentata 18/9/2026)** (pagina `amat-mi.it/it/progetti/report-mobilita/`, notizia 168). Ottenuta e letta solo la 2024, copia ospitata da Clean Cities Campaign (`raw/pdf/Report-della-Mobilita-2024_cleancities.pdf`, 114,6 MB, 106 pagine doppie). Le altre edizioni, compresa la 2025, non le ho trovate in PDF: nessun link sul sito AMAT.
- Cosa contiene di utile (pdf pag. 48, stampate 94-95): grafico "Passeggeri rete metropolitana" 2016-2024 per linea; grafico "Passeggeri intera rete TPL" 2016-2024; testo "oltre 341 milioni di passeggeri all'anno conteggiati dai tornelli" (2024); mappa dei carichi 7-9 feriale: M1 Pagano-Duomo e Palestro-Pasteur >20 mila, M2 Udine-Centrale >20 mila, M3 Centrale-Turati >18 mila, M5 Garibaldi-Monumentale circa 8 mila, M4 Coni Zugna-S. Ambrogio 7 mila. Pag. 40 (stampate 76-77): "Passeggeri al giorno nel 2024": metro 1.244.700, superficie 850.000 (dato stimato), ferroviaria suburbana 349.500. Pag. 5: M4 "circa 150 mila passeggeri giornalieri in continua crescita". Pag. 81 (stampate 160-161): passeggeri mensili ingresso/uscita Linate M4, dicembre 2022 - dicembre 2024.
- **Metodo di lettura dei grafici**: il PDF è vettoriale; `scripts/04_report24_grafici.py` legge la posizione dei marcatori e la taratura dell'asse. Verifica: somma delle 5 linee per anno contro i totali della stampa (Il Giorno 21/3/2024): 2018 368,6 vs 369,0; 2019 384,9 vs 386,8; 2020 167,0 vs 166,1; 2021 205,7 vs 205,1; 2022 284,6 vs 284,7; 2023 329,7 vs 331,3; 2024 340,6 vs 341. Tolleranza dichiarata ±0,5 mln per linea (±2 mln per il TPL intero, ±3 mila per Linate).

### 2.3 ATM - Carte della Mobilità 2016-2026 (11 PDF) e relazioni di bilancio
- Carte della Mobilità (`atm.it/it/IlGruppo/ChiSiamo/Pagine/CartaMobilita.aspx`; anno N = dati al 31/12 dell'anno N-1): tabella "ATM in numeri" con **passeggeri trasportati dalla rete ATM (metro + superficie)** e corse metro al giorno, linee, km, stazioni -> `pulito/atm_carta_mobilita_numeri.csv` (`scripts/08_carta_atm.py`, con pagina PDF). Serie: 715,9 (2016), 737,3, 775,9, 806,5 (2019), 351,9, 415,0, 569,9, 662,2, 675,0, 695,5 mln (2025). **Non c'è la metro separata.**
- Relazioni annuali integrate 2024 e 2025, bilanci 2018, 2020, 2021 (`raw/pdf/`): totali di rete, solo la metro di Copenaghen ha i passeggeri separati. Bilancio 2018, pdf p. 7: "In metropolitana i passeggeri sono stati 369 milioni, +21 milioni (+6%)"; rete totale 789 milioni. Bilancio 2020, pdf p. 14: prima del Covid 2,4 milioni di passeggeri al giorno (1,4 in metropolitana); con le restrizioni -95% e ingressi giornalieri in metropolitana ridotti a 100.000 (marzo 2020; testo estratto con caratteri rovinati, riletto a mano).
- Licenza: nessuna dichiarata, © ATM. Si citano numeri.
- Non ho trovato né le Carte 2015 e precedenti, né i dati per stazione.

### 2.4 Stampa e Wikipedia (fonti secondarie, usate solo dove manca altro)
- Il Giorno 21/3/2024 (G. Anastasio): metro 346,2 (2015), 348,2 (2017), 369,0, 386,8, 166,1, 205,1, 284,7, 331,3 (2023); superficie 398 / 405 / 427 / 444 / 193 / 228 / 313 / 364. "Secondo i dati di Comune e Atm", documento non indicato. Usato come controllo dei totali.
- it.wikipedia "Metropolitana di Milano" (wikitext `raw/web_probe/wiki_metropolitana_di_milano.wikitext`, CC BY-SA 4.0): infobox 2025: 352.406.864 passeggeri; per linea M1 117.994.445, M2 93.538.925, M3 76.498.903, M4 34.511.170, M5 29.863.421 (somma = totale). Cita "AMAT Report della Mobilità 2025, accesso 22/9/2026". **Non verificato sul report**.
- it.wikipedia "Stazioni della metropolitana di Milano" (`raw/web_probe/wiki_stazioni.wikitext`): 125 stazioni, 134 righe stazione-linea, date di apertura per linea -> `pulito/stazioni_wikipedia.csv` (`scripts/06_wiki_stazioni.py`) e `pulito/stazioni_metro.csv`.
- Affaritaliani 3/8/2023 (ATM): San Babila, la più usata, circa 12.000 accessi al giorno; Linate circa 5.000 passeggeri al giorno (primo mese dopo l'apertura di San Babila). Milano Città Stato 17/2/2023: M1 362.000/giorno (516.000 nel 2019), M2 322.000 (468.000), M3 circa 240.000 (320.000), M5 85.000; fonte dei numeri non dichiarata. Non usati nelle tabelle.

### 2.5 GTFS ATM/AMAT (già scaricato dal filone bici-auto-mezzi)
`..\bici-auto-mezzi\raw\gtfs\ext_comune_new\` (feed_version 425, valido dal 26/10 al 30/11/2026, fonte dati.comune.milano.it/gtfs.zip, CC-BY): 5 linee metro (route_type 1), 7.884 corse, 130 fermate fisiche -> 125 stazioni. `scripts/07_gtfs_metro.py` -> `pulito/gtfs_metro_servizio_giorno.csv` (data, linea, corse, prima e ultima partenza), `pulito/gtfs_metro_stazioni.csv`. **È solo l'orario di oggi: nessuno storico.**

### 2.6 Regione Lombardia - dati.lombardia.it - CC0
Frequentazione delle **stazioni ferroviarie**, misurata da Trenord, "viaggiatori saliti" per giorno medio di ciascuna campagna di rilevazione, arrotondati a 10:
- `m2u2-frtq` "Flussi Stazioni Ferroviarie" (dati 2015-2023, 4.073 righe in tutta la Lombardia): solo giorno feriale; novembre di ogni anno + luglio 2023.
- `ut63-s688` "Frequentazione delle stazioni del servizio ferroviario regionale" (6.930 righe, 2024-2025): maggio, luglio, novembre; feriale, sabato, festivo.
- Tenuto il comune di Milano: 25 stazioni, 685 righe (`pulito/stazioni_treno_milano_frequentazione.csv`; `scripts/05_download_trenord.py`, `09_trenord_pulito.py`). **Non sono stazioni della metropolitana**: Cadorna, Centrale, Garibaldi, Lambrate, Rogoredo, Porta Genova, Romolo, Dateo, Forlanini, San Cristoforo, Repubblica, Porta Venezia hanno però una stazione metro accanto o sono interscambi. Cosa manca: gli scesi (solo 7-9), il metro che si usa dopo il treno.
- Altri dataset Regione Lombardia toccati dalla ricerca (`Dati Agenzie TPL`, `Matrice OD2016`): bilanci delle agenzie e matrice origine-destinazione 2016, non ingressi di stazione: non scaricati.

### 2.7 Cose cercate e non trovate
Agenzia TPL Milano / ISTAT / Eurostat: nessun dato di ingressi per stazione. RFI pubblica la frequentazione delle sole stazioni RFI (citata nella bibliografia del Report, non scaricata). ATM "open data" come portale: non esiste (solo le schede del Comune). L'edizione 2025 del Report AMAT in PDF: non trovata. Nessun comunicato ATM con ingressi nei giorni di sciopero, concerti a San Siro o Olimpiadi.

## 3. Tabelle pulite (`pulito/`)

| File | Contenuto | Righe | Chiave |
|---|---|---|---|
| `metro_passeggeri_linea_anno.csv` | anno, linea, passeggeri_mln, metodo, fonte, dove | 44 | linea+anno (M4 da 2022) |
| `metro_passeggeri_totale_anno.csv` | totali dichiarati nei testi (2015, 2017-2025) | 11 | anno+fonte |
| `atm_carta_mobilita_numeri.csv` | passeggeri rete ATM, corse metro, linee, km, stazioni | 10 | anno_dati |
| `report24_*.csv` | letture grezze dai grafici AMAT: metro per linea, TPL totale, Linate M4 mensile | 39 / 9 / 25 | |
| `stazioni_metro.csv` | 125 stazioni: linee, apertura per linea, coordinate GTFS, corse/giorno | 125 | stazione |
| `stazioni_wikipedia.csv` | stazione-linea con data di apertura | 134 | stazione+linea |
| `gtfs_metro_servizio_giorno.csv`, `gtfs_metro_stazioni.csv` | corse per giorno e linea (26/10-30/11/2026); 130 fermate | | |
| `stazioni_treno_milano_frequentazione.csv` | 25 stazioni ferroviarie: anno, mese, tipo giorno, saliti 24h, saliti e discesi 7-9, corse | 685 | stazione+anno+mese+tipo_giorno |
| `stazioni_treno_covid_ripresa.csv` | saliti nov feriale 2015-2025 per stazione, % 2020 e 2025 su 2019 | 24 | stazione |
| `riepilogo.json`, `riepilogo.txt` | tutti i numeri del paragrafo 4 | | |

## 4. Numeri principali (ogni numero: tabella e fonte indicata sopra)

**4.1 Passeggeri per linea e anno (mln; 2016-2024 da `report24_metro_linea_anno.csv`, 2025 da Wikipedia)**

| Anno | M1 | M2 | M3 | M4 | M5 | Totale |
|---|---|---|---|---|---|---|
| 2016 | 129,6 | 110,1 | 74,7 | - | 21,8 | 336,2 |
| 2017 | 130,9 | 112,6 | 76,2 | - | 24,5 | 344,2 |
| 2018 | 138,7 | 119,3 | 81,2 | - | 29,4 | 368,6 |
| 2019 | 144,4 | 123,6 | 84,7 | - | 32,2 | 384,9 |
| 2020 | 63,7 | 50,9 | 38,5 | - | 13,9 | 167,0 |
| 2021 | 78,0 | 63,0 | 47,2 | - | 17,5 | 205,7 |
| 2022 | 105,1 | 88,7 | 65,6 | 0,2 | 25,0 | 284,6 |
| 2023 | 120,5 | 100,5 | 75,2 | 4,5 | 29,0 | 329,7 |
| 2024 | 121,2 | 99,7 | 76,8 | 13,4 | 29,5 | 340,6 |
| 2025 | 118,0 | 93,5 | 76,5 | 34,5 | 29,9 | 352,4 |

**4.2 Linea più forte / più debole**: M1 è sempre la più usata (118,0 nel 2025, 33%); la M5, la più piccola delle storiche, è l'unica che nel 2025 sta quasi al livello del 2019 (-7,3%), seguita da M3 (-9,7%). M2 è la più lontana (-24,3%), M1 -18,3% (2025 su 2019).

**4.3 Giorno feriale / festivo**: ingressi metro per tipo di giorno: nessun dato. Come ripiego: (a) servizio GTFS, corse metro totali: feriale 2.770, sabato 2.386-2.430 (86-88%), domenica 1.729-1.787 (62-65%) (`gtfs_metro_servizio_giorno.csv`, due varianti di orario per M1 sabato e domenica); (b) stazioni ferroviarie di Milano, novembre 2025, somma di 25 stazioni, saliti: feriale 278.330, sabato 166.240 (60%), festivo 131.430 (47%) (`stazioni_treno_milano_frequentazione.csv`). Non sono ingressi in metro.

**4.4 Profilo orario**: non esiste per la metro. Per i treni solo 7-9 (saliti e discesi). Dal Report 2024, solo il carico sui tratti tra le 7 e le 9 (vedi 2.2).

**4.5 Più e meno frequentate (treni, feriale nov 2025, saliti)**: Cadorna 35.190, Centrale 29.800, Porta Garibaldi superficie 26.180, Bovisa 23.330, Porta Garibaldi Passante 19.760; ultime: Quarto Oggiaro 4.060, Tibaldi Bocconi 1.890, Porta Romana 1.050, Romolo 920, Bruzzano 490. Per la metro: l'unico numero per stazione è San Babila "circa 12.000 accessi al giorno" (Affaritaliani, ATM, 3/8/2023, vecchio e solo per il primo mese). Sul traffico di superficie, Report 2024 p. 97: fermate più usate Maciachini, Centrale, Lotto, Piazza Fontana, Piazza Duomo, Porta Genova, Romolo, Lodi, Vigentino (somma saliti+discesi 7-9).

**4.6 Covid, per linea (2020 e 2025 su 2019)**: M1 -55,9% / -18,3%; M2 -58,8% / -24,3%; M3 -54,5% / -9,7%; M5 -56,8% / -7,3% (`riepilogo.txt`, punto 2). Rete ATM metro+superficie: 806,5 → 351,9 mln nel 2020 (-56,4%; identico al -56,4% del bilancio 2020, pdf p. 71, che confronta 358,1 con 820,4 mln del gruppo in Italia; il bilancio 2020 a p. 17 scrive anche -40% per M1 e M2 sul 2019 come media dell'anno). Stazioni ferroviarie di Milano, novembre 2020 su novembre 2019: somma 22%, da 14% (Greco Pirelli) a 38% (Certosa).
Tabella completa per stazione: `pulito/stazioni_treno_covid_ripresa.csv`. Oltre il 100% nel 2025: San Cristoforo 180% (interscambio M4), Quarto Oggiaro 131%, Forlanini 113%, Affori 109%.

**4.7 Effetto della M4 sulle vicine**: non si può dire per stazione (nessun dato). Per linea vedi il punto 4 del paragrafo 1: variazione 2024→2025 M1 -3,2, M2 -6,2, M3 -0,3, M5 +0,4, M4 +21,1 mln. Altra lettura: M1+M2+M3 salgono dal 2022 (259,4) al 2024 (297,7) e scendono nel 2025 (288,0). Sulla M4: Linate (grafico mensile) passa da 71 mila a dicembre 2022 a un massimo di 354 mila a novembre 2024; un buco di 16 mila a giugno 2023 e uno minore (160 mila) a luglio 2024; il report non spiega la causa. Il tratto Dateo-San Babila apre il 4/7/2023 (Wikipedia): ipotesi di chiusura per lavori, da verificare.

**4.8 Giorni di evento, Olimpiadi, scioperi**: nessun dato. Segnalo i giorni da prendere in considerazione quando ci sarà un dato: scioperi ATM del 2026 (15/1, quarto sciopero in quattro mesi e mezzo il 15/5: Il Fatto Quotidiano 15/5/2026), Olimpiadi invernali 6-22/2/2026 (Trenord: 13,9 milioni di passeggeri in più in tutta la Lombardia, 6 milioni sulle suburbane di Milano: comunicato citato da SaronnoNews, non verificato).

**4.9 Rete e servizio**: 5 linee, 111,3 km, 134 stazioni-linea = 125 stazioni distinte (9 di interscambio), 3.261 corse al giorno in media nel 2025 (Carta ATM 2026, pdf p. 11). Stazioni aperte per anno (Wikipedia, righe stazione-linea): 21 nel 1964, picchi 1990-91 (+15), 2015 (+10), 2024 (+13); 2022-2024 +21 con la M4.

## 5. Trappole

1. **Non confondere "passeggeri" con "ingressi".** Il Report AMAT parla di passeggeri "conteggiati dai tornelli", cioè ingressi in rete: chi cambia linea dentro la stazione non viene contato di nuovo. Un viaggio = un ingresso, due linee = una sola. Così AMAT e il testo ATM del 2020 ("ingressi giornalieri in metropolitana ridotti a 100.000").
2. **Anno dei dati e anno della Carta.** Carta della Mobilità ATM 2026 = dati al 31/12/2025. La stampa ha scambiato gli anni: "Atm nel 2025 con 675 milioni" (in realtà è 675,0 = 2024; 2025 = 695,5).
3. **Totali diversi dello stesso anno, perché diverse definizioni**: 2019 = 806,5 mln (Carta, solo ATM Milano), 809,7 (grafico AMAT TPL), 830,8 (Il Giorno, metro 386,8 + superficie 444), 820,4 (bilancio 2020, tutto il gruppo in Italia). 2018: 775,9 (Carta) contro 789 (bilancio 2018, gruppo). Mai mescolare le serie.
4. **134 stazioni o 125?** 134 sono stazioni-linea (38+35+21+21+19): le stazioni di interscambio contano due volte. Distinte sono 125 (Wikipedia, GTFS e filone nomi-fermate). Duomo, Cadorna, Loreto, Lotto, Sant'Ambrogio hanno due fermate GTFS ciascuna. Le "stazioni" del Comune ds535 sono 130 fermate fisiche.
5. **Report 2024 AMAT: diritti riservati, 114 MB.** I numeri letti sono dati di fatto, ma il grafico è loro. Se la pagina li usa, cita AMAT e rifà il grafico dai numeri, non lo incolla. Il PDF in `raw/pdf/` non va nel repo pubblico (comunque niente git qui).
6. **I numeri del 2025 per linea vengono da Wikipedia**, a sua volta da un report che non ho visto. Se il Report 2025 verrà trovato, verificare M2 (-6,2 mln sul 2024) prima di scrivere che "la M4 ha tolto passeggeri alla M2".
7. **Passeggeri al giorno nel 2024: 1.244.700** per la metro (Report AMAT, pdf p. 40). 341 mln ÷ 365 = 934 mila: il primo numero deve essere una media dei feriali, ma non è scritto. Non usarlo come media annuale.
8. **Le corse GTFS (2.770 in un feriale) non coincidono con "3.261 corse al giorno" della Carta 2026** (media annuale di lunedì-venerdì invernali): scarto 18%, causa non spiegata nei dati. Il GTFS ha anche M4 sabato (554) maggiore del feriale (472) e due varianti di orario per M1: non ho cercato la causa.
9. **Trenord**: arrotondato a 10; solo saliti in 24 ore; "Fer" e "Feriale" sono la stessa cosa; i nomi cambiano tra le due tabelle (Cadorna è "MILANO NORD CADORNA" prima e "MILANO CADORNA" dopo; Bovisa cambia nome e passa a "BOVISA POLITECNICO"); "Porta Garibaldi" sono due stazioni (superficie e Passante, per la tabella 2024-2025 "SOTTERRANEA"): ho tenuto i nomi separati. Novembre 2020 era in piena seconda ondata. La ripresa ferroviaria dipende anche dall'offerta (lavori, linee S, Cadorna): non è domanda pura.
10. **Linate M4 mensile**: "passeggeri ingresso/uscita" della stazione Linate, non tutta la M4. Il grafico dice "migliaia".
11. **Dataset del Comune con difetti**: ds2952 ha tram 2025 = 38,8 km (copia filovia) e per il 2005-2012 conta 3 linee (74,6-82,8 km, include tratte fuori comune) mentre ds528 per lo stesso periodo ha 64,3 km (2013, solo dentro Milano) e ds2952 87,1: perimetri diversi. Non mescolare.
12. **Il Giorno e gli altri riportano il 2015 (346,2 mln)**: anno dell'Expo, che AMAT scarta come base.

## 6. Cosa può mostrare una pagina (e cosa no)

Si può mostrare, con dati veri:
- **La rete cresce, i passeggeri no**: una linea doppia (km di rete e mln di passeggeri, 2016-2025), con il Covid in mezzo e la M4 che compare. È la cosa più chiara dai dati.
- **Le cinque linee in un'area impilata 2016-2025** (Covid, ripresa lenta, M4 che entra).
- **Quando sono nate le 125 stazioni**: mappa con i punti colorati per anno di apertura (coordinate GTFS, date Wikipedia), cursore 1964-2024.
- **Linate M4 mese per mese**, da dicembre 2022: la ripida risalita, il buco di giugno 2023, il picco di novembre 2024.
- **Le stazioni ferroviarie di Milano, 2019/2020/2025** (manubri), dichiarando bene che sono treni: Cadorna non è tornata (73%), Centrale quasi (92%), San Cristoforo e Forlanini oltre il 100% con la M4.
- Servizio: corse al giorno per linea (feriale, sabato, domenica).

Non si può mostrare: la stazione più affollata della metro, il profilo orario, i feriali contro i festivi della metro, partite, concerti, Olimpiadi, scioperi. Per averli serve una richiesta ad ATM/AMAT (accesso civico: decide Davide, io non scrivo a nessuno). Un indizio indiretto per gli scioperi è la serie giornaliera degli ingressi in Area C già pulita nel filone area-c (`..\area-c\pulito\ingressi_giornalieri.csv`): se nei giorni di sciopero le auto aumentano, si vede lì, ma sarebbe un'ipotesi, non un conteggio dei passeggeri.

## 7. Cosa NON ho fatto
- Non ho scaricato RFI (frequentazione Centrale e altre stazioni RFI), Eurostat, ISTAT oltre ds1547, né le edizioni 2022 e 2023 del Report AMAT (non trovate in PDF).
- Non ho tradotto "ingressi per stazione" in una stima (nessun modello).
- Non ho cercato scioperi e partite uno per uno (non c'è un dato a cui agganciarli).
- Il PDF 2025 dell'AMAT e gli altri documenti ATM sono nel `raw/` (215 MB complessivi): da non copiare altrove.
