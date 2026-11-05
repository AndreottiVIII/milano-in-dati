# Stato delle fonti: metodo e limiti (5/11/2026)

Regola: se una fonte risponde e quanto e' aggiornato il dato sono due cose diverse.

## Come si fa
- `scripts/stato.py`, da lanciare a mano (`python -I -X utf8 stato.py --radice <cartella milano-in-dati>`, circa 2-3 minuti). Non resta in esecuzione, non e' pianificato.
- Legge i link di `docs/fonti/data/fonti.json` (senza modificarlo). Per ogni sito legge prima il robots.txt. Una richiesta GET per link, senza salvare le pagine, al massimo una ogni 2 secondi per sito, nome `milano-in-dati/1.0 (+repo)`, nessun reindirizzamento seguito.
- Esiti: risponde (2xx/3xx), non_risponde (nessuna risposta, errore, 404), rifiuta (401/403/406/429: non e' un sito morto, nessun tentativo di aggirare), non_controllato (robots.txt illeggibile o che vieta).
- robots.txt: 404 o altri 4xx (anche 403) = nessun divieto (RFC 9309); se poi il link e' rifiutato, esito "rifiuta". Se il robots.txt e' una pagina web invece di regole (siti del Ministero dell'Interno), non si insiste: non_controllato.
- Catalogo del Comune: il sito blocca le pagine web ai programmi (403), ma l'API CKAN risponde. I link `/dataset/...` si controllano con `package_show`; i codici brevi (ds634) si risolvono nel nome completo con `package_search name:dsNNN*`, a gruppi di 12 (poche richieste). Nessun link scritto nelle pagine aveva davvero il codice breve con 404: gli 11 link a dataset rispondono (le 2 home del portale sono rifiutate).
- Risultato: `docs/fonti/data/stato.json` (scritto solo da stato.py; pagina.py non lo tocca, quindi non si perde quando pagina.py viene rilanciato). La pagina lo unisce a fonti.json per indirizzo del link: un link nuovo risulta "da controllare" finche' non si rilancia stato.py. Un controllo parziale (`--limite`, `--solo-sito`) non sovrascrive stato.json.

## Dato aggiornato a
- Non inventato. Catalogo del Comune: `metadata_modified` (scheda) e, accanto, la data piu' recente dei file (`resources[].last_modified`). Attenzione: per 113 dataset su 155 la scheda porta 8/5/2026 (aggiornamento di massa del catalogo): non dice quando e' cambiato il dato. Conta di piu' la data dei file.
- Altre fonti: `scripts/periodi.json` (a mano, 23 righe pagina+editore), ricopiato da `<filone>/NOTE.md` solo dove indica l'ultimo periodo coperto. Dopo una modifica: `stato.py --solo-periodi` (senza richieste). Non ho usato i riepilogo.json delle pagine.
- "Scaricato da noi" viene da fonti.json: e' un'altra cosa.

## Limiti
- 189 righe fonte citano solo il nome del sito, senza indirizzo completo: non controllate.
- Un link che risponde 200 non garantisce che la pagina contenga ancora il dato; il programma non legge il contenuto.
- Esito di un giorno solo: errori transitori (timeout, connessione) possono sparire al controllo successivo. TomTom: "certificato non valido" visto dal programma (puo' dipendere dall'archivio certificati di Python su questo PC), non verificato con altri strumenti.
- ds47 (codice nel testo di una pagina) non e' stato trovato nel catalogo; un codice corrisponde a piu' dataset e non e' collegato.
- Ripresentare "dato aggiornato a" per ogni fonte e' stato fatto solo per 23 righe su ~155 con link.
