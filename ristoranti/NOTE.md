# Cosa si mangia a Milano - FASE 1 (freschezza, copertura, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web, nessun giudizio. Ogni numero dice file e campo. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di ristoranti> <percorso assoluto di milano-in-dati>` (ordine e dettagli in STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle in `pulito/`.

## 1. VERDETTO: dati aggiornati, con riserve

Regola di Davide: "aggiornato" se (A) il registro del Comune è stato aggiornato negli ultimi ~12 mesi, OPPURE se (B) almeno il 60% dei locali OpenStreetMap (OSM) è stato modificato negli ultimi 3 anni E OSM e registro concordano entro ~20% in quasi tutti i NIL.

| Prova | Risultato | Esito |
|---|---|---|
| A. Registro del Comune: data di aggiornamento | I file CSV/GeoJSON di ds58, ds59, ds250 sono stati ricaricati il 24 e il 31/8/2026 (CKAN `resource.last_modified`, 62 giorni fa); frequenza dichiarata ANNUAL; licenza CC-BY | PASSA alla lettera |
| A'. Il registro è davvero cambiato? | Una copia del 19/7/2019 (Wayback) aveva lo stesso hash di quella del 6/5/2024 nell'indice Wayback (cioè non è stato aggiornato per 5 anni); oggi: dei 9.044 codici del 2019, 6.689 restano, 2.355 non ci sono più, 2.580 sono nuovi; i codici "PE" arrivano a 32.586 (nel 2019 a 29.144: +3.442 pratiche) | Sì, rinnovato |
| A''. Il registro dice a che data è fotografato? | NO. Nessuna colonna di data in ds58/ds59/ds250 (solo codice, indirizzo, tipo, superficie). Il "62 giorni" è la data di caricamento, non la data dei dati | Riserva |
| B1. OSM modificato di recente | 70,3% dei 6.637 locali (6 tipi) modificati negli ultimi 3 anni (60,1% in 2; 40,8% in 1 anno; mediana 1,27 anni). Soglia 60% | PASSA |
| B2. OSM vs registro per NIL | OSM = 72,4% del registro "in piano" (6.637 contro 9.166). Solo 24 NIL su 88 entro ±20%, 42 entro ±30%, 69 entro ±50%; mediana -27%. Correlazione tra NIL 0,985 | NON PASSA alla lettera |

Quindi: passa A (alla lettera) e B1, non passa B2. Sostanza: **i dati sono abbastanza freschi per una fotografia "oggi" della città** (OSM ha 40,8% dei locali toccati nell'ultimo anno e 714 locali con `check_date` negli ultimi 12 mesi; il registro è ricaricato da poco e contiene il 92-94% dei locali nuovi mappati nel 2025-26), **ma il registro non dice la data dei dati e non toglie in fretta i locali chiusi**, e OSM ne conta il 28% in meno del registro ovunque. Vedi le riserve in 5.

## 2. Fonti, una per una

### 2.1 OpenStreetMap - ODbL 1.0, "© OpenStreetMap contributors"
- Overpass API (overpass-api.de), una richiesta: `nwr["amenity"~"restaurant|fast_food|cafe|bar|pub|ice_cream|biergarten|food_court"]` dentro la relazione 44915 (Comune di Milano), `out meta center`. Stato del database: 1/11/2026 19:27 UTC. 6.647 elementi (6.575 nodi + 72 poligoni ridotti al centro). `raw/osm/osm_milano_food_overpass.json` [scripts/download_osm.py]. I primi due tentativi (502 e timeout) sono falliti; il terzo è andato in 38 secondi.
- Controllo indipendente: estratto Geofabrik nord-ovest del 31/10/2026 (594 MB, `raw/geofabrik/`) letto con pyosmium e tagliato sull'unione dei poligoni NIL: 6.646 elementi, praticamente gli stessi [scripts/extract_pbf.py]. Nota: gli estratti pubblici Geofabrik NON hanno `uid` né `changeset` (valgono 0): chi ha modificato si vede solo da Overpass.
- Locali segnati chiusi (`disused:amenity`, `was:amenity`...): 100, da pbf [scripts/extract_closed.py].
- Cosa NON c'è: elementi di tipo relazione (multipoligoni) non sono nell'estratto; negozi di cibo (`shop=bakery`, `shop=pastry`...) non scaricati; pizzerie e kebab da asporto spesso sono `amenity=fast_food`.

### 2.2 Comune di Milano, dati.comune.milano.it (CKAN) - CC-BY ("Comune di Milano - dati.comune.milano.it")
Ricerca con 30 parole chiave, 519 dataset: `raw/search_ckan.json` [scripts/search_ckan.py]. Quelli utili:

| Dataset | Righe | Cosa | Data nel file |
|---|---|---|---|
| ds58 pubblici esercizi **in piano** (bar, ristoranti, pub: somministrazione come attività primaria) | 9.269 (103 senza coordinate) | codice pratica, indirizzo, tipo (lettere a-i in `denominazione_pe`), insegna (solo 24%), superficie, NIL, coordinate | NESSUNA |
| ds59 pubblici esercizi **fuori piano** (circoli, stadi, mense, stazioni, musei...) | 3.799 (297 senza coordinate) | idem, ma non sono ristoranti veri | NESSUNA |
| ds250 artigianato alimentare (gelaterie, pizza da asporto, kebab, gastronomie) | 1.471 (27 senza coordinate) | tipo in testo libero, ATECO (mancante nel 44%) | NESSUNA |
| ds2954 attività commerciali, serie storica (conteggi) | tabella | in piano attivi: 9.417 (2023), 9.296 (2024); fuori piano 3.671 e 3.743. Finisce al 2024 | anno |
| ds202 aperture/chiusure 2018 | - | procedimenti 2018, vecchio | 2018 |
| ds612 attività storiche | - | negozi storici riconosciuti dalla Regione, aggiornato 19/10/2026, CC0 | - |
Scaricati anche ds251 panificatori e ds252 pubblico spettacolo (non usati). Cronologia delle modifiche CKAN in `raw/activity_*.json`. Copia 2019 di ds58: `raw/wayback/ds58_2019.csv`.

Il registro NON ha: cucina (sushi, kebab...), data di apertura/chiusura, nome nel 76% dei casi. La "cucina" si ricava solo da OSM.

## 3. Numeri della freschezza di OSM (`pulito/freschezza_osm.csv`, `freschezza.json`)
- 6.637 locali nei 6 tipi (ristorante 2.926, caffè 1.822, fast food 851, bar 617, gelateria 222, pub 199); 9 altri (food court, biergarten).
- Ultima modifica per anno: 2023 483, 2024 584, 2025 1.755, 2026 (fino al 31/10) 2.169; solo 359 locali (5,4%) fermi a prima del 2017 (686, il 10%, a prima di novembre 2018).
- Con `cuisine`: 42,3% di tutti; 65,3% dei ristoranti; 81,2% dei fast food; 68,9% di ristoranti+fast food. Con `opening_hours` 22,9%; con indirizzo (via+civico) 57,6%; con nome 96,4%; con sito o telefono 39,9%.
- `check_date`/`survey:date` (verifica esplicita) 22,7%; negli ultimi 3 anni 20,4%; per anno: 2023 115, 2024 148, 2025 549, 2026 641.
- **La freschezza dipende da pochi mappatori**: delle modifiche 2025-26 (3.924 locali) il 33,1% è di un solo utente, il 62,0% dei primi 5, il 74,7% dei primi 10 (263 utenti in tutto). Senza i primi 5 utenti la quota "modificati in 3 anni" scenderebbe da 70,3% a 31,7%. Il ritmo è però costante: tra gennaio e ottobre 2026 tra 149 e 313 locali modificati al mese (`controlli.json`).
- "Ultima modifica" non è "verificato": include correzioni di massa, indirizzi, tag. Per questo conta di più `check_date`.

## 4. Confronto OSM vs registro (`pulito/confronto_nil.csv`, `controlli.json`)
- Totali nei NIL: OSM 6 tipi 6.637; ds58 9.166; ds59 3.502; ds250 1.444. Rapporto OSM/ds58 0,724; OSM/(ds58+ds59) 0,524; OSM/(ds58+ds59+ds250) 0,470. Il confronto giusto è con ds58 (in piano): ds59 contiene stadi, circoli, mense.
- Per NIL contro ds58: correlazione 0,985; mediana -27,1%. I NIL di centro sono i più vicini (Città Studi 0,94, Duomo ~0,82), quelli di periferia i più lontani (Quarto Cagnino 0,21, San Siro 0,31, Quarto Oggiaro 0,35). Rispetto al rapporto di città (0,724), 43 dei 63 NIL con almeno 20 locali nel registro stanno entro ±20%, 49 entro ±30%: OSM è un campione coerente, non completo.
- **Abbinamento di 100 ristoranti OSM a caso** (seme fisso 20261101, `pulito/campione_100.csv`): 97 hanno una pratica del registro entro 50 m (88 entro 25 m; distanza mediana 10 m); dei 71 con indirizzo, 58 hanno via+civico identici nel registro. I 3 mancanti: un locale modificato a luglio 2026, uno senza nome né indirizzo, uno in via Gessi 12.
- Su tutti i 6.637 OSM: 84,0% entro 25 m e 95,0% entro 50 m. **Attenzione**: Milano è densa; spostando a caso gli stessi punti di 150-400 m si ottiene comunque 23,9% (25 m) e 56,3% (50 m). La prova forte è l'indirizzo: dei 3.823 OSM con via+civico, il 79,5% ha lo stesso via+civico nel registro.
- Al contrario: 85,6% delle pratiche ds58 ha un locale OSM entro 50 m (71,9% entro 25 m; controllo nullo 41,6%). Le pratiche più recenti (codici PE > 29.144, quindi dopo luglio 2019) ci sono nella stessa misura (86,0%) delle vecchie (85,4%).
- **Quanto è in ritardo il registro sui locali chiusi?** Dei 100 locali che OSM segna chiusi, 58 non hanno altro locale food attivo entro 20 m; di questi 36 (62%) sono ancora nel registro entro 25 m. Chiusi dal 2025: 33 su 54 (61%). Sono pochi casi (campione piccolo e solo quelli che qualcuno ha segnato) ma dicono che il registro conserva i locali chiusi per mesi.
- **E sulle aperture?** I locali OSM creati nel 2026 (versione 1: 424) hanno il registro entro 50 m nel 93,6% dei casi (27 senza); creati e mai più toccati nel 2025-26: 92,4% (682). Il registro tiene il passo sulle aperture.
- Turnover del registro ds58 2019 -> 2026 (`pulito/registro_2019_2026_nil.csv`): 9.044 -> 9.269 pratiche (+2,5%). Ma il 65% dei codici nuovi sta a un indirizzo che c'era già nel 2019 e il 70% dei codici spariti sta a un indirizzo che c'è ancora: sono subentri (nuovo gestore, nuovo codice). Per indirizzo: 969 spariti, 1.158 nuovi (+189, +2%).

## 5. Trappole e riserve
1. **Il registro non ha date interne**: "aggiornato" è deducibile (ricaricato ad agosto 2026, codici nuovi, locali nuovi di OSM presenti) ma non dichiarato. Per dire "a quando" sul sito serve un'altra prova o una domanda al Comune (opendatamilano@comune.milano.it, indirizzo nei metadati).
2. Il registro conta le pratiche, non i locali aperti oggi: locali chiusi restano; un cambio di gestione cambia il codice. Per 3 locali su 5 chiusi in OSM nel 2025-26 la pratica c'è ancora.
3. OSM conta il 28% in meno del registro e non uniformemente (periferia molto meno): niente classifiche "NIL con più locali" da OSM da solo in periferia. Meglio ds58 per i conteggi, OSM per le cucine.
4. La cucina è in OSM solo per il 68,9% di ristoranti+fast food, e il tag è scritto più spesso in centro: le quote per NIL sono "tra i locali con cucina nota". Con meno di 15-20 locali per NIL gli indici sono rumore.
5. Residenti: il denominatore (ds205, 2024, 1.407.044 abitanti) non conta chi lavora o visita. Duomo ha 41,7 pratiche in piano ogni 1.000 residenti, Gallaratese 1,0. NIL piccoli o parchi (Stephenson 172 abitanti, Parco Sempione 0) danno rapporti senza senso: nel CSV Parco Sempione ha vuoto, non infinito. Il file ds205 ha le superfici scambiate per 3 NIL (vedi alberi/NOTE punto 6.5).
6. `tipo` del registro ds58: lettere a-i concatenate nel testo libero, 4,6% non classificato; un locale può essere più tipi (colonna `tipo_dettaglio`, es. "ristorante_trattoria+pizzeria+bar_caffe"). Non si può contare "trattorie" dal registro; le parole "trattoria/osteria" nel nome in OSM sono 199 ristoranti.
7. `locali.csv` mette insieme OSM e registro: lo stesso locale compare due volte (una per fonte). Per contare, filtrare per `fonte`. Nessun abbinamento riga-per-riga è stato fatto.
8. Esclusi da `locali.csv`: 427 pratiche del registro senza coordinate (103 + 297 + 27).
9. Il 2019 ha NIL vecchi; per il confronto 2019-2026 i NIL sono ricalcolati dalle coordinate sui poligoni vigenti.
10. ds2954 ha un salto di definizione: "Cessato" in piano 7.125 nel 2023 e 8 nel 2024. Non usarlo per le chiusure.

## 6. Licenze
- OSM: ODbL 1.0. Citare "© OpenStreetMap contributors". **Un database derivato da OSM va ridistribuito con la stessa licenza (share-alike)**: `pulito/osm_poi.csv`, `locali.csv` (righe `fonte=osm`) e i riepiloghi sulle cucine sono derivati. Un grafico o una mappa sono "Produced Work": basta l'attribuzione. Se si pubblica la tabella, pubblicarla come ODbL e tenere separate le righe OSM da quelle del Comune.
- Comune: CC-BY (ds58, ds59, ds250, ds2954, `license_id: cc-by` nel CKAN, versione non indicata); citare "Comune di Milano - dati.comune.milano.it". ds612: CC0.
- Wayback Machine: la copia 2019 di ds58 è un file del Comune (CC-BY), preso da web.archive.org.
- Nessun Google, TripAdvisor, TheFork o account: non usati.

## 7. Cosa c'è in `pulito/` e che numeri dà (se positivo, come ora)
- `locali.csv` (20.758 righe: OSM 6.646, ds58 9.166, ds59 3.502, ds250 1.444): fonte, id, nome, tipo, cucina, lon, lat, id_nil, nil, ultima_modifica (solo OSM), tipo_dettaglio, cucina_gruppi, check_date, start_date, opening_hours, indirizzo.
- `nil_locali_per_1000ab.csv`: per NIL abitanti 2024, area, locali OSM (6 tipi e per tipo), pratiche ds58/ds59/ds250, per 1.000 abitanti e per km². Città: 4,72 locali OSM ogni 1.000 abitanti, 6,51 pratiche in piano (9,00 con fuori piano). Più alti (NIL con 3.000+ abitanti, ds58): Duomo 41,7, Porta Garibaldi-Porta Nuova 29,9, Brera 24,5, Porta Ticinese-Conchetta 19,2, Stazione Centrale 16,5. Più bassi: Gallaratese-San Leonardo-Lampugnano 0,96, QT8 1,0, Comasina 1,2, Barona 1,2, Muggiano 1,3.
- `nil_cucine.csv`, `cucine_concentrazione.csv`: mix di cucine per NIL.
- `locali_milanesi.csv`, `registro_2019_2026_nil.csv`, `freschezza_osm.csv`, `confronto_nil.csv`, `campione_100.csv`, `osm_chiusi_vs_registro.csv`, `freschezza.json`, `controlli.json`, `build_log.json`.

### Mix di cucine (OSM, ristoranti + fast food con cucina nota, n = 2.569; un locale può avere più cucine)
Pizza 30,6%, italiana 28,0% (italian, regional, pasta...), giapponese/sushi 11,1% (286), hamburger/panini 9,9%, kebab/Medio Oriente 8,6% (220), cinese 8,4% (217), pesce 5,5%, altro asiatico 4,0%, latinoamericana 3,2%, indiana/sudasiatica 1,6% (41), africana 0,7% (17). "Non italiana e non pizza" (giapponese, cinese, asiatica, indiana, mediorientale, latinoamericana, africana): 35,1%.
- Singoli tag più frequenti: pizza 765, italian 546, regional 221, chinese 218, japanese 174, kebab 167, burger 153, sushi 118.
- Il registro dà il tipo legale, non la cucina: in piano ristorante/trattoria 3.813, bar caffè 1.940, bar gastronomico 1.077, wine bar/pub 505, tavola calda/fast food 503, pizzeria 499. Artigianato (ds250): pizzeria da asporto 332, gelaterie 326, gastronomie/rosticcerie 311, kebab 211.

### Dove si raggruppano le cucine (indice di localizzazione LQ = quota del NIL / quota della città, solo NIL con 15+ locali con cucina)
- Cinese: Sarpi LQ 4,6 (51 locali cinesi su 132), 52% di tutti i cinesi di Milano nei primi 5 NIL; poi Loreto-Casoretto-NoLo (LQ 2,8; 19), Stadera-Chiesa Rossa (2,3).
- Indiana: Buenos Aires-Porta Venezia LQ 3,5 (11 su 41 totali).
- Kebab/Medio Oriente: Affori 3,2, Stadera-Chiesa Rossa 2,8, Padova-Turro-Crescenzago 2,6, Bovisa 2,2; i più numerosi sono Buenos Aires-Porta Venezia (17) e Porta Ticinese-Conca del Naviglio (15).
- Latinoamericana: Loreto-Casoretto-NoLo (8 su 82; LQ 3,1), Padova-Turro-Crescenzago.
- Giapponese/sushi: il più diffuso e meno concentrato (31,5% nei primi 5 NIL): Sarpi 21, Brera 21, Buenos Aires-Porta Venezia 20. LQ massimo: Corsica 2,4.
- Quota di cucine "etniche" più alta: Loreto-Casoretto-NoLo 66,7% (54 su 81), Sarpi 65,2% (86 su 132), Bovisa 57,7%; più bassa: Guastalla 17,1%, Pagano 18,5%, Duomo 19,2%, Brera 25,2%.

### I "più milanesi"
OSM non permette di dirlo bene. Solo 4 locali hanno nel tag `cuisine` milanese/risotto (`milanese`, `italian;milanese`, `risotto;soup`, `meat;pizza;pasta;risotto`); altri 20 hanno una parola come milanese/lombardo/risotto/cotoletta/cassoeula nel nome o nella descrizione (es. Osteria Milanese Oss Bus, Le Cotolette, Trattoria del Ciumbia, La Cassoeula del Togn, Trattoria Casa Fontana - 23 risotti). 24 in tutto: `locali_milanesi.csv`, di cui 5 a Brera e 4 a Porta Ticinese-Conca del Naviglio. Il tag `regional` (221 locali) non dice quale regione. Per una pagina serve una lista a mano o un'altra fonte (Slow Food, guide) - non cercata qui.

### Aperture e chiusure nel tempo
Il registro non ha date. Quello che si può dire: tra il 2019 e il 2026 le pratiche in piano passano da 9.044 a 9.269 (+2,5%); per NIL (≥40 nel 2019) crescono Isola +24,6% (264 -> 329), Moncucco-San Cristoforo +24,3%, Loreto-Casoretto-NoLo +18,5%, Sarpi +17,6%, Pagano +15,6%; calano Quarto Oggiaro -5,0%, Maciachini-Maggiolina -4,4%, Magenta-San Vittore -2,9%, Brera -2,4%. Il ricambio è molto più grande del saldo ma metà è cambio di gestione allo stesso indirizzo (trappola 5.2). OSM ha `start_date` su 71 locali soltanto.

### La cosa più sorprendente
Il quartiere con la quota più alta di cucine non italiane non è solo Sarpi: NoLo (Loreto-Casoretto-NoLo) è alla pari o poco sopra (la differenza, 1,5 punti su 81 locali, è nel rumore): 66,7% dei locali con cucina nota non è italiano né pizza (54 su 81), contro il 65,2% di Sarpi (86 su 132). Sarpi è soprattutto Asia orientale (cinese 51, giapponese 21, altro asiatico 12 su 132); NoLo ha cinque cucine con almeno 3 locali (cinese 19, mediorientale 12, altro asiatico 10, latinoamericana 8, giapponese 5). Seconda sorpresa, sul metodo: un database di volontari (OSM) concorda con il registro ufficiale (79,5% di via+civico identici tra i locali con indirizzo; correlazione 0,985 tra NIL) pur contando il 28% di locali in meno.

## 8. Cosa potrebbe mostrare una pagina (idee, non fatte)
1. Mappa a punti dei locali (OSM, con "© OpenStreetMap contributors") con filtro per tipo e cucina.
2. Classifica dei NIL per locali ogni 1.000 residenti (ds58), con avviso su centro/residenti.
3. "Impronta" di cucine per NIL (barre impilate, solo NIL con 20+ locali con cucina) e le tre mappe: Sarpi cinese, Porta Venezia indiano, NoLo.
4. Variazione 2019-2026 delle pratiche per NIL (Isola +25%).
5. Barra "quanto sono freschi i dati" sempre visibile, con le tre cifre: 70% OSM modificato in 3 anni, registro caricato ad agosto 2026, nessuna data nel registro.
6. Per le "più milanesi", chiedere a Davide una lista o una fonte.

## 9. Da decidere
- Procedere con la pagina? (verdetto positivo con riserve)
- Chiedere al Comune la data di riferimento di ds58/ds59/ds250.
- Aggiungere gli esercizi di vicinato alimentare (ds49) o `shop=*` da OSM per panetterie, pasticcerie, gastronomie.
- Rifare la prova dei locali chiusi con più casi (es. Overpass con `disused:*` + storico) prima di scrivere "il registro tiene i chiusi".
