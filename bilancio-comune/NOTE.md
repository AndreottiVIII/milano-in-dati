# Filone 17 - Dove vanno i soldi del Comune (FASE 1: raccolta e controlli)

Scaricato il 29-30 ottobre 2026. Niente grafici, niente pagine, nessun giudizio sulla spesa. Tutti gli script sono in `scripts/` (si lanciano da questa cartella con `python -I scripts/<nome>.py`). Dati grezzi in `raw/`, tabelle pulite in `pulito/`.

## 1. Cosa c'e' (in breve)

- **Bilancio del Comune di Milano, anni di rendiconto 2015-2025** (11 anni) a livello di singolo capitolo, con missione e programma per le uscite. Dieci "edizioni" (dataset), una per anno, ognuna con 2 anni di rendiconto + 3 anni di previsione.
- **Anni 2012, 2013**: solo spesa corrente (2012 a programma, 2013 piu' dettagliato) e, per il 2013, entrate correnti. **2014: manca il consuntivo** (c'e' solo una previsione di febbraio 2014).
- **Prima del 2012**: non sul portale del Comune. Esiste per via diversa (vedi punto 5): Ministero dell'Interno dal 1998.
- **Licenza**: tutti i dataset del Comune sono CC-BY 4.0 ("Creative Commons Attribution" nel catalogo). Si possono ripubblicare citando la fonte (Comune di Milano, dati.comune.milano.it). Quindi anche i file grezzi si possono ripubblicare.

## 2. Fonti e file (ogni dato dice il suo file)

Tutte le fonti del Comune sono su `https://dati.comune.milano.it/api/3/action/package_search?q=...` (CKAN). Ricerca fatta con 21 parole chiave (bilancio, rendiconto, spesa, entrate, PEG, missioni, tributi, sanzioni...), 687 dataset trovati in tutto; elenco in `raw/search_all.json`. Tutto in `pulito/inventario.csv` (39 righe).

| id | cosa | anni | dettaglio | file in raw/ |
|---|---|---|---|---|
| ds397 | Bilancio comunale, rendiconto 2015-16 e previsioni 2017-19 | rend. 2015, 2016 | capitolo PEG | ckan_ds397 |
| ds396 | idem, rendiconto 2016-17, previsioni 2018-20 | rend. 2016, 2017 | capitolo | ckan_ds396 |
| ds399 | idem, 2017-18, previsioni 2019-21 | rend. 2017, 2018 | capitolo | ckan_ds399 |
| ds400 | idem, 2018-19, previsioni 2020-22 | rend. 2018, 2019 | capitolo | ckan_ds400 |
| ds401 | idem, 2019-20, previsioni 2021-23 | rend. 2019, 2020 | capitolo | ckan_ds401 |
| ds1936 | idem, 2020-21, previsioni 2022-24 | rend. 2020, 2021 | capitolo | ckan_ds1936 |
| ds2352 | idem, 2021-22, previsioni 2023-25 | rend. 2021, 2022 | capitolo | ckan_ds2352 |
| ds2738 | idem, 2022-23, previsioni 2024-26 | rend. 2022, 2023 | capitolo | ckan_ds2738 |
| ds2956 | idem, 2023-24, previsioni 2025-27 | rend. 2023, 2024 | capitolo | ckan_ds2956 |
| ds3013 | idem, 2024-25, previsioni 2026-28 (aggiornato 21/8/2026) | rend. 2024, 2025 | capitolo | ckan_ds3013 |
| ds227 | Bilancio trasparente: spesa corrente per missioni e programmi | consuntivo 2012; assestato 2013; previsione 2014 | missione/programma (solo nomi) | ckan_ds227 |
| ds284 | PEG spese correnti, consuntivo 2013 | 2013 | titolo/macroaggregato/missione/programma/centro di costo | ckan_ds284 |
| ds285 | PEG entrate correnti, consuntivo 2013 | 2013 | titolo/tipologia/voce | ckan_ds285 |

Ogni dataset ha CSV + JSON (i piu' recenti anche ODS). Scaricati tutti: 102 MB circa per questi 13. I JSON e gli ODS sono copie degli stessi dati, non servono.

**Altri file scaricati (utili ma secondari):**
- SIOPE spese del Comune: 2017 e 2018 (annuale), poi 62 file mensili da settembre 2019 a luglio 2025 (`raw/ckan_siope_spese/`, `raw/ckan_ds738`, `ckan_ds739`). Sono PAGAMENTI (cassa) per codice SIOPE (natura economica), NON per missione. Servono solo come controllo. **Mesi che nel catalogo non esistono**: nov 2019, feb-mar-apr 2020, set-ott 2020, giu 2023, ago 2023, dic 2023; niente dopo luglio 2025 (cercati uno per uno, non trovati). Le colonne cambiano da un file all'altro (`importo_2017`, `imp_uscite_att`...).
- ds478 (pernottamenti con imposta di soggiorno, non euro), ds312 (addizionale IRPEF dovuta per anno d'imposta), ds697 (incassi PagoPA), ds633 (bilancio partecipativo: NON e' il bilancio del Comune, da ignorare).
- Popolazione: `raw/ckan_pop/` (ds71, ds73).
- Indici prezzi NIC di Milano per gruppi di spesa: `raw/ckan_nic/` (ds240, ds241, ds1431, ds2977). **Non hanno la riga "indice generale"**: per deflazionare conviene l'indice nazionale FOI gia' scaricato dal filone 12 (vedi punto 6).

## 3. Come e' fatto il dato del Comune (colonne, unita')

Colonne comuni alle dieci edizioni: Tipo (ENTRATE/USCITE); PDC-Missione, PDC-Programma (solo uscite); PDC-Livello1..4 (per le uscite: titolo, macroaggregato...; per le entrate: titolo, tipologia, categoria, IV livello) con descrizioni; Centro di costo; Capitolo (+ Articolo, Numero fino a ds2956); Centro di responsabilita'; **due colonne Rendiconto, tre Stanziamento, una Stanziamento di cassa**; Direzione. Importi in euro (non migliaia). Ogni riga e' un capitolo di bilancio: ~5.200-6.700 righe per edizione (ds1936: 6.699; ds3013: 5.183).

**Prevision vs consuntivo - come l'ho separato.** Nelle tabelle pulite c'e' sempre la colonna `fase`:
- `consuntivo` = colonne "Rendiconto" (misura `rendiconto`; per le entrate sono accertamenti, per le uscite impegni - il dataset non lo dice, lo deduco dal fatto che nelle entrate il totale supera le uscite di 0,5-0,9 miliardi e dal confronto col Ministero, vedi sotto);
- `previsione` = colonne "Stanziamento" (misura `stanziamento_competenza`) e "Stanziamento di cassa" (misura `stanziamento_cassa`, solo primo anno);
- colonna `anni_dopo_ultimo_rendiconto` (1, 2, 3) dice quanto lontano e' lo stanziamento.
- colonna `da_usare` = 1 sulle righe consigliate per non contare due volte la stessa cosa (rendiconto: edizione piu' recente che contiene quell'anno; previsione: solo il primo anno di stanziamento).

## 4. Tabelle pulite (cartella `pulito/`)

- `spesa_missioni.csv` (8.826 righe): anno, fase, misura, titolo di spesa (1 correnti, 2 conto capitale, 3 attivita' finanziarie, 4 rimborso prestiti, 5 anticipazioni, 7 conto terzi), missione, programma, importo in euro. Contiene anche ds227 (2012-2014) e ds284 (2013) con i codici ricostruiti dai nomi. Separatore `;`, punto decimale. **Per "quanto spende il Comune" filtrare titolo = 1 (spese correnti) e/o escludere titolo 7 (partite di giro).**
- `entrate.csv` (5.690 righe): anno, fase, titolo/tipologia/categoria/IV livello con descrizioni, importo. Per il 2013 (ds285) i livelli numerici sono -1 e ci sono solo i nomi.
- `bilancio_capitoli.csv` (245 mila righe, 33 MB): tutti i capitoli con importo diverso da zero, entrate e uscite, tutte le edizioni - serve per cercare voci precise (Area C, multe, ...). Descrizione capitolo come nel dato.
- `inventario.csv`: tutte le risorse, con anni, fase, dettaglio, unita', codifica, formato numeri, licenza, URL.
- `controllo_coerenza.csv`: i controlli del punto 7.
- `corrispondenza_funzioni_missioni.csv`: vecchia classificazione (DPR 194/1996) -> nuova (D.Lgs. 118/2011), a mano, con "1:1 / 1:n / n:1 / nessuna".
- `popolazione_milano.csv`: abitanti per anno (due definizioni, vedi sotto).
- `indice_prezzi_annuo_FOI_da_strand12.csv`: copia (non modificata) dal filone 12.

**Entrate che interessano alla domanda (livello capitolo, in `bilancio_capitoli.csv`, rendiconto in milioni di euro):**
- Area C (capitolo "PROVENTI DA ZTL AREA C"): 2016 64,6; 2019 65,7; 2023 57,6; 2025 33,7. Dal 2023 compare anche "PROVENTI DA ZTL - NUOVA TARIFFAZIONE ACCESSO AL CENTRO STORICO" (1,7; 1,0).
- Sanzioni codice della strada: 2016 556,6; 2019 487,9; 2023 488,1 (+33,4 "esercizi precedenti"); 2025 260,8 (+33,6). Nel 2013 (ds285) "AMMENDE PER CONTRAVV." 410,5. Il nome del capitolo cambia quasi ogni anno: **per le serie storiche serve un elenco di capitoli equivalenti, da fare in fase 2**.
- "Recupero spese postali notifica verbali" 2016 60,3; 2023 92,7; 2025 39,5 (e' un'entrata per rimborso spese, non una multa).
- Imposta di soggiorno: 2016 82,8; 2019 118,2; 2023 125,3 + 2,7; 2025 114,0 + 0,1.
- Tributi, trasferimenti, extratributarie: livello titolo/tipologia in `entrate.csv`.

## 5. Anni piu' vecchi: verdetto

**Conviene? Si', ma con il Ministero dell'Interno, non con OpenBilanci.** Da decidere con Davide.

1. **Ministero dell'Interno - Finanza locale - "Certificati Consuntivi"** (`finanzalocale.interno.gov.it/apps/floc.php/certificati/index/codice_ente/1030491450/cod/4/anno/ANNO/md/0/cod_modello/CCOU/tipo_modello/U/cod_quadro/QUADRO`, codice ente di Milano = 1030491450). Accesso libero senza login, ma e' **una pagina HTML per anno e per quadro**, nessun file da scaricare in blocco. Provato: Milano ha dati dal **1998** (1996 = "dati assenti"; 1997 non provato) al 2015 almeno. Quadro 3 = riepilogo spese per titolo (impegni, pagamenti); Quadro 4 = spese correnti per **funzione e servizio** x **intervento** (personale, beni, servizi, trasferimenti, interessi...); Quadro 5 = investimenti. Scaricate 8 pagine di prova in `raw/ministero_interno_campione/`.
   - Controllo: Titolo I 2013 = 2.615.331.335,35 euro = esattamente la somma di ds284. Titolo I 2015 = 2.793.159.486,27 = ds397 (2.793,2 M). Quindi i due mondi si agganciano.
   - 2014 (anno mancante nel Comune): Titolo I impegni 2.626,9 M; 2012: 2.505,3 M (ds227 dice 2.443,7 M: 61,6 M di differenza, da capire).
   - Licenza: la pagina non dice nulla. E' dato pubblico del Ministero, ma **da chiedere/verificare prima di ripubblicare i file grezzi**; i numeri si possono citare con la fonte.
   - Costo per fare tutta la serie: circa 18 anni x 3-4 quadri = ~70 pagine; con pause educate e' una mezz'ora.
2. **BDAP Open Data** (`bdap-opendata.rgs.mef.gov.it`, CKAN anche questo, licenza CC-BY). Ha dataset "20NN - Regione - Gestione finanziaria Entrate/Spese Enti Locali" per **2013, 2014, 2015 soltanto** (vecchia classificazione), un file per regione e anno: la Lombardia entrate pesa 46 MB per anno (Milano = 96 righe). **Le SPESE della Lombardia non ci sono** (19 regioni su 20), le entrate si'. Quindi: per le entrate 2013-2015 va bene (con risorsa per risorsa: ad es. 2013 Codice della strada 408,2 M, TPL 376,4 M, addizionale IRPEF 177,4 M, tutto coerente con ds285), per le spese no. Dal 2016 in poi i rendiconti armonizzati non sono su questo CKAN (c'e' un altro portale `openbdap.rgs.mef.gov.it`, a interfaccia web, non verificato). Scaricato: solo l'estratto di Milano 2013 (`raw/bdap_campione/entrate_2013_MILANO_estratto.csv`). Il file della Lombardia intero l'ho tenuto solo in streaming e cancellato.
3. **OpenBilanci** (Openpolis): non ha API pubblica (`/api/` = 404); riporta gli stessi certificati del Ministero (dichiarato nella pagina licenze); serie vecchia fino al 2015, nuova classificazione dal 2016; copertura dichiarata 2005-2022 (preventivi), consuntivi fino al 2021. **Licenza CC BY-NC-SA 4.0**: non commerciale e "condividi allo stesso modo" - scomoda per un sito. Verdetto: non serve, il Ministero e' la fonte originale e dal Ministero si ha di piu'.

## 6. Denominatori

- **Abitanti**: Comune di Milano ds71/ds73 = "popolazione calcolata ISTAT" a fine anno, 1880-2024 (**manca il 2025**). `pulito/popolazione_milano.csv` mette accanto la somma dei quartieri dell'anagrafe (ds205, del filone 15 minuti, letta senza modificarla). **Trappola: le due serie non coincidono** (2012: 1.263.087 calcolata vs 1.366.409 anagrafe, differenza 103 mila perche' la serie "calcolata" ha la rottura del censimento 2011; 2024: 1.365.698 vs 1.407.044). BDAP riporta per il 2013 "Popolazione ISTAT" = 1.345.851, che nel file del Comune e' il valore del 2015: serie ancora diversa. Per il "pro capite" bisogna scegliere una definizione e dirlo. Per il 2025 si puo' prendere ISTAT (demo.istat.it) quando serve.
- **Prezzi**: `indice_prezzi_annuo_FOI_da_strand12.csv` = FOI (famiglie operai e impiegati) senza tabacchi, Italia, medie annue 1996-2025 raccordate tra le basi, 2025 = 100 (es. 2015 = 82,372; 2025 = 100). Fatto dal filone 12, non rifatto. E' nazionale, non di Milano.

## 7. Controlli di coerenza (dettaglio in `pulito/controllo_coerenza.csv`)

1. **Stesso anno di rendiconto in due edizioni**: per 2016-2023 i valori sono identici capitolo per capitolo (differenza 0,00 euro, totali di entrate e uscite uguali). Per il **2024** i totali sono uguali (uscite 4.401,6 M; entrate 4.960,7 M) ma l'edizione 2024-2028 ha rinumerato tutti i capitoli (3.059 su 5.263 diversi) e ha spostato **90,4 M da 12/1 (Infanzia, minori, nidi) al nuovo programma 12/11 (Asili nido)**. Quindi 12/1 + 12/11 vanno sommati per avere continuita'.
2. **Pareggio delle previsioni**: in ogni edizione e anno, stanziamento entrate = stanziamento uscite (differenza 0,0 M). Quindi i totali previsti (6-11 miliardi) comprendono tutto, anche prestiti, fondi, partite di giro, anticipazioni.
3. **Previsione contro consuntivo (solo titolo 1, spese correnti)**: la previsione del primo anno e' sempre sopra il consuntivo: es. 2017 previsione 3.161 vs consuntivo 2.679; 2025 3.711 vs 3.209 (milioni). Dentro la previsione ci sono accantonamenti (fondo crediti di dubbia esigibilita' ecc.) e capitoli non impegnati. **Non vanno confrontati come se fossero la stessa cosa.**
4. **Stesso anno di previsione in edizioni diverse**: cambia molto (es. uscite 2022: 6.472 M nell'edizione 2018-22, 11.629 M in 2019-23, 10.266 M in 2020-24). Il "terzo anno" di ogni edizione e' una cifra di programmazione, non confrontabile con il resto. Usare solo il primo anno (flag `da_usare`).
5. **ds227 (milioni) vs ds284 (euro) per il 2013**: spesa corrente "assestato" 2.911,0 M (include 338,8 M di fondo svalutazione crediti) contro impegni a consuntivo 2.615,3 M. Coerente se si toglie il fondo (2.572 M, 43 M sotto: non e' lo stesso istante). In ds227 il TOTALE di ogni missione e il TOTALE generale quadrano con la somma dei programmi (differenza 0,00).
6. **PEG vs Ministero**: Titolo I 2013 e 2015 coincidono (punto 5). Il Ministero parla di "spese correnti al netto della spesa per alimentazione del fondo di solidarieta' comunale (FSC)" per 2013-2015: il trattamento del FSC cambia nel tempo, da verificare nei PEG.

## 8. Trappole dei dati (da non dimenticare)

1. **Formati dei numeri diversi per edizione**: ds397, ds396, ds399, ds400 usano "3.800.930,47" (punto migliaia, virgola decimale); ds401 usa "19,406.40" (virgola migliaia, punto decimale); ds1936 e successive "12222.22". ds399 ha "-" al posto di zero; ds396 ha celle di soli spazi (8.251). Parsing per file in `scripts/common.py`. Letto male = errori di 1000x.
2. **Codifiche diverse**: ds397, ds399, ds400, ds227, ds284, ds285 sono cp1252/ASCII; ds396, ds401 e le piu' recenti UTF-8. In ds227/ds284/ds285 accenti e apostrofi sono persi ("COMPETITIVIT+", "MOBILITA").
3. **Intestazioni delle colonne cambiano ogni anno** ("RENDICONTO 2015", "Rendiconto 2024", "STANZIAMENTO  2018" con doppio spazio, " RENDICONTO 2016 " con spazi in ds396; ds401 ha "ASSESTATO DI CASSA" senza anno; ds3013 ha 27 colonne, non 29).
4. **Codici di missione/programma scritti "1" o "01"** a seconda dell'edizione: vanno convertiti in numeri (fatto).
5. **Il rimborso dei prestiti (Titolo 4) e' distribuito su molte missioni**: nel rendiconto 2015 la missione 10 (trasporti) vale 1.324 M con tutti i titoli, ma solo 952 M di spese correnti (Titolo 1); 90 M sono rimborso prestiti (Titolo 4), nel 2025 99 M. Dal 2018 compare anche la missione 50 "Debito pubblico" che raccoglie solo una parte del Titolo 4 (41 M nel 2018, 31 M nel 2023, 109 M nel 2025 su 279 M di Titolo 4 totale). **Per sapere "quanto va ai trasporti" usare il Titolo 1 (e il Titolo 2 per gli investimenti), non il totale della missione.**
6. **Missione 99 (conto terzi/partite di giro)** vale 280-624 M all'anno e salta a 623,7 M nel 2023 (era 280,6 M nel 2022 e 357,2 M nel 2024). Non e' spesa del Comune.
7. **I totali di spesa del rendiconto cambiano di molto nel tempo** (4,0 miliardi 2015 -> 4,7 miliardi 2025) ma includono capitale, prestiti e partite di giro: per le serie da chiamare "spesa" usare spese correnti (Titolo 1: 2,8 -> 3,2 miliardi).
8. **Riclassificazioni possibili tra anni consecutivi** (non verificate): a rendiconto missione 1 sale da 285 M (2018) a 337 M (2019) e missione 3 scende da 216 a 177 M; la missione 14 (sviluppo economico) scende da 96 M (2015) a 14 M (2016) nel Titolo 1. Probabilmente cambio di assegnazione di costi (personale, trasferimenti) non cambiamento di spesa: controllare prima di commentare.
9. **Programmi che compaiono o spariscono**: 12/11 "Asili nido" ha importi solo nell'edizione 2024-2028 (88,3 M nel 2024, 90,8 M nel 2025, in Titolo 1), mentre 12/1 scende di conseguenza; 10/1 (ferroviario) e 10/4 (altre modalita') esistono come codici solo in alcune edizioni ma senza spese correnti; 12/5, 17/1, 20/3 hanno importi quasi nulli. Per l'elenco dei programmi per edizione vedere `pulito/spesa_missioni.csv`.
10. **Il "rendiconto" non e' denominato come tipo di dato**: le tabelle non dicono se sono impegni/accertamenti o pagamenti. Il confronto col Ministero (impegni) quadra al centesimo per il Titolo 1 2013 e 2015, quindi sono impegni/accertamenti di competenza.
11. **Il primo stanziamento di ogni edizione non e' dichiarato come "iniziale" o "assestato"**: l'edizione e' pubblicata a primavera dell'anno dopo il rendiconto, senza data di riferimento. Per il 2013 ds227 dice esplicitamente "assestato"; per il 2014 "al 27/02/2014".
12. **Il solo anno 2012 in ds227** ha 61,6 M in meno del Ministero (2.443,7 vs 2.505,3): non spiegato.
13. **Date di aggiornamento**: ds397 (2019), ds396 (2018/2022 JSON), alcuni JSON piu' recenti dei CSV: CSV e JSON potrebbero non coincidere. Ho usato i CSV.
14. **Le tabelle non hanno la "Direzione" stabile**: ds3013 ha codici tipo "2_C", prima codici "DIR14"; la riorganizzazione degli uffici impedisce confronti per direzione.
15. **Popolazione**: due definizioni e una rottura nel 2012 (punto 6).
16. **Pro capite 2025**: manca la popolazione del 2025 in ds71/ds73.

## 9. Cosa manca / cosa resta da decidere

- Consuntivo **2014** per missione: solo dal Ministero (Quadro 4, per funzioni vecchie) o dal PEG 2014 non pubblicato come dato aperto.
- Anni 2012-2013: solo spesa corrente (e 2013 entrate correnti); niente spese in conto capitale nelle fonti del Comune.
- Anni prima del 2012: decidere se fare la raccolta dal Ministero (70 pagine HTML) - con la corrispondenza vecchio/nuovo in `corrispondenza_funzioni_missioni.csv`: molte righe sono 1:1 o n:1, ma **non esiste una corrispondenza 1:1 per**: personale (interventi vs macroaggregati), assistenza/beneficenza (si spezza in 5-6 programmi), biblioteche/musei, anagrafe/statistica, farmacie e servizi produttivi, affissioni e pubblicita', e per le voci nuove (fondi, debito, giovani, lavoro, sicurezza urbana). Inoltre dal 2015 cambia il metodo di contabilizzazione (competenza finanziaria potenziata): le spese in conto capitale (3,0 miliardi di impegni nel 2008, 0,75 nel 2015) non sono confrontabili.
- Popolazione 2025.
- Elenco dei capitoli equivalenti per le serie storiche di multe, Area C, sosta, imposta di soggiorno.

## 10. Fase 3 - pagina (docs/bilancio-comune/)

Programma: `scripts/pagina.py` (`python -I -X utf8 scripts/pagina.py <cartella bilancio-comune>`), scrive `docs/bilancio-comune/data/` (riepilogo.json + 7 CSV con `;` e punto decimale). Pagina: `docs/bilancio-comune/index.html` (solo consuntivi 2015-2025, mai previsioni).

**Cosa mostra la pagina**
- Riquadro "cosa sorprende" (3 fatti, tutti calcolati dal JSON): (1) spese correnti per abitante in euro 2025: 2.520 (2015) -> 2.350 (2025), -6,7%; -9,3% fermandosi al 2024; (2) tariffe del TPL / spesa TPL: 52,6% (2015), 50,5% (2019), 37,9% (2025); (3) 2020: entrate correnti -2,8% (3.301 -> 3.208 M) con incassi propri -554 M e trasferimenti +555 M.
- Spese correnti per missione (barre impilate, 3 unita': euro 2025 per abitante / milioni euro 2025 / milioni di ogni anno), classifica dell'ultimo anno con variazione dal 2015, tabella, nomi ufficiali e programmi piu' grandi 2025.
- Entrate correnti per tipo (stesse 3 unita'), tributi principali, 15 voci piu' grandi del 2025.
- Voci concrete: trasporto pubblico (spesa 10/2, tariffe, trasferimenti Regione/Agenzia, fondi Stato; linee M4/M5), multe del codice della strada, Area C, imposta di soggiorno, dividendi (A2A, SEA). Sosta: NON mostrata (vedi sotto).

**Scelte**: spesa = titolo 1; euro 2025 = importo*100/FOI(anno); abitanti = pop_calcolata_istat_fine_anno (ds71); **2025 = valore 2024 (stima, segnata con * nelle pagine)**; entrate correnti = titoli 1-3 (tributi; trasferimenti; titolo 3 diviso nelle tipologie servizi / multe / interessi e dividendi / rimborsi). Sensibilita': con gli abitanti dell'anagrafe (somma quartieri) la variazione 2015-2024 per abitante e' -11,1% invece di -9,3%.

**Trappole trovate in questa fase**
1. **ERRORE nei numeri del punto 4 di questo file (e quindi anche nel JOURNAL)**: le cifre "2016 64,6 / 2019 65,7 / 2023 57,6" (Area C), "556,6 / 487,9 / 488,1" (sanzioni), "82,8 / 118,2 / 125,3" (imposta di soggiorno) sono state ottenute sommando `bilancio_capitoli.csv` senza scegliere un'edizione per anno: gli anni 2016-2024 stanno in due edizioni e venivano contati due volte. Valori giusti (una edizione per anno, milioni di euro): Area C 2016 32,3; 2019 32,9; 2023 28,8; 2025 33,7 (il 2025 era gia' giusto perche' compare in una sola edizione). Sanzioni CdS 2016 278,3 (include i regolamenti comunali); 2019 243,9; 2023 244,1; 2024 320,2; 2025 260,8. Imposta di soggiorno 2016 41,4; 2019 59,1; 2023 62,7; 2025 114,0. Quindi "Area C dimezzata" era falso: e' stabile (28-36 M, 16 M nel 2020). **Regola: su bilancio_capitoli.csv filtrare sempre un'edizione per (tipo, anno)** (lo fa pagina.py; nelle altre due tabelle c'e' `da_usare`).
2. **Nomi dei capitoli che cambiano**: multe CdS = 3 nomi (2015-16 "...a leggi e regolamenti comunali", 2017-19 "...alle norme", dal 2020 "...delle norme"); le "esercizi precedenti" cambiano nome nel 2020; imposta di soggiorno 2 nomi; trasferimenti TPL 4 nomi (Contributi regionali -> Trasferimenti da Regione -> da Agenzia -> "TPL - da Agenzia"; sempre 264-276 M). Le equivalenze sono per nome, segnate come stima nella pagina e nell'elenco `capitoli_usati.csv`. "Proventi da tariffe per il TPL" ha lo stesso nome in tutti gli anni.
3. **Salto 2018/2019 tra missione 1 e 3**: dentro la missione 1 il programma 10 "Risorse umane" passa da 51,3 a 123,1 M, e nella missione 3 "Polizia locale" scende da 213,1 a 173,9 M. Sembra uno spostamento dei costi del personale, non un taglio: pagina segna con * le missioni 1, 2, 3, 14 (2/14: salti 2015/2016; il programma 14/2 "Commercio" scende da 89,0 a 8,8 M).
4. **Sosta a pagamento**: i capitoli con "sosta a pagamento" valgono 0,1-7 M e cambiano nome (2015-19 "Corrispettivo per la gestione del servizio di sosta a pagamento"; dal 2020 "Proventi da parcheggi - servizio di sosta a pagamento", 0,6-3,7 M): non e' una serie affidabile, la pagina lo dice e non la disegna.
5. **Capitolo M5**: "Linea M5 - servizi di TPL su nuova infrastruttura" compare nel 2023 con 100,2 M mentre "Servizio di TPL" scende da 777 a 763: puo' essere uno spostamento di costi; la linea M4 cresce da 4,9 (2021) a 94,6 (2025).
6. **2020-2021**: il capitolo "Trasferimenti statali di cui ai DL 34/2020 e 104/2020 (emergenza Covid)" vale 411,7 M (2020), 283,1 (2021), 21,9 (2022); "TPL - fondo per riduzione ricavi tariffari" 66,3 / 183,5 (+28,2 servizi aggiuntivi Covid) / 77,0 (+8,0); ancora 75,8 M nel 2024 e 26,5 nel 2025.
7. **Dividendi**: 56,6 M (2015) -> 203,2 M (2025): A2A 28,4 -> 78,3; SEA 27,9 -> 89,8 (+32,9 "dividendi straordinari" nel 2025, 21,9 nel 2024); picco SEA 85,4 nel 2019.
8. Il 2025 del dataset ds3013 (aggiornato 21/8/2026) non dichiara se e' il rendiconto definitivo.

**Non mostrato / dubbi**: sosta (punto 4); anni 2012-2013 (solo spese correnti, abitanti con rottura 2012); ripartizione 2015 vs 2025 delle missioni 1, 3, 14 (da prendere con cautela); quote "tariffe/spesa TPL" sono un nostro rapporto tra due capitoli, non un indicatore ufficiale; popolazione 2025 = 2024 (da sostituire con il dato ISTAT quando disponibile: basta aggiungere la riga in `popolazione_milano.csv` e rilanciare pagina.py).

