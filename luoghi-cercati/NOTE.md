# I luoghi di Milano più cercati al mondo - FASE 1 (raccolta, pulizia, riepiloghi)

Scaricato il 1 novembre 2026 (ultimo mese completo: ottobre 2026). Niente pagina web, nessun giudizio. Ogni numero dice file e campo. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di luoghi-cercati> [<percorso assoluto di milano-in-dati>]` (vedi STATO.md). Dati grezzi in `raw/` (non fidati, mai eseguiti), tabelle pulite in `pulito/`.

"Cercati" qui vuol dire **letti su Wikipedia**: visualizzazioni (pageviews) degli articoli sui luoghi di Milano. Non sono visite, non sono ricerche su Google.

## 1. In breve

1. **1.802 elementi Wikidata** di Milano con coordinate e almeno un articolo Wikipedia (1.648 trovati con la catena "si trova nel territorio di" fino a Milano, 154 aggiunti da un controllo per distanza e confini; vedi 2). Di questi **1.527 sono "luoghi"** veri (edifici, chiese, piazze, parchi, stazioni, quartieri...), 95 istituzioni (università, ospedali, biblioteche), 3 opere d'arte, 177 non-luoghi (eventi, marchi, stati storici, enti). Tabella: `pulito/luoghi.csv`.
2. **8.154 coppie (luogo, edizione di Wikipedia)** in 201 lingue; per ognuna le visualizzazioni mensili da luglio 2015 a ottobre 2026 (136 mesi): **8.153 scaricate, 1 senza dati** (404: l'articolo telugu dell'Ultima Cena). 763.237 righe in `pulito/views_mensili.csv`.
3. **I luoghi di Milano hanno avuto 135,97 milioni di visualizzazioni in 11 anni e 4 mesi** (`riepilogo.json`, `views_totali_luoghi`), tutte le lingue. Il 53,7% in italiano, il 20,7% in inglese; le prime dieci lingue (it, en, de, fr, es, zh, ja, ru, pt, ar) fanno il 93,4%.
4. **Primo: lo stadio Giuseppe Meazza (San Siro), 16,67 milioni; secondo il Duomo, 15,80 milioni.** Seguono la Scala (5,61), il Castello Sforzesco (3,85), la Galleria Vittorio Emanuele II (3,71), il Bosco Verticale (3,14), Santa Maria delle Grazie (2,98), la Stazione Centrale (2,37).
5. **Il "Cenacolo" non è un luogo per Wikipedia**: l'articolo sul dipinto *Ultima Cena* ha 33,15 milioni di visualizzazioni (il doppio del Duomo) ma è un'opera, non un luogo. L'ho tenuto fuori dalla classifica dei luoghi e messo in `top60_non_luoghi.csv` con gli altri (Giochi olimpici 2026: 31,5 M; articolo "Milano": 46,4 M).
6. **Più della metà delle letture è in italiano, ma i grandi nomi sono stranieri**: lo stadio è 84% estero, il Duomo 76%, la Scala 75%, la Galleria 78%.
7. **Il Covid ha tolto un terzo delle letture (marzo 2020: -34%) e il ritorno ai livelli del 2019 è arrivato ad agosto 2022**; nel 2023 il massimo (15,05 M, +13% sul 2019). Dal 2024 scende, ma l'Italiano scende con tutta Wikipedia (vedi 5.3).
8. **Notre-Dame si vede**: il 15 aprile 2019 la voce italiana "Duomo di Milano" passa da circa 1.100 letture al giorno a 11.331, il 16 aprile a 17.292 (inglese 5.392 e 9.377). Date che coincidono col rogo (15 aprile 2019).
9. **Mappa per NIL**: tre quartieri fanno il 55% (Duomo 33,2%, Stadio-Ippodromi 12,8%, Brera 9,2%).

## 2. Come ho costruito l'elenco (fonte: Wikidata, CC0)

- **Quando e come**: 1/11/2026, endpoint SPARQL query.wikidata.org e API wbgetentities di wikidata.org. Programmi: `01_wikidata_luoghi.py`, `02_wikidata_sitelinks.py`, `03_elenco_luoghi.py`.
- **Query principale** (`raw/wikidata_items_classi.json`): elementi con `wdt:P131*` = Milano (Q490) e coordinate (P625), con le loro classi (P31): **4.406 elementi** (5.841 righe, una per classe). Di questi 1.648 hanno almeno un articolo Wikipedia (nelle 201 lingue) e le coordinate: sono la base.
- **Sitelink**: la query SPARQL sui sitelink va in timeout, quindi li ho presi con l'API `wbgetentities` (50 elementi alla chiamata, `raw/sitelinks_blocchi/`, riassunto `raw/wikidata_sitelinks.json`; 12.319 sitelink su 4.793 elementi).
- **Controllo di completezza**: la catena P131 non è sempre scritta. Query `wikibase:around` entro 12 km dal Duomo (`raw/wikidata_raggio12km.json`, 387 elementi con voce it.wikipedia fuori dalla catena); tengo solo quelli con coordinate **dentro i confini dei 88 NIL** (+30 m): **154 aggiunti** (8,5% dell'elenco finale; es. Naviglio Grande, Naviglio della Martesana, Olona). Per loro ho preso tutti i sitelink (non solo italiano).
- **Senza coordinate**: 326 elementi con voce italiana e catena P131 su Milano non hanno P625 (`raw/wikidata_senza_coordinate_count.json`). Guardati i 40 con più edizioni (`wikidata_senza_coordinate_top.json`): dipinti, reti di trasporto, case editrici, eventi; unica assenza da luogo di rilievo le "mura di Milano". Non li ho inclusi.
- **Rumore**: la catena P131* include Milano stessa (Q490) e qualche altro comune (es. Bresso, Q42898): esclusi a mano (`categorie_manuali.csv`).
- **Licenza**: Wikidata, dati strutturati CC0 (pagina Wikidata:Licensing: "All structured data ... is released into the public domain under Creative Commons Zero"; letta il 1/11/2026).

### 2.1 Categorie e "tipo"
- `categoria` (`luoghi.csv`): derivata dalle etichette inglesi delle classi P31 con regole in ordine di priorità (`03_elenco_luoghi.py`, lista CAT): chiesa_religioso 264, edificio_palazzo 415, quartiere 182, stazione 150, parco_verde 112, monumento_arte 95, museo 79, strada 53, teatro_cultura 50, castello_difesa 49, piazza 28, stadio_sport 25, canale_acqua 25, e così via.
- `tipo`: **luogo** (1.527), **istituzione** (95: università, scuole, ospedali, biblioteche; l'articolo è sull'ente, non sul posto), **opera** (3: Ultima Cena, Sposalizio della Vergine, Pietà Rondanini), **non_luogo** (177: eventi, marchi, stati storici, enti territoriali, Municipi, reti di trasporto, la città intera, Mediolanum).
- **Correzioni a mano**: 43 voci nei primi posti, in `scripts/categorie_manuali.csv` (qid, categoria, tipo, motivo). Es.: Bottega Veneta, Moncler, Loro Piana, Miu Miu (marchi con la sede come coordinata); Repubblica Cisalpina, Ducato di Milano (stati storici); Expo 2015, strage di piazza Fontana (eventi). **Le voci sotto i primi 330 posti non le ho riviste una per una**: possono esserci ancora errori di categoria.
- Le voci duplicate per lo stesso posto non sono unite: es. la chiesa di Santa Maria delle Grazie (Q244952, 2,98 M) e la voce Unesco "Chiesa di Santa Maria delle Grazie e Convento dei Domenicani con l'Ultima Cena" (Q11349456, 0,21 M); la stazione metro "Duomo" (Q2519375, 0,15 M) è separata dal Duomo.
- **NIL**: punto in poligono con i 88 NIL vigenti (`../citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson`, Comune di Milano CC-BY): 1.792 dentro, 2 entro 150 m (assegnati al più vicino), 8 fuori (non assegnati: sono luoghi sul confine o fuori comune). Per i grandi oggetti (parchi, canali) conta solo la coordinata di Wikidata.

## 3. Come ho scaricato le visualizzazioni (fonte: Wikimedia REST API, CC0)

- Endpoint: `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{lingua}.wikipedia/all-access/user/{titolo}/monthly/2015070100/2026103100`; `agent=user`, `all-access`. Dal 1/11/2026. Titolo = quello di Wikidata (titolo attuale). User-Agent: `MilanoInDati/1.0 (https://github.com/AndreottiVIII/milano-in-dati)`.
- **Limite**: a 10 richieste al secondo l'API risponde 429 (Too Many Requests, intestazione `retry-after`). Ho ridotto a **4 richieste/s** con 8 fili e pausa globale sul `retry-after` (`04_pageviews.py`; 249 risposte 429 gestite). Ogni risposta salvata in `raw/pageviews_mensili/<lingua>/<qid>.json` (riprendibile), 230 MB in tutto `raw/`.
- **Giornalieri** (`06_giornalieri_redirect.py`): luglio 2015 - ottobre 2026, in it e en, per i primi 60 luoghi/opere (`raw/pageviews_giornalieri/`). Servono a datare i picchi.
- **Riferimento Wikipedia intera** (`06b_aggregato_wikipedia.py`): totale mensile di tutte le visualizzazioni (user, all-access) delle 10 Wikipedia principali, endpoint `aggregate` (`raw/aggregato_wikipedia/`).
- **Licenza**: l'indice dei dataset Analytics di Wikimedia dice "All Analytics datasets are available under the Creative Commons CC0 dedication" (dumps.wikimedia.org/other/pageviews/readme.html, letto il 1/11/2026). **Attenzione**: la pagina radice della REST API dice invece che, se non indicato altrimenti, i contenuti ottenuti dall'API sono CC-BY-SA 3.0 e GFDL. I conteggi sono gli stessi dei dataset Analytics (CC0), ma conviene citare "Wikimedia Foundation, Pageviews API" in ogni caso.

## 4. Pulizia (`05_pulizia.py`, controlli in `pulito/controllo_pulizia.json`)

- Tutti i file letti: 8.154, nessuno illeggibile; 1 risposta 404; 763.237 righe mensili, da 2015-07 a 2026-10.
- **L'API non restituisce i mesi con 0 visualizzazioni**: un mese assente nel file = 0 (o articolo non ancora esistente). Non ho riempito gli zeri in `views_mensili.csv`.
- Tabelle: `views_mensili.csv` (qid;nome;lingua;mese;views), `totali_luogo.csv` (un record per luogo: totale, per ognuna delle 10 lingue principali, altre lingue, quota italiano, primo/ultimo mese, mese di picco, NIL, coordinate, tipo, categoria), `totali_lingua.csv`.

## 5. Riepilogo (`07_riepilogo.py`, `08_approfondimenti.py`; numeri in `riepilogo.json`, `approfondimenti.json` e nei csv)

### 5.1 I luoghi più letti (tipo = luogo; `top100_luoghi.csv`)
| # | Luogo | Totale | di cui it | Estero |
|---|---|---|---|---|
| 1 | stadio Giuseppe Meazza (San Siro) | 16,67 M | 15,9% | 84% |
| 2 | Duomo di Milano | 15,80 M | 24,2% | 76% |
| 3 | Teatro alla Scala | 5,61 M | 25,4% | 75% |
| 4 | Castello Sforzesco | 3,85 M | 31,0% | 69% |
| 5 | Galleria Vittorio Emanuele II | 3,71 M | 21,9% | 78% |
| 6 | Bosco Verticale | 3,14 M | 39,5% | 60% |
| 7 | chiesa di Santa Maria delle Grazie | 2,98 M | 28,3% | 72% |
| 8 | stazione di Milano Centrale | 2,37 M | 41,1% | 59% |
| 9 | Pinacoteca di Brera | 1,98 M | 39,9% | 60% |
| 10 | basilica di Sant'Ambrogio | 1,87 M | 60,5% | 40% |
| 11 | piazzale Loreto | 1,68 M | 39,8% | 60% |
| 12 | CityLife | 1,36 M | 73,4% | 27% |
| 13 | Torre Velasca | 1,23 M | 66,7% | 33% |
| 14 | Grattacielo Pirelli | 1,23 M | 56,8% | 43% |
| 15 | piazza del Duomo | 1,16 M | 28,5% | 71% |
| 16 | cimitero Monumentale | 1,11 M | 48,7% | 51% |
| 17 | Santa Maria presso San Satiro | 0,92 M | 65,8% | 34% |
| 18 | Arco della Pace | 0,87 M | 69,9% | 30% |
| 19 | Torre Isozaki | 0,70 M | 74,9% | 25% |
| 20 | Palazzo Reale | 0,67 M | 39,0% | 61% |
Fonte: `totali_luogo.csv`, campi `views_totali` e `quota_italiano_%` (lug 2015 - ott 2026). I primi 10 fanno il 42,6% di tutte le letture dei luoghi, i primi 20 il 50,7%. 196 luoghi superano le 100.000 letture, 16 il milione.
- Per tipo: quartieri 10,7 M (CityLife 1,36; Quarto Oggiaro 0,38; Baggio 0,32; Quadrilatero della moda 0,30; Gratosoglio 0,29), stazioni 11,6 M (Centrale 2,37; Porta Garibaldi 0,60; Cadorna 0,31), parchi/cimiteri 4,2 M (Monumentale 1,11; Sempione 0,57; Monte Stella 0,29), chiese 30,3 M (22% del totale), stadi e palasport 19,0 M (14%). `per_categoria.csv`.
- **Cosa cerca il mondo per lingua** (`top20_per_lingua.csv`): it: Duomo 3,83 M, stadio 2,64, Scala 1,43, Bosco Verticale 1,24, Castello 1,20. en: **stadio 5,24 M, Duomo 4,39**, Galleria 1,50, Scala 1,25, Bosco Verticale 1,00; piazzale Loreto 7º con 0,62. de: stadio 1,53, Bosco Verticale 0,39, Scala 0,35, Galleria 0,32. fr: **Duomo 0,95**, stadio 0,89, Scala 0,36. es: stadio 1,57, Duomo 1,31, Castello 0,32. ru: **Duomo 0,99**, stadio 0,69, Scala 0,60. zh: **Duomo 0,42** (stadio solo 0,12), Santa Maria delle Grazie 0,10, Galleria 0,10. ja: stadio 0,51, Duomo 0,45, Santa Maria delle Grazie 0,26 (+0,21 la voce Unesco). pt: stadio 0,57, Duomo 0,45. ar: stadio 0,39, Duomo 0,18.
- **Navigli**: Naviglio Grande 0,51 M (68% it), Martesana 0,33, Pavese 0,17, Cerchia dei Navigli 0,12; la Darsena 0,17. Il "luogo Navigli" non ha una voce sola.

### 5.2 Italiano e estero
- Tutti i luoghi: italiano 53,7%, inglese 20,7%, tedesco 4,2%, spagnolo 4,0%, francese 3,7%, russo 2,9%, giapponese 1,6%, polacco 1,2%, portoghese 1,0%, cinese 1,0% (`riepilogo.json`, `quota_lingua_%`). Estero = tutto tranne italiano: 46,3%.
- Per categoria: quota italiana più bassa negli stadi (21,7% it), nei castelli e porte (41,6%), nelle chiese (43,2%), nei teatri (43,2%); più alta nei canali (85,6%), quartieri (81,3%), parchi (75,1%) (`it_vs_estero_per_categoria.csv`).
- Luoghi con almeno 200.000 letture, i più stranieri: Santa Maria delle Grazie voce Unesco (0% it), Porta Nuova (0,09% it: manca la voce italiana del quartiere), Unipol Dome (8,7%), stadio (15,9%), Galleria (21,9%), Porta Sempione (22,3%), Duomo (24,2%), Scala (25,4%). I più italiani: carcere di Opera (99,97%), Derby Club (99,2%), piazza Gae Aulenti (97,2%), Leoncavallo (96,1%), Isola (95,4%), Seveso (95,2%).
- **Attenzione**: lingua non è nazionalità. L'inglese è letto anche dagli italiani, lo spagnolo è soprattutto americano. Dove manca la voce italiana (es. Porta Nuova), la quota italiana è bassa per costruzione.

### 5.3 Andamento 2015 -> oggi (`serie_annuale_totale.csv`, `luoghi_vs_wikipedia_annuale.csv`)
Totale luoghi (milioni): 2016 10,96; 2017 10,93; 2018 12,23; **2019 13,31**; **2020 10,26 (-23% sul 2019)**; 2021 10,88; 2022 12,45; **2023 15,05 (+13%)**; 2024 13,40; 2025 12,49; 2026 (gen-ott) 8,99. 2015 è parziale (lug-dic, 5,01 M) e 2026 lo è (10 mesi): non confrontare con anni interi.
- **Covid**: marzo 2020 -34% su marzo 2019 (italiano -32%, estero -36%); aprile -19% (italiano -29%, ma estero solo -5% per il picco del Duomo il giorno di Pasqua); giugno 2020 -34% (estero -51%). Il totale mensile torna stabilmente (3 mesi di fila) sopra lo stesso mese 2019 da **agosto 2022** (estero agosto 2022, italiano dicembre 2022).
- **Il 2023 è gonfiato dallo stadio** (maggio 2023: semifinali di Champions Milan-Inter, 908.000 letture in un mese contro 148.000 nei mesi vicini). Senza lo stadio: 2019 11,84 M, 2023 12,33 M (+4%), 2025 10,80 M (-9%) (`approfondimenti.json`, `serie_annuale_senza_meazza`).
- **Estero** cresce, **italiano** cala: 2025 contro 2019, estero +12%, italiano -20% (indici 111,7 e 80,0). Gen-ott 2026 contro gen-ott 2025: totale -15,5%, italiano -19,1%.
- **Ma tutta Wikipedia scende**: la Wikipedia italiana ha 6,46 miliardi di letture nel 2019 e 5,13 nel 2025 (-21%). Letture dei luoghi di Milano ogni milione di letture della Wikipedia italiana (`luoghi_vs_wikipedia_annuale.csv`, campo `per_milione`): 1.158 (2019), 879 (2020), 1.315 (2023), 1.167 (2025), 1.102 (2026 gen-ott). **Normalizzato, l'italiano nel 2025 è quasi uguale al 2019.** In inglese: 28,4 (2019) -> 33,3 (2025) -> 36,1 (2026): l'inglese guadagna davvero. Nel Covid la Wikipedia italiana *saliva* (+5% nel 2020) mentre i luoghi di Milano perdevano.
- **Stagionalità** (primi 20 luoghi, 2016-2019, quota per mese; `approfondimenti.json`): maggio 10,9%, aprile 9,3%, ottobre 9,1%, novembre 8,8%; luglio 6,7% e giugno 7,4% i più bassi. Maggio sale a 10,9% anche per i picchi dello stadio (finale 2016); senza lo stadio i primi mesi sono aprile 9,6%, ottobre 9,3%, maggio 9,0%, novembre 8,9% e i più bassi luglio 6,9% e giugno 7,4%.

### 5.4 Picchi e gli eventi dietro (`picchi_giornalieri.csv`, `picchi_mensili.csv`)
Metodo: un giorno è un picco se ha almeno 2.000 letture e 4 volte la mediana dei 28 giorni prima; un mese se ha almeno 5.000 letture e 3 volte la mediana dei 6+6 mesi attorno. Gli eventi sono scritti solo dove la **data coincide chiaramente**; l'evento lo conosco io, non l'ho verificato con una fonte in questa fase: **da verificare con fonte prima di pubblicarlo**.
- **15-16 aprile 2019, Duomo di Milano**: it 11.331 e 17.292 contro 1.109 di mediana; en 5.392 e 9.377 contro 1.060. Eccesso 15-21 aprile: 35.060 (it) + 21.204 (en) = circa 56.000. Coincide col rogo di Notre-Dame (15 aprile 2019). Probabile causa: la parola "Duomo" cercata dagli italiani per la cattedrale parigina (ipotesi mia).
- **28 maggio 2016, stadio (en)**: 88.859 letture in un giorno (mediana 2.016). Finale di Champions League a San Siro. Maggio 2016: 676.724 in un mese (mese più alto dopo maggio 2023).
- **10 e 16 maggio 2023, stadio (en)**: 93.999 e 40.131. Semifinali Milan-Inter. Maggio 2023: 907.836, il record assoluto di un mese per un luogo.
- **6 maggio 2025, stadio (en)**: 33.261. Semifinale Inter-Barcellona a San Siro. **16 febbraio 2022** (18.569): Inter-Liverpool.
- **24 giugno 2019, stadio (en)**: 23.470 (mediana 740): giorno dell'assegnazione a Milano-Cortina dei Giochi invernali 2026.
- **6 febbraio 2026, stadio (en)** 30.131, il 7 21.874: cerimonia di apertura dei Giochi olimpici a San Siro. Febbraio 2026: **Unipol Dome** 110.856 in un mese (mediana 5.939), **Villaggio Olimpico** 49.127, **Arco della Pace** 53.745, Porta Sempione 20.166: sedi e luoghi olimpici.
- **12-13 aprile 2020, Duomo (en)**: 53.638 e 23.987 (mediana 811). Pasqua 2020, concerto di Andrea Bocelli nel Duomo vuoto.
- **21-23 agosto 2025, Leoncavallo (it)**: 60.768, 43.605, 19.260 (mediana 50). Sgombero del centro sociale. Agosto 2025 152.856 (52 volte la mediana).
- **Ottobre 2015**: Albero della Vita 29.448 e Padiglione Zero di Expo 27.700 (mese; Expo chiude il 31 ottobre 2015).
- **Gennaio 2018, 2019, 2023, Memoriale della Shoah**: 21.484, 15.827, 21.634 in un mese: Giorno della Memoria (27 gennaio); coincidenza di mese, non verificata sul giorno.
- **Giugno 2020, monumento a Indro Montanelli**: 18.563 (mediana 248): mese dell'imbrattamento della statua (coincidenza di mese).
- **Gratosoglio, febbraio 2019, 2022, 2024**; **Baggio, febbraio 2024**: 20.000+ in un mese, 9-11 febbraio 2024 sia Gratosoglio sia Baggio. Sempre nelle settimane del Festival di Sanremo. Ipotesi mia, non verificata: cantanti legati ai quartieri.
- **Non spiegati**: Ultima Cena it, 6 aprile 2021 (100.096, giorno solo); Grattacielo Pirelli it, 31 gennaio 2018 (17.320); Torre Branca aprile-maggio 2026 (37.401, 24 volte la mediana); Seveso ottobre-novembre 2023 (25.685); carcere di Opera gennaio 2023 (32.408).
- **Ultima Cena (non luogo)**, en, 27-31 luglio 2024: 42.909, 56.740, 45.677, 33.442, 23.125: i giorni dopo la cerimonia di apertura delle Olimpiadi di Parigi (26 luglio 2024) con la scena ispirata al dipinto (mio ricordo, da verificare).
- **Dibattito sulla demolizione di San Siro**: **nessun picco che coincida chiaramente**. Il 2025-09 (150.133) è il doppio di luglio/agosto, ma settembre 2024 (148.481) ha lo stesso salto: è l'inizio del campionato. Non lo attribuisco al dibattito.

### 5.5 Mappa per NIL (`views_per_nil.csv`, `mappa_nil.png` solo di controllo)
88 NIL con almeno un luogo. **Duomo 45,09 M (33,2%) con 394 luoghi, Stadio-Ippodromi 17,34 M (12,8%) con 14 luoghi, Brera 12,45 M (9,2%, 172 luoghi), Magenta-San Vittore 5,67 M, Stazione Centrale-Ponte Seveso 4,95 M, Porta Garibaldi-Porta Nuova 4,37 M, Isola 3,82 M (Bosco Verticale), Parco Sempione 3,61 M, Guastalla 3,44 M, Tre Torri 3,43 M (CityLife)**. I primi tre fanno il 55,1%. 8 elementi dell'elenco (2 di tipo luogo) non hanno NIL perché cadono fuori da tutti i poligoni. Non è "dove stanno le cose": è dove cade la coordinata del luogo (Brera comprende la Scala e la Pinacoteca).

### 5.6 La cosa più sorprendente
**San Siro batte il Duomo: lo stadio ha più letture della cattedrale (16,7 M contro 15,8 M), per quattro quinti dall'estero, e un solo mese di semifinali (maggio 2023, 908.000) vale più di sei mesi del Duomo.** Chi cerca Milano nel mondo, in inglese, tedesco, spagnolo, portoghese, giapponese e arabo, cerca prima il calcio. Il Duomo vince solo in italiano, francese, russo e cinese. Seconda sorpresa: il Bosco Verticale (2014) è sesto, davanti a Pinacoteca di Brera e Sant'Ambrogio, e in tedesco è secondo.

## 6. Limiti dei dati

1. **Visualizzazioni ≠ visite**. Una persona può leggere dieci volte; lo studente che prepara l'esame e il turista che prenota sono contati uguali. Il carcere di Opera (464.000, 99,97% italiano) e il Leoncavallo dicono "cronaca", non "turismo".
2. **Bot**: `agent=user` esclude i bot dichiarati, non quelli che si fingono utenti. Non ho prove di traffico automatico, ma i picchi senza evento (vedi 5.4, "non spiegati") possono esserlo.
3. **Titoli e redirect**: ho scaricato solo il titolo attuale di Wikidata. Le letture arrivate tramite un redirect (vecchio titolo, minuscole, sigle) non sono contate. Controllo sui primi 62 luoghi della Wikipedia italiana (`raw/redirect_it/`, `redirect_it_riepilogo.csv`): i redirect valgono in totale il 5,3% delle letture del titolo attuale (mediana 0,95%), ma pochi casi pesano molto: **Torre UniCredit** (redirect "Torre_Unicredit" 536.873 contro 148.220 del titolo), **Unipol Dome** (Arena Santa Giulia 130.573 contro 28.855), **Cimitero Monumentale** (59%), Palazzo Reale (36%), Torre Isozaki (Torre Allianz, 17%), Bosco Verticale (10,6%). Per queste voci il totale è sottostimato. Non controllati i redirect delle altre lingue né i luoghi dopo il 62º. Eventuali spostamenti di pagina (rinomine) non emergono dal registro: non li ho trovati con certezza; il confronto dei redirect è l'unico indicatore.
4. **I mesi a zero non esistono nel file** (vedi 4): un luogo "senza dati" in un mese ha 0 letture, non un dato mancante.
5. **Wikipedia nel suo insieme cala** (-21% in italiano dal 2019 al 2025): confrontare sempre con `luoghi_vs_wikipedia_annuale.csv` prima di dire che "Milano interessa meno".
6. **Mix di cose diverse**: articoli su opere (Ultima Cena), marchi, eventi, istituzioni sono staccati dai luoghi con regole e con 43 correzioni a mano; fuori dai primi 330 posti ci possono essere errori. Le università e gli ospedali sono "istituzione", non "luogo": Bocconi 2,85 M, Politecnico 2,17 M, Statale 1,80 M, Cattolica 1,55 M.
7. **Un luogo, più voci**: Navigli (4-5 voci), Santa Maria delle Grazie (2), stazioni (metro e ferrovia), Piazza del Duomo e Duomo. Non unite.
8. **Il perimetro dipende da Wikidata**: P131 mancante (154 luoghi recuperati col controllo per distanza), nessuna coordinata (326 voci escluse), classi mancanti ("senza_classe" 1). Altri luoghi di Milano senza una voce Wikipedia non ci sono.
9. **Lingua ≠ nazionalità** (5.2).
10. **Periodi parziali**: 2015 (da luglio) e 2026 (fino a ottobre).
11. **Rate limit**: a 10 richieste al secondo l'API dà 429; sotto i 4/s va senza problemi. Un nuovo scarico completo richiede circa 35 minuti.
12. **Licenza**: Wikidata CC0; pageviews CC0 secondo la pagina dei dataset Analytics, ma CC-BY-SA/GFDL secondo l'intestazione della REST API (vedi 3). I titoli delle voci sono fatti; non riproduco testi di Wikipedia.

## 7. Cosa potrebbe mostrare una pagina

- **Classifica** dei primi 20 luoghi con barra italiano/estero e sparkline 2015-2026; selettore per lingua ("cosa cerca la Spagna / il Giappone / la Cina").
- **San Siro contro Duomo** con i picchi annotati: finali di Champions (2016, 2023, 2025), assegnazione e Olimpiadi 2026, e il Duomo con Notre-Dame (aprile 2019) e Pasqua 2020.
- **Linea del tempo** del totale dei luoghi con Covid e ripresa, e il confronto per milione di letture di Wikipedia (italiano stabile, inglese in crescita).
- **Mappa per NIL**: letture totali (Duomo 33%, Stadio 13%, Brera 9%) e il "luogo più letto" del quartiere; quartieri più cercati (CityLife, Quarto Oggiaro, Baggio, Gratosoglio) e i più "italiani".
- **I più stranieri / i più italiani**; la nota "il Cenacolo è un dipinto" con le sue 33 milioni di letture.
- Limiti evidenti sulla pagina: letture non visite, solo Wikipedia, redirect non contati, eventi da verificare.

## 8. Cosa non ho fatto

Nessuna pagina, nessun grafico per la pubblicazione (c'è solo `mappa_nil.png` di controllo). Non ho verificato gli eventi con fonti giornalistiche. Non ho controllato i redirect fuori da it.wikipedia né oltre il 62º luogo; non ho riletto tutte le categorie oltre il 330º posto. Niente confronto con altri dati (Google Trends, biglietti, accessi veri). Nessun account creato.
