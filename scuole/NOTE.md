# Scuole di Milano - FASE 1 (fonti, scarico, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web, nessun giudizio. Ogni numero dice file e campo. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di scuole> <percorso assoluto di milano-in-dati>` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`.
Sigle: **Comune** = dati.comune.milano.it (fonte originale ANASCO, Anagrafe Scolastica del Comune); **MIM** = Ministero dell'Istruzione e del Merito, dati.istruzione.it/opendata; **anno N** = anno scolastico N/N+1 (2024 = 2024/25).

## 1. In breve

1. **Due fonti vere, che si controllano a vicenda.** Il Comune ha, per ogni singola scuola di infanzia, primaria e secondaria di I grado (statali, comunali, paritarie e **anche private non paritarie**), iscritti, classi, genere, cittadinanza, paese di nascita, residenza, NIL: dal 2009/10 al 2024/25. Il MIM ha tutti e quattro gli ordini (anche le superiori) ma solo scuole statali e paritarie, dal 2015/16 al 2024/25 (infanzia dal 2017/18). Le statali primarie coincidono entro lo 0,3% (Comune 41.235 vs MIM 41.308 nel 2024); la somma delle scuole del Comune coincide **esattamente** con la serie per municipio (ds102-104) in tutte le 48 coppie anno-ordine.
2. **I dati sugli alunni si fermano al 2024/25** (entrambe le fonti). Il 2025/26 non c'è ancora (il MIM ha solo l'anagrafe delle scuole fino al 2026/27).
3. **Iscritti 2024/25 (Comune)**: infanzia 26.522 (293 scuole), primaria 54.137 (216), secondaria I grado 35.370 (147); **secondaria II grado (MIM, solo statali+paritarie) 73.818** (196 codici). I tre ordini bassi sono già sotto il picco: infanzia -19,6% dal 2011/12, primaria -9,6% dal 2017/18, sec. I -4,7% dal 2019/20. Le superiori sono sul picco (serie ds105: 75.098 nel 2021/22, 74.830 nel 2023/24).
4. **Il calo è demografico, non una fuga dalle scuole**: i bambini di prima elementare sono ogni anno il 94% (tra 91,5% e 94,7%, coorti 2009-2018) dei residenti che cinque anni prima avevano 5 anni (ds223). I residenti di 0 anni sono 11.818 nel 2012 e 8.751 nel 2025 (-26%).
5. **Statale vs paritaria**: dal 2015 al 2024, a parità di codici scuola, la primaria statale perde l'11,1%, la paritaria l'1,6%, la non paritaria cresce dell'11,6%; la secondaria I statale -7,4%, la paritaria +16,3%. L'infanzia è un caso a sé: lo Stato ne gestisce solo il 6,9%, il Comune il 66,8% (17.705 su 26.522).
6. **Cittadinanza non italiana 2024/25 (Comune)**: infanzia 20,5%, primaria 22,6%, sec. I 21,8%. **Ma il MIM dà 22,6 / 25,5 / 24,6** e i residenti della stessa fascia d'età (ds27) 23,2 / 25,7 / 24,8. Le due fonti ufficiali **non coincidono** per le statali: primaria 26,1% (Comune) vs 30,4% (MIM). Vedi trappole.
7. **Concentrazione**: tra scuole, gli alunni con cittadinanza non italiana sono distribuiti in modo molto più disuguale che tra quartieri (indice di dissimilarità, vedi 4.5): primaria 0,42 tra scuole contro 0,29 tra i NIL (bambini residenti 6-10 anni), 0,31 tra i NIL contando gli alunni nei NIL dove sta la scuola. Valori quasi uguali nel 2012, 2015, 2018, 2021, 2024: non è una novità recente.
8. **Più della metà dei bambini va a scuola fuori dal proprio NIL**: primaria 54,4%, infanzia 47,8%, sec. I 61,7% (Comune ds1739/1740/1741, 2023/24, solo residenti a Milano).
9. **Non esistono dati aperti** su: iscritti ai nidi (ds47 ha solo elenco e posizione delle strutture 2016-2019), refezione scolastica (ds2427/2428 hanno solo le tariffe), iscritti per scuola dopo il 2024/25, scuole private non paritarie nel MIM, bocciati per scuola, risultati/Invalsi per scuola (non cercati: fuori perimetro).

## 2. Fonti, una per una (anche in `pulito/inventario_fonti.csv`, con file, righe, byte e licenza)

**Licenze.**
- Comune: campo `license_id` del catalogo CKAN = `cc-by`, titolo "Creative Commons Attribution", `license_url` http://www.opendefinition.org/licenses/cc-by (la versione non è scritta). Per tutti i dataset del Comune usati, `metadata_modified` tra maggio e ottobre 2026 (ricarichi del portale; i dati di ds224/225/226 sono stati aggiornati il 23/9/2026). Citare "Comune di Milano - dati.comune.milano.it (fonte ANASCO)".
- MIM: nelle pagine del catalogo c'è, accanto a ogni dataset, il marchio "License:" con link http://www.dati.gov.it/iodl/2.0/ = **IODL 2.0 (Italian Open Data License v2.0)**. Non ho riletto il testo della licenza (obblighi esatti di citazione e di eventuale licenza dei lavori derivati): da leggere prima di ripubblicare.
- I dati MIM ripubblicati dal Comune (ds1305, ds1582, ds1872-1895...) hanno `license_id = other-at`: non usati.

### 2.1 MIM Portale Unico dei Dati della Scuola (141 CSV, 556 MB, `raw/miur/`, log con sha256 in `raw/miur/download_log.csv`)
File nazionali: scaricati interi, filtrati in locale su Milano (codice comune F205 nell'anagrafe). Pagine di catalogo salvate in `raw/_pagine/`. Dati "al 31/08" di ogni anno scolastico.

| Dataset | Anni | Cosa contiene | Milano |
|---|---|---|---|
| Anagrafe scuole statali (DS0400) `SCUANAGRAFESTAT` | 2015/16-2026/27 | codice meccanografico, denominazione, indirizzo, CAP, comune, tipologia; **niente coordinate** | 463-473 righe/anno |
| Anagrafe scuole paritarie (DS0410) `SCUANAGRAFEPAR` | 2015/16-2026/27 | idem, "non statale" | 458-477 righe/anno |
| Studenti per anno di corso e fascia di età, statale/paritaria (DS0010, DS0020) `ALUCORSOETASTA/PAR` | 2015/16-2024/25 | alunni per scuola, ordine, anno di corso, età (primaria, sec. I, sec. II) | 65.575 righe Milano |
| Studenti primaria/secondaria per cittadinanza (DS0050, DS0060) `ALUITASTRACITSTA/PAR` | 2015/16-2024/25 | alunni totali, con cittadinanza italiana, non italiana (UE / non UE) per anno di corso | |
| Studenti per anno di corso, classe e genere (DS0030, DS0040) `ALUCORSOINDCLASTA/PAR` | 2015/16-2024/25 | classi, maschi, femmine | |
| Infanzia: per età, cittadinanza, classi (DS1114-1119) `INFANZIAETA..`, `INFANZIASTRACIT..`, `INFANZIACLA..` | **2017/18**-2024/25 | bambini per fascia di età, cittadinanza italiana/non italiana, classi | |
| Edilizia scolastica, elenco edifici (DS0200) `EDIANAGRAFESTA` | 2015/16 (dati 2016), 2017/18, 2018/19, 2020/21-2024/25 | codice edificio, indirizzo, CAP | **niente coordinate**: scaricato, non usato |
- Non scaricati (restano nel catalogo): studenti per indirizzo di studio nelle superiori (DS0070/0080), per tempo scuola (DS0090/0100, DS1120/1121), anagrafe delle province autonome (DS0420/0430, non Milano), le altre 11 tabelle di edilizia (impianti, sicurezza, età...), RDF/JSON/XML, bilanci, PON, SNV.
- **Manca**: scuole private non paritarie, coordinate, serie prima del 2015/16, 2025/26. Il file paritarie 2026/27 differisce da quello 2025/26 solo per 2 scuole su 11.331 (anagrafe, non alunni).

### 2.2 Comune di Milano (39 dataset, `raw/comune_ds*/`, `_metadati.json` in ognuno, log in `raw/comune_download_log.csv`)
Ricerca CKAN con 22 parole chiave, 847 dataset trovati (`raw/search_comune.json`).
- **ds224 / ds225 / ds226 - Scuole infanzia / primarie / secondarie I grado, caratteristiche per singola scuola**, a.s. 2009/10-2024/25, 4.857 / 3.473 / 2.300 righe. Colonne: codice scuola (`Cod_Scuola`/`CodScuola`, codice del Comune, NON il meccanografico), gestione (statale / comunale / privata paritaria / privata non paritaria), denominazione, indirizzo, municipio, NIL (testo con id tra parentesi), capienza (solo primaria e sec. I; solo statali per intero), classi, alunni totali, M, F, residenti a Milano / non residenti, **nati per area geografica** (Italia, UE15, nuovi UE, altri Europa, Africa, America Nord, Centro-Sud, Asia, altro/non disponibile), **cittadinanza** italiana / non italiana / non disponibile. Fonte dichiarata: ANASCO. Tutti i campi pieni salvo le aree di nascita (celle vuote = zero, controllato con le somme).
- **ds102-ds105, ds187, ds188** - serie per municipio e gestione (infanzia, primaria, sec. I dal 2002/03 al 2024/25; sec. II dal 2002/03 al 2023/24, ds187 dal 1991/92). Usati per la serie lunga e il controllo.
- **ds294-299** - iscritti per quartiere e gestione / cittadinanza (2005/06 o 2009/10-2024/25). Per i NIL piccoli le celle sono vuote (soppressione): non usati, ricalcolati dalle scuole.
- **ds1736-1743** - % di alunni residenti in un NIL diverso da quello della scuola (2009-2024, solo NIL con più di 15.000 residenti); ds1742/1743 serie storica del Comune: femmine, stranieri, **stranieri nati in Italia**, ripetenti, scuole private, per ordine e tipo di superiore.
- **ds40, ds46, ds671** (localizzazione scuole primarie / sec. I / infanzia dal 2014/15, con lon/lat WGS84, NIL, tipo, flag paritaria, capienza) e **ds3014-3016** (stesso, a.s. 2025/26). Servono per le coordinate. **ds78** localizzazione delle sec. II: i dati risalgono al 2010 (`temporal_start` 31/1/2010), 174 sedi.
- **ds223** residenti per età, genere, cittadinanza, 2012-2025; **ds27** residenti per NIL, età, cittadinanza, 1999-2025 (164 MB decompresso): servono per il confronto scuola-quartiere. **ds47, ds709, ds672, ds678** nidi e servizi infanzia (elenco strutture 2016-2019), **ds2427/2428** tariffe mensa, **ds551** CPIA: solo contesto.
- ISTAT: non usato (nessun dato per singola scuola; i residenti per età ci sono già dal Comune). Non ho sondato i suoi cataloghi.

## 3. Pulizia (`scripts/build.py`, risultati e conteggi in `pulito/controlli_pulizia.json`)

Nessun valore è stato cancellato o corretto: le stranezze sono segnalate (flag).
- **`pulito/scuole_anno_tidy.csv`** (12.490 righe, `;`): anno scolastico, ordine (infanzia/primaria/sec1/sec2), codice (`C`+codice Comune per i primi tre ordini, meccanografico per sec2), denominazione, indirizzo, gestione, gruppo (statale/paritaria/non paritaria), classi, iscritti, `stranieri` (= cittadinanza non italiana), italiani, non disponibile, lon, lat, id_nil, nil, fonte. Infanzia-primaria-sec1 dal Comune (2009/10-2024/25), sec2 dal MIM (2015/16-2024/25).
- Tabelle di dettaglio: `comune_scuole_anno.csv` (tutti i campi ANASCO, compresa l'area di nascita), `miur_scuole_anno.csv` (4 ordini, anche iscritti al 1° anno di corso), `comune_scuole_anagrafica.csv` e `miur_scuole_anagrafica.csv` (una riga per scuola, con coordinate, NIL e come sono state ottenute).
- **NIL**: punto in poligono con i 88 NIL vigenti (`citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson`). Comune: 701 codici su 714 hanno coordinate (ultima localizzazione disponibile) e il NIL calcolato coincide con quello scritto nel file Comune in 698 casi su 701; i 13 senza coordinate (chiusi prima del 2014) prendono il NIL dal file Comune. Tutte le 10.630 righe hanno un NIL. MIM: le coordinate non ci sono; le ho trovate **agganciando l'indirizzo** alle localizzazioni del Comune (e a ds78 per le superiori): 398 scuole indirizzo uguale, 355 simile, 16 stesso indirizzo di altro ordine, 4 solo via; **96 su 869 non agganciate**. Per gli alunni 2024/25: **91,7%** con NIL (infanzia 89,9%, primaria 92,7%, sec. I 94,9%, sec. II 90,2%). Il resto ha `flag_senza_nil`.
- Controlli Comune: somma cittadinanze = totale in 10.628 righe su 10.630 (2 diverse); M+F = totale sempre; residenti+non residenti = totale tranne **607 righe, tutte del 2024/25** (campo non residenti incompleto quell'anno). 2 righe con zero iscritti. Nessun duplicato anno-ordine-codice.
- Controlli MIM: nessuna riga senza anagrafe, nessun alunno vuoto; la somma per cittadinanza coincide con quella per età in tutte le righe.
- Raccordo MIM-Comune per codice non esiste nei dati: `miur_scuole_anagrafica.csv` ha `codice_comune_corrispondente` dove l'indirizzo trova la stessa scuola (204 primarie, 115 sec. I, 264 infanzia); usato solo per i controlli.

## 4. Riepilogo (numeri in `pulito/riepilogo.json` e nelle tabelle csv, tutti da `scripts/analisi.py`)

### 4.1 Iscritti nel tempo per ordine (`iscritti_per_ordine_gruppo_anno.csv`, `serie_lunga_ordine_gestione.csv`, `nascite_e_prima_primaria.csv`)

| | picco | 2024/25 | var. dal picco | 2009/10 |
|---|---|---|---|---|
| Infanzia | 33.007 (2011/12) | 26.522 | -19,6% | 32.763 |
| Primaria | 59.909 (2017/18) | 54.137 | -9,6% | 55.698 |
| Sec. I grado | 37.109 (2019/20) | 35.370 | -4,7% | 32.759 |
| Sec. II grado | 75.098 (2021/22, ds105) | 73.818 (MIM, st.+par.); 74.830 nel 2023/24 (ds105, include non statali) | -0,4% (2023/24) | 62.914 |

Fonti: Comune ds224/225/226 (campo totale alunni, somma delle scuole) e ds102-105 (somma dei municipi). Serie dal 2002/03 in `serie_lunga_ordine_gestione.csv`. L'infanzia ha un salto da -8% nel 2020/21 (30.342 -> 27.896), in tutte le gestioni e in quasi tutte le scuole (mediana per scuola -7 bambini), e non risale: effetto del periodo Covid o cambio di rilevazione, non lo so.

### 4.2 Nascite e residenti -> iscritti
- Nati avvenuti a Milano (`nomi-bambini/pulito/nascite_milano_ds289.csv`): 12.292 (2009), 11.730 (2015), 10.238 (2020, ultimo anno del file).
- Bambini in prima primaria (MIM, `ANNOCORSO = 1`, statali+paritarie): 11.586 (a.s. 2015/16, coorte 2009) -> 9.913 (a.s. 2024/25, coorte 2018). **Rapporto con i nati a Milano 6 anni prima**: 0,94 (2009) -> 0,99 (2012) -> 0,88 (2018): scende perché "nati a Milano" è per luogo del parto, non per residenza (ds289).
- **Rapporto con i residenti di 5 anni a fine coorte+5** (ds223, `Eta`, `nonsposati_stima`): 0,945 0,946 0,940 0,946 0,946 0,915 0,944 0,943 0,947 0,934 (coorti 2009-2018). Quasi costante: il numero di prime classi segue i residenti.
- Residenti per fascia d'età (ds27, tutta la città): 3-5 anni 37.145 (2012) -> 28.426 (2025); 6-10: 58.682 -> 52.953; 11-13: 32.759 -> 34.740 (picco 36.779 nel 2021); 14-18: 51.230 -> 61.946 (picco 62.490 nel 2024). Segnali per gli anni prossimi: i 3-5enni sono già del 24% sotto il 2012, i 6-10enni del 10%.
- Iscritti / residenti nella fascia, 2024 (`iscritti_su_residenti_fascia.csv`): infanzia 0,91 (26.522 su 29.246 di 3-5 anni), primaria 0,99, sec. I 1,01, **sec. II 1,18** (73.818 su 62.490 residenti di 14-18: arrivano da fuori Milano, e comprende anche i maggiori di 18 anni).
- Alunni non residenti a Milano (ds224-226 `Alunni_NonResid`, 2023): infanzia 6,1%, primaria 8,4%, sec. I 10,2% (il 2024 non è confrontabile, vedi trappole).

### 4.3 Statale / paritaria / non paritaria (`quote_statale_paritaria.csv`, `iscritti_per_gestione_dettaglio.csv`, `variazione_per_ordine_gruppo_2015_2024_stessi_codici.csv`)
- Quota statale: infanzia 6,1% (2009) -> 6,9% (2024) [comunale 66,8%, privata paritaria 21,5%, non paritaria 4,8% nel 2024]; primaria 78,7% (2016) -> 76,2%; sec. I 81,8% (2014) -> 77,1%; sec. II (MIM) 85,4% (2016) -> 82,2% (2024).
- "Paritaria" nei dati del Comune include la scuola dell'infanzia **comunale** (la legge la considera paritaria: `PARITARIA = SI` in ds671); la tabella dettaglia le quattro gestioni.
- Variazione 2015-2024 a parità di codice scuola (primaria: 143 statali, 59 paritarie, 8 non paritarie; sec. I: 89, 39, 8): numeri nel punto 5 di "In breve". Infanzia: statale -14,8% (27 scuole), comunale+paritaria -14,2% (247), non paritaria -15,6% (10).

### 4.4 Scuole che si svuotano e che si riempiono (`scuole_variazione_2015_2024.csv`, 2015/16 -> 2024/25, Comune)

| | stesse in entrambi gli anni | cala >20% | cala 10-20% | stabile (±10%) | cresce 10-20% | cresce >20% | non più presenti / nuove |
|---|---|---|---|---|---|---|---|
| Infanzia | 284 | 87 | 68 | 98 | 9 | 22 | 25 / 9 |
| Primaria | 210 | 60 | 40 | 68 | 12 | 30 | 7 / 6 |
| Sec. I | 136 | 30 | 20 | 46 | 8 | 32 | 6 / 11 |

Attenzione: un cambio di codice (fusione, trasloco) sembra una chiusura più una nuova apertura; nella tabella molte variazioni grandi di singole scuole possono essere così (es. primaria Massaua, Bande Nere, da 460 a 169; secondaria Redaelli, Rogoredo, da 253 a 433). Per NIL (sede della scuola, tre ordini bassi): 51 NIL su 70 hanno meno iscritti nel 2024 che nel 2015. Più in calo (almeno 500 iscritti nel 2015): Duomo -29,4%, QT 8 -27,5%, Comasina -24,9%, Maciachini-Maggiolina -21,3%, Lodi-Corvetto -20,8%. Più in crescita: Adriano +53,0%, Portello +41,0%, Moncucco-San Cristoforo +29,2%, San Siro +21,4%, Maggiore-Musocco-Certosa +21,1%. Tabelle: `nil_iscritti_variazione_2015_2024.csv`.
Capienza dichiarata (campo `Capienza`, **significato non spiegato nel dataset**), statali 2024: primaria, 142 scuole, mediana 76% occupata, 50 sotto il 70%, 5 sopra il 100%; sec. I, 91 scuole, mediana 81%, 27 sotto il 70%, 8 sopra il 100%. Alunni per classe (Comune): infanzia 23,9 -> 21,1; primaria 21,7 -> 19,8; sec. I 22,0 -> 20,7 (2015 -> 2024).

### 4.5 Alunni con cittadinanza non italiana: per ordine, gestione, scuola e NIL
Definizione: campo "cittadinanza non italiana" (Comune: `Alunni_Cittad_Non_Ital`; MIM: `ALUNNICITTADINANZANONITALIANA`). **Non è nato all'estero** e non dice nulla sull'origine.
- Quota 2024/25, tre fonti: infanzia 20,5 / 22,6 / 23,2; primaria 22,6 / 25,5 / 25,7; sec. I 21,8 / 24,6 / 24,8 (Comune, MIM, residenti di 3-5, 6-10, 11-13 anni da ds27). Sec. II: MIM 16,4%, residenti 14-18 22,0% (`stranieri_serie_per_ordine.csv`).
- Nati fuori dall'Italia (Comune, somma delle aree note): infanzia 6,5%, primaria 9,9%, sec. I 11,5% degli alunni. Quindi almeno il 56% degli alunni di primaria con cittadinanza non italiana è nato in Italia (limite basso dalle due quote); il Comune pubblica "stranieri nati in Italia": infanzia 83,4%, primarie 71,8%, sec. I 63,2%, sec. II 57,0% (ds1742, 2023/24).
- Per gestione 2024/25 (Comune, `stranieri_per_gestione_2024.csv`): infanzia statale 38,2%, comunale 22,0%, privata paritaria 8,6%, privata non paritaria 27,2%; primaria statale 26,1%, paritaria 7,2%, non paritaria 34,7%; sec. I statale 25,3%, paritaria 5,4%, non paritaria 32,6%. Le non paritarie includono le scuole internazionali.
- Sec. II statali (MIM `tipologia` anagrafe; `sec2_per_tipo_stranieri.csv`): professionali 36,3% (9.705 iscritti), tecnici 26,2% (20.240), licei e magistrali 8,4% (30.728); paritarie 5,3% (13.145). Nel 2015: 29,0 / 23,6 / 6,3 / 3,1.
- **Indice di dissimilarità** D = metà della somma delle differenze assolute tra la quota di alunni non italiani e di italiani che sta in ciascuna unità (0 = distribuzione uguale, 1 = completamente separati), 2024 (`concentrazione_indici.csv`):

| ordine | tra scuole | tra scuole pubbliche (statali+comunali) | tra gestioni | tra NIL (sede scuola) | tra NIL (bambini residenti) |
|---|---|---|---|---|---|
| infanzia | 0,434 | 0,404 | 0,158 | 0,305 | 0,300 |
| primaria | 0,415 | 0,366 | 0,178 | 0,309 | 0,289 |
| sec. I | 0,373 | 0,311 | 0,182 | 0,310 | 0,273 |

  Primaria 2024: 20 scuole su 216 hanno più del 50% di alunni non italiani e ospitano il 23,1% di questi alunni; 69 scuole hanno meno del 10% e ospitano il 38,1% degli alunni con cittadinanza italiana.
- **Scuola contro quartiere** (`stranieri_scuole_vs_nil_2024.csv`, una riga per scuola 2024: quota della scuola, quota dei bambini residenti nello stesso NIL nella fascia d'età dell'ordine, quota nelle altre scuole dello stesso ordine nel NIL, differenza in punti): per le scuole con almeno 50 iscritti, il 10°-50°-90° percentile della differenza (scuola meno residenti) è -17,9 / -2,4 / +17,6 punti in primaria (infanzia -18,8 / -3,3 / +15,4; sec. I -16,5 / 0,0 / +16,9). 17 primarie sono oltre 20 punti sopra e 20 oltre 20 punti sotto la quota dei residenti del loro NIL. Correlazione scuola-quartiere 0,55 (primaria). Nello stesso NIL, tra le scuole pubbliche con almeno 50 alunni: divario mediano tra la meno e la più "straniera" 20,9 punti in primaria (38 NIL con 2 o più scuole), 11 NIL con più di 30 punti (`nil_divario_tra_scuole_pubbliche_2024.csv`).
  Gli scarti più alti **sopra** il quartiere sono scuole private non paritarie internazionali (es. Bloom International School, infanzia, 85,5% contro 29,5% dei residenti 3-5 anni del NIL Giambellino): un'altra storia rispetto agli scarti delle statali. Gli scarti più alti **sotto** sono scuole paritarie private (es. primaria La Zolla, San Siro: 1,2% contro 53,7% dei residenti 6-10 anni del NIL). Le scuole accolgono bambini di altri NIL (vedi punto 8 di 1), quindi la differenza non dice "chi vive vicino".
- Quota per NIL (`nil_stranieri_2024.csv`): quota negli alunni delle scuole del NIL, quota tra i residenti della fascia, numero di residenti.

## 5. Trappole e cose da non dimenticare

1. **Cittadinanza non italiana ≠ nato all'estero ≠ origine.** Almeno 56% degli alunni di primaria con cittadinanza non italiana è nato in Italia. Non dedurre mai origine, religione, lingua. L'area di nascita per scuola è nei dati ma non è stata riassunta per scuola.
2. **Comune e MIM non coincidono sulla quota di cittadinanza non italiana nelle statali**, dal 2020 in poi: primaria 2024 statale 26,1% (Comune, 10.759 su 41.235) vs 30,4% (MIM); sec. I 25,3% vs 29,2%; nel 2018 la differenza era di 1,1 e 2,0 punti. Nelle paritarie coincidono (primaria 7,2 vs 7,3). Scuola per scuola (129 primarie statali agganciate per indirizzo) il MIM conta in media 11,5 non italiani in più per scuola. Causa non trovata (data di rilevazione diversa? definizione?). I numeri del Comune coincidono con quelli che il Comune stesso pubblica (ds1742: 22,6/24,4/22,0 nel 2023/24). `confronto_quota_stranieri_MIM_vs_Comune_totali.csv`.
3. **Il MIM non ha le scuole private non paritarie** (Comune 2024: 1.274 infanzia, 1.996 primaria, 1.419 sec. I alunni): il confronto delle paritarie deve escluderle, e le quote di cittadinanza includono scuole internazionali che alzano il dato.
4. **Codici diversi**: il Comune usa un proprio codice per scuola (infanzia 1xxx, primarie 2xxx, sec. I 3xxx), il MIM il meccanografico (per sede). Nessuna tabella di raccordo: l'aggancio per indirizzo fallisce per 96 scuole su 869. Dentro il Comune denominazione e indirizzo cambiano formato negli anni (236 codici su 330 di infanzia hanno più di una denominazione): usare sempre il codice.
5. **2024/25 non residenti**: `Alunni_NonResid` e `Alunni_Resid` non sommano al totale in 607 righe (tutte del 2024/25): non confrontare con gli anni precedenti (la quota di non residenti sembra "scendere" da 8,4% a 5,1% in primaria ma è un vuoto).
6. **Infanzia -8% nel 2020/21** (vedi 4.1). **Infanzia MIM solo dal 2017/18.** Nel MIM i dati "al 31/08" sono sulle sedi: un'infanzia di un istituto comprensivo ha il proprio codice.
7. **Gestione scritta in modi diversi** nei file del Comune ("statale"/"Statale", "Non Statale"/"Non statale", "Pubbliche"/"Private"): normalizzata. Colonne con caratteri rovinati ("Unitx85 scol"). Età "100 e più" in ds27.
8. **Nomi dei NIL cambiano** tra file (es. "Magenta - S.Vittore" / "S. Vittore"): ho usato gli ID.
9. **Sec. II grado**: nel MIM non c'è la distinzione liceo/tecnico per le paritarie. Le coordinate dipendono da ds78 (elenco del 2010) e dagli indirizzi; per le sedi "ordinaria + succursale" ho usato la prima sede.
10. **Fusioni e trasferimenti** appaiono come chiusure e aperture (vedi 4.4).
11. Il file MIM "paritarie" per il 2026/27 esiste ma non ha alunni: l'ultimo anno con alunni è il 2024/25.
12. **Capienza** nei dati del Comune senza definizione e solo per primaria/sec. I (infanzia mai; paritarie per il 62-73%): non usare per dire "scuole vuote" senza chiedere al Comune che cosa conta.

## 6. La cosa più sorprendente

Tra le scuole, gli alunni con cittadinanza non italiana sono molto più concentrati che tra i quartieri: indice 0,42 in primaria tra le 216 scuole contro 0,29 tra gli 87 NIL con residenti (bambini residenti 6-10 anni), e **non è cambiato dal 2012** (0,416) mentre la quota di alunni con cittadinanza non italiana è passata dal 20,2% al 22,6%. Esempio concreto: nel NIL San Siro i bambini residenti di 6-10 anni con cittadinanza non italiana sono il 53,7%, la primaria paritaria La Zolla ne ha l'1,2% mentre le altre scuole primarie del NIL, insieme, il 72,4% (`quota_altre_scuole_nil_pct` della riga La Zolla). Secondo punto sorprendente, che spiega la cornice: il calo degli iscritti segue i residenti (prime classi = 94% dei residenti di 5 anni di 5 anni prima), quindi "le scuole si svuotano" è soprattutto "nascono meno bambini": residenti di 0 anni -26% dal 2012 al 2025.

## 7. Cosa potrebbe mostrare una pagina (da decidere con Davide, niente è stato fatto)
- **Linea per ordine** degli iscritti 2009-2024, con i residenti della fascia sullo stesso grafico (stesso indice 100 nel 2012) e le nascite.
- **Carta dei NIL**: variazione iscritti 2015-2024 per sede della scuola (con Adriano e Portello in crescita, Duomo in calo).
- **Statale / comunale / paritaria** per ordine, nel tempo; l'infanzia comunale è il fatto milanese.
- **Cittadinanza non italiana: scuola contro quartiere**: un punto per scuola (asse x quota dei residenti del NIL, asse y quota della scuola), presentato come confronto e con la diagonale; spiegare chiaramente cittadinanza ≠ nascita. Da decidere: nomi delle scuole private e internazionali nel confronto (dati pubblici, ma sono scuole private).
- Una frase di avviso su Comune vs MIM e sul fatto che i dati si fermano al 2024/25.

## INVALSI per istituto (raccolta del 5/11/2026)
- Fonte: pagina pubblica "Indicatori" del portale SNV (`snv.pubblica.istruzione.it`, collegata da Scuola in Chiaro), riquadro 2.2.a.1. Raccolta il 5/11/2026, 5 s tra richieste, UA `milano-in-dati/1.0`, nessun login.
- Condizioni: robots.txt 503 (manutenzione), nessuna nota legale propria del portale; note legali MIM CC BY 3.0 IT senza cenni a raccolta automatica. Dettagli in `_idee/invalsi_stranieri.md` sez. 7. Non pubblicare senza conferma del Ministero.
- Copertura: 135 istituti statali (anagrafe MIM 2025/26, comune F205): 127 pagine, 8 con 404, 71 con punteggi. Solo righe di istituto, mai plesso/sezione. Anno prevalente 2024/25.
- File: `raw/invalsi_rav/*.json` (non tracciati), `pulito/invalsi_istituti.csv`, `invalsi_istituti_quota_stranieri.csv`, `invalsi_istituti_incrocio.csv`. Programmi `scripts/invalsi_rav_raccolta.py`, `invalsi_rav_incrocio.py`.
