# Elezioni milanesi per sezione — note di fase 1 (solo scarico)

Data di scarico: **2026-10-29**. Nessuna analisi, nessuna pulizia, nessun git, niente pubblicato.
Fonte: portale open data del Comune di Milano, `https://dati.comune.milano.it` (CKAN).
Per il JOURNAL: questo file va unito a mano dal coordinatore.

Dove non è scritto altro, "file X, campo Y" si riferisce ai file in questa cartella:
`inventario_dataset.csv` (un riga per dataset), `inventario_risorse.csv` (una riga per file pubblicato),
e a `meta\*.csv` (controlli). I dati grezzi sono in `raw\<nome-dataset>\` (il nome è tagliato a 80 caratteri).

## 1. Domande fatte all'API (nessuna pagina web guardata)

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

## 2. Inventario in sintesi

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

### Cosa è stato scaricato

- 330 file tentati, **329 scaricati**: 182 ZIP (ognuno contiene un CSV) + 145 CSV diretti + 2 GeoJSON (collegi 2022). Registro in `meta\download_log.csv` (con SHA-256).
- Gli ZIP sono stati aperti in `raw\<dataset>\unzipped_<nome>\`; il file ZIP originale resta accanto.
- **Non scaricati di proposito**: 327 file JSON, copie degli stessi CSV (campo `format` = JSON in `inventario_risorse.csv`; 750,8 MB dichiarati nel campo `size_bytes`).
- Dimensione su disco di `raw\`: 257,9 MB (511 file): 14,6 MB di ZIP, 242,4 MB di CSV (327 file, 3.666.332 righe in tutto, campo `rows` di `meta\profilo_csv.csv`).
- **Bloccato**: ds504 "Collegi elettorali 2018" ha come unico file un link a `geoportale.comune.milano.it/ATOM/SIT/...xml` (campo `url`): il nome del sito non si risolve dal mio computer (errore DNS). Non scaricato. La cartella vuota è stata tolta.
- ds23 "banca dati interattiva" è solo un link a `https://siel.comune.milano.it/` (pagina con moduli, risponde 200, senza registrazione). Il testo del dataset dice: risultati ufficiali 1979 → oggi, a livelli "comune, collegi sub-comunali, zone di decentramento, sezioni". Non l'ho esplorata né scaricata; potrebbe servire in fase 2 per controllare i numeri.

## 3. Tabella di completezza

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

## 4. Le sezioni nel tempo (risposta alla domanda 3)

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

## 5. Formati, codifiche, nomi di colonna (solo elenco, la pulizia è fase 2)

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

## 6. Trappole dei dati (materiale per la rubrica)

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

## 7. File prodotti in questa cartella

- `NOTE.md` — questo file.
- `inventario_dataset.csv` — 328 righe, un dataset per riga (tipo, anno, righe, sezioni distinte, codifica, intestazione).
- `inventario_risorse.csv` — 658 righe, un file pubblicato per riga (url, formato, dimensione dichiarata, licenza).
- `raw\` — dati grezzi (257,9 MB, 511 file); `scripts\01_search.py … 06_master.py` — i programmi (vanno eseguiti con `python -I`).
- `meta\` — risposte grezze dell'API (`all_search.json`, `package_list.json`, `election_candidates.json`), `download_log.csv`, `profilo_csv.csv`,
  `controlli_coerenza_totali.csv`, `sezioni_per_elezione.csv`, `stabilita_territorio.csv`, `stabilita_sedi_consecutive.csv`.

## 8. Per la fase 2 (promemoria, non fatto)

- Unificare nomi di colonna e codifiche; decidere come trattare ballottaggi (data) e sezioni 9001–9011.
- Tabella di corrispondenza circoscrizione (1–20) ↔ zona (1–9) per i confronti a cavallo del 1999.
- Sezione → NIL: partire da ds939 (per civico) e ripetere con gli altri stradari (ds1614, ds1862, ds2169, ds2741, ds2922, ds2973) per vedere se la sezione cambia NIL negli anni; poi decidere la regola per le 345 sezioni a cavallo.
- Valutare SIEL (ds23) per controllare i totali delle elezioni 1979–2000.
