# Il consiglio comunale: presenze e voti - FASE 1 (raccolta, pulizia, riepiloghi) e dati della pagina

Scaricato il 2 novembre 2026. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorsi assoluti>` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`. Pagina: `docs/consiglio/index.html` (dati in `docs/consiglio/data/`).

## 1. In breve

1. **Fonte**: Comune di Milano, portale CKAN dati.comune.milano.it, licenza `cc-by` (Creative Commons Attribuzione, versione non scritta sul catalogo). Tre dataset, tutti trovati dal filone `amministratori/` (`amministratori/raw/comune/search_*.json`):
   - **ds743** "Consiglio comunale 2016-2021 - Presenze e votazioni dei consiglieri": 31 CSV. Tre file sono totali del solo anno (luglio-dicembre 2016, 2017, 2018); da gennaio 2019 a settembre 2021 sono totali CUMULATI dall'inizio del mandato, un file per mese (mancano agosto, novembre 2019, gennaio 2020 e agosto 2020).
   - **ds1643** "Consiglio comunale 2021-2026 - Presenze e votazioni dei consiglieri - Riepilogo": un CSV, totali cumulati dall'inizio del mandato per ogni mese da ottobre 2021 a **maggio 2026** (2.549 righe; ultimo aggiornamento 3/6/2026). Il catalogo non ha mesi successivi (controllato il 2/11/2026).
   - **ds1914** dimissioni o surrogazioni 2021-2026: 4 righe.
   - Controllo incrociato: 3 file mensili separati (ds1648 novembre 2021, ds2966 e ds2967 dicembre 2025) coincidono con ds1643 per tutti i 49 consiglieri.
2. **Cosa c'è**: per ogni consigliere e mese: gruppo, sedute del consiglio dall'ingresso in carica, presenze, votazioni tenute, votazioni a cui ha partecipato. **Cosa NON c'è**: il voto (sì/no/astenuto) e il titolo della delibera. Ricerca nel catalogo (per votazioni, delibere, sedute, ordine del giorno, mozioni, consiglio comunale; ricerche del filone amministratori + quelle del 2/11/2026): nessun dataset con il voto per votazione. Perciò **non rispondibili** con questi dati: quanto spesso maggioranza e opposizione votano insieme, quota di votazioni all'unanimità, votazioni più divisive per argomento. La pagina lo dice (sezione "Quello che i dati non dicono").
3. **Numeri chiave** (tutti in `docs/consiglio/data/riepilogo.json`, sindaco escluso salvo dove scritto):
   - 2016-2021 (luglio 2016 - settembre 2021): 381 sedute, 4.866 votazioni; presenze 89,0%, partecipazione al voto 66,5% (mediane 96,2% e 75,9%); 56 consiglieri + sindaco (8 entrati a mandato iniziato); in media 32 consiglieri su 49 per votazione, 43 per seduta.
   - 2021-2026 (ottobre 2021 - maggio 2026): 281 sedute, 4.021 votazioni; presenze 86,1%, voto 62,7% (mediane 90,6% e 65,5%); 58 consiglieri + sindaco (10 entrati dopo); 30 su 49 per votazione, 42 per seduta.
   - Per anno (senza sindaco): presenze 92,4% (2016), 90,1, 87,8, **85,9 (2019)**, 89,7, 91,3; 2021-26: 90,5 (ott-dic 2021), 88,6, **83,1 (2023)**, 85,0, 87,2, 84,9 (gen-mag 2026). Voto: minimo 62,8% (2019) e 57,6% (2023, anno con 1.410 votazioni in 67 sedute).
   - Divario presenze - voto per gruppo (2021-26, gruppi con almeno 800 sedute-persona): PD 15 punti, Beppe Sala sindaco 15, Riformisti 18, EV 19, Lega 33, FdI 41, Forza Italia 41.
   - Sindaco: 85 presenze su 281 (30,2%) nel 2021-26; 141 su 381 (37,0%) nel 2016-21; escluso da tutti i confronti.
   - Donne/uomini (presenze): 2016-21 90,4% / 88,2%; 2021-26 82,8% / 87,9%. Rispetto al proprio gruppo (stesso mese) le donne sono -2,4 e -4,3 punti, gli uomini +1,4 e +2,4. Rimescolando il sesso tra le persone dello stesso gruppo (20.000 volte, seme 20261102): p circa 0,11 (2016-21) e 0,03 (2021-26). Senza le 3 persone con meno presenze per sesso: 95,2 / 92,1 e 87,9 / 90,9.
   - Surroghe 2021-26: 10 ingressi e 10 uscite nei file di presenze; ds1914 ne nomina 2 e 4 (4 righe).
4. **La sorpresa** scelta per la pagina: presenti in aula ma non sempre al voto (86% di presenze, 63% di voti; divario da 15 a 41 punti secondo il gruppo), con minimo a metà mandato in entrambi i mandati.

## 2. Pulizia e metodo (`scripts/build.py`)
- Un file = una fotografia cumulata. Per il 2016-2018 i file annuali si sommano (per persona) in cumulati dall'inizio del mandato; il cumulo a dicembre 2018 (180 sedute, 1.537 votazioni) è <= a gennaio 2019 (188, 1.590): coerente (+8 sedute a gennaio 2019).
- Persona = nome normalizzato (senza accenti, apostrofi, note tra parentesi tipo "(dal 4/07/2022)" o "dall'8-11-2018)"). Refusi del Comune riconosciuti a mano e corretti: "Barberis Filipppo", "Celestino Pietro Girgio" (il Ministero scrive Giorgio). Note originali conservate in `nota_nel_nome` e `nota_nel_file`.
- Gruppo: come nel file, spazi ripuliti; si toglie "(dal ...)" dal nome (non è un altro gruppo). Nessun raggruppamento in schieramenti: nei file non c'è chi è maggioranza e chi opposizione.
- Percentuali scritte nei file 2016-21 = ricalcolate (0 differenze, tolleranza 0,01). Nessun valore mancante; presenze <= sedute e votazioni effettuate <= totali per tutte le righe; nessun nome ripetuto nello stesso mese.
- Incrementi annuali: differenza tra due mesi per persona, negativi posti a 0 (3 casi nella fonte: Sala 2020-06 -> 07 e 2021-04 -> 05, Giovanati 2023-12 -> 2024-01). Il primo mese di una persona = il suo cumulato.
- Totali per periodo del consiglio = differenze dei cumulati massimi: somma dei periodi = ultimo cumulato (381/4.866; 281/4.021).
- Sesso: Ministero dell'Interno (`amministratori/pulito/milano_amministratori.csv` e `milano_in_carica.csv`), corrispondenza per cognome e nome (esatta o per prefisso con unico sesso). Trovato per 115 persone su 116; manca Sacerdoti Michele (in carica dal 30/4/2026, non ancora nell'elenco del 24/8/2026): escluso dal confronto, non dedotto dal nome.
- Rispetto al gruppo: presenze attese = sedute x tasso del gruppo nel mese (sindaco escluso), differenza in punti sulle sedute.

## 3. Limiti dei dati (anche sulla pagina)
1. Presenza non è lavoro (commissioni, territorio, atti non sono nei file); assenze giustificate, missioni, congedi, malattie non distinguibili.
2. Il Comune non scrive cosa conti come "presenza" (appello iniziale? tutta la seduta?) né come "votazione effettuata" (sì/no/astensione? procedurali?). Quindi confronti tra persone e gruppi, non "ore in aula".
3. Totali cumulati; cifre annuali ricalcolate da noi; mancano alcuni mesi; ultimo mese maggio 2026 (il mandato non è concluso).
4. Errori nella fonte: 3 cumulati che scendono; refusi nei nomi; ds1914 incompleto (4 righe contro 10 ingressi e 10 uscite visibili nei file di presenze) e con date incoerenti (surrogazione di Marcora 6/4/2022 prima delle dimissioni di Feltri 22/6/2022; nei file di presenze Marcora compare da luglio 2022).
5. Persone con poche sedute (ingresso recente): percentuali instabili.
6. Il sindaco compare con gruppo vuoto nel 2016-21 e "SINDACO" nel 2021-26: categoria a parte.
7. Gruppi cambiano nome e composizione (20 persone hanno cambiato gruppo nel 2016-21, 12 nel 2021-26); le sedute contano nel gruppo del mese; i gruppi con poche sedute-persona non sono disegnati.
8. Con 20 donne e 37 uomini per mandato le differenze tra le medie sono piccole rispetto al caso (vedi test).
9. Altri incarichi pubblici dei consiglieri: non nei dati, non usati per spiegare le cifre.

## 4. Privacy
Consiglieri comunali = persone con ruolo pubblico, dati nel loro ruolo (nome, gruppo, presenze, votazioni, sesso dal Ministero) come nei file ufficiali. Nessun dato di nascita, residenza o altro. La pagina non attribuisce motivi alle assenze.

## 5. Possibili sviluppi
- Se il Comune (o il Consiglio) pubblicherà i voti per votazione o le delibere come dati aperti: maggioranza/opposizione, unanimità, votazioni divisive per argomento.
- Verbali delle sedute sul sito del Comune: non cercati né letti (non sono dati aperti).
- Collegare la tabella ai dati di candidati, preferenze e liste 2016 e 2021 (ds1617 ecc.).
