# Quanto è alta Milano: note

Pagina nuova (proposta P2 del rapporto del 13/11/2026). Bozza in `bozze-grafici/altezze-v2/index.html`, anteprima con `python -I -X utf8 bozze-grafici/anteprima.py altezze`.

## Dati
- Comune di Milano, Database Topografico 2020 (ds2889) e 2012 (ds2892), shapefile, CC BY 4.0. Scaricati il 15/11/2026 in `altezze/grezzi/` (zip da circa 590 MB l'uno, non nel repo: il .gitignore esclude tutto ciò che non è elencato).
- L'altezza c'è: nello strato delle unità volumetriche, campo `UN_VOL_AV` (metri). 2020: strato `UN_VOL` (237.743 unità, codice edificio `CEDIUV`). 2012: strato `A020101` (213.076 unità, codice edificio `ID_EDIF`). Coordinate RDN2008 UTM 32N.
- Estratti in `altezze/x20/` e `altezze/x12/` (non nel repo).
- Nomi delle torri: Wikidata (CC0), file `scripts/torri_wikidata.csv`. Nome assegnato solo se il punto Wikidata sta a meno di 80 m.

## Programmi (in ordine)
1. `scripts/01_estrai.py`: legge le due tabelle, calcola area in pianta e centro di ogni unità, salva `x_uv.pkl`.
2. `scripts/02_riassumi.py`: prova per edificio (codice edificio). NON usata dalla pagina: i codici edificio dei due anni non sono confrontabili (65.675 edifici nel 2020, 90.241 nel 2012).
3. `scripts/03_riassunti.py`: crea i riassunti in `docs/altezze/data/` (circa 120 KB in tutto).
4. `scripts/04_pagina.py`: assembla la bozza da `scripts/corpo.html` e dallo stile della pagina dei negozi.

## Scelte
- Si lavora sulle unità volumetriche, non sugli edifici. Altezza media di un quartiere = somma(pianta x altezza) / somma(pianta).
- Gruppo di torri = unità alte almeno 60 m unite se a meno di 40 m.
- Numeri in alto ricalcolati con un secondo programma indipendente (area con shapely, gruppi con componenti connesse): uguali.

## Limiti verificati
- Il confronto 2012-2020 non è omogeneo: lo stadio di San Siro (unità da 19.758 m², 54 m) c'è solo nel 2012; spiega quasi tutto il calo di Stadio-Ippodromi (-3,8 m).
- Torre UniCredit: 199,4 m nel 2012 (un elemento di 6 m²), 139,4 m nel 2020. Torre Diamante 119,3 m nei dati. Torre Libeskind a 0 m nel 2020 (cantiere).
- Torre Velasca 99,7 m (2012) e 100,1 m (2020): la soglia dei 100 m è fragile.
- Circa 0,5% delle unità cade fuori dai confini dei quartieri.
- 8 -> 14 gruppi sopra i 100 m: i nuovi sono CityLife (Isozaki, Hadid), Solaria e un edificio a Porta Romana senza nome verificato.
