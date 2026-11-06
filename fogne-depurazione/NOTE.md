# NOTE - Fogne e depurazione ("Dove va l'acqua che scarichi")

Lavoro del 6 novembre 2026. Pagina: `docs/fogne/index.html` (NON nel menu, NON in temi.json, NON in elenco/home: aspetta l'ok di Davide). Niente git.

## Come si rifa
1. `python -I -X utf8 scripts/01_cerca_comune.py raw` - ricerca nel catalogo del Comune (risultato: nulla su fogne/depurazione, vedi sotto).
2. `python -I -X utf8 scripts/02_scarica_eea.py raw` - depuratori, agglomerati, punti di scarico italiani dal servizio pubblico EEA (rapporti 2021 e 2023).
3. Download fatti a mano con curl (User-Agent `milano-in-dati/1.0`, pause 3-5 s), file in `raw/`: ARPA su dati.lombardia.it (`raw/lombardia/dati/`), ISTAT (`raw/istat/`), tariffe MM (`raw/latuaacqua/`), tariffe delle altre citta' (`raw/tariffe_citta/`, raccolte da un sotto-agente, con CSV riassuntivo), presentazioni MM e ARPA (`raw/pdf_convegni/`). Comandi esatti: vedi sezione 1.
4. `python -I -X utf8 scripts/03_elabora.py <filone> <docs/fogne> <bilancio-comune/pulito/indice_prezzi_annuo_FOI_da_strand12.csv>` - scrive `pulito/*.csv`, `pulito/_log_elabora.txt` e `docs/fogne/data/*`.

## 1. Fonti, licenze, date (scaricato tutto il 6/11/2026)

| Cosa | Fonte e come | Licenza | Uso |
|---|---|---|---|
| Depuratori: acqua trattata (m3), carichi BOD/COD/N/P in entrata e in uscita (t/anno, misurati), % riuso, capacita', carico (AE) | EEA, WISE UWWTD, ArcGIS REST `water.discomap.eea.europa.eu/arcgis/rest/services/WISE_UWWTD/TreatmentPlants_2020` e `_2022`, layer 0, `where rptMStateKey='IT'`, a pagine di 2000. Anni di riferimento: 2020 (rapporto 2021) e 2022 (rapporto 2023), scritto nella descrizione del servizio | CC BY 4.0 (note legali EEA: "EEA materials are published under the CC-BY license") | ripubblicati i valori dei 3 impianti (`data/depuratori.csv`) |
| Agglomerato Milano (AE generati, % raccolto in fogna) | EEA, `Agglomerations_2020/_2022` | CC BY 4.0 | riepilogo |
| Fiume in cui scarica ogni impianto | EEA, `DischargePoints_2020/_2022`, campo `dcpWaterbodyID` abbinato ai codici dei corpi idrici ARPA | CC BY 4.0 | testo e schema |
| Acqua immessa, erogata, perdite, fatturata, copertura fognatura/depurazione, Milano 2020 | ISTAT, Censimento delle acque per uso civile 2020, `Istat_Tavole_Censimento_acque_2020-21122022.xlsx`, tavole 15, 16, 36 | CC BY 4.0 | numeri |
| LIMeco 2018-2020 per stazione | ARPA Lombardia, dati.lombardia.it `mnqh-idjz` (CSV intero, 1.055 righe) | CC0 | ripubblicato per le stazioni usate |
| LIMeco 2013 | ARPA, `7ayk-kdfa` (CSV intero) | CC0 | idem |
| Analisi chimiche fiumi 2018-2021 | ARPA, `kr6i-f553`, filtrato `provincia in ('MI','MB','LO')`: 188.983 righe (su 1.060.320) | CC0 | mediane per stazione |
| Analisi corsi d'acqua Comune di Milano (2053 righe) | ARPA, `kqd6-884n` | CC0 | scaricato, non usato |
| Livello del Seveso a Niguarda | ARPA, sensore 3118 "Milano Niguarda", `gsyu-uxt3` (2011-2020) e `3e8b-w7ay` (dal 2021), filtrati per sensore: 589.290 misure ogni 10 min, 18/10/2013 - 1/1/2025. Anagrafica `nf78-nj6b`, codici qualita' allegato al dataset | CC0 | massimi giornalieri, giorni sopra 1 m |
| Tariffe MM Milano 2020-2026 | 7 PDF da latuaacqua.it (sito di MM per l'acqua; nessun robots.txt, 404). 2020-2023 testo; 2024-2026 tabelle in immagine, lette a vista dalle immagini estratte (`raw/latuaacqua/img/`) | nessuna licenza dichiarata (atto tariffario pubblico): solo i numeri citati | `data/tariffe_milano.csv` |
| Tariffe 2025 altre citta' | Acea Ato 2 (Roma), SMAT (Torino), ABC Napoli (+ tariffa depurazione Regione Campania 2015), ATERSIR/Hera (Bologna), Publiacqua (Firenze), Citta' Metropolitana di Genova/IRETI, CAP Holding (pagina web). Raccolte dal sotto-agente, robots rispettati; ricontrollati da me Torino, Bologna (rapporto teta 1,187/1,099), Firenze, Roma, Napoli (immagine) | nessuna licenza: numeri citati | `data/tariffe_citta_2025.csv` (solo i valori al m3) |
| Km di fogna (~1.630), fogna mista, volumi collettati (~240 Mmc), riuso irriguo Nosedo ~60 Mmc / 3.000 ha (apr-set) e San Rocco ~15 Mmc / 7.700 ha (mag-ago), Peschiera = bacino orientale 250.000 AE gestito da altro operatore | MM, presentazione "08-Blazina-MM_GdLriuso-16giugno26.pdf", impiantitrattamentoacque.unibs.it (robots: tutto permesso) | nessuna licenza: solo numeri citati | testi e limiti |
| Record del Seveso 5,01 m (nov 2014), 4,92 m l'8/7/2014 (esondazione) e il 22/9/2025 | ARPA via Legnanonews 22/9/2025 (la nostra serie dice 501 e 492 cm: coincide) | citato | testo |
| Vasca Parco Nord 250.000 m3, operativa da nov 2023 | Comune di Milano citato dalla stampa (Il Fatto Quotidiano 31/10/2023) | citato | segno sul grafico |
| Prezzi | FOI 2025=100 da `bilancio-comune/pulito/` (non copiato) | ISTAT | euro di oggi |

**Siti e robots.txt.** dati.comune.milano.it: robots.txt risponde 403 ("Accesso non consentito"), l'API CKAN risponde normalmente (usata solo per la ricerca, come gli altri filoni). **mmspa.eu risponde 403 a ogni richiesta del nostro programma (anche ai PDF): non usato, nessun tentativo di aggirarlo** (Relazione annuale integrata 2025 di MM quindi NON letta). arpalombardia.it: robots vieta `/media/` (dove stanno i PDF): non toccato. ATO Citta' metropolitana: robots vieta solo `/wp-content/uploads//`; nessun documento usato alla fine. dati.lombardia.it: crawl-delay 1, rispettato.

## 2. Cosa c'e' e cosa manca, per filone

1. **Dove finisce l'acqua** - c'e': ISTAT 2020 (immessa 203,3 Mmc, erogata 175,9, perdite 13,5%), EEA 2020 (Nosedo 122,5 Mmc, San Rocco 91,9, Peschiera 60,9; 2022: 127,1 / 116,8 / 49,1), riuso dichiarato (Nosedo 50,08%, San Rocco 8,68%, Peschiera 3,11%), fiume di scarico. **Risultato: 122 litri nei depuratori ogni 100 consegnati** (fogna mista). Manca: ISTAT 2022 per Milano (le tavole 2022 non sono state trovate in xlsx; pagina 2022 404), la quota di Milano dentro Peschiera, la divisione pioggia/falda.
2. **Quanto e' pulita** - c'e': in/out per sostanza (2022, Nosedo+San Rocco: BOD tolto 96,6%, COD 95,7%, N 80,9%, P 72,8%; Peschiera 97,9/97,6/72,8/88,1), LIMeco e analisi ARPA. Il Lambro peggiora scendendo: Lesmo sufficiente -> Peschiera scarso -> Sant'Angelo e Orio Litta cattivo (3 anni su 3); Po a Somaglia buono nel 2020; Navigli elevato. 6 punti su 10 migliorano 2013->2020 ma nessuno cambia classe. Manca: LIMeco dopo il 2020 e analisi dopo il 2021 in open data; dati degli impianti in uscita mese per mese.
3. **Le fogne della citta'** - c'e': km (MM, citato), livello del Seveso 2013-2024. **Mancano dati aperti su: eta' della rete, allagamenti stradali, sfioratori/scarichi di piena (i campi EEA `aggSewerOverflows_*` sono vuoti per Milano), elenco ufficiale delle esondazioni, volumi e stato delle vasche (solo stampa).** Indicatore ARERA M4a (allagamenti per 100 km): non trovato per MM.
4. **Quanto costa** - c'e': tariffe MM 2020-2026 (fogna+depurazione 0,513 -> 0,697 euro/m3; +36% nominale, +14% reale), 8 aree nel 2025. Milano 0,70 euro/m3 e' seconda piu' bassa dopo Napoli (0,62, ma con depurazione regionale del 2015).

## 3. Limiti dei dati e problemi trovati

1. **EEA, riuso identico nei due rapporti** (50,08 / 8,68 / 3,11% sia 2020 sia 2022): probabilmente non aggiornato. Il campo e' "percentuale media annua riusata" (dizionario EIONET). MM 2026: ~60 Mmc/anno da Nosedo su ~140 (43%), ~15 da San Rocco su ~100.
2. **EEA, carichi in entrata 2020 molto piu' bassi del 2022** (BOD Nosedo+SR 26.829 t -> 36.522 t; Peschiera 7.468 -> 14.489): Covid e/o metodo; per questo in pagina solo percentuali tolte.
3. **EEA, Peschiera Borromeo volume in calo** (60,9 -> 49,1 Mmc) mentre il carico raddoppia: non spiegato.
4. **EEA, collegamento agglomerato-impianto assente** (`aggCode` vuoto negli impianti): la parte di Milano che va a Peschiera non e' quantificabile. Stima indiretta: carico Nosedo+San Rocco 1.867.791 AE su 1.955.865 dell'agglomerato (differenza ~88.000 AE), NON usata in pagina.
5. **Flusso: "acqua in piu'" = differenza tra due fonti** (ISTAT erogata vs EEA trattata); include pioggia, falda drenata, scarichi di altri comuni, meno la parte che va a Peschiera; si assume che tutta l'acqua erogata torni in fogna.
6. **ARPA LIMeco**: il valore usa la virgola delle migliaia ("1,000"); 39 righe con classe "-"; nomi dei comuni in maiuscolo in alcuni anni ("PERO"/"Pero"): normalizzati. Il file 2013 scrive i nomi diversamente ("Sant.Angelo Lodigiano", "S. Giuliano Milanese", "Cavo Vettabbia"): abbinati a mano nel programma (lista ST). Olona a Rho 2013 ha due righe (0,109 e 0,242): non usato per il confronto.
7. **ARPA analisi**: valori "<" (sotto soglia, es. 26 per azoto ammoniacale) e ">" (3 per E. coli) esclusi dalle mediane, non convertiti. Mediana su tutti i prelievi 2018-2021.
8. **Seveso**: codici qualita' 1 (registrato buono) e 2 (elaborato buono) usati; 70 (stimato, 114.752 righe, valori bassi), 77, 82, 201, 202 esclusi. Giorni con dati validi: 2020 246, 2021 259, 2023 255 (altri anni 311-363). Il dataset si ferma al 1/1/2025 (la piena del 22/9/2025 non c'e'). Nessuna soglia ufficiale di esondazione trovata per il sensore: non contiamo esondazioni. La registrazione inizia il 18/10/2013.
9. **Tariffe**: Genova ha tre fasce secondo il comune/zona (non verificato quale valga per Genova citta'): mostrata come intervallo 1,11-1,49 euro/m3; il PDF di Genova si chiama "Definitiva" ma in testa dice "Tariffa PROVVISORIA". Napoli: depurazione 0,310423 da nota Regione Campania 2015. Roma: due periodi nel 2025 (stesse tariffe al m3, quote fisse diverse); usato dal 1/7. Quote fisse non confrontate (per abitazione, per utenza o per persona). IVA e componenti UI esclusi ovunque. CAP 2025 dalla pagina web (BURL 2025 non trovato; BURL 2024 scaricato: 0,218518/0,644546).
10. **MM 2026 provvisoria** = 2025.
11. **Comune di Milano open data**: nessun dataset su fogne, depuratori, allagamenti, Seveso (28 parole cercate, `raw/comune_ricerca.txt`). Gia' noto da `acqua-del-sindaco`: perdite 2018 (ds1571).

## 4. Pagina (docs/fogne/)
- Titolo "Dove va l'acqua che scarichi". 9 numeri cliccabili, 7 grafici in 4 capitoli: (1) **firma**: strisce del viaggio dell'acqua 2020 (acquedotto -> perdite, rubinetti -> fogne + pioggia -> Nosedo/San Rocco -> campi / Vettabbia / Lambro Meridionale -> Lambro -> Po); (2) quadretti in/out; (3) **linea del metro' del Lambro** con fermate = stazioni ARPA e 3 quadretti di classe; (4) pallini collegati 2013-2020; (5) calendario delle piene del Seveso con cerchi e note numerate; (6) **da toccare**: "quanti m3 usi" -> conto di Milano e barre delle 8 aree; (7) linee euro di oggi/di allora.
- `data/`: `riepilogo.json`, `depuratori.csv`, `fiumi_stazioni.csv`, `seveso_giorni_sopra_1m.csv`, `tariffe_milano.csv`, `tariffe_citta_2025.csv` (solo valori aggregati o citati).
- Test (Playwright, 375 e 1000 px, scala 2): nessun errore in console, nessuno scorrimento laterale, nessun testo sotto 12 px, nessuna etichetta SVG sovrapposta o fuori dal riquadro, tutti i numeri portano al loro grafico.
