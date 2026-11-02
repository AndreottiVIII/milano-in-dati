# Associazioni e terzo settore - FASE 1 + pagina

Scaricato il 2 novembre 2026. Ogni numero dice file e campo; tutti sono ricalcolati da `scripts/pagina.py` (controlli `check()`, campo `avvisi` di `docs/terzo-settore/data/riepilogo.json` vuoto). Programmi con `python -I -X utf8 <script> <percorsi assoluti>` (vedi STATO.md). File grezzi in `raw/` (non fidati, mai eseguiti).

## 1. In breve
1. **RUNTS: 154.244 enti iscritti in Italia, 3.986 con sede legale a Milano** (lista pubblica "Lista enti" del 2/11/2026). Sezioni a Milano: altri ETS 1.508, APS 1.214, imprese sociali 639 (449 cooperative sociali dal nome), ODV 560, enti filantropici 64, 1 senza sezione. Nessun ente con sezione "società di mutuo soccorso" a Milano (205 in Italia).
2. **Per 10.000 abitanti (residenti ISTAT 1/1/2025: 1.365.698): 29,2 contro 26,2 in Italia; 9ª su 18 grandi città** (Firenze 46,5, Padova 43,9, Bologna 39,3; ultime Genova 24,5, Napoli 21,6, Prato 20,1).
3. **Il risultato di Milano è tutto negli "altri enti"** (11,0 ogni 10.000: 1ª su 18); APS 8,9 (18ª, ultima), ODV 4,1 (16ª).
4. **Riconciliazione con benessere/ (53,9 contro 61,0, 85ª su 107)**: il Bes è la provincia (Città metropolitana, 133 comuni) e conta tutto il non profit ISTAT. Nella provincia gli enti RUNTS sono 20,4 ogni 10.000 (6.621 enti, 3.246.455 residenti) contro 26,2 in Italia; nel solo comune 29,2; nel resto della provincia 14,0 (2.635 enti, 1.880.757 residenti). ISTAT 2023 (tavola 22): 17.900 istituzioni nella provincia (55,1 con i residenti 2025; Italia 368.367, 62,5). RUNTS/ISTAT: 37% in provincia, 42% in Italia (date diverse: 2026 e 2023).
5. **2011 (ultimo dato ISTAT per comune)**: Milano 6.662 istituzioni, 142.539 volontari, 68.066 dipendenti+lavoratori esterni; per istituzione 21,4 volontari e 10,2 dipendenti/esterni, primi tra 18 città (Roma 20,6 e 8,1). I totali di Milano nel file ISTAT (DICA_N01GCOM) coincidono con ds273 del Comune.
6. 5 per mille: 67% degli enti milanesi (2.686) ha "Si" nella colonna 5x1000 (Italia 53%); lettura nostra della colonna.
7. Iscrizioni: 1.452 su 3.986 (36%) del 2022 = trasmigrazione dai vecchi registri; 2023-2026: 2.533.
8. **Per quartiere (NIL) non si può con il RUNTS**: la lista pubblica ha solo il comune. La mappa usa 3 elenchi minori (non sommabili): registro anagrafico delle associazioni del Comune ds1332 (795; 677 localizzate), albo cooperative sociali ds562 (277; 274 con NIL), persone giuridiche della Regione ds606 (338; 305 localizzate), più ONG ds596 (57, con NIL). Duomo ha l'1,2% dei residenti, il 20% delle persone giuridiche e il 9% delle cooperative sociali.

## 2. Fonti, una per una (`raw/*/download_log.csv`: byte e sha256)
| Fonte | File | Licenza | Note |
|---|---|---|---|
| RUNTS, Lista enti (servizi.lavoro.gov.it/runts/it-it/Lista-enti) | `raw/runts/2026-11-02_20261102_iscritti_v1.1.xlsx` (13 MB, 154.244 righe) | **nessuna licenza indicata** sul portale; registro pubblico per legge (art. 53 d.lgs. 117/2017); note legali: rispettare il GDPR | Il pulsante "Scarica" è un modulo ASP.NET: lo script `download_runts.py` fa GET + POST del modulo, una volta, user-agent dichiarato, nessun aggiramento. Il PDF gemello (30 MB) è stato scaricato e cancellato. |
| dati.lavoro.gov.it | - | - | Portale DataPortal.AI (JavaScript, API non documentata): nessun dataset RUNTS trovato (ricerca web e sonda dell'API); non insistito. |
| Comune di Milano CKAN | `raw/comune/ds1332 ds562 ds606 ds596 ds273 ds274 ds1301 ds1342 ds76` (CSV + package_show.json) | ds1332, ds273, ds274, ds1301, ds1342, ds76 CC BY; ds562, ds606, ds596 CC0 | Scaricati 2/11/2026. ds1332 aggiornato 28/8/2026 (trimestrale); ds562/ds606/ds596 12/10/2026. Non usati: ds274, ds1301 (case delle associazioni), ds1342 (albo comitati, 34 righe, sperimentazione chiusa 2021), ds76 (associazioni culturali 2020). |
| ISTAT, Tavole non profit 2023 | `raw/istat/2026-11-02_Tavole_nonprofit_2023.xlsx` (tavola 22: istituzioni e dipendenti per provincia) | CC BY 4.0 (note legali ISTAT) | Solo nazionale, regionale, provinciale. |
| ISTAT, censimento non profit 2011, dati comunali | `raw/istat/ds_N01GCOM/` (zip 21 MB), `ds_N01CCOM/` (160 MB), `ds_N01SS/` (26 MB) | CC BY 4.0 | Da esploradati.istat.it/databrowser/DWL/censtatv5db/... Nel "COM" solo il 2011 (non il 2015); N01SS ha il 2015 ma solo regioni/province (138 territori). N01CCOM scaricato ma non usato nella pagina (ANPIREV/EXP, forme giuridiche per classi). |
| ISTAT, popolazione 1/1/2025 e 2026 (stima) | `raw/istat_pop/POSAS_2025_it_Comuni.zip`, `POSAS_2026_it_Comuni.zip` | CC BY 4.0 | Usato il 2025 (definitivo). |
| Bes 2025 | già in `benessere/pulito/bes_lungo.csv` (05REL008) | CC BY 4.0 | Province e città metropolitane. |
| Civici ds634 e NIL ds964 | già in `citta-15-minuti/raw/` | CC BY | Per portare gli indirizzi ai NIL. Nessun geocodificatore esterno. |

## 3. Pulizia (`scripts/build.py`, risultati in `pulito/riepilogo_build.json`)
- RUNTS: tolta subito la colonna "Cognome e nome legali rapp." (nomi di persone); controllato che i 154.244 codici fiscali siano tutti da 11 cifre (nessuna persona fisica) e unici. **Trappola**: letto con pandas, la sigla di provincia "NA" (Napoli) diventava dato mancante e Napoli risultava a 0 enti; corretto con `keep_default_na=False` e un assert. Sezione "-" -> "n.d." (14 righe in Italia, 1 a Milano).
- "Tipo dal nome": cooperativa sociale = sezione imprese sociali + "COOP" nel nome (449 a Milano); fondazione = "FONDAZIONE"/"FOUNDATION" (584; sono approssimati, la lista non ha forma giuridica); le altre voci dalla sezione (ODV, APS, altro ETS).
- Grandi città = 18 comuni con almeno 197.000 residenti (1/1/2025): Roma, Milano, Napoli, Torino, Palermo, Genova, Bologna, Firenze, Bari, Catania, Verona, Venezia, Messina, Padova, Brescia, Parma, Trieste, Prato. Corrispondenza RUNTS: nome del comune normalizzato + sigla di provincia.
- Quartieri: geocodifica con il registro civici ds634 (modulo `lib_geocode.py`, copia di `botteghe/scripts/lib_botteghe.py`). ds1332: 663 ok + 14 senza lettera = 677 con NIL; 57 fuori Milano; 37 via non trovata, 16 civico non trovato, 8 senza civico. Controllo: il Municipio del NIL trovato coincide con "Municipio prevalente" nell'81% dei casi (non è un errore se differiscono). ds606: 302 + 3 = 305 su 338.
- Popolazione dei quartieri: ds205 2024 (1.407.044 totale) da `alberi/pulito/nil_alberi.csv`; quella ISTAT 2025 del comune è 1.365.698 (fonti diverse: usate in punti diversi della pagina e dette).
- Cooperative sociali: RUNTS (449 dal nome) e albo del Comune (277) non coincidono: definizioni diverse (albo regionale/comunale contro registro nazionale delle imprese sociali). Non riconciliati.

## 4. Limiti (anche nella pagina)
Solo enti iscritti; iscrizione non è nascita (2022 = trasmigrazione); sede legale non operativa; il RUNTS pubblico non ha indirizzo, settore, bilancio; gli elenchi del Comune/Regione sono piccoli, volontari, sovrapposti; numeri piccoli per quartiere; tipo dal nome approssimato; "5x1000" letto come presenza nell'elenco del 5 per mille (nessuna spiegazione nel file); 2011 non confrontabile con oggi; residenti ISTAT 2025 contro anagrafe del Comune.

## 5. Da decidere / non fatto
- **Licenza RUNTS non indicata**: la pagina pubblica nome, sezione, anno e 5x1000 di 3.986 enti (tabella con ricerca + `enti_milano.csv`); se si vuole prudenza, si può togliere la tabella e tenere solo i conteggi.
- Il dettaglio per ente (indirizzo, attività di interesse generale, bilancio) è nelle schede del portale RUNTS "Ricerca enti": non lette (una pagina per ente = scraping, escluso).
- Registro statistico ISTAT del non profit 2016-2023: solo regioni/province nelle tavole; non cercati i microdati.
- Confronto RUNTS con ds1332/ds562 per nome (sovrapposizione): non fatto.
- Rinominare/aggiungere la sezione in `docs/menu.js` e `docs/index.html` (non toccati qui).
