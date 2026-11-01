# Redditi dei milanesi dal 2000 - FASE 1 (raccolta, pulizia, riepilogo)

Scaricato il 1 novembre 2026. Niente pagina web. Programmi in `scripts/` (Python 3.12, `python -I -X utf8 scripts/<nome>.py <percorso assoluto di redditi> [<percorso assoluto di milano-in-dati>]`, ordine in STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle in `pulito/`. Tutti i numeri qui sotto escono da `pulito/riepilogo.txt` (rifacibile con `scripts/riepilogo.py`).

Parole: "anno d'imposta" t = redditi guadagnati nell'anno t, dichiarati nel t+1. "Contribuente" = chi ha presentato una dichiarazione (730, Redditi PF), non un residente. Euro 2025 = euro correnti x 100 / indice FOI annuale (2025 = 100, `prezzi-case/pulito/foi_annuale.csv`, ISTAT).

## 1. In breve

1. **Fonte unica e completa: MEF, Dipartimento delle Finanze, "Redditi e principali variabili IRPEF"**. Per comune: **tutti i 25 anni d'imposta 2000-2024** (7.897-8.101 comuni l'anno, Milano, Roma, Torino, Napoli, Bologna presenti in tutti gli anni). Per CAP (41 città, 38 CAP a Milano): **solo 2011, 2015, 2019-2024** (8 anni, non di più). Licenza: **CC BY 3.0** dichiarata nei metadati RDF dei file (`<ccorg:licenses ... licenses/by/3.0/deed.it>`); la pagina web del MEF ha il campo "Tipo licenza" vuoto. Dato da citare: "MEF - Dipartimento delle Finanze".
2. **Il reddito medio reale dei contribuenti milanesi nel 2024 (40.889 euro 2025) è uguale a quello del 2006 (40.595): +0,7% in 18 anni.** Tutta la crescita del periodo (+14,5% dal 2000) è avvenuta fino al 2006. Per Italia stessa storia (+0,5% dal 2006); Roma -3,7%, Torino -3,2%, Napoli -8,0%, Bologna -3,4%.
3. **Anche dentro la città, dal 2011 nessun gruppo di CAP è cresciuto più del 4% reale.** Dividendo i 38 CAP in quattro gruppi per reddito 2011, tra 2011 e 2024 il reddito medio reale (euro 2025) è +0,6% (gruppo più povero), +3,9%, +0,8%, +4,4% (gruppo più ricco); Milano intera +3,0%. Chi è sopra: la quota di reddito dichiarato da chi supera 120.000 euro è passata dal 16,9% (2000) al 33,0% (2024), ma con soglia fissa in euro correnti (trappola 2). Con soglie in euro reali del 2000, i contribuenti sopra 55.000 euro (≈ 87.000 del 2024) sono passati dal 6,5% (2000) al 8,0% (2006) al 9,3% (2024).
4. **Milano è la città con più disuguaglianza tra i grandi comuni**: Gini da classi 0,50 (2000) → 0,54 (2024) contro 0,43 → 0,42 dell'Italia; Roma 0,46 → 0,48, Napoli 0,46 → 0,48, Torino 0,43 → 0,44, Bologna 0,44 → 0,44. Tutte le città salgono fino al 2022 e scendono nel 2023-2024.
5. **Divario tra CAP**: a Milano sale fino al 2022 e poi scende (rapporto tra reddito dei CAP al 90° e al 10° percentile: 2,08 nel 2011, 2,44 nel 2022, 2,40 nel 2024; Gini tra CAP 0,201 → 0,218 → 0,204), mentre a Roma resta fermo (2,13 → 2,02), Bologna (1,69 → 1,57) e Genova (1,76 → 1,63) calano, Torino sale poco (1,79 → 1,92), Napoli è alto e stabile (2,28 → 2,33). Il Gini tra CAP 2024 è più alto a Milano (0,204) che a Napoli (0,186), Roma (0,165), Torino (0,147).
6. **Per tipo**: i pensionati sono scesi dal 37% (2002) al 27,5% (2024) dei contribuenti milanesi, i dipendenti saliti dal 48% al 59,6%; la pensione media per pensionato è salita del 30% reale (23.270 → 30.237 euro 2025) mentre il reddito da dipendente per dipendente è rimasto fermo (38.320 → 39.316).

## 2. La cosa più sorprendente

**Vent'anni senza crescita reale, anche se i numeri correnti salgono del 80%.** Il reddito medio per contribuente di Milano passa da 22.427 a 40.316 euro correnti (+80%), ma in euro 2025 dal 2006 è fermo (40.595 → 40.889), e dal 2011 sale solo del 3,0%; nessuno dei quattro gruppi di CAP supera il +4,4% reale in 13 anni. Milano resta la più ricca tra i grandi comuni (1,6 volte l'Italia) ma il vantaggio non cresce dal 2006. Come contorno, ancora più netto: dal 2010 al 2024 in Italia la pensione per pensionato è salita del 17% reale (19.475 → 22.708) e il reddito per dipendente è sceso del 4,5% (25.760 → 24.595). A Milano nello stesso periodo: pensione +15% (26.289 → 30.237), dipendente -2,5% (40.311 → 39.316).

Cautele: la media non dice chi ci ha guadagnato; le 8 classi non vedono il vertice (la media della classe >120k, in euro 2025, cala del 31% dal 2006 solo perché la classe si allarga). Ai livelli nazionali e regionali, dove ci sono le classi fini (file regionali 2016-2024), la quota di reddito di chi supera 300.000 euro cresce: Italia 2,6% → 3,2%, Lombardia 4,6% → 5,8%. Il CAP è l'indirizzo fiscale, non una persona seguita nel tempo; la media per dipendente è per chi ha anche solo qualche mese di lavoro.

## 3. Fonti, una per una

| Fonte | File (in `raw/`) | Anni | Licenza | Completezza |
|---|---|---|---|---|
| MEF Dip. Finanze, Redditi e principali variabili IRPEF **su base comunale** CSV | `raw/mef/Redditi_e_principali_variabili_IRPEF_su_base_comunale_CSV_<anno>.zip`, url `https://www1.finanze.gov.it/finanze/analisi_stat/public/v_4_0_0/contenuti/...`, log `raw/mef/download_log.csv` (sha256) | a.i. 2000-2024 (25 file) | CC BY 3.0 (metadati RDF) | tutti i comuni, ma celle oscurate nei comuni piccoli (trappola 6) |
| MEF, stesso, **su base sub-comunale (CAP)** CSV | `raw/mef/..._subcomunale_CSV_<anno>.zip` | a.i. 2011, 2015, 2019, 2020, 2021, 2022, 2023, 2024 | CC BY 3.0 | 41 città, 606-609 righe CAP l'anno. 2012-2014, 2016-2018 non esistono nell'open data MEF (il filone 9 usa 2019-2024 dalla copia del Comune, dataset ds1590-ds3009, CC BY). |
| MEF, **per regione e classe di reddito** (`REG_calcolo_irpef_<anno+1>.csv`) | `raw/mef_nazionale/` | a.i. 2016-2024 (dichiarazioni 2017-2025) | CC BY 3.0 (stessa pagina) | complete, classi fini. Serve per Italia e Lombardia 2023-2024 (trappola 6) |
| ISTAT demo.istat.it, popolazione residente al 1/1 | `raw/istat_pop/` (ricostruzione intercensuaria 2002-2019 per comune/regione/Italia; POSAS 2020-2026 per comune), log `download_log.csv` | 1/1/2002-1/1/2026 | CC BY 4.0 (ISTAT) | Milano, Roma, Torino, Napoli, Bologna, Lombardia, Italia. Per Milano 2000-2001 si usa ds71 del Comune (31/12, `bilancio-comune/pulito/popolazione_milano.csv`): sovrastimato di circa 4% perché precede il censimento 2001 |
| ISTAT FOI (indice prezzi) | `prezzi-case/pulito/foi_annuale.csv` (già su disco, 1996-2025, base 2025 = 100) | 2000-2025 | ISTAT | non rifatto, riusato |

Nessun account, nessun CAPTCHA. Pausa di 2 secondi tra i download. Il file CSV del 2011 sub-comunale ha etichette con caratteri rotti (`dell�imprenditore`): le colonne si riconoscono per parole chiave, i valori non sono toccati.

## 4. Cosa c'è nei file e come sono puliti

- **`pulito/mef_comuni_2000_2024.csv`** (200.619 righe = comuni x anni): `anno, catastale, istat, comune, prov, regione, ..., contribuenti` e per ogni voce `_n` (numero contribuenti) e `_eur` (ammontare): `fabbricati, dipendente, pensione, dip_e_pens (solo 2000-01), autonomo (+ autonomo_eia/eib/eii 2000-05), imp_ordinaria, imp_semplificata, partecipazione, imponibile, imposta_netta, imponibile_addiz, addiz_reg, addiz_com`, le **8 classi di reddito complessivo** (`cl0_le0` ≤0, `cl1_0_10k`, `cl2_10_15k`, `cl3_15_26k`, `cl4_26_55k`, `cl5_55_75k`, `cl6_75_120k`, `cl7_oltre120k`), `bonus_trattamento` (2015+), `reddito_complessivo` (solo 2023-24). Le etichette cambiano 8 volte tra il 2000 e il 2024: `scripts/pulisci_mef.py` le unifica.
- **`pulito/mef_cap_2011_2024.csv`** (4.863 righe): stesse colonne, più `cap`.
- Controlli: l'anno nel campo "Anno di imposta" coincide col nome del file (0 differenze, `pulito/mef_lettura_log.csv`); nessun codice catastale duplicato nello stesso anno; i cinque comuni hanno 25 anni.
- Ogni file ha 8 classi: 0-10k, 10-15k, 15-26k, 26-55k, 55-75k, 75-120k, oltre 120k (euro correnti, sempre le stesse soglie 2000-2024).

## 5. Metodo (come si calcola ciò che non è nei file)

- **Reddito complessivo** = somma degli importi delle 8 classi. Per Milano dal 2023 coincide al euro col campo "Reddito complessivo - Ammontare" (controllo in `serie_unita_anno.csv`, colonna `controllo_campo_reddito_complessivo_eur`).
- **Media per contribuente** = reddito complessivo / "Numero contribuenti" (come i riepiloghi MEF). Il numero di contribuenti è un po' più alto della somma delle classi: la differenza (Milano 2.291 nel 2000, 38.927 nel 2024) sono contribuenti senza reddito complessivo positivo (cedolare secca, forfettari, sole imposte sostitutive).
- **Gini da classi**: curva di Lorenz con un punto per classe (contribuenti e importo di ogni classe), segmenti rettilinei, classe ≤0 esclusa (nel 2017 la classe ≤0 nazionale ha 325.658 contribuenti per -13,5 miliardi, un'anomalia che sposta il Gini di 2,7 punti). **Sottostima la disuguaglianza** perché ignora quella dentro ogni classe: con le classi fini dei file regionali il Gini nazionale è 0,02 più alto (0,439 contro 0,416 nel 2024). Va bene per confronti nel tempo e tra città con le stesse classi, non come valore assoluto, e non è confrontabile con il Gini dell'Istat.
- **Mediana stimata** (colonna `mediana_stimata_*`): interpolazione lineare dentro la classe. Vale ±1-2.000 euro e per Milano cade vicino alla soglia 26.000: non da citare in pagina.
- **Soglie costanti in euro reali** (`soglie_reali.csv`): la quota di contribuenti sopra 26.000 o 55.000 euro del 2000 (spostati con il FOI), con densità uniforme dentro la classe.
- **Contribuenti per 100 abitanti** (Milano): 76,5 (2000), 72,6 (2019), 77,1 (2024). Popolazione al 1° gennaio dell'anno successivo. Il salto 2020-21 nella popolazione di Milano è una correzione di censimento, non demografia.
- **Per tipo**: quota di contribuenti che hanno quel tipo = `_n` / contribuenti; media per percettore = `_eur` / `_n`; autonomo = somma di E-IA, E-IB, E-II fino al 2005; "impresa" = contabilità ordinaria + semplificata.
- **CAP**: media per CAP = somma delle classi / contribuenti del CAP; divario = rapporto tra 90° e 10° percentile delle medie CAP pesate con i contribuenti, e Gini tra CAP (stessa formula, un punto per CAP). Calcolato per tutte le 41 città (`cap_divario_per_citta.csv`) e per Milano con 20121+20122 uniti (stesso risultato: p90/p10 2,41 contro 2,40 nel 2024). Dal 2023 il reddito del CAP è il campo "Reddito complessivo" (completo); prima è la somma delle classi (vedi trappola 6).

## 6. Trappole (verificate sui dati)

1. **Contribuenti non è residenti, e il CAP è un indirizzo fiscale.** Domicilio fiscale al 1° gennaio dell'anno dopo; fuori restano minori, chi non presenta dichiarazione. A Milano 77 contribuenti ogni 100 residenti, a Napoli 56.
2. **Soglie di classe fisse in euro correnti 2000-2024.** Con inflazione (+57% 2000-2024, FOI) e salari nominali che salgono, tanta gente "passa" di classe senza guadagnare di più: la quota sopra 120.000 euro e quella sotto 10.000 sono distorte nel tempo. Per questo `soglie_reali.csv` usa soglie in euro del 2000. Il "16,9% → 33%" del reddito sopra 120.000 euro NON è crescita reale della ricchezza: per Milano il rapporto tra media dei sopra-120k e media generale scende da 11,3 a 6,8 perché la classe si allarga. Da citare solo con la soglia reale.
3. **Riforme fiscali che cambiano cosa c'è dentro il reddito.** (a) Cedolare secca sugli affitti (dal 2011) e IMU al posto dell'IRPEF sulle case non affittate (2012): il reddito da fabbricati di Milano crolla da 1,64 miliardi (2010) a 1,41 (2011) e 0,90 (2012); i contribuenti senza classe di reddito raddoppiano tra 2011 e 2012 (9.687 → 22.610). (b) **Regime forfettario dal 2019** (forfettario introdotto nel 2015 con soglie basse, esteso nel 2019 a 65.000 euro di ricavi e aliquota 15%): chi vi aderisce esce dall'IRPEF ordinaria; gli autonomi milanesi con reddito da lavoro autonomo scendono da 42.909 (2018) a 27.585 (2019), e il reddito medio per autonomo "salta" da 78.800 a 101.800 euro 2025 solo perché restano i più grandi. I forfettari restano tra i "contribuenti" ma senza reddito complessivo (senza classe: 22.364 → 30.239). (c) Riforma IRPEF 2007 (nuove deduzioni al posto della no-tax area) e nuove aliquote 2022/2024: i salti non sono tutti reali. (d) Il 2006 ha un salto (+7,9% nominale a Milano, +5,6% Italia) non spiegato dai dati: cambiano nello stesso anno le voci del lavoro autonomo.
4. **Cambi di definizione delle voci.** 2000-2001 hanno "lavoro dipendente e pensione" come voce a parte e il 2000 ha un "E-II" gonfiato (Milano: 1,76 miliardi nel 2000, 0,09 nel 2001); dal 2008 "dipendente" diventa "dipendente **e assimilati**" (Milano: 455.909 → 495.952 dipendenti da 2007 a 2008); dal 2008 autonomo e impresa "compresi i valori nulli" (cambia la frequenza, non l'importo). La serie per tipo è affidabile **dal 2002 al 2007 e dal 2008 al 2024 in due blocchi**; i confronti per percettore reggono meglio dei totali.
5. **I CAP cambiano contribuenti da un anno all'altro senza motivo economico**: 20122 passa da 20.361 (2015) a 32.776 (2019) contribuenti; 20121 da 16.612 (2022) a 22.090 (2023). Sono cambi di assegnazione dell'indirizzo fiscale, non persone che si spostano. La classifica "CAP più ricco" cambia per questo (2011-2022 il 20121, 2023-24 il 20145 con 14.039 contribuenti). Le misure di divario (p90/p10, Gini tra CAP) resistono, e uniti 20121+20122 danno quasi lo stesso risultato; i confronti di singoli CAP no. I CAP sono anche molto diversi tra città (Roma 72, Messina 43, Genova 43, Milano 38, Bologna 19).
6. **Dati oscurati nei comuni piccoli (importante per Italia e Lombardia).** Il MEF lascia vuote le celle con pochi contribuenti: 2.700-2.900 comuni su 7.900 senza la classe >120k nel 2023-24 (31% dei contribuenti nazionali, contro 3,6% nel 2022). Sommando i comuni si perde il 2,4% del reddito nazionale nel 2023-24 (24.528 contro 25.125 euro di media 2024) e la quota dei redditi >120k risulta 7,9% invece di 9,9%. Fino al 2022 l'errore è invisibile (media -0,1%, controllo su 2016-2022 contro i file regionali). **Stesso problema per i CAP**: nel 2023-24 mancano gli importi di molte classi (>120k) in 11-18 CAP di Milano su 38 (anche grandi, 43.000 contribuenti); la somma delle classi dà 39,995 miliardi nel 2024 contro 42,357 del campo "Reddito complessivo" (-5,6%; Roma -6,2%, Bologna -9,3%). Per questo `analisi.py` usa per il CAP il campo "Reddito complessivo" quando c'è (2023-24) e le quote per classe (>120k, <15k) sono lasciate vuote nei CAP con classi incomplete. Nel 2011 la somma delle classi dei CAP è -1,5% del totale comunale (2011 usa quindi una base un po' bassa: le variazioni 2011-2024 sono sopravvalutate di circa un punto). **Rimedio per Italia/Lombardia**: `italia_lombardia_serie_definitiva.csv` usa la somma dei comuni fino al 2022 e i file per regione (complete) nel 2023-24; "senza Milano" = totale meno Milano (Milano ha tutte le celle). A livello comunale, Milano, Roma, Torino, Napoli, Bologna non hanno celle oscurate in nessun anno. Per il 2000-2015 non c'è un controllo indipendente, ma gli anni 2016-2022 suggeriscono errore trascurabile.
7. **Anno 2017 anomalo a livello nazionale** (classe ≤0 con -13,5 miliardi), 2020 (pandemia: -1,4% nominale in Italia, -1,7% a Milano), 2021-2022 (rimbalzo), 2023-2024 (la disuguaglianza da classi scende in tutte le città insieme: non c'è una causa nei dati, probabili effetti di rinnovi contrattuali e taglio del cuneo fiscale sui redditi bassi, da verificare).
8. **Reddito complessivo non è reddito disponibile né patrimonio**: lordo di imposte, solo ciò che si dichiara in IRPEF. Mancano redditi esenti, imposte sostitutive, evasione, rendite finanziarie tassate separatamente. I più ricchi sono sottostimati, soprattutto in anni di forfettario e cedolare.
9. **Popolazione di Milano pre-2001**: 1.30 milioni (ds71) contro 1.25 milioni dopo il censimento; i rapporti contribuenti/abitanti del 2000-2001 sono falsati verso il basso.

## 7. Numeri principali (tutti da `pulito/riepilogo.txt`)

**Reddito medio per contribuente** (euro correnti | euro 2025), fonte `serie_unita_anno.csv`, `italia_lombardia_serie_definitiva.csv`:

| | 2000 | 2006 | 2010 | 2015 | 2019 | 2022 | 2024 |
|---|---|---|---|---|---|---|---|
| Milano corr. | 22.427 | 29.062 | 30.574 | 32.486 | 34.531 | 37.732 | 40.316 |
| Milano euro 2025 | 35.714 | 40.595 | 39.752 | 39.438 | 40.858 | 40.681 | 40.889 |
| Roma euro 2025 | 30.612 | 33.078 | 33.046 | 31.856 | 32.005 | 31.432 | 31.870 |
| Torino euro 2025 | 28.196 | 30.491 | 29.386 | 29.628 | 30.085 | 29.079 | 29.508 |
| Bologna euro 2025 | 31.476 | 33.920 | 32.771 | 32.608 | 32.874 | 32.320 | 32.761 |
| Napoli euro 2025 | 24.080 | 26.892 | 26.235 | 25.420 | 24.948 | 24.652 | 24.734 |
| Lombardia euro 2025 | 27.838 | 30.143 | 29.291 | 29.397 | 29.853 | 29.371 | 29.838 |
| Italia euro 2025 | 23.199 | 25.366 | 24.765 | 24.771 | 25.173 | 24.867 | 25.482 |

Massimo reale di Milano: 41.888 euro nel 2021. **Milano / Italia (media nominale): 1,54 (2000), 1,60 (2006), 1,61 (2024)**: il vantaggio di Milano è salito di sei punti nei primi anni 2000 e poi è fermo. Lombardia senza Milano: 26.434 (2000) → 28.064 (2024) euro 2025, +6,2%.

**Concentrazione (Milano)**, `serie_unita_anno.csv`:
- Contribuenti sopra 120.000 euro correnti: 1,5% (2000), 2,4% (2006), 3,6% (2019), 4,9% (2024); quota del reddito complessivo da loro dichiarata 16,9%, 24,7%, 29,3%, 33,0%. Roma 8,7% → 18,4%, Torino 8,1% → 14,8%, Bologna 9,4% → 17,1%, Napoli 5,4% → 13,0%, Italia 4,8% → 9,9%, Lombardia 7,6% → 14,5%.
- Soglie in euro reali del 2000: quota di contribuenti sopra 55.000 euro del 2000 (Milano) 6,5% → 9,3%; Italia 2,2% → 2,6%; Roma 4,5% → 6,0%. Sopra 26.000 del 2000: Milano 21,9% → 33,3%, Italia 10,7% → 21,8%.
- Sotto 15.000 euro correnti: 49,4% (2000) → 29,4% (2024) (effetto della soglia nominale: in euro del 2000 la quota sotto 15.000 scende solo da 49,4% a 45,5%). Dato più solido: **un contribuente milanese su cinque dichiara meno di 10.000 euro** anche nel 2024.
- Gini da classi (Milano): 0,501 (2000), 0,528 (2006), 0,543 (2019), 0,553 (2022 massimo), 0,541 (2024). Lombardia senza Milano: 0,400 → 0,386.

**Per tipo di reddito (Milano)**, `tipi_reddito.csv`: quota di contribuenti con quel reddito 2002 / 2010 / 2024: dipendente 48,1% / 50,5% / 59,6%; pensione 36,8% / 36,5% / 27,5%; lavoro autonomo 4,9% / 4,3% / 2,9% (forfettari esclusi dal 2019); impresa 4,0% / 3,1% / 1,8%. Quota del reddito complessivo 2024: dipendente 57,3%, pensione 20,4%, autonomo 6,9%, partecipazione 5,1%, fabbricati 3,0%, impresa 1,9%. Media per percettore 2024 (euro 2025): dipendente 39.316, pensione 30.237, autonomo 96.630 (solo ordinario), impresa 42.047, partecipazione 63.530. Milano/Italia per percettore 2024: dipendente 1,60, pensione 1,33, autonomo 1,41, impresa 1,46.

**CAP di Milano** (`cap_milano_*.csv`, `cap_divario_per_citta.csv`): 38 CAP, media 2024 euro 2025: il più povero 20157 (21.100 euro), poi 20152 (27.250), 20153 (27.494), 20132 (27.552), 20161 (27.611); i più ricchi 20145 (93.778; solo 14.039 contribuenti), 20123 (86.406), 20121 (80.433), 20122 (70.849), 20129 (65.524). Rapporto tra massimo e minimo: 4,7 (2011) → 5,4 (2021) → 4,4 (2024) (sensibile ai cambi di CAP; il minimo è sempre il 20157). Contribuenti sopra 120.000 euro correnti per CAP, 2011 → 2024 (solo CAP con classi complete): 20145 11,6% → 17,5%; 20123 11,5% → 16,1%; 20129 7,0% → 12,5%; 20149 6,2% → 10,9%.

## 8. Cosa potrebbe mostrare una pagina

1. Una linea: reddito medio reale di Milano 2000-2024 (piatto dal 2006), con Italia e le altre città (le due serie in euro 2025, indice 2000 = 100).
2. Chi ha cosa: la curva delle classi di reddito per anno (quanti sotto 10.000, quanti sopra 120.000), con la soglia reale per non ingannare.
3. Mappa dei 38 CAP con il reddito medio reale 2011 → 2024 e cursore; avviso sui CAP che cambiano assegnazione (20121, 20122).
4. Milano contro le altre città nel divario tra CAP (p90/p10): Milano sale fino al 2022, Roma no.
5. I tipi di reddito: dipendenti in crescita, pensionati in calo, pensioni in crescita reale.
6. Pagina di "come leggere" con le trappole 2, 3, 5, 6.

## 9. Cosa non c'è

- Prima del 2000 e per CAP prima del 2011 (e 2012-2014, 2016-2018): non esistono nell'open data MEF.
- Quartieri (NIL): i redditi sono per CAP, non per NIL (già nota dal filone 9).
- Sesso, età, redditi per tipo di contribuente nel dettaglio comune: sono solo nei file nazionali/regionali (`REG_*` e `sesso_*`, non scaricati oltre `REG_calcolo_irpef`).
- Confronto con Istat/Banca d'Italia (reddito disponibile delle famiglie, indagini campionarie): non fatto.
