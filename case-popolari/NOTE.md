# Case popolari vuote - FASE 1 (fonti, scaricamento, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web, niente cause: solo confronti. Ogni numero dice file e campo. Programmi in `scripts/` (Python 3.12, `python -I -X utf8 scripts/<nome>.py <percorsi assoluti>`; comandi in `STATO.md`). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`. Nessun inquilino, nessun alloggio singolo: nei file ci sono solo totali e indirizzi di edifici (dall'elenco pubblico di ALER).

## 1. In breve

1. **Non esistono dati aperti sulle case popolari di Milano.** Né il portale del Comune (25 parole chiave, 165 dataset) né quello della Regione (31 parole chiave) hanno patrimonio, sfitti o graduatorie ERP. Tutto viene da PDF ufficiali (Regione, ALER, Comune) che ho letto con programmi, con pagina citata e controllo automatico dei numeri.
2. **Quante sono.** A Milano città le case popolari (SAP) sono **59.054** al 3/7/2026: 26.010 del Comune (gestite da MM) e 33.044 di ALER Milano (`pulito/patrimonio_sap_milano_serie.csv`, Rapporto regionale 2025, p.10). Sono il **7,1%** delle abitazioni di Milano (827.648 nel 2023, `censimenti/pulito/indicatori_comune.csv`, campo `abit_tot`); 7,3% sul dato 2021; 8,2% se si contano solo le abitazioni occupate. Il Comune scrive "circa il 10%" (2023) senza dire il denominatore.
3. **Quante sono vuote (marzo 2023, unico dato per la città con il motivo).** Dalla tabella del Comune (`pulito/stato_utilizzo_marzo_2023.csv`): Comune/MM 4.752 vuote su 26.489 (17,9%): 3.731 "sfitte per carenze manutentive" e 1.021 "libere" (in ristrutturazione/riatto). ALER 3.668 su 32.017 (11,5%): 3.274 per carenze manutentive e 394 libere. **In tutto 8.420 su 58.506 (14,4%).**
4. **Nel tempo (solo ALER, ma su tutto il territorio ALER Milano: 53.143 alloggi a canone sociale, non solo la città).** I "sfitti" scritti da ALER vanno da 5.919 (2018) a 8.350 (2021) a 5.175 (2025), cioè -38% dal 2021. **Ma dal 2022 ALER mette fuori dai "sfitti" tre voci (valorizzazione, vendita, demolizione): contando anche quelle i vuoti sono 8.350 (2021) e 7.735 (2025), -7%** (`pulito/aler_vuoti_serie_armonizzata.csv`; la somma torna col totale ALER in tutti e 8 gli anni, scarto 0).
5. **Perché sono vuote (ALER 2025, vuoti armonizzati 7.735):** in ristrutturazione 4.313 (55,8%), da valorizzare 2.003 (25,9%), in riassegnazione 862 (11,1%), destinati a vendita 401 (5,2%), in demolizione 156 (2,0%). Comune (marzo 2023): 78,5% carenza manutentiva, 21,5% in ristrutturazione/riatto. Le **occupazioni abusive** sono un'altra cosa (alloggi abitati senza titolo, non vuoti): ALER 2.324 consolidate nel 2025 (picco 3.467 nel 2018, 2.217 nel 2013), Comune/MM 459 nel 2025 (648 nel 2021); ALER Prospetto n.5: 2.713 "senza contratto" nel 2025.
6. **Domande e assegnazioni (Milano città, avvisi dell'anno).** 2025: 723 alloggi in avviso, 17.754 domande, 572 assegnati (luglio 2026). 2024: 869 / 24.122 / 720. 2022: 1.523 / 36.946 / 1.297. 2020: 560 / 22.345 / 367. 2019: 534 / 16.575 / 450. Circa **25-40 domande per alloggio** in tutti gli anni (`pulito/domande_per_alloggio.csv`). Mancano 2021 e 2023 (vedi limiti).
7. **Dove.** Non esiste un dato per quartiere. Per **Municipio** ho gli alloggi assegnabili nel 2026 (Piano annuale 2026) e per **NIL** solo l'elenco degli edifici ALER con il canone fatturato (2013/2015/2016, agganciato al 96,5% ai NIL): Gratosoglio-Missaglia-Terrazze 12,4% del canone ALER cittadino, San Siro 6,4%, Barona 6,0%, Giambellino 4,8%, Lodi-Corvetto 4,3%. Sono i soli edifici ALER, e il canone non è il numero di alloggi.
8. **La cosa più sorprendente:** il numero degli "sfitti" ALER è sceso del 38% in quattro anni, ma gli alloggi ALER vuoti per qualunque motivo sono quasi gli stessi (-7%): cambiano le caselle in cui ALER li scrive (vedi 5).
9. **Fonti bloccate o assenti:** il sito del Comune ha risposto 503 ("Maintenance") e poi 403 (blocco): non aggirato. Il sito di MM risponde 403 ai programmi: non aggirato. L'Internet Archive era offline per le ricerche aggiuntive. Nessun account creato.

## 2. Fonti, una per una (anche in `pulito/inventario_fonti.csv`; i file in `raw/` sono elencati con hash in `pulito/inventario_file_raw.csv`)

Licenze: i documenti ufficiali (Regione, ALER, Comune) non dichiarano una licenza nelle pagine da cui li ho presi. Vale: si citano i **numeri** con fonte e pagina, **non** si ripubblicano i PDF. Solo i dataset CKAN hanno una licenza dichiarata (CC-BY), ma non contengono dati ERP.

### 2.1 Portale open data del Comune (CKAN, `package_search`, 1/11/2026)
Parole chiave: ERP, edilizia residenziale pubblica, alloggi, MM Casa, sfitti, case popolari, patrimonio abitativo, assegnazioni, graduatoria, ALER, alloggi comunali, servizi abitativi, abitazioni pubbliche, emergenza abitativa, sfratti, bando alloggi, canone, inquilini, occupazioni abusive, housing sociale, edilizia sociale, residenziale pubblica, patrimonio immobiliare, MM spa, domande alloggi (`raw/_catalogo/search_comune.json`, 165 dataset). **Risultato: nessun dataset sulle case popolari.** Esaminato `ds677` (Elenco immobili di proprietà del Comune, 23.640 righe, 3.748 fabbricati, anno 2019, CC-BY): è terreni e fabbricati senza destinazione d'uso né NIL completo; non usato. `ds362` e `ds384` (condizione abitativa, censimento 2011): non distinguono le case popolari.

### 2.2 Dati aperti della Regione (dati.lombardia.it, API del catalogo, 1/11/2026)
31 parole chiave (`raw/_catalogo/search_lombardia.json`). Trovati solo: dati amministrativi delle 5 ALER (compensi e risultati di bilancio, 2020-2025), "Servizi Abitativi a Canone Convenzionato (SACC)" (interventi, non ERP), canoni di singoli comuni (Monza ecc.). **Nessun dataset su patrimonio, sfitti, graduatorie.** Il "Contatore Alloggi Sfitti di Regione Lombardia" e la Piattaforma regionale dei servizi abitativi esistono (citati nei bilanci ALER 2019) ma non sono aperti.

### 2.3 Rapporti annuali al Consiglio regionale (Osservatorio regionale sulla condizione abitativa)
Pagina: regione.lombardia.it/politiche-sociali-e-abitative/abitare-in-lombardia/osservatorio-regionale-sulla-condizione-abitativa. Scaricati in `raw/regione_rapporti_sap/`: zip dei Rapporti 2014-2022 (nove file chiamati 2014, 2015, 2017, 2017_2, 2018, 2019, 2020, 2021, 2022: **nessun file 2016 né 2023**; la numerazione è quella dei nomi nello zip, ogni file ha la sua data di riferimento in `patrimonio_sap_milano_serie.csv`), Rapporto 2024 (dati al 15/7/2025), Rapporto 2025 (DGR 6666 del 3/8/2026, dati al 3/7/2026), monitoraggio assegnazioni 2025 (1 pagina, solo Lombardia). Da qui: patrimonio SAP per ambito (riga "Milano Città"), avvisi/domande/assegnazioni, occupazioni abusive (p.43 del Rapporto 2025), casi di quartiere (Lorenteggio, Gratosoglio, San Siro, via Bolla).

### 2.4 ALER Milano - amministrazione trasparente
- **Prospetto n.5 "entrate da canoni di locazione per titolo giuridico"** (`aler.mi.it/amministrazione-trasparente/canoni-incassati/`, `raw/aler_trasparenza/canoni/prospetto_<anno>.pdf`): 2018-2025, 2 pagine l'uno. È la fonte migliore sugli sfitti, con il motivo. Copre **tutto il territorio ALER Milano** (53.143 alloggi a canone sociale nel 2025), non solo la città.
- Stessa pagina, anni 2013, 2015, 2016: elenco di **edifici** (località, indirizzo, canone fatturato nell'anno). Mancano 2014 e 2017.
- **Bilanci consuntivi 2019-2025** (`raw/aler_trasparenza/bilanci/`): le relazioni sulla gestione 2019-2023 (8-10 mila righe di testo ciascuna) non contengono il numero degli sfitti; contengono le occupazioni abusive 2013-2023 e i programmi di recupero. 2024 e 2025: solo bilanci sintetici (6 e 5 pagine).
- **Pagina "Patrimonio"** (`aler_patrimonio_per_uog.csv`): 335 righe (UOG, località, destinazione). Milano città (UOG1, UOG2, UOG4): 35.312 alloggi, 3.549 box/posti auto, 2.313 commerciali, 295 strumentali. Il totale scritto sulla pagina (70.947) supera di 1.080 la somma delle righe (69.867); non so quale sia giusto. Nessuna data dei dati.

### 2.5 Comune di Milano
- **Slide della delibera di Giunta 30/2026 sul Piano annuale 2026** (`raw/comune_piano_annuale/slide_giunta_30_26.pdf`): consistenza (SAP Comune 25.873, ALER 31.467; SAS 454 e 1.795; altri usi residenziali 1.379 e 1.954; totale 27.706 e 35.216) e alloggi **assegnabili nel 2026** per Municipio, in 5 voci. Tabelle in `pulito/piano_annuale_2026_per_municipio.csv` e `piano_annuale_2026_consistenza.csv`.
- **"Una nuova strategia per la casa"** (20/3/2023), presa dalla copia della Wayback Machine perché il sito del Comune non risponde: la tabella "analisi unità per stato di utilizzo" (p.38) e i numeri di p.34 e p.57.
- La delibera CC n.7 del 2/3/2026 e i piani annuali 2022-2025: non scaricabili (503, poi 403). Da riprovare.

### 2.6 MM spa, Corte dei conti, altro
MM spa (www.mmspa.eu): 403 ai programmi, non aggirato. Corte dei conti: nessun documento con numeri sugli sfitti ALER Milano trovato. Numeri di giornali e di Pagella Politica (6/6/2023, lettera Rizzi del 10/10/2022; tabella regionale al 31/3/2023 non pubblica): in `pulito/numeri_fonti_secondarie.csv`, **solo come confronto**, mai come base (sintesi lette via web, originali non pubblici).

## 3. Tabelle pulite (`pulito/`)

| File | Contenuto | Anni | Fonte (file, pagina) |
|---|---|---|---|
| `patrimonio_sap_milano_serie.csv` | unità SAP Comune / ALER / totale, Milano Città | 2017-2026 (9 edizioni) | Rapporti regionali, riga "Milano Città" (pagina nel file) |
| `aler_sfitti_serie.csv` | una riga per anno e voce del Prospetto n.5 (alloggi, mq) | 2018-2025 | `prospetto_<anno>.pdf` p.1-2 |
| `aler_vuoti_serie_armonizzata.csv` | vuoti ALER con definizione costante + controllo di somma | 2018-2025 | derivata dal precedente |
| `stato_utilizzo_marzo_2023.csv` | assegnati / liberi / sfitti per carenze, SAP-SAS-SAT, Comune e ALER, città | marzo 2023 | strategia 2023 p.38 |
| `piano_annuale_2026_per_municipio.csv`, `piano_annuale_2026_consistenza.csv` | alloggi assegnabili 2026 per Municipio e voce; consistenza | 2026 | slide Giunta 30/2026 p.3-7 |
| `avvisi_milano.csv` | per avviso: aperture, alloggi in avviso, domande, assegnati | 2019, 2020, 2022, 2024, 2025 | Rapporti 2020, 2022, 2024, 2025 |
| `domande_assegnazioni_erp_milano_2016_2020.csv` | domande in graduatoria e assegnazioni | 2016-2020 | Rapporti 2017-2020 |
| `domande_per_alloggio.csv` | rapporto domande / alloggi, % assegnati | come sopra | derivata |
| `occupazioni_abusive_serie.csv` | occupazioni consolidate ALER (2013-2025) e Comune/MM (2021-2025) | 2013-2025 | bilanci ALER; Rapporto 2025 p.43 |
| `aler_stabili_canone_<anno>.csv`, `aler_stabili_nil_<anno>.csv`, `aler_stabili_per_nil.csv`, `aler_stabili_per_municipio.csv`, `nil_aler_stabili_abitazioni.csv` | edifici ALER di Milano con canone fatturato, assegnati ai NIL e ai Municipi, con abitazioni del NIL | 2013, 2015, 2016 | Prospetti ALER; civici del Comune (`citta-15-minuti/out/civici_tempi.csv`); abitazioni da `censimenti/pulito/indicatori_NIL.csv` |
| `aler_patrimonio_per_uog.csv` | unità ALER per UOG, località, destinazione | senza data | pagina ALER |
| `quote_su_abitazioni.csv` | SAP / abitazioni (censimento 2011, registri 2021 e 2023) | - | derivata |
| `numeri_citati_documenti.csv` | 23 numeri "titolo" con pagina del PDF trovata dal programma | - | vari |
| `numeri_fonti_secondarie.csv` | confronti da giornali e Pagella Politica (non verificabili) | - | vari |
| `riepilogo.json` | i numeri principali | - | |

Controlli fatti: ogni numero preso da un PDF è cercato nel testo della pagina citata (se manca il programma si ferma); la somma "con contratto + senza contratto + vuoti = totale ALER" torna in tutti gli anni (scarto 0); Comune SAP 21.737+1.021+3.731 = 26.489 (torna); ALER SAP 24.333+394+3.274 = 28.001 contro 32.017 (**mancano 4.016**, il documento non dice dove); ALER Milano città: 35.312 alloggi dalla pagina Patrimonio contro 35.216 della slide del Piano 2026 (SAP+SAS+altri usi): differenza 96, coerente; ALER Prospetto 2021 sfitti 8.350 contro "oltre 8.300" della lettera Rizzi al 31/12/2021 (stessa origine: ALER). Aggancio edifici ALER ai NIL: 1.824 su 1.882 edifici del 2016 con indirizzo e civico identici, 32 con civico vicino della stessa via (entro 20 numeri), 5 con nome approssimato, 21 non trovati (3,5% del canone).

## 4. Riepilogo

### 4.1 Quante e di chi
- Serie Milano Città (`patrimonio_sap_milano_serie.csv`): Comune 23.172 (31/3/2018) → 26.010 (3/7/2026); ALER 34.821 → 33.044; totale 57.993 → 59.054 (+1.061). La Regione scrive che l'aumento del Comune è dovuto alla "riclassificazione" di alloggi comunali prima in "altri usi residenziali" (5.974 nel 2018; 1.261 nel 2026): in parte è carta, non edilizia. Per ALER la discesa include alloggi spostati in "valorizzazione" (la Regione dice "inclusi gli alloggi valorizzati" dal 2024).
- Non-SAP: SAS e SAT (servizi abitativi sociali e transitori) 1.985 nel 2023 (126 Comune, 1.859 ALER); altri usi residenziali del Comune 1.379 (Piano 2026).
- Complessi: il Comune conta **273 complessi** a Milano, 200 "cielo-terra" (100% comunali) con 22.876 unità in 682 edifici (strategia 2023 p.34). Casi citati dai documenti (`numeri_citati_documenti.csv`): Lorenteggio circa 2.600 alloggi ALER (Rapporto 2025 p.24); Gratosoglio 12 fabbricati/782 alloggi in efficientamento e 120 sfitti da recuperare (p.47); via Bolla circa 250 SAP (p.48); San Siro 3 stabili/195 SAP in riqualificazione (p.50); San Siro ALER 4.285 alloggi pubblici, 785 occupati abusivamente (Milano Post 17/10/2026, ricerca Politecnico-Sicet: fonte secondaria). **Non esiste un elenco aperto dei complessi con numero di alloggi**; Quarto Oggiaro: nessun numero di alloggi nei documenti (112 edifici ALER nel NIL Quarto Oggiaro-Vialba-Musocco nel 2016, 1,8% del canone).

### 4.2 Vuote, per motivo e nel tempo
- Città, marzo 2023 (Comune, tabella 03): vedi punto 3. Il Comune dice anche 27.075 unità comunali, 22.113 assegnate, 4.962 "sfitte e da ristrutturare" (p.57): somma coerente con 26.489+altro.
- ALER, serie 2018-2025 (`aler_vuoti_serie_armonizzata.csv`, alloggi): sfitti come scritti da ALER 5.919 / 6.830 / 7.872 / 8.350 / 6.263 / 6.351 / 6.442 / 5.175; vuoti armonizzati 5.919 / 6.830 / 7.872 / 8.350 / 8.070 / 7.890 / 7.713 / 7.735, cioè 10,8% → 15,4% (2021) → 14,6% (2025) degli alloggi ALER. In ristrutturazione: 4.184 (2018), 5.267 (2021), 5.983 (2024), 4.313 (2025).
- Piano 2026 (Comune e ALER insieme, assegnabili nel 2026): 2.047 SAP, di cui 220 in carenza manutentiva assegnabili com'è, 1.268 dopo ristrutturazione già programmata, 301 da nuova costruzione, 258 da turn-over (le quattro voci sommano esattamente a 2.047: 220+1.268+301+258; Comune 70+468+301+58 = 897, ALER 150+800+0+200 = 1.150). È l'unico dato sui flussi attesi, non sugli sfitti.
- Per Municipio (Piano 2026, assegnabili): ALER+Comune: Municipio 6 (560), 5 (328), 7 (401), 4 (278), 9 (197), 8 (182), 3 (53), 2 (44), 1 (4). Il Municipio 6 ha 340 assegnabili del Comune (il massimo), il 5 e il 4 il massimo di ALER (261, 248).

### 4.3 Per NIL (solo edifici ALER, canone fatturato 2016)
`nil_aler_stabili_abitazioni.csv`: 50 NIL su 88 hanno almeno un edificio ALER; i primi 5 NIL fanno il 33,9% del canone. Canone ALER 2016 per abitazione del NIL (euro, solo descrittivo): Gratosoglio 941, Bovisasca 496, Barona 448, Muggiano 400, Monluè-Ponte Lambro 327, Scalo Romana 293, Lambrate-Ortica 287, San Siro 273. Non ci sono gli edifici del Comune (MM): quindi niente Quarto Oggiaro intero, né Molise-Calvairate per intero. Non ho dati sugli sfitti per NIL.

### 4.4 Domande contro assegnazioni (Milano città)
- Per anno degli avvisi (`domande_per_alloggio.csv`): domande per alloggio in avviso 31,0 (2019), 39,9 (2020), 24,3 (2022), 27,8 (2024), 24,6 (2025); assegnati sul pubblicato 84,3%, 65,5%, 85,2%, 82,9%, 79,1% (assegnazioni registrate in ritardo: i numeri più recenti possono salire).
- Domande in graduatoria 2016-2020 (`domande_assegnazioni_erp_milano_2016_2020.csv`): 25.706, 27.234, 25.192, 25.192, 25.192; assegnazioni 781, 872, 859, 1.225, 451. Il valore 25.192 è identico per tre anni di fila: probabile dato non aggiornato.
- Lombardia 2025: 92 avvisi, 3.090 alloggi, 46.060 domande (circa 43.700 nuclei, stima regionale); Milano città 38,5% delle domande. Assegnati nel 2025 in tutta la Lombardia: 3.076 (935 comuni, 2.141 ALER; `monitoraggio_assegnazioni_2025.pdf`). Per Milano non esiste il totale annuo degli assegnati.
- Le domande sommate sugli avvisi possono contare due volte lo stesso nucleo (nel 2022 Milano ha fatto 3 avvisi).

## 5. La cosa più sorprendente

**ALER Milano ha ridotto i suoi "sfitti" del 38% dal 2021 al 2025 (da 8.350 a 5.175), ma i suoi alloggi vuoti sono ancora 7.735, cioè solo il 7% in meno.** Dal 2022 il Prospetto n.5 elenca a parte gli alloggi destinati a valorizzazione (2.003 nel 2025), vendita (401) e demolizione (156), che fino al 2021 stavano dentro "sfitti" (la somma col totale ALER lo conferma in 8 anni su 8). Un confronto, non una causa: la riduzione c'è nei numeri, in parte è un cambio di caselle. Seconda sorpresa, più piccola: parte della crescita delle case popolari del Comune dal 2018 (+2.838) è riclassificazione di alloggi già suoi (lo scrive la Regione), non case nuove.

## 6. Limiti dei dati

- **Non esistono dati aperti.** Quasi tutto è nei PDF; ho estratto con programmi, ma PDF cambiano impaginazione tra un anno e l'altro (i controlli automatici fermano il programma se un numero non si ritrova nella pagina).
- **Perimetro diverso tra fonti.** Prospetto ALER = tutta ALER Milano (53.143 alloggi a canone sociale), le tabelle del Comune e del Rapporto regionale = città (Comune + ALER, SAP). Non si possono mettere sulla stessa curva. Non posso dividere gli sfitti ALER tra città e provincia.
- **"Sfitti" non ha un significato fisso.** In ALER fino al 2021 includeva vendita e valorizzazione, dopo no. Per il Comune "sfitto" = carenza manutentiva, "libero" = in ristrutturazione/riatto: "in ristrutturazione" può essere un cantiere vero o un alloggio quasi pronto (lo dice anche Pagella Politica citando il sindacato Sicet). Il numero dei bilanci ALER ("unità immobiliari") include box e posti auto.
- **Gli sfitti per la città esistono una volta sola (marzo 2023).** Nessuna serie per il Comune/MM; il Piano annuale non è una misura degli sfitti; i piani 2022-2025 non erano scaricabili.
- **ALER 2023, tabella del Comune:** 4.016 unità SAP su 32.017 non sono né assegnate né libere né sfitte nella tabella (probabilmente occupate abusivamente e altre voci): non so quali.
- **Occupazioni abusive:** due serie ALER diverse per lo stesso anno (2021: 3.128 nei bilanci, 3.194 nel Rapporto regionale 2025); il Prospetto n.5 "senza contratto" (2.713 nel 2025) conta più cose delle sole occupazioni consolidate (2.324).
- **Domande:** niente anni 2021 e 2023 (il Rapporto 2023 non è sul sito della Regione; il Rapporto 2021 non ha le tabelle degli avvisi); domande sommate tra avvisi; 25.192 ripetuto tre anni; il Rapporto cambia formato tra 2017-2020 e 2022-2025.
- **Per NIL:** gli edifici ALER del 2016 sono vecchi di dieci anni; il canone fatturato include negozi, box e uffici (non è il numero degli alloggi) e la morosità è alta; mancano gli edifici del Comune; i NIL a cavallo di due Municipi sono assegnati al Municipio prevalente. Il quartiere "Lorenteggio" dei documenti sta in gran parte nel NIL Giambellino.
- **Pagina ALER Patrimonio:** nessuna data; totale scritto 1.080 sopra la somma delle righe.
- **Fonti secondarie** (giornali, Pagella Politica): lette tramite sintesi, originali non pubblici o pagine non aperte: non usate per i numeri principali.
- **Licenze:** nessuna dichiarata sui PDF; si citano numeri, non si ripubblicano i file.

## 7. Cosa può mostrare una pagina (senza giudicare)

1. Il numero: 59.054 case popolari, 7,1% delle abitazioni; di chi sono (Comune 26.010, ALER 33.044).
2. Un grafico a barre unico delle case popolari vuote, 14,4% nel marzo 2023, diviso per motivo e per ente (Comune 17,9%, ALER 11,5%), con la nota "dato unico per la città".
3. La serie ALER 2018-2025 con **due linee**: "sfitti come scritti" e "vuoti per qualsiasi motivo", con la spiegazione del cambio di caselle.
4. Domande e assegnati: una barra per anno (domande per alloggio 24-40), con i buchi 2021 e 2023 mostrati come buchi.
5. Una mappa per NIL degli edifici ALER (2016) con avvertenza "solo ALER, canone fatturato, non alloggi".
6. Occupazioni abusive 2013-2025 (ALER) e 2021-2025 (Comune), separate dai vuoti.

## 8. Come ripetere
Vedi `STATO.md`.
