# Medici e farmacie: note (fase 1 + pagina)

Data: 2 novembre 2026. Cartella: `medici-farmacie\`. Pagina: `docs\medici-farmacie\index.html` (scritta da `scripts\pagina.py`). Ogni numero dice file e campo; tutti i numeri della pagina sono in `docs\medici-farmacie\data\riepilogo.json` (campo `origine`). "Quartiere" = NIL (88).

## In breve
1. **Il numero di pazienti per medico non è aperto**: non c'è in ds234/ds235 del Comune, né sul portale dati.lombardia.it (cercato con 19 parole chiave, vedi `raw\ricerca_cataloghi.json`), né tra i dataset del Ministero che ho potuto vedere (la pagina con l'elenco di tutti i dataset risponde 403: non aggirata). Quindi **non si può contare chi ha raggiunto il massimale (1.500)**. Si fa un conto "sulla carta" (medici x 1.500 / residenti 14+) e lo si dichiara.
2. **Posti vacanti ("ambiti carenti")**: per Milano gli ambiti ATS sono i 9 Municipi. L'unico elenco leggibile è un PDF di bandi.regione.lombardia.it (`raw\ats_carenti\ambiti_carenti_AP_bandi_regione.pdf`, 306 KB; metadati: creato il 9/9/2022; nessuna data nel testo): 45 posti di assistenza primaria (Municipio 2: 5, 4: 2, 5: 7, 6: 11, 7: 7, 8: 5, 9: 8; Municipi 1 e 3 nessuno). Gli elenchi del 2023 (BURL SAC n. 26 del 28/6/2023, `raw\ats_carenti\BURL_SAC26_2023.pdf`, 29 MB) sono scansioni senza testo: non letti. Nessun elenco 2025/2026 trovato; nessun elenco dei pediatri leggibile. Vecchio di 4 anni: usato solo come contesto.
3. **Medici di famiglia: 999 attivi, 322 sono incaricati provvisori (età mediana 29 anni); 277 hanno come sede via G.B. Grassi 74 (ospedale Sacco), 9 via Stromboli 19, 5 via Gola 22**: sono sedi di servizio, non ambulatori. Regola: i provvisori con sede in un indirizzo che ne ospita 5 o più non entrano nei conti per quartiere (291). Restano 708 medici "localizzati" (677 titolari + 31 provvisori). Senza questa regola il quartiere Roserio (257 residenti) avrebbe 277 medici.
4. **Pediatri: solo 118 attivi per 142.721 bambini 0-13** (1.210 per pediatra): impossibile come conteggio reale (tetto circa 1.000 secondo una fonte sindacale; 800 non confermato). Elenco probabilmente incompleto: usato solo come confronto tra quartieri, nessun conto di "posti".
5. **Farmacie nel tempo**: il file del Ministero ha `data_inizio_validita` e `data_fine_validita` (dal 2005). 428 codici per Milano, 427 aperti; 423 a fine 2005, 427 dal 2015, nessuna chiusura dal 2012. Residenti per farmacia: 3.091 (2005) -> 3.277 (2025), massimo 3.320 nel 2023. 263 codici su 428 hanno cambiato partita IVA almeno una volta.
6. **Distanza**: minuti a piedi da `citta-15-minuti\out\civici_tempi.csv` (`min_farmacie`, `min_medici`; 46.885 civici residenziali pesati con i residenti 2025): mediana farmacia 3,9 minuti (296 m), medico 4,7 (356 m); oltre 10 minuti: 5,9% (farmacia) e 10,1% (medico).
7. **Età**: 677 titolari MMG, 144 con 65-69 anni, 40 con 70 o più; 190 avranno compiuto 70 anni entro il 2031. PLS titolari 115: 29 con 65-69, 1 con 70 o più.

## Fonti scaricate
| Fonte | Cosa | File | Data | Licenza |
|---|---|---|---|---|
| Comune di Milano ds234 `ds234-sociale-medici-medicina-generale` | medici di medicina generale, 1.189 righe, 1.153 medici | `raw\comune_mmg\20261029_mmg_final.csv` (copia dal filone citta-15-minuti, scaricato il 29/10/2026) | 29/10/2026 | **CC BY-NC** |
| Comune di Milano ds235 `ds235-sociale-pediatri-libera-scelta` | pediatri di libera scelta, 129 righe, 127 medici | `raw\comune_pls\20261029_pls_final.csv` (22 KB) | file 29/10/2026, scaricato 2/11/2026 | **CC BY-NC** (`license_id` cc-nc) |
| Ministero della Salute, dataset "Farmacie" | tutte le farmacie d'Italia con date di validità, 59.195 righe; Milano 1.066 righe | `raw\salute_gov\FRM_FARMA_5_20261031.csv` (11 MB) | file 31/10/2026, scaricato 2/11/2026 | IODL v2.0 |
| Comune di Milano ds501 | elenco regionale farmacie con coordinate, 422 | `..\citta-15-minuti\raw\comune_milano\farmacie` (non copiato) | 15/10/2026 | CC0 |
| Comune di Milano ds27 | residenti per NIL, anno, età singola | `..\popolazione\pulito\residenti_nil_anno_eta_genere.csv` (non copiato) | 31/12/2025 | CC BY |
| Comune di Milano ds964, ds634 + minuti a piedi | NIL, civici, minuti | `..\citta-15-minuti\` (non copiato) | 29/10/2026 | CC BY / ODbL (rete OSM) |
| ATS Milano / Regione Lombardia | ambiti carenti | `raw\ats_carenti\` | PDF 2022 (BURL 2023 non letto), scaricato 2/11/2026 | non dichiarata (documenti pubblici) |

Scaricamento: curl con User-Agent onesto (`milano-in-dati-ricerca/1.0`), nessuna registrazione, nessun blocco aggirato. `python requests` ha avuto un reset di connessione dal sito del Ministero (curl no): usato curl. La pagina "elenco di tutti i dataset" del Ministero risponde 403: non insistito.

## Problemi trovati ("limiti dei dati")
- **ds234/ds235 contengono nome, cognome, data di nascita e codice regionale** di ogni medico: non ripubblicati. La pagina scrive solo conteggi, fasce di età per tutta la città e, per quartiere, i "65 e più" solo se il quartiere ha almeno 10 medici. Licenza CC BY-NC: solo aggregati, con fonte, uso non commerciale.
- Sede dei provvisori (vedi sopra). 154 MMG e 9 PLS hanno `attivo`=0: esclusi. 35 MMG e 2 PLS lavorano in più ambulatori: contati una volta (ambulatorio principale, `ambulatorioPrincipale`=1; 2 MMG senza principale: prima riga).
- 6 MMG con coordinate sbagliate e `ID_NIL` mancante (via Stradivari 1, via Beatrice d'Este 38, via Ampere 112, via Cecov 48, via Borsi 8, via Grigna 9): quartiere trovato cercando via e civico tra i civici (`scripts\indirizzi.py`).
- Farmacie: Ministero 427 aperte, ds501 422; codici diversi (nazionali `2596...` contro regionali `MI2001`): nessuna chiave comune. Coordinate del Ministero: 75 delle 427 aperte cadono fuori da ogni NIL (geocodifica sbagliata): la posizione viene da ds501. Per ds501 il NIL dichiarato = NIL del poligono per tutte e 422. Nel file del Ministero le coordinate sono per codice (mai due posizioni per lo stesso codice): gli spostamenti di sede non si vedono. Per questo la serie per quartiere (2005, 2015) usa le farmacie di oggi e cambia solo la popolazione.
- Nessuna serie storica dei medici (solo il file del 29/10/2026). Cercato nel catalogo del Comune ("medici di base", "pediatri", "ambiti carenti", "assistiti", "massimale", "guardia medica"): ci sono solo ds234 e ds235. Wayback non provato.
- Residenti ds27 (anagrafe) = +2,7% rispetto a ISTAT (vedi `..\popolazione\NOTE.md`).
- PDF 2022: ambiti per Municipio; la pagina assegna i quartieri al Municipio prevalente (`..\popolazione\pulito\nil_anagrafica.csv`): approssimato.
- Fonti di terzi per massimale e pensione (non verificate sul testo dell'accordo): tetto 1.500 con deroghe a 1.800 (Quotidiano Sanità e AGI, ACN 2024 art. 38); limite 70 anni con proroga (FIMMG; i 72 anni non confermati); massimale pediatri 1.000 (fonte sindacale, rinnovo 2019-2021).

## Come ripetere
Con A = percorso assoluto di `medici-farmacie`, P = di `milano-in-dati`, D = `...\milano-in-dati\docs`:
- `python -I -X utf8 scripts\scarica.py A P`
- `python -I -X utf8 scripts\analizza.py A P` (scrive `pulito\` e `analisi_log.txt`)
- `python -I -X utf8 scripts\pagina.py A P D` (scrive `docs\medici-farmacie\`)
- `scripts\cerca_cataloghi.py A` rifà la ricerca nei cataloghi.

## Cosa non è stato fatto
- Nessuna serie storica per i medici; nessun elenco 2025/2026 degli ambiti carenti; il PDF 2023 (BURL) è una scansione e non è stato letto (servirebbe OCR).
- Nessun confronto dei pediatri con un secondo elenco.
- ISTAT / Health for All (medici per provincia) non cercati.
- Parafarmacie, dispensari, guardia medica: fuori perimetro.
