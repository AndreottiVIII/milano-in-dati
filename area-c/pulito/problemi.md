# Area C: registro dei problemi trovati nella pulizia (fase 2, 29/10/2026)

Ogni numero dice da quale file e campo viene. File in `area-c\pulito\`, script in `area-c\scripts\`.

## 1. La serie vecchia 2012 - 18/9/2016 NON si unisce alla nuova
- Fonte: `raw\ds779...ds783` (giornaliera, campo `totale`), `raw\ds814...ds818` (mezz'ora). Salvata a parte: `ingressi_giornalieri_2012-2016_conteggio_diverso.csv`.
- 2012-2015: media di 129.091 transiti al giorno (campo `totale`, 1.268 giorni con dato). Da gennaio 2016 la stessa serie scende a circa 45.000 (marzo 2016: 44.073 al giorno contro 139.554 di marzo 2015).
- Cosa succede in gennaio 2016: il 7/1 la serie conta 7.170 (giorno parziale), dall'8 al 27/1 non c'e' nessun dato, il 28/1 conta 10.317, poi riparte a circa 43.000. Sembra un guasto o un cambio del sistema di conteggio, non un calo del traffico.
- Prova decisiva nei 18 giorni in comune (1-18/9/2016, serie vecchia contro le somme dei file mensili per varco):
  - serie vecchia: 43.179 al giorno; ds1085 (ufficiale): 153.474; rapporto 0,28 (min 0,25, max 0,35; nei feriali 0,27, sabato-domenica 0,32);
  - contro le sole **autovetture** dei mensili (`moto` = 0): 125.133 al giorno; rapporto **0,345** (min 0,315, max 0,381, scarto tipico 6%). Il rapporto contro il totale con le moto e' piu' ballerino (11%): la serie vecchia non conta le moto.
  - Il rapporto 0,345 e' quasi lo stesso per quasi tutte le categorie: autorizzati 0,345, residenti 0,331, veicoli di servizio 0,347, merci 0,346, bus 0,351, Euro4 0,351, Euro5 0,345, Euro6 0,345, diesel 0,349. Fanno eccezione le caselle "non classificato" (NC): veicoli NC 0,144 e Euro NC 0,146 (nei mensili pesano il 22%, nella serie vecchia 2016 il 9%), e la benzina 0,275. Cioe' la serie vecchia dal 2016 sembra circa **un terzo delle autovetture** per ogni categoria (e un'altra classificazione dei veicoli non riconosciuti).
  - Non e' un sottoinsieme di varchi: una ricerca dei pesi (minimi quadrati non negativi, 864 mezz'ore del 1-18/9/2016 x 42 varchi) non da' pesi 0 o 1 e lascia un errore del 27%.
  - Lo stesso fattore circa 0,33 vale per tutte le mezz'ore del giorno (marzo-giugno 2016 contro 2015: 0,31-0,38), quindi il calo non dipende dall'orario.
- Conclusione: non esiste un rapporto stabile da applicare. Il fattore 0,345 vale solo per le autovetture, solo in settembre 2016, su 18 giorni. **Non e' stato applicato a nulla.** Se la serie 2012-2015 includa o no le moto non si capisce dai dati: il suo livello (settembre 2015: 136.698 al giorno) sta fra le sole autovetture di settembre 2016 (125.133) e il totale con le moto (162.262). Da chiedere ad AMAT.
- I campi `moto`/`areac` e le definizioni non sono spiegati in nessun dataset della serie vecchia (nemmeno nella decodifica `ds861`, che riguarda solo i mensili).
- Giorni mancanti nella serie vecchia (flag `mancante`): 91 (2012: 2; 2014: 16; 2015: 52; 2016: 21, cioe' 8-27 e 29/1/2016). Giorni parziali (flag `parziale_probabile`, valore sotto un quarto del normale per lo stesso giorno della settimana nelle 4 settimane intorno): 22 e 29/9/2013 (due domeniche, 14.396 e 13.088: 39 mezz'ore su 48 a zero), 24/10/2015 (16.368), 7/1/2016, 28/1/2016. I giornalieri coincidono con la somma delle mezz'ore (nessuna differenza in 1.268 giorni).
- Il campo `residenti` e' vuoto in alcuni giorni (2012: 13 giorni, 2014: 16, 2015: 52, 2016: 21): sono gli stessi giorni dei buchi.
- Agosto e' basso in tutti gli anni (agosto 2012: 73.921 al giorno), ed e' vero, non un buco.

## 2. Serie nuova (da 1/9/2016): come e' costruita e cosa non torna
- Spina dorsale: ds1085 (1/9/2016-31/12/2018), ds1072 vecchio (2019 - 30/11/2023), ds1072 nuovo, campo `totale_transiti_giornalieri_h24` (1/12/2023 - 30/11/2024). Nessun giorno doppio in nessuno dei tre (controllato).
- 3.013 giorni dal 1/9/2016 al 30/11/2024: 2.936 dalla serie ufficiale, 61 dalla somma dei mensili (flag `somma_mensili`: 2/5-1/6/2024 e 2-31/8/2024, mancanti nel ds1072 nuovo), **16 senza nessun dato** (27/1/2018, 29/7/2018, 20-26/12/2021, 25-31/12/2022; la nota del dataset ne dichiara solo due). Righe vuote tenute nel file, con flag `nessun_dato`.
- 40 giorni hanno solo il dato ufficiale e nessun file mensile (27-31/1/2020, 17-23/2/2020, 20-26/6/2022, 13-19/11/2022, 19-25/2/2023, 21-27/5/2023; flag `solo_ufficiale_senza_mensili`): per quei giorni mancano il dettaglio (tipo veicolo, Euro, ecc.) e i dati per varco.
- 29 giorni con scarto ufficiale-mensili oltre l'1% (flag `scarto_ufficiale_vs_mensili_oltre_1pct`): sempre l'ufficiale e' piu' alto, tra +1,0% e +2,1% (dic 2017-mar 2018, 2019, marzo-maggio 2020, 7-8/11/2020). Teniamo il valore ufficiale. Nei restanti 2.928 giorni lo scarto e' sotto l'1%.
- La somma dei transiti per varco coincide esattamente con il totale mensile giornaliero (controllo nello script 08).
- Il totale comprende le moto: nei feriali normali 2017-2019 le moto sono circa 30.000 su 158.000-162.000.

## 3. Il flag `areac` dei file mensili NON dice se Area C era sospesa
- Il campo `areac` vale 1 solo nelle mezz'ore 7.30-19.00 (cioe' fino alle 19.30) dei giorni feriali non festivi. Il giovedi' non ha orario ridotto in questo campo (una fonte, C40, parla di giovedi' fino alle 18: nei dati non si vede).
- Durante la sospensione Covid (marzo-giugno 2020, novembre 2020 - febbraio 2021) il campo continua a valere 1: e' il calendario regolamentare, non lo stato reale delle telecamere. Quindi "Area C attiva" non si puo' ricavare dai dati: le date di sospensione vengono da fonti pubbliche (vedi `eventi.csv`, stato "da verificare").
- Giorni feriali non festivi con campo `areac` a 0 (19): 27-30/12/2016, 2-5/1/2017, 9-10/2/2017, 14 e 16-18/8/2017, 13/10/2017, 22-23/2/2021, 25-26/7/2023. Nel calendario sono segnati ma non spiegati dai dati.

## 4. Covid e regole: fonti
- Il sito del Comune risponde 403 ai programmi: le pagine ufficiali (comune.milano.it) non sono state lette. Date prese da stampa e siti terzi, tutte "da verificare": sospensione 11/3/2020 (Mentelocale) o 12/3/2020 (Assolombarda), riattivazione 15/6/2020 (Sky TG24), seconda sospensione 5/11/2020 (ordinanza 53/2020 del 4/11, Assolombarda), riattivazione con orario 10.00-19.30 il 24/2/2021 (Mentelocale), orario pieno 9/6/2021 (Motorbox), ticket da 5 a 7,50 euro il 30/10/2023 (Sicurauto).
- Il lockdown nazionale 9/3-3/5/2020 viene dal mandato; l'ordine di grandezza dei dati e' coerente (marzo 2020: 65.873 al giorno nei feriali contro 155.441 di marzo 2019; aprile 40.072), ma la data esatta di inizio non e' stata verificata su un atto.
- Niente dati su domeniche aperte, estensioni di orario diverse da quelle sopra, o cambi di tariffa tra il 2012 e il 2023: non documentati.
- Scioperi dei trasporti: cercata una lista aperta (MIT, dati.gov.it) e non trovata. Saltati.

## 5. Dettaglio per tipo di veicolo: attenzione
- La quota "non classificato" (NC) cambia molto: categoria veicolo NC 21,2% nel 2016 contro 8,8% nel 2017 e 19,8% nel 2021; Euro NC 21,6% nel 2016, 9,4% nel 2017, 13,9% nel 2019, 21,8% nel 2021, 15,3% nel 2024 (`pulito\tabella_composizione_pct.csv`, feriali normali). Confrontare le singole classi Euro tra anni diversi senza guardare la quota NC puo' ingannare.
- Nei mensili 2016 e 2017 la quota di veicoli "ecologici" (classe_areac 2) e' 9,1% e 2,6%: le regole di esenzione sono cambiate (vedi evento 13/2/2017), non e' un errore.

## 6. Altre cose da sapere
- Nei giorni di passaggio all'ora legale (ultima domenica di marzo, 8 date) ci sono 46 mezz'ore; nei giorni di passaggio all'ora solare le mezz'ore 02.00-03.00 sono due volte nei dati e le tabelle per mezz'ora le sommano sotto la stessa etichetta (effetto trascurabile: 1 giorno l'anno).
- Formati diversi nei file (date con barre nel 2020, numeri tra virgolette nel 2024, fuso orario dopo la data nel ds1072): normalizzati in `YYYY-MM-DD`.
- Il 2016 (settembre-dicembre) e il 2024 (gennaio-novembre) non sono anni interi: per confrontare gli anni si usano i feriali di settembre-novembre, gli unici mesi presenti in tutti gli anni 2016-2024.
- Varchi: 42 varchi (id 57-98) fino al 29/5/2022; 87 (Sant'Agostino) e 89 (Olivetani) non compaiono piu' dal 30/5/2022 (ultimo giorno con dati: 29/5/2022, `varchi.csv`). Il file dei varchi li elenca ancora. Il varco 89 ha dati minimi (44 transiti al giorno in media nei feriali), il 87 circa 2.300 (media 2017-2022).
- Festivi: calendario calcolato da noi (feste nazionali, Pasqua e Lunedi' dell'Angelo calcolati, Sant'Ambrogio 7/12 come festivo milanese). Il 7/12 cade nei fine settimana in alcuni anni.
- Stazioni aria: il collegamento col filone aria (fase 3) e' solo preparato in `stazioni_aria_vicino_areac.csv`: nessuna stazione fuori dal confine entro 1 km; dentro: via Senato e Verziere; entro 1,5 km: viale Liguria (1,16 km), via Juvara (1,19 km, chiusa nel 2007). Distanze dal confine del poligono `AREA_C` di `raw\ds51...` (proiezione piana locale, errore di pochi metri).
