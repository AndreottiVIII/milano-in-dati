# Nomi dei bambini a Milano: note sulla fase 1 (fonti, scaricamento, pulizia)

Data: 1 novembre 2026. Cartella: `nomi-bambini\`. Nessuna pagina web fatta.
Come leggere: ogni numero dice da quale file e da quale campo viene. Tutti i programmi sono in `scripts\` (Python 3.12, `python -I -X utf8`, percorsi assoluti). Nessun account creato, nessuna registrazione, nessun git.

## In breve

1. **Il Comune di Milano NON pubblica i nomi dei nati come dati aperti.** Ho scaricato il catalogo intero di dati.comune.milano.it (2.611 dataset, 1/11/2026, `raw\ckan\catalogo_completo.json`) e cercato nome/nomi/prenome/cognome/battesimo/neonat in titoli, descrizioni, etichette e nomi dei file: nessun dataset con i nomi. Esistono solo i **totali** delle nascite (ds289, ds1942-1946, ds1495 "Nati vivi dal 1880") e un dataset sul pacco dono 2018 (`ds702`, solo numero di lettere per mese).
2. I nomi di Milano si trovano **solo nei comunicati stampa** dell'Anagrafe, riportati dai giornali: classifiche dei primi 3-10 nomi, per periodi diversi, a volte senza numeri. Li ho messi in `pulito\milano_stampa_top.csv` (63 righe, 2014, 2015, 2022, 2023 H1, 2024, 2025 H1). **Non è una serie**: periodi, lunghezza delle classifiche e perfino la presenza dei conteggi cambiano da un anno all'altro. La pagina del Comune (comune.milano.it) risponde 403 al download, non l'ho aggirata.
3. **Un dato più completo sui nomi di Milano esiste in mano al Comune** (la stampa riceve i numeri di ogni nome, anche i nomi con 1 solo bambino: "154 Giulia e una sola Shakira", LaPresse 11/8/2014) ma non è pubblicato. Strada possibile: richiesta all'Ufficio Statistica / Servizi Demografici del Comune (non fatta, non spetta a questa fase).
4. **ISTAT**: lo strumento "Conta nomi" (https://www.istat.it/dati/calcolatori/contanomi/) copre l'Italia dal 1999 (per anno: i primi nomi, con serie per ogni nome) da "Iscritti in anagrafe per nascita". Contenuti del sito sotto CC BY 4.0 (https://www.istat.it/note-legali/, letto il 1/11/2026). **Ma non è un file scaricabile**: i dati passano da un servizio web interno alla pagina (`birthName.js`, salvato in `raw\istat_probe\`). Ho provato a interrogarlo e il sistema di permessi me lo ha negato (accesso fuori dalle vie dichiarate): non ho insistito. Niente ISTAT nazionale in questa fase. Se serve: chiedere a ISTAT il file (Contact centre) o usare il grafico a mano per pochi nomi.
5. **Dati aperti completi sui nomi, vicini a Milano (tutti CC0, dati.lombardia.it, scaricati 1/11/2026)**: la fonte migliore è **Bergamo**: 1987-2025, ogni nome (anche con 1 bambino) per anno di nascita, sesso e cittadinanza (italiana/straniera). **Rozzano** (cintura sud di Milano): nomi dei nati sul territorio 2007-2017, tutti i nomi. Cremona e Brescia: foto di un solo anno (stock dei residenti), poco utili alla serie.
6. Tutto quello che segue è quindi **Bergamo come banco di prova** e **Rozzano come unica serie dell'hinterland milanese**, non Milano.

## 1. Fonti trovate

| Fonte | Che cosa | Anni | Righe | Licenza | Scaricato | Mancano |
|---|---|---|---|---|---|---|
| Comune di Milano, catalogo CKAN (`raw\ckan\`) | nessun dataset di nomi | - | 2.611 dataset esaminati | cc-by (campo `license_id` dei dataset) | 1/11/2026 | i nomi |
| Comune di Milano ds289 "Nascite avvenute a Milano" (`raw\milano_nascite\ds289_nascite.csv`) | totale nati per genere, cittadinanza dei genitori, luogo di residenza | 2003-2020 (ds1945 per 2021-2024) | 430 | CC BY (`license_id: cc-by`, titolo "Creative Commons Attribution") | 1/11/2026 | nomi |
| Comune di Milano ds1945 (`raw\milano_nascite\ds1945_nascite_milano_2021_2024.csv`) | nati per età dei genitori, parto, filiazione | 2021-2024 | 691 | CC BY | 1/11/2026 | nomi |
| Comunicati stampa Anagrafe via giornali (`pulito\milano_stampa_top.csv`) | classifica dei primi nomi, con o senza conteggi | 2014, 2015 (gen-lug), 2022, 2023 (H1), 2024, 2025 (H1) | 63 | non una banca dati: cifre del Comune citate da testate (LaPresse, Affaritaliani, Il Giorno) | 1/11/2026 | quasi tutto |
| **Bergamo, graduatoria dei nomi tra i neonati** (`raw\lombardia\bergamo_nomi_neonati_7nxs-kdhf.csv`) | residenti OGGI nati nell'anno X, per nome, genere, cittadinanza | nati 1987-2025 (39 anni) | 16.984 (→ 16.976 dopo la pulizia) | **CC0 1.0** https://creativecommons.org/publicdomain/zero/1.0/legalcode (campo `license` del metadato `.meta.json`) | 1/11/2026 (aggiornato dal Comune il 27/5/2026 secondo il catalogo) | chi non risiede più a Bergamo |
| Bergamo, graduatoria dei nomi (residenti, top 100 per anno) (`bergamo_nomi_residenti_s29g-dr7j.csv`) | primi 100 nomi tra tutti i residenti al 31/12 | 1987-2025 | 15.600 | CC0 1.0 | 1/11/2026 | oltre i primi 100 |
| Rozzano, nomi maschili e femminili (`rozzano_*.csv`) | nomi dei nati sul territorio del Comune | 2007-2017 (11 anni) | 1.134 + 1.209 | CC0 1.0 | 1/11/2026 | dopo il 2017 |
| Cremona graduatoria nomi (`cremona_graduatoria_rnp5-bkha.csv`) | stock residenti, un anno | 2022 | 16.423 | CC0 1.0 | 1/11/2026 | serie |
| Brescia graduatoria nomi per età (`brescia_eta_2018_4w2s-n4fk.csv`) | stock residenti per fascia di età | 1/1/2018 | 2.055 | CC0 1.0 | 1/11/2026 | serie |
| Emilia-Romagna, "Nomi attribuiti ai nati" (22 dataset annuali 2004-2024, CC BY 4.0, ospitati da un'Unione di comuni del Cesenate) | visti nei metadati, **non scaricati** | 2004-2024 | - | CC BY 4.0 | - | non è un'area comparabile con Milano |
| Torino, primi 10 nomi dei nati per circoscrizione 2015-2020 (CC BY 4.0) | **solo PDF**, non scaricati | 2015-2020 | - | CC BY 4.0 | - | - |
| ISTAT Conta nomi | strumento interattivo, non scaricabile | 1999-ultimo anno | - | contenuti CC BY 4.0 | - | tutto (vedi punto 4) |

Altri portali guardati (cataloghi in `raw\altri_portali\`): dati.gov.it (query "nomi nati", "nomi bambini", "graduatoria nomi" ecc.) → altre città con nomi (Rimini, Palermo, Firenze/Toscana, Vicenza, Rapallo "Nati 2020-2024 per nome e cittadinanza") ma nessuna per Milano. La Città metropolitana di Milano non ha dataset di nomi su dati.lombardia.it (ricerca "nomi", "prenomi", "graduatoria nomi", "cittadinanza nome").

## 2. Pulizia (`scripts\04_pulisci.py`, tabelle in `pulito\`)

- `nomi_nati_bergamo.csv`: colonne `anno, sesso, nome, cittadinanza, nati, fonte` (16.976 righe). `cittadinanza` = `italiana`/`straniera` come dichiarato dalla fonte (campo `CITTADINANZA`), niente stime di origine.
- `nomi_nati_rozzano.csv`: `anno, sesso, nome, nati, fonte` (2.342 righe).
- `nome` = chiave normalizzata (`scripts\common.py`): maiuscolo, accenti e apostrofi tolti (`NICOLO'` e `NICOLO` → `NICOLO`), virgole e trattini → spazio, spazi singoli. Le 35 coppie che si sono unite sono in `nomi_bergamo_varianti.csv`.
- Il nome originale non c'è più nelle tabelle pulite; è in `raw\`.

## 3. Trappole verificate

1. **Bergamo non conta le nascite, conta i residenti di oggi per anno di nascita.** Chi è nato a Bergamo nel 1990 e si è trasferito non c'è; chi è arrivato dopo da bambino sì. I totali per anno (788 nel 1987, 1.065 nel 2000, 719 nel 2025) NON sono le nascite del Comune (non ho i totali ufficiali di Bergamo per confrontare). Le coorti vecchie sono più "filtrate" delle nuove.
2. **Nome composto scritto in modi diversi**: `MARIA GIULIA` / `MARIAGIULIA` / `MARIA, GIULIA`. Virgole e trattini sono unificati; **gli spazi no** (`MARIAGIULIA` ≠ `MARIA GIULIA`, `ANNAMARIA` ≠ `ANNA MARIA`): non li ho uniti per non sbagliare (`XIN YI`/`XINYI`, `MAME DIARRA`...). Sono nomi rari; le classifiche in cima non cambiano.
3. **Una chiave doppia** (1997, PAOLO, M, italiana): sommata.
4. **Nomi dati a entrambi i sessi nello stesso anno**: ANDREA, MICHELE, JENNIFER, CELESTE, AYA, NOA, NOAH. Non toccati. Il sesso è quello del campo `GENERE`; nessun nome è riclassificato.
5. **Soglia di soppressione**: non c'è. Frequenza minima = 1 in tutti gli anni, sia a Bergamo sia a Rozzano. Quindi i nomi con 1 bambino sono presenti e i conteggi sono "veri" (la privacy è un tema del Comune, non del dato). Per Milano nulla da dire: il dato non c'è.
6. **Rozzano 2007-2017**: nel 2007 sono elencati 212 maschi e 213 femmine, nel 2017 183 e 192. Non so se coincidano con le nascite ufficiali (non ho il totale ufficiale per Rozzano): da verificare con ISTAT prima di usarlo.
7. **Formati diversi tra i dataset**: Milano ds289 usa `;` e nomi di colonna con numeri (`Cittadinanza_madre2`), Bergamo `,`, genere `M/F` nel dataset dei neonati e `Maschi/Femmine` in quello dei residenti. Non mescolati.
8. **Totali Milano vs stampa**: ds289/ds1945 contano le nascite avvenute a Milano (cittadini e non): 2022 = 9.876, 2024 = 9.165 (somma di `Numerosità` per `Anno_evento`). La stampa dà 9.886 (2022) e 9.147 (2024). Le differenze sono di 10 e 18: stesso ordine di grandezza, definizioni diverse (nati iscritti all'anagrafe vs avvenuti in città). Per una serie dei nomi va deciso a quale totale riferirsi.
9. **La stampa non è coerente**: Affaritaliani 14/8/2023 titola "Edoardo e Sofia" ma i numeri del 2022 (anno) dicono Leonardo 193, Tommaso 142, Edoardo 130; Edoardo è primo solo nel primo semestre 2023 (75). Il titolo si riferisce al semestre, il testo parla anche dell'anno. Meglio non usare i titoli.
10. **Sito del Comune**: comune.milano.it risponde 403 a WebFetch e a curl. Non aggirato.

## 4. Primi risultati (Bergamo come banco di prova; `out\riepilogo.txt`, `pulito\riepilogo_*.csv`)

Fonte per tutti i numeri sotto: `pulito\nomi_nati_bergamo.csv` (dal campo `FREQUENZA` di `bergamo_nomi_neonati_7nxs-kdhf.csv`, scaricato 1/11/2026). Sono residenti di oggi, per anno di nascita.

- **Nome più frequente per periodo di nascita** (maschi / femmine, totale del periodo): 1987-89 Andrea 116 / Chiara 59; 1990-99 Andrea 343 / Giulia 277; 2000-09 Andrea 244 / Giulia 190; 2010-19 Leonardo 159 / Sofia 144 (Alessandro 158, Giulia 139); 2020-25 Leonardo 89 / Vittoria 60. Andrea resta primo per 20 anni, poi sparisce dal podio.
- **Concentrazione**: i primi 10 nomi coprono il 41% dei maschi del 1987 e il 33% delle femmine; scendono al 24% (maschi 2012) e 18,5% (femmine 2012); i maschi poi risalgono (23,8% nel 2017, 28,3% nel 2025), le femmine restano intorno al 20%. Nomi distinti ogni 100 bambini: da 37 (M) e 46 (F) nel 1987, a un minimo di 26-31 nel 1997, a 60-63 nel 2017.
- **Nomi spariti** (almeno 20 bambini nel 1987-99 e al massimo 2 nel 2015-25): Valeria 54→2, Veronica 42→2, Daniela 37→0, Jessica 35→0, Simona 33→2, Manuel 25→2, Barbara 25→0, Mauro 24→1, Monica 24→0, Erica 24→2, Rossella 23→1 (`riepilogo_bergamo_scomparsi.csv`).
- **Nomi nuovi** (al massimo 1 bambino nel 1987-2004, almeno 25 nel 2015-25): Enea 33, Adam 29, Nina 28, Olivia 27. **Cresciuti di più in quota** (nomi che c'erano già): Ginevra 3→72 (x33), Vittoria 7→89 (x17,5), Aurora 9→60, Emma 12→79, Bianca 11→57, Matilde 16→77.
- **Cittadinanza straniera** (campo `CITTADINANZA`): quota dei nati residenti con cittadinanza straniera: 0,3% (1987), 9,4% (2000), 20,3% (2005), 28,6% (2010), 31,1% (2015), 24,3% (2020), 18,6% (2025). I nomi più dati ai bambini con cittadinanza straniera (2015-25): Sofia 19, Matteo 15, Rayan 10, Sara 10, Adam 10, Leonardo 10, Youssef 8, Emily 8; per gli italiani: Leonardo 163, Alessandro 137, Tommaso 135. Nomi che compaiono prima nel gruppo straniero: Omar, Yasmine, Zakaria (1987-2004). Nessuna classificazione di origine dei nomi.
- **Milano nascite** (`pulito\nascite_milano_ds289.csv`, ds289): 12.522 nati nel 2003, 11.646 nel 2014, 10.238 nel 2020; ds1945: 10.143 (2021), 9.876 (2022), 9.502 (2023), 9.165 (2024).
- **Milano dalla stampa**: Leonardo primo tra i maschi nel 2014 (154), nel 2015 (93, a pari con Alessandro) e nel 2022 (193); Giulia prima tra le femmine nel 2014 (154) e nel 2015 (71), Sofia nel 2022 (116). Nel 2024 Matilde è sul podio delle femmine: nel 2014 non era tra le prime 10, nel 2015 (gen-lug) era 9a con 38.

## 5. Cosa può mostrare una pagina

- Con i dati attuali: nessuna pagina "Milano" onesta sui nomi. Una pagina può mostrare Bergamo (e Rozzano) come esempio chiaro, dichiarando "residenti nati nell'anno", oppure **aspettare** i dati del Comune di Milano (richiesta formale all'Anagrafe).
- Se i dati di Milano arrivassero nel formato di Bergamo (anno, sesso, nome, nati): le tabelle di `pulito\` e gli script 04/05 funzionerebbero uguali.
