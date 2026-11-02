# Gli sfratti - FASE 1 (fonti, scaricamento, pulizia) + pagina

Scaricato il 1 novembre 2026. Programmi in `scripts/` (Python 3.12, `python -I -X utf8 scripts/<nome>.py <percorsi assoluti>`). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle in `pulito/`, pagina in `docs/sfratti/`. Nessun dato personale: solo totali per provincia/comune.

## 1. Fonti e licenze
- **Ministero dell'Interno, Ufficio centrale di statistica, indagine INT 00004 "Procedure di rilascio di immobili ad uso abitativo"**: `ucs.interno.gov.it/it/le-statistiche/le-indagini/territorio/procedure-di-rilascio-di-immobili-ad-uso-abitativo` (22 edizioni, dati 2004-2025). Scaricati: Excel 2013-2019 e 2021-2025 (non 2020), PDF dei rapporti 2004-2015, note metodologiche 2022-2026 (`raw/ministero_interno/`, hash in `raw/download_log.csv`). **Licenza**: le note legali (27/1/2025) non indicano una licenza aperta: riproduzione e distribuzione consentite citando la fonte; uso a fini di lucro solo con permesso scritto. Qui uso senza scopo di lucro con fonte; si pubblicano solo tabelle riassunte, non i file originali.
- **ISTAT esploradati**: famiglie dei censimenti 2001 e 2011 per provincia e comune, con titolo di godimento 2011 (`DICA_FAM_CARATT-data.zip`) e famiglie al 31/12 2018-2024 (`DCSS_FAM_POP`), in `raw/istat_probe/`. Licenza CC BY 4.0 (note legali ISTAT lette il 1/11/2026).
- Affitti (solo confronto): filone `costo-vita/` (OMI CC BY 4.0; indice ISTAT/Comune CC BY).

## 2. Cosa contano i dati
Tre numeri: provvedimenti esecutivi di sfratto **emessi** (per motivo: necessita' del locatore, finita locazione, morosita'/altra causa; con "capoluogo" e "resto provincia"), **richieste di esecuzione** presentate all'ufficiale giudiziario, sfratti **eseguiti "con l'intervento dell'ufficiale giudiziario"** (NON "con la forza pubblica": il dato non distingue la polizia). Richieste ed eseguiti solo per provincia. Dati raccolti mensilmente dagli uffici giudiziari tramite le Prefetture (applicativo ORI).

## 3. Numeri principali (tutti in `docs/sfratti/data/riepilogo.json`)
- Provincia di Milano con Monza e Brianza (perimetro unico): ordini emessi per 1.000 famiglie 3,57 (2014), 1,16 (2019), 1,25 (2025); Italia 3,09, 1,91, 1,39. Calo 2014-2025: -65% Milano, -55% Italia. Milano sotto l'Italia dal 2017.
- Comune di Milano (solo capoluogo, dal 2013): 2.802 ordini nel 2013 (4,3 per 1.000 famiglie), 1.107 nel 2025 (1,5).
- Covid, Italia 2019->2020: ordini -34%, richieste -78%, eseguiti -80%; 2022 richieste x3 sul 2021.
- Motivi: morosita' 89% degli ordini italiani nel 2012, 72% nel 2025; finita locazione +95% 2019-2025 (4.327 -> 8.415). Comune di Milano: morosita' 95% (2013) -> 69% (2025).
- Confronto 2025 (ordini per 1.000 famiglie): Roma 2,38, Napoli 2,05, Torino 1,95, Bologna 1,35, Milano 1,25, Firenze 1,16.
- Affitti Milano (solo confronto): OMI +51% 2013-2024; canoni in corso ISTAT +25% 2013-2025.

## 4. Limiti (verificati nei dati)
1. Richieste ed eseguiti di Milano non affidabili: richieste da 1.122 (2020) a 39.809 (2015); nel 2019 Milano ha il 20% delle richieste italiane e il 4,5% degli ordini; eseguiti/ordini > 100% in alcuni anni. Il Ministero non spiega. Non usati per tendenze.
2. Milano 2009->2010 ordini +151% (Italia +7%); dati "incompleti" segnalati per Milano nel 2004, 2006, 2011, 2012, 2013, 2015. Prima del 2010 quota di morosita' bassa (32-63%).
3. Fino al 2012 la "provincia di Milano" include Monza e Brianza; dal 2013 il Ministero le separa: sommate per avere un perimetro unico (e le famiglie).
4. Il "capoluogo" di Milano e' compilato solo dal 2013 (prima zero); peso del capoluogo sulla provincia varia (68% nel 2013, 48% nel 2019).
5. **File 2020 (`2021_Dati_Sfratti_al_31-12-2020-Provinciali.xlsx`, cartella `2025-09/` del sito) non scaricabile**: il server non risponde (timeout, 4 tentativi distanziati con `scripts/riprova.sh`, piu' prove); niente scorciatoie. Il 2020 delle province e' ricostruito dal file 2021 (valore 2021 / (1 + variazione %)): solo totale, richieste, eseguiti; somma province 32.504 contro 32.536 del totale nazionale. Stesso problema per la serie storica 2002-2020 e la nota 2024. Da riprovare.
6. Revisioni: serie nazionale rivista (2012: 67.790 nel rapporto, 70.315 oggi). Somma province vs totale nazionale: uguale nel 2022-2023-2025, scarti fino al 3,4% (eseguiti) nel 2013-2019.
7. Famiglie: censimenti 2001/2011 e permanente 2018-2024, interpolate in mezzo, 2025 = 2024. Tra 2011 e 2018 cambio di metodo ISTAT (+10% famiglie in provincia di Milano in 7 anni, +18% nel comune): tassi 2012-2017 con denominatore incerto di qualche punto.
8. Il blocco delle esecuzioni (marzo 2020 - 31/12/2021: DL 18/2020, art. 40-quater DL 41/2021 conv. L. 69/2021, Corte cost. 213/2021): date da riassunti giuridici sul web, non dai dati; non letto il testo ufficiale.
9. Famiglie in affitto (censimento 2011) usate solo per il confronto tra citta' del 2025: Roma 15,7 ordini per 1.000 famiglie in affitto, Milano 7,2.

## 5. Controlli automatici
`pulito/controlli_estrazione.txt` e `controlli_serie.txt`: somma dei motivi = totale in tutte le 1.276 righe; province lombarde = Lombardia in tutti gli anni; Italia 2001 1,857 per 1.000 famiglie = rapporto 1/539 del Ministero. `pagina.py` rifà 8 controlli puntuali.

## 6. Tabelle pulite
`serie_unita.csv` (unita' x anno, con fonte di ogni riga), `province_2013_2025.csv`, `grandi_province_2001_2012.csv`, `italia_2001_2025.csv`, `famiglie_territori.csv`, `famiglie_per_anno.csv`.
