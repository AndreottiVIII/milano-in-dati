# Violenza contro le donne - note (fase 1 + pagina)

Fatto il 2 novembre 2026. Pagina: `docs/violenza-donne/index.html` (costruita da `scripts/pagina.py`). Cartelle: `raw/` (file non fidati, mai eseguiti), `pulito/`, `scripts/`. Nessun dato personale: solo conteggi; mai nomi, indirizzi o telefoni di centri e case rifugio. Le denunce (maltrattamenti, stalking) NON sono qui: stanno in `docs/reati-citta/`, la pagina ci rimanda.

## Fonti (tutte aperte; dettaglio con impronte in `pulito/inventario_fonti.csv`)
- **Istat, 1522 anno 2025** (xlsx tavole 1-17, trimestri 2023-2025, giorni dal 2018, regioni; nota metodologica e glossario PDF). Fonte primaria DPO-PCM. Licenza: la pagina non ne scrive una; condizioni istat.it CC BY 4.0.
- **Istat esploradati**: `78_1205_DF_DCCV_1522UTENTI4_3` (utenti 2013-2024 per regione), `78_1121_DF_DCCV_1522_VITTIME_1` (vittime), `78_1260` (centri antiviolenza 2024, solo Italia/ripartizioni/regioni), `22_289_DF_DCIS_POPRES1_1` (donne residenti, dal 2019).
- **Regione Lombardia** (CC0): `dphu-pcij` albo CAV (14/4/2026), `jvq8-53gf` convenzionati (30/9/2026), `8eux-iam2` case rifugio (14/4/2026). Il filone reati-citta non li aveva trovati (aveva cercato altre parole): la ricerca giusta e' "antiviolenza".
- **Istat, report vittime di omicidio 2024** (PDF 25/11/2025): serie nazionale femminicidi, valori trascritti.
- **Comune di Milano (CKAN)**: nulla (ricerche "antiviolenza", "violenza donne", "case rifugio", "violenza di genere").

## Numeri chiave
- Chiamate valide utenti: 17.616 (2017) -> 65.048 (2024); Lombardia 2.542 -> 7.567. Serie con frattura 2023 (nuova piattaforma) e 2025 (gestore + estrazione mista). 2023->2024 (confrontabili): +25,8% Italia, +38,6% Lombardia.
- Regione ignota: 36,0% (2023), 34,5% (2024), 43,9% (2025). Quota Lombardia tra regione nota 17,8% (2024) vs 16,9% donne residenti.
- 25 novembre: 684 chiamate nel 2024 (mediana 173); 13 dei 15 giorni piu' alti dal 2018 sono a novembre.
- CAV Istat 2024: 364 Italia, 53 Lombardia = 1,21 / 1,04 per 100.000 donne. Le 53 coincidono con i "centri" dell'elenco convenzionato (53 centri + 43 sportelli = 96); albo 84 voci (33 enti).
- Case rifugio: 170 voci, 165 nomi; provincia = sede legale dell'ente (indirizzi segreti).
- Femminicidi (Istat): 106 stimati su 116 omicidi di donne nel 2024; 111/101 nel 2019.

## Controlli (`pulito/controlli.csv`, tutti OK)
Tavole 6-7 = esploradati (2023, 2024; Italia e Lombardia); somma giorni tavola 5 = chiamate valide annue 2018-2025; regione ignota 2024 uguale nelle due fonti.

## Trappole
- 2025: "aiuto vittima di violenza" 13.495 -> 25.912 e "info sul servizio" 21.779 -> 8.467 sono cambi di registrazione, non di fenomeno.
- "Vittime" nelle tavole = chi chiede aiuto per se' o segnala casi (nota b della tavola 1): non sono solo le vittime.
- Il flow `78_1260` ha le dimensioni appiattite: i codici delle voci (`Y_PRESENCE` 1 = si) sono letti dal codelist; `AVCBC`, `PAIDP`, `VOLUNT` valgono tutti 364: non usati. L'indicatore delle donne in carico (WPERSPV) e' nel codelist ma non nel file: non trovato.
- Popolazione femminile: solo dal 2019 (non ho cercato la serie precedente).

## Non fatto / non trovato
- Femminicidi per Lombardia/Milano: il report Istat ha un grafico per regione ma non una tabella; gli open data dell'Istat `73_230_DF_DCCV_AUTVITTPS_*` (vittime per sesso, provincia) non sono stati letti perche' ISTAT non rispondeva (connessione rifiutata dopo una richiesta troppo grande; la richiesta e' stata fermata). Il Ministero dell'Interno pubblica report in PDF, non dati aperti. Si puo' riprovare con chiave ristretta (area ITC4/ITC45, tipo di delitto omicidio).
- Donne accolte dai centri della Lombardia: nessun dato aperto trovato.
- Posti letto delle case rifugio: non nel dataset.
