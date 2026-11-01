# Le antenne dei cellulari - FASE 1 (raccolta, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web. Tono neutro: nessuna affermazione sulla salute oltre a quello che dicono le misure ufficiali, e queste per Milano non sono aperte. Ogni numero dice file e campo. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di antenne> <percorso assoluto di milano-in-dati>` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle in `pulito/`. Inventario dei file con sha256: `pulito/inventario_file.csv`.

## 1. In breve

1. **L'unica fonte aperta con le antenne di Milano è il catasto CASTEL di ARPA Lombardia pubblicato dal Comune di Milano (ds718, CC-BY).** 2.580 impianti (file ricaricato l'8/6/2025), 2.480 accesi e 100 "previsti con parere favorevole". Regione Lombardia (2.802 dataset nel catalogo Socrata) non ha né CASTEL né campi elettromagnetici.
2. **Mancano i due dati che servivano di più: la tecnologia (2G-5G) e la data di attivazione.** Nel file ci sono gestore, tipo (Telefonia, Microcella, Ponte, Radiofonia, Televisione, Altro, Wireless), stato, classe di potenza, indirizzo, CAP, NIL, coordinate. La crescita del 5G **non si può misurare** con dati aperti.
3. **Si può però vedere come è cambiato il catasto**: ho recuperato 5 versioni del file (2020-21, gen 2023, mag 2024, giu 2024, giu 2025) dalla Wayback Machine. Gli impianti di telefonia mobile accesi (Telefonia + Microcelle di operatori e società di infrastrutture) sono 1.389 (2020-21), 1.964 (gen 2023), 2.097 (giu 2025). Il salto 2020-21 -> 2023 può dipendere anche da come è stato estratto il file (vedi 4.3 e 5).
4. **Densità**: 2.097 impianti di telefonia mobile accesi in 181,76 km2 = 11,5 per km2 e 1,49 per 1.000 abitanti (abitanti ds205 2024: 1.407.044). Nel NIL Duomo 86 per km2, nel NIL mediano 10,2. Ma per 1.000 abitanti il Duomo (12,4) non misura l'esposizione dei residenti: lì le antenne servono chi ci lavora e passa.
5. **Misure di campo elettromagnetico per Milano: esistono ma non sono aperte.** ARPA le tiene dentro CASTEL (misure di breve durata e centraline in continuo, visibili nel viewer web) ma non le offre come file e non dichiara una licenza aperta: non le ho scaricate. Aperti ci sono solo indicatori regionali (2018: 887 misure vicino a stazioni radio base in Lombardia, 92% sotto 3 V/m, 7% tra 3 e 6, 1% tra 6 e 20). Per i limiti vedi 6: **6 V/m non è più, o non è sicuramente più, il valore in vigore**.
6. **Scuole**: 26,9% delle 835 scuole con coordinate ha un impianto di telefonia mobile entro 100 m; per i 46.896 civici residenziali è il 33,7%. Vicino non vuol dire esposto (vedi 4.4).
7. **La cosa più sorprendente (vedi 7)**: al terzo posto per numero di impianti non c'è un operatore telefonico ma CommsCon Italia, 373 microcelle.

## 2. Fonti, una per una

Licenza dei dataset del Comune: CKAN `license_id = cc-by` ("Creative Commons Attribution", versione non scritta). Si possono ripubblicare citando "Comune di Milano - dati.comune.milano.it".

### 2.1 Comune di Milano - ds718 CASTEL (USATO)
- Titolo: "CASTEL: Catasto localizzazione Impianti di Telecomunicazione e Radiotelevisione nel Comune di Milano". Fonte originale: catasto CASTEL di ARPA Lombardia (il Comune lo ripubblica). Manutentore: Comune di Milano - Unità Analytics e Open Data. `frequency = NEVER` nel catalogo: nessun aggiornamento programmato.
- File attuale: risorse CSV, JSON, GeoJSON, caricate l'8/6/2025 (CKAN `last_modified`), `metadata_modified` 8/5/2026 (ricarico del portale). Scaricati CSV e GeoJSON il 1/11/2026 in `raw/comune_ds718/`; il CSV è uguale byte per byte alla copia Wayback del 24/2/2026 (sha256).
- 2.580 righe, 17 colonne: `Sit_IDCodiceImpianto` (unico), `Sit_NomeImpianto`, `gestore` (90 nomi), `Ti_TipoImpianto` (7), `Sit_StatoImpianto` (8), via, civico, `INDIRIZZO`, `Potenza (W)` (classi), `CAP`, `MUNICIPIO`, `ID_NIL`, `NIL`, `LONG_X_4326`, `LAT_Y_4326`, `Location`.
- **Cosa manca**: tecnologia, data di attivazione o autorizzazione, frequenze, numero di antenne per impianto, altezza, direzione, potenza in watt (solo classi), misure.
- 11 impianti su 2.580 (quasi tutti "Ponte" di Wind Telecomunicazioni) **non hanno coordinate** né NIL: restano nei totali, non nelle mappe e nei NIL. 1 riga ha NIL ma non municipio.

### 2.2 Copie storiche di ds718 (Wayback Machine, USATE con cautela)
`raw/wayback_ds718/` (scaricate il 1/11/2026 con pause, log e sha256 in `download_log.csv`). Il Comune non tiene versioni vecchie sul portale; ho trovato le copie con l'indice CDX di archive.org.

| Snapshot | Copia | Righe | Note |
|---|---|---|---|
| 2020-21 | 22/1/2021 (la copia del 27/9/2020 ha gli stessi 1.793 impianti) | 1.793 | JSON; **senza codice impianto** e senza CAP; nel file del 2020 alcune righe hanno le colonne spostate (14), la versione 2021 è pulita |
| 2023-01 | 2/5/2024 | 2.443 | nome del file `impianti_20230124__final_-no_filter` (il "no filter" fa pensare che prima ci fosse un filtro) |
| 2024-05 | 15/5/2024 | 2.510 | |
| 2024-06 | 15/6/2024 | 2.513 | aggiunta la colonna Potenza |
| 2025-06 | file attuale | 2.580 | |

La data delle copie è l'ultimo momento in cui il file poteva essere già quello: la data vera dei dati dentro il file non è scritta (tranne "20230124" nel nome del file 2023).

### 2.3 CASTEL ARPA Lombardia, interfaccia web (SONDATA, non usata)
`castel.arpalombardia.it/castel/` ha pagine pubbliche (Banca dati, Report, Report statistici, Mappa) senza login; la home sulla radice risponde 403. Ho fatto **una sola ricerca** per Milano nel "Report" (`raw/web_probe/castel_milano_report.html`): **2.535 record** (il 1/11/2026, contro i 2.580 del file del Comune, quindi il catasto vivo è più recente o più filtrato), con le stesse colonne (gestore, nome, comune, tipo, stato) e 20 righe per pagina. Niente tecnologia, niente date, niente coordinate: non vale scorrere le 127 pagine. Nessuna licenza dichiarata; footer "ARPA Lombardia - Tutti i diritti sono riservati"; la pagina "Note legali" restituisce una pagina vuota. Non l'ho usata.
Il **manuale d'uso** (PDF, gennaio 2017, linkato nella pagina; salvato in `raw/web_probe/castel_manuale_utente.pdf` e `.txt`) dice che l'accesso "non accreditato" (senza login) a mappa e report è previsto e che **in CASTEL ci sono anche gli esiti delle misure di campo elettrico di ARPA**: (a) misure di breve durata ("punti di misura", strumento portatile): data, quota, valore massimo e medio di campo elettrico; (b) misure in continuo con centraline ("misure FUB"): andamento nel tempo del valore medio, con il periodo. Il viewer li mostra su mappa, uno alla volta; **non c'è un'esportazione dei dati** (solo PDF della scheda e dell'elenco impianti) e il viewer è un'applicazione GIS in una finestra a parte. Non ho automatizzato il viewer: licenza non aperta e nessuna esportazione prevista. La scheda impianto contiene "tipo e stato di realizzazione, gestore, localizzazione e fascia di potenza": **nemmeno nel catasto pubblico c'è la tecnologia**.

### 2.4 Regione Lombardia / ARPA Lombardia su dati.lombardia.it (NIENTE)
API catalogo Socrata (`api.eu.socrata.com`, dominio `www.dati.lombardia.it`): scaricato l'intero catalogo (2.802 dataset: `raw/catalogo_lombardia.json`) e cercato per radice (elettromagn, radiofrequen, cem, telefon, castel, radiobase, antenn, telecomun, ripetitor, v/m, 5g, emf, radiotelev, inquinamento). Nessun risultato pertinente (solo "Comuni lombardi raggiunti dalla banda larga" del 2014, non scaricato). Le ricerche per parola chiave su `raw/search_socrata.json` danno lo stesso esito.

### 2.5 ARPA Lombardia, indicatori e rapporti (SOLO CONTESTO, "tutti i diritti riservati")
- Indicatore "Campo elettromagnetico misurato - siti SRB" (2018, pubblicato 27/1/2020): **887 misure in Lombardia**, 92% < 3 V/m, 7% tra 3 e 6 V/m, 1% tra 6 e 20 V/m (file xlsx `raw/arpa_indicatori/misurato_srb_2018.xlsx`). **Solo livello regionale**, nessun dato di Milano. Nessuna licenza aperta: c'è un regolamento per l'uso dei dati (arpalombardia.it/urp/patrocinio-uso-del-logo-e-dei-dati). Non ripubblicare il file: citare i numeri con la fonte.
- Rapporto stato ambiente, sezione campi elettromagnetici (pagina letta, nessun file): "nel 98% dei casi viene rispettato il valore di attenzione" (analisi 2023), 99% (2022); per il 2024 "ampio rispetto dei limiti di legge" con "un necessario cambio di parametrizzazione dei dati misurati rispetto agli anni precedenti", quindi non confrontabile; tendenza a un aumento limitato della densità di potenza dal 2021 al 2024 per LTE, 5G e reti di nuovi operatori. Nessun numero per provincia o per Milano.
- Abstract ARPA Lombardia al seminario ISPRA del 28/11/2019 (`raw/arpa_indicatori/arpa_seminario_ispra_2019-11-28.pdf`): "A Milano, a causa dell'elevato numero di stazioni radiobase (1200 circa)... è notevolmente aumentata... l'estensione di aree con spazio elettromagnetico saturo", cioè siti attorno ai quali i valori **simulati** sulla potenza autorizzata superano il valore di attenzione. Nello stesso documento: sperimentazione 5G pre-commerciale di Vodafone a Milano (3,7-3,8 GHz) autorizzata dal 25/9/2017 fino al 31/12/2021.

### 2.6 Cartoradio (MIMIT / Fondazione Ugo Bordoni) e Catasto nazionale delle sorgenti radiomobili (NIENTE)
Cartoradio (cartoradio.it) è una mappa con **livelli di campo stimati con modelli** ("non costituiscono misurazioni"), dati aggregati e anonimi "senza riferimenti a singoli operatori o impianti". Il catasto nazionale delle sorgenti radiomobili (DM 13/2/2014, decreto direttoriale 9/12/2024) è aggiornato dagli operatori ogni trimestre, ma non risulta pubblicato come open data. Nessun download, nessuna licenza. Non scaricato nulla.

### 2.7 Altro cercato
- **Portale nazionale dati.gov.it** (API CKAN, 8 ricerche): trovati catasti SRB aperti di altre regioni (Toscana, Veneto, Bolzano, Trento, Liguria...), **nessuno per la Lombardia** oltre a ds718 del Comune.
- **AGCOM / MIMIT copertura mobile e 5G**: non ho trovato mappe scaricabili con licenza aperta (la ricerca non ha dato un file). Non scaricato nulla.
- **OpenCelliD**: richiede chiave API, saltato come da regola. Mozilla Location Service: non verificato (mi risulta chiuso nel 2024).
- **OpenStreetMap**: il ritaglio di Milano già presente nel filone bici-auto-mezzi (`bici-auto-mezzi/raw/osm_milano/milano_buffer.osm.gz`) non contiene antenne di comunicazione (4 "mast" in tutto, tre sono pali di illuminazione): inutile come controllo. Il PBF intero della Lombardia c'è (`bici-auto-mezzi/raw/osm_lombardia/`) ma non l'ho scandagliato: in OSM le antenne dei cellulari sono comunque mappate in modo molto parziale. ODbL.
- **Comune di Milano, altri dataset**: ds69 (antenne Open WiFi: sono hotspot wifi, non celle) e ds1864 "Ambiente e area scolastica" (ha una voce sull'inquinamento elettromagnetico per scuola statale; non scaricato, da valutare). Non esiste un dataset "piano antenne".
- **Misure ARPA su singoli casi** sono pubblicate dal Comune come PDF sparsi (es. Galleria Fontana 3, luglio 2013): non sono dati.

## 3. Pulizia (`scripts/build.py`, `scripts/common.py`; controlli in `pulito/controlli_pulizia.json`)

- `pulito/impianti.csv` (2.580 righe, separatore `;`): `id_impianto, nome, gestore, tipo, stato, potenza_classe_W, indirizzo, cap, municipio_file, id_nil_file, nil_file, lon, lat, gruppo_gestore, categoria, acceso, previsto, procedura_scia, segnalazione_parere, suffisso_id, sito_id, id_nil, nil, metodo_nil`.
- Nessun valore cancellato. `acceso` = stato che comincia per "Acceso" (2.480); `previsto` = "Previsto con parere favorevole" (100); `procedura_scia` = stato che contiene "SCIA" (747).
- **Gruppo gestore e categoria** (assegnati da me con regole in `common.py`; elenchi completi in `controlli_pulizia.json`): operatore mobile (TIM, Vodafone, WindTre = Wind Tre + Wind Telecomunicazioni + H3G, Iliad: 1.793 impianti); società di infrastrutture (CommsCon, Cellnex, INWIT, OpNet, Hightel, TowerCo: 451); radio e TV (286); altro operatore TLC (Fastweb, Fastweb Air, Solaris, Linkem...: 6); altro (RFI, ATM, A2A, ENAV, Politecnico...: 44). **Non so a quale operatore mobile appartengano le microcelle di CommsCon o Cellnex** (sono società che costruiscono e affittano).
- **Telefonia mobile (stima)** = impianti accesi di operatori mobili o società di infrastrutture con tipo Telefonia o Microcella: 2.097 (1.426 Telefonia + 671 Microcelle). Il file non dice quale tecnologia usino.
- **Siti**: stesse coordinate (6 decimali) = stesso sito. 1.772 siti con coordinate per 2.569 impianti (1.703 con almeno un impianto acceso): 1.227 siti con un solo impianto, 469 con due, 65 con 3-5, 8 con 6-20, 3 con più di 20 (massimo 84 in corso Sempione 27). Le coordinate di operatori diversi sullo stesso traliccio possono differire di qualche metro: "siti" è un massimo.
- **NIL**: punto in poligono con gli 88 NIL vigenti (`citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson`): 2.569 su 2.569 con coordinate cadono in un NIL; il NIL scritto nel file coincide in 2.569 casi su 2.569 (100%). Impianti in 84 NIL su 88; **4 NIL senza nessun impianto acceso**: Cantalupa, Ronchetto delle Rane, Chiaravalle (1.074 abitanti), Giardini P.ta Venezia.
- **Abitanti**: ds205 anno 2024, campo `Totale` (Comune, CC-BY). **Superfici**: dai poligoni NIL in UTM 32N (somma 181,76 km2), non da ds205 (ha le superfici scambiate per 3 NIL, vedi alberi/NOTE.md). 12 NIL hanno meno di 1.000 abitanti (Parco Sempione ne ha 0): per i rapporti "per 1.000 abitanti" li escludo dalle classifiche.
- Problemi corretti nelle copie vecchie: testi con codifica sbagliata ("LocalitÃ", rimessi a posto), colonne spostate nel JSON 2020 (non usato, ho usato la versione 2021 pulita).
- Gli stati "previsto" non entrano nei conteggi degli impianti accesi.

## 4. Riepilogo (tutti i numeri in `pulito/riepilogo.json` e nelle tabelle csv)

### 4.1 Quanti e chi (file attuale)
- 2.580 impianti: Telefonia 1.544, Microcella 673, Ponte 254, Radiofonia 41, Televisione 34, Altro 20, Wireless 14 (`gestori_per_tipo.csv`, `riepilogo.json`).
- Per gestore (`gestori.csv`): TIM 633 (24,5%), Vodafone 558 (21,6%), **CommsCon 373 (14,5%)**, WindTre 366 (14,2%), Iliad 236 (9,1%), RAI Way 88 (3,4%), Cellnex 62 (2,4%). Gli ultimi due non sono operatori mobili. Iliad ha 32 impianti "previsti" su 236, TIM 22, Vodafone 23, WindTre 12.
- **Telefonia mobile accesa per gestore**: TIM 607, Vodafone 528, CommsCon 369, WindTre 323, Iliad 204, Cellnex 56, OpNet 7, INWIT 2, TowerCo 1.
- **Microcelle**: 673, di cui il 63,6% di società di infrastrutture (quasi tutte CommsCon). Sono concentrate nel centro: 120 nel solo NIL Duomo, 49 a Brera, 35 Stazione Centrale. La classe di potenza di CommsCon è quasi sempre "<= 7" o "> 7 e <= 20" W.
- Torri radio-TV: **corso Sempione 27 (NIL Pagano) ha 84 impianti di cui 82 radio/TV**, il sito più affollato; poi via San Galdino 5 (21+12), via Silva 36 (21+7), via Turati 29 (11+7). Il NIL Pagano ha 90 impianti radio/TV, Sarpi 44.
- Macro-siti di telefonia (tipo Telefonia): 946 siti con coordinate distinte; 503 con un solo operatore, 412 con due, 25 con tre, 6 con quattro.
- Classe di potenza degli impianti "Telefonia" (campo `Potenza (W)`, significato esatto non spiegato): 1.028 in "> 300 e <= 1000", 186 in "> 1000", 187 in "> 20 e <= 300", 126 vuoti.

### 4.2 Per NIL (`nil_antenne.csv`, `nil_per_gestore.csv`)
- Città: 11,53 impianti di telefonia mobile per km2, 1,49 per 1.000 abitanti; macro-siti 5,2 per km2, 0,67 per 1.000 abitanti. Per municipio (impianti di telefonia mobile accesi): M1 471, M8 279, M9 253, M7 209, M2 193, M3 191, M4 187, M6 171, M5 140.
- Più densi per km2: Duomo 86,3, Brera 56,8, Stazione Centrale-Ponte Seveso 43,7, Guastalla 43,3, Magenta-S.Vittore 37,4, Porta Garibaldi-Porta Nuova 35,6, Pagano 34,1, De Angeli-Monte Rosa 32,5.
- Per 1.000 abitanti (NIL con almeno 1.000 abitanti): primi Duomo 12,4, Cascina Merlata 9,7, Brera 5,1, Tre Torri 4,8, Porta Garibaldi-Porta Nuova 4,8; ultimi Chiaravalle 0 (nessun impianto), Gratosoglio 0,42, Ronchetto sul Naviglio 0,55, Quarto Oggiaro-Vialba-Musocco 0,58, Padova-Turro-Crescenzago 0,60. Rapporto tra primo e ultimo (zeri esclusi): 29 volte.
- La densità di impianti per km2 segue quella degli abitanti ma non fino in fondo: correlazione di Spearman 0,79 tra i NIL.
- Cosa NON dice: gli abitanti sono i residenti. Nei quartieri degli uffici e dei turisti la rete serve molte più persone di quelle che ci abitano; per questo "per 1.000 abitanti" va letto come capacità di rete, non come esposizione dei residenti.

### 4.3 Nel tempo (`serie_snapshot.csv`, `serie_snapshot_gestori_mobile.csv`, `nil_crescita_2020_2025.csv`)
Impianti di telefonia mobile accesi (Telefonia + Microcelle):

| Snapshot | Totale | di cui Telefonia | Microcelle | Accesi (tutti i tipi) | "Acceso SCIA" su accesi |
|---|---|---|---|---|---|
| 2020-21 | 1.389 | 783 | 606 | 1.788 | 12,8% |
| 2023-01 | 1.964 | 1.317 | 647 | 2.355 | 34,6% |
| 2024-05 | 2.059 | 1.388 | 671 | 2.443 | 33,4% |
| 2024-06 | 2.072 | 1.401 | 671 | 2.456 | 32,4% |
| 2025-06 | 2.097 | 1.426 | 671 | 2.480 | 30,1% |

- Per gestore, mobile acceso, 2020-21 / 2023-01 / 2025-06: TIM 379 / 575 / 607; Vodafone 315 / 481 / 528; WindTre 244 / 304 / 323; Iliad 78 / 173 / 204; CommsCon 372 / 369 / 369 (fermo); Cellnex 0 / 53 / 56.
- **Comparabile**: da gen 2023 a giu 2025 (stesso formato con il codice impianto): +133 impianti mobili (+6,8%), di cui Telefonia +109 (+8,3%) e Microcelle +24 (+3,7%). In due anni e mezzo **257 codici nuovi** e **120 codici spariti** su 2.443, cioè il catasto cambia molto più di quanto dica il totale. Tra gen 2023 e mag 2024 i nuovi sono soprattutto Vodafone (55), TIM (36), Iliad (20), WindTre (17); tra giu 2024 e giu 2025 Iliad 40, Vodafone 29, TIM 25, WindTre 24. Gli stati cambiano spesso: 390 impianti hanno cambiato stato tra giu 2024 e giu 2025. Degli 86 impianti "previsti con parere favorevole" di gen 2023, in giu 2025: 46 "Acceso", 18 "Acceso SCIA", 2 "con incoerenza grave", 11 ancora previsti, 9 non più nel file.
- **Non comparabile con sicurezza**: 2020-21 -> 2023 (+575 impianti mobili, +41%). Il file del 2023 ha "no filter" nel nome e le copie 2020-21 non hanno il codice impianto; un confronto approssimato (stesso gruppo, tipo, posizione a ~10 m) trova 1.521 impianti in comune, 911 nuovi e 272 spariti (soprattutto WindTre/H3G, Vodafone, TIM: sostituzioni e unificazioni di nomi). Va letto come "il catasto si è molto ampliato", non come "le antenne sono aumentate del 42%".
- NIL con più impianti mobili in più dal 2020-21 al 2025: Duomo +35, Villapizzone-Cagnola-Boldinasco +30 (da 10 a 40), Sarpi +20, Isola +20, Gorla-Precotto +19; solo 2 NIL in calo (Parco Forlanini-Cavriano, Parco Sempione). Stessa avvertenza.
- **"SCIA"**: lo stato "Acceso SCIA" passa dal 12,8% degli accesi (2020-21) al 34,6% (2023) e al 30,1% (2025). Non so cosa distingua questi impianti: ipotesi non verificata, collegata alle semplificazioni di legge del 2020 per impianti e modifiche. Non usarla come indicatore del 5G.
- Segnalazioni nel file attuale: 23 impianti "con incoerenza grave" (significato non spiegato), 1 "con ultimo parere non rispetto limiti" (Solaris Mobile, televisione, via Giacosa 19, NIL Loreto-Casoretto-Nolo), 1 "con ultimo parere negativo" (WindTre, via Vincenzo Monti 81, NIL Pagano). Sono etichette di stato del catasto: non dicono se il campo misurato supera qualcosa (i pareri ARPA sono su simulazioni di progetto, secondo l'abstract del 2019), e non sono misure.

### 4.4 Scuole (solo confronto di posizione; `scuole_vicinanza_antenne.csv`, `scuole_antenne_per_nil.csv`)
Scuole: 835 con coordinate = infanzia 293, primaria 216, secondaria I grado 147 (tutte le gestioni, Comune ANASCO a.s. 2024/25, `scuole/pulito/comune_scuole_anagrafica.csv`) + 179 secondarie di II grado statali e paritarie con coordinate (MIM, `scuole/pulito/miur_scuole_anagrafica.csv`; 46 su 225 senza coordinate, escluse). Distanze in linea d'aria da impianti di telefonia mobile accesi con coordinate (UTM 32N).
- Impianti di telefonia mobile entro 100 m: **26,9% delle scuole** (225); entro 50 m 72; entro 20 m 20. Distanza mediana 163 m. Per ordine entro 100 m: infanzia 22,2%, primaria 25,0%, sec. I 25,2%, sec. II 38,5% (il centro ha più scuole superiori e più antenne).
- **Confronto con la città**: per i 46.896 civici residenziali (`citta-15-minuti/out/civici_tempi.csv`, RESIDENZIALE = 1) la quota entro 100 m è 33,7% e la distanza mediana 135 m; estraendo a caso 1.000 gruppi di 835 civici la quota va dal 30,7% al 36,9% (intervallo 95%). Le scuole stanno **un po' meno vicine** alle antenne di un indirizzo qualunque (anche solo macro-siti di telefonia: 16,5% contro 24,2%).
- **Limiti di questo confronto**: "vicino" in linea d'aria non è "esposto": il campo dipende da potenza, direzione, altezza, schermatura, e le antenne trasmettono in direzioni precise; una scuola sotto o accanto a un'antenna può ricevere meno campo di una a 200 m davanti al fascio. Quello che conta per legge sono i limiti di esposizione, i valori di attenzione e gli obiettivi di qualità, verificati con misure e simulazioni da ARPA. Il confronto si limita a dire dove stanno le antenne rispetto alle scuole.

## 5. Limiti dei dati (da dire in pagina)

1. **Nessuna tecnologia**: non si può dire "quante antenne 5G". Il campo `Potenza (W)` è una classe, non una tecnologia, e non so se indichi la potenza al connettore, in antenna o autorizzata.
2. **Nessuna data per impianto**: solo 5 fotografie del catasto, e la più vecchia (2020-21) non è confrontabile del tutto con le altre.
3. **Un impianto del catasto non è un'antenna.** Un "impianto" è l'insieme degli apparati di un gestore in un sito: può avere decine di antenne di tecnologie diverse, o essere una microcella. Contare impianti non è contare antenne né contare potenza.
4. **Gestore ≠ operatore**: 451 impianti sono di società di infrastrutture (CommsCon, Cellnex...), che ospitano più operatori. Le quote per operatore sottostimano gli operatori mobili.
5. **Radio e TV, ponti radio e telefonia stanno nello stesso elenco** ma sono cose diverse per potenza (la radio-TV di una torre come Sempione trasmette con potenze anche molto diverse da una microcella). Senza classificarle, un conteggio per NIL mescola cose non confrontabili: qui le tengo separate.
6. **Stato "acceso" = risultante dal catasto**, aggiornato dai gestori e da ARPA; non è un controllo in campo. Il catasto vivo ha 2.535 record per Milano, quello del Comune 2.580.
7. **Coordinate**: non le ho controllate (nessuna verifica a terra); il NIL scritto nel file coincide con quello dei poligoni al 100%, ma questo non prova che il punto sia giusto. 11 impianti non hanno coordinate.
8. **Residenti, non frequentatori**, per i rapporti per abitante.
9. **Misure di campo elettromagnetico: non aperte per Milano** (ci sono in CASTEL, vedi 2.3, ma non scaricabili). I numeri regionali ARPA (887 misure nel 2018, 98% di rispetto del valore di attenzione nel 2023, parametri cambiati nel 2024) non dicono nulla su un quartiere.
10. **Quanti impianti di telefonia mobile ha Milano?** Il numero cambia secondo la definizione: 946 macro-siti con coordinate (impianti "Telefonia" accesi di operatori mobili e società di infrastrutture), 1.426 impianti "Telefonia", 2.097 con le microcelle, 1.564 siti con coordinate distinte. ARPA nel 2019 scriveva "1200 circa" stazioni radiobase. Per una pagina serve scegliere una definizione e dirla.

## 6. Valori di legge (da verificare sul testo prima di pubblicare)

- La legge quadro 36/2001 e il DPCM 8/7/2003 fissano tre soglie per le radiofrequenze. Dal manuale CASTEL di ARPA (2017), tabella del DPCM, campo elettrico: **limiti di esposizione** 60 V/m (0,1-3 MHz), 20 V/m (3-3.000 MHz), 40 V/m (3-300 GHz); **valore di attenzione** 6 V/m (0,1 MHz-300 GHz) per edifici con permanenze di almeno 4 ore al giorno e loro pertinenze esterne (balconi, terrazzi, cortili); i limiti e i valori del manuale sono mediati su 6 minuti, mentre ARPA (articolo del 2026 sul sito) spiega che il valore di attenzione va verificato sulle 24 ore. L'obiettivo di qualità non è nel manuale: non lo riporto.
- **La legge 214/2023 (legge annuale concorrenza) ha previsto l'innalzamento di valore di attenzione e obiettivo di qualità**: la stampa specializzata (Agenda Digitale, 30/10/2023) parla di passaggio da 6 a **15 V/m "in via provvisoria e cautelativa"**, a meno di adeguamenti entro 120 giorni; ARPA Lombardia (analisi 2024) scrive che la modifica c'è stata e che "ha cambiato la parametrizzazione dei dati". Non ho letto il testo ufficiale (Normattiva non l'ha restituito) né il decreto attuativo: **il valore in vigore oggi va verificato in Gazzetta Ufficiale prima di scrivere "6 V/m" in una pagina**. Le misure ARPA citate qui (2018, 2022, 2023) sono rispetto a 6 V/m.
- Il riferimento europeo (ICNIRP, Raccomandazione 1999/519/CE) è 61 V/m: i limiti italiani sono più bassi.

## 7. La cosa più sorprendente

**Il terzo "operatore" di Milano non è un operatore telefonico: è CommsCon Italia S.r.l., con 373 impianti, quasi tutti microcelle (368), più di WindTre (366 con i vecchi nomi) e di Iliad (236).** Chi non fa il mestiere non l'ha mai sentita nominare, eppure costruisce e gestisce una parte importante della rete in città: le microcelle dei centri storici, a bassa potenza (classe "<= 7" o "> 7 e <= 20" W), quasi sempre senza una procedura "SCIA" e senza un solo impianto "previsto". Nel NIL Duomo 120 impianti su 202 sono microcelle. Il campo "Potenza (W)" di CommsCon è nelle classi più basse del file (151 impianti "<= 7", 93 "> 7 e <= 20", 10 "> 20 e <= 300", 119 vuoti). Contare impianti, quindi, sovrastima il peso del centro rispetto a contare potenza.

Altre due sorprese (da usare come secondo o terzo punto): (a) **le scuole stanno un po' meno vicine alle antenne di un normale indirizzo di casa** (26,9% entro 100 m contro 33,7%), il contrario di quello che ci si aspetta; (b) **il sito più affollato è una torre radio-TV, non un'antenna dei cellulari**: corso Sempione 27 ha 84 impianti, il 98% dei quali radio e TV.

## 8. Cosa può mostrare una pagina

- Una mappa dei 1.772 siti, colori per categoria (operatore mobile, società di infrastrutture, radio-TV, altro), con filtro Telefonia / Microcelle / Ponte.
- Densità per NIL (per km2) e per 1.000 abitanti, con la nota sui residenti.
- Barre dei gestori con la distinzione operatori / società di infrastrutture, e la sorpresa CommsCon.
- Serie 2023 -> 2025 per gestore; il 2020-21 solo con l'avvertenza del 5.2.
- Il confronto scuole contro indirizzi qualunque, con la frase dei limiti di legge e "vicino non vuol dire esposto".
- Niente grafici sul 5G e niente mappe di campo elettromagnetico: i dati non ci sono. La pagina può dire apertamente che mancano e come si potrebbero avere (accesso agli atti ad ARPA Lombardia, URP).

## 9. Da decidere

- Chiedere ad ARPA Lombardia (URP o accesso civico) l'estratto del catasto con tecnologia e date, e le misure per Milano? Lo farebbe Davide, non io.
- Leggere il testo della legge 214/2023 e dell'eventuale decreto per fissare il valore di attenzione corrente (6 o 15 V/m).
- Valutare ds1864 (ambiente e area scolastica) per le scuole statali.
- Verificare con ARPA o gli operatori il significato di "Acceso SCIA", "incoerenza grave" e delle classi di potenza.

## 10. Aggiornamento: valore di attenzione verificato e pagina (1 novembre 2026, sera)

- **Valore di attenzione**: letto l'articolo 10 della legge 30/12/2023 n. 214 su Normattiva (`raw/normativa/art10_L214_2023_note.txt`, note di lavoro con i frammenti): comma 2, in assenza dei regolamenti di adeguamento, valori di attenzione e obiettivi di qualità "in via provvisoria e cautelativa" a **15 V/m** (campo elettrico), 0,039 A/m, 0,59 W/m2. Conferme: decreto MIMIT-MASE sul limite emissivo assentibile (cita l'innalzamento previsto dall'art. 10; testo in `raw/normativa/mimit_DM_criteri_limite_emissivo.txt`) e MIMIT, *La Comunicazione* n. 71/2026 (valore di attenzione 15 V/m, "in vigore da aprile 2024"; limite di esposizione 20 V/m tra 3 MHz e 3 GHz invariato; `raw/normativa/mimit_rivista71_2026_nuova_normativa_cem.txt`). Il testo di legge è stato letto tramite un lettore di pagine (riassunto con citazioni brevi), non scaricato in PDF dalla Gazzetta Ufficiale; non ho letto il decreto attuativo definitivo (se esiste). Le misure ARPA 2018/2022/2023 citate sono riferite al vecchio 6 V/m. La sezione 6 sopra va letta con questo aggiornamento: **6 V/m era il valore fino al 2024; ora il riferimento provvisorio è 15 V/m**.
- **ds1864** (Comune, "Ambiente e area scolastica - Scuole statali", a.s. 2020/21, licenza "Other (Attribution)", non CC BY): 560 edifici, colonna `VICINANZASORGENTIRADIAZIONIELETTROMAGNETICHE` = SI per 8, NO per 552; è un sì/no di scheda edilizia, non una misura. Non usato; citato come limite sulla pagina. File in `raw/comune_ds1864/`.
- **Pagina**: `docs/antenne/index.html` + `docs/antenne/data/`, generati da `scripts/pagina.py` (si rilancia: `python -I -X utf8 antenne/scripts/pagina.py <A> <P> <docs>`). Pubblicati: siti con impianti accesi (1.703, posizione + conteggi per categoria e gestori), NIL (confini semplificati e valori), gestori, serie delle cinque versioni, scuole per ordine, riepilogo.json. NON pubblicati: elenco impianto per impianto, posizioni delle singole scuole, qualsiasi dato ARPA a licenza riservata (solo cifre citate nel testo). La voce di menu per "antenne/" va aggiunta in `docs/menu.js` e `docs/index.html` dal coordinatore.
