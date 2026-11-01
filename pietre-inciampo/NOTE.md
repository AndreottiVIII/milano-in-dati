# Pietre d'inciampo di Milano - FASE 1 (raccolta, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web. Questi dati ricordano vittime: si parla di luoghi, anni, categorie, mai di classifiche di persone. Ogni numero dice file e campo (tra parentesi: `riepilogo.json` o il file). Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorsi assoluti>` (vedi STATO.md). Dati scaricati in `raw/` (non fidati, mai eseguiti), tabelle pulite in `pulito/`.

## 1. In breve

1. **Il Comune di Milano non pubblica le pietre come dati aperti**: 0 dataset su 10 parole chiave (CKAN). La fonte vera e' il sito del **Comitato per le Pietre d'inciampo di Milano** (pietredinciampomilano.it): una mappa con **262 punti** (coordinate incluse nella pagina) e **262 schede**, una per persona, con campi strutturati.
2. **Pietre totali in `pulito/pietre.csv`: 265** = 262 persone con scheda + 3 pietre per poliziotti della Questura (posate il 28/1/2025) che stanno solo su Wikipedia. Wikipedia ne conta 264 righe (3 poliziotti, ma manca Cesare Pistelli); la prima pietra e' del 19 gennaio 2017.
3. **Tutte le 262 persone con scheda risultano morte** (259 con "Morto a" nella scheda, 3 dall'iscrizione su Wikipedia): non ci sono pietre per sopravvissuti. 134 per motivi politici, 123 razziali, 5 internati militari italiani (IMI) (`categoria`, dal campo "Motivo dell'arresto").
4. **Posa per anno** (265 pietre): 2017: 6; 2018: 26; 2019: 30; 2020: 28; 2021: 31; 2022: 23; 2023: 26; 2024: 43; 2025: 31; 2026 (a oggi): 21 (`riep_anno_posa.csv`). Il 2024 e' alto per le 17 pietre di Cibeno posate il 14-15 novembre 2024 (vedi limiti dei dati).
5. **Dove**: 40 dei 88 NIL hanno almeno una pietra, 48 nessuna. Il NIL con piu' pietre e' Buenos Aires-Porta Venezia-Porta Monforte (36); rapportato agli abitanti (abitanti_2024 di `alberi/pulito/nil_alberi.csv`, NIL con almeno 5.000 abitanti; nella pagina) il primo e' Magenta-S. Vittore (25 pietre, 13,9 ogni 10.000 abitanti; media citta' 1,9; i numeri della fase 1 con abitanti_2023 davano 13,7) (`riep_nil.csv`).
6. **Cosa sorprende di piu'**: 108 delle 249 pietre con data di arresto nota (43%) ricordano un arresto avvenuto in soli due mesi, dicembre 1943 (retate degli ebrei dopo l'ordine di polizia del 30 novembre) e marzo 1944 (dopo gli scioperi); tutti gli altri mesi insieme ne contano 141. Su 227 con luogo di nascita noto, solo 73 (32%) sono nati a Milano.

## 2. Fonti, una per una (anche in `pulito/inventario.csv`)

### 2.1 Comune di Milano - dati.comune.milano.it (CKAN)
- Cercate 10 parole (pietre d'inciampo, pietre inciampo, stolpersteine, stolpersteine milano, deportati, deportazione, memoria, shoah, monumenti, lapidi): 0 risultati per le prime 9, 1 per "monumenti" (ds642, un indicatore "Osservatorio Milano - Citta' smart", non c'entra). `raw/search_ckan.json`.
- Quindi: nessun dato aperto sulle pietre. Le pagine "Milano e' memoria" del Comune sono comunicati stampa. Dal Comune uso solo i **civici** (ds634, 57.405 applicati, CC-BY, gia' su disco in `citta-15-minuti/raw/comune_milano/civici/estratto/`) e i **NIL** (ds964, 88 poligoni) per il controllo degli indirizzi e per assegnare il quartiere.

### 2.2 Comitato per le Pietre d'inciampo - Milano (pietredinciampomilano.it) - fonte principale
- `pietredinciampo.eu` (il dominio citato nell'incarico) rimanda al nuovo sito; vecchie pagine "portfolio" non piu' disponibili.
- Condizioni: `robots.txt` = `Disallow:` vuoto (tutto permesso). "Note legali" (pagina `?page_id=1378`): i dati sono responsabilita' del Comitato, che "concede libero accesso e diritto di riproduzione dei contenuti con l'esclusione di quelli coperti da copyright di altri". Non e' una licenza tipo CC e non dice se serve citare; le foto e i documenti sono spesso di terzi (es. Archivio CDEC). Scelta: riuso solo i **campi strutturati** (fatti) e cito la fonte; **non ripubblico i testi biografici ne' le immagini**, restano in `raw/`.
- Cosa c'e': la pagina "La mappa delle pietre" ha dentro uno script con 262 punti `[lon, lat, nome, id scheda]`; ogni scheda e' `?page_id=451&ricerca=N` (N = 1..262; 263-270 sono schede vuote). Campi: nome, nato (data, luogo), arrestato (luogo, data), morto (luogo, data), motivo dell'arresto (razziale / politica / internato militare italiano), anno di posa, detenzione, deportazione (tappe), trasporto, indirizzo della pietra, "Richiesta da" (solo 28 schede) + biografia.
- Scaricato 1 richiesta ogni 1,2 s, con User-Agent che dice chi siamo (`scripts/scarica_biografie.py`, `raw/biografie/N.html`, log `raw/download_biografie_log.csv`). Nessun login, nessun blocco.
- Cosa manca: **la data esatta di posa** (c'e' solo l'anno), il sesso (lo ricavo da Nato/Nata), l'esito per i sopravvissuti (non ce ne sono), luogo e data di morte per alcune schede.

### 2.3 Wikipedia it (CC BY-SA 4.0)
- Voci "Pietre d'inciampo a Milano" (revisione 2026-10-20T18:36Z) e "Pietre d'inciampo nel centro storico di Milano" (Municipio 1, revisione 2026-10-05), scaricate con l'API MediaWiki (`raw/wikipedia/*.json`). I template `{{pdi}}` hanno data di posa, luogo, coordinate (spesso solo per la prima pietra di un gruppo) e testo dell'iscrizione. 264 righe. Servono qui per la **data esatta di posa**, per controllare indirizzi e coordinate e per il Municipio. `pulito/wikipedia_pdi.csv` (tabella estratta) e `wikipedia_pdi_riempito.csv` (celle unite riempite) derivano dalla voce: **CC BY-SA 4.0, citare Wikipedia e gli autori della voce; se si ripubblicano, con la stessa licenza**. In `pietre.csv` entra della voce solo la data di posa, il municipio e (per 3 pietre) il nome.

### 2.4 Wikidata e OpenStreetMap (solo controllo)
- Wikidata (CC0), query SPARQL nel rettangolo di Milano per l'istanza "pietra d'inciampo" (Q26703203): **0 elementi**. `raw/wikidata/`.
- OpenStreetMap, Overpass, `memorial=stolperstein` o `memorial:type=stolperstein` nel rettangolo 45,38-45,57 N / 9,04-9,32 E: **26 nodi** (circa il 10% delle pietre; base OSM 1/11/2026 19:13Z). Licenza ODbL. Non fusi nei dati: solo per sapere che OSM e' molto incompleto. `raw/osm/`.

### 2.5 CDEC - Nomi della Shoah (solo controllo dei nomi)
- Il vecchio sito `nomidellashoah.it` **adesso mostra un sito di casino online** (dominio perso): non usarlo. Il CDEC pubblica i dati come Linked Open Data su `dati.cdec.it`, interrogabili con SPARQL a `lod.xdams.org/sparql` (il file "download data" e' vuoto: 79 byte). **Nessuna licenza trovata sulle pagine di dati.cdec.it** (una ricerca web parla di CC BY 4.0, non verificata): quindi li uso solo per un controllo, non ripubblico.
- Scaricati 8.946 persone (cognome, nome, anno di nascita, flag "sopravvissuto") in 400 finestre, 1 richiesta ogni 1,2 s (`raw/cdec/cdec_persone.csv`). Controllo con le 123 pietre "razziali": **107 trovate con stesso nome e anno di nascita, 4 solo per nome, 12 non trovate** (nomi stranieri o scritti diversamente, elenco in `pulito/controllo_cdec.json`). Nessuna delle 107 e' segnata "sopravvissuto" dal CDEC: coerente con "tutte morte". Il CDEC conta solo ebrei, quindi non controlla le pietre politiche.

## 3. Pulizia (`scripts/build.py`, risultati in `pulito/build_log.json`)

- `pulito/pietre.csv` (265 righe, `;`, UTF-8). Colonne principali: `id_scheda, nome, cognome, sesso, anno_nascita, data_nascita, luogo_nascita, data_arresto, luogo_arresto, eta_arresto, categoria (razziale/politica/IMI), sottogruppo, detenzione, deportazione, trasporto, luogo_morte, data_morte, eta_morte, campo_gruppo, esito, indirizzo, municipio, lon, lat, fonte_coord, id_nil, nil, anno_posa, anno_posa_comitato, anno_posa_conflitto, fonte_anno_posa, data_posa, richiesta_da, note_scheda, ... , fonte`. Le 3 pietre solo-Wikipedia hanno `solo_wikipedia = 1` e quasi tutti i campi vuoti.
- **Schede del Comitato con testo mancante** (difetto del sito): in 16 schede mancano le parole "Arrestato a ...", "Morto a ..." e restano date orfane (es. `Nato il 23/12/1917 a Milano il 08/09/1943 il 14/02/1945`). Le leggo cosi': prima data in piu' = arresto, seconda = morte; il luogo resta vuoto. Le 21 schede toccate hanno `note_scheda` compilata. Una scheda (Besso, IMI) non ha il campo "Nato": anno e luogo di nascita vuoti (il sesso viene da "Arrestato").
- **Wikipedia e le celle unite**: nelle tabelle `{{pdi}}` data e luogo valgono per piu' persone ("unito"); riempiti in avanti solo dove la cella dice "unito". L'abbinamento persona-riga e' per nome (239 uguali, 16 inclusi, 6 simili con ortografia diversa: Caielli/Cajelli, Heimann/Heiman, Marye Kuh/Kuth, Bergamaschi/Donino, Semmel, Sorias; 1 senza riga: Pistelli).
- **Coordinate**: dalla mappa del Comitato per tutte le 262. Controllo con i civici del Comune (indirizzo interpretato e abbinato per 246 su 262: 167 via esatta, 68 per iniziali/sottoinsieme ("L. Necchi"), 11 simile): distanza mediana mappa-civico 8 m, 90% entro 34 m, 8 oltre i 100 m, 3 oltre i 300 m. Corrette 2 (usato il civico perche' Wikipedia concorda col civico): scheda 124 (via Pinamonte da Vimercate, la mappa era 2,2 km fuori) e scheda 3 (via Leonardo Bruni, 302 m). Nel terzo caso (scheda 10, via Vespri Siciliani) il civico abbinato e' sbagliato (692 m) e mappa e Wikipedia concordano: tenuta la mappa. 16 indirizzi non abbinati ai civici (via non trovata, "angolo", senza numero), ma hanno coordinate della mappa.
- **NIL**: punto in poligono con i 88 NIL vigenti (`citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson`). 262 su 262 dentro un poligono, 0 fuori. Il NIL calcolato dal punto e quello del civico coincidono sempre (0 differenze su 246).
- **Categoria**: dal campo "Motivo dell'arresto". Sottogruppi (derivati, non nel sito): "strage di Cibeno" = morto al Poligono di Cibeno (Fossoli, 12/7/1944): 19; "arrestato a marzo 1944" (politici, probabile sciopero): 48 (31 nelle cui schede compare la parola "sciopero"). Il sito non ha un campo "scioperi": e' una mia ipotesi sulle date.
- **Campo** (`campo_gruppo`): luogo di morte; se manca, l'ultima tappa di "Deportazione". Raggruppato per nome (Auschwitz; Mauthausen con Gusen, Ebensee, Hartheim...; ecc.); 16 "altro" (marce della morte, sottocampi minori, Rodi).
- **Eta'**: differenza fra date complete (anni compiuti); solo dove ci sono entrambe.

## 4. Numeri principali (262 persone con scheda, salvo dove detto)

| Cosa | Numero | Da dove |
|---|---|---|
| Categoria | politica 134, razziale 123, IMI 5 | `categoria` |
| Genere | donne 66 (25%), uomini 196. Razziali: 60 donne su 123 (49%); politici: 6 su 134 (4%); IMI: 0 su 5 | `sesso` (Nata/Nato) |
| Eta' all'arresto (241 note) | mediana 41; 20 sotto i 18 anni (16 razziali, 4 politici); 51 sotto i 30; 32 da 60 anni in su. Mediana: razziali 44, politici 38,5, IMI 27,5 | `eta_arresto` |
| Eta' alla morte (220 note) | mediana 41 | `eta_morte` |
| Campo di morte | Auschwitz 104 (tutte razziali); Mauthausen e sottocampi 94 (90 politici); Poligono di Cibeno 19 (politici); Flossenburg 9; Ravensbruck 6; Bergen-Belsen 4; Dachau 3; Buchenwald 3; Gross-Rosen 2; Bolzano 1; Fossoli 1; altro 16 | `campo_gruppo` |
| Anno di morte (225 con data) | 1943: 14; 1944: 109; 1945: 102 | `data_morte` |
| Mesi di arresto piu' frequenti (249 con data) | marzo 1944: 55; dicembre 1943: 53; novembre 1943: 21; ottobre 1943: 20; febbraio 1944: 16 | `data_arresto` |
| Arrestati a Milano | 164 (politici 115 su 134; razziali 49 su 123: molti ebrei sono arrestati fuori Milano, per esempio a Tirano, Bormio, Como o alla frontiera svizzera, secondo le schede) | `luogo_arresto` |
| Nati a Milano | 73 su 227 con luogo noto; nati all'estero 33 (27 razziali): Gelibolu/Gallipoli (Turchia) 7, Bulgaria 4... | `luogo_nascita` |
| Indirizzi | 203 indirizzi distinti, 185 vie; 170 indirizzi con 1 pietra, 15 con 2, 11 con 3, 6 con 4, 1 con 5 (famiglie). Vie con piu' pietre: via dei Cinquecento 6, via delle Forze Armate 6, via De Togni 5 | `indirizzo` (`riep_vie.csv`) |
| Distanza dal Duomo | mediana 2,7 km (razziali 2,4; politici 2,9); 90 pietre entro 2 km | calcolata dalle coordinate |
| NIL | 40 con pietre / 48 senza. Razziali: 23 NIL, 51% nei primi 5 (Buenos Aires-Porta Venezia 25, Magenta-S.Vittore 18, De Angeli-Monte Rosa 8, Forze Armate 6, Duomo 6). Politici: 37 NIL, 33% nei primi 5 (Buenos Aires-Porta Venezia 11, Brera 10, Villapizzone-Cagnola-Boldinasco 8, XXII Marzo 8, Magenta-S.Vittore 7) | `riep_nil.csv`, `riepilogo.json` |
| Municipi (da Wikipedia, 264 righe) | M1 76 (con i 3 poliziotti), M3 49, M4 32, M7 25, M2 24, M8 23, M9 18, M6 9, M5 8 | `municipio` |
| Richiedente | indicato solo in 28 schede | `richiesta_da` |

"La cosa piu' sorprendente": vedi il punto 6 di "In breve". Candidate di riserva: 48 NIL su 88 non hanno nemmeno una pietra; il 25% sono donne ma quasi tutte nelle pietre razziali; 7 delle persone nate a Gelibolu (Gallipoli, Turchia) vivevano a Milano.

## 5. Limiti dei dati (da leggere prima di fare una pagina)

1. **Una pietra e' una richiesta, non un censimento.** Le pietre sono posate su domanda (famiglie, associazioni, scuole, Municipi) e sono 265 in tutto: non rappresentano proporzionalmente le vittime milanesi. Gli IMI sono 5 pietre a fronte di decine di migliaia di internati italiani morti; le donne politiche sono 6. Non scrivere "a Milano furono deportati X politici": scrivere "le pietre ricordano...".
2. **Anni di posa in conflitto (22), verificati il 1/11/2026.** Vedi sezione 7. Per 17 persone di Cibeno il Comitato scrive 2026, Wikipedia (fonte Fondazione Fossoli/ANED) 14-15 novembre 2024: usato Wikipedia. Altre 5 schede (45, 113, 119, 137, 201): 4 risolte con stampa, 1 resta 'da verificare'. Le pietre del 2026 sono 21 (a oggi) e non 39 come dicono le schede del Comitato.
3. **Wikipedia e' indietro e ha celle unite.** Il testo dice "264 pietre" (dati del 2024); le righe sono 264 ma includono 3 poliziotti e non Pistelli. La data posa e' comune a gruppi di righe: un'unione sbagliata sposta una persona di anno.
4. **Il sito del Comitato ha righe mancanti** (16 schede con date orfane, 21 con note): vedi 3. Nessun controllo di uguaglianza fra schede e Wikipedia per luoghi/date di arresto e morte (solo i nomi e le posizioni): quei campi vengono dal solo Comitato.
5. **"Qui abitava" non e' sempre l'ultima casa**: la posizione e' quella indicata dalla famiglia o dall'ente richiedente (a volte il posto di lavoro). Gli indirizzi possono essere stati rinumerati dopo la guerra: le coordinate sono quelle del sito, controllate coi civici di oggi.
6. **Il NIL non e' dove si e' arrestati**: dice dove sta la pietra oggi.
7. **Categoria "sciopero" e "Cibeno" sono derivate da me** (date e luogo di morte), non un dato del sito; la cifra 48 e' un limite superiore (i politici arrestati a marzo 1944 possono esserlo per altri motivi).
8. **CDEC**: dominio storico perso, nessuna licenza trovata, solo ebrei; il controllo per nome ha 12 mancanti per ortografia.
9. **OSM e Wikidata** coprono solo il 10% e 0%: non servono per questo lavoro.
10. I **testi delle biografie** e le foto non si ripubblicano (potrebbero avere diritti di terzi). Per una pagina meglio collegare la scheda del Comitato (`https://www.pietredinciampomilano.it/?page_id=451&ricerca=N`).

## 6. Cosa puo' mostrare una pagina (fase 2, non fatta)

- **Mappa** dei 262+3 punti, colori per categoria, filtro per anno di posa; zoom sul centro (90 pietre entro 2 km dal Duomo).
- **Posa nel tempo**: barre per anno 2017-2026 (con il picco 2024 spiegato).
- **I due mesi** (dicembre 1943 e marzo 1944) come grafico a barre per mese di arresto, con le due storie: la retata degli ebrei e gli operai degli scioperi.
- **Mappa del quartiere (NIL)**: pietre per 10.000 abitanti; confronto razziali / politiche; i 48 NIL senza pietre.
- **Dove sono finiti**: Auschwitz (104) contro Mauthausen (94) per categoria; anni di morte.
- **Eta'** in fasce (con rispetto: aggregato, mai il piu' giovane o il piu' anziano).
- **Famiglie**: indirizzi con piu' pietre (15 con 2, 11 con 3, ...).
- Nessuna classifica di persone; link alle schede del Comitato per chi vuole saperne di piu'.

## 7. Verifica dei 5 anni di posa in conflitto (1 novembre 2026)

Fonti consultate: AGI e Mentelocale (23/1/2025), Mosaico (gennaio 2020), Sky TG24 (novembre 2023), citydoormilano.it (elenco 2019 che riprende il Comitato), pagina Comune "Posa pietre d'inciampo 2023" (403 Forbidden: non leggibile da qui). Pagine salvate in `raw/verifica_anni/`.

| Scheda | Persona | Comitato | Wikipedia | Esito |
|---|---|---|---|---|
| 113 | Ugo Milla (via Natale Battaglia 41) | 2019 | 24/1/2020 | **2019** (elenco 2019 su citydoormilano.it; totali cumulati 62 a fine 2019, 90 dopo le 28 pietre del 15-17 gennaio 2020 secondo Mosaico: coincidono con i conteggi del Comitato) |
| 119 | Gino Emanuele Neppi (via Boscovich 30) | 2019 | 24/1/2020 | **2019** (stesse fonti) |
| 137 | Adriano Pogliaghi (via Zumbini 39) | 2022 | 23/1/2025 | **2025** (AGI 23/1/2025: tra le 14 posate quel giorno; Mentelocale: "posta giovedi' 23 gennaio 2025", la stampa scrive "Poliaghi") |
| 201 | Ezio Bortolotti (via Gadames 119) | 2026 | 13/3/2025 | **2025, "annunciato"** (Mentelocale di gennaio 2025 annuncia la posa del 13/3/2025; Wikipedia cita il Comune; nessuna cronaca della posa trovata) |
| 45 | Lucia De Benedetti (via Mozart 2) | 2023 | 25/1/2024 | **2023, "da verificare"**: Sky TG24 (novembre 2023) conta 171 pietre 2017-2023, uguale alla somma del Comitato con questa pietra, ma il Comitato stesso conta (a torto) Pogliaghi nel 2022; una ricerca web cita la pagina del Comune per il 2023 con "posa virtuale per lavori edili", non verificabile |

Nota: il totale 171 di Sky TG24 coincide col conteggio del Comitato anche includendo la pietra di Pogliaghi (che per la stampa e' del 2025): quindi quel totale non basta a decidere il caso 45. La tabella e' nello script `build.py` (`RISOLTI`).

## 8. Pagina web (fase 2, fatta il 1/11/2026)

`scripts/pagina.py` scrive `docs/pietre-inciampo/data/` (pietre.json/csv, nil.geojson/csv, riepilogo.json); la pagina e' `docs/pietre-inciampo/index.html` (scritta a mano, i numeri arrivano da riepilogo.json). Nella pagina: nome, anni di nascita e di morte, categoria, campo, anno di posa, indirizzo, coordinate e link alla scheda; niente biografie, foto, eta' o sesso delle singole persone; niente dati CDEC.
