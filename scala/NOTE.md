# La Scala, spettacoli dal 1778 a oggi - note della fase 1 (scaricamento)
Aggiornato il 29/10/2026. Cartella: `scala\`. Fase 1 = solo scaricare e capire le fonti; nessuna analisi, nessuna pagina del sito.

## Riassunto
- **1778-1881 (e 1862): fatto.** Le cronologie di Cambiasi (1872, 1881) e di Romani (1862) sono scaricate, libere, con testo OCR già pronto.
- **1943-oggi: FERMATO.** L'archivio storico della Scala è nella parte del sito che `robots.txt` vieta ai programmi. Non ho raccolto nulla.
- **1906-1943: buco.** Solo riempimento parziale da Wikidata e Wikipedia. Pista nuova: Marangoni-Vanbianchi copre 1906-1920.
- **Cambiasi 5a edizione (1778-1906): non scaricabile dall'Italia** (HathiTrust la apre solo agli USA).

## 1. Cambiasi e le altre cronologie dell'Ottocento
Tutto da Internet Archive (`https://archive.org/download/<id>/<file>`), scaricato il 29/10/2026 con `scripts\scarica_cambiasi.py`. Nessun account, nessun clic di licenza.

| Cartella in `raw\` | Che cos'è | File (MB) |
|---|---|---|
| `cambiasi\teatroallascala100camb` | **Cambiasi, "Teatro alla Scala 1778-1881"** (Ricordi 1881), copia Getty/Internet Archive, 168 pagine, scansione 300 dpi. **È la copia migliore.** | pdf 12,5; testo OCR `_djvu.txt` 0,35; **hOCR con riquadri delle parole** 11,1; immagini JP2 (zip) 88,8 |
| `cambiasi\teatroallascala00cambgoog` | Stessa edizione 1881, copia Google, più scadente | pdf 5,1; testo 0,34 |
| `cambiasi\bub_gb_e864LY_9qOUC` | **Cambiasi, "Rappresentazioni date nei reali teatri di Milano 1778-1872"** (Ricordi 1872) | pdf 7,6; testo 0,27 |
| `romani\teatroallascalac00romauoft` | **Luigi Romani, "Teatro alla Scala. Cronologia di tutti gli spettacoli" (1862)**, copia Toronto, 224 pagine. Seconda cronologia indipendente 1778-1862: serve per controllare Cambiasi | pdf 17,2; testo 0,47 |
| `cambiasi\pdf24_merged-16` | **Marangoni e Vanbianchi, "La Scala. Studi e ricerche, note storiche e statistiche 1906-1920"** (1922). **Solo il testo OCR** (il pdf pesa 520 MB, non scaricato) | testo 1,35 |

**Cosa copre e cosa no.**
- Il volume 1881 non è un elenco di tutte le sere: è una *serie delle opere in musica* e una *serie dei balli*, per stagione (anno, stagione, mese, giorno, titolo, maestro, poeta, tipo, esecutori principali, esito). In una stagione ogni opera compare una volta (la riga "id." ripete la stagione), non con tutte le repliche. Vale lo stesso per il 1872.
- La tabella delle opere occupa **due pagine affiancate**: a sinistra anno/stagione/mese/giorno/titolo/maestro (PDF pagina 25, hOCR pagina 24), a destra poeta/tipo/esecutori/esito (pagina seguente). Per fare una riga sola bisogna riunire le due metà in ordine.
- La "Spiegazione delle abbreviature" (pag. 400 originale) dice: asterisco = opera scritta apposta per la Scala; esiti = ottimo, buonissimo, buono, mediocre, cattivo, pessimo; C. carnevale, Q. quaresima, P. primavera, E. estate, A. autunno, Aw. avvento. Le note a piè di pagina `(1)`, `(2)` sono mescolate nei campi data.
- Romani (1862) è invece prosa per stagione: "1781 CARNEVALE / Antigono. D. s. Musica ..." con attori e balli, quindi più difficile da tabulare ma ricco di nomi.
- Marangoni-Vanbianchi riporta i cartelloni delle stagioni 1906-1920 (titoli, autori, elenco artistico) in testo continuo. **È la prima pista concreta per il buco 1906-1943, ma solo fino al 1920.**

**Prova OCR (8 pagine).** Tesseract **non è installato** (`tesseract: command not found`, nessuna cartella Program Files); non l'ho installato. Ho fatto così:
1. Il testo e le coordinate di Internet Archive (motore ABBYY FineReader) esistono già per tutto il libro: per l'1881 non serve rifare l'OCR. L'hOCR dà ogni parola con il suo riquadro (pagina 24: 513 parole). Raggruppando per altezza si ricostruiscono bene le righe: x circa 680 anno, 840 stagione, 1090 mese, 1250 giorno, 1400 titolo, 2280 maestro. Difetti visti: nomi dei maestri storpiati ("Sftlieri" = Salieri, "Mjsliweczek" = Myslivecek, "Yaleutini" = Valentini), "id." a volte perso, accenti sporchi. Serve una lista di nomi (Wikidata) per correggere.
2. Ho provato anche il **motore OCR integrato di Windows 11 (it-IT, senza installare nulla)** su 8 pagine (`test_layout\c1881_p*_winocr.txt` e immagini `.png`). Funziona ma peggio di ABBYY: legge colonna per colonna, sbaglia sulle colonne strette ("Rub:nelli", "Baldueci"). Va bene come ripiego, e per le foto di Gatti (script al punto 4).
Opzioni se serve di meglio: installare Tesseract con i dati `ita` (decisione di Davide), oppure usare l'hOCR già pronto per Cambiasi.

**Cambiasi 5a edizione 1778-1906** (Ricordi 1906, "completamente rifusa", 350 illustrazioni): è su HathiTrust (record 100371822, copia Harvard `hvd.32044082278698`, codice diritti `pdus` = pubblico dominio solo negli USA). Dall'Italia la pagina risponde 403 e l'Online Books Page scrive "US access only". Non l'ho aggirato. Una copia Google esisterebbe (scheda della Biblioteca Nazionale di Israele) ma l'API di Google Books oggi ha la quota esaurita. **Da fare**: cercare la copia 1906 su Google Books con "scarica PDF", o chiedere a una biblioteca (Braidense, Biblioteca del Museo Teatrale alla Scala) o a qualcuno negli USA.

**Licenza.** Cambiasi e Romani sono morti da ben più di 70 anni: opere di pubblico dominio. Internet Archive segna `NOT_IN_COPYRIGHT` per Romani e per l'edizione Google 1881 e "Public Domain Mark 1.0" per il 1872. Le scansioni (Google, Getty, Toronto) chiedono in genere uso non commerciale e di non togliere le note di provenienza: **i pdf e le immagini non li ripubblicherei**; i *dati* estratti (titoli, date, nomi) sono fatti, citando la fonte. Marangoni-Vanbianchi: la licenza "CC BY-NC-ND" l'ha messa chi ha caricato il file (un privato), non gli autori, e non ho verificato le date di morte: **solo pista, nessuna ripubblicazione**. (Valutazione mia, non parere legale.)

## 2. Archivio storico della Scala dal 1943 - FERMATO
- `https://www.teatroallascala.org/robots.txt` (letto il 29/10/2026): `User-agent: *` ... `Disallow: /it/archivio` e `Disallow: /en/archive` (più `/api/`, `/web/`). L'archivio storico è proprio su `/it/archivio/archivio-storico.html`.
- Il dominio `www.archiviolascala.org` (citato dal sito come "DAM Digital Archive") **rimanda alla stessa pagina** vietata; `archivio.teatroallascala.org` non risponde.
- Per il mandato ("se robots.txt o i termini lo vietano, STOP") **non ho raccolto stagioni né record**. Nota onesta: seguendo il rimando di archiviolascala.org ho scaricato una sola pagina (la maschera di ricerca, 116 kB) che sta nella zona vietata; non l'ho conservata e ne ho letto solo il menu (filtri per tipo di spettacolo, titolo, autore, artista, luogo; sezioni Locandine, Fotografie, Libretto, Opera in breve, Discografia, Costumi, Accessori). Non ho aperto il `disclaimer` (anch'esso sotto `/it/archivio/`).
- Termini d'uso: le pagine `disclaimer` e `contatti` dell'archivio stanno nella zona vietata, quindi non le ho lette. **Strada giusta: chiedere il permesso e i dati direttamente alla Scala** (archivio storico / ufficio stampa). Il sito dice che la versione online è "limitata e semplificata" rispetto all'archivio completo. Copyright: ©Teatro alla Scala, da citare.
- Stima del totale: non fatta (richiederebbe interrogare l'archivio).

## 3. Buco 1906-1943: riempimento parziale da fonti aperte
**Wikidata** (CC0). Interrogazioni SPARQL del 29/10/2026 con `scripts\wikidata_scala.py` (Q5471 = Teatro alla Scala):
- `raw\wikidata\premiere_p4647.json` (0,70 MB): 580 righe, 456 opere con "luogo della prima rappresentazione" (P4647) = Scala; 442 con data (P1191). Per decennio: 1900-09: 15, 1910: 15, 1920: 24, 1930: 22, 1940: 7. Tipi (P31): opera 489 righe, balletto 19.
- `raw\wikidata\premiere_p276_event.json` (0,82 MB): 1248 righe, 1008 voci con "luogo" (P276) = Scala; **426 "stagione del Teatro alla Scala", 107 "serata inaugurale della stagione", 479 "produzione operistica", 59 "prima mondiale"**; solo 514 voci hanno la data (P585).
- `raw\wikidata\premiere_location_any.json` (0,52 MB): 822 righe, 772 voci con data di prima e luogo Scala (P291/P276/P4647 uniti). Per decennio 1900: 48, 1910: 15, 1920: 33, 1930: 24, 1940: 6; nel 2010 ce ne sono 60 (produzioni recenti).
- Le voci Wikidata Q52277762 / Q52277360 sono proprio il libro di Romani 1862.

**Wikipedia italiana** (CC BY-SA 4.0), via API MediaWiki, `scripts\wikipedia_scala.py`, in `raw\wikipedia\`:
- `Stagioni_liriche_del_Teatro_alla_Scala.json` (0,28 MB, revisione 152735080 del 03/10/2026): cronistoria 1778-2020 con opere per anno, direttore, interpreti, regia. Per 1906-1943 è **molto rado**: circa 2-5 titoli all'anno (es. 1930: Turandot, La Sagredo, La fanciulla del West), mentre le stagioni vere ne avevano molti di più. Contiene anche "Opere più rappresentate" e "Apertura della stagione lirica".
- `Prime_stagionali_al_Teatro_alla_Scala.json` (rev. 150788130), `Stagioni_di_balletto_del_Teatro_alla_Scala.json` (rev. 148776796), `Teatro_alla_Scala.json` (rev. 152968485).
- Il buco **non è chiuso**: l'unica fonte completa resta Gatti vol. 2 (carta) più, per 1906-1920, Marangoni-Vanbianchi.

## 4. Programma per le foto di Gatti (solo scheletro)
`scripts\gatti_foto_ocr.py` + `scripts\winocr.ps1`: cartella di foto -> pretrattamento (grigi, contrasto, ingrandimento) -> OCR con riquadri (Tesseract se c'è, altrimenti motore Windows) -> righe -> due CSV (`gatti_grezzo.csv` righe con data, `gatti_da_rivedere.csv` il resto). Colonne comuni a tutto il progetto: fonte, pagina_o_foto, data_iso, stagione, luogo, tipo, titolo, compositore, direttore, interpreti, regia_coreografia, note, testo_riga, affidabilita_ocr. Provato su una pagina di prova (gira, 50 righe); il riconoscimento del formato di Gatti va adattato guardando 3-4 foto vere.

## 5. Come confrontare le fonti più avanti
- **Cambiasi 1881 / 1872 / Romani 1862** (stessi anni 1778-1862): confronto per (anno, stagione, titolo normalizzato, maestro). Tre fonti indipendenti permettono di trovare errori di OCR e di stampa.
- **Cambiasi vs Wikidata**: per ogni opera con P4647 = Scala e data, cercare nella serie di Cambiasi lo stesso anno + titolo normalizzato (senza articoli e accenti, varianti ortografiche) e controllare la data (Cambiasi dà mese e giorno della prima).
- **Wikipedia (stagioni) vs Cambiasi**: per 1778-1881 trova i titoli che mancano in Wikipedia; per 1906-1943 il contrario.
- **Dopo il 1943**: Wikipedia vs archivio Scala solo se la Scala concede i dati.
- Il collegamento tra tutte è una tabella di titoli normalizzati e compositori (Wikidata ha anche gli alias).

## Trappole dei dati
- Il libro 1881 elenca opere per stagione, non rappresentazioni: non si contano le sere di spettacolo.
- Tabelle su due pagine; note `(1)`, `(2)` dentro le celle; "id." per ripetere la stagione.
- Nomi storpiati dall'OCR; accenti e ligature diventano `�`.
- La copia Google 1881 ha nel titolo "1776-1881" per errore del catalogo: l'inizio è il 1778.
- Wikidata: lo stesso spettacolo può comparire come opera (P4647) e come produzione/evento (P276): contare per voce, non per riga (580 righe = 456 opere).
- L'API di Google Books ha oggi la quota esaurita.

## Archivio Scala (fase 2, 29/10/2026) - in attesa
- La Scala ha autorizzato la raccolta (vedi JOURNAL 29/10/2026). Citazione: "(c) Teatro alla Scala".
- Struttura: l'archivio storico non ha elenchi di stagioni ne' indirizzi fissi per spettacolo: si arriva ai dati solo da una maschera di ricerca (`/it/archivio/ricerca.html`) con filtri su tipo, titolo, autore, artista, luogo e stagioni (86 stagioni dalla 1943-44 alla 2025-26). Non ci sono servizi JSON dietro.
- Problema: la ricerca funziona solo se il browser invia un codice "info" prodotto da uno script anti-bot (`etnobot.js`). Senza, il sito risponde "Non sono stati trovati spettacoli" (provato su stagione 1946 e su "Callas"). Falsificare quel codice vorrebbe dire aggirare l'anti-bot: non l'ho fatto.
- Risultato: nessuna stagione ne' spettacolo raccolti, nessun `pulito/archivio_scala.csv`. Serve che la Scala tolga l'anti-bot per questa raccolta o mandi i dati direttamente (dettagli in STATO.md).

---

# FASE 2 - la tabella unica del cartellone (29/10/2026)
Cartella `pulito\`. Programmi in `scripts\`. Nessuna pagina del sito, nessun git. L'archivio storico della Scala (la ricerca con anti-bot) resta fuori: non si tocca.

## Che cosa c'e adesso
| File | Che cos'e |
|---|---|
| `cartellone.csv` | **Tabella unica**: 5146 righe, una per titolo e stagione secondo UNA fonte (le fonti si sovrappongono apposta). Colonne: stagione, data, anno, titolo, autore, genere, direttore, regista, interpreti (separati da `;`), sala, fonte, affidabilita (alta/media/bassa), riga_fonte, ripubblicabile (si/no). |
| `copertura.csv` | Per ogni anno 1778-2027: titoli distinti in tutte le fonti, titoli per fonte, fonti presenti. |
| `copertura_stagioni_1906_1963.csv` | Per ogni stagione 1906-07 ... 1962-63: titoli da Wikipedia, Wikidata, Marangoni, da Gatti, quanti nuovi grazie a Gatti. |
| `gatti_vol1_citazioni.csv` | Tutto quello che si ricava da Gatti vol. I (3025 righe: titolo, autore, pagina del libro, stagione, direttore, regista, interpreti, confidenza). Solo fatti, nessun testo copiato. |
| `gatti_vol1_verifica.md` | Controllo a mano: precisione dell'estrazione. |
| `differenze.md` | Confronti: Cambiasi / Romani / Wikipedia (1778-1862) e Gatti / Wikipedia / Wikidata / Marangoni (1906-1963). |
| file che iniziano con `_` | Passaggi intermedi. **`_gatti_contesti_locali.csv` contiene brani del libro di Gatti (ancora protetto): resta solo sul PC, mai su GitHub.** |

## Righe per fonte
| Fonte (`fonte`) | Righe | Anni | Qualita | `ripubblicabile` |
|---|---|---|---|---|
| `cambiasi_1881` (opere) | 1076 | 1778-1881 (tranne 1832 e 1835, vuoti) | OCR di Internet Archive: media, bassa dove la confidenza OCR e sotto 45 | si (opera libera; la scansione no) |
| `romani_1862` | 750 | 46 anni su 85 tra 1778 e 1862 | lettura parziale del testo OCR: titolo, genere, a volte maestro | si |
| `wikipedia_it_stagioni_liriche` | 1092 | 1778-2024 | media; alcuni titoli troncati | si, ma CC BY-SA 4.0: citare e riusare con la stessa licenza |
| `wikidata_prime` | 772 | 1778-2020 circa | prime assolute con data, solo cio che Wikidata ha | si (CC0) |
| `marangoni_vanbianchi_1922` | 118 | 1906-1918 | 64 righe dalla tabella delle opere (1906-1913) + 54 titoli dai cartelloni di 6 stagioni (titoli corretti a mano sull'OCR) | **no** |
| `gatti_vol1` | 951 | 1882-1962 | media/bassa, vedi sotto | **no** (i fatti si possono usare citando: "C. Gatti, Il Teatro alla Scala nella storia e nell'arte, vol. I, Ricordi 1964") |
| `scala_sito_pubblico` | 387 | 2023-24 ... 2026-27 | alta (dati ufficiali) | si, citando "(c) Teatro alla Scala" (autorizzazione ricevuta da Davide) |

## Gatti vol. I - come e stato letto
Il volume 1 e il *racconto*: non ha la cronologia (quella e nel volume 2), quindi **non e un elenco completo**. Si e fatto cosi:
1. Il testo OCR del PDF (682 pagine) e stato estratto con pymupdf. Pagina stampata = pagina del PDF meno 12; l'appendice 1958-63 ha numeri romani.
2. Letti i due indici: **indice delle opere** (1263 voci + 161 dell'appendice) e **indice dei nomi** (3007 + 167). Dicono su quali pagine ogni opera e ogni persona compaiono.
3. La stagione di ogni pagina si ricava dai titoli di sezione ("La stagione 1932-33.", 57 in tutto) e dalle date con giorno, mese e anno. Le date che rimandano al passato dentro una sezione ("nel maggio del 1950") vengono scartate.
4. Per ogni titolo e ogni pagina dell'indice si cerca il titolo nel testo della pagina (anche con piccoli errori OCR e nelle pagine accanto). Se la frase dice che l'opera "si rappresenta", "va in scena", "diretta da ..." la riga conta come spettacolo (`segnale_spettacolo = si`).
5. Direttore, regista e interpreti: si cercano nomi **che l'indice dei nomi mette proprio su quella pagina**, vicino al titolo, dopo parole come "diretta da", "cantanti principali", "protagonista". Se la frase contiene piu titoli il legame e segnato come incerto e nel `cartellone.csv` i nomi restano vuoti.

**Numeri:** 2992 coppie (titolo, pagina); titolo ritrovato nel testo 80%; 1529 righe con segnale di spettacolo; solo 180 righe con almeno un nome (il racconto nomina i cantanti col solo cognome e spesso senza dire in quale opera).
**Precisione (controllo a mano, vedi `gatti_vol1_verifica.md`):** titolo e stagione giusti in 61 righe su 70 = **87%**. Nomi: 79% sui verificabili; 100% sulle righe non segnate "incerte".
**Limite principale:** Gatti nomina circa 10-12 titoli per stagione contro i 20-30 reali. Quello che Gatti non cita non c'e: il buco 1906-1963 si riduce molto ma non si chiude.

## Copertura per periodo (titoli distinti per anno, tutte le fonti)
| Periodo | Titoli per anno | Da quali fonti |
|---|---|---|
| 1778-1881 | 18 in media (104 anni su 104) | Cambiasi, Romani, Wikipedia, Wikidata |
| 1882-1905 | 11 | **Gatti** (6 per anno) + Wikipedia e Wikidata (3-4 ciascuno): il buco dopo Cambiasi 1881 e riempito in parte |
| 1906-1920 | 15 (13 anni su 15) | Marangoni 7,6 + Gatti 8,5 + Wikipedia 2,4 + Wikidata 1,2 |
| 1921-1943 | 13,5 | Gatti 10,3 + Wikipedia 3 + Wikidata 2 |
| 1944-1963 | 15,6 | Gatti 9,2 + Wikipedia 4,7 + Wikidata 2,5 |
| 1964-2022 | 4 | solo Wikipedia e Wikidata: **buco da chiudere** (serve l'archivio della Scala) |
| 2023-2027 | 75 | sito della Scala |

**1906-1963 prima e dopo Gatti** (somma su 57 stagioni): titoli-stagione da Wikipedia 202 (per eccesso); da Wikipedia + Wikidata + Marangoni 372; con Gatti 878. Stagioni con almeno 5 titoli: 14 con la sola Wikipedia, 34 con Wikidata e Marangoni, **55 su 57 con Gatti**. Le uniche stagioni sotto i 5 titoli sono 1919-20 e 1920-21 (il racconto di Gatti passa in fretta sugli anni dell'Ente Autonomo). Dettaglio per stagione in `copertura_stagioni_1906_1963.csv`.

## Qualita dell'OCR e dei programmi di lettura
- **Cambiasi 1881**: hOCR di Internet Archive (ABBYY). Righe grezze 1136, 1076 tenute. Riparate due pagine che il primo programma saltava (pagine 42 e 90 del file: una riga cominciava con "(" ed era scambiata per una nota). L'anno si legge bene solo in 116 righe: per le altre si contano i cambi di stagione (Autunno poi Carnevale = anno dopo). Nomi dei maestri storpiati ("Sftlieri"): corretti solo quando una forma simile compare almeno 3 volte. Segni "-fa" e "^" tolti dai titoli. La data completa (giorno e mese) c'e solo su una parte delle righe. **La serie dei balli (dopo la pagina 104) non e stata letta.**
- **Romani 1862**: letto il testo OCR; funziona per le stagioni scritte "Titolo. D. s.", 46 anni su 85. Mancano 39 anni (1783, 1785, 1788, 1794, 1802-03, 1807-08, 1810, 1812-15, 1820-24, ...) perche l'intestazione dell'anno e storpiata.
- **Marangoni-Vanbianchi**: la tabella ha le colonne spezzate dall'OCR; si sono lette solo data, titolo, genere e maestro dove stanno sulla stessa riga; gli esecutori non si possono abbinare. Vuoti: 1914-15, 1917-18, 1919-20.
- **Sito Scala**: 390 pagine, 387 righe; 345 con data, 196 con direttore. I concerti non hanno compositore ne programma.

## Trappole dei dati (nuove)
- Cambiasi e Romani contano per *anno teatrale* (il Carnevale che comincia il 26 dicembre vale per l'anno dopo), Wikipedia per anno del calendario: i confronti guardano anche l'anno prima e quello dopo.
- Gatti: una citazione non e una rappresentazione. Le righe "senza segnale di spettacolo" restano solo in `gatti_vol1_citazioni.csv`. Le tournee (Berlino, Genova, Edimburgo) compaiono nel racconto accanto ai titoli della stagione: la colonna `sala` e vuota per Gatti.
- Gatti: gli indici hanno pagine sbagliate dall'OCR (un 2xx al posto di un 26x): per questo il titolo si cerca anche nelle pagine accanto (75 casi, segnati nella nota).
- Wikipedia: alcune righe hanno titoli troncati ("Fior", "La fanciulla", "Figli"); le righe senza data valgono per due stagioni possibili, quindi i conteggi per stagione sono per eccesso.
- Nei conteggi un titolo vale una volta per stagione: le repliche non si contano.

## Come rifare tutto
```
python -I -X utf8 scripts/gatti_estrai_testo.py raw/programmi_davide/programmi_scala.pdf raw/gatti_testo/gatti_pagine.json
python -I -X utf8 scripts/gatti_indici.py raw/gatti_testo/gatti_pagine.json pulito
python -I -X utf8 scripts/gatti_citazioni.py raw/gatti_testo/gatti_pagine.json pulito
python -I -X utf8 scripts/parse_cambiasi_opere.py pulito/_cambiasi_hocr.json pulito/_cambiasi_opere.csv
python -I -X utf8 scripts/pulisci_cambiasi.py pulito/_cambiasi_opere.csv pulito/_wp_stagioni.csv pulito/_cambiasi_pulito.csv
python -I -X utf8 scripts/parse_romani.py raw/romani/teatroallascalac00romauoft/teatroallascalac00romauoft_djvu.txt pulito/_romani_opere.csv
python -I -X utf8 scripts/parse_marangoni.py raw/cambiasi/pdf24_merged-16/pdf24_merged-16_djvu.txt pulito/_marangoni_opere.csv
python -I -X utf8 scripts/parse_scala_stagioni.py raw/scala_stagioni pulito/_scala_sito.csv
python -I -X utf8 scripts/costruisci_cartellone.py pulito
python -I -X utf8 scripts/confronti.py pulito
```

## Da decidere / prossimi passi
1. Gatti vol. 2 (la cronologia completa 1778-1963): il racconto riempie solo meta dei titoli.
2. 1964-2022: serve l'archivio della Scala (dati dalla Scala, oppure togliere l'anti-bot per il programma).
3. Cambiasi: leggere anche la serie dei balli (pagina 104 in poi) e controllare a campione 20 pagine del parser contro le immagini.
4. Romani: sistemare l'intestazione degli anni per recuperare i 39 anni mancanti.
