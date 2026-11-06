# Impianti sportivi: note (2 novembre 2026)

Cartella `sport/`. Pagina: `docs/sport/index.html`. Regola: ogni numero dice da quale file viene; i conti si rifanno con i programmi in `scripts/`.

## In breve
1. **Non esiste un elenco unico e aggiornato.** Ho unito 5 fonti di anni diversi (2011-2026). Risultato: 851 "impianti" dentro il Comune (più 593 "campi liberi" in giardini e cortili), circa 6,1 impianti ogni 10.000 abitanti (`pulito/citta_sport.json`).
2. **Il 99,2% dei residenti arriva a piedi in 15 minuti a un impianto, ma solo il 62,2% a una piscina** (48,4% a una piscina comunale, 36,6% a un impianto Milanosport).
3. **Solo 124 impianti su 851 (14,6%) sono del Comune** (23 Milanosport, 93 in concessione ad altri, 8 da verificare); 196 sono palestre di scuole; 510 "non risultano comunali" (non vuol dire privati).
4. **Le fonti concordano poco sul singolo quartiere** (Spearman tra le classifiche per NIL: 0,37-0,63); 411 impianti su 851 sono in una sola fonte. La pagina è più sicura sui totali di città che sul singolo quartiere.
5. Censimento Sport e Salute/CONI: **non aperto** (solo schede regionali in PDF); anagrafe regionale degli impianti: accesso riservato ai referenti dei Comuni (pagina regione.lombardia.it, letta il 2/11/2026). Non usati.

## Fonti (tutte scaricate il 2/11/2026; log in `raw/download_log.csv`)
| Fonte | id | Licenza | Anno dei dati | Uso |
|---|---|---|---|---|
| Comune, impianti sportivi (punti) | ds34 | CC BY | **dichiarato 31/1/2011** (metadati `temporal_coverage`); file 2020-2023 | base: 1.041 righe (una per disciplina) = 357 punti |
| Comune, impianti in concessione | ds2941 | CC BY | 28/2/2025 | 130 righe (2 aree parcheggio scartate); campo `Denominazione Concessionario`: 23 Milanosport |
| Comune, centri balneari/piscine | ds32 | CC BY | 2011-2017 | 28 righe, tutte piscine |
| Comune, campi nei giardini (poligoni) | ds1640 | CC BY | 31/10/2024 (righe 2000-2024) | 502 poligoni, 58 piste ciclabili escluse = 444 campi |
| Comune, spazi scuole statali | ds1867 | "altro (attribuzione)" | a.s. 2020/21 | 81 edifici con palestra o piscina |
| Comune, Milanosport 2019 / 2018 | ds1491 / ds292 | CC BY | 2019 / 2018 | solo controllo dei nomi (22 complessi; senza coordinate) |
| Regione Lombardia, elenco centri sportivi georef | qkfs-wmmh | CC0 | aggiornato 14/4/2016 | 459 righe "MILANO", 456 con coordinate, 417 dentro il Comune (39 con coordinate fuori: scartate) |
| OpenStreetMap (Overpass) | - | ODbL | 2/11/2026 09:28 UTC | `leisure=sports_centre/pitch/swimming_pool/fitness_centre/sports_hall/stadium/ice_rink/track/golf_course/horse_riding`, `amenity=gym`: 4.282 elementi nel rettangolo 45,36-45,56 / 9,00-9,32 |

Non usati: ds632 "street sport" (2018, parchi con orari, 217 aree: già coperti da ds1640), presenze Milanosport 2010-2019 (niente coordinate).
Confini NIL (ds964), residenti 2025 (ds27), civici (ds634) e rete pedonale: da `citta-15-minuti/` (scaricati il 29/10/2026), solo letti.

## Regole di costruzione (scripts/build.py)
- **Luogo** = punti di fonti diverse a meno di 80 m (o con lo stesso numero civico e nome via entro 350 m; `addrkey`) contati una volta. Priorità: ds34, ds2941, ds32, ds1867, ds1640, Regione, OSM centri/piscine/palestre, OSM campi (raggruppati a 30 m). **Sensibilità:** impianti 948 a 50 m, 851 a 80 m, 673 a 150 m (`pulito/build_log.json`).
- **Impianto** = luogo con almeno una fonte fra ds34, ds2941, ds32, ds1867, Regione, OSM centri; gli altri (solo ds1640 o campi OSM) sono "campi liberi".
- **Tipo** (etichette multiple): piscina, palestra/fitness, campo/palazzetto, centro (3 o più discipline o "CENTRO SPORTIVO"). Mappa discipline -> tipo in `build.py` (`PISC`, `PAL`, testo libero per ds2941 e Regione).
- **Gestore** (una sola classe, la più forte vince): `milanosport` (concessionario Milanosport in ds2941), `comune_concessione` (altri concessionari ds2941), `comune_da_verificare` (Milanosport o Comune solo secondo ds34, per URL milanosport.it o nome "Milano Sport Spa", e ds32), `comune_libero` (ds1640), `scuola` (ds1867 o nome Regione con SCUOL/ISTITUTO/LICEO), `altro`. "Altro" = **non risulta comunale**: non è una prova di proprietà privata né di accesso a pagamento.
- **OSM:** piscine solo con nome (piscina/nuoto/pool/acqua/club/terme...) e `access` diverso da private/no/customers/members/permit; campi `pitch` senza accesso privato (2.746 su 2.886); fitness_centre e sports_hall sono "palestra"; nessun elemento OSM ha un gestore (tutti "altro", salvo l'unione con altre fonti).
- Posizione delle sedi olimpiche da OSM per nome (`scripts/olimpiadi_osm.py`, `raw/osm/overpass_olimpiadi*.json`).

## Accesso a piedi (scripts/analisi.py)
Identico a `citta-15-minuti/scripts/f4_tempi.py`: 57.405 civici, rete pedonale OSM (Geofabrik 29/10/2026), 4,5 km/h, Dijkstra multi-sorgente con distanza di aggancio, tetto 3.200 m, soglia 15 minuti, residenti 2025 per NIL distribuiti in parti uguali sui civici residenziali (1.399.079 in totale, controllato). Luoghi usati: quelli dentro il Comune + 200 m, a meno di 150 m dalla rete (9 scartati). Gruppi: tutti, piscine, palestre, campi, comunali, Milanosport, campi liberi del Comune, scuole, altro, piscine comunali.

## Risultati principali (`pulito/citta_sport.json`, `pulito/nil_sport.csv`)
- Per 10.000 abitanti (città): tutti 6,06; piscine 0,44 (62 piscine); palestre 3,53; comunali 0,89; Milanosport 0,16.
- Residenti entro 15 minuti: tutti 99,2% (mediana 3,8 min); palestre 97,9%; piscine 62,2% (12,7); comunali 89,4% (9,5); piscine comunali 48,4%; Milanosport 36,6% (18,2); scuole 96,4%; campi liberi del Comune 95,7%.
- 75 NIL con almeno 1.000 residenti: 4 senza nessun impianto (Tre Torri, Triulzo Superiore, Chiaravalle, Monlue' - Ponte Lambro), 20 senza impianti comunali, 36 senza piscina. Mediana 6,2 impianti ogni 10.000. In cima Parco Forlanini - Cavriano 31,8 e QT 8 25,1 (grandi centri su pochi abitanti). I 10 NIL con più impianti hanno il 26,2% del totale. Correlazione con il punteggio "15 minuti" della fase 2: -0,17 (nessun legame).
- Duomo (15.892 residenti): 21 impianti, 0 comunali (18 non comunali, 3 scuole).
- Olimpiadi: San Siro (NIL Stadio - Ippodromi, 17 impianti), Arena Santa Giulia (NIL Taliedo - Morsenchio - Q.re Forlanini, 16), villaggio di Porta Romana (Scalo Romana, 4 impianti, 3,3 ogni 10.000). Rogoredo - Santa Giulia: 0% dei residenti a 15' da una piscina nei dati. Fatti sulle sedi: Wikipedia "2026 Winter Olympics" (2/11/2026), Il Post 25/9/2026 (arena solo concerti, Europei di pallavolo spostati ad Assago), Il Giorno 21/12/2025 (villaggio -> studentato da 1.700 posti).

## Limiti (elenco completo nella pagina)
Anni diversi (ds34 è del 2011); poche fonti per luogo; "non risulta comunale" non vuol dire privato; palestre di scuole non aperte a tutti; nessun orario né prezzo; niente impianti fuori dal Comune; ds1867 solo statali 2020/21; la regola degli 80 m cambia il totale (673-948); quartieri piccoli (sotto i 1.000 residenti) fuori classifica; 39 coordinate Regione sbagliate; 8 luoghi "da verificare"; non ho letto il sito di Milanosport; OSM può mancare di impianti o avere campi in cortili privati senza il tag access.

## Palestre private: prova sulle catene (4 novembre 2026)
Programma `scripts/prova_catene.py`: sedi nel Comune copiate dai siti di 5 catene (Virgin Active, McFit, Urban Fitness, GetFit, FitActive) contro OpenStreetMap del 2/11/2026 e contro `pulito/siti.csv`. Trovata = punto con il nome della catena entro 300 m dal civico, o dalla via se il sito non dà il numero (GetFit, FitActive, tre sedi di altre catene).
- 31 sedi su 41 trovate (76%), uguale su mappa e pagina: Virgin Active 11/12, McFit 2/3, Urban Fitness 8/14, GetFit 8/8, FitActive 2/4. Con una palestra qualsiasi entro 100 m: 34 su 41.
- Mancano: Virgin Active via Cena; McFit Fulvio Testi; Urban Fitness Carlo Erba, Coni Zugna, Piranesi, Rubens, Sabotino, Cinque Giornate; FitActive Ripamonti, Sismondi.
- Il contrario esiste: Urban Fitness in via Circo è sulla mappa ma non sul sito della catena. La mappa può conservare sedi chiuse.
- Limiti della prova: le catene sono le più facili da mappare, quindi il 76% non vale per le palestre indipendenti, che non hanno un elenco con cui confrontarle. Solo 5 catene scelte da me; il raggio sulla via è largo per le vie lunghe.
- Riferimento ufficiale ma vecchio: sedi di impresa con codice 93130 "Gestione di palestre", Comune ds170 e ds201: 134 nel 2007, 118 nel 2010, per quartiere nel 2010 (Magenta-San Vittore 10, Brera 9, Guastalla 7). Non comprendono le associazioni sportive (ds274: almeno 1.200 sedi non profit di attività sportive, anno non verificato). Nessun numero ufficiale attuale trovato.

## Licenze e ripubblicazione
Il file dei luoghi (`docs/sport/data/siti.csv|json`) contiene dati OSM: va ripubblicato con ODbL; dati Comune CC BY (ds1867 attribuzione); Regione CC0. Telefoni, email e persone non sono ripresi (il nome del luogo è il campo `Nome` di ds34, cioè società o centro).

## Cose non fatte
- Verifica con il sito di Milanosport, con le piante organiche delle scuole e con Sport e Salute.
- Reddito per CAP (gli impianti sono per NIL).
- Distinzione coperto/scoperto; orari e tariffe.
- Esagoni 100 m per l'accesso (solo NIL).

## Piscine "solo per iscritti" (6 novembre 2026, richiesta di Davide: "la Virgin in Duomo non la conta")
Prima le piscine OSM con access=customers/members/private erano tutte escluse. Ora sono una categoria a parte, mai mischiata con le "aperte a tutti" (62 nei dati).
**Regola** (scripts/tempi_a_piedi.py):
- piscine OSM (leisure=swimming_pool) dentro il Comune con access=customers/members/permit; oppure senza access ma a meno di 80 m da una palestra/centro sportivo/circolo con nome (virgin, aspria, club, tennis, sporting, fitness, wellness, palestra, gym) non segnato private/no;
- **sempre escluse** le piscine access=private o no (condomini, case, alberghi chiusi), anche se vicine a un circolo;
- non si contano due volte: a meno di 80 m da una piscina gia' aperta a tutti, o da un'altra "per iscritti" (si tiene quella con nome);
- 8 sedi Virgin Active dove la pagina del club (virginactive.it/club/milano-..., letta il 6/11/2026) dice che c'e' una piscina: Cavour, Corso Como, Vittorio Emanuele, Bocconi (era gia' tra le aperte, a meno di 80 m: non aggiunta), Bicocca, Kennedy, Maciachini, Piazzale Lodi. Dal sito si usa solo il si'. Corso Vercelli e Diaz: non chiaro; Porta Vittoria e Citta' Studi: pagina 404; non contate. Altre catene non controllate.
**Risultato:** 15 piscine aggiunte: Aspria Harbour Club, Tennis Club Ambrosiano, Tennis Club Lombardo, 7 Virgin Active (Vittorio Emanuele, Cavour, Corso Como, Bicocca, Kennedy, Maciachini, Piazzale Lodi), 5 piscine senza nome segnate "solo clienti" (2 Parco Bosco in citta', 2 Lorenteggio, 1 Porta Romana; potrebbero essere di alberghi o residence).
Minuti a piedi, residenti entro 15': aperte a tutti 62,2% (mediana 12,7 min); anche per iscritti 65,0% (12,2 min); solo le 15 per iscritti 16,8% (26,9 min). Dati in docs/sport/data/sport_tempi.json (campo `iscritti` con la lista).
Dubbio aperto: tra le "aperte a tutti" ci sono 5 piscine di scuole (ds1867), non davvero aperte.
