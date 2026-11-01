# Quanto costa vivere a Milano - FASE 1 (raccolta, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web, nessun giudizio. Ogni numero dice file e campo. Programmi in `scripts/` (si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di costo-vita>`; elenco in STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`, tutti i numeri qui sotto sono anche in `pulito/riepilogo_costo_vita.txt` / `.json` (script `riepilogo.py`).

## 1. In breve

1. **Prezzi in euro di prodotti veri a Milano esistono, ma solo dal gennaio 2021**: l'Osservatorio Prezzi e Tariffe del Ministero (MIMIT) pubblica, mese per mese e provincia per provincia, prezzo minimo / massimo / medio di oltre 120 beni e servizi in 6 tipologie (caffe' al bar, cappuccino, biglietto del tram, pasto in pizzeria, pane, taglio di capelli, benzina...). Ho scaricato Milano per 69 mesi (gen 2021 - set 2026) e per 3 delle 6 tipologie (alimentari, servizi, energetici: 87 prodotti); le altre 3 (ortofrutta, ittici, cura persona/casa) solo per i primi 22 mesi, poi interrotte perche' non servono alla domanda. **Prima del 2021 non c'e' nessuna fonte aperta di prezzi in euro per Milano**: per il passato ci sono solo gli indici (numeri indice, "100 = anno base").
2. **Gli indici dei prezzi di Milano (ISTAT, pubblicati dal Comune, CC-BY) vanno dal 2005 fino a settembre 2026**, fino al dettaglio di circa 200-240 voci ("pane", "pizza", "energia elettrica", "affitti", "benzina", "autobus"...). L'indice generale di Milano parte dal 2011 (2005-2010 non c'e'); prima del 2005 c'e' solo il **tasso di inflazione annuo di Milano dal 2000** (e mensile dal 1971): serve per il confronto con l'Italia.
3. **Milano contro Italia (indice generale, medie annue)**: 2000-2025 Milano +58,0%, Italia +63,3%; 2010-2025 +31,4% contro +31,8%; 2020-2025 +19,2% contro +19,4%. Cioe': prima del 2010 i prezzi sono saliti un po' meno a Milano, dopo uguale.
4. **Lo shock energetico 2022-23 a Milano e' stato enorme**: indice dell'energia elettrica a 419 (2015=100) a novembre 2022 contro una media 2021 di 123 (+241% al picco); gas 272 contro 104 (+161%); benzina +24%, gasolio +33% al picco. L'inflazione mensile di Milano (ds1499) tocca il **12,0% a dicembre 2022**. Nel 2025 elettricita' e gas stanno ancora +50% e +42% sopra il 2021.
5. **Il biglietto del tram/metro/bus (ATM) e' passato da 1,00 a 2,20 euro: +120%**, contro un'inflazione di Milano 2002-2025 del +51%. Passaggi: 1,50 (1 sett 2011), 2,00 (15 lug 2019), 2,20 (9 gen 2023). **Ma l'indice ISTAT del trasporto su autobus di Milano e' salito solo dell'8% dal 2015 al 2025**: perche' il biglietto occasionale pesa poco rispetto agli abbonamenti, rimasti fermi (mensile 39 euro dal 2019, annuale 330).
6. **Caffe' espresso al bar a Milano (MIMIT)**: media 1,02 euro (gen 2021) -> 1,26 euro (set 2026), +23,5%; cappuccino 1,40 -> 1,72. Il caffe' sale piu' o meno quanto l'inflazione generale (+22,7% nello stesso periodo): non c'e' un "caffe' a 1 euro" tradito. Il range min-max dei locali rilevati e' 1,0-1,5 euro (marzo 2024).
7. **Affitti: due serie che dicono cose molto diverse.** Il canone dei contratti in corso (ISTAT, voce "affitti reali") a Milano e' salito del +24% in 10 anni (2015-2025) e +19% in 5; i valori OMI dei contratti nuovi (Agenzia delle Entrate, STIME) del +64% e +55%. Un appartamento di 60 m2 in zona mediana OMI costava 503 euro al mese nel 2015, 745 nel 2024, 864 nel primo semestre 2026.
8. **Affitto e redditi**: un mese d'affitto per 60 m2 (stima OMI) valeva il 31,9% del reddito mensile mediano dei dichiaranti (2006), il 27,8% nel 2021 (minimo), il **34,5% nel 2024**. In ore di lavoro (a tempo pieno, 173 ore al mese): 55 ore nel 2006, 48 nel 2021, 60 nel 2024. I redditi sono disponibili solo fino al 2024 (anno d'imposta): l'affitto 2026 non si puo' confrontare.
9. **Il 2026 e' un secondo scossone, piu' forte del 2022 sui carburanti**: nei distributori di Milano la benzina self passa da 1,70 euro/litro (dic 2025) a 2,108 (set 2026), il gasolio self da 1,67 a 2,265: sopra i massimi mensili del giugno 2022 (2,053 e 2,002); indice del gas di rete +23% da dicembre 2025 a settembre 2026; inflazione mensile Milano 3,7% a settembre 2026 (ds1499, ds2977).
10. **Mancano**: bar e pizzeria in indice dopo il 2016 (sono stati fusi in una voce unica), prezzi in euro prima del 2021, prezzo di una pizza in pizzeria (c'e' "pasto in pizzeria" 8-19,5 euro), stipendi veri per mestiere, mediana dei redditi da fonte diretta (e' un'interpolazione).

## 2. Fonti (tutte lette il 1/11/2026)

| Fonte | Cosa | Anni | Licenza | File in raw/ |
|---|---|---|---|---|
| Comune di Milano, dati.comune.milano.it (CKAN) | indici NIC di Milano per gruppi, classi, sottoclassi, voci (ds240-248 per 2005-2015; ds1431-1437 per 2016-2025; ds2976-2982 per 2026; ds91 divisioni 2011-15) | 2005-gen 2026... set 2026 | CC-BY (campo `license_id=cc-by` nel catalogo; versione non scritta) | `raw/comune/dsNNN/` (+ `_metadati.json`) |
| Comune, ds1499 e ds1821 | tasso di inflazione mensile (dal 1971) e annuale (dal 2000) "calcolato sui prezzi rilevati nel Comune di Milano" (fonte ISTAT) | 1971-2026 / 2000-2025 | CC-BY | `raw/comune/ds1499`, `ds1821` |
| Comune, redditi Irpef su base comunale (MEF) | ds941-ds957, 1267, 1589, 1824, 2274, 2276, 2733, 2947, 3010 (un file per anno d'imposta, Milano), ds310, ds531 (classi di reddito 2008-2024) | anni d'imposta 2000-2024 | CC-BY | `raw/comune/` |
| ISTAT esploradati (SDMX) | NIC Milano (ITC45) e Italia (IT): 12 divisioni 2016-2025, 3 cifre 2011-2025, 2026; NIC Italia 1996-2025 tutte le basi, ECOICOP 2 | 1996-2026 (Italia), 2011-2026 (Milano) | ISTAT: CC BY (come da note legali ISTAT; non ho riletto la pagina il 1/11: **da verificare**) | `raw/istat_sdmx/` |
| MIMIT Osservatorio Prezzi e Tariffe (osservaprezzi.mise.gov.it) | prezzi min / max / medio, Milano, 3 tipologie (alimentari, servizi, energia) | gen 2021 - set 2026 (69 mesi) | pagina "note legali": testi CC-BY 3.0 IT, dati "alle condizioni della licenza con cui sono pubblicati" (la licenza dei dati non e' scritta in modo esplicito: **citare la fonte, chiedere conferma prima di ripubblicare i file**) | `raw/mimit_osservaprezzi/AAAA_MM_tipo.html` (69 mesi x 3 tipologie + 22 mesi x 3 tipologie minori = 273 pagine), `raw/web_probe/` |
| MIMIT carburanti, archivio trimestrale (opendatacarburanti.mise.gov.it) | "prezzo alle 8", impianti di Milano | 2015-2026 | IODL 2.0 (dichiarata nella pagina) | `raw/mimit/archivio_milano/` (i tar.gz originali, 40-110 MB l'uno, sono stati cancellati dopo l'estrazione: dimensioni e sha256 in `raw/download_log.csv`); snapshot del giorno 31/10/2026 in `raw/mimit/` |
| ATM, pagine ufficiali (biglietti e abbonamenti) e stampa (Il Giorno, Open, Sky TG24) | prezzi del biglietto e degli abbonamenti, storico | 2002-2026 | pagine ATM e articoli: **non riproducibili**, ho trascritto solo i numeri e la fonte | `raw/atm/` |
| Agenzia delle Entrate OMI (dal filone `prezzi-case/`) | affitti in euro/m2/mese per zona, mediana delle zone, "Abitazioni civili" | 2006-S1 - 2026-S1 | CC BY 4.0 (pagina Forniture dati OMI) | `prezzi-case/pulito/prezzi_citta_mediana_zone.csv` (non copiato) |

Elenchi di controllo: `raw/comune_search_all.json` (ricerca CKAN, 347 pacchetti), `raw/istat_sdmx/avail_*.xml` (dimensioni e valori dei flussi ISTAT), `raw/download_log.csv` (ogni scaricamento con data, dimensione, sha256).

**Provati e non utili**:
- ISTAT SDMX, flusso "1999-2010 provinciale" (`144_125_DF_DCSP_NICDUE_1`): per Milano contiene solo una riga vuota (2002-01, nessun valore). Quindi **non c'e' un indice provinciale ISTAT per Milano prima del 2011 in SDMX**; si usano i file del Comune (2005-2010).
- MIMIT "Osservatorio prezzi e tariffe" vecchio indirizzo (`osservatorioprezzi.mise.gov.it`) non risponde; il sito nuovo e' `osservaprezzi.mise.gov.it`. Le tipologie "ortofrutta", "ittici", "cura della persona e della casa" non le ho scaricate (non servono alla domanda; si possono aggiungere lanciando `osservaprezzi_milano.py` con i nomi `orto,ittici,groc`).
- MIMIT carburanti dataset corrente: solo foto del giorno; il passato e' nell'archivio trimestrale (usato).
- Retribuzioni contrattuali ISTAT (flussi `155_*`): non scaricate. Per il confronto ho usato i redditi Irpef dei residenti di Milano (piu' vicini a "quanto guadagna chi vive a Milano").
- Il Comune non ha dataset di "prezzi medi" in euro (ds639 Osservatorio Milano e ds120 sulla spesa delle famiglie 2007-2013 non sono prezzi).

## 3. Come e' fatto il dato e come l'ho pulito

**Indici NIC (`scripts/build_nic.py`)**. Quattro file diversi con quattro basi: 2005-2010 base 1998=100 (`ds240/242/244/248`), 2011-2015 base 2010=100 (`ds241/243/245/91`), 2016-2025 base 2015=100 (`ds1431-1437`), 2026 base 2025=100 (`ds2976-2982`). Li porto tutti a **base 2015=100** con la media annua 2010, 2015 e 2025 come anno di aggancio (stesso principio ISTAT; gli indici hanno una cifra decimale, errore tipico 0,2-0,5 punti percentuali). **Controllo**: l'indice generale di Milano dei file del Comune coincide con quello ISTAT SDMX (ITC45, 00) su 189 mesi, differenza massima 0,00. **Controllo dei raccordi**: salto dicembre -> gennaio ai tre punti di aggancio, confrontato col salto tipico mensile (in `pulito/controlli_nic.txt`): quasi sempre sotto l'1%; le eccezioni sono beni dai prezzi volatili (benzina +3,4% a gen 2011, -4,0% a gen 2026; gasolio -6,4% a gen 2016; elettricita' +6,5% a gen 2026).
- Valori `0,0` nei file del Comune = dato mancante: li ho trattati come mancanti (altrimenti falsano le medie).
- Nomi con accenti rotti ("Caff", "CaffŠ", "Gas di citt"): abbinati per prefisso.
- Le 29 voci scelte e i nomi nei 4 segmenti sono in `scripts/build_nic.py` (`ITEMS`); ogni cambio di definizione e' scritto nella colonna nota di `pulito/riepilogo_indici_voci.csv`.
- Divisioni di spesa (`nic_milano_divisioni_base2015.csv`): solo quelle con lo stesso contenuto prima e dopo il 2026 (00-07, 10, 11); la 08, 09, 12 cambiano con la classificazione ECOICOP 2 e non le ho raccordate.

**Indice generale annuale 2000-2025 (`nic_milano_generale_annuo_2000_2025.csv`)**. Per il 2000-2010 Milano non ha un indice in nessun file: ho ricostruito il livello **concatenando i tassi annui del Comune (ds1821, una cifra decimale)**; controllo sul 2011-2025, dove l'indice vero esiste: errore massimo 0,08 punti (2025=100). Per il 2000-2010 l'errore non e' controllabile: in 25 anni gli arrotondamenti possono sommare 0,3-0,5 punti percentuali.

**Prezzi in euro MIMIT (`scripts/parse_osservaprezzi.py`)**: pagine HTML -> `pulito/prezzi_medi_milano_mimit.csv` (anno, mese, tipologia, prodotto, quantita', unita', min, max, medio; 6.795 righe). Controllo: la pagina dice quale anno, mese e provincia mostra: uguale a quello richiesto in tutte le pagine. Il prodotto cambia nome nel tempo ("Pane Fresco" -> "Pane Fresco Con Farina Di Grano" dal 2022) e, per i carburanti, l'unita' passa da "Cl 1" a "L 1" ad agosto 2021 (errore di etichetta: il prezzo e' continuo).

**Affitti e redditi (`scripts/build_affitti_redditi.py`)**:
- affitto = mediana, tra le zone OMI di Milano, del centro (min+max)/2 delle quotazioni di locazione "Abitazioni civili", euro/m2/mese, media dei due semestri; x 60 m2 (ipotesi). E' una **stima** (valore OMI, non un contratto) e una mediana non pesata (zone 55 fino al 2013, 40-42 dopo: vedi NOTE di `prezzi-case/`).
- reddito mediano = mediana del reddito complessivo dichiarato ai fini Irpef dai residenti di Milano, **interpolata linearmente dentro le classi** (0-10, 10-15, 15-26, 26-55 mila euro...) dai file del Comune: **non e' una mediana diretta** (la mediana 2024 cade in 15-26 mila); non conta chi non presenta dichiarazione. Mensile = annuo/12. Reddito = anno d'imposta (la dichiarazione e' presentata l'anno dopo).
- ore di lavoro = affitto / reddito mensile x 173 ore al mese (ipotesi: tempo pieno, 40 ore x 52 / 12). Il reddito dichiarato include pensioni e redditi parziali: non e' il salario orario di chi lavora a tempo pieno. Il reddito da lavoro dipendente per dichiarante (dal 2012): 2.640 euro al mese nel 2012, 3.230 nel 2024.
- Controllo: "Numero contribuenti" ufficiale (2012: 979.681; 2018: 1.017.272; 2024: 1.052.520) e' 2-4% sopra la somma delle classi (957.071; 994.908; 1.013.593): i contribuenti senza classe (presumibilmente reddito complessivo nullo) non stanno nelle classi.

**ATM (`scripts/build_atm.py`)**: trascrizione a mano in `pulito/atm_tariffe_storico.csv` con una fonte per riga.

## 4. Numeri (riepilogo; ogni riga e' nei file pulito/ indicati)

### 4.1 Inflazione (indice generale, medie annue; `nic_milano_generale_annuo_2000_2025.csv`)
| Periodo | Milano | Italia (NIC) |
|---|---|---|
| 2000 -> 2025 | +58,0% | +63,3% |
| 2005 -> 2025 | +42,7% | +44,9% |
| 2010 -> 2025 | +31,4% | +31,8% |
| 2015 -> 2025 | +22,2% | +22,6% |
| 2020 -> 2025 | +19,2% | +19,4% |

Tassi annui di Milano: 2021 1,5%; 2022 8,1%; 2023 6,1%; 2024 1,1%; 2025 1,3% (ds1821). Mensile (ds1499): massimo 12,0% a dicembre 2022; 3,7% a settembre 2026.
Per divisioni (`riepilogo_indici_voci.csv`), 2020 -> 2025, Milano contro Italia: alimentari +21,1% contro +27,3%; abitazione, acqua, elettricita' e combustibili +47,5% contro +43,1%; trasporti +21,1% contro +19,5%; servizi ricettivi e ristorazione +30,5% contro +24,2%.

### 4.2 Cosa e' salito di piu' e di meno a Milano (voci; media 2025 sulla media dell'anno)
- **Dal 2005**: piu' su: energia elettrica +160%, alberghi +128%, acqua +98%, giornali +91%, treno +86%, caffe' in pacchetto +79%. Meno su: assicurazione auto +29%, trasporto autobus +24%, tariffa rifiuti +14%, medicinali -22%, istruzione universitaria -33%, telefonia -39%.
- **Dal 2010**: elettricita' +120%, alberghi +97%, acqua +90%, caffe' +69%, gas +60%, giornali +58%; in coda: autobus +24%, rifiuti +14%, assicurazione auto +9%, medicinali -7%, telefonia -34%, universita' -42%.
- **Dal 2020**: gas +74%, alberghi +73%, elettricita' +72%, acqua +48%, caffe' +35%, gasolio +24%; in coda: assicurazione auto +8%, parrucchiere uomo +6%, medicinali +4%, telefonia -4%, universita' -7%, rifiuti -9%.
- Altre voci (2005 -> 2025): pane +57%, pasta +58%, latte +45%, uova +76%, ristoranti e pizzerie +58%, affitti ISTAT +52%, taxi +57%, cinema e teatri +50%, benzina +48%, sigarette +77%. Bar (solo 2005-2015) non confrontabile.
- **Diffidare di** (vedi trappole): spese condominiali (serie 2005-2010 con molti zeri), istruzione universitaria (indice quasi dimezzato nel 2021: effetto di come si misurano le tasse), telefonia (2005-2010 fissa + mobile insieme), alberghi (stagionali, +/-10% al mese).

### 4.3 Shock energetico 2022-23 (indici Milano, base 2015=100, `riepilogo_costo_vita.txt`)
| Voce | media 2021 | picco (mese) | picco su 2021 | media 2022 su 2021 | media 2023 su 2021 | media 2025 su 2021 | set 2026 |
|---|---|---|---|---|---|---|---|
| Energia elettrica | 122,9 | 419,4 (nov 2022) | +241% | +112% | +100% | +50% | 212,8 |
| Gas di rete | 104,2 | 271,5 (nov 2022) | +161% | +85% | +67% | +42% | 171,2 |
| Benzina | 108,6 | 134,5 (giu 2022) | +24% | +12% | +13% | +6% | 137,8 |
| Gasolio auto | 109,1 | 144,7 (lug 2022) | +33% | +22% | +20% | +11% | 160,9 |
Indice generale di Milano: media 2021 104,0; il +8,1% del 2022 e +6,1% del 2023 sono in gran parte energia e alimentari (alimentari +7,1% nel 2022 e +9,4% nel 2023 per la divisione 01 di Milano).

### 4.4 Il biglietto ATM (`atm_tariffe_storico.csv`)
Biglietto ordinario urbano: 1.500 lire (0,77 euro) fino al 6 gennaio 2002; 1.950 lire = 1,00 euro da gennaio 2002; 1,50 euro dal 1 settembre 2011 (durata da 75 a 90 minuti); 2,00 euro dal 15 luglio 2019 (delibera del Consiglio comunale del 25/6/2019); 2,20 euro dal 9 gennaio 2023; **2,20 euro ancora il 1/11/2026** (sito ATM). Il passaggio da 1,00 a 2,20 e' +120%; con l'inflazione di Milano 2002-2025 (+51,3%), 1 euro del 2002 vale 1,51 euro 2025: il biglietto di oggi costa 1,45 volte il valore reale di allora. Da 1,50 (2011) a 2,20: +47% contro un'inflazione del +27,4%. Altri titoli: carnet 10 corse 13,80 (2011) -> 18 (2019) -> 19,50 (2023); giornaliero 4,50 -> 7 -> 7,60; mensile ordinario 35 -> 39 (2019, fermo da allora), annuale 330 (fermo dal 2019); mensile giovani fino a 27 anni 22 euro, annuale 200.
**Verifica**: la tua ipotesi "1,00 -> 2,20" e' confermata dall'articolo de Il Giorno (9/1/2023: "Poi 1 euro, 1.50, 2" e 2,20) e dalle pagine ATM; il 2,00 e' confermato da Open (26/6/2019) e Sky TG24 (9/1/2023: "da 2 a 2,20"). Il 2011 e il 2002 vengono da un solo articolo (Il Giorno): **non ho trovato un secondo riscontro** (delibera, sito ATM dell'epoca; la pagina ATM del 2019 sul nuovo sistema tariffario oggi da' "pagina non trovata"). La stampa non e' uniforme sul giorno del 2019 (Il Giorno: "1 luglio", Open: 15 luglio).
Confronto con l'indice: autobus Milano ISTAT 2015 -> 2025 +8,1%, 2019 -> 2025 +9,3%, 2011 -> 2025 +19,9%: l'indice e' guidato dagli abbonamenti e dagli altri servizi su gomma, non dal biglietto occasionale.

### 4.5 Prezzi in euro a Milano (MIMIT Osservatorio, media dei locali rilevati; `prezzi_medi_milano_mimit.csv`)
| Prodotto | gen 2021 | set 2026 | var. | media 2021 | media 2025 |
|---|---|---|---|---|---|
| Caffe' espresso al bar | 1,02 | 1,26 | +23,5% | 1,04 | 1,22 |
| Cappuccino al bar | 1,40 | 1,72 | +22,9% | 1,39 | 1,64 |
| Panino al bar | 4,36 | 5,87 | +34,6% | 4,52 | 5,60 |
| Pasto in pizzeria | 10,14 | 14,09 | +39,0% | 10,74 | 13,32 |
| Pasto al fast food | 6,97 | 10,87 | +56,0% | 6,92 | 9,44 |
| Biglietto trasporto urbano | 2,00 | 2,20 | +10,0% | 2,00 | 2,20 |
| Pane fresco (euro/kg) | 4,11 | 4,95 | +20,4% | 4,19 | 4,89 |
| Taglio capelli uomo | 22,03 | 21,97 | -0,3% | 21,77 | 21,57 |
| Cinema, biglietto | 9,18 (mag 2021) | 9,28 | +1,1% | 9,14 | 9,27 |
| Taxi, corsa per l'aeroporto | 95 | 114 | +20,0% | 96,3 | 114 |
| Benzina senza servizio (euro/l) | 1,47 | 2,10 | +42,4% | 1,64 | 1,74 |
| Gasolio senza servizio (euro/l) | 1,35 | 2,24 | +65,4% | 1,50 | 1,67 |
| B&B, una notte | 65,55 (mag 2021) | 173,44 | +164,6% | 70,7 | 147,3 |
| Tariffa rifiuti (100 m2) | 308,96 | 263,36 (dic 2025) | -14,8% | 309,6 | 273,6 |
Altri valori del marzo 2024: oculista 120,7 euro; dentista otturazione 142 euro; lavaggio auto 14,6; autorimessa 203 euro/mese; riparazione auto 88 euro; bed and breakfast 131 euro; tutti nel file.
Sul confronto con l'indice: pane +20,4% (prezzo, gen 2021 - set 2026) contro l'indice ISTAT del pane di Milano +18,4% (media 2021 - 2025); espresso +23,5% contro l'indice generale +22,7% (media 2021 -> set 2026).

### 4.6 Affitto, redditi e ore di lavoro (`affitto_vs_reddito.csv`)
| Anno | affitto 60 m2 (OMI, stima) | reddito mensile mediano (interpolato) | quota | ore di lavoro |
|---|---|---|---|---|
| 2006 | 502,5 | 1.574,6 | 31,9% | 55,2 |
| 2010 | 495,0 | 1.668,0 | 29,7% | 51,3 |
| 2015 | 503,2 | 1.765,1 | 28,5% | 49,3 |
| 2019 | 522,8 | 1.842,8 | 28,4% | 49,1 |
| 2021 | 522,8 | 1.879,7 | 27,8% | 48,1 |
| 2022 | 591,0 | 1.949,6 | 30,3% | 52,4 |
| 2023 | 669,0 | 2.060,5 | 32,5% | 56,2 |
| 2024 | 745,5 | 2.159,9 | 34,5% | 59,7 |
Affitto OMI "civili": 8,38 euro/m2/mese nel 2006 e 8,39 nel 2015 (nominali: **identici in 9 anni**), 12,43 nel 2024, 14,40 nel 2026-S1 (= 864 euro per 60 m2). In euro 2025 (FOI): 11,6 (2006) -> 14,1 (2026-S1) per m2.
Il reddito dichiarato medio ("imponibile addizionale") per contribuente: 2.747 euro al mese nel 2006, 3.849 nel 2024.
**ISTAT contro OMI**: affitti ISTAT Milano 2015 -> 2025 +24,1%, 2020 -> 2025 +19,0%; OMI nuovi contratti 2015 -> 2025 +64,4%, 2020 -> 2025 +55,4%.

### 4.7 Carburanti nei distributori di Milano (archivio MIMIT)
Fonte: `pulito/carburanti_milano_mensile.csv` (da `build_carburanti.py`; 47 trimestri 2015-01 / 2026-09, 141 mesi; impianti con Comune = MILANO e Provincia = MI nelle anagrafiche; 492 impianti nell unione di 33 anagrafiche trimestrali (tutti i trimestri dal 2015-1 al 2021-3, poi solo il 1o trimestre di ogni anno e il 3o 2026: impianti chiusi tra un campione e l altro potrebbero mancare); ogni giorno ~200 impianti self e ~130 serviti con prezzo). Per ogni giorno, mediana dei prezzi degli impianti; per ogni mese, media delle mediane. Euro al litro.
| Carburante | gen 2015 | gen 2021 | picco 2022 | dic 2025 | set 2026 |
|---|---|---|---|---|---|
| Benzina self | 1,476 | 1,484 | 2,053 (giu 2022) | 1,700 | **2,108** |
| Benzina servita | 1,556 | - | - | - | 2,281 |
| Gasolio self | 1,393 | 1,373 | 2,002 (giu 2022) | 1,673 | **2,265** |
| Metano (euro/kg) | 1,037 | 0,999 | 2,822 (ott 2022) | 1,449 | 1,799 |
Medie annue benzina self: 2015 1,535; 2016 1,431; 2019 1,577; 2020 1,449; 2021 1,649; 2022 1,836; 2023 1,868; 2024 1,817; 2025 1,729. Gasolio self: 2015 1,407; 2019 1,489; 2021 1,515; 2022 1,850; 2025 1,680. **A settembre 2026 benzina e gasolio a Milano costano piu' del massimo mensile del 2022** (benzina self 2,108 contro 2,053; gasolio self 2,265 contro 2,002). Controllo: la benzina senza servizio dell'Osservatorio MIMIT a settembre 2026 e' 2,099 (media dei prezzi rilevati) contro 2,108 dell'archivio: tornano.
Nota: il prezzo "alle 8" e' quello in vigore, comunicato dal gestore: un impianto che non aggiorna resta con il vecchio prezzo (non l'ho escluso). 411 righe scartate su 4,0 milioni (prezzo fuori da 0,4-4,0 euro). Giorni con file vuoto o senza intestazione nell'archivio (es. 14-15 gennaio 2015, 3-4 ottobre 2019, 7 maggio 2020, 25 dicembre 2020, 20-22 febbraio 2021): saltati.

## 5. Trappole

1. **Livelli e confronti nel tempo**: lo dice il Ministero (pagina "Beni e servizi di largo consumo"): *"i confronti temporali possono essere effettuati correttamente solo utilizzando gli indici dei prezzi al consumo"*; i livelli in euro di un mese possono riferirsi a marca, confezione e punto vendita diversi dal mese precedente e non vanno confrontati tra mesi e tra citta'. Quindi il caffe' a 1,02 e a 1,26 euro e' una **buona indicazione**, non una misura esatta; la crescita vera di un prodotto si legge nell'indice. Il prezzo medio del MIMIT per gli alimentari confezionati e' una media pesata su ~1.800 punti vendita (scanner data), per carburanti e servizi la media semplice delle quotazioni raccolte dai Comuni.
2. **Il "caffe' al bar" in indice non c'e' dopo il 2015**: la voce "consumazioni al bar" (2005-2015) sparisce e diventa "Ristoranti, pizzerie, bar e simili": la serie `ristoranti` ha una rottura nel 2016 (raccordata con la media 2015, ma e' un'altra cesta). Nel 2026 la voce diventa "Ristoranti, bar e simili - con servizio completo".
3. **Il canone ISTAT non e' un prezzo di mercato**: "affitti reali" misura i canoni di tutti i contratti in corso (anche quelli vecchi, spesso bloccati); l'OMI stima i valori di mercato dei nuovi contratti, per zona, come intervallo min-max scelto dal rilevatore. Sono due fenomeni diversi: non sono in contraddizione, ma non vanno scambiati.
4. **OMI = stime**, non contratti; mediana non pesata tra zone; il numero di zone cambia (55 -> 40 nel 2014, 42 dal 2024/25): la mediana puo' muoversi per il cambio di zonizzazione, non solo per i prezzi.
5. **Mediana interpolata**: calcolata dalle classi di reddito (non esiste la mediana ufficiale nei file); l'errore dipende da come i redditi si distribuiscono dentro la classe 15-26 mila (dove cade). Il reddito dichiarato non e' lo stipendio: include chi lavora parte dell'anno, pensionati, redditi bassi e nulli.
6. **Le ore di lavoro sono un conto illustrativo** (173 ore/mese, 60 m2 fissi). Se si usasse un 70 m2 o il reddito da lavoro dipendente (3.230 euro al mese nel 2024), le ore scenderebbero ma la tendenza (minimo 2021, salita 2022-24) no.
7. **L'inflazione di Milano 2000-2010 e' ricostruita dai tassi annui**, non da un indice vero (vedi sopra); per quel periodo il confronto con l'Italia (indice vero) ha un'incertezza di qualche decimo di punto.
8. **Le basi cambiano**: mai confrontare i numeri di un indice con quelli di un altro file senza passare da `pulito/` (base 2015=100).
9. **Voci con serie tagliate**: pasta e telefonia mancano nel 2026; pizza (confezionata, non pizzeria) c'e' solo dal 2011; gasolio e parrucchiere dal 2011; "trasporto urbano 2005-2010" e' una voce, dal 2011 "autobus e pullman" (comprende l'extraurbano).
10. **Zeri nei file del Comune**: il valore 0,0 e' dato mancante (spese condominiali 2005-2010, ad es.), non indice zero. Trattati come mancanti, ma chi usa i file grezzi deve saperlo.
11. **Energia 2026 per MIMIT**: la tipologia "energetici" per Milano non ha dati da gennaio ad agosto 2026 (la pagina del sito non mostra righe), c'e' solo settembre 2026. Il carburante del 2026 si legge dall'archivio carburanti, non dall'Osservatorio.
12. **Cinema**: la media annua 2024 (7,86 euro) e' bassa per un cambio di campione dei locali, il biglietto non e' sceso davvero.
13. **Mojibake nei file del Comune** (ds244, ds248, ds245 con "?" al posto delle lettere accentate): trattati con prefissi, vedi sopra.
14. **I testi di stampa su ATM non si ripubblicano**: nella pagina servono i numeri e il nome della fonte.
15. **Il quadro 2026 non e' completo**: il Comune ha gli indici fino a settembre 2026; i redditi arrivano al 2024; l'affitto OMI al primo semestre 2026.

## 6. Cosa potrebbe mostrare una pagina

- **Una sola frase d'apertura**: "In 20 anni il biglietto del tram e' passato da 1 a 2,20 euro; l'inflazione e' stata la meta'." (verificare con un secondo riscontro il 2002 e il 2011 prima di pubblicare).
- **Grafico principale**: indice (2005 = 100) di 8-10 voci di Milano (pane, caffe', affitti ISTAT, elettricita', gas, benzina, autobus, alberghi, telefonia) con l'indice generale in grigio: si vedono le due impennate (2008 e 2022) e le voci che scendono. Da usare i dati di `nic_milano_voci_base2015.csv`.
- **Lo shock del 2022**: elettricita' e gas come mensile 2020-2026, con il 12,0% di inflazione di dicembre 2022 nel titolo.
- **Il biglietto**: una scala con i 4 gradini (1,00 / 1,50 / 2,00 / 2,20) e accanto "se fosse salito come l'inflazione sarebbe 1,51 euro".
- **Il caffe'**: una tabella "cosa costava a gennaio 2021 e cosa a settembre 2026" con 8 prodotti reali (caffe', cappuccino, pane, pizzeria, taxi aeroporto, benzina...), con la nota che sono medie rilevate e non vere e proprie serie.
- **Affitti**: due linee "ISTAT (contratti in corso)" contro "OMI (nuovi contratti, stima)" dal 2006; poi "quante ore di lavoro per un mese d'affitto" 2006-2024 (55, 48, 60). Il messaggio e' in quanto cambia dal 2021.
- **Milano contro Italia**: tabella a 5 righe (2000/2005/2010/2015/2020 -> 2025). La differenza e' piccola: dirlo.
- **Cosa non mostrare** come fatto: confronti mensili di livelli MIMIT con precisione al centesimo; la mediana del reddito come dato ufficiale; i valori 2005-2010 delle voci con definizione cambiata.

## 7. Non fatto / da decidere

- Seconda fonte per il biglietto 2002 e 2011 (delibere del Comune/ATM; archivio Wayback del sito ATM).
- Tipologie MIMIT mancanti (ortofrutta, ittici, cura persona/casa) e provincia di confronto (Roma, Torino...) per dire se Milano e' piu' cara: il Ministero stesso sconsiglia i confronti tra citta'.
- Prezzi in euro prima del 2021: nessuna fonte aperta; si potrebbero cercare le "rilevazioni prezzi medi" della Camera di Commercio di Milano o delle riviste di consumatori, ma non sono dati aperti.
- Retribuzioni contrattuali ISTAT (indici per settore) e ore lavorate Eurostat per un vero salario orario.
- Altri affitti: Immobiliare.it / Idealista (non aperti) e canoni concordati del Comune.
- Spesa delle famiglie milanesi (ds120, 2007-2013) per capire quanto pesano pane o carne nel bilancio: non usato.
