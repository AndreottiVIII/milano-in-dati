# Differenze tra le fonti - derby di Milano (fase 1)

Generato da `scripts/10_build.py` il 2026-10-30. Le fonti sono confrontate partita per partita con la lista di it.wikipedia (246 derby giocati).

## 1. Quadro per fonte

| Fonte | Partite confrontate | Concordano (data, casa, punteggio) | Differiscono | Attese ma non trovate | Righe della fonte senza partita corrispondente |
|---|---|---|---|---|---|
| en.wikipedia | 246 | 238 | 8 | 0 | 0 |
| engsoccerdata | 186 | 177 | 9 | 0 | 0 |
| football-data.co.uk | 66 | 65 | 1 | 0 | 0 |
| openfootball | 31 | 31 | 0 | 0 | 0 |
| RSSSF | 196 | 188 | 8 | 27 | 1 |
| it.wikipedia edition pages | 23 | 22 | 1 | 2 | 0 |
| RSSSF (Champions League pages) | 6 | 6 | 0 | 0 | 0 |
| interfc.it almanac (archive.org) | 149 | 149 | 0 | 0 | 0 |

Nota: per RSSSF la data e' quella della giornata (non sempre quella reale); per questo molte differenze di data RSSSF sono solo di calendario.

## 1b. Correzioni applicate alla lista di it.wikipedia (4)

Regola: si corregge solo se almeno 3 fonti indipendenti da Wikipedia concordano contro it.wikipedia e en.wikipedia. Tutte le altre differenze restano come in it.wikipedia e sono solo elencate qui sotto.

| Partita | Campo | Valore in it.wikipedia (e en.wikipedia) | Valore corretto | Prova |
|---|---|---|---|---|
| D022 | date | 1931-03-19 | 1931-03-15 | engsoccerdata, RSSSF and interfc.it almanac all give 1931-03-15 |
| D057 | date | 1948-10-16 | 1948-10-17 | engsoccerdata, RSSSF and interfc.it almanac all give 1948-10-17 |
| D071 | home/away | Inter 2-1 Milan | Milan 1-2 Inter | engsoccerdata, RSSSF and interfc.it almanac all give the mirrored home/away; scorers (minutes) match the mirrored version; it.wikipedia 'Referto' links of D071/D072 are also exchanged |
| D072 | home/away | Milan 1-2 Inter | Inter 2-1 Milan | engsoccerdata, RSSSF and interfc.it almanac all give the mirrored home/away; scorers (minutes) match the mirrored version; it.wikipedia 'Referto' links of D071/D072 are also exchanged |

Le tabelle seguenti confrontano le fonti con `derby.csv` DOPO le correzioni: dove it.wikipedia/en.wikipedia compaiono come 'differenti' per queste 4 partite, e' per via delle correzioni.

## 2. Differenze di PUNTEGGIO (8)

| Partita | Data (derby.csv) | Fonte | derby.csv | Fonte |
|---|---|---|---|---|
| D071 | 1955-10-16 | en.wikipedia | 1-2 | 2-1 |
| D072 | 1956-03-11 | en.wikipedia | 2-1 | 1-2 |
| D083 | 1960-11-20 | engsoccerdata | 0-1 | 1-0 |
| D084 | 1961-03-26 | engsoccerdata | 1-2 | 2-1 |
| D091 | 1964-11-15 | engsoccerdata | 3-0 | 0-3 |
| D092 | 1965-03-28 | engsoccerdata | 5-2 | 2-5 |
| D091 | 1964-11-15 | RSSSF | 3-0 | 0-3 |
| D092 | 1965-03-28 | RSSSF | 5-2 | 2-5 |

## 3. Differenze di SQUADRA DI CASA (8)

| Partita | Data (derby.csv) | Fonte | derby.csv | Fonte |
|---|---|---|---|---|
| D071 | 1955-10-16 | en.wikipedia | Milan | Inter |
| D072 | 1956-03-11 | en.wikipedia | Inter | Milan |
| D083 | 1960-11-20 | engsoccerdata | Milan | Inter |
| D084 | 1961-03-26 | engsoccerdata | Inter | Milan |
| D091 | 1964-11-15 | engsoccerdata | Milan | Inter |
| D092 | 1965-03-28 | engsoccerdata | Inter | Milan |
| D091 | 1964-11-15 | RSSSF | Milan | Inter |
| D092 | 1965-03-28 | RSSSF | Inter | Milan |

## 4. Differenze di DATA (19)

| Partita | Data in derby.csv | Fonte | derby.csv | Fonte (data diversa) |
|---|---|---|---|---|
| D022 | 1931-03-15 | en.wikipedia | 1931-03-15 | 1931-03-19 |
| D057 | 1948-10-17 | en.wikipedia | 1948-10-17 | 1948-10-16 |
| D077 | 1958-06-15 | en.wikipedia | 1958-06-15 | 1958-06-16 |
| D109 | 1972-06-07 | en.wikipedia | 1972-06-07 | 1972-06-08 |
| D119 | 1975-05-25 | en.wikipedia | 1975-05-25 | 1975-05-16 |
| D176 | 1999-10-23 | en.wikipedia | 1999-10-23 | 1999-10-24 |
| D056 | 1948-04-11 | engsoccerdata | 1948-04-11 | 1948-04-15 |
| D089 | 1964-01-19 | engsoccerdata | 1964-01-19 | 1963-11-03 |
| D117 | 1974-11-10 | engsoccerdata | 1974-11-10 | 1974-11-04 |
| D165 | 1995-04-15 | engsoccerdata | 1995-04-15 | 1995-04-14 |
| D181 | 2001-05-11 | engsoccerdata | 2001-05-11 | 2001-05-13 |
| D109 | 1972-06-07 | it.wikipedia edition pages | 1972-06-07 | 1972-06-08 |

Date diverse nella sola RSSSF: 6 (probabilmente data nominale della giornata). Elenco completo:

| Partita | Data in derby.csv | derby.csv | RSSSF |
|---|---|---|---|
| D021 | 1930-10-26 | 1930-10-26 | 1930-10-19 (RSSSF uses round date) |
| D170 | 1997-11-22 | 1997-11-22 | 1997-11-23 (RSSSF uses round date) |
| D174 | 1998-11-08 | 1998-11-08 | 1998-11-01 (RSSSF uses round date) |
| D188 | 2003-10-05 | 2003-10-05 | 2003-09-28 (RSSSF uses round date) |
| D199 | 2008-05-04 | 2008-05-04 | 2008-04-20 (RSSSF uses round date) |
| D218 | 2017-04-15 | 2017-04-15 | 2017-04-09 (RSSSF uses round date) |

## 5. Differenze di COMPETIZIONE (0)


## 6. Differenze di STADIO (2)

| Partita | Data (derby.csv) | Fonte | derby.csv | Fonte |
|---|---|---|---|---|
| D001 | 1909-01-10 | it.wikipedia edition pages | Campo Milan di Porta Monforte | Arena Civica |
| D206 | 2011-08-06 | it.wikipedia edition pages | Stadio nazionale di Pechino | Stadio Nazionale |

## 7. Differenze di ARBITRO (3)

| Partita | Data (derby.csv) | Fonte | derby.csv | Fonte |
|---|---|---|---|---|
| D120 | 1975-06-15 | it.wikipedia edition pages | Agnolin L. di Bassano del Grappa | Luigi Agnolin |
| D133 | 1981-09-06 | it.wikipedia edition pages | Agnolin L. di Bassano del Grappa | Luigi Agnolin |
| D158 | 1993-02-10 | interfc.it almanac (archive.org) | Baldas di Trieste | Paparesta R. di Bari |

## 8. Differenze sui MARCATORI (23 segnalazioni)

| Fonte | Tipo | N. |
|---|---|---|
| RSSSF | minutes differ | 15 |
| RSSSF | player not found in source | 2 |
| interfc.it almanac (archive.org) | minutes differ | 3 |
| it.wikipedia edition pages | minutes differ | 3 |

Avvertenza: il controllo sui giocatori cerca il cognome del marcatore di it.wikipedia nel testo della fonte (senza accenti): ortografie diverse (es. Sevcenko/Shevchenko) producono falsi allarmi. L'elenco completo e' in `differenze_marcatori.csv`; qui le prime righe per tipo.

### RSSSF - minutes differ

| Partita | Data | Dettaglio |
|---|---|---|
| D025 | 1932-11-06 | it.wiki [2, 6, 10, 25, 44, 59, 74, 76, 79] vs RSSSF [2, 6, 10, 25, 44, 54, 74, 76, 79] |
| D030 | 1935-04-14 | it.wiki [2, 88] vs RSSSF [1, 88] |
| D049 | 1945-11-04 | it.wiki [7, 10, 58, 63] vs RSSSF [7, 10, 59, 63] |
| D051 | 1946-05-30 | it.wiki [13, 32, 35, 36, 75] vs RSSSF [13, 32, 35, 36, 47] |
| D073 | 1956-10-21 | it.wiki [12, 16] vs RSSSF [17, 17] |
| D136 | 1983-11-06 | it.wiki [5, 18] vs RSSSF [9, 36] |
| D156 | 1992-11-22 | it.wiki [40, 69] vs RSSSF [40, 74] |
| D159 | 1993-04-10 | it.wiki [44, 83] vs RSSSF [44, 84] |
| D174 | 1998-11-08 | it.wiki [7, 13, 48, 59] vs RSSSF [7, 13, 48, 60] |
| D176 | 1999-10-23 | it.wiki [20, 72, 90] vs RSSSF [20, 28, 89] |
| D177 | 2000-01-12 | it.wiki [28, 44, 54, 55, 69] vs RSSSF [28, 44, 53, 55, 68] |
| D180 | 2001-01-07 | it.wiki [11, 65, 72, 85] vs RSSSF [11, 65, 72, 84] |
| D184 | 2002-11-23 | it.wiki [13] vs RSSSF [12] |
| D188 | 2003-10-05 | it.wiki [39, 46, 77, 78] vs RSSSF [39, 46, 77, 79] |
| D200 | 2008-09-28 | it.wiki [37] vs RSSSF [36] |

### RSSSF - player not found in source

| Partita | Data | Dettaglio |
|---|---|---|
| D032 | 1936-02-02 | Mario Zorzan (Inter 90') |
| D136 | 1983-11-06 | Aldo Serena (Inter 5') |

### interfc.it almanac (archive.org) - minutes differ

| Partita | Data | Dettaglio |
|---|---|---|
| D006 | 1911-11-05 | it.wiki [55, 59, 79] vs interfc.it almanac (archive.org) [53, 59, 79] |
| D051 | 1946-05-30 | it.wiki [13, 32, 35, 36, 75] vs interfc.it almanac (archive.org) [13, 32, 35, 36, 47] |
| D073 | 1956-10-21 | it.wiki [12, 16] vs interfc.it almanac (archive.org) [17, 17] |

### it.wikipedia edition pages - minutes differ

| Partita | Data | Dettaglio |
|---|---|---|
| D171 | 1998-01-08 | it.wiki [28, 33, 43, 46, 60] vs it.wikipedia edition pages [29, 33, 44, 46, 60] |
| D172 | 1998-01-21 | it.wiki [31] vs it.wikipedia edition pages [32] |
| D177 | 2000-01-12 | it.wiki [28, 44, 54, 55, 69] vs it.wikipedia edition pages [29, 44, 54, 55, 69] |

## 9. Righe di una fonte senza partita corrispondente (o con data troppo lontana)

- **RSSSF**: {'page': 'ital44', 'date': '', 'home': 'Milan', 'hg': '1', 'ag': '3', 'raw': 'Milano-Ambrosiana \t\t1-3\t\t2-0'}

## 10. Partite attese ma non trovate in una fonte

- **RSSSF** (27): D047, D048, D077, D078, D099, D100, D109, D110, D114, D116, D119, D120, D125, D132, D133, D140, D141, D157, D158, D162, D163, D171, D172, D207, D208, D245, D246
- **it.wikipedia edition pages** (2): D243, D244
