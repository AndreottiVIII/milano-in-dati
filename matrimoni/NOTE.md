# Matrimoni e separazioni - FASE 1 (raccolta, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web, nessun giudizio. Ogni numero dice file e campo. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di matrimoni> [<percorso assoluto di milano-in-dati>]` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`. Inventario di ogni fonte (righe, byte, licenza, cosa manca): `pulito/inventario.csv`.

## 1. In breve

1. **Fonti buone e aperte ce ne sono due**: il portale del Comune (10 dataset, CC-BY) e `demo.istat.it` (tavole pubbliche, CC BY 4.0, senza registrazione). L'Annuario statistico del Comune non c'e' tra gli open data (CKAN: 1 solo risultato, sulle imprese) e www.comune.milano.it risponde 403: non cercato oltre.
2. **Riti: 1948-2024 per il comune di Milano** (civile/religioso), **1930-2024 per l'Italia**. Quindi il sorpasso si vede bene: **a Milano i matrimoni civili superano i religiosi nel 2002, in Italia nel 2018: 16 anni dopo.** Nel 2024 a Milano i civili sono l'81,0% (ISTAT provincia: 79,1%), in Italia il 61,3%.
3. **Eta', cittadinanza e rito dettagliati ci sono solo per anni recenti.** Eta' degli sposi a livello di comune: solo 2021-2024 (classi di 5 anni). Cittadinanza: 2003-2024. Prima, per l'eta', ISTAT da' solo la provincia (2004-2024) e la regione (primo matrimonio, 1990-2024).
4. **Unioni civili: 2016-2024 dal Comune** (1.879 in totale), 2018-2024 da ISTAT.
5. **Separazioni e divorzi: mai a livello di comune.** ISTAT li da' per **provincia del tribunale** 2007-2024 (in tre sensi: vedi trappole); prima del 2007 per provincia non sono riuscito a scaricare nulla (volumi ISTAT su ebiblio.istat.it non raggiungibili, non archiviati su Internet Archive). Il Comune ha solo i 1.438 "scioglimenti" annotati nel 2018 (ds705), non confrontabili.
6. **La cosa piu' sorprendente** (sezione 5): i matrimoni civili di Milano non sono mai cresciuti. Sono 2.018 nel 2024, meno dei 3.308 del 1972. A scomparire e' stato il matrimonio in chiesa (10.525 nel 1961, 474 nel 2024).
7. **Trappole serie**: un refuso nel file storico del Comune (civili 2024), due dataset del Comune con descrizione sbagliata (ds132, ds1949), un anno ISTAT anomalo (2010), i confini della provincia (Monza), le "nozze di residenti" che non sono nozze a Milano. Sezione 6.

## 2. Fonti, una per una

Licenza dei dataset del Comune: nel catalogo CKAN `license_id = cc-by`, titolo "Creative Commons Attribution", link http://www.opendefinition.org/licenses/cc-by (versione non scritta; la home milanostatistica.comune.milano.it cita CC-BY 3.0 e 4.0). Autore: "Comune di Milano - Unita' Analytics e Open Data". Si puo' ripubblicare citando "Comune di Milano - dati.comune.milano.it". Licenza ISTAT: "Creative Commons - Attribuzione - versione 4.0" (https://www.istat.it/it/note-legali, letta il 1/11/2026): menzione di paternita', link alla licenza, indicare se modificato. Data di scaricamento di tutto: **1 novembre 2026** (`raw/download_log.csv`, con hash).

### 2.1 Comune di Milano (CKAN, `package_search` con 17 parole chiave: `raw/search_all.json`, 287 dataset trovati, 9 pertinenti piu' 1)

| id | Contenuto | Anni | Righe | Byte | Cosa manca |
|---|---|---|---|---|---|
| **ds1496** serie storica matrimoni | civili e religiosi per anno, comune di Milano, fonte "Anagrafe della popolazione residente" | 1948-2024 | 77 | 1.243 | solo rito; 2024 civili = 2218 (refuso, vedi 6.1) |
| **ds138** matrimoni celebrati a Milano | rito x cittadinanza marito x cittadinanza moglie | 2003-2020 | 306 | 11.028 | niente eta' (la descrizione dice "eta'", nel file non c'e'); 69 matrimoni senza cittadinanza (2005-2010) |
| **ds1947** idem, nuova serie | rito x cittadinanze | 2021-2024 | 60 | 2.275 | come sopra |
| **ds132** matrimoni "con almeno un coniuge residente" | rito x cittadinanze | 2011-2020 | 191 | 7.058 | descrizione sbagliata (6.2) |
| **ds1949** idem, nuova serie | rito x cittadinanze | 2021-2024 | 66 | 2.480 | idem; 2024 incompleto? |
| **ds1950** celebrati a Milano per eta' | classe di 5 anni marito x classe moglie | 2021-2024 | 474 | 14.611 | niente rito/cittadinanza; solo 4 anni |
| **ds1952** residenti per eta' | idem | 2021-2024 | 534 | 16.356 | righe "n.d" |
| **ds398** unioni civili celebrate a Milano | sesso della coppia, classe di eta' (10 anni) e cittadinanza dei due partner | 2016-2024 | 638 | 40.343 | niente regime patrimoniale, niente stato civile precedente, niente scioglimenti |
| **ds705** scioglimenti dei matrimoni 2018 | un record per scioglimento: sesso, anno di nascita, cittadinanza dei due coniugi | solo 2018 | 1.438 | 60.282 | niente anno del matrimonio, durata, figli, ne' se separazione o divorzio; solo coppie M+F |
| **ds361** indicatori famiglie e coppie (censimenti) | per Milano: coppie miste e non coniugate ogni 100 coppie | 1991, 2001, 2011 | 2.133 | 386.899 | 1991 non disponibile (e' "-") |

Aggiornamento dichiarato: ds1496, ds1947, ds1949, ds1950, ds1952, ds398 = ANNUAL; ds138, ds132, ds705, ds361 = NEVER (storici chiusi). Ultima modifica nel catalogo (`metadata_modified`): 8/5/2026 per tutti.

Non scaricati ma visti nell'elenco: ds1439-1442 (famiglie anagrafiche per tipologia 1999-2025, file da 340 KB a 6 MB; utili per "famiglie con una persona sola" ma non per matrimoni), ds301 (stato civile storico dei censimenti), ds1519/ds1638 (famiglie dei censimenti 2001/1991).

### 2.2 ISTAT demo.istat.it (tavole pubbliche; licenza CC BY 4.0)

Il sito risponde a un modulo web (POST su `https://demo.istat.it/app/RPCCerca.php`): l'ho usato come lo usa il browser, 32 richieste riuscite (piu' 3 andate in errore per un parametro sbagliato) a 2 secondi l'una, nessun login. I file sono in `raw/istat_demo/*.json` (risposta grezza). Non e' un'API documentata: puo' cambiare. Dettaglio per ogni richiesta in `pulito/inventario.csv` e `scripts/download_istat_demo.py`.

- **MA1 q1** "Matrimoni per comune e rito": **comune di Milano 2004-2024** (religiosi, civili, totale); anche Italia e tutti i comuni della provincia.
- **MA1 q3** indicatori di nuzialita' per **provincia** (Milano, Monza e Brianza, Italia): quoziente di nuzialita', % civili, % almeno uno straniero, % secondi matrimoni, tassi di nuzialita' e primo-nuzialita'. 2004-2024.
- **MA1 q4** eta' media al matrimonio per stato civile prima delle nozze, provincia di Milano e Italia, sposi e spose, 2004-2024.
- **MA3 q1 / q3** matrimoni per cittadinanza (tipologia di coppia) e per rito x tipologia, provincia di Milano, Monza, Lombardia, Italia, 2004-2024.
- **MA4 q1** matrimoni per rito, **Italia 1930-2024**; q3 tipologia di coppia 1996-2024; q4 classi di eta' dal 1865.
- **NU1** eta' media al primo matrimonio e tasso di primo-nuzialita', regioni e ripartizioni, 1990-2024 (file con 1981-2024).
- **UC4 q4** unioni civili nei grandi comuni (Milano 2018-2024, per sesso); **UC2 q1** per sesso e mese, provincia di Milano e Italia; UC4 q1 per ripartizione.
- Non scaricato: tavole sul "turismo matrimoniale" (MA3 q7), regime patrimoniale, titolo di studio, mese (MA1 q2, MA2) - per Milano erano a livello provinciale o regionale.

Anni disponibili: matrimoni 2004-2024 (prima, serie storiche nazionali; "indagine sui matrimoni" ISTAT dal 1926), unioni civili 2018-2024.

### 2.3 ISTAT separazioni e divorzi (file Excel pubblici su demo.istat.it/data/sepdiv/)

Scaricati in `raw/istat_sepdiv/` (14 file, 1,4 MB circa): serie storiche 2007-2024 (tavole 1.1-1.5 separazioni, 2.1-2.5 divorzi: regioni, per 1.000 abitanti, indicatori, classi di eta', **province**) e tavole 1.1 / 2.1 del 2011 e 2012 (per distretto di Corte d'Appello: Milano 2012 = 11.230 procedimenti di separazione conclusi, ma e' tutto il distretto, non comparabile con la serie provinciale). Anni 2008-2014 esistono come archivi/tabelle singole (non scaricati). Licenza CC BY 4.0. "Valori assoluti stimati": ISTAT stima i dati assenti.

### 2.4 Fonti provate e non utilizzabili

- **ISTAT esploradati (SDMX, https://esploradati.istat.it/SDMXWS/rest/...)**: due richieste (elenco dataflow) sono andate in timeout a 60-90 s. La documentazione ISTAT avverte: massimo 5 richieste al minuto per IP, oltre blocco di 1-2 giorni. Non ho insistito (e i dati che servivano c'erano gia' su demo.istat.it).
- **ISTAT ebiblio (annuari "Matrimoni, separazioni e divorzi" 1988-2006, con tavole per provincia e comune capoluogo)**: i PDF rimandano alla pagina di avviso di ISTAT; non ci sono copie su Internet Archive. Quindi nessun dato su separazioni e divorzi per provincia prima del 2007.
- **www.comune.milano.it (Annuario statistico)**: 403. **milanostatistica.comune.milano.it**: la pagina iniziale e' solo il rimando agli open data.
- **Chiesa/diocesi**: nessun dato sui matrimoni religiosi per sacramento o diocesi cercato (fuori dal perimetro dato).

## 3. Pulizia (scripts/build.py -> pulito/)

- Tutti i CSV del Comune sono in UTF-8 (ds361 in Windows-1252, letto cosi'). Separatore `;`.
- `rito_milano_1948_2024.csv`: anno, rito, `n_fonte`, `n_usato`, nota. L'unica correzione e' civili 2024: 2218 -> 2018, motivata in nota.
- `matrimoni_rito_cittadinanza_milano.csv`: ds138+ds1947 (perimetro `celebrati_a_milano`) e ds132+ds1949 (`almeno_un_coniuge_residente`) in una tabella unica: perimetro, anno, rito (cattolico, civile, evangelico, geova, israelita, altri_riti), cittadinanza marito/moglie (italiana/straniera/n.d.), n.
- `matrimoni_eta_milano_2021_2024.csv`: perimetro, anno, classe di eta' marito, classe moglie, n.
- `unioni_civili_milano_2016_2024.csv` (record per classe, cittadinanza) e `unioni_civili_per_anno_sesso_milano.csv`.
- `scioglimenti_2018_comune_milano_aggregati.csv`: ds705 ridotto ad aggregati (eta' = 2018 - anno di nascita, cittadinanza); nessun dato individuale nelle tabelle pulite.
- Tabelle ISTAT: `istat_*.csv` (rito, indicatori, eta' media, tipologia di coppia, primo matrimonio, unioni civili, separazioni e divorzi per provincia). Le cifre ISTAT sono testo con separatori diversi (`8.086` = migliaia nelle tavole MA3, `293,766` = migliaia in MA4, `403,9` = decimale in MA1): gestito per tavola.
- Riepiloghi (scripts/riepilogo.py): `tassi_per_mille_milano.csv`, `confronto_comune_istat_2004_2024.csv`, `coppie_miste_milano_2003_2024.csv`, `eta_sposi_milano_2021_2024.csv`, `residenti_vs_celebrati_2011_2024.csv`, `unioni_civili_riepilogo.csv`, `separazioni_divorzi_riepilogo.csv`, `covid_2020.csv`, `riepilogo.json`, `riepilogo_log.txt` (tutti i numeri stampati).
- **Denominatore** dei tassi: popolazione calcolata annuale del Comune (ds1494, copiata in `censimenti/pulito/popolazione_milano_annuale_1880_calcolata.csv`, campo `popolazione_calcolata`). Per il 2000-2024 c'e' anche la popolazione ISTAT di fine anno (`bilancio-comune/pulito/popolazione_milano.csv`, campo `pop_calcolata_istat_fine_anno`): i due tassi differiscono di pochissimo (2024: 1,77 contro 1,82 per mille). Salti nelle serie di popolazione: il 2002 (dopo il censimento 2001) e il 2012 (dopo il censimento 2011): i tassi tra 2001 e 2002 e tra 2011 e 2012 non sono perfettamente confrontabili.

## 4. Numeri principali (file e campo; scaricati il 1/11/2026)

### 4.1 Matrimoni celebrati a Milano per 1.000 abitanti (`pulito/tassi_per_mille_milano.csv`, colonna `per1000_ab_ds1494`; dati ds1496 + ds1494)
- 1948: 8.485 matrimoni (396 civili, 8.089 religiosi) = **6,7 per mille**.
- Massimo: **1963, 12.398 matrimoni, 7,5 per mille** (popolazione 1.657.640).
- 1972: 12.926 (3.308 civili, 9.618 religiosi), 7,4 per mille. 1990: 6.579, 4,6 per mille. 2002: 4.815, 3,9. 2010: 2.890, 2,2. 2019: 2.959, **2,1**. **2020: 1.529, 1,1 (minimo)**. 2024: 2.492, **1,8**.
- ISTAT (provincia di Milano, quoziente di nuzialita', `istat_indicatori_nuzialita_2004_2024.csv` campo `quoziente_nuzialita_per1000`): 3,5 (2004), 2,5 (2012), 2,2 (2019), 1,2 (2020), 2,1 (2024). Italia: 4,3, 3,4, 3,1, 1,6, 2,9. Milano ha un tasso piu' basso dell'Italia da sempre (2004-2024).
- Attenzione: "celebrati a Milano" include chi non ci risiede (stranieri, fuori sede). Per le nozze di milanesi ovunque celebrate c'e' la serie dei residenti 2011-2024 (sotto): 4,3 per mille nel 2011-2013, 3,4 (2019), **2,6 (2024, probabilmente incompleto)**.

### 4.2 Sorpasso civile / religioso
- **Milano: 2002** (`rito_milano_1948_2024.csv`, ds1496): nel 2001 civili 2.376 / religiosi 2.516, nel 2002 civili 2.502 / religiosi 2.313 (52,0% civili). **Italia: 2018** (`istat_italia_rito_1930_2024.csv`, MA4 q1): 2017 civili 94.715 / religiosi 96.572, 2018 civili 98.182 / religiosi 97.596 (50,1%). Anticipo di Milano: **16 anni**.
- Quota di civili: 25% a Milano nel 1972, in Italia nel 2001 (29 anni dopo); 50% Milano 2002 / Italia 2018; 75% Milano 2018 (poi 77,6% nel 2019, 81,0% nel 2024). In Italia il 75% non e' ancora raggiunto (61,3% nel 2024).
- Religiosi a Milano: 10.525 (1961, massimo) -> 474 (2024), cioe' il 4,5%.

### 4.3 Eta' al matrimonio
- Comune, solo 2021-2024, celebrati a Milano (`eta_sposi_milano_2021_2024.csv`, ds1950; eta' stimata con il centro della classe): sposi 43,5 (2021) -> 44,4 (2024), spose 39,9 -> 41,2. Sono tutti i matrimoni (anche secondi). Tra i matrimoni celebrati a Milano: **la moglie e' piu' grande del marito nel 12,7% (2024) e nella stessa classe nel 40,2%**; il marito ha almeno 10 anni piu' della moglie nel 19,9% dei casi; nel 41,3% hanno entrambi 40 anni o piu'.
- ISTAT, provincia di Milano, eta' media di tutti gli sposi (`istat_eta_media_al_matrimonio_2004_2024.csv`, `eta_media_totale`): sposi 36,4 (2004) -> 38,4 (2012) -> 41,6 (2019) -> **43,8 (2024)**; spose 31,0 -> 33,8 -> 36,5 -> **39,0**. Solo celibi/nubili: sposi 33,0 -> 39,4; spose 29,8 -> 36,4.
- **Primo matrimonio** (NU1, `istat_primo_matrimonio_lombardia_italia_1990_2024.csv`): Lombardia sposi 29,05 (1990) -> 31,24 (2000) -> 33,99 (2010) -> 36,54 (2019) -> **37,85 (2024)**; spose 26,27 -> 28,21 -> 31,02 -> 33,52 -> **34,94**. Italia: sposi 28,92 -> 37,13, spose 25,88 -> 34,25. Salto del 2020 (anno anomalo). Non c'e' il dato per il solo comune.
- Secondi o successivi matrimoni per lo sposo, provincia (campo `sposi_secondo_o_succ_pct`): 10,9% (2004) -> 20,5% (2024); Italia 8,4% -> 17,6%.

### 4.4 Coppie miste (cittadinanza)
- Celebrati a Milano, almeno uno sposo straniero (`coppie_miste_milano_2003_2024.csv`, da ds138/ds1947): **24,0% (2003) -> 35,3% (2008) -> 33,5% (2012) -> 40,0% (2019) -> 32,4% (2024)**. Coppie miste (uno italiano e uno straniero): 18,0% -> 29,5% (2019) -> 23,6%; entrambi stranieri: 6,1% -> 10,5% -> 8,9%.
- Per rito (2024): nei civili il 37,1% ha almeno uno straniero, nei religiosi il 12,7% (nel 2003: 43,8% e 3,8%). 
- Residenti (ds132/ds1949): 21,3% (2011), 32,3% (2019), 29,7% (2024).
- ISTAT provincia di Milano, `almeno_uno_straniero` su `totale` (MA3 q1): 20,9% (2004), 28,2% (2012), 32,8% (2019), 27,7% (2024). Italia: 12,3%, 14,8%, 18,6%, 16,9%. Cioe' a Milano le coppie con uno straniero sono quasi il doppio che in Italia.
- Censimenti (ds361, Milano): coppie miste 3,1% di tutte le coppie nel 2001, 4,2% nel 2011; coppie non coniugate 8,5% (2001) -> 12,5% (2011). Sono coppie in generale, non nozze dell'anno.
- Come cambia la composizione: dopo il 2019 la quota cala. Perche' non lo so: possibili effetti Covid (frontiere, viaggi) sui matrimoni di stranieri celebrati a Milano. Non affermarlo senza altri dati.

### 4.5 Unioni civili (dal luglio 2016)
- Comune, celebrate a Milano (`unioni_civili_riepilogo.csv`, ds398): 2016: 221 (anno parziale: la legge 76/2016 e' in vigore dal 5 giugno 2016), **2017: 388 (massimo)**, 2018: 249, 2019: 218, 2020: 109, 2021: 142, 2022: 166, 2023: 207, 2024: 179. Totale 2016-2024: **1.879**: 1.398 tra uomini (74%), 481 tra donne.
- Rispetto ai matrimoni celebrati nello stesso anno: 6-8 unioni ogni 100 matrimoni nel 2018-2024 (7,2 nel 2024); 13,9 nel 2017.
- ISTAT (UC4, MA1 non usato): Milano comune 257 (2018) ... 180 (2024), tra 5,9% (2022) e 9,5% (2019) di **tutte le unioni civili italiane** (Italia 2.808 nel 2018, 2.936 nel 2024), mentre Milano ha circa l'1,4% dei matrimoni italiani (2.493 su 173.272 nel 2024). Quota di coppie di uomini: Milano 72% (2024 Comune), Italia 55% (2024) e 64% (2018).
- Almeno un partner straniero: 29,1% (2016-2024); coppie miste (uno italiano e uno straniero) 25,8%. Eta' media stimata dei due partner 46,8 (centro classe; classi larghe 10 anni: prendere con cautela).
- **Dati che mancano**: scioglimenti di unioni civili (ISTAT li include nei "divorzi" dal 2024 con nota), regime patrimoniale, rito (le unioni sono sempre in comune).

### 4.6 Separazioni e divorzi (ISTAT, per provincia del tribunale; area "Milano + Monza e Brianza" per tenere uguale il confine)
(`separazioni_divorzi_riepilogo.csv`; da tavole ISTAT 1.5 e 2.5, "valori assoluti stimati")
- **Separazioni**: 6.559 (2007), 5.929 (2014), 5.639 (2015), **7.300 (2016)**, 6.786 (2019), 5.582 (2020), 6.210 (2021), 5.702 (2022), 4.815 (2023), **4.410 (2024)** (-35% su 2019). Italia: 81.359 (2007) -> 97.474 (2019) -> 75.014 (2024).
- **Divorzi**: 4.243 (2007), 3.675 (2014), 5.696 (2015), **8.291 (2016)**, 6.573 (2019), 4.796 (2020), 5.550 (2021), 5.888 (2022), 5.325 (2023), 5.782 (2024). **Tra il 2014 e il 2016 +126%** (Italia: 52.355 -> 99.071, +89%): il "divorzio breve" (L. 55/2015) e gli accordi fuori dal tribunale (D.L. 132/2014) hanno cambiato il modo di divorziare e di contare. Dal 2024 ISTAT inserisce nei divorzi anche gli scioglimenti di unioni civili.
- Dal 2022 i divorzi superano le separazioni nell'area di Milano (5.888 contro 5.702) e nel 2024 sono 5.782 contro 4.410; in Italia solo nel 2024 (77.364 divorzi contro 75.014 separazioni; nel 2022 erano 82.596 contro 89.907).
- Nel 2020: separazioni -17,7%, divorzi -27,0% rispetto al 2019 (a Milano+Monza); i matrimoni -48%.
- **Rapporto grezzo** tra eventi dell'anno e matrimoni dell'anno nella stessa area (campi `sep_su_100_matrimoni_milano`, `div_su_100_matrimoni_milano`): 2019: 72,5 separazioni e 70,2 divorzi ogni 100 matrimoni (Italia: 52,9 e 46,4). Non e' una probabilita' di rottura: i divorzi del 2019 vengono da matrimoni di anni diversi e da coppie che si sono sposate altrove.
- Tribunale = Tribunale di Milano (che copre buona parte della provincia). Le persone divorziate possono risiedere altrove.
- **Comune, solo 2018** (ds705, `scioglimenti_2018_comune_milano_aggregati.csv`): 1.438 scioglimenti annotati nei registri di Milano. Eta' media del marito 51,6 (mediana 51), della moglie 48,7 (48); moglie piu' grande nel 23,2% dei casi (333); entrambi italiani 1.149 (79,9%), uno solo italiano 266 (18,5%), nessuno italiano 23. Questi 1.438 NON sono i divorzi di Milano nel 2018: ISTAT conta 5.652 divorzi (provincia di Milano senza Monza) e 5.772 separazioni (`istat_separazioni_divorzi_province_2007_2024.csv`). Non e' chiaro cosa conti ds705 (annotazioni sugli atti di matrimonio tenuti dall'anagrafe di Milano? separazioni e divorzi insieme?).

### 4.7 Il tuffo del Covid (2020) (`covid_2020.csv`)
- Matrimoni celebrati a Milano: **2.959 (2019) -> 1.529 (2020), -48,3%**; civili -44,8% (2.297 -> 1.267); religiosi **-60,4%** (662 -> 262). Italia: -47,4% (184.088 -> 96.841); civili -28,9%, religiosi -67,9%.
- Matrimoni di residenti: -47,9% (4.739 -> 2.469). Unioni civili: -50,0% (218 -> 109). Separazioni -17,7%, divorzi -27,0% (Milano+Monza).
- Il rimbalzo 2021: 2.283 (-22,8% sul 2019). Nel 2023: 2.765 (-6,6%); nel 2024: 2.492 (-15,8% sul 2019). I civili nel 2023 (2.270) hanno quasi pareggiato il 2019 (2.297), i religiosi no (495 contro 662: -25%). In Italia nel 2024 i civili sono +9,8% sul 2019, i religiosi -23,2%.

## 5. La cosa piu' sorprendente

**I matrimoni civili di Milano non sono mai cresciuti. La storia "il civile ha preso il posto della chiesa" e' falsa: e' sparita la chiesa, e il civile e' rimasto fermo.**
- Civili: 396 (1948), 469 (1963), 1.460 (1971), **3.308 (1972)** e 3.419 (1973), poi 2.000-2.600 ogni anno per mezzo secolo (mediana 1972-2024: 2.297); nel **2024 sono 2.018, meno del 1972**. Per mille abitanti: 1,90 (1972), 1,80 (2000), 1,64 (2019), **1,43 (2024)** (`civili_per1000`).
- Religiosi: 7,20 per mille (1963) -> 0,34 (2024): 10.525 nozze in chiesa nel 1961, 474 nel 2024.
- Quindi il "sorpasso" del 2002 non e' il civile che sale: e' la chiesa che scende sotto un civile che c'era gia'. Il vero scatto del civile e' uno solo, il 1972 (da 1.460 a 3.308; il raddoppio e' identico in tutta Italia, da 15.591 a 30.674: coerente con la legge sul divorzio del 1970, ma la causa e' una mia deduzione, non dei dati).
- Seconda sorpresa, collegata: **il grosso delle nozze in chiesa dei milanesi non si celebra a Milano.** Nel 2011 i matrimoni religiosi (tutti i riti non civili) con un coniuge residente erano 2.780, contro 1.080 celebrati in citta' (compresi quelli di non residenti): almeno 1.700, il 61%, altrove (solo cattolici: 2.734 contro 1.055, stessa quota). Nel 2018: 64% (`pulito/residenti_vs_celebrati_2011_2024.csv`).
- Terza: nell'area di Milano i divorzi sono piu' che raddoppiati tra il 2014 (3.675) e il 2016 (8.291): cambio di legge, non di costumi.

## 6. Trappole

1. **Refuso nel file storico del Comune (ds1496)**: civili 2024 = 2218, ma ds1947 (somma delle quattro righe 1270+373+166+209), ds1950 (totale 2.492) e ISTAT (MA1: 2.018) dicono **2.018** (totale 2.493 ISTAT). Corretto in `n_usato` con nota. Gli altri anni 2003-2020 coincidono con ds138 al matrimonio, 2021-2023 con ds1947.
2. **ds132 / ds1949 non sono "celebrati a Milano"** come dice la descrizione: i numeri superano sempre i celebrati (2011: 5.823 contro 2.909). Sono matrimoni di residenti ovunque celebrati (l'ipotesi e' mia; la descrizione non lo dice). **Il 2024 (3.655 contro 4.511) e il 2019 (4.739 contro 5.359) sembrano incompleti**: religiosi di residenti 649 nel 2024 contro 1.105 nel 2023 (-41%) mentre quelli celebrati a Milano sono 455 contro 478. Non usare il trend dei residenti sull'ultimo anno.
3. **ISTAT comune di Milano contro Comune**: quasi uguali dal 2013 (differenze di 1-10 unita'), ma nel **2010 ISTAT ha 4.080 matrimoni contro 2.890 del Comune** (+1.190; religiosi 1.808 contro 1.139), nel 2009 -178, 2011 +152, 2012 -142 (`confronto_comune_istat_2004_2024.csv`). Il 2010 ISTAT e' un valore fuori traiettoria (3.183 -> 4.080 -> 3.061). Non e' chiaro quale sia giusto; ho usato il Comune per la serie lunga.
4. **Confini provinciali**: nelle tavole ISTAT su separazioni e divorzi Monza e Brianza e' un trattino fino al 2009 (dentro Milano) e ha dati dal 2010. Quindi **Milano scende da 5.712 a 4.577 separazioni dal 2009 al 2010 senza che sia successo nulla**. Ho fatto una serie "Milano + Monza e Brianza" (colonna `milano_piu_monza`). Le tavole ISTAT su matrimoni, invece, sono gia' ricostruite con i confini attuali (Monza separata anche prima).
5. **"Provincia" nelle separazioni/divorzi = provincia del tribunale (o dell'ufficio di stato civile), non residenza**; "valori assoluti stimati"; divorzi 2024 includono scioglimenti di unioni civili. Nessun dato per comune o per quartiere.
6. **Unioni civili 2016**: anno parziale (legge del 5/6/2016); il 2017 e' gonfiato dal primo anno pieno. ISTAT parte dal 2018 e conta per luogo di costituzione; Comune e ISTAT differiscono di poche unita' (249 contro 257 nel 2018, 179 contro 180 nel 2024). Nella tavola ISTAT UC2 ogni anno ha 12 righe mensili piu' una riga "Tutti i mesi": sommare tutto raddoppia i totali (errore evitato).
7. **Eta' media ISTAT = tutti i matrimoni, anche i secondi**: 43,8 anni lo sposo nel 2024. Per i primi matrimoni, in Lombardia, 37,85. Le classi di eta' del Comune sono di 5 anni: le medie sono stime col centro di classe.
8. **Formati**: ISTAT usa `8.086` (migliaia con punto) in MA3 e `293,766` (migliaia con virgola) in MA4; ds138 ha celle con cittadinanza vuota (69 matrimoni); ds1952 ha eta' "n.d". Etichetta rito: `Cattolico` nei dataset dettagliati, `religioso` in ds1496/ISTAT: ho unito evangelico, geova, israelita e altri riti nei "religiosi" per confrontare con ds1496 (controllato: coincide al matrimonio 2003-2020).
9. **ISTAT NU1**: il 1983 del Piemonte e' 48,84 anni di eta' media al primo matrimonio (impossibile; vicini 27-28): errore fuori dal periodo usato (1990-2024).
10. **ds705** (scioglimenti 2018): vedi 4.6; non confrontarlo con ISTAT.
11. **Popolazione**: due serie (ds1494 e ISTAT) con salti ai censimenti 2001 e 2011 (2012: 1.366.409 contro 1.263.087 ISTAT; i tassi 2012 variano del 8% a seconda della serie). Usata ds1494 per coerenza con il filone `censimenti`; la colonna ISTAT e' accanto.
12. **Rilevazioni**: l'Italia nel 2020 ha 96.841 matrimoni (MA4/MA1); i numeri 2021-2024 sono quelli piu' recenti e potrebbero essere ritoccati.

## 7. Cosa puo' mostrare una pagina

1. **Una linea sola 1948-2024**: i matrimoni a Milano per 1.000 abitanti, con due aree (civili/religiosi) che mostrano la chiesa che si svuota e il civile fermo (`tassi_per_mille_milano.csv`). Il 1972 come scatto, il 2002 come sorpasso, il 2020 come tuffo.
2. **Milano contro Italia**: stesso grafico, sorpasso 2002 contro 2018 (`istat_italia_rito_1930_2024.csv`), con la quota di civili 81% contro 61%.
3. **Eta'**: due linee, sposi e spose (provincia, 2004-2024) piu' il primo matrimonio in Lombardia (1990-2024); eta' media 43,8/39,0 e "la moglie piu' grande nel 13% dei casi" (2021-2024).
4. **Coppie miste**: quota di nozze con uno straniero, 24% -> 40% -> 32% a Milano, contro 12% -> 19% -> 17% in Italia; civile contro religioso.
5. **Unioni civili**: barre annuali 2016-2024 con il picco 2017 e il 2020; quota Milano sul totale italiano (6-9%) e quota di coppie di uomini (74%).
6. **Rotture**: separazioni e divorzi 2007-2024 (provincia del tribunale), con le due note sul divorzio breve e sulla provincia di Monza; il confronto con i matrimoni dell'anno va presentato come rapporto grezzo.
7. **Il 2020**: un riquadro con -48% (Milano), -47% (Italia), -60% religiosi, -45% civili, -18%/-27% separazioni/divorzi.
8. **Chi si sposa dove**: nozze di residenti contro nozze celebrate a Milano (2011-2018 sicuri, 2019 e 2024 da prendere con cautela).

## 8. Cosa manca

- Eta' degli sposi a livello di comune prima del 2021 (nessuna fonte aperta: ISTAT da' solo provincia).
- Matrimoni per quartiere/NIL: nessuna fonte.
- Separazioni e divorzi: per comune non esistono; per provincia solo dal 2007; per Milano comune solo i 1.438 scioglimenti del 2018.
- Pre-2007: ISTAT ebiblio non raggiungibile. Possibile via: chiedere a ISTAT (contact.istat.it) o cercare i volumi in biblioteca; dati nazionali di divorzio e separazione prima del 2007 non sono stati cercati nelle serie storiche ISTAT (tavole 1.x e 2.x partono dal 2007).
- Tipo di rito a cui appartengono i "religiosi" (cattolici 96%: 2024 455 su 474, `matrimoni_rito_per_anno_milano.csv`).
- Durata del matrimonio alla separazione per Milano (ISTAT la da' solo per Italia: 17 anni, tavola 1.3).
