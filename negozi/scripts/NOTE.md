# I negozi di Milano: note (10 novembre 2026)

Programma: `python -I -X utf8 negozi/scripts/build.py <percorso di milano-in-dati>`. Legge `negozi/raw/` (copie dei dati scaricati in `_esplorazione/aree/negozi/`) e scrive `docs/negozi/data/`. Bozza: `bozze-grafici/negozi-v2/index.html`.

## Fonti (tutte Comune di Milano, dati.comune.milano.it, CC BY)
- ds512 commercio al dettaglio 2003-2025 (numero e superficie per tipo).
- ds49 esercizi di vicinato in sede fissa (28.131 righe, con quartiere, settore, via).
- ds202 aperture e cessazioni di attività, solo 2018.
- ds2471 mercati comunali coperti (26), ds291 mercati settimanali scoperti (85 attivi).
- Confini dei quartieri: copia di `docs/ospedali/data/nil_quartieri.geojson`, alleggerita (id, nome, abitanti dall'anagrafe al 31/12/2025, CC BY).
- User-Agent usato per ogni scarico: "milano-in-dati/1.0", nessun login.

## Passi
1. Serie 2003-2025: strutture per tipo. La superficie di vendita dei negozi di vicinato 2003-2011 è la stessa cifra copiata (1.261.052): messa vuota.
2. Settori: testo del settore in minuscolo, raggruppato in non alimentare, alimentare, misto, tabacchi, farmacie, carburanti, non indicato.
3. Quartieri: conteggio per ID_NIL (245 negozi senza quartiere), negozi ogni 1.000 abitanti.
4. 2018: avvii e cessazioni per tipo (EV vendita: "Iniziale vendita" 1.521 e "Cessazione vendita" 838). Esclusi affido di reparto/poltrona, cessazioni per affitto o trasformazione dei bar, occupazioni di suolo delle edicole.
5. Mercati: scoperti con status "attivo"; giorno = colonne LUNEDI..DOMENICA.

## Limiti
Vedi la sezione «Limiti dei dati» della pagina: superficie 2003-2011 sbagliata, medie strutture 2022-2023 vuote, aperture solo 2018, fotografia senza data di apertura, settore a testo libero, vicinato fino a 250 mq.

## Licenze da segnalare
Nessun problema sui dati usati (tutti CC BY). Non usati: flussi turistici di Regione Lombardia (licenza non dichiarata).
