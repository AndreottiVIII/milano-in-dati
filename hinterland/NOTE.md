# Hinterland di Milano: note (programma, dati, pagina)

Data: 2 novembre 2026. Niente git, niente commit. Non toccati: `docs/temi.json`, `docs/menu.js`, `docs/elenco`, `JOURNAL.md`, `STATO_PROGETTO.md` (da aggiornare a mano dal coordinatore).

## 1. Cosa c'è
- `scripts/build.py`: legge `raw/` e i dati puliti degli altri filoni, scrive `docs/hinterland/data/` e `out/controlli.txt`. Si lancia con `python -I -X utf8 hinterland/scripts/build.py <percorso assoluto di milano-in-dati>` (circa 20 secondi).
- `scripts/scarica.sh` (già presente): POSAS, STRASA e P2 da demo.istat.it. `scripts/scarica_extra.py` (nuovo): 9 Camere da Eligendo + due prove (esploradati, demo.istat.it). Pausa 6 secondi, User-Agent `MilanoInDati-ricerca-personale`, nessuna registrazione; registro in `raw/download_log_extra.csv`.
- `docs/hinterland/index.html`: pagina scritta a mano, JS puro, grafici SVG, Leaflet come in `docs/pendolari/`. Carica i dati con `fetch(..., {cache:'no-cache'})`.
- Dati online (`docs/hinterland/data/`, 0,5 MB): `comuni.csv` e `comuni.json` (una riga per comune), `gruppi.json` e `gruppi_serie.csv` (Milano, hinterland, le due parti), `voto.json` (percentuali per famiglia, nessun file grezzo), `metro.json`, `riepilogo.json`, `comuni.geojson`. `raw/`, `pulito/` e `out/` non vanno online.

## 2. Perimetro e conteggi (verificati in `out/controlli.txt`)
187 comuni = 132 della Città metropolitana senza Milano (codice provincia 015) + 55 di Monza e Brianza (108). Milano (015146) sempre a confronto. Geografia unica: i 188 comuni del 1/1/2021 (`pendolari/pulito/comuni_2021.csv`). Si vedono anche separati (pulsanti in cima alla pagina).

## 3. Fonti, una per una
| Dato | File (campo) | Licenza | Scaricato |
|---|---|---|---|
| Residenti per età, 1/1/2019-2026 | `raw/posas/POSAS_<anno>_it_Comuni.zip` (Età, Totale; età 999 = totale) | CC BY 4.0 (ISTAT) | 2/11/2026 |
| Stranieri per età, 1/1/2019-2026 | `raw/strasa/STRASA_<anno>_it_Comuni.zip` (Maschi+Femmine) | CC BY 4.0 | 2/11/2026 |
| Bilancio 2025 | `raw/p2/P2_2025_Comuni.zip` (colonne "- Totale", provvisorio) | CC BY 4.0 | 2/11/2026 |
| Residenti per età 2002-2019 | `redditi/raw/istat_pop/ricostruzione_2002_2019_comuni.zip` (primo blocco di ogni file, maschi e femmine; controllato: totali uguali alla serie dei residenti, over 65 del 2019 uguali a POSAS) | CC BY 4.0 | 1/11/2026 |
| Residenti per età 2002-2019 | `redditi/raw/istat_pop/ricostruzione_2002_2019_comuni.zip` (primo blocco di ogni file, maschi e femmine; controllato: totali uguali alla serie dei residenti, over 65 del 2019 uguali a POSAS) | CC BY 4.0 | 1/11/2026 |
| Ricostruzione 2001-2018 (popolazione, nati, morti, iscritti/cancellati interni ed esteri, acquisizioni di cittadinanza, "Tutte" e "Straniera") | `popolazione/raw/istat_demo/RBD-Dataset-<anno>.csv.zip` | CC BY 4.0 | 1/11/2026 |
| Bilancio mensile 2019-2024 | `censimenti/raw/istat_demo/D7B<anno>.csv.zip` (mesi 1-12 per i flussi, mese 13 = aggiustamento statistico, mese 15 = popolazione censita al 31/12) | CC BY 4.0 | 30/10/2026 |
| Redditi 2000-2024 | `redditi/pulito/mef_comuni_2000_2024.csv` (contribuenti, importi per fascia, reddito complessivo dal 2023) | CC BY 3.0 (MEF) | 1/11/2026 |
| Pendolari 1991-2021 | `pendolari/pulito/flussi_milano.csv`, `mappa_comuni.csv` (entra, totale), distanze | CC BY 4.0 (ISTAT) | 1/11/2026 |
| Cambi di residenza di Milano 2020-2024 | `popolazione/pulito/flussi_luogo_2020_2024.csv` | CC BY (Comune di Milano) | filone Popolazione |
| Voto, Camera 1976, 1979 | `elezioni/raw/eligendo/camera/` | licenza non indicata (Eligendo) | 29/10/2026 |
| Voto, Camera 1987, 1992, 1996, 2001, 2006, 2008, 2013, 2018, 2022 | `raw/eligendo/camera-<data>.zip` (voti di lista per comune) | licenza non indicata | 2/11/2026 |
| Fermate | `metro/pulito/stazioni_metro.csv` (coordinate GTFS, anno di apertura Wikipedia) | GTFS ATM/AMAT; Wikipedia CC BY-SA 4.0 | filone Metro |
| Confini | `docs/pendolari/data/comuni.geojson` (ISTAT 1/1/2021) | CC BY 4.0 | 1/11/2026 |
| Inflazione FOI | `prezzi-case/pulito/foi_annuale.csv` | ISTAT | filone Prezzi-case |

Eligendo: online solo percentuali per comune aggregate per famiglia (gruppi e per unità), con citazione; mai i file grezzi.

## 4. Scelte
- **Unità di confronto.** Baranzate nasce da Bollate nel 2004 (zero abitanti 2001-2003 nelle RBD): per crescita e voto i due sono sommati e segnati "insieme" (186 unità di confronto per 187 comuni). Vermezzo e Zelo Surrigone (fusi nel 2019): le RBD hanno già il comune fuso; nei POSAS/STRASA 2019 e nei redditi i due vecchi comuni sono sommati (redditi agganciati per codice catastale). Monza e Brianza: le RBD hanno già i codici 108 anche per gli anni prima del 2009.
- **Serie della popolazione.** 2001 = censimento 21/10/2001 (RBD 2001, inizio periodo); 2002-2018 = fine periodo dell'anno prima (RBD); 2019-2026 = POSAS. Flussi: RBD 2002-2018, D7B 2019-2024, P2 2025. "Ricalcoli e altro" = differenza che resta tra la popolazione al 1° gennaio e la somma di nati, morti, iscritti e cancellati.
- **Reddito medio** = reddito complessivo / contribuenti. Reddito complessivo = campo MEF dove c'è (2023, 2024), altrimenti somma delle fasce (la fascia "<= 0" non ha importo in molti comuni piccoli: trascurabile). Hinterland = somma dei redditi / somma dei contribuenti. Milano 2024 = 40.316 euro (controllato).
- **Cintura rossa** = comuni dell'hinterland con PCI >= 45% dei voti di lista alla Camera 1976 (40 unità su 186; Milano 31,7%, controllato contro `elezioni/pulito/milano_pre1979.csv`). Soglia scelta guardando la distribuzione (40% = 64 unità, 50% = circa 20).
- **Famiglie politiche** (regole in `build.py`, `RULES`): quelle del sito (Centrosinistra, Sinistra, Centro, Centrodestra, Destra, Lega, M5S, Altri). Il PCI sta in Sinistra, scelta di Davide valida per tutto il sito e scritta in `elezioni/famiglie_partiti.csv`: la frase contraria di `elezioni/NOTE_fase2.md` è superata. I confronti nel tempo sommano Sinistra e Centrosinistra. Differenze piccole dal csv: Liga Veneta, Futuro e Libertà. Le liste che nessuna regola copre vanno in "Altri": da 0,0% (1976, 1979) a 4,1% (1992) e 3,6% (2022: Italexit, Italia sovrana e popolare).
- **Metropolitana.** 125 stazioni collocate per punto-in-poligono nei confini 2021: 103 a Milano, 22 in 12 comuni dell'hinterland (Assago, Bussero, Cassina de' Pecchi, Cernusco sul Naviglio, Cologno Monzese, Gessate, Gorgonzola, Pero, Rho, Segrate, Sesto San Giovanni, Vimodrone). Per ogni comune con fermata, confronto con i 5 comuni senza fermata più vicini per km stradali (mediana). Sensibilità: San Donato (M3), dentro Milano a circa 100 m dal confine; solo fermate aperte prima del 2001. Ricontrollo sui confini ISTAT più precisi `Com2021_g`: stesso comune per tutte le 125 fermate dell'area guardate (Molino Dorino in Pero a 109 m dal confine, San Donato in Milano a 102 m, Cologno Sud in Cologno a 14 m). Segrate conta per la sola Linate Aeroporto (2022).
- **Pendolari.** "Quota" = su 100 residenti del comune che lavorano o studiano (anche nel proprio comune), quanti vanno a Milano (ISTAT 2021: stima).

## 5. Controlli (tutti passati, vedi `out/controlli.txt`)
Conteggi 132 + 55 = 187; pendolari 2021 = 269.466 (resto Città metropolitana) e 72.265 (Monza e Brianza); somma di Milano + 132 comuni = totale provincia 015 e 55 comuni = provincia 108 in RBD 2005, 2012, 2018 e = POSAS Milano 2020, 2021, 2022; Milano 2024 reddito 40.316; saldo cambi di residenza -5.988 ... -10.413; nessun comune mancante per anno in nessuna fonte (Baranzate prima del 2004 a parte, come previsto); stranieri mai più dei residenti (188 x 26 anni); ogni numero del riquadro "cosa sorprende" ricalcolato rileggendo i file scritti; fine 2018 (RBD) = 1/1/2019 (POSAS) per Milano e hinterland (nessun salto), stranieri RBD 2018 = STRASA 2019.

## 6. Cosa sorprende (dai dati, non presi dal testo di partenza)
1. **Più stranieri nell'hinterland che a Milano**: 316.894 contro 267.986 (1/1/2026), dal 2008 in numeri assoluti; ma su 100 residenti sono 11,4 contro 19,7. Solo 5 comuni hanno una quota sopra Milano (Baranzate 37,6%, Pioltello, Cinisello Balsamo, Pero, San Giuliano Milanese).
2. **L'hinterland è ora più vecchio di Milano**: over 65 al 15,9% contro 22,9% nel 2002, sorpasso nel 2021, 24,1% contro 22,7% nel 2026. Il primo anno del sorpasso coincide con il ricalcolo ISTAT; il distacco si allarga anche dopo.
3. **La cintura non è più rossa**: nei 40 comuni sinistra e centrosinistra prendevano il 64% nel 1976 (48% nel resto dell'hinterland), nel 2022 il 27% (25%). Centrodestra, destra e Lega: 46% nella ex cintura.
4. **Solo 2 comuni su 187 hanno un reddito medio sopra Milano** (Basiglio 52.885 euro, Cusago 43.328; Segrate 40.234 è a un soffio). Hinterland 29.278 euro, 73 ogni 100 di Milano (80 nel 2000).
5. **Dal 2015 nell'hinterland muoiono più persone di quante nascono**: dal 2002 al 2025 la crescita (+320.850 dal 1/1/2002) viene da chi arriva (+99.094 dall'Italia, +243.631 dall'estero). Milano: -63.949 nati meno morti e -73.618 con il resto d'Italia; la tengono su gli arrivi dall'estero (+300.487).
6. **Solo Assago riceve da Milano più persone di quante ne mandi** (4.591 contro 2.442, 2021); era così anche in altri tre comuni nel 1991.
7. **Il confronto metro non dà una differenza chiara**: crescita 2001-2026 sopra il confronto in 8 comuni su 12 (mediana +13,8% contro +4,6%), ma sotto nella fascia 15-20 km (+7,4% contro +14,2%); con 12 comuni è un risultato che può capitare per caso (probabilità circa 39%).

## 7. Limiti dei dati
- **Salti della serie**: fine 2018 (RBD) e 1/1/2019 (POSAS) coincidono al numero. Tra il 2020 e il 2022 l'ISTAT ha applicato un "aggiustamento statistico" (D7B, mese 13): Milano -27.193 (2020) e -23.365 (2021), hinterland +11.464 e -6.385. Sono i salti del 1/1/2021 e del 1/1/2022 (Milano -31.660 e -24.652; hinterland +8.066 e -2.237). Spiegati sulla pagina. 2026 stima; bilancio 2025 provvisorio. Le quote per età 2019 e 2026 non sono del tutto confrontabili per questo.
- **Stranieri**: chi prende la cittadinanza esce dal conteggio (RBD: 44.175 acquisizioni a Milano e 70.439 nell'hinterland tra il 2002 e il 2018; poi il dato non c'è). **Nazionalità non inserita**: la pagina iniziale di demo.istat.it offre la popolazione per cittadinanza e comune solo come consultazione dinamica (`app/?i=...`), nessun file scaricabile trovato (una sola richiesta, 2/11/2026, `raw/probe/demo_istat_home.html`).
- **Matrice dei trasferimenti ISTAT** tra comuni (esploradati.istat.it): **non ha risposto** alla richiesta unica con 90 secondi di attesa (2/11/2026, `raw/download_log_extra.csv`: timeout). Non usata. I cambi di residenza vengono solo dai dati di Milano 2020-2024; la Brianza sta in "Altre prov. Lombardia" e non si isola.
- **Pendolari 2021**: stima da modello, solo numero di persone; lo 0,2% circa dei flussi verso Milano non si aggancia a un comune attuale (Baranzate 1991 e 2001 dentro Bollate).
- **Redditi**: contribuenti non residenti; euro correnti; celle MEF oscurate nei comuni piccoli: dal 2023 la somma delle fasce sottostima del 5,2% per l'hinterland (campo "reddito complessivo" usato); fino al 2022 mancano fasce in 2-11 comuni l'anno. Cedolare secca (2011) e forfettari (2019) cambiano la composizione. Nel 2022 i contribuenti sopra 120.000 euro sono il 4,2% e dichiarano il 32,7% del reddito a Milano; 1,3% e 10,6% nell'hinterland.
- **Voto**: sistemi diversi (proporzionale 1976-1992; misto 1996 e 2001, qui solo la parte proporzionale; premio di maggioranza 2006-2013; Rosatellum 2018 e 2022, qui voti di lista); famiglie scelte da noi; il file 2006 scrive "TRUGGIO" per Triuggio; Bollate comprende Baranzate in tutti gli anni; nel 1996 e 2001 Milano è divisa in 11 collegi (sommati; nel 2001 il nome del comune è "Milano N"). Voti di lista, non persone.
- **Metro**: 12 comuni; il confronto non dice che la metro causi crescita o pendolarismo; 9 fermate su 12 sono anteriori al 2001.
- **Correlazione non è causa**: ricordato in pagina a ogni confronto; le ipotesi sono segnate come tali.

## 8. Cose da decidere
- Licenza Eligendo non esplicita: online solo percentuali aggregate; scrivere a elezioni.storico@interno.it se si volessero i dati per comune.
- Voci da aggiungere a mano: `docs/temi.json`, menu, `elenco`, JOURNAL, STATO_PROGETTO.
