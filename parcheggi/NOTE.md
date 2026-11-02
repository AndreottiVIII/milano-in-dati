# Parcheggi: quanto spazio alle auto - FASE 1 (raccolta, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorsi assoluti>` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle in `pulito/`. Tutti i numeri sono in `pulito/riepilogo.json`.

## 1. In breve (e la cosa che sorprende)

1. **Il Comune non pubblica, in dati aperti, quanti stalli ci sono su strada, né per tipo né per quartiere.** Il dataset "Ambiti della sosta" (ds83, CC-BY) ha i 36 perimetri ma i campi `posti_pagamento`, `posti_residenti`, tariffe e orari sono **vuoti in tutte le righe**. Nessun dataset su strisce blu/gialle/disabili/carico-scarico (17 parole chiave cercate, 509 schede viste).
2. **L'unico totale ufficiale che ho trovato è di seconda mano**: la presentazione "La sosta a Milano" (Paola Taglietti, Comune di Milano, sul sito di partecipazione del Comune) dice circa **297.000 stalli su strada**, di cui, in % sul totale: blu 37,2, gialli residenti 18,2, disabili 1,9, carico/scarico 1,5, autorizzati 2,0, **non regolamentati (bianchi) 39,2**. Io non ho potuto aprire il PDF: il server del Comune risponde 403 ai programmi (non ho aggirato il blocco; il browser integrato ha provato a scaricarlo e ha mostrato una finestra di salvataggio, che non ho completato). Le cifre le ho da Sicurauto (7/2/2025: "circa 300 mila" in totale, "180 mila" regolamentati, "poco più di 100 mila" bianchi, stesse percentuali) e da una ricerca che cita lo stesso PDF. Le percentuali sommano 60,8% = circa 180.000 su 297.000, quindi sono quote sul totale (Motori Magazine le legge, a torto, come quote sui regolamentati). **Da verificare sul PDF originale**: lo può aprire Davide dal browser (`https://partecipazione.comune.milano.it/uploads/decidim/attachment/file/685/LA_SOSTA_A_MILANO__Paola_Taglietti.pdf`). Anno della rilevazione non noto.
3. **Stima dell'area**: 297.000 x 12 m² = **3,56 km²** (sensibilità: 2,97 con 10 m², 4,46 con 15 m²) = **1,96% della superficie del Comune** (181,76 km²) = circa **500 campi da calcio** (105 x 68 m = 7.140 m²). Per abitante: 2,5 m² (1.407.044 residenti 2024). Per autovettura: 5,0 m².
4. **Auto: 706.764 autovetture nel 2025** (PRA, ds529 del Comune); 699.002 nel 2024 (identico a ACI Autoritratto 2024, riga MILANO). Solo livello comunale: per quartiere non esiste in forma aperta. Quindi **0,42 stalli su strada per auto**, ovvero 2,4 auto per stallo; 502 auto ogni 1.000 abitanti.
5. **La cosa che sorprende**: lo spazio di sosta su strada (3,6 km²) è circa **10 volte quello di tutte le corsie e piste ciclabili** (194 km, circa 0,37 km² con larghezze ipotizzate) e circa **12 volte quello di tutte le aree pedonali** (0,30 km²); per ogni milanese ci sono 2,5 m² di sosta su strada contro 18,8 m² di verde urbano (ds2926, 2023). E **quasi 4 stalli su 10 (39%) sono ancora senza alcuna regola** (strisce bianche), anche se gli ambiti regolamentati coprono il 61% della città e l'82% dei km di strada.
6. **Per quartiere (NIL) i posti su strada sono una mia stima** (ripartizione per lunghezza di strada, vedi 5.2): la mappa per NIL è costruita su perimetri veri (ambiti), parcheggi fuori strada reali (Comune e OpenStreetMap), ciclabili reali; ma i posti per NIL no.

## 2. Fonti, una per una (licenza, data, cosa manca)

Licenza dei dataset del Comune: nel catalogo CKAN `license_id = cc-by` ("Creative Commons Attribution", versione non scritta). Ripubblicabili citando "Comune di Milano - dati.comune.milano.it". Scaricati il 1/11/2026 con `scripts/download_comune.py` (log in `raw/download_log.csv`); ricerca CKAN in `scripts/search.py` (`raw/search_all.json`).

| Fonte | Cosa è | Data | Licenza | Mancano |
|---|---|---|---|---|
| **ds83 Ambiti della sosta** (`raw/comune_ds83/`) | 36 poligoni (35 ambiti + sottoambito 901 = 1A), nome, numero. CSV + GeoJSON | scheda modificata 8/5/2026; geometrie senza data | CC-BY | **posti, tariffe, orari, delibera: tutti vuoti** |
| **ds342 Parcheggi pubblici** (`raw/comune_ds342/`) | 53 parcheggi in struttura: nome, posti, indirizzo, tipo (autorimessa convenzionata 32, pubblici/residenti 15, pubblici 6). Totale **11.351 posti** | scheda 8/5/2026; elenco senza data | CC-BY | occupazione, tariffe, orari; è l'elenco dei parcheggi del Comune/convenzionati, NON di tutte le autorimesse (private) |
| **ds45 Parcheggi di interscambio** (`raw/comune_ds45/`) | 21 righe, 17.867 posti (19 in città = 16.753; Cologno Nord 614 e Gessate 500 sono fuori Comune). Testo libero "N POSTI AUTO (di cui rosa, disabili)" | scheda 8/5/2026 | CC-BY | **occupazione/posti liberi: non pubblicati**; tariffe |
| ds740 Bus turistici, ds51 Aree pedonali/ZTL, ds670 sosta biciclette, ds79 car sharing, ds540 colonnine | scaricati; usato ds51 (aree pedonali AP: 110 poligoni, 0,297 km²) | 2026 | CC-BY | |
| **ds60 Itinerari ciclabili** (`raw/comune_ds60/`) | 4.411 tratti: tipologia (corsia, pista, promiscuo), sede, marcia, lunghezza | scheda 25/10/2026 | CC-BY | **larghezze** (ipotizzate da me: 1,5 m per senso, 2,5 m se bidirezionale) |
| **ds529 Parco veicolare** (`raw/comune_veicoli/`) + ds721, ds1094 | autovetture, motocicli ecc. dei veicoli iscritti nel Comune (PRA/ACI), serie 2007-2025 | 2025 | CC-BY | per quartiere; solo "iscritte a Milano" (non dove sono parcheggiate) |
| **ACI Autoritratto 2024** (`raw/aci_autoritratto_2024/`) | Parco_veicolare_2024.ods, foglio 45: MILANO 699.002 autovetture, 196.912 motocicli, 995.550 veicoli totali. Letto con `scripts/ods_lettore.py` (solo libreria standard) | pubblicato 11/2025 | CC-BY 4.0 (dichiarata da aci.gov.it) | sotto il comune non c'è nulla; ACI 2025 è un .rar (non scaricato) |
| **Pass sosta residenti** ds700/ds701 (`raw/comune_pass/`) | 22.504 + 36.646 richieste, ambito e categoria | solo 9/2017-2/2019 (online) e 2018 (sportello) | CC-BY | niente dopo il 2019: **non usabile per contare i pass attivi** (non usato) |
| **OpenStreetMap** (`pulito/osm_parcheggi.pkl`, ricavato dal file Lombardia del 29/10/2026 già in `bici-auto-mezzi/raw/osm_lombardia/`) | `scripts/osm_parcheggi.py`: 4.334 nodi e 21.959 way di parcheggio, 659 relazioni (non risolte), 181.476 strade con tutti i tag, nel rettangolo di Milano | OSM 29/10/2026 | ODbL 1.0 | copertura molto parziale (vedi 4) |
| **ATM, tariffe della sosta su strada** (`raw/atm/tariffe_e_aree_sosta.pdf`, 514 KB) | tabella per codice-ambito: Area C 3,00 euro/h (max 2 h), filoviaria 2,00, extra-filoviaria 1,20, interscambio via Impastato a fasce, bus turistici 8,00; "dal 1 novembre 2023" | 11/2023 | non indicata (PDF di ATM): **non ripubblicare il file, solo i valori** | |
| Sicurauto 16/6/2026 | stesse tariffe, per ambito (Area C = ambiti 1,3,4,5,6,7; filoviaria = 2, 9-23; extra = 8, 25, 30, 31, 34, 35, 36, 40, 42, 43). Gli ambiti 32 e 33 sono "extra" nel PDF ATM (codici 3219, 3319) | 2026 | giornale: solo fatti | un articolo dice che nei festivi non si paga, la tabella dice "tutti i giorni" per Area C: **da controllare sul cartello** |
| Sicurauto 7/2/2025, Motori Magazine 8/2/2025 | 297.000 / 180.000 / 100.000+ (vedi 2) | 2025 | giornale: solo fatti | PDF originale non letto |
| Discoradio (ricerca) | "circa 83.000" stalli blu, senza anno chiaro (probabilmente 2023): 37,2% di 297.000 = 110.000 blu. **I due numeri non coincidono**: o l'offerta blu è cresciuta (il Comune vuole eliminare le strisce bianche), o sono definizioni diverse. Non risolto. | | | |
| Comune, FAQ abbonamento sosta (ricerca) | extra-filoviaria: 50 euro/mese, 500 euro/anno (40 e 400 con abbonamento ATM); pass residenti | | | da verificare |

Non trovato / non fatto: stalli per ambito; occupazione dei parcheggi di interscambio (nessun dato aperto); geoportale del Comune (non consultato: il portale CKAN ha già gli stessi dati); ACI per quartiere (non esiste); Overpass (non serviva: ho letto il file locale).

## 3. Pulizia (cosa ho fatto)
- Strade: dal file OSM tengo `highway` in residential, tertiary, secondary, primary, unclassified, living_street, trunk e i loro `_link`; escludo service (cortili), pedonali, autostrade, sentieri. Le taglio sugli 88 NIL (poligoni vigenti ds964 del filone citta-15-minuti): **1.859,9 km** in città, di cui 1.521,3 km dentro gli ambiti e 338,6 km fuori (appartenenza dal punto medio di ogni pezzo).
- NIL: punto in poligono; tutti i 53 parcheggi ds342 e le 19 interscambio in città cadono in un NIL (nessuno scartato).
- Residenti per NIL: `alberi/pulito/nil_alberi.csv` (ds205 anno 2024, totale 1.407.044); superfici dai poligoni (181,76 km²). I NIL con meno di 5.000 residenti (24 su 88, parchi e aree quasi vuote) non entrano nelle classifiche per abitante.
- Nessun dato cancellato. I poligoni OSM di parcheggio sono tenuti come sono (area dal poligono, UTM 32N): 1.774 poligoni "fuori strada" nel Comune, 2,72 km² (2,70 km² uniti: quasi nessuna sovrapposizione).

## 4. Che cosa dice OpenStreetMap (e perché non basta per i posti su strada)
- **Fuori strada** (`amenity=parking`, escluso street_side/lane): 1.774 poligoni nel Comune, **2,72 km²**: a raso 2,59 km² (1.724 poligoni), in struttura/sotterranei 0,127 km² (47), coperti 0,001. Il 28% dell'area è marcata private/clienti/permesso (`access`), il 42% senza `access`. **Capacità dichiarata solo su 139+4 poligoni** (6.581 + 5.250 posti): non è un conteggio dei posti. Sono dati di area, non di posti. Ingressi `parking_entrance`: 522 in città (sotterranei e strutture: nessuna capacità). `building=garages`: 1.420 edifici, 0,32 km² (box privati: molto incompleto).
- **Su strada**: aree `parking=street_side/lane`: 697 poligoni, 0,152 km² = circa 12.600 stalli a 12 m²; 3.118 stalli singoli (`parking_space`), di cui 1.445 su strada. In totale **circa il 5% dei 297.000**: la mappatura è molto parziale e non uniforme.
- **Tag sulle strade**: solo il **14,8%** dei km di strada ha un tag `parking:*` (275,5 km). Sui lati di strada dove c'è un tag (532 km di lato), la sosta è ammessa nel **46%**. Estendendo questa quota a tutti i km di strada si ottengono 286.000-312.000 stalli (6,0-5,5 m per stallo): **dello stesso ordine di grandezza di 297.000**, ma è solo un controllo, non un dato: le strade con tag non sono un campione casuale.

## 5. Riepilogo

### 5.1 Stalli su strada per tipo (città intera; da Taglietti via stampa, area a 12 m²)
| Tipo | % | Stalli | Area km² |
|---|---|---|---|
| Blu (a pagamento) | 37,2 | circa 110.500 | 1,33 |
| Gialli (residenti) | 18,2 | circa 54.000 | 0,65 |
| Disabili | 1,9 | circa 5.600 | 0,07 |
| Carico/scarico | 1,5 | circa 4.500 | 0,05 |
| Autorizzati | 2,0 | circa 5.900 | 0,07 |
| Liberi (bianche) | 39,2 | circa 116.400 | 1,40 |
| **Totale** | 100 | 297.000 | 3,56 |

### 5.2 Per quartiere (stima mia, `pulito/nil_parcheggi.csv`)
Ipotesi: densità di stalli uniforme lungo le strade, 159,7 stalli per km di strada (un posto ogni 6,3 m di strada, cioè ogni 12,5 m per lato). I circa 180.000 regolamentati stanno tutti nei 36 ambiti (74% degli stalli di dentro; fuori dagli ambiti tutti liberi). **Questo non è un dato, è un modello**: i posti per NIL dipendono quasi solo dai km di strada, e nel centro (zone pedonali, Area C, cordoli con aiuole) la densità reale sarà più bassa. Risultati: tra i 64 NIL con almeno 5.000 residenti, mediana 2,4 m² di stalli per abitante (da 1,2 a Loreto-Casoretto-NoLo a 6,8 a Maggiore-Musocco-Certosa); quota di area del quartiere occupata dagli stalli dallo 0,8% (Monluè-Ponte Lambro) al 4,2% (Buenos Aires-Porta Venezia-Porta Monforte).
Dati veri per NIL: quota di area dentro gli ambiti (`quota_area_in_ambiti_pct`), km di strade dentro e fuori, posti dei parcheggi ds342 e ds45, area di parcheggi fuori strada OSM, km e area delle ciclabili, aree pedonali.

### 5.3 Ambiti e tariffe
- 36 ambiti = **111,5 km², il 61,4% del Comune** (Area C/Bastioni 8,4; filoviaria 22,2; extra-filoviaria 81,1; interscambio 0,14) e l'82% dei km di strada.
- Tariffe orarie (ATM, in vigore dal 1/11/2023): **3,00 euro** Area C / Bastioni (max 2 h per ambito; 8-19 tutti i giorni, 19-24 prime 2 ore); **2,00 euro** cerchia filoviaria (feriali 8-19; alcune zone tutti i giorni fino alle 24); **1,20 euro** extra-filoviaria (feriali 8-19; 10 euro al giorno per San Siro/Ippodromo nei giorni di eventi); interscambio via Impastato (ambito 38) a fasce da 1,50 a 4,00; bus turistici 8,00. Notte (24-8) gratis in Area C.
- Per la tariffa di un indirizzo: `pulito/ambiti.csv` (ambito, cerchia, tariffa).

### 5.4 Parcheggi fuori strada
- Ufficiali: ds342 11.351 posti (53 parcheggi) + ds45 interscambio 16.753 posti in città (19) = **28.104 posti**, cioè 4,0 posti ogni 100 autovetture. Interscambio più grandi: Famagosta 2.200, Lampugnano 2.000, Molino Dorino 1.700, Bisceglie 1.400, Cascina Gobba 1.373, Bovisa 1.200.
- Occupazione: **non pubblicata**.
- Totale dei posti in autorimesse, box e cortili privati: **non esiste in dati aperti** (è la parte di sosta più grande, ma invisibile in questi dati).

### 5.5 Auto e spazio per altro
- Autovetture 2025: 706.764; 2023: 701.443; 2011: 724.450 (ds1094): la città ha poche auto in meno di 15 anni fa.
- Ciclabili: 194,3 km (127,4 km piste in sede propria, 67,0 km corsie dipinte), area stimata 0,367 km². Aree pedonali (ds51 AP): 0,297 km².
- Verde urbano: 18,8 m² per abitante nel 2023 (ds2926, fonte ISTAT).

## 6. Limiti (per la pagina: "limiti dei dati")
1. Il totale di 297.000 stalli e la sua ripartizione vengono da una presentazione del Comune che non ho letto direttamente; anno non noto; una fonte parla di 83.000 stalli blu (2023?) contro 110.000 derivati.
2. 12 m² per stallo è un'ipotesi (5 x 2,2 m + manovra); sensibilità 10-15 m². Il posto in diagonale/a pettine occupa più spazio, quello in doppia fila nessuno.
3. I posti per NIL sono un modello per lunghezza di strada, non un conteggio.
4. Le auto sono le iscritte al PRA a Milano, non quelle che stanno ferme a Milano.
5. Gli stalli su strada non sono tutte le auto ferme: 0,42 stalli per auto, il resto sta in box, cortili, parcheggi interrati: dato inesistente in forma aperta.
6. OSM è parziale (5% dei posti su strada mappati, 14,8% delle strade con tag): le aree di parcheggio fuori strada sono la parte più completa ma senza capacità.
7. Ciclabili: larghezze ipotizzate; non sono contate le strade 30 e i percorsi promiscui. Pedonali: solo aree pedonali formali (ds51), non marciapiedi.
8. Tariffe: due fonti secondarie discordano su festivi e su una tariffa precedente; la fonte di riferimento è il PDF ATM del 2023.
9. Interscambio: ds45 è un elenco senza data; i posti sono scritti in un campo di testo.

## 7. Cosa può mostrare una pagina (fase 2)
Il box "cosa sorprende" (3,6 km², 500 campi da calcio, 10x ciclabili, 2,5 m² vs 18,8 m² di verde), mappa per NIL con 3 viste (area dentro gli ambiti = dato vero; parcheggi a raso OSM = area vera ma mappatura parziale; stima dell'area di sosta su strada = modello, in etichetta), tipi di stallo, tariffe per cerchia, parcheggi di interscambio, metodo e limiti, file.
