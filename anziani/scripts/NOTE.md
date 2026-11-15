# Anziani: note (15/11/2026)

Bozza: `bozze-grafici/anziani-v2/index.html` (generata da `anz_03_pagina.py` con `anz_pagina_modello.html`). Anteprima: `python -I -X utf8 bozze-grafici/anteprima.py anziani`. Dati della pagina in `docs/anziani/data/` (tutti sotto 100 KB). Non pubblicato, nessun commit.

## Passaggi (python -I -X utf8, argomento = cartella del progetto)
1. `anz_01_scarica.py`: RSA (Socrata export completo), metadati e ADI (CC0) in `anziani/raw/`. User-Agent milano-in-dati/1.0, pausa 2 s.
2. `anz_02_elabora.py`: RSA di Milano nei quartieri (punto nel poligono), over 80 per quartiere (docs/eta/data), over 80 per comune (POSAS 2026 già in hinterland/raw/posas), province lombarde, gestori, csv.
3. `anz_03_pagina.py`: compone la bozza.

## Fonti e licenze
- Regione Lombardia, «Elenco Residenze Sanitarie Assistenziali (RSA)», https://hub.dati.lombardia.it/d/jyyh-hybn, aggiornato 14/11/2026, scaricato 15/11/2026. Nessuna licenza dichiarata: art. 52 c. 2 CAD (decisione di Davide).
- ISTAT POSAS 1/1/2026 (CC BY 4.0). Comune di Milano residenti per quartiere 31/12/2025 e NIL (CC BY). Comune di Milano ADI DS618 (CC0, 15/10/2026): solo il conteggio (33 servizi) nei limiti.
- INPS lavoratori domestici: NON usato (vedi sotto).

## INPS: perché saltato
Le tavole per provincia/sesso/colf-badanti esistono solo nella banca dati interattiva (servizi2.inps.it/servizi/osservatoristatistici/12, serie 2016-2025 con provincia, sesso, colf/badante). Nessun file scaricabile trovato. Si potrebbe interrogare l'interfaccia interna del portale, ma il tentativo è stato bloccato dal sistema di permessi e non è stato aggirato. Per farlo serve l'ok esplicito di Davide, oppure i file dal Statistiche in breve (solo regioni).

## Verifiche
Posti Milano 7.784 (59 RSA), accreditati 7.728; hinterland 9.320 in 91 RSA; somma 17.104 = provincia. Over 80 Milano 115.137 (POSAS) / 116.213 (anagrafe, quartieri). 51 quartieri su 87 senza RSA (NIL 8 senza dato). Tutti i punti RSA cadono in un quartiere.

## Capitolo badanti (15/11/2026)
Dati INPS scaricati dal coordinatore (anz_04_inps.py, anz_05_domestici.py, grezzi in anziani/raw/inps/) -> docs/anziani/data/domestici.json. `anz_06_capitolo_badanti.py` (+ `anz_badanti.js`) riparte dalla pagina pubblicata docs/anziani/index.html, aggiunge il capitolo, il numero in alto "1,8 volte" (al posto di "1,7 a Buenos Aires"), limiti, metodo, file e piè di pagina, e scrive domestici.csv. Fonte: INPS, Osservatorio sui lavoratori domestici, dati annuali 2016-2025, https://servizi2.inps.it/servizi/osservatoristatistici/12, consultata il 15/11/2026; nessuna licenza dichiarata: art. 52 CAD.
