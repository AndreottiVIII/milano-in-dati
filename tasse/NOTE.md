# Le tasse a Milano (pagina `docs/tasse/`)

Costruita il 3 novembre 2026. Programmi in `scripts/` (Python 3.12, `python -I -X utf8 <script> <percorsi assoluti>`), dati scaricati in `raw/` (non fidati, mai eseguiti), tabelle intermedie in `pulito/`, controlli in `out/controlli.txt`, dati della pagina in `docs/tasse/data/`. Milano sempre al centro: le altre sei città (Roma, Torino, Napoli, Bologna, Firenze, Genova) solo come confronto.

Ordine di lancio:

1. `scarica_ministero.py <raw/ministero_interno>`: certificati al rendiconto del Ministero dell'Interno, 7 città x 2016-2018 x quadri 01, 02, 09, 18, 20 (105 pagine, pausa 2 s).
2. `cerca_siope_regioni.py` + `scarica_siope.py <raw/siope> <elenco>`: SIOPE entrate (BDAP) per regione e anno, letto in streaming e filtrato sulle 7 città (il file intero non si salva). Il server a volte risponde con 7 righe invece del file: lo script ritenta (fino a 6 volte, 20 s). Lombardia 2015-2025, altre 6 regioni 2018-2025. Lombardia 2014 e 2026 non scaricate (2014 vecchio schema e non serve; 2026 incompleto).
3. `estrai_ministero.py`, `estrai_siope.py`, `estrai_mef_pop.py <tasse> <redditi>`: tabelle in `pulito/`.
4. `build.py <tasse> <milano-in-dati>`: scrive `docs/tasse/data/` e `out/controlli.txt` (63 controlli, 0 errori al momento della consegna; esce con codice 1 se uno fallisce).

## Cosa c'è e da dove

| Parte | Dato | Fonte (file, campo) | Anni | Licenza |
|---|---|---|---|---|
| 1 | Accertato IMU, TASI, TARI, addizionale, soggiorno, recupero evasione | `docs/bilancio-comune/data/capitoli_usati.csv` (una sola edizione per anno), controllato contro `tributi_principali.csv` | 2015-2025 | CC BY 4.0 (Comune) |
| 1 | Entrate correnti e tributi (per il "peso") | `docs/bilancio-comune/data/entrate_per_tipo.csv` | 2015-2025 | idem |
| 1 | Incassi di cassa per città | BDAP SIOPE "Movimenti cumulati mensili di Entrata", valore di dicembre; codici E1010106 (IMU), E1010116 (addizionale), E1010141 (soggiorno), E1010151/E1010161 (rifiuti), ecc. | 2019-2025 (Milano 2015-2025) | CC BY |
| 2 | Aliquote IMU 2026 | Dipartimento Finanze, prospetto n. 13159 (delibera CC n. 110 del 18/12/2025), `raw/finanze/`; informativa IMU 2026 del Comune `raw/comune_milano/` | 2026 | pubblico, citato |
| 2 | Addizionale (0,8%, soglia 23.000), TARI (esempi), soggiorno (tariffe 2026) | **fonti indirette**: pagine di assistenza del Comune lette tramite motore di ricerca, Ecodallecittà, MilanoFree, Assolombarda, AGI, Greenme | 2026 | citati |
| 3 | IRPEF netta, addizionale dovuta, classi di reddito | MEF, redditi per comune (`redditi/pulito/mef_comuni_2000_2024.csv`), campi `imposta_netta_eur`, `addiz_com_eur`, `cl*_n/eur` | a.i. 2000-2024 | CC BY 3.0 |
| 4 | Accertato / riscosso / residui per tributo | Pareri dell'organo di revisione sui rendiconti 2024 e 2025 del Comune (`raw/comune_milano/*.pdf`), tabelle "principali entrate correnti", "anzianità dei residui", "recupero evasione" | 2024, 2025 | documenti del Comune, solo numeri |
| 4 | Residui e riscossioni di 7 città | Ministero dell'Interno, certificati al rendiconto, quadro 2 (imposte, tasse e proventi assimilati), quadro 9, quadro 18, quadro 1 (abitanti) | 2016-2018 | non dichiarata, solo numeri aggregati |

Abitanti: sempre **residenti ISTAT al 1° gennaio** (ricostruzione 2002-2019 e POSAS 2020-2026, da `redditi/raw/istat_pop/`), uguale per tutte le città; per i conti dell'anno t si prende il 1/1/t, per l'IRPEF dell'anno d'imposta t il 1/1/(t+1). Confrontato con la tabella del cartella redditi: 125 righe uguali, 0 differenze. Non coincide con gli abitanti della pagina del bilancio (stime del Comune), dichiarato nei limiti. Prezzi: FOI nazionale già pronto (`bilancio-comune/pulito/indice_prezzi_annuo_FOI_da_strand12.csv`).

## Numeri principali

- Quattro tributi accertati 2025: **1.445 M** (IMU 777, TARI 304, addizionale 250, soggiorno 114), 1.058 euro per abitante, 37,4% delle entrate correnti, 92,4% delle entrate tributarie.
- Imposta di soggiorno: 59,1 M (2019), 11,0 (2020), 114,0 (2025). Cause non indagate.
- **Residui attivi delle entrate tributarie** a fine anno: 643 M (2016), 855 (2017), 745 (2018), 725 (2024), **715 (2025)**; nel 2025 340,5 M sono dell'anno e 374,5 degli anni prima. Incassato nell'anno su accertato, tutto il titolo 1: 79% (2024), 78% (2025).
- Per tributo, incassato nell'anno 2025: IMU 99,8%, soggiorno 81%, TARI 72%, addizionale 37%, recupero evasione 34%. Addizionale nei conti 2016-2018: 33-40% nell'anno, il resto dai residui.
- Recupero evasione: accertato 90,1 M (2024) e 112,6 (2025), riscosso nell'anno 23,4 (26%) e 37,8 (34%); residui totali a fine 2025 264,5 M, fondo crediti accantonato 65,46%. Crediti stralciati dai conti: 310,9 M (residui 2017-2018, nel 2024) e 141,3 M (residui 2019, nel 2025), senza dire di quali entrate.
- IRPEF 2024 Milano: **10,56 miliardi** netti, 10.036 euro per contribuente (Roma 6.862, Bologna 6.589, Firenze 6.192, Torino 5.863, Genova 5.267, Napoli 4.742), 7.735 per abitante; addizionale dovuta 275,9 M = 2,6% dell'IRPEF (Roma 3,6%, Torino 4,0%, Napoli 4,3%, Genova 4,6%, Bologna 3,3%, Firenze 0,8%). Aliquota media effettiva dell'addizionale 0,72% (l'aliquota è 0,8% con esenzione fino a 23.000). Oltre 120.000 euro: 4,9% dei contribuenti, 33,0% del reddito.
- Incassi di cassa per abitante all'anno, media 2019-2025: Milano 965, Roma 904, Firenze 861, Bologna 845, Genova 766, Torino 712, Napoli 504.
- Ministero 2016-2018, incassato nell'anno su accertato (imposte e tasse, media dei tre anni): Genova 92%, Firenze 86%, Bologna 81%, Torino 75%, Milano 73%, Roma 66%, Napoli 55%. Residui a fine 2018 per abitante: Milano 534, Roma 937, Torino 554, Napoli 1.239, Bologna 282, Firenze 239, Genova 246. Da leggere con cautela (vedi sotto).

## Scelte

- **Città**: le stesse sei della pagina sui rifiuti (Roma, Torino, Napoli, Bologna, Firenze, Genova).
- **Anni**: parte 1 2015-2025 (gli anni dei consuntivi del Comune); confronto di cassa media 2019-2025 (sette anni, per non farsi ingannare da un anno solo: l'IMU di Milano è 565 M nel 2024 e 821 nel 2025 per ritardi di versamento di fine anno); IRPEF 2000-2024; arretrati 2016-2018 (Ministero) e 2024-2025 (revisori).
- **Euro**: grafici della parte 1 di default in euro 2025 con FOI nazionale; tabelle e parte 4 in euro di ogni anno.
- **Esempi**: tre profili, ipotesi scritte. Aliquota IMU 2026 dal prospetto ufficiale; rendita ipotizzata 1.000 euro (base 168.000 = 1.000 x 1,05 x 160); addizionale 0,8% con soglia 23.000 (soglia, non franchigia); TARI solo con gli esempi pubblicati dal Comune (293 euro tre persone 106 mq; 113 euro persona sola sotto i 30 anni 52 mq) perché la tabella ufficiale non è stata trovata: non si stima. Imposta di soggiorno: tabella, nessun esempio (non la pagano i milanesi).
- Non è stata fatta nessuna stima di evasione.

## Controlli automatici (`out/controlli.txt`)

Una sola edizione per anno; totali uguali al bilancio già pubblicato (5 serie, differenza massima 5.000 euro); addizionale e soggiorno uguali al Ministero 2016-2018 (a 20.000 euro); IMU+ICI+TASI e rifiuti con recupero entro 1% e 2% dal Ministero; SIOPE = riscossioni del Ministero (competenza + residui) 2018 per tutte e 7 le città (scarto massimo 0,25%) e Milano 2016; residui finali = iniziali - riscossi + riaccertato + accertato - riscosso (tutte le righe del quadro 2); accertato dei rendiconti 2024-2025 = bilancio già pubblicato; somme delle tabelle dei revisori (accertato - incassato = residuo, residui iniziali - riscossi - eliminati = rimasti, fasce di anzianità = totale); MEF Milano = dataset del Comune ds312 (differenza 0 euro); somma delle classi = reddito complessivo MEF; nessun grezzo in `docs/tasse/`.

## Problemi dei dati (da non dimenticare)

1. Il server BDAP risponde a volte con 129 byte (7 righe) invece del file da 200 MB: serve il tentativo ripetuto. L'elenco dei dataset si trova solo con la ricerca di una parola alla volta (`q=Lazio`), non con frasi.
2. **SIOPE, cassa a fine anno**: l'IMU di Milano oscilla (2017 505 M, 2018 828, 2024 565, 2025 821) per ritardi di accredito; nel 2017 ci sono 270 M in "altre imposte" per codifica. Usare solo medie pluriennali o il totale.
3. **Codifiche diverse tra città**: Roma registra la TARI come TARES e non ha una riga di imposta di soggiorno (le "altre imposte" sono 181-298 M, probabilmente c'è il contributo di soggiorno: non verificato). Nel confronto si somma tutto tranne IMU/TASI e addizionale.
4. **Ministero quadro 9, nel 2016**: la TARI sta nella riga "Altre imposte, tasse e proventi n.a.c." (318,6 M) e la TASI si chiama "Tassa sui servizi comunali". Le righe cambiano nome anche tra 2017 e 2018 (TARES/TARSU "esercizi precedenti"). Funzione `q9grp` in `build.py`.
5. **Tributi accertati per cassa** (principio contabile 3.7): per alcune città non esistono residui, e il fondo crediti (Q18) va da 0 a 85%. Il confronto degli arretrati fra città non è alla pari: nella pagina è un grafico piccolo con avviso grande.
6. **IMU**: nel Ministero è "al netto della quota per il fondo di solidarietà comunale" e per Milano torna col bilancio; per le altre città non è stato verificato.
7. Il bilancio di Milano: l'IMU "ordinaria" + il recupero IMU = IMU del Ministero (718,5 M nel 2018). `tributi_principali.csv` "IMU e TASI" è solo l'ordinaria.
8. Addizionale a bilancio: cifre tonde (195, 250 milioni) e diverse dall'addizionale dovuta del MEF (276 M per il 2024 contro 240 accertati nel 2024 e 250 nel 2025). Non spiegato.
9. Firenze: addizionale effettiva 0,17-0,18%, dato vero (MEF) non un errore.
10. Le tariffe di soggiorno da aprile 2026 (delibera 144 del 12/2/2026) hanno una sola fonte (Greenme).
11. Il titolo 1 dei revisori include fondi perequativi (4 M nel 2025, 23 M nel 2024): differenza trascurabile con "imposte, tasse e proventi" del Ministero 2018.

## Fonti che hanno rifiutato

- `comune.milano.it` (pagine di servizio: IMU, TARI, addizionale, tributi) e `servizicrm.comune.milano.it`, `palazzorealemilano.it`, `milanotoday.it`: **403 Forbidden** a curl con User-Agent `milano-in-dati/1.0` e a WebFetch. Non aggirato. Fonte cambiata: documenti PDF dello stesso sito (percorso `/documents/`, che risponde) e fonti indirette.
- Ministero dell'Interno: nessun rifiuto, ma "dati assenti" per i certificati dal 2019 (provati 2019, 2021, 2023 per Milano).
- `openbdap.rgs.mef.gov.it` (interfaccia web): non ha mostrato un archivio da scaricare. `bdap-opendata` risponde, ma i dataset di rendiconto armonizzato non sono nel catalogo trovato.
- OpenBilanci: scartato (licenza CC BY-NC-SA).

## Non fatto / aperto

- Gli arretrati per tributo 2019-2023 e le riscossioni per tributo 2019-2023 (solo cassa); servirebbero i pareri dei revisori degli anni 2019-2023 (stessi documenti del Comune, PDF).
- La delibera TARI con la tabella ufficiale 2025/2026 e le delibere sull'addizionale: non lette (sito che rifiuta). Sul portale del Dipartimento delle Finanze esistono i prospetti TARI e addizionale, la chiave del file non si trova senza il motore di ricerca interno.
- IRPEF per fascia di reddito: nei dati comunali non c'è. Nei file regionali sì (Lombardia), ma non è Milano.
- Compartecipazione del Comune al recupero di imposte dello Stato: una sola cifra da stampa (centinaia di migliaia di euro), non inserita nei conti.
- Il menu e l'elenco temi (`docs/menu.js`, `docs/temi.json`, `docs/elenco/`) non sono stati toccati: la pagina non compare ancora nel menu.
