# Città dei 15 minuti: note sulla fase 1 (scaricamento e controlli)

Data: 29 ottobre 2026. Cartella: `citta-15-minuti\`. Nessun calcolo di tempi a piedi fatto (è la fase 2).
Come leggere: ogni numero dice da quale file e da quale campo viene. Dove non c'è scritto altro, i file sono in `raw\comune_milano\<cartella>\`.
Tutti i controlli sono rifacibili con `scripts\controlli.py` e `scripts\analisi_collegamenti.py` (risultati in `controlli_risultati.json` e `collegamenti_risultati.json`).

## In breve (le cose che decidono il resto del lavoro)

1. **I redditi sono per CAP, non per quartiere.** 38 CAP (da 20121 a 20162), 6 anni di imposta (2019-2024). Un CAP non coincide con un NIL: il confronto con i redditi si può fare con precisione solo a livello di CAP (38 zone), non di 88 NIL. Dettagli nel paragrafo "Redditi".
2. **I punti (civici) ci sono e sono buoni:** 65.160 righe, 57.405 "applicati" (in vigore), 51.917 numeri civici distinti (via + numero + lettera): è questo il numero "circa 51.000" scelto da Davide.
3. **Le poste ci sono nei dati del Comune** (85 uffici): OSM serve solo come controllo incrociato.
4. **Gli asili nido sono vecchi** (anno scolastico 2018/19, l'ultimo) e per il 16,5% delle righe mancano le coordinate. Va segnalato nei risultati o integrato con OSM.
5. **I parchi sono poligoni**, 1.065 pezzi, di cui 737 sotto i 500 m²: per "arrivare a un parco" non basta il centro del parco (le coordinate nel CSV sono centroidi). Servono i bordi/ingressi e una soglia di dimensione.
6. **La rete pedonale c'è già:** la fase 1 della filiera "bici-auto-mezzi" (strand 7) ha già ritagliato OSM per Milano + circa 3 km di margine. Non copiato, solo referenziato (vedi "Rete pedonale").
7. **Nessun blocco:** nessun sito ha chiesto registrazione o accettazione di licenze con un clic.

---

## 1. Servizi con una posizione (portale dati del Comune, CKAN, `https://dati.comune.milano.it/api/3/action/package_show?id=<id>`)

Scaricato il 29/10/2026. Per ogni cartella ci sono anche i metadati originali in `_metadati.json`. Le coordinate sono sempre gradi WGS84 (EPSG:4326), tranne dove scritto. La data "metadata_modified" è la data in cui il file è stato caricato sul portale (molti sono stati ricaricati in blocco l'8/5/2026): **non** dice quanto sono aggiornati i dati. Dove si legge un anno vero, è indicato.

Controlli fatti su ogni set (script `scripts\controlli.py`): coordinate mancanti o a zero; punti fuori dal confine del Comune (`confine_comune`); NIL dichiarato nel file diverso dal NIL calcolato dal poligono (`nil_vigenti`); punti dentro un poligono di parco (`parchi`); duplicati (stesso nome+indirizzo, stesso punto, righe identiche).

| Servizio | Dataset (id) | Cartella | Record | Dati di | Coordinate (campi) | Licenza |
|---|---|---|---|---|---|---|
| Farmacie | `ds501_farmacie-nel-comune-di-milano` | `farmacie` | 422 | elenco regionale, aggiornato 15/10/2026 | `LONGITUDINE`, `LATITUDINE` | CC0 |
| Medici di medicina generale | `ds234-sociale-medici-medicina-generale` | `mmg` | 1.189 righe = 428 punti distinti | 29/10/2026 | `LONG_X_4326`, `LAT_Y_4326` | **CC BY-NC (non commerciale)** |
| Asili nido | `ds47-istruzione-asili-nido-localizzazione-delle-strutture` | `nidi` | 1.790 righe (3 anni) | a.s. 2016/17, 2017/18, 2018/19 (`CODANNOSCOLASTICO`) | `LONG_WGS84`, `LAT_WGS84` | CC BY |
| Scuole infanzia | `ds3014-...-2025-2026` (e storico `ds671`) | `scuole_infanzia_2025`, `scuole_infanzia_ds671` | 294 (a.s. 2025/26); `ds671` ha 3.640 righe = 12 anni | 2025/26 | `LONG_X_4326`, `LAT_Y_4326` | CC BY |
| Scuole primarie | `ds40-infogeo-scuole-primarie-localizzazione` | `scuole_primarie` | 2.604 righe = 12 anni; ultimo anno 216 | 2025/26 | idem | CC BY |
| Scuole secondarie I grado | `ds3016-...-2025-2026` (e storico `ds46`) | `scuole_sec1_2025`, `scuole_sec1_ds46` | 147 (2025/26); `ds46` 1.736 = 12 anni | 2025/26 | idem | CC BY |
| Scuole secondarie II grado | `ds78_infogeo_scuole_secondarie_ii_grado_localizzazione_` | `scuole_sec2` | 174 righe = 109 punti distinti | anno non dichiarato | idem | CC BY |
| Edifici scolastici statali (controllo) | `ds1863-...-as-2020-2021` | `scuole_edifici_statali_2020` | 560 | a.s. 2020/21 | idem | altro (attribuzione) |
| Scuole paritarie (controllo) | `ds1582-...-2020-2021` | `scuole_paritarie_2020` | 461 | a.s. 2020/21 | `LONG_X_4326`, `LAT_Y_4326` (non controllate) | altro (attribuzione) |
| Biblioteche | `ds1306-sistema-bibliotecario-milano` | `biblioteche_sistema` | 26 | caricato 10/7/2026 | `long`, `lat` | CC BY |
| Biblioteche (vecchi, solo confronto) | `ds41...` (2007), `ds287` (2013-15, senza coordinate) | `biblioteche_loc_2007`, `biblioteche_rionali_2013` | 232 e 81 | 2007; 2013-2015 | non controllate | CC BY |
| Mercati comunali coperti | `ds2471-mercati-comunali-coperti` | `mercati_coperti` | 26 (21 attivi, 5 no: Selinunte, Ca' Granda, Umbria, Gorla, QT8; campo `attivo`) | "mag24" nel nome file = maggio 2024 | `LONG_X_4326`, `LAT_Y_4326` | CC BY |
| Mercati settimanali scoperti | `ds291-economia-mercati-settimanali-scoperti` | `mercati_settimanali` | 85 (tutti `status mss`=attivo) | maggio 2024 | idem | CC BY |
| Mercati degli agricoltori | `ds2629-mercati-degli-agricoltori` | `mercati_agricoltori` | 9 | non dichiarato | `LONG_WGS84`, `LAT_WGS84` | CC BY |
| Parchi e giardini | `ds89_infogeo_parchi_giardini_localizzazione_` | `parchi` | 1.065 poligoni | non dichiarato | GeoJSON (poligoni); CSV = centroidi `LONG_X_4326_CENTROID`, `LAT_Y_4326_CENTROID` | CC BY |
| Impianti sportivi (punti) | `ds34_infogeo_impianti_sportivi_localizzazione_` | `sport_ds34` | 1.041 | non dichiarato | `LONG_X_4326`, `LAT_Y_4326` | CC BY |
| Impianti sportivi (poligoni di campi) | `ds1640_infogeo_impianti_sportivi_localizzazione` | `sport_ds1640` | 502 poligoni; date dei rilievi da 23/11/2000 a 25/3/2024 (campo `data_ini`) | 2000-2024 | solo GeoJSON (il CSV non ha coordinate) | CC BY |
| Uffici postali | `ds555_uffici_postali_milano` | `poste` | 85 (tutti `Ente`="Ufficio PT") | non dichiarato | `LONG_X_4326`, `LAT_Y_4326` | CC BY |
| Esercizi di vicinato | `ds49-economia-esercizi-vicinato-sede-fissa` | `vicinato` | 28.131 righe = 13.370 punti distinti | caricato 31/8/2026 | `LONG_X_4326`, `LAT_Y_4326` | CC BY |

Dimensioni: tutta la cartella `raw\comune_milano` pesa circa 243 MB (il grosso sono i 164 MB del CSV della popolazione estratto dallo zip da 13 MB e i 23 MB dei civici estratti).

### Problemi trovati ("trappole dei dati")

- **Farmacie** (`farmacie`): pulite. 422 righe, 0 coordinate mancanti, 0 fuori confine, 0 dentro un parco, 0 duplicati, NIL dichiarato sempre uguale a quello del poligono. Confronto con OSM: 413 delle 422 hanno una farmacia OSM entro 100 m; OSM dentro Milano ne ha 451 (`collegamenti_risultati.json`, campi `farmacie_Comune_con_OSM_entro_100m`, `OSM_farmacie_dentro`).
- **Medici di base** (`mmg`): il file è una riga per medico, non per ambulatorio. 1.189 righe ma solo 428 punti distinti (`duplicati_stesso_punto` = 761): contare i medici come "servizi" gonfierebbe le zone con ambulatori di gruppo. 154 medici hanno `attivo`=0 (1.035 attivi; 414 punti distinti attivi). 38 hanno `ambulatorioPrincipale`=0. 6 medici sono **fuori dal confine del Comune** (per esempio Via Stradivari, Via Ampere, Via Beatrice d'Este: indirizzi che sono a Milano, quindi coordinate sbagliate, spostate fino a lat 45,63) e hanno `ID_NIL` mancante; 5 cadono dentro un poligono di parco. **Il file contiene nomi, cognomi e data di nascita dei medici (`dataNascita`) e la licenza è CC BY-NC: non ripubblicare il file grezzo.** Il nome del file cambia ogni giorno (`20261029_mmg_final.csv`).
- **Asili nido** (`nidi`): i dati arrivano solo fino all'a.s. 2018/19 (600 righe quell'anno, 377 nomi distinti, 295 punti distinti). **99 righe su 600 (anno 2018/19) non hanno coordinate né NIL né CAP** (in tutto 295 righe su 1.790). Una riga è una sezione/fascia d'età, non un edificio: bisogna ridurre a un punto per edificio. Non esiste un dataset più recente sul portale (cercato: "nidi", "servizi prima infanzia 0-3"; c'è anche `ds709` "servizi integrativi all'infanzia", non scaricato). Per i nidi serve OSM (`amenity=kindergarten` / `childcare`) o accettare il limite. 3 punti dentro un poligono di parco.
- **Scuole infanzia/primarie/secondarie I grado**: i file storici (`ds671`, `ds40`, `ds46`) hanno una riga per scuola per anno scolastico (12 anni, 2014/15-2025/26): **va filtrato l'ultimo anno** (`ANNOSCOL`=2025/2026) o si contano le scuole 12 volte. Ultimo anno: infanzia 294 (166 comunali, 27 statali, 40 enti privati laici, 36 enti religiosi, 17 privati, 6 privati convenzionati, 2 privati accreditati), primarie 216 (215 punti distinti), secondarie I grado 147 (146 punti distinti). Il campo `NIL` dichiarato differisce dal poligono in 1 scuola infanzia, 2 secondarie I grado (ultimo anno). Dentro un parco: 4 infanzia, 0 secondarie (normale: scuole in giardino). Le **superiori** (`scuole_sec2`) hanno 174 righe ma 109 punti (65 righe sono "stesso punto", più istituti nello stesso edificio) e nessun anno scolastico dichiarato.
- **Biblioteche** (`biblioteche_sistema`): solo 26 sedi del Sistema Bibliotecario Milanese. OSM ha 57 punti `amenity=library` dentro Milano (`collegamenti_risultati.json`, `OSM_library_dentro`), ma comprendono biblioteche di scuole/università/condominio: non sono confrontabili uno a uno. Una cade dentro un parco.
- **Mercati**: coperti 26 righe di cui 5 inattivi (filtrare `attivo`='SI'); settimanali 85, tutti attivi ma ognuno funziona solo certi giorni (campi `LUNEDI`...`DOMENICA`, `giorno`, `orari`): un mercato aperto un giorno a settimana non è un servizio quotidiano; agricoltori 9. Dati di maggio 2024 per i primi due. OSM: 35 `amenity=marketplace` dentro Milano.
- **Parchi** (`parchi`): 1.065 poligoni, area totale 7,74 milioni di m² (campo `AREA_MQ`, somma). Mediana 78 m², 737 poligoni sotto 500 m² (aiuole), 18 sopra 10 ha. Il più grande: Parco delle Cave (59,4 ha); lo stesso nome compare su più poligoni (non è un duplicato, il parco è diviso in pezzi: 991 righe hanno nome+codice ripetuto). 22 righe identiche e 22 punti duplicati. Il CSV ha solo centroidi: inutile per l'accessibilità a piedi, serve il GeoJSON. Non è dichiarato l'anno dei dati. Confronto: OSM ha 817 `leisure=park` + 879 `leisure=garden` dentro Milano.
- **Impianti sportivi**: due set diversi. `ds34` (1.041 punti, tipo nel campo `info`: 232 centri sportivi, 159 calcio a 11, 113 pallacanestro, 93 ginnastica, 85 fitness, 77 tennis, 34 nuoto, 13 piscina...) e `ds1640` (502 poligoni di singoli campi pubblici, con 34 piste ciclabili, 26 piste di schettinaggio ecc., rilevati dal 2000 al 2024): **in `ds1640` ci sono piste ciclabili che non sono impianti sportivi nel senso del servizio**; filtrare per `descrizione_codice`. Nessun centroide fuori confine in nessuno dei due. Anno non dichiarato per `ds34`. Il problema "sport" dipende da cosa si intende: per la fase 2 conviene `ds34` come "luogo dove fare sport" e `ds1640` come "campo libero nel quartiere".
- **Poste** (`poste`): pulite (85 righe, 0 problemi). Il Comune ha quindi gli uffici postali, **non serve OSM**. Controllo incrociato: 74 delle 85 hanno un punto OSM `amenity=post_office` entro 150 m; OSM ha 111 `post_office` dentro Milano, di cui 95 con operatore "Poste Italiane", 8 senza operatore e 8 di corrieri (DHL, GLS, Nexive, Mail Boxes Etc., Posta Express). Quindi OSM sembra contare anche sportelli/punti non ufficiali o uffici più recenti; i due elenchi non coincidono perfettamente.
- **Esercizi di vicinato** (`vicinato`): 28.131 righe, 245 senza coordinate, 13.370 punti distinti (`duplicati_stesso_punto`=14.516: più negozi allo stesso civico), 8 dentro un parco. Il campo `settore_merceologico` è sporco: scritto in maiuscolo/minuscolo diverso e concatenato ("Non AlimentareAlimentare", "tabella speciale monopolio" = tabaccai, "tabella speciale farmacie", "tabella speciale carburanti"): per dire "negozio alimentare" serve normalizzare. Alimentari puri (`Alimentare`+`alimentare`): 5.005 righe; circa 10.557+8.130 sono non alimentari. Il campo `tipologia` è 'vicinato' in 28.039 righe, 'ND' in 91, 'media SV' in 1. `Area di Competenza` è sempre "VENDITA - In sede fissa". Il file è una fotografia dell'autorizzazione commerciale: negozi chiusi di fatto possono esserci ancora.
- **Tutti i set con ID_NIL**: il NIL dichiarato coincide con il NIL calcolato dal poligono tranne i pochi casi indicati sopra (`nil_dichiarato_diverso_dal_poligono` in `controlli_risultati.json`).

## 2. Civici con coordinate (`ds634-numeri-civici-coordinate`, cartella `civici`)

- File originale: `ds634_civici_coordinategeografiche_20261001_final_csv.zip` (4,6 MB), estratto in `civici\estratto\` (23 MB, 65.160 righe, 41 colonne, aggiornato al 1/10/2026). Licenza CC BY.
- `STATOCIVICO`: Applicato 57.405; Iter in corso 7.649; In attesa Fine Lavori 106. `RESIDENZIALE`: 1 = 47.238, 0 = 17.917, vuoto 5. Livello stradale quasi sempre (65.123 su 65.160).
- **Applicati**: 57.405 punti, tutti distinti; **numeri civici distinti** (chiave `CODICE_VIA`+`NUMERO`+`LETTERA`): 51.917, ed è questo il numero "circa 51.000". Applicati residenziali: 46.896. Mi sembra la scelta migliore tenere gli "Applicati" e decidere in fase 2 se partire da 51.917 (numeri) o da 57.405 (punti con i "barrati").
- Coordinate in gradi: **`LONG_WGS84` / `LAT_WGS84`** (con il punto). **Trappola**: le colonne `WGS84_X`/`WGS84_Y` si chiamano "WGS84" ma contengono metri UTM 32N (es. `514817,0392`), con la virgola decimale; le colonne `GAUSSB_X/Y` sono Gauss-Boaga, `WEBMERC_X/Y` Web Mercator.
- Controlli: 0 coordinate mancanti, 1 punto fuori dal confine del Comune, 2 senza `ID_NIL` (anche fuori da ogni poligono NIL), nessun `IDMASTER` duplicato, `ID_NIL` dichiarato = NIL del poligono per tutti. Applicati per NIL: da 12 a 2.902.
- Nel file **non c'è il CAP**: per i redditi serve stimarlo (vedi sotto).

## 3. Redditi (Irpef sub-comunale) e come collegarli ai NIL

- Dataset: `ds1590` (anno di imposta 2019), `ds1830` (2020), `ds2275` (2021), `ds2734` (2022), `ds2946` (2023), `ds3009` (2024, caricato 26/8/2026): cartelle `redditi_<anno>_ai<anno-imposta>`. CSV con 4 colonne: `Anno di imposta`, `CAP`, `Redditi e variabili Irpef`, `Importi`. Licenza CC BY. **Sono 6 anni (2019-2024); più indietro non c'è un dataset sub-comunale** (quelli del 2000-2018 sono solo a livello comunale: `ds941`...`ds1267`, non scaricati).
- **Zone: 38 CAP**, da 20121 a 20162 (stessi 38 in tutti gli anni). Nessun dato per NIL, né per sezione di censimento.
- 43 variabili nei primi cinque anni, 45 nel 2024: per ogni tipo di reddito un numero di contribuenti (`- Frequenza`) e un importo (`- Ammontare in euro`), più le classi di reddito complessivo (fino a 10.000, 10-15, 15-26, 26-55, 55-75, 75-120, oltre 120 mila euro). Il "reddito medio" non è dato: va calcolato come `Reddito complessivo - Ammontare in euro` / `Reddito complessivo - Frequenza` (o diviso per `Numero contribuenti`). Il "Numero contribuenti" è di chi presenta dichiarazione, non di tutti i residenti. Esempio 2024 (`ds3009`): `Numero contribuenti` da 13.625 (CAP 20136) a 46.726 (CAP 20146).
- **Collegamento CAP → NIL.** Non ho trovato i confini dei CAP né sul portale (cercato "CAP") né in OSM (nessuna relazione `boundary=postal_code` per Milano: 0 risultati). Ho quindi usato i 27.721 punti (vicinato, farmacie, poste, medici) che hanno **sia CAP sia NIL** (`collegamento_CAP_NIL_tabella_punti.csv`) e i civici (`collegamento_CAP_NIL_tabella_civici_stimati.csv`, CAP del punto noto più vicino).
  - La tabella CAP × NIL ha 186 celle non vuote (punti) o 233 (civici stimati): un NIL tocca più CAP e viceversa.
  - Solo 1 CAP su 38 ha un NIL dominante ≥ 90%; in media il NIL più frequente di un CAP ne copre il 56,6% dei punti. Nell'altro verso (NIL → CAP) 44 NIL su 87 hanno un CAP che ne copre ≥ 90%, ma 44 NIL toccano due o più CAP con almeno il 10% ciascuno; in media il CAP dominante di un NIL copre l'81,9% dei punti (81,3% con i civici).
  - Test sul CAP stimato col punto più vicino (12.839 punti distinti, ciascuno escluso da sé stesso): lo stesso CAP nel 96,6% dei casi. Dei 57.405 civici applicati, 47.901 hanno un punto con CAP noto entro 100 m (mediana 37 m, 95° percentile 192 m).
  - **Conclusione:** il confronto con i redditi si fa **a livello di CAP (38 zone)**: punteggio dei servizi medio per CAP, calcolato sui civici assegnati a ciascun CAP (pesati con i residenti stimati), contro reddito per contribuente di quel CAP. Distribuire i redditi sui NIL richiederebbe ipotesi (peso per superficie o per residenti) e darebbe false precisioni; se serve, farlo come analisi secondaria e dichiararlo.
- Il CAP stimato per i civici resta una stima (96,6%): i confini veri non sono scaricabili (Poste Italiane non li pubblica liberamente). Non fatto: ricerca di confini CAP su altre fonti (ISTAT, Regione Lombardia), da valutare se serve più precisione.

## 4. Popolazione per quartiere (NIL)

- `ds27-popolazione-residenti-cittadinanza-quartiere-serie-storica` (cartella `pop_cittadinanza_quartiere`): `ds27_pop_sto_quartiere.zip` (13 MB), estratto `estratto\ds27_pop_sto_quartiere.csv` (164 MB, 3.131.527 righe). Campi: `Anno` (1999-2025), `IdNil`, `Nil`, `Eta` (0-99 e "100 e più"), `Genere`, `Cittadinanza`, `Residenti`. Licenza CC BY.
  - **Ultimo anno: 2025, 1.399.079 residenti** (somma di `Residenti`, `Anno`=2025), in **87 NIL su 88**: manca il NIL 8 `PARCO SEMPIONE` (nessun residente). Per i NIL più piccoli i numeri sono bassi (min 38 residenti nel 2025, max 61.964).
  - Si può ricavare per ogni NIL: totale, età (anno per anno), genere, cittadinanza. Non c'è il reddito.
- `ds205-sociale-caratteristiche-demografiche-territoriali-quartiere` (cartella `pop_caratteristiche_quartiere`): 2011-2024, 1.243 righe, totale 2024 = 1.407.044 (campo `Totale`), con `Minori`, `Stranieri`, `65 e +`, `80 e +`, numero di scuole, `Area (metri quadrati)`. Ha 89 righe per anno: l'ultima è "N.D." (senza NIL, `Totale` vuoto). Utile per la superficie.
- Differenza di data: ds27 arriva al 2025, ds205 al 2024, i redditi sono del 2024 (anno di imposta) → per un confronto coerente usare 2024 per tutti.

## 5. Confini

- NIL vigenti (`ds964-nil-vigenti-pgt-2030`, cartella `nil_vigenti`): `ds964_nil_wm.geojson` (88 poligoni, 1 MB; nonostante "wm" nel nome le coordinate sono in gradi EPSG:4326) e `ds964_nil_wm_4326.csv` (centroidi). Valido dal 5/2/2020, fonte PGT Milano 2030. Licenza CC BY. Campi `ID_NIL`, `NIL`. Esiste anche la versione "OBSOLETI" (`ds61`, non scaricata).
- Confine del Comune (`ds2841-confini-amministrativi-del-comune-di-milano`, cartella `confine_comune`): `confine_comune_milano_layer_0_confine_comune_milano.geojson`, 1 poligono, 1,9 MB, EPSG:4326, 19.553 vertici; la superficie calcolata dal poligono è circa 180,6 km². Attenzione: i campi `Shape_Area` (369.827.250) e `Shape_Length` (155.386) valgono circa il doppio e non sono in m² reali: non usarli. Licenza CC BY.

## 6. Rete pedonale (OpenStreetMap)

- **Già scaricata dalla filiera 7** (`..\bici-auto-mezzi\`): non copiata, solo referenziata.
  - `C:\Users\davide\Desktop\ClaudeTower\milano-in-dati\bici-auto-mezzi\raw\osm_milano\milano_buffer.osm.gz` (17,9 MB, formato XML OSM compresso). Riquadro: lat 45,350-45,572, lon 8,99-9,33 (dichiarato nell'intestazione `<bounds>`; i nodi vanno da 45,35 a 45,572 e da 8,99 a 9,33): copre tutto il Comune con circa 2,5-3 km di margine. Contiene 779.196 nodi, 181.476 strade (way con tag `highway`), 4.469 relazioni (restrizioni/rotte bici). Estratto da `lombardia-latest.osm.pbf` (356 MB, Geofabrik, nella stessa filiera in `raw\osm_lombardia\`, scaricato 29/10/2026 17:21).
  - Percorribili a piedi: `footway` 73.376 tag, `residential` 24.802, `service` 33.415, `pedestrian` 2.866, `path` 2.927, `steps` 3.309, `crossing` (nodi) 40.175 ecc. (conteggio dei tag `highway=*` nel file, nodi e strade insieme). Le strade sono troncate al riquadro.
  - Sistema di riferimento: lat/lon OSM. Licenza ODbL: attribuzione obbligatoria, ridistribuzione con la stessa licenza. Se serve ritagliare di nuovo: comando in `..\bici-auto-mezzi\STATO.md`.
- **Limite:** il ritaglio tiene solo le strade e i nodi relativi (nessun punto d'interesse), per questo i servizi del bordo vanno presi dal file seguente.

## 7. Effetto bordo e punti di interesse OSM

- File: `raw\osm_poi\overpass_poi_milano.json` (2,9 MB) = una sola interrogazione Overpass (`scripts\overpass_poi.py`), data base OSM 29/10/2026 16:36 UTC, rettangolo lat 45,36-45,56 / lon 9,00-9,32, 11.518 elementi. Tabella estratta e classificata: `raw\osm_poi\osm_poi_milano_estratto.csv` (campo `fascia`: dentro il Comune / fuori entro 1.500 m / fuori oltre).
- **Comuni confinanti** (confini OSM `admin_level=8`, `raw\osm_poi\overpass_comuni_admin8.json`, 3 MB; confinante = un vertice a meno di 150 m dal confine): Rozzano, Opera, Assago, San Donato Milanese, Buccinasco, Cesano Boscone, Peschiera Borromeo, Settimo Milanese, Segrate, Pero, Sesto San Giovanni, Novate Milanese, Baranzate, Trezzano sul Naviglio, Cusago, Corsico, Rho, Vimodrone, Cologno Monzese, Cormano, Bresso, Arese, Bollate, Cornaredo (24). Vicini ma non confinanti (entro 3 km): San Giuliano Milanese (616 m), Cinisello Balsamo, Pieve Emanuele, Cusano Milanino, Locate di Triulzi, Bareggio, Pioltello, Gaggiano, Paderno Dugnano, Cernusco sul Naviglio, Cisliano, Pregnana Milanese, Basiglio, Zibido San Giacomo, Senago. (La verifica è fatta sui vertici, non è una verifica ufficiale dei confini.)
- I servizi di questi comuni **non sono nei dati del Comune**. Chi abita al margine rischia un punteggio più basso solo perché il servizio più vicino è oltre il confine. OSM può riempire il bordo: nel rettangolo, fra 0 e 1.500 m fuori dal confine ci sono (campo `fascia`=`fuori_entro_1500m`, `collegamenti_risultati.json`, `OSM_poi_per_tag_e_fascia`): `amenity=pharmacy` 90, `amenity=school` 125, `amenity=kindergarten` 72, `amenity=library` 27, `amenity=doctors` 37, `amenity=post_office` 27, `amenity=marketplace` 10, `shop=supermarket` 77, `shop=bakery`/`butcher`/`greengrocer`/`convenience` (non riportati qui), `leisure=park` 337, `leisure=garden` 550, `leisure=sports_centre` 99, `leisure=swimming_pool` 107.
- **Non riempito ancora**, come da mandato: solo valutazione. Limiti di OSM: le scuole con tag `amenity=school` includono scuole di ogni grado senza una distinzione unica; i medici di base di fuori non sono su OSM in modo completo (`doctors` 37 entro 1,5 km); `amenity=post_office` mescola uffici e punti Poste/corrieri. Per scuole e farmacie OSM è il candidato migliore per il bordo (le farmacie OSM coincidono con quelle del Comune per il 98%, 413/422).
- Licenza OSM: ODbL (attribuzione, stessa licenza se si ripubblica).

## 8. Licenze e ripubblicazione

- Dataset del Comune: **CC BY** (si può ripubblicare citando la fonte), eccetto: **farmacie CC0** (libere) e **medici di base CC BY-NC (uso non commerciale: non ripubblicare il grezzo, e comunque contiene nomi e date di nascita dei medici)**; `ds1863` e `ds1582` (scuole 2020/21) hanno licenza "altro (attribuzione)".
- Il file `ds27` e il CSV dei civici sono grandi (164 MB e 23 MB estratti): se si ripubblica qualcosa, solo risultati aggregati, non il grezzo.
- OSM: ODbL.

## 9. Cosa non ho fatto / aperto

- Non ho scaricato i file JSON/RDF dei dataset (solo CSV e GeoJSON, che bastano).
- Non ho cercato i confini dei CAP su fonti diverse da Comune e OSM.
- Nessun calcolo di tempi di cammino (fase 2).
- Non ho scaricato `ds709` (servizi integrativi all'infanzia), né le liste di scuole paritarie più recenti (esistono per anno scolastico: `ds2286` infanzia paritarie 2021/22, `ds1582` 2020/21 qui scaricata). Le paritarie recenti sono già nei file scuole 2025/26 (`PARITARIA`, `TIPO` privati/enti religiosi).
- Il campo `Shape_Area` del confine comunale è circa il doppio della superficie vera (180,6 km² calcolati dal poligono): la superficie va calcolata dal poligono.
- I file `scuole_paritarie_2020`, `biblioteche_loc_2007` e `biblioteche_rionali_2013` sono solo di confronto: non ho fatto i controlli geografici su di loro (colonne e righe sì).
