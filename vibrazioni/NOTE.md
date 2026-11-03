# Vibrazioni: prova sul sismografo di Milano

Prova chiesta da Davide il 3/11/2026 ("signit su Milano": capire la città ascoltando segnali). Nessuna pagina, nessun commit.

Fonte: INGV, stazione IV.MILN (45,4803 N, 9,2321 E), canale verticale HHZ, 100 campioni al secondo, attiva dal 2012. Scaricata senza registrazione, circa 21 MB al giorno. Licenza CC BY 4.0.

Metodo: due fasce, "città" 2-20 Hz e controllo 0,1-1 Hz (mare e meteo). Vibrazione media in finestre da 10 minuti, in nanometri al secondo, poi mediana per ora. Scala dello strumento dai metadati INGV. Programmi in `scripts/`, risultati in `out/`.

## Risultati

Mediana, ore 8-19 dei giorni feriali e ore 1-5 di notte:

| Settimana | Giorno | Notte | Domenica | Controllo |
|---|---|---|---|---|
| 25-31/3/2019 | 604 | 223 | 431 | 98 |
| 17-23/2/2020, prima del lockdown | 588 | 222 | 443 | 276 |
| 23-29/3/2020, lockdown | 442 | 172 | 344 | 121 |

- Lockdown: giorno -27% sul 2019 e -25% su febbraio 2020; notte -23% su entrambe; domenica -20% e -22%.
- La fascia di controllo non segue il calo: +24% sul 2019, -56% su febbraio 2020.
- Ritmo del giorno feriale 2019: minimo circa 175 alle 2-3, 269 alle 4, 488 alle 5, 607 alle 6.
- Non spiegato: la notte cala quanto il giorno.

## Seconda prova: Ferragosto e San Siro

Licenza verificata su DataCite (DOI 10.13127/SD/X0FXNH7QFY, Rete Sismica Nazionale): CC BY 4.0.

Ferragosto 2019, fascia città, ore 8-19: 12/8 514, 13/8 501, 14/8 506, **15/8 402**, 16/8 447, sabato 17/8 432, domenica 18/8 418, lunedì 19/8 512. Giorni feriali della settimana 490: -19% su marzo 2019, ma più del lockdown (442). Notte 204 (-9%), domenica 418 (-3%). Un solo anno, e il confronto è con un'altra stagione.

San Siro: partite da Wikipedia, tutte alle 21: Milan-Inter 10/5/2023, Inter-Milan 16/5/2023, Inter-Barcellona 6/5/2025. Stazione a circa 8 km dallo stadio (distanza calcolata con coordinate dello stadio a memoria, da rifare se si pubblica). Fasce 1,5-4 Hz e 2-20 Hz, minuto per minuto.

- Dalle 21 alle 23, rispetto a serate senza partita: -3% e 0%; -2% e +5%; 0% e +1%. Nessuna differenza visibile.
- Dalle 23 alle 24, fascia 2-20 Hz: +5%, +14%, -11%: niente di coerente.
- Gol: la finestra di ±3 minuti attorno ai gol sta tra il 46° e l'88° percentile delle finestre della serata (Lautaro 2023 63°). Il minuto più forte è fuori dalle finestre dei gol, e le serate senza partita hanno picchi pari o maggiori.
- Il 6/5/2025 alle 20:49 c'è il minuto più forte (1.955), prima del calcio d'inizio: causa ignota, non va attribuito alla partita.
- Conclusione: con questa stazione San Siro non si sente. Non vuol dire che lo stadio non vibri: è lontana, e il minuto è grossolano per un'esultanza di pochi secondi; le ore dei gol nel secondo tempo sono stimate.
- Errore evitato: il 3/5/2023, scelto a memoria come serata senza partita, Milan-Cremonese si giocava a San Siro. Scartato. Per gli altri confronti ho controllato solo le partite di Inter e Milan su Wikipedia, non concerti o altri eventi.

## Limiti dei dati

- **Salto dello strumento o del luogo.** Il livello diurno passa da 644 (17/3/2021) a 1.953 (15/12/2021) e poi resta tra 1.860 e 2.200 fino al 2026. Quasi il triplo, e non dipende dalla stagione. I metadati segnano un cambio il 15/11/2021 sui canali di accelerazione HN, non su HHZ: la coincidenza è un'ipotesi, la causa non è verificata. Prima e dopo non si confrontano sulla stessa scala.
- Giorni singoli molto variabili: 782 il 16/12/2020 e 644 il 17/3/2021, contro circa 600 delle settimane normali. Servono settimane intere.
- Capodanno 2023-24: a mezzanotte non si vede un picco chiaro, il rumore tra finestre (712-1.387 la notte prima) è più grande. Dopo l'una il livello è più alto della notte precedente (+18% alle 1, +41% alle 2, +27% alle 3), ma è una sola notte, confrontata con un sabato sera.
- Una sola stazione: non sappiamo quanto copra della città, né quale parte delle vibrazioni venga da traffico, metrò o altro. Correlazione non è causa.
- 42 ore su 771 incomplete. Il 11/12/2019 senza dati di notte.
- `raw/` pesa circa 1,4 GB e resta solo sul PC.

## La pagina "Il respiro di Milano" (3/11/2026)

- `scripts/build.py <radice>` (avvio: `python -I -X utf8 <percorso assoluto>/build.py <radice>`) legge `out/prova_oraria.csv`, `minuti_ferragosto.csv`, `minuti_partite.csv`, `livello_campione.csv`, ricalcola i numeri come gli script di analisi e li confronta con quelli di questa nota (34 controlli). Se uno non torna, si ferma senza scrivere. Altrimenti scrive `docs/vibrazioni/data/pagina.json` e `docs/vibrazioni/data/vibrazioni_orarie.csv` (987 righe: 771 ore delle settimane di confronto e di Capodanno, più le ore di agosto 2019 ricalcolate dai minuti; nessun file grezzo del sismografo).
- `docs/vibrazioni/index.html` legge solo `pagina.json`: tutti i numeri del testo vengono da lì (le definizioni, come "un nanometro è un milionesimo di millimetro", sono scritte nel testo). Grafici in SVG a mano, nessuna libreria. Tre grafici: curva sulle 24 ore, barre di Ferragosto, giorni campione del salto di livello. Controllato a 375 px (nessuno scorrimento orizzontale) e a 1100 px.
- Distanza stazione-stadio: 8,44 km in linea d'aria (formula di haversine), con le coordinate della stazione (45,4803 N; 9,2321 E) e quelle dello stadio dalla voce it.wikipedia "Stadio Giuseppe Meazza" (45,478056 N; 9,123889 E, API di Wikipedia del 3/11/2026). Controllo con OpenStreetMap (way 218520505, Nominatim, 3/11/2026: 45,4782003 N; 9,1239640 E): 8,43 km. Sostituisce il "circa 8 km a memoria" di sopra.
- Nella pagina i gol sono 7, con posto 46-88 su 100; gli orari del secondo tempo e dei supplementari (Lautaro 74', Acerbi 90'+3, Frattesi 99') sono stimati e segnati con "≈".
- I 42 ore incomplete e il Capodanno (+18%, +41%, +27% dopo l'una) tornano dai file orari. Il "712-1.387" di rumore tra finestre del Capodanno non si ricalcola dai file in `out/` (viene dal controllo a passi di 10 minuti): nella pagina non c'è, c'è solo il confronto orario a mezzanotte (1.070 contro 1.065).
- Non verificato: le due pagine Wikipedia citate come fonte di orari e gol (UEFA Champions League 2022-2023 e 2024-2025) esistono, ma gli orari e i marcatori sono quelli già in `analizza_ferragosto_sansiro.py`, non riletti uno per uno.
