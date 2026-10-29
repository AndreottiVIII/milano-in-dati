# Violenza politica a Milano dal 1900: note sulle fonti

Data di raccolta: 29 ottobre 2026. Tutto è stato scaricato con programmi (cartella `scripts\`), nessun accesso con login.

## Cosa abbiamo fatto, in breve
1. Chiesto a Wikidata (SPARQL) gli eventi del Comune di Milano dal 1900 e gli attentati in Italia.
2. Scaricato da Wikipedia in italiano (API MediaWiki) le categorie su stragi, attentati, anni di piombo, vittime e simili (profondità 3), più 45 ricerche per parola, e letto l'introduzione di 4.243 pagine.
3. Trovato che la base migliore sono le tabelle di Wikipedia «Persone uccise negli anni di piombo (1969-1982)» e le cronologie «Cronologia dello squadrismo» e «Cronologia degli anni di piombo…». Da lì e dalle voci dedicate abbiamo fatto l'elenco curato in `scripts\eventi_seed.py` (65 eventi + 26 esclusi con il motivo).
4. Unito tutto in `pulito\eventi.csv` (colonne: data, tipo, luogo, coordinate, morti, feriti, vittime, responsabili come scritti da Wikipedia, se la voce parla di rivendicazione o di condanne, link it/en, codice Wikidata, data della versione di Wikipedia letta, confidenza, note).

## Fonti, query, file
| Fonte | Come | File | Note |
|---|---|---|---|
| Wikidata | 3 query SPARQL (`scripts\01b_wikidata.py`): A = eventi con data ≥1900 e luogo Milano (P276/P131), B = attentati/stragi/omicidi in Italia con data ≥1900, C = persone morte a Milano con morte per omicidio | `raw\wikidata\A_eventi_milano.json` (786 righe), `B_attentati_italia.json` (1.562), `C_morti_milano.json` (284) | CC0. Wikidata ha pochi eventi di questo tipo: 39 dei 65 hanno un codice Wikidata (preso dalla pagina Wikipedia); gli altri 26 sono in gran parte righe di cronologie senza voce propria e non hanno un elemento Wikidata |
| Wikipedia it, categorie | `scripts\02_categorie.py` | `raw\wikipedia\pagine_categorie.json` (2.798 pagine dopo il filtro), `categorie_visitate.json` (217) | CC BY-SA 4.0 |
| Wikipedia it, ricerche | `scripts\02b_ricerche.py` | `raw\wikipedia\ricerche.json` (1.872 titoli) | |
| Wikipedia it, introduzioni | `scripts\03_info_pagine.py`, `04_candidati.py` | `info_pagine.jsonl`, `candidati.txt` (168 candidati con «Milano» e parole di violenza) | |
| Wikipedia it, tabelle e cronologie | `scripts\05_liste_piombo.py`, `06_parse_tabelle.py` | `liste_piombo.json` (testi con numero di versione), `piombo_righe_tutte.json` (239 righe, Italia), `piombo_righe_milano.json` (36 righe), `cronologia_milano.txt` | |
| Wikipedia it, testo delle voci | `scripts\07_wikitext.py` | `wikitext_eventi.json` (48 pagine, con numero di versione) | per i dati dell'infobox |
| Numeri civici del Comune (ds634) | letto sola lettura da `donne-nelle-vie\raw\comune\ds634\` | — | CC BY. Usato solo per dare un punto alla strada quando Wikipedia dà la via ma non le coordinate |

## Licenze
- Wikidata: CC0. Wikipedia: CC BY-SA 4.0. Sul sito si pubblicano solo fatti brevi (data, luogo, numeri, nomi di vittime e responsabili come li scrive Wikipedia) e i link alle pagine, non il testo delle voci. Il campo `rivendicazione_snippet` (una frase) è solo nel file locale `pulito\eventi.csv`, non sul sito.
- I file grezzi (`raw\`) non vanno ripubblicati così come sono.

## Come sono scelti i tipi
- **strage/bomba**: bombe con più vittime e stragi (anche eccidi con fucilazioni: Arena 1943, Loreto 1944; e l'agguato di via Schievano, che Wikipedia chiama «strage»).
- **attentato**: altre azioni con bomba o incendio (ferite o con una vittima).
- **omicidio politico**: uccisioni nelle liste di Wikipedia sulla violenza politica, comprese le rapine di autofinanziamento con un morto indicate dalla cronologia.
- **scontro o custodia**: morti in scontri di piazza, per spari delle forze dell'ordine, in custodia (Pinelli), e brigatisti o militanti uccisi in conflitti a fuoco. Questa categoria non era nel mandato: l'abbiamo aggiunta perché Wikipedia mette questi casi negli stessi elenchi.

## Responsabili, rivendicazioni, condanne
Il campo `responsabili_wikipedia` è copiato dalla colonna «Responsabili» delle tabelle o dall'infobox. `rivendicazione_citata` e `condanne_citate` valgono «sì» se nel testo della voce compaiono le parole *rivendic…* o *condann…/ergastolo*: è un rilevamento automatico, può dare falsi «sì» (per esempio una condanna per un altro fatto). Sul sito è scritto «la voce parla di…», senza dire chi.

## Copertura e limiti (da dire chiaramente)
- Solo eventi che Wikipedia o Wikidata registrano. Gli eventi minori non ci sono.
- Per le tabelle degli anni di piombo, Wikipedia elenca le persone uccise: gli attentati senza morti e le gambizzazioni non ci sono (le gambizzazioni stanno in una categoria a parte che non abbiamo percorso: da fare se serve).
- Anni 1946-1968: un solo evento (1947). Non vuol dire che non ci siano stati: manca la fonte.
- Dopo il 1993: un solo evento (2003). Non abbiamo trovato su Wikipedia attentati del XXI secolo a Milano con morti per violenza politica.
- 21 eventi su 65 non hanno coordinate (Wikipedia non dà un luogo preciso): sono solo nell'elenco.
- Le posizioni ricavate dalla sola via sono approssimate (centro dei civici della via). La nota di ogni evento lo dice.

## Controlli fatti
Vedi `pulito\problemi.md` (trappole, differenze Wikidata/Wikipedia, esclusioni, eventi attesi non trovati).
