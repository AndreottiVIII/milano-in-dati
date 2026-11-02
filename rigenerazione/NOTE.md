# I progetti di rigenerazione - fase 1 e pagina

Scaricato il 1 novembre 2026. Programmi in `scripts/` (python -I -X utf8, percorsi assoluti), dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle in `pulito/`, pagina in `docs/rigenerazione/`.

## 1. In breve
1. **L'Atlante della rigenerazione urbana del Comune (circa 145 progetti, mappa aggiornata a 02/2026) NON è riusabile.** Il servizio ArcGIS "Mappa dei progetti di Rigenerazione urbana" (Geoportale, `gisportal.comune.milano.it`, cartella `D_Rigenerazione_urbana/Mi2030_Rigenerazione_Urbana`) dice nella descrizione: "Copyright Comune di Milano. Solo consultazione autorizzata" (nessuna licenza di riuso). Non ho scaricato i suoi dati (solo elenco dei livelli e descrizione: `raw/web_probe/rig_mapserver.json`, `gis_search_rigenerazione.json`). La pagina ufficiale dell'Atlante su comune.milano.it risponde 403 ai programmi: non aggirato. Un tentativo di leggerne una copia dalla Wayback Machine è stato bloccato dal sistema di controllo e non è stato ripetuto.
2. **Non c'è nulla su CKAN (dati.comune.milano.it)**: 26 parole chiave (`scripts/search.py`, `raw/search_all.json`, 74 dataset) non trovano piani attuativi, PII, accordi di programma, convenzioni, Atlante, Reinventing Cities. Solo confini NIL (ds964), edilizia (ds270-271, 2983-2985), edifici degradati (ds503).
3. **Fonte usata: PGT Milano 2030 vigente, Tavola R02, CC BY 4.0** (descrizione del servizio ArcGIS `PGT/Milano_2030_PGT_Vigente_Tavola_R02`, "approvati il 05/02/2020", responsabile Direzione Rigenerazione urbana, "Frequenza di aggiornamento: Non pianificato"). Livello 10 "Ambiti interessati da provvedimenti in itinere approvati e adottati": 405 record (uno, objectid 444 "Fiera - CityLife", senza geometria: scartato), campi `tipopianif`, `nome`, `statoattuazione`, `tipoarea`, area. **Non ci sono** case, volumi, quota di edilizia sociale, verde, date, soggetti attuatori.
4. Numeri: 404 poligoni, 277 ambiti (tipo+nome; 258 nomi), **978 ettari** (unione; somma dei poligoni 1.199, 18% sovrapposto) = 5,4% dei 18.176 ha dei NIL. Accordi di programma e intese 644 ha, programmi integrati 259, piani attuativi 63. Stato nel 2020: 214 ambiti non attuati (396 ha), 25 attuati in parte (536 ha), 37 attuati (94 ha).
5. **Sorpresa**: gli ambiti (5,4% del territorio) contengono 100 dei 244 ettari di suolo diventato consumato 2012-2025 (41%); più della metà in due ambiti (MIND-ex Expo 30,5 ha, Cascina Merlata 23,6); Calchi Taeggi (Lorenteggio) 15,3. Le trasformazioni famose (Porta Nuova, CityLife, Portello, Romana, Farini) quasi 0: erano già consumate (80-96%). Gli ambiti erano consumati nel 2012 al 63%, la città al 58%. Prezzi OMI: mediana +27,3% nei 13 NIL (>=5.000 residenti) con >=10% di ambiti, +27,2% negli altri 60; Spearman +0,13 (IC -0,09/+0,35). Abitazioni nuove ogni 1.000 residenti: Spearman +0,26 (IC +0,01/+0,47).

## 2. Fonti (una per una)
| Fonte | Contenuto | Licenza | Scaricata | Manca |
|---|---|---|---|---|
| PGT R02, livelli 10, 12, 21, 6, 2, 4 (`raw/pgt/r02_*.geojson`) | ambiti in itinere (405), piani attuativi obbligatori (22 poligoni, 16 nomi, 136 ha), aree ERS di nuova previsione (9, 3,4 ha), grandi funzioni urbane (11, 195 ha), ambiti di rigenerazione ambientale (279, 667 ha), nodi di interscambio (13, non usato) | CC BY 4.0 (descrizione servizio) | 1/11/2026 | tutto ciò che è quantità edilizia |
| PGT R10, livello 3 (`raw/pgt/r10_rigenerazione.geojson`) | 1.601 poligoni "Ambiti di Rigenerazione" (concetto LR 31/2014), 3.682 ha; solo nei conti di controllo (coincidono con gli ambiti R02 per 72 ha) | CC BY 4.0 | 1/11/2026 | |
| NIL vigenti ds964 | confini | CC BY | già nel filone citta-15-minuti | |
| ISPRA/SNPA carte del consumo di suolo 2012 e 2025 | 10 m, già scaricate dal filone suolo | CC BY 4.0 IT | filone suolo | |
| Prezzi OMI, abitazioni nuove, ALER | per NIL, da docs/quartieri-che-cambiano, docs/costruzioni, docs/case-popolari | vedi quei filoni | | |
| Atlante / "Mappa dei progetti di Rigenerazione urbana" | ~145 progetti | **solo consultazione**: non usata | NO | |
| Reinventing Cities (sito ufficiale) | non raggiungibile dal programma (`reinventingcities.org` non risolve); non cercato altrove | - | NO | |

## 3. Pulizia (`scripts/build.py`, log in `pulito/build_log.txt`)
- Area ricalcolata in UTM 32N: coincide con l'attributo del file (rapporto mediano 1,0000). Unione dei poligoni per non contare due volte le sovrapposizioni.
- Tipi di piano raggruppati a mano in 6 gruppi (vedi `GRUPPO` nel programma). "Fondo Comune Milano 1 e 2" (94 poligoni, 11 ha, tutti non attuati): il significato non è spiegato nel file (ipotesi non verificata: lotti di fondi immobiliari del Comune).
- Stato: `tipoarea` del file (ambito attuato / attuato in parte / non attuato / area non attuata). "Area non attuata" ha `statoattuazione` = "---" (70 record): lo leggo come parte da realizzare di un ambito più grande (ipotesi).
- Stato di un ambito (tipo+nome): uguale a quello dei poligoni se tutti uguali; altrimenti "attuato in parte" (se c'è almeno un attuato) o "non attuato".
- NIL di un ambito: quello con più area in comune. Quota di NIL in ambiti: intersezione con l'unione.
- Suolo: pixel (10 m) non consumato nel 2012 e consumato nel 2025 (classi 1, 11, 12, 111-126) dentro i poligoni. Controllo: somma NIL = 244,18 ha = pagina suolo (scarto massimo per NIL 0,000).
- Correlazioni di Spearman con IC 95% bootstrap (2.000), solo NIL con >=5.000 residenti (73).

## 4. Cosa può mostrare la pagina e cosa no
Può: dove, tipo, ettari, stato 2020, NIL, suolo nuovo dentro gli ambiti, confronto con prezzi e abitazioni nuove (confronto, non causa).
Non può: case, volumi, quota di edilizia sociale, verde promesso, date, soggetti attuatori, stato attuale. Servirebbe l'Atlante: per usarlo bisogna chiedere al Comune una licenza di riuso (decisione di Davide).

## 5. Pagina
`docs/rigenerazione/index.html` + `data/` (0,31 MB). Costruita da `scripts/pagina.py` (controlli interni, rilanciabile). Verificata in browser: nessun errore in console, nessuno scroll orizzontale a 375 px.
