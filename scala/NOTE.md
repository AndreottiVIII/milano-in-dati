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


## SBN programmi di sala (29/10/2026)
**Che cos'è.** Il catalogo delle biblioteche italiane (SBN OPAC) schedula i programmi di sala della Scala: uno per opera o balletto, più i libretti di stagione e i concerti. Dà titolo, compositore, spesso direttore e regia, a volte una nota con la data ("prima rappresentazione 11 gennaio 1963"). Non dà le repliche giorno per giorno.

**Come l'ho raccolto.** Interfaccia JSON che usa il sito stesso (`opacmobilegw/search.json` e `full.json`). `robots.txt` permette tutto, nessuna chiave, nessun blocco, nessun errore. Una richiesta alla volta, almeno 3 secondi di pausa, User-Agent "milano-in-dati research project", ogni risposta salvata in `raw\sbn\` (riprendibile). Programmi: `scripts\sbn_lib.py`, `sbn_raccogli.py`, `sbn_schede.py`, `sbn_parse.py`, `sbn_copertura.py`.
- Ricerche (318 richieste): "teatro alla scala AAAA" per ogni anno 1963-2024 (tutte le pagine), "rappresentazioni teatro alla scala AAAA-AA" e "teatro alla scala stagione AAAA-AA" per ogni stagione, "piccola scala AAAA", Arcimboldi, tournée. 6.313 record letti, 2.072 sono della Scala (editore o ente), ma non tutti sono programmi (il resto: mostre del Museo, libri, cataloghi).
- Schede complete (1.240 richieste, solo produzioni, ospiti, tournée, libretti di stagione): note (date), compositore, biblioteche. Circa 1.558 richieste in tutto, 11 MB di risposte.

**Risultato.** `sbn\sbn_programmi.csv`: 1.725 righe dopo aver unito i doppioni (stesso programma schedato da più biblioteche: 347 schede unite). Di queste 920 produzioni + 8 ospiti (opere, balletti, serate) + 4 tournée, 498 concerti, 224 libretti di stagione, 71 "da verificare". Ogni riga ha il titolo originale, il BID, il link alla scheda e le biblioteche (in media 8,6 per programma). Sala: quasi tutto "Scala" (è il valore di partenza: SBN non lo dice); Piccola Scala 10 e Arcimboldi 6 solo dove il titolo lo scrive.
- Compositore trovato nell'91% delle produzioni; **direttore solo nel 14%, regia 16%, coreografo 20%, interpreti 4%**: il cast compare nel titolo solo per una parte dei record.
- Data (giorno) per 683 produzioni su 928 (dalle note: spesso la prima, non le repliche). Stagione nota per 702 (da "stagione 1962-63" nel testo o ricavata dalla data: da settembre in poi = stagione che comincia quell'anno).

**Copertura per decennio (produzioni distinte, anno di stampa del programma).**

| Decennio | Programmi (produzioni) | Titoli distinti | Per anno | Concerti | Libretti di stagione |
|---|---|---|---|---|---|
| 1963-69 | 80 | 77 | 11 | 11 | 36 |
| 1970-79 | 167 | 130 | 17 | 48 | 42 |
| 1980-89 | 136 | 119 | 14 | 84 | 31 |
| 1990-99 | 167 | 151 | 17 | 187 | 52 |
| 2000-09 | 183 | 155 | 18 | 64 | 33 |
| 2010-19 | 148 | 119 | 15 | 91 | 23 |
| 2020-24 | 47 | 44 | 9 | 13 | 7 |

Una stagione tipica della Scala ha 15-20 produzioni tra opere e balletti (più il balletto di settembre). Quindi 1970-2009 è vicino alla stagione quasi intera (per anno 14-18); **1963-69 è più rado** (4-19 per anno, poche schede del 1965 e del 1969); **dal 2020 cala** (2022-23: nessuna produzione con stagione nota, 2023-24: una): il catalogo ha ritardo, non sono mancate le produzioni. File per anno: `sbn\copertura_sbn_per_anno.csv`; per stagione: `sbn\copertura_sbn.csv` (colonna "stima totale" = quelle con stagione nota + metà delle senza stagione dei due anni vicini).

**Confronto con Wikipedia** (`sbn\confronto_wikipedia.csv`, sola lettura di `pulito\_wp_stagioni.csv`). Wikipedia ha una sola riga all'anno dopo il 1963 (l'apertura del 7 dicembre), tranne 2011-15 e dal 2022 (stagioni intere).
- Aperture 1963-2024: 56 righe, **45 trovate in SBN con lo stesso titolo (80%)**, 8 trovano solo un'altra opera dello stesso compositore (programma dell'apertura non catalogato), 3 niente (1963 "Cavalleria-Amico Fritz", 1993 La Vestale, 2022 Boris Godunov).
- Stagioni 2011-15 e 2022-24: 93 titoli Wikipedia, **67 trovati (72%)**; 26 no: 2012 Hoffmann e Don Pasquale; quasi tutto il 2022 e il 2023 (catalogo in ritardo). Non è Wikipedia contro SBN a vincere: i due elenchi si completano.
- Differenze di grafia che il confronto ha dovuto aggirare: Götterdämmerung / Il crepuscolo degli dei, Tristan und Isolde / Tristano e Isotta, Die Walküre / La Walkiria; nomi sbagliati in Wikipedia (compositore "W", "cane").

**Licenza.** Nessuna licenza dichiarata sull'OPAC. Sono fatti bibliografici (titolo, nomi, anno, biblioteca). Citazione da usare: "Catalogo SBN – ICCU; licenza non indicata". Pubblichiamo solo i fatti con la citazione, non i testi dei programmi. Interfaccia JSON non documentata: resta consigliato scrivere all'ICCU (ic-cu.opacsbn@cultura.gov.it) come già scritto in `FONTI_POST_1963.md`.

**Problemi.**
- Solo l'anno di stampa, non il giorno delle repliche; il programma del 1975 può essere della stagione 1974-75 o 1975-76 (risolto con le note nel 40% dei casi).
- Nel titolo SBN il compositore e il cast hanno forme libere: l'estrazione è fatta con regole e **va controllata** (es. a volte "regia" contiene più nomi). Il testo originale resta in `titolo_originale`.
- 71 righe "da_verificare" (recital, gala, titoli senza parole chiave) e gruppi di concerti dei quali non ho scaricato le schede complete (solo ricerca: senza biblioteche né note).
- Doppioni residui possibili (stesso titolo scritto in modo diverso) e raggruppamenti sbagliati (stesso titolo, due produzioni nello stesso anno): controllare con `bid_altri`.
- Per un paio di minuti due copie del programma di scarico sono girate insieme (due richieste ogni 3 secondi invece di una): nessun errore.


## SBN nomi e altre fonti (30/10/2026)
Richiesta di Davide: "di programmi Scala puoi trovare qualcosa in più?". Risposta breve: dai dati SBN già scaricati si ricava un po' di più (nomi con ruolo), ci sono due fonti nuove di controllo (registrazioni dal vivo); i veri buchi (cartellone 1964-2022 giorno per giorno) restano.

### 1. Nomi con ruolo nelle schede SBN (nessun nuovo scarico)
**Che cosa c'è nelle schede complete** (`raw\sbn\full\*.json`, 1.240 programmi). Il campo `nomi` è una lista di nomi con l'etichetta del ruolo tra parentesi quadre: `[Compositore]`, `[Librettista]`, `[Regista]`, `[Direttore d'orchestra]`, `[Coreografo]`, `[Scenografo]`, `[Costumista]`, `[Interprete]`, `[Cantante]`, `[Strumentista]` e altri; per qualche cantante c'è anche la voce (`[590S=Soprano]`). Molti nomi però non hanno etichetta (1.623 occorrenze) e allora il ruolo si ricava dal titolo o dalle note ("regia di ...", "direttore d'orchestra ...", "interpreti principali ..."). Le note contengono anche le date ("Prima rappresentazione: 19 giugno 2012").
**Programma:** `scripts\sbn_nomi.py` (da lanciare dopo `sbn_parse.py`). Scrive:
- `sbn\sbn_persone.csv`: 5.088 righe (BID della riga, BID della scheda, nome, ruolo, dettaglio, **fonte**, etichetta originale, persona/ente). Fonte = `nomi` (etichetta della scheda; 3.059 righe), `nomi+titolo` (nome senza etichetta a cui titolo/note danno il ruolo; 907), `titolo` (999) o `note` (123) per nomi che stanno solo nel testo. 1.632 nomi di persona diversi. Ruoli più frequenti: compositore 803, interprete 779, librettista 776, direttore 340, coreografo 340, regista 233, scenografo 168, costumista 162. Nomi senza ruolo noto: 297 (restano "nome senza ruolo").
- `sbn\sbn_programmi.csv` arricchito (colonne vecchie intatte; nuove: `scenografo`, `costumista`, `librettista`, `fonte_ruoli`, `data_prima`, `data_tipo`, `date_scala`, `mese_rappr`, `data_fonte`, `n_ordine`). Regola: se ci sono nomi strutturati, sostituiscono il valore ricavato dal titolo (e si aggiungono i nomi del solo testo con cognome diverso); altrimenti resta il valore vecchio, ripulito. **Ogni cambio è in `sbn\sbn_nomi_log.csv`** (1.654 righe: programma, campo, prima, dopo, fonte). Copia di sicurezza della versione di ieri: `sbn\_sbn_programmi_v1_backup.csv`.

**Errore corretto in `sbn_parse.py`:** il numero d'ordine del programma ("3: I due Foscari", "12. Falstaff") finiva nel titolo, o lo troncava a "3". Ora viene tolto e messo nella colonna `n_ordine` (295 righe); resta intatto "9. sinfonia". I programmi che prima sembravano diversi per quel numero ora si uniscono: 1.725 → 1.707 righe. Le registrazioni sonore non entrano più tra i programmi (3 righe uscite).

**Nuova copertura** (`sbn\sbn_nomi_copertura.csv`, produzioni + ospiti = 911 righe):

| Campo | Prima | Dopo |
|---|---|---|
| Direttore | 130 (14,3%) | 199 (21,8%) |
| Regia | 144 (15,8%) | 226 (24,8%) |
| Coreografia | 171 (18,8%) | 199 (21,8%) |
| Interpreti | 36 (4,0%) | 86 (9,4%) |
| Scenografo / costumista (nuovi) | 0 | 154 / 150 |
| Librettista (nuovo) | 0 | 561 |
| Giorno (data_iso) | 676 (74,2%) | 679 (74,5%) |
| Giorno della prima rappresentazione (data_prima, nuovo) | 0 | 609 (66,8%) |

Concerti (498 righe; di loro non ho le schede complete, solo il titolo): direttore 0 → 120 (24%), interpreti (solisti: "Dino Ciani, pianista") 0 → 217 (44%). Dopo il passaggio 519 produzioni su 911 non hanno ancora né direttore né regia né coreografia né interpreti: **le schede non li scrivono, non c'è altro da estrarre**.

**Date.** Il giorno c'era già per il 74% delle produzioni; ora si evita di prendere la data di un altro teatro ("prima rappresentazione 7 ottobre 1994 al Teatro Ponchielli di Cremona, 14 ottobre 1994 al Teatro alla Scala" → 14 ottobre), si prende il primo giorno degli elenchi ("17 e 28 aprile 1985" → 17) e si distingue la prima rappresentazione (`data_tipo` = prima, 611 righe) da una data qualunque (296). Solo mese: 29 righe ("Rappresentazioni: marzo-aprile 2011") in `mese_rappr`. 45 `data_iso` e 6 stagioni sono cambiate, tutte nel log.

**Limiti.** (a) Le etichette sono dei catalogatori: `[Regista]` è messo anche al coreografo-regista (Nureyev 20 volte come regista) e, per balletti tratti da film, al regista del film (La strada: Fellini). (b) Due nomi con lo stesso cognome nello stesso ruolo si fondono se vengono dal testo. (c) Gli enti (Teatro alla Scala, Corpo di ballo...) non sono nelle colonne, solo in `sbn_persone.csv` con tipo_nome = ente. (d) Nelle liste del titolo con "A, B soprano" si prende solo il nome davanti al ruolo.

**Sito.** `scripts\pagina_dati.py` rilanciato: `docs\scala\data\*.json` ora usano direttore, regia e interpreti arricchiti (anche i solisti dei concerti); layout invariato, nota della fonte SBN aggiornata in `fonti.json`; nessun git.

### 2. Internet Archive (nessun login; ricerca avanzata + API metadata, 3 s tra richieste)
Programmi: `scripts\ia_cerca.py`, `ia_cerca2.py`, `ia_metadati.py`. Uscite in `raw\ia_scala\`: `tutti.json`, `tutti2.json` (circa 400 risultati unici), `ia_elementi_scala.csv` (41 elementi controllati: accesso, testo OCR, MB), `testi\` (2 testi aperti di prova, 1,2 MB).
Esito: **nessuna cronologia di stagioni dopo il 1881 è aperta su IA**. Elementi utili:

| Elemento (identifier) | Anni | Accesso | Testo | A cosa serve |
|---|---|---|---|---|
| `teatroallascala00cambgoog`, `teatroallascala100camb` (Cambiasi 1881) | 1778-1881 | aperto | OCR sì | già usato |
| `teatroallascalac00romauoft` e 3 copie (Romani 1862) | 1778-1861 | aperto | OCR sì | già usato |
| `pdf24_merged-16` (Marangoni-Vanbianchi) | 1906-1920 | aperto | OCR sì (1,8 MB) | già in raw |
| `bwb_W8-BSY-089` (Gatti, Il Teatro alla Scala nella storia e nell'arte 1778-1963, ed. 1964) | 1778-1963 | **prestito** (serve account) | OCR esiste, non scaricabile | la cronologia completa 1882-1963; non usata |
| `la-scala-rivista-s.-b.-47.56` (rivista "La Scala", Branzi) | 1956-1960 | **prestito** | OCR 18 kB | un solo volume; la rivista 1949-1963 non c'è aperta |
| `lascala0000arru` (Arruga 1975), `lascala00lott` (Lotti 1979), `lecartedellascal0000giaz` (Giazotto 1990), `lascalaencyclope0000bagn` (Bagnoli 1993), `massimomilaallas0000mila` | 1975-1993 | **prestito** | | libri di storia, non cronologie |
| `teatro-alla-scala` (Secchi, Il Teatro alla Scala 1778-1978: architettura, tradizione, società) | 1977 | aperto ("public domain mark") | OCR 0,8 MB | letto: architettura e saggi, **nessuna lista di stagioni** (OCR sporco) |
| circa 40 programmi "Teatro alla Scala - [opera] - Stagione 2009-2010 / 2010-2011" e 2002-2003 | 2002-2011 | aperto | OCR sì (40-750 kB) | cast e saggi per produzione; scaricato 1 campione (Don Giovanni 2009, 0,4 MB); si può collegare a SBN |

Non trovati su IA: "Musica d'oggi", Tintori (la cronologia 1778-1977 esiste solo in carta), "Duecento anni". Molti LP/CD dal vivo (Callas, Karajan...) con l'anno ma senza il giorno.

### 3. Archivi di giornali (solo verifica, nessuna raccolta di massa)
- **La Stampa** (`archiviolastampa.it`): da questo PC il sito in HTTPS ha un certificato che non corrisponde al nome (errore `SEC_E_WRONG_PRINCIPAL`): **non l'ho forzato**. In HTTP semplice funziona. `robots.txt`: vieta solo Googlebot e cartelle tecniche, gli altri sono ammessi. Condizioni d'uso: sul sito non ci sono (solo il rimando alle note legali generiche della Regione Piemonte); gli articoli sono di Editrice La Stampa. Ricerca: modulo web (POST) con testo, data esatta o intervallo, testata; la risposta è HTML leggibile con titolo, data, numero, pagina e anteprima di circa 300 caratteri. **Prova unica per il 7 dicembre**: ricerca "Scala" l'8/12/1976 → 317 articoli, in prima pagina l'inviato racconta la serata del 7 dicembre. I PDF delle pagine si scaricano solo dopo aver copiato le lettere di un'immagine (CAPTCHA): non usati. Il giornale arriva al 2005. File: `raw\giornali\`. Conclusione: **utile per controllare a mano o a campione la serata del 7 dicembre, non per costruire il cartellone** (nessuna API, testi con errori OCR, diritti non chiariti: per pubblicare bisognerebbe chiedere a La Stampa).
- **l'Unità**: `archivio.unita.news`, `archivio.unita.it` e il sito dell'archivio storico presso la Fondazione Gramsci **non si risolvono (DNS)** da questo PC; `www.unita.it` risponde ma non ha l'archivio storico. Bloccato, non provato altro.

### 4. Registrazioni dal vivo alla Scala (fonti di controllo, non programmi)
**a) SBN, registrazioni sonore.** Programmi: `scripts\sbn_registrazioni_cerca.py`, `scripts\sbn_registrazioni.py` -> `sbn\sbn_registrazioni.csv`. Stesso cliente di `sbn_lib` (3 s, cache). 7 ricerche (circa 160 pagine) con "orchestra e coro del teatro alla scala" ecc.: in cache ora 7.494 registrazioni sonore, 2.994 con "Scala" nel titolo, nell'autore o nell'editore. Per non fare 3.000 richieste ho scaricato la scheda completa (con le note "Registrazione dal vivo, Milano, Teatro alla Scala, 10 maggio 1961") solo dei **377** candidati con parole come live/dal vivo/inedito, un anno nel titolo o un'etichetta nota per i dal vivo (Melodram, Myto, Arkadia, Foyer, Urania, Musicom...). Esito: **412 schede con la Scala** (alcune sono antologie), **68 dal vivo, 25 con il giorno**, 320 con direttore, 281 con interpreti. Esempi: Beatrice di Tenda 10/5/1961 (Votto, Sutherland), Semiramide 17/12/1962 (Santini), Macbeth 7/12/1952 (Callas), Werther 12/2/1976 (Prêtre, Kraus), Rigoletto 13/5/1994 (Muti). Solo 2 date coincidono con una data già nei programmi di sala. Le ricerche sulle registrazioni sono tenute fuori dai programmi (elenco `SALTA` in `sbn_parse.py`). Non ho scaricato le altre circa 2.600 schede: si può fare in seguito (riprendibile, stesso comando).
**b) Operadis (CLOR)**, discografia ferma al 2009, `www.operadis-opera-discography.org.uk`: `robots.txt` vieta solo SemrushBot e MJ12bot, nessuna condizione d'uso scritta, ma i dati sono il lavoro di un compilatore: **uso solo per controllo, nei file locali, non per ripubblicare**. 632 pagine (una per opera, 27 MB, `raw\discografie\operadis\`), programmi `scripts\operadis_scala.py` (scarico) e `scripts\operadis_parse.py` (lettura dalla cache) -> `raw\discografie\operadis_scala.csv`. **452 registrazioni con orchestra o coro della Scala, 296 dal vivo (LI), 212 con il commento "performance at La Scala", 239 con una data scritta** (anno, direttore, cast ruolo per ruolo, a volte il giorno: "Fidelio 10 dicembre 1974, Böhm"). Per decennio (dal vivo): anni '50 54, '60 46, '70 64, '80 45, '90 47, 2000-09 39. Attenzione: alcune dal vivo sono in tournée (Bruxelles 1958) e il giorno scritto può essere quello di una recensione.
**c) MusicBrainz** (già in `FONTI_POST_1963.md`): 3.933 registrazioni, dopo il 1963 solo 38 date. **d) Internet Archive audio**: decine di LP/CD con l'anno ma senza giorno; non raccolti.
Per le serate del 7 dicembre e per controllare il cartellone: le date dal vivo SBN + Operadis + MusicBrainz sono un controllo, non una fonte da cui costruire il cartellone.

### Cose da sapere (trappole)
- Due programmi di scarico di Operadis sono girati insieme per circa 25 minuti (due richieste ogni 3 secondi invece di una) e per un paio di minuti due copie di `sbn_registrazioni_cerca.py`; nessun errore né blocco, ma da non ripetere. Un solo errore di rete (connessione interrotta) con ripresa automatica.
- Errore mio, corretto: in alcuni programmi `\b` era diventato un carattere invisibile e le espressioni non trovavano nulla; i numeri riportati sopra sono quelli dopo la correzione.
- Ordine per rifare tutto: `sbn_parse.py` → `sbn_nomi.py` → `pagina_dati.py`. Rilanciare `sbn_nomi.py` due volte senza `sbn_parse.py` in mezzo falserebbe il "prima/dopo".

## Tre lavori approvati da Davide (30/10/2026)

### 1. Balli di Cambiasi 1778-1881 (serie dei balli, libro p. 83-110)
Programma: `scripts\parse_cambiasi_balli.py` (legge il testo OCR ABBYY `raw\cambiasi\teatroallascala100camb\..._djvu.txt`, non l'hOCR a riquadri: qui l'ordine di lettura ABBYY e' migliore) -> `pulito\_cambiasi_balli.csv`, log `pulito\_cambiasi_balli_log.txt`, copertura `pulito\copertura_balli_1778_1881.csv`.
La serie dei balli NON e' una tabella come quella delle opere, ma un testo a stagioni: "1779. CARNEVALE - Porzia, di Candiani - La festa campestre ..., tutti di Regina. P. B. <prime ballerine>; <primi ballerini>." Il programma riconosce anno e stagione (anche composte: "Carnevale e Quaresima", "Autunno ed Avvento"), divide i balli, assegna "tutti di X" a quelli senza coreografo, legge "m. di Y" (compositore), le date tra parentesi (3 agosto) e l'esito (ottimo...buono...cattivo).
Esito: **871 balli, 104 anni su 104** (1778-1881), 2-16 per anno (media 8,4: 10,5 nel 1778-99, 12 nel 1800-29, 6,5 nel 1830-59, 3,8 nel 1860-81: negli anni tardi Cambiasi elenca meno balli). Coreografo nel 93%, compositore nel 25%, data nel 33%, esito nel 38%.
Controllo sulle immagini (3 stagioni a caso, seme 1881): **1817, 1824, 1826** (pagine 92, 94, 95 del libro): titoli, coreografi, date ed esiti coincidono; solo errori di lettura dell'OCR (ad es. "Eradamante" per "Bradamante", "Lircea" per "Dircea", "Clorico" per "Clerico"). Le voci "Compositore, X" senza titolo (4) non entrano.
Trappole: i numeri d'anno sono letti male dall'OCR (1500 per 1800, 17S9, ISSO...) e per 11 stagioni mancano: l'anno e' ricostruito dalla successione (ogni Carnevale apre un anno) e la sequenza torna per tutti i 104 anni; 9 righe corrette a mano nel programma (elenco nel log); la data "(7 ottobre" con la parentesi persa dall'OCR a volte perde il giorno; le prime ballerine sono per STAGIONE, non per ballo (restano nel csv, non nel cartellone).
Nel cartellone: `fonte = cambiasi_1881` (stessa etichetta delle opere, cosi' il codice C della pagina le tiene insieme; i balli si riconoscono da `genere = ballo`), coreografo in `regista` come "coreografia X", compositore in `autore`, ripubblicabile si (libro 1881, pubblico dominio).

### 2. Programmi di sala 2002-2011 su Internet Archive
Programmi: `scripts\ia_programmi_cerca.py` (ricerca avanzata, 3 s), `ia_programmi_scarica.py` (testo OCR di ogni elemento; PDF solo se <= 12 MB: i 4 programmi grandi pesano 116-162 MB e il testo basta), `ia_programmi_estrai.py` -> `pulito\ia_programmi_2002_2011.csv` e `pulito\ia_programmi_storico_alla_scala.csv`. Raw in `raw\ia_programmi\<identificativo>\` (metadata.json, testo.txt, programma.pdf se piccolo).
**I programmi di sala aperti con testo sono 14, non circa 40** (le ricerche per titolo, creatore e data non ne trovano altri; gli altri "Teatro alla Scala" 2002-2011 sono in prestito o sono DVD): 5 opere in forma di "dispensa" (Rigoletto 2010, Tosca 2011, Roméo et Juliette 2011, Der Rosenkavalier 2011, Fidelio 2003 al Teatro degli Arcimboldi), 4 programmi grandi di 200-700 pagine (Carmen, Don Giovanni, L'elisir d'amore, Der Rosenkavalier) e 5 concerti (Pappano, Robertson, Jordan, Requiem con Barenboim, Gala Domingo). Nota: il titolo IA di alcuni porta la stagione sbagliata (Carmen "2009-2010" e' la ripresa di ottobre 2010).
Cosa c'e': titolo, compositore, data della prima (14 su 14; per un concerto ricavata dal titolo), repliche (lette per 5 programmi dove l'OCR le tiene in ordine: Don Giovanni 7 date, Fidelio 6, Rigoletto, Roméo, Tosca 11), direttore e regia (Carmen: Dudamel, Emma Dante; Don Giovanni: Langree, Mussbach; Elisir: Renzetti, Pelly; Rosenkavalier: Jordan, Wernicke; concerti: direttore dal titolo, solisti dal sommario), cast per ruolo **solo per il Gala Domingo** (Siegmund, Sieglinde, Hunding): le dispense non pubblicano il cast.
**Bonus: i capitoli "<opera> alla Scala dal ... al ..."** dei 4 programmi grandi elencano ogni produzione storica con data, numero di recite, direttore, regia, scene, costumi, direttore del coro: **55 produzioni (1814-2009), 29 dopo il 1945** (Carmen 1946, 49, 59, 60, 63, 74, 2009; Don Giovanni 1948, 53, 56, 63, 89, 99, 2006; Elisir 1947 ... 2001; Rosenkavalier 1952, 61, 76, 2003). Direttore in 41 su 55, regia in 30. Il **cast per ruolo delle produzioni storiche non e' letto**: l'OCR mescola le colonne (nomi e ruoli in ordine sparso); il testo grezzo resta nella colonna `interpreti_grezzo`. Per averlo servirebbe l'hOCR con le coordinate (non scaricato). Tre produzioni (Rosenkavalier 1976, Elisir 1958 e 1970) non hanno direttore perche' il blocco delle etichette e' fuori posto nel testo.
Licenza: libri delle Edizioni del Teatro alla Scala caricati su IA da un utente, senza licenza dichiarata: si usano solo fatti (titolo, data, direttore, regia, solisti), citando il programma; niente testi ne' pagine.

### 3. Registrazioni dal vivo alla Scala: tutte le schede SBN
Programmi: `scripts\sbn_registrazioni_tutte.py` (scarica la scheda completa dei ~2.600 candidati ancora mancanti; stesso cliente educato di `sbn_lib`: 1 richiesta ogni 3 s, cache in `raw\sbn\full`, riprendibile, UN SOLO processo; lanciato in background dopo il download IA) e `scripts\sbn_registrazioni.py` (riscritto) -> `sbn\sbn_registrazioni.csv` (solo esecuzioni al Teatro alla Scala) e `sbn\_registrazioni_tutte_schede.csv` (tutte le schede lette, con la colonna `esclusa` che dice perche'). Copia della versione di ieri: `sbn\_sbn_registrazioni_v1_backup.csv`.
Esito: download finito alle 10:55 (2.581 schede nuove in circa 2 h 20, nessun blocco ne' CAPTCHA, un solo timeout con ripresa automatica); in cache ora 2.785 schede complete di registrazioni sonore su 2.994 candidati (le altre 209 non sono registrazioni sonore musicali). Regole di filtro (in `sbn_registrazioni.py`): si tiene una scheda se e' dal vivo (dal vivo / live / in diretta / registrazione storica / inedita effettuata dal vivo) E il luogo e' il Teatro alla Scala (nota "Teatro alla Scala", "alla Scala di Milano": **esplicito**) oppure "Milano" con orchestra o coro della Scala e nessun altro luogo (**probabile**); si scartano studio, altri luoghi (Salisburgo, Monaco, Roma...), antologie senza luogo.
Risultato: **111 esecuzioni dal vivo alla Scala** (66 con luogo esplicito, 45 probabili): **68 con il giorno**, 9 con il mese, 27 solo con l'anno, 7 senza data; direttore in 89, interpreti (nomi, con la voce quando la scheda la da') in 76, compositore in 66. Per decennio (con data): anni '50 51, '60 27, '70 5, '80 7, '90 14. Esempi: Walkure 9/3/1950 (Furtwangler), Falstaff 26/5/1951 (De Sabata), Macbeth 7/12/1952, Alceste 4/4/1954 (Giulini), Anna Bolena 14/4/1957 (Gavazzeni), Lucia di Lammermoor 7/12/1967 (Abbado), L'assedio di Corinto 14/4/1969 (Schippers), Boris Godunov 7/12/1978 (Abbado), Rigoletto 13/5/1994 (Muti). Prima erano 25 date: **ora 68 (e solo 3 coincidono con una data gia' nei programmi di sala SBN)**.
Cast per ruolo: le schede SBN danno i NOMI con l'etichetta [Cantante]/[Interprete] (a volte la voce), quasi mai il personaggio: nel csv ci sono i nomi, con la voce dove c'e'; il personaggio ("Nome (Ruolo)" nel titolo) e' nella colonna `ruoli_personaggi` ma e' rarissimo.
Non tenute (in `_registrazioni_tutte_schede.csv`, colonna `esclusa`): 2.422 non dal vivo e senza luogo Scala (antologie, ristampe, incisioni in studio), 145 "registrate alla Scala" ma senza scritto "dal vivo" (**dubbie: possono essere sedute di studio nel teatro o riprese di recite**: es. Traviata Muti 1992, Rigoletto 1994 in un'altra edizione, Medea 1957; se Davide le vuole, vanno guardate a mano), 33 live senza luogo (Muti 2003-2007: Moise et Pharaon, Carmelites, Idomeneo...), 27 con luogo non indicato, 24 studio, 23 altro luogo.
Nel cartellone entrano solo le righe con luogo esplicito o probabile E almeno l'anno: **98 righe** (`fonte = sbn_registrazioni`; affidabilita alta se giorno + luogo esplicito, media altrimenti); "concerto (registrazione dal vivo)" per sinfonie e messe, "opera (registrazione dal vivo)" per il resto. La data e' quella della serata registrata, non della produzione intera.

### Unione nella pagina
`scripts\costruisci_cartellone.py` (ora legge anche `_cambiasi_balli.csv`, `ia_programmi_*.csv`, `sbn\sbn_registrazioni.csv`; con i dati di ieri riproduce identico `cartellone.csv`: verificato prima di toccarlo) e `scripts\pagina_dati.py` (due codici fonte nuovi: **I** programmi IA, **V** registrazioni SBN; nel grafico I e V contano nella classe "SBN"; i balli di Cambiasi contano nel grafico come balletti ma NON nelle classifiche delle opere) -> `docs\scala\data\*.json` rigenerati, `index.html` non toccato. `scripts\confronto_prima_dopo.py` mette a confronto i dati di ieri (`pulito\_backup_prima_balli\`) con quelli di oggi.
Da sapere: nell'`index.html` restano due frasi scritte a mano che ora sono superate (non toccate per la regola "niente layout"): "nel Cambiasi, 1778-1881, ne contiamo in media 17 per anno" (con i balli sono circa 26) e la legenda "Programmi di sala SBN (1963-2024)" che ora comprende anche IA e le registrazioni.
Per rifare tutto (dalla cartella scala/): `python -I -X utf8 scripts/parse_cambiasi_balli.py raw/cambiasi/teatroallascala100camb/teatroallascala100camb_djvu.txt pulito/_cambiasi_balli.csv ; python -I -X utf8 scripts/ia_programmi_estrai.py ; python -I -X utf8 scripts/sbn_registrazioni.py ; python -I -X utf8 scripts/costruisci_cartellone.py pulito ; python -I -X utf8 scripts/pagina_dati.py`.

### Copertura nuova (dati della pagina, `confronto_prima_dopo.py`; righe = titoli per anno, senza i concerti)
| Periodo | Righe prima -> dopo | Con giorno | Con direttore | Con regia | Con interpreti |
|---|---|---|---|---|---|
| 1946-1963 | 326 -> 356 | 136 -> 164 | 87 -> 115 | 52 -> 64 | 45 -> 67 |
| 1964-2022 | 950 -> 962 | 771 -> 787 | 282 -> 308 | 428 -> 440 | 125 -> 147 |
| 1946-2022 | 1.276 -> 1.318 | 907 -> 951 | 369 -> 423 | 480 -> 504 | 170 -> 214 |
Balli 1778-1881: da 55 (sola Wikipedia/Wikidata/SBN) a **864 balli nella pagina** (871 righe nel cartellone), 104 anni su 104, **8,4 balli per anno** (2-16). Titoli totali della pagina 4.636 -> 5.502. Il guadagno dopo il 1946 viene soprattutto dalle registrazioni (date e solisti 1950-1969) e dai capitoli storici dei programmi IA (direttore e regia 1946-2009); il buco 1964-2022 (cast e giorno per giorno) resta quello descritto sopra.
Backup dei dati di ieri: `pulito\_backup_prima_balli\`.


---

# Prime di stagione (30/10/2026)
Cartella `pulito\`. Tabella `aperture.csv` (250 righe: 76 aperture dal 7/12/1951 al 7/12/2026 + 174 righe prima del 1951, colonna `blocco`), registro `aperture_differenze.md`, pagina `docs\scala\prime\` (dati in `data\aperture.json` e `statistiche.json`).

## Copertura
- **Prima:** 72 serate su 76 con data 7 dicembre nei dati (mancavano 2017, 2018, 2020, 2021). **Ora: 76 su 76** con titolo, compositore, data, direttore e regia. Il 2020 e' il gala televisivo «A riveder le stelle» (nessuna opera); il 2026 e' programmato (non ancora avvenuto al 30/10/2026).
- Direttore: 76 su 76 (1955 e 1959: Antonino Votto); confermato da 2+ fonti in 74 casi. Regia: 76 su 76. Cast: 42 su 76 (con ruoli per circa la metà). **Documentate a pieno (titolo, data, direttore 2+ fonti, regia, cast): 41.** Disaccordo non risolto: 1954 (direttore) e 1978 (inaugurazione o replica?).
- Prima del 1951: 174 righe (inaugurazione 3/8/1778 + stagioni 1778/79-1950/51). Affidabilita: alta 69, media 73, bassa 27, teatro chiuso 5 (1897/98, 1917/18-1920/21). Data del giorno per 95 righe; direttore per 79.

## Come e' fatta (scripts\)
`aperture_scarica.py` / `aperture_scarica_it.py` (wikitesto en/it di 45+ opere, raw\aperture_wp), `aperture_wikidata.py` (107 voci «serata inaugurale» con direttore P3300, regia P57, cast P161, raw\aperture_wikidata), `aperture_scala_vecchie.py` (prova di 16 indirizzi del sito Scala: solo la pagina del Boris 2022 esiste ancora; le altre 404 o pagina generica), `aperture_scala_cast.py` (ruolo per ruolo 2022-2026), `aperture_parse_wp.py` (lista it.wikipedia «Prime stagionali»), `aperture_pre1951.py` (primo incrocio), `aperture_costruisci.py` (tabella), `aperture_pagina.py` (json della pagina + differenze.md), `aperture_lib.py`.
Rifare: dalla cartella `scala\`: parse_wp, scala_cast, costruisci, pagina (nell'ordine; la rete serve solo per i primi tre).

## Trappole
- Lista WP e cronistoria SL (stessa Wikipedia) si contraddicono (1954 direttore; 1978; 2021 «4 dicembre»); Wikidata ha «serata inaugurale» al 26 dicembre anche dove la lista WP ha un'apertura a novembre (1923, 1928, 1930).
- Cambiasi: anno ricavato dal programma di lettura, in alcuni tratti sfalsato di uno (1861-1868); le righe ricostruite dal libro sono OCR («A demira»).
- SBN: «Franco Cordelli» (1960); registrazione del Boris datata 7/12/1978 mentre la Scala data il Boris di Abbado al 1979. it.wikipedia «L'amico Fritz»: «7 dicembre 1962» (refuso per 1963).
- Arcimboldi: solo 2002 e 2003 (il 2004 e' la riapertura del Piermarini), non 2002-2004 come scritto nel mandato.
- Cast dalla stampa (2007-2009, 2013, 2014, 2016-2019, 2021): fonti web citate nella colonna `controlli` di aperture.csv; i ruoli mancano dove non li dice la fonte. Operadis e' stato usato solo per controllo (colonna locale in `_aperture_cast_operadis_LOCALE.csv`, mai nel json).
- menu.js: la sezione corrente ora si riconosce anche dalle sottopagine (`scala/prime/`).
