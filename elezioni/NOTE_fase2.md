# Elezioni milanesi: note di fase 2 (pulizia, famiglie, mappe, pagina)

Per il JOURNAL (da unire a mano dal coordinatore). Data: 2026-10-29. Niente git, niente GitHub.

## File prodotti
- `pulito\elezioni.csv` (157 consultazioni), `pulito\risultati_sezione.csv` (246.527 righe), `pulito\voti_sezione.csv` (1.903.679 righe), `pulito\aggregati_territorio.csv`, `pulito\problemi.md` (trappole e correzioni), `pulito\confini_verifiche.json`.
- `famiglie_partiti.csv` (tabella modificabile, "da rivedere").
- Script: `scripts\11_carica.py`, `13_pulizia.py`, `14_problemi.py`, `15_famiglie.py`, `16_aggrega.py`, `20_confini_ckan.py`, `21_confini_build.py` (nuovi scarichi in `raw\_confini\`).
- Sito: `..\docs\elezioni\index.html` + `data\index.json` (aggregati per territorio, 164 KB), `data\e\<id>.json` (una per elezione, sezione per sezione, 6,5 MB in tutto), `data\municipi.geojson`, `data\circoscrizioni.geojson`, `data\famiglie_partiti.csv`. Totale 6,9 MB. Per vederlo serve un server web (`preview milano-in-dati`, porta 8796, pagina `/elezioni/index.html`).

## Famiglie
463 nomi di lista/candidato diversi (nelle 64 consultazioni usate) + Si/No. Assegnati: Centrosinistra 66, Sinistra 57, Centro 51, Centrodestra 39, Destra 31, Lega 11, M5S 8, Altri 201 (di cui 131 senza nessuna regola, 70 messi in Altri per scelta: radicali, pensionati, liste civiche locali, autonomisti minori). In voti: Altri e circa il 4% del totale. 69 righe sono segnate `da_rivedere`. Scelta da confermare: PCI-PDS-DS-PD tutti nel Centrosinistra (il PCI 1979-1992 non sta in Sinistra, altrimenti l'emiciclo "salta" nel 1992); PSI nel Centrosinistra; DC, PRI, PLI, PSDI nel Centro; UDC nel Centro ma NCD, Noi con l'Italia e Noi Moderati nel Centrodestra; +Europa e Azione-IV nel Centro; Verdi e Rifondazione nella Sinistra; AN, MSI, Fratelli d'Italia, Fiamma, Forza Nuova, CasaPound nella Destra; La Rete 1993 in Sinistra. Sindaco/ballottaggio: candidato -> famiglia della coalizione (verificato su Wikipedia per 1993 e 1997).

## Mappe
Confini trovati sul portale: ds379 (9 municipi), ds153 (9 zone di decentramento, 2013) e ds378 ("ex 20 zone di decentramento"). Le 9 zone 1999-2011 coincidono con i municipi: superfici uguali entro lo 0,005%, stessi numeri. Le 20 ex zone servono per le circoscrizioni fino al 1997 (assunto che il numero coincida: non c'e una tabella ufficiale; la 1 contiene il Duomo). Quindi la mappa c'e per tutte le epoche, nessun elenco di ripiego.

## Prima del 1979 (Eligendo, archivio storico del Ministero dell'Interno)
Il sito ha una sezione "Open data" (`/eligendo/opendata.php`, info in `/eligendo/info_opendata.php`) con: Assemblea Costituente 1946, Politiche dal 1948, Europee dal 1979, Referendum dal 1946, cicli regionali dal 1970, solo le ULTIME amministrative (quindi niente Comunali di Milano storiche). Le pagine raggiungibili senza JavaScript non dicono formato, livello territoriale (comune/sezione) ne licenza, e non danno link diretti a file; e indicata una mail (elezioni.storico@interno.it). Non ho guardato altro (niente scarico pagina per pagina, nessuna registrazione). Da capire a mano: se i dati delle Politiche 1948-1976 sono scaricabili per comune (quindi anche Milano citta) e in che formato.

## Problemi aperti
- Date dei ballottaggi 1993, 1997 e 2009 prese dal calendario, non dal portale: da verificare.
- Affluenza non disponibile in 13 consultazioni del sito (Elettori a zero: 9 dataset 1979-1992; Votanti vuoti: Senato 1996 e 2001, Provinciali 2009, Circoscrizionali 2011).
- Politiche 2018/2022 e Regionali 2023 sono "dati ufficiosi" (segnalato nella pagina).
- 2 sezioni dei referendum 1981 senza territorio; sezioni 9001-9011 del 2025 tenute.
- Pagina senza grafica curata, come richiesto; la pagina e testata solo nel browser integrato (desktop), non su telefono.

## Elezioni prima del 1979 (Eligendo)

Data: 2026-10-29. Questa sezione corregge quella sopra intitolata "Prima del 1979": i file ci sono, si scaricano in blocco, e il livello e il Comune (una riga per lista).

**Fonte.** Archivio storico del Ministero dell'Interno, https://elezionistorico.interno.gov.it/ , sezione "Open data" (`/eligendo/opendata.php`). L'elenco dei file e scritto dentro la pagina stessa. Ogni file e un ZIP con link diretto: `https://elezionistorico.interno.gov.it/daithome/documenti/opendata/<tipo>/<tipo>-<AAAAMMGG>.zip` (il sito rimanda poi a `dait.interno.gov.it`). Nessuna registrazione, nessun login. In tutto 315 file; il catalogo e salvato in `raw\eligendo\_pagine\dataset.json`.

**File scaricati (29/10/2026).** 25 ZIP, 14,7 MB in totale, in `raw\eligendo\<tipo>\`:
- Costituente 1946 (0,45 MB), referendum 1946, 1974, 1978 (0,16 + 0,16 + 0,33 MB);
- Camera e Senato 1948, 1953, 1958, 1963, 1968, 1972, 1976 e 1979 (Camera 0,63-1,5 MB l'uno, Senato 0,32-0,60 MB l'uno);
- Regionali 1970 e 1975 (0,47 + 0,45 MB);
- Comunali 1964, 1970, 1975 (1,0-1,1 MB l'uno, formato Excel; gli altri sono testo con `;`).

**Licenza.** Non l'ho trovata: ne le pagine Open data e Info del sito, ne la pagina open data del Dipartimento (dait.interno.gov.it) indicano una licenza. L'unica frase e che l'archivio e messo a disposizione "a puro scopo divulgativo", che i dati vengono dai verbali conservati dalla Direzione Centrale per i Servizi Elettorali e che sono "ufficiali" piu "ufficiosi" (comunicati dai comuni). Per ripubblicare conviene citare la fonte ("Ministero dell'Interno, Eligendo") e, se serve certezza, scrivere a elezioni.storico@interno.it.

**Cosa c'e per Milano (`pulito\milano_pre1979.csv`, 231 righe, 25 consultazioni).**

| Tipo | Anni |
|---|---|
| Assemblea Costituente | 1946 |
| Referendum | 2/6/1946 (Repubblica/Monarchia), 12/5/1974 (divorzio), 11/6/1978 (2 quesiti) |
| Camera | 1948, 1953, 1958, 1963, 1968, 1972, 1976, 1979 |
| Senato | 1948, 1953, 1958, 1963, 1968, 1972, 1976, 1979 |
| Regionali | 1970, 1975 |
| Comunali (liste) | 1964, 1970, 1975 |

Manca: Comunali 1946, 1951, 1956, 1960 (non sono nell'archivio). Non ci sono i sindaci (prima del 1993 non si eleggevano direttamente). Le Europee iniziano nel 1979 e sono gia nei dati del Comune. Colonne: elezione_id, tipo, data, quesito, lista, voti, seggi (solo Comunali), elettori, votanti, schede_bianche, somma_voti_liste, n_collegi, fonte. Elettori, votanti e bianche sono ripetuti su ogni riga della stessa consultazione. I voti validi non sono nel file: la somma delle liste e il 98-99% di (votanti meno bianche), la differenza sono le nulle.

**Controllo con i dati del Comune (Camera 1979, `pulito\eligendo_confronto_camera1979.csv`).** Votanti identici (1.197.265). Somma dei voti di lista: Eligendo 1.160.750, sezioni del Comune 1.161.303, cioe 553 voti in meno (-0,05%). Per partito le differenze sono piccole: DC -95, PCI -241, PSI -83, PSDI -80, MSI -73, PLI -35, PRI +15, PDUP +20. Le liste minuscole differiscono di piu in percentuale (Operai Europei +28 su 699, PPI -8 su 425). Elettori Eligendo: 1.282.022 (nei dati del Comune per il 1979 gli elettori mancano). Le due fonti sono dunque coerenti: si possono attaccare le serie senza salto.

**Trappole.**
- I nomi delle liste cambiano da una fonte all'altra: Eligendo scrive `P.RAD`, `MSI-DN`, `NUOVA SIN.UNITA`, `DN-CD`, `POE`, `PARTITO POPOLARE ITALIANO`, `DEM.PROL`, il Comune `Part. Radicale`, `MSI`, `Nuova Sin. Unita`, `Dem. Nazionale`, `Part. Op. Eur.`, `PPI`, `Dem. Proletaria`. Anche dentro Eligendo lo stesso partito ha piu grafie (`PSIUP`/`PSI UP`, `MSI-DN`/`MSI DN`, `DEM.PROL`/`DEM. PROL.`, `PART MON NAZ`/`PART.MON.NAZ.`).
- Senato: Milano e divisa in 6 collegi, ogni collegio e una riga a parte; il CSV li somma. Gli elettori del Senato sono solo i maggiori di 25 anni, quindi sono meno di quelli della Camera (es. 1976: 1.146.221 contro 1.287.015): non confrontarli.
- Camera 1953: schede bianche a 0 (dato mancante, non vero zero).
- Codifica dei file diversa da uno all'altro (alcuni UTF-8, altri Windows-1252): lo script prova prima UTF-8.
- Referendum: i voti sono SI e NO. Nel 1946 SI = Repubblica (487.125 contro 231.711); nel 1974 SI = abrogare il divorzio (293.045 contro 812.955).
- Alleanze: nel 1948 il Fronte Democratico Popolare (PCI+PSI) e liste comuni (PCI-PSIUP al Senato 1968-72, PSU 1968) sono una sola riga: non si scompongono.
- Comunali 1964-1975: sono i voti di lista per il Consiglio comunale (come nei dati del Comune dal 1980), non i sindaci.
- Il sito avverte che dati riepilogativi e somma dei comuni possono differire (fonti diverse) e che i votanti possono superare gli elettori.

**Famiglie.** `famiglie_proposte_pre1979.csv` (60 liste non ancora in `famiglie_partiti.csv`, stesse colonne e stesse famiglie): 13 Sinistra, 11 Destra, 9 Centro, 2 Centrosinistra, 25 Altri. Regole: PCI, PSIUP, DP, Manifesto e marxisti-leninisti in Sinistra; PSU in Centrosinistra (da rivedere); socialdemocratici, repubblicani, liberali in Centro; MSI e monarchici in Destra. Uomo Qualunque 1946 e messo in Destra con `da_rivedere` (l'alternativa e Altri). Le righe con `da_rivedere = si` sono le dubbie (liste del 1946-1953 come Blocco Nazionale, Unione Democratica Nazionale, Unita Popolare, Fronte Democratico Popolare).

**Script.** `30_eligendo_catalogo.py` (elenco file dalla pagina), `31_eligendo_scarica.py`, `32_eligendo_ispeziona.py`, `33_eligendo_milano.py`, `34_eligendo_confronto_1979.py`, `35_eligendo_famiglie.py`. Eseguire con `python -I` e le cartelle come argomenti.

## Senato 1983-1994 (aggiunto 2026-10-29)

Nel sito la serie del Senato aveva un buco 1983-1994 (i dati del Comune partono dal 1996). Scaricati da Eligendo, con lo stesso schema degli altri (`raw\eligendo\senato\senato-19830626.zip` 0,58 MB, `-19870614` 0,76 MB, `-19920405` 2,1 MB, `-19940327` 0,48 MB; stesso URL e stesse colonne dei file 1948-1979). Aggiunti a `pulito\milano_pre1979.csv` (ora 286 righe; il nome resta, contiene tutto Eligendo) rigenerandolo con `33_eligendo_milano.py`, poi `16_aggrega.py`: il sito ha 167 consultazioni e la serie Senato e continua 1948-2022 (19 tappe).
- Milano e divisa in 6 collegi in tutti e quattro gli anni: sommati. Elettori solo di 25 anni e piu. Elettori/votanti: 1983 1.108.697/979.634; 1987 1.082.199/959.339; 1992 1.063.812/936.598; 1994 1.059.347/930.793.
- 1994: sistema in parte maggioritario, ma il file da comunque i voti di lista per collegio; le "liste" sono le coalizioni (Polo delle Liberta, Progressisti, Patto per l'Italia) piu Alleanza Nazionale e Lega a parte. Non si scompongono.
- Liste non ancora in `famiglie_partiti.csv`: 28, in `famiglie_proposte_senato.csv` (stesse colonne; da rivedere: Liga Veneta-PU, Lg. Angela Bossi, PSDI-Lega Nuova). Finche il coordinatore non le unisce, 16_aggrega le mette in Altri (pesa molto nel 1994: Polo 396.000 voti, Progressisti 244.000, Patto 89.000, AN 80.000). Dopo l'unione: rieseguire solo `16_aggrega.py` e ricopiare `famiglie_partiti.csv` in `docs\elezioni\data\`.
- Test: preview milano-in-dati, `/elezioni/`, Senato 1983, 1987, 1992, 1994, 1996: 100 seggi, nessun errore in console.

## Risultati per quartiere (NIL), dal 2016 (aggiunto 2026-10-29)

Per il JOURNAL. Mappa e focus per gli 88 NIL nella pagina `docs\elezioni\index.html` (selettore "Mappa per: Quartieri (NIL), dal 2016"), 30 consultazioni dal 2016 al 2026. Nessun git.

**Il legame sezione -> NIL.** Unica fonte ufficiale: ds939 (stradario del referendum 2020, una riga per civico: sezione, municipio, NIL). 51.323 civici, 1.238 sezioni, 88 NIL (stessi id e stessi nomi del confine ds964). Un civico non ha NIL (sezione 1847, via Cassinis Gino 6): escluso dai pesi. Sezioni su un solo NIL: 894; su 2: 292; su 3 o più: 52 (massimo 4): **344 sezioni divise** (NOTE.md ne contava 345 perché contava anche il civico senza NIL). Il file `pulito\sezione_nil.csv` ha una riga per (sezione, NIL): `n_civici`, `peso` (quota dei civici della sezione in quel NIL, la somma per sezione fa 1), `prevalente` (si/no: NIL col peso maggiore; 4 parità esatte, vince l'id più basso). Il NIL prevalente delle sezioni divise ha peso mediano 0,80 (minimo 0,42). `pulito\nil_info.csv`: per NIL sezioni, sezioni "effettive" (somma dei pesi, da 0,07 a 56,6; mediana 13,9), civici, quota di civici in sezioni condivise.

**Due varianti, entrambe nel sito** (selettore accanto alla mappa; predefinita la proporzionale).
- Proporzionale: voti, elettori e votanti della sezione moltiplicati per il peso in ogni NIL. Peso = numero di civici, non di elettori: un palazzo grande e una villetta contano uguale.
- Prevalente: tutta la sezione al NIL col peso maggiore. 8 NIL restano senza nessuna sezione (Giardini P.ta Venezia, Parco Sempione, Cascina Merlata, Parco Nord, Parco delle Abbazie, Parco dei Navigli, Assiano, Parco Bosco in Città) e nella mappa sono grigi.
- Confronto (`pulito\nil_confronti.csv`, NIL con almeno 2.000 votanti, 6 elezioni 2016-2026): la quota della famiglia in testa differisce in media di 0,2 punti (massimo 1,8) e la famiglia in testa cambia in un solo NIL su circa 64 (Camera 2018). Nell'insieme dei 30 file i NIL con leader diverso tra le due varianti sono da 0 a 4 per elezione (media 0,8), quasi tutti piccoli. Le due scelte raccontano la stessa storia; la proporzionale tiene tutti i NIL.

**Match sezioni (script 16, `pulito\nil_match.csv`).** Soglia: almeno il 95% delle sezioni E il 95% dei votanti con un abbinamento in ds939. Tutte e 30 le consultazioni 2016-2026 passano: sezioni abbinate 98,2-99,2% (1.237 o 1.238 su 1.247-1.260; non abbinate 10-23), votanti abbinati 97,3-99,99%. Il caso peggiore è il referendum 2025: 1.260 sezioni (23 senza abbinamento: le 11 speciali 9001-9011 e 12 normali che non sono nel 2020) e 97,3% dei votanti. Nel sito i voti non attribuiti sono scritti sotto la mappa (es. Europee 2024: 407 votanti, 0,08%). Nessuna elezione scartata per il 95%.

**Perché non prima del 2016.** Il numero di sezione coincide anche prima (2005-2014: 98,4-99,0% delle sezioni, 99,6-99,9% dei votanti), ma non basta: contano i civici. Controllo con gli stradari delle altre elezioni (`pulito\sezione_nil_stabilita.csv`, chiave via+civico+barrato contro ds939): la stessa sezione del 2020 si ritrova nel 98,8-100% dei civici per tutti gli stradari 2016-2026, nel 98,8-99,0% per 2013 e 2014, nel 92-98% per 2001-2011 (2001: 92,2%; 2008-2009: 97,8%). Quindi prima del 2013 il legame del 2020 sbaglia più spesso (fino a 8 civici su 100 in un'altra sezione) e quelle elezioni non sono pubblicate per quartiere; 2013 e 2014 passerebbero la soglia e si possono aggiungere con `ANNO_NIL = 2013` in 16_aggrega.py (decisione del coordinatore). Prima del 1999 la numerazione è un altro sistema (20 circoscrizioni): impossibile.

**Pesi del 2020 contro pesi dell'anno** (stradario di ogni elezione, civici ritrovati nel ds939 per chiave): su 6 elezioni (2016, 2018, 2021, 2023, 2024, 2026) la quota della famiglia in testa cambia di 0,01-0,07 punti in media (massimo 2,1, referendum 2026), nessun cambio di famiglia in testa. Usare i pesi del 2020 per tutti gli anni costa quindi pochissimo. Controllo indipendente: elettori per NIL (Comunali 2021, proporzionale) contro residenti adulti 2021 (ds205, filone citta-15-minuti, sola lettura): correlazione 0,98; rapporto mediano 0,88 (gli stranieri non votano). Fuori scala (rapporto fuori da 0,5-1,5): 10 NIL "fragili", segnati sulla pagina come i NIL con meno di 1.000 votanti (righe oblique): Giardini P.ta Venezia, Parco Sempione, Cantalupa, Cascina Merlata (quartiere costruito dopo il 2020: 13 civici nello stradario, 68 votanti nel 2024), Stephenson, Parco Nord, Parco delle Abbazie, Parco dei Navigli, Assiano, Parco Bosco in Città (`pulito\nil_controllo_popolazione.csv`).

**Esempi.** Comunali 2021 (Consiglio): famiglia in testa il Centrosinistra in tutti gli 88 NIL; quota Centrosinistra da 39,0% (Comasina) e 41,0% (Quarto Oggiaro) a 60,7% (Porta Vigentina - Porta Lodovica); affluenza da 38,7% (Quarto Oggiaro) a 54,5% (QT 8). Europee 2024: Centrosinistra in testa in 82 NIL, Destra in 6 (Giardini P.ta Venezia, Muggiano, Roserio, Quarto Oggiaro, Comasina, Assiano); Destra al 27,0% a Quarto Oggiaro e 28,4% a Comasina; Buenos Aires - Porta Venezia - Porta Monforte (NIL 21): Centrosinistra 35%, Destra 20% (Europee 2024), affluenza 51,3% (Comunali 2021).

**Cose da sapere (trappole).**
- Il confine usato è ds964 (NIL vigenti, PGT Milano 2030, già nel filone citta-15-minuti), non "ds61": i NIL e i nomi coincidono con quelli di ds939. Gli id vanno da 1 a 88.
- Il legame è fermo al 2020: i quartieri cresciuti dopo (es. Cascina Merlata) sono sottostimati.
- ds1979 (Politiche 2022) ha i collegi uninominali chiamati "Milano: NIL 52 - Bande Nere": è il nome del collegio, non un legame civico -> NIL; non usato.
- Elettori e votanti dei NIL sono arrotondati (la somma dei NIL può differire di qualche unità dal totale città). Nelle sezioni a cavallo il risultato del NIL è una stima, mai un dato ufficiale.
- ds939 è in Windows-1252; la colonna CAP contiene solo 3 cifre (già nelle trappole).

**File nuovi.** `pulito\sezione_nil.csv`, `nil_info.csv`, `sezione_nil_stabilita.csv`, `nil_match.csv`, `nil_confronti.csv`, `nil_controllo_popolazione.csv`. Sito: `docs\elezioni\data\nil.geojson` (72 KB), `nil_info.json` (9 KB), `nil_sezioni.json` (20 KB), `sezione_nil.csv`, `nil\<id>.json` (30 file, 408 KB, circa 14 KB l'uno, caricati solo quando servono). `index.json` ha in più il campo `nil` per le 30 consultazioni (226 KB). Script: `40_sezione_nil.py` (pesi, info, stabilità), `41_nil_geo.py` (confini, tabelle del sito), `16_aggrega.py` (modificato: scrive anche `data\nil\` e `nil_match.csv`), `42_nil_confronti.py` (confronti, controllo con la popolazione, campo `x`/`r` in nil_info.json). Ordine: 40 -> 41 -> 16 -> 42 (42 riscrive nil_info.json: dopo 41 rieseguire sempre 42).

**Test.** Preview milano-in-dati, `/elezioni/`: Comunali 2021 ed Europee 2024 per NIL, focus con emiciclo, tabella sezioni con quota, andamento nel tempo, tutte le 30 consultazioni (88 NIL colorati, 100 seggi, nessun errore JS), variante prevalente, ritorno ai municipi, scelta NIL su elezione pre-2016 (ritorno ai territori dell'epoca con nota). Nel browser integrato resta nel registro un vecchio errore "Unexpected identifier 'Massimo'" che compare su tutte le pagine del sito, anche su `docs\index.html` che non ho toccato: non viene da questa pagina.
