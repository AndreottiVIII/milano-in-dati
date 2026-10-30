# Prezzi delle case a Milano dal 2004: note sulla fase 1 (scaricamento e preparazione)

Data: 30 ottobre 2026. Cartella: `prezzi-case\`. Nessuna analisi dei prezzi fatta: mancano ancora le quotazioni OMI (servono lo SPID di Davide, vedi `COSA_SCARICARE.md`).
Come leggere: ogni numero dice da quale file e da quale campo viene. Tutti i programmi sono in `scripts\`, il comando per rifare tutto è in `STATO.md`.
Nessun servizio con SPID o con registrazione è stato usato. Pause di 2-5 secondi tra le richieste, User-Agent dichiarato, nessun errore "troppe richieste".

## In breve

1. **Le quotazioni OMI (prezzi di vendita e affitti per zona) si possono avere solo con SPID/CIE/credenziali Entratel/Fisconline.** Disponibili dal 1° semestre 2004 (pagina "Forniture dati OMI", aggiornata 5/10/2026), ultimo semestre pubblicato: 2026/1. Licenza CC BY 4.0. Tocca a Davide: `COSA_SCARICARE.md`.
2. **I perimetri delle zone per Milano li ho presi io, senza login**, dal servizio di mappa pubblico: 32 semestri, dal 2010/2 al 2026/1. Prima del 2010/2 non esistono.
3. **Le zone cambiano molto**: 55 zone fino al 2013/2, 41 dal 2014/1, 43 dal 2024/2. Solo 2 zone su 55 sono confrontabili uno-a-uno dal 2010 a oggi; dal 2014/1 in poi 29 zone su 43 sì. Niente viene unito in silenzio: `pulito\zone_non_1a1.csv`.
4. **Compravendite (NTN) di Milano**: serie trimestrale 2004-2026, aperta, solo per tutto il comune. Per zona OMI non esiste.
5. **Inflazione ISTAT** (FOI senza tabacchi) raccordata tra le basi: mensile dal 12/2003 al 9/2026, annuale 1996-2025.
6. **Fermate metro con data di apertura**: 134 fermate (M1-M5), `pulito\fermate_metro.csv`.
7. **Pipeline pronta** e provata su un campione FINTO e su 6 semestri veri (copie di terzi, solo come prova): legge i semestri, tiene solo Milano, calcola centro e ampiezza, reale, rapporto affitto/prezzo.

---

## 1. Quotazioni OMI (NON scaricate: serve lo SPID)

- Pagina: https://www.agenziaentrate.gov.it/portale/it/web/guest/schede/fabbricatiterreni/omi/forniture-dati-omi (letta il 30/10/2026, salvata in `raw\pagine_ae\forniture.html`).
- Dice: download gratuito delle quotazioni "a partire dal 1° semestre 2004"; perimetri (file KML) "dal 2° semestre 2010" per tutta l'Italia, una provincia o un comune; volumi di compravendita (NTN) per comune "dall'annualità 2011" (esclusi i comuni dei territori col sistema tavolare). Accesso: "utenti che accedono ai servizi telematici nell'area riservata". Licenza: CC BY 4.0, da citare «Agenzia delle Entrate – OMI».
- Come funziona (articolo Eutekne del 6/4/2018, da riverificare perché vecchio): ambito = Italia / area / regione / provincia / comune; risultato = un .zip con 2 CSV, `VALORI` e `ZONE`; ogni richiesta si scarica **una sola volta, entro 7 giorni**.
- Formato di un file vero (visto su copie di terzi, 2016-2018): separatore `;`, prima riga di titolo, intestazione `Area_territoriale;Regione;Prov;Comune_ISTAT;Comune_cat;Sez;Comune_amm;Comune_descrizione;Fascia;Zona;LinkZona;Cod_Tip;Descr_Tipologia;Stato;Stato_prev;Compr_min;Compr_max;Sup_NL_compr;Loc_min;Loc_max;Sup_NL_loc;`, numeri con la virgola. Milano = `Comune_cat` `F205`. Nome file: `QI_<numero richiesta>_1_<anno><semestre>_VALORI.csv` / `_ZONE.csv`.
- Per i semestri **prima del 2016** il "tracciato ante 2016" dell'Agenzia (https://github.com/ondata/quotazioni-immobiliari-agenzia-entrate/blob/master/doc/Tracciato_record_dati_ante2016.pdf, copia di terzi di un documento dell'Agenzia, salvato in `raw\ondata_mirror_schema\`) descrive campi separati da `|` con nomi diversi (`VALMIN`, `VALMAX`, `LOCMIN`, `LOCMAX`, `COD_TIP_PREV`...). **Non ho visto un file vero di quel periodo**: il lettore è scritto sul tracciato ma non provato su dati veri.
- Il manuale OMI 2025 (PDF) dice che il volume è proprietà dell'Agenzia e non si riproduce senza autorizzazione: vale per il testo del manuale, non per i dati (che sono CC BY 4.0).
- **Copia di terzi** (6 semestri 2016/1-2018/2, 12 MB): repository "ondata/quotazioni-immobiliari-agenzia-entrate" su GitHub, `rawData\2016-1.zip ... 2018-2.zip`, scaricati il 30/10/2026 in `raw\ondata_mirror_rawdata\`. Il progetto scrive che la licenza non è chiarita (ma i dati originali sono CC BY 4.0 per l'Agenzia). Non verificabile contro gli originali. Servono come prova del programma, non come fonte finale.

## 2. Perimetri delle zone OMI di Milano (scaricati, senza login)

- Fonte: servizio di mappa pubblico dell'Agenzia, `https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/zoneomi.php?richiesta=6&codcom=F205&semestre=<AAAAS>` (è la stessa chiamata che usa la mappa; l'ho trovata leggendo `js\cittadino.js` della pagina, salvato in `raw\geopoi_probe\`). Scaricato il 30/10/2026.
- File: `raw\geopoi\F205_<AAAAS>.json`, 32 file, circa 35 MB. Da `20102` (2010 2° sem.) a `20261` (2026 1° sem.). Per `20101` e prima la risposta è vuota (coerente con "dal 2° semestre 2010").
- Il menu della mappa elenca solo 2016/1-2026/1 (campo `SEMESTRE` di `zoneomi.php?richiesta=5`), ma il servizio risponde anche per i semestri 2010/2-2015/2: li ho usati. Non è una funzione dichiarata: andrà citato come "servizio di mappa GEOPOI".
- Licenza: banche dati OMI CC BY 4.0 (stessa pagina "Forniture"). Ripubblicabile citando la fonte.
- **Il download ufficiale in KML/GML (`perimetri.php?...&formato=kml`) non funziona oggi**: 4 prove su Milano (2016/1, 2025/2, formato kml e gml) hanno dato errore 500 con il testo "Impossibile creare l'archivio ZIP". Ho usato i dati JSON della mappa. Se Davide vuole i KML ufficiali: stessa pagina "Forniture dati OMI", sezione "Perimetri di Zona" (SPID).
- **Trappola dei dati:** ogni zona arriva come un solo `Polygon` con più anelli, dove gli anelli sono spesso pezzi staccati, non buchi. Letto come GeoJSON normale, l'area totale di Milano scende a circa 100 km² (e per qualche semestre a 52 km²) invece di 181,8 km². Il programma `05_zone_corrispondenza.py` usa la regola pari/dispari sugli anelli: l'area torna a 181,3-181,8 km² in tutti i 32 semestri (campo `area_totale_km2` in `pulito\zone_periodi.csv`).
- Controllo con file veri: per il 2018/2 i 41 codici zona dei perimetri coincidono esattamente con i 41 codici del file `ZONE` ufficiale (copia di terzi). Le zone con valori sono 40: la zona rurale `R2` non ha quotazioni.

## 3. Corrispondenza tra zonizzazioni (`pulito\zone_*.csv`)

Fatta per sovrapposizione di aree (UTM 32N), con `scripts\05_zone_corrispondenza.py`. Soglie: una zona è "uguale" se si sovrappone per almeno il 90% a una sola zona dell'altro periodo, in entrambe le direzioni.

| Periodo | Semestri | Zone | Nota (da `zone_periodi.csv`) |
|---|---|---|---|
| P1 | 2010/2 - 2013/2 (7) | 55 | zonizzazione "vecchia" |
| P2 | 2014/1 (1) | 41 | prima zonizzazione con 41 zone (codici come `B15`, `R2`) |
| P3 | 2014/2 - 2019/2 (11) | 41 | perimetri quasi uguali a P2, ma 21 codici zona rinumerati |
| P4 | 2020/1 (1) | 41 | ritocco: una zona (`B21`) con sovrapposizione 0,86 |
| P5 | 2020/2 - 2021/2 (3) | 41 | ritocco: sovrapposizione minima 0,86 |
| P6 | 2022/1 - 2024/1 (5) | 41 | ritocchi, minima 0,93 |
| P7 | 2024/2 - 2026/1 (4) | 43 | revisione 2024: sparite `D15`, `D30`; nuove `D37`-`D40` |

- Da P1 a P2 (revisione del 2014): su 55 zone vecchie, solo 2 sono uno-a-uno (`zone_non_1a1.csv`: 29 "complessa", 21 "accorpata", 1 "divisa", 4 "perimetro cambiato" fra zona vecchia e nuova). **Non si può fare una serie per zona che attraversi il 2013/2-2014/1**: per quel salto serve un altro metodo (per esempio prezzi riportati su una griglia fissa con pesi d'area, da dichiarare come stima).
- Dal 2014/1 al 2026/1: 29 delle 43 zone di oggi hanno una serie uno-a-uno continua (30 se si accettano i ritocchi, colonna `id_serie_larga`).
- Il codice zona da solo **non identifica** la zona: `D38` può essere un'area diversa in due periodi. Usare `id_serie`, non il codice.
- Semestri 2004/1-2010/1: nessun perimetro. Il programma `07_prezzi.py` lascia `id_serie` vuoto; se i codici zona del file ZONE coincidono con quelli del 2010/2 si può assumere lo stesso disegno (da verificare e dichiarare).
- Il file ZONE ufficiale ha anche `LinkZona` (es. `MI00003228`): potrebbe essere un identificativo stabile. Da verificare quando arrivano i file di Davide (se resta uguale quando cambia il codice zona, è una conferma ufficiale delle corrispondenze).

## 4. Compravendite (NTN), Comune di Milano

- Serie nuova 2011-2024 (definitiva): `raw\omi_ntn\RESIDENZIALE_DEFINITIVO_2011_2024.zip` (146 kB), file `RES.csv`; provvisoria 2025-2026: `raw\omi_ntn\RESIDENZIALE_2025_2026_PROVV.zip` (49 kB). Anche non residenziale (`NON_RESIDENZIALE_*.zip`, 255 kB e 63 kB), non elaborato. Pagina: https://www.agenziaentrate.gov.it/portale/schede/fabbricatiterreni/omi/banche-dati/volumi-di-compravendita (letta il 30/10/2026). Link diretti, nessun login.
- Serie vecchia 2004-2016: `raw\omi_ntn_archivio\Residenziale_<anno>.xls` (13 file + `Residenziale_2000-2003.xls`, 2 MB), dalla pagina "Archivio volumi di compravendita". Foglio 1 = trimestrale.
- Livello: provincia e capoluogo (campo `Cap` = `cap`, riga `Prov` = `MI`). Il capoluogo di Milano è il Comune di Milano. **Non c'è dato per zona OMI né per quartiere.**
- Elaborato in `pulito\ntn_milano_trimestrale.csv` (114 righe), campi `anno`, `trimestre`, `serie`, `ntn_capoluogo`, `ntn_provincia`. Le serie NON sono fuse: dove si sovrappongono (2011-2016) `pulito\ntn_milano_confronto_2011_2016.csv` mostra le differenze: media -0,25%, da -1,27% a +0,87% (24 trimestri). Per il 2011-2016 conviene la serie nuova.
- Totali annui capoluogo (campo `ntn_capoluogo`, somma dei trimestri): 2004: 24.966; 2008: 18.977; 2012: 14.575 (minimo, serie nuova); 2019: 26.232; 2020: 21.650; 2022: 28.617; 2024: 24.003; 2025 (provvisorio): 25.173. Il 2026 ha solo 2 trimestri (12.388).
- Licenza: la pagina non la scrive per questi file; la pagina "Forniture dati OMI" dice che le banche dati OMI sono CC BY 4.0. Da citare «Agenzia delle Entrate – OMI».

## 5. Inflazione ISTAT (FOI senza tabacchi)

- Fonte: ISTAT, servizio SDMX `https://esploradati.istat.it/SDMXWS/rest/data/IT1,<flusso>,1.0/<chiave>`, scaricato il 30/10/2026 in `raw\istat\`:
  - `169_748_DF_DCSP_FOI1B2025_1.m.csv` (906 kB): mensile, 4 basi concatenate, 2003-12 -> 2026-09; `169_748_DF_DCSP_FOI1B2025_2.m.csv` (874 kB): la stessa serie in versione "tutte le basi 1996-2025" (non usato); `169_745_DF_DCSP_FOI1B2015_1.m.csv` (444 kB): base 2015 fino al 2025 (non usato, serve da controllo);
  - `169_750_DF_DCSP_FOI2B2025_1.csv` (62 kB): medie annue 1996-2025.
- Voce usata: `ECOICOP_2` = `00ST` (tutti i prodotti senza tabacchi), `MEASURE` = 4 (indice). Basi: 1995, 2010, 2015, 2025 (mensile: campo `DATA_TYPE` 4, 11, 55, 101; annuale: 5, 12, 56).
- Raccordo (`scripts\03_istat_foi.py`): il coefficiente tra una base e la precedente è la media dell'anno-base nella serie precedente diviso 100, come fa ISTAT; poi tutto è portato a 2025 = 100. Risultato in `pulito\foi_mensile.csv` e `pulito\foi_annuale.csv` (indice originale e raccordato).
- Controllo: le variazioni a 12 mesi ricalcolate coincidono con quelle pubblicate da ISTAT (campo `MEASURE` 7): 12/2010 1,92% (ISTAT 1,9), 1/2026 0,81% (0,8), 9/2026 4,04% (4,0); annuale 2025 su 2024 +1,4%. Media 2025 dei mesi = 100,00.
- Licenza: CC BY 4.0 (https://www.istat.it/note-legali/, letta il 30/10/2026). Ripubblicabile citando ISTAT.
- Trappola: il server ISTAT con chiave "tutto" non risponde entro 90 secondi per i flussi mensili; con chiave `M.IT.....` e `startPeriod=2003-12` ha risposto in circa 2 minuti.

## 6. Fermate della metro con data di apertura

- Fermate, nomi e coordinate: GTFS del Comune (AMAT) già scaricato dalla filiera 7, letto in sola lettura (`..\bici-auto-mezzi\raw\gtfs\ext_comune_new`, versione 425 del 26/10/2026); estratto l'ordine delle fermate in `raw\gtfs_metro_estratto\metro_stop_ordine.csv`.
- Date di apertura: tabelle "Apertura" e "Le date delle aperture" delle voci it.wikipedia Linea M1-M5 (lette via API, `raw\wikipedia_metro\`), controllate con en.wikipedia (Line 4 e 5) e articoli di stampa. Le date sono fatti, ma la fonte è Wikipedia (CC BY-SA): il testo non va copiato, i fatti sì.
- Risultato: `pulito\fermate_metro.csv`, 134 fermate (M1 38, M2 35, M3 21, M4 21, M5 19), campi `linea`, `fermata`, `lat`, `lon`, `data_apertura`, `tratta`, `fonte`. Tutte le fermate del GTFS hanno una data; nessuna senza. Alcune fermate sono fuori dal Comune di Milano (es. Rho, Pero, Sesto, Cologno, Gessate, Assago): da filtrare nel passo spaziale. Nello stesso nome la stazione di interscambio compare una volta per linea.
- **Date M4** (campo `data_apertura`): 26/11/2022 Linate Aeroporto, Repetti, Stazione Forlanini, Argonne, Susa, Dateo; 4/7/2023 Tricolore, San Babila; 12/10/2024 le altre 13 (Sforza-Policlinico ... San Cristoforo). Confermate da it.wikipedia, en.wikipedia, VareseNews/Il Giorno.
- **Date M5**: 10/2/2013 Bignami-Zara (7 fermate); 1/3/2014 Isola e Garibaldi FS; 29/4/2015 Domodossola, Lotto, Segesta, San Siro Ippodromo, San Siro Stadio; poi Portello 6/6/2015, Cenisio 20/6/2015, Gerusalemme 26/9/2015, Monumentale 11/10/2015, Tre Torri 14/11/2015.
- **Aperture dopo il 2004 sulle linee vecchie**: M1 Rho Fieramilano 14/9/2005 (provvisoria dal 30/3/2005) e Pero 19/12/2005; M2 Abbiategrasso 17/4/2005 (**dubbio**: la voce it.wikipedia scrive 17 aprile nel testo e 17 marzo nell'elenco; scelto aprile perché è una domenica) e Assago Milanofiori Nord e Forum 20/2/2011; M3 Dergano, Affori Centro, Affori FN, Comasina 26/3/2011.
- Non verificate con fonti ufficiali del Comune/ATM/MM: le pagine ufficiali non sono state lette (nessuna è servita per decidere). Per le date a giorno preciso delle aperture pre-2004 non ho fatto controlli incrociati: non servono per l'analisi dal 2004.

## 7. Riuso di materiale di altri filoni (solo riferimenti, niente copie)

`pulito\riferimenti_riuso.csv` elenca i percorsi assoluti: parchi, servizi e punteggi "15 minuti" (filone 9), redditi per CAP (filone 9: attenzione, sono per CAP e non per quartiere), confine del Comune e NIL vigenti (filone 9), varchi e ingressi di Area C (filone 6), GTFS (filone 7).

## 8. Pipeline pronta (codice)

- Programmi in `scripts\` (Python 3.12, `python -I`): `01_metro_da_gtfs.py`, `02_fermate_metro.py`, `03_istat_foi.py`, `04_ntn_milano.py`, `05_zone_corrispondenza.py`, `06_leggi_omi.py`, `07_prezzi.py`, `esegui_pipeline.py`. Prova: `scripts\test\make_fake.py` crea un campione finto in `test_finto\`.
- Cosa calcola `07_prezzi.py`: per ogni semestre/zona/tipologia/stato, **centro = (min+max)/2**, **ampiezza = max-min** e ampiezza relativa; versione **reale in euro 2025** (media FOI del semestre); **resa lorda annua = affitto centro × 12 / prezzo centro** e anni di affitto per pagare il prezzo; riga di stato prevalente (`Stato_prev` = P); mediana NON pesata fra le zone (non è il prezzo medio della città: non esistono pesi per zona).
- Un valore 0 o vuoto vuol dire "dato assente", non zero: diventa vuoto e la riga è segnalata (`flag_compr`, `flag_loc`).
- Prove fatte: (a) campione finto di 4 semestri (3 nel formato `;`, 1 nel formato `|` inventato, uno dentro uno zip in cp1252, con righe di un altro comune da scartare e una zona divisa in due) → tutto letto, zona divisa segnalata in `zone_non_1a1.csv`; (b) 6 semestri veri 2016/1-2018/2 (copie di terzi): 2.811 righe di Milano, nessun duplicato, nessun minimo > massimo, 40 zone con valori per semestre; esempio zona `B12`, abitazioni civili, stato prevalente: 8.100 euro/m² nel 2016/1 e 8.150 nel 2018/2 (centro di min e max; campo `Compr_min`, `Compr_max`), che in euro 2025 sono 9.866 e 9.660.
- Controlli scritti in chiaro in `pulito\omi_controlli.txt` dopo ogni lettura: buchi di semestri, righe doppie, minimo > massimo, zeri, cambi dei codici zona.

## Trappole dei dati (riassunto)

1. Perimetri GEOPOI: anelli multipli letti come buchi → area errata (vedi sezione 2).
2. Il download KML ufficiale ha dato errore 500 il 30/10/2026.
3. Codici zona rinumerati nel 2014 (2014/1 → 2014/2 senza cambio di disegno) e di nuovo nel 2024: il codice non basta.
4. Ritocchi di perimetro tra semestri (fino al 14% di area in una zona, 2020/1).
5. Revisione decennale 2014: 55 → 41 zone, quasi nessuna zona confrontabile prima/dopo.
6. Le quotazioni sono intervalli indicativi stimati dall'Agenzia, non prezzi di vendita (lo dice la pagina "Forniture dati OMI").
7. Affitti a 0 = mancanti (il progetto "ondata" stima circa il 10% di righe con affitto 0 nelle copie 2016-2018; nelle 2.811 righe di Milano che ho letto non ce n'è).
8. NTN: due serie con piccole differenze nel 2011-2016; 2025-2026 provvisorio; 2026 con soli 2 trimestri.
9. Download delle quotazioni: una volta sola, entro 7 giorni.
10. M2 Abbiategrasso: due date diverse nella stessa voce Wikipedia.
