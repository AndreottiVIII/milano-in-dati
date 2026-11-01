# Pendolari: chi entra a Milano ogni giorno - FASE 1 (fonti, scarico, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Ogni numero dice file e campo. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di pendolari>` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`.

## 1. In breve

1. **Esistono quattro matrici comune-per-comune dell'ISTAT, tutte scaricabili senza registrazione: censimenti 1991, 2001, 2011 e censimento permanente 2021** (lavoro e studio in due file). Licenza ISTAT: CC BY 4.0 (pagina "Note legali" dell'ISTAT, letta il 1/11/2026). I totali nazionali dei file coincidono con quelli dichiarati dall'ISTAT in tutti e quattro gli anni (controllo in `pulito/controlli_parse.json`).
2. **La matrice 2021 è un'altra cosa**: non è un conteggio, è una *stima da modello* (dati amministrativi INPS/fiscali + indagine, flussi tra province con modello Fay-Herriot, poi distribuiti tra comuni). Ha solo il numero di persone per coppia di comuni: **niente mezzo di trasporto, niente orario, niente durata**. Il confronto 2011-2021 sui totali è utile ma non è "la stessa misura" (vedi sezione 6).
3. **Mezzo, orario e durata esistono solo per 1991, 2001, 2011.** Per il 2021 non c'è nulla di equivalente nei dati aperti.
4. **La "matrice OD 2020" della Regione Lombardia non esiste come dato misurato**: ci sono la OD 2014 e la OD 2016 (spostamenti di un giorno feriale medio, stima da modello di trasporto, CC0) e uno "Scenario 2020" che è una proiezione. Ho usato la OD 2016 solo per un confronto sui mezzi (con riserva).
5. **Ogni giorno entrano a Milano circa 490.000 persone (lavoro + studio, stima 2021; 475.000 nel censimento 2011)**, contro circa 108.000 milanesi che escono (2021). Il numero è quasi fermo dal 1991 (470.000).
6. **Più della metà di chi lavora a Milano abita altrove: 51,5% nel 2021 (49,8% nel 2011, 45,9% nel 1991).**
7. **La geografia non si è mossa in trent'anni**: la mediana dei pendolari in entrata abita a 21 km di strada nel 1991 e a 24 km nel 2011 e nel 2021; uno su nove (11%) viene da oltre 50 km.
8. **La cosa più sorprendente**: Assago è l'unico comune vicino che *riceve più persone da Milano di quante gliene mandi* (4.591 milanesi vanno ad Assago nel 2021, 2.442 assaghesi vengono a Milano), e lo era già nel 1991, 2001 e 2011. Altre sorprese in sezione 5.

## 2. Fonti, una per una (anche in `raw/` e nell'inventario sotto)

| Fonte | Cosa | Anni | Licenza | Scaricato | File |
|---|---|---|---|---|---|
| ISTAT, Matrici del pendolarismo 1991 (https://www.istat.it/dati-della-ricerca/matrici-del-pendolarismo/) | comune di residenza x comune di destinazione, sesso, mezzo (6 gruppi), condizione (studente o altro / occupato), orario, tempo; 27.540.213 persone | 1991 | CC BY 4.0 (ISTAT) | 1/11/2026 | `raw/istat_1991/matrici_pendolarismo_1991.zip` (11 MB) |
| idem 2001 | come sopra, mezzo in 10 classi, sesso, motivo, "si è spostato mercoledì" sì/no; 26.764.361 persone | 2001 | CC BY 4.0 | 1/11/2026 | `raw/istat_2001/...zip` (14,5 MB) |
| idem 2011 | record S (totali) e L (con mezzo in 12 classi, orario, durata); 28.871.447 persone; comuni con almeno 20.000 abitanti: stime da campione | 2011 | CC BY 4.0 | 1/11/2026 | `raw/istat_2011/...zip` (36 MB) |
| ISTAT, Matrice di pendolarismo per lavoro 2021 (https://www.istat.it/notizia/matrice-di-pendolarismo-per-lavoro/, pubblicata 2/10/2025) | origine, destinazione, numero; 19.565.808 occupati; solo Italia | 31/12/2021 | CC BY 4.0 | 1/11/2026 | `raw/istat_2021/matrix_pendoLAVORO_2021.zip` (1,6 MB), via esploradati.istat.it (file collegato alla scheda del dataflow `DF_BULK_PEND_LAV_2021_1`) |
| ISTAT, Matrice di pendolarismo per studio 2021 (nota del 22/9/2026) | 9.279.329 persone *non occupate* che studiano (esclusi gli studenti-lavoratori) | 31/12/2021 | CC BY 4.0 | 1/11/2026 | `raw/istat_2021/matrix_pendoSTUDIO_2021.zip` (0,6 MB) |
| ISTAT, matrici delle distanze (aggiornamento 2021) | km stradali e minuti (con traffico e senza) tra tutti i comuni, calcolati su grafo TomTom 2020; Lombardia = 163 MB | comuni 1/1/2021 | CC BY 4.0 | 1/11/2026 | `raw/istat_distanze/Lombardia.zip` |
| ISTAT, confini dei comuni 1/1/2021 generalizzati; elenco comuni 2021; elenco comuni con codici storici | poligoni, nomi, abitanti 2021, codici 103/107/110 province | 2021 | CC BY 4.0 | 1/11/2026 | `raw/istat_codici/` |
| Regione Lombardia, Matrice OD 2016 passeggeri (dati.lombardia.it `tezw-ewgk`; zip `64n7-bhkf`) | 8.513.232 righe: coppia di zone (1.450 interne; Milano in 16 zone) x ora x motivo x 8 modi; persone da 14 anni, giorno feriale medio | 2016 | CC0 (campo "license" del dataset) | 1/11/2026 | `raw/lombardia_od2016/` (zip 88 MB; il csv estratto, 2,8 GB, si può cancellare e rifare) |
| Regione Lombardia, OD 2014 e "Scenario 2020/2030" | stesse strutture; 2014 obsoleta, 2020 e 2030 sono scenari | - | CC0 | solo elencati | nessun file |
| Comune di Milano (CKAN), pendolarismo 2011 per sezione di censimento e indicatori 1991-2011 | già scaricati dal filone `censimenti/` (ds390-395; ds361-366), NON rifatti qui | 2011 | CC BY | (altro filone) | - |

Elenco delle ricerche sul catalogo di Regione Lombardia (API catalogo Socrata): `raw/web_probe/lombardia_cat_*.json` (parole "pendolarismo", "pendolari", "spostamenti", "origine destinazione", "matrice origine destinazione"). Metadati dei dataset usati: `raw/web_probe/lombardia_view_*.json`. Altro trovato e non usato: `2fda-un7h` "Distribuzione lavoratori rispetto alla residenza" (avvii di rapporti di lavoro, non pendolarismo) e molte matrici parziali del 2024 (traffico su singole direttrici).

Cosa manca (ISTAT): mezzo/orario/durata per il 2021; il motivo "studio" 2021 esclude chi lavora; estero escluso nel 2021. Comune di Milano: nessun dataset CKAN diverso da quelli del filone `censimenti/` (cercato "pendolar*" nel registro del filone).

**Dati che NON ho scaricato**: Copernicus, Waze/telefonia, Trenord (nessuna matrice aperta di saliti/discesi per stazione trovata nelle ricerche), ISTAT matrici per altre regioni (non servono: l'origine fuori Lombardia pesa il 4%).

## 3. Pulizia (`scripts/codici.py`, `parse_censimenti.py`)

- **Geografia di riferimento = comuni al 1/1/2021** (7.904). I codici storici (1991, 2001, 2011) sono portati ai codici 2021 con: (a) le colonne storiche dell'elenco ISTAT attuale (103 province per il 2001, 110 per il 2011), (b) il nome normalizzato dentro la stessa regione se univoco, (c) per le fusioni, il nome vecchio contenuto nel nuovo se univoco. Non agganciati: 231 comuni su 8.094 (2011), 270 su 8.100 (1991). **Quota dei flussi in ingresso a Milano non agganciata: 0,19% (1991), 0,22% (2001), 0,25% (2011).** Restano nei totali di Milano, ma non nelle mappe. Tabella: `pulito/raccordo_codici.csv`.
- **Formati**: 1991 larghezza fissa (destinazione 060000 = stesso comune); 2001 larghezza fissa 43 caratteri; 2011 testo con spazi (record S e L); 2021 tab. Le regole di lettura sono nell'intestazione di `parse_censimenti.py`.
- **2001**: il totale dichiarato dall'ISTAT (26.764.361) si ottiene sommando *tutti* i record, compresi quelli di chi "non si è recato al luogo di lavoro/studio mercoledì" (3,9% dei movimenti): per i totali di flusso li ho inclusi; per mezzo/orario/durata solo chi si è spostato (gli altri non hanno mezzo).
- **2011**: per i totali di flusso uso il conteggio intero dei record S (come consiglia il leggimi); per mezzo/orario/durata la stima decimale dei record L. Somma L = 474.680 contro S = 475.238 per le entrate a Milano (0,1%).
- **Estero**: gli spostamenti verso l'estero (2011: 66.007 persone; 1991/2001 non nelle tabelle) sono esclusi dai flussi tra comuni.
- **Mezzi**: confronto tra anni solo con 6 gruppi (a piedi/bici/altro; treno-tram-metro; autobus anche aziendale/scolastico; auto conducente; auto passeggero; moto). 1991 ha già questi gruppi; per il 2001 e il 2011 li ho ricavati dalle classi dettagliate. Il 3,1% delle persone in entrata nel 1991 non ha il mezzo indicato (escluso dalle quote).
- **Distanze**: `pulito/distanze_milano.csv`: km e minuti stradali verso Milano per i 1.506 comuni lombardi (ISTAT, grafo stradale 2020, orario di riferimento con traffico). Fasce: 0-10, 10-20, 20-30, 30-50, 50-80, oltre 80 km. I pendolari da fuori Lombardia (4,4%) sono nella fascia "fuori Lombardia" (non ho scaricato le matrici delle altre regioni).
- **OD 2016**: solo le righe con Milano da un lato (70.176 righe). Le zone grandi città sono spezzate (es. "MONZA 1..5"): per le fasce di distanza uso il nome senza numero; il 2% degli spostamenti viene da zone composte non agganciate a un solo comune.

## 4. Riepilogo (tutti i numeri sono in `pulito/riepilogo.json` e nei csv)

### 4.1 Quanti
Persone (lavoro + studio), file `pulito/serie_totali.csv`, `flussi_milano.csv`:

| | 1991 | 2001 | 2011 | 2021 |
|---|---|---|---|---|
| Entrano a Milano da altri comuni | 470.331 | 436.097 | 475.238 | 489.785 |
| - per lavoro | 339.135 | 321.369 | 368.473 | 384.744 |
| - per studio | 131.196 | 114.728 | 106.765 | 105.041 |
| Escono da Milano | 95.892 | 87.733 | 89.746 | 108.160 |
| Restano a Milano (stesso comune) | 619.914 | 542.571 | 560.333 | 566.899 |
| Lavoratori di Milano che lavorano fuori (quota) | 18,5% | 18,5% | 18,8% | 21,3% |
| Posti di lavoro a Milano occupati da non residenti (quota) | 45,9% | 46,9% | 49,8% | 51,5% |

(il rapporto entrate/uscite è 4,9 - 5,0 - 5,3 - 4,5; il saldo giornaliero 2021, +381.625 persone, equivale al 28% dei 1.349.930 residenti del censimento 2021). Il "posto di lavoro a Milano" è il posto dichiarato dalla persona (1991-2011) o ricostruito dagli archivi (2021).

### 4.2 Da dove (2021, `origini_gruppi.csv`, `top_comuni.csv`)
- Resto della città metropolitana di Milano 269.466 (55,0%), Monza e Brianza 72.265 (14,8%), Varese 28.927, Pavia 24.607, Bergamo 19.544, Como 15.935, Lodi 12.830, Lecco 10.345, Brescia 6.772, Cremona 6.433; fuori Lombardia 21.657 (4,4%): Piemonte 13.997, Emilia-Romagna 4.283, altre regioni 3.377.
- Primi comuni di residenza (2021): Sesto San Giovanni 14.360, Monza 12.453, Cinisello Balsamo 10.491, Segrate 8.723, Rozzano 8.515, Cologno Monzese 8.277, Corsico 7.245, Paderno Dugnano 7.028, Rho 6.542, Buccinasco 6.395. Nel 2011 la stessa classifica con Rozzano al 4° posto e Segrate al 6°.
- **In 1.457 dei 1.506 comuni lombardi almeno una persona va a Milano ogni giorno (2021).** In 86 comuni più del 20% dei pendolari va a Milano (`mappa_comuni.csv`, colonna `quota_2021`). Esempi: Assago 45,6%, Settimo Milanese 45,3%, Segrate 44,2%.
- Peso dei gruppi di origine sul totale in entrata: la città metropolitana pesa più della metà (58,8% nel 1991 -> 55,0% nel 2021); Monza e Brianza cresce (13,2% -> 14,8%), come Pavia (3,8% -> 5,0%) e Brescia (0,7% -> 1,4%); Cremona scende (2,0% -> 1,3%).

### 4.3 Quanto lontano
Mediana dei pendolari in entrata: 21,4 km (1991), 22,5 (2001), 24,1 (2011), 24,1 (2021); media 27,7 - 28,1 - 29,0 - 29,3 km. **Più di 30 km: 33% (1991), 34% (2001), 37% (2011, 2021). Più di 50 km: 11% in tutti gli anni.** Lavoratori da oltre 50 km: 31.000 (1991), 41.000 (2021). Minuti stradali mediani verso Milano: 47 - 48 - 50 - 50 (ISTAT, tempi con traffico dal comune di origine, non misurati sui pendolari).

### 4.4 Come (1991, 2001, 2011; `modi_per_banda.csv`)
In entrata, lavoro (quota delle persone con mezzo noto): auto da sola/conducente 42% - 51% - 46%; auto passeggero 5%; moto 1% - 4% - 5%; treno/tram/metro 39% - 32% - 37%; autobus 11% - 7% - 5%; a piedi/bici/altro 2% - 1% - 3%. Studio: treno-tram-metro 69% - 58% - 67%, autobus 16% - 14% - 12%, auto (conducente e passeggero) 13% - 25% - 16%.
Per distanza (2011, lavoro; auto = conducente + passeggero + moto): 0-10 km treno/metro 45% e auto 47% (la metropolitana); 10-20 km treno 30% e auto 61%; 20-30 km treno 31% e auto 61%; 30-50 km treno 43% e auto 51%; 50-80 km treno 45% e auto 48%; oltre 80 km treno 48% e auto 43%; da fuori Lombardia treno 51% e auto 42%. **Il treno supera l'auto solo oltre gli 80 km**: nella fascia 10-30 km, dove abita la maggior parte dei pendolari, l'auto vale il doppio del treno. Studio: il treno vale il 59% a 0-10 km e l'80-87% oltre 30 km; l'auto non supera il 29%.
**Avviso sul 1991**: la nota ISTAT del 1991 dice che per le province "di seconda corona" il rientro giornaliero è stato accettato solo per chi usa il treno e impiega più di un'ora: il 63% di treno a oltre 80 km nel 1991 (contro 48% nel 2011) è in buona parte frutto di questa correzione. Non va letto come un calo del treno.

### 4.5 Quanto tempo (1991, 2001, 2011; `tempi_per_banda.csv`)
Durata dichiarata, in entrata: oltre 60 minuti per il 29% nel 1991, 28% nel 2001, 33% nel 2011; fino a 30 minuti il 28% - 23% - 21%. Per fascia di distanza (2011, lavoro + studio): da 10 a 20 km il 13% impiega più di un'ora, da 30 a 50 km il 45%, da 50 a 80 km il 71%, oltre 80 km il 90%. Chi vive a Milano e ci lavora: 3% oltre l'ora, 75% entro 30 minuti.
Orario di partenza dei lavoratori in entrata (`orari_entrata.csv`): nel 2011 il 42% parte prima delle 7:15, il 40% tra le 7:15 e le 8:14, l'11% tra le 8:15 e le 9:14.

### 4.6 Chi esce
Dove vanno i milanesi (lavoro + studio, 2021): Sesto San Giovanni 6.478 (4.527 nel 2011), San Donato Milanese 4.622, Assago 4.591, Segrate 4.217 (4.899 nel 2011), Rozzano 3.142, Monza 2.925, Cinisello 2.789 (`uscite_top.csv`). Gli studenti milanesi che studiano altrove sono 3.686 (2011) e 10.143 (2021): salto troppo grande per non sospettare un effetto del metodo 2021.

### 4.7 Matrice regionale OD 2016 (spostamenti, non persone)
Verso Milano per lavoro 490.128 spostamenti, per studio 143.875; da Milano 104.523 e 6.502. Quote per mezzo (lavoro, in entrata): auto 57%, ferro 30%, bus 5%, moto 5%, piedi/bici/altro 3%; studio: ferro 59%, auto 24%, bus 13%. **Differenza forte col censimento 2011**: a oltre 80 km l'auto vale il 76% (OD 2016) contro il 42% (censimento 2011); i lavoratori in entrata sono 490.000 contro 368.000. Due fonti, due risposte: non le ho riconciliate (la OD è un modello; la sua stessa nota dice che "si presta ad analisi di tipo globale su dimensione provinciale o sovralocale", non a singoli comuni).

## 5. La cosa più sorprendente (e altre)

1. **Assago**: unico comune con almeno 2.000 scambi in cui escono verso il comune più di quanti ne entrino a Milano, in tutti e quattro gli anni (1991: 3.141 da Milano, 2.009 verso Milano; 2001: 2.902 / 2.130; 2011: 3.526 / 2.260; 2021: 4.591 / 2.442). Assago ha circa 9.000 abitanti (2021). *Ipotesi, non misurata*: Milanofiori e i centri direzionali intorno al Forum attirano più addetti milanesi di quanti assaghesi vadano a Milano.
2. **Il flusso non cresce quasi più da trent'anni, ma cambia chi lo fa**: lavoro +13% (339.000 -> 385.000), studio -20% (131.000 -> 105.000).
3. **Un posto di lavoro su due a Milano è di un non residente** (51,5% nel 2021).
4. **Sesto San Giovanni** (79.000 abitanti nel 2021) manda 14.360 persone a Milano e ne riceve 6.478 dalla città (4.527 nel 2011): in dieci anni +43% in uscita da Milano, contro +5% in entrata.
5. **Uno su tre impiega più di un'ora** (33% nel 2011) per arrivare a Milano.

## 6. Limiti dei dati (da tenere sulla pagina)

1. **Il 2021 non è un conteggio.** È una stima da modello (flussi tra province con modello di area; probabilità individuale di essere pendolare; poi distribuzione tra comuni con la tecnica di concentrazione dei flussi di Lenormand). Per le coppie di comuni con pochi pendolari i numeri sono ricostruiti, non osservati. Il confronto con i censimenti precedenti sui totali di Milano è plausibile, sui singoli comuni piccoli no.
2. **Il luogo di lavoro 2021 viene da archivi amministrativi** (INPS, fiscali): è il luogo registrato dal datore, non dove la persona lavora davvero. Smart working e lavoro "in sede" altrove non si vedono. I censimenti 1991-2011 contano il luogo dichiarato.
3. **Soglia diversa**: 2021 conta chi si sposta *almeno tre giorni a settimana*; i censimenti precedenti chi dichiara di spostarsi *ogni giorno* (2001: il mercoledì precedente il censimento). Gli studenti 2021 escludono gli studenti-lavoratori.
4. **Il 2011 per i comuni da 20.000 abitanti in su è una stima da campione**; mezzo/orario/durata sono dichiarati dai rispondenti (campione).
5. **Il 1991 ha correzioni** del rientro giornaliero per le province più lontane (vedi 4.4): i mezzi e le distanze lunghe del 1991 non vanno confrontati con gli anni successivi.
6. **Persone, non spostamenti**: ogni persona conta una volta (andata). Chi cambia mezzo conta per quello principale (come dichiarato).
7. **Riferimento geografico**: i comuni sono quelli al 2021; i comuni fusi dopo il censimento senza un nome simile (0,2% dei flussi a Milano) non sono sulla mappa.
8. **Distanza e tempi di percorrenza** sono dell'ISTAT (strada, 2021): non sono i tempi in treno né le durate dichiarate.
9. **Nessun dato sui non residenti**: studenti fuori sede e domiciliati non sono "pendolari" per il censimento (contano dove sono residenti), e non si vedono i turisti, i city user occasionali, i lavoratori in nero.
10. **Manca il 2020/2024**: né i dati del dopo-Covid né il lavoro agile sono nelle matrici.

## 7. Cosa può mostrare la pagina (fase 2, fatta)

Mappa dei comuni lombardi (quanti vanno a Milano, per anno; quota del comune), elenco dei primi comuni, province, distanza, mezzi per fascia, durata, chi esce, cambiamento 1991-2021, metodo e limiti. Vedi `docs/pendolari/index.html` e `STATO.md`.
