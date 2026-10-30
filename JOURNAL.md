# Milano in dati — JOURNAL

Diario del progetto: fonti, date di scarico, licenze, scelte, problemi.
Ogni problema trovato nei dati va annotato: diventa materiale per la rubrica "trappole dei dati".

## Decisioni generali

- 2026-10-29 — Cartella `milano-in-dati/`, repository GitHub pubblico `AndreottiVIII/milano-in-dati`, sito `andreottiviii.github.io/milano-in-dati` (scelti da Davide).
- 2026-10-29 — Filoni indipendenti (prima 4, poi 8: aria, Area C, bici/auto/mezzi, Scala aggiunti lo stesso giorno), ognuno nella sua sottocartella: `temperature/`, `donne-nelle-vie/`, `beni-culturali/`, `elezioni/`.
- 2026-10-29 — Regola licenze: se una fonte non permette di ripubblicare, nel repo vanno solo programmi e risultati, non i dati grezzi.
- 2026-10-29 — Divisione del lavoro: Opus coordina e fa il delicato, Sonnet scrive il codice, Sonnet medio il meccanico, Haiku solo controlli di testo.

- 2026-10-29 — **Idea: film e libri ambientati a Milano** (prima "dopo"; avviata la notte del 29/10, sezione 11). Fonti individuate:
  - Wikidata: P840 "luogo dell'ambientazione" = Milano e, per i film, P915 "luogo delle riprese"; CC0, in blocco.
  - Categorie di it.wikipedia: Film ambientati a / girati a Milano, Romanzi ambientati a Milano.
  - Open Library e Library of Congress, con il soggetto "Milan (Italy) -- Fiction".
  - Catalogo SBN, con i soggetti in italiano (accesso in blocco da verificare).
  - Lombardia Film Commission ed eventuali permessi per le riprese del Comune (da verificare).
  - Da non usare: IMDb, perché i luoghi delle riprese non sono nei file scaricabili e leggere il sito pagina per pagina non è permesso.
  - Limite: le fonti dicono raramente dove, dentro Milano.

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
- **Verificato il 29/10 sera** (`temperature/discrepanza/verifica_2026.md`): anche le stazioni vicine hanno l'estate 2026 più calda del 2022 (Juvara +0,62, Marche +0,50, Zavattari +0,84, Lambrate 0,00; Brera +0,63); Brera meno la media delle vicine nel 2026 = -0,11. Il record 2026 non è un difetto del sensore. Prima: il 2026 risulta il più caldo di sempre nello stesso periodo (19,3 °C contro i 18,7 del 2022). L'estate 2026 a Brera ha una media di 28,1 °C, contro i 27,4 del 2022. Il confronto con le stazioni vicine per il 2026 non è stato possibile: l'API di ARPA ha risposto "too many requests". Da rifare.
- **2026-10-29 notte, Brera 2008-2016** (`temperature/discrepanza/RAPPORTO_2008_2016.md`): con 10 stazioni ARPA vicine (6 scaricate ora, solo letture :00, CC0, `temperature/raw/arpa_omog/`) e il test SNHT, il sensore di Brera risulta più caldo di circa 0,65 °C (massime e minime) dal 11/12/2007 al 29/9/2016. Inizio e fine subito dopo ore di dati non validi (7-11/12/2007; 29/9/2016); sensori nuovi a Brera a luglio 2016 (anagrafica ARPA). Causa scritta non trovata. Correzione mese per mese proposta e **spenta** in `splice.json` (`"attivo": false`): decide il coordinatore. Se accesa: normale 1991-2020 da 14,45 a 14,26 °C, tendenza dal 1980 da +4,2 a +3,6 °C/secolo, 2022 resta l'anno più caldo, 2026 resta primo "finora".
- **Trappola dei dati**: quasi tutte le stazioni ARPA dell'area milanese hanno salti propri di 0,4-2 °C tra il 2002 e il 2019 (per esempio Lambrate luglio 2008-gennaio 2012): confrontare Brera con una sola vicina inganna.
- 2026-10-30 — **Brera 2008-2016** (`temperature/discrepanza/RAPPORTO_2008_2016.md`, agente Opus):
  - **Rottura del sensore Brera**: dall'11/12/2007 al 29/9/2016, cioè subito dopo dati non validi; nuovi sensori nel luglio 2016. Confermata in 6-7 coppie di stazioni su 10 (test SNHT).
  - **Ampiezza**: Tmax -0,64 °C (90%: -0,87 / -0,52), Tmin -0,65 °C. Causa non documentata.
  - **Effetto della correzione**: tendenza dal 1980 da +4,24 a +3,59 °C per secolo; record giornalieri del 2008-2016 da 70 a 40; il 2022 resta l'anno più caldo.
  - **Decisione di Davide**: nessuna correzione, solo una nota in pagina. In `splice.json` la correzione è pronta con `attivo: false`.

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
- 2026-10-30 — **Isabella d'Aragona confermata da Davide**: è la duchessa di Milano (1470-1524), moglie di Gian Galeazzo Sforza (`decisioni_davide.csv`); pagina delle vie ripubblicata.

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

### Fase 2 — tabella pulita e pagina (2026-10-29)

- `beni-culturali/pulito/beni_milano.csv`: 30.721 righe, chiave `iri` (l'`id` non è unico). Trappole in `pulito/problemi.md` (34).
- **Completezza** (27.459 schede con sede a Milano):
  - autore indicato nel 47,0%;
  - datazione nel 94,4%;
  - ente che le conserva nel 31,4%;
  - luogo più preciso di "Milano" nel 21,7%;
  - coordinate dentro il Comune nel 48,0% (13.193 schede in 769 punti).
- **Correzioni**: 2 coordinate con latitudine e longitudine scambiate, corrette; una (Cascina Mirabello) cade fuori dal Comune e non è sulla mappa.
- **Da verificare**:
  - Le 3.195 schede senza ente hanno tutte le coordinate di Brera; restano con l'ente "non indicata".
  - Link alle schede (`https://catalogo.beniculturali.it/detail/<Classe>/<codice>`): **verificati da Davide il 29/10 alle 21:36**. Il link di prova (HistoricOrArtisticProperty/0100106854) apre la scheda giusta: "Circoncisione di Gesù Bambino", dipinto di Benvenuti Giovanni Battista detto l'Ortolano.
- Pagina `docs/beni-culturali/`; dati derivati CC BY-SA 4.0 con attribuzione a ICCD (ArCo 2.0).

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
- 2026-10-29 sera — **Senato 1983-1994** aggiunto da Eligendo (i 6 collegi di Milano sommati; votanti di almeno 25 anni; nel 1994 le "liste" sono coalizioni): la serie del Senato ora va dal 1948 al 2022 senza buchi. Le 28 liste nuove sono state rivedute dal coordinatore: Polo delle Libertà nel Centrodestra, Progressisti nel Centrosinistra, Patto per l'Italia nel Centro. Il sito ha 167 elezioni.
- 2026-10-30 notte — **Elezioni per quartiere (NIL) dal 2016**:
  - 30 elezioni 2016-2026, con il legame ufficiale sezione-civico del 2020 (ds939); sezioni ritrovate tra il 98,2% e il 99,2%.
  - I voti di ogni sezione sono divisi tra i NIL in proporzione ai civici. La variante "NIL prevalente" differisce in media di 0,2 punti.
  - Prima del 2016 non si pubblica: il legame tiene solo per il 92-98% dei civici.
  - Esempi: comunali 2021, centrosinistra primo in tutti gli 88 NIL (dal 39% di Comasina al 61% di Porta Vigentina); europee 2024, destra prima in 6 NIL, tra cui Quarto Oggiaro (27%).

## 5. Qualità dell'aria, centralina per centralina

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `aria/`._

### Fase 1 — scarico (2026-10-29)

**Aria, stazione per stazione: note sul download (fase 1)**

Scaricato il 29/10/2026. Nessuna analisi, nessuna pagina del sito. Cartella: `milano-in-dati\aria\`.
Script in `scripts\` (01 ricerca, 02 scarico Comune, 03 scarico ARPA, 04-07 inventari e confronto). Risultati in `out\`.

#### 1. Fonti scaricate

##### A. Comune di Milano, dati aperti (CKAN, dati.comune.milano.it)
- Ricerca: `package_search?q=Rilevazione qualità aria` (risultato salvato in `raw\ckan_search.json`).
- Cartella: `raw\comune\` (36 file, 6,5 MB in totale; l'elenco con URL e date è in `raw\comune\_manifest.json`).
- **Rilevazione qualità aria 2002-2026** (uno per anno, 25 file CSV, nomi `ds4xx_qaria_datoariagiornostazione_year-AAAA.csv` fino al 2020 e `qaria_datoariagiornostazione_<data>.csv` dal 2021). Colonne: `stazione_id;data;inquinante;valore`. Un valore al giorno per stazione e inquinante. Il file 2026 (`ds2969`, `qaria_datoariagiornostazione_2026-10-29.csv`) viene aggiornato ogni giorno: arriva fino al 28/10/2026.
- **Report qualità aria 2005-2024** (20 file, `*_reportariagiorno_*.csv`). Colonne: `data;descrizione;previsione;tendenza`. Sono bollettini scritti a parole (per esempio "Superamento del Valore Limite per il PM10"), non numeri. Fermi al 16/04/2024 (`qaria_reportariagiorno_2024-05-08.csv`, 74 righe). Per il 2025 e il 2026 non esiste il report.
- **Stazioni monitoraggio inquinanti** (`ds484`): `qaria_stazione.csv`, `qaria_stazione.geojson`, `qaria_stazione_shp.zip`. 9 stazioni, con coordinate, id Comune (`id_amat`), id ARPA (`id_arpa`), inizio e fine attività.
- **Valori rilevati per i principali inquinanti 2004-2023** (`ds573_inquinanti_aria.csv`, 4,6 KB): solo riassunti annuali (media annua PM10 e NO2, giorni di superamento PM10 e O3). Utile come controllo, non come dato.
- Licenza: CC-BY (campo `license_id` = `cc-by` in `raw\ckan_search.json`). I dati grezzi si possono ripubblicare citando la fonte (Comune di Milano).

##### B. ARPA Lombardia, dati.lombardia.it (Socrata)
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

#### 2. Le stazioni (9) e come si corrispondono

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

#### 3. Cosa c'è, stazione per stazione (inventario completo in file)
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

#### 4. Il Comune e ARPA si sovrappongono? Chi è più lungo?
**Sì, sono le stesse misure.** Il Comune pubblica un riassunto giornaliero dei dati ARPA. Confronto fatto su tutti i giorni in comune (`out\confronto_comune_arpa.csv`):
- **La data del Comune è il giorno dopo la misura.** Se spostiamo la data ARPA di un giorno avanti, il PM10 coincide nel 98-100% dei giorni (differenza entro ±1 µg/m³, colonna `uguali_1_mean`; per esempio stazione 6 PM10: 0,993, 4.740 giorni). Senza spostamento la coincidenza scende al 10%.
- **Cosa rappresenta il valore giornaliero del Comune** (trovato per confronto, non dichiarato nei metadati):
  - PM10 e PM2.5: media giornaliera (coincidenza 99%).
  - NO2 e O3: **massimo orario del giorno**, non la media (coincidenza entro il 5%: 94-99% per il NO2, 90-99% per l'O3; colonne `uguali_5pc_max`).
  - CO (`CO_8h`): massimo della media mobile su 8 ore (coincidenza 95-99%, colonna `uguali_1_max8h`).
  - Benzene e SO2: più vicini alla media giornaliera (benzene entro 1 µg/m³ nel 82-95% dei giorni; SO2 solo 60-70%, da verificare in fase 2).
- **Lunghezza**: ARPA è molto più lunga (NO2 dal 1977, SO2 dal 1971, polveri totali dal 1976, `inventario_arpa.csv`, campo `prima`; il Comune parte dal 2002) e ha il dato **orario**. Il Comune è più comodo (un valore al giorno già pronto) e **ha dati che ARPA non ha** in alcuni periodi (vedi trappole 9 e 10).
- Consiglio per la fase 2: ARPA per le serie lunghe, per l'orario e per i metalli; il Comune per riempire i buchi di ARPA (trappole 15 e 16), dopo aver riallineato la data e l'indicatore.

#### 5. Unità, medie, flag, codici di dato mancante
- Unità (campo `unitamisura` del registro ARPA): µg/m³ per tutto tranne CO (mg/m³) e metalli/benzo(a)pirene (ng/m³). Il Comune non scrive le unità nei file: CO_8h è in mg/m³ (valori 0-10), gli altri in µg/m³.
- ARPA: NO2, CO, SO2, O3, benzene, black carbon, ammoniaca, NOx sono **orari** (`inventario_arpa.csv`, `passo_mediano` = 0 days 01:00:00). PM10, PM2.5 e polveri totali sono **giornalieri** (passo 1 giorno). Metalli e benzo(a)pirene sono giornalieri a intervalli: passo mediano 3-6 giorni.
- ARPA: l'ora è "a fine ora": la prima riga di ogni anno è alle 01:00 e l'ultima è alle 00:00 del 1° gennaio dell'anno dopo. Per questo ogni sensore ha 1 riga isolata nel primo giorno dell'anno successivo. Per i PM la data è il giorno stesso alle 00:00.
- ARPA: codice di dato mancante **`-9999`** nel campo `valore` (380.679 righe su 8,8 milioni; sempre insieme a `stato` vuoto). `stato` vale `VA` (valido, 8.458.001 righe) oppure vuoto (380.895). `idoperatore` quasi sempre 1 (restano 51 righe con 39 e 29 con 10). Nessun altro valore negativo.
- Il Comune: dato mancante = **cella vuota** nel campo `valore`; nessun flag di validazione. Decimali con il punto. Valori 0 presenti in 45 righe (benzene, CO, PM10: da guardare in fase 2, possono essere dati sotto soglia).
- 22 righe ARPA hanno orari non tondi (per esempio 16:00:03).

#### 6. Trappole dei dati (non sono cambiamenti dell'aria)

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

#### 7. Cosa NON ho scaricato / limiti
- ARPA: solo i 71 sensori con `comune` = Milano. Non ho scaricato le stazioni vicine (Pioltello, Cinisello, Rho, Limito…) né le stime comunali (`ysm5-jwrn` e simili), né i dati meteo.
- Il file `out\_arpa_all.pkl` (535 MB) è stato cancellato; si rigenera con `python -I scripts\05_inventario_arpa.py raw\arpa out` (serve anche per rilanciare `scripts\06_confronto.py out`).
- Il confronto Comune-ARPA è fatto con tutti i giorni in comune ma non per ogni inquinante e per ogni anno a parte: i risultati per stazione sono in `out\confronto_comune_arpa.csv`.
- Non ho verificato le posizioni dei punti con fonti esterne né la causa dell'asterisco nei nomi "via Pascal *" e "via Senato *".
- Il significato esatto degli indicatori del Comune (max orario, max 8 ore) è dedotto dal confronto: da confermare con chi pubblica il dataset.

### Fase 2 — serie pulita e pagina (2026-10-29)

- File pulito `aria/pulito/aria_giornaliera.csv` (337.417 righe giornaliere, 1977-28/10/2026; ARPA prima, Comune solo dove ARPA manca, con la data spostata di -1 giorno); storia delle stazioni in `stazioni_storia.csv`; trappole in `aria/pulito/problemi.md` (23).
- Primi numeri (ARPA, CC0; nessuno è una stima di causa, mancano i dati meteo):
  - PM10 2021-25: Senato ha una media di 33,3 µg/m³, con 55,6 giorni l'anno sopra 50 (la UE ne ammette 35). Ricalcolato dal coordinatore: torna.
  - NO2 2021-25: Marche ha una media di 41,9, sopra il limite UE di 40 e 4,2 volte il valore OMS 2021.
  - Area C, 12 mesi prima e dopo il 16/1/2012: NO2 -16,9% a Senato e Verziere (le due centraline dentro Area C), -5,1% nelle altre di Milano, -6,7% fuori Milano. Negli altri anni lo stesso confronto per il centro va da -9,2% a +9,5%.
  - Lockdown 2020 contro 2017-19: NO2 -37,8% a Milano e -39,0% fuori Milano.
- **Controllo del coordinatore**: sul poligono ufficiale di Area C (`area-c/raw/ds51.../disciplina_aree.geojson`, tipo AREA_C) cadono dentro solo Senato e Verziere, come ipotizzato dall'agente.
- Scaricati anche NO2 e PM10 di 5 stazioni ARPA fuori Milano (Pioltello, Magenta, Sesto, Rho, Cinisello) come confronto: tutte le stazioni di Milano sono dentro Area B.
- Ipotesi da ricordare: un anno conta come valido se ha almeno il 75% dei giorni (la UE chiede il 90%).

## 6. Ingressi in Area C

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `area-c/`._

### Fase 1 — scarico (2026-10-29)

**Area C (ingressi nel centro di Milano) - note sul download, fase 1**

Data del download: 29/10/2026. Nessuna analisi fatta: solo scaricamento e controllo dei file.
Tutto in `area-c\raw\` (558 MB, 185 file). Scripts in `area-c\scripts\`. Controlli in `area-c\verifica\`.

#### Fonte unica
Open data del Comune di Milano (CKAN): https://dati.comune.milano.it/api/3/action/package_search?q=area%20c
(ricerche fatte: area c, ecopass, area b, varchi, accessi, ztl, congestion, ingressi; il catalogo trovato e' in `raw\_catalogo\catalogo.json`).
Gestore dei dati: AMAT (Agenzia Mobilita' Ambiente Territorio). Licenza di tutti i 175 dataset scaricati: **CC-BY (Creative Commons Attribution)**.
Si possono ripubblicare anche i dati grezzi, citando "Comune di Milano / AMAT" come fonte.
Nessuna registrazione o clic di licenza richiesti. Nessun errore di download (`raw\_download_log.tsv`).

#### Cosa c'e' (tre serie diverse, con livelli di dettaglio diversi)

##### A. 01/01/2012 - 18/09/2016: serie "vecchia", solo aggregata (niente varchi)
- 5 anni x 7 tipi di tabella x 2 (giornaliere ds779-ds813, "orarie" ds814-ds848). I tipi: totale, per classe Euro, per categoria veicolo (persone, merci, bus, altro, NC), per autorizzati/non autorizzati, per residenti/non residenti, per alimentazione, per veicoli di servizio.
- File: `raw\ds779_...` ... `raw\ds848_...` (CSV; i JSON uguali non sono stati scaricati).
- Le tabelle "orarie" sono in realta' **a mezz'ora** (campo `data` + `timeIndex` 00:00, 00:30, ...; 48 righe al giorno). I giornalieri hanno `timeIndex` (data) e `totale`; il campo `areac` = 1 se Area C era attiva in quel momento.
- Controllo: per ogni anno la somma dei giornalieri `totale` e' identica alla somma delle mezz'ore `totale` (es. 2012: 46.601.227 transiti in entrambi).

##### B. 01/09/2016 - 31/12/2018: ds1085 (solo totale giornaliero)
- `raw\ds1085_area-c-accessi-giornalieri-2016-2018\ds1085_ingressi_areac_precedenti.csv`: 850 righe, campi `data_giorno`, `numero_transiti_giornalieri`.

##### C. 09/2016 - 11/2024: file mensili, a mezz'ora e PER VARCO
- 99 zip, uno per mese (ds862-ds896, ds899-ds958, ds1070-ds2885), da settembre 2016 a novembre 2024, mesi tutti presenti. Ognuno contiene un CSV con le colonne: `dataora, id_varco, esenti, moto, residenti, veicoli_servizio, categoria_euro, tipologia_alimentazione, categoria_veicolo, classe_areac, fap, areac, numero_transiti` (13 colonne, uguali in tutti i mesi). Una riga = una mezz'ora x un varco x una combinazione di caratteristiche del veicolo; `numero_transiti` = quanti passaggi. 0,6-1,6 milioni di righe al mese, 5-7 MB per zip.
- I codici dei campi sono decodificati in `raw\ds861_area-c-decodifica-dei-campi\ingressi_areac_decode.csv` (es. categoria_veicolo: 1 altro, 2 bus, 3 merci, 4 persone; classe_areac: 1 autorizzati, 2 ecologici, 3 paganti residenti, 4 paganti di servizio, 5 altri paganti, 6 moto; categoria_euro 0-7; tipologia_alimentazione 0-14).
- Posizione dei varchi: `raw\ds82_varchi-area-c\ingressi_areac_varchi.csv` (+ geojson e shapefile): 42 varchi, `id_amat` 57-98, nome, longitudine, latitudine. **I dati mensili si collegano ai varchi**: `id_varco` mensile = `id_amat` (verificato: tutti gli id coincidono).
- Orario: `dataora` e' ora locale con scostamento (+01 inverno, +02 estate); nel giorno del cambio d'ora di marzo 2024 ci sono 46 mezz'ore, come atteso.

##### D. Serie giornaliera ufficiale 2019-2024 (ds1072), due file
- `raw\ds1072_...\ingressi_areac_2019-2023_no_dic.csv`: 1781 righe, 01/01/2019 - 30/11/2023, solo totale (`numero_transiti_giornalieri`). Manca dicembre 2023 (da qui "no_dic").
- `raw\ds1072_...\ingressi_areac_2025-01-17.csv`: 305 righe, 01/12/2023 - 30/11/2024, con totale h24 e dettaglio autoveicoli / ciclomotori-moto, nelle fasce 7.30-19.30 (Area C attiva), 00.00-7.29 e 19.30-23.59.

##### E. Altri dataset utili (piccoli)
- `raw\ds959_varchi-areab`: varchi di Area B (188 righe: nome, stato, atto autorizzativo, coordinate; 149 attivi e sanzionanti, 22 in pre-esercizio, 17 da programmare). Aggiornato 07/11/2023. **Non ci sono dati di accessi Area B.**
- `raw\ds51_aree-pedonali-e-ztl`: poligoni di aree pedonali, ZTL, Area C e Area B (aggiornato 02/05/2023). La riga di Area C ha solo `val_inizio` 2000-01-01 e `val_fine` 2050-01-01: **valori segnaposto, non la vera data di inizio**. Nessuna ordinanza o tariffa e' indicata.
- **Ecopass (2008-2011): nessun dataset trovato** nel portale (ricerca "ecopass" = 0 risultati). Il primo anno disponibile e' il 2012.

#### Risposte alle domande della fase 1

**Granularita'.** Cambia negli anni. 2012 - 18/09/2016: totale per mezz'ora o per giorno, con spaccati per tipo di veicolo, ma senza varco. Dal 09/2016: mezz'ora x varco x caratteristiche del veicolo (file mensili). Serie ds1072 2019-2024: solo giornaliera.

**Copertura 2012 - 11/2024.**
- Serie A, giorni mancanti nei giornalieri: 2012 31/3 e 1/4 (2 giorni); 2014 6/2, 1/6 e 4-17/8 (16); 2015 dal 25/10 al 15/12 (52); 2016 dall'8/1 al 29/1 tranne il 28/1 (21). 2013 completo. Le tabelle "orarie" hanno gli stessi giorni vuoti (NaN o zero) piu' alcuni giorni a zero (es. 30/5/2015, 24/10/2015) e restano vuote dopo il 18/9/2016, anche se i file arrivano a fine anno.
- Dal 01/09/2016 i file mensili sono tutti presenti. Giorni senza nessun dato in nessuna serie: 27/01/2018, 29/07/2018, 20-26/12/2021, 25-31/12/2022 (16 giorni). La nota del dataset ds1072 dichiara solo gli ultimi due buchi (2021 e 2022).
- Nei file mensili mancano anche 27-31/01/2020, 17-23/02/2020, 20-26/06/2022, 13-19/11/2022, 19-25/02/2023, 21-27/05/2023: ci sono pero' nella serie giornaliera ds1072. Per avere una serie giornaliera completa vanno unite ds1085 + ds1072 + mensili.
- Il file ds1072 "nuovo" (12/2023-11/2024) manca di 61 giorni (2/5-1/6/2024 e 2-31/8/2024), presenti nei mensili.
- Dopo il 30/11/2024: **nulla**. Mancano tutto il 2025 e il 2026 (ds1072 aggiornato al 17/01/2025).

**Varchi.** 42 varchi (id 57-98) da 09/2016 a 05/2022. Da giugno 2022 i file mensili hanno 40 varchi: spariscono 87 (SANT'AGOSTINO) e 89 (OLIVETANI). Il file dei varchi li elenca ancora tutti e 42 (aggiornato 25/10/2026) e non dice quando sono stati tolti.

**Date di cambio delle regole.** Nessun dataset le elenca. Pagina ufficiale citata dai dataset: https://www.comune.milano.it/aree-tematiche/mobilita/area-c (non consultata). Da verificare con fonti ufficiali prima di usarle: avvio di Area C (gennaio 2012), eventuali cambi di tariffa e divieti per classe Euro.

#### Trappole dei dati
1. **Rottura di livello nel 2016.** Fino a fine 2015 la serie A ha una media di circa 130.000-140.000 transiti/giorno (campo `totale`; con agosto piu' basso). Da gennaio 2016 la stessa serie scende a circa 45.000 (tutte le categorie, anche merci e bus, calano di circa 3 volte). Nei 18 giorni in comune (1-18/9/2016) la serie A dice 43.179 al giorno in media contro 162.262 di ds1085. Non spiegato nei dataset: probabilmente conteggio parziale (pochi varchi o solo alcuni transiti) da gennaio a settembre 2016. **Non unire la serie A del 2016 al resto senza correggerla.**
2. Agosto e' ovunque molto basso (es. agosto 2012: 73.921 al giorno contro circa 137.000 dei mesi normali): e' reale, non un buco.
3. Le tabelle "orarie" sono a mezz'ora.
4. La somma dei mensili coincide con le serie giornaliere (rapporto 0,999-1,02; identico per il ds1072 nuovo). Scarti oltre l'1% in 6 giorni di ds1085 (dic 2017-mar 2018) e 23 giorni del ds1072 vecchio (soprattutto 2020). Vedi `verifica\` e script 04.
5. Formati diversi: nei mensili 2024 i numeri sono tra virgolette, nei mensili 2020 la data ha le barre (`2020/03/01`), negli altri i trattini; nei file mensili 2016-2018 `id_varco` e' senza virgolette.
6. Il ds1072 dice che "dall'anno 2024" c'e' il dettaglio auto/moto, ma la colonna `moto` esiste nei mensili da sempre. Il totale ds1072 comprende moto e ciclomotori.
7. File non scaricati di proposito: i JSON identici ai CSV dei dataset 2012-2016.
8. Il portale segna "ultima modifica" 08/05/2026 per quasi tutti i dataset, ma i dati finiscono nel 2024: la data di aggiornamento non indica nuovi dati.

#### File di controllo
`verifica\copertura_mensili.csv` (per mese: righe, giorni, varchi, transiti, giorni mancanti; le colonne `dt`, `n`, `day` non ci sono: la colonna `col` e' 16 perche' include 3 campi di servizio aggiunti dal controllo, il file originale ne ha 13), `verifica\varchi_per_mese.csv`, `verifica\giornaliero_da_mensili.csv` (totale, moto, auto per giorno sommando i varchi, 2016-2024).
Script: 01_catalogo.py (catalogo), 02_scarica.py (download, riprendibile), 03_verifica.py, 04_confronto_giornaliero.py.

### Fase 2 — serie pulita e pagina (2026-10-29)

- Serie giornaliera `area-c/pulito/ingressi_giornalieri.csv`: 3.013 giorni, dall'1/9/2016 al 30/11/2024 (ds1085 e ds1072, moto comprese), con le suddivisioni per tipo di veicolo, classe Euro e paganti. Ingressi per varco in `ingressi_varco_giorno.csv`. Trappole in `area-c/pulito/problemi.md`.
- **La serie 2012-2015 resta a parte**: nei 18 giorni in comune legge 43.179 ingressi al giorno contro 153.474 (rapporto 0,28; sulle sole auto 0,345, quasi uguale per tutte le categorie). Sembra contare circa un terzo delle auto e nessuna moto. Non è un sottoinsieme di varchi. Non è stata corretta; da chiedere ad AMAT.
- Primi numeri (feriali di settembre-novembre): 163.933 al giorno nel 2017, 163.981 nel 2019, 137.788 nel 2024 (-16%). Ad aprile 2020 40.072 contro 153.559 ad aprile 2019 (-74%). Il varco più usato è Turati, con 11.828 al giorno; il picco è alle 8:30 nel 2019 e alle 9:00 nel 2023.
- **Controllo del coordinatore**: ricalcolato sulla serie pulita, includendo i festivi: 163.165 nel 2019 e 136.985 nel 2024 (-16%), aprile 2020 -73%. Torna.
- **Altre trappole**:
  - Il campo `areac` resta a 1 anche durante le sospensioni Covid.
  - Le date di Covid e regole vengono dalla stampa (il sito del Comune risponde 403 ai programmi): sono "da verificare".
  - Non esiste un elenco aperto degli scioperi.
  - I varchi 87 e 89 spariscono dal 30/5/2022.
- **Per il legame con l'aria**: dentro Area C ci sono Senato e Verziere; nessuna centralina fuori Area C sta entro 1 km dal confine (Liguria e Juvara a circa 1,2 km).

### Legame con l'aria (filone 5) — 2026-10-29

- **Metodo**:
  - Differenze nello stesso giorno: NO2 dentro Area C (Senato, Verziere) meno fuori, cioè Marche, Liguria e Pascal più 5 centraline fuori Milano.
  - Solo feriali, dall'1/9/2016 al 30/11/2024.
  - Si tengono fermi giorno della settimana, mese, anno e meteo ARPA di Brera (vento, pioggia, temperatura).
  - Intervalli al 95%.
  - Dettagli in `area-c/legame_aria/RISULTATI.md`.
- **Risultato**:
  - Nessun legame stabile: 10.000 ingressi in più vanno con -0,08 µg/m³ [-0,71; +0,54] nella differenza dentro meno resto di Milano.
  - Gli esperimenti naturali non vanno nello stesso senso: agosto -2,3, lockdown stretto -8,2, Natale +1,5, seconda sospensione Covid +6,0.
  - Dal 2016 al 2024 gli ingressi calano di un quarto, ma la differenza resta piatta.
  - Prima e dopo il 16/1/2012: -17,5% dentro contro -4,2% nel resto di Milano. Su 13 altre coppie di anni, 5 mostrano cambi altrettanto grandi.
- **Cosa si può dire**: con queste stazioni non si vede un legame, e non si riesce a misurarlo; effetti fino a circa 0,5 µg/m³ ogni 10.000 ingressi non si vedrebbero. Non vuol dire che Area C non conti. La pagina lo dice così.

## 7. Bici contro auto contro mezzi

_Fonti, date di scarico, licenze, ipotesi, scelte, problemi. Cartella `bici-auto-mezzi/`._

### Fase 1 — scarico (2026-10-29)

**NOTE - filone 7: bici contro auto contro mezzi pubblici (fase 1, solo scarico)**

Scaricato il 29 ottobre 2026. Nessuna analisi fatta. Scripts in `scripts\`, dati in `raw\`.

#### 1. Rete stradale OpenStreetMap
- **Fonte**: estratto della Lombardia di openstreetmap.fr, `https://download.openstreetmap.fr/extracts/europe/italy/lombardia-latest.osm.pbf` (340 MB). Dati OSM aggiornati al **29/10/2026 ore 01:08 UTC** (file `lombardia.state.txt`, sequenza 7349062).
- **Perche' questa strada**: Overpass (tutti i server provati) rispondeva "pieno/timeout"; Geofabrik "nord-ovest" (594 MB, 28/10/2026) funzionava ma e' piu' grande. Nessun programma di ritaglio (osmium) sul PC, quindi ho scritto un ritagliatore in Python (`scripts\clip_pbf.py`, usa solo numpy).
- **Ritaglio**: rettangolo lat 45.350-45.572, lon 8.990-9.330 (Comune di Milano piu' circa 4 km intorno). File `raw\osm_milano\milano_buffer.osm.gz` (17,9 MB compresso, XML OSM standard, anche letto da molti programmi). Statistiche con `scripts\osm_stats.py`.
- **Contenuto** (conteggi dal file, tag `highway`, `oneway`, `maxspeed`, ecc.): 181.476 strade/percorsi con tag `highway` (73.376 footway, 33.415 service, 24.802 residential, 9.519 tertiary, 6.716 cycleway, 2.838 pedestrian, ecc.); 779.196 nodi; `oneway=yes` su 39.964 strade, `oneway:bicycle` su 939 (no=469, yes=467, -1=3); `maxspeed` su 18.433 strade; 4.072 semafori (`highway=traffic_signals`), 40.175 attraversamenti pedonali (`highway=crossing`), 3.426 stop, 4.524 dare-precedenza. Relazioni: 4.380 divieti di svolta (`type=restriction`), 61 itinerari (`route=bicycle`), 28 multipoligoni stradali.
- **Piste ciclabili**: `highway=cycleway` 6.716 strade; il conteggio "ciclabile" che esce dallo script (15.712) e' troppo largo perche' conta anche `cycleway:*=no`. Da rifare con regole precise in fase 2.
- **Licenza**: ODbL 1.0, (c) contributori OpenStreetMap. Si puo' ripubblicare citando la fonte; chi ripubblica una versione modificata deve usare la stessa licenza.
- **Trappole**: i nodi con tag sono tenuti solo se `highway`, `crossing`, `barrier`, `traffic_calming`; le strade sono troncate al rettangolo (nessun nodo fuori). Nel file ci sono anche strade `proposed`/`construction` (298) e `platform`/`corridor`: da scartare in fase 2. Il tag `maxspeed` c'e' solo su ~10% delle strade: per le altre servono velocita' tipiche per tipo di strada.

#### 2. GTFS (orari mezzi pubblici)
Nessun account, chiave o clic di accettazione necessari.
- **ATM / Comune di Milano (AMAT)**: `https://dati.comune.milano.it/gtfs.zip` (scheda `ds929-orari-del-trasporto-pubblico-locale-nel-comune-di-milano-in-formato-gtfs`, mantenuto da AMAT, aggiornato ogni 2-4 settimane). File `raw\gtfs\gtfs_comune_milano_amat.zip`, 25,4 MB (la scheda dichiara 60 MB, errata). Estratto in `raw\gtfs\ext_comune\`.
  - `feed_info.txt`: versione 424, inizio 16/10/2026. **Validita': 16/10/2026 - 20/11/2026** (`calendar_dates.txt`, 36 giorni; `calendar.txt` e' vuoto, tutto e' per data). Oggi (29/10) e' coperto, ma scade tra tre settimane: va riscaricato.
  - Un solo ente (`agency.txt`: ATM). `routes.txt`: 169 linee = 5 metro (M1-M5, `route_type` 1), 17 tram (`route_type` 0), 147 bus/filobus (`route_type` 3). `stops.txt`: 4.915 fermate. `trips.txt`: 124.020 corse. `stop_times.txt`: 2.900.116 righe (307 MB estratto). Ha anche `shapes.txt`. Tutte le fermate sono dentro il rettangolo di Milano.
  - **Non ci sono** treni suburbani/Passante, ne' linee extraurbane ATM: sono nell'altro file.
  - Licenza: CC-BY (scheda CKAN "Creative Commons Attribution"): ripubblicabile citando Comune di Milano / AMAT.
- **Trenord (treni regionali, S, RE, R)**: portale Regione Lombardia, scheda `3z4k-mxz9` "Orario Ferroviario Regionale Gtfs", `https://www.dati.lombardia.it/api/views/3z4k-mxz9/files/d893b62a-6f97-44fc-b31b-e92a9c37b057?download=true&filename=trenord_gtfs.zip`. File `raw\gtfs\trenord_gtfs.zip`, 1,66 MB, estratto in `ext_trenord\`.
  - File datato 03/08/2026; **validita' fino al 12/12/2026** (`calendar_dates.txt`: 140 date da 26/07 al 12/12/2026, include oggi). Un ente (Trenord). 63 linee (60 `route_type` 2, 3 di tipo bus), 566 stazioni (38 nel rettangolo di Milano), 8.470 corse, 90.553 righe di `stop_times` (circa 10,7 fermate per corsa).
  - Ci sono le S (S1-S13, S19, S30-S50), RE, R e RE51/RE54 per Malpensa. Non ho verificato se il Malpensa Express e' completo.
  - Licenza: CC BY 4.0 (Trenord, via PoliS-Lombardia/Regione): ripubblicabile citando.
- **Trappole**: il feed ATM non ha `calendar.txt` (solo date); il feed Trenord non ha ne' `calendar.txt` ne' `shapes`, ogni corsa ha un suo `service_id`. Le due fonti hanno ID fermate diversi: i trasferimenti metro-treno vanno costruiti a mano (distanza a piedi). Nessun orario in tempo reale. Le corse Trenord hanno poche fermate per corsa (mediana 10): da controllare in fase 2 che i tempi di percorrenza bastino.

#### 3. BikeMi e incidenti
##### BikeMi
- Scheda `ds65_infogeo_aree_sosta_bike_sharing_localizzazione_` (Stazioni BikeMi). File `raw\bikemi\bikemi_stazioni.csv` (61 KB, separatore `;`) e `.geojson` (127 KB). Campi: `id_amat, stato, numero, nome, tipo, stalli, sede, indirizzo, zd_attuale, anno, LONG_X_4326, LAT_Y_4326`.
- 325 stazioni, tutte `attiva` (264 monofacciali, 58 bifacciali, 3 virtuali), 9.452 stalli in totale; anno di installazione fino al **2021**. **Trappola**: i file risalgono a settembre 2022 (il Comune ha toccato la scheda il 08/05/2026 ma non i file): il numero attuale di stazioni potrebbe essere diverso. Niente disponibilita' in tempo reale (non richiesta). Licenza CC-BY.

##### Incidenti stradali
Nessuna fonte aperta con le coordinate di ogni incidente a Milano: ISTAT non le pubblica nei file aperti; il Comune pubblica solo conteggi mensili.
- **Migliore con luogo (strada/civico)**: Regione Lombardia / PoliS-Lombardia, "Incidenti Stradali - Microdati - Anno AAAA" (dati ISTAT, rilevazione IST-00142, incidenti con lesioni a persone). Un file per anno, schede Socrata su dati.lombardia.it (ID in `scripts\incidenti_ids.json`; per es. 2024 = `san9-3hvn`). Scaricato solo il Comune di Milano (`denominazione_comune = MILANO`) per **2010-2024**: `raw\incidenti\lombardia_microdati\incidenti_microdati_lombardia_AAAA_MILANO.json`, 15 file, ~66 MB. Righe per anno: 12.085 (2010), 8.263 (2019), 4.856 (2020), 7.743 (2024). Script: `scripts\scarica_incidenti.py`. Il 2025 non c'e' ancora.
  - Campi: anno, mese (niente giorno ne' ora), `nome_strada` (testo libero: "via Monte Rosa, 57", "via Padova, palo luce 124", "via Valtellina incrocio viale Jenner"), `tipo_strada`, `localizzazione_incidente`, `intersezione_nonintersezione`, `natura_incidente`, tipo veicolo A/B/(C), eta' conducenti, pedoni morti/feriti, morti entro 24 ore/30 giorni, feriti. **Niente coordinate**: per metterli su mappa serve geocodificare `nome_strada` (circa 46% ha civico o palo luce, 49% e' un incrocio). Granularita': via/incrocio.
  - Licenza: CC BY 4.0 (PoliS-Lombardia - ISTAT). Ripubblicabile citando.
- **Conteggi del Comune** (totali mensili, senza luogo preciso): `raw\incidenti\comune_milano\` - `ds175` per mese 2001-2025 (300 righe; campi `Anno, Mese, IncidentiMortali, IncidentiSoliFeriti, Morti, Feriti`), `ds176` per natura dell'incidente (2.698 righe), `ds177` per municipio 2020-2025 (703 righe), `ds179` per numero di veicoli (300 righe). Dati Polizia Locale; licenza CC-BY. Il 2025 e' completo fino a dicembre.
- **Trappola dei numeri**: i due archivi non coincidono. 2024: Comune `ds175` 7.602 incidenti (IncidentiMortali + IncidentiSoliFeriti), 9.384 feriti; microdati 7.743 righe, 9.585 feriti. Il 2020 (Covid) ha circa meta' dei casi. I morti nei microdati vanno letti da `tot_morti_a_24ore_incidente` o `..._30gg`, che sono due definizioni diverse.

#### 4. Strumenti di calcolo percorsi su questo PC (non installato nulla)
PC: Intel i5-12600K (10 core, 16 thread), 31,8 GB RAM, 78 GB liberi su disco, Windows 11.
- **Presenti**: Python 3.12.10 con numpy 2.5, scipy 1.18, networkx 3.6, pandas 3.1, numba 0.67, scikit-learn, matplotlib, lxml, requests; Git Bash con `pdftotext`.
- **Assenti**: Java (`java -version` non trovato), Docker (non trovato), WSL (non installato); anche igraph, osmium, shapely, pyproj, geopandas, pyarrow, r5py, osmnx, pyrosm.
- **Installabili da pip** (esistono pacchetti per Windows, non installati): r5py 1.1.7, pyvalhalla 3.9.1, igraph 1.0.0, osmium 4.3.2, shapely 2.2.0, pyproj 3.8.0, pandana 0.8, pyarrow 26.0.
- **Valutazione**:
  - r5py e OpenTripPlanner: vanno bene su carta (bici, piedi, GTFS insieme), ma servono Java (JDK 21 o simile) che qui non c'e'; l'OSM va in formato `.pbf` (si converte con osmium da pip). Pro: motore completo, mappe di tempi gia' pronte. Contro: installare Java, 4-8 GB RAM, poco controllo sulle ipotesi (semafori, auto).
  - OSRM/Valhalla: OSRM ha bisogno di Docker (assente). Valhalla ha pacchetto pip per Windows (pyvalhalla), ma e' solo strade (bici/auto/piedi), non i mezzi pubblici.
  - **Consigliato: approccio in Python puro** con `scipy.sparse.csgraph` (Dijkstra veloce) sui grafi bici, auto e piedi costruiti dal file OSM, piu' un percorso mezzi pubblici di tipo "connection scan / RAPTOR" scritto con numba sul GTFS, con camminata fino alla fermata e attesa. Pro: nessuna installazione grossa, tutte le ipotesi (velocita' per tipo di strada, semafori, sensi unici per bici, Area C, tempo di parcheggio) in chiaro e modificabili, mappe a colori per punto di partenza con un solo calcolo da un punto verso tutti. Contro: da scrivere e collaudare (alcune settimane di lavoro in piu'), serve `shapely/pyproj` o equivalenti per le coordinate (si possono evitare con formule semplici su Milano).
  - Piano B se il Python puro e' troppo lento o impreciso: installare un JDK e usare r5py solo per i mezzi pubblici + piedi, tenendo bici e auto in Python.

#### 5. Area C: tariffa e orari
- **Tariffe**: PDF ufficiale del Comune "Area C: ticket in vigore dal 30 ottobre 2023", `https://www.comune.milano.it/documents/20118/35188/Area+C+nuove+tariffe+dal+2023+Area+C.pdf/5ee21a73-7301-60c7-d2fe-5e2f77e8a158?version=1.0&t=1746021538283&download=true`, salvato in `raw\areac\area_c_tariffe_2023.pdf` (45 KB). Valori: tutti i veicoli **7,50 euro**; residenti (e assimilati) con veicolo registrato **3,00 euro dal 51° accesso/anno**; veicoli "di servizio" 4,50; veicoli in sosta in autorimesse in Area C 4,50; pagamento tardivo (entro 7 giorni) 22,50; NCC oltre nove posti 60 / 97,50 / 150 secondo la lunghezza. Il PDF e' versione 1.0 caricata ad aprile 2025.
- **Orari**: lunedi'-venerdi' 7:30-19:30, festivi esclusi; nel fine settimana non e' attiva. Un biglietto vale per tutti i passaggi dello stesso veicolo nel giorno. Fonte: riassunto dei risultati di ricerca sulle pagine FAQ ufficiali del Comune (`https://servizicrm.comune.milano.it/centro-supporto/KA-01151/Orari-di-attivazione-Area-C`, "Quando e' attiva Area C?"; `.../KA-01642/Costo-accesso-giornaliero-Area-C`; `.../KA-01156/Ingressi-gratuiti-residenti-Area-C`). **Non ho potuto leggere le pagine ufficiali**: il sito del Comune risponde "403 Forbidden" a qualsiasi programma (curl, WebFetch, anche la copia di web.archive.org). Gli orari vanno quindi verificati a mano su `https://www.comune.milano.it/aree-tematiche/mobilita/area-c` prima di usarli. Alcuni siti terzi indicano 5 euro: sono vecchi o sbagliati, vale il PDF.
- Il confine di Area C (poligono) non e' scaricato qui: probabilmente e' nei dati del filone `area-c`.
- Licenza del PDF: non indicata, non ripubblicare il file; i valori sono un fatto pubblico e si possono citare.

#### Cosa manca / bloccato
- Orari e regole Area C da pagina ufficiale (sito del Comune blocca i programmi); il poligono di Area C.
- Incidenti con coordinate: non esiste in forma aperta; serve geocodificare le strade (fase 2).
- Stazioni BikeMi aggiornate a oggi (file del 2022).
- Velocita' reali del traffico auto: nessun dato aperto, come previsto.

### Fase 2 — motore dei percorsi e taratura (2026-10-29)

- **Motore in Python** (numpy/scipy/numba, niente servizi a pagamento né chiavi):
  - grafi a piedi, in bici e in auto da OSM;
  - Connection Scan sugli orari GTFS: ATM aggiornato alla v425, valido dal 26/10 al 30/11/2026, più Trenord;
  - mezzi: fino a 800 m a piedi per la fermata, cambi con al massimo 300 m a piedi, media di 6 partenze;
  - griglia di 2.915 celle da 250 m; da un punto a tutte le celle in 0,1-0,3 secondi.
- **Ipotesi da tarare** (tabella in `bici-auto-mezzi/NOTE.md`, "Fase 2"):
  - bici 15 km/h sulle ciclabili e 13 km/h su strada, con attese ai semafori (in pratica circa 12 km/h);
  - auto alle 8:00 tarata su TomTom 2025 (38'43" ogni 10 km); alle 12:00 e alle 21:00 sono ipotesi;
  - minuti per parcheggiare per zona;
  - Area C 7,50 €, orari "da verificare".
- **Primi risultati** (ore 8:00, 300 origini casuali verso tutte le celle):
  - 0-2 km vince la bici nel 92% dei casi;
  - 2-4 km la bici nel 78%;
  - 4-6 km bici 44%, auto 39%, mezzi 17%;
  - 6-8 km l'auto nel 55%;
  - 8-12 km l'auto nel 68%.
  - Provvisori fino alla taratura.
- **Taratura**: `bici-auto-mezzi/tragitti_prova.csv` (20 tragitti, martedì 3/11/2026 alle 8:00, 12:00 e 21:00) con le istruzioni in `COME_CONTROLLARE.md`. Davide riempie i tempi di Google Maps.
- **Incidenti**: su 500 righe di prova, il 74% si colloca bene sulla mappa (28,6% al civico esatto, 45,4% all'incrocio), il 17% solo con la via, l'8% non si trova.
- 2026-10-29 sera — **Taratura su Google Maps**: un agente ha letto nel browser i tempi di Google Maps per i 20 tragitti (martedì 3/11/2026, senza account né controlli anti-robot; per l'auto il punto medio della forchetta indicata da Google). Mediana del rapporto nostra stima / Google:
  - bici 1,45 (le nostre stime sono troppo lente);
  - auto 0,87 (alle 8:00 1,05, alle 12:00 0,72, alle 21:00 0,75);
  - mezzi 0,91.
  - Dettagli in `bici-auto-mezzi/out/taratura_confronto.md`. Nel sito non si pubblicano i tempi di Google, solo i nostri errori in percentuale.
- 2026-10-30 notte — **Taratura finale e pubblicazione**:
  - **Verifica dei mezzi** (`out/verifica_mezzi.md`): il 14,5% delle celle non ha una fermata a meno di 800 m a piedi (parchi, campi, scali, bordo della città). Non è un errore. Corretti due errori veri:
    - un minuto di accesso "da stazione" applicato a ogni fermata d'autobus;
    - mancavano i cambi tra linee oltre i 300 m (Loreto M1-M2, Centrale): ora si usa `transfers.txt` di ATM.
  - **Taratura su 120 tragitti Google** (84 per tarare, 36 per controllare). Errore mediano sui 36 di controllo:
    - bici dal 38% al 6%;
    - auto dal 17% al 10%;
    - mezzi dal 13% al 7,5%.
  - **Parametri finali** in `docs/bici-auto-mezzi/data/taratura.json`:
    - bici 16-19 km/h, con 6 s per semaforo;
    - auto con fattori 0,92 alle 8:00, 0,77 alle 12:00, 0,85 alle 21:00;
    - mezzi con 180 s di margine nei cambi e 60 s di accesso alle stazioni.
  - **Risultati**: alle 8:00 la bici vince nell'88% delle coppie, l'auto nell'11%, i mezzi nell'1%; alle 21:00 l'auto nel 57%. Il risultato dipende molto dalla velocità della bici: la pagina lo dice.
  - Nel sito non ci sono i tempi di Google, solo i nostri errori. Pagina `docs/bici-auto-mezzi/` pubblicata.
- 2026-10-30 notte — **Incidenti in bici (fase 4)**:
  - **Collocazione sulla mappa**: 131.435 incidenti 2010-2024 collocati solo con dati locali (civici e incroci OSM): l'80,1% ha una posizione (incidenti in bici: 83,8%). Gli incroci, confrontati con i civici, distano in mediana 30 m.
  - **Numeri**: la bici è coinvolta in 16.067 incidenti con feriti in 15 anni (dall'8% al 13% del totale), 74 morti in quegli incidenti; 573 incidenti con monopattino nel 2024.
  - **Punti critici**: corso Buenos Aires / piazzale Loreto (47), via Gioia / viale Lunigiana (24), corso Buenos Aires / piazza Oberdan (21). Sono conteggi, non rischio per viaggio: mancano i conteggi delle bici che passano.
  - **Trappola**: `morti24` e `morti30` si sommano, non sono uno dentro l'altro.
  - Sezione "Dove la bici è più a rischio" pubblicata nella pagina bici-auto-mezzi.

## 8. La Scala, cartellone dal 1778 a oggi

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `scala/`._

- 2026-10-29 — **Archivio online della Scala (dal 1943-44)**: il robots.txt di teatroallascala.org vieta ai programmi le pagine dell'archivio, e al primo giro l'agente si è fermato. Davide comunica di aver ricevuto l'autorizzazione dal Teatro alla Scala: si raccoglie con un programma, lentamente (pause di alcuni secondi), citando la fonte "©Teatro alla Scala".
- 2026-10-29 — **Cambiasi**: si usa l'edizione 1778-1881 (Internet Archive) più la cronologia di Romani 1862 per i confronti; la quinta edizione (1778-1906) è solo su HathiTrust, non accessibile dall'Italia, e va bene così (decisione di Davide).

### Fase 1 — scarico (2026-10-29)

**La Scala, spettacoli dal 1778 a oggi - note della fase 1 (scaricamento)**
Aggiornato il 29/10/2026. Cartella: `scala\`. Fase 1 = solo scaricare e capire le fonti; nessuna analisi, nessuna pagina del sito.

#### Riassunto
- **1778-1881 (e 1862): fatto.** Le cronologie di Cambiasi (1872, 1881) e di Romani (1862) sono scaricate, libere, con testo OCR già pronto.
- **1943-oggi: FERMATO.** L'archivio storico della Scala è nella parte del sito che `robots.txt` vieta ai programmi. Non ho raccolto nulla.
- **1906-1943: buco.** Solo riempimento parziale da Wikidata e Wikipedia. Pista nuova: Marangoni-Vanbianchi copre 1906-1920.
- **Cambiasi 5a edizione (1778-1906): non scaricabile dall'Italia** (HathiTrust la apre solo agli USA).

#### 1. Cambiasi e le altre cronologie dell'Ottocento
Tutto da Internet Archive (`https://archive.org/download/<id>/<file>`), scaricato il 29/10/2026 con `scripts\scarica_cambiasi.py`. Nessun account, nessun clic di licenza.

| Cartella in `raw\` | Che cos'è | File (MB) |
|---|---|---|
| `cambiasi\teatroallascala100camb` | **Cambiasi, "Teatro alla Scala 1778-1881"** (Ricordi 1881), copia Getty/Internet Archive, 168 pagine, scansione 300 dpi. **È la copia migliore.** | pdf 12,5; testo OCR `_djvu.txt` 0,35; **hOCR con riquadri delle parole** 11,1; immagini JP2 (zip) 88,8 |
| `cambiasi\teatroallascala00cambgoog` | Stessa edizione 1881, copia Google, più scadente | pdf 5,1; testo 0,34 |
| `cambiasi\bub_gb_e864LY_9qOUC` | **Cambiasi, "Rappresentazioni date nei reali teatri di Milano 1778-1872"** (Ricordi 1872) | pdf 7,6; testo 0,27 |
| `romani\teatroallascalac00romauoft` | **Luigi Romani, "Teatro alla Scala. Cronologia di tutti gli spettacoli" (1862)**, copia Toronto, 224 pagine. Seconda cronologia indipendente 1778-1862: serve per controllare Cambiasi | pdf 17,2; testo 0,47 |
| `cambiasi\pdf24_merged-16` | **Marangoni e Vanbianchi, "La Scala. Studi e ricerche, note storiche e statistiche 1906-1920"** (1922). **Solo il testo OCR** (il pdf pesa 520 MB, non scaricato) | testo 1,35 |

**Cosa copre e cosa no.**
- Il volume 1881 non è un elenco di tutte le sere: è una *serie delle opere in musica* e una *serie dei balli*, per stagione (anno, stagione, mese, giorno, titolo, maestro, poeta, tipo, esecutori principali, esito). In una stagione ogni opera compare una volta (la riga "id." ripete la stagione), non con tutte le repliche. Vale lo stesso per il 1872.
- La tabella delle opere occupa **due pagine affiancate**: a sinistra anno/stagione/mese/giorno/titolo/maestro (PDF pagina 25, hOCR pagina 24), a destra poeta/tipo/esecutori/esito (pagina seguente). Per fare una riga sola bisogna riunire le due metà in ordine.
- La "Spiegazione delle abbreviature" (pag. 400 originale) dice: asterisco = opera scritta apposta per la Scala; esiti = ottimo, buonissimo, buono, mediocre, cattivo, pessimo; C. carnevale, Q. quaresima, P. primavera, E. estate, A. autunno, Aw. avvento. Le note a piè di pagina `(1)`, `(2)` sono mescolate nei campi data.
- Romani (1862) è invece prosa per stagione: "1781 CARNEVALE / Antigono. D. s. Musica ..." con attori e balli, quindi più difficile da tabulare ma ricco di nomi.
- Marangoni-Vanbianchi riporta i cartelloni delle stagioni 1906-1920 (titoli, autori, elenco artistico) in testo continuo. **È la prima pista concreta per il buco 1906-1943, ma solo fino al 1920.**

**Prova OCR (8 pagine).** Tesseract **non è installato** (`tesseract: command not found`, nessuna cartella Program Files); non l'ho installato. Ho fatto così:
1. Il testo e le coordinate di Internet Archive (motore ABBYY FineReader) esistono già per tutto il libro: per l'1881 non serve rifare l'OCR. L'hOCR dà ogni parola con il suo riquadro (pagina 24: 513 parole). Raggruppando per altezza si ricostruiscono bene le righe: x circa 680 anno, 840 stagione, 1090 mese, 1250 giorno, 1400 titolo, 2280 maestro. Difetti visti: nomi dei maestri storpiati ("Sftlieri" = Salieri, "Mjsliweczek" = Myslivecek, "Yaleutini" = Valentini), "id." a volte perso, accenti sporchi. Serve una lista di nomi (Wikidata) per correggere.
2. Ho provato anche il **motore OCR integrato di Windows 11 (it-IT, senza installare nulla)** su 8 pagine (`test_layout\c1881_p*_winocr.txt` e immagini `.png`). Funziona ma peggio di ABBYY: legge colonna per colonna, sbaglia sulle colonne strette ("Rub:nelli", "Baldueci"). Va bene come ripiego, e per le foto di Gatti (script al punto 4).
Opzioni se serve di meglio: installare Tesseract con i dati `ita` (decisione di Davide), oppure usare l'hOCR già pronto per Cambiasi.

**Cambiasi 5a edizione 1778-1906** (Ricordi 1906, "completamente rifusa", 350 illustrazioni): è su HathiTrust (record 100371822, copia Harvard `hvd.32044082278698`, codice diritti `pdus` = pubblico dominio solo negli USA). Dall'Italia la pagina risponde 403 e l'Online Books Page scrive "US access only". Non l'ho aggirato. Una copia Google esisterebbe (scheda della Biblioteca Nazionale di Israele) ma l'API di Google Books oggi ha la quota esaurita. **Da fare**: cercare la copia 1906 su Google Books con "scarica PDF", o chiedere a una biblioteca (Braidense, Biblioteca del Museo Teatrale alla Scala) o a qualcuno negli USA.

**Licenza.** Cambiasi e Romani sono morti da ben più di 70 anni: opere di pubblico dominio. Internet Archive segna `NOT_IN_COPYRIGHT` per Romani e per l'edizione Google 1881 e "Public Domain Mark 1.0" per il 1872. Le scansioni (Google, Getty, Toronto) chiedono in genere uso non commerciale e di non togliere le note di provenienza: **i pdf e le immagini non li ripubblicherei**; i *dati* estratti (titoli, date, nomi) sono fatti, citando la fonte. Marangoni-Vanbianchi: la licenza "CC BY-NC-ND" l'ha messa chi ha caricato il file (un privato), non gli autori, e non ho verificato le date di morte: **solo pista, nessuna ripubblicazione**. (Valutazione mia, non parere legale.)

#### 2. Archivio storico della Scala dal 1943 - FERMATO
- `https://www.teatroallascala.org/robots.txt` (letto il 29/10/2026): `User-agent: *` ... `Disallow: /it/archivio` e `Disallow: /en/archive` (più `/api/`, `/web/`). L'archivio storico è proprio su `/it/archivio/archivio-storico.html`.
- Il dominio `www.archiviolascala.org` (citato dal sito come "DAM Digital Archive") **rimanda alla stessa pagina** vietata; `archivio.teatroallascala.org` non risponde.
- Per il mandato ("se robots.txt o i termini lo vietano, STOP") **non ho raccolto stagioni né record**. Nota onesta: seguendo il rimando di archiviolascala.org ho scaricato una sola pagina (la maschera di ricerca, 116 kB) che sta nella zona vietata; non l'ho conservata e ne ho letto solo il menu (filtri per tipo di spettacolo, titolo, autore, artista, luogo; sezioni Locandine, Fotografie, Libretto, Opera in breve, Discografia, Costumi, Accessori). Non ho aperto il `disclaimer` (anch'esso sotto `/it/archivio/`).
- Termini d'uso: le pagine `disclaimer` e `contatti` dell'archivio stanno nella zona vietata, quindi non le ho lette. **Strada giusta: chiedere il permesso e i dati direttamente alla Scala** (archivio storico / ufficio stampa). Il sito dice che la versione online è "limitata e semplificata" rispetto all'archivio completo. Copyright: ©Teatro alla Scala, da citare.
- Stima del totale: non fatta (richiederebbe interrogare l'archivio).

#### 3. Buco 1906-1943: riempimento parziale da fonti aperte
**Wikidata** (CC0). Interrogazioni SPARQL del 29/10/2026 con `scripts\wikidata_scala.py` (Q5471 = Teatro alla Scala):
- `raw\wikidata\premiere_p4647.json` (0,70 MB): 580 righe, 456 opere con "luogo della prima rappresentazione" (P4647) = Scala; 442 con data (P1191). Per decennio: 1900-09: 15, 1910: 15, 1920: 24, 1930: 22, 1940: 7. Tipi (P31): opera 489 righe, balletto 19.
- `raw\wikidata\premiere_p276_event.json` (0,82 MB): 1248 righe, 1008 voci con "luogo" (P276) = Scala; **426 "stagione del Teatro alla Scala", 107 "serata inaugurale della stagione", 479 "produzione operistica", 59 "prima mondiale"**; solo 514 voci hanno la data (P585).
- `raw\wikidata\premiere_location_any.json` (0,52 MB): 822 righe, 772 voci con data di prima e luogo Scala (P291/P276/P4647 uniti). Per decennio 1900: 48, 1910: 15, 1920: 33, 1930: 24, 1940: 6; nel 2010 ce ne sono 60 (produzioni recenti).
- Le voci Wikidata Q52277762 / Q52277360 sono proprio il libro di Romani 1862.

**Wikipedia italiana** (CC BY-SA 4.0), via API MediaWiki, `scripts\wikipedia_scala.py`, in `raw\wikipedia\`:
- `Stagioni_liriche_del_Teatro_alla_Scala.json` (0,28 MB, revisione 152735080 del 03/10/2026): cronistoria 1778-2020 con opere per anno, direttore, interpreti, regia. Per 1906-1943 è **molto rado**: circa 2-5 titoli all'anno (es. 1930: Turandot, La Sagredo, La fanciulla del West), mentre le stagioni vere ne avevano molti di più. Contiene anche "Opere più rappresentate" e "Apertura della stagione lirica".
- `Prime_stagionali_al_Teatro_alla_Scala.json` (rev. 150788130), `Stagioni_di_balletto_del_Teatro_alla_Scala.json` (rev. 148776796), `Teatro_alla_Scala.json` (rev. 152968485).
- Il buco **non è chiuso**: l'unica fonte completa resta Gatti vol. 2 (carta) più, per 1906-1920, Marangoni-Vanbianchi.

#### 4. Programma per le foto di Gatti (solo scheletro)
`scripts\gatti_foto_ocr.py` + `scripts\winocr.ps1`: cartella di foto -> pretrattamento (grigi, contrasto, ingrandimento) -> OCR con riquadri (Tesseract se c'è, altrimenti motore Windows) -> righe -> due CSV (`gatti_grezzo.csv` righe con data, `gatti_da_rivedere.csv` il resto). Colonne comuni a tutto il progetto: fonte, pagina_o_foto, data_iso, stagione, luogo, tipo, titolo, compositore, direttore, interpreti, regia_coreografia, note, testo_riga, affidabilita_ocr. Provato su una pagina di prova (gira, 50 righe); il riconoscimento del formato di Gatti va adattato guardando 3-4 foto vere.

#### 5. Come confrontare le fonti più avanti
- **Cambiasi 1881 / 1872 / Romani 1862** (stessi anni 1778-1862): confronto per (anno, stagione, titolo normalizzato, maestro). Tre fonti indipendenti permettono di trovare errori di OCR e di stampa.
- **Cambiasi vs Wikidata**: per ogni opera con P4647 = Scala e data, cercare nella serie di Cambiasi lo stesso anno + titolo normalizzato (senza articoli e accenti, varianti ortografiche) e controllare la data (Cambiasi dà mese e giorno della prima).
- **Wikipedia (stagioni) vs Cambiasi**: per 1778-1881 trova i titoli che mancano in Wikipedia; per 1906-1943 il contrario.
- **Dopo il 1943**: Wikipedia vs archivio Scala solo se la Scala concede i dati.
- Il collegamento tra tutte è una tabella di titoli normalizzati e compositori (Wikidata ha anche gli alias).

#### Trappole dei dati
- Il libro 1881 elenca opere per stagione, non rappresentazioni: non si contano le sere di spettacolo.
- Tabelle su due pagine; note `(1)`, `(2)` dentro le celle; "id." per ripetere la stagione.
- Nomi storpiati dall'OCR; accenti e ligature diventano `�`.
- La copia Google 1881 ha nel titolo "1776-1881" per errore del catalogo: l'inizio è il 1778.
- Wikidata: lo stesso spettacolo può comparire come opera (P4647) e come produzione/evento (P276): contare per voce, non per riga (580 righe = 456 opere).
- L'API di Google Books ha oggi la quota esaurita.

#### Archivio Scala (fase 2, 29/10/2026) - in attesa
- La Scala ha autorizzato la raccolta (vedi JOURNAL 29/10/2026). Citazione: "(c) Teatro alla Scala".
- Struttura: l'archivio storico non ha elenchi di stagioni ne' indirizzi fissi per spettacolo: si arriva ai dati solo da una maschera di ricerca (`/it/archivio/ricerca.html`) con filtri su tipo, titolo, autore, artista, luogo e stagioni (86 stagioni dalla 1943-44 alla 2025-26). Non ci sono servizi JSON dietro.
- Problema: la ricerca funziona solo se il browser invia un codice "info" prodotto da uno script anti-bot (`etnobot.js`). Senza, il sito risponde "Non sono stati trovati spettacoli" (provato su stagione 1946 e su "Callas"). Falsificare quel codice vorrebbe dire aggirare l'anti-bot: non l'ho fatto.
- Risultato: nessuna stagione ne' spettacolo raccolti, nessun `pulito/archivio_scala.csv`. Serve che la Scala tolga l'anti-bot per questa raccolta o mandi i dati direttamente (dettagli in STATO.md).
- 2026-10-29 — **Locandine della Scala dal 1943 (archivio-storico-locandine)**: la ricerca funziona solo con il campo `info`, prodotto da uno script anti-robot (`etnobot.js`) con i movimenti del mouse e il tempo passato sulla pagina. Senza quel campo risponde "Non sono stati trovati oggetti" (prova del 29/10, una sola richiesta). Davide riferisce che la Scala permette la raccolta anche con Chrome "headless". Il coordinatore (Claude) non lo esegue: superare con un programma un controllo anti-robot ancora attivo è un'azione che non fa, nemmeno su richiesta o con un'autorizzazione riferita a voce. Strade possibili:
  1. Davide salva le pagine dei risultati dal suo browser in `scala/locandine_salvate/`, e un programma le legge.
  2. La Scala manda un file con i dati, oppure toglie il controllo per il programma del progetto (eccezione per indirizzo o User-Agent). A quel punto la raccolta automatica, lenta e con citazione, è possibile.
  - Filone in pausa per decisione di Davide. L'agente della tabella unica (Cambiasi, Romani, Wikipedia) è stato fermato a metà, con lo stato salvato in `scala/STATO.md`.
- 2026-10-29 sera — **PDF da Davide (iCloud)**, salvato in `scala/raw/programmi_davide/programmi_scala.pdf` (146 MB, 682 pagine). È Gatti, "Il Teatro alla Scala nella storia e nell'arte (1778-1963)", **volume 1** (il racconto), copia Internet Archive `owo_W8-BSY-089` della Seattle Public Library, con il testo già riconosciuto. Non contiene la cronologia: "Cronologia" compare una sola volta, a pagina 449, e la premessa rimanda al secondo volume. Come deciso all'inizio da Davide, il volume 1 non si usa come fonte di dati. Il libro è del 1964 e ancora protetto: resta solo sul PC. Per il cartellone 1906-1963 serve il volume 2.
- 2026-10-29 notte — **Fonti dopo il 1963** (`scala/FONTI_POST_1963.md`):
  - (1) **Catalogo SBN**: programmi di sala, una scheda per produzione, 1964-2023, spesso con direttore, regista e cast; manca il giorno. Esempi: 18 produzioni nel 1975-76, 14 nel 1985-86, 13 nel 1965-66. Si legge dall'interfaccia JSON che il sito stesso usa (robots permette, nessuna chiave, nessun anti-robot). Licenza non indicata: si usano solo fatti, con citazione. Raccolta avviata, lenta (circa 300 richieste).
  - (2) **Tintori, "Duecento anni di Teatro alla Scala"**, vol. 2, cronologia 1778-1977 (1979): solo su carta, in 55 biblioteche (anche Braidense e Biblioteche di Milano). Darebbe i giorni del 1964-77: Davide può fotografare le pagine.
  - (3) **MusicBrainz** (CC0): utile solo per controllo, con 38 date.
  - Non utilizzabili: gli archivi dei giornali, che non si raggiungono da questo PC, ed Europeana, che chiede una chiave.
  - Per il 1978-2022 nessuna fonte libera dà le date dei singoli giorni.
- 2026-10-29 notte — **Tabella unica del cartellone** (`scala/pulito/cartellone.csv`, 5.146 righe; copertura in `copertura.csv`):
  - **Righe per fonte**: Cambiasi 1.076 (1778-1881), Romani 750, Wikipedia 1.092, prime assolute da Wikidata 772, Marangoni 118, Gatti vol. 1 951 (1882-1962), stagioni della Scala 2023-27 387.
  - **1906-1963**: le stagioni con almeno 5 titoli passano da 14 su 57 (solo Wikipedia) a 55 su 57 con Gatti. Gatti nomina però circa 10 titoli a stagione su 20-30 reali.
  - **Ancora scoperto**: 1964-2022 ha circa 4 titoli all'anno (arriverà SBN).
  - **Estrazione da Gatti**: titolo e stagione giusti nell'87% di 70 casi controllati a mano; i nomi nel 79%. I collegamenti incerti sono lasciati vuoti.
  - **Fonti non ripubblicabili** (`ripubblicabile=no`): Gatti e Marangoni. I brani di Gatti (`_gatti_contesti_locali.csv`) restano solo sul PC.
  - **Problemi aperti**:
    - i balli di Cambiasi non sono ancora letti;
    - mancano Cambiasi 1832 e 1835;
    - Marangoni non ha i cast;
    - in Gatti le tournée sono mescolate agli spettacoli in sede.
- 2026-10-30 notte — **Raccolta SBN finita** (`scala/sbn/`):
  - 318 ricerche e 1.240 schede complete, nessun blocco; 1.725 righe dopo aver unito 347 doppioni del catalogo.
  - Contenuto: 920 produzioni, 498 concerti, 224 libretti di stagione.
  - Produzioni per decennio: 1963-69 80, anni '70 167, '80 136, '90 167, 2000 183, 2010 148, 2020-24 47.
  - Copertura: circa 14-18 all'anno nel 1970-2019, contro le 15-20 di una stagione tipica; il calo dal 2020 dipende dal ritardo di catalogazione.
  - Accordo con Wikipedia: 45 aperture su 56 (80%); 67 titoli su 93 nelle stagioni complete.
  - Limiti:
    - c'è l'anno di stampa; la data si ricava dalle note (683 produzioni);
    - il direttore è indicato solo nel 14% dei casi, il regista nel 16%, il cast nel 4%.
  - Licenza non indicata: si usano solo fatti, con la citazione "Catalogo SBN – ICCU".
- 2026-10-30 notte — **Pagina della Scala pubblicata** (`docs/scala/`, dati da `scala/scripts/pagina_dati.py`):
  - 4.635 titoli per anno dopo l'unione delle fonti.
  - Copertura per anno con i buchi segnati: A 1882-1905; B 1919-21, probabile chiusura; C 1943-46; D le date dopo il 1977.
  - Fonti con licenza e citazione, compreso "(c) Teatro alla Scala" per le stagioni 2023-27: autorizzazione riferita da Davide ("poi li citiamo").
  - Da Gatti si pubblicano solo titolo, autore, stagione e direttore; Marangoni compare solo nei conteggi.
  - Sistemato in pubblicazione un difetto di `sbn_parse.py`: il numero d'ordine del libretto finiva nel titolo (181 righe).
- 2026-10-30 notte — **Libri e locandine in biblioteca** (`scala/LIBRI_E_LOCANDINE.md`):
  - **Locandine**: nel catalogo SBN ce ne sono solo una quarantina, sparse. La Biblioteca Livia Simoni (Museo Teatrale) ne conserva circa 3.000, consultabili su appuntamento e senza catalogo online.
  - **Libri**:
    - Tintori vol. 2 (1964-77, con i giorni) si trova alla Braidense, alla Civica d'Arte e nelle Biblioteche di Milano.
    - Dopo il 1977 non risulta in SBN nessuna cronologia.
    - Da verificare di persona: Tintori, "Cronologia" [1993?], e gli annuari EDT "Opera '87-2012".
  - **Programmi di sala**: il Conservatorio Verdi ha i programmi del 62% delle produzioni 1964-2022.
  - **Visita consigliata**: la biblioteca del Conservatorio Verdi.

## 9. Redditi e servizi: la città dei 15 minuti

_Fonti, date di scarico, licenze, ipotesi (velocità a piedi 4,5 km/h), scelte, problemi. Cartella `citta-15-minuti/`._

- 2026-10-29 — Punti di partenza: i numeri civici del Comune con coordinate (circa 51 mila), non una griglia (scelta di Davide). Media per quartiere (NIL) pesata sugli abitanti. Velocità a piedi: 4,5 km/h, lungo le strade.

### Fase 1 — scarico (2026-10-29)

**Città dei 15 minuti: note sulla fase 1 (scaricamento e controlli)**

Data: 29 ottobre 2026. Cartella: `citta-15-minuti\`. Nessun calcolo di tempi a piedi fatto (è la fase 2).
Come leggere: ogni numero dice da quale file e da quale campo viene. Dove non c'è scritto altro, i file sono in `raw\comune_milano\<cartella>\`.
Tutti i controlli sono rifacibili con `scripts\controlli.py` e `scripts\analisi_collegamenti.py` (risultati in `controlli_risultati.json` e `collegamenti_risultati.json`).

#### In breve (le cose che decidono il resto del lavoro)

1. **I redditi sono per CAP, non per quartiere.** 38 CAP (da 20121 a 20162), 6 anni di imposta (2019-2024). Un CAP non coincide con un NIL: il confronto con i redditi si può fare con precisione solo a livello di CAP (38 zone), non di 88 NIL. Dettagli nel paragrafo "Redditi".
2. **I punti (civici) ci sono e sono buoni:** 65.160 righe, 57.405 "applicati" (in vigore), 51.917 numeri civici distinti (via + numero + lettera): è questo il numero "circa 51.000" scelto da Davide.
3. **Le poste ci sono nei dati del Comune** (85 uffici): OSM serve solo come controllo incrociato.
4. **Gli asili nido sono vecchi** (anno scolastico 2018/19, l'ultimo) e per il 16,5% delle righe mancano le coordinate. Va segnalato nei risultati o integrato con OSM.
5. **I parchi sono poligoni**, 1.065 pezzi, di cui 737 sotto i 500 m²: per "arrivare a un parco" non basta il centro del parco (le coordinate nel CSV sono centroidi). Servono i bordi/ingressi e una soglia di dimensione.
6. **La rete pedonale c'è già:** la fase 1 della filiera "bici-auto-mezzi" (strand 7) ha già ritagliato OSM per Milano + circa 3 km di margine. Non copiato, solo referenziato (vedi "Rete pedonale").
7. **Nessun blocco:** nessun sito ha chiesto registrazione o accettazione di licenze con un clic.

---

#### 1. Servizi con una posizione (portale dati del Comune, CKAN, `https://dati.comune.milano.it/api/3/action/package_show?id=<id>`)

Scaricato il 29/10/2026. Per ogni cartella ci sono anche i metadati originali in `_metadati.json`. Le coordinate sono sempre gradi WGS84 (EPSG:4326), tranne dove scritto. La data "metadata_modified" è la data in cui il file è stato caricato sul portale (molti sono stati ricaricati in blocco l'8/5/2026): **non** dice quanto sono aggiornati i dati. Dove si legge un anno vero, è indicato.

Controlli fatti su ogni set (script `scripts\controlli.py`): coordinate mancanti o a zero; punti fuori dal confine del Comune (`confine_comune`); NIL dichiarato nel file diverso dal NIL calcolato dal poligono (`nil_vigenti`); punti dentro un poligono di parco (`parchi`); duplicati (stesso nome+indirizzo, stesso punto, righe identiche).

| Servizio | Dataset (id) | Cartella | Record | Dati di | Coordinate (campi) | Licenza |
|---|---|---|---|---|---|---|
| Farmacie | `ds501_farmacie-nel-comune-di-milano` | `farmacie` | 422 | elenco regionale, aggiornato 15/10/2026 | `LONGITUDINE`, `LATITUDINE` | CC0 |
| Medici di medicina generale | `ds234-sociale-medici-medicina-generale` | `mmg` | 1.189 righe = 428 punti distinti | 29/10/2026 | `LONG_X_4326`, `LAT_Y_4326` | **CC BY-NC (non commerciale)** |
| Asili nido | `ds47-istruzione-asili-nido-localizzazione-delle-strutture` | `nidi` | 1.790 righe (3 anni) | a.s. 2016/17, 2017/18, 2018/19 (`CODANNOSCOLASTICO`) | `LONG_WGS84`, `LAT_WGS84` | CC BY |
| Scuole infanzia | `ds3014-...-2025-2026` (e storico `ds671`) | `scuole_infanzia_2025`, `scuole_infanzia_ds671` | 294 (a.s. 2025/26); `ds671` ha 3.640 righe = 12 anni | 2025/26 | `LONG_X_4326`, `LAT_Y_4326` | CC BY |
| Scuole primarie | `ds40-infogeo-scuole-primarie-localizzazione` | `scuole_primarie` | 2.604 righe = 12 anni; ultimo anno 216 | 2025/26 | idem | CC BY |
| Scuole secondarie I grado | `ds3016-...-2025-2026` (e storico `ds46`) | `scuole_sec1_2025`, `scuole_sec1_ds46` | 147 (2025/26); `ds46` 1.736 = 12 anni | 2025/26 | idem | CC BY |
| Scuole secondarie II grado | `ds78_infogeo_scuole_secondarie_ii_grado_localizzazione_` | `scuole_sec2` | 174 righe = 109 punti distinti | anno non dichiarato | idem | CC BY |
| Edifici scolastici statali (controllo) | `ds1863-...-as-2020-2021` | `scuole_edifici_statali_2020` | 560 | a.s. 2020/21 | idem | altro (attribuzione) |
| Scuole paritarie (controllo) | `ds1582-...-2020-2021` | `scuole_paritarie_2020` | 461 | a.s. 2020/21 | `LONG_X_4326`, `LAT_Y_4326` (non controllate) | altro (attribuzione) |
| Biblioteche | `ds1306-sistema-bibliotecario-milano` | `biblioteche_sistema` | 26 | caricato 10/7/2026 | `long`, `lat` | CC BY |
| Biblioteche (vecchi, solo confronto) | `ds41...` (2007), `ds287` (2013-15, senza coordinate) | `biblioteche_loc_2007`, `biblioteche_rionali_2013` | 232 e 81 | 2007; 2013-2015 | non controllate | CC BY |
| Mercati comunali coperti | `ds2471-mercati-comunali-coperti` | `mercati_coperti` | 26 (21 attivi, 5 no: Selinunte, Ca' Granda, Umbria, Gorla, QT8; campo `attivo`) | "mag24" nel nome file = maggio 2024 | `LONG_X_4326`, `LAT_Y_4326` | CC BY |
| Mercati settimanali scoperti | `ds291-economia-mercati-settimanali-scoperti` | `mercati_settimanali` | 85 (tutti `status mss`=attivo) | maggio 2024 | idem | CC BY |
| Mercati degli agricoltori | `ds2629-mercati-degli-agricoltori` | `mercati_agricoltori` | 9 | non dichiarato | `LONG_WGS84`, `LAT_WGS84` | CC BY |
| Parchi e giardini | `ds89_infogeo_parchi_giardini_localizzazione_` | `parchi` | 1.065 poligoni | non dichiarato | GeoJSON (poligoni); CSV = centroidi `LONG_X_4326_CENTROID`, `LAT_Y_4326_CENTROID` | CC BY |
| Impianti sportivi (punti) | `ds34_infogeo_impianti_sportivi_localizzazione_` | `sport_ds34` | 1.041 | non dichiarato | `LONG_X_4326`, `LAT_Y_4326` | CC BY |
| Impianti sportivi (poligoni di campi) | `ds1640_infogeo_impianti_sportivi_localizzazione` | `sport_ds1640` | 502 poligoni; date dei rilievi da 23/11/2000 a 25/3/2024 (campo `data_ini`) | 2000-2024 | solo GeoJSON (il CSV non ha coordinate) | CC BY |
| Uffici postali | `ds555_uffici_postali_milano` | `poste` | 85 (tutti `Ente`="Ufficio PT") | non dichiarato | `LONG_X_4326`, `LAT_Y_4326` | CC BY |
| Esercizi di vicinato | `ds49-economia-esercizi-vicinato-sede-fissa` | `vicinato` | 28.131 righe = 13.370 punti distinti | caricato 31/8/2026 | `LONG_X_4326`, `LAT_Y_4326` | CC BY |

Dimensioni: tutta la cartella `raw\comune_milano` pesa circa 243 MB (il grosso sono i 164 MB del CSV della popolazione estratto dallo zip da 13 MB e i 23 MB dei civici estratti).

##### Problemi trovati ("trappole dei dati")

- **Farmacie** (`farmacie`): pulite. 422 righe, 0 coordinate mancanti, 0 fuori confine, 0 dentro un parco, 0 duplicati, NIL dichiarato sempre uguale a quello del poligono. Confronto con OSM: 413 delle 422 hanno una farmacia OSM entro 100 m; OSM dentro Milano ne ha 451 (`collegamenti_risultati.json`, campi `farmacie_Comune_con_OSM_entro_100m`, `OSM_farmacie_dentro`).
- **Medici di base** (`mmg`): il file è una riga per medico, non per ambulatorio. 1.189 righe ma solo 428 punti distinti (`duplicati_stesso_punto` = 761): contare i medici come "servizi" gonfierebbe le zone con ambulatori di gruppo. 154 medici hanno `attivo`=0 (1.035 attivi; 414 punti distinti attivi). 38 hanno `ambulatorioPrincipale`=0. 6 medici sono **fuori dal confine del Comune** (per esempio Via Stradivari, Via Ampere, Via Beatrice d'Este: indirizzi che sono a Milano, quindi coordinate sbagliate, spostate fino a lat 45,63) e hanno `ID_NIL` mancante; 5 cadono dentro un poligono di parco. **Il file contiene nomi, cognomi e data di nascita dei medici (`dataNascita`) e la licenza è CC BY-NC: non ripubblicare il file grezzo.** Il nome del file cambia ogni giorno (`20261029_mmg_final.csv`).
- **Asili nido** (`nidi`): i dati arrivano solo fino all'a.s. 2018/19 (600 righe quell'anno, 377 nomi distinti, 295 punti distinti). **99 righe su 600 (anno 2018/19) non hanno coordinate né NIL né CAP** (in tutto 295 righe su 1.790). Una riga è una sezione/fascia d'età, non un edificio: bisogna ridurre a un punto per edificio. Non esiste un dataset più recente sul portale (cercato: "nidi", "servizi prima infanzia 0-3"; c'è anche `ds709` "servizi integrativi all'infanzia", non scaricato). Per i nidi serve OSM (`amenity=kindergarten` / `childcare`) o accettare il limite. 3 punti dentro un poligono di parco.
- **Scuole infanzia/primarie/secondarie I grado**: i file storici (`ds671`, `ds40`, `ds46`) hanno una riga per scuola per anno scolastico (12 anni, 2014/15-2025/26): **va filtrato l'ultimo anno** (`ANNOSCOL`=2025/2026) o si contano le scuole 12 volte. Ultimo anno: infanzia 294 (166 comunali, 27 statali, 40 enti privati laici, 36 enti religiosi, 17 privati, 6 privati convenzionati, 2 privati accreditati), primarie 216 (215 punti distinti), secondarie I grado 147 (146 punti distinti). Il campo `NIL` dichiarato differisce dal poligono in 1 scuola infanzia, 2 secondarie I grado (ultimo anno). Dentro un parco: 4 infanzia, 0 secondarie (normale: scuole in giardino). Le **superiori** (`scuole_sec2`) hanno 174 righe ma 109 punti (65 righe sono "stesso punto", più istituti nello stesso edificio) e nessun anno scolastico dichiarato.
- **Biblioteche** (`biblioteche_sistema`): solo 26 sedi del Sistema Bibliotecario Milanese. OSM ha 57 punti `amenity=library` dentro Milano (`collegamenti_risultati.json`, `OSM_library_dentro`), ma comprendono biblioteche di scuole/università/condominio: non sono confrontabili uno a uno. Una cade dentro un parco.
- **Mercati**: coperti 26 righe di cui 5 inattivi (filtrare `attivo`='SI'); settimanali 85, tutti attivi ma ognuno funziona solo certi giorni (campi `LUNEDI`...`DOMENICA`, `giorno`, `orari`): un mercato aperto un giorno a settimana non è un servizio quotidiano; agricoltori 9. Dati di maggio 2024 per i primi due. OSM: 35 `amenity=marketplace` dentro Milano.
- **Parchi** (`parchi`): 1.065 poligoni, area totale 7,74 milioni di m² (campo `AREA_MQ`, somma). Mediana 78 m², 737 poligoni sotto 500 m² (aiuole), 18 sopra 10 ha. Il più grande: Parco delle Cave (59,4 ha); lo stesso nome compare su più poligoni (non è un duplicato, il parco è diviso in pezzi: 991 righe hanno nome+codice ripetuto). 22 righe identiche e 22 punti duplicati. Il CSV ha solo centroidi: inutile per l'accessibilità a piedi, serve il GeoJSON. Non è dichiarato l'anno dei dati. Confronto: OSM ha 817 `leisure=park` + 879 `leisure=garden` dentro Milano.
- **Impianti sportivi**: due set diversi. `ds34` (1.041 punti, tipo nel campo `info`: 232 centri sportivi, 159 calcio a 11, 113 pallacanestro, 93 ginnastica, 85 fitness, 77 tennis, 34 nuoto, 13 piscina...) e `ds1640` (502 poligoni di singoli campi pubblici, con 34 piste ciclabili, 26 piste di schettinaggio ecc., rilevati dal 2000 al 2024): **in `ds1640` ci sono piste ciclabili che non sono impianti sportivi nel senso del servizio**; filtrare per `descrizione_codice`. Nessun centroide fuori confine in nessuno dei due. Anno non dichiarato per `ds34`. Il problema "sport" dipende da cosa si intende: per la fase 2 conviene `ds34` come "luogo dove fare sport" e `ds1640` come "campo libero nel quartiere".
- **Poste** (`poste`): pulite (85 righe, 0 problemi). Il Comune ha quindi gli uffici postali, **non serve OSM**. Controllo incrociato: 74 delle 85 hanno un punto OSM `amenity=post_office` entro 150 m; OSM ha 111 `post_office` dentro Milano, di cui 95 con operatore "Poste Italiane", 8 senza operatore e 8 di corrieri (DHL, GLS, Nexive, Mail Boxes Etc., Posta Express). Quindi OSM sembra contare anche sportelli/punti non ufficiali o uffici più recenti; i due elenchi non coincidono perfettamente.
- **Esercizi di vicinato** (`vicinato`): 28.131 righe, 245 senza coordinate, 13.370 punti distinti (`duplicati_stesso_punto`=14.516: più negozi allo stesso civico), 8 dentro un parco. Il campo `settore_merceologico` è sporco: scritto in maiuscolo/minuscolo diverso e concatenato ("Non AlimentareAlimentare", "tabella speciale monopolio" = tabaccai, "tabella speciale farmacie", "tabella speciale carburanti"): per dire "negozio alimentare" serve normalizzare. Alimentari puri (`Alimentare`+`alimentare`): 5.005 righe; circa 10.557+8.130 sono non alimentari. Il campo `tipologia` è 'vicinato' in 28.039 righe, 'ND' in 91, 'media SV' in 1. `Area di Competenza` è sempre "VENDITA - In sede fissa". Il file è una fotografia dell'autorizzazione commerciale: negozi chiusi di fatto possono esserci ancora.
- **Tutti i set con ID_NIL**: il NIL dichiarato coincide con il NIL calcolato dal poligono tranne i pochi casi indicati sopra (`nil_dichiarato_diverso_dal_poligono` in `controlli_risultati.json`).

#### 2. Civici con coordinate (`ds634-numeri-civici-coordinate`, cartella `civici`)

- File originale: `ds634_civici_coordinategeografiche_20261001_final_csv.zip` (4,6 MB), estratto in `civici\estratto\` (23 MB, 65.160 righe, 41 colonne, aggiornato al 1/10/2026). Licenza CC BY.
- `STATOCIVICO`: Applicato 57.405; Iter in corso 7.649; In attesa Fine Lavori 106. `RESIDENZIALE`: 1 = 47.238, 0 = 17.917, vuoto 5. Livello stradale quasi sempre (65.123 su 65.160).
- **Applicati**: 57.405 punti, tutti distinti; **numeri civici distinti** (chiave `CODICE_VIA`+`NUMERO`+`LETTERA`): 51.917, ed è questo il numero "circa 51.000". Applicati residenziali: 46.896. Mi sembra la scelta migliore tenere gli "Applicati" e decidere in fase 2 se partire da 51.917 (numeri) o da 57.405 (punti con i "barrati").
- Coordinate in gradi: **`LONG_WGS84` / `LAT_WGS84`** (con il punto). **Trappola**: le colonne `WGS84_X`/`WGS84_Y` si chiamano "WGS84" ma contengono metri UTM 32N (es. `514817,0392`), con la virgola decimale; le colonne `GAUSSB_X/Y` sono Gauss-Boaga, `WEBMERC_X/Y` Web Mercator.
- Controlli: 0 coordinate mancanti, 1 punto fuori dal confine del Comune, 2 senza `ID_NIL` (anche fuori da ogni poligono NIL), nessun `IDMASTER` duplicato, `ID_NIL` dichiarato = NIL del poligono per tutti. Applicati per NIL: da 12 a 2.902.
- Nel file **non c'è il CAP**: per i redditi serve stimarlo (vedi sotto).

#### 3. Redditi (Irpef sub-comunale) e come collegarli ai NIL

- Dataset: `ds1590` (anno di imposta 2019), `ds1830` (2020), `ds2275` (2021), `ds2734` (2022), `ds2946` (2023), `ds3009` (2024, caricato 26/8/2026): cartelle `redditi_<anno>_ai<anno-imposta>`. CSV con 4 colonne: `Anno di imposta`, `CAP`, `Redditi e variabili Irpef`, `Importi`. Licenza CC BY. **Sono 6 anni (2019-2024); più indietro non c'è un dataset sub-comunale** (quelli del 2000-2018 sono solo a livello comunale: `ds941`...`ds1267`, non scaricati).
- **Zone: 38 CAP**, da 20121 a 20162 (stessi 38 in tutti gli anni). Nessun dato per NIL, né per sezione di censimento.
- 43 variabili nei primi cinque anni, 45 nel 2024: per ogni tipo di reddito un numero di contribuenti (`- Frequenza`) e un importo (`- Ammontare in euro`), più le classi di reddito complessivo (fino a 10.000, 10-15, 15-26, 26-55, 55-75, 75-120, oltre 120 mila euro). Il "reddito medio" non è dato: va calcolato come `Reddito complessivo - Ammontare in euro` / `Reddito complessivo - Frequenza` (o diviso per `Numero contribuenti`). Il "Numero contribuenti" è di chi presenta dichiarazione, non di tutti i residenti. Esempio 2024 (`ds3009`): `Numero contribuenti` da 13.625 (CAP 20136) a 46.726 (CAP 20146).
- **Collegamento CAP → NIL.** Non ho trovato i confini dei CAP né sul portale (cercato "CAP") né in OSM (nessuna relazione `boundary=postal_code` per Milano: 0 risultati). Ho quindi usato i 27.721 punti (vicinato, farmacie, poste, medici) che hanno **sia CAP sia NIL** (`collegamento_CAP_NIL_tabella_punti.csv`) e i civici (`collegamento_CAP_NIL_tabella_civici_stimati.csv`, CAP del punto noto più vicino).
  - La tabella CAP × NIL ha 186 celle non vuote (punti) o 233 (civici stimati): un NIL tocca più CAP e viceversa.
  - Solo 1 CAP su 38 ha un NIL dominante ≥ 90%; in media il NIL più frequente di un CAP ne copre il 56,6% dei punti. Nell'altro verso (NIL → CAP) 44 NIL su 87 hanno un CAP che ne copre ≥ 90%, ma 44 NIL toccano due o più CAP con almeno il 10% ciascuno; in media il CAP dominante di un NIL copre l'81,9% dei punti (81,3% con i civici).
  - Test sul CAP stimato col punto più vicino (12.839 punti distinti, ciascuno escluso da sé stesso): lo stesso CAP nel 96,6% dei casi. Dei 57.405 civici applicati, 47.901 hanno un punto con CAP noto entro 100 m (mediana 37 m, 95° percentile 192 m).
  - **Conclusione:** il confronto con i redditi si fa **a livello di CAP (38 zone)**: punteggio dei servizi medio per CAP, calcolato sui civici assegnati a ciascun CAP (pesati con i residenti stimati), contro reddito per contribuente di quel CAP. Distribuire i redditi sui NIL richiederebbe ipotesi (peso per superficie o per residenti) e darebbe false precisioni; se serve, farlo come analisi secondaria e dichiararlo.
- Il CAP stimato per i civici resta una stima (96,6%): i confini veri non sono scaricabili (Poste Italiane non li pubblica liberamente). Non fatto: ricerca di confini CAP su altre fonti (ISTAT, Regione Lombardia), da valutare se serve più precisione.

#### 4. Popolazione per quartiere (NIL)

- `ds27-popolazione-residenti-cittadinanza-quartiere-serie-storica` (cartella `pop_cittadinanza_quartiere`): `ds27_pop_sto_quartiere.zip` (13 MB), estratto `estratto\ds27_pop_sto_quartiere.csv` (164 MB, 3.131.527 righe). Campi: `Anno` (1999-2025), `IdNil`, `Nil`, `Eta` (0-99 e "100 e più"), `Genere`, `Cittadinanza`, `Residenti`. Licenza CC BY.
  - **Ultimo anno: 2025, 1.399.079 residenti** (somma di `Residenti`, `Anno`=2025), in **87 NIL su 88**: manca il NIL 8 `PARCO SEMPIONE` (nessun residente). Per i NIL più piccoli i numeri sono bassi (min 38 residenti nel 2025, max 61.964).
  - Si può ricavare per ogni NIL: totale, età (anno per anno), genere, cittadinanza. Non c'è il reddito.
- `ds205-sociale-caratteristiche-demografiche-territoriali-quartiere` (cartella `pop_caratteristiche_quartiere`): 2011-2024, 1.243 righe, totale 2024 = 1.407.044 (campo `Totale`), con `Minori`, `Stranieri`, `65 e +`, `80 e +`, numero di scuole, `Area (metri quadrati)`. Ha 89 righe per anno: l'ultima è "N.D." (senza NIL, `Totale` vuoto). Utile per la superficie.
- Differenza di data: ds27 arriva al 2025, ds205 al 2024, i redditi sono del 2024 (anno di imposta) → per un confronto coerente usare 2024 per tutti.

#### 5. Confini

- NIL vigenti (`ds964-nil-vigenti-pgt-2030`, cartella `nil_vigenti`): `ds964_nil_wm.geojson` (88 poligoni, 1 MB; nonostante "wm" nel nome le coordinate sono in gradi EPSG:4326) e `ds964_nil_wm_4326.csv` (centroidi). Valido dal 5/2/2020, fonte PGT Milano 2030. Licenza CC BY. Campi `ID_NIL`, `NIL`. Esiste anche la versione "OBSOLETI" (`ds61`, non scaricata).
- Confine del Comune (`ds2841-confini-amministrativi-del-comune-di-milano`, cartella `confine_comune`): `confine_comune_milano_layer_0_confine_comune_milano.geojson`, 1 poligono, 1,9 MB, EPSG:4326, 19.553 vertici; la superficie calcolata dal poligono è circa 180,6 km². Attenzione: i campi `Shape_Area` (369.827.250) e `Shape_Length` (155.386) valgono circa il doppio e non sono in m² reali: non usarli. Licenza CC BY.

#### 6. Rete pedonale (OpenStreetMap)

- **Già scaricata dalla filiera 7** (`..\bici-auto-mezzi\`): non copiata, solo referenziata.
  - `C:\Users\davide\Desktop\ClaudeTower\milano-in-dati\bici-auto-mezzi\raw\osm_milano\milano_buffer.osm.gz` (17,9 MB, formato XML OSM compresso). Riquadro: lat 45,350-45,572, lon 8,99-9,33 (dichiarato nell'intestazione `<bounds>`; i nodi vanno da 45,35 a 45,572 e da 8,99 a 9,33): copre tutto il Comune con circa 2,5-3 km di margine. Contiene 779.196 nodi, 181.476 strade (way con tag `highway`), 4.469 relazioni (restrizioni/rotte bici). Estratto da `lombardia-latest.osm.pbf` (356 MB, Geofabrik, nella stessa filiera in `raw\osm_lombardia\`, scaricato 29/10/2026 17:21).
  - Percorribili a piedi: `footway` 73.376 tag, `residential` 24.802, `service` 33.415, `pedestrian` 2.866, `path` 2.927, `steps` 3.309, `crossing` (nodi) 40.175 ecc. (conteggio dei tag `highway=*` nel file, nodi e strade insieme). Le strade sono troncate al riquadro.
  - Sistema di riferimento: lat/lon OSM. Licenza ODbL: attribuzione obbligatoria, ridistribuzione con la stessa licenza. Se serve ritagliare di nuovo: comando in `..\bici-auto-mezzi\STATO.md`.
- **Limite:** il ritaglio tiene solo le strade e i nodi relativi (nessun punto d'interesse), per questo i servizi del bordo vanno presi dal file seguente.

#### 7. Effetto bordo e punti di interesse OSM

- File: `raw\osm_poi\overpass_poi_milano.json` (2,9 MB) = una sola interrogazione Overpass (`scripts\overpass_poi.py`), data base OSM 29/10/2026 16:36 UTC, rettangolo lat 45,36-45,56 / lon 9,00-9,32, 11.518 elementi. Tabella estratta e classificata: `raw\osm_poi\osm_poi_milano_estratto.csv` (campo `fascia`: dentro il Comune / fuori entro 1.500 m / fuori oltre).
- **Comuni confinanti** (confini OSM `admin_level=8`, `raw\osm_poi\overpass_comuni_admin8.json`, 3 MB; confinante = un vertice a meno di 150 m dal confine): Rozzano, Opera, Assago, San Donato Milanese, Buccinasco, Cesano Boscone, Peschiera Borromeo, Settimo Milanese, Segrate, Pero, Sesto San Giovanni, Novate Milanese, Baranzate, Trezzano sul Naviglio, Cusago, Corsico, Rho, Vimodrone, Cologno Monzese, Cormano, Bresso, Arese, Bollate, Cornaredo (24). Vicini ma non confinanti (entro 3 km): San Giuliano Milanese (616 m), Cinisello Balsamo, Pieve Emanuele, Cusano Milanino, Locate di Triulzi, Bareggio, Pioltello, Gaggiano, Paderno Dugnano, Cernusco sul Naviglio, Cisliano, Pregnana Milanese, Basiglio, Zibido San Giacomo, Senago. (La verifica è fatta sui vertici, non è una verifica ufficiale dei confini.)
- I servizi di questi comuni **non sono nei dati del Comune**. Chi abita al margine rischia un punteggio più basso solo perché il servizio più vicino è oltre il confine. OSM può riempire il bordo: nel rettangolo, fra 0 e 1.500 m fuori dal confine ci sono (campo `fascia`=`fuori_entro_1500m`, `collegamenti_risultati.json`, `OSM_poi_per_tag_e_fascia`): `amenity=pharmacy` 90, `amenity=school` 125, `amenity=kindergarten` 72, `amenity=library` 27, `amenity=doctors` 37, `amenity=post_office` 27, `amenity=marketplace` 10, `shop=supermarket` 77, `shop=bakery`/`butcher`/`greengrocer`/`convenience` (non riportati qui), `leisure=park` 337, `leisure=garden` 550, `leisure=sports_centre` 99, `leisure=swimming_pool` 107.
- **Non riempito ancora**, come da mandato: solo valutazione. Limiti di OSM: le scuole con tag `amenity=school` includono scuole di ogni grado senza una distinzione unica; i medici di base di fuori non sono su OSM in modo completo (`doctors` 37 entro 1,5 km); `amenity=post_office` mescola uffici e punti Poste/corrieri. Per scuole e farmacie OSM è il candidato migliore per il bordo (le farmacie OSM coincidono con quelle del Comune per il 98%, 413/422).
- Licenza OSM: ODbL (attribuzione, stessa licenza se si ripubblica).

#### 8. Licenze e ripubblicazione

- Dataset del Comune: **CC BY** (si può ripubblicare citando la fonte), eccetto: **farmacie CC0** (libere) e **medici di base CC BY-NC (uso non commerciale: non ripubblicare il grezzo, e comunque contiene nomi e date di nascita dei medici)**; `ds1863` e `ds1582` (scuole 2020/21) hanno licenza "altro (attribuzione)".
- Il file `ds27` e il CSV dei civici sono grandi (164 MB e 23 MB estratti): se si ripubblica qualcosa, solo risultati aggregati, non il grezzo.
- OSM: ODbL.

#### 9. Cosa non ho fatto / aperto

- Non ho scaricato i file JSON/RDF dei dataset (solo CSV e GeoJSON, che bastano).
- Non ho cercato i confini dei CAP su fonti diverse da Comune e OSM.
- Nessun calcolo di tempi di cammino (fase 2).
- Non ho scaricato `ds709` (servizi integrativi all'infanzia), né le liste di scuole paritarie più recenti (esistono per anno scolastico: `ds2286` infanzia paritarie 2021/22, `ds1582` 2020/21 qui scaricata). Le paritarie recenti sono già nei file scuole 2025/26 (`PARITARIA`, `TIPO` privati/enti religiosi).
- Il campo `Shape_Area` del confine comunale è circa il doppio della superficie vera (180,6 km² calcolati dal poligono): la superficie va calcolata dal poligono.
- I file `scuole_paritarie_2020`, `biblioteche_loc_2007` e `biblioteche_rionali_2013` sono solo di confronto: non ho fatto i controlli geografici su di loro (colonne e righe sì).

### Fase 2 e 3 — calcolo e pagina (2026-10-29)

- **Metodo**:
  - Rete pedonale OSM del filone 7: 647 mila nodi, 12.299 km.
  - 57.405 civici in vigore, agganciati alla rete (mediana 14,5 m).
  - 4,5 km/h, quindi 15 minuti = 1.125 m lungo le strade.
  - Un calcolo di distanza da tutti i servizi insieme per ogni tipo.
  - **10 tipi** di servizio: i tre mercati contano come uno; l'"11" del mandato era un errore del coordinatore.
  - Parchi da 5.000 m² in su, con l'ingresso dal bordo.
  - Abitanti 2025 di ogni NIL distribuiti in parti uguali sui suoi civici residenziali.
  - Dettagli in `citta-15-minuti/NOTE.md`, "FASE 2".
- **Risultati**:
  - Punteggio medio della città 8,97 su 10; il 35,2% dei residenti ha tutti e 10 i tipi entro 15 minuti.
  - La biblioteca è il servizio che manca: la raggiunge il 46,5% dei residenti (59% con le biblioteche OSM).
  - Redditi per CAP (38 zone, `cap_redditi_servizi.csv`): Spearman 0,54 (IC 95% 0,28-0,71) senza Cascina Merlata; il terzo più povero ha un punteggio di 8,7, il più ricco di 9,4; per la sola biblioteca la correlazione è 0,00.
  - Meglio serviti: Tibaldi, Porta Vigentina, Guastalla, Ortomercato, XXII Marzo. Peggio serviti: Chiaravalle, Muggiano, Parco Forlanini, Figino, Monluè.
- **Controlli**:
  - La distanza lungo la rete non è mai minore di quella in linea d'aria.
  - 20 civici ricalcolati uno per uno: differenza massima 0,005 minuti.
  - L'effetto bordo (servizi OSM entro 1,5 km fuori dal Comune) è trascurabile, salvo nei NIL minuscoli di confine.
- **Trappola Cascina Merlata** (controllo del coordinatore): nel registro dei civici del Comune ha solo 13 indirizzi, tutti in via Cristina Belgioioso. È il quartiere nuovo dell'ex villaggio Expo, e anche i servizi recenti mancano nei dati. Il suo punteggio di 0,33 non vale: è in grigio, fuori dalle classifiche e dal confronto con i redditi.
- **Classifiche**: entrano solo i NIL con almeno 30 civici e 1.000 abitanti (75 su 88).
- **Dati personali**: il file dei medici di base (nomi e date di nascita, licenza CC BY-NC) non è pubblicato; nel sito ci sono solo i tempi a piedi aggregati.
- Pagina `docs/citta-15-minuti/`, approvata da Davide dopo la "sorpresa".

## 10. Violenza politica a Milano dal 1900

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `violenza-politica/`._

- 2026-10-29 — Filone chiesto da Davide: dove e quando sono avvenuti gli attentati a Milano dal 1900, su una mappa collegata a Wikipedia. Si contano bombe, stragi e omicidi politici (scelta di Davide); non si contano ordigni inesplosi, incendi e gambizzazioni senza morti. Nome della cartella e della sezione: `violenza-politica` (scelta di Davide). Fonti: Wikidata e Wikipedia. La Global Terrorism Database (1970-2020) chiede la registrazione: non la usiamo, salvo che Davide si registri lui.
- 2026-10-29 notte — **Fase 1 e 2** (`violenza-politica/NOTE.md`, `pulito/eventi.csv`):
  - **65 eventi, 1919-2003, 167 morti indicati.** Per decennio: 1910 5, 1920 10, 1940 5, 1960 4, 1970 22, 1980 17, 1990 1, 2000 1; negli anni '50 nessuno.
  - **Fonti**: le tabelle di Wikipedia "Persone uccise negli anni di piombo", la "Cronologia dello squadrismo", le voci dedicate e Wikidata (39 eventi con QID). 21 eventi senza coordinate compaiono solo nell'elenco.
  - **Revisione del coordinatore** (`pulito/correzioni_coordinatore.csv`, applicata da `scripts/09_pubblica.py`):
    - Arena 1943, piazzale Loreto e viale Tibaldi 1944 passano dal tipo "strage/bomba" al nuovo tipo "rappresaglia o esecuzione";
    - l'agguato di via Schievano 1980 diventa "omicidio politico".
  - **Da decidere (Davide), prima di pubblicare**:
    1. L'agente ha aggiunto il tipo "scontro o custodia" (16 morti: polizia ai comizi del 1919-20, Pinelli, Saltarelli, Franceschi, Zibecchi, Luca Rossi, brigatisti uccisi negli scontri a fuoco…), che è fuori dalla definizione scelta (bombe, stragi, omicidi politici).
    2. Le rapine di autofinanziamento con morti (Saporito 1977, Carloni 1982) sono contate come omicidio politico.
    3. I casi "DA DECIDERE" in `esclusi.csv`: Ambrosoli, Abbruciati, Saronio, Lahderi, Pasqua Rossa.
  - **Mancano**: la bomba al Cova (1920) e l'attentato alla caserma Santa Barbara (2009), senza voce su it.wikipedia; il 1946-68 e il dopo 1993 sono poco coperti.
  - **Pagina** `docs/violenza-politica/` pronta e provata, **non pubblicata** in attesa dell'ok di Davide.
- 2026-10-30 notte — **Decisioni di Davide (con i clic)**:
  1. I morti negli scontri o in custodia contano a tutti gli effetti.
  2. Le rapine di autofinanziamento (Saporito 1977, Carloni 1982) restano, con la nota "rapina di autofinanziamento" (`pulito/correzioni_coordinatore.csv`, colonna `nota`).
  3. I 5 casi incerti (Saronio, Ambrosoli, Abbruciati, Lahderi, Pasqua Rossa) entrano, ciascuno con una nota "caso incerto"; li aggiunge l'agente che riempie i buchi.
  - **Pagina pubblicata** con 65 eventi; i casi incerti e le aggiunte arriveranno con il prossimo aggiornamento.
- 2026-10-30 notte — **Fase 3, buchi riempiti** (`violenza-politica/pulito/aggiunte_fase3.md`):
  - Ora 84 eventi (+19) e 202 morti indicati.
  - Aggiunti: bombe al Cova e a un albergo (1920); viale Abruzzi 1944; Volante Rossa 1947-49; Pasqua Rossa 1946; Ambrosoli, Lahderi e Abbruciati (con nota "caso incerto"); attentati con feriti 2009 (caserma Santa Barbara), 2017 e 2019 (Stazione Centrale).
  - Saronio resta escluso: la voce non dice che morì a Milano.
  - Per il 1900-1918 e il 1950-1968 non si è trovato nulla.
  - Conflitti tra le fonti risolti: Mazzanti a Milano (via Orseolo); Tavecchio, scontri l'11 marzo e morte il 14; Fiera 1928, 20 morti.
  - Pagina ripubblicata.

## 11. Film e libri ambientati a Milano

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `film-e-libri/` (nome proposto dal coordinatore, da confermare con Davide)._

- 2026-10-29 notte — Avviata la fase 1 su richiesta di Davide ("continua, più agenti in parallelo"). Le fonti sono quelle dell'idea in attesa, nelle Decisioni generali.

### Fase 1 — scarico (2026-10-30)

**NOTE - Film e libri ambientati a Milano (fase 1: scarico e controllo)**

Data di scarico: 29/10/2026. Nessuna pagina del sito, nessun git. Tutti i numeri vengono da `pulito/_statistiche.json` (costruito da `scripts/costruisci_pulito.py`).

#### Risposta breve

- Film: **435** (in `pulito/film.csv`). Serie TV: 17 (`serie_tv.csv`). Libri: **280** righe (`libri.csv`: 125 da Wikidata/Wikipedia, 123 nuovi da Open Library, 32 nuovi da Library of Congress; 44 record LoC e 1 di Open Library erano gia fra i primi). Altro (videogiochi, quadri, opere liriche): 12 (`altro.csv`).
- Con un luogo **piu preciso di "Milano"**: solo **10 film** e **4 libri** (campo `ha_luogo_preciso`, tutti con coordinate). Per una mappa sono pochissimi. Gli altri dicono solo "Milano".
- Il collo di bottiglia e Wikidata: P840 (ambientazione) quasi sempre punta alla citta intera; solo 7 opere hanno un luogo interno (Teatro alla Scala, viale Bligny, Palazzo del Monte di Pietà, Mediolanum). P915 (luogo delle riprese) e piu preciso: 10 film su 83 hanno una piazza, una strada, una stazione o un teatro.
- Per mappare serve una fase 2 diversa (per esempio leggere le trame su Wikipedia o schedare a mano i casi famosi). Questo non e stato fatto.

#### Film per decennio (campo `decennio`, da `anno` = prima data di P577; 12 film senza data)

1930: 5 - 1940: 14 - 1950: 38 - 1960: 43 - **1970: 95** - 1980: 64 - 1990: 37 - 2000: 43 - 2010: 54 - 2020: 30.
Il picco degli anni Settanta (poliziotteschi, commedie) e netto. Dopo il 1990 c'e un calo e poi una ripresa.

#### Libri per decennio (242 con data su 280)

Prima del 1900: 25 - 1920: 1 - 1930: 2 - 1940: 8 - 1950: 4 - 1960: 12 - 1970: 17 - 1980: 17 - 1990: 34 - **2000: 58 - 2010: 55** - 2020: 9 (il decennio 2020 e ancora in corso).
Attenzione: i conteggi dei libri dipendono molto da chi ha schedato (Wikidata + Open Library), non misurano quanto si e scritto davvero.

#### Fonti, una per una

##### 1. Wikidata (SPARQL, CC0) - `raw/wikidata\`
- Endpoint `https://query.wikidata.org/sparql`. Filtro: opere con P840 o P915 che puntano a Milano (Q490) o a un luogo con P131* = Milano (6.486 luoghi in Milano su Wikidata).
- File: `luoghi_p840.json` (1,8 MB), `luoghi_p915.json` (0,4 MB), `opere_*.json` (titoli it/en, classi, anno, regia/autore, genere, IMDb id, link Wikipedia), `etichette_extra.json`. Totale 3,4 MB.
- Risultato: **393 opere** (339 con P840, 83 con P915; sovrapposte 29). Classi (campo `tipo_wikidata`): 291 film, 70 "opera letteraria", 11 serie TV, 2 miniserie, resto vario.
- Completezza: Wikidata e **incompleto**. Dei 484 articoli nelle categorie di it.wikipedia, 196 non hanno P840/P915 dentro Milano (116 non hanno P840 per niente, 80 lo hanno ma su altro luogo, es. Q220 Roma). Quindi Wikidata da solo perde circa un terzo.
- Licenza: CC0, si puo ripubblicare.
- Trappole: (a) un film con piu P31/piu luoghi genera piu righe: il file `luoghi_p840.json` ha 2.025 righe per 339 opere; si deduplica per QID (fatto). (b) Alcuni libri e film non hanno etichetta italiana/inglese (restano col QID come titolo). (c) Le serie TV non hanno P577 (hanno P580, data d'inizio, non scaricata): solo 3 su 17 hanno l'anno. (d) Il numero di "libri" in Wikidata e basso: i romanzi usano quasi sempre "opera letteraria" (Q7725634) e P840 e raro.
- Non usato: query con P31/P279* sulle classi (andava in timeout; basta P31 diretto, controllato).

##### 2. Categorie di it.wikipedia (API MediaWiki) - `raw/wikipedia\`
- `categorie.json`: "Film ambientati a Milano" 351 pagine, "Film girati a Milano" 156, "Romanzi ambientati a Milano" 71, "Opere ambientate a Milano" (1 pagina + 4 sottocategorie), "Serie televisive ambientate a Milano" 2, "Opere teatrali ambientate a Milano" 9. La categoria "Opere letterarie ambientate a Milano" **non esiste** (0 pagine). Profondita 2: le sottocategorie non hanno altre sottocategorie. Totale 484 pagine uniche; una ("Rider (film)") senza QID.
- `pagine_qid.json` (QID Wikidata di ogni pagina), `mancanti_wikidata.json` (dati base delle 196 pagine fuori da Wikidata-Milano).
- Resa: film solo da categoria 142; da Wikidata e categoria insieme 256; solo Wikidata 37. Libri: solo categoria 46, entrambe 29, solo Wikidata 50.
- Licenza: i nomi delle pagine/categorie sono fatti; il testo di Wikipedia e CC BY-SA. Non abbiamo scaricato testi, solo titoli e appartenenza alle categorie.
- Trappola: "Film girati a Milano" contiene film girati a Milano ma ambientati altrove; la categoria dice dove si gira, non dove si svolge la storia. Nel CSV l'origine e nel campo `fonte_itwiki_categoria`.

##### 3. Open Library - `raw/openlibrary\` (2,1 MB)
- API `https://openlibrary.org/search.json`, 1 richiesta ogni 2 s. Query: `place:"Milan (Italy)"` 2.738 libri; `subject:"Milan (Italy)"` 1.578; `place:"Milano"` 46; `subject:"Milano"` 710; `subject:"Milan (Italy) -- Fiction"` solo **2**; `place:"Milan (Italy)" AND subject:fiction` 82. Unione: **4.562 libri** (tutti in `pulito/openlibrary_tutti.csv`).
- Il soggetto esatto "Milan (Italy) -- Fiction" quasi non esiste su Open Library: i romanzi sono etichettati con soggetti separati (Fiction + luogo Milan). Ho preso come narrativa i libri con un soggetto che contiene fiction / narrativa / novel / romanz / racconti / detective / mystery: **124**, di cui 1 gia in Wikidata/Wikipedia (agganciati per titolo e cognome). 123 sono nuovi in `libri.csv`.
- Trappole: il luogo "Milan (Italy)" vale anche per "Ducato di Milano" (romanzi storici su Leonardo, Sforza), per libri di storia o per opere solo citate; non e sinonimo di "ambientato a Milano". Il controllo manuale e necessario. Molti libri sono inglesi di serie rosa (Harlequin) con un tocco milanese.
- Licenza: Open Library dichiara i metadati liberi (pubblico dominio/CC0); da verificare nei termini prima di ripubblicare.

##### 4. Library of Congress - `raw/loc\` (0,2 MB)
- L'API `loc.gov/books` risponde 403 (Cloudflare "Just a moment"): **non aggirato**, come da regole. Usato invece il catalogo pubblico SRU `http://lx2.loc.gov:210/lcdb` (nessun login).
- `bath.subject="Milan (Italy)--Fiction"`: **76 record** (tutti scaricati, 2 file XML; 44 agganciati a libri gia presenti, 32 nuovi). `bath.subject="Milan (Italy)"` in generale: 4.830 (solo conteggio in `tutti_milan_italy_conteggio.xml`).
- Licenza: record bibliografici della LoC (opera del governo USA, pubblico dominio); la condizione esatta non e stata verificata.

##### 5. SBN OPAC - `raw/sbn\` (0,2 MB, solo conteggi)
- Stessa interfaccia JSON della fase scala (`opac.sbn.it/opacmobilegw/search.json`, parametro `subject`), cliente educato (3 s). Conteggi in `raw/sbn/_conteggi.json`: "Milano - Narrativa" 6, "Milano - Romanzi" 3, "Milano - Racconti" 6, "Milano - Letteratura" 63, "Milano - Film" 29, "Milano - Cinema" 31, "Milano" 30.987.
- Fattibile ma inutile per i romanzi: i soggetti italiani per la narrativa non portano il luogo, quindi quasi nessun romanzo e indicizzato come "Milano - Narrativa". Il parametro `subject` sembra anche abbastanza largo (alcuni risultati non c'entrano: "romanzi cavallereschi"). Non entra in `libri.csv` (colonna `fonte_sbn` vuota). Utile al massimo per saggi su Milano e cinema.
- Licenza: non verificata (fase 1 solo conteggi).

##### 6. Lombardia Film Commission e Comune di Milano
- Il sito vero e `https://www.filmcomlombardia.it` (i domini lombardiafilmcommission.* non esistono). Ha un database di location (oltre 25.000 foto secondo la stampa) e un elenco "produzioni", ma il suo `robots.txt` dice `User-agent: * Disallow: /`: **tutto vietato ai programmi**. Non scaricato (ho letto solo la home e il robots.txt). Nessun download aperto. Possibile contatto: filmcom@filmcomlombardia.it (da fare solo se Davide vuole).
- Portale open data del Comune (CKAN): ricerche "riprese", "set cinematografici", "film", "fiction", "audiovisivo" = 0 risultati; "cinema" 3 risultati non pertinenti (ingressi spettacoli, musei). Esistono solo "Occupazioni suolo temporanee straordinarie 2020 e 2021", che non riguardano le riprese. Elenco delle ricerche in `raw/altro/ckan_milano_ricerche.json`.
- dati.lombardia.it (Socrata): "film", "riprese", "audiovisivo" 0; "cinema" solo cinema di altri comuni.
- IMDb: non usato.

#### Cosa manca

- Luoghi precisi: vedi sopra, 14 opere su circa 730.
- Serie TV: anno quasi sempre mancante; 17 sono poche (Wikipedia ne ha 2 in categoria).
- Non cercati: categorie di en.wikipedia (es. "Films set in Milan"), altri sottoinsiemi di Wikidata (P840 su luoghi senza P131 verso Milano, per esempio un quartiere o una via senza "comune"), cortometraggi e documentari fuori dalla classe film, fumetti, canzoni.
- Libri: nessun controllo se l'ambientazione e davvero Milano; la fonte forte e Wikidata/Wikipedia (125), Open Library e LoC sono rumorosi.
- Titoli senza etichetta: pochi (es. `Q17150542`, `Q18327213` rimasti col solo QID).

#### File

- `pulito\film.csv`, `serie_tv.csv`, `libri.csv`, `altro.csv`: una riga per opera, colonne `fonte_wikidata_P840`, `fonte_wikidata_P915`, `fonte_itwiki_categoria`, `fonte_openlibrary`, `fonte_loc`, `fonte_sbn`, `imdb_id` (solo identificatore, nessun dato IMDb), `luogo_preciso`, `lat_lon_primo_luogo_preciso`.
- `pulito\openlibrary_tutti.csv` (4.562 righe, con colonna `narrativa_probabile`), `pulito\_statistiche.json`.
- Programmi in `scripts\`; `raw\` non va pubblicato intero (le parti Wikipedia/Open Library sono comunque ripubblicabili, vedi licenze sopra).

### Fase 2 — luoghi e pagina (2026-10-30)

- I luoghi precisi di Milano sono estratti dalle voci di Wikipedia (trama, produzione, riprese) con un elenco di luoghi preparato da noi (stradario, NIL, luoghi OSM, monumenti). Le opere con un luogo preciso passano da 14 a 185 (144 film e serie, 37 libri): 426 collegamenti opera-luogo, 179 luoghi diversi.
- Precisione controllata a mano: 28 su 30 nell'ultimo giro, 111 su 120 su quattro giri.
- Luoghi più raccontati: Stazione Centrale 26, Scala 26, Duomo 23, San Siro 13, San Vittore 12, San Babila 11.
- Le frasi di Wikipedia restano solo sul PC (`pulito/_frasi_locali.csv`); nel sito ci sono solo fatti e link.
- **Nome della sezione scelto da Davide: `milano-raccontata`** (pagina `docs/milano-raccontata/`); la cartella dei dati resta `film-e-libri/`.

## 12. Prezzi delle case dal 2004

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `prezzi-case/` (nome scelto da Davide); i file OMI scaricati da Davide con SPID vanno in `prezzi-case/omi_da_davide/`._

- 2026-10-30 — Filone chiesto da Davide (nella sua richiesta "filone 10", rinumerato 12 perché il 10 è la violenza politica e l'11 Milano raccontata). Domanda: come sono cambiati i prezzi zona per zona dal 2004, e se le zone vicine a cose nuove (M4, M5, parchi, riqualificazioni, Area C) si sono mosse diversamente.
- **Regole specifiche**:
  - Le quotazioni OMI sono stime, non prezzi di vendite reali: va sempre scritto accanto ai grafici.
  - Per la M4 si presenta un confronto, non una prova.
  - Prima del sito, Davide riceve la cosa più sorprendente in due righe e dà l'ok.
  - Niente SPID per Claude: gli scarichi con SPID li fa Davide.
- Avvio: si fa solo la parte senza SPID (Davide, consumo oltre il 90%).

### Fase 1 — raccolta (2026-10-30)

**Prezzi delle case a Milano dal 2004: note sulla fase 1 (scaricamento e preparazione)**

Data: 30 ottobre 2026. Cartella: `prezzi-case\`. Nessuna analisi dei prezzi fatta: mancano ancora le quotazioni OMI (servono lo SPID di Davide, vedi `COSA_SCARICARE.md`).
Come leggere: ogni numero dice da quale file e da quale campo viene. Tutti i programmi sono in `scripts\`, il comando per rifare tutto è in `STATO.md`.
Nessun servizio con SPID o con registrazione è stato usato. Pause di 2-5 secondi tra le richieste, User-Agent dichiarato, nessun errore "troppe richieste".

#### In breve

1. **Le quotazioni OMI (prezzi di vendita e affitti per zona) si possono avere solo con SPID/CIE/credenziali Entratel/Fisconline.** Disponibili dal 1° semestre 2004 (pagina "Forniture dati OMI", aggiornata 5/10/2026), ultimo semestre pubblicato: 2026/1. Licenza CC BY 4.0. Tocca a Davide: `COSA_SCARICARE.md`.
2. **I perimetri delle zone per Milano li ho presi io, senza login**, dal servizio di mappa pubblico: 32 semestri, dal 2010/2 al 2026/1. Prima del 2010/2 non esistono.
3. **Le zone cambiano molto**: 55 zone fino al 2013/2, 41 dal 2014/1, 43 dal 2024/2. Solo 2 zone su 55 sono confrontabili uno-a-uno dal 2010 a oggi; dal 2014/1 in poi 29 zone su 43 sì. Niente viene unito in silenzio: `pulito\zone_non_1a1.csv`.
4. **Compravendite (NTN) di Milano**: serie trimestrale 2004-2026, aperta, solo per tutto il comune. Per zona OMI non esiste.
5. **Inflazione ISTAT** (FOI senza tabacchi) raccordata tra le basi: mensile dal 12/2003 al 9/2026, annuale 1996-2025.
6. **Fermate metro con data di apertura**: 134 fermate (M1-M5), `pulito\fermate_metro.csv`.
7. **Pipeline pronta** e provata su un campione FINTO e su 6 semestri veri (copie di terzi, solo come prova): legge i semestri, tiene solo Milano, calcola centro e ampiezza, reale, rapporto affitto/prezzo.

---

#### 1. Quotazioni OMI (NON scaricate: serve lo SPID)

- Pagina: https://www.agenziaentrate.gov.it/portale/it/web/guest/schede/fabbricatiterreni/omi/forniture-dati-omi (letta il 30/10/2026, salvata in `raw\pagine_ae\forniture.html`).
- Dice: download gratuito delle quotazioni "a partire dal 1° semestre 2004"; perimetri (file KML) "dal 2° semestre 2010" per tutta l'Italia, una provincia o un comune; volumi di compravendita (NTN) per comune "dall'annualità 2011" (esclusi i comuni dei territori col sistema tavolare). Accesso: "utenti che accedono ai servizi telematici nell'area riservata". Licenza: CC BY 4.0, da citare «Agenzia delle Entrate – OMI».
- Come funziona (articolo Eutekne del 6/4/2018, da riverificare perché vecchio): ambito = Italia / area / regione / provincia / comune; risultato = un .zip con 2 CSV, `VALORI` e `ZONE`; ogni richiesta si scarica **una sola volta, entro 7 giorni**.
- Formato di un file vero (visto su copie di terzi, 2016-2018): separatore `;`, prima riga di titolo, intestazione `Area_territoriale;Regione;Prov;Comune_ISTAT;Comune_cat;Sez;Comune_amm;Comune_descrizione;Fascia;Zona;LinkZona;Cod_Tip;Descr_Tipologia;Stato;Stato_prev;Compr_min;Compr_max;Sup_NL_compr;Loc_min;Loc_max;Sup_NL_loc;`, numeri con la virgola. Milano = `Comune_cat` `F205`. Nome file: `QI_<numero richiesta>_1_<anno><semestre>_VALORI.csv` / `_ZONE.csv`.
- Per i semestri **prima del 2016** il "tracciato ante 2016" dell'Agenzia (https://github.com/ondata/quotazioni-immobiliari-agenzia-entrate/blob/master/doc/Tracciato_record_dati_ante2016.pdf, copia di terzi di un documento dell'Agenzia, salvato in `raw\ondata_mirror_schema\`) descrive campi separati da `|` con nomi diversi (`VALMIN`, `VALMAX`, `LOCMIN`, `LOCMAX`, `COD_TIP_PREV`...). **Non ho visto un file vero di quel periodo**: il lettore è scritto sul tracciato ma non provato su dati veri.
- Il manuale OMI 2025 (PDF) dice che il volume è proprietà dell'Agenzia e non si riproduce senza autorizzazione: vale per il testo del manuale, non per i dati (che sono CC BY 4.0).
- **Copia di terzi** (6 semestri 2016/1-2018/2, 12 MB): repository "ondata/quotazioni-immobiliari-agenzia-entrate" su GitHub, `rawData\2016-1.zip ... 2018-2.zip`, scaricati il 30/10/2026 in `raw\ondata_mirror_rawdata\`. Il progetto scrive che la licenza non è chiarita (ma i dati originali sono CC BY 4.0 per l'Agenzia). Non verificabile contro gli originali. Servono come prova del programma, non come fonte finale.

#### 2. Perimetri delle zone OMI di Milano (scaricati, senza login)

- Fonte: servizio di mappa pubblico dell'Agenzia, `https://www1.agenziaentrate.gov.it/servizi/geopoi_omi/zoneomi.php?richiesta=6&codcom=F205&semestre=<AAAAS>` (è la stessa chiamata che usa la mappa; l'ho trovata leggendo `js\cittadino.js` della pagina, salvato in `raw\geopoi_probe\`). Scaricato il 30/10/2026.
- File: `raw\geopoi\F205_<AAAAS>.json`, 32 file, circa 35 MB. Da `20102` (2010 2° sem.) a `20261` (2026 1° sem.). Per `20101` e prima la risposta è vuota (coerente con "dal 2° semestre 2010").
- Il menu della mappa elenca solo 2016/1-2026/1 (campo `SEMESTRE` di `zoneomi.php?richiesta=5`), ma il servizio risponde anche per i semestri 2010/2-2015/2: li ho usati. Non è una funzione dichiarata: andrà citato come "servizio di mappa GEOPOI".
- Licenza: banche dati OMI CC BY 4.0 (stessa pagina "Forniture"). Ripubblicabile citando la fonte.
- **Il download ufficiale in KML/GML (`perimetri.php?...&formato=kml`) non funziona oggi**: 4 prove su Milano (2016/1, 2025/2, formato kml e gml) hanno dato errore 500 con il testo "Impossibile creare l'archivio ZIP". Ho usato i dati JSON della mappa. Se Davide vuole i KML ufficiali: stessa pagina "Forniture dati OMI", sezione "Perimetri di Zona" (SPID).
- **Trappola dei dati:** ogni zona arriva come un solo `Polygon` con più anelli, dove gli anelli sono spesso pezzi staccati, non buchi. Letto come GeoJSON normale, l'area totale di Milano scende a circa 100 km² (e per qualche semestre a 52 km²) invece di 181,8 km². Il programma `05_zone_corrispondenza.py` usa la regola pari/dispari sugli anelli: l'area torna a 181,3-181,8 km² in tutti i 32 semestri (campo `area_totale_km2` in `pulito\zone_periodi.csv`).
- Controllo con file veri: per il 2018/2 i 41 codici zona dei perimetri coincidono esattamente con i 41 codici del file `ZONE` ufficiale (copia di terzi). Le zone con valori sono 40: la zona rurale `R2` non ha quotazioni.

#### 3. Corrispondenza tra zonizzazioni (`pulito\zone_*.csv`)

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

#### 4. Compravendite (NTN), Comune di Milano

- Serie nuova 2011-2024 (definitiva): `raw\omi_ntn\RESIDENZIALE_DEFINITIVO_2011_2024.zip` (146 kB), file `RES.csv`; provvisoria 2025-2026: `raw\omi_ntn\RESIDENZIALE_2025_2026_PROVV.zip` (49 kB). Anche non residenziale (`NON_RESIDENZIALE_*.zip`, 255 kB e 63 kB), non elaborato. Pagina: https://www.agenziaentrate.gov.it/portale/schede/fabbricatiterreni/omi/banche-dati/volumi-di-compravendita (letta il 30/10/2026). Link diretti, nessun login.
- Serie vecchia 2004-2016: `raw\omi_ntn_archivio\Residenziale_<anno>.xls` (13 file + `Residenziale_2000-2003.xls`, 2 MB), dalla pagina "Archivio volumi di compravendita". Foglio 1 = trimestrale.
- Livello: provincia e capoluogo (campo `Cap` = `cap`, riga `Prov` = `MI`). Il capoluogo di Milano è il Comune di Milano. **Non c'è dato per zona OMI né per quartiere.**
- Elaborato in `pulito\ntn_milano_trimestrale.csv` (114 righe), campi `anno`, `trimestre`, `serie`, `ntn_capoluogo`, `ntn_provincia`. Le serie NON sono fuse: dove si sovrappongono (2011-2016) `pulito\ntn_milano_confronto_2011_2016.csv` mostra le differenze: media -0,25%, da -1,27% a +0,87% (24 trimestri). Per il 2011-2016 conviene la serie nuova.
- Totali annui capoluogo (campo `ntn_capoluogo`, somma dei trimestri): 2004: 24.966; 2008: 18.977; 2012: 14.575 (minimo, serie nuova); 2019: 26.232; 2020: 21.650; 2022: 28.617; 2024: 24.003; 2025 (provvisorio): 25.173. Il 2026 ha solo 2 trimestri (12.388).
- Licenza: la pagina non la scrive per questi file; la pagina "Forniture dati OMI" dice che le banche dati OMI sono CC BY 4.0. Da citare «Agenzia delle Entrate – OMI».

#### 5. Inflazione ISTAT (FOI senza tabacchi)

- Fonte: ISTAT, servizio SDMX `https://esploradati.istat.it/SDMXWS/rest/data/IT1,<flusso>,1.0/<chiave>`, scaricato il 30/10/2026 in `raw\istat\`:
  - `169_748_DF_DCSP_FOI1B2025_1.m.csv` (906 kB): mensile, 4 basi concatenate, 2003-12 -> 2026-09; `169_748_DF_DCSP_FOI1B2025_2.m.csv` (874 kB): la stessa serie in versione "tutte le basi 1996-2025" (non usato); `169_745_DF_DCSP_FOI1B2015_1.m.csv` (444 kB): base 2015 fino al 2025 (non usato, serve da controllo);
  - `169_750_DF_DCSP_FOI2B2025_1.csv` (62 kB): medie annue 1996-2025.
- Voce usata: `ECOICOP_2` = `00ST` (tutti i prodotti senza tabacchi), `MEASURE` = 4 (indice). Basi: 1995, 2010, 2015, 2025 (mensile: campo `DATA_TYPE` 4, 11, 55, 101; annuale: 5, 12, 56).
- Raccordo (`scripts\03_istat_foi.py`): il coefficiente tra una base e la precedente è la media dell'anno-base nella serie precedente diviso 100, come fa ISTAT; poi tutto è portato a 2025 = 100. Risultato in `pulito\foi_mensile.csv` e `pulito\foi_annuale.csv` (indice originale e raccordato).
- Controllo: le variazioni a 12 mesi ricalcolate coincidono con quelle pubblicate da ISTAT (campo `MEASURE` 7): 12/2010 1,92% (ISTAT 1,9), 1/2026 0,81% (0,8), 9/2026 4,04% (4,0); annuale 2025 su 2024 +1,4%. Media 2025 dei mesi = 100,00.
- Licenza: CC BY 4.0 (https://www.istat.it/note-legali/, letta il 30/10/2026). Ripubblicabile citando ISTAT.
- Trappola: il server ISTAT con chiave "tutto" non risponde entro 90 secondi per i flussi mensili; con chiave `M.IT.....` e `startPeriod=2003-12` ha risposto in circa 2 minuti.

#### 6. Fermate della metro con data di apertura

- Fermate, nomi e coordinate: GTFS del Comune (AMAT) già scaricato dalla filiera 7, letto in sola lettura (`..\bici-auto-mezzi\raw\gtfs\ext_comune_new`, versione 425 del 26/10/2026); estratto l'ordine delle fermate in `raw\gtfs_metro_estratto\metro_stop_ordine.csv`.
- Date di apertura: tabelle "Apertura" e "Le date delle aperture" delle voci it.wikipedia Linea M1-M5 (lette via API, `raw\wikipedia_metro\`), controllate con en.wikipedia (Line 4 e 5) e articoli di stampa. Le date sono fatti, ma la fonte è Wikipedia (CC BY-SA): il testo non va copiato, i fatti sì.
- Risultato: `pulito\fermate_metro.csv`, 134 fermate (M1 38, M2 35, M3 21, M4 21, M5 19), campi `linea`, `fermata`, `lat`, `lon`, `data_apertura`, `tratta`, `fonte`. Tutte le fermate del GTFS hanno una data; nessuna senza. Alcune fermate sono fuori dal Comune di Milano (es. Rho, Pero, Sesto, Cologno, Gessate, Assago): da filtrare nel passo spaziale. Nello stesso nome la stazione di interscambio compare una volta per linea.
- **Date M4** (campo `data_apertura`): 26/11/2022 Linate Aeroporto, Repetti, Stazione Forlanini, Argonne, Susa, Dateo; 4/7/2023 Tricolore, San Babila; 12/10/2024 le altre 13 (Sforza-Policlinico ... San Cristoforo). Confermate da it.wikipedia, en.wikipedia, VareseNews/Il Giorno.
- **Date M5**: 10/2/2013 Bignami-Zara (7 fermate); 1/3/2014 Isola e Garibaldi FS; 29/4/2015 Domodossola, Lotto, Segesta, San Siro Ippodromo, San Siro Stadio; poi Portello 6/6/2015, Cenisio 20/6/2015, Gerusalemme 26/9/2015, Monumentale 11/10/2015, Tre Torri 14/11/2015.
- **Aperture dopo il 2004 sulle linee vecchie**: M1 Rho Fieramilano 14/9/2005 (provvisoria dal 30/3/2005) e Pero 19/12/2005; M2 Abbiategrasso 17/4/2005 (**dubbio**: la voce it.wikipedia scrive 17 aprile nel testo e 17 marzo nell'elenco; scelto aprile perché è una domenica) e Assago Milanofiori Nord e Forum 20/2/2011; M3 Dergano, Affori Centro, Affori FN, Comasina 26/3/2011.
- Non verificate con fonti ufficiali del Comune/ATM/MM: le pagine ufficiali non sono state lette (nessuna è servita per decidere). Per le date a giorno preciso delle aperture pre-2004 non ho fatto controlli incrociati: non servono per l'analisi dal 2004.

#### 7. Riuso di materiale di altri filoni (solo riferimenti, niente copie)

`pulito\riferimenti_riuso.csv` elenca i percorsi assoluti: parchi, servizi e punteggi "15 minuti" (filone 9), redditi per CAP (filone 9: attenzione, sono per CAP e non per quartiere), confine del Comune e NIL vigenti (filone 9), varchi e ingressi di Area C (filone 6), GTFS (filone 7).

#### 8. Pipeline pronta (codice)

- Programmi in `scripts\` (Python 3.12, `python -I`): `01_metro_da_gtfs.py`, `02_fermate_metro.py`, `03_istat_foi.py`, `04_ntn_milano.py`, `05_zone_corrispondenza.py`, `06_leggi_omi.py`, `07_prezzi.py`, `esegui_pipeline.py`. Prova: `scripts\test\make_fake.py` crea un campione finto in `test_finto\`.
- Cosa calcola `07_prezzi.py`: per ogni semestre/zona/tipologia/stato, **centro = (min+max)/2**, **ampiezza = max-min** e ampiezza relativa; versione **reale in euro 2025** (media FOI del semestre); **resa lorda annua = affitto centro × 12 / prezzo centro** e anni di affitto per pagare il prezzo; riga di stato prevalente (`Stato_prev` = P); mediana NON pesata fra le zone (non è il prezzo medio della città: non esistono pesi per zona).
- Un valore 0 o vuoto vuol dire "dato assente", non zero: diventa vuoto e la riga è segnalata (`flag_compr`, `flag_loc`).
- Prove fatte: (a) campione finto di 4 semestri (3 nel formato `;`, 1 nel formato `|` inventato, uno dentro uno zip in cp1252, con righe di un altro comune da scartare e una zona divisa in due) → tutto letto, zona divisa segnalata in `zone_non_1a1.csv`; (b) 6 semestri veri 2016/1-2018/2 (copie di terzi): 2.811 righe di Milano, nessun duplicato, nessun minimo > massimo, 40 zone con valori per semestre; esempio zona `B12`, abitazioni civili, stato prevalente: 8.100 euro/m² nel 2016/1 e 8.150 nel 2018/2 (centro di min e max; campo `Compr_min`, `Compr_max`), che in euro 2025 sono 9.866 e 9.660.
- Controlli scritti in chiaro in `pulito\omi_controlli.txt` dopo ogni lettura: buchi di semestri, righe doppie, minimo > massimo, zeri, cambi dei codici zona.

#### Trappole dei dati (riassunto)

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


## 13. La neve (e la nebbia) a Milano

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `neve-e-nebbia/`._

- 2026-10-30 — Filone chiesto da Davide (nella sua richiesta numerato 11; rinumerato perché 10-12 erano già occupati). Domanda: quanti giorni di neve per inverno dagli anni '50, se nevica meno o diversamente; con la stessa fonte (NOAA, Linate e Malpensa) i giorni di nebbia. Attenzione ai cambi di strumento (osservatore umano poi sensori automatici). Nomi delle cartelle scelti da Davide ("cinema" diventa `cinema-spariti`). Fase 1: solo raccolta, poi un riassunto e la cosa più sorprendente prima di grafici e pagine.

### Fase 1 — raccolta (2026-10-30)

**Neve e nebbia a Milano - note della fase 1 (raccolta e controllo)**

Domanda: a Milano nevica meno, o in modo diverso (meno episodi ma più forti)? E "che fine ha fatto la nebbia?".
Stato: fase 1 finita il 30/10/2026. Nessun grafico, nessuna pagina. Tutto scaricato in blocco con programmi (nessun login, nessuna registrazione).

#### 1. Fonti, indirizzi, data di scarico (30/10/2026)

| Fonte | Indirizzo | Cosa è | File scaricati |
|---|---|---|---|
| NOAA ISD (Integrated Surface Database), versione completa (non "Lite": la Lite non ha il tempo presente) | https://www.ncei.noaa.gov/pub/data/noaa/AAAA/USAF-WBAN-AAAA.gz | osservazioni orarie/tri-orarie, un file per stazione e anno | `raw\noaa\isd\160800-99999\` (80 file, 21 MB), `raw\noaa\isd\160660-99999\` (60 file, 22 MB), `raw\noaa\isd\160810-99999\` (9 file, 1,4 MB) |
| NOAA GSOD (Global Summary of the Day) | https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/AAAA/16080099999.csv | riassunto giornaliero (flag FRSHTT, SNDP, VISIB, PRCP, TEMP) | `raw\noaa\gsod\16080099999\` (69 file, 5,5 MB), `...\16066099999\` (60 file, 4,9 MB), `...\16081099999\` (9 file, 0,4 MB) |
| Storia delle stazioni ISD | https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv (e .txt) | date di inizio/fine, coordinate, quota | `raw\isd_history\isd-history.csv` (2,9 MB) |
| Inventario ISD | https://www.ncei.noaa.gov/pub/data/noaa/isd-inventory.txt | n. osservazioni per mese | `raw\isd_history\isd-inventory.txt` (17,8 MB). TRAPPOLA: per queste stazioni mostra solo il 2020-2025, non è usabile per gli anni vecchi; i conteggi veri li ho fatti io dai file |
| Documentazione | isd-format-document.pdf, isd readme, gsod readme (stessa cartella NOAA) | codici e licenza | `raw\isd_history\` |

Totale scaricato: circa 55 MB. Download riprendibile: `python -I scripts\scarica_isd_gsod.py <percorso_assoluto>\raw\noaa` (salta i file già presenti). Registro: `raw\noaa\log_download.txt`. Nessun errore, solo i 404 degli anni in cui NOAA non ha il file.

Stazioni (da isd-history.csv):
- **LINATE**: USAF-WBAN 160800-99999, WMO 16080, ICAO LIML, 107 m, inizio record 1931. È la serie principale.
- **MALPENSA**: 160660-99999, WMO 16066, ICAO LIMC, 234 m, inizio 1965. Serve di confronto.
- **LINATE_160810**: 160810-99999, "MILANO/LINATE", solo SYNOP 2005-2009 e 2015-2018 (1480 giorni). Duplicato del SYNOP di Linate sotto un altro numero. NON usato nei totali; tenuto nel file giornaliero con il nome `LINATE_160810`.
- Brera (strand 1) non esiste in ISD: per la temperatura uso `..\temperature\serie\serie_unica.csv` (solo lettura).

GSOD di Linate 1975-2025 era già in `..\temperature\raw\gsod_linate\`: ho verificato che i 51 file sono identici byte per byte a quelli che ho riscaricato (stesso hash). Il programma legge la mia copia, ma sono gli stessi dati.

#### 2. Copertura (da `pulito\completezza_per_anno.csv`)

LINATE ISD (giorni con almeno 4 ore di osservazioni, per anno):
- 1931-1938: solo 1-2 osservazioni al giorno, con buchi (167-356 giorni/anno). Non utilizzabile per contare giorni di neve/nebbia.
- 1939-1950: NESSUN file.
- 1951-1955: ogni ora (24 ore/giorno), anno completo (il 1951 solo da ottobre). 1956 completo a metà (274 giorni). 1957: 2,5 osservazioni/giorno, mezzo anno. 1958: 4/giorno. 1959-1961: UNA osservazione al giorno (non basta). 1962-1963: nessun file. 1964: solo 113 giorni.
- 1965-1970: ogni 3 ore (8/giorno), anni completi. 1971: solo gennaio-marzo. 1972: nessun file.
- 1973-1983: ogni ora (METAR + SYNOP), completo.
- 1984-1989: solo SYNOP ogni 3 ore (i METAR mancano nell'ISD, anche se l'aeroporto li emetteva), completo ma più rado.
- 1990-2025: ogni ora, completo. Dal 1994 al 1998 le osservazioni orarie sono circa 16-20 al giorno (mancano alcune ore, soprattutto di notte). 2019: 351 giorni; 2024: 359; 2025 solo fino al 24 agosto.
- Inverni (novembre-marzo) con dati sufficienti (almeno 90% dei giorni con 4 ore o più): 65 inverni a Linate (1952-1956, 1958, 1965-1971, 1974-2025, mancano 1957, 1959-1964, 1972, 1973 e prima del 1952).

MALPENSA ISD: 1965 (solo 14 giorni), 1966-1971 (3-orario), 1972 mancante, 1973-2025 ore. 57 inverni sufficienti (1967-1971, 1974-2025).

GSOD Linate: 1951-1958, 1964-1971, 1973-2025 (mancano 1959-1963 e 1972). GSOD Malpensa: 1965, 1966-1971, 1973-2025 (manca 1972).

#### 3. Tabelle prodotte (`pulito\`)

- `giorni_neve_nebbia.csv` - una riga per stazione e giorno (50.313 righe; Linate 27.600, Malpensa 21.233, LINATE_160810 1.480). Il "giorno" è il giorno UTC (come in GSOD), non quello locale. Colonne principali: `isd_n_obs`, `isd_n_hours` (ore diverse con almeno un rapporto), `isd_n_synoptic_hours` (ore 00,03,...,21 UTC), le bandiere di neve e nebbia (sotto), `min_vis_m`, le bandiere GSOD (`gsod_snow`, `gsod_fog`, `gsod_sndp_cm`, `gsod_prcp_mm`, `gsod_tmean_c`) e `report_types` (quanti rapporti per tipo). Vuoto = dato non esistente per quel giorno (ISD o GSOD assente), non zero.
- `inverni_neve_nebbia.csv` - totali per stazione e inverno (novembre-marzo, etichetta = anno di gennaio: inverno 2012 = nov 2011 - mar 2012). Contiene giorni attesi, giorni con dati (`pct_days_ge4h`, `winter_complete_isd` = "si" se almeno 90%), tutte le definizioni, profondità massima, pioggia equivalente nei giorni di neve GSOD, temperatura media nov-mar di Brera (`brera_tmean_nov_mar`, dalla serie unica del strand 1) e di Linate (GSOD).
- `totali_annuali.csv` - lo stesso per anno solare (la nebbia c'è anche in ottobre e aprile).
- `completezza_per_anno.csv` - per stazione e anno: giorni con dati, ore medie al giorno, quota di osservazioni con tempo presente e con visibilità, n. rapporti SYNOP e METAR/SPECI, rapporti con testo METAR completo, quota di METAR "AUTO", n. rapporti di profondità neve.
- `isd\isd_giorni_*.csv` e `isd\isd_diagnostica_*.csv` - passaggio intermedio (un file per stazione ISD). Programmi: `scripts\estrai_isd.py` poi `scripts\costruisci_giorni.py` (si rifà tutto con `python -I scripts\estrai_isd.py <abs>\raw\noaa\isd <abs>\pulito\isd` e `python -I scripts\costruisci_giorni.py <abs cartella strand>`).

#### 4. Definizioni (tutte mantenute, mai mescolate)

Neve (un giorno conta se c'è almeno una osservazione che soddisfa):
- `snow_obs_strict`: tempo presente "neve in atto" - codici WMO 4677 (MW) 70-75, 77, 78, 85, 86; codici automatici (AW) 70-73, 85-87; METAR automatico (AU) neve o granuli di neve. Esclusi diamond dust (76) e ice pellets (79). QUESTA è la definizione principale.
- `snow_obs_wide`: strict + pioggia e neve mista (MW 68, 69, 83, 84; AW 45, 46, 67, 68) + neve nell'ora precedente (MW 22, 23, 26; AW 24).
- `snow_heavy_obs`: neve forte (MW 74-75, AW 73/87, AU intensità forte). Pochissimi casi, serve solo come indizio per "meno episodi ma più forti".
- `snow_synoptic_hours`: come strict ma contando solo le osservazioni delle ore 00,03,...,21 UTC (al massimo 8 al giorno): campione omogeneo nel tempo, utile per confrontare anni con 8 e anni con 24 osservazioni al giorno.
- `snow_metar_text`: neve letta direttamente nel testo del METAR (SN, SG; esclusi BLSN e DRSN), solo dal 2006.
- `snow_depth_isd_gt0` e `gsod_snow_depth_gt0`: profondità di neve al suolo maggiore di zero (campo ISD AJ1 e GSOD SNDP).
- `gsod_snow`: flag neve/ice pellets di GSOD (terza cifra di FRSHTT).
- Nelle tabelle inverno c'è anche `snow_days_union_any` = neve strict OPPURE profondità > 0 OPPURE flag GSOD.

Nebbia:
- `fog_code_strict`: almeno un'osservazione con codice di nebbia sulla stazione (MW 41-49, AW 30-35, AU nebbia FG senza descrittore).
- `fog_code_wide`: strict + nebbia nell'ora precedente, nebbia lontana, nebbia bassa (MW 28, 40, 11, 12; AW 20; AU qualunque FG).
- `fog_code_vis_lt1km`: nebbia (wide) nello stesso rapporto con visibilità sotto 1000 m. **Consigliata per confrontare gli anni**, perché la definizione internazionale di nebbia è visibilità < 1 km.
- `vis_lt1km_any`: la visibilità minima del giorno è sotto 1000 m, a prescindere dal codice (comprende anche foschia fitta, pioggia/neve forte).
- `fog_synoptic_code` e `fog_synoptic_code_vis_lt1km`: come sopra, solo ore sinottiche.
- `fog_metar_text` (FG/BCFG/MIFG/PRFG/FZFG nel testo) e `fog_metar_text_dense` (FG, FZFG, PRFG): dal 2006.
- `gsod_fog`: flag nebbia GSOD (prima cifra di FRSHTT).
- Qualità: scartati i valori con codice di qualità 2, 3, 6, 7 (sospetto/errato).

#### 5. Risultati preliminari (solo numeri, nessuna interpretazione; inverni completi, medie per decennio dell'etichetta)

Linate, giorni di neve per inverno nov-mar (`snow_days_strict`): anni 1950 (1952-56,58): 10,5; 1960 (1965-69): 8,0; 1970: 10,5; 1980: 9,0; 1990: 5,8; 2000: 7,1; 2010: 8,3; 2020 (2020-2025): 2,0. Singoli inverni: da 0 (1990, 2025) a 21 (1986). Neve forte (codici "forte"): 0-3 giorni per inverno, mai oltre. Correlazione inverno per inverno tra giorni di neve e temperatura media nov-mar di Brera: circa -0,6 (Linate, 65 inverni).
Linate, giorni di nebbia per anno solare (`fog_code_vis_lt1km`, anni con dati completi): 1950: 121; 1960: 121; 1970: 108; 1980: 85; 1990: 79; 2000: 62; 2010: 53; 2020-2024: 52.
Malpensa: neve strict 7, 11, 12, 7, 9, 10, 2 (decenni 1960-2020); nebbia (vis<1 km) 90, 101, 123, 106, 55, 34, 32 giorni per anno.
Questi numeri sono preliminari: vedi le trappole sotto prima di usarli.

#### 6. Cambi di strumenti/modalità trovati (non è clima)

1. **1984-1989, Linate**: nell'ISD ci sono solo i SYNOP ogni 3 ore (i METAR mancano). I conteggi con l'insieme completo delle osservazioni sono quindi meno sensibili; per questo ho creato le colonne "sinottiche" (stesse 8 ore in tutti gli anni).
2. **1994-1998, entrambe le stazioni**: le osservazioni scendono a circa 9.000 l'anno (da 20.000-27.000) e la quota di rapporti con "tempo presente" scende al 40%; dal 1999 risale al 98%. In quegli stessi anni i giorni di nebbia calano insieme a Linate e a Malpensa (Malpensa: 142 giorni nel 1994, 95 nel 1995, 58 nel 1998). Sospetto di cambio di codifica/di flusso dati, non solo di clima.
3. **1999-2004**: quasi ogni rapporto METAR ha un codice di tempo presente anche se non c'è nulla (92%); dal 2006 il codice c'è solo quando c'è un fenomeno (circa 30%). Quindi "assenza di codice" non vuol dire "dato mancante" dopo il 2005, ma lo vuol dire prima. Per questo non ho usato la quota di tempo presente come misura di completezza dei giorni.
4. **2006**: nell'ISD compare per la prima volta il testo completo del METAR (campo REM). Da lì i giorni di nebbia per codice di Linate salgono (SYNOP a ore sinottiche: 46 nel 2005, 69 nel 2006) mentre i giorni con codice di nebbia E visibilità < 1 km non salgono: dal 2006 il codice nebbia comprende anche nebbia a banchi (BCFG, MIFG) con visibilità sopra 1 km. A Malpensa lo stesso stacco si vede dal 2016-2018. Per questo motivo `fog_code_vis_lt1km` è più omogenea di `fog_code_strict` e di `gsod_fog`.
5. **Differenza Linate-Malpensa (giorni di nebbia con vis<1 km)**: Malpensa ha 28-70 giorni in più per anno nel 1982-1994, differenza vicino a zero nel 1998-2005, poi Linate ha 15-30 giorni in più dal 2006. Salti a 1982, 1995-1998, 2006: sono candidati a cambi non climatici (strumenti di visibilità, metadati: Malpensa ha quota 211/234 m e coordinate che cambiano nel 1981, nel 1998 e nel 2013; Linate cambia coordinate nel 1986, 1998-2000, 2010, 2013).
6. **Automazione**: nell'ISD i METAR di Linate con la parola AUTO compaiono dal 2018 (1,1% nel 2018, 5,1% nel 2019, 23,1% nel 2020, 11,6% nel 2021, poi 1-5%). Sono quasi tutti emessi di notte (ore 21-04 UTC). Nello stesso periodo compaiono i gruppi AW (tempo presente automatico: 77 rapporti nel 2018, 500 nel 2020). Controllo fatto sulle notti nov-feb 2019-2025: nei METAR AUTO la visibilità è sotto 1 km nel 22% dei casi e nel testo c'è FG nel 19,5%; nei METAR non automatici 11,6% e 11,3%. Non c'è quindi sottostima da parte dei sensori, ma il campione AUTO è piccolo e non confrontabile (periodi di chiusura notturna/Covid). Il tipo di rapporto "AUTO" nel campo tipo (non nel testo) compare solo 8 volte (2005-2012). Non c'è nessun file che dichiari quando i sensori sono entrati in servizio: andrebbe chiesto a ENAV/Aeronautica o all'ARPA.
7. **2013-2017**: la visibilità manca nel 18-36% dei rapporti ISD di Linate (probabilmente i CAVOK); torna a posto nel 2018. Non tocca `vis_lt1km_any` (se c'è nebbia c'è la visibilità).
8. **Coordinate Linate**: SYNOP e METAR hanno posizioni diverse in ISD dal 2010 (SYNOP 45,450 N 9,267 E, 104 m; METAR 45,445 N 9,277 E, 108 m): due punti di osservazione o due codifiche. Prima del 1956 la quota era 120 m, poi 103-107 m.

Nessun salto improvviso "pulito" è stato attribuito al clima prima di aver escluso questi cambi; la parte di analisi spetta alla fase 2.

#### 7. Trappole dei dati

- **Profondità della neve inaffidabile**: tutti i rapporti ISD di profondità (campo AJ1, 11.011 rapporti) hanno il codice di condizione "9 = mancante" anche con un valore presente, e compaiono valori assurdi (264, 287 cm a Linate nel gennaio 1991; 225 cm nel febbraio 1985; 179 e 269 cm nel 2002-2003 in giorni senza neve). GSOD SNDP copia questi valori. Nel file giornaliero i valori oltre 60 cm sono tolti da `snow_depth_isd_cm` e `gsod_sndp_cm` (restano in `snow_depth_isd_cm_raw` e segnalati con `snow_depth_suspect_gt60`). Dal 2012 quasi non ci sono più rapporti. Non usare la profondità per la frase "episodi più forti" senza un'altra fonte (ARPA/Brera).
- **Giorno UTC**, non locale: alcune nebbie/nevicate notturne vengono spezzate tra due giorni.
- **Numero di ore osservate cambia molto** (da 1 a 24 al giorno, vedi sezione 2): un conteggio "giorni con almeno una osservazione di nebbia" favorisce gli anni con più osservazioni. Usare `isd_n_hours`, le colonne sinottiche e la colonna `winter_complete_isd`.
- **Inverni incompleti**: gli inverni con meno del 90% dei giorni utili hanno `winter_complete_isd` = "no"; i totali ci sono lo stesso nella tabella ma non vanno confrontati. Sono tutti i 1931-1938, 1957, 1959-1964, 1972, 1973 (solo gennaio-marzo) a Linate.
- **GSOD ≠ ISD per la nebbia**: GSOD segnala nebbia con una regola che comprende anche i casi larghi (nebbia a banchi, ora precedente). Dal 2006 i giorni di nebbia GSOD sono 10-30 più alti di quelli con vis<1 km. Per la neve, GSOD e ISD strict concordano quasi sempre (GSOD un po' più alto perché comprende ice pellets).
- Il testo METAR dà qualche giorno di neve in più del codice ISD (126 contro 115 giorni a Linate da giugno 2006): nei METAR le nevicate miste (RASN) e le segnalazioni "SG" non sempre diventano codici ISD.
- **Inventario ISD inutilizzabile** per gli anni vecchi (vedi sezione 1).
- **Neve in Linate 1988-1990** (1, 1, 0 giorni): inverni davvero poveri di neve, ma in quegli anni il campione è solo sinottico ogni 3 ore; non confrontare direttamente con gli anni a 24 ore senza usare le colonne sinottiche.
- Anni non coperti da ISD né GSOD: 1939-1950, 1962-1963, 1972 (Linate); 1972 (Malpensa).

#### 8. Licenza

I dati NOAA sono pubblici e gratuiti per uso di ricerca e non commerciale. Ma NOAA scrive (readme ISD): "The non-U.S. data in ISD are subject to WMO Resolution 40 restrictions, and cannot be redistributed to other users or customers" e (readme GSOD) che per i dati non statunitensi "the data or any derived product shall not be provided to other users or be used for the re-export of commercial services". I dati italiani sono quindi dati WMO Risoluzione 40.
Conseguenza pratica: **NON ripubblicare i file raw** (`raw\`) né, per prudenza, il file giornaliero completo sul sito pubblico. Sul sito si possono mostrare grafici e totali per inverno/anno con citazione "NOAA NCEI, Integrated Surface Database e Global Summary of the Day, stazioni Milano Linate e Malpensa". Il punto "prodotti derivati" va deciso da Davide prima di pubblicare tabelle scaricabili.

#### 9. Cosa manca / da fare

- Una seconda fonte di verifica per la neve e la profondità (ARPA Lombardia, Osservatorio di Brera, Servizio Meteorologico AM): il progetto "temperature" ha già Brera per la temperatura.
- Informazioni ufficiali su quando Linate e Malpensa hanno cambiato strumenti di visibilità/tempo presente (non nei dati NOAA).
- Anni mancanti 1939-1950, 1962-1963, 1972; l'inverno 2026 (nov 2025 - mar 2026) non esiste ancora nei dati (ultimo giorno 24/08/2025).
- Non è stata fatta nessuna analisi di tendenza e nessun grafico (fase 2).

### Fase 2 — pagina (2026-10-30)

- Pagina `docs/neve-e-nebbia/`: si pubblicano solo conteggi derivati (WMO Resolution 40), mai le osservazioni grezze.
- Sei periodi dubbi (A-F, cambi nel modo di registrare il tempo) segnati in grigio su ogni grafico; regola di completezza: 90% dei giorni.
- Il legame con Brera è presentato come associazione, con la nota sul periodo 2008-2016.

## 14. I cinema spariti di Milano

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `cinema-spariti/`._

- 2026-10-30 — Filone chiesto da Davide (nella sua richiesta numerato 12; rinumerato perché 10-12 erano già occupati). Domanda: quante sale c'erano e dove, decennio per decennio; quando e dove sono sparite e cosa c'è al loro posto. Fonti: OSM (anche disused/was:amenity=cinema), Wikipedia, Wikidata, Comune; elenchi storici solo dopo averne verificato l'affidabilità. Nomi delle cartelle scelti da Davide ("cinema" diventa `cinema-spariti`). Fase 1: solo raccolta, poi un riassunto e la cosa più sorprendente prima di grafici e pagine.

### Fase 1 — raccolta (2026-10-30)

**NOTE - cinema scomparsi di Milano (fase 1)**
Data: 30/10/2026. Cartella: milano-in-dati\cinema-spariti. Nessun grafico, nessuna pagina.

#### Risultato in due righe
Abbiamo un elenco di 170 cinema milanesi chiusi (anni di apertura e chiusura, indirizzo) più 29 cinema aperti oggi (OpenStreetMap). Mancano i cinema che erano attivi nel passato e sono ancora aperti, le sale parrocchiali e il numero di sale dei cinema chiusi.

#### Fonti
1. **Elenco spazioCinema (Anteo)**. Pagina: https://www.spaziocinema.info/cinema/notizie/scegli-il-nome-delle-nuove-sale-di-anteo-tra-le-insegne-di-storici-cinema-milanesi ; PDF alla stessa pagina, link "at_download/programma". Scaricato 30/10/2026. File: raw\storiche\spaziocinema\programma.pdf (251 KB), tabella_grezza.csv (170 righe: campi sala, periodo, indirizzo). Periodo coperto: 1896-2017. Licenza: copyright Anteo, nessuna licenza aperta: il PDF non va ripubblicato. Trappola: il testo estratto "a righe" mescola le colonne, si legge bene solo con l'estrazione per tabella (script 05).
2. **OpenStreetMap (Overpass)**, estrazione del 29/10/2026 23:28 UTC, area del comune di Milano. File: raw\osm\cinema_attuali_e_storici.json (15 KB, 37 elementi), raw\osm\teatri.json (26 KB), raw\osm\oggi_vicino.json e oggi_vicino_grezzo.json (negozi e locali entro 30 m dai cinema chiusi). Campi: amenity, disused:amenity, screen (numero schermi), start_date. Trappola: solo 2 cinema "disused" e nessun "was:": OSM non ha la storia. Licenza ODbL (ripubblicabile citando OSM). Il file del settore 7 (bici-auto-mezzi) ha solo strade, quindi non usato.
3. **Wikidata (SPARQL)**, 30/10/2026. File: raw\wikidata\a_cinema_inMilano_P131.json (76 KB, 59 cinema), b_cinema_box.json (stessi 59), c_teatri_box.json (136 KB, 90 teatri). Campi: inception P571, dissolved P576, coordinate P625, indirizzo P6375. Trappola: l'anno di chiusura c'è per 1 cinema, l'apertura per 6. Licenza CC0.
4. **Wikipedia italiana (API)**, 30/10/2026. File: raw\wikipedia\categorie.json, wikitext.json (413 KB, 37 voci della categoria "Teatri di Milano"). Trappola: le categorie sui cinema di Milano non esistono. Licenza CC BY-SA.
5. **Comune di Milano, dati aperti (CKAN)**, 30/10/2026. File in raw\comune: ds157 (ingressi e spettacoli per tipo, 1995-2010, CSV 2 KB), ds252 (295 locali di pubblico spettacolo, CSV 62 KB, nessun cinema), ds59 (pubblici esercizi fuori piano, CSV 845 KB, non rilevante), _metadati.json. Licenza CC-BY. Trappola in ds157: anni 2004-2005 con campi vuoti.
6. **Nominatim (OSM)** per le coordinate: raw\storiche\geocode_nominatim.json (163 indirizzi, 12 senza risultato).
7. **Archive.org**: le guide "Milano Scelta" 1905 e 1907 (raw\storiche\archive_org, circa 2 MB l'una) quasi non parlano di cinema. Google Books: quota esaurita.

#### File puliti (cartella pulito)
- `cinema.csv` (203 righe): 170 dall'elenco, 29 cinema aperti solo da OSM, 4 solo da Wikidata. Campi: id, nome, altri_nomi, indirizzo, lat, lon, precisione_posizione, fonte_posizione, anno_apertura, anno_chiusura, apertura_incerta e chiusura_incerta (1 = data "circa"), periodi_attivita, periodo_testo_originale, n_sale (solo 15 cinema aperti con tag screen), stato_2026, wikidata, osm_id, cosa_c_ora, fonti.
- `elenco_spaziocinema_parsed.csv`, `conteggi_decenni_preliminari.csv`, `wikipedia_frasi_cinema.csv` (30 frasi), `fonti_valutate.md`.
- Posizione dei 170 cinema dell'elenco: 42 con coordinate Wikidata, 70 Nominatim con civico (da controllare), 46 solo via, 12 senza.
- `cosa_c_ora`: 93 candidati OSM (negozi o locali entro 30 m), da confermare a mano; mancano per gli altri.

#### Conteggi preliminari (cinema dell'elenco attivi a gennaio dell'anno; file conteggi_decenni_preliminari.csv)
1910: 23; 1920: 52; 1930: 82; 1940: 82; 1950: 98; 1960: 118; 1970: 110; 1980: 101; 1990: 50; 2000: 35; 2010: 4. Sono solo sale poi chiuse: vanno aggiunte quelle ancora aperte. Oggi (OSM 2026): 29 cinema.
Chiusure per decennio (fine dell'ultimo periodo): 1930: 20; 1940: 7; 1950: 3; 1960: 11; 1970: 21; 1980: 50; 1990: 17; 2000: 31; 2010: 4.

#### Cosa manca
- Cinema attivi nel passato e ancora aperti nel 2017; sale parrocchiali, arene, cinema a luci rosse non elencati; numero di sale storico.
- "Cosa c'è ora" confermato; coordinate esatte per 58 cinema.
- Verifica indipendente delle date (Wikidata deriva forse dalla stessa lista). Possibili aggiunte: CineMi (Roaro, fino al 1955), dati Anec, Google Books.

### Fase 2 — pagina (2026-10-30)

- Pagina `docs/cinema-spariti/`:
  - 171 sale chiuse: le 170 dell'elenco spazioCinema/Anteo 2017, più l'Odeon, chiuso nel 2023 anche se OSM lo dà aperto;
  - 28 cinema aperti oggi (OSM), di cui solo 7 con l'anno di apertura;
  - massimo di 123 sale attive nel 1960 (almeno).
- **Decisione di Davide**: pubblicare tutte le sale citando la fonte, sapendo che pubblicare l'intero elenco potrebbe contare come estrazione di una banca dati (diritto sui generis UE). Il coordinatore aveva consigliato di pubblicare solo i conteggi e le sale confermate da altre fonti. Il PDF e il testo dell'elenco non sono pubblicati. Se l'Anteo chiede di togliere i dati, si torna alla versione con conteggi e sale confermate.

## 15. Il derby Inter-Milan dal 1909

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `derby/`._

- 2026-10-30 — Filone chiesto da Davide (nella sua richiesta numerato 13; rinumerato perché 10-12 erano già occupati). Domanda: tutti i derby ufficiali con risultati, marcatori e competizione; epoche, serie più lunghe, effetto "casa" nello stesso stadio dal 1947. Almeno due fonti incrociate; amichevoli e campionati di guerra tenuti a parte. Nomi delle cartelle scelti da Davide ("cinema" diventa `cinema-spariti`). Fase 1: solo raccolta, poi un riassunto e la cosa più sorprendente prima di grafici e pagine.

### Fase 1 — raccolta (2026-10-30)

**NOTE - derby di Milano dal 1909 (filone 15, fase 1: solo raccolta e controllo)**

Cartella: `milano-in-dati\derby\`. Data del lavoro: 30 ottobre 2026. Nessun grafico, nessuna pagina, niente git.

#### Che cosa c'e' di pronto

| File | Che cosa contiene |
|---|---|
| `pulito\derby.csv` | una riga per partita giocata: 246 derby (244 ufficiali + 2 del campionato di guerra 1944). Colonne: id, data, stagione, competizione, turno, stato (ufficiale / `wartime_honorary`), squadra di casa e ospite (e il nome di allora: Ambrosiana, Ambrosiana-Inter, Milano), gol, vincitore, stadio, stadio neutro, arbitro, note sul risultato, quante fonti hanno controllato e quante concordano, `home_label_disputed` |
| `pulito\marcatori.csv` | una riga per gol: 663 righe (partita, squadra a cui va il gol, giocatore, minuto, autogol, rigore, club del giocatore) |
| `pulito\differenze.md` | tutte le differenze trovate tra le fonti (data, punteggio, casa, stadio, arbitro, marcatori) |
| `pulito\differenze_marcatori.csv` | stesso elenco dei marcatori, in forma di tabella |
| `pulito\non_ufficiali_riepilogo.csv` | le 72 partite non ufficiali: SOLO i totali per torneo (le singole partite non le ho trovate in fonti libere) |
| `pulito\_*.csv` | file intermedi (uno per fonte), si rigenerano con gli script |
| `scripts\01..12` | gli script (si rilanciano con `python -I`; ordine: 01, 02, 03, 04, 05, 06, 07, 08, 09, 11, 12, poi 10) |
| `raw\` | i file scaricati, intatti |

Totali (identici alla tabella riassuntiva di it.wikipedia): 246 derby ufficiali in senso largo = 91 vittorie Inter, 71 pareggi, 84 vittorie Milan; gol Inter 341, gol Milan 324.
Per competizione (derby / Inter-pari-Milan): Prima Categoria 14 (5-2-7); Divisione Nazionale 1926-28 e 1945-46 8 (3-1-4); Serie A 184 (70-57-57); Coppa Italia 29 (9-9-11); Supercoppa 3 (1-0-2); Champions League 6 (2-2-2); Campionato Alta Italia 1944 2 (1-0-1, stato `wartime_honorary`, riconosciuto solo a titolo onorifico).
Non incluse: la partita del 31 ottobre 2026 (domani, Serie A 2026-27) e quella di febbraio 2027, che it.wikipedia gia' elenca come "da giocare".

#### Le fonti (URL, data di scarico, file, periodo, licenza)

Scarico: 30 ottobre 2026. User-Agent con contatto, pause di 1-3 secondi, nessun login, nessuna registrazione.

1. **it.wikipedia, "Derby di Milano"** - API MediaWiki, revisione 153044197 del 24/10/2026. File `raw\wikipedia\it_Derby_di_Milano.json` e `.wiki` (203 KB). Lista completa dal 1909: data, stadio, competizione, squadra di casa, punteggio, marcatori (con minuto, rigori, autogol), arbitro, link al referto. Ho tolto le 2 partite future. **E' la spina dorsale** di `derby.csv`. Licenza CC BY-SA 4.0: si prendono solo i fatti (date, punteggi, nomi), non il testo; citare "Wikipedia, CC BY-SA".
2. **en.wikipedia, "Derby della Madonnina"** - revisione 1382484836 del 28/10/2026 (`raw\wikipedia\en_Derby_della_Madonnina.*`, 99 KB). Data, competizione con turno, casa, punteggio; note a pie' di pagina (partita sospesa 2005, supplementari 2017). Stessa licenza. E' un'altra pagina ma scritta dalla stessa comunita': non e' un controllo del tutto indipendente.
3. **35 pagine di edizione di it.wikipedia** (campionati 1909-1928, 1944, 1945-46; Coppa Italia; Supercoppa; Champions) in `raw\wikipedia\seasons\`. Dove c'e' il riquadro "Incontro di club" danno turno, stadio, arbitro, marcatori: 23 partite controllate (Coppa Italia 1958-2000 e Supercoppa).
4. **engsoccerdata** (James Curley) - `https://raw.githubusercontent.com/jalapic/engsoccerdata/master/data-raw/italy.csv`, 1,9 MB, 28.824 partite di Serie A 1929-30 / 2024-25 (186 derby). Licenza del pacchetto: GPL (>= 2) (file `raw\engsoccerdata\DESCRIPTION`). Uso solo come controllo; non ripubblicare il file grezzo. Tratta la Divisione Nazionale 1945-46 come Serie A; non ha le stagioni di guerra.
5. **football-data.co.uk** - 31 CSV 1993-94 / 2023-24 dalla copia `footballcsv/cache.footballdata` (CC0 per la copia) + 3 CSV 2024-26 direttamente dal sito (`raw\footballdata\`, 0,9 MB). **Attenzione ai termini del sito**: dati gratuiti ma "solo per privati, non per prodotti commerciali o di addestramento con bot/scraper/IA". Qui servono solo a controllare data e punteggio di 66 partite; non vanno ripubblicati e non fanno parte dei file finali.
6. **openfootball/italy** (CC0, pubblico dominio) - `https://github.com/openfootball/italy`, stagioni 2013-14 / 2026-27 (anche Serie B e C, scaricate per errore, inutili). 31 derby controllati (campionato 2013-26 + Coppa Italia 2020-25). Il file `2025-26_1-seriea-full.txt` ha marcatori con minuto e spettatori dei 2 derby 2025-26.
7. **RSSSF** (Rec.Sport.Soccer Statistics Foundation) - `https://www.rsssf.org/tablesi/ital{AA}.html`, 107 pagine di stagione dal 1925-26 + pagine Coppa dei Campioni (`raw\rsssf\`, 6 MB). robots.txt assente (404). Licenza: "libera copia citando RSSSF". Elenchi partita per partita con data della giornata e marcatori. Il mio programma non legge le pagine 2012, 2026, 81 e 83 (nel 1980-81 e 1982-83 il Milan era in B: niente derby). Pagine Champions League: confermano i 3 incroci.
8. **Almanacco nerazzurro di interfc.it**, copia di web.archive.org del febbraio 2017 (link nella colonna "Referto" di it.wikipedia): data, risultato, marcatori con minuto, arbitro delle partite ufficiali dell'Inter fino al 2000. Contenuto dell'Inter: serve solo come controllo dei fatti, non si ripubblica. Scaricate 149 pagine (circa 17 KB l'una) in `raw\interfc_archive\`, con pause di 3 secondi.
9. **Wikidata** (SPARQL, `raw\wikidata\`): provato, **non utilizzabile**. Le partite non sono modellate: ci sono solo le stagioni dei campionati, 3 finali di Coppa Italia/Supercoppa e un elemento "derby". Nessun dato partita per partita.
10. **footballcsv/italy**: nel repository ci sono solo la specifica del formato e la licenza (CC0), nessun dato.

#### Come concordano le fonti

Confronto partita per partita con la lista di it.wikipedia (dettaglio in `pulito\differenze.md`). Prima ho **corretto 4 voci di it.wikipedia** dove 3 fonti indipendenti da Wikipedia (engsoccerdata, RSSSF, Almanacco Inter) dicono la stessa cosa contro it.wikipedia ed en.wikipedia:
- 1931-03-19 -> 1931-03-15 (il 19 marzo 1931 era un giovedi', festa di San Giuseppe); 1948-10-16 -> 1948-10-17;
- 1955-10-16 e 1956-03-11: la squadra "di casa" era invertita in tutte e due (e i link "Referto" sono scambiati). Giusto: 16/10/1955 Milan-Inter 1-2; 11/3/1956 Inter-Milan 2-1.
Dopo le correzioni:
- **Almanacco Inter (archive.org)**: 149 partite (tutte le ufficiali dal 1909 al 27/1/2000 con link), 149 concordano su data, casa e punteggio. Differenze: 1 arbitro (1993-02-10), 3 minuti di gol.
- **engsoccerdata** (186): 177 identiche; 9 diverse: 4 con casa/ospite invertiti (1960-11-20, 1961-03-26, 1964-11-15, 1965-03-28) e 5 date (1948-04-15, 1963-11-03 invece del 1964-01-19, 1974-11-04, 1995-04-14, 2001-05-13).
- **RSSSF** (196 lette dal programma): 188 identiche; 8 diverse: 2 con casa invertita (1964-11-15, 1965-03-28) e 6 date (di giornata, vedi trappole).
- **football-data** (66): 65 identiche; 1 data (1995-04-14 invece del 15).
- **openfootball** (31): tutte identiche.
- **en.wikipedia** (246): 238 identiche; 8 diverse: le 2 partite 1955-56 (stesso errore di it.wikipedia) e 6 date diverse (1931-03-19, 1948-10-16, 1958-06-16, 1972-06-08, 1975-05-16, 1999-10-24).
- **Pagine edizione it.wikipedia** (23 Coppa Italia/Supercoppa): 22 identiche; 1 data (1972-06-08). Stadio: 1909-01-10 (Arena Civica contro Porta Monforte); arbitri scritti in modo diverso.
- **RSSSF Champions League**: i 6 punteggi confermati.
- Il punteggio e' concorde tra tutte le fonti su 240 partite su 246. Le 6 eccezioni sono solo di **etichetta casa/ospite** (il vincitore non cambia mai): le 2 del 1955-56 (en.wikipedia ripete l'errore di it.wikipedia, corretto sopra) e le 4 del 1960-61 e 1964-65: per il 1960-61 RSSSF e Almanacco stanno con it.wikipedia contro engsoccerdata; per il 1964-65 it.wikipedia, en.wikipedia e Almanacco Inter contro engsoccerdata e RSSSF (ho lasciato la versione di it.wikipedia). Colonna `home_label_disputed` = 1 se almeno una fonte discorda.
- **Marcatori**: i gol di it.wikipedia tornano col punteggio in tutte le partite (tranne la assegnata del 2005). Confronto con RSSSF, Almanacco e pagine edizione: 23 segnalazioni, quasi tutte differenze di 1 minuto; casi piu' grossi: 1946-05-30 (ultimo gol al 75' in Wikipedia, al 47' in RSSSF e Almanacco), 1956-10-21 (12' e 16' contro 17' e 17'), 1983-11-06, 1999-10-23. Non corretti, solo segnalati.

#### Trappole dei dati (da non dimenticare)

1. **"Casa" nel derby e' un'etichetta**: dal 1947 le due squadre dividono San Siro, e anche prima il calendario assegnava la "casa" a una delle due ma non sempre si giocava nel suo stadio (anni 1930-40: partite col Milan "di casa" all'Arena Civica). Per studiare l'effetto campo servono la colonna `venue` e le 6 partite con etichetta contestata (4 dopo le correzioni: 1960-11-20, 1961-03-26, 1964-11-15, 1965-03-28; piu' le 2 del 1955-56 gia' corrette).
2. **Stadi**: Campo Milan di Porta Monforte (6), Arena Civica (23), Campo di via Goldoni (5, campo dell'Ambrosiana), San Siro (208), 3 stadi esteri per le Supercoppe (`neutral_venue` = 1: Pechino 2011, Riad 2023 e 2025). La partita del 1909-01-10: it.wikipedia dice Porta Monforte, la pagina del campionato 1909 dice Arena Civica (differenza registrata). Una partita (1921-01-30) non ha lo stadio.
3. **Nomi**: Inter si chiama Ambrosiana (4 partite, 1929-31) e Ambrosiana-Inter (26 partite, 1931-44); il Milan si chiama Milano (10 partite, 1939-44). Colonne `home_club_name`, `away_club_name`.
4. **Partita assegnata a tavolino**: Inter-Milan 12/4/2005, Champions (quarti, ritorno). Sospesa al 73' sullo 0-1 per i fumogeni; UEFA ha dato 0-3. In `derby.csv` il risultato e' 0-3 (come nelle statistiche ufficiali, che sommano 246 partite e 341-324 gol), nei marcatori c'e' solo il gol vero (Sevcenko 30'). Per questo i gol in `marcatori.csv` sono 663 e non 665.
5. **Campionato Alta Italia 1944** (guerra, gironi regionali): riconosciuto solo a titolo onorifico. L'ho tenuto a parte: `status = wartime_honorary`, `official = 0`. Con lui il totale e' 246 come Wikipedia; senza, 244. RSSSF lo mostra come un solo incrocio con andata e ritorno e concorda.
6. **Interruzione 1915-1920**: nessun derby tra il 2/5/1915 (Prima Categoria) e il 19/12/1920. Poi nessuno fino al 3/4/1927; nel 1928-29 non si sono incontrati (nelle fonti non c'e' nessun derby).
7. **Stagioni**: "Coppa Italia 1958" e' l'edizione 1957-58 giocata a giugno-luglio 1958 (idem altre edizioni "estive" 1968, 1972, 1975, 1977, 1985). Nel campo `season` ho usato l'edizione. Il campionato 1909 e' una stagione solo (gennaio-aprile 1909).
8. **Tornei interrotti da piu' fasi** (Coppa Italia a gironi 1958, 1968, 1981...) hanno il turno in `round` (da en.wikipedia) e in `round_it_box` (dalle pagine edizione). Per il campionato di Serie A non ho il numero di giornata.
9. **Punteggi dopo supplementari/rigori**: solo il derby di Coppa Italia 27/12/2017 e' finito dopo i supplementari (1-0, gol di Cutrone al 104'); nei dati non risulta nessun derby deciso ai rigori.
10. **Marcatori**: i gol sono assegnati alla squadra che li ha segnati sul tabellino (autogol compresi: `team_credited`); `scorer_club` dice di che squadra era il giocatore. 14 gol del 1911-1914 non hanno minuto. `penalty = some` quando in una riga con piu' gol c'e' un solo rigore e non si sa quale. Gli accenti dei nomi (Sevcenko/Ševčenko) cambiano tra fonti.
11. **Date RSSSF**: RSSSF usa la data della giornata; partite spostate hanno data diversa. Le differenze di data della sola RSSSF non vanno considerate errori.
12. **engsoccerdata e 1945-46**: contiene i 4 derby della Divisione Nazionale 1945-46 come "Serie A" (livello 1); in `derby.csv` restano "Divisione Nazionale" come in it.wikipedia. Non ha le stagioni di guerra.
13. **football-data.co.uk**: termini d'uso restrittivi (solo privati). Tenerlo come controllo, non come fonte del sito.

#### Cosa manca

- Le **72 partite non ufficiali** (amichevoli, tornei minori, coppe di guerra, Mundialito, ecc.): ho solo i totali per torneo (`non_ufficiali_riepilogo.csv`), non le singole partite. Non esiste una lista libera e completa; servirebbe il PDF dell'almanacco di magliarossonera.it (fonte citata da Wikipedia) o altre ricerche.
- Il **numero di giornata** per le partite di campionato e il **turno** per la Coppa Italia delle prime edizioni.
- Punteggio/data senza nessun controllo indipendente da Wikipedia: le 3 Supercoppe (2011, 2022, gennaio 2025: solo it.wikipedia, en.wikipedia e la pagina dell'edizione). Tutto il resto ha almeno un'altra fonte non Wikipedia (Almanacco Inter fino al 27/1/2000, poi football-data, engsoccerdata, openfootball, RSSSF).
- Marcatori dal 2000 al 2025: oltre a it.wikipedia c'e' solo RSSSF (non in tutte le stagioni: mancano i minuti per molte partite 2012-2025) e le pagine edizione per alcune coppe. Sono quindi i meno controllati.
- I gol delle partite 2025-26 hanno come controllo il file `full` di openfootball (minuti concordano).

### Fase 2 — pagina (2026-10-30)

- Pagina `docs/derby/`: 246 derby (Inter 91, pareggi 71, Milan 84; gol 341-324). I 2 del 1944 sono contati come fa Wikipedia, con la nota "solo a titolo onorifico"; senza, i derby sono 244.
- Le partite non ufficiali sono 72 (non 73: Perth vale 1); compare solo il totale.
- Dati pubblicati con licenza CC BY-SA 4.0; i dati di football-data.co.uk sono usati solo per i controlli e tolti dai file pubblici.

## 16. Da chi prendono il nome le fermate

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `nomi-fermate/`._

- 2026-10-30 — Filone chiesto da Davide (nella sua richiesta numerato 14; rinumerato perché 10-12 erano già occupati). Domanda: da chi o da cosa prendono il nome le fermate della metro (e, se fattibile, di tram e bus principali): persone (donne e uomini, mestieri, epoche), luoghi, santi, eventi. Riusa il filone "donne nelle vie"; i casi incerti vanno segnalati. Nomi delle cartelle scelti da Davide ("cinema" diventa `cinema-spariti`). Fase 1: solo raccolta, poi un riassunto e la cosa più sorprendente prima di grafici e pagine.

### Fase 1 — raccolta (2026-10-30)

**NOTE - A chi sono intitolate le fermate (filone 16)**

Data del lavoro: 30/10/2026. FASE 1: raccolta e classificazione, nessun grafico, nessuna pagina.

#### Fonti usate

1. **Orari ATM (GTFS), gia' scaricati dal filone bici-auto-mezzi**
   File: `..\bici-auto-mezzi\raw\gtfs\ext_comune_new\` (stops.txt, routes.txt, trips.txt, stop_times.txt). Versione feed 425, dal 26/10/2026.
   Metro = route_type 1 (M1-M5), tram = route_type 0 (17 linee). Le fermate sono quelle servite da almeno una corsa.
   Risultati: `raw\metro_stops_gtfs.csv` (130 fermate fisiche -> 125 stazioni, perche' Duomo, Cadorna, Loreto, Lotto e Sant'Ambrogio hanno due fermate), `raw\tram_stops_gtfs.csv` (724 fermate, 341 nomi diversi).
   Licenza: dati del Comune/ATM, gia' valutata dal filone bici-auto-mezzi; qui non si ripubblica il file grezzo.
2. **Wikidata (SPARQL, query.wikidata.org), 30/10/2026**
   Stazioni metro nel riquadro di Milano con la proprieta' "intitolato a" (P138): `raw\wd_metro_stations.csv` (250 KB). Poi due-tre salti lungo la catena stazione -> via/piazza -> persona/luogo: `raw\wd_hop2.csv`. Mestieri delle persone: `raw\wd_persone.csv`. Santi: `raw\wd_santi.csv`.
   Licenza: CC0 (si puo' ripubblicare).
3. **donne-nelle-vie (filone 2)**, solo lettura: `strade_classificate_arricchite_v2.csv` (4.278 vie, categoria uomo/donna/non_persona, mestieri, anni) e `decisioni_davide.csv`. Serve per controllare le persone delle stazioni e per classificare i tram.
4. **OpenStreetMap (Overpass)**: provato due volte, il server ha risposto 502 e poi e' andato in timeout. Saltato. Non cambia molto: il filone 2 usa gia' i tag OSM "name:etymology:wikidata" per le vie (campo `fonte` = tag_osm).

#### Come ho classificato (metro) - script `scripts\06_build_metro.py`

- Il nome della stazione si collega, con Wikidata, alla via/piazza/luogo da cui prende il nome. Da li si scende fino alla persona (es. Pasteur: stazione -> via Luigi Pasteur -> Louis Pasteur).
- Si scende solo attraverso vie, piazze, porte e stazioni ferroviarie. Non si scende da quartieri, comuni, edifici (Duomo resta "edificio", non diventa "festa dell'Assunta").
- Categorie: persona (uomo/donna, mestiere, anni), santo/santa, luogo (comune, quartiere, citta', regione/stato, natura), evento/data, edificio/istituzione, altro.
- Il mestiere e il gruppo di mestiere vengono da donne-nelle-vie quando la via c'e', altrimenti da Wikidata. Il "gruppo di mestiere" e' una regola a parole chiave sulla descrizione (la prima professione citata).
- Pochi casi a mano, tutti in `scripts\override_metro.json` e tutti segnalati: santi (Wikidata non ha la persona), stazioni senza dati Wikidata (Comasina, Cassina de' Pecchi, Cascina Burrona, ecc.), nomi doppi (Lodi T.I.B.B., Sforza-Policlinico, Sesto 1 Maggio).
- Ogni dubbio e' in `pulito\da_verificare.csv` (27 stazioni). Niente e' stato deciso in silenzio.

#### Come ho classificato (tram) - script `scripts\09_build_tram.py`

- Le fermate tram sono incroci ("via Farini v.le Stelvio"): ho separato le strade e abbreviazioni (v.le, p.za, s., l.go...). Ogni strada e' una riga (375 denominazioni). `n_fermate` = quante fermate fisiche la contengono.
- Abbinamento col registro vie del filone 2: nome uguale (con iniziali), poi parte finale del nome ("via meda" = Giuseppe Meda), poi parte iniziale solo se unica. Il metodo usato e' scritto in `registro_via`.
- Per i "non persona" uso il motivo scritto dal filone 2 (luogo su Wikidata, data/evento, parola chiave): quindi "luogo/altro" e' una categoria larga, non distingue edifici da luoghi.
- Nomi senza tipo di via (Teatro alla Scala, Stazione Centrale, ecc.): stessa classificazione della stazione metro con lo stesso nome oppure parola chiave.
- Fermate nei comuni vicini (Rozzano, Cinisello, Sesto) non sono nel registro di Milano: restano "fuori Milano (non classificato)".
- Dubbi in `pulito\da_verificare_tram.csv` (79 righe).

#### Trappole dei dati

- Le fermate GTFS delle stazioni hanno nomi doppi (DUOMO M1 / DUOMO M3) e sigle (P.TA GENOVA F.S., VILLA S.G.): ho unito le fermate della stessa stazione. Una stazione serve piu' linee: la colonna `linee` le elenca.
- La stazione e' intitolata a una via/piazza, che e' a sua volta intitolata a qualcuno. "Cadorna" = piazzale Luigi Cadorna = il generale (persona), non un luogo.
- Wikidata sbaglia o e' incerto in alcuni punti: Dateo ha la data di morte 878 (dubbia), Romolo e' una figura leggendaria, la via della Moscova e' collegata al fiume ma ricorda la battaglia, le descrizioni in italiano mancano spesso.
- **Il filone 2 ha tre vie che non risultano persona ma lo sono**: piazza Simone Bolivar (Simon Bolivar), piazzale Dateo (arcivescovo), viale Romolo (leggendario, dubbio). Segnalo per eventuale correzione di donne-nelle-vie (non l'ho toccato).
- Santa Sofia: potrebbe essere la martire romana oppure la Sapienza divina; sesso e identita' da confermare.
- Ogni fermata "da santo" ma che indica un quartiere (San Siro, San Leonardo, San Donato, Villa San Giovanni) l'ho messa in "luogo" e non in "santo", con nota.
- Sul tram il registro vie ha anche vie con "cognome" (es. Cusani, Tibaldi, Negroli): probabili persone, ma non identificate. Sono in "non classificato".
- I conteggi per "persona" contano le stazioni, non i passeggeri.

#### File prodotti (cartella `pulito\`)

- `fermate_metro_nomi.csv` - 125 stazioni (stazione, linee, categoria, sottocategoria, riferimento diretto, intitolato a, persona, sesso, mestiere, gruppo di mestiere, nascita-morte, QID, fonte, confidenza, controllo con filone 2, note, da verificare)
- `da_verificare.csv` - 27 stazioni dubbie
- `fermate_tram_nomi.csv` - 375 denominazioni di strade/luoghi sulle fermate tram
- `da_verificare_tram.csv` - 79 righe dubbie
- `riepilogo.json` - conteggi

#### Come rifare tutto

`cd nomi-fermate` poi `python -I scripts\01_metro.py raw\metro_stops_gtfs.csv` (come da STATO.md), poi 02, 03, 03b, 05, 07 (Wikidata), poi `06_build_metro.py`, `08_tram_stops.py raw\tram_stops_gtfs.csv`, `09_build_tram.py`, `10_riepilogo.py`.

### Fase 2 — decisioni e pagina (2026-10-30)

- Decisioni di Davide sulle 27 stazioni dubbie: tutti i consigli del coordinatore (`pulito/decisioni_davide.csv`, applicate da `scripts/11_applica_decisioni.py`).
  - Località come luogo.
  - Argonne, Coni Zugna, Moscova, Repubblica, Sesto 1° Maggio come evento.
  - Bolivar, Dateo, Inganni, Sforza come persona.
  - Romolo come persona leggendaria.
  - Santa Sofia come santa.
  - Cordusio e Tre Torri come edificio.
  - Gelsomini e Tricolore come altro.
- **Risultato**: tra le 33 persone reali c'è una sola donna (Veronica Gambara, M1) e ci sono 32 uomini. 5 santi e Romolo sono contati a parte. Su 125 stazioni, 33 (26,4%) ricordano una persona reale.
- Tram: le 79 righe incerte restano "da verificare". Pagina `docs/nomi-fermate/` pubblicata.

## 17. Dove vanno i soldi del Comune

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `bilancio-comune/` (nome scelto da Davide)._

- 2026-10-30 — Filone chiesto da Davide (nella sua richiesta numerato 15). Domanda: come spende Milano, voce per voce, e come è cambiato; quanto per abitante.
- **Regole**:
  - Distinguere sempre la previsione dal consuntivo.
  - Costruire la corrispondenza tra le voci prima e dopo la riforma 2015-16.
  - Dare i valori a prezzi costanti e per abitante, e mostrare anche le entrate.
  - Nessun giudizio sulla spesa.
  - Anni più vecchi (OpenBilanci, BDAP): prima dire a Davide se vale la pena.

### Fase 1 — raccolta (2026-10-30)

**Filone 17 - Dove vanno i soldi del Comune (FASE 1: raccolta e controlli)**

Scaricato il 29-30 ottobre 2026. Niente grafici, niente pagine, nessun giudizio sulla spesa. Tutti gli script sono in `scripts/` (si lanciano da questa cartella con `python -I scripts/<nome>.py`). Dati grezzi in `raw/`, tabelle pulite in `pulito/`.

#### 1. Cosa c'e' (in breve)

- **Bilancio del Comune di Milano, anni di rendiconto 2015-2025** (11 anni) a livello di singolo capitolo, con missione e programma per le uscite. Dieci "edizioni" (dataset), una per anno, ognuna con 2 anni di rendiconto + 3 anni di previsione.
- **Anni 2012, 2013**: solo spesa corrente (2012 a programma, 2013 piu' dettagliato) e, per il 2013, entrate correnti. **2014: manca il consuntivo** (c'e' solo una previsione di febbraio 2014).
- **Prima del 2012**: non sul portale del Comune. Esiste per via diversa (vedi punto 5): Ministero dell'Interno dal 1998.
- **Licenza**: tutti i dataset del Comune sono CC-BY 4.0 ("Creative Commons Attribution" nel catalogo). Si possono ripubblicare citando la fonte (Comune di Milano, dati.comune.milano.it). Quindi anche i file grezzi si possono ripubblicare.

#### 2. Fonti e file (ogni dato dice il suo file)

Tutte le fonti del Comune sono su `https://dati.comune.milano.it/api/3/action/package_search?q=...` (CKAN). Ricerca fatta con 21 parole chiave (bilancio, rendiconto, spesa, entrate, PEG, missioni, tributi, sanzioni...), 687 dataset trovati in tutto; elenco in `raw/search_all.json`. Tutto in `pulito/inventario.csv` (39 righe).

| id | cosa | anni | dettaglio | file in raw/ |
|---|---|---|---|---|
| ds397 | Bilancio comunale, rendiconto 2015-16 e previsioni 2017-19 | rend. 2015, 2016 | capitolo PEG | ckan_ds397 |
| ds396 | idem, rendiconto 2016-17, previsioni 2018-20 | rend. 2016, 2017 | capitolo | ckan_ds396 |
| ds399 | idem, 2017-18, previsioni 2019-21 | rend. 2017, 2018 | capitolo | ckan_ds399 |
| ds400 | idem, 2018-19, previsioni 2020-22 | rend. 2018, 2019 | capitolo | ckan_ds400 |
| ds401 | idem, 2019-20, previsioni 2021-23 | rend. 2019, 2020 | capitolo | ckan_ds401 |
| ds1936 | idem, 2020-21, previsioni 2022-24 | rend. 2020, 2021 | capitolo | ckan_ds1936 |
| ds2352 | idem, 2021-22, previsioni 2023-25 | rend. 2021, 2022 | capitolo | ckan_ds2352 |
| ds2738 | idem, 2022-23, previsioni 2024-26 | rend. 2022, 2023 | capitolo | ckan_ds2738 |
| ds2956 | idem, 2023-24, previsioni 2025-27 | rend. 2023, 2024 | capitolo | ckan_ds2956 |
| ds3013 | idem, 2024-25, previsioni 2026-28 (aggiornato 21/8/2026) | rend. 2024, 2025 | capitolo | ckan_ds3013 |
| ds227 | Bilancio trasparente: spesa corrente per missioni e programmi | consuntivo 2012; assestato 2013; previsione 2014 | missione/programma (solo nomi) | ckan_ds227 |
| ds284 | PEG spese correnti, consuntivo 2013 | 2013 | titolo/macroaggregato/missione/programma/centro di costo | ckan_ds284 |
| ds285 | PEG entrate correnti, consuntivo 2013 | 2013 | titolo/tipologia/voce | ckan_ds285 |

Ogni dataset ha CSV + JSON (i piu' recenti anche ODS). Scaricati tutti: 102 MB circa per questi 13. I JSON e gli ODS sono copie degli stessi dati, non servono.

**Altri file scaricati (utili ma secondari):**
- SIOPE spese del Comune: 2017 e 2018 (annuale), poi 62 file mensili da settembre 2019 a luglio 2025 (`raw/ckan_siope_spese/`, `raw/ckan_ds738`, `ckan_ds739`). Sono PAGAMENTI (cassa) per codice SIOPE (natura economica), NON per missione. Servono solo come controllo. **Mesi che nel catalogo non esistono**: nov 2019, feb-mar-apr 2020, set-ott 2020, giu 2023, ago 2023, dic 2023; niente dopo luglio 2025 (cercati uno per uno, non trovati). Le colonne cambiano da un file all'altro (`importo_2017`, `imp_uscite_att`...).
- ds478 (pernottamenti con imposta di soggiorno, non euro), ds312 (addizionale IRPEF dovuta per anno d'imposta), ds697 (incassi PagoPA), ds633 (bilancio partecipativo: NON e' il bilancio del Comune, da ignorare).
- Popolazione: `raw/ckan_pop/` (ds71, ds73).
- Indici prezzi NIC di Milano per gruppi di spesa: `raw/ckan_nic/` (ds240, ds241, ds1431, ds2977). **Non hanno la riga "indice generale"**: per deflazionare conviene l'indice nazionale FOI gia' scaricato dal filone 12 (vedi punto 6).

#### 3. Come e' fatto il dato del Comune (colonne, unita')

Colonne comuni alle dieci edizioni: Tipo (ENTRATE/USCITE); PDC-Missione, PDC-Programma (solo uscite); PDC-Livello1..4 (per le uscite: titolo, macroaggregato...; per le entrate: titolo, tipologia, categoria, IV livello) con descrizioni; Centro di costo; Capitolo (+ Articolo, Numero fino a ds2956); Centro di responsabilita'; **due colonne Rendiconto, tre Stanziamento, una Stanziamento di cassa**; Direzione. Importi in euro (non migliaia). Ogni riga e' un capitolo di bilancio: ~5.200-6.700 righe per edizione (ds1936: 6.699; ds3013: 5.183).

**Prevision vs consuntivo - come l'ho separato.** Nelle tabelle pulite c'e' sempre la colonna `fase`:
- `consuntivo` = colonne "Rendiconto" (misura `rendiconto`; per le entrate sono accertamenti, per le uscite impegni - il dataset non lo dice, lo deduco dal fatto che nelle entrate il totale supera le uscite di 0,5-0,9 miliardi e dal confronto col Ministero, vedi sotto);
- `previsione` = colonne "Stanziamento" (misura `stanziamento_competenza`) e "Stanziamento di cassa" (misura `stanziamento_cassa`, solo primo anno);
- colonna `anni_dopo_ultimo_rendiconto` (1, 2, 3) dice quanto lontano e' lo stanziamento.
- colonna `da_usare` = 1 sulle righe consigliate per non contare due volte la stessa cosa (rendiconto: edizione piu' recente che contiene quell'anno; previsione: solo il primo anno di stanziamento).

#### 4. Tabelle pulite (cartella `pulito/`)

- `spesa_missioni.csv` (8.826 righe): anno, fase, misura, titolo di spesa (1 correnti, 2 conto capitale, 3 attivita' finanziarie, 4 rimborso prestiti, 5 anticipazioni, 7 conto terzi), missione, programma, importo in euro. Contiene anche ds227 (2012-2014) e ds284 (2013) con i codici ricostruiti dai nomi. Separatore `;`, punto decimale. **Per "quanto spende il Comune" filtrare titolo = 1 (spese correnti) e/o escludere titolo 7 (partite di giro).**
- `entrate.csv` (5.690 righe): anno, fase, titolo/tipologia/categoria/IV livello con descrizioni, importo. Per il 2013 (ds285) i livelli numerici sono -1 e ci sono solo i nomi.
- `bilancio_capitoli.csv` (245 mila righe, 33 MB): tutti i capitoli con importo diverso da zero, entrate e uscite, tutte le edizioni - serve per cercare voci precise (Area C, multe, ...). Descrizione capitolo come nel dato.
- `inventario.csv`: tutte le risorse, con anni, fase, dettaglio, unita', codifica, formato numeri, licenza, URL.
- `controllo_coerenza.csv`: i controlli del punto 7.
- `corrispondenza_funzioni_missioni.csv`: vecchia classificazione (DPR 194/1996) -> nuova (D.Lgs. 118/2011), a mano, con "1:1 / 1:n / n:1 / nessuna".
- `popolazione_milano.csv`: abitanti per anno (due definizioni, vedi sotto).
- `indice_prezzi_annuo_FOI_da_strand12.csv`: copia (non modificata) dal filone 12.

**Entrate che interessano alla domanda (livello capitolo, in `bilancio_capitoli.csv`, rendiconto in milioni di euro):**
- Area C (capitolo "PROVENTI DA ZTL AREA C"): 2016 64,6; 2019 65,7; 2023 57,6; 2025 33,7. Dal 2023 compare anche "PROVENTI DA ZTL - NUOVA TARIFFAZIONE ACCESSO AL CENTRO STORICO" (1,7; 1,0).
- Sanzioni codice della strada: 2016 556,6; 2019 487,9; 2023 488,1 (+33,4 "esercizi precedenti"); 2025 260,8 (+33,6). Nel 2013 (ds285) "AMMENDE PER CONTRAVV." 410,5. Il nome del capitolo cambia quasi ogni anno: **per le serie storiche serve un elenco di capitoli equivalenti, da fare in fase 2**.
- "Recupero spese postali notifica verbali" 2016 60,3; 2023 92,7; 2025 39,5 (e' un'entrata per rimborso spese, non una multa).
- Imposta di soggiorno: 2016 82,8; 2019 118,2; 2023 125,3 + 2,7; 2025 114,0 + 0,1.
- Tributi, trasferimenti, extratributarie: livello titolo/tipologia in `entrate.csv`.

#### 5. Anni piu' vecchi: verdetto

**Conviene? Si', ma con il Ministero dell'Interno, non con OpenBilanci.** Da decidere con Davide.

1. **Ministero dell'Interno - Finanza locale - "Certificati Consuntivi"** (`finanzalocale.interno.gov.it/apps/floc.php/certificati/index/codice_ente/1030491450/cod/4/anno/ANNO/md/0/cod_modello/CCOU/tipo_modello/U/cod_quadro/QUADRO`, codice ente di Milano = 1030491450). Accesso libero senza login, ma e' **una pagina HTML per anno e per quadro**, nessun file da scaricare in blocco. Provato: Milano ha dati dal **1998** (1996 = "dati assenti"; 1997 non provato) al 2015 almeno. Quadro 3 = riepilogo spese per titolo (impegni, pagamenti); Quadro 4 = spese correnti per **funzione e servizio** x **intervento** (personale, beni, servizi, trasferimenti, interessi...); Quadro 5 = investimenti. Scaricate 8 pagine di prova in `raw/ministero_interno_campione/`.
   - Controllo: Titolo I 2013 = 2.615.331.335,35 euro = esattamente la somma di ds284. Titolo I 2015 = 2.793.159.486,27 = ds397 (2.793,2 M). Quindi i due mondi si agganciano.
   - 2014 (anno mancante nel Comune): Titolo I impegni 2.626,9 M; 2012: 2.505,3 M (ds227 dice 2.443,7 M: 61,6 M di differenza, da capire).
   - Licenza: la pagina non dice nulla. E' dato pubblico del Ministero, ma **da chiedere/verificare prima di ripubblicare i file grezzi**; i numeri si possono citare con la fonte.
   - Costo per fare tutta la serie: circa 18 anni x 3-4 quadri = ~70 pagine; con pause educate e' una mezz'ora.
2. **BDAP Open Data** (`bdap-opendata.rgs.mef.gov.it`, CKAN anche questo, licenza CC-BY). Ha dataset "20NN - Regione - Gestione finanziaria Entrate/Spese Enti Locali" per **2013, 2014, 2015 soltanto** (vecchia classificazione), un file per regione e anno: la Lombardia entrate pesa 46 MB per anno (Milano = 96 righe). **Le SPESE della Lombardia non ci sono** (19 regioni su 20), le entrate si'. Quindi: per le entrate 2013-2015 va bene (con risorsa per risorsa: ad es. 2013 Codice della strada 408,2 M, TPL 376,4 M, addizionale IRPEF 177,4 M, tutto coerente con ds285), per le spese no. Dal 2016 in poi i rendiconti armonizzati non sono su questo CKAN (c'e' un altro portale `openbdap.rgs.mef.gov.it`, a interfaccia web, non verificato). Scaricato: solo l'estratto di Milano 2013 (`raw/bdap_campione/entrate_2013_MILANO_estratto.csv`). Il file della Lombardia intero l'ho tenuto solo in streaming e cancellato.
3. **OpenBilanci** (Openpolis): non ha API pubblica (`/api/` = 404); riporta gli stessi certificati del Ministero (dichiarato nella pagina licenze); serie vecchia fino al 2015, nuova classificazione dal 2016; copertura dichiarata 2005-2022 (preventivi), consuntivi fino al 2021. **Licenza CC BY-NC-SA 4.0**: non commerciale e "condividi allo stesso modo" - scomoda per un sito. Verdetto: non serve, il Ministero e' la fonte originale e dal Ministero si ha di piu'.

#### 6. Denominatori

- **Abitanti**: Comune di Milano ds71/ds73 = "popolazione calcolata ISTAT" a fine anno, 1880-2024 (**manca il 2025**). `pulito/popolazione_milano.csv` mette accanto la somma dei quartieri dell'anagrafe (ds205, del filone 15 minuti, letta senza modificarla). **Trappola: le due serie non coincidono** (2012: 1.263.087 calcolata vs 1.366.409 anagrafe, differenza 103 mila perche' la serie "calcolata" ha la rottura del censimento 2011; 2024: 1.365.698 vs 1.407.044). BDAP riporta per il 2013 "Popolazione ISTAT" = 1.345.851, che nel file del Comune e' il valore del 2015: serie ancora diversa. Per il "pro capite" bisogna scegliere una definizione e dirlo. Per il 2025 si puo' prendere ISTAT (demo.istat.it) quando serve.
- **Prezzi**: `indice_prezzi_annuo_FOI_da_strand12.csv` = FOI (famiglie operai e impiegati) senza tabacchi, Italia, medie annue 1996-2025 raccordate tra le basi, 2025 = 100 (es. 2015 = 82,372; 2025 = 100). Fatto dal filone 12, non rifatto. E' nazionale, non di Milano.

#### 7. Controlli di coerenza (dettaglio in `pulito/controllo_coerenza.csv`)

1. **Stesso anno di rendiconto in due edizioni**: per 2016-2023 i valori sono identici capitolo per capitolo (differenza 0,00 euro, totali di entrate e uscite uguali). Per il **2024** i totali sono uguali (uscite 4.401,6 M; entrate 4.960,7 M) ma l'edizione 2024-2028 ha rinumerato tutti i capitoli (3.059 su 5.263 diversi) e ha spostato **90,4 M da 12/1 (Infanzia, minori, nidi) al nuovo programma 12/11 (Asili nido)**. Quindi 12/1 + 12/11 vanno sommati per avere continuita'.
2. **Pareggio delle previsioni**: in ogni edizione e anno, stanziamento entrate = stanziamento uscite (differenza 0,0 M). Quindi i totali previsti (6-11 miliardi) comprendono tutto, anche prestiti, fondi, partite di giro, anticipazioni.
3. **Previsione contro consuntivo (solo titolo 1, spese correnti)**: la previsione del primo anno e' sempre sopra il consuntivo: es. 2017 previsione 3.161 vs consuntivo 2.679; 2025 3.711 vs 3.209 (milioni). Dentro la previsione ci sono accantonamenti (fondo crediti di dubbia esigibilita' ecc.) e capitoli non impegnati. **Non vanno confrontati come se fossero la stessa cosa.**
4. **Stesso anno di previsione in edizioni diverse**: cambia molto (es. uscite 2022: 6.472 M nell'edizione 2018-22, 11.629 M in 2019-23, 10.266 M in 2020-24). Il "terzo anno" di ogni edizione e' una cifra di programmazione, non confrontabile con il resto. Usare solo il primo anno (flag `da_usare`).
5. **ds227 (milioni) vs ds284 (euro) per il 2013**: spesa corrente "assestato" 2.911,0 M (include 338,8 M di fondo svalutazione crediti) contro impegni a consuntivo 2.615,3 M. Coerente se si toglie il fondo (2.572 M, 43 M sotto: non e' lo stesso istante). In ds227 il TOTALE di ogni missione e il TOTALE generale quadrano con la somma dei programmi (differenza 0,00).
6. **PEG vs Ministero**: Titolo I 2013 e 2015 coincidono (punto 5). Il Ministero parla di "spese correnti al netto della spesa per alimentazione del fondo di solidarieta' comunale (FSC)" per 2013-2015: il trattamento del FSC cambia nel tempo, da verificare nei PEG.

#### 8. Trappole dei dati (da non dimenticare)

1. **Formati dei numeri diversi per edizione**: ds397, ds396, ds399, ds400 usano "3.800.930,47" (punto migliaia, virgola decimale); ds401 usa "19,406.40" (virgola migliaia, punto decimale); ds1936 e successive "12222.22". ds399 ha "-" al posto di zero; ds396 ha celle di soli spazi (8.251). Parsing per file in `scripts/common.py`. Letto male = errori di 1000x.
2. **Codifiche diverse**: ds397, ds399, ds400, ds227, ds284, ds285 sono cp1252/ASCII; ds396, ds401 e le piu' recenti UTF-8. In ds227/ds284/ds285 accenti e apostrofi sono persi ("COMPETITIVIT+", "MOBILITA").
3. **Intestazioni delle colonne cambiano ogni anno** ("RENDICONTO 2015", "Rendiconto 2024", "STANZIAMENTO  2018" con doppio spazio, " RENDICONTO 2016 " con spazi in ds396; ds401 ha "ASSESTATO DI CASSA" senza anno; ds3013 ha 27 colonne, non 29).
4. **Codici di missione/programma scritti "1" o "01"** a seconda dell'edizione: vanno convertiti in numeri (fatto).
5. **Il rimborso dei prestiti (Titolo 4) e' distribuito su molte missioni**: nel rendiconto 2015 la missione 10 (trasporti) vale 1.324 M con tutti i titoli, ma solo 952 M di spese correnti (Titolo 1); 90 M sono rimborso prestiti (Titolo 4), nel 2025 99 M. Dal 2018 compare anche la missione 50 "Debito pubblico" che raccoglie solo una parte del Titolo 4 (41 M nel 2018, 31 M nel 2023, 109 M nel 2025 su 279 M di Titolo 4 totale). **Per sapere "quanto va ai trasporti" usare il Titolo 1 (e il Titolo 2 per gli investimenti), non il totale della missione.**
6. **Missione 99 (conto terzi/partite di giro)** vale 280-624 M all'anno e salta a 623,7 M nel 2023 (era 280,6 M nel 2022 e 357,2 M nel 2024). Non e' spesa del Comune.
7. **I totali di spesa del rendiconto cambiano di molto nel tempo** (4,0 miliardi 2015 -> 4,7 miliardi 2025) ma includono capitale, prestiti e partite di giro: per le serie da chiamare "spesa" usare spese correnti (Titolo 1: 2,8 -> 3,2 miliardi).
8. **Riclassificazioni possibili tra anni consecutivi** (non verificate): a rendiconto missione 1 sale da 285 M (2018) a 337 M (2019) e missione 3 scende da 216 a 177 M; la missione 14 (sviluppo economico) scende da 96 M (2015) a 14 M (2016) nel Titolo 1. Probabilmente cambio di assegnazione di costi (personale, trasferimenti) non cambiamento di spesa: controllare prima di commentare.
9. **Programmi che compaiono o spariscono**: 12/11 "Asili nido" ha importi solo nell'edizione 2024-2028 (88,3 M nel 2024, 90,8 M nel 2025, in Titolo 1), mentre 12/1 scende di conseguenza; 10/1 (ferroviario) e 10/4 (altre modalita') esistono come codici solo in alcune edizioni ma senza spese correnti; 12/5, 17/1, 20/3 hanno importi quasi nulli. Per l'elenco dei programmi per edizione vedere `pulito/spesa_missioni.csv`.
10. **Il "rendiconto" non e' denominato come tipo di dato**: le tabelle non dicono se sono impegni/accertamenti o pagamenti. Il confronto col Ministero (impegni) quadra al centesimo per il Titolo 1 2013 e 2015, quindi sono impegni/accertamenti di competenza.
11. **Il primo stanziamento di ogni edizione non e' dichiarato come "iniziale" o "assestato"**: l'edizione e' pubblicata a primavera dell'anno dopo il rendiconto, senza data di riferimento. Per il 2013 ds227 dice esplicitamente "assestato"; per il 2014 "al 27/02/2014".
12. **Il solo anno 2012 in ds227** ha 61,6 M in meno del Ministero (2.443,7 vs 2.505,3): non spiegato.
13. **Date di aggiornamento**: ds397 (2019), ds396 (2018/2022 JSON), alcuni JSON piu' recenti dei CSV: CSV e JSON potrebbero non coincidere. Ho usato i CSV.
14. **Le tabelle non hanno la "Direzione" stabile**: ds3013 ha codici tipo "2_C", prima codici "DIR14"; la riorganizzazione degli uffici impedisce confronti per direzione.
15. **Popolazione**: due definizioni e una rottura nel 2012 (punto 6).
16. **Pro capite 2025**: manca la popolazione del 2025 in ds71/ds73.

#### 9. Cosa manca / cosa resta da decidere

- Consuntivo **2014** per missione: solo dal Ministero (Quadro 4, per funzioni vecchie) o dal PEG 2014 non pubblicato come dato aperto.
- Anni 2012-2013: solo spesa corrente (e 2013 entrate correnti); niente spese in conto capitale nelle fonti del Comune.
- Anni prima del 2012: decidere se fare la raccolta dal Ministero (70 pagine HTML) - con la corrispondenza vecchio/nuovo in `corrispondenza_funzioni_missioni.csv`: molte righe sono 1:1 o n:1, ma **non esiste una corrispondenza 1:1 per**: personale (interventi vs macroaggregati), assistenza/beneficenza (si spezza in 5-6 programmi), biblioteche/musei, anagrafe/statistica, farmacie e servizi produttivi, affissioni e pubblicita', e per le voci nuove (fondi, debito, giovani, lavoro, sicurezza urbana). Inoltre dal 2015 cambia il metodo di contabilizzazione (competenza finanziaria potenziata): le spese in conto capitale (3,0 miliardi di impegni nel 2008, 0,75 nel 2015) non sono confrontabili.
- Popolazione 2025.
- Elenco dei capitoli equivalenti per le serie storiche di multe, Area C, sosta, imposta di soggiorno.


## 18. L'acqua del rubinetto, zona per zona

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `acqua-del-sindaco/` (nome scelto da Davide)._

- 2026-10-30 — Filone chiesto da Davide (nella sua richiesta numerato 16). Domanda: com'è l'acqua nelle diverse zone MM (durezza, minerali, nitrati), nelle stagioni e negli anni; più le perdite della rete.
- **Regole**:
  - I valori sotto soglia ("<0,05") restano "sotto soglia".
  - Gli accenti rovinati si correggono e si annotano qui.
  - L'acqua sotto i limiti di legge è acqua a norma: le differenze tra zone non vanno presentate come rischi.
  - Servizio "scrivi il tuo indirizzo" con i civici aggregati per zona.

### Fase 1 — raccolta (2026-10-30)

**NOTE - L'acqua del sindaco, zona per zona (fase 1: raccolta e controllo)**

Data di lavoro: 30 ottobre 2026. Nessun grafico, nessuna pagina. Tutto in locale, niente git.
Regola di tono: se un valore e' sotto il limite di legge, l'acqua e' conforme. Mai linguaggio di rischio.

#### 1. Le fonti (tutte dal portale dati.comune.milano.it, CKAN, senza login)

Ricerca fatta con l'API `package_search` (parole: "analisi dell'acqua", "trimestre", "perdite", "acquedotto", "potabile", "rete idrica") e con `package_list` (2.611 dataset in tutto). Ho scaricato 15 dataset = 30 file (CSV + JSON di ognuno, il JSON di ds1827 e' uno zip), totale 13,3 MB in `raw\<dataset>\`. Elenco con dimensioni e licenze: `pulito\inventario_fonti.csv`; elenco grezzo: `raw\_inventario.json`. Comando per rifare: `scripts\01_scarica.py`.

| Dataset (CKAN) | Che cosa contiene | Periodo | File (byte) |
|---|---|---|---|
| ds1828, ds1829, ds1861, ds1915, ds1948, ds2970 "Analisi dell'acqua 2021 ... 2026" | un valore per parametro, zona MM, mese (colonne `parametroMisurato, limitiLegge, valoreRilevato, unitaMisura, zonaNome, zonaId, mese, anno, dataCaricamento, info`) | gen 2021 - set 2026 (67 mesi su 69 attesi, vedi sotto) | CSV da 142.791 a 215.103 byte, 576-864 righe ciascuno |
| ds679 (4T 2018), ds737 (2T 2019), ds712 (4T 2020), ds1586/1605/1646/1670 (1T-4T 2021) "Ambiente: Analisi dell'acqua N trimestre" | un solo valore per parametro per tutta Milano ("Acqua di Milano"), senza zona e senza mese (colonne `Parametro, Limiti di legge, Acqua di Milano, Unita' di misura`) | 7 trimestri sparsi: 2018-Q4, 2019-Q2, 2020-Q4, 2021-Q1..Q4 | CSV di ~590 byte, 18 righe ciascuno |
| ds1827 "civici aggregati per zone MM" | civico -> zona MM (+ municipio, NIL, coordinate) | foto del 2022 | `civici_zone_mm_no_dupl.csv`, 8.258.347 byte, 62.587 righe |
| ds1571 "Acqua immessa, erogata e perdite idriche - Anno 2018" | 1 sola riga | 2018 | CSV 220 byte |

Non esistono altri trimestri (1T-3T 2018, 1T/3T/4T 2019, 1T-3T 2020): non ci sono sul portale. Non esiste un dataset con i **poligoni** delle zone MM (cercato per "zone", "milanoblu", "acquedotto"): le zone vanno ricostruite dai civici (vedi sotto).
Extra visti ma NON scaricati (fuori mandato): ds502 fontanelle, ds625 case dell'acqua, ds523 consumo di acqua pro capite 2000-2011.

**Licenza.** Tutti i dataset sono `cc-by` su CKAN; per le analisi e per ds1827 la risorsa dichiara CC BY 4.0 (A21_CCBY40), per ds1571 CC BY 3.0 IT (A23_CCBY30IT): la fonte vera dei dati di ds1571 e' ISTAT (tavola 17 GMA 2021), il Comune li ha estratti. Si possono ripubblicare citando la fonte ("Comune di Milano - dati.comune.milano.it, CC BY 4.0"; per le perdite anche ISTAT). Il file dei civici del Comune (ds634, in `citta-15-minuti`) e' letto soltanto, non copiato.

#### 2. Il problema degli accenti (per il JOURNAL)

Controllati byte per byte tutti i CSV e JSON di dati. Risultato: **solo 3 file hanno un problema**, gli altri sono UTF-8 pulito (nessun "Ã¨" da nessuna parte; il "\x88" non c'e').

1. **`getdatiqualitaacqua_2024.csv` (e anche il suo .json)**, solo le righe di **dicembre 2024** (48 righe, 16 campi): doppia codifica **cp850 -> letto come cp1252 -> salvato in UTF-8**. Segni: "µ" appare come `æ` (cp850 0xE6), "°" come `ø` (0xF8), "à" come `…` (0x85, che in cp1252 e' i puntini). Esempi: `æg/l`, `æS/cm`, `øF`, `Residuo Fisso A 180ø`, `Conducibilit…`, `Unit… pH`. Riparazione: `testo.encode('cp1252').decode('cp850')` applicata ai campi che contengono uno di quei tre caratteri.
2. **`ds737_qualita_acqua_.csv`** (2T 2019): una sola parola, `conducibilitŕ` (ŕ = U+0155). E' una "à" scritta in cp1252 e letta come cp1250. Riparazione: `encode('cp1250').decode('cp1252')`. (Lo stesso difetto e' nel .json di ds679, che non uso.)
3. **`ds679_analisi_acqua.csv`** (4T 2018): non e' UTF-8 ma **cp1252** (byte singoli 0xE0, 0xB0, 0xB5). Letto come cp1252 e' corretto. Il suo .json invece e' UTF-8 corretto (tranne la parola del punto 2).

Altre sporcizie di testo: spazi non separabili (U+00A0) nei limiti ("valori consigliati", "da  6,5 a 9,5": ripuliti); `Unita'` e `conducibilita'` con apostrofo al posto della "à" nei trimestrali 2020-2021 (normalizzati al nome del parametro); l'unita' della conducibilita' nei mensili e' scritta `µS/cm a 20°` (manca la "C"). Dopo le riparazioni nei campi tenuti restano solo `°`, `à`, `µ`, tutti attesi (controllo automatico nello script). Dettaglio: `pulito\_controlli\codifica_riparazioni.csv`, `pulito\_log_pulizia.txt`.

#### 3. Valori sotto la soglia di rilevabilita' ("<0,05")

Tengo il testo originale (`valore_testo`), poi `sotto_soglia` = 1, `soglia` = numero dopo il "<", e `valore` VUOTO. Mai convertito in 0 e mai nella soglia.
- Sul totale: 1.239 righe su 4.699 misurate sono sotto soglia = **26,4%** (nei soli mensili 1.200 su 4.573 = 26,2%).
- Per parametro (quota sotto soglia sulle misurate): ammonio 100%, fluoruri 100%, nitriti 100% (in tutta la serie non c'e' mai un numero), manganese 91%, cloro residuo 56%, arsenico 33%; tutti gli altri 0%. File: `pulito\_controlli\sotto_soglia_per_parametro.csv`.
- **Trappola: la soglia cambia nel tempo** (cambia il laboratorio/metodo, non l'acqua). Ammonio da <0,10 a <0,05; nitriti da <0,20 a <0,05; fluoruri da <0,5 a <0,15; cloro residuo da <0,01 a <0,04; manganese da <1 a <1,25 (sale!). Il cambio e' nel 2022 (convivono nello stesso anno). Quindi la "quota sotto soglia" per anno non si puo' confrontare e non si puo' mai fare un grafico delle soglie come se fossero valori. File: `soglie_sotto_limite_per_parametro_anno.csv`.
- Scritti anche con il punto ("<0.10", "<0.5") nei file 2021, 2024 (e dic 2024): tutti letti.
- 4 valori di manganese "0" (mag-giu 2023, NE/NO/SO): sono quasi certamente "sotto soglia" scritti 0. Li tengo come numero ma con una nota (`nota_valore`).

#### 4. La tavola pulita `pulito\analisi.csv` (4.926 righe, 33 colonne, separatore `;`, UTF-8)

- 4.800 righe mensili per zona (2021-01 .. 2026-09) + 126 righe trimestrali "Tutta Milano" (7 trimestri x 18 parametri). Le righe trimestrali hanno `periodo_tipo = trimestre`, `zona_codice = MI`, `zona_id` vuoto; NON si sommano ai mensili (nel 2021 si sovrappongono).
- Colonne chiave: `periodo` (2024-03 o 2021-Q2), `anno`, `mese`, `trimestre`, `data_riferimento`, `zona_codice/nome/id`, `parametro` (nome normalizzato), `valore`, `unita`, `sotto_soglia`, `soglia`, `qualita_dato` (ok / sotto_soglia / non_misurato / anomalo), `valore_testo` (originale), `limite_testo`, `limite_tipo` (legge / consigliato / nessuno), `limite_min`, `limite_max`, `entro_limite_legge`, `entro_valore_consigliato`, `data_caricamento`, `file_origine`, `riga_origine`.
- **18 parametri** (nomi uniformati; unita' uniformate): pH; residuo fisso a 180 °C (mg/L); durezza (°F); conducibilita' a 20 °C (µS/cm); calcio, magnesio, sodio, potassio, bicarbonati, cloruri, solfati, fluoruri, nitrati, nitriti, ammonio, cloro residuo (mg/L); arsenico, manganese (µg/L). Nomi: nei trimestrali sono minuscoli e "bicarbonato", nei mensili "Bicarbonati"; "Cloro Residuo" ecc. Nessun parametro e' cambiato nome o unita' in modo sostanziale (controllo automatico: 1 sola unita' per parametro dopo la normalizzazione). `pulito\parametri_info.csv` contiene la spiegazione in italiano di ogni parametro (colonna `info` dei file, un solo testo per parametro).
- **Limiti.** Cloruri 250, solfati 250, sodio 200, potassio 10, nitrati 50, nitriti 0,5, ammonio 0,5, fluoruri 1,5, arsenico 10, manganese 50, conducibilita' 2500, pH 6,5-9,5 sono "limiti di legge" come li chiama il file. Durezza 15-50 °F, residuo fisso 1500 mg/L (asterisco) e cloro residuo 0,2 (asterisco) sono solo **valori consigliati** (i trimestrali lo scrivono: "valori consigliati", "valore max consigliato", "valore consigliato 0,2"). Calcio, magnesio, bicarbonati: "non previsto". Per questo ho due colonne separate, `entro_limite_legge` e `entro_valore_consigliato`. Il cloro residuo 0,2: il file dice "massimo consigliato", ma nella pratica quel valore e' spesso citato come minimo: **da verificare con MM prima di scriverlo in pagina**. Due valori (1,43 mg/L ott 2024 NE; 1,33 mg/L set 2026 SO) sono sopra quel 0,2 consigliato: sono valori di cloro, non un superamento di legge.
- Valori fuori dai limiti di legge in tutta la tavola: **zero** (controllo: `valori_oltre_limite.csv` contiene solo i 2 casi di cloro "consigliato"). Nessuna riga sotto soglia con soglia piu' alta del limite.
- Duplicati: nessuno (chiave periodo + zona + parametro; nessuna riga identica).
- Valori estremi (z robusto > 6): 14, quasi tutti cloruri/solfati di singoli mesi e i due cloro sopra; elencati in `valori_estremi_z_robusto_oltre_6.csv`, NON tolti.

#### 5. Trappole dei dati (da non dimenticare)

1. **Lacune nei mesi**: mancano **novembre 2025** e **maggio 2026** per intero. Ottobre 2026 non c'e' ancora. Il 2026 va da gennaio a settembre.
2. **Dicembre 2024 e' strano**: solo 3 zone (manca Sud-Ovest), Sud-Est ha 12 parametri su 18, il campo `info` contiene "Lorem ispum" (testo finto), data di caricamento 15/06/2024 (sei mesi PRIMA del mese a cui si riferisce) e proprio queste righe hanno la codifica sbagliata. Va trattato come dato sospetto/provvisorio, non come serie regolare.
3. **`dataCaricamento` non e' una data di pubblicazione affidabile**: ottobre 2021-aprile 2022 risultano caricati tra marzo e maggio 2021, dicembre 2025 risulta caricato il 14/01/2025 (probabile refuso per 2026), ecc. Elenco in `caricamento_prima_della_fine_del_mese.csv`. Non usarla per niente. Settembre 2021 ha una data diversa quasi per ogni riga (dal 9 ottobre al 28 dicembre 2021): date evidentemente generate.
4. **Il 2024 e' un anno "a metà" per i parametri**: il 24% delle righe del 2024 e' `-` (non misurato; 227 righe in tutto, di cui 24 a gennaio 2025). Nel 2024 (e a gennaio 2025) i parametri sono misurati a rotazione, in due gruppi: gruppo A = ammonio, cloruri, fluoruri, nitrati, nitriti, solfati (6); gruppo B = arsenico, calcio, durezza, magnesio, manganese, potassio, sodio (7). Ogni mese ne manca uno dei due gruppi (si misurano 11 o 12 parametri su 18; pH, residuo fisso, conducibilita', bicarbonati e cloro sempre). Quindi per calcio, magnesio e durezza nel 2024 ci sono valori solo in alcuni mesi (e per zona in modo diverso, vedi `parametri_misurati_per_mese_zona.csv`). `-` NON e' zero: e' "non misurato" (`qualita_dato = non_misurato`).
5. **Valori ripetuti**: nel 2021 il 74% dei valori e' identico a quello del mese prima (stessa zona, stesso parametro): i valori mensili 2021 sono a blocchi di 2-3 mesi uguali, cioe' sono in pratica trimestrali. Nel 2022 il 15%, 2023 30%, 2024 14%, 2025 44%, 2026 49% (es. gennaio e febbraio 2025 hanno gli stessi calcio e durezza). Non e' un errore di lettura: e' come il Comune pubblica. Impatto: la "stagionalita'" mensile non e' misurata mese per mese in tutti gli anni. Controllo: `valori_uguali_al_mese_precedente_per_anno.csv`.
6. Due valori non leggibili tenuti ma NON numerici (`qualita_dato = anomalo`): calcio NO maggio 2022 = `7'`; cloro residuo SE ottobre 2024 = `>0,04` (probabile "<0,04" scritto male). Non li ho "corretti".
7. Decimali con virgola e con punto mescolati (es. "0,2*" e "0.2*", "Da 6.5 a 9.5"); asterischi sui limiti; tutti normalizzati ma il testo originale e' in `valore_testo` / `limite_testo`.
8. Ordine delle righe: nei JSON 2021-2024 le righe sono in ordine diverso dai CSV. Confrontati per chiave: CSV e JSON sono identici in tutti i campi di dati (0 celle diverse). Uso i CSV.
9. Controllo di coerenza: le medie mensili 2021 delle 4 zone sono vicine ai 4 valori trimestrali "Tutta Milano" 2021 (differenza mediana 0,9%, massima 12,5% su potassio che vale 1-2 mg/L, quindi arrotondamento). `confronto_2021_trimestrale_vs_mensile.csv`.
10. I valori sono di **4 zone**, non dei singoli quartieri: ogni zona e' una grande area di rete (Nord-Ovest id 6, Sud-Ovest id 15, Sud-Est id 16, Nord-Est id 18). I codici id non sono mai cambiati nel tempo e i nomi coincidono con quelli dei civici ("Milano Nord Ovest" = "Nord-Ovest").
11. Sulle differenze tra zone: sono differenze tra acque diverse tutte conformi (durezza tra 20 e 36 °F in tutta la serie, sempre dentro 15-50). Vietato dire "peggiore/migliore" o "a rischio".

#### 6. Zone e indirizzi

- **4 zone MM**, nessun poligono ufficiale. Il file dei civici (ds1827, 62.587 civici, 8 senza zona) assegna ogni civico a una zona. Municipio -> zone: il 4 e' tutto Sud-Est, l'8 e il 9 tutto Nord-Ovest, il 6 tutto Sud-Ovest; il 1 contiene tutte e 4 le zone, il 2/3/5/7 ne hanno due.
- Le zone sono **spazialmente compatte**: controllo a vicini (7 civici piu' vicini): il 99,68% dei civici ha la stessa zona della maggioranza dei vicini; solo lo 0,18% ha il vicino piu' prossimo in un'altra zona. Quindi i confini esistono davvero e si possono ricostruire. File: `zone_civici_incoerenti_con_i_vicini.csv` (quelli che non tornano).
- **Centro storico**: il confine passa dentro il quartiere: il NIL Duomo ha civici in tutte e 4 le zone (50% Sud-Ovest), Stazione Centrale 52%/48%, Guastalla 73%, Magenta-S.Vittore 64%, Stadio-Ippodromi 60%. 72 NIL su 88 sono interamente in una zona. In centro anche la stessa piazza (Piazza del Duomo) ha civici in zone diverse: con il solo quartiere non si puo' rispondere, serve l'indirizzo. `nil_zone.csv`.
- **Zone approssimate**: celle di 100 m classificate con i 15 civici piu' vicini, levigate, ritagliate sul confine del Comune: `zone_approx.geojson` (4 poligoni, EPSG:4326, etichettati come APPROSSIMATI) e `zone_celle.csv` (18.802 celle con confidenza). Aree: Nord-Ovest 60,7 km2 (33%), Sud-Ovest 56,6 (31%), Sud-Est 51,4 (28%), Nord-Est 14,1 (8%). Il Nord-Est ha l'8% dell'area ma il 16% dei civici (edificato fitto). Sono ricostruzioni, **non confini ufficiali**: 292 celle (1,6%) hanno confidenza < 0,7 (aree di confine) e 491 celle sono a oltre 500 m dal civico piu' vicino (parchi, aree non edificate: zona assegnata per vicinanza). Chiedere a MM i confini veri se si vuole una mappa definitiva.
- **Tavola per "scrivi il tuo indirizzo"**: `civici_zone.csv` (66.826 civici: 62.579 con zona MM ufficiale, 4.247 con zona STIMATA dai vicini perche' non erano in ds1827 o avevano zona vuota; colonna `fonte_zona` e `confidenza`; 4.199 hanno confidenza >= 0,9), `indirizzi_zona.csv` (55.242 coppie via + numero + lettera, ignorando le barre/interni, con zona prevalente: 3 soli indirizzi hanno civici in piu zone), `strade_zona.csv` (4.039 vie: 80 attraversano piu' zone; per queste una via sola non basta, serve il numero). Chiavi di ricerca senza accenti e minuscole: `chiave_via` (es. "via ciccotti ettore") e `chiave_via_token` (parole ordinate, senza "di/del/della": "via ettore ciccotti" e "via ciccotti ettore" danno lo stesso). Le coordinate arrivano dal file civici del Comune di ottobre 2026 (ds634, unite per `IDMASTER`: 60.921 civici su 62.587 combaciano); per gli altri 1.666 restano quelle di ds1827 (probabilmente civici soppressi). Le coordinate dei due file coincidono entro pochi cm (mediana).
- **Trappole indirizzi**: i civici contengono "barre" tipo `15N05`, `1M01`, `93P01` (negozi/interni): il numero che scrive un cittadino e' il numero base. 150 nomi di via compaiono in piu' municipi (vie lunghe che li attraversano o omonime): i 6 indirizzi che risultano in due municipi vanno disambiguati. I nomi nel Comune sono "COGNOME NOME" (es. "CICCOTTI ETTORE") mentre la gente scrive "Ettore Ciccotti".
- I 4.239 civici del file Comune senza zona in ds1827: 2.856 "Iter in corso", 1.298 "Applicato", 85 "In attesa fine lavori".

#### 7. Perdite idriche (`pulito\perdite.csv`)

Una sola riga, **anno 2018** (periodo 1/1-31/12/2018): acqua immessa 213.352, erogata 182.776, pro capite 426 e 365, perdite 14,3%. Le unita' NON sono scritte nel file: ho dedotto **migliaia di m3** (volume) e **litri per abitante al giorno** (pro capite) perche' tornano i conti: (213.352-182.776)/213.352 = 14,33% (= 14,3 dichiarato) e 213.352.000 m3 / (426 L x 365 g) = 1.372.127 abitanti (Milano ha circa 1,37 milioni). Fonte: ISTAT tavola 17 GMA 2021. Niente serie storica, niente suddivisione per zona. Solo un numero di contesto.

#### 8. Quello che manca / da chiedere

- Un confine ufficiale delle 4 zone (MM / Comune): da chiedere.
- Perche' nel 2024 meta' dei parametri manca a mesi alterni (cambio del piano di controlli? da chiedere).
- Il significato esatto di 0,2 mg/L di cloro residuo ("massimo" o "minimo consigliato").
- Altri trimestri 2018-2020 e altri anni di perdite: non pubblicati.

#### 9. Come rifare tutto

`python -I scripts\01_scarica.py <strand>` (download, riprendibile) -> `02_pulisci.py <strand>` -> `03_zone.py <strand> <...\citta-15-minuti\raw\comune_milano>` -> `04_perdite_inventario.py <strand>`. Controlli e log: `pulito\_controlli\`, `pulito\_log_pulizia.txt`, `pulito\_log_zone.txt`.

### Fase 2 — pagina (2026-10-30)

- Pagina `docs/acqua-del-sindaco/`:
  - servizio "scrivi il tuo indirizzo" (l'indirizzo resta nel browser);
  - mappa delle 4 zone (confini approssimati);
  - schede per zona come le etichette delle acque in bottiglia;
  - serie mensili 2021-2026.
- Nessun valore oltre i limiti di legge in nessun mese pubblicato; nessuna stagionalità visibile.
- Quattro valori di manganese scritti "0" (maggio-giugno 2023) sono trattati come probabili "sotto soglia", mai disegnati come zero.

## 19. I censimenti di Milano

_Fonti, date di scarico, licenze, scelte, problemi. Cartella `censimenti/` (nome proposto dal coordinatore; Davide può cambiarlo)._

- 2026-10-30 — Davide: "dati censimento, scaricali fino da quando ci sono, poi per il nuovo filone". Fase 1: scaricare in blocco tutto quello che c'è, dal primo censimento disponibile (1861) a oggi, per il Comune di Milano e, dove esiste, per sezione di censimento o per quartiere.

### Fase 1 — scarico (2026-10-30)

**Censimenti di Milano - fase 1 (scaricamento e controllo)**

Scaricato il 30 ottobre 2026. Niente grafici, niente pagine, niente git. Tutti gli script sono in `scripts\`, i dati originali in `raw\`, i file ripuliti in `pulito\`. L'elenco completo delle fonti, con dimensioni e licenze, e' in `pulito\inventario.csv`.

#### In breve

- Milano ha i dati dei censimenti **per sezione di censimento** per 1991, 2001, 2011, 2021 e anche per il censimento permanente del 31.12.2023. Prima del 1991 il dettaglio e' solo per comune (1861-1981).
- Il Comune ha anche pubblicato i **record individuali** (una riga per persona, famiglia, abitazione) dei censimenti 1991 e 2001, con il codice di sezione. Il numero di righe coincide con il totale ufficiale ISTAT (1.369.231 e 1.256.211 persone).
- I **codici delle sezioni non sono confrontabili** da un censimento all'altro (vedi sotto). ISTAT non ha una tabella di corrispondenza che io abbia trovato.
- Licenza: ISTAT dichiara CC BY 4.0 su tutto il sito (pagina "Note legali", letta il 30/10/2026). I dati del Comune sono "Creative Commons Attribution" (campo license_id = cc-by in tutti gli 80 pacchetti). Si possono ripubblicare citando la fonte.

#### Quali anni, a quale livello

| Anno | Comune | ACE (86) | Municipi/NIL | Sezione | Fonte |
|---|---|---|---|---|---|
| 1861-1981 | si | no | no | no | volume ISTAT 1994 (pdf), ds303 Comune |
| 1991 | si | no | via tabella ds1635 (zone 9/20) | si, 5.583 sezioni con dati | ISTAT CPA 1991, Comune ds1636-1639 |
| 2001 | si | no | via ds1529 (zone 9/20, NIL) | si, 5.983 | ISTAT CPA 2001, Comune ds1518-1529 |
| 2011 | si | si | si | si, 6.017 | ISTAT CPA 2011, Comune ds382-385, ds364 |
| 2021 | si | no | si (COM_ASC1 municipio, COM_ASC2 NIL dentro il file) | si, 6.055 con indicatori (7.095 poligoni) | ISTAT Dati_regionali_2021 |
| 2023 | si | no | si | si, 6.059 | ISTAT Comuni_2023 |

Totali dei residenti, controllati sommando le sezioni (campo P1 di `pulito\sezioni_<anno>.csv`): 1991 = 1.369.231; 2001 = 1.256.211; 2011 = 1.242.123 (uguale alla popolazione legale 2011); 2021 = 1.349.930; 2023 = 1.371.499.

#### Variabili disponibili

- **1991 e 2001** (`sezioni_1991.csv`, `sezioni_2001.csv`, 207 e 204 colonne): popolazione per sesso, eta', stato civile, cittadinanza, titolo di studio, condizione professionale, famiglie, abitazioni, edifici. Il significato di ogni colonna e' in `variabili_1991.csv` e `variabili_2001.csv` (foglio "Metadati" originale; righe di intestazione sporche, da ripulire in fase 2).
- **2011** (`sezioni_2011.csv`, circa 140 colonne): come sopra, piu' cittadinanza, istruzione, occupazione, famiglie, abitazioni, edifici. Tracciato in `variabili_2011_sezioni.csv`. Esistono anche ACE (`ace_2011.csv`, 86 righe) e municipi (`aree_subcomunali_2011.csv`, 9 righe).
- **2021 e 2023** (`sezioni_2021.csv`, `sezioni_2023.csv`, circa 120 e 148 colonne): popolazione, eta', cittadinanza, paese di nascita, istruzione, occupazione, famiglie, auto (2023), abitazioni. Tracciati in `variabili_2021.csv` e `variabili_2023.csv`.
- **Attivita' economiche per sezione** (imprese, unita' locali, addetti per gruppo ATECO): `sezioni_1991_attivita.csv`, `sezioni_2001_attivita.csv`, `sezioni_2011_attivita.csv`.
- **Record individuali del Comune** (in `raw\comune_ckan\ds1636...`, `ds1518...`, ecc., dentro zip): persone con sesso, eta' singola, stato civile, cittadinanza (singolo paese), titolo di studio, condizione e posizione professionale, settore, pendolarismo (2001), anno di arrivo in Italia (1991). Tracciati nei file `...descriz-col.csv` e `...decodifiche.csv`. Non li ho estratti: pesano 100-180 MB ciascuno.
- **Pendolarismo 2011** per sezione di origine e di destinazione (ds390-395), indicatori 1991-2001-2011 (ds361-366), stranieri 2011 (ds386-389): scaricati.

#### Le sezioni cambiano: i codici non sono confrontabili

- Il codice e' sempre 15146 + 7 cifre (per es. 151460000001), ma il numero progressivo viene riutilizzato con confini diversi. Prova: dei codici presenti sia nel 1991 sia nel 2001 (5.509), solo 14 hanno la stessa popolazione; tra 2011 e 2021, 141 su 5.633. Quindi "stesso codice" non vuol dire "stessa sezione".
- Numero di sezioni con dati: 5.583 (1991), 5.983 (2001), 6.017 (2011), 6.055 (2021). I poligoni sono piu' numerosi (5.831, 6.083, 6.085, 7.095): alcune sezioni hanno piu' pezzi o sono senza residenti.
- La nota ISTAT sulle basi territoriali 2021 riporta che le sezioni in Italia sono molto piu' numerose nel 2021 (402.677 nel 2011, 756.376 nel 2021). (Non ho verificato l'affermazione, letta in un riassunto, che i confini 2011 derivino da quelli 2001.) Non ho trovato una tabella ufficiale di corrispondenza sezione per sezione. Per confrontare nel tempo servira' la sovrapposizione geometrica (le geometrie di Milano sono in `pulito\geometrie\`) oppure l'aggregazione a NIL.
- Il Comune fornisce, per 1991 e 2001, una tabella che collega ogni sezione alle sue zone (ds1635, ds1529: Zona9, Zona20, e NIL per il 2001), cosi' si puo' confrontare a livello di zona.
- Il codice di sezione dei record del Comune coincide con quello ISTAT per il 97% (1991) e il 99% (2001) delle sezioni; le differenze sono piccole (in totale 1.234 persone nel 1991, 2.450 nel 2001).
- Per 2011 e 2021 i NIL esistono nei file ISTAT del 2021 (88 NIL) e nei dati del Comune; per il 2011 c'e' l'ACE e il campo COD_ASC.

#### Popolazione del comune 1861-2021 (e confini)

File: `pulito\popolazione_comune_1861_2021.csv`, con due serie:
1. `confini_dell_epoca` (Comune ds303, dati ISTAT): popolazione e superficie, 14 censimenti, dal 1861 al 2011.
2. `confini_al_20_ott_1991` (volume ISTAT 1994, Tavola 3): popolazione ricalcolata ai confini del 1991. Valori ricostruiti da ISTAT con proporzioni, non contati; per il 1971 il volume da' 1.732.000 (cifra tonda) contro 1.728.686 della serie dell'epoca.
Piu' le righe 2001, 2011, 2021, 2023 (somma delle sezioni). La serie annuale calcolata dal Comune (1880-2025, ds1494) e' in `popolazione_milano_annuale_1880_calcolata.csv`.

Cambi di confine che si vedono nei dati:
- Tra 1871 e 1881 la superficie passa da 9,7 a 72,9 km2 e la popolazione da 199.009 a 321.839: e' l'annessione dei Corpi Santi (ricavata dai dati; la data 1873 e' dalla mia memoria, da verificare).
- Tra 1921 e 1931 la superficie passa da 76,3 a 187,2 km2 e la serie annuale salta da 697.368 (1922) a 826.469 (1923): sono le annessioni del 1923. Dalla mia memoria: undici comuni (Affori, Baggio, Chiaravalle Milanese, Crescenzago, Gorla Primo, Greco Milanese, Lambrate, Musocco, Niguarda, Trenno, Vigentino). **Elenco e decreto da verificare con una fonte in fase 2**, non li ho trovati in nessun file scaricato.
- Tra 1971 e 1981 la superficie scende da 181,7 a 171,7 km2 e poi risale a 181,6 nel 1991: dato strano nel file ds303, da controllare (puo' essere un errore di misura o un cambiamento di metodo).
- Mancano il 1891 (censimento non fatto) e il 1941 (guerra); il 1936 e' nel volume ISTAT ma non in ds303.

#### Trappole dei dati

1. Il volume ISTAT 1861-1991 e' un PDF scansionato con OCR: ho letto a mano solo la riga di Milano e l'ho controllata sull'immagine. Per altri comuni servirebbe lavoro in piu'.
2. I file ISTAT 2011 sono in codifica Windows-1252 (apostrofo = byte 0x92); letti cosi' nei file ripuliti.
3. I file dbf 2001 e 2011 scrivono i numeri in notazione scientifica ("3.00000000000e+000"); ho convertito PRO_COM con float.
4. Nel file ISTAT 2021 "base" (`sezioni_2021_base.csv`) ci sono 7.095 sezioni, di cui 5.937 con residenti; nel file con gli indicatori ce ne sono 6.055. Non ho verificato quali mancano.
5. I nomi delle variabili (P1, P2, ...) hanno lo stesso prefisso in tutti gli anni, ma solo P1 (popolazione totale) ho verificato che e' uguale; per il resto serve una tabella di raccordo nomi 1991-2001-2011-2021 (da fare in fase 2).
6. Nei file 2023 ci sono sezioni "fittizie" (codici 888888x = senza fissa dimora iscritti in anagrafe; 999999x = zone contese): vedi nota ISTAT del 9 giugno 2026. In Milano compaiono con codice 15146888888x.
7. Il censimento 2021 e 2023 non e' "porta a porta" ma permanente (registri + campioni): i numeri per sezione sono stime assegnate con il collegamento anagrafe-luoghi, non conteggi. Il confronto con 1991-2011 va fatto con cautela (nota ISTAT sul passaggio al censimento permanente).
8. Il censimento del 1991, per le attivita' economiche, ha solo i record "significativi" (con almeno un contatore diverso da zero).
9. Le geometrie di Milano 1991 e 2001 le ho estratte con un lettore di shapefile scritto in Python (`scripts\shp_milano.py`), senza programmi GIS; sistema di coordinate EPSG:32632 (UTM 32N). Non le ho confrontate con altre fonti; il numero di poligoni per anno e' sopra.

#### Cosa non c'e' o non ho potuto prendere

- **Volumi digitalizzati dei censimenti 1861-2011 (ebiblio.istat.it)**: il sito oggi risponde 403 e rimanda a avvisi.istat.it. Per il solo volume 1861-1991 ho usato la copia salvata da Internet Archive (6 ottobre 2026). Gli altri volumi (per es. popolazione residente e presente 1861-1981, volumi provinciali 1961/1971/1981) non sono stati scaricati. Non ho tabelle per comune di famiglie, abitazioni o professioni prima del 1991 se non gli aggregati di Milano dei dataset ds300-302.
- **Serie 1951-2011 per comune ai confini 2011 (8milaCensus)**: il sito e' fermo; Internet Archive era momentaneamente fuori servizio quando ho provato. Non fondamentale per Milano.
- **Dati annuali del censimento permanente 2018-2024 per comune**: sono su IstatData (esploradati.istat.it), che si interroga con un'API che non ha risposto (nessuna risposta in tre tentativi, fino a 120 s). Un terzo tentativo con un'identita' di browser finta e' stato bloccato dal sistema e non l'ho fatto. Per Milano abbiamo comunque il 2021 e il 2023 per sezione. **Da decidere con Davide**: scaricare a mano dal browser, oppure cercare un altro percorso.
- **Tabella di corrispondenza sezioni tra censimenti**: non trovata (cercata sul sito ISTAT e nelle note).
- **Censimenti per ACE/sezione prima del 1991** (1951, 1961, 1971, 1981): nessun dato digitale trovato (la ricerca "censimento 1951/1971" sul portale del Comune da' 0 risultati).
- Il file regionale 2023 (`Dati_regionali_2023.zip`, 261 MB) e' scaricato ma non aperto: Milano e' gia' nel file dei capoluoghi.
- Le sezioni 2021 in `Sezioni_21-kmz.zip`, `Limiti`, `Localita` nazionali non sono scaricate (non servono).

#### Cosa c'e' in raw (circa 1,9 GB)

Vedi `pulito\inventario.csv` per una riga per fonte con URL, dimensione e righe di Milano. In sintesi: `istat_sezioni_<anno>` (shapefile regionali Lombardia), `istat_variabili_cpa` (zip nazionali 1991/2001/2011, 182 MB), `istat_variabili_cis` (attivita'), `istat_variabili_2021` e `2023` (xlsx), `istat_aree_subcomunali`, `istat_volumi_storici` (2 pdf), `istat_documentazione`, `istat_pagine` (pagine HTML salvate), `comune_ckan` (80 pacchetti, 353 file; elenco in `pacchetti_censimento.json`), `estratti` (R03 e Milano estratti dagli zip nazionali: dati originali, non modificati).

#### Comandi per rifare tutto

```
python -I scripts\dl_istat.py <cartella censimenti>
python -I scripts\ckan_list.py <cartella censimenti>     (poi filtrare: pacchetti_censimento.json)
python -I scripts\dl_ckan.py <cartella censimenti>
python -I scripts\extract.py <cartella censimenti>
python -I scripts\build_sezioni.py <cartella censimenti>
python -I scripts\build_2023.py <cartella censimenti>
python -I scripts\shp_milano.py <cartella censimenti>
python -I scripts\build_popolazione.py <cartella censimenti>
python -I scripts\inventario.py <cartella censimenti>
```
(Il filtro dei pacchetti con "censim" e' stato fatto a mano in una riga e non e' salvato come script; il risultato e' in `raw\comune_ckan\pacchetti_censimento.json`.)

- 2026-10-30 — Storie scelte da Davide: com'è cambiata Milano 1991-2023 quartiere per quartiere; Milano dal 1861; dove invecchia o ringiovanisce; chi è arrivato. La serie annuale 2018-2024 si cerca per vie aperte, senza chiedere scarichi a Davide.
