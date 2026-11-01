# Chi governa Milano - FASE 1 (raccolta, pulizia, riepiloghi) e dati della pagina

Scaricato il 1 novembre 2026. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di amministratori> [<percorso assoluto di docs>]` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`. Pagina: `docs/amministratori/index.html`.

## 1. In breve

1. **La fonte è l'Anagrafe degli amministratori locali e regionali del Ministero dell'Interno (DAIT)**: fotografie "in carica al 31 dicembre" per ogni anno **2007-2025** (comuni, province, regioni) + elenco "in carica" aggiornato al **24/8/2026**. **Prima del 2007 non esistono file aperti delle persone** (nell'archivio open-data del DAIT filtrato per l'argomento "Anagrafe degli Amministratori" ci sono solo questi 20 elementi): il "1985" non è disponibile. I sindaci dal 1946 si hanno solo da Wikipedia/Wikidata.
2. Licenza: la pagina del DAIT non la scrive. I cataloghi dati.gov.it e dati.comune.milano.it, che ripubblicano gli stessi file (2014-2022 sul portale del Comune: ds2444-ds2452), indicano **CC BY 4.0** (`raw/catalogo/datigovit_search.json`). Va citata la fonte.
3. **Numeri chiave** (tutti da `pulito/serie_temporali.csv`, `ricambio.csv`, `milano_in_carica.csv`, `sindaci_milano.csv`):
   - Milano oggi (24/8/2026): sindaco Giuseppe Sala (68 anni); giunta 12 persone, 6 donne, età media 50,2; consiglio 48 consiglieri, 18 donne (37,5%), età media 50,7, 38 su 47 con laurea o più (titolo non indicato per 1), professione indicata per 12 su 48.
   - Donne in consiglio (fine anno): Milano 11,7% (2007), 20,8% (2012), 39,6% (2016), 35,4% (2025); comuni sopra 100.000 ab. 13,4% -> 31,8%; tutta Italia 17,9% -> 35,2%.
   - Donne in giunta: Milano 1 su 16 (6,2%) a fine 2010, **6 su 11 (54,5%) a fine 2011**; tutta Italia 19,8% (2010), 20,6% (2011), 41,7% (2025).
   - Sindache nelle 10 maggiori città (Roma, Milano, Napoli, Torino, Palermo, Genova, Bologna, Firenze, Bari, Catania): 3 a fine 2007 (Genova, Milano, Napoli), 0 a fine 2012-2015, 2 a fine 2016-2020 (Roma, Torino), 0 a fine 2021-2023, 2 a fine 2025 (Firenze, Genova). Milano: 1 sindaca su 13 sindaci dal 1946 (Moratti). Donne sindaco in tutta Italia: 9,8% (2007), 15,3% (2025).
   - Età media consiglieri: Milano 48,2 (2007), 47,3 (2016), 50,2 (2025); Italia 46,7 -> 50,0.
   - Laureati tra chi indica il titolo (consiglio, fine 2025): Milano 78,7% (titolo indicato dal 97,9%); sopra 100.000 ab. 64,4%; Italia 36,9% (indicato dal 75,8%).
   - Riconfermati (consiglieri del nuovo mandato già in carica nel precedente): Milano 39,6% (2016), 52,1% (2021); Italia, comuni al voto 2021: 37,2%; ultime elezioni delle altre grandi città tra 12,5% (Torino 2021) e 52,8% (Bari 2024).
   - Sindaci di Milano dal 1946: 13; il più lungo Tognoli 10,6 anni, poi Sala 10,2 (in carica); il più breve Borghini 1,1.
4. **La sorpresa** scelta per la pagina: tra i consiglieri le donne sono triplicate (11,7% -> 35,4%) e in giunta da 1/16 a 6/11 in un anno (2010 -> 2011), ma tra i sindaci delle dieci maggiori città non c'è stata una crescita (3 su 10 nel 2007, 2 oggi, zero nel 2012-2015).

## 2. Fonti, una per una

### 2.1 DAIT - amministratori comunali al 31 dicembre (2007-2025) - `raw/dait/comuni_31dic<anno>.csv`
- Contenuto: una riga per persona e carica nel comune (tutti i ~7.900 comuni): comune, popolazione censita, data elezione, carica, data nomina/inizio e cessazione, cognome, nome, sesso, data e luogo di nascita, lista/partito, titolo di studio, professione. Il DAIT ripubblica ogni anno il file con lo stesso nome base; dal 2023 lo schema cambia (colonne `LISTA_APPARTENENZA/COLLEGAMENTO`, `DATA_INIZIO_CARICA`, `INCARICO`, `FUNZIONE`) e la codifica passa da cp1252 a UTF-8. Dimensione 34-43 MB l'uno; 19 file; SHA-256 in `raw/dait/download_log.csv`.
- Cosa manca: i Municipi di Milano (presidenti e consigli); le persone entrate e uscite tra due 31 dicembre; prima del 2007; liste unificate per partito; titolo di studio e professione per una parte crescente di persone (vedi 4).
- Controlli (`pulito/controlli_build.json`): in tutti gli anni nessuna persona ha l'inizio dopo il 31/12 (un caso nel 2025); la cessazione prima del 31/12 appare solo dal 2023 (10, 23, 41 casi); sesso mancante 130-250 righe per anno su ~126.000-160.000; età fuori da 18-100 anni al massimo 3 righe (poste a "mancante"). Circa 15% delle righe sono persone presenti in due organi dello stesso comune (assessore e consigliere insieme, nei piccoli comuni); a Milano nessuna.
- Milano (ISTAT 015146): 60-77 righe per anno. Consiglio 48 + sindaco dal 2011 (59-60 consiglieri nel 2007-2010, prima della riduzione per legge); giunta 11-16.

### 2.2 DAIT - elenco "in carica" al 24/8/2026 - `raw/dait/in_carica_ammcom.csv` (+ `in_carica_sindaciincarica.csv`, `in_carica_maggiororgano.csv`, `in_carica_organistraordinariincarica.csv`)
- Stessa struttura (nomi di colonna in minuscolo, senza codice ISTAT: comune riconosciuto da codici regione/provincia/comune del Ministero e, per le grandi città, da nome + sigla di provincia). 125.953 righe.
- Milano: 61 righe (sindaco, 12 giunta, 48 consiglio). Sindaci delle 10 maggiori città: tutti trovati; 2 donne (Genova, Firenze).

### 2.3 Wikipedia italiana "Sindaci di Milano" - `raw/wikidata/wp_sindaci_milano.json` (wikitext, 72.601 caratteri)
- Licenza CC BY-SA 4.0. Qui si usano solo fatti (date di inizio/fine e partito). Non si ripubblica il testo. Programma `scripts/sindaci.py` controlla che ogni data scritta nel programma compaia nel testo salvato.
- Limiti: partito indicato per mandato come scrive Wikipedia (Bucalossi: Wikidata PRI, Wikipedia PSDI -> usato PSDI, annotato); Greppi nominato dal CLN il 27/4/1945, mandato "repubblicano" contato dal 7/4/1946 (linea del tempo di Wikipedia).

### 2.4 Wikidata (CC0) - `raw/wikidata/sindaci_p39.json` (SPARQL, P39 = Q3961545 "sindaco di Milano")
- 34 righe (alcune persone ripetute per più partiti). Usato per anno di nascita e sesso dei 13 sindaci dal 1946. Date di mandato su Wikidata incomplete prima del 1976 -> non usate. Controllo: i sindaci 2006-2025 coincidono con quelli del file del Ministero (nome e anno di nascita) in `pulito/controlli_sindaci.json`.

### 2.5 Comune di Milano (CKAN dati.comune.milano.it, CC BY) - ricerca in `raw/comune/search_*.json`
- Trovati e **NON scaricati** (non servivano alla pagina): ds1617 candidati consigliere 2021; ds1616 liste e candidati sindaco 2021; ds1625/ds1629 voti 2021 consiglio; ds743 e ds1643 presenze e votazioni dei consiglieri 2016-2021 e 2021-2026; ds1642 ecc. votazioni mensili; ds1914 dimissioni o surrogazioni dei consiglieri 2021-2026; ds2444-ds2452 copia dei file DAIT 2014-2022. Possibili sviluppi: presenze in aula per consigliere, surroghe, candidati/eletti per lista e preferenze. Nessun dataset su giunta/assessori/deleghe.
- `ds1914` permetterebbe di verificare le surroghe tra 31/12/2025 e 24/8/2026 (una donna in più su 48).

## 3. Pulizia e metodo (`scripts/build.py`, `analisi.py`)
- Carica -> ruolo: sindaco; giunta = vicesindaco e assessori (anche "non di origine elettiva"); consiglio = consiglieri, presidente e vicepresidenti, consiglieri candidati sindaco. Esclusi commissari, sub-commissari, "delega funzioni".
- Titolo di studio -> 4 livelli (Laurea o più; Diploma superiore; Licenza media; Elementare o nessun titolo). Professione (circa 400 voci, due elenchi) -> 13 gruppi con parole chiave (`scripts/comune_lib.py`): scelta nostra.
- Persona = SHA-1 di cognome|nome|data di nascita (solo per riconoscere la stessa persona tra anni; non pubblicato).
- Gruppi: 10 maggiori città (ISTAT), comuni con popolazione censita >= 100.000 alla data dell'elezione (44 nel file 2025), tutta Italia (7.772 comuni nel 2025). Città-anno incomplete: Roma 2021 (3 righe), Roma 2015 (solo commissario): escluse.
- Ricambio: persone del consiglio nella prima fotografia del mandato presenti (qualunque ruolo, qualunque fotografia) nel mandato precedente dello stesso comune; il mandato precedente deve essere osservato dall'inizio (non il primo del file).

## 4. Limiti dei dati (anche sulla pagina)
1. Solo 31 dicembre 2007-2025 + 24/8/2026; nulla prima.
2. Titolo di studio indicato per il 97% dei consiglieri italiani a fine 2007, 76% a fine 2025 (Milano 98%); professione: Italia 97% (2007) -> 66,5% (2025); Milano consiglio 98,5% (mandato 2006), 48% (2011), 36% (2016), 25% (2021), 12 su 48 oggi. Perciò la professione si mostra solo per il 2007 e nessun trend.
3. Roma 2015 e 2021 incompleti; Napoli e Roma con titolo spesso non indicato (Roma 21% nel 2016, Napoli 65% nel 2024-25): punti non disegnati sotto il 70%.
4. Organi piccoli (giunta 10-16 persone): variazioni di 6-10 punti per una persona.
5. Liste (non partiti), nomi di liste come presentati; assessori senza lista; niente aggregazione per schieramenti.
6. Età: 0,3-0,5% delle date di nascita sono "01/01" (forse segnaposto); non corrette.
7. Il riconoscimento della persona per nome + data di nascita può dare falsi "nuovi" per errori di scrittura.
8. Il confronto tra "tutta Italia" (piccoli comuni) e Milano ha regole diverse (numero di assessori, assessori che sono anche consiglieri).
9. Contesto di legge citato nella pagina (non è nei dati): legge 56/2014 art. 1 c. 137 (giunte nei comuni sopra 3.000 abitanti: nessun sesso sotto il 40%), legge 215/2012 (parità di accesso); confermata da una ricerca web (note delle consigliere di parità; testo non scaricato).

## 5. Privacy
- `comuni_ruoli.csv.gz` (tutta Italia, 2,4 milioni di righe): senza cognome, nome, luogo e data di nascita (solo sesso, anno di nascita, età, hash). `milano_amministratori.csv` (con nomi e cognomi, ruoli pubblici di Milano 2007-2025) resta in `pulito/`, non è pubblicato. Sul sito: aggregati + elenco di Milano 24/8/2026 con nome, ruolo, lista, sesso, fascia d'età, titolo, categoria di professione (senza data né luogo di nascita).
- Il raw contiene date e luoghi di nascita e non va ripubblicato.
