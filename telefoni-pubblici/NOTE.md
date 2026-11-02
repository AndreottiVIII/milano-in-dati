# Telefoni pubblici di Milano

Pagina: `docs/telefoni-pubblici/index.html` (dati in `docs/telefoni-pubblici/data/`). Scaricato e costruito il 2 novembre 2026.

## Regola sulla licenza
Le note legali di TIM (https://www.tim.it/note-legali) vietano di ripubblicare l'elenco senza consenso scritto. Quindi:
- il file grezzo TIM sta solo in `raw/` (non tracciato da git: `**/raw/` nel `.gitignore`);
- in `docs/` e in questo repo ci sono solo conteggi aggregati, mai indirizzi né righe dell'elenco (nemmeno come esempio);
- `scripts/build.py` controlla a ogni esecuzione che nessuna via dell'elenco compaia nei file scritti in `docs/` e si ferma se la trova;
- i punti OpenStreetMap si possono pubblicare (ODbL): "© OpenStreetMap contributors" e licenza visibili nella pagina e in `docs/telefoni-pubblici/data/LICENZE.txt`.

## Fonti e date
- TIM, elenco dei telefoni pubblici caricato dalla pagina https://www.tim.it/assistenza/trova-telefono, file `cabine01072026.json`, dati al 1 luglio 2026, scaricato il 2 novembre 2026. Campi usati: DESCRIZIONE_COMUNE, DESCRIZIONE_PROVINCIA, DESC_VIA (solo per contare indirizzi ripetuti), CODE_CAP_GIS (idem), ACCESSO, STATO. MEZZO_DI_PAGAMENTO e' sempre MONETA.
- OpenStreetMap via Overpass (`overpass-api.de`), `amenity=telephone` nell'area admin_level 8 con wikidata Q490 (Comune di Milano), dati del 2 novembre 2026 19:50 UTC.
- ISTAT, popolazione residente al 1 gennaio 2026 (stima), `POSAS_2026_it_Comuni.zip` (https://demo.istat.it/data/posas/POSAS_2026_it_Comuni.zip), gia' scaricato il 1 novembre 2026 per il tema redditi e copiato in `raw/`. Il totale di un comune e' la riga con Eta = 999 (il programma controlla che sia uguale alla somma delle singole eta'). La riga di titolo e quella di note vanno saltate.
- Stampa (rilette il 2 novembre 2026): Il Giorno 25/7/2026 e 30/9/2023; Il Post 3/2/2019 e 26/5/2023. Link nella pagina.

## Programmi
`python -I -X utf8 scripts/scarica.py <raw> [<POSAS_2026_it_Comuni.zip gia' scaricato>]` poi
`python -I -X utf8 scripts/build.py <raw> <docs/telefoni-pubblici/data> <out>` (percorsi assoluti). `out/controlli.txt` ha tutti i controlli (non tracciato).
Le fonti vengono scaricate con un User-Agent onesto (`milano-in-dati/1.0`); se una fonte rifiuta, il programma si ferma.

## Scelte
- "Telefoni" = tutte le righe dell'elenco TIM del comune, anche le "IN RIMOZIONE" (627 a Milano: 624 attivi + 3). Stessa regola per tutte le citta'.
- Confronto: i 12 comuni piu' popolosi secondo ISTAT 2026 (Roma, Milano, Napoli, Torino, Palermo, Genova, Bologna, Firenze, Bari, Catania, Verona, Venezia). Nome del comune TIM abbinato al nome ISTAT in maiuscolo; per ogni citta' il programma controlla che nell'elenco ci sia una sola provincia.
- Indirizzi ripetuti: righe meno indirizzi distinti, con indirizzo = testo della via in maiuscolo senza punteggiatura + CAP. Non si riconoscono scritture diverse dello stesso indirizzo.
- "Dove sono": campo ACCESSO letto come in strada / in un locale o negozio / altro. Il file non spiega le voci: la lettura e' dichiarata come nostra nella pagina.
- Mappa: solo i punti OSM (id, posizione, operatore, check_date, covered). I campi liberi (fixme, note) non sono pubblicati.
- Nessuna spiegazione del perche' le citta' siano diverse: la pagina dice solo che l'elenco non lo spiega.

## Numeri (ricalcolati da `build.py`)
Italia 10.002 righe (9.886 attivo, 116 in rimozione). Milano 627 (624 + 3); accesso: 444 strada, 68 esercizio commerciale, 115 altro. Milano 549 indirizzi distinti, 78 righe che ripetono. 4,60 telefoni ogni 10.000 abitanti (1.362.863 abitanti). Firenze 5,28 e' la prima per abitante. OSM: 273 nodi, 142 con check_date (95 del 2025-2026), 75 con operatore TIM/Telecom Italia.

## Limiti
Vedi la sezione "Limiti dei dati" della pagina: stato "attivo" dichiarato da TIM; sulle chiamate solo medie nazionali AGCOM riportate dal Post (277 nel 2019, 118 nel 2021 per postazione), niente per Milano; 468 (progetto) e 627 (elenco) non spiegabili insieme; indirizzi ripetuti non verificati; una sola data; confronto 2019 da un articolo; OSM incompleto; elenco TIM non ripubblicabile.
Differenze fra le fonti della stampa: nel 2023 il giornale parla di 450 postazioni, nel 2026 di 468 cabine. Il Post 2019 dice "cabine" (poco meno di 18mila) e cita separatamente circa 40mila postazioni di telefonia pubblica in tutto; il Post 2023 parla di circa 18mila postazioni (16.073 in strada, 1.801 in ospedali, carceri e caserme, 470 nei rifugi). Non si sa se l'elenco TIM del 2026 conti le stesse cose.

## Da fare / non fatto
- La sezione non e' ancora in `docs/menu.js`, `docs/temi.json`, `docs/index.html` (non toccati su richiesta): la pagina carica `../menu.js` ma non e' evidenziata nell'elenco.
