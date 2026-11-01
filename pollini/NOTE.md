# Pollini e allergie - FASE 1 (raccolta, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web. Ogni numero dice file e campo. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di pollini> [<percorso assoluto di milano-in-dati>]` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`.

## 1. In breve

1. **Per Milano città non esiste una serie giornaliera scaricabile.** Il monitoraggio non lo fa ARPA Lombardia ma ATS Città Metropolitana di Milano (stazioni di Milano, Legnano, Rho, Magenta, Lodi). Pubblica solo il bollettino della settimana in corso (PDF, a classi: assente/bassa/media/alta) e un calendario pollinico 2016-2025. Nessun archivio storico numerico online.
2. **La Lombardia non è in POLLnet** (la rete aperta dell'ISPRA): 72 stazioni, 21 tra regioni ed enti, nessuna lombarda. Il dataset aperto Socrata di Regione Lombardia non contiene pollini dell'aria (la ricerca "pollini" trova solo il Friuli Venezia Giulia (ARPA FVG, altra regione); "polline" trova il miele).
3. **Quello che c'è, aperto e in blocco (CC-BY 4.0): POLLnet, stazioni vicine a Milano.** Novara (45 km dal Duomo, 2007-2026), Piacenza (59 km, 2007-2026), Vercelli (63 km, 2012-2019), Alessandria (75 km, 2010-2026), Omegna (77 km, 2008-2026), Verona (141 km, 2010-2026). Sono "la pianura padana attorno a Milano", **non Milano**: ogni risultato va letto così.
4. **Per Milano ci sono solo numeri di testata** (da note di Regione Lombardia): massimo giornaliero e totale stagionale dell'Ambrosia per stazione, anni 2016, 2024, 2025. Milano: 2024 massimo 39, totale 428; 2025 massimo 12, totale 183 granuli/m3.
5. **Letteratura (solo contesto):** Sci. Rep. 2026, Legnano 1995-2022 (graminacee, urticacee, artemisia, ambrosia): le stagioni cominciano prima con più temperatura; i dati sono "su richiesta all'autore".

## 2. Fonti, una per una (anche in `raw/` e `pulito/stazioni.csv`)

### 2.1 POLLnet - ISPRA / SNPA (usata per i numeri)
- Cosa: rete italiana di monitoraggio aerobiologico (ISPRA + ARPA/APPA). Concentrazioni medie giornaliere in pollini o spore per m3 d'aria, per taxon (livelli: 1 totale, 2 famiglia, 3 genere/specie). Pagina: https://pollnet.isprambiente.it/opendata/ ; servizio WFS `https://sdi.isprambiente.it/geoserver/om/ows`, layer `om:Concentrazione_pollini_spore`, `om:Stazioni_POLLnet`, `om:Pollini_spore`, `om:Regioni`.
- **Licenza: CC-BY 4.0** (dichiarata sulla pagina "opendata" del sito POLLnet). Si possono ripubblicare i dati citando "ISPRA - POLLnet (SNPA)".
- Scaricato il 1/11/2026 [scripts/scarica_pollnet.py]: 810.500 righe (102 MB di CSV) per 6 stazioni, nessuna registrazione, nessun account. Elenco stazioni e coperture in `pulito/stazioni.csv`.

| Stazione | Codice | Km dal Duomo | Primo giorno | Ultimo giorno |
|---|---|---|---|---|
| Novara | NO1 | 44,6 | 2007-01-01 | 2026-10-18 |
| Piacenza | PC1 | 59,2 | 2007-02-11 | 2026-10-25 |
| Vercelli | VC1 | 62,9 | 2012-03-28 | 2019-12-15 |
| Alessandria | AL6 | 75,4 | 2010-12-31 | 2026-11-01 (*) |
| Omegna | VB1 | 77,1 | 2008-02-25 | 2026-10-25 |
| Verona | VR1 | 141,1 | 2010-02-01 | 2026-10-25 |

(*) Alessandria ha 306 righe con date future (2-8 novembre 2026): scartate.
- Taxa: 44 famiglie e circa 33 generi; per l'analisi uso 11: Corylus, Alnus, Cupressaceae/Taxaceae, Betula, Platanaceae, Fraxinus, Quercus, Gramineae, Urticaceae, Artemisia, Ambrosia. Classi di riferimento POLLnet (limiti basso/medio/alto) in `raw/ispra/pollini_spore.csv`.
- Altre stazioni dell'elenco ma non scaricate: Torino (dal 12/2025), Bolzano, Treviso, Padova, Bologna ecc. Per ricostruire altre stazioni basta `scarica_pollnet.py <raw/ispra> <id>`.
- Cosa manca: Milano e tutta la Lombardia; stazioni prima del 2006; metodo di conteggio per stazione e anno (non nel dataset).

### 2.2 ATS Città Metropolitana di Milano (solo contesto e testata)
- Pagina: https://www.ats-milano.it/ats/carta-servizi/guida-servizi/ambiente/igiene-urbana-sanita-pubblica/pollini-spore (salvata in `raw/ats_milano/`). Dice "quattro stazioni" (tre ATS e una con il Policlinico), ma i bollettini sono cinque (Milano, Legnano, Rho, Magenta, Lodi): la pagina non è coerente.
- Bollettino settimanale (PDF, una pagina per stazione, classi, solo l'ultimo): Milano, settimana 19-25/10/2026: graminacee, pinacee, urticacee e Alternaria "basse", il resto "assente". `raw/ats_milano/bollettini/`.
- **Calendario pollinico di Milano e provincia, elaborazione 2016-2025** (PDF con tabella a decadi e classi di colore): `raw/ats_milano/bollettini/Calendario pollinico 2026_0.pdf`. Letto a occhio: rosso (alta) per il cipresso tra febbraio e marzo, per la betulla in aprile, per il platano a inizio aprile, per le graminacee da fine aprile a giugno, per l'ambrosia in agosto.
- Licenza: non dichiarata sul sito. Non ripubblicare i PDF; si citano pagina e data.
- Cosa manca: ogni serie giornaliera o storica. Richiesta possibile a pollini@ats-milano.it (non fatta).

### 2.3 Regione Lombardia - note sull'ambrosia (solo numeri di testata)
- Note annuali della Direzione Welfare alle ATS con massimo giornaliero e totale stagionale di polline di Ambrosia per stazione (granuli/m3). Tre trovate: **2016** (solo massimi, senza Milano), **2024** (nota del 30/4/2025, ATS Insubria prot. 0046901) e **2025** (allegato 1, nota di luglio 2026, copia sul sito del Comune di Rescaldina prot. 14804). Estratti in `pulito/ambrosia_regione_lombardia.csv` [scripts/regione_ambrosia.py]; i PDF sono in `raw/regione_ambrosia/` (copie ospitate da Comuni e ATS, non dalla Regione).
- Tre testi dicono la stessa cosa: dal 2013 il coleottero *Ophraella communa* (arrivato per caso) mangia l'ambrosia e ha fatto scendere il polline; negli ultimi anni l'insetto è diminuito e la pianta e il polline sono risaliti (nota 2024); il 2025 ha avuto "una generale cospicua diminuzione" rispetto al 2023-24, che la nota 2025 attribuisce a più piogge tra luglio e settembre, agli interventi di contenimento e al coleottero.
- Licenza: atti amministrativi pubblici, nessuna licenza dichiarata. Ho preso solo i numeri (fatti).
- Cosa manca: tutti gli anni 2017-2023; il metodo di conteggio per stazione.

### 2.4 Portale dati.lombardia.it
- Ricerca nel catalogo API (il catalogo del portale copre anche altri portali Socrata, per cui compare il Friuli) (10 parole: pollini, pollen, aerobiologia, aerobiologico, spore, polline, ambrosia, graminacee, betulla, allergeni): `raw/dati_lombardia/ricerca_catalogo.json` [scripts/cerca_dati_lombardia.py]. Unico dataset pertinente nel nome: "Analisi Palinologica del Polline in Apiari Lombardi" (ERSAF, id 3wjv-dd3u, analisi dei mieli: non è polline in aria). ARPA Lombardia non ha un dataset di pollini.

### 2.5 Letteratura (solo contesto, non scaricata)
- "Effects of climate change on pollen season features of herbaceous species in the Milan area, Northern Italy", Scientific Reports, 27/2/2026, https://doi.org/10.1038/s41598-026-41641-w (ATS Milano + Università di Milano-Bicocca). Stazione di Legnano, 1995-2022, graminacee/urticacee/artemisia/ambrosia/cannabacee/chenopodiacee. Più temperatura e radiazione: inizio stagione anticipato (solo graminacee e urticacee); più temperatura: durata più lunga (ambrosia, urticacee). Proiezione: inizio fino a 2 settimane prima in 60 anni. Dati "a richiesta". Licenza CC BY-NC-ND 4.0: solo citazione. Copia della pagina in `raw/letteratura/` (non ripubblicare).
- ISPRA, "Stato e trend dei principali pollini allergenici in Italia (2003-2019)", Rapporto 338/2021 (non letto per intero: non dice nulla di Lombardia/Milano nella scheda).

## 3. Pulizia (`scripts/build.py`, esiti in `pulito/controlli_pulizia.json`)

`pulito/concentrazioni_giornaliere.csv` (790.260 righe, 45 MB, separatore `;`): `data;stazione;codice_stazione;stat_id;taxon;livello;gruppo;granuli_m3`. Scartato (e contato): 19.731 righe senza valore; 203 valori negativi (-1...-35, tutti Alessandria 2024-2026); 306 date future (Alessandria); 0 duplicati. In più il servizio contiene righe con data 1899-1900 (zero di Excel; Novara 203 righe): non scaricate. Nessun valore è stato corretto.

## 4. Definizioni usate (stesse parole nel codice `scripts/analisi.py`)

- Dato: media giornaliera in granuli/m3 (POLLnet).
- **Integrale annuo**: somma dei valori giornalieri dell'anno solare (granuli x giorno / m3). È un minimo se mancano giorni.
- **Inizio / fine della stagione**: primo giorno in cui la somma cumulata dell'anno raggiunge il 5% / il 95% dell'integrale. **Durata** = fine - inizio. **Picco**: giorno col valore massimo. **Giorni sopra il limite "medio"** POLLnet del taxon (es. graminacee 10, betulla 16, ambrosia 5, cipressi 30).
- **Anno valido** per una stazione e un taxon: integrale >= 30; giorni campionati >= 75% dentro la finestra inizio-fine; >= 80% dentro una finestra fissa per il taxon (es. graminacee aprile-agosto, ambrosia luglio-ottobre); >= 200 giorni campionati nell'anno. 819 su 964 stagioni (stazione x taxon x anno) valide; scartate 71 per buchi, 54 per copertura, 14 per integrale basso, 2 per giorni, 4 per taxon mai > 0.
- **Tendenza**: pendenza di Theil-Sen con intervallo al 95% e test di Mann-Kendall; servono >= 10 anni validi. Tabelle per stazione `pulito/tendenze_stazione.csv` e **indicatore "pianura attorno a Milano"** `pulito/indicatore_regionale_anno.csv` / `tendenze_regionali.csv` (anomalia mediana rispetto alla media di ogni stazione, dal 2011, >= 3 stazioni per anno; è un indicatore costruito da me, non una serie ufficiale).
- Temperature: `temperature/serie/serie_unica.csv` (Brera, la serie pubblicata dal sito, senza la correzione 2008-2016 che nel JOURNAL sezione 1 è "proposta, spenta"). Medie dei due mesi che precedono la stagione (es. betulla/platano/frassino febbraio-marzo; graminacee/urticacee marzo-aprile; ambrosia/artemisia giugno-luglio). Correlazione di Spearman, pendenza in giorni per grado (con errore standard), e la stessa correlazione dopo aver tolto a entrambe le serie la tendenza lineare (cioè solo le oscillazioni da un anno all'altro). **È un confronto, non una prova di causa.**

## 5. Numeri principali (file e campo tra parentesi)

### 5.1 Quando comincia, finisce, è al massimo: valori tipici (mediane) a Novara e Piacenza (`riepilogo_taxon_stazione.csv`)
| Taxon | Novara inizio / picco / fine | Piacenza inizio / picco / fine | Integrale mediano Novara (granuli*giorno/m3) |
|---|---|---|---|
| Nocciolo | 20/01, 13/02, 14/03 | 22/01, 12/02, 05/03 | 3.327 |
| Ontano | 11/02, 23/02, 15/05 | 07/02, 19/02, 05/06 | 4.928 |
| Cipressi e affini | 18/02, 27/02, 27/04 | 11/02, 01/03, 22/05 | 10.939 |
| Platano | 31/03, 08/04, 18/04 (16 giorni) | 31/03, 06/04, 18/04 | 17.945 |
| Betulla | 30/03, 09/04, 01/05 | 27/03, 18/04, 06/05 | 2.857 |
| Quercia | 01/04, 09/04, 07/05 | 02/04, 25/04, 15/05 | 2.166 |
| Frassino | 10/03, 31/03, 26/04 | 01/03, 28/04, 15/05 | 1.468 |
| Graminacee | 12/04, 03/05, 24/09 | 15/04, 29/04, 18/08 | 7.695 |
| Urticacee | 28/04, 21/08, 24/09 | 26/04, 27/08, 23/09 | 13.813 |
| Artemisia | 09/08, 20/09, 09/10 | 18/08, 27/09, 10/10 | 624 |
| Ambrosia | 11/08, 06/09, 23/09 | 13/08, 02/09, 25/09 | 1.385 |

(Piacenza: i generi, tranne cipressi/graminacee/urticacee/platano/artemisia, solo dal 2018 circa; "anni_validi" è nel file.) Le "fini" delle graminacee e delle urticacee sono lontane perché c'è una coda lunga a basso livello tra agosto e ottobre: il 5-95% è sensibile a questa definizione.

### 5.2 Le stagioni stanno cambiando? Tendenze dell'indicatore "pianura attorno a Milano" 2011-2026 (`tendenze_regionali.csv`; giorni per decennio, intervallo 95%; n = 11-16 anni)
| Taxon | Inizio | Durata | Integrale (fattore per decennio) |
|---|---|---|---|
| Graminacee | **-8,2 (da -17,2 a -0,3)** | **+16,3 (da +4,9 a +28,3)** | 1,17 (0,92-1,60) |
| Platano | -4,2 (da -13,5 a +3,3) | **+5,4 (da +1,4 a +11,7)** | 1,54 (0,98-2,50) |
| Betulla | -4,0 (da -12,9 a +3,2) | +0,8 (da -11,9 a +15,5) | 0,87 (0,35-1,71) |
| Cipressi e affini | -5,5 (da -19,6 a +5,4) | +16,7 (da -8,3 a +35,0) | 1,31 (0,90-1,91) |
| Nocciolo | +3,5 (da -11,8 a +17,2) | +17,0 (da -18,2 a +71,8) | 2,24 (1,00-4,83) |
| Ontano | -3,0 (da -14,0 a +7,9) | -14,6 (da -66 a +34) | 1,47 (0,67-3,48) |
| Frassino | -4,9 (da -32,3 a +9,6) | +18,6 (da -15 a +44) | 1,54 (0,40-8,09) |
| Quercia | -2,2 (da -9,6 a +2,7) | -3,3 (da -9,5 a +4,8) | 1,58 (0,99-3,12) |
| Urticacee | **+9,8 (da +1,7 a +17,4)** | -3,0 (da -11,5 a +10,4) | 0,96 (0,68-1,35) |
| Artemisia | **+6,9 (da +3,5 a +11,0)** | **-6,3 (da -12,8 a -0,2)** | 1,36 (0,96-1,78) |
| Ambrosia | +1,4 (da -3,9 a +8,8) | -2,0 (da -8,1 a +6,7) | 0,72 (0,42-1,28) |

Lettura onesta: **solo poche cose sono distinguibili dal caso** (in grassetto). L'inizio delle graminacee (cinque stazioni su cinque con pendenza negativa, da -6 a -12 giorni per decennio) e la loro durata più lunga reggono; la maggior parte degli alberi "tende" a partire prima ma con intervalli che includono lo zero. Gli integrali degli alberi salgono quasi tutti (fattore 1,2-2,2 per decennio) ma anche qui lo zero (fattore 1) è nell'intervallo per quasi tutti; a Novara salgono 8 taxon su 11 con p < 0,05 (nocciolo, ontano, cipressi, frassino, graminacee, platano, quercia, artemisia), tutti nella stessa direzione: la cosa può essere un cambio di conteggio, non solo più pollini (limite 3). **Urticacee e artemisia partono più tardi, non prima**; per le urticacee potrebbe essere un effetto del 5%-95% su una stagione con due picchi (primavera e agosto). Sono 55 tendenze regionali + 276 per stazione: qualcuna uscirà "significativa" per caso.

### 5.3 Anni peggiori (integrale più alto rispetto alla media di ogni stazione; `anni_peggiori.csv`)
Ontano 2022 (x2,2), Betulla 2020 (x2,4), Nocciolo 2022 (x2,1), Frassino 2020 (x2,9), Quercia 2019 (x1,9), Platano 2026 (x1,7), Cipressi 2026 (x1,5), Graminacee 2025 (x1,5), Urticacee 2016 (x1,6), Artemisia 2026 (x1,7), Ambrosia 2012 (x2,4). Il numero di stazioni cambia da anno ad anno (3-5), quindi è un'indicazione, non una classifica. Il 2026 è fino al 18-25 ottobre.

### 5.4 Legame con la temperatura di Brera (`legame_temperature.csv`; confronto, non prova)
| Taxon (mesi di temperatura) | Anni | Giorni per grado in più | Correlazione (Spearman) | Dopo aver tolto la tendenza |
|---|---|---|---|---|
| Platano (feb-mar) | 14 (regionale) | -4,7 (errore 0,4) | -0,88 | -0,87 |
| Betulla (feb-mar) | 13 | -4,2 (0,4) | -0,80 | -0,86 |
| Frassino (feb-mar) | 11 | -7,5 (1,9) | -0,76 | -0,87 |
| Quercia (mar-apr) | 14 | -4,7 (1,4) | -0,49 | -0,71 |
| Graminacee (mar-apr) | 14 | -3,7 (1,3) | -0,51 | -0,74 |
| Urticacee (mar-apr) | 14 | -4,6 (2,1) | -0,76 | -0,33 (p=0,25) |
| Cipressi (gen-feb) | 15 | -5,3 (2,3) | -0,51 | -0,50 |
| Ambrosia, artemisia (giu-lug) | 16 | ~ 0 | 0,1-0,4 (p > 0,1) | ~ 0 |
(i valori della serie Novara sono simili: platano -4,95 giorni per grado, rho -0,89.) **Negli anni più caldi prima dell'inizio, le piante primaverili cominciano prima, circa 4-5 giorni per grado**; per ambrosia e artemisia (agosto) nessun legame con la temperatura di giugno-luglio. Cautele: la temperatura è quella di Brera (50 km dalle stazioni); la serie Brera 2008-2016 è nota per essere più calda di circa 0,65 C (JOURNAL sezione 1; correzione proposta ma spenta), quindi un po' di tendenza in più rispetto al vero; molti test (22 correlazioni); con 11-17 anni l'intervallo è largo. Curiosità: la temperatura di marzo-aprile a Brera non è salita (tendenza -0,90 C/decennio nel 2011-2025, -0,20 nel 2007-2025; a febbraio-marzo +0,65, a gennaio-febbraio +1,3), eppure le graminacee cominciano prima di circa 8 giorni per decennio: il caldo di Brera non spiega quella tendenza.

### 5.5 Ambrosia e il coleottero (`ambrosia_prima_dopo_2013.csv`, `pulito/stagioni_taxon_anno.csv`)
Integrale dell'ambrosia 2012 contro 2013 (granuli*giorno/m3): Novara 3.362 -> 475; Alessandria 3.334 -> 1.620; Vercelli 1.311 -> 280; Verona 842 -> 307. **Calo del 51-86% in tutte e quattro le stazioni con entrambi gli anni.** A Novara la mediana 2007-2012 è 3.236 e quella 2013-2025 è 987 (rapporto 0,31); ad Alessandria 0,33; a Verona 0,60; a Vercelli 0,45. Nessun anno dopo il 2012 ha raggiunto i valori 2011-2012 tranne un rimbalzo nel 2019 (Novara 2.904, Piacenza 1.699, Alessandria 2.530). Le note di Regione Lombardia indicano come causa *Ophraella communa*, arrivata in Lombardia nel 2013; il dato in sé (calo di colpo e simultaneo in quattro stazioni) è compatibile ma **la causa non si vede nei dati POLLnet**. In Lombardia la Regione scrive di fluttuazioni dal 2018 e di un aumento a nord di Milano. Milano (Regione): 2024 massimo 39, totale 428; 2025 massimo 12, totale 183. Altre stazioni 2025: Desio 1.257, Busto Arsizio 1.167, Legnano 948, Magenta 614.

### 5.6 Alberi del Comune come contesto (`alberi_contesto.csv`, da `alberi/pulito/alberi.csv`, edizione 2025; 251.165 alberi gestiti dal Comune)
Platano (Platanus) 22.712 (9,0%); frassino 12.651 (5,0%); quercia 13.591 (5,4%); olmo 11.754; pioppo 10.567; bagolaro (Celtis) 15.546; carpino 8.108; **cipressi e affini (Cupressaceae) 6.410 (2,6%) + tasso 970; ontano 1.340; betulla 850 (0,34%); nocciolo 841**. Non contano per le erbe (graminacee, urticacee, ambrosia, artemisia) e non dicono quanti alberi ci sono fuori dal perimetro del Comune (giardini privati, Parco Nord, Parco Sud, Brianza, Valle del Ticino). Il confronto va fatto con prudenza: **la betulla ha solo 850 alberi in città ma è tra i pollini più importanti della primavera** (calendario ATS: rosso in aprile): arriva da lontano. Il platano è il secondo albero più numeroso del censimento (dopo l'acero) e anche il polline arboreo con l'integrale più alto a Novara (17.945, in una stagione di appena 16 giorni): qui il legame è plausibile, ma Novara non è Milano.

## 6. La cosa più sorprendente

**L'ambrosia, il polline più temuto, in realtà è crollata di colpo nel 2013 in tutte le stazioni vicine a Milano, mentre il clima si scaldava, e non è tornata ai livelli del 2011-2012.** A Novara il suo integrale è passato da 3.362 (2012) a 475 (2013); in quattro stazioni su quattro con i due anni il calo è tra il 51 e l'86%. Le note della Regione Lombardia dicono perché: un coleottero arrivato per caso (*Ophraella communa*). Sotto il riscaldamento, un insetto ha pesato più di qualunque grado in più (e a Milano nel 2025 il totale è sceso di nuovo: 183 contro 428 nel 2024). Altro risultato non scontato: urticacee e artemisia **partono più tardi**, non prima, mentre le graminacee partono prima di circa 8 giorni per decennio e la temperatura di marzo-aprile a Brera non è cresciuta.

## 7. Limiti dei dati (da dire in pagina)

1. **Non c'è Milano.** Nessuna stazione lombarda in POLLnet; per Milano solo numeri di testata e il calendario ATS. Novara/Piacenza sono 45-60 km a ovest e a sud-est: stesse specie e stagioni, ma non gli stessi numeri.
2. **Gli zeri non sono sempre scritti.** Alcune stazioni e anni (Novara 2017-2019, Piacenza dal 2018 per i generi, Omegna) registrano solo i giorni con valore > 0 per un taxon: l'assenza non distingue "zero" da "non contato". Somme, inizi e picchi non cambiano, i conteggi di giorni sì. I giorni "campionati" sono quelli in cui la stazione ha almeno una riga.
3. **Metodo di conteggio e taxon cambiano da una stazione all'altra e nel tempo:** Piacenza dà "Betulaceae" fino al 2018 e "Betula" dopo; molti generi (Betula, Alnus, Corylus, Ambrosia...) a Piacenza compaiono dal 2018. Novara 2017-2019 ha pochissimi giorni per taxon. Cambi di conteggio possono far salire o scendere gli integrali (a Novara 2007-2026 quasi tutti gli alberi "crescono": prudenza).
4. **Serie corte:** 11-20 anni per taxon e stazione, per l'indicatore 2011-2026 appena 11-16. Le stagioni pollinica sono molto variabili da un anno all'altro; gli intervalli al 95% sono larghi.
5. **Anni con buchi:** 71 stagioni scartate per buchi nella finestra attesa; il 2026 arriva solo al 18-25 ottobre (le stagioni primaverili e estive sono complete).
6. **Il 5%-95% dipende dalla definizione.** Per graminacee e urticacee la durata comprende una coda lunga a basso livello; per le specie che cominciano a dicembre (cipressi, nocciolo) l'anno solare taglia la parte di dicembre.
7. **Il servizio mostra un numero sbagliato:** `resultType=hits` dà sempre 3000 (tetto per richiesta); bisogna paginare con `startIndex` e `sortBy`. Date 1899/1900 (zero di Excel) e date future in Alessandria; valori negativi (Alessandria).
8. **Temperature:** serie Brera con salto non corretto nel 2008-2016, 50 km dalle stazioni.
9. **L'ambrosia e la causa:** il coleottero è una spiegazione della Regione, non un risultato dei dati POLLnet.
10. **Licenze:** POLLnet CC-BY 4.0 (ripubblicabile con citazione); ATS Milano, note della Regione, articolo Sci. Rep.: non ripubblicare i PDF o le pagine; solo numeri e citazioni.

## 8. Cosa può mostrare una pagina

1. **Il calendario pollinico del Nord-ovest in un colpo d'occhio**: per ogni taxon, la barra dall'inizio alla fine della stagione (mediana 2007-2026) con il picco; dal cipresso e nocciolo a gennaio-febbraio, alla betulla e platano ad aprile, alle graminacee da fine aprile, ad artemisia e ambrosia ad agosto-settembre. Con il calendario ATS 2016-2025 di Milano accanto.
2. **Anno per anno, stagione per stagione**: una riga per anno con l'inizio e la fine della stagione (grafico a barre o "cascata"), da cliccare per taxon. Con onestà: banda di incertezza e l'indicazione di quali anni non sono validi.
3. **Il caso ambrosia 2013**: grafico dell'integrale 2007-2026 per le stazioni, con il salto del 2013 e la sola frase "la Regione parla di un coleottero".
4. **Il legame con la temperatura**: dispersione "febbraio-marzo più caldo / inizio platano-betulla-frassino più presto", con la retta e la dicitura "4-5 giorni in meno per ogni grado in più, in 11-17 anni; non è una prova".
5. **Dire con chiarezza che Milano non ha una serie aperta**, mostrare le stazioni vicine su una mappa con la distanza, e il numero di testata 2024-2025 di Milano.
6. **Gli alberi del Comune**: platano 22.712, cipressi 6.410, betulla 850 contro il peso del loro polline (e il fatto che gran parte del polline arrivi da fuori città).
7. Una richiesta dati a ATS Milano (pollini@ats-milano.it) per la serie di Milano e Legnano potrebbe cambiare tutto (decisione di Davide).

## 9. File prodotti (`pulito/`)
`concentrazioni_giornaliere.csv`, `stazioni.csv`, `controlli_pulizia.json`, `stagioni_taxon_anno.csv` (964 righe: inizio, fine, picco, durata, integrale, giorni sopra il limite medio, copertura, valida), `riepilogo_taxon_stazione.csv`, `tendenze_stazione.csv`, `indicatore_regionale_anno.csv`, `tendenze_regionali.csv`, `anni_peggiori.csv`, `ambrosia_prima_dopo_2013.csv`, `ambrosia_regione_lombardia.csv`, `legame_temperature.csv`, `alberi_contesto.csv`, `riepilogo.json`.
