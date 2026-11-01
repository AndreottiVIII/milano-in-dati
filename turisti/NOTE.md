# Turisti per nazionalità a Milano - FASE 1 (fonti, scaricamento, pulizia, riepilogo)

Data: 1 novembre 2026. Cartella: `turisti\`. Nessuna pagina web (solo fase 1). Nessun git; `JOURNAL.md` e `docs\` non toccati.
Come leggere: ogni numero dice da quale file e da quale campo viene. I programmi sono in `scripts\` (comandi in `STATO.md`); i numeri del testo sono stampati da `out\riepilogo.txt` (programma 09) o dai controlli in `pulito\controlli_comune_polis.txt` e `pulito\bdi_controlli.txt`.
Nessun account creato, nessuna richiesta d'archivio per modulo o mail, nessun accesso aggirato. Pause di 2-3 secondi tra i download, User-Agent dichiarato. Sull'API ISTAT: circa 14 richieste in 15 minuti, con pause di 15 secondi o più.
"Paese" qui = paese di **residenza** degli ospiti (come lo rileva l'ISTAT), non la cittadinanza.

## In breve

1. **La fonte giusta esiste ed è aperta: il Comune di Milano ripubblica (CC BY) i dati ISTAT/PoliS-Lombardia del movimento clienti per paese di residenza, per il comune di Milano, ogni anno 2000-2025** (`ds211`+`ds213`: arrivi e presenze, dal 2005; `ds210`+`ds212`: dal 2000), **per mese e paese dal 2015 al 2025** (`ds214`/`ds215`) e **albergo / extra-albergo per paese dal 2008** (`ds219`/`ds220` per gli stranieri, `ds217`/`ds218` per gli italiani per regione). I totali coincidono con PoliS-Lombardia: 12.946.065 notti nel 2019 e 17.748.326 nel 2025.
2. **ISTAT (esploradati) non dà nulla in più**: il dataflow per paese di origine (`122_54_DF_DCSC_TUR_5`) esiste solo con territorio "Italia"; quello per tipo di esercizio (`_7`) arriva alle province ma **senza Milano** (codici fino a ITC4B); per il comune c'è solo la capacità (`_1`). I dati del Comune di Milano sono la stessa rilevazione ISTAT, e sono la via giusta.
3. **Banca d'Italia: i microdati dell'indagine sul turismo internazionale sono aperti** (CSV, 1997-2025, citando la fonte) e hanno la provincia e il comune visitati. Scaricati tutti i 29 anni (180 MB). Danno spesa, viaggiatori e notti (stime da campione, 9.000-15.000 interviste l'anno per il comune di Milano; poche per singolo paese). Spesa dei viaggiatori stranieri verso il comune di Milano: 3.858 milioni di euro nel 2019, 5.532 nel 2025.
4. **Gli italiani sono il fatto nuovo**: nel 2025 le notti di italiani sono 3.905.864, il 12,8% **sotto** il 2019 (4.478.745), mentre le notti totali sono +37,1% e quelle di stranieri +63,5%. Quota di notti di italiani: 34,6% nel 2019, 22,0% nel 2025. Notti di italiani **in albergo**: 3.280.621 -> 2.159.317 (-34,2%).
5. **Cina**: 503.445 notti nel 2019, 67.874 nel 2020, 130.964 nel 2022, **475.164 nel 2025 (94% del 2019, sotto il picco del 2015: 506.756)**. Arrivi: 236.856 (2019), 226.614 (2025). Tra i grandi è l'unico paese asiatico/europeo-orientale che non è tornato sopra il 2019 insieme a Russia (55% del 2019, 40% del picco 2013) e Giappone (73%; picco 2002: 570.379, nel 2005 era il primo paese).
6. **Stati Uniti**: 798.473 notti (2019) -> 1.460.226 (2025), x1,83, primo paese in tutti gli anni dal 2019. **Regno Unito**: 494.897 -> 873.860 (x1,77); già prima del 2020 (2015: 359.876; 2019: 494.897) la crescita c'era, dopo Brexit non si vede un calo. **Polonia**: x3,31 (131.329 -> 434.960, ottava nel 2025, 68% delle notti fuori dagli alberghi). **Turchia** x2,28; **Romania** x2,15; **Altri Paesi del Medio Oriente** (Golfo compreso, non separato dai dati) x2,12 (357.431 -> 756.522).
7. **Expo 2015** si vede: 11.741.374 notti nel 2015 (+14,7% sul 2014), 10.976.484 nel 2016 (-6,5%). Nei mesi maggio-ottobre 6.745.341 notti nel 2015 contro 5.753.927 nel 2016 (-14,7%); ottobre 2015 è il mese più alto fino al 2018 (1.272 migliaia). Francia +87% e Svizzera +104% su maggio-ottobre 2016 (italiani +34%).
8. **Olimpiadi invernali (febbraio 2026): non si vedono**, i dati si fermano a dicembre 2025 (comune e provincia).
9. **Nel 2025 l'extra-alberghiero ha il 46,9% delle notti** (22,3% nel 2019). Con avvertenza: da gennaio 2025 l'ISTAT include anche le locazioni brevi gestite in forma non imprenditoriale (vedi trappole 6).

## 1. Fonti, una per una (anche in `pulito\inventario_fonti.csv`)

### 1.1 Comune di Milano, open data (CKAN `dati.comune.milano.it`)
Ricerca con `package_search` (11 parole chiave: turismo, arrivi, presenze, nazionalità, provenienza, imposta di soggiorno, turisti, strutture ricettive, flussi turistici, movimento clienti, paese di residenza), risultati in `raw\ricerche\ckan_milano_turismo.json`. **Licenza: `license_id = cc-by`, risorse con tipo licenza "CC BY 4.0"** (vocabolario `A21_CCBY40`). Citare "Comune di Milano - dati.comune.milano.it; fonte ISTAT / Regione Lombardia - PoliS-Lombardia (flussituristici.servizirl.it)". Scaricati il 1/11/2026 in `raw\comune_milano\` (ds213 copiato da `affitti-brevi\raw`):

| Dataset | Contenuto | Anni | Granularità | Righe | Scheda modificata |
|---|---|---|---|---|---|
| `ds211` | arrivi per paese di residenza | 2005-2025 | annuale, comune | 1.176 | 27/10/2026 |
| `ds213` | presenze (notti) per paese | 2005-2025 | annuale, comune | 1.176 | 27/10/2026 |
| `ds210` | arrivi per paese | 2000-2024 | annuale, serie vecchia | 1.075 | 1/10/2026 |
| `ds212` | presenze per paese | 2000-2024 | annuale, serie vecchia | 1.090 | 8/5/2026 |
| `ds214` | arrivi per paese e mese | 2015-2025 | mensile, comune | 7.392 | 27/10/2026 |
| `ds215` | presenze per paese e mese | 2015-2025 | mensile, comune | 7.392 | 27/10/2026 |
| `ds219` / `ds220` | arrivi / presenze di stranieri per paese e tipo (alberghi, extra-alberghi) | 2008-2025 | annuale | 990 + 990 | 27/10/2026 |
| `ds217` / `ds218` | arrivi / presenze di italiani per regione e tipo | 2008-2025 | annuale | 378 + 378 | 27/10/2026 |
| `ds526` | passeggeri aeroporti Milano (contesto, non analizzato) | 2003-2025 | annuale | 207 | 18/6/2026 |
| `ds681` | visitatori stranieri Design Week 2017 per nazione (non analizzato) | 2017 | 4-9 aprile 2017 | 80 | 8/5/2026 |

Mancano: arrivi/presenze per paese per **mese prima del 2015**; **tipo di struttura per mese**; paesi singoli per Golfo e Africa (solo "Altri Paesi del Medio Oriente", "Altri Paesi dell'Africa", "Paesi dell'Africa Mediterranea"); quartieri.

### 1.2 Regione Lombardia, open data (Socrata `dati.lombardia.it`)
Attribuzione "Polis Lombardia - ISTAT". **Licenza: il portale non la indica** ("licenza non specificata"). Scelta prudente: pubblicare solo numeri aggregati con attribuzione; gli stessi dati comunali sono ripubblicati dal Comune in CC BY.
- `xzck-giqt` "Flussi turistici per mese nelle province lombarde" (2019-2025, **provincia di Milano**): arrivi e presenze **per mese e per provenienza** (82 voci: regioni italiane + paesi), totale / alberghiero / extra-alberghiero. 6.528 righe per Milano. **È il solo dato mensile per paese con la divisione albergo / extra-albergo**, ma per la provincia (nel 2019-2025 il comune pesa tra il 73% e il 79% delle notti della provincia).
- `c9ae-qhbj` "Provenienza dei turisti nei comuni lombardi" (2019-2024, comune di Milano): le prime 10 provenienze per anno (solo "Totale" per Milano), 60 righe. Contiene regioni italiane (Lazio, Lombardia...) e paesi insieme: nel 2024 USA 1.342.986 notti, Francia 862.514, Regno Unito 775.801, Germania 759.194, Spagna 644.240.
- `vyxt-7jdx` (italiani/stranieri per tipo, 2019-2025) e `mzxz-sz25` (mensile totale, 2019-2025): già scaricati da `affitti-brevi` e copiati. Il mensile di `mzxz-sz25` coincide con la somma dei paesi di `ds215` (differenza massima 0,14% nel solo 2021).
- **Aperti nel catalogo ma non apribili**: "Flussi turistici della Regione 2011-2022" (un dataset per anno: `xxbx-zbms`, `8yaz-ueds`, `2zbf-mna8`, `avbs-npy6`, `7z56-5r62`, `44rc-7uf8`, `wgdm-wjkr`, `e7rs-wmwc`, `bjgk-23jk`, `9vte-f7jk`, `ur9q-yzuu`, `vekj-jk3h`) e "Flussi turistici dei Comuni della Regione dal 2022" (`7eps-cpgr`): l'API risponde 404 (1/11/2026), stesso difetto già visto in `affitti-brevi`. Non ho cercato di aggirarlo. Se si aprissero, darebbero probabilmente il paese per comune di quegli anni, ma per Milano i dati del Comune bastano.

### 1.3 ISTAT esploradati (SDMX `esploradati.istat.it/SDMXWS/rest`)
Provato con pause (le richieste del 1/11/2026 sono in `raw\istat\`): dataflow `122_54_DF_DCSC_TUR_1` (capacità, comuni), `_2` (dimensione alberghi, prov.), `_3` (movimento mensile per tipo), `_4`/`_8` ("residenti per regione di origine"), `_5` ("Paese di origine"), `_6` (tipo di località), `_7` (movimento annuale per tipo). Risultati: `_5` con frequenza mensile ha REF_AREA = solo `IT` (82.416 osservazioni), con frequenza annuale zero; `_7` ha 134 territori fino alla provincia di Bolzano... senza Milano (ITC4C assente, anche il comune 015146). **ISTAT, via esploradati, non dà Milano x paese.** Licenza ISTAT: CC BY 4.0 (non riletta sulla pagina oggi: non verificato). La descrizione del dataflow dice: "Da gennaio 2025, i dati degli alloggi in affitto includono anche quelli gestiti in forma non imprenditoriale (locazioni brevi o per finalità turistiche). Questo genera discontinuità nelle serie extra-alberghiere e nei totali." (`raw\istat\df_TUR_3.xml`). L'elenco completo dei dataflow (richiesta unica) è andato in timeout: non ho il catalogo intero.

### 1.4 Banca d'Italia, Indagine sul turismo internazionale dell'Italia
Pagine lette il 1/11/2026 (`raw\bancaditalia\*.html`). Indagine campionaria alle frontiere (aeroporti, valichi, porti, stazioni). **Condizioni d'uso** (pagina "Distribuzione dei microdati"): citare la fonte (Banca d'Italia, Indagine sul turismo internazionale dell'Italia), non coinvolgere l'istituto, indicare chiaramente le elaborazioni proprie ("elaborazioni su dati Banca d'Italia"); la pagina chiede anche di inviare copia dei lavori (non fatto, nessuna mail). Nessun account né modulo per scaricare i file.
- **Microdati stranieri, variabili principali, CSV, 1997-2025** (29 file, `raw\bancaditalia\microdati_stranieri\`): per ogni intervista data contabile (mese), comune, provincia e regione visitati, Stato di residenza, motivo, tipo di alloggio principale, notti e valori espansi `FPD_VIAG` (viaggiatori a destinazione), `FPD_NOTTI`, `FPD_SPESA_FMI` (spesa in euro). Codici di Stato e alloggio nei metadati (`Metadati_csv.zip`, estratto in `raw\bancaditalia\meta_x\`). Comune di Milano = codice 1600, provincia di Milano = 16. 9.000-15.000 interviste l'anno per il comune (4.594 nel 2020).
- **Tavole Excel** `Turismo_TS_1997-2025.xlsx` (serie storiche annuali, 24 tavole): per paese di origine e per **regione** (non provincia) visitata. Scaricato ma non analizzato (il livello regionale è meno utile dei microdati).
- Tabelle pivot (Excel) per il 2020 scaricate (885 KB); le altre (2007-2025) hanno solo la regione visitata, non servono.
- **Cosa manca**: è un'indagine campionaria, non un conteggio. Per singoli paesi a Milano il campione è piccolo (Cina 2019: 90 interviste; Corea del Sud 18; Russia 2023: 40). La spesa è dichiarata dal viaggiatore, e dipende dal luogo dell'intervista (frontiera, partenza). Le interviste sono sospese da marzo a giugno 2020. Dal febbraio 2025 la Banca ha internalizzato l'espansione dei dati ("le ripartizioni di maggior dettaglio possono differire").
- **Spesa per provincia pubblicata**: la Banca ha tavole per regione, non per provincia. Quella di Milano è un'elaborazione mia sui microdati.

## 2. Pulizia (`pulito\`)
Tabelle tidy (UTF-8, virgola, un valore per riga):
| File | Righe | Contenuto |
|---|---|---|
| `annuale_paese.csv` | 1.403 | anno, paese, arrivi, presenze, permanenza media, fonte; 2000-2025, comune di Milano, tutte le strutture |
| `annuale_paese_tipo.csv` | 3.024 | anno, paese, tipo (alberghiero / extra-alberghiero / totale), arrivi, presenze; 2008-2025; "Italia" = somma delle regioni |
| `italiani_regione_tipo.csv` | 1.134 | italiani per regione di provenienza e tipo, 2008-2025 |
| `mensile_paese.csv` | 7.404 | anno, mese (1-12), paese, arrivi, presenze; 2015-2025 |
| `provincia_mensile.csv` | 19.584 | provincia di Milano 2019-2025: anno, mese, tipo provenienza (estero / italia_regione / non_specificato), provenienza, tipo struttura, arrivi, presenze |
| `milano_top10.csv`, `milano_italiani_stranieri.csv`, `milano_mensile_totale.csv` | | da PoliS (c9ae-qhbj, vyxt-7jdx, mzxz-sz25) |
| `bdi_milano_paese_anno.csv` | | Banca d'Italia: anno, ambito (comune_milano / provincia_milano / italia), Stato, interviste, viaggiatori, notti, spesa |
| `bdi_milano_mese.csv`, `bdi_milano_alloggio.csv` | | mese e tipo di alloggio, per comune e provincia |
| `riepilogo_*.csv` | | tabelle di sintesi (programma 09) |

Il "tipo di struttura" in tabella è quello della fonte (alberghiero = esercizi alberghieri; extra-alberghiero = alloggi in affitto, B&B, agriturismi, campeggi, ostelli, case per ferie ecc.). Per ogni paese-anno-mese: arrivi, presenze, tipo struttura sono presenti dove la fonte li ha; il **mese per paese** non ha la divisione per tipo (c'è solo per la provincia).
Pulizie fatte: un solo nome per paese (la fonte scrive lo stesso paese in maiuscolo/minuscolo e con refusi: "ITALIA/Italia", "Altri Parsi Dell'America Latina", "Austrialia", "Israel"); mesi abbreviati in numeri; separatore delle migliaia (vedi trappole 2).

## 3. Controlli di coerenza (`pulito\controlli_comune_polis.txt`)
- Il totale annuale per paese (ds211/ds213) coincide con il totale per tipo (ds217-220) in tutti gli anni 2008-2025 tranne il **2018** (5.766.133 arrivi contro 5.695.214; 12.286.018 notti contro 12.058.831).
- La somma dei 12 mesi per paese (ds214/ds215) coincide con l'annuale in tutti gli anni 2015-2025 tranne **2017** (5.545.347 arrivi contro 5.510.200) e un'oscillazione minima nel **2021**.
- Le due serie annuali (2000 e 2005) non coincidono: su 860 voci paese-anno-misura 2005-2024 confrontabili, **181 diverse**; le notti totali 2019 sono 13.116.501 nella serie vecchia contro 12.946.065 nella nuova (+1,3%); nel 2024 sono uguali. **Uso la serie nuova dal 2005 e la vecchia solo per 2000-2004.** Giuntura: 2004 = 6.977.255 notti (serie vecchia), 2005 = 6.848.363 (serie nuova; la vecchia dava 6.925.788).

## 4. Riepilogo (numeri in `out\riepilogo.txt`)

### 4.1 Italiani e stranieri (comune di Milano, tutte le strutture, notti)
| Anno | Totale | Italiani | Stranieri | Quota stranieri |
|---|---|---|---|---|
| 2000 | 5.040.877 | 2.232.690 | 2.808.187 | 55,7% |
| 2005 | 6.848.363 | 2.832.988 | 4.015.375 | 58,6% |
| 2010 | 8.420.430 | 3.346.722 | 5.073.708 | 60,3% |
| 2015 | 11.741.374 | 4.483.024 | 7.258.350 | 61,8% |
| 2019 | 12.946.065 | 4.478.745 | 8.467.320 | 65,4% |
| 2020 | 3.522.945 | 1.852.060 | 1.670.885 | 47,4% |
| 2022 | 11.142.087 | 3.694.022 | 7.448.065 | 66,8% |
| 2025 | 17.748.326 | 3.905.864 | 13.842.462 | 78,0% |
(Arrivi stranieri 2025: 5.708.819 su 7.640.762, 74,7%.) Gli italiani nel 2020-2021 hanno resistito meglio (41% del 2019 nel 2020, contro 20% degli stranieri). Nel 2025 stranieri = 163,5 e italiani = 87,2, indice 2019 = 100.

### 4.2 Primi paesi (notti, tutte le strutture, solo paesi singoli)
- 2005: Giappone 479.493; Regno Unito 386.580; USA 376.543; Germania 285.738; Spagna 257.428; Francia 216.074; Russia 146.741; Cina 110.408.
- 2015: Francia 628.356; USA 574.188; **Cina 506.756**; Germania 501.045; Regno Unito 359.876; Svizzera 354.161; Giappone 303.375; Russia 294.477.
- 2019: USA 798.473; Germania 546.547; Francia 537.848; Cina 503.445; Regno Unito 494.897; Russia 416.113; Spagna 407.212.
- 2025: USA 1.460.226; Francia 971.840; Regno Unito 873.860; Germania 839.163; Spagna 728.374; Cina 475.164; Brasile 465.255; Polonia 434.960; Svizzera 418.951. Escluse le voci "Altri ..." (la maggiore: Altri Paesi del Medio Oriente 756.522, che sarebbe quinta).
- Provincia (PoliS, `xzck-giqt`, 2025): USA 1,56 milioni; Francia 1,13; Germania 0,99; Regno Unito 0,98; Spagna 0,87; Cina 0,65 (la Cina nella provincia 2019: 730 mila contro 503 mila nel comune: fuori Milano comune stanno fiera, outlet e aeroporti; il confronto va fatto stessa-unità).

### 4.3 Paesi scelti (notti; indice sul 2019 = 100; tutte le strutture)
| Paese | 2019 | 2020 | 2022 | 2023 | 2024 | 2025 | Picco |
|---|---|---|---|---|---|---|---|
| Cina | 503.445 (100) | 13 | 26 | 61 | 90 | 94 | 2015 |
| Stati Uniti | 798.473 (100) | 13 | 104 | 148 | 168 | 183 | 2025 |
| Regno Unito | 494.897 (100) | 23 | 105 | 134 | 157 | 177 | 2025 |
| Germania | 546.547 (100) | 20 | 94 | 116 | 139 | 154 | 2025 |
| Francia | 537.848 (100) | 26 | 117 | 138 | 160 | 181 | 2025 |
| Russia | 416.113 (100) | 24 | 27 | 45 | 51 | 55 | 2013 |
| Giappone | 247.772 (100) | 17 | 20 | 48 | 60 | 73 | 2002 |
| Altri Paesi del Medio Oriente | 357.431 (100) | 18 | 88 | 142 | 177 | 212 | 2025 |
| Israele | 115.450 (100) | 14 | 144 | 148 | 138 | 184 | 2025 |
| India | 185.568 (100) | 23 | 61 | 106 | 136 | 130 | 2024 |
| Polonia | 131.329 (100) | 22 | 116 | 166 | 245 | 331 | 2025 |
Regno Unito per Brexit: ricordare che la fonte lo sposta nel 2022 dal gruppo "UE 15" a "Paesi europei non UE"; le notti 2016 (anno del voto) sono 440.000 contro 359.876 nel 2015 e 470.000 nel 2018: nessun calo visibile, ma il confronto non spiega nulla.
Non ci sono i Paesi del Golfo come voce: "Altri Paesi del Medio Oriente" (Israele è a parte) è il contenitore. Con la Banca d'Italia: Arabia Saudita 44 milioni di euro nel 2019 (99 interviste) e 122 nel 2025 (50 interviste), 451 euro per notte (la spesa per notte più alta).

### 4.4 Permanenza media (notti per arrivo)
- 2019, paesi con almeno 100.000 arrivi: Russia 2,46; Brasile 2,40; Regno Unito 2,27; Spagna 2,19; USA 2,18; Germania 2,15; Cina 2,13; Francia 2,07; Giappone 2,05; Svizzera 1,70. Totale Milano 2,16; Italia 1,99. India 3,50 (53.007 arrivi); Altri Paesi del Medio Oriente 2,84.
- 2025: Romania 2,68; Brasile 2,62; Turchia 2,60; Polonia 2,55; Regno Unito 2,46; Spagna 2,42; Australia 2,42; Germania 2,35; Francia 2,34; USA 2,32; Cina 2,10; Svizzera 1,86. Totale Milano 2,32; Italia 2,02. Altri Paesi del Medio Oriente 2,95.
- In **albergo** gli italiani stanno 1,62 notti, in extra-albergo 2,91; in generale l'extra-albergo ha sempre una permanenza più lunga (USA 2,14 contro 2,71, Cina 1,94 contro 2,50, Regno Unito 2,26 contro 2,76). (`riepilogo_alberghi_extra_perm.csv`.)

### 4.5 Albergo contro extra-albergo per paese (notti, 2008-2025)
Totale: quota extra 4,0% (2008), 11,3% (2013), 14,2% (2017), 19,1% (2018), 22,3% (2019), 35,7% (2020), 29,5% (2022), 46,9% (2025). Quota extra nel 2025 per paese (≥250.000 notti): Polonia 68%, Romania 62%, America Latina (altri) 58%, Spagna 56%, Francia 55%, Germania 53%, Paesi Bassi 52%, Australia 50%, Turchia 50%, Regno Unito 46%, Italia 45%, Brasile 43%, USA 37%, Cina 34%, Giappone 25% (tutti i valori in `riepilogo_alberghi_extra_per_paese.csv`). Nel 2019 la quota andava dal 14% (Medio Oriente) al 27% (Italia); USA 17%, Cina 18%, Giappone 9%. Cambiamento 2019-2025 nelle notti alberghiere: Italia -1,12 milioni, Russia -185 mila, Cina -98 mila, Giappone -90 mila; USA +258 mila, Medio Oriente +158 mila.

### 4.6 Expo 2015 e Olimpiadi 2026
Vedi In breve 7-8. Mese per mese (migliaia di notti): maggio-ottobre 2015 = 1.048 / 1.039 / 1.112 / 1.066 / 1.209 / 1.272; stessi mesi 2016 = 1.020 / 905 / 1.012 / 744 / 1.031 / 1.042; 2019 = 1.173 / 1.158 / 1.155 / 860 / 1.117 / 1.196. Gennaio-aprile e novembre-dicembre 2015 sono invece 4,5% **sotto** il 2016 (4.996.033 contro 5.222.557): l'effetto Expo è tutto nei sei mesi. Febbraio 2025 (1.224 mila) e dicembre 2025 (1.326 mila) sono i riferimenti per le Olimpiadi, non c'è febbraio 2026.

### 4.7 Banca d'Italia: spesa e notti (comune di Milano, stime)
Spesa in milioni di euro (viaggiatori stranieri con destinazione il comune): 2005: 2.371; 2010: 2.595; 2015: 3.352; 2019: 3.858; 2020: 997; 2021: 1.910; 2022: 4.292; 2023: 5.260; 2024: 5.483; 2025: 5.532. Quota della spesa stranieri in Italia: 8,9% (2010), 8,7% (2019), 9,8% (2025). Per paese 2025: USA 518 (546 interviste), Regno Unito 495, Francia 442, Germania 410, Spagna 368, **Cina 301** (101 interviste; 94 nel 2019 con 90 interviste), Svizzera 237. Nel 2019 il primo era la Germania (495, 828 interviste) davanti agli USA (395). **Cautela: la graduatoria per spesa tra i singoli paesi si muove molto da un anno all'altro; usare solo ordini di grandezza.** Le notti BdI per il comune (31,97 milioni nel 2025) sono quasi il doppio delle notti ufficiali nelle strutture (17,7 milioni): comprendono anche case di amici, seconde case ecc.

## 5. La cosa più sorprendente
**A Milano il turista "in calo" è l'italiano, non il cinese.** Dal 2019 al 2025 le notti totali sono +37,1% (da 12.946.065 a 17.748.326) e le notti straniere +63,5%, ma le notti di italiani sono **-12,8%** (4.478.745 -> 3.905.864): negli alberghi -34,2% (3.280.621 -> 2.159.317), nell'extra-albergo +45,8%. Gli italiani passano da 34,6% a 22,0% delle notti. Per confronto la Cina, che si ricorda come "non tornata", è al 94% del 2019 per le notti (96% per gli arrivi); nei soli alberghi cinesi -24% (414.190 -> 316.109), gli italiani -34%. Poi Polonia: era 31 mila notti nel 2005, 131 mila nel 2019, 435 mila nel 2025 (ottava, davanti a Svizzera e Paesi Bassi). (Fonte: `annuale_paese.csv`, `riepilogo_italiani_stranieri.csv`, `annuale_paese_tipo.csv`.)

## 6. Trappole (verificate)
1. **Due serie annuali sovrapposte con numeri diversi** (ds210/212 dal 2000 e ds211/213 dal 2005): per il 2019 le notti sono 13.116.501 e 12.946.065. Le altre fonti (PoliS) coincidono con la nuova. Dal 2025 il Comune ha rinominato i dataset ("2005-2025"), ma le schede della serie vecchia sono ancora online.
2. **Separatore delle migliaia: in `ds212` (30 valori) e `ds219` (3 valori) i numeri sono scritti con il punto** ("29.531" = 29531), negli altri file senza separatore, in `vyxt-7jdx` con la virgola ("1,943,585"). Letti come numeri decimali dànno valori mille volte più piccoli. Gestito nel programma 07 (regola: gruppi di tre cifre dopo il punto).
3. **I nomi cambiano**: maiuscole nel 2017-2019 di `ds213`, "Stati Uniti D'America"/"d'America", refusi ("Altri Parsi", "Austrialia", "Israel"). Il gruppo ("Area geografica") è inaffidabile: il Regno Unito è in "UE 15" fino al 2021 e in "Paesi europei non UE" dal 2022; Croazia, Turchia e altri cambiano. **Non usare l'area della fonte; fare gruppi propri.**
4. **Voci residuali instabili**: "Altri Paesi", "Altri Paesi Extraeuropei" e "Altri paesi europei" sono vuote o diverse tra 2005-2016 e dal 2017; nascono "Paesi dell'Africa Mediterranea" e "Altri Paesi del Medio Oriente". Si possono confrontare nel tempo solo i paesi singoli.
5. **Totali diversi tra dataset nel 2017 e nel 2018** (vedi sezione 3): mensile 2017 +0,6% sull'annuale; tipo 2018 +1,9% sul paese. Per le serie lunghe uso il totale per paese; per albergo/extra il totale per tipo.
6. **Rotture di serie nell'extra-alberghiero**: 5,6% (2012) -> 11,3% (2013) e 14,2% (2017) -> 19,1% (2018): salti di definizione o di copertura, non ancora spiegati (non verificato). **Da gennaio 2025 l'ISTAT include anche le locazioni brevi non imprenditoriali**: l'extra-albergo passa da 7,00 a 8,33 milioni di notti (+19%) tra 2024 e 2025 in parte per questo. Il confronto 2025/2024 sull'extra e sui totali non è pulito.
7. **La residenza non è la nazionalità**: un cinese residente in Italia è "Italia". "Italiani" = clienti residenti in Italia.
8. **Le presenze sono notti nelle strutture, non persone**; non ci sono gli ospiti di case di amici o di locazioni non dichiarate, né gli escursionisti. Gli "arrivi" sono check-in, non persone distinte.
9. **Comune e provincia sono unità diverse**: Cina nel 2019 730 mila notti in provincia, 503 mila nel comune. Il rapporto comune/provincia varia da un paese all'altro (e il mensile con la divisione albergo/extra c'è solo per la provincia). Provincia = Milano senza Monza e Brianza dal 2019 (la provincia "MI" cambia nome in "Milano" nel 2024).
10. **Il mese di una tabella è il mese del soggiorno**; l'ultimo mese disponibile è dicembre 2025.
11. **Banca d'Italia: "viaggiatori a destinazione" sono anche escursionisti** (stessa persona contata per ogni destinazione; la Svizzera ha 1,13 milioni di viaggiatori e 1,10 milioni di notti nel 2019). La spesa per notte è quindi fuorviante per chi viaggia senza dormire. Le interviste per singolo paese sono poche (vedi 4.7); marzo-giugno 2020 senza interviste. Le notti BdI includono case di amici, seconde case.
12. **Nome dei paesi nel tempo (BdI)**: i codici di Stato cambiano (Serbia e Montenegro, ex Jugoslavia ecc.): usati i nomi validi nell'anno dai metadati. Un solo codice "CINA REP.POP." (senza Hong Kong, Taiwan).
13. **Anno e mese della BdI**: `DATA_CONTABILE` è il mese di rilievo, non quello di arrivo.
14. **ISTAT esploradati**: dataflow `_5` (Paese di origine) solo Italia; elenco completo dei dataflow in timeout; il limite di 5 richieste al minuto non è stato superato.

## 7. Cosa potrebbe mostrare una pagina (fase 2)
1. **La curva dei 25 anni**: notti a Milano 2000-2025, divise italiani / stranieri; il crollo 2020 e la salita fino a 17,7 milioni; l'Expo come gobba.
2. **Classifica dei paesi, anno per anno** (bar chart race o slope chart 2005 / 2015 / 2019 / 2025): Giappone primo nel 2005, Francia nel 2015 (Expo), USA dal 2019.
3. **Una mini-scheda per paese** (Cina, USA, Regno Unito, Russia, Giappone, Germania, Polonia, Medio Oriente): notti per anno, indice sul 2019, permanenza, quota extra-albergo.
4. **Il mese dell'anno per paese** (stagionalità, 2015-2025): americani a giugno, francesi ad agosto, cinesi a luglio, britannici a settembre, spagnoli a dicembre (valori 2019 e 2025 in `out\riepilogo.txt`, sezione 8).
5. **Albergo / extra-albergo per paese**: quanto l'extra-albergo ha pesato nel 2019 e nel 2025, con l'avvertenza sulla copertura dal 2025.
6. **La spesa** (BdI): un solo grafico, la spesa 2005-2025 dei viaggiatori stranieri nel comune, con la fascia di incertezza; mai la classifica tra singoli paesi.
7. **Le trappole di lettura** in una nota in fondo (residenza non nazionalità, notti non persone, serie a pezzi).

## 8. Non fatto / da decidere
- Non ho letto `Turismo_TS_1997-2025.xlsx` né le tavole BdI per regione; non ho calcolato intervalli di confidenza per la spesa (il campione per paese è piccolo).
- Non ho cercato i dati mensili per paese prima del 2015 (non esistono aperti) né il mese per tipo di struttura al comune (solo provincia).
- I dataset regionali dal 2011 al 2022 ("Flussi turistici della Regione") e "dal 2022" non si aprono: da riprovare più avanti.
- Da decidere con Davide: se la pagina deve usare solo il comune (consigliato: ds211-ds220, CC BY) o aggiungere la provincia (stagionalità con albergo/extra); se mostrare la spesa BdI (stime, campione piccolo); come trattare il 2025 per la rottura ISTAT; se citare "Altri Paesi del Medio Oriente" come "Golfo" (non è esatto).
- Non ho confrontato con il numero di passeggeri degli aeroporti (`ds526`, scaricato).
