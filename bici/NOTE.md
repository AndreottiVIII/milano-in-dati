# BikeMi e bici in città - NOTE (fase 1 + pagina)

Scaricato e analizzato il 2 novembre 2026. Programmi in `scripts/`, dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle in `pulito/`, tutti i numeri in `pulito/riepilogo.json`. Pagina: `docs/bici/index.html` (costruita da `scripts/pagina.py` + `scripts/pagina_template.html`).

## 1. In breve
1. **Dati aperti solidi**: serie annuale 2011-2025 del bike sharing del Comune (ds574, CC BY): stazioni, bici, e-bike, abbonati, noleggi medi giornalieri, free floating. Più stazioni (ds65) e itinerari ciclabili con anno di fine lavori (ds60).
2. **Cosa sorprende**: BikeMi ha più stazioni e bici del 2017 ma meno noleggi (11.740 al giorno nel 2017, 8.321 nel 2025, -29,1%); le e-bike sono il 21,2% della flotta e il 42,1% dei noleggi (2,7 volte l'uso per bici); il 2020 è l'anno record per le piste (32,0 km, 15% di tutti i km datati) mentre i noleggi cadono del 41,5%; 62,2 km su 212,6 di piste/corsie (29%) hanno norma "ordinanza lavori stradali".
3. **Contatori di biciclette: NON ci sono in dati aperti** (vedi 4). La pagina non ha serie per ora/stagione/meteo delle piste.
4. **Ore, stagioni, stazioni più usate, pioggia**: solo per BikeMi, 2011-2013, da un archivio Zenodo (Trentini, CC BY 4.0): indice di movimento orario, circa la metà dei noleggi del Comune (rapporto 0,57; 0,49; 0,54 nei tre anni).

## 2. Fonti
| Fonte | Contenuto | Licenza | File |
|---|---|---|---|
| Comune di Milano ds574 "Servizi di Car Sharing, Bike Sharing, Scooter sharing e monopattini" (scheda 4/8/2026) | serie 2011-2025: Station Based (stazioni, bici, e-bike, abbonati, noleggi medi giornalieri, anche bike/ebike/ebike con seggiolino dal 2022); Free Floating (bici, e-bike, noleggi, dal sett. 2017); percorrenze annue (stima) dal 2018 | CC BY | `raw/comune/ds574_1.csv` |
| ds65 "Stazioni BikeMi" | 325 stazioni attive, 9.452 stalli, anno installazione 2008-2021, Municipio; file di settembre 2022 | CC BY | `raw/comune/ds65_1.csv` |
| ds60 "Itinerari ciclabili" (25/10/2026) | 4.411 tratti, tipologia, norma, anno fine lavori (`fine_lavor`, 0 = non indicato), lunghezza in metri | CC BY | `raw/comune/ds60_itinerari_ciclabili.{csv,geojson}` (identico a `parcheggi/raw/comune_ds60`) |
| BikeMi GBFS `https://gbfs.urbansharing.com/bikemi.com/` | una fotografia del 2/11/2026 ore 10:28 (321 stazioni, 4.283 bici disponibili, 802 e-bike) | NLOD 2.0 secondo bikemi.com/en/open-data/realtime | `raw/gbfs/*.json`. Una sola richiesta, con intestazione `Client-Identifier` come chiede la pagina ufficiale. Non ripubblicato per stazione. |
| Zenodo 1209115 "Scraped Data BikeMI 2011-2014" (A. Trentini) | disponibilità (bici, stalli liberi) per stazione, ogni ora 2011-2013, ogni 20-30 min 2014 | CC BY 4.0 | `raw/zenodo_bikemi/{11,12,13,14}.csv` (md5 verificato; 304,6 MB) |
| ARPA Lombardia (pioggia-e-caldo) e serie di temperature/ | pioggia oraria 2013 (Rosellini 14121, Zavattari 9341, Lambrate 2006), temperatura media giornaliera | CC0 / serie del sito | solo letti, non copiati |

`scripts/search.py` ha cercato nel catalogo CKAN (2.611 schede) con 20 parole; esito in `raw/search_all.json`. Nelle schede: ds670 "Sosta biciclette" (stalli per bici, non usato), ds2829 "Esposizione al calore urbano degli itinerari ciclabili" (luglio 2024, non usato: possibile sviluppo), ds1490 censimento "mezzi di trasporto".

## 3. Numeri chiave (da `pulito/riepilogo.json`)
- BikeMi (con stazioni) noleggi medi/giorno: 2011 2.957; 2017 11.740 (picco); 2019 7.786; 2020 4.552; 2024 7.320; 2025 8.321. Abbonati: 57.021 (2017), 30.514 (2024), 39.364 (2025). Stazioni 325 dal 2021, bici 5.430 dal 2019, e-bike 1.150 dal 2018.
- Free floating 2025: 15.000 bici (tutte elettriche), 11.068 noleggi/giorno; insieme a BikeMi 19.389/giorno. Km annui (BikeMi + FF, stima Comune): 14,66 milioni nel 2025.
- Piste e corsie (sede propria + segnaletica): 212,6 km (127,7 + 84,8); tutti gli itinerari 346,3 km; 194,8 km senza i tratti "attraversamento" (= 194,3 km di parcheggi/). Cumulati per anno fine lavori: 58,5 (2010), 127,4 (2019), 159,4 (2020), 200,6 (2025), +11,7 nel 2026.
- Zenodo 2013: 285 giorni completi, indice 2.813/giorno; ore feriali: picco 13,5% tra le 8 e le 9, 8,2% tra le 18 e le 19; agosto 84 e luglio 133 (100 = media); domenica 60. Top 15 stazioni = 14,7% del movimento (Cadorna 3, Duomo, Palazzo Marino...).
- Pioggia (2013, feriali, ore 7-20, marzo-novembre): movimento nelle ore con pioggia = 0,50 delle ore asciutte (0,38 con 3 mm o più in due ore); giorni piovosi 88 contro 105 (100 = media del mese). Temperatura, a parità di mese: da 94 a 104.

## 4. Contatori: ricerca e esito
Cercato: CKAN Comune (contabici, conteggio bici, conta bici, contatori, rilevatori, spire, postazioni di conteggio, passaggi, transiti, ciclisti, flussi, traffico + elenco completo dei nomi dei dataset filtrato su bici/ciclab/bike/conta/mobil/sharing/rilev/traffic/flus): nessun dataset con conteggi di biciclette (i "transiti/accessi giornalieri" sono Area C). Web: AMAT, Regione Lombardia (dati.lombardia.it), Città metropolitana (Cambio: studio traffico Corelli, solo PDF): nessun file di dati. Tracce non aperte: Moto.it 27/2/2023 (dati AMAT 2022 Corso Buenos Aires: media 6.792 bici/giorno, punte vicine a 10.000); Il Giorno novembre 2025 (ciclabile Loreto-Oberdan circa 117.000 passaggi/mese, +14.000 sul 2024: visto solo nel riassunto di una ricerca, non letto, non usato); rivistabc: il Comune ha avviato un censimento con 79 strade (articolo datato). **Rapporti AMAT in PDF non trovati/non aperti**: nessun numero con pagina. **Passo successivo possibile**: chiedere ad AMAT/Comune i conteggi come dati aperti (decide Davide).

## 5. Metodo dell'indice di movimento (Zenodo)
Per stazione e ora: |bici(h) - bici(h-1)| solo se le misure distano 1 ora esatta; somma su tutte le stazioni, diviso 2. Stazione = numero nel nome (es. "094"), altrimenti nome normalizzato (tolto il suffisso " 0"). Scartate righe con bici/stalli negativi o capienza > 60, righe non leggibili (nel 2013 15.334, tra cui quelle senza il campo stalli liberi). Giorni tenuti: almeno il 90% del numero mediano di misure del giorno. Ora indicata = fine dell'intervallo. Meteo: pioggia dell'ora e di quella prima (orario ARPA solare, archivio probabilmente locale), media di 3 pluviometri con almeno 2 attivi; confronto a parità di mese e ora. Temperatura: classi di media giornaliera, relativo alla media del mese (feriali, marzo-novembre).

## 6. Limiti (anche in pagina)
- Noleggi/giorno: medie annuali del Comune, base di calcolo non dichiarata; noleggi/anno = media x giorni (mio calcolo).
- Solo bike sharing comunale e free floating autorizzato; non le bici private.
- ds65 del 2022, GBFS solo fotografia: nessun storico di stazioni; 4 stazioni di ds65 non nel GBFS, 0 nel GBFS non in ds65.
- Zenodo: archivio privato, indice = circa metà dei noleggi (include camion di ribilanciamento, perde andata-ritorno nella stessa ora); nome/ID stazione instabili (2,9% righe 2013 senza numero; 6 stazioni tra le 183 valutate senza abbinamento al ds65; il numero potrebbe essere stato riassegnato); 2013 finisce il 2/12; 2014 non usato (cadenza e nomi diversi).
- Meteo: confronto, non causa; tre pluviometri; 16-52 giorni per classe di temperatura.
- ds60: solo tratti esistenti oggi; la norma "ordinanza lavori stradali" non è spiegata (mia lettura: provvedimento temporaneo, anche emergenza Covid: NON verificata); 1 tratto (0,3 km) senza anno; il 2026 è parziale.

## 7. Ripetere tutto (B = .../milano-in-dati/bici, P = .../milano-in-dati, D = .../milano-in-dati/docs)
```
python -I -X utf8 B/scripts/search.py B/raw/search_all.json
python -I -X utf8 B/scripts/scarica.py B        (scarica solo se manca; --force per rifare)
python -I -X utf8 B/scripts/analisi.py B P
python -I -X utf8 B/scripts/pagina.py B D
```
Richiede pandas, numpy, pyarrow, shapely (Python 3.12).

## 8. Idee per fase 2
- Chiedere ad AMAT/Comune i conteggi dei contatori (vedi 4).
- ds2829 (calore urbano sugli itinerari ciclabili) + alberi.
- ds670 stalli per bici, ds60 per NIL (km per abitante), incidenti con bici (bici-auto-mezzi/ ha i microdati).
- Perché +29% abbonati nel 2025: non spiegato nei dati (tariffe? nuove formule?).
