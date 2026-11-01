# Affitti brevi a Milano: note sulla fase 1 (fonti, scaricamento, pulizia, riepilogo)

Data: 1 novembre 2026. Cartella: `affitti-brevi\`. Nessuna pagina web (e' solo la fase 1). Nessun git, `JOURNAL.md` e `docs\` non toccati.
Come leggere: ogni numero dice da quale file e da quale campo viene. Tutti i programmi sono in `scripts\` (comandi in `STATO.md`); i numeri del testo sono stampati da `out\riepilogo.txt` (programma 05) e `out\crescita.txt` (programma 06).
Nessun account creato, nessuna richiesta d'archivio per modulo o mail, nessun accesso aggirato. Pause di 2-3 secondi tra i download, User-Agent dichiarato.

## In breve

1. **Inside Airbnb ha per Milano 4 snapshot liberi** (26/12/2025, 27/03/2026, 25/06/2026, 19/09/2026). L'ultimo ha **25.338 annunci**: 22.309 case intere (88,0%), 2.948 stanze private (11,6%), 57 stanze condivise, 24 camere d'hotel. Licenza CC BY 4.0, ma le regole della comunita' dicono "non ripubblicare i dati" (vedi sotto).
2. **Lo snapshot di marzo 2026 e' incompleto** (18.835 annunci, un solo giorno di scarico; 5.562 dei 7.958 annunci "spariti" tra dicembre e marzo tornano a giugno). Non e' un calo vero.
3. **Il registro nazionale dei CIN e quello regionale dei CIR NON sono aperti.** Aperti ci sono solo conteggi aggregati: PoliS-Lombardia/ISTAT e Comune di Milano (strutture "extra-alberghiere", case vacanza, locazioni turistiche, strutture dell'imposta di soggiorno).
4. **Crescita:** le strutture extra-alberghiere ISTAT di Milano passano da 4.266 (2019) a 29.973 (2025), x7,0. Gli annunci Airbnb con almeno una recensione nell'anno: da 2.775 a 16.759, x6,0. I due indicatori si muovono insieme.
5. **Dove stanno:** 3,06 annunci ogni 100 abitazioni in tutta la citta' (2,70 case intere). Duomo 12,3 per 100, Stazione Centrale-Ponte Seveso 10,2, Porta Garibaldi-Porta Nuova 8,7, Brera 7,5.
6. **Host:** il 79,0% degli host ha 1 solo annuncio, ma il 64,2% degli annunci e' in mano a host con 2 o piu' annunci; 139 host (1,2%) con 20 o piu' annunci tengono il 29,9% degli annunci. Il piu' grande ne ha 468.
7. **Prezzo:** mediana di una casa intera 174,6 euro a notte (quotazione di settembre per 1-7 notti), 144,0 a giugno. **Attenzione: e' una quotazione per date precise, non un prezzo medio** (vedi trappole).
8. **Notti per un affitto:** con affitto OMI di una casa di 60 mq servono in mediana 5,8 notti al mese (quartile 4,4-7,3). Ma la casa intera mediana ha solo 30 notti occupate stimate in 12 mesi.

## 1. Fonti, una per una

### 1.1 Inside Airbnb (insideairbnb.com)
- **Pagina letta il 1/11/2026:** `https://insideairbnb.com/get-the-data/` (salvata in `raw\pagine\get-the-data.html`). `robots.txt` blocca solo il crawler `ia_archiver` sulla pagina `/get-the-data`; i file si scaricano da `data.insideairbnb.com`.
- **Licenza, parola per parola** (pagina get-the-data): "This data is licensed under a Creative Commons Attribution 4.0 International License." Il sito (non i dati) e' CC0 di Murray Cox.
- **Regole della comunita'** (`raw\pagine\data-policies.txt`): "Do not republish the data. We think this site provides the best context for the data." e "Inside Airbnb data should be attributed and cited appropriately". Chiedono anche di scaricare i dati una volta, non a ogni analisi. **Conseguenza:** nel repo pubblico vanno solo programmi e risultati aggregati; MAI `raw\`, `annunci_snapshot.csv`, `recensioni_per_annuncio.csv` (tabelle per singolo annuncio, con coordinate e codice host). Scelta prudente: la licenza CC BY di per se' permetterebbe la ripubblicazione con attribuzione, ma la richiesta della comunita' e' esplicita. Citare: "Inside Airbnb (insideairbnb.com), Milan, snapshot ... , CC BY 4.0".
- **Metodo** (`raw\pagine\data-assumptions.txt`, pagina del 1/11/2026): dati pubblici dal sito Airbnb, compreso il calendario dei 365 giorni futuri e le recensioni; ogni annuncio e' una fotografia a una data, perche' gli annunci possono essere cancellati; la posizione e' anonimizzata da Airbnb entro 0-450 piedi (150 m); il calendario non distingue notte prenotata da notte bloccata dall'host; i quartieri sono assegnati confrontando le coordinate con i confini della citta'. **Modello di occupazione** ("San Francisco Model"): tasso di recensione 50% per passare da recensioni a prenotazioni; soggiorno medio 3 notti (o il minimo di notti se piu' alto); occupazione con tetto al 70%. Il dizionario dei campi e' in `raw\pagine\dizionario.csv` (Google Sheet citato dal sito).
- **Snapshot liberi sulla pagina:** il sito mostra solo l'ultimo; gli altri 3 sono sotto "show archived data" e si trovano nel file dati della pagina (`raw\pagine\sq3176684073.json`, campo `datasets` con city=Milan: 4 date). Tutti e 4 scaricati. Non ho fatto richieste di dati d'archivio.
- **File scaricati** (cartelle `raw\insideairbnb\<data>\`): `listings.csv.gz`, `reviews.csv.gz`, `calendar.csv.gz`, `neighbourhoods.csv`, `neighbourhoods.geojson`. Scaricati il 1/11/2026 tra le 18:58 e le 18:59 (dimensione totale 629 MB; elenco con byte e righe in `pulito\inventario_fonti.csv`). Non scaricati i `listings.csv`/`reviews.csv` "sintetici" (ripetono i file dettagliati).

| Snapshot | Annunci (righe) | Host distinti | Scarico (`last_scraped`) | Recensioni nel file | Con prezzo |
|---|---|---|---|---|---|
| 2025-12-26 | 24.107 | 11.726 | 26/12/2025-05/01/2026 | 1.043.997 | 0 (campo vuoto) |
| 2026-03-27 | 18.835 | 9.110 | 27/03/2026 (1 giorno) | 939.621 | 0 (campo vuoto) |
| 2026-06-25 | 25.750 | 11.745 | 25/06-03/07/2026 | 1.148.401 | 22.937 |
| 2026-09-19 | 25.338 | 11.475 | 20-21/09/2026 | 1.171.528 | 21.654 |

(fonte: `pulito\snapshot_controlli.csv`, `pulito\riepilogo_snapshot.csv`, `out\log_03.txt`). Il file `calendar.csv.gz` ha solo `listing_id, date, available, minimum_nights, maximum_nights` (nessun prezzo): 9,2 milioni di righe per l'ultimo snapshot, non usato in questa fase.
- **Cosa manca:** nessuno storico prima di dicembre 2025 (serve richiesta d'archivio); `host_since` e' vuoto in TUTTI e 4 gli snapshot (non si puo' datare l'ingresso degli host); niente prezzi nei primi due snapshot; nessun altro portale (Booking, Vrbo, annunci diretti): Airbnb e' solo una parte del mercato.

### 1.2 Open data Regione Lombardia (dati.lombardia.it, Socrata)
- **Cercato nel catalogo** (`https://dati.lombardia.it/api/catalog/v1`, programma `01_cerca_catalogo.py`, 1/11/2026) con: strutture ricettive, locazioni turistiche, CIR, CIN, affitti brevi, case vacanza, alloggi, ricettiv*, turismo. **Nessun elenco di singole strutture con codice CIR o CIN a Milano.** Esistono schede "Bed and Breakfast" (jzsu-f86x), "Affittacamere" (6var-2hht), "Strutture Alberghiere e RTA" (fiiw-i5su) con solo denominazione, comune, sito, email, ma il catalogo le elenca (aggiornate 19/09/2024) e i dati NON si aprono: l'API risponde "Cannot find view" / 404 (1/11/2026). Non ho cercato di aggirare nulla.
- **Scaricati (Milano, filtro `comune='Milano'`, codice ISTAT 15146)**, in `raw\opendata\lombardia\`:
  - `2724-d4dt` "Strutture turistiche nei comuni lombardi": anno, tipo struttura (alberghiere / extra-alberghiere / totale), numero strutture, numero letti, capienza media; 2019-2025; 21 righe per Milano. Attribuzione "Polis Lombardia - ISTAT"; dati aggiornati sul portale il 22/10/2026 (metadato "ultima modifica" 19/09/2025). Gli esercizi extra-alberghieri sono definiti nella scheda: campeggi e villaggi, **alloggi in affitto a gestione imprenditoriale**, agriturismi, ostelli, case per ferie e altre strutture, rifugi, **bed and breakfast e altri alloggi privati**.
  - `vyxt-7jdx` "Flussi turistici nei comuni lombardi": arrivi e presenze per tipo, cittadinanza e anno, 2019-2025 (63 righe per Milano; numeri con virgole delle migliaia, da pulire).
  - `mzxz-sz25` "Flussi turistici mensili": arrivi e presenze per mese, 2019-2025, per Milano solo il tipo "Totale" (84 righe); non usato.
- **Licenza:** il portale non la indica per questi dataset ("La licenza di questo set di dati non e' stata specificata"). Per sicurezza: citare PoliS-Lombardia/ISTAT, pubblicare solo i numeri aggregati (gia' pubblici), non ripubblicare i file grezzi senza averlo verificato.
- Il tetto: PoliS pubblica i comuni con almeno 4 strutture.

### 1.3 Open data Comune di Milano (dati.comune.milano.it, CKAN)
Cercato con l'API `package_search` (1/11/2026): imposta di soggiorno, strutture ricettive, alloggi turistici, affitti brevi, locazioni turistiche, airbnb, CIR. Scaricati in `raw\opendata\comune_milano\`:

| Dataset | Contenuto | Righe | Licenza | Ultima modifica scheda |
|---|---|---|---|---|
| `ds2955` strutture attive e posti letto per tipologia, serie storica | per anno: alberghiere (AL, dal 2012), extra-alberghiere classiche (EA, dal 2014), **locazioni turistiche (LT, "cd. Affitti brevi", dal 2020)**, **case e appartamenti per vacanze (CAV, dal 2014)**; esercizi attivi e posti letto; fino al 2025 | 44 | CC BY | 30/06/2026 |
| `ds593` strutture turistiche nel comune di Milano | stessi numeri di PoliS/ISTAT (2019-2025) | 21 | CC0 | 27/10/2026 |
| `ds500` imposta di soggiorno: n. strutture accreditate 2019-2024 | per trimestre | 6 anni | CC BY | 8/4/2025 (file) |
| `ds477` idem 2015-2018 | per mese | 48 | CC BY | 16/4/2019 (file) |
| `ds478` soggetti passivi ed esenti dell'imposta 2014-2024 | persone paganti ed esenti | 11 | CC BY | 8/4/2025 (file) |
| `ds216` strutture ricettive per tipologia 2002-2018 | include B&B, alloggi; dati da Regione Lombardia | 177 | CC BY | 19/11/2019 (file) |
| `ds213` presenze per provenienza 2005-2025 | non usato qui | 1.176 | CC BY | 27/10/2026 |

Mancano: nessun elenco di singole strutture, nessun indirizzo; la scheda `ds2955` non dice da quale registro vengano "le strutture attive" (CIR? comunicazioni dei Comuni?).

### 1.4 Registro nazionale CIN (BDSR, Ministero del Turismo)
**Non e' aperto.** Il CIN si chiede e si consulta nella Banca Dati delle Strutture Ricettive con SPID (ricerca di fonti 1/11/2026: Regione Abruzzo, Provincia di Trento, ecc.: il CIN presuppone il CIR; scadenza 1/1/2025). Non ho trovato nessun elenco scaricabile. Non ho provato a interrogare la verifica pubblica un codice alla volta (sarebbe uno scraping). In alternativa, il campo `license` di Inside Airbnb contiene i CIN dichiarati dagli host (sezione 5).

## 2. Pulizia (`pulito\`)
- `annunci_snapshot.csv`: 94.030 righe (un annuncio per snapshot), colonne essenziali; **tolti nomi, descrizioni, URL, foto, nome e testo dell'host** (dati personali non necessari). Contiene `host_id`, coordinate e il NIL. LOCALE, non per il repo pubblico.
- **Assegnazione ai NIL:** punto-in-poligono con i poligoni dei 88 NIL gia' su disco (`citta-15-minuti\out\nil_poligoni_punteggi.geojson`, ID_NIL e nome; stessi del JOURNAL sez. 9). **Tutti i 94.030 annunci cadono dentro un NIL** (nessuno "vicino" o "fuori"). Il NIL di Inside Airbnb (`neighbourhood_cleansed`) ha gli stessi confini ma altri nomi (per esempio "NAVIGLI" invece di "Porta Ticinese - Conchetta"): il 99,93% degli annunci cade nella stessa coppia NIL-nome Airbnb. 87 NIL su 88 hanno almeno un annuncio.
- **Assegnazione alle zone OMI** (`docs\prezzi-case\data\zone.geojson`, 42 zone): dentro 25.296 su 25.338 annunci a settembre; 15 entro circa 200 m; 27 fuori (non usati nel confronto).
- Codici licenza classificati in `licenza_tipo`: formato CIN valido (IT + 6 cifre + lettera + cifra + 8 caratteri), richiesto-non-ricevuto, esente, altro testo, assente.
- Altre tabelle: `riepilogo_snapshot.csv`, `host_concentrazione.csv`, `nil_riepilogo.csv`, `prezzi_distribuzione.csv`, `licenze_per_snapshot.csv`, `confronto_affitto_notti.csv` e `_zone.csv`, `recensioni_anno.csv`, `recensioni_mese.csv`, `recensioni_nil_anno.csv`, `crescita_confronto.csv`, `crescita_nil.csv`, `ufficiale_strutture_milano.csv`, `ufficiale_flussi_milano.csv`, `inventario_fonti.csv`. Tutte aggregate (pubblicabili con attribuzione) salvo `annunci_snapshot.csv` e `recensioni_per_annuncio.csv`.

## 3. Quanti sono e dove (snapshot 19/09/2026)
Fonte: `pulito\annunci_snapshot.csv`, campi `room_type`, `host_id`, `nil_id`; abitazioni: `censimenti\pulito\indicatori_NIL.csv`, anno 2023, campo `abit_tot`.
- 25.338 annunci; 17.669 (69,7%) con almeno una recensione negli ultimi 12 mesi (`number_of_reviews_ltm`); 3.664 mai recensiti.
- **Per 100 abitazioni** (somma dei 88 NIL: 827.648 abitazioni; 722.273 occupate da residenti): 3,06 annunci; 2,70 case intere; 1,95 case intere con recensione negli ultimi 12 mesi (16.177 case); 3,09 case intere ogni 100 abitazioni occupate da residenti.
- Nei NIL con almeno 2.000 abitazioni e 2.000 residenti (69 NIL): mediana 2,22 per 100; 10 NIL con 5 o piu' per 100, 2 con 10 o piu'. Piu' alti: Duomo 12,3 (1.800 annunci), Stazione Centrale-Ponte Seveso 10,2 (1.169), Porta Garibaldi-Porta Nuova 8,7 (425), Brera 7,5 (1.062), Porta Ticinese-Conchetta 7,1 (961), Porta Ticinese-Conca del Naviglio 5,8 (952), Sarpi 5,5 (1.115), Isola 5,3 (793). Piu' bassi: Bovisasca 0,35, Quarto Oggiaro-Vialba-Musocco 0,39, Gratosoglio 0,41, Baggio 0,43. I 10 NIL piu' densi (non piccoli) contengono il 35,5% degli annunci.
- NIL con pochissime abitazioni: Parco Sempione (1 abitazione nel censimento, 29 annunci) e Giardini P.ta Venezia (29 abitazioni, 11 annunci) danno rapporti assurdi: colonna `piccolo_denominatore` in `nil_riepilogo.csv`; non vanno in classifica.

## 4. Chi e' l'host
Fonte: conteggio di `host_id` sui 25.338 annunci. Host totali 11.475.
| Annunci per host | Host | Annunci | Quota host | Quota annunci |
|---|---|---|---|---|
| 1 | 9.066 | 9.066 | 79,0% | 35,8% |
| 2 | 1.150 | 2.300 | 10,0% | 9,1% |
| 3-4 | 615 | 2.064 | 5,4% | 8,1% |
| 5-9 | 345 | 2.182 | 3,0% | 8,6% |
| 10-19 | 160 | 2.151 | 1,4% | 8,5% |
| 20 o piu' | 139 | 7.575 | 1,2% | 29,9% |

Annunci in mano a host con 5+: 47,0%; con 10+: 38,4%. I 10 host piu' grandi (468, 461, 433, 239, 173, 145, 145, 140, 135, 111) hanno 2.450 annunci (9,7%). Solo case intere: 62,8% in mano a host con 2+. Il conteggio `calculated_host_listings_count` di Inside Airbnb coincide con il mio per tutti gli host (differenza massima 0). Nomi degli host non registrati.

## 5. Licenza/CIN dichiarati dagli host
Fonte: campo `license`, `pulito\licenze_per_snapshot.csv`. 19/09/2026: CIN di formato valido 20.533 (81,0%); "richiesto ma non ricevuto" 486; esente 102; altro testo 366; assente 3.851 (15,2%). 98,8% dei CIN validi porta il codice ISTAT 015146 (Milano); 246 hanno codici di altri comuni (157 codici diversi). **1.228 CIN sono usati da piu' annunci** (3.401 annunci, 16,6%); il massimo e' 24 annunci con lo stesso CIN. Un CIN per piu' annunci puo' essere legittimo (palazzo, struttura con piu' unita') o un errore: non interpretato. Dopo il codice ISTAT la lettera e' C per 12.521, B per 7.773, A per 197 (significato non verificato). Il formato valido NON prova che il CIN esista nel registro.

## 6. Prezzi a notte
Fonte: campo `price` (+ `price_quote_*` da giugno 2026). Pulito in `prezzi_distribuzione.csv`.
Case intere, quotazione di 1-7 notti non mensile (euro):
| Snapshot | n | 5% | 25% | mediana | 75% | 95% | sopra 1.000 |
|---|---|---|---|---|---|---|---|
| 25/06/2026 | 17.904 | 85,5 | 114,0 | 144,0 | 194,0 | 370,8 | 183 |
| 19/09/2026 | 17.007 | 98,0 | 135,0 | 174,6 | 243,0 | 487,9 | 214 |
Stanze private (settembre): mediana 119,5 (n=1.871). Quotazioni mensili (>=28 notti, case intere): mediana 102,3 (n=2.017): sono prezzi al giorno di un affitto mensile scontato. Il 14,5% degli annunci di settembre non ha prezzo.

## 7. Crescita nel tempo (da recensioni, con limiti)
Fonte: `pulito\recensioni_anno.csv` e `crescita_confronto.csv`. Ho letto solo `listing_id`, `id`, `date` delle recensioni (non i testi); ho unito le recensioni dei 4 snapshot (1.312.056 recensioni distinte contro 1.171.528 nell'ultimo) per recuperare quelle di annunci spariti da dicembre.
- Recensione piu' vecchia: 20/12/2010. Prime recensioni dell'anno: 2012: 437; 2014: 3.888; **2015 (Expo): 15.810**; 2019: 58.385; **2020: 18.957**; 2022: 111.496; 2025: 307.639 (dati: unione 4 snapshot).
- Annunci con almeno una recensione nell'anno (unione): 2015: 1.002; 2019: 2.775; 2020: 2.468; 2022: 5.675; 2023: 8.548; 2024: 12.463; **2025: 16.759**.
- **Limiti (importanti):**
  1. **Solo i sopravvissuti:** le recensioni di un annuncio tolto dal sito spariscono dal file. Misura diretta: confrontando il file di dicembre 2025 con quello di settembre 2026, le recensioni del 2024 scendono da 236.626 a 208.430 (-11,9%) e gli annunci recensiti nel 2024 da 12.224 a 10.531 (-13,8%); anche il 2019 perde il 7,3% delle recensioni. Il passato lontano e' quindi sottostimato, e piu' si va indietro meno si vede (annunci dell'unione con prima recensione prima del 2015: 382; con recensioni anche nel 2026: 218).
  2. La recensione arriva dopo il soggiorno e solo una parte degli ospiti recensisce (il modello Inside Airbnb assume 50%).
  3. "Prima recensione" non e' la data di apertura dell'annuncio.
  4. Non vede gli annunci mai prenotati, ne' altri portali.
- **Confronto con i dati ufficiali (Milano, strutture):**
  | Anno | Airbnb: annunci recensiti nell'anno | ISTAT extra-alberghiere (strutture) | Comune: CAV + locazioni turistiche | Comune: accreditate imposta di soggiorno (fine anno) |
  |---|---|---|---|---|
  | 2019 | 2.775 | 4.266 | 7.435 | 4.945 |
  | 2021 | 3.374 | 6.928 | 8.695 | 5.424 |
  | 2023 | 8.548 | 16.690 | 16.649 | 10.365 |
  | 2025 | 16.759 | 29.973 | 24.155 | n.d. (2024: 13.406) |
  Le serie salgono insieme (x7,0 ISTAT e x6,0 Airbnb tra 2019 e 2025) ma **non sono la stessa cosa**: definizioni diverse, e l'ISTAT conta tutti i canali.
- Per NIL (`crescita_nil.csv`): negli annunci recensiti 2025/2019 il rapporto mediano e' 5,9 nei 29 NIL con almeno 30 annunci recensiti nel 2019 (da 4,4 Porta Genova a 9,1 Lodi-Corvetto). I tre NIL piu' densi pesano meno: 17,5% degli annunci recensiti nel 2019, 16,2% nel 2025 (la crescita si e' allargata, non concentrata).

## 8. Confronto con gli affitti lunghi (strand 12)
Fonte affitti: `docs\prezzi-case\data\zone_ultimo_semestre.csv`, campo `loc_centro` (euro per mq al mese, valori OMI per abitazioni civili, ultimo semestre 2026/1). **I valori OMI sono stime, non affitti reali**: sono spesso piu' bassi degli annunci (non verificato qui). Confronto, non prova.
- Metodo: 16.793 case intere con prezzo di 1-7 notti non mensile, fino a 1.000 euro (16.777 con zona OMI); affitto = `loc_centro` x 60 mq (ipotesi mia: la superficie non e' nel file); notti al mese = affitto / prezzo a notte. Risultato in `confronto_affitto_notti.csv`.
| Superficie ipotizzata | Affitto mediano | Notti al mese (mediana) | quartile 25-75% | annunci con meno di 10 notti |
|---|---|---|---|---|
| 40 mq | 680 euro | 3,9 | 2,9-4,9 | 99,6% |
| 60 mq | 1.020 euro | 5,8 | 4,4-7,3 | 94,5% |
| 80 mq | 1.360 euro | 7,7 | 5,9-9,8 | 77,0% |
- Per zona OMI (60 mq, `confronto_affitto_notti_zone.csv`): mediana delle zone 5,9 notti; da 4,1 (E6, E7) a 12,4 (C14 Porta Nuova, solo 67 annunci; C13 ne ha solo 6).
- **Il guadagno lordo non e' l'incasso netto:** commissioni della piattaforma, pulizie, biancheria, utenze, tassa di soggiorno, imposta (cedolare), vuoti. E la quotazione di settembre riguarda check-in del 21-28/09/2026 (possibile effetto della settimana della moda: non verificato), con prezzi forse sopra la media dell'anno.
- Occupazione stimata dal modello Inside Airbnb (campo `estimated_occupancy_l365d`): mediana delle case intere 30 notti in 12 mesi, media 68,5; 27,5% a zero. Nelle case intere con recensioni negli ultimi 12 mesi (14.395 con zona OMI, prezzo <=1.000) il ricavo mensile stimato (`estimated_revenue_l365d`/12, modello, lordo) ha mediana 918 euro contro un affitto OMI di 60 mq di 1.020: il 47,6% supera l'affitto.

## 9. La cosa piu' sorprendente
**Tra il 2019 e il 2025 tutta la crescita delle notti di turisti a Milano e' venuta dalle strutture extra-alberghiere.** Fonte: `vyxt-7jdx` (PoliS-Lombardia/ISTAT), campo `presenze`: alberghi 10.063.696 notti nel 2019, 9.415.893 nel 2025 (-6,4%); extra-alberghiere 2.882.369 nel 2019, 8.332.433 nel 2025 (x2,9). Le notti totali passano da 12.946.065 a 17.748.326 (+4,8 milioni): l'extra-alberghiero aggiunge 5,45 milioni, gli alberghi ne perdono 0,65. La quota di notti fuori dagli alberghi: 22,3% nel 2019, 29,5% nel 2022, **46,9% nel 2025**. Seconda sorpresa: 139 host (1,2%) tengono il 29,9% degli annunci Airbnb.

## 10. Trappole (verificate)
1. **Il prezzo e' in euro, anche se il campo scrive "$".** Lo dice il campo `price_quote_raw` (`"currency": "EUR"`, "1 night x €105.00"). Il simbolo e' solo formattazione di Inside Airbnb.
2. **Il prezzo e' una quotazione per date precise** (check-in del giorno dopo lo scarico, 1-2 notti per la maggior parte, 31 notti per 2.575 annunci con quotazione mensile scontata), non il prezzo medio dell'anno. Giugno (mediana 144) e settembre (174,6) non sono confrontabili: date diverse, forse un evento in citta' a fine settembre (non verificato). Prezzi fino a 88.100 euro (errori o ville): usare mediane e percentili, tagliare sopra 1.000 per i confronti.
3. **I primi due snapshot (dic 2025, mar 2026) non hanno prezzi** (campo vuoto); le colonne `price_quote_*` esistono solo da giugno 2026.
4. **Lo snapshot di marzo 2026 e' incompleto** (vedi In breve): non leggere il calo dic-mar come reale.
5. **Gli snapshot non sono scaricati nello stesso giorno:** dicembre copre 11 giorni (26/12-05/01), giugno 9 giorni.
6. **Passato che si erode:** le recensioni di un anno cambiano da snapshot a snapshot (-12% per il 2024 in 9 mesi). Non usare un solo file per la storia.
7. **Abitazioni del censimento:** dal 2021 i totali di `abit_tot` sono ricavati da registri (salto da 643.053 a 809.990 abitazioni, non e' edilizia: nota in `censimenti\NOTE.md`); le abitazioni "non occupate da residenti" sono molte nei NIL centrali (Duomo 2023: 5.732 su 14.679). Per questo il rapporto annunci/abitazioni va letto come ordine di grandezza.
8. **I nomi dei quartieri di Inside Airbnb non sono quelli dei NIL del Comune** (stessi confini, nomi diversi).
9. **Tre serie "ufficiali" sul numero di strutture, tre numeri diversi per il 2024:** ISTAT extra-alberghiere 24.166; Comune (CAV + locazioni turistiche) 22.637; strutture accreditate nell'imposta di soggiorno 13.406. Definizioni diverse e non spiegate nelle schede.
10. **Posti letto delle case vacanza (`ds2955`, CAV):** da 19.507 (2018) a 116.440 (2019) con strutture che passano da 3.452 a 7.435: i posti letto per struttura da 5,7 a 15,7. Probabile cambio di definizione o errore: non usare i posti letto CAV prima/dopo il 2019 insieme.
11. **Il CIN in formato valido non e' prova di regolarita'** (sezione 5) e quasi un annuncio su sei condivide il CIN con altri.
12. **PoliS: i campi numerici di `vyxt-7jdx` sono testo con virgole** (gia' puliti in `ufficiale_flussi_milano.csv`); la colonna `provincia` cambia da "MI" a "Milano" nel 2024; "totale/Totale" e "TOTALE" cambiano maiuscole.

## 11. Cosa potrebbe mostrare una pagina (fase 2)
1. Mappa dei 88 NIL con annunci per 100 abitazioni (con avviso per i NIL piccoli e per le abitazioni vuote), e cursore tra gli snapshot (giugno e settembre soli completi).
2. La curva della crescita: strutture extra-alberghiere ISTAT 2019-2025 con gli annunci Airbnb recensiti sovrapposti, e lo stacco del 2015 (Expo) e del 2020.
3. "Dove sono le notti": la quota di notti fuori dagli alberghi, 22% - 47%.
4. Chi affitta: 79% degli host con 1 annuncio, ma meta' degli annunci in mano a pochi.
5. Il conto del proprietario: notti al mese per pagare un affitto, per zona OMI, con grandi avvertenze (lordo, stime).
6. Una nota di metodo con tutte le trappole sopra. Nel repo pubblico solo tabelle aggregate e programmi.

## 12. Non fatto / da decidere
- Non ho letto `calendar.csv.gz` (solo disponibilita', niente prezzi) ne' i testi delle recensioni.
- Non ho confrontato con OpenStreetMap o altri portali.
- Da decidere con Davide: se chiedere a Inside Airbnb i dati d'archivio (serve una richiesta formale: non l'ho fatta); se usare le abitazioni 2021 o 2023 come denominatore; se riportare i prezzi solo da giugno/settembre.
