# Le vie che hanno cambiato nome (bozza)

Fonte: Comune di Milano, ds2914 "Vie di Milano e corrispondenza toponomastica nelle mappe storiche dal 1884", CC BY 4.0
(pagina del dataset, controllata il 6/11/2026; ultima modifica del dataset 8/5/2026). Dataset del progetto LetMi
(letteratura e turismo a Milano): censisce le vie "di rilevanza per LetMi", non tutte le vie. Mappe: 1884, 1910, 1930,
1946, 1956, 1965, 1972, 1990, 2006, 2012, più il nome attuale. Nomi letti a mano dalle mappe georeferenziate del GIS del Comune.

## Programmi (in scripts/)
- `scarica.py`: scarica CSV, JSON, GeoJSON e i metadati in `raw/` (User-Agent `milano-in-dati/1.0`).
- `pulisci.py`: pulisce, applica la regola sotto, scrive `pulito/vie.json` e `pulito/riepilogo.json`.
- `genera_html.py`: scrive `bozze-grafici/vie-storiche.html` (dati dentro il file). `foto.py`: immagine a 375 px in `bozze-grafici/screen/`.

## Dati
- 37 righe, 36 vie: le righe 22 (Piazzale Francesco Baracca) e 31 (Piazzale Baracca) hanno stesse coordinate e stessa storia; si conta una sola volta.
- Caselle "MAPPA NON LEGGIBILE" (11 dopo l'eliminazione del doppione) e "NON ESISTENTE" (7): non sono nomi, si saltano. Il confronto va tra le due mappe leggibili più vicine; se in mezzo c'era una mappa illeggibile, il cambio è "con salto" e non si può assegnare a un solo periodo.
- "NON ESISTENTE" seguito da un nome = la via nasce (Corso Matteotti, Corso Europa): non è un cambio.

## Regola: cambio vero o cambio di grafia
Ogni casella diventa un elenco di nomi (si divide su virgola, "/" e "incrocio tra A e B"). Ogni nome diventa un insieme di parole dopo: minuscole, senza accenti e punteggiatura; tolti via/viale/corso/piazza/piazzale/largo/vicolo/strada, articoli e preposizioni (di, del, della, delle...), iniziali isolate (F., G.); S.=San, P.=Porta; XXIV/Ventiquattro=24, XXV/Venticinque=25; Giovine=Giovane; Ospitale=Ospedale; testo fra parentesi ignorato.
Due nomi sono lo stesso nome se hanno le stesse parole, o se uno è contenuto nell'altro (nome di battesimo in più) e le parole in più non sono "naviglio, cerchia, porta, cascina, ponte, quartiere, cimitero, bastioni".
Confronto tra due caselle: **uguale** (stessi nomi) = grafia; **parziale** (almeno un nome in comune, ma si aggiunge/toglie un nome) = segnato, non contato; **cambio** (nessun nome in comune) = contato.
Esempi grafia: "Piazza delle Cinque Giornate" / "Piazza Cinque Giornate"; "Via Turati" / "Via Filippo Turati"; "Viale Col di Lana" / "Via Col Lana"; "Piazzale 24 Maggio" / "Piazza XXIV Maggio" / "Piazza Ventiquattro Maggio"; "Piazza Giovane Italia" / "Giovine"; "Via dell'Ospitale" / "Via Ospedale".
Esempi cambio: "Viale di Porta Nuova" -> "Viale Monte Grappa"; "Via Principe Umberto" -> "Via Albania" -> "Via Filippo Turati"; "Naviglio di via San Damiano" -> "Via San Damiano" (naviglio -> via: contato come cambio).
Esempio parziale: "Piazza Fiume" -> "Piazza Carnaro, Piazza G. D'Annunzio, Piazza Fiume" (Fiume resta, si aggiungono due nomi).
Scelte discutibili: "Ospitale=Ospedale" e "Giovine=Giovane" sono mie (varianti della stessa parola); Via Melchiorre Gioia nel 1930/1946: la casella dice "Ponte delle Gabelle, Naviglio Martesana (Via Melchiorre Gioia)": il nome fra parentesi è ignorato, quindi il cambio cade tra 1946 e 1956; se la parentesi fosse il nome sulla mappa, cadrebbe tra 1910 e 1930.

## Risultati (36 vie)
- 33 vie cambiano nome almeno una volta, 3 no (Via Verziere, Corso Matteotti e Corso Europa, nate dopo il 1884). 26 una volta, 7 due volte, nessuna di più. 40 cambi in tutto.
- Per periodo (tra mappe consecutive): 1884-1910: 5; **1910-1930: 19**; 1930-1946: 5; 1946-1956: 4; 1956-1965: 1; 1965-1972: 1; 1972-1990: 2; 1990-2006 e 2006-2012: 0. Altri 3 cambi con mappa illeggibile in mezzo (2 tra 1884 e 1930, 1 tra 1884 e 1946).
- L'ipotesi "molti cambi tra 1930 e 1946" non regge: sono 5 su 40; la concentrazione è tra 1910 e 1930 (quasi metà). Intervalli di durata diversa (20 e 16 anni).
- 6 viali che nel 1884 erano "Viale di Porta ..." / "Viale di P. Umberto" cambiano tutti nome nella mappa del 1930.
- Donne (aggancio a docs/vie): tra i nomi attuali solo Piazzale Principessa Clotilde (compare dal 1930); nessun nome di donna riconosciuto nel 1884 e 1910 (lettura a occhio: "Via Vittoria" 1884 non è chiaro). La classificazione di docs/vie dà "uomo" a Piazza Giovine Italia: errore (è un movimento), non usata.

## Non controllato
- La correttezza delle trascrizioni dei nomi dalle mappe (se ne fida il dataset). Nessun controllo sulle mappe originali.
- Nessuna spiegazione storica dei cambi: i dati non la danno e la bozza non la dà.
- Le coordinate non sono usate (niente mappa nella bozza).
- Verificato solo con Edge a 375 px, non su altri browser.
