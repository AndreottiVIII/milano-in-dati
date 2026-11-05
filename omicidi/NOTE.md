# Omicidi a Milano - FASE 1 (fonti e pulizia, niente pagina)

Fatto il 5 novembre 2026. Solo conteggi annuali: nessun nome, nessun caso singolo. Nessuna registrazione, login o modulo. User-Agent `milano-in-dati/1.0`. Numeri citati qui: `out/riepilogo.txt` e `out/controlli.txt`. Elenco degli scaricamenti con impronta sha256: `pulito/inventario_download.csv`.

## Le misure, da non mescolare
| misura | fonte | area | anni | file in `pulito/` |
|---|---|---|---|---|
| Omicidi volontari consumati e tentati, denunciati dalla polizia, luogo del fatto | ISTAT (tre archivi, sotto) | province, Italia | 1983-2024 | `serie_lunga_polizia_1983_2024.csv`, `confronto_periodi_1983_2024.csv` |
| Stessa misura, per movente | ISTAT | provincia | 1983-2003 | `milano_moventi_1983_2003.csv` |
| Stessa misura | Comune ds564 + ISTAT | comune di Milano | 2004-2024 | `comune_milano_2003_2024.csv` |
| Stessa misura | ISTAT | 12 grandi comuni | 2006-2024 | `grandi_comuni_2006_2024.csv`, `grandi_comuni_periodi.csv` |
| Morti per omicidio, da certificato di morte, per sesso | ISTAT cause di morte | province, per luogo e per residenza | 2003-2023 | `decessi_causa_omicidio_province_2003_2023.csv` |
| Morti per omicidio avvenute a Milano / di residenti | Comune ds337 e ds338 | comune | 2003-2011 / 2012-2013 | colonne in `comune_milano_2003_2024.csv` |
| Vittime per sesso, dati di polizia | ISTAT AUTVITTPS_8 | regioni 2008-2024; province solo 2022-2024 | | `vittime_polizia_sesso_aree.csv` |
| Relazione vittima-autore | ISTAT su dati del Ministero (DCPC) | Italia 2002-2024; Lombardia 2019, 2023, 2024 | | `italia_relazione_2002_2024.csv`, `lombardia_relazione_anni.csv` |
| Tassi nazionali di lungo periodo | ISTAT, storia dati | Italia | 1880-2024 | `italia_tassi_1880_2024.csv` |

**"Area milanese"** = Milano + Monza e Brianza + Lodi: è l'unico modo di avere gli stessi confini per tutta la serie. La provincia pubblicata comprende Lodi fino al 1995 e Monza fino al 2010 (nelle cause di morte Monza è a parte già dal 2010).

## Fonti (scaricate il 5/11/2026)
1. **ISTAT, Delitti denunciati 1983-2003** (`DF_BULK_CRIMESINTO`, zip con xls): `https://esploradati.istat.it/databrowser/DWL/Giustizia e sicurezza/DELITTI_DENUNCIATI_1983_2003.zip`. Province, regioni, Italia; omicidi per movente, tentati, infanticidi, preterintenzionali. Lodi, Lecco e altre province nuove dal 1996. Fonte: Ministero dell'Interno, modello 165.
2. **ISTAT, Delitti persone condannati 1985-2008** (`DF_BULK_CRIMESPERS`): stessa cartella, `DELITTI_PERS_CONDAN_1985_2008.zip`. Usate le tavole per provincia 2000-2008, per coprire 2004 e 2005.
3. **ISTAT, Delitti denunciati** `73_67_DF_DCCV_DELITTIPS_1`, tutte le aree, 7 voci di omicidio, 2006-2024 (province e capoluoghi).
4. **ISTAT, Vittime** `73_230_DF_DCCV_AUTVITTPS_8`, solo vittime di omicidio, cittadinanza = totale. La cittadinanza non è stata usata.
5. **ISTAT, Cause di morte** `39_493_DF_DCIS_CMORTE1_EV_1` (luogo) e `39_494_DF_DCIS_CMORTE1_RES_1` (residenza), voce 17_3 "omicidio, aggressione", 2003-2023.
6. **ISTAT, Popolazione** `164_279_DF_DCIS_RICPOPRES1991_1`, `164_305_DF_DCIS_RICPOPRES2001_1`, `164_164_DF_DCIS_RICPOPRES2011_1`, `22_289_DF_DCIS_POPRES1_1`. Tasso = omicidi / media di due 1 gennaio.
7. **ISTAT, relazione con l'autore**: `https://www.istat.it/wp-content/uploads/2025/11/omicidi-relazione-autore-DCPC-anni-2002-2024.xlsx`; tavole dei report: anno 2023 (`2024/11/Tavole.zip`), 2019 (`2021/02/Tavole-Fuori-testo-Omicidi.xlsx`), 2018 (`2020/03/Tavole-e-figure-appendice-omicidi.xlsx`), 2017 (`2018/11/Tavole.xlsx`, scaricata, non usata).
8. **ISTAT, storia dati**: `https://www.istat.it/wp-content/uploads/2026/06/storia-dati-criminalita-giustizia.xlsx`.
9. **Comune di Milano**: ds564 (già in `reati/`, riusato, con la correzione della riga 2019), ds337, ds338. Licenza CC-BY. In ds337 e ds338 le righe sono per età e possono valere 1: si usano e si pubblicano solo somme per anno e sesso.
10. **Ministero dell'Interno**: report omicidi 2024-2026 (CSV e PDF), `https://www.interno.gov.it/it/stampa-e-comunicazione/dati-e-statistiche/omicidi-volontari-e-violenza-genere`. Solo Italia, ultimi anni.
11. Riusati da `reati/`: totale e tasso dei grandi comuni (popolazione implicita) e residenti ds27.

Licenza ISTAT: CC BY 4.0 secondo le condizioni generali, non rilette oggi. CSV del Ministero: la pagina li chiama "opendata", licenza non scritta: citare la fonte e non ripubblicare i file. `raw/`, `pulito/` e `out/` non vanno nel repo (verificato con `git check-ignore`); `NOTE.md` e `scripts/` sì.

## Controlli fatti
- File 1983-2003 contro tavole 2000-2008, anni 2000-2003: 401 confronti tra province, 0 differenze.
- Tavole 2000-2008 contro ISTAT DELITTIPS, 2006-2008, 15 aree: 45 confronti, 0 differenze.
- Comune ds564 contro ISTAT, 2006-2023: 18 confronti, 0 differenze.
- Omicidi di mafia in Lombardia, somma del file contro tavola ISTAT per quinquenni 1983-2002: 10, 61, 10, 4 in entrambi.
- Italia, file storico contro report 2018, 1983-2003: differenze di 1 caso nel 1983 e nel 1991.
- Somma dei moventi = totale in tutte le righe. Tavole regionali: somma delle relazioni = totale.
- Polizia contro certificati di morte, area milanese 2003-2023: correlazione 0,93; somme 642 e 612; scarto massimo 9 in un anno. Italia: correlazione 0,99, morti = 86% dei casi di polizia.
- Comune, polizia contro ds337, 2004-2011: somme 152 e 150, ma correlazione anno per anno solo 0,57: con numeri così piccoli il singolo anno non regge.
- Verifica esterna, solo come cifre citate (vedi "Incidente da sapere"): studio dell'Istituto di medicina legale di Milano (Legal Medicine 68, 2024, doi 10.1016/j.legalmed.2024.102433, CC BY), autopsie nel "distretto di Milano": massimo 83 nel 1991, tasso 2,21. Polizia, area milanese 1991: 86 e 2,19. L'area del distretto non è definita.

## Risultati
- **Area milanese.** Massimo 96 omicidi nel 1990 (2,44 per 100.000), minimo 13 nel 2020. Media 1990-92: 88 l'anno, 2,24. Media 2020-24: 18 l'anno, 0,41. Il tasso scende dell'82%; in Italia da 3,03 a 0,54, anche lì -82%.
- **Sotto la media italiana** in 35 anni su 42 (eccezioni 2003, 2006-2009, 2014, 2017). Rapporto con l'Italia: 0,66 nel 1983-87, 0,85 nel 2013-24.
- **Altre province**, tasso 1988-92 e 2018-24: area milanese 1,98 e 0,44; Roma 1,42 e 0,51; Torino 1,53 e 0,55; Bologna 1,81 e 0,52; Firenze+Prato 0,61 e 0,48; Napoli 7,20 e 0,98; Palermo 5,09 e 0,52; Catania 9,98 e 0,70.
- **Comune.** 22 nel 2004, 6 nel 2024. Media 20 l'anno nel 2004-08 (1,54), 7,7 nel 2019-24 (0,55). Peso del comune sull'area: dal 52% al 41%. Grandi comuni 2021-24: Milano 0,57 (31 casi), sesta su 12 dal valore più alto; Napoli 1,99, Bari 0,87, Bologna 0,77, Roma 0,52, Palermo 0,40. Pochi casi spostano molto la posizione.
- **Moventi**, provincia pubblicata, 1988-92: 389 omicidi, 48 di mafia (12%), 35 "onore o passione", 17 rapina, 289 "altri motivi" (74%). La voce residua è enorme: il movente dice poco.
- **Tentati.** Area milanese: 80 l'anno nel 1983-92, 65 nel 2020-24 (-19%), contro -71% dei consumati. Da 1,3 a 3,6 tentati per ogni consumato. Non si può dire perché.
- **Donne e uomini**, certificati di morte, area milanese, media annua 2003-07 e 2018-23: donne 13,2 e 6,0; uomini 25,8 e 11,5; quota di donne 33,8% e 34,3%. Italia: donne 149,6 e 97,2; uomini 430,0 e 164,3; quota 25,8% e 37,2%.
- **In famiglia**, Italia: partner, ex partner e parenti 135 nel 2002, 152 nel 2024 (donne 98 e 99); tutti gli altri 507 e 175. Lombardia: 24 su 43 (2019), 19 su 41 (2023), 20 su 45 (2024); tra le donne 16 su 18, 10 su 13, 10 su 14.

## Numeri che girano, confrontati
- "In media 150 omicidi l'anno a Milano tra anni Settanta e Ottanta" (Il Post 2024 e altri, senza fonte): nei dati di polizia il massimo dell'area è 96 e la media 1983-92 è 62,7. Gli anni Settanta non si possono controllare. Consumati più tentati fanno 127 l'anno nel 1983-89: è solo un'ipotesi sull'origine del numero.
- "Negli anni 80 50 omicidi l'anno, oggi meno di 10" (il sindaco, Il Giorno, 4/6/2026, nessuna area indicata): l'area milanese fa 51,9 nel 1983-89 e 18 nel 2020-24; il comune 7,7 nel 2019-24. Il comune degli anni Ottanta non è disponibile, quindi la frase non si può verificare; sulla stessa area il confronto è 52 contro 18.
- Tasso provinciale 2,8 nel 1984 e 3,1 nel 1992 "record" (Il Post 2016, rimanda a un rapporto del Ministero non trovato): qui 1,69 e 2,09, e il massimo è il 1990. Differenza non spiegata.

## Limiti dei dati
1. **Prima del 1983 Milano non c'è.** Gli Annuari di statistiche giudiziarie ISTAT (dal 1955) sono su `ebiblio.istat.it`, ma non li ho raggiunti: con lo User-Agent dichiarato il PDF rimanda a una pagina di avviso di manutenzione con date del 2014-2015 (due prove nella giornata) e dal programma Python la connessione cifrata fallisce. Una lettura con WebFetch è stata negata da un controllo dei permessi. Non ho cambiato User-Agent né altro. Non so se quei volumi abbiano la tavola per provincia: dal risultato di ricerca si vede solo che il volume 1976 ha una sezione sui delitti denunciati.
2. **Comune prima del 2004:** non trovato (CKAN: nessun dataset "omicidi"; "annuario" dà un solo dataset, sulle imprese). Stimarlo con la quota sull'area sarebbe un'invenzione.
3. **Cambio di metodo nel 2004:** dal modello 165 alla banca dati SDI; ISTAT avverte che la serie può non essere omogenea. Non si vede un gradino netto (Italia 712 e 714; area milanese 49 e 35, con calo simile nei certificati di morte), ma sulla pagina va segnato.
4. **Più conteggi per lo stesso anno.** Italia 2024: 326 ISTAT, 327 DCPC-ISTAT, 314 Ministero a gennaio 2025, 335 Ministero a gennaio 2026. I dati si aggiornano dopo l'estrazione.
5. **Certificati di morte:** registrano il decesso, non il reato; luogo e residenza danno numeri diversi (provincia di Milano 2004: 34 e 22). Non ho spiegato il valore basso del 2023 (10 contro 16 di polizia).
6. **Sesso:** per l'area milanese la serie viene solo dai certificati di morte; i dati di polizia per provincia esistono solo dal 2022. Non ho scaricato la popolazione per sesso: quote e conteggi, non tassi.
7. **Famiglia:** per Milano non esiste. Lombardia solo tre anni qui; le tavole regionali 2020-2022 non le ho cercate. I primi anni sono deboli: nessun "ex partner" nel 2002-03, 218 autori non identificati nel 2002 e 29 nel 2024, quindi il confronto 2002-2024 può dipendere anche da questo. Le tavole 2012-15 e 2016-18 (solo tassi) non sono state pulite.
8. **Confini:** Firenze sommata a Prato. Bari esclusa dal confronto tra province (nel 2011 nasce la BAT); resta tra i comuni. Tassi dei grandi comuni su popolazione implicita, quelli di `comune_milano_2003_2024.csv` su residenti ds27 (2024 implicita): non identici.
9. **Valori strani non spiegati:** Milano 1989, 14 preterintenzionali e 7 infanticidi; 2000, 6 infanticidi. Non sono sommati agli omicidi consumati.
10. **Terrorismo e moventi:** pubblicare solo per periodi, perché per singolo anno una riga può coincidere con un fatto riconoscibile. Con dati dal 1983 questa serie non racconta gli anni di piombo: per quello c'è `violenza-politica/`.
11. **Nessuna causa.** I dati dicono quanti, non perché.

## Incidente da sapere
Il PDF dello studio di medicina legale (`air.unimi.it`, licenza CC BY) è stato scaricato una volta prima di leggere il robots.txt del sito. Dopo, un controllo filtrato ha mostrato righe `Disallow: /` vicino a `User-agent: *`; poi il server non ha più risposto e non ho potuto chiarire a chi si applichino. Per prudenza il file e il testo estratto sono stati cancellati. Restano solo le cifre citate sopra, presenti anche nel risultato di ricerca web. Altri robots.txt: `www.istat.it` nessun divieto; `esploradati.istat.it` non ne ha (risponde la pagina dell'app); `www.interno.gov.it` vieta solo `/sites/README.txt`; `ebiblio.istat.it` 404; `dati.comune.milano.it` nessuna riga rilevante trovata.

## Cercato e non trovato
- Dati sotto il comune: nessuno (già in `reati-citta/`).
- Dati aperti del Ministero per provincia: nessuno; i report trimestrali sono nazionali.
- Serie annuale su Milano in letteratura o dalla Questura: nessuna in due ricerche; solo cifre sparse in stampa, non usate come dati.
- Sole 24 Ore: non cercato per gli anni vecchi; i suoi dati recenti sono esclusivi del Ministero (`reati/NOTE.md`).
- `app4-capoluoghi` (report 2018): è un'immagine, senza numeri. `raw/istat_storia_dati/6_Storia_delle_fonti_Giustizia.pdf` è in realtà una pagina HTML: ignorare.

## Come rifare
Con `python -I -X utf8` e percorsi assoluti, da una cartella fuori da `raw/`: `scripts/scarica.py <raw> <lista.tsv> [pausa]` con `scripts/lista*.tsv`; `01_estrai_1983_2003.py <omicidi>`; `02_estrai_2000_2008.py <omicidi>`; `03_serie.py <omicidi> <milano-in-dati>`; `04_riepilogo.py <omicidi>`.
