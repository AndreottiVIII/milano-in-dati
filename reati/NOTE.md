# Reati denunciati - FASE 1 (fonti, scaricamento, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Cartella: `reati/`. Niente pagina web, nessun giudizio, nessun nesso causale. Ogni numero dice file e campo; i numeri del testo sono stampati in `out/riepilogo.txt` e `out/chiavi.txt`. Programmi in `scripts/` (comandi in `STATO.md`), dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`. Nessun account creato, nessun accesso aggirato, nessun git. Su ISTAT circa 25 richieste in un'ora (quelle andate a buon fine con almeno 15 secondi di pausa; alcune in timeout o rifiutate con errore 404/422), User-Agent dichiarato.

**Cosa è e cosa non è questo dato.** Sono i *delitti denunciati dalle forze di polizia all'autorità giudiziaria* (Polizia di Stato, Carabinieri, Guardia di Finanza ecc.), estratti da ISTAT dalla banca dati interforze del Ministero dell'Interno. Non sono i reati commessi, non sono le condanne, non sono le persone coinvolte. Contravvenzioni e illeciti amministrativi non ci sono.

## 1. In breve

1. **La fonte aperta c'è e basta: ISTAT (esploradati, dataflow `DCCV_DELITTIPS`, CC BY 4.0).** Serie annuale **2006-2024** per Italia, province, 12 grandi comuni, 56 tipi di delitto, sia come numero di denunce sia come tasso per 100.000 abitanti. Il Comune di Milano ripubblica gli stessi numeri per il comune (`ds564`, CC-BY, 2004-2023): **tutte le 1.000 righe 2006-2023 coincidono con ISTAT**, ma il Comune aggiunge **2004 e 2005** (solo per il comune; per le province prima del 2006 non esiste una serie).
2. **Il Ministero dell'Interno non ha dati aperti per provincia.** I dati 2025 che ha dato in esclusiva al Sole 24 Ore (indice del 12/10/2026) non sono scaricabili; ISTAT arriva al 2024. Non ho trovato altro (due ricerche web; il sito dell'Ufficio centrale di statistica indica l'indagine INT 00062 ma non l'ho esplorato oltre).
3. **A livello più piccolo del comune non esiste nulla di aperto.** Nel catalogo del Comune (CKAN, 20 parole chiave: reati, sicurezza, polizia locale, incidenti, denunce, delitti, criminalità, furti, pendolari, popolazione presente...) c'è un solo dataset sui reati (ds564, per tipo, solo comune intero). Nessun dato per municipio o quartiere: né reati, né interventi della polizia locale (c'è solo l'elenco dei comandi decentrati, ds1302). Incidenti stradali sì (ds175-179, per municipio dal 2020) ma sono un altro tema.
4. **Milano (provincia, confini attuali) è prima per tasso totale dal 2010 secondo la serie pubblicata, ma il primato dipende dai confini (correzione del 1/11 sera):** con Milano e Monza e Brianza sommate dal 2011 (come erano fino al 2010) il rango è 1º nel 2011 e nel 2023, ma 2º-4º negli altri anni (3º nel 2024: 6.276 contro Firenze 6.567 e Roma 6.434; `riepilogo_rango_milano.csv`, colonna `rango_milano_con_monza`). Serie pubblicata: Milano è prima tra le province per tasso totale dal 2010 (103 province nel 2010; 106 dal 2011), con l'eccezione del 2015 (seconda dopo Rimini). Nel 2006 era quarta, nel 2007 terza, nel 2008-2009 seconda (dietro Rimini). Nel 2024: Milano **6.989** denunce ogni 100.000 abitanti, Firenze 6.567, Roma 6.434, Bologna 6.108, Rimini 6.042 (`pulito/riepilogo_rango_milano.csv`). Italia: 4.070.
5. **Il "primato" è fatto di furti e danneggiamenti, non di reati contro la persona.** Differenza tra il tasso del comune di Milano (10.343) e quello italiano (4.070) nel 2024: 6.273 ogni 100.000, di cui furti 65,7%, danneggiamenti 13,0%, truffe e frodi informatiche 4,5%, rapine 3,3% (`riepilogo_scomposizione_divario.csv`). Omicidi volontari consumati: tasso del comune di Milano 0,8 volte quello italiano nel 2024 (6 casi; 22 nel 2006).
6. **Il numero assoluto di denunce nel comune è tornato dove era nel 2004**: 141.636 (2004), picco 174.040 (2007), minimo 94.796 (2020), 140.974 (2024): -0,5% sul 2004, -19,0% sul picco. Il tasso per 100.000 (ISTAT) del comune: 13.025 (2006) -> 10.343 (2024), -20,6%; Italia nello stesso periodo -14,2%.
7. **Covid: il calo è stato più forte a Milano che in Italia** (2020 su 2019, tasso totale: comune -30,6%, provincia -27,2%, Firenze -31,1%, Roma -18,0%, Italia -17,0%), soprattutto per i furti con destrezza (-49,2%) e i furti in generale (-43,3% contro -32,3% in Italia). Nel 2022 il comune era già sopra il 2019 (10.691 contro 9.829).
8. **Cosa cresce dal 2019 al 2024 nel comune di Milano** (tasso per 100.000): violenze sessuali +70,1% (267 -> 442 denunce; Italia +41,7%), rapine +59,2% (2.259 -> 3.499), furti con strappo +53,4%, furti di motocicli +53,1%, percosse +38,9%, delitti informatici +94,0% (655 -> 1.236). **Cosa scende:** furti in abitazione -34,5%, furti in auto in sosta -25,9%, furti di ciclomotori -24,4%, furti di autovetture -18,1%. Sul lungo periodo (2006-2024) furti in auto in sosta -62,6%, furti di autovetture -77,7%, furti in generale -30,5%; truffe e frodi informatiche **+145,7%** (3.926 -> 10.455 denunce, da 2,4% a 7,4% del totale).
9. **Turisti e pendolari spiegano poco o molto a seconda di cosa si guarda** (sezione 5): i turisti, in media giornaliera, sono il 3,3% dei residenti nel comune di Milano nel 2024 (3,6% nella provincia di Firenze, 3,1% in quella di Roma); i pendolari in entrata a Milano al censimento 2011 erano 474.680 (saldo con le uscite +384.617, il 28% dei residenti). Con il saldo dei pendolari 2011 più i turisti il tasso del comune 2024 passa da 10.343 a 7.863, valore vicino al tasso del comune di Roma calcolato sui soli residenti (7.906); ma per Roma non ho la stessa correzione, quindi il confronto non è completo. Il dato dei pendolari è del 2011 e solo per Milano.
10. **La cosa più sorprendente** (sezione 7): le denunce del comune sono tornate al livello di vent'anni fa, ma Milano resta prima, perché negli altri posti sono calate di più; e nel 2020, quando la gente era a casa, le denunce sono scese del 31% (-49% i borseggi): i numeri seguono le persone che ci sono, più che quelle che ci abitano.

## 2. Fonti, una per una (anche in `pulito/inventario_fonti.csv`, con sha256)

### 2.1 ISTAT, esploradati (SDMX), "Delitti denunciati dalle forze di polizia all'autorità giudiziaria" - `DCCV_DELITTIPS`
- Endpoint `https://esploradati.istat.it/SDMXWS/rest/data/IT1,<dataflow>,1.0/<chiave>` (formato `application/vnd.sdmx.data+csv`). Ultimo aggiornamento del dataflow: 3/3/2026 (annotazione `LAST_UPDATE`). Licenza ISTAT: CC BY 4.0 (la pagina delle condizioni non è stata riletta oggi: **non verificato**; vale per i dati ISTAT in generale).
- Dataflow usati (tutti `IT1,73_67_DF_DCCV_DELITTIPS_n`):

| n | contenuto | dimensione | file in `raw/istat/` |
|---|---|---|---|
| 1 | numero di denunce (`CRIMEN`), per territorio e tipo | 7 aree x 56 tipi; 6 comuni x 56 tipi; totale per 242 aree | `df1_CRIMEN_7aree_tutti_tipi.csv`, `df1_CRIMEN_6comuni_tutti_tipi.csv`, `df1_CRIMEN_tutte_aree_TOT.csv` |
| 9 | tasso per 100.000 abitanti (`CRIMET`), tutte le province, 56 tipi | 140.798 righe | `df9_CRIMET_tutte_aree.csv` |
| 8 | tasso per 100.000, 12 grandi comuni (Torino, Milano, Genova, Venezia, Verona, Bologna, Firenze, Roma, Napoli, Bari, Catania, Palermo) | 12.684 righe | `df8_grandi_comuni_CRIMET.csv` |
| 5 | % di delitti con autore scoperto, grandi comuni (`CRIMEP`) | scaricato, **non usato** | `df5_grandi_comuni_CRIMEN.csv` (il nome inganna: contiene CRIMEP) |

- Altri dataflow esistono (`_3`, `_4`, `_6`, `_7`: delitti "con autore noto", per periodo del commesso delitto) e il dataflow `DCCV_AUTVITTPS` (autori e vittime, con sesso, età e **cittadinanza**). **Non scaricati**: l'indicazione era di non usare la cittadinanza degli autori, e questa analisi non ne ha bisogno.
- Anni: 2006-2024 per tutti. Territori: Italia, ripartizioni, regioni, 103 province nel 2006-2010, 106 dal 2011 (nascono Monza e Brianza, Fermo, Barletta-Andria-Trani). Tipi: 56 voci (totale + voci di dettaglio **selezionate**, nota ISTAT: "le voci di dettaglio sono solo una selezione delle più rilevanti"); `Ingiurie` solo fino al 2017.
- Mancano in questi dataflow, pur presenti nei codici ISTAT (`CL_REATI_PS`): maltrattamenti contro familiari e conviventi (CP572), atti persecutori (CP612bis), reati contro la pubblica amministrazione. Quindi **violenza domestica e stalking non si vedono** in queste tabelle.
- Non ottenuta: popolazione residente ISTAT (`DCIS_POPRES1`, `DCIS_RICPOPRES2011`): il server ha risposto con timeout (3 tentativi) e 404 (1). **Ho usato il denominatore implicito**: popolazione = denunce / tasso x 100.000, dal totale. Controllo: usando i furti al posto del totale lo scarto massimo è 0,004% su 247 casi. Il tasso "per 100.000" del file pulito è calcolato da me con quel denominatore (`per_100mila`); il valore pubblicato da ISTAT è accanto (`per_100mila_pubblicato_istat`).

### 2.2 Comune di Milano, open data (CKAN `dati.comune.milano.it`)
- Ricerca `package_search`, 20 parole chiave, risultati in `raw/probe/comune_search.json` e `comune_search2.json`. Licenza dichiarata: `license_id = cc-by` (versione non scritta). Citare "Comune di Milano - dati.comune.milano.it".
- **ds564 "Reati denunciati all'autorità giudiziaria dalle forze di polizia (2004-2023)"**: 1.120 righe = 20 anni x 56 tipi, solo comune di Milano. Origine dichiarata: milanostatistica.comune.milano.it - Sicurezza e giustizia. File `raw/comune_ds564/ds564_reati_denunciati_2004_2023.csv`; risorsa del 16/10/2024, scheda modificata l'8/5/2026.
- **ds395 / ds345** (Censimento 2011): pendolari in entrata a Milano per comune di origine, mezzo, orario (ds395, 65.846 righe, stime) e in uscita per destinazione (ds345). Servono solo per la sezione 5.
- Turisti: `turisti/pulito/riepilogo_italiani_stranieri.csv` (presenze del comune, Comune di Milano ds211-ds213, vedi `turisti/NOTE.md`). ISTAT `122_54_DF_DCSC_TUR_7` (notti per provincia, `raw/istat/tur7_6aree.csv`) per Roma, Torino, Napoli, Bologna, Firenze: **Milano non c'è nel dataflow ISTAT**, per Milano si usa il Comune (comune, non provincia).

### 2.3 Ministero dell'Interno e Sole 24 Ore
- Nessun portale di dati aperti raggiunto (`dati.interno.gov.it`: il nome non si risolve, errore DNS). L'Ufficio centrale di statistica (`ucs.interno.gov.it`) elenca l'indagine INT 00062 "delitti denunciati all'autorità giudiziaria" con livello provinciale; non ho trovato file scaricabili e non ho insistito.
- L'indice della criminalità del Sole 24 Ore usa la banca dati interforze del Dipartimento di Pubblica sicurezza, data in esclusiva (LaPresse 12/10/2026, letta oggi via WebFetch). Edizione 2026 (dati 2025): Milano "supera quota 7.000" denunce per 100.000, +0,6% sul 2024; Firenze 6.374; Roma -5,3%; Italia circa 2,36 milioni di delitti, -1,8%. **Coerenza con ISTAT**: 6.989 x 1,006 = 7.031. Non verificato sulla fonte primaria.

## 3. Cosa c'è nelle tabelle pulite (`pulito/`)

| file | contenuto |
|---|---|
| `delitti_tipo_territorio_anno.csv` | tidy: anno, territorio, livello, tipo, gruppo, denunce, per 100.000 (mio), per 100.000 (ISTAT), popolazione implicita. Italia, Milano/Roma/Torino/Napoli/Bologna/Firenze provincia, gli stessi 6 comuni, Monza (solo totale), Milano+Monza ricostruita (solo totale). 13.760 righe |
| `province_totale_anno.csv` | tutte le province: totale, tasso ISTAT, rango per anno (1999 righe) |
| `milano_comune_ds564.csv` | comune di Milano 2004-2023 dal Comune, con tasso su residenti anagrafici (ds27) e confronto con ISTAT |
| `riepilogo_*.csv` | totale 100k, rango (province e grandi comuni), tipi per territorio, variazioni, Covid, presenti, scomposizione del divario, turisti per residente |
| `riepilogo.json`, `controlli_build.txt`, `inventario_fonti.csv` | numeri chiave, controlli, inventario |

Raggruppamenti per la lettura (miei, in `build.py`, colonna `gruppo`): furti, rapine, contro la persona, sessuali, frodi e informatici, stupefacenti, altro. "Reati violenti" non esiste come voce in questi dataflow: non l'ho costruito.

## 4. Numeri principali (fonte: `pulito/*.csv`, stampati in `out/riepilogo.txt`)

**Totale delitti per 100.000 (ISTAT; provincia):**

| anno | Milano | Milano+Monza (ricostruita) | Roma | Torino | Napoli | Bologna | Firenze | Italia |
|---|---|---|---|---|---|---|---|---|
| 2006 | 7.648 | 7.648 | 7.014 | 7.614 | 4.716 | 8.020 | 6.447 | 4.746 |
| 2010 | 7.089 | 7.089 | 5.906 | 6.640 | 4.078 | 6.478 | 5.603 | 4.382 |
| 2011 | 8.576 | 7.518 | 6.330 | 6.840 | 4.321 | 6.977 | 5.688 | 4.603 |
| 2019 | 6.743 | 5.979 | 5.167 | 5.211 | 4.262 | 5.858 | 6.254 | 3.854 |
| 2020 | 4.906 | 4.420 | 4.239 | 4.285 | 3.668 | 4.633 | 4.309 | 3.198 |
| 2024 | 6.989 | 6.276 | 6.434 | 5.866 | 4.489 | 6.108 | 6.567 | 4.070 |

(Il salto di Milano tra 2010 e 2011 non è reale: vedi limiti dei dati, punto 3. Nelle colonne "provincia" i valori 2006-2010 includono Monza e Brianza, quelli dal 2011 no.)

**Grandi comuni, tasso totale 2024:** Firenze 11.422, Milano 10.343, Bologna 9.973, Torino 9.170, Venezia 9.092, Roma 7.906, Catania 7.484, Verona 6.667, Napoli 6.521, Genova 5.692, Palermo 5.384, Bari 4.616. **Milano comune è prima tra i 12 in 13 anni su 19**; seconda nel 2013, 2018, 2019, 2023 e 2024 (dietro Bologna nel 2013, Firenze negli altri quattro) e terza nel 2020. Il comune e la provincia non sono la stessa cosa: nel 2024 il comune ha il 62% delle denunce della provincia e il 42% degli abitanti.

**Per tipo, 2024, per 100.000 (Milano comune / Milano provincia / Roma provincia / Italia):** furti 5.912 / 3.720 / 3.682 / 1.789; furti con destrezza 1.557 / 791 / 792 / 239; rapine 257 / 138 / 81 / 49; rapine in pubblica via 156 / 81 / 48 / 28; violenze sessuali 32,4 / 21,3 / 12,1 / 11,6; truffe e frodi informatiche 767 / 620 / 538 / 485; stupefacenti 163 / 93 / 107 / 56; danneggiamenti 1.290 / 970 / 626 / 472; omicidi volontari consumati 0,4 / 0,5 / 0,5 / 0,6; lesioni dolose 162 / 127 / 111 / 114. Nel 2024 il tasso di furti della provincia di Roma (3.682) è quasi uguale a quello della provincia di Milano (3.720), e il tasso di furti con destrezza è lo stesso (792 e 791).

**Denunce assolute, comune di Milano** (ds564 + ISTAT 2024; `out/chiavi.txt`): totale 141.636 (2004), 163.817 (2006), 174.040 (2007), 164.569 (2011), 137.709 (2019), 94.796 (2020), 144.864 (2023), 140.974 (2024). Furti 96.128 (2004) -> 80.580 (2024). Furti con destrezza 22.970 (2006), 22.685 (2019), 21.215 (2024), circa 58 al giorno. Truffe e frodi informatiche 3.163 (2004) -> 10.455 (2024). Omicidi volontari consumati: 22 nel 2004, 22 nel 2006, 8 nel 2019, 6 nel 2024.

**Covid** (variazione del tasso totale 2020 su 2019 e 2024 su 2019; `riepilogo_covid.csv`): comune di Milano -30,6% / +5,2%; provincia di Milano -27,2% / +3,6%; Roma prov. -18,0% / +24,5%; Torino -17,8% / +12,6%; Napoli -13,9% / +5,3%; Bologna -20,9% / +4,3%; Firenze -31,1% / +5,0%; Italia -17,0% / +5,6%. Nel 2024 Roma e Torino (province) sono molto sopra il 2019; Milano no.

## 5. Residenti, turisti, pendolari: il confronto "per presenti"

Tutto in `pulito/riepilogo_presenti_milano.csv` e `riepilogo_turisti_per_residente.csv`.
- **Turisti** (notti / 365 = presenti medi al giorno). Comune di Milano: 19.300 (2006), 35.469 (2019), 9.652 (2020), 45.181 (2024) = 3,3 ogni 100 residenti nel 2024 (1,5 nel 2006). Province ISTAT, 2024: Firenze 3,6, Roma 3,1, Bologna 1,6, Napoli 1,3, Torino 0,8, Italia 2,2. Il peso medio dei turisti sul numero di persone è piccolo ovunque; ma un'attenzione: è una media annua, e i turisti si concentrano in alcune zone e periodi.
- **Pendolari** (censimento 2011, ds395 e ds345, stime, solo Milano): 474.680 persone che entrano ogni giorno per studio o lavoro (367.953 lavoro, 106.727 studio, di cui 259.807 dalla provincia di Milano), 90.063 che escono; saldo +384.617. Dato di 15 anni fa, tenuto costante: serve a dare l'ordine di grandezza, non una serie.
- **Tasso del comune di Milano 2024 per 100.000 persone:** sui residenti 10.343; residenti + turisti 10.011; residenti + turisti + saldo pendolari 2011 7.863; residenti + turisti + tutti i pendolari in entrata 7.487. Stesso calcolo nel 2019: 9.829 / 9.586 / 7.562 / 7.205. Roma comune sui soli residenti: 7.906; non ho il saldo dei pendolari di Roma né degli altri comuni (il censimento 2011 per tutti i comuni è un file grande, non scaricato).
- **Cosa dice e cosa no.** Dividere per i presenti riduce il tasso di Milano di un quarto circa; non si può dire se Milano resti prima, perché non ho la stessa correzione per le altre città; e non si può dire quanti dei reati vedano coinvolti proprio i pendolari o i turisti.

## 6. Limiti dei dati (da riportare tutti sulla pagina)

1. **Denunciato non è commesso.** Contano solo i reati che qualcuno denuncia e che la polizia registra: dipendono dalla fiducia, dall'obbligo di denuncia per l'assicurazione (furti, borseggi), dalla facilità di denunciare (anche online), dalla presenza di strumenti per farlo. Un aumento di denunce può essere più denunce, più reati o entrambe le cose. Le indagini ISTAT sulla sicurezza dei cittadini (vittimizzazione) misurano quanto è sommerso: **non usate qui**. Il "primato" di Milano può derivare anche da una maggiore propensione a denunciare; i dati non permettono di separarla.
2. **Provincia non è città.** I tassi "provinciali" (quelli del Sole 24 Ore) mescolano circa 130 comuni (Milano città: 62% delle denunce, 42% degli abitanti). Il comune ha tassi di 1,5 volte quelli della provincia. Dare il tasso in "province" e in "città" è un'altra misura, non un errore.
3. **Salto di confine Milano/Monza nel 2011.** Fino al 2010 la provincia di Milano include Monza e Brianza (popolazione implicita 3,89 milioni nel 2010); dal 2011 no (3,08 milioni; Monza e Brianza 0,84 milioni: `IT108`). Il tasso "pubblicato" sale da 7.089 (2010) a 8.576 (2011) solo per questo. Ho ricostruito Milano+Monza dal 2011 sommando le due province (7.518 nel 2011, 6.276 nel 2024). Per i tipi di delitto non ho ricostruito la serie (Monza è disponibile solo come totale): per i tipi confrontare 2011-2024 o usare il comune.
4. **Denominatore e censimento 2011.** Nota di ISTAT sul dataflow dei tassi: lo scarto tra popolazione censita (9/10/2011) e anagrafica ha portato a un "notevole recupero" di residenti reiscritti nel 2012-2013 e quindi a un rialzo della popolazione "non dovuto a fenomeni reali"; ISTAT stessa suggerisce di leggere gli andamenti con i dati assoluti. Nel comune di Milano il denominatore implicito ISTAT è 1,253 milioni (2010) e 1,346 milioni (2015), mentre la somma delle età di ds27 (anagrafe comunale) è 1,323 e 1,360 milioni. Il calo 2011-2024 del comune: -14,3% sulle denunce assolute, circa -17% sul tasso con i residenti anagrafici (ds564 2011 -> 2023), -20,2% sul tasso ISTAT. Citare più misure, non una.
5. **Le cifre sono congelate alcuni mesi dopo la fine dell'anno** (nota ISTAT: estratte dalla banca dati operativa dopo alcuni mesi, poi non aggiornate; per gli omicidi di matrice mafiosa i cambiamenti successivi possono essere rilevanti). I numeri del Viminale/Sole 24 Ore, consolidati più tardi, possono differire di poco.
6. **Luogo del reato.** Il dato è per territorio in cui è stato commesso il delitto (così le tavole storiche ISTAT, "per provincia del commesso delitto"; non riletto nei metadati attuali), non per residenza di vittima o autore. Per Milano significa che reati ai danni di non residenti, pendolari e turisti contano in Milano.
7. **Tipi di delitto.** Voci di dettaglio selezionate; non ci sono maltrattamenti in famiglia e stalking (sono nei codici ISTAT, non in questi dataflow); le "ingiurie" finiscono nel 2017 (il Comune lascia il vuoto dal 2018); `Altri delitti` è una voce residua (13% del totale a Milano). "Furti" include voci non tutte distinte (non c'è il totale di "furti in strada").
8. **Difetti del file del Comune (ds564), corretti da me e dichiarati.** (a) Una riga "2009 - Omicidi volontari totale - 8" è in realtà del 2019 (compare nel blocco 2020-2018 alla riga 227; il 2009 ha già 22, che coincide con ISTAT; il 2019 manca, e ISTAT dà 8): riattribuita nel programma `build.py`. (b) Per 2004 e 2005, 15 voci di dettaglio per anno (furti per tipo, rapine per tipo) sono "non disponibile". (c) Contrabbando 2017-2018 e ingiurie 2018-2023 vuoti. (d) Lettere accentate sostituite da `?` in due voci. Per il resto il file coincide con ISTAT in tutte le 1.000 righe confrontabili.
9. **Le serie lunghe hanno cambiato modo di registrare.** Le denunce online e i canali di segnalazione sono cambiati nel tempo (non verificato in questi dati): non attribuire i salti di una voce (ad esempio truffe e frodi informatiche +146% dal 2006) a "più truffe" senza dire che è cambiato anche il modo di denunciare.
10. **Turisti.** ISTAT conta solo le strutture ricettive registrate; dal 2025 include anche le locazioni brevi non imprenditoriali (nota in `turisti/NOTE.md`): fino al 2024 non c'è effetto. Per Milano si usa il comune (Comune di Milano), per gli altri la provincia ISTAT: misure non perfettamente confrontabili.
11. **Pendolari.** Dato del censimento 2011, stime, tenuto costante; saldo con uscite da dataset diverso (ds345, conteggio, ds395 stima). Solo Milano. Non include studenti fuorisede residenti altrove, city users occasionali, lavoratori in nero o altro.
12. **Niente cittadinanza.** Il dato è in ISTAT per autori e vittime (DCCV_AUTVITTPS) ma non è stato scaricato né usato, per scelta. Nessun dato pulito qui permette di collegare i reati alla nazionalità; la pagina non deve farlo.
13. **Nessuna causa.** I dati non dicono perché le denunce salgono o scendono. Non attribuire variazioni a politiche, eventi, amministrazioni o categorie di persone.

## 7. La cosa più sorprendente

**Il numero di denunce nel comune di Milano nel 2024 (140.974) è praticamente uguale a quello del 2004 (141.636)** e il 19% sotto il picco del 2007 (174.040): in vent'anni è tornato dove era partito, mentre i residenti anagrafici sono cresciuti di circa 120.000 (1,298 milioni nel 2004, 1,418 milioni nel 2023, ds27). Eppure Milano (provincia, confini attuali) è "prima" dal 2010 nella serie pubblicata, anche se con Monza sommata il rango cambia (vedi punto 4 della sezione 1): altrove le denunce sono scese ancora di più (tasso 2006 -> 2024: Rimini 8.357 -> 6.042, Genova 8.032 -> 4.865, Bologna 8.020 -> 6.108, Italia 4.746 -> 4.070). Il primato dice quanto è alto il tasso rispetto agli altri, non che sia in aumento.

Due cose in più che cambiano la lettura. (1) Il divario con l'Italia è quasi tutto furti (65,7%) e danneggiamenti (13,0%); i reati contro la persona pesano poco: nel 2024 6 omicidi volontari consumati nel comune, tasso 0,8 volte quello italiano. (2) Il 2020 mostra che il numero segue le persone presenti più di quelle residenti: con la gente a casa le denunce del comune scendono del 30,6% (borseggi -49,2%), contro -17,0% in Italia.

## 8. Cosa può mostrare una pagina (non fatta)

1. **Linea del tasso totale 2006-2024**: Milano (provincia ricostruita con Monza e comune), Roma, Torino, Napoli, Bologna, Firenze, Italia; evidenziare il buco 2020 e il pareggio degli ultimi anni; didascalia sul salto Monza e sul denominatore.
2. **Classifica delle province anno per anno** (bump chart: Milano da 4ª a 1ª tra 2006 e 2010), con avviso che è una classifica di *denunce*, e un secondo grafico dei 12 grandi comuni (dove Firenze supera Milano in cinque anni).
3. **Da cosa è fatto il divario**: barra a pile del tasso Milano comune/provincia contro Italia per gruppi (furti, danneggiamenti, frodi, rapine, persona, altro).
4. **Chi sale e chi scende** (2006, 2019, 2024): furti in auto, auto rubate e furti in casa giù; violenze sessuali, rapine, scippi, delitti informatici e frodi su.
5. **Il 2020 come esperimento involontario**: calo per tipo di delitto, Milano contro Italia.
6. **Per residenti, per presenti**: tre barre (solo residenti, + turisti, + pendolari) per Milano, con tutti i limiti dei dati della sezione 6 sopra il grafico.
7. **Assenti per scelta**: nazionalità, causalità, mappe per quartiere (non esistono dati aperti).

## 9. Da decidere / non fatto
- Popolazione ISTAT ufficiale (`DCIS_POPRES1`) al posto del denominatore implicito: riprovare quando il server risponde (≤5 richieste al minuto).
- Pendolari 2011 di tutti i comuni (file `DF_BULK_PEND_LAV_2021_1` del censimento 2021 / bulk 2011) per fare il confronto "per presenti" anche con Roma, Firenze, Bologna.
- Provincia di Milano per tipo ricostruita con Monza (richiede Monza per tipo: richiesta ISTAT in più).
- Serie pre-2006 (1983-2003, `DF_BULK_CRIMESINTO`) per Italia/regioni: esiste; non scaricata (ci sarebbe un cambio di classificazione).
- Dati 2025 del Viminale: non aperti; se il Sole 24 Ore pubblica la tabella per provincia, si può citare ma non scaricare.
- Chiedere al Comune (milanostatistica) se esistono dati per municipio; qui nessuno.
