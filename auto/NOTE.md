# Le auto dei milanesi - note (fase 1 + pagina)

Scaricato il 1-2 novembre 2026. Programmi in `scripts/`, dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle in `pulito/`. Pagina: `../docs/auto/`.

## 1. In breve (cosa sorprende)
1. **Meno auto per abitante di 18 anni fa**: 584 ogni 1.000 abitanti nel 2007 (726.896 auto, 1.245.440 residenti ISTAT), minimo 491 nel 2019, 519 nel 2025 (706.764 auto, 1.362.863 residenti). Le auto sono -2,8%, i residenti +9,4%.
2. **Tra i 10 comuni piu' grandi solo Genova ha meno auto per abitante** (468; Milano 519; Roma 701; Torino 819). Il dato di Torino e Firenze e' gonfiato dal noleggio a lungo termine (provincia di Torino 10,9% di auto in noleggio senza conducente, Firenze 31,7%, Roma 7,6%, Milano 1,4%, Italia 4,0%). Con "uso privato" per 1.000 abitanti (provincia) Milano e' seconda piu' bassa dopo Genova (566 contro 507).
3. **Le moto crescono ogni anno dal 2007**: 135.923 -> 200.004 (+47%), da 109 a 147 ogni 1.000 abitanti; 28 moto ogni 100 auto (erano 19).
4. **Carburante (provincia di Milano, autovetture)**: gasolio 32,7% (2019) -> 21,0% (2025); ibride 2,1% -> 13,8%; elettriche 1,4% (25.911). Italia 2025: gasolio 38,4%, ibride 8,7%.
5. **Euro 0: 68.968 auto (9,8%) nel 2025, 95.734 nel 2007** (-28% in 18 anni, mentre ogni auto invecchiava di 18 anni). Euro 0-3 dal 71% (2007) al 19% (2025); Euro 6 52%. Il calo delle Euro 0-3 non accelera dopo Area B (3,7 punti in meno all'anno fino al 2018, 1,5 dopo).
6. **Area B** (dal 25/2/2019 vieta benzina Euro 0 e gasolio Euro 0-3): nella provincia di Milano queste auto erano 213.632 a fine 2019, 167.438 a fine 2025 (-22%): gasolio -38%, benzina Euro 0 -7%.
7. **Passaggi in Area C vs parco** (2024, passaggi % su tutti i veicoli): elettrici 5,5% contro 1,1% delle auto, ibridi 24,8% contro 11,3%, diesel 21,0% contro 23,0%.
8. **Potenza**: oltre 130 kW il 7,9% delle auto della provincia di Milano (Italia 5,4%, Roma 5,0%). Almeno 16 anni: 30,5% (Italia 40,0%). SUV non misurabili.
9. **Auto nuove**: immatricolazioni 90.953 (2007) -> 37.810 (2025), -58%.

## 2. Fonti, una per una
| Fonte | Cosa | Licenza | Note |
|---|---|---|---|
| Comune di Milano **ds529** (letto da `parcheggi/raw/comune_veicoli/ds529.csv`, non copiato) | parco circolante, immatricolazioni, radiazioni per tipo di veicolo, 2007-2025; proprietari residenti a Milano (PRA) | CC-BY | autovetture 2025 = 706.764 |
| Comune di Milano **ds1081** (`raw/comune_ds1081/`) | autovetture per classe Euro, 2007-2020, con Euro 0 | CC-BY | usato per 2007-2018 |
| Comune di Milano **ds530** (`raw/comune_ds530/`) | classi Euro per tipo veicolo 2007-2025 | CC-BY | **senza le righe Euro 0 nel 2007-2023**: solo controllo (v. 5.1) |
| Comune di Milano **ds545** (`raw/comune_ds545/`, zip 17,8 MB, CSV 125 MB) | **un veicolo per riga** (Motorizzazione, MIT), residenti a Milano, fine 2017: alimentazione, kW, cilindrata, CO2, massa, classe Euro, data immatricolazione, uso, eta' e sesso dell'intestatario | CC-BY (portale) | 749.263 autovetture e 189.262 moto; contiene dati personali: pubblicati solo conteggi |
| ACI **Autoritratto 2019-2025** open data (`raw/aci/`) | `Parco_veicolare_AAAA.ods` (categorie per provincia/comune, autovetture per provincia: anno immatricolazione, kW, cilindrata, uso, soggetto) e `Circolante_Copert_AAAA.ods` (autovetture e moto per provincia/comune x alimentazione x Euro) | CC BY 4.0 (dichiarata da aci.gov.it/open-data) | 2025 e' un .rar (si estrae con `tar.exe` di Windows); soggetto solo 2024-2025, uso 2020-2025 |
| ISTAT **POSAS** (`raw/istat_posas/`, demo.istat.it) | residenti per eta' al 1 gennaio 2019-2026 per provincia (10 province + regioni) | CC BY 4.0 | script `scarica_popolazione.sh`; Italia = somma delle regioni |
| ISTAT bilancio demografico ricostruito 2001-2018 | popolazione fine periodo di Milano | CC BY 4.0 | riusato da `popolazione/pulito/istat_bilancio_milano_2001_2018.csv` |
| Filone Area C `area-c/pulito/tabella_composizione_pct.csv` | composizione dei passaggi (feriali normali) | CC-BY (Comune/AMAT) | copiato in `pulito/areac_composizione_pct.csv` |
| Confcommercio Milano (pagina 2019) | date e classi vietate all'avvio di Area B (25/2/2019: benzina Euro 0, diesel Euro 0-3) | giornale: solo fatti | unica fonte usata per Area B |

Non trovato / non fatto: MIT/Motorizzazione open data (dati.mit.gov.it) con piu' snapshot: il dataset e' fermo a febbraio 2017 (lo stesso di ds545); nessun file piu' recente aperto. ACI Autoritratto prima del 2019 non e' nella pagina open data. Dati per quartiere (NIL): non esistono in forma aperta. Carrozzeria/SUV: non esiste. Comune di Milano per comune x carburante: non esiste (solo ds545 2017).

## 3. Pulizia (cosa fa `scripts/build.py`)
- Legge i fogli .ods con `parcheggi/scripts/ods_lettore.py` (solo libreria standard); i nomi dei fogli e le colonne cambiano da un anno all'altro (2019-2023 contro 2024-2025): il lettore normalizza i nomi e riconosce le colonne-etichetta.
- Le tabelle Copert per provincia contengono anche totali regionali, di area, "X TOTALE" e riepiloghi: scartati con `aggregato()`. Italia = somma delle province.
- Controlli interni (nessun avviso nell'ultima esecuzione, `pulito/avvisi_build.txt`): somma delle classi Euro = totale in ogni riga; totali ACI di Milano = ds529 2019-2025; ds1081 = ds529 2007-2018; ACI = ds1081 (2019-2020) e = ds530 (Euro 1-4 2019-2025, Euro 0 2024-2025); ds530 = ds1081 (Euro 1-5, 2007-2018); somma dei gruppi di carburante = totale.
- Residenti: ISTAT POSAS al 1 gennaio dell'anno dopo; 2007-2018 dal bilancio ricostruito (stesso significato).

## 4. Tabelle in `pulito/`
`serie_milano_comune.csv` (2007-2025), `confronto_citta.csv` (10 comuni + province + resto provincia di Milano + Italia, 2019-2025), `carburante_province.csv`, `euro_milano_comune_2007_2025.csv`, `euro_comuni.csv`, `euro_province.csv`, `euro_milano_provincia_per_carburante.csv`, `euro_moto_comuni.csv`, `eta_potenza_province.csv`, `bande_uso_soggetto.csv`, `areac_composizione_pct.csv`, `milano_2017_motorizzazione.json`.

## 5. Limiti dei dati (anche sulla pagina)
1. **Il PRA registra l'intestatario, non l'uso.** Auto ferme o mai radiate contano; pendolari e turisti no.
2. **Leasing/noleggio**: l'auto e' del locatore (nel comune della sua sede). Torino e Firenze sono gonfiate; auto aziendali usate da milanesi ma intestate altrove non si vedono. L'uso privato esiste solo per provincia.
3. **5.1 Buco in ds530**: nel 2007-2023 mancano le righe "EURO 0" e il totale e' piu' basso di ds529 (2019: 615.529 contro 690.914; la differenza, 75.385, e' esattamente il numero delle Euro 0 di ds1081/ACI). Da segnalare al Comune.
4. **Residenti**: ISTAT contro anagrafe del Comune (fino al +3%); la pagina Parcheggi usa l'anagrafe (502 per 1.000 nel 2025), questa ISTAT (519). Dal 2020 ISTAT rivede i residenti col censimento permanente (-32.000 nel 2020, poi -24.000 nel 2021): parte della salita 2019-2021 e' effetto statistico.
5. **Carburante solo provincia** (circa 38% delle auto e' nel comune); "ibride" = tutte; elettriche = a batteria.
6. **Eta'**: fasce biennali mobili: solo "almeno 16 anni" (fascia "fino al" = anno-16) e "ultimi 2 anni" sono confrontabili. **SUV** non misurabili: proxy kW e massa (2017).
7. **Area B**: regole oltre il primo giorno non verificate (fonti discordanti, sito del Comune 403 ai programmi): non usate.
8. **Passaggi Area C**: includono moto (18%), furgoni, bus e NC (12-22%): solo ordine di grandezza. Euro 0 dei passaggi non usato (la maggior parte e' probabilmente moto).
9. **ds545**: 7% di auto in piu' rispetto al PRA 2017 (749.263 contro 700.723), non spiegato; snapshot unico.
10. **Radiazioni**: 28.487 (2022) -> 60.765 (2024) -> 62.040 (2025) senza che il parco cali: non spiegato.
11. **Confronto tra citta'** solo 2019-2025.

## 6. Cosa non e' stato fatto
- Consultare le pagine ufficiali del Comune (403 ai programmi): regole Area B/C per classe, esenzioni degli elettrici (la pagina dice "da verificare").
- Confronto con aria/inquinamento (filone Aria) e con i tempi di viaggio (bici-auto-mezzi): solo link.
- Euro 0 persistenti: non si sa quanti circolino (idea: incrociare con i passaggi Area C per classe Euro con distinzione moto/auto, oggi non separabile nei dati).
