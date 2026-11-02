# Le carceri di Milano - note (fase 1 + pagina)

Scaricato il 2 novembre 2026. Pagina: `docs/carceri/index.html` (scritta a mano, legge `docs/carceri/data/riepilogo.json`). Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di carceri> [<percorso assoluto di milano-in-dati>]`.

## 1. Fonti (tutte giustizia.it, Ministero della giustizia)
- **Capienze e presenze per istituto**, serie mensile "Detenuti italiani e stranieri presenti e capienze per istituto": 94 pagine HTML (gen 2019 - set 2026; il 31/12/2021 ha due pagine uguali). Colonne: regione, (sigla provincia fino a set 2025), istituto, tipo, capienza regolamentare, presenti, di cui donne, di cui stranieri. Nessun CSV: la tabella e' nella pagina (`raw/mensili/`). Elenco: `statistiche?selectedNode=0_2_7&all=true`.
- **"Detenuti presenti - aggiornamento al ..."**: 93 pagine mensili, tabelle per regione: capienza e presenti, e **posizione giuridica** (in attesa di primo giudizio, condannati non definitivi, definitivi...), anche per stranieri. Solo per regione, mai per istituto.
- **Serie storiche nazionali** (`raw/serie/`): posizione giuridica 2008-2025; eventi critici 1992-2025 (suicidi e decessi per cause naturali, solo totale nazionale); presenti italiani/stranieri 1991-2026; stranieri per area 2007-2025.
- **Schede degli istituti** (`dettaglio_scheda.page?s=...`, `raw/schede/`): San Vittore maschile MII158895, San Vittore femminile MII178501, Bollate MII172344, Opera MII179237. Posti regolamentari, non disponibili, detenuti (1/11/2026), personale (30/9/2026: polizia penitenziaria, amministrativi, educatori, effettivi/previsti), stanze. Solo situazione di oggi.
- **IPM (minorenni)**: PDF semestrali/annuali 2020-2025 del Dipartimento per la giustizia minorile e di comunita' (`raw/ipm/`), testo in `raw/ipm_txt/` (pdftotext). Per Milano: ingressi, uscite, presenti a fine periodo, presenza media giornaliera. Nessuna capienza.
- Non usati: Antigone, Garante nazionale (nessun numero ripreso).

## 2. Termini d'uso
`note_legali` (agg. 2/12/2025): uso e riproduzione consentiti per finalita' non commerciali, con indicazione della fonte e garantendo l'integrita' degli elementi riprodotti; vietato ledere immagine/onore delle persone citate. Nessuna licenza aperta (CC BY) dichiarata. robots.txt: `Disallow:` vuoto. Scaricato con User-Agent dichiarato, 1,5 s tra richieste, ritentativi su 504 (il server dà 504 a tratti). Nessun login, nessun aggiramento.

## 3. Numeri principali (30/9/2026 salvo diversa data)
- Italia: 66.063 presenti / 51.319 posti = 128,7 ogni 100 (119 a gen 2019). 131 istituti su 172 (>=50 posti, no ICAM/IP) sopra 100; mediana 132.
- San Vittore: 1.219 / 748 = 163 (122 a gen 2019, massimo della serie); scheda 1/11: posti 702+46 (femminile) = 748, **218 non disponibili**, detenuti 1.113+100 = 1.213 -> 229 ogni 100 posti disponibili. Polizia 569/858 in organico.
- Bollate: 1.612 / 1.267 = 127 (101 a gen 2019, picco 130 a gen 2026). Donne 136 -> 202.
- Opera: 1.359 / 918 = 148 (146 a gen 2019). Stranieri 25,6% -> 34,4%.
- Lombardia: 153,5 ogni 100 (137 nel 2019). Senza condanna definitiva 24,8% (31,2% nel 2019); Italia 24,3% (32,6%).
- IPM Milano, presenza media giornaliera: 33,4 (2020) -> 71,8 (2025); Italia 587,7 (2025).
- Suicidi Italia 2025: 74 (11,8 ogni 10.000 presenti in media).
- Dic 2025: San Vittore 1.199 -> 914, Bollate 1.472 -> 1.650 in un mese (il dato non dice perche').

## 4. Controlli e difetti trovati (dettagli in `pulito/controlli.txt`)
1. Per la Lombardia la somma degli istituti = riga regionale in tutti i 93 mesi e per tutte e 5 le misure (istituti, posti, presenti, donne, stranieri). Per il Lazio 9 differenze in 8 mesi (un istituto in piu'/in meno e qualche posto); non toccano Milano.
2. San Vittore: capienza in tabella (748) = scheda maschile 702 + femminile 46 (assert in `pagina.py`). Il nome cambia ("FRANCESCO DI CATALDO" / "F. DI CATALDO"): riconosciuto da parola chiave.
3. Da ottobre 2025 la tabella perde la colonna sigla provincia e i nomi finiscono con " -".
4. Caselle vuote (donne, presenti di istituti chiusi) = 0.
5. Refusi: "febbreio" nella data; aprile 2022, tabella regionale, Abruzzo "in attesa" = "\" -> ricavato dal totale (181).
6. Totale Italia della tabella per posizione giuridica = somma degli istituti in tutti i 93 mesi.
7. PDF IPM: celle dei semestri vuote/spostate (parser automatico inaffidabile): si usa solo la presenza media annuale, riga letta a mano e verificata dal programma sulla pagina indicata (`analisi.py`).

## 5. Cosa non c'e'
- Posizione giuridica, eta', reati per istituto: non pubblicati (solo regione/Italia).
- Morti/suicidi per istituto: nessun dato ufficiale aperto trovato (solo totale nazionale).
- Capienza dell'IPM Beccaria: non nei PDF.
- Personale: solo oggi, solo 4 schede (servirebbero 189 schede per il confronto nazionale; i codici scheda non sono elencati in modo semplice).
- Garante nazionale/Antigone: non cercati a fondo (nessun numero ripreso).
