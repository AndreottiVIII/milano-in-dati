# Reati in città (sotto il comune) - note

Fatto il 2 novembre 2026. Pagina: `docs/reati-citta/index.html` (costruita da `scripts/pagina.py`). Cartella: `raw/` (file non fidati, mai eseguiti), `pulito/`, `scripts/`, `out/riepilogo.txt` (numeri citati nella pagina).

## Verdetto
**Sotto il comune non esiste nessun dato aperto sui reati** (né per municipio, né per NIL, stazione, via, ora). Ho costruito la pagina perché esistono tre serie ufficiali aperte che `docs/reati/` non ha:
1. **Istat, altri delitti per mese** (`73_1187_DF_DCCV_ALTRIDELPS_2`, CC BY 4.0): maltrattamenti contro familiari e conviventi (CP572), atti persecutori (CP612BIS), diffusione illecita di immagini (CP612TER). Provincia di Milano (`ITC45`) e Italia, annuale 2018-2024 (2019-2024 per CP612TER), mensile dal 2019. Era il buco dichiarato in `reati/NOTE.md` (punto 7 dei limiti).
2. **Istat, percezione della sicurezza nei 27 grandi comuni** (`DF_DCSS_BEST_PPC_1_GC` famiglie/rischio criminalita' nella zona; `_6_GC` persone 14+/sicurezza camminando al buio), 2022-2024, comune di Milano compreso.
3. **Comune di Milano, ds516, interventi del 118 per "Aggressioni ed eventi violenti"**, 2004-2015 (CC BY), serie chiusa.

## Numeri chiave (da `out/riepilogo.txt`)
- Totale delitti 2024: provincia di Milano 6.989 per 100.000 (226.860), Italia 4.070 (2.399.347): rapporto 1,72.
- Maltrattamenti 2024: Milano 1.541 (47,5 per 100.000), Italia 28.896 (49,0). Dal 2018 tasso +25,2% Milano, +68,1% Italia. Quota Milano su Italia 5,3% (popolazione implicita 5,5%).
- Stalking 2024: 987 (30,4) contro 36,1. Immagini 2024: 111 (3,4) contro 2,6; 26 nel 2019.
- Mesi 2019-2024: quote tra 7,2% e 8,9% (CP572) e tra 7,0% e 9,8% (CP612BIS): nessuna stagione netta. Somma dei 12 mesi = totale annuo in 34 casi su 34.
- Percezione, Milano: camminare al buio poco/per niente sicuri 35,4% (2022, 5ª su 26), 41,7% (2023, 1ª su 27), 43,2% (2024, 1ª su 27; Prato 43,1%; media semplice 34,2%). Rischio di criminalita' nella zona molto/abbastanza 38,0% / 44,1% / 44,4% (2ª su 27 nel 2023 e 2024; Napoli 62,4%).
- 118: aggressioni (verde+giallo+rosso) 4.684 (2004), 3.328 (2007, minimo; cala anche il totale), 4.645 (2015); quota 2,7-3,1% di tutti gli interventi.

## Fonti cercate senza esito (dettaglio sulla pagina)
- **CKAN Comune** (25 parole chiave il 2/11, oltre alle 20 del 1/11): nessun dato di polizia locale per municipio; solo ds564 (comune intero), ds1302 (indirizzi comandi), ds175-179 (incidenti stradali per zona di decentramento: tema diverso, non toccato), ds503 (edifici degradati), ds516 (usato), ds645 (Osservatorio Milano, percezione di sicurezza 2017 solo confronto tra citta', fermo al 2018, superato dai dati Istat 2022-2024; non usato).
- **Regione Lombardia** (`dati.lombardia.it`, API cataloghi Socrata): nessun reato; solo incidenti, indirizzi polizie locali, tabelle di altri comuni.
- **Polizia Locale Milano**: nessun rapporto ufficiale trovato; cifre solo in stampa (Italpress, discorso del sindaco): non usate.
- **ATM** (Rendicontazione di sostenibilita' 2025, Informazioni sociali, PDF, `raw/atm/`, pagine 244 e 278 del documento): le aggressioni al personale sono citate come rischio e come causa dell'aumento degli infortuni, nessun numero.
- **Non letti**: Relazione al Parlamento (Viminale), Relazione annuale DCSA (sequestri di droga per citta' metropolitane, PDF), rapporto PoliS-Lombardia/Cattolica "Sicurezza in Lombardia" (gen. 2025). Tutti e tre, per quanto so, sono provinciali: non scendono sotto il comune.
- **ISTAT BES territoriale Sicurezza** (`DF_BES_TERRIT_7`, scaricato, esplorato): province, stesse voci di `reati/`; non usato.

## Scelte e cose da sapere
- Denominatore del tasso: popolazione implicita gia' costruita in `reati/` (denunce totali / tasso pubblicato). ITC45 da `province_totale_anno.csv`, Italia da `delitti_tipo_territorio_anno.csv`.
- ISTAT indica per la tabella "altri delitti" il periodo del commesso delitto `YRDUR` ("durante l'anno di riferimento"): non letta la nota metodologica completa; scritto nei limiti.
- CP612TER (art. 612-ter c.p., Codice Rosso, legge 69/2019): il fatto che sia del 2019 e' dalla mia conoscenza, non verificato in questa ricerca; la pagina lo dice.
- Rimini manca nel 2022 nelle tabelle di percezione (26 comuni invece di 27).
- Il nome dell'indagine campionaria della percezione non e' nel file scaricato (probabilmente "Aspetti della vita quotidiana", NON verificato: non scritto nella pagina).
- ds516: file in Windows-1252; il codice bianco c'e' solo dal 2012 (escluso dalla somma); il totale per colore non e' confrontabile nel tempo (rossi 194 nel 2006, 85 nel 2007).
- Scaricamento: richieste ISTAT con User-Agent dichiarato `milano-in-dati-research/1.0`, pausa di 20 s; 5 richieste ISTAT (tre tabelle di dati, BES, struttura della percezione; la piu' grande, altridelps2, 26 MB). Nessun account, nessuna registrazione, nessun git.

## Se si vuole andare sotto il comune
Solo con una richiesta di accesso civico generalizzato (D.Lgs. 33/2013) al Comune (Polizia Locale: interventi e verbali per municipio) o alla Questura. Non fatta: e' una decisione di Davide.
