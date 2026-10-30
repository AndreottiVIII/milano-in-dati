# NOTE - L'acqua del sindaco, zona per zona (fase 1: raccolta e controllo)

Data di lavoro: 30 ottobre 2026. Nessun grafico, nessuna pagina. Tutto in locale, niente git.
Regola di tono: se un valore e' sotto il limite di legge, l'acqua e' conforme. Mai linguaggio di rischio.

## 1. Le fonti (tutte dal portale dati.comune.milano.it, CKAN, senza login)

Ricerca fatta con l'API `package_search` (parole: "analisi dell'acqua", "trimestre", "perdite", "acquedotto", "potabile", "rete idrica") e con `package_list` (2.611 dataset in tutto). Ho scaricato 15 dataset = 30 file (CSV + JSON di ognuno, il JSON di ds1827 e' uno zip), totale 13,3 MB in `raw\<dataset>\`. Elenco con dimensioni e licenze: `pulito\inventario_fonti.csv`; elenco grezzo: `raw\_inventario.json`. Comando per rifare: `scripts\01_scarica.py`.

| Dataset (CKAN) | Che cosa contiene | Periodo | File (byte) |
|---|---|---|---|
| ds1828, ds1829, ds1861, ds1915, ds1948, ds2970 "Analisi dell'acqua 2021 ... 2026" | un valore per parametro, zona MM, mese (colonne `parametroMisurato, limitiLegge, valoreRilevato, unitaMisura, zonaNome, zonaId, mese, anno, dataCaricamento, info`) | gen 2021 - set 2026 (67 mesi su 69 attesi, vedi sotto) | CSV da 142.791 a 215.103 byte, 576-864 righe ciascuno |
| ds679 (4T 2018), ds737 (2T 2019), ds712 (4T 2020), ds1586/1605/1646/1670 (1T-4T 2021) "Ambiente: Analisi dell'acqua N trimestre" | un solo valore per parametro per tutta Milano ("Acqua di Milano"), senza zona e senza mese (colonne `Parametro, Limiti di legge, Acqua di Milano, Unita' di misura`) | 7 trimestri sparsi: 2018-Q4, 2019-Q2, 2020-Q4, 2021-Q1..Q4 | CSV di ~590 byte, 18 righe ciascuno |
| ds1827 "civici aggregati per zone MM" | civico -> zona MM (+ municipio, NIL, coordinate) | foto del 2022 | `civici_zone_mm_no_dupl.csv`, 8.258.347 byte, 62.587 righe |
| ds1571 "Acqua immessa, erogata e perdite idriche - Anno 2018" | 1 sola riga | 2018 | CSV 220 byte |

Non esistono altri trimestri (1T-3T 2018, 1T/3T/4T 2019, 1T-3T 2020): non ci sono sul portale. Non esiste un dataset con i **poligoni** delle zone MM (cercato per "zone", "milanoblu", "acquedotto"): le zone vanno ricostruite dai civici (vedi sotto).
Extra visti ma NON scaricati (fuori mandato): ds502 fontanelle, ds625 case dell'acqua, ds523 consumo di acqua pro capite 2000-2011.

**Licenza.** Tutti i dataset sono `cc-by` su CKAN; per le analisi e per ds1827 la risorsa dichiara CC BY 4.0 (A21_CCBY40), per ds1571 CC BY 3.0 IT (A23_CCBY30IT): la fonte vera dei dati di ds1571 e' ISTAT (tavola 17 GMA 2021), il Comune li ha estratti. Si possono ripubblicare citando la fonte ("Comune di Milano - dati.comune.milano.it, CC BY 4.0"; per le perdite anche ISTAT). Il file dei civici del Comune (ds634, in `citta-15-minuti`) e' letto soltanto, non copiato.

## 2. Il problema degli accenti (per il JOURNAL)

Controllati byte per byte tutti i CSV e JSON di dati. Risultato: **solo 3 file hanno un problema**, gli altri sono UTF-8 pulito (nessun "Ã¨" da nessuna parte; il "\x88" non c'e').

1. **`getdatiqualitaacqua_2024.csv` (e anche il suo .json)**, solo le righe di **dicembre 2024** (48 righe, 16 campi): doppia codifica **cp850 -> letto come cp1252 -> salvato in UTF-8**. Segni: "µ" appare come `æ` (cp850 0xE6), "°" come `ø` (0xF8), "à" come `…` (0x85, che in cp1252 e' i puntini). Esempi: `æg/l`, `æS/cm`, `øF`, `Residuo Fisso A 180ø`, `Conducibilit…`, `Unit… pH`. Riparazione: `testo.encode('cp1252').decode('cp850')` applicata ai campi che contengono uno di quei tre caratteri.
2. **`ds737_qualita_acqua_.csv`** (2T 2019): una sola parola, `conducibilitŕ` (ŕ = U+0155). E' una "à" scritta in cp1252 e letta come cp1250. Riparazione: `encode('cp1250').decode('cp1252')`. (Lo stesso difetto e' nel .json di ds679, che non uso.)
3. **`ds679_analisi_acqua.csv`** (4T 2018): non e' UTF-8 ma **cp1252** (byte singoli 0xE0, 0xB0, 0xB5). Letto come cp1252 e' corretto. Il suo .json invece e' UTF-8 corretto (tranne la parola del punto 2).

Altre sporcizie di testo: spazi non separabili (U+00A0) nei limiti ("valori consigliati", "da  6,5 a 9,5": ripuliti); `Unita'` e `conducibilita'` con apostrofo al posto della "à" nei trimestrali 2020-2021 (normalizzati al nome del parametro); l'unita' della conducibilita' nei mensili e' scritta `µS/cm a 20°` (manca la "C"). Dopo le riparazioni nei campi tenuti restano solo `°`, `à`, `µ`, tutti attesi (controllo automatico nello script). Dettaglio: `pulito\_controlli\codifica_riparazioni.csv`, `pulito\_log_pulizia.txt`.

## 3. Valori sotto la soglia di rilevabilita' ("<0,05")

Tengo il testo originale (`valore_testo`), poi `sotto_soglia` = 1, `soglia` = numero dopo il "<", e `valore` VUOTO. Mai convertito in 0 e mai nella soglia.
- Sul totale: 1.239 righe su 4.699 misurate sono sotto soglia = **26,4%** (nei soli mensili 1.200 su 4.573 = 26,2%).
- Per parametro (quota sotto soglia sulle misurate): ammonio 100%, fluoruri 100%, nitriti 100% (in tutta la serie non c'e' mai un numero), manganese 91%, cloro residuo 56%, arsenico 33%; tutti gli altri 0%. File: `pulito\_controlli\sotto_soglia_per_parametro.csv`.
- **Trappola: la soglia cambia nel tempo** (cambia il laboratorio/metodo, non l'acqua). Ammonio da <0,10 a <0,05; nitriti da <0,20 a <0,05; fluoruri da <0,5 a <0,15; cloro residuo da <0,01 a <0,04; manganese da <1 a <1,25 (sale!). Il cambio e' nel 2022 (convivono nello stesso anno). Quindi la "quota sotto soglia" per anno non si puo' confrontare e non si puo' mai fare un grafico delle soglie come se fossero valori. File: `soglie_sotto_limite_per_parametro_anno.csv`.
- Scritti anche con il punto ("<0.10", "<0.5") nei file 2021, 2024 (e dic 2024): tutti letti.
- 4 valori di manganese "0" (mag-giu 2023, NE/NO/SO): sono quasi certamente "sotto soglia" scritti 0. Li tengo come numero ma con una nota (`nota_valore`).

## 4. La tavola pulita `pulito\analisi.csv` (4.926 righe, 33 colonne, separatore `;`, UTF-8)

- 4.800 righe mensili per zona (2021-01 .. 2026-09) + 126 righe trimestrali "Tutta Milano" (7 trimestri x 18 parametri). Le righe trimestrali hanno `periodo_tipo = trimestre`, `zona_codice = MI`, `zona_id` vuoto; NON si sommano ai mensili (nel 2021 si sovrappongono).
- Colonne chiave: `periodo` (2024-03 o 2021-Q2), `anno`, `mese`, `trimestre`, `data_riferimento`, `zona_codice/nome/id`, `parametro` (nome normalizzato), `valore`, `unita`, `sotto_soglia`, `soglia`, `qualita_dato` (ok / sotto_soglia / non_misurato / anomalo), `valore_testo` (originale), `limite_testo`, `limite_tipo` (legge / consigliato / nessuno), `limite_min`, `limite_max`, `entro_limite_legge`, `entro_valore_consigliato`, `data_caricamento`, `file_origine`, `riga_origine`.
- **18 parametri** (nomi uniformati; unita' uniformate): pH; residuo fisso a 180 °C (mg/L); durezza (°F); conducibilita' a 20 °C (µS/cm); calcio, magnesio, sodio, potassio, bicarbonati, cloruri, solfati, fluoruri, nitrati, nitriti, ammonio, cloro residuo (mg/L); arsenico, manganese (µg/L). Nomi: nei trimestrali sono minuscoli e "bicarbonato", nei mensili "Bicarbonati"; "Cloro Residuo" ecc. Nessun parametro e' cambiato nome o unita' in modo sostanziale (controllo automatico: 1 sola unita' per parametro dopo la normalizzazione). `pulito\parametri_info.csv` contiene la spiegazione in italiano di ogni parametro (colonna `info` dei file, un solo testo per parametro).
- **Limiti.** Cloruri 250, solfati 250, sodio 200, potassio 10, nitrati 50, nitriti 0,5, ammonio 0,5, fluoruri 1,5, arsenico 10, manganese 50, conducibilita' 2500, pH 6,5-9,5 sono "limiti di legge" come li chiama il file. Durezza 15-50 °F, residuo fisso 1500 mg/L (asterisco) e cloro residuo 0,2 (asterisco) sono solo **valori consigliati** (i trimestrali lo scrivono: "valori consigliati", "valore max consigliato", "valore consigliato 0,2"). Calcio, magnesio, bicarbonati: "non previsto". Per questo ho due colonne separate, `entro_limite_legge` e `entro_valore_consigliato`. Il cloro residuo 0,2: il file dice "massimo consigliato", ma nella pratica quel valore e' spesso citato come minimo: **da verificare con MM prima di scriverlo in pagina**. Due valori (1,43 mg/L ott 2024 NE; 1,33 mg/L set 2026 SO) sono sopra quel 0,2 consigliato: sono valori di cloro, non un superamento di legge.
- Valori fuori dai limiti di legge in tutta la tavola: **zero** (controllo: `valori_oltre_limite.csv` contiene solo i 2 casi di cloro "consigliato"). Nessuna riga sotto soglia con soglia piu' alta del limite.
- Duplicati: nessuno (chiave periodo + zona + parametro; nessuna riga identica).
- Valori estremi (z robusto > 6): 14, quasi tutti cloruri/solfati di singoli mesi e i due cloro sopra; elencati in `valori_estremi_z_robusto_oltre_6.csv`, NON tolti.

## 5. Trappole dei dati (da non dimenticare)

1. **Lacune nei mesi**: mancano **novembre 2025** e **maggio 2026** per intero. Ottobre 2026 non c'e' ancora. Il 2026 va da gennaio a settembre.
2. **Dicembre 2024 e' strano**: solo 3 zone (manca Sud-Ovest), Sud-Est ha 12 parametri su 18, il campo `info` contiene "Lorem ispum" (testo finto), data di caricamento 15/06/2024 (sei mesi PRIMA del mese a cui si riferisce) e proprio queste righe hanno la codifica sbagliata. Va trattato come dato sospetto/provvisorio, non come serie regolare.
3. **`dataCaricamento` non e' una data di pubblicazione affidabile**: ottobre 2021-aprile 2022 risultano caricati tra marzo e maggio 2021, dicembre 2025 risulta caricato il 14/01/2025 (probabile refuso per 2026), ecc. Elenco in `caricamento_prima_della_fine_del_mese.csv`. Non usarla per niente. Settembre 2021 ha una data diversa quasi per ogni riga (dal 9 ottobre al 28 dicembre 2021): date evidentemente generate.
4. **Il 2024 e' un anno "a metà" per i parametri**: il 24% delle righe del 2024 e' `-` (non misurato; 227 righe in tutto, di cui 24 a gennaio 2025). Nel 2024 (e a gennaio 2025) i parametri sono misurati a rotazione, in due gruppi: gruppo A = ammonio, cloruri, fluoruri, nitrati, nitriti, solfati (6); gruppo B = arsenico, calcio, durezza, magnesio, manganese, potassio, sodio (7). Ogni mese ne manca uno dei due gruppi (si misurano 11 o 12 parametri su 18; pH, residuo fisso, conducibilita', bicarbonati e cloro sempre). Quindi per calcio, magnesio e durezza nel 2024 ci sono valori solo in alcuni mesi (e per zona in modo diverso, vedi `parametri_misurati_per_mese_zona.csv`). `-` NON e' zero: e' "non misurato" (`qualita_dato = non_misurato`).
5. **Valori ripetuti**: nel 2021 il 74% dei valori e' identico a quello del mese prima (stessa zona, stesso parametro): i valori mensili 2021 sono a blocchi di 2-3 mesi uguali, cioe' sono in pratica trimestrali. Nel 2022 il 15%, 2023 30%, 2024 14%, 2025 44%, 2026 49% (es. gennaio e febbraio 2025 hanno gli stessi calcio e durezza). Non e' un errore di lettura: e' come il Comune pubblica. Impatto: la "stagionalita'" mensile non e' misurata mese per mese in tutti gli anni. Controllo: `valori_uguali_al_mese_precedente_per_anno.csv`.
6. Due valori non leggibili tenuti ma NON numerici (`qualita_dato = anomalo`): calcio NO maggio 2022 = `7'`; cloro residuo SE ottobre 2024 = `>0,04` (probabile "<0,04" scritto male). Non li ho "corretti".
7. Decimali con virgola e con punto mescolati (es. "0,2*" e "0.2*", "Da 6.5 a 9.5"); asterischi sui limiti; tutti normalizzati ma il testo originale e' in `valore_testo` / `limite_testo`.
8. Ordine delle righe: nei JSON 2021-2024 le righe sono in ordine diverso dai CSV. Confrontati per chiave: CSV e JSON sono identici in tutti i campi di dati (0 celle diverse). Uso i CSV.
9. Controllo di coerenza: le medie mensili 2021 delle 4 zone sono vicine ai 4 valori trimestrali "Tutta Milano" 2021 (differenza mediana 0,9%, massima 12,5% su potassio che vale 1-2 mg/L, quindi arrotondamento). `confronto_2021_trimestrale_vs_mensile.csv`.
10. I valori sono di **4 zone**, non dei singoli quartieri: ogni zona e' una grande area di rete (Nord-Ovest id 6, Sud-Ovest id 15, Sud-Est id 16, Nord-Est id 18). I codici id non sono mai cambiati nel tempo e i nomi coincidono con quelli dei civici ("Milano Nord Ovest" = "Nord-Ovest").
11. Sulle differenze tra zone: sono differenze tra acque diverse tutte conformi (durezza tra 20 e 36 °F in tutta la serie, sempre dentro 15-50). Vietato dire "peggiore/migliore" o "a rischio".

## 6. Zone e indirizzi

- **4 zone MM**, nessun poligono ufficiale. Il file dei civici (ds1827, 62.587 civici, 8 senza zona) assegna ogni civico a una zona. Municipio -> zone: il 4 e' tutto Sud-Est, l'8 e il 9 tutto Nord-Ovest, il 6 tutto Sud-Ovest; il 1 contiene tutte e 4 le zone, il 2/3/5/7 ne hanno due.
- Le zone sono **spazialmente compatte**: controllo a vicini (7 civici piu' vicini): il 99,68% dei civici ha la stessa zona della maggioranza dei vicini; solo lo 0,18% ha il vicino piu' prossimo in un'altra zona. Quindi i confini esistono davvero e si possono ricostruire. File: `zone_civici_incoerenti_con_i_vicini.csv` (quelli che non tornano).
- **Centro storico**: il confine passa dentro il quartiere: il NIL Duomo ha civici in tutte e 4 le zone (50% Sud-Ovest), Stazione Centrale 52%/48%, Guastalla 73%, Magenta-S.Vittore 64%, Stadio-Ippodromi 60%. 72 NIL su 88 sono interamente in una zona. In centro anche la stessa piazza (Piazza del Duomo) ha civici in zone diverse: con il solo quartiere non si puo' rispondere, serve l'indirizzo. `nil_zone.csv`.
- **Zone approssimate**: celle di 100 m classificate con i 15 civici piu' vicini, levigate, ritagliate sul confine del Comune: `zone_approx.geojson` (4 poligoni, EPSG:4326, etichettati come APPROSSIMATI) e `zone_celle.csv` (18.802 celle con confidenza). Aree: Nord-Ovest 60,7 km2 (33%), Sud-Ovest 56,6 (31%), Sud-Est 51,4 (28%), Nord-Est 14,1 (8%). Il Nord-Est ha l'8% dell'area ma il 16% dei civici (edificato fitto). Sono ricostruzioni, **non confini ufficiali**: 292 celle (1,6%) hanno confidenza < 0,7 (aree di confine) e 491 celle sono a oltre 500 m dal civico piu' vicino (parchi, aree non edificate: zona assegnata per vicinanza). Chiedere a MM i confini veri se si vuole una mappa definitiva.
- **Tavola per "scrivi il tuo indirizzo"**: `civici_zone.csv` (66.826 civici: 62.579 con zona MM ufficiale, 4.247 con zona STIMATA dai vicini perche' non erano in ds1827 o avevano zona vuota; colonna `fonte_zona` e `confidenza`; 4.199 hanno confidenza >= 0,9), `indirizzi_zona.csv` (55.242 coppie via + numero + lettera, ignorando le barre/interni, con zona prevalente: 3 soli indirizzi hanno civici in piu zone), `strade_zona.csv` (4.039 vie: 80 attraversano piu' zone; per queste una via sola non basta, serve il numero). Chiavi di ricerca senza accenti e minuscole: `chiave_via` (es. "via ciccotti ettore") e `chiave_via_token` (parole ordinate, senza "di/del/della": "via ettore ciccotti" e "via ciccotti ettore" danno lo stesso). Le coordinate arrivano dal file civici del Comune di ottobre 2026 (ds634, unite per `IDMASTER`: 60.921 civici su 62.587 combaciano); per gli altri 1.666 restano quelle di ds1827 (probabilmente civici soppressi). Le coordinate dei due file coincidono entro pochi cm (mediana).
- **Trappole indirizzi**: i civici contengono "barre" tipo `15N05`, `1M01`, `93P01` (negozi/interni): il numero che scrive un cittadino e' il numero base. 150 nomi di via compaiono in piu' municipi (vie lunghe che li attraversano o omonime): i 6 indirizzi che risultano in due municipi vanno disambiguati. I nomi nel Comune sono "COGNOME NOME" (es. "CICCOTTI ETTORE") mentre la gente scrive "Ettore Ciccotti".
- I 4.239 civici del file Comune senza zona in ds1827: 2.856 "Iter in corso", 1.298 "Applicato", 85 "In attesa fine lavori".

## 7. Perdite idriche (`pulito\perdite.csv`)

Una sola riga, **anno 2018** (periodo 1/1-31/12/2018): acqua immessa 213.352, erogata 182.776, pro capite 426 e 365, perdite 14,3%. Le unita' NON sono scritte nel file: ho dedotto **migliaia di m3** (volume) e **litri per abitante al giorno** (pro capite) perche' tornano i conti: (213.352-182.776)/213.352 = 14,33% (= 14,3 dichiarato) e 213.352.000 m3 / (426 L x 365 g) = 1.372.127 abitanti (Milano ha circa 1,37 milioni). Fonte: ISTAT tavola 17 GMA 2021. Niente serie storica, niente suddivisione per zona. Solo un numero di contesto.

## 8. Quello che manca / da chiedere

- Un confine ufficiale delle 4 zone (MM / Comune): da chiedere.
- Perche' nel 2024 meta' dei parametri manca a mesi alterni (cambio del piano di controlli? da chiedere).
- Il significato esatto di 0,2 mg/L di cloro residuo ("massimo" o "minimo consigliato").
- Altri trimestri 2018-2020 e altri anni di perdite: non pubblicati.

## 9. Come rifare tutto

`python -I scripts\01_scarica.py <strand>` (download, riprendibile) -> `02_pulisci.py <strand>` -> `03_zone.py <strand> <...\citta-15-minuti\raw\comune_milano>` -> `04_perdite_inventario.py <strand>`. Controlli e log: `pulito\_controlli\`, `pulito\_log_pulizia.txt`, `pulito\_log_zone.txt`.
