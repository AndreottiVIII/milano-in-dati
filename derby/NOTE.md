# NOTE - derby di Milano dal 1909 (filone 15, fase 1: solo raccolta e controllo)

Cartella: `milano-in-dati\derby\`. Data del lavoro: 30 ottobre 2026. Nessun grafico, nessuna pagina, niente git.

## Che cosa c'e' di pronto

| File | Che cosa contiene |
|---|---|
| `pulito\derby.csv` | una riga per partita giocata: 246 derby (244 ufficiali + 2 del campionato di guerra 1944). Colonne: id, data, stagione, competizione, turno, stato (ufficiale / `wartime_honorary`), squadra di casa e ospite (e il nome di allora: Ambrosiana, Ambrosiana-Inter, Milano), gol, vincitore, stadio, stadio neutro, arbitro, note sul risultato, quante fonti hanno controllato e quante concordano, `home_label_disputed` |
| `pulito\marcatori.csv` | una riga per gol: 663 righe (partita, squadra a cui va il gol, giocatore, minuto, autogol, rigore, club del giocatore) |
| `pulito\differenze.md` | tutte le differenze trovate tra le fonti (data, punteggio, casa, stadio, arbitro, marcatori) |
| `pulito\differenze_marcatori.csv` | stesso elenco dei marcatori, in forma di tabella |
| `pulito\non_ufficiali_riepilogo.csv` | le 72 partite non ufficiali: SOLO i totali per torneo (le singole partite non le ho trovate in fonti libere) |
| `pulito\_*.csv` | file intermedi (uno per fonte), si rigenerano con gli script |
| `scripts\01..12` | gli script (si rilanciano con `python -I`; ordine: 01, 02, 03, 04, 05, 06, 07, 08, 09, 11, 12, poi 10) |
| `raw\` | i file scaricati, intatti |

Totali (identici alla tabella riassuntiva di it.wikipedia): 246 derby ufficiali in senso largo = 91 vittorie Inter, 71 pareggi, 84 vittorie Milan; gol Inter 341, gol Milan 324.
Per competizione (derby / Inter-pari-Milan): Prima Categoria 14 (5-2-7); Divisione Nazionale 1926-28 e 1945-46 8 (3-1-4); Serie A 184 (70-57-57); Coppa Italia 29 (9-9-11); Supercoppa 3 (1-0-2); Champions League 6 (2-2-2); Campionato Alta Italia 1944 2 (1-0-1, stato `wartime_honorary`, riconosciuto solo a titolo onorifico).
Non incluse: la partita del 31 ottobre 2026 (domani, Serie A 2026-27) e quella di febbraio 2027, che it.wikipedia gia' elenca come "da giocare".

## Le fonti (URL, data di scarico, file, periodo, licenza)

Scarico: 30 ottobre 2026. User-Agent con contatto, pause di 1-3 secondi, nessun login, nessuna registrazione.

1. **it.wikipedia, "Derby di Milano"** - API MediaWiki, revisione 153044197 del 24/10/2026. File `raw\wikipedia\it_Derby_di_Milano.json` e `.wiki` (203 KB). Lista completa dal 1909: data, stadio, competizione, squadra di casa, punteggio, marcatori (con minuto, rigori, autogol), arbitro, link al referto. Ho tolto le 2 partite future. **E' la spina dorsale** di `derby.csv`. Licenza CC BY-SA 4.0: si prendono solo i fatti (date, punteggi, nomi), non il testo; citare "Wikipedia, CC BY-SA".
2. **en.wikipedia, "Derby della Madonnina"** - revisione 1382484836 del 28/10/2026 (`raw\wikipedia\en_Derby_della_Madonnina.*`, 99 KB). Data, competizione con turno, casa, punteggio; note a pie' di pagina (partita sospesa 2005, supplementari 2017). Stessa licenza. E' un'altra pagina ma scritta dalla stessa comunita': non e' un controllo del tutto indipendente.
3. **35 pagine di edizione di it.wikipedia** (campionati 1909-1928, 1944, 1945-46; Coppa Italia; Supercoppa; Champions) in `raw\wikipedia\seasons\`. Dove c'e' il riquadro "Incontro di club" danno turno, stadio, arbitro, marcatori: 23 partite controllate (Coppa Italia 1958-2000 e Supercoppa).
4. **engsoccerdata** (James Curley) - `https://raw.githubusercontent.com/jalapic/engsoccerdata/master/data-raw/italy.csv`, 1,9 MB, 28.824 partite di Serie A 1929-30 / 2024-25 (186 derby). Licenza del pacchetto: GPL (>= 2) (file `raw\engsoccerdata\DESCRIPTION`). Uso solo come controllo; non ripubblicare il file grezzo. Tratta la Divisione Nazionale 1945-46 come Serie A; non ha le stagioni di guerra.
5. **football-data.co.uk** - 31 CSV 1993-94 / 2023-24 dalla copia `footballcsv/cache.footballdata` (CC0 per la copia) + 3 CSV 2024-26 direttamente dal sito (`raw\footballdata\`, 0,9 MB). **Attenzione ai termini del sito**: dati gratuiti ma "solo per privati, non per prodotti commerciali o di addestramento con bot/scraper/IA". Qui servono solo a controllare data e punteggio di 66 partite; non vanno ripubblicati e non fanno parte dei file finali.
6. **openfootball/italy** (CC0, pubblico dominio) - `https://github.com/openfootball/italy`, stagioni 2013-14 / 2026-27 (anche Serie B e C, scaricate per errore, inutili). 31 derby controllati (campionato 2013-26 + Coppa Italia 2020-25). Il file `2025-26_1-seriea-full.txt` ha marcatori con minuto e spettatori dei 2 derby 2025-26.
7. **RSSSF** (Rec.Sport.Soccer Statistics Foundation) - `https://www.rsssf.org/tablesi/ital{AA}.html`, 107 pagine di stagione dal 1925-26 + pagine Coppa dei Campioni (`raw\rsssf\`, 6 MB). robots.txt assente (404). Licenza: "libera copia citando RSSSF". Elenchi partita per partita con data della giornata e marcatori. Il mio programma non legge le pagine 2012, 2026, 81 e 83 (nel 1980-81 e 1982-83 il Milan era in B: niente derby). Pagine Champions League: confermano i 3 incroci.
8. **Almanacco nerazzurro di interfc.it**, copia di web.archive.org del febbraio 2017 (link nella colonna "Referto" di it.wikipedia): data, risultato, marcatori con minuto, arbitro delle partite ufficiali dell'Inter fino al 2000. Contenuto dell'Inter: serve solo come controllo dei fatti, non si ripubblica. Scaricate 149 pagine (circa 17 KB l'una) in `raw\interfc_archive\`, con pause di 3 secondi.
9. **Wikidata** (SPARQL, `raw\wikidata\`): provato, **non utilizzabile**. Le partite non sono modellate: ci sono solo le stagioni dei campionati, 3 finali di Coppa Italia/Supercoppa e un elemento "derby". Nessun dato partita per partita.
10. **footballcsv/italy**: nel repository ci sono solo la specifica del formato e la licenza (CC0), nessun dato.

## Come concordano le fonti

Confronto partita per partita con la lista di it.wikipedia (dettaglio in `pulito\differenze.md`). Prima ho **corretto 4 voci di it.wikipedia** dove 3 fonti indipendenti da Wikipedia (engsoccerdata, RSSSF, Almanacco Inter) dicono la stessa cosa contro it.wikipedia ed en.wikipedia:
- 1931-03-19 -> 1931-03-15 (il 19 marzo 1931 era un giovedi', festa di San Giuseppe); 1948-10-16 -> 1948-10-17;
- 1955-10-16 e 1956-03-11: la squadra "di casa" era invertita in tutte e due (e i link "Referto" sono scambiati). Giusto: 16/10/1955 Milan-Inter 1-2; 11/3/1956 Inter-Milan 2-1.
Dopo le correzioni:
- **Almanacco Inter (archive.org)**: 149 partite (tutte le ufficiali dal 1909 al 27/1/2000 con link), 149 concordano su data, casa e punteggio. Differenze: 1 arbitro (1993-02-10), 3 minuti di gol.
- **engsoccerdata** (186): 177 identiche; 9 diverse: 4 con casa/ospite invertiti (1960-11-20, 1961-03-26, 1964-11-15, 1965-03-28) e 5 date (1948-04-15, 1963-11-03 invece del 1964-01-19, 1974-11-04, 1995-04-14, 2001-05-13).
- **RSSSF** (196 lette dal programma): 188 identiche; 8 diverse: 2 con casa invertita (1964-11-15, 1965-03-28) e 6 date (di giornata, vedi trappole).
- **football-data** (66): 65 identiche; 1 data (1995-04-14 invece del 15).
- **openfootball** (31): tutte identiche.
- **en.wikipedia** (246): 238 identiche; 8 diverse: le 2 partite 1955-56 (stesso errore di it.wikipedia) e 6 date diverse (1931-03-19, 1948-10-16, 1958-06-16, 1972-06-08, 1975-05-16, 1999-10-24).
- **Pagine edizione it.wikipedia** (23 Coppa Italia/Supercoppa): 22 identiche; 1 data (1972-06-08). Stadio: 1909-01-10 (Arena Civica contro Porta Monforte); arbitri scritti in modo diverso.
- **RSSSF Champions League**: i 6 punteggi confermati.
- Il punteggio e' concorde tra tutte le fonti su 240 partite su 246. Le 6 eccezioni sono solo di **etichetta casa/ospite** (il vincitore non cambia mai): le 2 del 1955-56 (en.wikipedia ripete l'errore di it.wikipedia, corretto sopra) e le 4 del 1960-61 e 1964-65: per il 1960-61 RSSSF e Almanacco stanno con it.wikipedia contro engsoccerdata; per il 1964-65 it.wikipedia, en.wikipedia e Almanacco Inter contro engsoccerdata e RSSSF (ho lasciato la versione di it.wikipedia). Colonna `home_label_disputed` = 1 se almeno una fonte discorda.
- **Marcatori**: i gol di it.wikipedia tornano col punteggio in tutte le partite (tranne la assegnata del 2005). Confronto con RSSSF, Almanacco e pagine edizione: 23 segnalazioni, quasi tutte differenze di 1 minuto; casi piu' grossi: 1946-05-30 (ultimo gol al 75' in Wikipedia, al 47' in RSSSF e Almanacco), 1956-10-21 (12' e 16' contro 17' e 17'), 1983-11-06, 1999-10-23. Non corretti, solo segnalati.

## Trappole dei dati (da non dimenticare)

1. **"Casa" nel derby e' un'etichetta**: dal 1947 le due squadre dividono San Siro, e anche prima il calendario assegnava la "casa" a una delle due ma non sempre si giocava nel suo stadio (anni 1930-40: partite col Milan "di casa" all'Arena Civica). Per studiare l'effetto campo servono la colonna `venue` e le 6 partite con etichetta contestata (4 dopo le correzioni: 1960-11-20, 1961-03-26, 1964-11-15, 1965-03-28; piu' le 2 del 1955-56 gia' corrette).
2. **Stadi**: Campo Milan di Porta Monforte (6), Arena Civica (23), Campo di via Goldoni (5, campo dell'Ambrosiana), San Siro (208), 3 stadi esteri per le Supercoppe (`neutral_venue` = 1: Pechino 2011, Riad 2023 e 2025). La partita del 1909-01-10: it.wikipedia dice Porta Monforte, la pagina del campionato 1909 dice Arena Civica (differenza registrata). Una partita (1921-01-30) non ha lo stadio.
3. **Nomi**: Inter si chiama Ambrosiana (4 partite, 1929-31) e Ambrosiana-Inter (26 partite, 1931-44); il Milan si chiama Milano (10 partite, 1939-44). Colonne `home_club_name`, `away_club_name`.
4. **Partita assegnata a tavolino**: Inter-Milan 12/4/2005, Champions (quarti, ritorno). Sospesa al 73' sullo 0-1 per i fumogeni; UEFA ha dato 0-3. In `derby.csv` il risultato e' 0-3 (come nelle statistiche ufficiali, che sommano 246 partite e 341-324 gol), nei marcatori c'e' solo il gol vero (Sevcenko 30'). Per questo i gol in `marcatori.csv` sono 663 e non 665.
5. **Campionato Alta Italia 1944** (guerra, gironi regionali): riconosciuto solo a titolo onorifico. L'ho tenuto a parte: `status = wartime_honorary`, `official = 0`. Con lui il totale e' 246 come Wikipedia; senza, 244. RSSSF lo mostra come un solo incrocio con andata e ritorno e concorda.
6. **Interruzione 1915-1920**: nessun derby tra il 2/5/1915 (Prima Categoria) e il 19/12/1920. Poi nessuno fino al 3/4/1927; nel 1928-29 non si sono incontrati (nelle fonti non c'e' nessun derby).
7. **Stagioni**: "Coppa Italia 1958" e' l'edizione 1957-58 giocata a giugno-luglio 1958 (idem altre edizioni "estive" 1968, 1972, 1975, 1977, 1985). Nel campo `season` ho usato l'edizione. Il campionato 1909 e' una stagione solo (gennaio-aprile 1909).
8. **Tornei interrotti da piu' fasi** (Coppa Italia a gironi 1958, 1968, 1981...) hanno il turno in `round` (da en.wikipedia) e in `round_it_box` (dalle pagine edizione). Per il campionato di Serie A non ho il numero di giornata.
9. **Punteggi dopo supplementari/rigori**: solo il derby di Coppa Italia 27/12/2017 e' finito dopo i supplementari (1-0, gol di Cutrone al 104'); nei dati non risulta nessun derby deciso ai rigori.
10. **Marcatori**: i gol sono assegnati alla squadra che li ha segnati sul tabellino (autogol compresi: `team_credited`); `scorer_club` dice di che squadra era il giocatore. 14 gol del 1911-1914 non hanno minuto. `penalty = some` quando in una riga con piu' gol c'e' un solo rigore e non si sa quale. Gli accenti dei nomi (Sevcenko/Ševčenko) cambiano tra fonti.
11. **Date RSSSF**: RSSSF usa la data della giornata; partite spostate hanno data diversa. Le differenze di data della sola RSSSF non vanno considerate errori.
12. **engsoccerdata e 1945-46**: contiene i 4 derby della Divisione Nazionale 1945-46 come "Serie A" (livello 1); in `derby.csv` restano "Divisione Nazionale" come in it.wikipedia. Non ha le stagioni di guerra.
13. **football-data.co.uk**: termini d'uso restrittivi (solo privati). Tenerlo come controllo, non come fonte del sito.

## Cosa manca

- Le **72 partite non ufficiali** (amichevoli, tornei minori, coppe di guerra, Mundialito, ecc.): ho solo i totali per torneo (`non_ufficiali_riepilogo.csv`), non le singole partite. Non esiste una lista libera e completa; servirebbe il PDF dell'almanacco di magliarossonera.it (fonte citata da Wikipedia) o altre ricerche.
- Il **numero di giornata** per le partite di campionato e il **turno** per la Coppa Italia delle prime edizioni.
- Punteggio/data senza nessun controllo indipendente da Wikipedia: le 3 Supercoppe (2011, 2022, gennaio 2025: solo it.wikipedia, en.wikipedia e la pagina dell'edizione). Tutto il resto ha almeno un'altra fonte non Wikipedia (Almanacco Inter fino al 27/1/2000, poi football-data, engsoccerdata, openfootball, RSSSF).
- Marcatori dal 2000 al 2025: oltre a it.wikipedia c'e' solo RSSSF (non in tutte le stagioni: mancano i minuti per molte partite 2012-2025) e le pagine edizione per alcune coppe. Sono quindi i meno controllati.
- I gol delle partite 2025-26 hanno come controllo il file `full` di openfootball (minuti concordano).


---

# Fase 2 - la pagina `docs\derby\` (30 ottobre 2026)

Pagina pubblica semplice come `docs\aria\` (nero su bianco; blu Inter, rosso Milan e grigio per i pareggi solo come colori dei dati). Anteprima: server "milano-in-dati", porta 8796, `http://127.0.0.1:8796/derby/`. Nessun errore in console, nessuno scorrimento orizzontale a 375 px. `docs\index.html` NON toccato (il link dalla home non c'e' ancora).

## Come si rifa

`python -I scripts\pagina_dati.py` (da `derby\`; opzionali: cartella derby, cartella di uscita). Legge `pulito\derby.csv`, `marcatori.csv`, `differenze.md`, `non_ufficiali_riepilogo.csv`, usa il modello `scripts\pagina_template.html` e riscrive tutto in `docs\derby\`: `index.html` e `data\` (`partite.json` per grafico ed elenco; `derby.csv`, `marcatori.csv` pubblici; `differenze.md`). Ogni numero del testo e' calcolato dal programma; ci sono controlli (246 derby, 91-71-84, 341-324, 663 gol con marcatore + 2 a tavolino).

## Cosa c'e' nella pagina

In breve (totali e per competizione); saldo cumulato Inter-Milan 1909-oggi (grafico SVG con passaggio del mouse/dito, pause senza derby a righe) + fasi lunghe + tabella per decennio; serie record (vittorie, imbattuto, senza pareggi, pareggi di fila), vittorie larghe (scarto >= 4), partite con piu' gol (>= 8); "Conta giocare in casa?" (prima/dopo il 1 gennaio 1947, 53 contro 189 derby, esclusi 3 campi neutri e il 2005 a tavolino, margini d'errore dichiarati, controprova invertendo le 4 etichette contestate); marcatori (>= 5 gol, autogol a parte); elenco ricercabile dei 246 derby; fonti e differenze.

## Scelte da ricordare

- Serie e saldo contano tutti i 246 derby di Wikipedia, 1944 e 2005 compresi (il 2005 resta vittoria del Milan, perche' stava gia' vincendo 0-1). Nota in pagina: senza i due derby del 1944 la serie senza pareggi di 13 sarebbe 11.
- "Casa" prima/dopo il 1947: per il colore delle barre NON si usano blu/rosso (sarebbero scambiati per Inter/Milan): nero = casa, grigio = pareggio, bianco = ospite.
- **Correzione di un numero della fase 1**: `non_ufficiali_riepilogo.csv` dava 73 partite non ufficiali (Tournee a Perth = 2); il totale di it.wikipedia e' **72**, quindi Perth vale 1. Nella pagina uso 72 e lo dico. Il CSV di fase 1 non e' stato modificato.
- Licenza dei file pubblici in `docs\derby\data\`: dichiarata CC BY-SA 4.0 (partono dai fatti di Wikipedia). `derby.csv` pubblico toglie `sources_list`, `report_url` (link all'Almanacco Inter) e `official`. `differenze.md` pubblico toglie le righe che citano football-data.co.uk. Nessun dato di football-data ne' dell'Almanacco Inter e' ripubblicato.
- Decennio 1909-1919 unisce il solo derby del 1909 agli anni Dieci.
- Da decidere con Davide: aggiungere il link dalla home `docs\index.html`; pubblicazione (GitHub Pages) non fatta, niente git.
