# Censimenti di Milano - fase 1 (scaricamento e controllo)

Scaricato il 30 ottobre 2026. Niente grafici, niente pagine, niente git. Tutti gli script sono in `scripts\`, i dati originali in `raw\`, i file ripuliti in `pulito\`. L'elenco completo delle fonti, con dimensioni e licenze, e' in `pulito\inventario.csv`.

## In breve

- Milano ha i dati dei censimenti **per sezione di censimento** per 1991, 2001, 2011, 2021 e anche per il censimento permanente del 31.12.2023. Prima del 1991 il dettaglio e' solo per comune (1861-1981).
- Il Comune ha anche pubblicato i **record individuali** (una riga per persona, famiglia, abitazione) dei censimenti 1991 e 2001, con il codice di sezione. Il numero di righe coincide con il totale ufficiale ISTAT (1.369.231 e 1.256.211 persone).
- I **codici delle sezioni non sono confrontabili** da un censimento all'altro (vedi sotto). ISTAT non ha una tabella di corrispondenza che io abbia trovato.
- Licenza: ISTAT dichiara CC BY 4.0 su tutto il sito (pagina "Note legali", letta il 30/10/2026). I dati del Comune sono "Creative Commons Attribution" (campo license_id = cc-by in tutti gli 80 pacchetti). Si possono ripubblicare citando la fonte.

## Quali anni, a quale livello

| Anno | Comune | ACE (86) | Municipi/NIL | Sezione | Fonte |
|---|---|---|---|---|---|
| 1861-1981 | si | no | no | no | volume ISTAT 1994 (pdf), ds303 Comune |
| 1991 | si | no | via tabella ds1635 (zone 9/20) | si, 5.583 sezioni con dati | ISTAT CPA 1991, Comune ds1636-1639 |
| 2001 | si | no | via ds1529 (zone 9/20, NIL) | si, 5.983 | ISTAT CPA 2001, Comune ds1518-1529 |
| 2011 | si | si | si | si, 6.017 | ISTAT CPA 2011, Comune ds382-385, ds364 |
| 2021 | si | no | si (COM_ASC1 municipio, COM_ASC2 NIL dentro il file) | si, 6.055 con indicatori (7.095 poligoni) | ISTAT Dati_regionali_2021 |
| 2023 | si | no | si | si, 6.059 | ISTAT Comuni_2023 |

Totali dei residenti, controllati sommando le sezioni (campo P1 di `pulito\sezioni_<anno>.csv`): 1991 = 1.369.231; 2001 = 1.256.211; 2011 = 1.242.123 (uguale alla popolazione legale 2011); 2021 = 1.349.930; 2023 = 1.371.499.

## Variabili disponibili

- **1991 e 2001** (`sezioni_1991.csv`, `sezioni_2001.csv`, 207 e 204 colonne): popolazione per sesso, eta', stato civile, cittadinanza, titolo di studio, condizione professionale, famiglie, abitazioni, edifici. Il significato di ogni colonna e' in `variabili_1991.csv` e `variabili_2001.csv` (foglio "Metadati" originale; righe di intestazione sporche, da ripulire in fase 2).
- **2011** (`sezioni_2011.csv`, circa 140 colonne): come sopra, piu' cittadinanza, istruzione, occupazione, famiglie, abitazioni, edifici. Tracciato in `variabili_2011_sezioni.csv`. Esistono anche ACE (`ace_2011.csv`, 86 righe) e municipi (`aree_subcomunali_2011.csv`, 9 righe).
- **2021 e 2023** (`sezioni_2021.csv`, `sezioni_2023.csv`, circa 120 e 148 colonne): popolazione, eta', cittadinanza, paese di nascita, istruzione, occupazione, famiglie, auto (2023), abitazioni. Tracciati in `variabili_2021.csv` e `variabili_2023.csv`.
- **Attivita' economiche per sezione** (imprese, unita' locali, addetti per gruppo ATECO): `sezioni_1991_attivita.csv`, `sezioni_2001_attivita.csv`, `sezioni_2011_attivita.csv`.
- **Record individuali del Comune** (in `raw\comune_ckan\ds1636...`, `ds1518...`, ecc., dentro zip): persone con sesso, eta' singola, stato civile, cittadinanza (singolo paese), titolo di studio, condizione e posizione professionale, settore, pendolarismo (2001), anno di arrivo in Italia (1991). Tracciati nei file `...descriz-col.csv` e `...decodifiche.csv`. Non li ho estratti: pesano 100-180 MB ciascuno.
- **Pendolarismo 2011** per sezione di origine e di destinazione (ds390-395), indicatori 1991-2001-2011 (ds361-366), stranieri 2011 (ds386-389): scaricati.

## Le sezioni cambiano: i codici non sono confrontabili

- Il codice e' sempre 15146 + 7 cifre (per es. 151460000001), ma il numero progressivo viene riutilizzato con confini diversi. Prova: dei codici presenti sia nel 1991 sia nel 2001 (5.509), solo 14 hanno la stessa popolazione; tra 2011 e 2021, 141 su 5.633. Quindi "stesso codice" non vuol dire "stessa sezione".
- Numero di sezioni con dati: 5.583 (1991), 5.983 (2001), 6.017 (2011), 6.055 (2021). I poligoni sono piu' numerosi (5.831, 6.083, 6.085, 7.095): alcune sezioni hanno piu' pezzi o sono senza residenti.
- La nota ISTAT sulle basi territoriali 2021 riporta che le sezioni in Italia sono molto piu' numerose nel 2021 (402.677 nel 2011, 756.376 nel 2021). (Non ho verificato l'affermazione, letta in un riassunto, che i confini 2011 derivino da quelli 2001.) Non ho trovato una tabella ufficiale di corrispondenza sezione per sezione. Per confrontare nel tempo servira' la sovrapposizione geometrica (le geometrie di Milano sono in `pulito\geometrie\`) oppure l'aggregazione a NIL.
- Il Comune fornisce, per 1991 e 2001, una tabella che collega ogni sezione alle sue zone (ds1635, ds1529: Zona9, Zona20, e NIL per il 2001), cosi' si puo' confrontare a livello di zona.
- Il codice di sezione dei record del Comune coincide con quello ISTAT per il 97% (1991) e il 99% (2001) delle sezioni; le differenze sono piccole (in totale 1.234 persone nel 1991, 2.450 nel 2001).
- Per 2011 e 2021 i NIL esistono nei file ISTAT del 2021 (88 NIL) e nei dati del Comune; per il 2011 c'e' l'ACE e il campo COD_ASC.

## Popolazione del comune 1861-2021 (e confini)

File: `pulito\popolazione_comune_1861_2021.csv`, con due serie:
1. `confini_dell_epoca` (Comune ds303, dati ISTAT): popolazione e superficie, 14 censimenti, dal 1861 al 2011.
2. `confini_al_20_ott_1991` (volume ISTAT 1994, Tavola 3): popolazione ricalcolata ai confini del 1991. Valori ricostruiti da ISTAT con proporzioni, non contati; per il 1971 il volume da' 1.732.000 (cifra tonda) contro 1.728.686 della serie dell'epoca.
Piu' le righe 2001, 2011, 2021, 2023 (somma delle sezioni). La serie annuale calcolata dal Comune (1880-2025, ds1494) e' in `popolazione_milano_annuale_1880_calcolata.csv`.

Cambi di confine che si vedono nei dati:
- Tra 1871 e 1881 la superficie passa da 9,7 a 72,9 km2 e la popolazione da 199.009 a 321.839: e' l'annessione dei Corpi Santi (ricavata dai dati; la data 1873 e' dalla mia memoria, da verificare).
- Tra 1921 e 1931 la superficie passa da 76,3 a 187,2 km2 e la serie annuale salta da 697.368 (1922) a 826.469 (1923): sono le annessioni del 1923. Dalla mia memoria: undici comuni (Affori, Baggio, Chiaravalle Milanese, Crescenzago, Gorla Primo, Greco Milanese, Lambrate, Musocco, Niguarda, Trenno, Vigentino). **Verificato in fase 2** su Normattiva (R.D. 2 settembre 1923 n. 1912, in vigore dal 14/10/1923): 11 comuni, ma 'Gorla-Precotto' e non 'Gorla Primo' (vedi sezione Fase 2).
- Tra 1971 e 1981 la superficie scende da 181,7 a 171,7 km2 e poi risale a 181,6 nel 1991: dato strano nel file ds303, da controllare (puo' essere un errore di misura o un cambiamento di metodo).
- Mancano il 1891 (censimento non fatto) e il 1941 (guerra); il 1936 e' nel volume ISTAT ma non in ds303.

## Trappole dei dati

1. Il volume ISTAT 1861-1991 e' un PDF scansionato con OCR: ho letto a mano solo la riga di Milano e l'ho controllata sull'immagine. Per altri comuni servirebbe lavoro in piu'.
2. I file ISTAT 2011 sono in codifica Windows-1252 (apostrofo = byte 0x92); letti cosi' nei file ripuliti.
3. I file dbf 2001 e 2011 scrivono i numeri in notazione scientifica ("3.00000000000e+000"); ho convertito PRO_COM con float.
4. Nel file ISTAT 2021 "base" (`sezioni_2021_base.csv`) ci sono 7.095 sezioni, di cui 5.937 con residenti; nel file con gli indicatori ce ne sono 6.055. Non ho verificato quali mancano.
5. I nomi delle variabili (P1, P2, ...) hanno lo stesso prefisso in tutti gli anni, ma solo P1 (popolazione totale) ho verificato che e' uguale; per il resto serve una tabella di raccordo nomi 1991-2001-2011-2021 (da fare in fase 2).
6. Nei file 2023 ci sono sezioni "fittizie" (codici 888888x = senza fissa dimora iscritti in anagrafe; 999999x = zone contese): vedi nota ISTAT del 9 giugno 2026. In Milano compaiono con codice 15146888888x.
7. Il censimento 2021 e 2023 non e' "porta a porta" ma permanente (registri + campioni): i numeri per sezione sono stime assegnate con il collegamento anagrafe-luoghi, non conteggi. Il confronto con 1991-2011 va fatto con cautela (nota ISTAT sul passaggio al censimento permanente).
8. Il censimento del 1991, per le attivita' economiche, ha solo i record "significativi" (con almeno un contatore diverso da zero).
9. Le geometrie di Milano 1991 e 2001 le ho estratte con un lettore di shapefile scritto in Python (`scripts\shp_milano.py`), senza programmi GIS; sistema di coordinate EPSG:32632 (UTM 32N). Non le ho confrontate con altre fonti; il numero di poligoni per anno e' sopra.

## Cosa non c'e' o non ho potuto prendere

- **Volumi digitalizzati dei censimenti 1861-2011 (ebiblio.istat.it)**: il sito oggi risponde 403 e rimanda a avvisi.istat.it. Per il solo volume 1861-1991 ho usato la copia salvata da Internet Archive (6 ottobre 2026). Gli altri volumi (per es. popolazione residente e presente 1861-1981, volumi provinciali 1961/1971/1981) non sono stati scaricati. Non ho tabelle per comune di famiglie, abitazioni o professioni prima del 1991 se non gli aggregati di Milano dei dataset ds300-302.
- **Serie 1951-2011 per comune ai confini 2011 (8milaCensus)**: il sito e' fermo; Internet Archive era momentaneamente fuori servizio quando ho provato. Non fondamentale per Milano.
- **Dati annuali del censimento permanente 2018-2024 per comune**: sono su IstatData (esploradati.istat.it), che si interroga con un'API che non ha risposto (nessuna risposta in tre tentativi, fino a 120 s). Un terzo tentativo con un'identita' di browser finta e' stato bloccato dal sistema e non l'ho fatto. Per Milano abbiamo comunque il 2021 e il 2023 per sezione. **Risolto in fase 2** con demo.istat.it (file aperti, nessun login): vedi sezione Fase 2.
- **Tabella di corrispondenza sezioni tra censimenti**: non trovata (cercata sul sito ISTAT e nelle note).
- **Censimenti per ACE/sezione prima del 1991** (1951, 1961, 1971, 1981): nessun dato digitale trovato (la ricerca "censimento 1951/1971" sul portale del Comune da' 0 risultati).
- Il file regionale 2023 (`Dati_regionali_2023.zip`, 261 MB) e' scaricato ma non aperto: Milano e' gia' nel file dei capoluoghi.
- Le sezioni 2021 in `Sezioni_21-kmz.zip`, `Limiti`, `Localita` nazionali non sono scaricate (non servono).

## Cosa c'e' in raw (circa 1,9 GB)

Vedi `pulito\inventario.csv` per una riga per fonte con URL, dimensione e righe di Milano. In sintesi: `istat_sezioni_<anno>` (shapefile regionali Lombardia), `istat_variabili_cpa` (zip nazionali 1991/2001/2011, 182 MB), `istat_variabili_cis` (attivita'), `istat_variabili_2021` e `2023` (xlsx), `istat_aree_subcomunali`, `istat_volumi_storici` (2 pdf), `istat_documentazione`, `istat_pagine` (pagine HTML salvate), `comune_ckan` (80 pacchetti, 353 file; elenco in `pacchetti_censimento.json`), `estratti` (R03 e Milano estratti dagli zip nazionali: dati originali, non modificati).

## Comandi per rifare tutto

```
python -I scripts\dl_istat.py <cartella censimenti>
python -I scripts\ckan_list.py <cartella censimenti>     (poi filtrare: pacchetti_censimento.json)
python -I scripts\dl_ckan.py <cartella censimenti>
python -I scripts\extract.py <cartella censimenti>
python -I scripts\build_sezioni.py <cartella censimenti>
python -I scripts\build_2023.py <cartella censimenti>
python -I scripts\shp_milano.py <cartella censimenti>
python -I scripts\build_popolazione.py <cartella censimenti>
python -I scripts\inventario.py <cartella censimenti>
```
(Il filtro dei pacchetti con "censim" e' stato fatto a mano in una riga e non e' salvato come script; il risultato e' in `raw\comune_ckan\pacchetti_censimento.json`.)


---

# Fase 2 (30 ottobre 2026): armonizzazione, indicatori, storia dal 1861, anni 2018-2025

Niente pagine, niente git. Risultati leggibili: `out\sorpresa.md` (la sorpresa in due righe) e `out\risultati.md` (numeri principali per le quattro storie, con file e campo di ogni numero e le cautele). Script `scripts\h1_...` - `h9_...`, dati in `pulito\`.

## 1. Armonizzazione: sezioni -> 88 NIL e 9 municipi (2021)

- **Metodo.** Le sezioni cambiano da un censimento all'altro, quindi la geografia stabile e' quella dei NIL 2021. I poligoni dei 88 NIL e dei 9 municipi sono ottenuti unendo le sezioni 2021 per COM_ASC2 / COM_ASC1 (`h1_raccordo.py`). Ogni sezione 1991, 2001 e 2011 va al NIL con cui ha piu' area in comune. Per ogni sezione salvo purezza (area nel NIL scelto / area sezione) e copertura (`raccordo_sezioni_<anno>.csv`) e le quote di area in ogni NIL (`raccordo_quote_area_<anno>.csv`). Nessuna sezione e' stata unita in silenzio: `sezioni_armonizzate.csv` ha una riga per sezione e anno con il NIL, il municipio e la **fonte** dell'assegnazione.
- **Dove esiste un'assegnazione ufficiale la uso:** 1991 municipio = Zona9 del Comune (ds1635; il NIL non esiste); 2001 NIL = CodNIL e municipio = Zona9 (ds1529); 2011 municipio = CODASC ISTAT; 2021 e 2023 NIL e municipio dai campi COM_ASC2 / COM_ASC1. Altrimenti sovrapposizione.
- **Copertura** (`copertura_raccordo.csv`): popolazione collocata in un NIL 100% (1991), 99,90% (2001), 99,98% (2011), 99,37% (2021), 99,27% (2023). Il resto sono le sezioni speciali 'senza fissa dimora' (codici 8xxxxxx: 24 sezioni nel 2001 con 1.225 persone, 6 nel 2011 con 266, 1 nel 2021 con 8.545, 1 nel 2023 con 10.038): le tengo fuori da tutti i NIL e le conto nel totale del comune. **Trappola:** nei file ISTAT 2021 e 2023 la sezione fittizia 151468888888 ha COM_ASC2 = Duomo; se non la si toglie, Duomo risulta +37,5% invece di -15%.
- **Qualita' della sovrapposizione.** Il 5,8% della popolazione 1991 sta in sezioni con meno del 90% dell'area dentro un solo NIL (2001: 0,4%; 2011: 0,1%). Convalide: il municipio per sovrapposizione coincide con la Zona9 del Comune per il 99,97% degli abitanti 1991 e il 100% nel 2001; il NIL per sovrapposizione coincide con il CodNIL del Comune per il 99,91% nel 2001. Alternativa 'ripartizione per area' (`sensibilita_ripartizione_area.csv`): differenza mediana sulla popolazione di un NIL 1,4% (1991), 0,2% (2001), 0,01% (2011); i casi grossi sono parchi e NIL con meno di 1.000 abitanti. Per le graduatorie uso solo i 66 'NIL robusti' (campo `robusto` in `variazioni_NIL_1991_2023.csv`).
- **Record individuali 1991/2001** (`h3_micro.py`): letti in streaming dagli zip, aggregati per CodSez in `micro_sezioni_<anno>.csv` e `micro_cittadinanza_<anno>.csv`; i totali coincidono con ISTAT (1.369.231 e 1.256.211). Servono per: eta' media esatta (42,54 nel 1991; 44,98 nel 2001), 80+ (57.471 e 69.357), cittadinanze del comune. Non li ho usati per i NIL (il codice sezione del Comune coincide con quello ISTAT per circa il 97-99% delle sezioni: non mescolo le due fonti).

## 2. Indicatori (`indicatori_NIL.csv`, `indicatori_municipi.csv`, `indicatori_comune.csv`; anni 1991, 2001, 2011, 2021, 2023)

Colonne: popolazione, quote 0-14, 65+, 75+, indice di vecchiaia, eta' media, stranieri (numero e quota), laureati (due denominatori), famiglie e componenti medi, famiglie di un componente, abitazioni totali / occupate da residenti / non occupate da residenti, occupati e tasso di occupazione. Convalida contro gli indicatori pubblicati dal Comune (`convalida_indicatori_Comune.csv`): coincidono entro 0,1 punti (eta' media, famiglie di una persona, stranieri, componenti medi, occupazione 1991 e 2011); occupazione 2001 +0,7.

**Dove le definizioni cambiano** (tabella completa in `out\risultati.md`): l'80+ non e' nelle sezioni di nessun anno (solo 75+); eta' media da classi di 5 anni con 75+ fissato a 82 anni, circa 0,5 anni sopra l'eta' media esatta; laureati su 6+ anni (1991-2011) e su 9+ (2021-2023); occupati dal 2021 solo 15-64 anni; abitazioni dal 2021 conteggiate con i registri (salto da 643.053 a 809.990, non e' edilizia); componenti per famiglia 2021-2023 stimati; 1991 stranieri = ST16 (ST15 e' un altro campo, 39.710, non verificato); 2021 e 2023 sono stime del censimento permanente.
Cittadinanze: comune 1991 e 2001 dai record individuali, 2011 da ds386 (10 cittadinanze), 2023 dalle colonne CIT_* (10 cittadinanze); per NIL solo la quota di stranieri (il dettaglio per cittadinanza non c'e' in tutti gli anni). L'occupazione per NIL e' calcolata ma con definizioni diverse (vedi sopra): non la uso nei risultati.

## 3. Milano dal 1861 (`serie_milano_1861_2023.csv`, `variazioni_confini_milano.csv`, `eta_storica_milano_1881_2011.csv`, `serie_annuale_milano_1880_2025_flag.csv`)

- **Fonti primarie lette su Normattiva il 30/10/2026** (pagine salvate in `raw\storia_confini\`): R.D. 8 giugno 1873 n. 1413 (Corpi Santi uniti a Milano dal 1 settembre 1873); D.L. luogotenenziale 31 gennaio 1918 n. 209 (Turro Milanese); **R.D. 2 settembre 1923 n. 1912**, GU n. 229 del 29/09/1923, in vigore dal 14/10/1923, art. 1: *Affori, Baggio, Chiaravalle Milanese, Crescenzago, Gorla-Precotto, Greco Milanese, Lambrate, Musocco, Niguarda, Trenno, Vigentino*. Il dataset ISTAT 'Variazioni amministrative dal 1861' non e' scaricabile come file (SITUAS e' un'applicazione web con API che non ho usato; il file Excel ISTAT copre solo 1991-2025).
- Ritocchi dopo il 1923 (1924 Lorenteggio e Ronchetto, 1925 Morsenchio, 1932 cessione a San Donato): solo da Wikipedia italiana (estratto in `raw\storia_confini\`), segnati 'da verificare'.
- La serie annuale del Comune ha il salto del 1923 (+129.101, +18,5%): e' l'annessione, marcato nel file. La superficie 1981 di ds303 (171,7 km2) resta sospetta.

## 4. Popolazione annuale 2018-2025 (`annuale_milano_2018_2025.csv`)

Da demo.istat.it, file aperti senza login (note legali ISTAT, CC BY 4.0): POSAS (residenti per eta' e sesso al 1 gennaio, 2019-2026), STRASA (stranieri per eta'), D7B (bilancio demografico mensile 2019-2024, tutti i comuni). Scaricati in `raw\istat_demo\` con `h4_dl_demo.sh` (2 secondi di pausa, User-Agent dichiarato, nessuna identita' finta). Il file del 1 gennaio 2018 non esiste (404). **La popolazione al 1 gennaio 2022 e 2024 coincide esattamente con il censimento permanente 2021 e 2023.** Trappola: tra le righe del bilancio c'e' 'aggiustamento statistico' (-27.193 nel 2020, -23.365 nel 2021), che spiega quasi tutto il calo apparente del 2020-2021. Il file `raw\comune_annuale_nil\ds205_dati_quartieri_2011_2024_.csv` (Comune, quartieri/NIL 2011-2024, registro anagrafico) e' scaricato dal CKAN del Comune: e' del registro, non confrontabile con i censimenti (3,4% in piu' nel 2023, 8,0% nel 2011).

## 5. Comandi per rifare la fase 2

```
python -I scripts\h1_raccordo.py <cartella censimenti>
python -I scripts\h3_micro.py <cartella censimenti>
bash scripts\h4_dl_demo.sh <cartella censimenti>
python -I scripts\h5_indicatori.py <cartella censimenti>
python -I scripts\h6_storia.py <cartella censimenti>
python -I scripts\h7_annuale.py <cartella censimenti>
python -I scripts\h8_risultati.py <cartella censimenti>
python -I scripts\h9_convalida.py <cartella censimenti>
```
(ds205: `https://dati.comune.milano.it/dataset/fcddb7d2-b106-48f5-9a2a-64d3136621dc/resource/084457a7-ec4b-4a6b-b463-d8ab53c64fbb/download/ds205_dati_quartieri_2011_2024_.csv`, scaricato con curl; non e' in uno script.)

## 6. Aperto

Ritocchi di confine dopo il 1923; laureati 1991 a Quarto Oggiaro (1,2%) non controllati con altra fonte; nessun dato per NIL prima del 1991; occupazione per NIL non armonizzata; l'80+ per NIL esiste solo 1991 e 2001 (record individuali), non usato.


---

# Fase 3 (30 ottobre 2026): la pagina

Pagina `docs\censimenti\index.html` + `docs\censimenti\data\` (`dati.json` 41 KB, `nil.geojson` 79 KB; in tutto 120 KB). Stile di `docs\citta-15-minuti\` (bianco e nero + un colore, blu #1a56a8; Leaflet 1.9.4 da cdnjs con tessere OSM in grigio; SVG scritti a mano; `fetch(..., {cache:'no-cache'})`). Menu del sito: tag `menu.js` nella pagina e voce `censimenti/` "Censimenti" in fondo all'array `SEZIONI` di `docs\menu.js` (dopo "Acqua del sindaco"); l'elenco di `docs\index.html` lo aggiorna il coordinatore e deve avere la stessa voce in fondo.

## Come e' fatta

- **Programma:** `scripts\pagina_dati.py` (ripetibile: `python -I scripts\pagina_dati.py`) + modello `scripts\pagina_template.html`. Legge solo `pulito\` (e `raw\comune_annuale_nil\ds205...` per il confronto anagrafe/censimento) e scrive pagina e dati. Tutti i numeri del testo sono calcolati dal programma e messi nei segnaposto `{{...}}` del modello (nessun numero a mano, salvo le cifre dei decreti e le definizioni cambiate, copiate da `out\risultati.md`). Se un segnaposto manca il programma si ferma.
- **NIL sulla mappa:** unione delle sezioni 2021 per COM_ASC2 (come in h1_raccordo.py, sezione fittizia 151468888888 compresa nella geometria), semplificate a 4 m e riproiettate EPSG:32632 -> WGS84.
- **Sezioni della pagina:** sorpresa (barre SVG), mappa con indicatore (residenti, variazione dal 1991, eta' media, over 65, stranieri, laureati, famiglie di una persona, componenti per famiglia) e anno (cursore 1991-2023) con scheda del NIL e tabella; "Piu' giovani o piu' vecchi" (indice di vecchiaia 1991-2025, grafico eta' media 1991 contro 2023, tabelle); "Chi e' arrivato" (quota stranieri nel tempo, tabelle per NIL, cittadinanze per anno); "Milano dal 1861" (serie, annessioni 1873/1918/1923, aggiustamento statistico 2020-2021, tabella flussi 2019-2024); "Fonti e metodo".

## Scelte da ricordare

- **I 22 NIL non robusti** (campo `robusto`) sono in grigio tratteggiato sulla mappa; nella scheda mostrano solo i residenti e il motivo (meno di 2.000 residenti nel 1991 o 2023, oppure differenza di assegnazione >= 5%). Le graduatorie usano solo i 66 robusti. Il motivo e' ricostruito in `pagina_dati.py` ed e' verificato contro `robusto` (asserzione).
- **Soglie dei colori fisse** per tutti gli anni (cosi' il cursore mostra davvero il cambiamento); per la variazione dal 1991 il 1991 vale zero per definizione e la mappa e' neutra.
- **Laureati:** uso la quota sulla base 6+ (1991-2011) e 9+ (2021-2023), come in `risultati.md`, con avviso nella pagina. Componenti per famiglia: stima "approx" in tutti gli anni.
- **Annuale 2018-2025:** nel file `annuale_milano_2018_2025.csv` l'anno e' `anno_fine_periodo` = 31 dicembre (la riga "1 gennaio 2019" e' il 31 dicembre 2018); i grafici usano il 31 dicembre, cosi' 2021 e 2023 coincidono con i censimenti permanenti. Il programma controlla che inizio + saldo naturale + saldo migratorio + aggiustamento = fine anno.
- Il rialzo della quota di stranieri nel 2020 (20,1%) nella serie annuale e' un effetto del periodo precedente all'aggiustamento del 2021: non commentato oltre l'avviso "serie fino al 2020 non confrontabili".
- Cittadinanze: 1991 e 2001 le dieci piu' numerose tra tutte (record individuali); 2011 e 2023 solo le dieci principali (circa 75% e 71%); nomi uniformati (Cina, Jugoslavia, Sri Lanka, Peru').

## Provato

Server "milano-in-dati" (porta 8796): pagina caricata senza errori in console, `dati.json` e `nil.geojson` 200; mappa, selettore indicatore, cursore anno, scheda da clic sulla mappa e dal menu, NIL grigio, bottoni cittadinanze; a 375 px nessuno scorrimento orizzontale della pagina (solo le tabelle larghe scorrono dentro il loro riquadro).

## Aperto

`docs\index.html`: aggiungere la voce "Censimenti" in fondo all'elenco (lo fa il coordinatore); `docs\MENU_README.md` parla di 16 sezioni (ora 17). Il testo non spiega perche' alcuni NIL come Giardini P.ta Venezia hanno meno di 100 abitanti oltre a "pochi residenti".
