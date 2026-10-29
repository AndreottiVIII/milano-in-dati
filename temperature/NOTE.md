# Temperature Milano Brera — NOTE di scarico (fase 1, solo download)

Data di scarico: 2026-10-29. Nessuna registrazione fatta, nessun account creato. Berkeley Earth (richiede registrazione) NON usato.
Tutti i dati grezzi sono in `raw/`. I programmi sono in `scripts/`. I controlli di copertura sono in `controlli/`.
Le unità: ECA&D e GHCN-D danno i gradi in decimi di °C (es. -36 = -3,6 °C). ARPA dà i gradi interi con decimali.

## In breve

- La serie lunga giornaliera 1763-2008 esiste ed è aperta (senza registrazione): massime (TX) e minime (TN) dal 1763-01-01 al 2008-11-30, medie (TG) idem.
- È la serie di Maurizio Maugeri (Università di Milano), passata a ECA&D. GHCN-D (NOAA) ne ha una copia identica per TMAX/TMIN: 89.686 giorni TMAX e 89.697 TMIN, tutti uguali valore per valore a ECA&D (confronto fatto, 0 differenze).
- Per il periodo recente c'è ARPA Lombardia, sensore 5897 "Milano v.Brera": dal 1990-03-19 al 2026-10-29, licenza CC0. Con ARPA la sovrapposizione con la serie lunga è di quasi 19 anni (1990-2008).
- Il "buco 1999": NON c'è. La serie Maugeri/ECA&D continua senza interruzioni fino al 2008-11-30, e ARPA copre dal 1990. Ma attenzione alla trappola 1 qui sotto: le due serie si separano di circa 3 °C dopo il 2000.

## Fonte 1 — GHCN-Daily (NOAA), stazione ITE00100554 "MILAN"

- URL: https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/ITE00100554.csv.gz (più `ghcnd-stations.txt`, `ghcnd-inventory.txt`, `readme.txt`, `status.txt` nella stessa cartella ftp).
- File: `raw/ghcnd/ITE00100554.csv.gz` (0,96 MB), `ghcnd-stations.txt` (10,9 MB), `ghcnd-inventory.txt` (34,7 MB), `readme.txt`, `status.txt`.
- Campo `elem`: TMAX dal 1763-01-01 al 2008-11-30 (89.686 righe), TMIN stesso periodo (89.697 righe), PRCP (precipitazioni) dal 1858-01-01 al 2008-12-01 (55.087 righe). Coordinate 45,4717 N 9,1892 E, quota 150 m (`ghcnd-stations.txt`).
- Completezza (da `scripts/inspect_ghcnd.py`): su 89.819 giorni possibili mancano 133 TMAX e 122 TMIN. Gli anni 1779 (342 giorni TMAX), 2007 (331) e 2008 (335) sono incompleti.
- Altre stazioni "Milano" in GHCN-D: nessuna italiana (le altre "MILAN" sono negli USA/Canada/Australia). Linate e Malpensa non sono in GHCN-D come stazioni a sé.
- Il campo `sflag` è sempre `E`: secondo `readme.txt` significa "dati ECA&D non-blended". Cioè GHCN-D non è una fonte indipendente: è la stessa serie di ECA&D.
- Controllo qualità NOAA (campo `qflag`): TMAX 482 giorni con flag `I` (incoerenza interna) e 17 con `N`; TMIN 475 con `I` e 17 con `N`. Sono concentrati nel 1700 (es. 1788, 1784, 1795 con ~11 giorni l'anno). Da decidere cosa farne più avanti.
- Licenza: la pagina NCEI di GHCN-Daily non riporta alcuna licenza né termini. I dati italiani vengono però da ECA&D: per prudenza vale il vincolo ECA&D (vedi sotto). **Ripubblicare il grezzo: no (solo programmi e risultati).**

## Fonte 2 — ECA&D (European Climate Assessment & Dataset, ecad.eu)

- URL pagina: https://www.ecad.eu/dailydata/predefinedseries.php ; archivi: `https://knmi-ecad-assets-prd.s3.amazonaws.com/download/ECA_{blend|nonblend|homblend}_{tx|tn|tg}.zip`. Nessuna registrazione richiesta per i dati di stazione (policy punto 3a).
- Gli zip interi pesano 187-895 MB l'uno (9 zip, circa 5,2 GB in tutto). Per non scaricare 5 GB di tutta Europa ho letto solo l'indice dello zip e scaricato i soli file di Milano (HTTP Range, programma `scripts/ecad_extract.py`): la roba grezza è identica a quella degli zip. Totale scaricato circa 12 MB. Se serve l'archivio intero, gli URL sono quelli sopra.
- File di zip scaricati (data file creazione 2026-10-12, `date_timestamp.txt`; gli homblend sono del 2019-04-08):
  - `raw/ecad/nonblend_{tx,tn,tg}/`: serie originali per fonte (SOUID). Maugeri: `TX_SOUID105248.txt`, `TN_SOUID105247.txt`, `TG_SOUID105249.txt` (3,2 MB ciascuno). Poi le serie ARPA "Milano V.BRERA" già dentro ECA&D (`TX_SOUID180713`, `TN_SOUID180712`, `TG_SOUID178822`, `TX_SOUID178821`, `TN_SOUID178820`) e Via Marche/Via Feltre (180667, 180785, 178864 ecc.).
  - `raw/ecad/blend_{tx,tn,tg}/`: serie "fuse" di ECA&D. STAID 173 "MILAN" (3,3 MB), STAID 11493 "MILANO (V.BRERA)" e 11425 "MILANO (LAMBRATE)" (0,47 MB ciascuno).
  - `raw/ecad/homblend_{tx,tn,tg}/TX_STAID000173.txt` ecc.: serie omogeneizzata di Squintu et al. 2019 (Int. J. Climatol. 39, 1243-1261, doi:10.1002/joc.5874).
  - In ogni cartella: `stations.txt`, `sources.txt`, `elements.txt` (metadati ECA&D).
- Periodo e completezza (da `controlli/copertura_completa.txt`, campo valido = valore diverso da -9999 e `Q_` diverso da 9):
  - Maugeri non-blended `TX_SOUID105248.txt`: 1763-01-01 → 2008-11-30, 89.686 giorni validi su 89.819 (133 mancanti). Buchi lunghi: 2004-05-21→06-04 (15 giorni), 2007-10-02→10-31 (30 giorni). Anni con mancanze: 1779 (23 giorni), 2007 (34), 2004 (15). TN: 89.697 validi (122 mancanti). TG: 89.759 validi (60 mancanti).
  - Blended STAID 173 `TX_STAID000173.txt`: 1763-01-01 → 2017-12-05, 93.037 giorni validi, 74 mancanti nel mezzo. Dopo il 2008-11-30 NON è più Brera (vedi trappola 2). Dopo il 2017-12-05 non ci sono dati per la 173.
  - Blended STAID 11493 "MILANO (V.BRERA)" `TX_STAID011493.txt`: 1989-01-01 → 2026-09-30, 13.425 validi su 13.787. Buchi: 2017-12-06→2018-06-19 (196 giorni), 2018-07-23→08-11, 2019-10-11→10-25, 2021-08-10→10-21 (73).
  - Omogeneizzata STAID 173: TX dal 1840-01-01, TN dal 1832-01-01, TG dal 1781-01-01, tutte fino al 2008-11-30; 161 TX, 171 TN, 60 TG giorni mancanti (`controlli/copertura_completa.txt`).
- Metadati stazione (`stations.txt` STAID 173): "MILAN", +45:28:18 N, +009:11:21 E, 150 m. STAID 11493 "MILANO (V.BRERA)": +45:28:23, +009:11:21, 122 m (stesso punto, 5" di differenza).
- Qualità: `Q_` 0 valido, 1 sospetto, 9 mancante. Nella 173 TX: 1 solo giorno sospetto; nelle altre poco. Nella omogeneizzata il campo `Q_` vale -9 per tutti (marcatura propria), e i mancanti sono -9999.
- Licenza: la dicitura nei file dice "non-commercial research and education"; nei file `stations.txt` c'è invece "used freely provided source acknowledged". La Data Policy (https://www.ecad.eu/documents/ECAD_datapolicy.pdf, punto 1b) dice: dati "strictly for use in non-commercial research and education projects only", con citazione obbligatoria (Klein Tank et al. 2002, Int. J. Climatol. 22, 1441-1453) e per le omogeneizzate Squintu et al. 2019. **Ripubblicare il grezzo: no** (non è un permesso esplicito di ridistribuzione; sito pubblico del progetto = rischio). Solo programmi e risultati derivati, con citazione. Se vogliamo certezza: scrivere a eca@knmi.nl (suggerito dal punto 1b della policy).

## Fonte 3 — ARPA Lombardia, dati.lombardia.it (Socrata)

- Anagrafica: dataset `nf78-nj6b` "Stazioni Idro Nivo Meteorologiche" → `raw/arpa/nf78-nj6b_stazioni.csv` (0,26 MB, 1.462 sensori). Trovata la stazione **Milano v.Brera** (idstazione 620, quota 122 m, 45,47166 N 9,18911 E) con il sensore **temperatura idsensore 5897**, `datastart` 1990-03-19, in funzione (`datastop` vuoto, `storico` N).
- Dati temperatura (non esistono archivi "Dati sensori meteo <anno>": i dati di temperatura sono in tre archivi per periodo più uno del periodo in corso), scaricati con `scripts/arpa_download.py` filtrando `idsensore='5897'`:
  - `6eu4-4tja` "Temperatura fino al 2010" → `raw/arpa/brera_5897_6eu4-4tja.csv` (7,6 MB, 174.516 righe, 1990-03-19 01:00 → 2011-01-01 00:00, passo orario).
  - `d4kj-kbpj` "Temperatura dal 2011 al 2020" → `brera_5897_d4kj-kbpj.csv` (16,5 MB, 379.155 righe, 2011-01-01 01:00 → 2021-01-01 00:00, orario).
  - `w9wd-u6jh` "Temperatura dal 2021" → `brera_5897_w9wd-u6jh.csv` (11,8 MB, 271.088 righe, 2021-01-01 00:10 → 2026-03-01 00:00, ogni 10 minuti).
  - `647i-nhxk` "Dati sensori meteo" (mese in corso, in realtà dal 2026-03-30) → `brera_5897_647i-nhxk.csv` (1,5 MB, 30.683 righe, 2026-03-30 00:10 → 2026-10-29 12:20, ogni 10 minuti).
  - Totale 855.442 righe, nessun timestamp duplicato né sovrapposto tra i file.
- Campi: `idsensore`, `data`, `valore`, `stato` (e `idoperatore` nell'ultimo file). Orario in **ora solare**, riferito alla **fine** dell'intervallo di misura (dalle descrizioni dei dataset).
- Completezza (da `controlli/copertura_completa.txt`): 12.808 giorni con almeno un dato valido dal 1990-03-19 al 2026-10-29, 566 giorni senza dati. Buchi lunghi: 1990-04-09→07-09 (92 giorni), 1993-06-04→10-14 (133), 2010-07-18→10-04 (79), 2013-09-05→10-13 (39), 2014-02-26→04-13 (circa 46, con 1 giorno in mezzo), 2026-03-01→03-29 (29 giorni, tra la fine di `w9wd-u6jh` e l'inizio di `647i-nhxk`). Anni quasi interi: tutti dal 1994 al 2009, e 2015-2025. Anni con più buchi: 1990 (195 giorni, parte dal 19 marzo), 1993 (232), 2010 (280), 2013-2014 (315-319).
- Licenza: CC0 1.0 (pubblico dominio) per tutti i dataset, attribuzione "ARPA Lombardia" (`/api/views/<id>.json`, campo `license`). **Ripubblicare il grezzo: sì**, senza vincoli.
- Per i confronti futuri, nella stessa anagrafica ci sono altri sensori di temperatura a Milano non scaricati ora: Zavattari 5920 (dal 1989), Juvara 5909 (1989), Marche 5911 (1989), Feltre 8162 (2000), Lambrate 2001 (2001).

## Domanda: buco tra 1999 e l'inizio dei dati ARPA?

No. La serie Maugeri (ECA&D/GHCN-D) va senza interruzione fino al 2008-11-30, quindi copre tutto il 1999. ARPA Brera inizia nel 1990-03, quindi le due serie si sovrappongono per 1990-03 → 2008-11. Dopo il 2008-11-30 la serie lunga finisce: per il periodo successivo vale ARPA (dal 2008-12 in poi, con i buchi sopra).

## Cambi di stazione e strumenti DOCUMENTATI (da citare, non ancora analizzati)

Fonti trovate: Maugeri, Buffoni e Chlistovsky 2002 (storia delle osservazioni, Climatic Change 53, 101-117, doi:10.1023/A:1014970825579); Maugeri, Buffoni, Delmonte e Fassina 2002 (completamento e omogeneizzazione, Climatic Change 53, 119-149, doi:10.1023/A:1014923027396); Meda, Asnaghi e Ricciardi, Nimbus 49-50 (cronologia di Brera, copia in `raw/letteratura/nimbus_4904_brera.pdf` e `.txt`). I due articoli del 2002 non sono ad accesso aperto (il repository dell'Università di Milano non ha il pdf): ho letto solo gli abstract. I dettagli esatti degli spostamenti 1763-1998 stanno nel testo completo dei due articoli e non li ho.

- 1763: inizio delle osservazioni, padre Luigi Lagrange (scritto "La Grange" in Nimbus) alla specola di Palazzo Brera, 148 m (Nimbus).
- 1763-1804: periodo più problematico per omogeneità (abstract Maugeri et al. 2002).
- 1835: riforma di Francesco Carlini, strumenti in una collocazione più idonea e più osservazioni al giorno: è il principale punto di rottura, divide la serie in due grandi periodi (abstract Maugeri et al. 2002; Nimbus).
- 1948: osservazioni affidate a meteorologi professionisti (Luigi Santomauro) (Nimbus).
- 1963-oggi: anch'esso indicato come periodo problematico (abstract Maugeri et al. 2002).
- 1971: l'Osservatorio astronomico sospende la meteorologia; le osservazioni continuano a Palazzo Brera con un osservatorio meteorologico autonomo (associazione privata dal 1983) (Nimbus).
- 1987: l'osservatorio meteorologico autonomo si trasferisce in piazza Duomo (Osservatorio Milano-Duomo, tetto, 154 m; fino al 1994 "Brera-Duomo"); nello stesso anno Brera reintroduce la meteorologia con una stazione automatica (Nimbus). Il sensore ARPA 5897 parte nel 1990-03-19.
- Le coordinate ECA&D della "MILAN" (150 m) e quelle ARPA Brera (122 m) sono praticamente lo stesso punto (45,47166 / 9,18911): differenza di quota di 28 m, perché sono sensori/fonti diversi.
- Dopo il 1998: non ho trovato documentazione sul cambio di sito o strumento. Brunetti et al. 2006 (Int. J. Climatol., "Temperature and precipitation variability in Italy in the last two centuries", tabella delle stazioni) elenca Milano fino al 2003, quindi la serie era stata estesa oltre il 1998 (non verificato il come).

## Sovrapposizioni utili per la fase successiva

- Maugeri (ECA&D `TX_SOUID105248`/`TN_SOUID105247`) e ARPA Brera (5897): 1990-03-19 → 2008-11-30, quasi 19 anni, circa 6.400 giorni con dati di entrambe le serie. Nel file ECA&D ci sono anche le serie ARPA Brera (`TX_SOUID180713` ecc.): coincidono con il sensore 5897 (differenza media 0,00 °C 1995-2013, `controlli/`).
- Stazioni vicine con dati dal 1989: Via Marche, Zavattari, Juvara (ARPA, in ECA&D come serie 0-0 LT oraria e come TX3/TG3).
- Linate (SOUID 916080, GTS) è in ECA&D solo nelle serie fuse (STAID 11425 e 11493): 1982-01-12 → 2026-09-30. Linate è a circa 7 km, 103 m, aeroporto: non è Brera.

## Trappole dei dati (per la rubrica)

1. **La serie lunga e il sensore ARPA si separano di circa 3 °C dopo il 2000.** Media annua della differenza ARPA Brera meno Maugeri, giornaliera, da `controlli/sovrapposizione_ARPA_Maugeri_annuale.csv`: massime 1994-2000 tra -0,3 e -0,7 °C; 2001 -1,7; 2002 -2,9; 2006 -3,5 °C; minime da +1,1 (1994-1999) a -2,3 (2006). Medie annue delle massime (nostri conti sugli stessi file): Maugeri 18,4 °C nel 2000, 22,1 °C nel 2006; ARPA 17,8 e 18,5. Non so ancora perché: forse la serie Maugeri dopo il 1998 è un'altra fonte o un altro punto (non omogeneizzata), o è il sensore ARPA a derivare. **Da chiarire prima di mettere insieme le due serie.**
2. **La serie omogeneizzata ECA&D (Squintu 2019) è più calda della grezza prima del 2001.** `TX_STAID000173.txt` omogeneizzata meno non-blended: es. medie annue massime 1990 20,93 contro 18,57 °C; dal 2002 le due coincidono (20,31 = 20,31). Cioè l'omogeneizzazione ha portato i valori vecchi al livello della parte recente, che è quella sospetta (trappola 1).
3. **La serie fusa "MILAN" (STAID 173) cambia stazione senza dirlo.** Fino al 2008-11-30 è Maugeri; poi è Via Marche (fonti 80667 fino al 2014-06-18, poi 78863 fino al 2017-12-05) e Via Feltre (fonte 80785, 48 giorni); il nome resta "MILAN". Fonte: colonna `SOUID` di `TX_STAID000173.txt` e `sources.txt` (conteggi in `controlli/copertura_completa.txt`). Via Marche e Via Feltre servono anche a riempire alcuni giorni mancanti della serie Maugeri tra 2001-06-07 e 2008 (fonte 80667: 2.038 giorni in tutto, di cui la gran parte dopo il 2008-11-30). Ancora: la serie fusa "MILANO (V.BRERA)" (STAID 11493) dal 2017-12-06 è solo Milano/Linate (fonti 916080 e 916081), con un buco di 196 giorni (2017-12-06 → 2018-06-19): non è Brera.
4. **GHCN-D non è indipendente da ECA&D.** Stessi identici valori (0 differenze su 89.686 TMAX e 89.697 TMIN) e il flag di fonte `E` lo dice.
5. **Unità e sentinelle diverse.** ECA&D e GHCN-D: decimi di °C, -9999 = mancante (ECA&D, insieme a `Q_`=9). ARPA: °C con decimali, e nei dati compare il valore -999,0 come "mancante" con `stato` vuoto: 2.518 righe in `6eu4-4tja`, 5.045 in `d4kj-kbpj`, 1.836 in `w9wd-u6jh`. Vanno scartate le righe con `stato` diverso da `VA`.
6. **Passo temporale e ora ARPA cambiano.** Orario fino al 2020, ogni 10 minuti dal 2021; ora solare; il timestamp è la fine dell'intervallo, quindi 00:00 appartiene al giorno prima. Le massime e minime giornaliere da dati orari non sono confrontabili con quelle da dati ogni 10 minuti (le massime vere sono più alte di quelle orarie).
7. **Definizione giornaliera diversa.** ECA&D usa codici diversi per l'intervallo di osservazione: Maugeri TX1/TN1 "intervallo non noto", TG5 "mattina→mattina"; le serie ARPA in ECA&D TX14/TN13 "0-0 ora locale da dati orari", TX3 "0-0 UT" (`elements.txt`). Le massime non sono da mettere insieme senza controllare.
8. **ECA&D ha intestazioni diverse nello stesso file di licenza.** `stations.txt` dice "usabili liberamente", `sources.txt` e i file dati dicono "solo ricerca e istruzione non commerciale". Vale la più restrittiva (policy punto 1b).
9. **Il dataset ARPA "mese in corso" non è solo un mese.** `647i-nhxk` contiene da 2026-03-30; se viene aggiornato a inizio mese, i dati più vecchi passano nell'archivio semestrale e il buco di marzo 2026 può chiudersi: ricontrollare prima di pubblicare.
10. **Nel GHCN-D il flag NOAA `I`/`N` colpisce soprattutto il Settecento** (circa 10 giorni l'anno 1767-1803): possibili letture vere ma insolite, o errori di trascrizione. Da valutare.

## Programmi

- `scripts/inspect_ghcnd.py` (copertura GHCN-D), `scripts/ecad_list_zip.py` e `ecad_extract.py` / `ecad_extract_souid.py` (estrazione dei soli file di Milano dagli zip ECA&D via HTTP Range), `scripts/arpa_download.py` (scarico a pagine da Socrata), `scripts/check_coverage.py` (copertura e buchi), `scripts/overlap_check.py` (differenze annue ARPA-Maugeri).
- Per rilanciare: `python -I scripts/<nome>.py <argomenti>` (gli argomenti sono scritti nella prima riga di ogni programma).

## Cose non fatte / da fare

- Nessuna analisi di omogeneità (fatta solo la tabella di confronto annuale come controllo).
- Non ho scaricato i testi completi degli articoli Maugeri 2002 (non aperti): chi ha accesso all'università o a Springer può leggere le date esatte dei cambi.
- Non scaricati gli archivi ECA&D interi (5,2 GB, tutta Europa).
- Non scaricati gli altri sensori ARPA di Milano (Zavattari, Juvara, Marche, Feltre, Lambrate).
