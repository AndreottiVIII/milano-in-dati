# Milano in dati — JOURNAL

Diario del progetto: fonti, date di scarico, licenze, scelte, problemi.
Ogni problema trovato nei dati va annotato: diventa materiale per la rubrica "trappole dei dati".

## Decisioni generali

- 2026-10-29 — Cartella `milano-in-dati/`, repository GitHub pubblico `AndreottiVIII/milano-in-dati`, sito `andreottiviii.github.io/milano-in-dati` (scelti da Davide).
- 2026-10-29 — Filoni indipendenti (prima 4, poi 8: aria, Area C, bici/auto/mezzi, Scala aggiunti lo stesso giorno), ognuno nella sua sottocartella: `temperature/`, `donne-nelle-vie/`, `beni-culturali/`, `elezioni/`.
- 2026-10-29 — Regola licenze: se una fonte non permette di ripubblicare, nel repo vanno solo programmi e risultati, non i dati grezzi.
- 2026-10-29 — Divisione del lavoro: Opus coordina e fa il delicato, Sonnet scrive il codice, Sonnet medio il meccanico, Haiku solo controlli di testo.

## 1. Temperature (Milano Brera, dal 1763)

- **Fonti:** GHCN-Daily (NOAA, stazione ITE00100554), ECA&D (serie Maugeri 1763-2008 e fuse/omogeneizzate), ARPA Lombardia (sensore 5897 Milano v.Brera, dal 1990).
- **Data di scarico:** 2026-10-29.
- **Licenze:** GHCN-D e ECA&D solo ricerca non commerciale, grezzo non ripubblicabile; ARPA Lombardia CC0, ripubblicabile.
- **Trappole dei dati:** 10 trappole, elencate più sotto nella sezione "Trappole dei dati (per la rubrica)".

### Fase 1 — scarico (2026-10-29)

**Temperature Milano Brera — NOTE di scarico (fase 1, solo download)**

Data di scarico: 2026-10-29. Nessuna registrazione fatta, nessun account creato. Berkeley Earth (richiede registrazione) NON usato.
Tutti i dati grezzi sono in `raw/`. I programmi sono in `scripts/`. I controlli di copertura sono in `controlli/`.
Le unità: ECA&D e GHCN-D danno i gradi in decimi di °C (es. -36 = -3,6 °C). ARPA dà i gradi interi con decimali.

#### In breve

- La serie lunga giornaliera 1763-2008 esiste ed è aperta (senza registrazione): massime (TX) e minime (TN) dal 1763-01-01 al 2008-11-30, medie (TG) idem.
- È la serie di Maurizio Maugeri (Università di Milano), passata a ECA&D. GHCN-D (NOAA) ne ha una copia identica per TMAX/TMIN: 89.686 giorni TMAX e 89.697 TMIN, tutti uguali valore per valore a ECA&D (confronto fatto, 0 differenze).
- Per il periodo recente c'è ARPA Lombardia, sensore 5897 "Milano v.Brera": dal 1990-03-19 al 2026-10-29, licenza CC0. Con ARPA la sovrapposizione con la serie lunga è di quasi 19 anni (1990-2008).
- Il "buco 1999": NON c'è. La serie Maugeri/ECA&D continua senza interruzioni fino al 2008-11-30, e ARPA copre dal 1990. Ma attenzione alla trappola 1 qui sotto: le due serie si separano di circa 3 °C dopo il 2000.

#### Fonte 1 — GHCN-Daily (NOAA), stazione ITE00100554 "MILAN"

- URL: https://www.ncei.noaa.gov/pub/data/ghcn/daily/by_station/ITE00100554.csv.gz (più `ghcnd-stations.txt`, `ghcnd-inventory.txt`, `readme.txt`, `status.txt` nella stessa cartella ftp).
- File: `raw/ghcnd/ITE00100554.csv.gz` (0,96 MB), `ghcnd-stations.txt` (10,9 MB), `ghcnd-inventory.txt` (34,7 MB), `readme.txt`, `status.txt`.
- Campo `elem`: TMAX dal 1763-01-01 al 2008-11-30 (89.686 righe), TMIN stesso periodo (89.697 righe), PRCP (precipitazioni) dal 1858-01-01 al 2008-12-01 (55.087 righe). Coordinate 45,4717 N 9,1892 E, quota 150 m (`ghcnd-stations.txt`).
- Completezza (da `scripts/inspect_ghcnd.py`): su 89.819 giorni possibili mancano 133 TMAX e 122 TMIN. Gli anni 1779 (342 giorni TMAX), 2007 (331) e 2008 (335) sono incompleti.
- Altre stazioni "Milano" in GHCN-D: nessuna italiana (le altre "MILAN" sono negli USA/Canada/Australia). Linate e Malpensa non sono in GHCN-D come stazioni a sé.
- Il campo `sflag` è sempre `E`: secondo `readme.txt` significa "dati ECA&D non-blended". Cioè GHCN-D non è una fonte indipendente: è la stessa serie di ECA&D.
- Controllo qualità NOAA (campo `qflag`): TMAX 482 giorni con flag `I` (incoerenza interna) e 17 con `N`; TMIN 475 con `I` e 17 con `N`. Sono concentrati nel 1700 (es. 1788, 1784, 1795 con ~11 giorni l'anno). Da decidere cosa farne più avanti.
- Licenza: la pagina NCEI di GHCN-Daily non riporta alcuna licenza né termini. I dati italiani vengono però da ECA&D: per prudenza vale il vincolo ECA&D (vedi sotto). **Ripubblicare il grezzo: no (solo programmi e risultati).**

#### Fonte 2 — ECA&D (European Climate Assessment & Dataset, ecad.eu)

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

#### Fonte 3 — ARPA Lombardia, dati.lombardia.it (Socrata)

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

#### Domanda: buco tra 1999 e l'inizio dei dati ARPA?

No. La serie Maugeri (ECA&D/GHCN-D) va senza interruzione fino al 2008-11-30, quindi copre tutto il 1999. ARPA Brera inizia nel 1990-03, quindi le due serie si sovrappongono per 1990-03 → 2008-11. Dopo il 2008-11-30 la serie lunga finisce: per il periodo successivo vale ARPA (dal 2008-12 in poi, con i buchi sopra).

#### Cambi di stazione e strumenti DOCUMENTATI (da citare, non ancora analizzati)

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

#### Sovrapposizioni utili per la fase successiva

- Maugeri (ECA&D `TX_SOUID105248`/`TN_SOUID105247`) e ARPA Brera (5897): 1990-03-19 → 2008-11-30, quasi 19 anni, circa 6.400 giorni con dati di entrambe le serie. Nel file ECA&D ci sono anche le serie ARPA Brera (`TX_SOUID180713` ecc.): coincidono con il sensore 5897 (differenza media 0,00 °C 1995-2013, `controlli/`).
- Stazioni vicine con dati dal 1989: Via Marche, Zavattari, Juvara (ARPA, in ECA&D come serie 0-0 LT oraria e come TX3/TG3).
- Linate (SOUID 916080, GTS) è in ECA&D solo nelle serie fuse (STAID 11425 e 11493): 1982-01-12 → 2026-09-30. Linate è a circa 7 km, 103 m, aeroporto: non è Brera.

#### Trappole dei dati (per la rubrica)

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

#### Programmi

- `scripts/inspect_ghcnd.py` (copertura GHCN-D), `scripts/ecad_list_zip.py` e `ecad_extract.py` / `ecad_extract_souid.py` (estrazione dei soli file di Milano dagli zip ECA&D via HTTP Range), `scripts/arpa_download.py` (scarico a pagine da Socrata), `scripts/check_coverage.py` (copertura e buchi), `scripts/overlap_check.py` (differenze annue ARPA-Maugeri).
- Per rilanciare: `python -I scripts/<nome>.py <argomenti>` (gli argomenti sono scritti nella prima riga di ogni programma).

#### Cose non fatte / da fare

- Nessuna analisi di omogeneità (fatta solo la tabella di confronto annuale come controllo).
- Non ho scaricato i testi completi degli articoli Maugeri 2002 (non aperti): chi ha accesso all'università o a Springer può leggere le date esatte dei cambi.
- Non scaricati gli archivi ECA&D interi (5,2 GB, tutta Europa).
- Non scaricati gli altri sensori ARPA di Milano (Zavattari, Juvara, Marche, Feltre, Lambrate).

### Fase 2 — la discrepanza e la serie unica (2026-10-29)

- **Sbagliata è la serie storica (Maugeri), non ARPA.** Confrontata con la media di tre altre stazioni ARPA di Milano (Juvara, Marche, Zavattari), Brera ARPA resta piatta dal 1995 al 2007; la serie Maugeri invece si scalda d'estate dal 1995, fa un salto il 21/6/2001 (Maugeri meno Brera sulle massime da +1,06 a +3,54 °C) e un altro di circa 1 °C nella primavera 2006. Nessuno documenta da dove vengano i dati Maugeri dopo il 1998 (l'omogeneizzazione del 2002 si ferma lì). Dettagli e numeri: `temperature/discrepanza/RAPPORTO.md`.
- **Cucitura scelta** (`temperature/splice.json`, costruita da `temperature/discrepanza/scripts/giunzione.py`): Maugeri 1763 → 14/11/1986; Linate (NOAA GSOD) corretto 15/11/1986 → 15/9/1987, durante il trasloco dell'osservatorio; Maugeri 16/9/1987 → 1994; ARPA Brera dal 1995, solo letture orarie, con scarti mensili (`discrepanza/out/giunzione_scarti.csv`); buchi riempiti con la media delle vicine ARPA. Incertezza della giunzione: 0,2-0,4 °C.
- **Problema aperto**: Brera ARPA è più calda delle vicine di 0,5-1,7 °C sulle massime nel 2008-2016. Non corretto: servirebbe un'omogeneizzazione con più stazioni.
- **Trappole dei dati**:
  - La serie "omogeneizzata" di ECA&D prende per buona la parte rotta recente e alza tutto il 1781-2001 di 2-2,5 °C: da non usare.
  - ARPA passa ai dati ogni 10 minuti il 19/3/2014, non nel 2021: con le letture ogni 10 minuti le massime salgono di +0,28 °C.
  - Il codice GHCN-D di Linate (ITM00016080) non esiste.
  - Prima del 1835 le minime Maugeri sono sospette: troppe notti tropicali.
- **Effetto sui numeri**: la differenza tra le normali 1961-90 e 1991-2020 passa da +1,3 °C (cucitura provvisoria) a +0,5 °C. Anno più caldo: 2022, con 16,2 °C.
- **Licenza**: nel sito solo valori aggregati; la serie giornaliera prima del 1995 (ECA&D/GHCN, non ridistribuibile) resta sul PC.

- **2026-10-29, giorno singolo e 2026**: Davide ha deciso di pubblicare anche la serie giornaliera completa (pagina "Un giorno a scelta"), citando Maugeri et al. 2002, ECA&D (Klein Tank et al. 2002), NOAA GHCN-D e GSOD, ARPA; sito non commerciale. Il 2026 (dati fino al 28/10) entra in tutte le tabelle come anno in corso; nelle classifiche annuali c'è un confronto a parte "2026 finora", fatto sugli stessi 271 giorni di calendario per tutti gli anni.
- **Da verificare**: il 2026 risulta il più caldo di sempre nello stesso periodo (19,3 °C contro i 18,7 del 2022). L'estate 2026 a Brera ha una media di 28,1 °C, contro i 27,4 del 2022. Il confronto con le stazioni vicine per il 2026 non è stato possibile: l'API di ARPA ha risposto "too many requests". Da rifare.

## 2. Donne nelle vie

- **Fonti:** OpenStreetMap (Overpass), Wikidata, Comune di Milano (registro civici ds634, vie storiche ds2914), Mapping Diversity (solo controllo).
- **Data di scarico:** 2026-10-29 (dati OSM al 2026-10-29T14:21:50Z).
- **Licenze:** OSM ODbL (share-alike), Wikidata CC0, Comune di Milano CC BY, Mapping Diversity CC BY 4.0 (citare la fonte).
- **Trappole dei dati:** 8 trappole, elencate più sotto nella sezione "4. Trappole dei dati (problemi trovati)".

### Fase 1 — scarico (2026-10-29)

**Donne nelle vie — NOTE fase 1 (scarico + primo conteggio)**

Data di scarico: 2026-10-29. Tutto in `milano-in-dati/donne-nelle-vie/`. Nulla è stato pubblicato, nessun git.
Programmi in `scripts/` (numerati 01-09, si rilanciano in ordine). I dati scaricati sono in `raw/` (copie originali, non modificate). I file ricavati sono in `out/` e nella cartella principale.

#### 1. Fonti scaricate

##### 1.1 OpenStreetMap (strade e tag `name:etymology:wikidata`)
- **Come:** una sola richiesta Overpass (`https://overpass-api.de/api/interpreter`) sull'area del Comune di Milano (relazione amministrativa con `admin_level=8` e `wikidata=Q490`, quindi solo il comune, non la città metropolitana). Contenuto: tutte le `way` con `highway=*` e `name`, più `place=square` e le aree pedonali con nome. Il testo della richiesta è in `scripts/01_overpass.py`.
- **File:** `raw/osm/overpass_milano.json`, 11,26 MB. 31.950 elementi (31.886 `way`, 64 `relation`). Campo `osm3s.timestamp_osm_base` = **2026-10-29T14:21:50Z** (questo è il momento dei dati OSM).
- **Completezza:** una sola richiesta, finita senza errori. Tag tenuti: `name`, `name:etymology`, `name:etymology:wikidata`, `subject:wikidata`, `old_name`, `highway`, `loc_ref`, id dell'elemento (nel JSON c'è tutto).
- **Licenza:** ODbL (OpenStreetMap contributors). Si può ripubblicare, ma con la citazione e con la stessa licenza per i database derivati (obbligo "share-alike"). Regola del JOURNAL: nel repo meglio solo risultati e programmi, non il JSON grezzo.
- **Aggregazione:** `scripts/03_aggregate_osm.py` → `out/osm_strade_aggregate.csv` (una riga per nome). Campi: `name`, `n_elementi`, `highway`, `etymology_wikidata`, `loc_ref_codes`.

##### 1.2 Wikidata (chi è la persona)
- **Come:** query SPARQL a `https://query.wikidata.org/sparql` con User-Agent proprio, blocchi di 150 QID (8 blocchi, pausa di 5 s). Campi chiesti: tipo (P31), sesso (P21), professioni in italiano (P106), anno di nascita (P569), anno di morte (P570), cittadinanza (P27), etichetta e descrizione in italiano. Programma: `scripts/04_wikidata_fetch.py`; lettura: `scripts/07_parse_wikidata.py`.
- **File:** `raw/wikidata/osm_etymology_batches/batch_000.json … batch_007.json` (circa 1,2 MB in tutto) → `out/etimologie_wikidata.csv` (0,15 MB, una riga per QID).
- **Completezza:** chiesti 1.173 QID (tutti i QID unici trovati nel campo `name:etymology:wikidata`, separati da `;`), ricevuti 1.173, nessuno mancante.
- **Licenza:** CC0 (pubblico dominio). Si può ripubblicare liberamente.
- **Secondo scarico, per il matching:** `raw/wikidata/matching_untagged/search_results.json` (1,4 MB, ricerca `wbsearchentities` per 3.047 nomi) e `entities.json` (2,4 MB, dettagli `wbgetentities` di 10.307 candidati). Stessa licenza CC0.

##### 1.3 Comune di Milano — registro dei numeri civici (la fonte ufficiale)
- **URL:** `https://dati.comune.milano.it/dataset/ds634-numeri-civici-coordinate` (CKAN, API `package_show`). Risorsa CSV zip: `…/ds634_civici_coordinategeografiche_20261001_final_csv.zip` (4,35 MB). Ultimo aggiornamento sul portale: 2026-10-04, frequenza mensile.
- **File:** `raw/comune/ds634/ds634_civici_coordinategeografiche_20261001_final.csv` (21,90 MB, 65.160 righe = civici, 41 colonne, separatore `;`) e lo zip originale.
- **Cosa contiene (importante):** una riga per civico, ma ogni via ha un `CODICE_VIA` (numero ufficiale). Vie uniche per `CODICE_VIA`: **4.030**. Colonne utili: `CODICE_VIA`, `TIPO` (Via, Piazza, Viale…), `DENOMINAZIONE` (formato "COGNOME NOME", es. "GENTILE GIOVANNI"), `DESCRITTIVO` (formato "NOME COGNOME"), **`DATA_INTITOLAZIONE`** (formato AAAAMMGG), `STATOVIA` (sempre "Intitolata"), `ANNO_SOPPRESSIONE`.
- **Licenza:** CC BY (campo `license_id` = `cc-by` nella scheda CKAN). Si può ripubblicare citando il Comune di Milano.
- **Limite:** contiene solo le vie che hanno civici. Vie senza civici (alcune piazze, giardini, sottopassi) possono mancare. Nella tabella dei campi non ho trovato la spiegazione ufficiale di `DATA_INTITOLAZIONE` (il "Data Dictionary" della pagina si carica con JavaScript e non l'ho letto): quello che scrivo sulla data è dedotto dai dati.

##### 1.4 Comune di Milano — vie e nomi storici (mappe dal 1884)
- **URL:** `https://dati.comune.milano.it/dataset/ds2914-vie-di-milano-e-corrispondenza-toponomastica-nelle-mappe-storiche-dal-1884`. File: `raw/comune/ds2914/ds2914_vie.csv` (0,01 MB). Licenza CC BY.
- **Contenuto:** solo una selezione di vie (progetto LetMi), con il nome in 10 mappe storiche (1884-2012). Non ha date di intitolazione né codice via (solo un `identificativo` interno). Utile solo come curiosità sui cambi di nome; non per la data.

##### 1.5 Mapping Diversity (OBC Transeuropa / EDJNet) — solo per controllo incrociato
- **URL:** `https://github.com/EDJNet/mapping_diversity` (file `street names aggregate results.xlsx`), pagina del dataset `https://www.europeandatajournalism.eu/cp_dataset/street-names-in-european-cities/`. Scaricato in `raw/altri/mapping_diversity/`: l'xlsx (0,08 MB), `README.md`, `LICENSE.md`. È un file di sole somme per città (non vie una per una). I dati via-per-via sono su Google Sheet (non scaricati).
- **Licenza:** il repository GitHub dichiara CC BY 4.0; il testo del README dice a un certo punto CC BY-SA (incoerenza interna); nomi delle vie e dati geografici sono © OpenStreetMap (ODbL), dati Wikidata CC0. Per un confronto basta citare la fonte.
- **Dato per Milano** (`street_names_aggregate_results.xlsx`, fogli `overview` e `gender gap`, riga "Milano", febbraio 2023): vie totali **4.480**; vie dedicate a persone **2.677**; a uomini **2.523**; a donne **135** (5,04%); genere misto/incerto **19**. Persone uniche con Wikidata: 2.426.

##### 1.6 Toponomastica femminile (associazione)
- Nessun file aperto scaricabile trovato (solo censimenti nei comunicati). Cifra riportata da un articolo de Il Giorno (visto solo come risultato di ricerca, non scaricato né verificato): censimento 2019, 4.250 strade a Milano, 2.538 a uomini, 141 a donne. Licenza dei loro dati: non trovata, da chiedere se servisse.

##### 1.7 Ricerca di altre fonti sulle date di intitolazione
Sul portale `dati.comune.milano.it` ho cercato `stradario`, `toponomastica`, `viario`, `intitolazione`, `denominazione`, `toponimi`, `grafo stradale`, `arco viario`: i risultati sono solo gli "stradari elettorali" (strade con sezioni elettorali, nessuna data), i civici (ds634) e le mappe storiche (ds2914). Nessun registro separato con delibere. Nessuna fonte ha richiesto registrazione.

#### 2. Data di intitolazione: esiste?
**Sì, in parte.** Il campo `DATA_INTITOLAZIONE` di ds634 è compilato per **1.232 vie su 4.030 (30,6%)**; per le altre 2.798 è vuoto (file `raw/comune/ds634/…csv`, campo `DATA_INTITOLAZIONE`, righe uniche per `CODICE_VIA`). Mancano soprattutto le vie storiche (Manzoni, Dante, Garibaldi, Verdi non hanno data). Sono segnaposto 14 valori: `17000101` (Piazza del Duomo) e 13 valori `19000101` (= "prima del 1900", presumibilmente). Le date più comuni sono dal 1921 al 1930. Nel 2017 o dopo risultano 23 vie con data. **Chiave per unire con OSM:** il tag OSM `loc_ref` ha la forma `CODICE_VIA_progressivo` (es. `7238_35162`): la prima parte è il `CODICE_VIA` del Comune. Su 4.030 vie del Comune, 3.979 si agganciano al codice; 4.012 con codice o nome (18 non risultano in OSM). Lo scrive `out/strade_unite.csv` (campo `in_osm`).
Nel registro Comune le vie dedicate a donne (con la nostra classificazione) sono 104 e di queste solo 29 hanno la data (`strade_persone.csv`, campi `sesso` e `data_intitolazione`).

#### 3. Copertura (primo conteggio grezzo)
Tutti i numeri vengono da `copertura.json` (calcolato da `scripts/09_coverage.py` sul file `strade_persone.csv`). Il file `out/strade_unite.csv` unisce registro Comune e OSM.

**Quante strade ci sono**
- Nomi unici in OSM (`out/osm_strade_aggregate.csv`, campo `name`): **5.168**. Includono anche sentieri, marciapiedi, banchine, ecc.
- Vie nel registro del Comune (ds634, `CODICE_VIA`): **4.030**.
- Nomi presenti solo in OSM: 1.061, ma solo 250 sono vere strade (residenziali, secondarie, piazze, pedonali); gli altri 811 sono soprattutto `footway` (560) e `platform` (141).
- **Universo di lavoro** ("core"): 4.030 + 250 = **4.280**.

**Con il tag OSM (`name:etymology:wikidata`)**
- Nomi unici OSM con il tag: **1.186** (`out/osm_strade_aggregate.csv`, campo `etymology_wikidata` non vuoto). Elementi con il tag: 10.846 su 31.950.
- Nell'universo di lavoro: **1.202 strade con tag (28,1%)**, 3.078 senza.
- Dei 1.202 tag: **882** puntano a una persona (Wikidata P31 = essere umano, più 4 "esistenza discussa" come Omero e Alberto da Giussano); **874** con sesso noto (`strade_persone.csv`, campo `sesso`); 8 con più persone di sesso diverso o sesso non indicato; **320** puntano a luoghi o altro (non persone: comuni, fiumi, quartieri, specie…).
- Sesso tra le 874: **28 donne**, **846 uomini**.
- Persone uniche nei tag: 826 QID umani su 1.173 QID unici (`out/etimologie_wikidata.csv`, campo `umano`): 30 donne, 796 uomini. (La differenza con le 28 strade deriva da donne con una sola strada o con più strade/tag.)

**Senza tag: 3.078 strade, primo giro di matching** (`matching_candidati.csv`, campi `categoria` e `confidenza`)
- **sicuro: 756** (un solo umano con nome identico o chiaramente prevalente): 33 donne, 722 uomini, 1 sesso non indicato.
- **incerto: 692** (omonimi, nome parziale, o legame con l'Italia non chiaro): sesso del primo candidato 53 donne, 632 uomini, 7 non indicato.
- **nessuno: 1.630**, di cui: 419 luoghi (comune, fiume…), 16 date/eventi, 404 altra cosa non umana su Wikidata, **791 senza alcun candidato** (non si sa se persone o luoghi).
- Quindi "chiaramente non persone" in tutto: 320 (tag) + 419 + 16 + 404 = **1.159** strade (l'ultimo gruppo di 404 è "altra cosa non umana", meno sicuro).

**Conta grezza donne/uomini** (solo tag + match "sicuro", senza gli incerti): **61 donne e 1.568 uomini**, cioè 3,7% donne su 1.629 persone trovate. Se si aggiungono i primi candidati degli "incerti": +53 donne, +632 uomini. Per confronto Mapping Diversity (feb 2023, controllo manuale): 135 donne su 2.677 vie dedicate a persone (5,04%) e il registro Comune ne conta 104 con la nostra classificazione: la nostra cifra è per ora **sicuramente troppo bassa** per le donne (vedi limiti).

#### 4. Trappole dei dati (problemi trovati)
1. **Il tag OSM non è completo né sempre una persona.** Solo 28% delle strade ha il tag; di quelle che lo hanno, 27% (320/1.202) non punta a una persona. Un tag può contenere più QID: 149 strade ne hanno più di uno (es. "Gioacchino Murat" con due QID; "Della Scala" con due; "Sesto San Giovanni" due).
2. **Un nome OSM non è una strada.** 5.168 "nomi" ma 4.280 strade vere; la stessa via può avere più `way` e anche nomi leggermente diversi (es. "Via Johann Gutemberg" e "Via Johannes Gutenberg" compaiono insieme come strade separate solo in OSM). 704 nomi OSM hanno più di un codice `loc_ref`; ci sono codici non nel registro ufficiale (205 su 4.184 codici distinti, fra cui `-9999` e `100058`).
3. **Il registro del Comune ha due ordini del nome:** `DENOMINAZIONE` = "COGNOME NOME", `DESCRITTIVO` = "NOME COGNOME", e usa maiuscole, apostrofi al posto degli accenti ("NICCOLO'") e parentesi per particelle ("VIVARINI (F.LLI)"). Per cercare su Wikidata serve il `DESCRITTIVO`.
4. **Data di intitolazione presente solo per il 31% delle vie**, con 14 valori segnaposto (1700-01-01, 1900-01-01), vuota proprio per le vie storiche. Per le donne sono 29 su 104.
5. **Wikidata:** 5 elementi su 1.173 non hanno etichetta in italiano né in inglese (la query restituisce il codice QID come nome, es. Q7186 = Marie Curie); 12 persone senza anno di nascita, 10 senza anno di morte, 10 senza professione. Le professioni sono molte e disordinate (Santa Cecilia = "musicista"; Caterina Sforza = "scrittore, politico"). "Fratelli X" o famiglie (Della Scala, Visconti) non sono persone singole.
6. **Matching dei senza tag (primo giro):** funziona bene sui nomi completi (Nome Cognome), male su titoli e nomi parziali: "Via Don Carlo Porro", "Fra Giovanni Pantaleo", "Padre G.B. Martini", "Madre Cabrini" (trovata), "Via del Caravaggio", "Via Piermarini" ricadono in "nessuno" o in "incerto". I santi e le sante ("Santa Lucia", "San Clemente") sono difficili da distinguere da chiese e luoghi. Alcuni "sicuri" potrebbero comunque essere omonimi sbagliati: il controllo manuale resta da fare. Le strade intitolate a donne con ruolo religioso o titolo (Santa, Madre, Regina, Suor) sono quelle più perse.
7. **Mapping Diversity ha cifre diverse dalle nostre** (4.480 vie, 135 donne, febbraio 2023) perché usa altro metodo e altra data: confrontare con cautela. Il Giorno/Toponomastica femminile danno 141 donne su 4.250 (2019).
8. **Overpass:** il timestamp dei dati OSM è del 29/10/2026 14:21 UTC; tra qualche mese i conteggi dei tag cambieranno (OSM è modificato di continuo). Da citare sempre con la data.

#### 5. File prodotti (cartella `donne-nelle-vie/`)
| File | Contenuto | MB |
|---|---|---|
| `raw/osm/overpass_milano.json` | risposta Overpass grezza | 11,26 |
| `raw/wikidata/osm_etymology_batches/` | 8 risposte SPARQL grezze | 1,2 |
| `raw/wikidata/matching_untagged/` | ricerca e dettagli per il matching | 3,7 |
| `raw/comune/ds634/` | civici Comune (CSV + zip) | 26,25 |
| `raw/comune/ds2914/ds2914_vie.csv` | vie e mappe storiche | 0,01 |
| `raw/altri/mapping_diversity/` | xlsx + README + licenza | 0,10 |
| `out/osm_strade_aggregate.csv` | 5.168 nomi unici OSM | 0,42 |
| `out/etimologie_wikidata.csv` | 1.173 QID: sesso, professioni, anni | 0,15 |
| `out/strade_unite.csv` | 5.091 righe: registro Comune + solo OSM | 0,45 |
| `matching_candidati.csv` | 3.078 strade senza tag: candidato, motivo, confidenza | 0,53 |
| `strade_persone.csv` | tabella unica: strada, persona, sesso, anni, data intitolazione, fonte | 0,69 |
| `copertura.json` | tutti i conteggi di questa nota | <0,01 |

#### 6. Da decidere / prossimi passi suggeriti (non fatti)
- Secondo giro sul matching togliendo i titoli (Don, Fra, Padre, Madre, San/Santa, Beato) e provando le due varianti del nome.
- Controllo manuale degli incerti, partendo dai 53 con primo candidato donna, e delle 33+28 donne trovate.
- Per ogni donna: professione leggibile (le professioni Wikidata vanno raggruppate in poche categorie).
- Data di intitolazione solo dove c'è (30,6%): decidere se basta o se cercare le delibere altrove.

### Fase 2 — percentuali e mappa (2026-10-29)

- **Percentuali** (`donne-nelle-vie/out/percentuali.json`; "certe" = tag OSM o abbinamento sicuro, la forchetta aggiunge i casi incerti): tra le vie intitolate a persone, donne **4,7%** (96 su 2.063), forchetta 4,7-5,8%; senza le sante 4,2% (83 su 1.986). Su tutte le 4.278 vie: 2,2% (forchetta 2,2-3,5%).
- **Per periodo di intitolazione** (solo le vie con data nel registro del Comune, ds634): fino al 1949 2,6%, 1950-79 4,3%, 1980-99 7,0%, dal 2000 11,0%.
- **Confronti**: Mapping Diversity (feb. 2023) 5,04% (135 su 2.677); censimento giornalistico 2019 141 su 4.250 (3,3%). Le differenze sono spiegate in `donne-nelle-vie/NOTE.md`, "Fase 2".
- **Da verificare**: 55 casi in `donne-nelle-vie/da_verificare_donne.csv` (decide Davide).
- **Controllo del coordinatore**: su 25 vie "certe" estratte a caso, una era sbagliata: Via Donna Prassede abbinata a una santa (Santa Prassede / Adelaide di Kiev), ma è il personaggio dei Promessi Sposi. Da correggere nella revisione.
- **Trappole dei dati**:
  - Wikidata ha restituito risposte vuote "too busy" con codice 200 (737 ricerche).
  - Il codice via del Comune (`loc_ref`) raggruppa più nomi OSM, e un tag finiva sulla via sbagliata (Via Fezzan = Caterina Sforza).
  - Gaetanina Calvi non ha la via su OSM.
  - Lo sfondo cartografico CARTO ora chiede una chiave: si usano le tessere OSM in grigio.
  - L'elenco completo delle trappole è in NOTE.md.
- **2026-10-29, decisioni di Davide sui 56 casi dubbi** (`donne-nelle-vie/decisioni_davide.csv`, applicate da `scripts/11c_decisioni.py`; le tabelle di prima sono in `out/prima_delle_decisioni/`):
  - Contano come donna: Anita Garibaldi, Maria Drago, Maria Teresa, Mafalda di Savoia, Isabella d'Aragona (probabilmente la duchessa di Milano, da confermare), Bianca Maria Visconti, Maddalena (santa), le 23 vie "Santa…/Sant'…" (le "Santa Maria" come la Madonna), le 2 "Madre…", le 12 vie con nome e cognome di donna, e Donna Prassede come personaggio dei Promessi Sposi.
  - Non contano: Emilia, Postumia, Sabina e Teano sono luoghi; Zuccaro, Braschi e Garofalo sono uomini; Costanza, Letizia e Marinella sono persone non identificate.
  - Via Santa Croce è stata tolta dal gruppo delle sante dal coordinatore: è la croce, non una persona.
- **Nuove percentuali**: tra le vie intitolate a persone, donne **6,6%** (140 su 2.110); senza sante **5,1%** (103 su 2.009). Su tutte le vie 3,3%. Contando le 486 vie incerte, quasi tutte di uomini, la quota scende a 5,4%.


## 3. Opere d'arte e beni culturali

- Fonti: ArCo knowledge graph 2.0 (dump del 2023-12-01, CNR-ISTC, http://arco.istc.cnr.it/arco-data/2.0/)
- Data di scarico: 2026-10-29
- Licenze: non chiarita (CC BY 4.0 secondo il catalogo, CC BY-SA 4.0 secondo Zenodo e ICCD); per prudenza CC BY-SA 4.0 con attribuzione a ICCD
- Trappole dei dati: vedi l'elenco più sotto

### Fase 1 — scarico (2026-10-29)

**Beni culturali di Milano (Catalogo generale ICCD / ArCo) - note della fase 1**

Data del lavoro: 2026-10-29. Fase 1 = solo scarico e controlli di completezza, nessuna analisi.

#### In breve

- Fonte scelta: **dump ArCo 2.0 del 1 dicembre 2023** (grafo di conoscenza del Catalogo generale dei beni culturali, ICCD), scaricato da `http://arco.istc.cnr.it/arco-data/2.0/` (server del CNR-ISTC). E' l'ultima versione pubblica che ho trovato.
- Nel dump ci sono **2.640.709 schede** in tutta Italia (file `work/conteggi_nazionali.json`, campo `proprieta_nazionali_totale`).
- **Milano**: `beni_culturali_milano.csv` ha **30.721 schede**, divise in due gruppi (campo `ambito`):
  - **27.459 `sede_milano`**: il bene e' a Milano (campo riassuntivo `dc:coverage` = "Milano (MI)" e indirizzo del bene = Comune di Milano). E' il numero da usare come "schede di Milano".
  - **3.262 `solo_luogo_collegato`**: il bene NON e' a Milano, ma una sua localizzazione "altra" (luogo di fabbricazione, di ritrovamento, collocazione precedente o successiva) e' a Milano. Esempio: una coppa del Museo della Valle di Formazza fatta a Milano. Vanno tenute a parte.
- Il dato e' fermo al **2022-2023** (colonna `ultimo_aggiornamento`: 26.806 schede del 2022 e 653 del 2023 tra le `sede_milano`). Il catalogo vivo, oggi, e' piu' avanti e non si riesce a raggiungerlo (vedi "Cosa non ho potuto fare").
- Licenza: vedi sezione apposita. Sintesi: metadati CC BY 4.0 dichiarati dal catalogo, ma il grafo ArCo e' pubblicato altrove come CC BY-SA 4.0. Nessuna immagine scaricata.

#### Fonti confrontate

| Fonte | Esito | Note |
|---|---|---|
| Endpoint SPARQL `dati.beniculturali.it/sparql` | **Non raggiungibile**: il nome non esiste piu' nel DNS (risposta NXDOMAIN da 8.8.8.8, 1.1.1.1 e Cloudflare, 2026-10-29) | Stessa cosa per `dati.cultura.gov.it`, `sparql.dati.cultura.gov.it`, `arco.beniculturali.it`. Quindi niente interrogazioni a pagine (LIMIT/OFFSET): non c'e' a chi farle. |
| Catalogo `catalogo.beniculturali.it` / `catalogo.cultura.gov.it` (con sezione OpenICCD `/opendata/`) | **Bloccato da un controllo anti-bot** (Anubis, "Making sure you're not a bot!", risposta HTTP 401/403) | Non ho aggirato il controllo (regola: niente bot-detection). Nessun download da qui. Non ho creato account e nessuno e' stato richiesto. |
| Zenodo, ArCo Knowledge Graph v1.0 (2019-04-05), record 3242580 | Non scaricato | 3,7 GB, licenza CC BY-SA 4.0. Obsoleto. |
| Zenodo, ArCo v0.1 (giugno 2020), record 3872004 | Non scaricato | 285,6 MB, CC BY-SA 4.0. Obsoleto. |
| CNR-ISTC `arco-data/1.1` (2020-10-29) | Non scaricato | un solo file di 5.121.864.209 byte (`Content-Length`) |
| CNR-ISTC `arco-data/1.2` (2021-01-10) | Non scaricato | circa 5,9 GB (43 parti) |
| **CNR-ISTC `arco-data/2.0` (2023-12-01)** | **SCARICATO** | 97 parti + indice. Il file unico `arco-knowledge-graph-2.0.nt.gz` da 13 GB non e' stato scaricato (stesso contenuto delle parti). |
| GitHub `ICCD-MiBACT/ArCo` | Solo lettura di testi | Il codice e' attivo (ultimi commit 2026-10-19), ma non ci sono release dati dopo il dump 2.0: `KG_release_notes.md` si ferma alla 1.1 e la cartella `release_notes` ha solo `1.1.md`. |

Conteggi per Milano per fonte: solo il dump 2.0 e' stato letto, quindi **30.721 (27.459 + 3.262)** e' l'unico conteggio. Le versioni 1.x e 0.x non le ho scaricate (piu' vecchie e piu' piccole: 5,1 e 5,9 GB contro 14,2 GB di oggi) e non ho un numero di Milano per loro. Per confronto: il lavoro scientifico del 2019 parla di circa 820.000 entita' nel grafo, il dump 2.0 ne ha 2.640.709.

#### Cosa ho scaricato

Cartella `raw\arco-2.0\` (dati grezzi, non toccati):

- `arco-knowledge-graph-2.0_part_0.nt.gz` ... `_part_96.nt.gz`: 97 file, **14.236.239.680 byte (circa 13,3 GiB, 13.577 MB per `du`)**. Ogni file e' un pezzo di RDF in formato N-Triples compresso; le prime 96 parti hanno 10.000.000 di righe ciascuna, la parte 96 e' piu' piccola (96,9 MB). Righe totali lette: **966.591.725** (`logs/estrazione2.log`, seconda colonna).
- `index.txt` (3.773 byte): elenco dei file, copia dall'indice del server.
- Verifica: ogni parte ha la dimensione attesa (`Content-Length` del server, `logs/download.log`), tutte sono state lette per intero senza errori di compressione, SHA-256 in `logs/sha256_arco2.0.txt`.
- Non scaricato: `quarantine.nt.gz` (18 MB, triple scartate dal controllo di qualita' di ArCo): non serve.

Come: `scripts\01_download_arco20.sh` (una parte alla volta, pausa di 1 s, ripresa se interrotto), partito alle 15:24 e finito alle 16:30.

#### File prodotti

| File | Cosa contiene |
|---|---|
| `beni_culturali_milano.csv` (18,3 MB, 30.721 righe, UTF-8) | una riga per scheda di Milano; colonne qui sotto |
| `controlli_completezza.txt` | tutti i conteggi di questa nota |
| `controllo_istituzioni.txt` | controllo: le istituzioni milanesi hanno schede fuori dall'elenco? |
| `work\conteggi_nazionali.json` | conteggi Italia per classe di bene |
| `work\tsv\` (6,9 GB, 97 file) | passaggio intermedio: solo i triple utili, riscrivibile in circa 10 minuti con `scripts\02_estrai_triple.py`; si puo' cancellare |
| `scripts\` | 01 scarico, 02 estrazione, 03 costruzione tabella, 04 controlli, 05 verifica istituzioni, 00 lancio automatico |
| `logs\` | log di scarico e di esecuzione, SHA-256 |

Colonne del CSV: `iri` (identificativo unico della scheda nel grafo, da usare come chiave), `id` (numero di catalogo generale, NON unico), `ambito`, `classe_bene`, `tipo_scheda`, `codice_catalogo` (ICCD...), `url_catalogo` (pagina della scheda), `titolo`, `tipo_oggetto`, `soggetto`, `autore`, `datazione`, `materia_tecnica`, `categoria_catalogazione`, `diritti` (proprieta' del bene, non licenza), `copertura_dc`, quattro colonne 0/1 per i criteri di Milano (`cov_milano`, `indirizzo_milano`, `loc_attuale_mi`, `loc_altra_mi`), `indirizzo_bene`, `localizzazione_attuale`, `altre_localizzazioni`, `istituzione`, `codice_sito`, `lat`, `long`, `ultimo_aggiornamento`, `ente_catalogatore` (codice, non nome).

##### Come ho deciso che una scheda e' "di Milano"

Il dump e' un grafo: la localizzazione e' una catena (bene -> localizzazione nel tempo -> luogo o sito -> indirizzo -> comune). Ho seguito la catena con lo script `03_milano.py` e salvato quattro criteri separati:

1. `cov_milano`: il campo riassuntivo `dc:coverage` e' esattamente "Milano (MI)" (27.459 schede in tutta Italia, `logs\milano3.log`).
2. `indirizzo_milano`: l'indirizzo del bene (`hasCulturalPropertyAddress`) ha `clv:hasCity` = `City/milano`. Si usa il **comune** (City), non la provincia: i comuni della provincia di Milano (Sesto San Giovanni, Rho...) restano fuori.
3. `loc_attuale_mi`: la localizzazione fisica attuale (`CurrentPhysicalLocation`) porta a un indirizzo del Comune di Milano (15.788 schede).
4. `loc_altra_mi`: una localizzazione di altro tipo (precedente, ritrovamento, fabbricazione...) porta a Milano, sia da luoghi (`Feature`) sia da siti (`Site`).

`sede_milano` = almeno uno tra 1, 2, 3. Nei dati i tre criteri coincidono quasi sempre: tutte le schede con criterio 1 hanno anche il 2, e tutte quelle con criterio 3 hanno anche 1 e 2 (`controlli_completezza.txt`, righe "di cui ...").

Controllo "oggetti in musei milanesi ma venuti da fuori": `controllo_istituzioni.txt` mostra che le istituzioni milanesi (Brera, Castello Sforzesco, Poldi Pezzoli, Bertarelli, Villa Necchi, ecc.) hanno tutte le loro schede dentro l'elenco (fuori = 0). Le uniche eccezioni sono istituzioni che hanno sedi in piu' citta': Archivio Franca Rame Dario Fo (764 a Milano, 170 a Verona), Pinacoteca Civica Alberto Martini (261 a Milano, 216 a Oderzo). Quelle fuori Milano sono giustamente escluse.

#### Conteggi (campo `tipo_scheda`, solo `sede_milano`, 27.459)

Il tipo di scheda e' preso dal nome della scheda collegata (`CatalogueRecordOA`, `...D`, ecc.) in `dc:source`; nelle 30.721 righe non e' mai vuoto.

| Tipo | Schede | | Tipo | Schede |
|---|---|---|---|---|
| OA (opere d'arte) | 17.292 | | OAC | 166 |
| D (disegni) | 4.464 | | MA | 38 |
| RA (reperti archeologici) | 2.204 | | F (fotografie) | 36 |
| S (stampe) | 1.578 | | NU (numismatica) | 16 |
| PST (strumenti scientifici) | 788 | | CA | 11 |
| A (architettura) | 665 | | PG | 2 |
| BDM (demoetnoantropologici) | 199 | | | |

Fonte: `controlli_completezza.txt`, sezione "SOLO sede_milano: PER TIPO DI SCHEDA". Il totale 27.459 e' la somma. Le sigle sono quelle delle schede ICCD: disegni `D` e stampe `S` sono schede a parte rispetto a OA.

Per classe del bene (percorso nell'IRI): HistoricOrArtisticProperty 23.500, ArchaeologicalProperty 2.253, ScientificOrTechnologicalHeritage 788, ArchitecturalOrLandscapeHeritage 667, DemoEthnoAnthropologicalHeritage 199, PhotographicHeritage 36, NumismaticProperty 16. (`controlli_completezza.txt`, sezione "SOLO sede_milano: PER CLASSE DEL BENE").

##### Primi 20 detentori (campo `istituzione`, `sede_milano`)

| Istituzione | Schede |
|---|---|
| `CulturalInstituteOrSite/DBunicoCG106788` (nome non presente nel dump) | 3.195 |
| Raccolte storiche dell'Accademia di Brera | 1.593 |
| Civica Raccolta delle Stampe "Achille Bertarelli" | 1.256 |
| Raccolte Grafiche e Fotografiche del Castello Sforzesco | 1.137 |
| Raccolte Artistiche del Castello Sforzesco | 1.081 |
| Museo Poldi Pezzoli | 1.076 |
| Museo Archeologico | 636 |
| Villa Necchi Campiglio | 633 |
| Museo Teatrale alla Scala, medagliere Eisner von Eisenhof Angelo | 322 |
| Collezione Istituto dei Ciechi di Milano | 236 |
| Collezione Torno | 211 |
| Soprintendenza Archeologica | 206 |
| Museo Teatrale alla Scala | 93 |
| Polo del Novecento e Arte Contemporanea | 84 |
| `CulturalInstituteOrSite/ICCD_CG_7658429273461` (senza nome) | 67 |
| Pinacoteca di Brera Archivio Cagnola | 19 |
| Fondo Alfredo Coppola, scatola 2 | 11 |
| Pinacoteca di Brera Collezione Vitali | 5 |
| Collezione dell'Accademia di Belle Arti di Brera | 3 |
| Universita' degli Studi di Milano | 2 |

Fonte: `controlli_completezza.txt`, sezione "SOLO sede_milano: PRIMI 20 ISTITUZIONI". Attenzione: il nome e' il campo `istituzione`, una stessa raccolta puo' comparire con identificatori diversi, quindi alcune righe vanno unite.

##### Campi mancanti (`sede_milano`, 27.459 schede)

| Campo | Mancano | % |
|---|---|---|
| titolo (`dc:title`) | 0 | 0,0 |
| datazione (`dc:date`) | 1.543 | 5,6 |
| autore (`dc:creator`/`pico:author`) | 14.565 | 53,0 |
| soggetto | 183 | 0,7 |
| materia/tecnica | 732 | 2,7 |
| localizzazione fisica attuale (`CurrentPhysicalLocation`) | 11.671 | 42,5 |
| coordinate (lat/long) | 14.265 | 52,0 |
| istituzione detentrice | 15.587 | 56,8 |
| link alla pagina del catalogo | 0 | 0,0 |

Fonte: `controlli_completezza.txt`, sezione "SOLO sede_milano: CAMPI MANCANTI". "Autore mancante" e' normale: molti beni (reperti, architetture, stampe anonime) non hanno autore.

#### Licenza (cosa so e cosa no)

Trovati tre testi diversi:

1. **Pagina del catalogo** (`catalogo.cultura.gov.it`, letta solo tramite un motore di ricerca perche' il sito e' dietro il controllo anti-bot): "LICENZA METADATI CC-BY 4.0". Cioe' i metadati delle schede sono attribuzione semplice.
2. **Zenodo** (ArCo Knowledge Graph v1.0 2019 e v0.1 2020, record 3242580 e 3872004): licenza **CC BY-SA 4.0**. Un articolo del 2024 (GARR) dice lo stesso del nodo di grafo costruito sul dataset ICCD. La pagina del singolo record sul sito lodview dell'ICCD risulta anch'essa CC BY-SA 4.0, con "eccezioni".
3. **Ontologia ArCo** (file `arco.owl` nel repository GitHub, ultima modifica 2023-12-01 = data del dump): `dct:license` CC BY 4.0.

Il dump 2.0 in se' non contiene dichiarazioni di licenza (ho cercato "licen" e "creativecommons" nelle parti 0 e 3: nessun triple di licenza, solo parole italiane nei testi).

Quindi la sintesi onesta e': **metadati CC BY 4.0 secondo il catalogo; CC BY-SA 4.0 secondo la pubblicazione ArCo su Zenodo e sul sito ICCD**. Non l'ho risolto. Le immagini possono avere condizioni diverse (non le abbiamo scaricate; la colonna immagine non e' nel CSV).

Ripubblicare nel repo pubblico: i dati sono aperti e riusabili con **citazione della fonte** (ICCD - Catalogo generale dei beni culturali, ArCo). Per stare sul sicuro conviene ripubblicare **solo il CSV derivato** (non i 14 GB di grezzi), dichiarare **CC BY-SA 4.0** (la piu' restrittiva tra le due, compatibile con la CC BY) e linkare le pagine originali. Il testo preciso della licenza va confermato dall'ICCD (indirizzo indicato dal sito del Ministero: redazione.mic@cultura.gov.it) o aprendo a mano la pagina "Termini d'uso" del catalogo in un browser. **Questa decisione resta al coordinatore.**

#### Trappole dei dati (tutte verificate)

1. **Gli indirizzi sono quasi sempre solo "Milano".** Tra le `sede_milano`, 12.845 + 10.456 + 2.158 + 199 hanno un indirizzo del bene fatto solo da "Italia, Lombardia, MI, Milano" (varianti di maiuscole); solo 1.745 contengono una via o piazza (`indirizzo_bene`, ricerca di via/piazza/corso). La piazza Castello (Castello Sforzesco) da sola vale 1.141 schede. Quindi niente mappa dettagliata dai soli indirizzi: gli indirizzi precisi sono nelle istituzioni, che nel dump hanno solo il nome (e a volte neppure quello).
2. **Il numero di catalogo `id` non e' unico**: 4.366 righe condividono l'`id` con un'altra (esempio: `0100127418-2`, `-21`, `-23`, `-24` sono parti dello stesso bene, tutte con `id` 0100127418). La chiave giusta e' `iri` (zero duplicati) oppure `codice_catalogo`/`url_catalogo` (zero duplicati).
3. **Il dump ha moltissime righe doppie**: 966.591.725 righe lette, ma dopo avere tolto le doppie nei triple che ci servono ne restano 83.583.345 (circa 850.000 per parte; somma della terza colonna di `logs/estrazione2.log`). Lo stesso fatto e' ripetuto decine di volte, quindi non si possono contare le righe grezze.
4. **Un bene e' sparso su piu' parti del dump**: i triple di una scheda stanno in file diversi. Non basta cercare "Milano" in una parte: serve leggere tutte le 97 e unire.
5. **`dc:coverage` e `localizzazione fisica attuale` non coincidono**: 11.671 schede `sede_milano` hanno `dc:coverage` Milano ma nessuna localizzazione attuale che arrivi a un indirizzo di Milano. Tutte e 11.671 hanno invece un "sito" con un codice numerico (colonna `codice_sito`) che nel dump non ha nome ne' indirizzo. Per questo ho usato `dc:coverage`+indirizzo come criterio principale e non la sola localizzazione.
6. **Istituzione senza nome**: 3.195 schede (la voce piu' grande) hanno come istituzione solo `CulturalInstituteOrSite/DBunicoCG106788`, senza etichetta nel dump. Sono 2.863 dipinti OA e 332 disegni D (ad esempio Hayez, Voghera), catalogati dall'ente `033c02867cc5...`: probabilmente raccolta di Brera, ma e' una mia ipotesi, non scritta nel dump. Idem `ICCD_CG_7658429273461` (67). In totale il 56,8% delle `sede_milano` non ha istituzione.
7. **Coordinate con latitudine e longitudine scambiate**: su 13.194 schede con coordinate, 2 sono fuori dal rettangolo di Milano perche' invertite (es. scheda 0300101865 Palazzo Gallarati Scotti: lat 9,19 e long 45,47). Le altre 13.192 cadono nel rettangolo 45,38-45,54 N / 9,04-9,28 E.
8. **Ente catalogatore e istituzioni: solo codici/hash** (`ente_catalogatore` e' un codice di 32 caratteri); i nomi stanno in altre parti del grafo che non ho estratto. Il piu' frequente (19.287 schede) ha come nome, nelle schede che ho visto a campione, la Soprintendenza per i beni storici artistici ed etnoantropologici per le province di Milano e di altre (scheda 0300004394).
9. **Titoli con aggiunte tra parentesi**: il titolo `dc:title` include la forma della catalogazione, es. "dipinto (opera isolata)", "capitello composito (serie)", oppure frasi molto lunghe. Per i nomi puliti usare `tipo_oggetto` e `categoria_catalogazione`.
10. **Tipo scheda `D`, `S`, `OAC`**: in ArCo sono tipi diversi da OA; se si vuole "opere d'arte" nel senso comune vanno sommati OA, D, S (circa 23.300). Decisione per la fase 2.
11. **Il sito DNS `dati.beniculturali.it` e' sparito**: tutti i link di vecchi articoli e README (`dati.beniculturali.it/arco`, `.../sparql`) sono morti. Nel dump restano migliaia di URI `http://dati.beniculturali.it/iccd/cf/resource/CulturalInstituteOrSite/<numero>` che non portano piu' a nulla.
12. **Link di catalogo**: `url_catalogo` e' del tipo `http://www.catalogo.beniculturali.it/sigecSSU_FE/dettaglioScheda.action?keycode=ICCD...` (indirizzo vecchio, per ora il nome esiste ancora nel DNS ma e' dietro il controllo anti-bot). Il nuovo sito e' `catalogo.cultura.gov.it`; il formato dei nuovi indirizzi di scheda non e' verificato.
13. **Le 3.262 `solo_luogo_collegato` sono beni di altre citta'**: per tipo sono OA 1.447, D 1.407, F 237, S 74, BDM 62, PST 16, RA 14, altri 5. Le fotografie (F) sono 237 di questo gruppo contro 36 di `sede_milano`: Milano e' spesso solo il luogo della ripresa. Non contarle come patrimonio "di Milano".
14. **Aggiornamento**: il dump e' del 2023-12-01 ma le schede sono state aggiornate l'ultima volta nel 2022 o 2023 (colonna `ultimo_aggiornamento`). Il catalogo di oggi ha certamente piu' schede.

#### Cosa non ho potuto fare

- Nessun accesso all'endpoint SPARQL (non esiste piu' nel DNS) e nessun download diretto dal catalogo (controllo anti-bot Anubis, non aggirato). Quindi non so quante schede di Milano ci sono oggi nel catalogo vivo, solo nel dump di fine 2023. Se serve il dato piu' recente, un essere umano puo' aprire `catalogo.cultura.gov.it` nel browser, oppure scrivere a redazione.mic@cultura.gov.it chiedendo un dump piu' nuovo.
- Nessun conteggio per Milano delle versioni vecchie del grafo (non scaricate).
- Nessun nome per gli enti catalogatori e per alcuni istituti (mancano nel dump).
- Nessuna immagine scaricata (come richiesto).
- Nessun account creato; nessun sito ha chiesto registrazione.
- Nessun git, nessuna pubblicazione.

#### Come rifare tutto

```
bash scripts/01_download_arco20.sh raw/arco-2.0
python -I scripts/02_estrai_triple.py raw/arco-2.0 work/tsv 8 logs/download.log
python -I scripts/03_milano.py work/tsv beni_culturali_milano.csv work/conteggi_nazionali.json
python -I scripts/04_controlli.py beni_culturali_milano.csv work/conteggi_nazionali.json controlli_completezza.txt
python -I scripts/05_verifica_istituzioni.py work/tsv beni_culturali_milano.csv controllo_istituzioni.txt
```

Tempi: scarico circa 66 minuti, estrazione circa 10 minuti, tabella Milano circa 10 minuti, 7-8 GB di RAM al massimo.

## 4. Elezioni milanesi

- **Fonti:** portale open data del Comune di Milano (dati.comune.milano.it, CKAN): 328 dataset elettorali, 658 file pubblicati.
- **Data di scarico:** 2026-10-29.
- **Licenze:** tutti i dataset CC BY (grezzo ripubblicabile citando il Comune di Milano; attenzione ai dataset "dati ufficiosi").
- **Trappole dei dati:** 18 trappole, elencate più sotto nella sezione "6. Trappole dei dati (materiale per la rubrica)".

### Fase 1 — scarico (2026-10-29)

**Elezioni milanesi per sezione — note di fase 1 (solo scarico)**

Data di scarico: **2026-10-29**. Nessuna analisi, nessuna pulizia, nessun git, niente pubblicato.
Fonte: portale open data del Comune di Milano, `https://dati.comune.milano.it` (CKAN).

Dove non è scritto altro, "file X, campo Y" si riferisce ai file in questa cartella:
`inventario_dataset.csv` (un riga per dataset), `inventario_risorse.csv` (una riga per file pubblicato),
e a `meta\*.csv` (controlli). I dati grezzi sono in `raw\<nome-dataset>\` (il nome è tagliato a 80 caratteri).

#### 1. Domande fatte all'API (nessuna pagina web guardata)

Tutte con `GET https://dati.comune.milano.it/api/3/action/...` (script `scripts\01_search.py`, pausa di 1 secondo tra le richieste):

- `package_search?q=elezioni&rows=1000` → 337 risultati (campo `result.count`). Stessa cosa con
  `q=referendum` (106), `voti` (271), `sezioni` (384), `elettorale` (331), `sezione elettorale` (327),
  `politiche` (97), `europee` (215), `regionali` (103), `affluenza` (5), `comunali` (325), `municipali` (19),
  `seggi` (5), `plessi` (143). Il motore cerca parole anche vicine e non solo esatte, quindi i conteggi sono gonfiati.
  Le 14 ricerche insieme danno 1.003 dataset diversi (`meta\all_search.json`).
- `group_list` → 13 gruppi tematici, nessuno è "elezioni" (le elezioni stanno in `gove` = governo).
- `tag_list?query=elezion` → 47 tag, uno per elezione (es. `elezioni_comunali_2021`, `elezioni_politiche_2022`); `tag_list?query=vot` → solo `sede_votazione`.
- `package_list` → 2.611 nomi in tutto il portale (`meta\package_list.json`). Controllo di completezza: ho cercato nei
  nomi le parole elez, referend, elett, plessi, affluen, votaz, voti, seggi, sedi, collegi: **nessun dataset elettorale
  manca** rispetto a quelli già trovati (gli altri nomi trovati sono fuori tema: sedi dei municipi, energia elettrica, ecc.).
- `organization_list?all_fields=true` → **errore 500 del server** (non risolto, ma inutile: tutto è dell'organizzazione `comunedimilano`).

Filtro per tenere solo i dataset elettorali (script `scripts\02_inventory.py`): titolo con elezion/referendum/elettoral/elettori,
tolti Censimento, Prezzi al consumo, Votazioni del Consiglio comunale, ecc. Risultato: **328 dataset, 658 file pubblicati**.

#### 2. Inventario in sintesi

Tipo di dato (campo `kind` in `inventario_dataset.csv`), numero di dataset, MB scaricati, righe totali nei CSV:

| tipo | dataset | MB | righe |
|---|---|---|---|
| risultati_sezione (votanti, validi, nulli per sezione) | 153 | 7,76 | 241.535 |
| riepilogo_sezione (come sopra, nome usato nel 2021) | 4 | 0,36 | 4.992 |
| voti_lista_sezione (voti a liste/candidati per sezione) | 83 | 24,47 | 1.673.768 |
| stradario_civici_sezioni (via+civico → sezione) | 33 | 26,36 | 1.701.659 |
| sezioni_sedi (sezione → indirizzo del seggio) | 29 | 1,13 | 36.249 |
| indirizzi_plessi (scuole usate come seggi) | 9 | 0,35 | 3.636 |
| elettori (iscritti per sezione 2016 e 2019; serie semestrale) | 3 | 0,10 | 2.569 |
| affluenza (2021, per municipio e per ora) | 5 | 0,03 | 440 |
| candidati_liste (2021) | 3 | 0,09 | 1.229 |
| seggi_accessibili (senza barriere) | 3 | 0,01 | 250 |
| collegi_geo (confini dei collegi 2018, 2022) | 2 | 0,89 | — |
| visualizzatore_html (banca dati interattiva SIEL) | 1 | — | — |
| **totale** | **328** | **61,56** | |

- Licenza: **tutti i 328 dataset sono `license_id = cc-by`** ("Creative Commons Attribution", campo `license` in `inventario_dataset.csv`).
  A livello di file: 652 file dichiarano CC BY 4.0 (`license_type` = A21_CCBY40), 6 file CC BY 3.0 IT (A23_CCBY30IT): sono i file del dataset ds1993 (collegi 2022).
  Titolare: Comune di Milano, "Unità Servizi Statistici" (campi `holder_name`, `maintainer`). Frequenza di aggiornamento: quasi tutti `NEVER`.
- **I dati grezzi si possono ripubblicare**, citando la fonte (CC BY: attribuzione obbligatoria). Attenzione:
  (a) alcuni dataset sono marcati "dati ufficiosi" nel titolo (Politiche 2018 e 2022, Regionali 2023): citare la cosa;
  (b) il dataset ds504 (collegi 2018) cita come fonte il Servizio Studi di Camera e Senato: non scaricato, licenza da verificare se servirà.
- Date dei metadati: i dataset sono stati creati tra 2017-11-16 e 2026-03-25 (`metadata_created`); 327 su 328 risultano modificati il 2026-05-08 (`metadata_modified`) — è una data di migrazione del portale, non una correzione dei dati.
- Nessuna richiesta di registrazione o account incontrata. Tutti i file scaricati senza login.

##### Cosa è stato scaricato

- 330 file tentati, **329 scaricati**: 182 ZIP (ognuno contiene un CSV) + 145 CSV diretti + 2 GeoJSON (collegi 2022). Registro in `meta\download_log.csv` (con SHA-256).
- Gli ZIP sono stati aperti in `raw\<dataset>\unzipped_<nome>\`; il file ZIP originale resta accanto.
- **Non scaricati di proposito**: 327 file JSON, copie degli stessi CSV (campo `format` = JSON in `inventario_risorse.csv`; 750,8 MB dichiarati nel campo `size_bytes`).
- Dimensione su disco di `raw\`: 257,9 MB (511 file): 14,6 MB di ZIP, 242,4 MB di CSV (327 file, 3.666.332 righe in tutto, campo `rows` di `meta\profilo_csv.csv`).
- **Bloccato**: ds504 "Collegi elettorali 2018" ha come unico file un link a `geoportale.comune.milano.it/ATOM/SIT/...xml` (campo `url`): il nome del sito non si risolve dal mio computer (errore DNS). Non scaricato. La cartella vuota è stata tolta.
- ds23 "banca dati interattiva" è solo un link a `https://siel.comune.milano.it/` (pagina con moduli, risponde 200, senza registrazione). Il testo del dataset dice: risultati ufficiali 1979 → oggi, a livelli "comune, collegi sub-comunali, zone di decentramento, sezioni". Non l'ho esplorata né scaricata; potrebbe servire in fase 2 per controllare i numeri.

#### 3. Tabella di completezza

Per ogni tipo di elezione: quali tornate sono presenti nei dataset "risultati" + "voti di lista" (quasi sempre in coppia: tutti gli 83 dataset "voti" hanno il corrispondente "risultati", con lo stesso numero di sezioni; confronto fatto sui campi `sezioni_distinte`).
Gli anni vengono dal titolo e dal campo `Sessione`.

| tipo | presenti (anno) | mancano / note |
|---|---|---|
| Comunali (Consiglio) | 1980, 1985, 1990, 1993, 1997, 2001, 2006, 2011, 2016, 2021 | — (21 dataset risultati) |
| Comunali (Sindaco) | 1993, 1997, 2001, 2006, 2011, 2016, 2021 | — |
| Ballottaggio sindaco | 1993, 1997, 2011, 2016 | 2001, 2006, 2021 non servito (non risulta un ballottaggio: da verificare fuori portale) |
| Municipali (Presidente, Consiglio) | 2016, 2021 | prima del 2016 esistevano i Consigli di zona/circoscrizione |
| Circoscrizionali | 2011 (coalizioni + liste) | 1980–2006: nessun dataset (da verificare se si votavano) |
| Politiche, Camera | 1979, 1983, 1987, 1992, 1994 (maggioritario + proporzionale), 1996 (idem), 2001 (idem), 2006, 2008, 2013, 2018, 2022 | 2018 e 2022 solo "candidati nel collegio uninominale" e "liste nel collegio uninominale", dati ufficiosi |
| Politiche, Senato | 1996, 2001, 2006, 2008, 2013, 2018, 2022 | **1979, 1983, 1987, 1992, 1994: nessun dataset Senato** |
| Europee | 1979, 1984, 1989, 1994, 1999, 2004, 2009, 2014, 2019, 2024 | — (tutte) |
| Regionali | 1980, 1985, 1990, 1995, 2000, 2005, 2010, 2013, 2018, 2023 | — (tutte; "liste regionali" e "provinciali" separate dal 1995) |
| Provinciali | 2009 (presidente, consiglio, ballottaggio) | 1995, 1999, 2004 (probabilmente votate: nessun dataset) |
| Referendum nazionali/regionali | 1981 (5), 1985, 1987 (5), 1989 (consultivo), 1995 (12), 1997 (7), 1999, 2000 (7), 2001, 2003 (2), 2005 (4), 2006, 2009 (3), 2011 (4), 2016 (aprile e dicembre), 2017 (Lombardia), 2020, 2022 (5), 2025 (5), 2026 | **1990, 1991, 1993**: nessun dataset (probabilmente votati: da verificare) |
| Referendum cittadini di Milano | 2011 (5 quesiti, ds1426–ds1430) | — |
| Affluenza oraria | solo 2021 (ds1618–ds1622), per municipio, non per sezione | tutte le altre tornate: nessuna |
| Candidati e liste | solo 2021 (ds1615–ds1617) | tutte le altre |

Conti di controllo (campo `election_type` in `inventario_dataset.csv`): 157 dataset "risultati/riepilogo" = 74 referendum + 26 politiche + 21 comunali + 17 regionali + 10 europee + 4 municipali + 3 provinciali + 2 circoscrizionali.

**Dataset sulle sezioni (indirizzi, stradari) per anno**: ci sono per le tornate dal **2001** in poi (sedi + stradario: 13/5/2001, 7/10/2001, 12/6/2004, 3/4/2005, 12/6/2005, 9/4/2006, 28/5/2006, 25/6/2006, 13/4/2008, 6/6/2009, 21/6/2009, 28/3/2010, 15/5/2011, 12/6/2011, 24/2/2013, 25/5/2014, 17/4/2016, 5/6/2016, 4/12/2016, 22/10/2017, 4/3/2018, 26/5/2019, 2020, 2021, 2022, 12/2/2023, 8/6/2024, 8/6/2025, 22/3/2026; Politiche 2022 solo stradario + plessi). **Per le elezioni 1979–2000 non c'è nessun elenco di indirizzi dei seggi né stradario.**

#### 4. Le sezioni nel tempo (risposta alla domanda 3)

**Il numero cambia molto, la numerazione molto meno.**

Numero di sezioni con risultati (campo `sezioni_distinte` di `inventario_dataset.csv`, calcolato sul campo `Sezione` di ogni CSV; file `meta\sezioni_per_elezione.csv`):

| periodo | sezioni | esempi (file) |
|---|---|---|
| 1979–1990 | 2.157–2.160 (referendum 1981: 2.162) | ds1195 Politiche 1979: 2.157; ds1198 Comunali 1980: 2.160; ds1372 ref. 1981: 2.162; ds1206 Comunali 1990: 2.157 |
| 1992–1997 | 2.086–2.087 | ds1207 Politiche 1992: 2.087; ds1219 Comunali 1997: 2.086 |
| 1999 → | scende a circa 1.250 | ds1222 Europee 1999: 1.250 |
| 2001–2013 | 1.247–1.253 | ds1228 Comunali 2001: 1.251; ds1235 Comunali 2006: 1.253; ds1250 Politiche 2013: 1.250 |
| 2014–2024 | 1.247–1.248 | ds1255 Comunali 2016: 1.248; ds1624 Comunali 2021: 1.248; ds2746 Europee 2024: 1.248 |
| 2025 | 1.260 (1.249 normali + 11 speciali numerate 9001–9011) | ds2930 referendum 2025, campo `Sezione` |
| 2026 | 1.249 | ds2975 referendum 2026 |

- Conferma indipendente: il dataset **ds720** (serie semestrale del corpo elettorale, campo `TOTALE SEZIONI`, 74 righe dal 31/12/1988 al 31/12/2025) mostra lo stesso salto: 2.086 (giugno 1997) → 2.055 (dicembre 1997) → 1.949 (giugno 1998) → **1.250 (dicembre 1998)**; poi tra 1.247 e 1.254 fino a 1.249 a fine 2025.
- **La numerazione resta quella "vecchia"**: in tutti i file il numero di sezione va da 1 a **2.243** (campo `sez_max` di `meta\profilo_csv.csv`); dal 1999 mancano circa 1.000 numeri (buchi), cioè i numeri delle sezioni soppresse non sono stati riutilizzati. Fanno eccezione le 11 sezioni 9001–9011 del 2025.
- Confronto tra elezioni consecutive (`meta\stabilita_territorio.csv`): dal 2001 in poi gli stessi numeri sono quasi sempre gli stessi sezioni: da 2016 a 2018 identici 1.248 su 1.248; 2018→2021 1.247 in comune; 2021→2022 1.248. Tra due tornate vicine cambiano da 0 a 13 sezioni (es. 2024→2025: 13 nuove; 2025→2026: 11 tolte).
- **Il salto 1997 → 1999–2001 è un vero cambio di sistema**: 836 numeri spariscono (2.086 → 1.251) e il codice territoriale passa da 20 circoscrizioni a 9 zone: nel confronto 1997 → 2001 il codice coincide solo in 287 casi su 1.250 comuni (valore casuale, `meta\stabilita_territorio.csv`). Prima del 1999 il campo si chiama `Circoscrizione` (valori 1–20), dal 1999 `Zona` (1–9), dal 2016 `Municipio` (1–9). **Non si possono confrontare i territori a cavallo del 1999 senza una tabella di corrispondenza.**
- Dentro lo stesso periodo la zona/municipio di una sezione cambia pochissimo: 2001→2006 uguale in 1.241 su 1.245; 2006→2011 in 1.246 su 1.247; 2011→2016 in 1.245 su 1.245 (zona 1–9 → municipio 1–9, stessi numeri).
- **Lo stesso numero non è lo stesso posto**: confrontando l'indirizzo del seggio (testo senza punteggiatura, campo `INDIRIZZO_SEDE`/`Sede`) tra tornate in ordine di data, il seggio cambia per 0–18% delle sezioni a ogni giro (`meta\stabilita_sedi_consecutive.csv`; es. 2018→2019: 83,2% uguali; 2004→2005: 91,4%); **tra il 13/5/2001 e il 22/3/2026 solo 618 sezioni su 1.233 hanno lo stesso indirizzo scritto**. È un confronto di testo, quindi sovrastima i cambi (alcuni indirizzi sono solo scritti in modo diverso); per fase 2.
- **Corrispondenza ufficiale sezione → municipio/zona**: c'è, ed è dentro i file dei risultati (campo `Circoscrizione`/`Zona`/`Municipio`, 1 valore per sezione e per elezione). Copre tutte le tornate 1979–2026.
- **Corrispondenza ufficiale sezione → NIL (quartiere)**: **esiste in un solo dataset**, ds939 (stradario del referendum del 20-21/9/2020), che ha i campi `ID_NIL` e `NIL` accanto a `SEZIONE` e `MUNICIPIO` per ogni civico (51.323 righe, 1.238 sezioni, 89 NIL). Ma la corrispondenza è per **civico**, non per sezione: **345 sezioni su 1.238 contengono civici di più di un NIL (fino a 4)**, quindi serve una regola (es. NIL prevalente). Solo un riferimento: nessun dataset di sezione → NIL per le altre date. Non è stato costruito nessun abbinamento.
- **Sezione → indirizzo**: dal 2001 in poi con i dataset "sezioni e sedi"/"elenco delle sedi" (una riga per sezione, 1.247–1.260 righe, campo `SEZIONE`). Sezione → via/civico (tutti i civici serviti da una sezione) con gli stradari (33 dataset; il più grande ds505, Politiche 2018: 52.496 righe).
- **Non esiste nel portale un file con i confini (poligoni) delle sezioni elettorali.** Ci sono solo i collegi (ds1993, 2022; ds504, 2018, non scaricabile) e, in altri filoni del portale, i confini di NIL (`ds61_infogeo_nil_localizzazione_`), municipi (`ds379-infogeo-municipi-superficie`), sezioni di **censimento** 2011 e 2021 (`ds98_infogeo_sezioni_censimento_localizzazione_2011c`, `ds2845-...2021`) — che sono un'altra cosa.
- Attenzione al municipio della **sede**: in `ds2920` (referendum 2025) i campi `MUNICIPIO_SEZ` e `MUNICIPIO_SEDE` sono diversi per 96 sezioni su 1.260; in ds1609 (2021) e ds2742 (2024) `ZD_SEZ` ≠ `ZD_SEDE` per 99 e 96 sezioni su 1.248. Quindi **il municipio dell'indirizzo del seggio non è sempre quello della sezione**: usare il campo della sezione, non geocodificare l'indirizzo.

#### 5. Formati, codifiche, nomi di colonna (solo elenco, la pulizia è fase 2)

Fonte: `meta\profilo_csv.csv` (327 CSV; campi `encoding`, `delimiter`, `header`).

- Separatore `;` in 325 file; `,` in 2 (ds1621 affluenza 2021, ds2741 stradario Europee 2024).
- Codifica: 317 file UTF-8 (nessun BOM), **10 file in Windows-1252** (non UTF-8): ds1610, ds1617, ds1847, ds1848, ds1980, ds2175, ds2740, ds2747 (voti di lista Europee 2024), ds938, ds940.
- Fine riga `\r\n` in tutti.
- Intestazioni tra virgolette in 69 file (es. `"Sessione";"Elezione";...`).
- Nomi dei campi che cambiano per lo stesso concetto: territorio = `Circoscrizione` / `Zona` / `Municipio`; sezione = `Sezione` (285 file), `SEZIONE` (20), `Sezione Elettorale` (1); sede = `Sede` / `INDIRIZZO_SEDE` / `INDIRIZZO` / `UBICAZIONE`; stradario = `Via`/`DESCRIZIONE_VIA`/`INDIRIZZO_SEDE`, `Civico`/`CIVICO`/`Esponente Civico`.
- Colonne in più, secondo la tornata: `Nome_Elezione` (assente nei referendum con Sì/No), `CollCam/CollSen/CollPro` (presenti solo in parte dei file; assenti in alcuni file 2018–2023), `Si/No` (referendum), `Voti validi solo Candidato Sindaco` / `Presidente Municipio` / `Liste Regionali` / `Coalizioni` / `Voti solo candidato uninominale` / `Voti da ripartire tra le liste in coalizione`, `Di cui al solo candidato uninominale` (nei voti di lista).
- **28 intestazioni diverse** (togliendo le virgolette) tra i soli file "risultati/riepilogo" (19) e "voti di lista" (9 in aggiunta, alcune uguali) (campo `header` di `meta\profilo_csv.csv`).
- Formati data nel campo `Sessione`: `gg/mm/aaaa` in 246 file; `aaaa-mm-gg` in 26 (dal referendum 2020); date senza zeri (`15/6/2003`) negli stradari di referendum; vuoto in 41 file (sezioni e sedi 2021 ecc.); `2022-06-12` e codici `114`, `117` (vedi trappole).
- 41 file CSV senza campo di data (es. ds1609, ds1610, ds1614–ds1617; campo `dates` vuoto in `meta\profilo_csv.csv`).

#### 6. Trappole dei dati (materiale per la rubrica)

Ogni voce nomina file e campo.

1. **Il ballottaggio porta la data del primo turno.** ds1210 (Comunali 1993 ballottaggio): `Sessione` = 06/06/1993, ma il ballottaggio fu dopo; ds1247 (2011): `Sessione` = 15/05/2011, mentre il titolo di ds1111 dice "Ballottaggio del 29-30/5/2011"; ds1257 (2016): 05/06/2016, mentre ds1117 dice "Ballottaggio del 19/6/2016". I votanti sono diversi dal primo turno (ds1210: 827.953 contro 934.166 in ds1208, somma del campo `Votanti`), quindi i dati sono davvero del ballottaggio: sbagliata solo la data.
2. **Date sbagliate nel referendum 2025.** ds2931, ds2932, ds2933, ds2934: `Sessione` = `2022-06-12` (data del referendum 2022), mentre ds2930 ha 2025-06-08. I file si chiamano "20250608_Voti_E2" ma dentro la data è sbagliata.
3. **`Sessione` a volte non è una data.** ds1369 (referendum trivelle 17/4/2016): `Sessione` = `114`; ds1371 (referendum Lombardia 22/10/2017): `Sessione` = `117`. È un codice interno.
4. **Titolo tagliato.** ds1889: titolo "...Incandidabilità per reati non colposi: Risultati di Sez" (campo `title` del portale). Inoltre in molti titoli il carattere accentato è diventato `�` (es. "Unit�", "Indennit�", "Servit�", ds274, ds1377, ds1413...) già nei metadati del portale: non è un errore di scarico.
5. **Il file "Elettori" è a zero.** Nei 9 file ds1195, ds1196, ds1197, ds1198, ds1199, ds1200, ds1203, ds1204, ds1207 (Politiche 1979/83/87/92, Europee 1979/84/89, Regionali e Comunali 1980) il campo `Elettori` è 0 in tutte le righe (somma del campo = 0). Non si può calcolare l'affluenza.
6. **Elettori a zero in alcune sezioni, votanti > elettori in altre.** In quasi tutte le tornate dal 1985 in poi (esclusi i referendum 1981–1989, 1997 e 2017) ci sono da 2 a 24 sezioni con `Elettori` = 0 e da 4 a 39 con `Votanti` > `Elettori` (es. ds1624 Comunali 2021: 15 con elettori zero e 22 con votanti > elettori; `meta\controlli_coerenza_totali.csv`, campi `righe_elettori_zero`, `righe_votanti_gt_elettori`). Probabili sezioni ospedaliere/speciali (ds720 dichiara 24–31 sezioni ospedaliere): da verificare.
7. **Camera 1994 maggioritario: elettori diversi dal proporzionale.** ds1211: somma di `Elettori` 1.053.043 e ben 827 sezioni con votanti > elettori; ds1212 (stesso giorno, proporzionale): 1.183.474.
8. **`Votanti` a zero.** ds1216 (Senato 1996), ds1225 (Senato 2001), ds1240/ds1241/ds1242 (Provinciali 2009), ds1248/ds1249 (Circoscrizionali 2011): campo `Votanti` = 0 in tutte le righe (somma = 0).
9. **I conti non tornano.** In 39 dataset `Votanti` ≠ `Validi` + `Non validi` in molte righe (es. ds1209 Comunali 1993 Consiglio: 2.077 righe su 2.087; ds1220: 2.079 su 2.086; ds1396 caccia 1997: solo 4 righe; ds1216 e ds1225: tutte le righe, ma lì `Votanti` è 0). Elenco in `meta\controlli_coerenza_totali.csv`, campo `righe_votanti_ne_validi_piu_nonvalidi`. Nei referendum invece `Si` + `No` = `Validi` in tutte le righe di tutti i 74 dataset (campo `righe_si_piu_no_ne_validi` = 0).
10. **Sì/No con virgola decimale.** ds1369 e ds1371: campi `Si` e `No` scritti come `113,00` (testo con ",00"); negli altri referendum sono interi.
11. **Le 11 sezioni "9001–9011" del 2025.** ds2930–ds2934, ds2920: numeri fuori dalla numerazione (max 2.243), indirizzi `VIA S.VITTORE 35` (9001–9005) e `PZA ASCOLI GRAZIADIO ISAIA 2/A` (9006–9011), ciascuna con ~880–960 elettori e affluenza tra 82% e 92% (campi `Votanti`/`Elettori` di ds2930) mentre l'intera città è al 36,8% (354.138 / 961.877, somme degli stessi campi): probabilmente seggi per elettori fuori sede (ipotesi mia, da verificare). Contano nelle somme di `Elettori` del 2025 (961.877).
12. **Stesso giorno, numero di sezioni diverso tra file.** Politiche 2001 (13/5/2001): ds1225 (Senato) 1.247 sezioni, ds1226/ds1227 (Camera) e ds1228 (Comunali) 1.251 (campo `sezioni_distinte`). Dettaglio in `meta\sezioni_per_elezione.csv`.
13. **Il campo "CAP" dello stradario 2020 contiene solo le ultime 3 cifre** (es. `138` per 20138): ds939, campo `CAP` (valori 54–162).
14. **Il nome "Zona" cambia significato:** nei referendum 1985–1997 (ds1377–ds1402) la colonna `Zona` contiene le 20 circoscrizioni (1–20), dal 1999 le 9 zone; nei 5 referendum del 1981 (ds1372–ds1376) è vuota.
15. **Dati "ufficiosi".** Politiche 2018 (ds1188–ds1191, ds1260–ds1263), Politiche 2022 (ds1983–ds1990), Regionali 2023 (ds2204–ds2207): il titolo dice "dati ufficiosi", non ufficiali. Il portale non dice se sono stati sostituiti da quelli ufficiali.
16. **Metadati di migrazione.** 327 dataset su 328 hanno `metadata_modified` = 2026-05-08; non usarlo come data di aggiornamento reale.
17. **Il motore di ricerca del portale è impreciso**: `q=elezioni` restituisce 337 risultati (inclusi Censimento, Prezzi, ecc.); l'unico modo affidabile è filtrare per titolo e confrontare con `package_list`.
18. **Stesso campo, due scritture:** ds376 (elettori 2016) ha `INDIRIZZO SEDE` (con spazio), ds725 (elettori 2019) ha `INDIRIZZO_SEDE` (con underscore).

#### 7. File prodotti in questa cartella

- `NOTE.md` — questo file.
- `inventario_dataset.csv` — 328 righe, un dataset per riga (tipo, anno, righe, sezioni distinte, codifica, intestazione).
- `inventario_risorse.csv` — 658 righe, un file pubblicato per riga (url, formato, dimensione dichiarata, licenza).
- `raw\` — dati grezzi (257,9 MB, 511 file); `scripts\01_search.py … 06_master.py` — i programmi (vanno eseguiti con `python -I`).
- `meta\` — risposte grezze dell'API (`all_search.json`, `package_list.json`, `election_candidates.json`), `download_log.csv`, `profilo_csv.csv`,
  `controlli_coerenza_totali.csv`, `sezioni_per_elezione.csv`, `stabilita_territorio.csv`, `stabilita_sedi_consecutive.csv`.

#### 8. Per la fase 2 (promemoria, non fatto)

- Unificare nomi di colonna e codifiche; decidere come trattare ballottaggi (data) e sezioni 9001–9011.
- Tabella di corrispondenza circoscrizione (1–20) ↔ zona (1–9) per i confronti a cavallo del 1999.
- Sezione → NIL: partire da ds939 (per civico) e ripetere con gli altri stradari (ds1614, ds1862, ds2169, ds2741, ds2922, ds2973) per vedere se la sezione cambia NIL negli anni; poi decidere la regola per le 345 sezioni a cavallo.
- Valutare SIEL (ds23) per controllare i totali delle elezioni 1979–2000.

## 5. Qualità dell'aria, centralina per centralina

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `aria/`._

## 6. Ingressi in Area C

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `area-c/`._

## 7. Bici contro auto contro mezzi

_Fonti, date di scarico, licenze, ipotesi, scelte, problemi. Cartella `bici-auto-mezzi/`._

## 8. La Scala, cartellone dal 1778 a oggi

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `scala/`._

- 2026-10-29 — **Archivio online della Scala (dal 1943-44)**: il robots.txt di teatroallascala.org vieta ai programmi le pagine dell'archivio, e al primo giro l'agente si è fermato. Davide comunica di aver ricevuto l'autorizzazione dal Teatro alla Scala: si raccoglie con un programma, lentamente (pause di alcuni secondi), citando la fonte "©Teatro alla Scala".
- 2026-10-29 — **Cambiasi**: si usa l'edizione 1778-1881 (Internet Archive) più la cronologia di Romani 1862 per i confronti; la quinta edizione (1778-1906) è solo su HathiTrust, non accessibile dall'Italia, e va bene così (decisione di Davide).

## 9. Redditi e servizi: la città dei 15 minuti

_Fonti, date di scarico, licenze, ipotesi (velocità a piedi 4,5 km/h), scelte, problemi. Cartella `citta-15-minuti/`._

- 2026-10-29 — Punti di partenza: i numeri civici del Comune con coordinate (circa 51 mila), non una griglia (scelta di Davide). Media per quartiere (NIL) pesata sugli abitanti. Velocità a piedi: 4,5 km/h, lungo le strade.
