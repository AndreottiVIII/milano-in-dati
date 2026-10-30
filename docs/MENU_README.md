# Menu del sito

`docs/menu.js` (JavaScript puro, nessuna dipendenza) mette in cima a ogni pagina una barra con il link a "Milano in dati" (la home) e il pulsante "Sezioni" che apre l'elenco di tutte le sezioni. La sezione corrente è in grassetto e sottolineata. Il menu non resta fisso e non copre il contenuto; Esc lo chiude; non si stampa.

L'elenco delle sezioni è l'array `SEZIONI` dentro `menu.js` (stesso ordine e stesse etichette dell'elenco numerato di `docs/index.html`).

## Come aggiungere una sezione

1. Creare `docs/<nuova-sezione>/index.html`.
2. Nel `<head>` della pagina (prima di `</head>`) mettere `<script src="../menu.js" defer></script>`.
3. Aggiungere una riga a `SEZIONI` in `docs/menu.js` (`{ path: 'nuova-sezione/', label: 'Etichetta' }`) e la voce corrispondente nell'elenco di `docs/index.html`.
4. Se la pagina è generata da un programma, mettere il tag nel programma o nel suo modello (vedi sotto).

I link "← Milano in dati" che stavano in alcune pagine sono stati tolti: li sostituisce il menu.

## Pagine che portano il tag

- `docs/index.html` (tag `menu.js`, senza `../`)
- `docs/<sezione>/index.html` per tutte e 16 le sezioni: temperature, vie, beni-culturali, elezioni, aria, area-c, bici-auto-mezzi, scala, citta-15-minuti, violenza-politica, milano-raccontata, neve-e-nebbia, derby, nomi-fermate, cinema-spariti, acqua-del-sindaco.

## Programmi e modelli che scrivono una pagina (il tag c'è, così una ricostruzione lo mantiene)

- `donne-nelle-vie/scripts/15_costruisci_pagina.py` (scrive `docs/vie/index.html`)
- `acqua-del-sindaco/scripts/pagina_template.html` (usato da `pagina_dati.py`)
- `beni-culturali/scripts/pagina_template.html` (usato da `07_pagina.py`)
- `cinema-spariti/scripts/pagina_template.html` (usato da `pagina_dati.py`)
- `derby/scripts/pagina_template.html` (usato da `pagina_dati.py`)

Le altre pagine (temperature, elezioni, aria, area-c, citta-15-minuti, scala, violenza-politica, milano-raccontata, neve-e-nebbia, nomi-fermate, bici-auto-mezzi, prezzi-case) sono scritte a mano: i programmi di quelle cartelle producono solo `data/`. `bici-auto-mezzi/scripts/f4_inserisci.py` inserisce soltanto una sezione dentro la pagina esistente e non tocca il `<head>`.
