# Lapidi e targhe di Milano - FASE 1 (verifica dell'archivio): ESITO = NON PROCEDERE

Controllo fatto il 2 novembre 2026. Niente pagina web, niente `pulito/`. Regola dell'incarico: andare avanti solo con almeno 500 targhe con luogo e soggetto da fonti il cui uso e' permesso. **Non c'e'. Vedi sezione 1.**

## 1. Verdetto
**Non esiste un archivio aperto utilizzabile.** Cio' che c'e':
- **Pietre della Memoria** (pietredellamemoria.it, ANMIG): l'unico archivio vero, 496 voci per il Comune di Milano con indirizzo, coordinate, data di posa e testo, ma (a) **"Tutti i diritti sono riservati"**, nessuna licenza di riuso, e' una banca dati con diritto del costitutore; (b) di quelle 496 voci **101 sono pietre d'inciampo** (gia' nel filone `../pietre-inciampo`) e le targhe vere (lastra, lapide, targa) sono **326**, piu' 26 monumenti, 11 cippi, 9 stele e 22 altre voci; quindi anche con il permesso **non si arriva a 500 targhe**; (c) sono quasi tutte guerra e Resistenza: non e' "le targhe di Milano" ma "le memorie di guerra".
- Le fonti con termini chiari (OSM ODbL, Wikidata CC0, Commons per file) danno **meno di 500 targhe con luogo** (stima sotto) e il soggetto si conosce per una minoranza.
- Il Comune di Milano **non ha un dataset** (CKAN, 9 ricerche: "lapidi" 0, "toponomastica commemorativa" 0, "partigiani" 0, "resistenza" 0, "memoria" 0; `raw/ckan_ricerca.json`). Le ~470-500 targhe partigiane e il "recupero di un centinaio di targhe" del 2025 sono notizie di stampa, non dati. ANPI Milano e Istituto Parri/INSMLI: nessun elenco scaricabile trovato.

## 2. Fonti, una per una

| Fonte | Contenuto | Righe | Termini | Scaricato | Cosa manca |
|---|---|---|---|---|---|
| Pietre della Memoria `/comuni/milano/` | schede con titolo, indirizzo, lat/lon, data di collocazione, materiali, ente, testo | 496 voci (83 pagine da 6): 204 lastre, 121 lapidi, 1 targa, 101 pietre d'inciampo, 26 monumenti, 11 cippi, 9 stele, 23 altro | `robots.txt`: solo `/wp-admin/` vietato (elenchi ok). Piede di pagina: "(c) 2012-2026 Anmig e Fondazione. Tutti i diritti sono riservati." Nessuna pagina di licenza. Foto di volontari | 2/11/2026, solo le 83 pagine ELENCO + 1 scheda di prova, 1 richiesta ogni 1,3 s, User-Agent con la nostra identita' | permesso di riuso; solo guerra e Resistenza; molte schede nuove (2025-26: la banca dati cresce) |
| OpenStreetMap (Overpass) | `memorial=plaque` ecc. nel Comune | 165 targhe (209 elementi con le altre ricerche); 64 con `name`, 79 con `inscription`, 128 con uno dei due, 3 con soggetto Wikidata | ODbL (citare (c) OpenStreetMap contributors, share-alike) | 2/11/2026 07:42Z, `raw/osm/overpass_targhe.json` | soggetto, anno (12 su 165) |
| Wikidata | targhe (Q721747) a Milano | 61 targhe (56 solo Wikidata + 5 anche OSM, dal filone statue) | CC0 | 1/11/2026 (filone statue) | ~140 senza coordinate |
| Wikimedia Commons | categoria "Plaques in Milan", 105 categorie | 1.674 FOTO (non targhe), 298 con coordinate, che si riducono a 172 punti distinti, 141 non vicini (30 m) a targhe OSM | testi CC BY-SA/CC0, ogni foto con la sua licenza (solo metadati letti) | 2/11/2026, `raw/commons/plaques_milan.json` | una foto non e' una targa; molte sono iscrizioni di chiese e palazzi |
| ICCD / Lombardia Beni Culturali | lapidi commemorative | 143 schede nel filone beni-culturali (107+4+32) | CC BY o CC BY-SA, da chiarire | dump 2023 | 470 su 715 schede di "scultura/lapide" senza coordinate, 228 con quelle di un museo |
| Comune di Milano (CKAN) | nulla | 0 | - | 2/11/2026 | tutto |
| "80 luoghi x 80 anni di Liberta'" (Comune + Statale) | mappa PDF | 19 targhe con 1.739 nomi di partigiani | comunicato stampa, no dati | non scaricata | non e' un dataset |
| Filone `statue` | 218 lapidi (157 OSM, 56 Wikidata, 5 insieme) | 213 con coordinate, 86 con un soggetto | misto ODbL/CC0 | 1/11/2026 | stima di cattura-ricattura ~1.800 targhe esistenti |

## 3. Il conto
Union massima delle fonti con termini chiari, con luogo: OSM 165 + Wikidata ~56 senza OSM + Commons ~141 punti nuovi (non verificati come targhe) = **circa 360 al massimo**, di cui con un soggetto leggibile (nome, iscrizione, Wikidata) meno di 200. Se si aggiungessero le 326 targhe di Pietre della Memoria, con sovrapposizioni si arriverebbe a ~600-650: **solo con un permesso scritto di ANMIG** (info@pietredellamemoria.it) e solo con guerra e Resistenza ben rappresentate (non milanesi in generale).

## 4. Cosa si puo' fare (decisione di Davide)
1. Lasciare le targhe dove sono: nel filone statue (218 lapidi) e nella pagina esistente.
2. Chiedere ad ANMIG/Pietre della Memoria il permesso di riuso dei campi fattuali (titolo, indirizzo, coordinate, data, tipo) con citazione. Con un si', la pagina e' fattibile ma sara' "le targhe di guerra e Resistenza" (326 targhe + 26 monumenti, 101 pietre gia' coperte).
3. Una pagina piccola solo con OSM+Wikidata: ~220 targhe, con la stima ~1.800 attesi: sarebbe una pagina "i dati aperti non sanno dove sono le targhe", gia' detta nel filone statue.

## 5. File
`raw/pdm/` (pagine elenco, NON per il repo: materiale con diritti riservati), `raw/osm/overpass_targhe.json`, `raw/commons/plaques_milan.json`, `raw/ckan_ricerca.json`. Programmi: `scripts/01_pdm_elenco.py`, `03_pdm_titoli.py`, `02_overpass.py`, `04_commons.py` (`python -I -X utf8 <programma> <percorsi assoluti>`).

## 6. AGGIORNAMENTO: pagina costruita con le sole fonti libere
Vedi STATO.md. Pagina `docs/targhe/index.html`: 228 targhe (OSM ODbL, Wikidata CC0, 10 foto Commons come metadati). Categorie con regole di parole (in `scripts/pagina.py`, lista `RULES`/`GR`/`KW2`), sesso solo da Wikidata P21 (3 donne su 80 persone, 3,8%), NIL per punto in poligono.
