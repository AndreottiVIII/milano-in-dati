# Aria, stazione per stazione: note sul download (fase 1)

Scaricato il 29/10/2026. Nessuna analisi, nessuna pagina del sito. Cartella: `milano-in-dati\aria\`.
Script in `scripts\` (01 ricerca, 02 scarico Comune, 03 scarico ARPA, 04-07 inventari e confronto). Risultati in `out\`.

## 1. Fonti scaricate

### A. Comune di Milano, dati aperti (CKAN, dati.comune.milano.it)
- Ricerca: `package_search?q=Rilevazione qualità aria` (risultato salvato in `raw\ckan_search.json`).
- Cartella: `raw\comune\` (36 file, 6,5 MB in totale; l'elenco con URL e date è in `raw\comune\_manifest.json`).
- **Rilevazione qualità aria 2002-2026** (uno per anno, 25 file CSV, nomi `ds4xx_qaria_datoariagiornostazione_year-AAAA.csv` fino al 2020 e `qaria_datoariagiornostazione_<data>.csv` dal 2021). Colonne: `stazione_id;data;inquinante;valore`. Un valore al giorno per stazione e inquinante. Il file 2026 (`ds2969`, `qaria_datoariagiornostazione_2026-10-29.csv`) viene aggiornato ogni giorno: arriva fino al 28/10/2026.
- **Report qualità aria 2005-2024** (20 file, `*_reportariagiorno_*.csv`). Colonne: `data;descrizione;previsione;tendenza`. Sono bollettini scritti a parole (per esempio "Superamento del Valore Limite per il PM10"), non numeri. Fermi al 16/04/2024 (`qaria_reportariagiorno_2024-05-08.csv`, 74 righe). Per il 2025 e il 2026 non esiste il report.
- **Stazioni monitoraggio inquinanti** (`ds484`): `qaria_stazione.csv`, `qaria_stazione.geojson`, `qaria_stazione_shp.zip`. 9 stazioni, con coordinate, id Comune (`id_amat`), id ARPA (`id_arpa`), inizio e fine attività.
- **Valori rilevati per i principali inquinanti 2004-2023** (`ds573_inquinanti_aria.csv`, 4,6 KB): solo riassunti annuali (media annua PM10 e NO2, giorni di superamento PM10 e O3). Utile come controllo, non come dato.
- Licenza: CC-BY (campo `license_id` = `cc-by` in `raw\ckan_search.json`). I dati grezzi si possono ripubblicare citando la fonte (Comune di Milano).

### B. ARPA Lombardia, dati.lombardia.it (Socrata)
- Registro stazioni: dataset `ib47-atvt` "Stazioni qualità dell'aria", 998 righe in tutta la Lombardia; salvato intero in `raw\arpa\ib47-atvt_stazioni_tutte.csv`. Le righe con `comune` = Milano sono 71 sensori su 9 stazioni. Esiste anche `9xaz-9vbz` (stazioni NRT, 222 righe): `raw\arpa\9xaz-9vbz_stazioni_NRT.csv`.
- Dati orari/giornalieri dei sensori, scaricati solo per i 71 sensori di Milano, un file per sensore in ognuna di queste cartelle (`raw\arpa\<dataset>\sensore_<id>.csv`; 424 MB in totale, 8.838.896 righe):
  - `evzn-32bs_fino1999` (Dati sensori aria fino al 1999): 134 MB, 2.792.469 righe
  - `cthp-zqrr_2000-2009`: 122 MB, 2.536.542 righe
  - `nr8w-tj77_2010-2017`: 97 MB, 2.026.524 righe
  - `g2hp-ar79_dal2018` (2018-2025): 63 MB, 1.302.209 righe
  - `nicp-bhqi_corrente` ("Dati sensori aria", 2026): 9 MB, 180.936 righe
  - `ykhg-b8rs_NRT` (ultimi giorni, in tempo quasi reale): 1 MB, 216 righe. Sono doppioni degli ultimi giorni di `nicp-bhqi`.
- Colonne dati: `idsensore, data, valore, stato, idoperatore`. Colonne registro: `idsensore, nometiposensore, unitamisura, idstazione, nomestazione, quota, provincia, comune, storico, datastart, datastop, utm_nord, utm_est, lat, lng`.
- Licenza: CC0 (Creative Commons 1.0 Universal, dedica al pubblico dominio), attribuzione ARPA Lombardia (dai metadati Socrata `api/views/<id>.json`, campi `license` e `attribution`). Si possono ripubblicare i dati grezzi.
- Nessuna registrazione, nessun accesso, nessuna accettazione di licenza richiesta, né per il Comune né per ARPA.

## 2. Le stazioni (9) e come si corrispondono

Il Comune e ARPA usano **codici diversi**. Il legame va fatto a mano, con i nomi e le coordinate (distanza tra i due punti in metri, da `qaria_stazione.csv` e dal registro ARPA, campi lat/lng):

| Comune `id_amat` | Nome Comune | ARPA `idstazione` | Nome ARPA | Distanza |
|---|---|---|---|---|
| 1 | p.le Abbiategrasso | 549 | P.zza Abbiategrasso | 12 m |
| 2 | via Pascal * | 705 | Pascal Città Studi | **531 m** |
| 3 | viale Liguria | 539 | v.Liguria | 123 m |
| 4 | viale Marche | 501 | v.Marche | 8 m |
| 5 | Parco Lambro | 547 | Parco Lambro | 3 m |
| 6 | via Senato * | 548 | v.Senato | 36 m |
| 7 | Verziere | 528 | Verziere | 17 m |
| 8 | p.le Zavattari | 503 | P.zza Zavattari | 4 m |
| 9 | via Juvara | 502 | v.Juvara | 149 m |

Il campo `id_arpa` del Comune (126, 100, 107, 2, 124, 125, 85, 7, 7) **non coincide** con `idstazione` di ARPA, e il valore "7" è usato due volte (Zavattari e Juvara). Non va usato per fare il collegamento. Le due stazioni col asterisco (Pascal, Senato) nel nome: il significato non è spiegato nei dati.

## 3. Cosa c'è, stazione per stazione (inventario completo in file)
- `out\inventario_stazioni_inquinanti.csv`: per ogni stazione e inquinante, prima/ultima data e buchi, per ARPA e per il Comune insieme.
- `out\inventario_arpa.csv` (71 sensori: tipo, unità, prima/ultima data, passo, buco più lungo, stati) e `out\inventario_arpa_per_anno.csv` (valori validi per sensore e anno).
- `out\inventario_comune.csv` (63 coppie stazione-inquinante: righe, validi, vuoti, prima/ultima data, buco più lungo) e `out\inventario_comune_per_anno.csv`.
- `out\confronto_comune_arpa.csv`: confronto giorno per giorno.

Sintesi (da `inventario_comune.csv`, campi `prima`, `ultima`; da `inventario_arpa.csv`):
- Chiuse: Zavattari, Parco Lambro, Abbiategrasso (dati Comune fino al 31/08/2017 per NO2; ARPA registro `datastop` = 30/07/2018; i dati ARPA finiscono con il 2016). Juvara chiusa l'11/06/2007.
- Aperte oggi: Pascal (ARPA 705), Senato (548), Marche (501), Verziere (528), Liguria (539, ma il CO è spento dal 03/10/2023, `inventario_arpa.csv` sensore 5823).
- Inquinanti nel dato giornaliero del Comune: NO2, CO (CO_8h), PM10, PM25, O3, benzene (C6H6), SO2. In ARPA ci sono anche ossidi di azoto, Black Carbon, ammoniaca, metalli (arsenico, cadmio, nichel, piombo) e benzo(a)pirene, solo a Senato e Pascal.
- Il Comune non ha dati di SO2 dopo il 2007 tranne Pascal (SO2, `inventario_comune.csv`, stazione 2, fino al 28/10/2026); gli altri SO2 sono righe sempre vuote.
- Il NO2 ha la serie più lunga (ARPA: Marche dal 1980; Verziere dal 1988; Liguria dal 1991; Senato dal 1995; Pascal dal 2007). Il PM10 inizia a Juvara nel 1998 (ARPA sensore 6905), a Verziere nel 2001, a Senato nel 2007, a Pascal nel 2007, a Marche nel 2018.
- Il PM2.5: Juvara 2005-2007 (sensore 9874), Pascal dal 2007, Senato dal 2012, Marche dal 2021 (sensore 20529; il registro dice 2022, i dati partono dal 30/09/2021).

## 4. Il Comune e ARPA si sovrappongono? Chi è più lungo?
**Sì, sono le stesse misure.** Il Comune pubblica un riassunto giornaliero dei dati ARPA. Confronto fatto su tutti i giorni in comune (`out\confronto_comune_arpa.csv`):
- **La data del Comune è il giorno dopo la misura.** Se spostiamo la data ARPA di un giorno avanti, il PM10 coincide nel 98-100% dei giorni (differenza entro ±1 µg/m³, colonna `uguali_1_mean`; per esempio stazione 6 PM10: 0,993, 4.740 giorni). Senza spostamento la coincidenza scende al 10%.
- **Cosa rappresenta il valore giornaliero del Comune** (trovato per confronto, non dichiarato nei metadati):
  - PM10 e PM2.5: media giornaliera (coincidenza 99%).
  - NO2 e O3: **massimo orario del giorno**, non la media (coincidenza entro il 5%: 94-99% per il NO2, 90-99% per l'O3; colonne `uguali_5pc_max`).
  - CO (`CO_8h`): massimo della media mobile su 8 ore (coincidenza 95-99%, colonna `uguali_1_max8h`).
  - Benzene e SO2: più vicini alla media giornaliera (benzene entro 1 µg/m³ nel 82-95% dei giorni; SO2 solo 60-70%, da verificare in fase 2).
- **Lunghezza**: ARPA è molto più lunga (NO2 dal 1977, SO2 dal 1971, polveri totali dal 1976, `inventario_arpa.csv`, campo `prima`; il Comune parte dal 2002) e ha il dato **orario**. Il Comune è più comodo (un valore al giorno già pronto) e **ha dati che ARPA non ha** in alcuni periodi (vedi trappole 9 e 10).
- Consiglio per la fase 2: ARPA per le serie lunghe, per l'orario e per i metalli; il Comune per riempire i buchi di ARPA (trappole 15 e 16), dopo aver riallineato la data e l'indicatore.

## 5. Unità, medie, flag, codici di dato mancante
- Unità (campo `unitamisura` del registro ARPA): µg/m³ per tutto tranne CO (mg/m³) e metalli/benzo(a)pirene (ng/m³). Il Comune non scrive le unità nei file: CO_8h è in mg/m³ (valori 0-10), gli altri in µg/m³.
- ARPA: NO2, CO, SO2, O3, benzene, black carbon, ammoniaca, NOx sono **orari** (`inventario_arpa.csv`, `passo_mediano` = 0 days 01:00:00). PM10, PM2.5 e polveri totali sono **giornalieri** (passo 1 giorno). Metalli e benzo(a)pirene sono giornalieri a intervalli: passo mediano 3-6 giorni.
- ARPA: l'ora è "a fine ora": la prima riga di ogni anno è alle 01:00 e l'ultima è alle 00:00 del 1° gennaio dell'anno dopo. Per questo ogni sensore ha 1 riga isolata nel primo giorno dell'anno successivo. Per i PM la data è il giorno stesso alle 00:00.
- ARPA: codice di dato mancante **`-9999`** nel campo `valore` (380.679 righe su 8,8 milioni; sempre insieme a `stato` vuoto). `stato` vale `VA` (valido, 8.458.001 righe) oppure vuoto (380.895). `idoperatore` quasi sempre 1 (restano 51 righe con 39 e 29 con 10). Nessun altro valore negativo.
- Il Comune: dato mancante = **cella vuota** nel campo `valore`; nessun flag di validazione. Decimali con il punto. Valori 0 presenti in 45 righe (benzene, CO, PM10: da guardare in fase 2, possono essere dati sotto soglia).
- 22 righe ARPA hanno orari non tondi (per esempio 16:00:03).

## 6. Trappole dei dati (non sono cambiamenti dell'aria)

**Cambi di stazione, strumento o posizione**
1. **Juvara è stata sostituita da Pascal.** Juvara (Comune 9 / ARPA 502) chiude l'11/06/2007 (`datastop` ARPA dei sensori NO2, PM10; campo `fine_operativita` Comune); Pascal (Comune 2 / ARPA 705) apre il 16/06/2007 (NO2) a circa 925 m (calcolato sulle coordinate ARPA). Nel Comune la stazione 2 inizia il 12/06/2007 (PM10) e il 17/06/2007 (NO2). Una linea "unica" Juvara+Pascal mescola due posti diversi.
2. **Le coordinate della stazione Pascal divergono di 531 m** tra Comune (45,4741 N; 9,2348 E, `qaria_stazione.csv`) e ARPA (45,4783 N; 9,2317 E). Per la mappa conviene usare ARPA.
3. **Chiusure**: Abbiategrasso (1), Parco Lambro (5), Zavattari (8) chiudono nel 2017 (Comune; NO2 fino al 31/08/2017, O3 e CO fino al 28/12/2017). Il registro ARPA dice 30/07/2018 per le stesse. I loro dati ARPA finiscono con l'anno 2016.
4. **Gli inquinanti si accendono e si spengono**: CO a Verziere fino al 04/07/2011; CO a Liguria fino al 03/10/2023; SO2 a Marche fino al 1999, a Liguria fino al 1999, a Verziere fino al 2004, a Abbiategrasso fino al 2003, a Zavattari fino al 2010; benzene a Senato dal 1999, a Zavattari dal 2000, a Marche e Pascal dal 12/09/2012; O3 a Parco Lambro fino al 01/01/2018 (registro ARPA).
5. **Doppioni di sensori per lo stesso inquinante** (cambio strumento): Black Carbon a Marche (29001 fino al 2015; 20455 dal 2020), a Senato (20005 fino al 2019; 20465 dal 2020), a Pascal (20004 dal 2013; 20581 dal 2023); ammoniaca a Pascal (20020 dal 2007; 20484 dal 2020). Il codice del sensore cambia quando cambia lo strumento: la serie va ricomposta a mano. Le polveri totali sospese (PTS) finiscono tra 1996 e 2013 e sono sostituite dal PM10.
6. **Il nome dello strumento per il PM10** è "PM10 (SM2005)" in tutte le stazioni (campo `nometiposensore`): i dati non dicono se il metodo di misura è cambiato nel tempo.
7. Le date di inizio nel registro ARPA non sempre coincidono con i dati: PM2.5 Marche registro 01/01/2022, dati dal 30/09/2021 (sensore 20529); NO2 Pascal registro 16/06/2007, prima riga 16/06/2007 (ok); ammoniaca Pascal 20020 registro 30/03/2007, dati dal 15/06/2007.

**Buchi e difetti nei file Comune** (da `out\inventario_comune.csv`, `_per_anno.csv`, e dai file annuali)
8. **Dal 2016 i file del Comune contengono solo i giorni da lunedì a venerdì** (nelle date): 229-242 giorni distinti all'anno (2016: 229; 2017: 236; 2018: 242). Fa eccezione il 2019, completo (365 giorni). Il 2020 ha 271 giorni. Sabato e domenica quasi assenti. Poiché la data è il giorno dopo la misura, probabilmente mancano le misure di venerdì e sabato (deduzione, non verificata). Le medie annuali vanno calcolate con questo avvertimento (per questo conviene usare ARPA, che ha tutti i giorni).
9. **2013: mancano 47 giorni** (`ds464`, 318 giorni distinti, ultimo 23/12/2013). 2014 e 2015 sono completi.
10. **Dal 2024 il Comune ha solo 5 stazioni** (2, 3, 4, 6, 7) e pochi giorni: 139 giorni nel 2024 (ultimo 24/12/2024), 99 nel 2025 (7/1-17/12/2025), 57 nel 2026 (10/2-28/10/2026). Il file 2024 e 2025 non è completo.
11. **Righe doppie con una cella vuota**: 56 coppie stazione-data-inquinante duplicate nei file del 2021, 2022 e 2025 (una riga col valore e una riga vuota). Se si legge il file senza eliminare i vuoti si contano giorni di troppo.
12. Righe di "stazione-inquinante" che non esistono davvero (per esempio la stazione 1 con O3, PM10) appaiono con una sola riga vuota: sono segnaposto, non misure.
13. Il valore del Comune non è lo stesso indicatore per tutti gli inquinanti (vedi sezione 4): non si può mettere NO2 del Comune (massimo orario) accanto a un NO2 medio ARPA.
14. Il file 2020 e 2019 sono stati ricaricati il 30/04/2021 (campo `last_modified` in `_manifest.json`), 2002-2013 il 29/04/2019: ci sono versioni diverse dello stesso anno, non verificate.

**Buchi nei file ARPA** (da `out\inventario_arpa_per_anno.csv`)
15. **Il dataset 2018-2025 (`g2hp-ar79`) manca di alcuni sensori attivi.** Benzene (Marche 17127, Pascal 17126), Black Carbon Pascal (20004) e ammoniaca Pascal (20020) **non hanno nessun dato nel 2018-2025**, pur avendone prima e dal 2026 (verificato anche con una richiesta diretta: `g2hp-ar79`, `nicp-bhqi`, `nr8w-tj77` per il sensore 17127). Marche PM10 (20429), PM2.5 (20529), Black Carbon (20455 e Senato 20465), ammoniaca (20484) **non hanno il 2025**. Per il benzene di Marche il Comune ha invece i dati (`inventario_comune.csv`, stazione 4, C6H6, 2012-2026).
16. **ARPA non ha il 2017 (e il 2018) per le stazioni chiuse nel 2017**: i dati di Zavattari, Parco Lambro, Abbiategrasso finiscono al 31/12/2016, mentre il Comune li ha fino all'agosto-dicembre 2017.
17. **Vecchi anni con anni incompleti** (inizio e chiusura): NO2 Juvara 2007 solo 3.857 ore (fino all'11/06); sensori con buchi di anni all'inizio (1977, 1979, 1986 NO2 Juvara).
18. **Buchi lunghi in singoli sensori**: i valori `max_buco_giorni` di `inventario_arpa.csv` arrivano a 2.922 giorni per i sensori citati al punto 15 e a 365 giorni per quelli recenti. NO2 di Marche ha un buco di 130 giorni; CO Senato 29 giorni (stesso campo).
19. **Una riga isolata al 1° gennaio dell'anno dopo** per ogni sensore (vedi sezione 5). In `inventario_arpa_per_anno.csv` sembra un anno con 1 dato: non è un buco.
20. **Sovrapposizioni tra archivi**: i dataset ARPA si sovrappongono sul confine (`nicp-bhqi` e `g2hp-ar79`, `ykhg-b8rs`): 17 righe duplicate per ogni sensore (`righe_duplicate_t` in `inventario_arpa.csv`). Vanno tolte prima di sommare.
21. Il dataset `nicp-bhqi` ("Dati sensori aria") si aggiorna ogni giorno e contiene solo l'anno in corso (2026): il conteggio righe cambia a ogni scarico.

## 7. Cosa NON ho scaricato / limiti
- ARPA: solo i 71 sensori con `comune` = Milano. Non ho scaricato le stazioni vicine (Pioltello, Cinisello, Rho, Limito…) né le stime comunali (`ysm5-jwrn` e simili), né i dati meteo.
- Il file `out\_arpa_all.pkl` (535 MB) è stato cancellato; si rigenera con `python -I scripts\05_inventario_arpa.py raw\arpa out` (serve anche per rilanciare `scripts\06_confronto.py out`).
- Il confronto Comune-ARPA è fatto con tutti i giorni in comune ma non per ogni inquinante e per ogni anno a parte: i risultati per stazione sono in `out\confronto_comune_arpa.csv`.
- Non ho verificato le posizioni dei punti con fonti esterne né la causa dell'asterisco nei nomi "via Pascal *" e "via Senato *".
- Il significato esatto degli indicatori del Comune (max orario, max 8 ore) è dedotto dal confronto: da confermare con chi pubblica il dataset.
