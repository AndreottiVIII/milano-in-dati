# Il tribunale di Milano - FASE 1 + pagina (docs/tribunale/)

Scaricato il 2 novembre 2026. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto>` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`, file della pagina in `docs/tribunale/data/`.

## 1. In breve

1. **I dati ci sono e sono solidi.** Il Ministero della Giustizia (Direzione generale di statistica e analisi organizzativa) pubblica file xlsx scaricabili su `datiestatistiche.giustizia.it`, per tutti i 140 tribunali e 29 corti di appello: flussi civili e penali 2014-2025, durata effettiva civile 2014-2025, monitoraggio PNRR (tempo di smaltimento, cause aperte, arretrato, obiettivi) 2019 - I semestre 2026.
2. **`webstat.giustizia.it` NON è stato usato**: risponde "Web Page Blocked" (HTTP 500) ai programmi, anche con User-Agent dichiarato. Non è stato aggirato né imitato un browser. Basta `datiestatistiche.giustizia.it` (robots.txt: `Allow: /`).
3. **Nessuna licenza aperta.** Le note legali del Ministero (`datiestatistiche.giustizia.it/it/note_legali.page`) dicono: contenuti protetti dal diritto d'autore; riuso ammesso "per finalità non commerciali, garantendo l'integrità degli elementi riprodotti e mediante indicazione della fonte"; vietato il "deep linking" non trasparente. Quindi: la pagina non ripubblica i file originali, solo tabelle ricalcolate (aggregati per ufficio) con la fonte accanto a ogni numero. **Da verificare dal coordinatore** se basta (io ritengo di sì: sito non commerciale, fonte citata, tabelle elaborate).
4. **Tutto il quadro nazionale si ricalcola e coincide con la relazione ufficiale** "Monitoraggio statistico degli indicatori PNRR - I semestre 2026" (Ministero, 14/9/2026): disposition time civile e penale dei tre gradi (tabelle 5 e 9), pendenti di protezione internazionale e di ATP previdenza (tabella 8). 54 controlli in `pulito/verifiche.csv`, nessuno fallito.
5. **Cosa dicono i dati su Milano** (anno 2025, salvo diversa indicazione; tutti i numeri della pagina sono in `docs/tribunale/data/riepilogo.json` con il file di origine):
   - Tribunale civile: tempo di smaltimento 435 giorni (417 nel 2019; Italia da 556 a 435), 86esimo su 140 (mediana 395). Cause vecchie (>3 anni): 6,9% delle aperte contro 15,1% in Italia, 44esimo su 140. Indice di ricambio 96,7 (Italia 100,1): le cause aperte crescono dal 2023 (37.975 -> 44.538).
   - Il peso della protezione internazionale: 15.397 cause aperte a Milano (35% del totale usato per il DT; 22% nel 2019), il numero più alto d'Italia (12% del totale nazionale). **Nostro calcolo**: senza di esse il DT di Milano sarebbe 317 giorni (344 nel 2019), 38esimo su 140.
   - Corte d'appello: civile 230 giorni (2ª su 29), penale 210 (3ª su 29). Tribunale penale: 199 giorni (25esimo su 140); solo dibattimento monocratico (nostro calcolo) 237 giorni, 8º su 140.
   - PNRR: gli obiettivi sono nazionali (non per tribunale). Italia: DT civile -50,2% (target -40%), DT penale -38,8% (target -25%) nel I semestre 2026. Milano tribunale: DT civile +4% e penale +14% sul 2019 (I sem. 2026), Corte d'appello -43% e -62%. Obiettivo di smaltimento 2026 (-90%): Milano tribunale -95,8%, Corte -99,7%.

## 2. Fonti, una per una (`raw/download_log.csv`: data, URL, byte, sha256, last-modified)

| File (raw/ministero/) | Pagina di origine | Cosa contiene |
|---|---|---|
| Monitoraggio_PNRR.xlsx | datiestatistiche.giustizia.it/it/pnrr.page | fogli Civile e Penale (definiti, pendenti a fine periodo per sede, anni 2019-2025 + I sem. 2026; arretrato >3 anni tribunali / >2 anni corti; baseline e pendenti per gli obiettivi di smaltimento 2024 e 2026), fogli Indicatori (DT già calcolato), foglio Leggimi |
| CivileFlussi20142025.xlsx | .../it/flussi_per_ufficio.page | sopravvenuti, definiti, pendenti per ufficio, macromateria, materia, dettaglio, 2014-2025, registri SICID e SIECIC |
| PenaleFlussi20142025.xlsx | .../it/flussi_per_ufficio_penale.page | sopravvenuti, definiti, pendenti per ufficio e sezione, 2014-2025 |
| Durata_SICID_20142025.xlsx (e SIECIC, non usato) | .../it/durata_dei_procedimenti_civile.page | durata media effettiva in giorni dei procedimenti chiusi, per ufficio e materia |
| 251231Milano Monitoraggio{CIVILE,PENALE,SIECIC}.xlsx | giustizia.it/giustizia/it/mg_1_14_1.page?contentId=SST244010 | monitoraggio del distretto di Milano IV trim. 2025: usato solo per controllare i flussi (SIECIC non usato) |
| Nota_metodologica.pdf, Guida_alle_Statistiche_Civile.pdf, relazione I sem. 2026 (Allegato_MDG...pdf) | pnrr.page, flussi_per_ufficio.page | definizioni e controlli |
| Monitoraggio_mensile.xlsx (7 MB) | .../it/monitoraggio_mens_tribunali.page | flussi mensili civili dal 2019: scaricato, NON usato (possibile sviluppo: andamento mensile) |

Non scaricati: cruscotti Oracle Analytics e Power BI (`datalake.giustizia.it`, `app.powerbi.com`): sono interattivi, e gli stessi dati sono negli xlsx. CEPEJ: non usato (solo come contesto: la definizione di disposition time è quella CEPEJ / EU Justice Scoreboard, citata dalla relazione del Ministero).

## 3. Definizioni usate (e perché il confronto è onesto)

- **Disposition time (DT)** = giorni del periodo x pendenti a fine periodo / definiti nel periodo (365 o 366 per l'anno, 181 o 182 per il I semestre). Aggregato civile del Ministero: solo cause "contenziose" secondo CEPEJ (nota metodologica pag. 2). Ricalcolato da `Civile`/`Penale` del file PNRR e **confrontato con i fogli Indicatori: 2.366 confronti, scarto massimo 4,5e-13 giorni**.
- **Italia** = somma dei dati degli uffici (per il DT: somma delle pendenti diviso somma dei definiti, non media dei DT). **Fascia grigia**: 25º-75º percentile degli uffici (non pesata).
- **Indice di ricambio** = definiti / iscritti, da `CivileFlussi` / `PenaleFlussi`. Civile tribunali: SICID senza la macromateria "Altre procedure" (giudice tutelare, ATP previdenza, atti amministrativi), come il monitoraggio distrettuale; corti: tutto il SICID. Penale tribunali: GIP/GUP + dibattimento (monocratico, collegiale, appello g.d.p.) + assise; corti: ordinaria, assise, minorenni. Penale: coincide col monitoraggio di Milano al numero e con il file PNRR per tutti gli uffici e gli anni. Civile: i flussi sono sempre un po' più alti del monitoraggio (0,5%-2,7% per i 9 tribunali del distretto; Milano 2025: 0,5% sugli iscritti; indice di ricambio di Milano scarto < 1 punto): estrazione diversa del Ministero, non risolta.
- **Cause vecchie** = colonna `Arretrato` del file PNRR (iscritte da più di 3 anni in tribunale, 2 in corte: arretrato "legge Pinto"); **quota** = arretrato / pendenti SICID dei flussi (stesso registro; il totale è più grande di quello del DT: due elenchi diversi).
- **Senza protezione internazionale (nostro)**: DT con pendenti e definiti meno le voci `Dettaglio` che contengono "nternazionale" ("Protezione internazionale" e "- Altri procedimenti"). Gli uffici senza quelle righe contano zero. Pendenti nazionali coincidono con la tab. 8 della relazione per 2020-2023 e 2025 (2019 e 2024 scarto ~1%: la relazione ha dati aggiornati dopo).
- **Dibattimento monocratico (nostro)**: DT solo sulla sezione "Dibattimento monocratico" dei flussi penali (primo grado, giudice singolo); non comprende le indagini. Resta una stima, non una durata.

## 4. Limiti (diventano "Limiti dei dati" nella pagina)

1. DT è una stima (un solo giorno, ritmo dell'anno). 2. Due elenchi civili diversi (DT contenzioso CEPEJ; arretrato e indice SICID). 3. Indice di ricambio civile ricalcolato (scarti sopra). 4. Penale: DT dei tribunali comprende il GIP/GUP (archiviazioni); nei file non ci sono durata effettiva penale né pendenti vecchi penali. 5. I semestre 2026 provvisorio e annualizzato; norma sugli ATP previdenza (DL 117/2025): pendenti nei tribunali 183.533 -> 116.296 tra fine 2024 e fine 2025 (78% nel "Sud" del file), Milano 307. 6. Cambi di classificazione (2021 tribunale delle imprese, 2022 CCII, 2023 Cartabia/famiglia). 7. Valori estremi (Venezia: pendenti da 15.158 a 48.899; voce "Stato della persona" da 6.364 a 43.022; Trieste simile): il Ministero segnala la crescita delle cause sulla "cittadinanza" ma i file non dicono per sede; non è stato verificato. 8. Perimetro: niente giudici di pace, minorenni, esecuzioni, Cassazione (salvo totale PNRR). 9. La baseline penale 2019 è stata corretta dal Ministero nella relazione (corti: 835 -> 841; totale 1.392 -> 1.398): il file PNRR già riporta il valore corretto (ricalcolo = 841).

## 5. Punti aperti / cose strane

- **Obiettivo di smaltimento 2024**: dal file PNRR il dato dei tribunali è -93,2% (337.740 -> 23.129; corti: 98.371 -> 610, -99,4%; insieme -94,6%), sotto il -95% richiesto, mentre la relazione dice "già raggiunto e rendicontato". Non so ricostruire il calcolo ufficiale: la pagina cita solo la dichiarazione del Ministero per l'Italia e i numeri di Milano.
- Nel file PNRR la Cassazione ha `Sede` vuota (riempita da build.py); la pendenza penale della Cassazione 2025 è 13.619 nel file e 13.628 nella relazione (non usata).
- `CivileFlussi`: i nomi delle sedi differiscono per maiuscole ("Vallo della Lucania") e "Bolzano/Bozen" (penale): si appaiano per chiave minuscola.
- Guida alle statistiche penali (`Guida_alle_Statistiche_PENALE_1.pdf`): elencata nella sitemap ma 404, non scaricata.
- "Italia" del tempo di smaltimento 2026 (291) è molto più basso del 2025 (435): in parte effetto ATP/norma (vedi limiti), in parte riduzione vera; non separabile con questi file.
- Da decidere: aggiungere l'andamento mensile (Monitoraggio_mensile.xlsx) e i SIECIC (esecuzioni, fallimenti) in una seconda fase.
