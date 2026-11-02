# Nascite e mamme, quartiere per quartiere: note (fase 1 + pagina)

Data: 2 novembre 2026. Cartella `nascite\`. Pagina: `docs\nascite\index.html` (dati in `docs\nascite\data\`). Programmi in `scripts\` (Python 3.12, `python -I -X utf8`, percorsi assoluti). Nessun account, nessuna registrazione, nessun git. Ogni numero dice file e campo.

## In breve
1. **I nati per quartiere (NIL) esistono e sono aperti (CC BY).** ds141 (2003-2020) e ds1943 (2021-2024): nati vivi da madri **residenti**, per anno, quartiere, genere, cittadinanza della madre e del padre (solo «Italiana»/«Straniera», dal 2021 anche «n.d.»). La somma per anno coincide **esattamente** con la serie ds1495 (nati vivi residenti dal 1880) in tutti i 22 anni (controllo in `01_pulisci.py`). Nomi quartiere: 88 NIL; 2 troncati in ds1943 (Niguarda, Stadera) agganciati per prefisso; "Cascina Merlata" ha nome diverso in ds141 (non è un problema).
2. **L'età della madre NON c'è per quartiere**: le descrizioni di ds140/ds141 la nominano ma i file hanno solo anno, quartiere, genere, cittadinanza madre/padre, numerosità. L'età c'è solo per la città e solo 2021-2024: ds1944 (residenti), ds1945 (nati avvenuti a Milano), classi di 5 anni.
3. **ISTAT**: via API SDMX pubblica (esploradati.istat.it, risposta in 2-60 s, una richiesta ogni 15 s) ho preso `25_326_DF_DCIS_FECONDITA1_5` (tasso di fecondità totale) e `_6` (età media delle madri) per anno 2000-2025, province, per cittadinanza (TOTAL/ITL/FRG). **Milano = codice ITC45** (provincia/Città metropolitana, non il comune). Il TFR per il solo comune non esiste nei file ISTAT. 2025 è «stima». Le tabelle ISTAT dei nati per età della madre (NATI1_7) sono per provincia e arrivano al 2021: non usate (scaricate e cancellate).
4. **TFR del comune: calcolo mio**, non ufficiale: 1,124 (2021), 1,089, 1,023, 0,984 (2024), da ds1944 e ds27. ISTAT provincia: 1,24, 1,22, 1,17, 1,13. Differenza dovuta in parte ai denominatori del registro (che dal 2020 conta +2,7% residenti, +10% stranieri rispetto a ISTAT, vedi `popolazione\NOTE.md`).

## Fonti (tutte scaricate il 2/11/2026; log in `raw\download_log.csv`)
| Fonte | File in `raw\comune\` | Anni | Uso |
|---|---|---|---|
| ds141 nascite per quartiere | ds141-popolazione-nascite-quartiere.csv | 2003-2020 | nati per NIL |
| ds1943 nascite dei residenti per quartiere | ds1943_popolazione-nascite-residenti-quartiere.csv | 2021-2024 | idem |
| ds140 / ds1942 per municipio | - | - | scaricati, non usati |
| ds1944 residenti per età della madre, parto, filiazione | ds1944_popolazione-nascite-residenti-eta.csv | 2021-2024 | età madre città, TFR |
| ds1945 nati avvenuti a Milano per età | ds1945_...csv | 2021-2024 | confronto |
| ds1946 / ds289 nati avvenuti a Milano per cittadinanza e residenza genitori | ds1946_...csv, ds289-...csv | 2003-2024 | quota di nati in città con genitori residenti |
| ds1495 serie storica nati vivi residenti | ds1495_...csv | 1880-2024 | controllo totali |
| ds2918 tassi di natalità, ds72 gemellari | - | - | scaricati, non usati |
| ds27 residenti per NIL × età × genere × cittadinanza | `popolazione\raw\comune_ds27\` | 1999-2025 | donne 15-49, residenti |
| ISTAT FECONDITA1_5 e _6 | `raw\istat\` | 2000-2025 | TFR, età media madri |
| ISTAT bilancio demografico (nati) | `popolazione\pulito\istat_bilancio_*.csv` | 2001-2024 | confronto |
Licenza: Comune `license_id: cc-by`; ISTAT CC BY 4.0 (note legali, già lette dal filone popolazione).

## Numeri principali (tutti ricalcolati da `pagina.py` con `check`)
- Nati da madri residenti: 12.518 (2006, massimo), 12.467 (2008), 11.643 (2014), 9.147 (2024: −26,6% sul 2008).
- Donne 15-49 (media 31/12 anno prima e anno, ds27): 288.058 (2008), 299.966 (2024). Nati per 1.000 donne 15-49: 43,3 (2008), 30,5 (2024); per 1.000 abitanti 9,6 e 6,5.
- Madre straniera: 23,7% (2003), 35,6% (2013), 27,2% (2024). Dal 2014 al 2024: −2.496 nati, di cui −1.657 madri straniere, −849 madri italiane.
- Per cittadinanza della madre (donne 15-49 per cittadinanza al 31/12): straniere 69,0 → 30,2 per 1.000; italiane 37,5 → 30,6 (2003 → 2024). **Attenzione**: ISTAT (TFR, provincia) dà ancora 1,55 (straniere) contro 1,06 (italiane) nel 2024: le due misure non vanno lette come uguali (denominatori, età, arrivi recenti, naturalizzazioni).
- Quartieri (≥3.000 residenti nel 2024, 70): mediana 31,4 nati per 1.000 donne 2022-24 (da 24,3 a 60,3); scesi in 66 su 70 dal 2003-05 al 2022-24, mediana −25%. Più alto Maggiore-Musocco-Certosa 60,3 (residenti 4.900 nel 2011, 9.930 nel 2024: fuori scala, causa non verificata).
- Età madre città 2024 (ds1944): 49,4% ha 35+ anni (47,4% nel 2021), 13,9% 40+. Età media da classi ~34,6 (ISTAT provincia 33,4; Italia 32,6).
- TFR ISTAT 2024: Italia 1,18, provincia di Milano 1,13 (2008: 1,44 e 1,50). Milano sopra l'Italia fino al 2019.
- Nati avvenuti in città vs residenti: 9.165 vs 9.147 (2024); 8.515 dei primi hanno genitori residenti a Milano (92,9%; 86,6% nel 2003). Nel bilancio ISTAT: 9.364 (2024).

## Limiti (anche sulla pagina)
Nati da residenti ≠ nati in città; ISTAT conta in altro modo; registro > ISTAT dal 2020 (denominatori); salti 2002→2003 e 2011→2012; assegnazione ai NIL prima del 2012 non documentata; 199 nati senza quartiere (2004-2012: 58 nel 2011, 99 nel 2012) nei totali ma non nelle mappe; 18 NIL <3.000 residenti in grigio; Parco Sempione senza residenti in ds27; cittadinanza ≠ origine (acquisizioni 7.660-9.021/anno 2022-24); età madre solo città 2021-2024; TFR/età media ISTAT per provincia; madri 50+ (15-23/anno) nei nati ma non nel denominatore.
In ds27 la cittadinanza "n.d."/"Altre nazioni o n.d." è contata tra le straniere.

## Cosa non è stato fatto
- Età della madre per quartiere o prima del 2021: non nei dati aperti (si potrebbe chiedere a Servizi Demografici / milanostatistica.comune.milano.it).
- TFR ufficiale del comune di Milano: non pubblicato da ISTAT; se serve, richiesta al Comune.
- Nessun modello per standardizzare per età le donne dei quartieri.
