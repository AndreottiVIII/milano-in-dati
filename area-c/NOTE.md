# Area C (ingressi nel centro di Milano) - note sul download, fase 1

Data del download: 29/10/2026. Nessuna analisi fatta: solo scaricamento e controllo dei file.
Tutto in `area-c\raw\` (558 MB, 185 file). Scripts in `area-c\scripts\`. Controlli in `area-c\verifica\`.

## Fonte unica
Open data del Comune di Milano (CKAN): https://dati.comune.milano.it/api/3/action/package_search?q=area%20c
(ricerche fatte: area c, ecopass, area b, varchi, accessi, ztl, congestion, ingressi; il catalogo trovato e' in `raw\_catalogo\catalogo.json`).
Gestore dei dati: AMAT (Agenzia Mobilita' Ambiente Territorio). Licenza di tutti i 175 dataset scaricati: **CC-BY (Creative Commons Attribution)**.
Si possono ripubblicare anche i dati grezzi, citando "Comune di Milano / AMAT" come fonte.
Nessuna registrazione o clic di licenza richiesti. Nessun errore di download (`raw\_download_log.tsv`).

## Cosa c'e' (tre serie diverse, con livelli di dettaglio diversi)

### A. 01/01/2012 - 18/09/2016: serie "vecchia", solo aggregata (niente varchi)
- 5 anni x 7 tipi di tabella x 2 (giornaliere ds779-ds813, "orarie" ds814-ds848). I tipi: totale, per classe Euro, per categoria veicolo (persone, merci, bus, altro, NC), per autorizzati/non autorizzati, per residenti/non residenti, per alimentazione, per veicoli di servizio.
- File: `raw\ds779_...` ... `raw\ds848_...` (CSV; i JSON uguali non sono stati scaricati).
- Le tabelle "orarie" sono in realta' **a mezz'ora** (campo `data` + `timeIndex` 00:00, 00:30, ...; 48 righe al giorno). I giornalieri hanno `timeIndex` (data) e `totale`; il campo `areac` = 1 se Area C era attiva in quel momento.
- Controllo: per ogni anno la somma dei giornalieri `totale` e' identica alla somma delle mezz'ore `totale` (es. 2012: 46.601.227 transiti in entrambi).

### B. 01/09/2016 - 31/12/2018: ds1085 (solo totale giornaliero)
- `raw\ds1085_area-c-accessi-giornalieri-2016-2018\ds1085_ingressi_areac_precedenti.csv`: 850 righe, campi `data_giorno`, `numero_transiti_giornalieri`.

### C. 09/2016 - 11/2024: file mensili, a mezz'ora e PER VARCO
- 99 zip, uno per mese (ds862-ds896, ds899-ds958, ds1070-ds2885), da settembre 2016 a novembre 2024, mesi tutti presenti. Ognuno contiene un CSV con le colonne: `dataora, id_varco, esenti, moto, residenti, veicoli_servizio, categoria_euro, tipologia_alimentazione, categoria_veicolo, classe_areac, fap, areac, numero_transiti` (13 colonne, uguali in tutti i mesi). Una riga = una mezz'ora x un varco x una combinazione di caratteristiche del veicolo; `numero_transiti` = quanti passaggi. 0,6-1,6 milioni di righe al mese, 5-7 MB per zip.
- I codici dei campi sono decodificati in `raw\ds861_area-c-decodifica-dei-campi\ingressi_areac_decode.csv` (es. categoria_veicolo: 1 altro, 2 bus, 3 merci, 4 persone; classe_areac: 1 autorizzati, 2 ecologici, 3 paganti residenti, 4 paganti di servizio, 5 altri paganti, 6 moto; categoria_euro 0-7; tipologia_alimentazione 0-14).
- Posizione dei varchi: `raw\ds82_varchi-area-c\ingressi_areac_varchi.csv` (+ geojson e shapefile): 42 varchi, `id_amat` 57-98, nome, longitudine, latitudine. **I dati mensili si collegano ai varchi**: `id_varco` mensile = `id_amat` (verificato: tutti gli id coincidono).
- Orario: `dataora` e' ora locale con scostamento (+01 inverno, +02 estate); nel giorno del cambio d'ora di marzo 2024 ci sono 46 mezz'ore, come atteso.

### D. Serie giornaliera ufficiale 2019-2024 (ds1072), due file
- `raw\ds1072_...\ingressi_areac_2019-2023_no_dic.csv`: 1781 righe, 01/01/2019 - 30/11/2023, solo totale (`numero_transiti_giornalieri`). Manca dicembre 2023 (da qui "no_dic").
- `raw\ds1072_...\ingressi_areac_2025-01-17.csv`: 305 righe, 01/12/2023 - 30/11/2024, con totale h24 e dettaglio autoveicoli / ciclomotori-moto, nelle fasce 7.30-19.30 (Area C attiva), 00.00-7.29 e 19.30-23.59.

### E. Altri dataset utili (piccoli)
- `raw\ds959_varchi-areab`: varchi di Area B (188 righe: nome, stato, atto autorizzativo, coordinate; 149 attivi e sanzionanti, 22 in pre-esercizio, 17 da programmare). Aggiornato 07/11/2023. **Non ci sono dati di accessi Area B.**
- `raw\ds51_aree-pedonali-e-ztl`: poligoni di aree pedonali, ZTL, Area C e Area B (aggiornato 02/05/2023). La riga di Area C ha solo `val_inizio` 2000-01-01 e `val_fine` 2050-01-01: **valori segnaposto, non la vera data di inizio**. Nessuna ordinanza o tariffa e' indicata.
- **Ecopass (2008-2011): nessun dataset trovato** nel portale (ricerca "ecopass" = 0 risultati). Il primo anno disponibile e' il 2012.

## Risposte alle domande della fase 1

**Granularita'.** Cambia negli anni. 2012 - 18/09/2016: totale per mezz'ora o per giorno, con spaccati per tipo di veicolo, ma senza varco. Dal 09/2016: mezz'ora x varco x caratteristiche del veicolo (file mensili). Serie ds1072 2019-2024: solo giornaliera.

**Copertura 2012 - 11/2024.**
- Serie A, giorni mancanti nei giornalieri: 2012 31/3 e 1/4 (2 giorni); 2014 6/2, 1/6 e 4-17/8 (16); 2015 dal 25/10 al 15/12 (52); 2016 dall'8/1 al 29/1 tranne il 28/1 (21). 2013 completo. Le tabelle "orarie" hanno gli stessi giorni vuoti (NaN o zero) piu' alcuni giorni a zero (es. 30/5/2015, 24/10/2015) e restano vuote dopo il 18/9/2016, anche se i file arrivano a fine anno.
- Dal 01/09/2016 i file mensili sono tutti presenti. Giorni senza nessun dato in nessuna serie: 27/01/2018, 29/07/2018, 20-26/12/2021, 25-31/12/2022 (16 giorni). La nota del dataset ds1072 dichiara solo gli ultimi due buchi (2021 e 2022).
- Nei file mensili mancano anche 27-31/01/2020, 17-23/02/2020, 20-26/06/2022, 13-19/11/2022, 19-25/02/2023, 21-27/05/2023: ci sono pero' nella serie giornaliera ds1072. Per avere una serie giornaliera completa vanno unite ds1085 + ds1072 + mensili.
- Il file ds1072 "nuovo" (12/2023-11/2024) manca di 61 giorni (2/5-1/6/2024 e 2-31/8/2024), presenti nei mensili.
- Dopo il 30/11/2024: **nulla**. Mancano tutto il 2025 e il 2026 (ds1072 aggiornato al 17/01/2025).

**Varchi.** 42 varchi (id 57-98) da 09/2016 a 05/2022. Da giugno 2022 i file mensili hanno 40 varchi: spariscono 87 (SANT'AGOSTINO) e 89 (OLIVETANI). Il file dei varchi li elenca ancora tutti e 42 (aggiornato 25/10/2026) e non dice quando sono stati tolti.

**Date di cambio delle regole.** Nessun dataset le elenca. Pagina ufficiale citata dai dataset: https://www.comune.milano.it/aree-tematiche/mobilita/area-c (non consultata). Da verificare con fonti ufficiali prima di usarle: avvio di Area C (gennaio 2012), eventuali cambi di tariffa e divieti per classe Euro.

## Trappole dei dati
1. **Rottura di livello nel 2016.** Fino a fine 2015 la serie A ha una media di circa 130.000-140.000 transiti/giorno (campo `totale`; con agosto piu' basso). Da gennaio 2016 la stessa serie scende a circa 45.000 (tutte le categorie, anche merci e bus, calano di circa 3 volte). Nei 18 giorni in comune (1-18/9/2016) la serie A dice 43.179 al giorno in media contro 162.262 di ds1085. Non spiegato nei dataset: probabilmente conteggio parziale (pochi varchi o solo alcuni transiti) da gennaio a settembre 2016. **Non unire la serie A del 2016 al resto senza correggerla.**
2. Agosto e' ovunque molto basso (es. agosto 2012: 73.921 al giorno contro circa 137.000 dei mesi normali): e' reale, non un buco.
3. Le tabelle "orarie" sono a mezz'ora.
4. La somma dei mensili coincide con le serie giornaliere (rapporto 0,999-1,02; identico per il ds1072 nuovo). Scarti oltre l'1% in 6 giorni di ds1085 (dic 2017-mar 2018) e 23 giorni del ds1072 vecchio (soprattutto 2020). Vedi `verifica\` e script 04.
5. Formati diversi: nei mensili 2024 i numeri sono tra virgolette, nei mensili 2020 la data ha le barre (`2020/03/01`), negli altri i trattini; nei file mensili 2016-2018 `id_varco` e' senza virgolette.
6. Il ds1072 dice che "dall'anno 2024" c'e' il dettaglio auto/moto, ma la colonna `moto` esiste nei mensili da sempre. Il totale ds1072 comprende moto e ciclomotori.
7. File non scaricati di proposito: i JSON identici ai CSV dei dataset 2012-2016.
8. Il portale segna "ultima modifica" 08/05/2026 per quasi tutti i dataset, ma i dati finiscono nel 2024: la data di aggiornamento non indica nuovi dati.

## File di controllo
`verifica\copertura_mensili.csv` (per mese: righe, giorni, varchi, transiti, giorni mancanti; le colonne `dt`, `n`, `day` non ci sono: la colonna `col` e' 16 perche' include 3 campi di servizio aggiunti dal controllo, il file originale ne ha 13), `verifica\varchi_per_mese.csv`, `verifica\giornaliero_da_mensili.csv` (totale, moto, auto per giorno sommando i varchi, 2016-2024).
Script: 01_catalogo.py (catalogo), 02_scarica.py (download, riprendibile), 03_verifica.py, 04_confronto_giornaliero.py.

# FASE 2 (29/10/2026): pulizia e prima pagina

Cartella `pulito\` (dati puliti), script 05-08 in `scripts\`, pagina in `..\docs\area-c\`. Regole delle trappole: vedi `pulito\problemi.md` (con tutti i numeri).

## Cosa c'e' in `pulito\`
- `ingressi_giornalieri.csv`: un giorno per riga, dal 1/9/2016 al 30/11/2024 (3.013 giorni). Colonne: `totale` (serie ufficiale: ds1085 fino al 2018, ds1072 dal 2019), `serie`, `fonte_dataset`, `flag`, `tot_mensili` (somma dei varchi), e il dettaglio dai file mensili (tipo di veicolo, autorizzati, residenti, servizio, categoria, classe Area C, Euro, alimentazione, FAP). 61 giorni del 2024 vengono dai mensili; 16 giorni non hanno nessun dato.
- `ingressi_giornalieri_2012-2016_conteggio_diverso.csv`: la serie vecchia, **separata e non unibile** (vedi sotto).
- `ingressi_varco_giorno.csv`: giorno x varco (42 varchi; 40 dal 30/5/2022). La somma dei varchi coincide con il totale dei mensili.
- `varchi.csv` (nome, posizione, primo/ultimo giorno, medie), `calendario.csv` (festivi, agosto, Natale, feriali), `eventi.csv` (date delle regole e del Covid con link, "da verificare"), `stazioni_aria_vicino_areac.csv` (per il confronto futuro con l'aria), `tabella_*.csv` (le tabelle della pagina), `problemi.md`.

## La serie 2012-2015
Dal gennaio 2016 scende da circa 135.000 a circa 45.000 al giorno: e' il modo di contare, non il traffico. Nei 18 giorni in comune (1-18/9/2016) la serie vecchia dice 43.179 al giorno, quella ufficiale 153.474 (rapporto 0,28). Contro le sole autovetture dei mensili (125.133) il rapporto e' 0,345, quasi uguale per quasi tutte le categorie: sembra circa un terzo delle auto, senza le moto. Non e' un sottoinsieme di varchi. Non e' stato applicato nessun fattore. Non si sa se il 2012-2015 includesse le moto: da chiedere ad AMAT.

## Prime cifre (solo numeri, nessuna causa)
- Feriali di settembre-novembre: 163.933 al giorno nel 2017, 163.981 nel 2019, 137.788 nel 2024 (meno 16% sul 2017 e sul 2019). Totale con le moto.
- Aprile 2020: 40.072 al giorno nei feriali contro 153.559 di aprile 2019. Settembre-novembre 2021: 93% del 2019.
- Feriali di agosto: circa meta di un feriale normale. Ferragosto: 26%.
- Varco piu usato: Turati (11.828 al giorno). I primi 5 varchi: 31% del totale (2019).
- Profilo orario: picco alle 8.30 (2019) e alle 9.00 (2023).

## Cose da sapere
- Il campo `areac` dei mensili e' il calendario regolamentare (7.30-19.30 dei feriali), non dice se Area C era davvero sospesa nel Covid. Le date di sospensione vengono da giornali e siti (il sito del Comune blocca i programmi): 11-12/3/2020 - 15/6/2020 e 5/11/2020 - 24/2/2021 (poi orario 10-19.30 fino al 9/6/2021). Tutto "da verificare" in `eventi.csv`.
- Il lockdown 9/3-3/5/2020 viene dal mandato, non da un atto.
- Scioperi dei trasporti: nessuna lista aperta trovata, saltati.
- Confronto con l'aria (fase 3, non fatto): nessuna stazione fuori dall'Area C sta entro 1 km dal confine; dentro: via Senato (573 m dal confine) e Verziere (837 m); entro 1,5 km: viale Liguria, via Juvara (chiusa 2007); le altre come controllo, piu 15 stazioni ARPA dell'hinterland.
- Pagina: `docs\area-c\index.html` (grafici in SVG, mappa Leaflet, tabelle). Dati del sito: 1,5 MB in `docs\area-c\data\`. Provata sul server "milano-in-dati" (porta 8796), nessun errore in console.

Ripetere la pulizia: `python -I scripts/05_aggrega_mensili.py raw pulito/_agg` (3-4 minuti), poi `06_giornaliero_calendario.py raw pulito`, `07_serie_vecchia.py raw pulito`, `08_varchi_tabelle_sito.py . ..\docs\area-c\data ..\aria`.
