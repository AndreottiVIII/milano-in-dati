# Sharing: note sui dati e sulle scelte (15/11/2026)

Pagina: `docs/sharing/` (bozza in `bozze-grafici/sharing-v2/`). Programma: `sharing/scripts/prepara.py`. Dati grezzi: `sharing/raw/`. Dati della pagina: `docs/sharing/data/`.

## Fonti scaricate (User-Agent «milano-in-dati/1.0», 15/11/2026)
- Comune di Milano ds574, «Servizi di Car Sharing, Bike Sharing, Scooter sharing e monopattini», CSV 2011-2025, CC BY 4.0 (`sharing/raw/ds574.csv`, 296 righe: anno, servizio, tipologia, indicatore, valore, nota).
- Comune di Milano ds179, incidenti per mese e veicoli coinvolti, CSV 2001-2025, CC BY (`sharing/raw/ds179.csv`).

## ds179 non contiene i monopattini
Le colonne di ds179 sono «incidenti con 1 veicolo, 2 veicoli... 7 e più»: conta QUANTI veicoli, non di che TIPO. Non si può ricavare nessuna serie di incidenti con monopattini. Usato solo come controllo del totale annuo (2020-2024: 5.254, 7.286, 7.606, 7.558, 7.602 contro 4.856, 7.465, 7.783, 7.812, 7.743 dei microdati ISTAT già elaborati per la pagina Bici, auto e mezzi: differenza da -3,3% a +8,2%, il 2020 più lontano; il Comune non dichiara se ds179 includa gli incidenti senza feriti).
Gli incidenti con monopattini vengono quindi da `docs/bici-auto-mezzi/data/incidenti.json` (microdati ISTAT / Regione Lombardia, CC BY 4.0), serie annuale 2020-2024, NON mensile (la proposta chiedeva «mese per mese»: non è possibile con questi dati).

## Pulizia di ds574: scelte
1. Chiavi lette in minuscolo: la stessa riga è scritta con maiuscole diverse («Scooter totale»/«scooter totale», «Free floating»/«Free Floating»). Unite; se due righe uguali avessero valori diversi lo script si ferma (non succede).
2. **Auto a stazione (noleggi): escluse.** Esistono solo 2018-2023: 108, 115, 89, 47, 15, 11 noleggi al giorno. Non sono il servizio intero (nei 2011-2017 e nel 2024-2025 non c'è nulla) e pesano meno dell'1% del totale. Per avere lo stesso perimetro in tutti gli anni, «auto» = solo auto libere (free floating, dal 2013). Annotato in pagina («Limiti dei dati» e sotto il grafico 1). Non sono nascoste: sono nel riepilogo.json (`auto_stazione`).
3. Auto libere: nessun valore da escludere (2.314 nel 2013 → picco 16.851 nel 2018 → 6.646 nel 2025). Il «car sharing con poche decine» della proposta era la riga a stazione.
4. Bici: due righe, a stazione (BikeMi, dal 2011) e libere (dal 2017). Tenute separate nel grafico 1 e 2, sommate nei grafici 3 e 4 (mezzi e chilometri sono dati per bici in tutto).
5. Mezzi: bici = a stazione + libere (5.430 + 15.000 nel 2025). Scooter: righe «scooter totale» 2015-16 e 2017-25 unite. Monopattini: «Monopattini totale». Auto: «Autovetture totale» libere.
6. Servizi partiti a metà anno (auto libere 12/8/2013, scooter 15/7/2015, bici libere settembre 2017, monopattini 2/2/2020), scooter fermo 1/7-14/10/2017, scooter 2018 «parziale, solo alcuni operatori»: tenuti con nota, non corretti.
7. **Chilometri:** usati solo per il 2025 (l'unico anno con tutti e quattro i servizi dallo stesso criterio). Scooter 2023 = 14,2 milioni di km contro 3,5 nel 2024 con noleggi dimezzati (4 volte): non credibile, quindi nessuna serie dei chilometri. Auto 2025 = solo libere.
8. Iscritti: serie con anni mancanti e valori incoerenti (es. scooter 5.766 nel 2017, 290.000 nel 2020): non usati.
9. Monopattini nel 2024: 6.714 noleggi (da 9.053) e 4,15 milioni di km, poi 12.673 nel 2025: tenuto, con nota («il Comune non spiega»).
10. Noleggi annui = media giornaliera × 365 (366 nel 2020 e 2024). Per il 2020 è una stima grossolana (servizio da febbraio).

## Verifica dei 6 numeri in alto (ricalcolati a mano dal CSV grezzo)
- 12.673 noleggi/giorno monopattini 2025 (BikeMi 8.321, bici libere 11.068, auto libere 6.646, scooter 3.660; totale 42.368 = 14,3 volte il 2011 con 2.957).
- Auto libere: 1° posto 2018-2023, 4° nel 2025; 16.851 → 6.646 = -60,6% (scritto -61%).
- 2,1 noleggi al giorno per monopattino (12.673/6.000 = 2,11); bici 0,95 (19.389/20.430).
- 10.709 km per auto libera (25.882.582/2.417), 1.619 per monopattino (9.713.668/6.000).
- 573 incidenti con monopattini nel 2024 (178 nel 2020), 7,4% dei 7.743 incidenti con feriti.
- 233 incidenti ogni milione di noleggi nel 2024 (573/(6.714×366)); 113,5 nel 2020. Conto approssimato: gli incidenti sono di tutti i monopattini, i noleggi solo quelli in condivisione.
