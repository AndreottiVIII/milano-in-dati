# I proverbi alla prova: note

Pagina nuova (bozza in bozze-grafici/proverbi-v2/, dati in docs/proverbi/data/). Non pubblicata, non nel menu.

## Fonti e licenze (copiate dalle pagine Temperature e Quanto piove)
- Temperature: Brera 1763-1994, Maugeri e altri (2002), Climatic Change 53, via NOAA GHCN-Daily ITE00100554 e ECA&D ("data from the ECA&D project", uso non commerciale); Linate NOAA GSOD per 15/11/1986-15/9/1987; dal 1995 ARPA Lombardia sensore Brera, CC0 1.0. File: docs/il-tuo-giorno/data/temperature_brera_giornaliere_*.csv.
- Pioggia: Maugeri e altri via ECA&D fino al 2008; ARPA Lombardia CC0 dal 2009. File: docs/pioggia/data/anni/.
- Il sito non è commerciale: chi riusa i dati deve citare le fonti.

## Passi (proverbi/scripts/)
01_calcola.py legge i due insiemi e scrive docs/proverbi/data/proverbi.json (11 KB). Python con -I -X utf8, serve scipy e python-dateutil. Con -q non stampa i controlli.

## Periodi
Temperature 1763-2025 (anni interi) e ultimi 30 anni 1996-2025; pioggia 1858-2025 e 1996-2025; Santa Bibiana 1858-2024 (servono 47 giorni di gennaio). Soglia di pioggia 1 mm. Media del giorno = (minima+massima)/2.

## Risultati (verdetti)
- Merla: Falso. Merla 2,6 C, 42° gruppo di tre giorni su 365; più freddi 10-12 gennaio 1,4 C. Tris più freddo partito il 29/1 in 1 inverno su 252 (4 tra 28 e 30). Ultimi 30: 17-19 gennaio, Falso.
- San Martino: Falso. 11/11 più caldo della settimana prima 80 anni su 261 (31%), media dei giorni 37%, 54° su 57. Ultimi 30: 9 su 30.
- Prima di Natale: Vero (78%); ultimi 30 inverni 66%, meno netto.
- Marzo pazzerello: Falso (5° su 12); ultimi 30 anni Quasi (3° su 12).
- Weekend: Falso (p 0,36); ultimi 30 anni p 0,18.
- Ascensione: Falso (11,2 contro 10,4 giorni, p 0,26). Santa Bibiana: Falso (10,9 contro 10,1, p 0,41; ultimi 30 anni 11,9 contro 9,1 con 9 anni, p 0,17).
- Natale-Pasqua: Quasi (correlazione -0,16, p 0,01; -0,21 con media di tre giorni); ultimi 30 anni -0,02, Falso. Sole non misurato.

## Limiti
Serie fatta di pezzi, cambi di strumento (1835, 1971, 1987), sensore ARPA +0,65 C dal 2008 al 2016 non corretto, Settecento poco sicuro, pioggia in due modi (un pluviometro fino al 2008, mediana ARPA dopo), 65 giorni di pioggia mancanti, molti proverbi provati insieme (qualcuno sembra funzionare per caso), pochi anni negli ultimi 30.

## Differenza dall'esplorazione
Weekend: qui 1858-2025 (23,2-24,0%), l'esplorazione usava il 1950+ (22,0-23,0%): stesso esito.
