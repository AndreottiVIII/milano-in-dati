# Alberi della città - FASE 1 (raccolta, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web, nessun giudizio. Ogni numero dice file e campo. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di alberi> <percorso assoluto di milano-in-dati>` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`.

## 1. In breve

1. **Esiste un solo censimento degli alberi, quello del Comune (ds2484), CC-BY, ma in tre edizioni annuali: 31/3/2023, 31/3/2024, 31/3/2025.** Quella del 2023 non è più sul portale: l'ho presa dalla Wayback Machine (copia del file del Comune). Prima del 2023 non esiste (il dataset è nato il 26/10/2023).
2. **Il censimento copre solo gli alberi che gestisce il Comune** ("tutte le piante gestite dal Comune", campo `notes` del dataset): strade, piazze, parchi, giardini, cimiteri. Non i giardini privati, non i parchi di altri enti. Non è "gli alberi di Milano".
3. **251.165 alberi nell'edizione 2025** (255.075 nel 2023). 1 albero ogni 5,6 abitanti (178,5 per 1.000 abitanti; 1.382 per km²).
4. **Le misure (tronco, altezza, chioma) sono in gran parte segnaposto**: il 24% degli alberi ha esattamente tronco 8 cm, altezza 5 m, chioma 2 m; il 90-95% degli alberi presenti in due edizioni ha lo stesso tronco. Non usare le misure per dire quanto sono grandi o vecchi.
5. **La data (`data_ini`) è per il 46,3% "21 ottobre"**: vale l'anno, non il giorno.
6. **Fonti che NON danno nulla di nuovo o non scaricabili**: Forestami (nessun dato aperto, solo pagine web con il numero di piante), Regione Lombardia (nessun censimento alberi per Milano), Copernicus Urban Atlas 2021 "Street Tree Layer" per Milano (25 MB, esiste ma richiede login: saltato).

## 2. Fonti, una per una (anche in `pulito/inventario.csv`)

Licenza dei dataset del Comune: nel catalogo CKAN `license_id = cc-by`, titolo "Creative Commons Attribution", link http://www.opendefinition.org/licenses/cc-by (la versione, es. 4.0, non è scritta). Si possono ripubblicare citando "Comune di Milano - dati.comune.milano.it".

### 2.1 Censimento alberi - `ds2484_infogeo_alberi_localizzazione` (Direzione Verde e Ambiente)
- Cosa: elenco georeferenziato "di tutte le piante gestite dal Comune di Milano alla data di riferimento", con genere, specie, varietà, diametro tronco, diametro chioma, altezza, area (`id_area`, `localita`), municipio. Aggiornamento dichiarato: ANNUAL (CKAN `frequency`).
- Colonne: `id_area, municipio, area, localita, obj_id, codice, data_ini, genere, specie, varieta, diam_tronc, diam_chiom, h_m, LONG_X_4326, LAT_Y_4326, Location`. Nessuna famiglia, nessun nome comune: le ho aggiunte io (vedi 4).
- Edizioni (file in `raw/comune_ds2484/`):

| Edizione | Formato | Righe | Come l'ho avuta |
|---|---|---|---|
| 31/3/2023 | CSV (zip 8,4 MB, csv 47,6 MB) | 255.075 | Wayback Machine, snapshot del 6/5/2024 del file `ds2484_alberi_20230331_csv.zip` del Comune. Non verificabile con un checksum del Comune; struttura identica, e il 91% degli `obj_id` del 2023 si ritrova nel 2025. |
| 31/3/2024 | GeoJSON (zip 11,5 MB, 131,9 MB) | 247.779 | dati.comune.milano.it (sul portale la risorsa GeoJSON è ancora quella del 2024) |
| 31/3/2025 | CSV (zip 9,5 MB, csv 46,9 MB) | 251.165 | dati.comune.milano.it (risorse CSV e JSON sono 2025) |

- Il JSON è una copia del CSV e non l'ho scaricato. Coordinate: gradi WGS84; nel GeoJSON 2024 la geometria coincide con i campi lon/lat a 6e-14.
- Date: `metadata_modified` 8/5/2026 (ricarico in blocco del portale, non dice nulla sull'aggiornamento dei dati); le risorse sono state ricaricate il 23/4/2025.
- Ho cercato edizioni più vecchie anche nell'archivio Wayback del dataset (CDX): trovato solo 2023 (CSV, JSON, GeoJSON) e il 2024.
- Cosa manca: famiglia, nome comune, età certa dell'albero, stato di salute, motivo delle rimozioni, perimetro preciso della "gestione comunale" (es. Parco Nord, Parco Agricolo Sud, aree di altri enti). Gli alberi privati non ci sono.

### 2.2 Altri dataset del Comune (CC-BY, scaricati il 1/11/2026 in `raw/comune_<id>/`)
- **ds2489 alberi monumentali**: 13 schede (3/11/2023), circonferenza (non diametro). Solo contesto.
- **ds2813 / ds2810 indice di verde urbano per NIL / Municipi**, luglio 2024, calcolato dal progetto SPOTTED (satellite); il campo `value` ha un nome e basta, il metodo sta su un portale che chiede registrazione (non fatta). Usato solo per un confronto.
- **ds1323 verde urbano 2011-2024** (superfici per tipo e gestione), **ds2926** (mq di verde per abitante: 17,2 nel 2011, 18,8 nel 2023, fonte ISTAT), **ds2927** (verde / superficie comunale: 12,0% nel 2011, 14,1% nel 2023). Sono superfici, non alberi.
- **ds339 aree verdi per zona e superficie 2014** (2.917 aree: filari, parchi, scuole; encoding latin-1, decimali con virgola): `Zona_Area` aggancia circa il 91% degli alberi. Non l'ho usato; è la via per calcolare alberi per ettaro di parco/filare.
- **ds3018** parchi e aree "spazi freschi" 2026 (67 righe): non usato.

### 2.3 Forestami (forestami.org)
- Nessun dataset aperto: nessuna pagina "open data/dati" (le pagine /open-data/, /dati/ rispondono con la home), nessun file geojson/csv/zip linkato. C'è solo un elenco di 52 piantagioni (sitemap `piantagione-sitemap.xml`) ognuna con "Numero di piante". Salvato in `pulito/forestami_piantagioni.csv` solo nome, stagione, numero (fatti); le pagine HTML sono in `raw/forestami/` e **non vanno ripubblicate** (pie' di pagina: "Copyright © Forestami - Tutti i diritti riservati").
- Totale delle 52 piantagioni: 72.571 "piante" (alberi **e arbusti**: a via Chiasserini 1.151 = 554 alberi + 597 arbusti, cfr. testo della pagina). **A Milano città: 8 siti, 5.760 piante** (Parco dei Fontanili e Parco Andrea Campagna 2021; Cava Ongari 2022; via Chiasserini, via Bovisasca, via Valla 2023; via Belgioioso primavera 2024; Bosco Forestami autunno 2024). Mancano coordinate e specie. Non so se quelle aree siano gestite dal Comune (e quindi nel censimento): i due insiemi non sono confrontabili.
- La pagina "Mappatura" parla di canopia (copertura arborea) di tutta la Città metropolitana, senza link a dati.

### 2.4 Regione Lombardia (dati.lombardia.it, API catalogo Socrata)
- Ricerche "alberi", "verde urbano", "alberi monumentali": trovati solo "Villa Monastero - Censimento Alberi", "COMUNE CREMONA Aree verdi", "Bellezze individue" (alberi monumentali regionali, turismo). Nessun censimento di Milano. Non ho scaricato nulla. Il Geoportale (DUSAF uso del suolo, DBT) darebbe copertura del suolo, non alberi: non cercato oltre.

### 2.5 Copernicus (Urban Atlas, Tree Cover Density)
- **Urban Atlas Street Tree Layer 2021**, area funzionale urbana di Milano (IT002L3 MILANO): 25.394.403 byte; **Urban Atlas Land Cover/Land Use 2018 e 2021** Milano (140-147 MB). Elenco file pubblico (`raw/web_probe/ua_streettree_files.csv`, `ua_lcu_files.csv`). Il file vero richiede un token (`DAT-ZIP-604 Token not found`, HTTP 401): **non scaricato, nessun account creato**. È però la fonte giusta per un controllo indipendente (alberi stradali da satellite): se Davide vuole, il login lo fa lui.

## 3. Pulizia (`scripts/build.py`, risultati in `pulito/controlli_pulizia.json`)

- Tre edizioni sovrapposte in `pulito/alberi.csv` (754.019 righe, 194 MB, separatore `;`). Colonne: `id` (= `obj_id`, unico dentro l'edizione), `edizione`, `specie_binomio` (come nel file), `specie_binomio_normalizzata` (sinonimi uniti, vedi 4), `genere`, `epiteto`, `varieta`, `famiglia`, `nome_comune`, `lon`, `lat`, `diam_tronc_cm`, `diam_chioma_m`, `altezza_m`, `data_inizio_scheda` (solo data), `municipio_file`, `id_area`, `localita`, `id_nil`, `nil`, `assegnato_per_vicinanza`, `cap_stimato`, `flag_data`, `flag_misure`, `flag_dup_posizione`, `fonte`.
- Nessun valore è stato cancellato o corretto: le stranezze sono segnalate (flag). Segnalati: tronco > 300 cm (4-8 per edizione, il massimo è 1.115 cm), altezza > 50 m (3-8, il massimo è 2.610 m), date prima del 1900 (544-557 per edizione, la più vecchia 1176), date dopo l'edizione (2 nel 2023), alberi con la stessa posizione di un altro (circa 730 per edizione), generi vuoti (105/129/121), `specie` = "Red" (cultivar scritta come specie, "Malus Red Sentinel", 69 righe in tutto).
- **NIL**: punto in poligono con i 88 NIL vigenti (`citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson`, EPSG:4326). 418 punti unici (su 512.234) cadono fuori da ogni poligono: 331 entro 100 m dal NIL più vicino (assegnati, `assegnato_per_vicinanza = True`), 87 oltre (massimo 524 m, non assegnati: sono 41-46 alberi per edizione). Nessun punto in due NIL.
- **Controllo**: il `municipio` scritto nel file coincide col municipio prevalente del NIL calcolato nel 95,0% dei casi (la differenza è prevista: un NIL può stare a cavallo di due municipi).
- **CAP**: i confini dei CAP non esistono aperti. `cap_stimato` = CAP del civico più vicino (`citta-15-minuti/out/civici_tempi.csv`, civici con CAP a meno di 300 m dal punto con CAP noto), solo se il civico è entro 250 m dall'albero; è una stima, come nel filone 9 (che per il CAP del civico ha trovato 96,6% di accordo).

## 4. Specie, nome comune, famiglia: li ho messi io

Il censimento non ha famiglia né nome comune. `scripts/taxonomia_genere.csv` (genere -> famiglia, nome italiano, 112 generi) e `scripts/nomi_specie.csv` (binomio -> nome comune e unione dei sinonimi) sono scritti da me a mano. Famiglie secondo APG IV (es. Acer e Aesculus insieme in Sapindaceae; Tilia e Hibiscus in Malvaceae); con la classificazione tradizionale (Aceraceae, Tiliaceae...) le quote sarebbero più basse, quindi la regola 10-20-30 è più facile da rispettare. Sinonimi uniti in `specie_binomio_normalizzata`: *Platanus hybrida* -> *Platanus x acerifolia*; *Tilia hybrida* -> *Tilia x europaea*; *Tilia argentata* -> *Tilia tomentosa*; *Ulmus carpinifolia* -> *Ulmus minor*. Da far rivedere a un botanico prima di pubblicare i nomi.
`epiteto = spp` (24.466 alberi nel 2025 = 9,7%) significa "specie non indicata".

## 5. Riepilogo (tutti i numeri sono in `pulito/riepilogo.json` e nelle tabelle csv)

### 5.1 Quanti e quali (edizione 2025, `pulito/alberi.csv`)
- 251.165 alberi, 111 generi, 47 famiglie, 339 binomi (335 dopo l'unione dei sinonimi). Strade e piazze 64,9%, parchi e giardini 32,0%, cimiteri 3,0% (dalla prima parola di `localita`, `riepilogo.json`).
- Specie più frequenti (`top_specie.csv`): platano comune *Platanus x acerifolia* 16.618 (6,62%), bagolaro 13.938 (5,55%), acero riccio 10.032 (3,99%), frassino maggiore 8.348 (3,32%), carpino bianco 8.108 (3,23%), liquidambar 7.681 (3,06%), pioppo nero 6.588 (2,62%), robinia 6.542 (2,60%), tiglio selvatico 6.135 (2,44%), quercia rossa 5.626 (2,24%).
- Generi (`top_generi.csv`): Acer 27.613 (10,99%), Platanus 22.712 (9,04%), Tilia 21.270 (8,47%), Prunus 15.851 (6,31%), Celtis 15.546 (6,19%), Quercus 13.591 (5,41%), Fraxinus 12.651 (5,04%), Ulmus 11.754 (4,68%), Populus 10.567 (4,21%), Carpinus 8.108 (3,23%).
- Famiglie (`top_famiglie.csv`): Sapindaceae 13,37%, Malvaceae 9,52%, Rosaceae 9,19%, Platanaceae 9,04%, Fabaceae 7,33%.

### 5.2 Diversità: regola 10-20-30 (`citta_per_edizione.csv`)
Regola: nessuna specie sopra il 10%, nessun genere sopra il 20%, nessuna famiglia sopra il 30%.
- **Rispettata in tutte e tre le edizioni**: specie al massimo 6,6%, genere al massimo 11,0% (Acer), famiglia al massimo 13,4% (Sapindaceae).
- Caso peggiore: se tutti gli alberi "Platanus spp" (specie non indicata) fossero *P. x acerifolia*, la prima specie salirebbe all'8,7%: ancora sotto il 10%.
- **A scala di quartiere la regola non regge**: 56 NIL su 88 hanno una specie sopra il 10% e 30 hanno un genere sopra il 20% (la regola è pensata per la città, ma i quartieri piccoli sono quasi sempre sotto). Esempi: Maggiore-Musocco-Certosa 30,0% *Calocedrus decurrens* (3.179 dei 3.614 calocedri della città stanno nei cimiteri, soprattutto Maggiore: siepi dei cimiteri); Quintosole 77,8% liquidambar (117 alberi); Buenos Aires-Porta Venezia-Porta Monforte 27,1% platano (3.970 alberi).

### 5.3 Alberi per abitante e per km², per NIL (`nil_alberi.csv`)
Abitanti: `ds205` (Comune), campo `Totale`, anno **2024** (totale 1.407.044), usato anche per l'edizione 2025; anno 2023 (1.417.597) per l'edizione 2023. File: `citta-15-minuti/raw/comune_milano/pop_caratteristiche_quartiere/ds205_dati_quartieri_2011_2024_.csv`. Superficie: dai poligoni NIL in UTM 32N (somma 181,76 km²).
- Città intera: 178,5 alberi per 1.000 abitanti; 1.382 per km². Mediana dei NIL con almeno 5.000 abitanti (64 su 88): 139 per 1.000 abitanti.
- Classifica solo NIL con almeno 5.000 abitanti (gli altri 24 sono parchi o aree quasi senza residenti: Parco Sempione 0 abitanti, Giardini Porta Venezia 40, Parco Nord 100...). **Più alberi per abitante**: Maggiore-Musocco-Certosa 763 per 1.000 (7.576 alberi, 9.930 abitanti; ci sono i cimiteri), Cimiano-Rottole-Feltre 650, Lorenteggio 439, Barona 349, Adriano 325, Monluè-Ponte Lambro 294. **Meno**: Bovisa 47, Loreto-Casoretto-Nolo 50, San Siro 57, Stazione Centrale-Ponte Seveso 62, Buenos Aires-Porta Venezia-Porta Monforte 64, Dergano 76, Comasina 77, Porta Magenta 82. Rapporto massimo/minimo: 16,3 volte. (Con tutti gli 88 NIL la forbice è assurda perché i parchi hanno pochi residenti.)
- Più alberi per km² (con residenti): Quarto Oggiaro-Vialba-Musocco 3.238, Barona 2.882, Cimiano 2.566, Lorenteggio 2.516, Maggiore-Musocco-Certosa 2.500; fuori classifica Giardini Porta Venezia 8.336, Parco Sempione 6.275, QT8 5.349. Il Parco delle Abbazie (13,7 km²) ne ha 321 per km², Cascina Merlata 17 per km² (30 alberi).
- **Il rapporto con la densità**: alberi per abitante e abitanti per km² nei NIL (almeno 5.000 abitanti): Spearman -0,76 (IC 95% -0,87/-0,59). Dove vivono più persone per km² ci sono meno alberi a testa: vale come descrizione, non come causa.

### 5.4 Cambiamenti 2023-2025 (`cambiamenti_edizioni.csv`, per `obj_id`)
- Totale: 255.075 (31/3/2023) -> 247.779 (2024, -7.296; -2,86%) -> 251.165 (2025, +3.386; +1,37%). Tra 2023 e 2025: **-3.910 (-1,53%)**: 21.815 alberi spariti, 17.905 nuovi, 233.260 in comune. 64 NIL con meno alberi, 21 con più.
- I 17.905 nuovi hanno `data_ini` quasi tutta 2023-2025 (92%: 2023: 3.152; 2024: 8.241; 2025: 5.042): piantagioni vere o schede nuove; il dato non distingue.
- Dei 21.815 spariti: 54,7% con tronco fino a 12 cm; **6.429 (29%) con data scheda dal 2019** (alberi piantati da meno di 6 anni); data scheda più frequente 2021 (1.922), 2022 (1.481), 2023 (1.312). Il dataset non dice se sono morti, abbattuti, sostituiti o usciti dalla gestione comunale.
- Per genere (2023-2025, saldo = nuovi - spariti): Acer -716, Populus -878, Prunus -554, Ulmus -611, Carpinus -615, Platanus -321, Robinia -378; Tilia +140, Celtis +290 (`cambiamenti_per_genere_2023_2025.csv`). Per NIL peggiori: Gallaratese-San Leonardo-Lampugnano -470 (-5,1%), Quarto Oggiaro-Vialba-Musocco -349, QT8 -270, Niguarda -238, Cimiano -231; migliori: Giambellino +171 (+5,1%), Adriano +109, Ronchetto sul Naviglio +98.
- Alberi in comune fra due edizioni: ~95-90% ha **lo stesso diametro del tronco** (crescita mediana 0 cm/anno): le misure non sono riviste ogni anno. 887 alberi hanno cambiato specie nella scheda 2023-2025 (rettifiche), 277 si sono spostati di più di 5 m (32 oltre 50 m).

### 5.5 Confronto col reddito (come confronto, non prova)
- Per CAP (38 CAP, `pulito/cap_alberi_reddito.csv`): alberi per 1.000 abitanti (2025, abitanti stimati dal filone 9, `residenti_stimati`) contro imponibile medio 2024 (`citta-15-minuti/out/cap_redditi_servizi.csv`, campo `imponibile_medio_2024`): **Spearman -0,47 (IC 95% -0,72/-0,16)**: i CAP con reddito più alto hanno in media meno alberi per abitante. Col numero assoluto di alberi: -0,56. I CAP con meno alberi per abitante: 20131 (Loreto-Nolo, 51 per 1.000), 20158 (Bovisa, 68), 20122 (Guastalla, 71, reddito medio 63 mila €), 20125 (Maciachini, 73), 20129 (Buenos Aires, 74); più alberi: 20151 (Gallaratese, 344), 20134 (Lambrate-Ortica, 320), 20142 (Gratosoglio, 283). Non vuol dire "i ricchi hanno meno verde": i CAP ricchi sono i più centrali e densi (vedi 5.3), e i giardini privati non sono nel censimento. Il CAP degli alberi è stimato.
- Per NIL con l'indice di verde SPOTTED di luglio 2024 (`value`): alberi per km² contro indice, Spearman +0,24 (IC -0,01/+0,48): quasi nulla; l'indice misura verde da satellite (anche privato e agricolo), il censimento solo gli alberi comunali.

### 5.6 Misure e date (`riepilogo.json`, `misure_ultima_edizione`)
Edizione 2025: tronco 8 cm esatti 30,6%; altezza 5 m esatti 36,0%; chioma 2 m esatta 41,3%; i tre insieme (8 cm, 5 m, 2 m) 60.261 alberi = 24,0%. Mediana tronco 12 cm, altezza 5 m; tronco da 50 cm in su l'11,3%, da 100 cm lo 0,38%. Data scheda: 38,7% prima del 2000, 29,1% dal 2015, 16,7% dal 2020; "21 ottobre" 46,3%, "31 dicembre" 1,1%.

## 6. Cose strane e trappole

1. **Misure segnaposto** (punto 1.4, 5.6): niente classi di taglia, niente "alberi grandi" senza una pulizia o senza usare solo le misure plausibili.
2. **`data_ini` non è una data di impianto affidabile**: 46% "21 ottobre" di un anno qualsiasi (data convenzionale). Usare solo l'anno, e con cautela.
3. **Il perimetro cambia da un'edizione all'altra** senza spiegazione (alberi "aggiunti" con data scheda precedente al periodo: 7-11%): il saldo non è "quanti ne sono stati piantati".
4. **CSV e JSON del dataset sono 2025, il GeoJSON è 2024** (stesso titolo/id): rischio di confrontare edizioni diverse senza accorgersene.
5. **ds205 ha le superfici sbagliate (scambiate) per 3 NIL**: Porta Vigentina-Porta Lodovica (3,43 km² nel ds205, 1,14 reali), Gorla-Precotto (1,14 nel ds205, 3,00 reali), Villapizzone-Cagnola-Boldinasco (3,01 nel ds205, 3,43 reali). Ho usato le superfici dei poligoni (somma 181,76 km² contro 181,77 di ds205 intero: il totale torna, gli addendi no). Anche il filone 9 (`citta-15-minuti/NOTE.md`) cita il ds205 "per la superficie": da controllare.
6. **Parchi senza residenti**: alberi per abitante esplode (Parco delle Abbazie 13.389 per 1.000, Giardini Porta Venezia 52.025); classifica solo con NIL da 5.000 abitanti.
7. Le specie "Red" (*Malus* 'Red Sentinel') e i valori "spp" sono voci non pulite del Comune.
8. Taxonomia, nomi comuni, unione dei sinonimi: miei, da far rivedere (punto 4).

## 7. Cosa potrebbe mostrare una pagina

- Mappa dei 251 mila punti (denso; meglio esagoni o contorni per NIL) con filtro per genere/specie e per anno di scheda.
- "Il tuo quartiere in alberi": alberi per 1.000 abitanti e per km² del NIL, specie più frequente, quota del primo genere.
- Regola 10-20-30: barre di specie/genere/famiglia della città contro le soglie; lo stesso per ogni quartiere.
- 2023-2025: saldo per NIL e per genere, con l'avvertenza sul perimetro; "chi sparisce": alberi giovani.
- Albero per albero: i 13 monumentali (ds2489) a parte.
- Limiti evidenti sulla pagina: solo alberi comunali, misure non affidabili.
- Estensioni da decidere (non fatte): Street Tree Layer 2021 di Copernicus (richiede login di Davide); alberi per ettaro di parco/filare con ds339; stesso conteggio con OpenStreetMap `natural=tree`.

## 8. Cosa non ho fatto

Nessuna pagina, nessun grafico. Nessun account. Non ho pulito le misure (solo flag). Non ho scaricato Copernicus. Non ho confrontato con OSM. Nessuna verifica botanica dei nomi.
