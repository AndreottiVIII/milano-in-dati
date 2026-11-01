# Quali scuole si svuoteranno - FASE 1 (solo analisi)

Fatto il 1 novembre 2026. Niente pagina web, niente git. Programmi in `scripts/` (Python 3.12, `python -I -X utf8 <script> <percorso assoluto di milano-in-dati> <percorso assoluto di scuole-domani>`), risultati in `out/`.
Sigle: **anno N** = anno scolastico N/N+1 (2024 = 2024/25); **riferimento 2015** = a.s. 2015/16; "bande di eta'" = infanzia 3-5 anni, primaria 6-10, secondaria di I grado 11-13 (eta' compiuta al 31/12 dell'anno N, stessa regola di `scuole/NOTE.md`).

**Questo e' uno scenario, non una previsione.** Dice che cosa succede agli iscritti se i bambini che abitano a Milano oggi crescono e vanno a scuola come hanno fatto finora. Non sa nulla di arrivi e partenze di famiglie, nuove case, scelte delle famiglie, chiusure o fusioni di scuole.

## 1. In breve

1. **Scenario centrale, tutta la citta', iscritti nelle scuole di Milano** (stesse scuole del 2024/25, tre ordini): infanzia 26.522 (2024) -> 25.780 (2025) -> 24.090 (2029) -> **24.190 (2034), -8,8%**; primaria 54.137 -> 52.150 -> 46.550 -> **43.750, -19,2%**; secondaria di I grado 35.370 -> 34.840 -> 32.040 -> **28.020, -20,8%** (`out/proiezione_citta.csv`). A parita' di alunni per classe del 2024 (21,1 / 19,8 / 20,7) sono circa 110, 520 e 360 classi in meno rispetto a oggi (solo un conto, non un piano).
2. **Gran parte del calo e' gia' "scritto" perche' i bambini sono gia' nati.** I ragazzi che nel 2034 faranno la secondaria di I grado hanno oggi 2-4 anni e abitano a Milano: lo scenario non fa nessuna ipotesi sulle nascite per questo ordine (-20,8% in qualsiasi scenario di nascite). Per la primaria l'88% del calo 2024-2034 e' gia' scritto al 2031; per l'infanzia tutto il calo e' scritto al 2028 (-8,9%). L'incertezza sulle nascite pesa solo sull'infanzia: nel 2034 da 22.140 (nascite che continuano a calare come negli ultimi 5 anni, -1,8% l'anno) a 26.400 (nascite che risalgono allo stesso ritmo) (`out/sensibilita_scenari.csv`).
3. **Differenze tra quartieri: piccole nello scenario, e non per caso** (vedi 6): per i NIL con almeno 300 iscritti il cambio 2024-2034 degli iscritti nelle primarie va da -25,5% a -15,8% (scarto tipico 2 punti); infanzia da -12,9% a -6,5%; secondaria di I grado da -27,2% a -16,8% (`out/proiezione_nil.csv`). I bambini che *abitano* nel NIL cambiano molto di piu' (primaria 6-10 anni, 2025 -> 2034: da -43% a +48%, scarto tipico 13 punti, `out/proiezione_residenti_nil.csv`), ma la prova all'indietro dice che questo non aiuta a prevedere le scuole (vedi 4).
4. **Scuole con iscritti proiettati nel 2034 sotto il 70% di quelli del 2015** (scenario centrale; solo scuole presenti nel 2015 e nel 2024): infanzia **74 su 284**, primaria **92 su 210**, secondaria di I grado **47 su 136**. Di queste ne sono gia' sotto nel 2024: 47, 32, 12. Il 70% e' una soglia vicina alla media: tra il 2015 e il 2034 la primaria perde in media il 26% (59.092 -> 43.750). Con soglia 60% / 80% i numeri sono in `out/sorpresa_soglie.csv`. Una scuola e' "robusta" se e' sotto la soglia in tutte e 6 le varianti: infanzia 51, primaria 76, secondaria 42 (`out/scuole_sotto_70.csv`, colonna `tenuta_del_risultato`). **L'elenco e' meno affidabile per le singole scuole che per i totali** (vedi 4).
5. **Prova all'indietro** (si proietta dal passato e si confronta col vero), totali di citta': partendo dal 2014 e proiettando il 2019 l'errore e' +2,1% (infanzia), 0,0% (primaria), +1,4% (sec. I); dal 2019 al 2024 -1,8%, +1,5%, -0,4%. "Tenere gli alunni fermi" sbaglia di piu': +6,7/-0,8/-6,1% e +14,4/+9,2/+4,9%. Per le singole scuole l'errore e' molto piu' grande: nel caso 2019->2024 la meta' delle scuole ha un errore minore di 12,5% (infanzia), 12,5% (primaria), 13,7% (sec. I) e solo il 37%, 43%, 41% e' entro il 10%.
6. **La cosa piu' sorprendente**: il quartiere dove vivono i bambini dice pochissimo sulle scuole del quartiere. Vedi 5.

## 2. Dati usati (ogni numero dice file e campo)

| Che cosa | File | Campo | Licenza / fonte |
|---|---|---|---|
| Iscritti per singola scuola, 2009-2024, infanzia, primaria, sec. I | `scuole/pulito/scuole_anno_tidy.csv` | `iscritti`, `codice`, `id_nil` (NIL della sede), `anno_inizio` | Comune di Milano, ANASCO (ds224/225/226), CC BY |
| Classi per scuola | stesso file | `classi` | idem |
| Residenti per NIL, eta' singola 0-100, genere, 1999-2025 (31/12) | `popolazione/pulito/residenti_nil_anno_eta_genere.csv` | `residenti` | Comune di Milano, ds27, CC BY |
| Confini dei 88 NIL | `citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson` | geometria, `ID_NIL` | Comune di Milano, CC BY. Servono per sapere quali NIL confinano |
| Nati (contesto) | `nomi-bambini/raw/milano_nascite/ds289_nascite.csv` (2003-2020), `ds1945_...csv` (2021-2024) | totali | Comune di Milano, CC BY. Per l'anno 2024 i nati avvenuti a Milano sono 9.165 (somma di `Numerosita'` in ds1945), i residenti di 0 anni a fine 2024 sono 8.792 (ds27): non coincidono perche' ds289/ds1945 contano per luogo del parto. **Nel modello si usano i residenti di 0 anni (ds27).** |
| Altre fonti guardate | `scuole/raw/comune_ds1736-1741` (ds1739 = primaria, citta') | % di alunni residenti in un altro NIL | Hanno la **percentuale**, non la matrice NIL di residenza -> NIL della scuola. I flussi tra NIL **non sono nei dati aperti**. |

## 3. Metodo (semplice, tutto in `scripts/lib.py`)

1. **Bambini dell'area, anno per anno.** Per ogni area (un NIL, un NIL con i NIL confinanti, tutta la citta') si parte dai residenti per eta' singola al 31/12/2025 e si fanno "invecchiare" di un anno per ogni anno di proiezione: chi ha a anni nel 2025 ne ha a+1 nel 2026 (metodo delle coorti). **Nessun arrivo o partenza** (rapporto di passaggio = 1): la prova all'indietro dice che usare i passaggi osservati negli ultimi 5 anni non migliora (anzi, nei totali e' leggermente peggio; e' una variante).
2. **Nati futuri.** I bambini ancora da nascere (dopo il 2025) entrano con 0 anni secondo lo scenario: *stabili* = media dei residenti di 0 anni 2023-2025 (centrale); *in calo* = continuano a calare allo stesso ritmo degli ultimi 5 anni della citta' (-1,76% l'anno); *in risalita* = salgono allo stesso ritmo. Servono solo dal 2029 per l'infanzia e dal 2032 per la primaria; mai per la sec. I.
3. **Dai bambini agli iscritti.** Per ogni scuola: iscritti(anno N) = iscritti 2024 x (bambini dell'area nella fascia d'eta' dell'ordine nell'anno N / stessi bambini nel 2024). Cioe' si applica alla scuola il rapporto osservato oggi tra iscritti e bambini, e lo si tiene fisso (e la quota che ciascuna scuola ha nel suo NIL). Poiche' non ci sono i flussi NIL -> scuola, i movimenti tra NIL (il 54% degli alunni di primaria va a scuola fuori dal proprio NIL, ds1739 2023/24) restano dentro questo rapporto e non vengono modellati.
4. **Area di riferimento: scelta con la prova all'indietro.** Provate: solo il NIL della scuola, il NIL piu' i confinanti, i confinanti dei confinanti, tutta la citta', e miscele. A livello di scuola e di NIL sono tutte equivalenti tra loro nel passato, tranne "solo il NIL" che e' peggiore. Metodo **centrale** = media geometrica tra la variazione della citta' e quella del NIL piu' i confinanti (metà e metà): stesso errore della sola citta', ma lascia vedere le differenze locali. Varianti: `solo_citta`, `solo_nil`, `con_migrazione` (passaggi osservati), piu' le due varianti di nascite. Le sei combinazioni sono in `proiezione_scuole.csv` (`p2034_...`).
5. **Fasce di errore.** Nel file delle scuole le colonne `fascia_bassa_`/`fascia_alta_` (2029, 2034) sono la proiezione moltiplicata per il 10° e il 90° percentile del rapporto reale/proiettato misurato nella prova all'indietro, per ordine e orizzonte (`out/backtest_bande_errore.csv`). Per 10 anni: infanzia 0,62-1,14; primaria 0,68-1,34; sec. I 0,65-1,58. Quindi, per esempio, una primaria proiettata a 200 iscritti nel 2034 ha un intervallo 136-268 che copre l'80% dei casi passati.

## 4. Prova all'indietro: quanto ci si puo' fidare

Procedura (`scripts/02_backtest.py`): per ogni anno di partenza T da 2010 a 2023 e orizzonte da 1 a 10 anni si usano solo gli iscritti fino a T e i residenti fino a T+1 (come oggi: iscritti fino al 2024, residenti fino al 31/12/2025), si proietta e si confronta con gli iscritti veri. Le scuole confrontate sono quelle presenti (con iscritti) in entrambi gli anni; chiusure, fusioni e scuole nuove restano fuori dal confronto per scuola ma entrano nei totali.

**I tre casi chiesti** (`out/backtest_casi.csv`; errore = proiettato/vero - 1; WAPE = somma degli errori assoluti / somma del vero; il metodo e' quello centrale con nascite stabili):

| Caso | Ordine | Alunni vero | Alunni proiettati | Errore citta' | Errore per NIL (WAPE, NIL con >= 200 alunni) | Errore per scuola (WAPE) | Scuole con errore <= 10% / <= 20% | "Fermo": errore citta' |
|---|---|---|---|---|---|---|---|---|
| 2014 -> 2019 | infanzia | 30.342 | 30.972 | +2,1% | 7,2% | 10,4% | 61% / 81% | +6,7% |
| | primaria | 59.119 | 59.135 | 0,0% | 5,4% | 12,4% | 49% / 73% | -0,8% |
| | sec. I | 37.109 | 37.644 | +1,4% | 10,7% | 16,8% | 31% / 59% | -6,1% |
| 2019 -> 2024 | infanzia | 26.522 | 26.035 | -1,8% | 7,4% | 15,2% | 37% / 75% | +14,4% |
| | primaria | 54.137 | 54.938 | +1,5% | 8,0% | 14,5% | 43% / 72% | +9,2% |
| | sec. I | 35.370 | 35.243 | -0,4% | 11,2% | 16,6% | 41% / 65% | +4,9% |
| 2014 -> 2024 (10 anni) | infanzia | 26.522 | 30.736 | +15,9% (con i nati veri: -2,0%) | 18,9% | 21,1% | 39% / 58% | +22,1% |
| | primaria | 54.137 | 56.570 | +4,5% | 12,2% | 20,9% | 34% / 57% | +8,4% |
| | sec. I | 35.370 | 36.623 | +3,5% | 19,7% | 25,8% | 20% / 46% | -1,5% |

Tutte le partenze insieme, 5 anni (`out/backtest_riepilogo.csv`, `backtest_nil.csv`, `backtest_citta.csv`): errore medio assoluto sui totali di citta' 3,1% / 1,6% / 2,3% (infanzia / primaria / sec. I) contro 9,0% / 5,0% / 4,3% di "fermo"; per NIL 8,2% / 7,1% / 12,1% (fermo 11,9 / 8,5 / 11,7); per scuola 12,2% / 12,8% / 17,3% (fermo 13,9 / 13,7 / 16,7).

Che cosa dice la prova, senza abbellire:
- **I totali (citta', e in buona parte i NIL) sono ben previsti a 5 anni; a 10 anni l'infanzia no**, perche' le nascite del 2015-2024 sono scese piu' dello scenario "stabili". Con i nati veri l'errore a 10 anni scende da +15,9% a -2,0%. Per questo l'infanzia ha le tre possibilita' sulle nascite e non una sola.
- **Per le singole scuole il metodo non batte "tenere ferme le scuole" in modo netto**: per la secondaria di I grado, a livello di scuola, e' pari o peggio di "fermo" (17,3% contro 16,7%). La proiezione dice quanto cala l'ordine e il NIL, non quale singola scuola perde piu' bambini.
- **Le differenze locali nei bambini residenti non migliorano la previsione**: usare solo i bambini del NIL fa errori piu' grandi (5 anni, per scuola: 14,9% / 14,3% / 17,6%); NIL piu' confinanti o sola citta' sono uguali (12,0 / 12,8 / 17,2). E' la ragione per cui il metodo centrale e' una media con la citta'.
- **Prova della soglia** (`out/backtest_soglia_riepilogo.csv`, partenze 2014-2019, riferimento = 5 anni prima della partenza, bersaglio = 5 anni dopo, soglia 70%): delle scuole che il metodo mette sotto il 70% del riferimento, quelle che ci sono davvero finite sono il 59% (infanzia), 63% (primaria), 30% (sec. I); ne ritrova (richiamo) il 35%, 28%, 14% di quelle che ci sono finite. Quindi l'elenco sotto il 70% e' un elenco di scuole *a rischio di superare la soglia*, non una lista chiusa; per la secondaria di I grado e' poco informativo a livello di singola scuola.
- La proiezione tende a **sovrastimare un po'** (errore sulla somma delle scuole confrontate, 5 anni: +1,8% infanzia, +1,0% primaria, +2,8% sec. I): la quota di bambini nelle scuole e' scesa piu' dello scenario.

## 5. La cosa piu' sorprendente

**Quello che succede ai bambini che abitano in un quartiere dice pochissimo di quello che succede alle scuole di quel quartiere.** Numeri (`out/sorpresa_quartiere_vs_scuola.csv`, NIL con almeno 200 alunni nel 2015 e nel 2024 e 200 bambini residenti nel 2015, variazione 2015 -> 2024):
- correlazione tra la variazione degli iscritti nelle scuole del NIL e quella dei bambini residenti nel NIL: **0,23 (infanzia, 49 NIL), 0,28 (primaria, 58 NIL), 0,42 (sec. I, 45 NIL)**; se ai bambini del NIL si aggiungono quelli dei NIL confinanti scende a 0,05 / 0,08 / 0,01. In pratica il quartiere spiega il 5% (infanzia), l'8% (primaria) e il 18% (sec. I) delle differenze tra quartieri nel cambio degli iscritti;
- in **11 NIL su 58** (primaria) i bambini di 6-10 anni residenti sono diminuiti dal 2015 al 2024 mentre gli iscritti nelle primarie del NIL sono aumentati (infanzia 3 su 49, sec. I 6 su 45);
- il rapporto tra alunni nelle scuole del NIL e bambini residenti nel NIL va da 0,21 a 2,44 in primaria (NIL con almeno 300 bambini; mediana 1,01; 9 NIL sopra 1,5, 3 sotto 0,5) e da 0,12 a 3,12 in sec. I (`out/sorpresa_nil_rapporto_alunni_residenti.csv`): molte scuole accolgono bambini di altri NIL (coerente con il 54% fuori NIL di ds1739).
- E' anche il risultato della prova all'indietro del punto 4: nel passato usare i bambini del quartiere al posto del dato cittadino non ha migliorato la previsione.
Il resto: la seconda cosa notevole (punto 2 di "In breve") e' che per la secondaria di I grado e per la gran parte della primaria il calo e' gia' deciso dai bambini nati.
Come dirlo (parole neutre): "il numero di bambini in un quartiere non basta a dire quante saranno le iscrizioni nelle sue scuole: contano anche le famiglie che scelgono scuole in altri quartieri".

## 6. Per quartiere e per scuola: come leggere i file

- `out/proiezione_scuole.csv`: una riga per scuola attiva nel 2024/25 (infanzia 293, primaria 216, sec. I 147). Colonne: codice Comune, denominazione, indirizzo, gestione, NIL della sede, classi 2024, iscritti 2015 / 2019 / 2024, proiezione `p2025`...`p2034` (scenario centrale), fasce di errore 2029 e 2034, variazione % 2034 su 2024, rapporto 2024 e 2034 su 2015, `gia_sotto_70_nel_2024`, `sotto_70_nel_2034`, primo anno sotto soglia, numero di varianti (su 6) in cui la scuola e' sotto soglia, `tenuta_del_risultato`, le sei proiezioni 2034 alternative, `piccola_meno_50_alunni_2024` (con poche decine di bambini una variazione di 5 alunni e' gia' 10%), `ultima_localizzazione_incerta` (NIL non da punto-in-poligono).
- `out/scuole_sotto_70.csv`: le sole scuole sotto il 70% del 2015 nel 2034.
- `out/proiezione_nil.csv`: per NIL (della sede) e ordine: iscritti 2015 (tutte le scuole del NIL, anche chiuse dopo), iscritti 2024, proiezione per anno, 2034 con le altre cinque combinazioni, numero di scuole sotto il 70%, quota di alunni 2024 che sta in scuole sotto soglia.
- `out/proiezione_residenti_nil.csv`: bambini residenti nel NIL per fascia (2015, 2024, 2025, e 2025-2034 proiettati, solo coorti, nascite stabili; `res2034_nati_in_calo`).
- `out/proiezione_citta.csv` (con classi equivalenti), `out/sensibilita_scenari.csv`, `out/backtest_*.csv`, `out/sorpresa_*.csv/json`.

## 7. Limiti dei dati

1. **Gli iscritti si fermano al 2024/25** (`scuole/NOTE.md`); il 2025/26 e' gia' in corso e qui e' una proiezione (anche se i residenti 2025 sono noti).
2. **Nessuna matrice di residenza -> scuola.** I dati aperti dicono solo "quanti alunni abitano in un altro NIL" (ds1736-1741, solo come percentuale), non verso quale. Per questo il flusso e' assorbito nel rapporto iscritti/bambini e non e' stato modellato.
3. **Scuole che cambiano codice** (fusioni, trasferimenti, nuove aperture) sembrano chiusure e aperture (`scuole/NOTE.md`, 4.4): una scuola con grandi salti nel passato puo' essere un cambio di codice, non un calo vero. La proiezione non sa che cosa il Comune o lo Stato decideranno su chiusure, accorpamenti o nuove aperture.
4. **Migrazione e nuove case** non sono modellate (rapporto di passaggio = 1). Un'area con grandi nuovi insediamenti (es. Maggiore-Musocco-Certosa: nei residenti 6-10 anni +48% al 2034 gia' solo con le coorti attuali) puo' cambiare molto. La variante `con_migrazione` (che usa i passaggi di eta' osservati negli ultimi 5 anni, che sono sotto 1) da' -23% in primaria e -25% in sec. I al 2034.
5. **L'infanzia e' meno rigida delle altre**: la quota di bambini di 3-5 anni che frequenta (iscritti / residenti) e' scesa da 0,94 (2009) a 0,83 (2020) e risalita a 0,91 (2024) (`scuole/NOTE.md`, 4.1 e 4.2): lo scenario la tiene ferma al 2024.
6. **Anno di riferimento.** La soglia "70% del 2015" prende un anno vicino al massimo di molti ordini (primaria 2015/16: 59.092, picco 59.909 nel 2017): una soglia piu' bassa o un altro anno cambia gli elenchi (`out/sorpresa_soglie.csv`).
7. **Scuole piccole.** 53 infanzie, 4 primarie e 9 secondarie hanno meno di 50 iscritti nel 2024: la variazione percentuale e' instabile (colonna `piccola_meno_50_alunni_2024`). Per 9 infanzie, 6 primarie e 11 secondarie non c'e' il riferimento 2015.
8. **Gestione e cittadinanza.** I dati non permettono di dire perche' una famiglia sceglie una scuola. Nessun risultato qui descrive la composizione degli alunni (cittadinanza: vedi `scuole/NOTE.md`).
9. **Secondaria di II grado esclusa** (dati MIM solo statali e paritarie, circa il 10% degli alunni senza NIL, 1,18 alunni per residente: arrivano da fuori Milano).
10. **Residenti di 0 anni a fine anno** sottostimano un po' la coorte (rispetto ai residenti di 1 anno dell'anno dopo: +1-6% negli ultimi anni): e' coperto nella variante `con_migrazione`.
11. **Residenti 2025**: Comune di Milano ds27, anno 2025 (controlli sul file in `popolazione/pulito/controlli_ds27.json`); la data esatta di riferimento (31/12) e' quella usata in tutto il filone Scuole.

## 8. Cosa potrebbe mostrare una pagina (da decidere con Davide, niente e' stato fatto)

- **Un grafico per ordine**: iscritti 2009-2024 (veri) e 2025-2034 (scenario, con la fascia tra "nascite in calo" e "nascite in risalita" per l'infanzia), con l'avviso "scenario, non previsione" e l'indicazione che per la sec. I i bambini sono gia' nati.
- **Carta dei NIL**: variazione % degli iscritti 2024-2034 (scenario centrale), con accanto i bambini che abitano nel NIL (la differenza e' il messaggio del punto 5).
- **Cerca la tua scuola**: tabella con iscritti 2015, 2024, 2029, 2034 e fascia di errore; mostrare sempre l'avviso sulle scuole piccole e sui cambi di codice; decidere se mostrare i nomi delle scuole private (dati pubblici del Comune).
- **Elenco "sotto il 70% del 2015"** per NIL, distinguendo "gia' sotto" e "robuste in tutte le varianti"; spiegare la soglia e che e' un elenco di scuole *a rischio di superarla*, con il test del punto 4.
- **La prova all'indietro** in una riga: "nel 2019 lo stesso metodo avrebbe stimato gli iscritti 2024 con un errore tra -2% e +1,5% sul totale e circa il 12-15% sulla singola scuola".
- Da non fare: classifica di scuole "che si svuotano", valutazioni, previsioni di chiusura.
