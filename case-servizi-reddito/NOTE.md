# Case, servizi e reddito (filoni 12 + 9): note della fase 1 (solo analisi, nessuna pagina)

Data: 1 novembre 2026. Cartella: `case-servizi-reddito/`. Domanda di Davide: le zone con tutti i servizi vicino costano di più? Quanto vale "un servizio sotto casa"?
Come leggere: ogni numero dice da quale file (in `out/`) e da quale campo viene. Tutti i programmi sono in `scripts/` (Python 3.12, `python -I -X utf8`, percorsi assoluti come argomenti); il comando per rifare tutto è in `STATO.md`.

**I prezzi OMI sono STIME dell'Agenzia delle Entrate (intervalli minimo-massimo per zona, il "prezzo" qui è il centro dell'intervallo), non prezzi di vendite reali.** Vale per ogni numero di questa nota. Fonte: Agenzia delle Entrate - OMI, CC BY 4.0, semestre 2026/1, abitazioni civili, stato prevalente.

## In breve

1. **Sì, le zone con più servizi costano molto di più: ma quasi tutto il legame è centralità e reddito.** Spearman prezzo-servizi (su 20) 0,87 (IC 95% 0,76-0,93) su 41 zone (`out/correlazioni_spearman.csv`, riga "prezzo vs servizi su 20"). Il terzo di zone con più servizi ha un prezzo mediano di 6.750 €/m², il terzo con meno servizi 3.338 €/m² (`out/gruppi_terzili.csv`).
2. **A parità di distanza dal Duomo e di reddito, il legame si riduce a circa un quinto e non si distingue da zero con certezza.** Regressione sui logaritmi (`out/modelli.csv`): +15,6% di prezzo per ogni servizio in più (su 20) se non si controlla nulla; **+3,0% (IC 95% da -0,1% a +7,5%)** controllando distanza e reddito. Sopravvive il 21% del coefficiente (`out/risultati_03.json`, `quota_coefficiente_che_sopravvive_S20` = 0,207). Con anche le fasce OMI (B/C/D/E) il coefficiente scende a -0,1% (da -3,3% a +3,1%).
3. **"Quanto vale un servizio in più": una stima grossolana di circa +3%, cioè circa 120 €/m² (da -6 a +301), cioè circa 8.500 € su una casa di 70 m² (da -400 a +21.000),** applicata al prezzo mediano delle zone (4.000 €/m²). È un massimo ragionevole, non un prezzo certo: vedi "Perché è un massimo" qui sotto. Il controllo a livello di NIL dà un valore più basso: +1,7% (da +0,7% a +3,0%).
4. **La sorpresa:** i servizi "di base" (i 10 essenziali: farmacia, medico, scuole, parco, ecc.) non spiegano il prezzo; contano gli extra e, tra gli extra, soprattutto la metro. Coefficiente degli essenziali, a parità di extra, distanza e reddito: -4,5% per servizio (da -15,4% a +2,2%) (`out/modelli.csv`, riga "effetto essenziali"); degli extra +6,3% per servizio (da +0,8% a +15,5%). La metro da sola è l'unico servizio con correlazione parziale chiaramente positiva (0,56, IC 0,26-0,75) (`out/servizi_singoli.csv`).
5. **Zone di cui ci si stupisce** (`out/sorprese_zone.csv`): Quarto Oggiaro (E8) ha più servizi essenziali (9,28 su 10) di CityLife (8,79), Porta Nuova (8,96) e della zona Sant'Ambrogio-Via Dante (8,64), ma è la zona più economica (2.350 €/m² contro 10.400, 13.100 e 8.200). E Venezia-Porta Romana (B19) è la prima per servizi su 20 (19,63) ma solo l'ottava per prezzo (7.650).
6. **Il "troppo caro" è nuovo e di moda, non "servito":** Porta Nuova (C14), Brera (B15) e CityLife (C13) costano molto più di quanto servizi, distanza e reddito prevedano (+97%, +32%, +30%: `residuo_B_con_distanza_reddito` 0,678, 0,277, 0,265, convertiti con exp-1). Due di queste zone (C13, C14) sono segnate dall'OMI come stato "OTTIMO" (edifici nuovi): il prezzo di un quartiere di grattacieli nuovi, non confrontabile con il resto.

## 1. Metodo e fonti

- **Zone OMI (2026/1):** `prezzi-case/raw/geopoi/F205_20261.json` (43 zone, area totale 181,78 km², `out/log_01.json`). Perimetri letti con la regola pari/dispari sugli anelli (OR esclusivo), come spiegato in `prezzi-case/scripts/05_zone_corrispondenza.py`: letti come GeoJSON normale darebbero un'area sbagliata (trappola del filone 12). Non ho usato `docs/prezzi-case/data/zone.geojson` perché ha 42 zone (senza la rurale R2) e coordinate arrotondate.
- **Civici:** `citta-15-minuti/out/civici_tempi.csv` (57.405 civici applicati; campi `x`,`y` = metri UTM 32N, EPSG:32632; controllato: ritrasformando `lon`,`lat` si ottiene lo stesso punto con scarto massimo 0,07 m, `out/log_01.json`, `controllo_crs_max_scarto_m`), `punteggio` (10 servizi entro 15 minuti a piedi) e `civici_tempi_extra.csv` (`punteggio_20`, `punteggio_extra`). Ho ricalcolato i punteggi dai minuti per controllo: coincidono al 100% (soglia 15 minuti, minuti mancanti = servizio non raggiunto).
- **Assegnazione civico-zona:** punto-in-poligono con shapely (STRtree). 8 civici cadono in due zone (le zone si sovrappongono per 58.681 m²) e si tiene la prima; 4 civici non cadono in nessuna zona e sono stati assegnati alla zona più vicina (tutti entro 50 m); 0 civici senza zona (`out/log_01.json`).
- **Reddito:** `citta-15-minuti/out/cap_redditi_servizi.csv`, campo `imponibile_medio_2024` (reddito imponibile medio per contribuente del CAP, anno d'imposta 2024). Il reddito esiste solo per CAP (38 CAP) e il CAP di ogni civico è una stima (corretto nel 96,6% dei casi secondo il test del filone 9). Reddito della zona = media dei CAP dei civici, pesata con i residenti stimati.
- **Pesi:** `peso` = residenti 2025 del NIL (`citta-15-minuti/out/nil_punteggi.csv`, campo `residenti_2025`, totale 1.399.079) distribuiti in parti uguali sui civici residenziali del NIL: stessa ipotesi del filone 9. Tutte le medie di zona sono pesate così (i civici non residenziali pesano 0). Dove scrivo "n civici" senza altro è il numero di civici applicati.
- **Prezzi:** `prezzi-case/pulito/prezzi_zona_semestre_prevalente.csv`, righe `semestre`=2026-S1, `tipologia`=Abitazioni civili, `prevalente`=True; campi `compr_centro` (€/m²) e `loc_centro` (€/m² al mese). Controllato: coincide al 100% con `docs/prezzi-case/data/zone_ultimo_semestre.csv` (scarto massimo 0, `out/log_02.json`). 42 zone con prezzo; la rurale R2 non ha quotazioni.
- **Distanza dal Duomo:** dal centroide del perimetro della zona (UTM) a Piazza del Duomo (45,46427 N, 9,19192 E). Variante: media delle distanze dei civici (pesata).
- **Statistica:** Spearman con intervalli bootstrap sulle zone (5.000 ripetizioni, seme 20261101); correlazione parziale = Spearman dei residui dei ranghi; regressione ln(prezzo) ~ servizi + ln(km dal Duomo) + ln(reddito) con minimi quadrati, errori robusti HC3 e bootstrap sulle zone (`scripts/03_correlazioni.py`). Niente statsmodels: è codice scritto qui con numpy.
- **Campione principale: 41 zone** = 43 meno R2 (nessun prezzo) meno D39 (vedi trappole).

## 2. Tabella per zona

`out/zone_tabella.csv` (43 righe): per ogni zona numero di civici (tutti e residenziali), residenti stimati, punteggio medio su 10 e su 20, quota di premium (civici con 20/20, pesata), reddito pesato, numero di CAP, distanza dal Duomo, prezzo e affitto (OMI), stato prevalente. Zone per prezzo (ultime cifre: €/m², servizi su 20):

- Più care: C14 Porta Nuova 13.100 (18,96); B15 Brera 11.150 (17,97); C13 CityLife 10.400 (17,93); B12 Duomo-San Babila 10.050 (18,33); B16 Sant'Ambrogio-Via Dante 8.200 (17,42).
- Più economiche: E8 Quarto Oggiaro 2.350 (13,24); E7 Missaglia-Gratosoglio 2.500 (11,23); E5 Baggio-Muggiano 2.650 (11,98); D32 Bovisasca-Comasina 3.000 (14,84).
- Premium (20/20): solo B19 ha una quota alta (64%), B12 23%, C20 27%; in 32 zone su 43 la quota è sotto il 5% (in 29 è zero) (`quota_premium_pesata`). Per questo la quota premium (Spearman 0,62 con il prezzo) è meno utile del punteggio medio.

## 3. Correlazioni (Spearman, 41 zone; `out/correlazioni_spearman.csv`)

| Coppia | Spearman | IC 95% |
|---|---|---|
| prezzo vs reddito del CAP | 0,93 | 0,84-0,97 |
| prezzo vs distanza dal Duomo | -0,88 | da -0,94 a -0,77 |
| prezzo vs servizi su 20 | 0,87 | 0,76-0,93 |
| prezzo vs servizi extra (10) | 0,91 | 0,80-0,95 |
| prezzo vs quota premium | 0,62 | 0,41-0,80 |
| prezzo vs servizi essenziali (su 10) | 0,52 | 0,27-0,71 |
| affitto vs servizi su 20 | 0,82 | 0,71-0,89 |
| servizi su 20 vs reddito | 0,82 | 0,70-0,89 |
| servizi su 20 vs distanza | -0,85 | da -0,91 a -0,75 |
| reddito vs distanza | -0,85 | da -0,92 a -0,73 |

I tre "spiegatori" sono quasi la stessa cosa: centrali, ricchi e serviti. Fattore di inflazione della varianza (VIF) 3,3 (servizi), 3,6 (distanza), 4,7 (reddito) (`out/risultati_03.json`, `VIF`).

**Correlazione parziale (Spearman dei ranghi, controllando distanza e reddito; `out/spearman_parziale.csv`):**

| Servizi | nessun controllo | + distanza | + reddito | + distanza + reddito |
|---|---|---|---|---|
| su 20 | 0,87 | 0,49 | 0,51 | **0,37 (IC 0,04-0,63)** |
| essenziali (su 10) | 0,52 | -0,24 | 0,30 | **0,02 (IC -0,31-0,37)** |
| extra (10) | 0,91 | 0,68 | 0,53 | **0,47 (IC 0,05-0,72)** |

Lettura: con i controlli la correlazione dei servizi su 20 con il prezzo passa da 0,87 a 0,37, cioè circa il 42% sopravvive come correlazione sui ranghi (e circa il 21% come coefficiente della regressione). Per i soli servizi essenziali non sopravvive nulla (0,02).

**R² (quota di variabilità dei log-prezzi spiegata; `out/risultati_03.json`, `r2`):** i soli servizi 0,68; distanza + reddito 0,87; distanza + reddito + servizi 0,87. I servizi aggiungono 0,9 punti percentuali di R² a quanto già spiegano distanza e reddito.

## 4. Regressione e "quanto vale un servizio"

Modello principale: ln(prezzo €/m²) = a + b·servizi(su 20) + c·ln(km dal Duomo) + d·ln(reddito), 41 zone. (`out/modelli.csv`, riga "S20 + distanza + reddito", e `out/robustezza.csv`.)

| Variante | n | % di prezzo per servizio in più | IC 95% bootstrap |
|---|---|---|---|
| nessun controllo | 41 | +15,6 | +12,5 / +19,3 |
| + distanza | 41 | +8,8 | |
| + reddito | 41 | +3,4 | |
| **+ distanza + reddito (principale)** | 41 | **+3,0** | **-0,1 / +7,5** |
| + distanza + reddito + fascia OMI | 41 | -0,1 | -3,3 / +3,1 |
| principale con D39 incluso | 42 | -0,8 | -3,8 / +6,2 |
| senza zone con meno di 100 civici residenziali | 38 | +2,0 | -0,6 / +4,5 |
| solo zone con stato NORMALE | 39 | +2,1 | -0,5 / +4,5 |
| affitto invece del prezzo | 41 | +1,0 | -2,9 / +6,3 |
| servizi su 10 invece che su 20 (per punto) | 41 | -0,4 | -7,1 / +6,2 |
| togliendo una zona alla volta | 40 | da +1,7 (senza C14) a +3,7 (senza B15) | |

(Righe "+ distanza" e "+ reddito": `b_S20` 0,084 e 0,034 in `out/modelli.csv`, convertite con exp-1.)

**Traduzione in euro** (prezzo mediano delle 41 zone 4.000 €/m², `out/risultati_03.json`): un servizio in più (su 20) vale circa +121 €/m² (IC da -6 a +301), circa +8.500 € su 70 m² (da -400 a +21.000). Una deviazione standard di servizi tra le zone (2,48 servizi) vale +7,7% a parità di distanza e reddito. Intervallo di servizi nel campione: da 11,09 a 19,63 su 20.

**Cosa dire e cosa no:**
- Dire: "il legame lordo è forte (+16% per servizio), ma quasi tutto si spiega con centralità e reddito; a parità di queste due cose resta un residuo piccolo, circa +3% per servizio, con un intervallo che arriva a zero".
- Non dire: "un servizio sotto casa vale 8.500 euro". Non è un prezzo.

**Perché è un massimo e non una stima centrale:**
1. Il reddito è del CAP, non della zona: in 30 zone su 43 almeno due CAP pesano più del 10% (`out/cap_per_zona.csv`, `n_cap_ge10pct`) e in 12 zone un solo CAP copre più del 90% dei residenti. Un controllo per reddito così grossolano assorbe solo in parte la ricchezza del quartiere: ciò che resta ai servizi può essere ricchezza non misurata. Questo spinge il coefficiente dei servizi verso l'alto.
2. Con la fascia OMI (che già dice "centrale, semicentrale, periferica") il coefficiente va a zero.
3. Le zone sono 41 e non indipendenti: zone vicine si assomigliano; gli intervalli sono probabilmente un po' troppo stretti.
4. Sull'altro lato, il punteggio dei servizi è una misura grezza (un servizio conta 1 sia se è a 2 sia a 14 minuti; i servizi contano tutti uguale): questo attenua il coefficiente, spingendolo verso il basso. I due effetti non si compensano in modo noto.

**Stessa distanza, più servizi** (`out/stessa_distanza.csv`; 41 zone divise in 3 gruppi di distanza, poi in metà con più e meno servizi): nelle zone vicine al Duomo (0,2-2,5 km) quelle con più servizi costano meno (mediana 6.500 contro 8.000 €/m²); nelle zone a distanza media (2,6-4,9 km) di più (4.950 contro 3.575, +38%); nelle lontane (4,9-9,1 km) di più (3.550 contro 3.050, +16%). Un legame che sparisce o si inverte vicino al centro non è un prezzo dei servizi: nel centro ci sono i servizi ovunque e i prezzi seguono altro (prestigio, edifici, reddito).

## 5. Servizio per servizio (esplorativo; `out/servizi_singoli.csv`)

Per ogni servizio: quota di residenti della zona con il servizio entro 15 minuti; correlazione parziale (Spearman) con il prezzo controllando distanza e reddito. 20 confronti su 41 zone: qualche valore alto può essere un caso.

- **Metro 0,56 (IC 0,26-0,75)** è l'unico il cui intervallo non include lo zero. Seguono (intervallo che include lo zero): uffici postali 0,36, aree cani 0,36, supermercati 0,35, ospedali 0,31, teatri e musei 0,30, cinema 0,30, BikeMi 0,28.
- Sotto 0,15: medici 0,10, mercati 0,07, parchi 0,03. **Biblioteche -0,31** (IC da -0,61 a +0,14), anche prima dei controlli la correlazione è -0,07: le biblioteche non si associano al prezzo (era già emerso nel filone 9: correlazione 0,00 con il reddito).
- Molti servizi sono raggiunti da quasi tutti i residenti in quasi tutte le zone (scuole, farmacie, negozi, aree gioco: quota media sopra il 98%), per cui non hanno quasi variabilità da spiegare.

## 6. Livello NIL (quartieri; `out/nil_tabella.csv`, `out/nil_risultati.json`)

Prezzo per NIL in due modi: **per area** (media dei prezzi OMI pesata con l'area di sovrapposizione zona-NIL; esclusa R2) e **per residenti** (prezzo della zona di ogni civico, pesato con i residenti stimati). NIL ammessi: 74 (almeno 30 civici e 1.000 residenti, senza Cascina Merlata, senza Chiaravalle perché è tutta in zona rurale R2 senza prezzo; 14 esclusi, elenco in `nil_risultati.json`).

- I due metodi concordano (Spearman fra loro 0,99; scarto relativo mediano 0,6%, massimo 35%).
- **Spearman prezzo-servizi su 20: 0,87 (IC 0,74-0,93); prezzo-reddito 0,89; prezzo-distanza -0,88** (prezzo per residenti, intervalli bootstrap a grappoli per zona OMI).
- **Regressione a parità di distanza e reddito: +1,7% per servizio (IC 95% da +0,7% a +3,0%)**; lordo +8,2%. Prezzo per area: +1,6% (da +0,6% a +2,9%). Solo i 47 NIL con almeno l'80% dell'area in una sola zona: +1,5% (da +0,4% a +3,3%). Correlazione parziale (Spearman) 0,40 (residenti) e 0,37 (area).

**Quale livello è più affidabile: le zone.** (a) Il prezzo esiste per zona, non per NIL: il prezzo del NIL è un valore derivato, uguale per tutti i NIL della stessa zona; i 74 NIL non sono 74 osservazioni indipendenti, ma le zone OMI "dominanti" sono 36. (b) Il 44,6% dei NIL ammessi tocca due o più zone per almeno il 10% dell'area e solo il 63,5% ha una zona dominante sopra l'80%. (c) Dentro una zona i servizi variano ma il prezzo no, quindi il legame viene attenuato: il +1,7% dei NIL è probabilmente una sottostima. (d) Anche il reddito del NIL è una media di CAP. I NIL servono come controllo di coerenza (stesso segno, stesso ordine di grandezza, intervallo sopra zero perché il numero di punti è più alto) e per la mappa, non come stima principale. Per una frase sola: tra +1,5% e +3% per servizio, la seconda cifra dalle zone.

## 7. Trappole trovate

1. **Perimetri GEOPOI a più anelli** (già nota dal filone 12): letti come buchi darebbero un'area di Milano sbagliata. Qui l'area totale con il metodo pari/dispari è 181,78 km² (`out/log_01.json`).
2. **Le zone si sovrappongono** per 58.681 m² e 8 civici cadono in due zone; 4 civici cadono fuori da ogni zona (entro 50 m dal bordo, assegnati alla più vicina).
3. **D39 Cascina Merlata:** nei dati del Comune ha solo 105 civici (38 residenziali) e un punteggio di 2,74 su 10, falsato dai servizi mancanti nei registri (stessa trappola del filone 9, dove il NIL è fuori dalle classifiche). Con D39 incluso il coefficiente dei servizi diventa -0,8% e R² scende da 0,87 a 0,84. È fuori dal campione principale. Anche il suo prezzo (4.700 €/m²) è di stato "OTTIMO".
4. **Stato prevalente OTTIMO** in 3 zone (C13 CityLife, C14 Porta Nuova, D39); NORMALE nelle altre 39 (`out/log_02.json`). Il prezzo di queste zone è quello di edifici in stato ottimo, più alto per costruzione; senza di loro il coefficiente passa a +2,1% (da -0,5 a +4,5).
5. **Zone con pochissimi civici residenziali:** C13 (14), D39 (38), C14 (55), D34 (86). Medie di punteggio su pochi civici sono instabili e il peso in residenti (NIL diviso in parti uguali sui civici) può essere molto lontano dalla realtà. Senza queste quattro zone il coefficiente è +2,0% (da -0,6 a +4,5).
6. **Pesi in residenti:** i residenti del NIL sono distribuiti in parti uguali sui civici residenziali: in alcune zone il peso è inverosimile (es. D16 ha 28.582 residenti stimati su 643 civici residenziali). Non verificato con dati di censimento per zona.
7. **Reddito per CAP e CAP stimato:** vedi sopra; in nessun caso il reddito è della zona. Il legame prezzo-reddito (Spearman 0,93) è probabilmente gonfiato dalla coincidenza geografica tra zone e CAP.
8. **R2 rurale:** nessun prezzo OMI; il NIL Chiaravalle è tutto in R2 e non ha prezzo.
9. **Prezzo = centro di un intervallo stimato.** Intervalli larghi in alcune zone (es. C14 da 10.500 a 15.700 €/m², `compr_min`, `compr_max` in `out/zone_tabella.csv`). Non ho usato l'ampiezza come incertezza.
10. **Confondenti non considerati:** età e qualità del patrimonio edilizio, rumore, verde, presenza di stazione ferroviaria, immigrazione, scuole di prestigio, effetto brand del quartiere. Il reddito e la distanza non li assorbono.

## 8. Avvertenza in italiano semplice (da riportare vicino ai risultati)

Correlazione non è causa. Le zone con più servizi sono anche le più centrali e le più ricche, e di solito le più care in ogni caso: non possiamo sapere quanto del prezzo sia dovuto ai servizi e quanto al fatto di essere in centro o in un quartiere ricco. Le zone sono grandi, sono poche (41) e i redditi sono per CAP: il risultato è un ordine di grandezza, non una cifra da usare per valutare una casa. I prezzi sono stime dell'Agenzia delle Entrate, non prezzi di vendita.

## 9. Cosa potrebbe mostrare una pagina (idee, non fatte)

1. **Grafico a punti prezzo vs servizi su 20** con tre interruttori "togli la distanza", "togli il reddito": si vede la pendenza che si appiattisce da +15,6% a +3% per servizio. Le zone sorprendenti (E8 Quarto Oggiaro, B19 Venezia-Porta Romana, C14 Porta Nuova) etichettate.
2. **Tabella "servito ma economico / caro ma poco servito"** (`out/sorprese_zone.csv`) con la frase di Quarto Oggiaro contro CityLife.
3. **"Cosa si paga davvero": barre per servizio** (correlazione parziale per ognuno dei 20, `out/servizi_singoli.csv`): la metro in cima, le biblioteche in fondo, gli essenziali al centro; con l'avvertenza dei 20 confronti. Oppure una mappa delle zone colorate per residuo del modello.
