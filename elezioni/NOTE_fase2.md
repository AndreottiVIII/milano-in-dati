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
