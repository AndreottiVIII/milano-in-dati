# Appalti pubblici: note sulla pagina

Data: 1 novembre 2026. Pagina: `docs/appalti/index.html`. Dati: `docs/appalti/data/`. Programma: `appalti/scripts/pagina.py`.

## Da dove viene

L'analisi è il "Focus Milano" del progetto `appalti-anac` (cartella `C:\Users\davide\Desktop\ClaudeTower\appalti-anac\`, letta soltanto, non toccata): referto `risultati/60_focus_milano.md`, pagina `paper/milano.html` (testo di partenza, adattato), file `risultati/60_*.csv`, decisioni e gruppi di enti in `JOURNAL.md` (sezione "Focus Milano (Sonnet)").
Fonte dei dati: ANAC open data (dati.anticorruzione.it), licenza CC BY-SA 4.0. I file derivati in `docs/appalti/data/` sono rilasciati con la stessa licenza (lo dice la pagina, sezione "File").

## Come si rifà

```
python -I -X utf8 C:\Users\davide\Desktop\ClaudeTower\milano-in-dati\appalti\scripts\pagina.py ^
  C:\Users\davide\Desktop\ClaudeTower\appalti-anac\risultati ^
  C:\Users\davide\Desktop\ClaudeTower\milano-in-dati\docs\appalti\data
```

Il programma legge i `60_*.csv`, scrive i csv e `riepilogo.json`, e **si ferma con un errore** se un numero chiave non coincide con quello scritto a mano nel testo della pagina (funzione `controlli()`: decine di controlli su perimetro, soglia, un solo offerente, lavori, coppie, PNRR e Olimpiadi). Se i csv di `appalti-anac` cambiano, il testo della pagina va riletto a mano.

## Che cosa usa la pagina, da quale file

| Parte della pagina | File prodotto in `data/` | Letto da (`appalti-anac/risultati/`) |
|---|---|---|
| Perimetro: tabella degli otto gruppi, totali, ARIA | `perimetro_gruppi.csv`, `perimetro_totali.csv` | `60_s0_gruppo.csv`, `60_s0_totale.csv`, `60_s0_citta.csv` (505 enti), `60_top30_enti_per_importo.csv` (solo la riga ARIA) |
| 1. Soglia: grafico nove città, Italia 17,1% | `soglia_citta.csv` | `60_s1_citta.csv`, `60_s1_nazionale.csv` |
| 1. Soglia: tabella per periodo di legge | `soglia_periodi.csv` | `60_s1_dimensioni.csv` (dimensione `per`) |
| 1. Soglia: gruppi; enti che spiccano (solo conteggi); rapporto senza i 5 enti | `soglia_gruppi.csv`, `riepilogo.json` | `60_s1_gruppi.csv`, `60_s1_enti_area.csv`, `60_s1_milano_senza_top5.csv` |
| 2. Un solo offerente: grafico per gruppo (2019-2023) | `offerente_gruppi.csv` | `60_s2_2019_2023_gruppi.csv`, `60_s2_2024_2025_gruppi.csv` |
| 2. Milano città, senza ARIA, enti locali, 2019-2023 e 2024-2025; Italia | `offerente_milano.csv`, `riepilogo.json` | `60_s2_*_citta.csv`, `60_s2_*_senza_aria.csv`, `60_s2_*_nazionale.csv`, `60_s2_2019_2023_copertura.csv` |
| 2. Altre città (a scomparsa) | `offerente_citta.csv` | `60_s2_2019_2023_citta.csv` |
| 2. Per tipo di acquisto | `offerente_tipi.csv` | `60_s2_2019_2023_settore.csv` |
| 2. ARIA e Comune di Milano (due soli enti nominati) | `offerente_enti.csv`, `offerente_settori.csv` | `60_s2_2019_2023_enti.csv` (righe ARIA e Comune), `60_s2_2019_2023_cpv.csv` |
| 3. Lavori: grafico per fascia di importo | `lavori_fasce.csv` | `60_s3_fascia.csv` |
| 3. Lavori: quadro e gruppi; lavori di un solo operatore della fibra (solo i due numeri, senza nome) | `lavori_quadro.csv`, `lavori_gruppi.csv`, `riepilogo.json` | `60_s3_quadro.csv`, `60_s3_gruppi.csv`, `60_s3_enti_con_attesi.csv` |
| 4. Vincitori ricorrenti: tabella e grafico (solo conteggi per tipo di procedura) | `vincitori_coppie.csv` | `60_s4_coppie.csv` (conteggi; nessun ente né impresa nei file prodotti) |
| 5. PNRR e Olimpiadi | `pnrr.csv`, `olimpiadi.csv` | `60_s3_pnrr_quota.csv`, `60_s3_speciali.csv`, `60_s3_olimpiadi_enti.csv` (solo totali) |

La pagina legge solo `riepilogo.json`; i csv sono gli stessi numeri in forma piatta, per chi li scarica.

## Numeri che nel testo vengono dal referto e non da un csv

- Totali italiani delle coppie estreme (70 nelle gare, 751 nelle dirette, 193 negli accordi quadro, 5 altro) e le 28.896 coppie italiane sopra soglia: dal testo del referto 60, sezione 4 (che li prende dal referto 10); scritti nel programma (`coppie()`), non verificabili dai `60_*.csv`.
- "Da 70 a 26" estreme italiane contando una volta gare e accordi quadro, "10 adesioni sono fornitori di gas medicali", "78 enti su 2.338" con rapporto almeno 2: dal testo del referto 60 (sezioni 1.3 e 4). Anche i periodi di legge e le soglie in euro (40.000, 75.000, 139.000, 140.000; 40.000 e 150.000 per i lavori) e le date.
- Le percentuali tra parentesi accanto ai lotti (87% di ARIA in farmaci e dispositivi, 42% del Comune in servizi sanitari e sociali) sono calcolate dal programma (7.587 su 8.736; 398 su 937) e controllate.

## Scelte sui nomi

- Si nominano solo ARIA e il Comune di Milano, più i gruppi di enti. Mai persone fisiche.
- Nessuna impresa nominata: l'operatore della fibra ottica del PNRR è "un solo operatore della fibra ottica"; i casi delle coppie ente-impresa sono descritti solo per settore; le società e gli enti che nel referto sono nominati (MM, FerrovieNord, Politecnico, ASST, ecc.) sono descritti per tipo ("società tecniche del Comune e della Regione", "un'università tecnica", "un'azienda ospedaliera").
- Nei csv i campi con nomi di enti sono solo i nomi dei gruppi, delle città e delle due righe ARIA e Comune di Milano.

## Cose lasciate in sospeso

- Il link al paper nazionale non c'è: nel `<footer>` della pagina c'è il commento `<!-- link paper nazionale: lo decide Davide -->` e la frase "L'analisi nazionale da cui viene questo focus sarà pubblicata a parte."
- La voce di menu e la home non sono state toccate (`docs/index.html`, `docs/menu.js`, `docs/MENU_README.md`): le aggiunge chi coordina. La pagina ha già il tag `<script src="../menu.js" defer>`.
- Il controllo del JavaScript non è stato fatto con `node` (non installato) ma aprendo la pagina in un browser: nessun errore in console, 5 grafici e 7 tabelle disegnati, nessuno scorrimento orizzontale a 375 px.

## Sezione "Quanti appalti senza gara" (Comune di Milano), 5 novembre 2026

Sezione aggiunta alla pagina (`id="senzagara"`, prima di "Metodo e limiti dei dati"). Programma: `appalti/scripts/diretti_comune.py`; dati: `docs/appalti/data/diretti_comune.json` (la pagina legge solo questo, con un `fetch` a parte: se manca, il resto della pagina funziona).

Come si rifà (serve duckdb: si usa il Python del progetto appalti-anac, non quello di sistema):
```
C:\Users\davide\Desktop\ClaudeTower\appalti-anac\.venv\Scripts\python.exe -I -X utf8 ^
  C:\Users\davide\Desktop\ClaudeTower\milano-in-dati\appalti\scripts\diretti_comune.py ^
  C:\Users\davide\Desktop\ClaudeTower\appalti-anac\dati\appalti.duckdb ^
  C:\Users\davide\Desktop\ClaudeTower\milano-in-dati\docs\appalti\data\diretti_comune.json
```
Metodo: CIG e smartcig del Comune (codice fiscale 01199250158), senza doppioni (`flag_doppione`), anno = `anno_cig`. Diretti = codici 24, 32, 37, 40, 12, 18, 26; in house (25) e adesioni (27) fuori. Valore = `importo_lotto` senza gli importi anomali (12 righe). Serie principale: importo da 5.000 euro in su (numero: tutte le righe; valore: senza anomali, come nel rapporto). Fornitori: un vincitore per CIG (tolti ausiliari, mandanti, consorziati; codici fiscali non validi esclusi), solo CIG ordinari; quota dei diretti con vincitore noto che va a fornitori con almeno 3 diretti nell'anno, con e senza ordini da accordo quadro.
Il programma si ferma se la serie principale non coincide con il rapporto `_idee/verifica_quattro_pagine.md` e se i numeri scritti a mano nel testo della sezione non tornano; le differenze sul resto sono nel campo `differenze` del JSON.

Differenze rispetto al rapporto: la serie (totali, diretti, valore, quote da 5.000 euro, smartcig, diretti sopra 40.000, ordini da accordo quadro) coincide in tutto. Cambiano di poco i fornitori, perché la regola "un vincitore per CIG" è nostra: vincitori noti 587 e 593 (rapporto 594 e 595); quota con almeno 3 diretti 30,7% e 28,5% (29,3% e 28,1%); senza accordi quadro 18,0% e 9,7% (17,2% e 10,2%); persone fisiche 18 e 50 (20 e 51); vincitori noti prima del 2024: 14, 33, 48, 84, 82 (8, 32, 42, 72, 78). Il testo della pagina usa i numeri ricalcolati, arrotondati.

Limiti: il vincitore c'è solo per i CIG ordinari (mai per gli smartcig), quindi i fornitori si misurano solo nel 2024-2025. Il calo degli smartcig dal 2024 resta senza spiegazione verificata: per questo la serie parte da 5.000 euro (soglia scelta per confrontare gli anni, non una soglia di legge). Un diretto 2024-2025 può essere un ordine da accordo quadro (126 e 182), dato assente prima. Proroghe e rinnovi: nessun campo; segnali in `varianti` (motivo 18 e 19, `cig_proroga`) da 3 a 20 CIG all'anno fino al 2023 e 0 nel 2024-2025: non si pubblica un numero, solo una frase nei limiti.
Norme: verificate su normattiva.it la data di entrata in vigore del DL 76/2020 (17/07/2020), le soglie 139.000/150.000 del DL 77/2021 (in vigore dal 01/06/2021) e l'art. 50 del d.lgs. 36/2023 (140.000/150.000). Non verificato sul testo originale del 17/07/2020 il valore di 75.000 euro (è nel testo convertito dalla legge 120/2020): la pagina dice solo "più alte". Il correttivo 209/2024 non è citato.
