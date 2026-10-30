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
- Tra 1921 e 1931 la superficie passa da 76,3 a 187,2 km2 e la serie annuale salta da 697.368 (1922) a 826.469 (1923): sono le annessioni del 1923. Dalla mia memoria: undici comuni (Affori, Baggio, Chiaravalle Milanese, Crescenzago, Gorla Primo, Greco Milanese, Lambrate, Musocco, Niguarda, Trenno, Vigentino). **Elenco e decreto da verificare con una fonte in fase 2**, non li ho trovati in nessun file scaricato.
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
- **Dati annuali del censimento permanente 2018-2024 per comune**: sono su IstatData (esploradati.istat.it), che si interroga con un'API che non ha risposto (nessuna risposta in tre tentativi, fino a 120 s). Un terzo tentativo con un'identita' di browser finta e' stato bloccato dal sistema e non l'ho fatto. Per Milano abbiamo comunque il 2021 e il 2023 per sezione. **Da decidere con Davide**: scaricare a mano dal browser, oppure cercare un altro percorso.
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
