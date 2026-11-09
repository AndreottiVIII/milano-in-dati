# Il catasto di Milano: note

## Fonte e licenza
- Agenzia delle Entrate, Osservatorio del Mercato Immobiliare, "Statistiche catastali" 2018-2025 (catasto fabbricati al 31 dicembre; edizione 2025 pubblicata il 9/7/2026). Pagina: https://www.agenziaentrate.gov.it/portale/web/guest/schede/fabbricatiterreni/omi/pubblicazioni/statistiche-catastali (archivio: .../archivio-statistiche-catastali).
- Licenza: NON è CC BY. Il PDF 2025 (pagina 2) dice: informazioni di proprietà dell'Agenzia; vietato vendere, affittare, cedere; "possono essere utilizzate, anche ai fini della loro elaborazione, purché, nel caso di pubblicazione, venga citata la fonte". Quindi si pubblicano solo numeri elaborati e si cita la fonte. DA CONFERMARE da Davide.
- robots.txt del sito: con curl rispondeva "Access Denied", non si è potuto leggere; si sono scaricati solo i link pubblici della pagina, una volta sola.
- Residenti: ISTAT POSAS (CC BY 4.0), già nel sito (docs/auto/data/confronto_citta.csv), 10 città, 2025.

## Passi
1. Scaricati in dati_grezzi/: Tabelle 2018-2025 (zip), PDF 2025, errata 2024. Gli anni 2018-2024 sono xlsx (cartelle Capoluogo e Provincia), il 2025 è CSV con "cap/NonCap" per provincia. Non scaricati 2015-2017 (host vecchio).
2. scripts/01_estrai_catasto.py: tabella unica pulito/catasto_categorie.csv (anno, provincia, capoluogo/resto, categoria). Resto = provincia - capoluogo per 2018-2024.
3. scripts/02_prepara_pagina.py: scrive docs/catasto/data/ (catasto.json, serie_categorie.csv, capoluoghi_2025.csv, grandi_citta_2025.csv, tutti sotto 60 KB).
4. scripts/03_prova_anteprima.py: prova a 375 e 1000 px e schermate in bozze-grafici/nuove-png/catasto-1..6.png.

## Controlli
- Totali Italia 2025 (somma province) = tabelle 5 e 6 del PDF per A/1-A/4 (31.922; 97.794.844 euro; 13.510.027; ...).
- Serie di Milano senza salti 2024-2025 (cambio formato).

## Limiti
- Solo comune capoluogo e resto provincia (niente quartieri, niente singoli comuni intorno: niente mappa).
- Rendita = valore fiscale, non prezzo. "Popolari" = categoria A/4, non case pubbliche.
- Variazioni nel tempo possono essere riclassificazioni (A/2 +20%, A/4 -3%, C/2 magazzini +121% senza causa nei dati; C/2 fuori dal grafico).
- Gruppo D: solo 2025 (nelle tabelle 2018-24 non è verificato che "unità" sia lo stesso conteggio). Gruppo F non estratto.
- 10 città per abitante scelte a mano (quelle con residenti nel sito).
