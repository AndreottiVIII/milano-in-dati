# Parchi e verde, quartiere per quartiere (verde/)

Scaricato il 1-2 novembre 2026. Pagina: `docs/verde/index.html` (dati in `docs/verde/data/`). Ogni numero ha file e campo nei `pulito/*.csv|json` e in `docs/verde/data/riepilogo.json`. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorsi assoluti>` (vedi STATO.md). `raw/` = dati grezzi non fidati (mai eseguiti).

## 1. In breve
1. **Non esiste una mappa completa e aggiornata del verde pubblico di Milano.** Le fonti aperte del Comune (CC BY) sono due, incomplete: i poligoni di "parchi e giardini" (ds89: 74 parchi con nome in 1.065 pezzi, 7,36 km² dopo l'unione, nessun anno) e l'elenco "aree verdi per zona e superficie" (ds339, dato 2014: 2.917 aree, 22,4 km², nessuna geometria).
2. **Stima B (quella mostrata)** = poligoni ds89 + aree ds339 delle classi ISTAT 1 (verde attrezzato), 2 (parchi urbani), 3 (verde storico) non disegnate, collocate nei NIL con gli alberi del censimento 2025 (stesso codice zona_area). Città: **15,07 km², 10,7 m² per abitante, 8,3% della superficie**. **44 dei 64 NIL con almeno 5.000 residenti sono sotto i 9 m² (73,5% dei residenti), mediana 6,0, 11 sotto i 2, 19 sotto i 3.** Senza i 4 parchi sopra i 40 ha (Cave, Trenno, Forlanini, Lambro): 7,3 m² e 47 NIL sotto i 9.
3. **Stima A (solo poligoni)**: 7,36 km², 5,2 m² per abitante, solo 5 NIL su 64 sopra i 9: troppo incompleta per giudicare.
4. **Controlli**: la serie del Comune ds1323 dà per il 2014 16,83 km² per le stesse categorie (parchi, ville, verde attrezzato, aree naturali protette, forestazione), contro i 16,45 km² delle classi ISTAT 1-3 di ds339; OpenStreetMap `leisure=park` dentro Milano = 14,88 km² (10,6 m² per abitante), Spearman fra NIL con B +0,84 (con A: +0,45). OSM non è un controllo del tutto indipendente (include aree non comunali).
5. **Distanza dal parco** (riuso del calcolo di `citta-15-minuti/`, 81 parchi di almeno 5.000 m² di ds89): mediana 8,7 minuti a piedi (circa 650 m); entro 5 / 10 / 15 minuti 23% / 59% / 83% dei residenti; 234.830 residenti oltre 15 minuti.
6. **Nel tempo (solo città)**: ds1323 parchi e verde attrezzato 15,96 km² (2011), 16,83 (2014), 19,33 (2024): +2,49 km² (+14,8%) dal 2014, non collocati nei NIL (la stima si ferma al 2014). ISTAT (ds2926/ds2927, tavole 12.1 e 11.1): 17,2 -> 18,8 m² per abitante 2011-2023; 12,0% -> 14,1% della superficie. Per NIL non c'è nessun anno di apertura: solo le "schede" (`data_ini`) di aree gioco, cani, orti, giardini condivisi.
7. **Legame con altri indicatori** (Spearman fra NIL, IC 95% in `pulito/confronti.json`): m² per abitante (B) contro suolo consumato 2025 -0,78; calore (indice SPOTTED ds2811, luglio 2024) -0,66; densità di abitanti -0,62; alberi per 1.000 abitanti +0,75 (in parte costruito: B è collocato con gli alberi; con A +0,43).

## 2. Fonti e licenze (scaricate in `raw/`, log in `raw/download_log.csv`)
| Dato | Id Comune | Licenza | Scaricato | Nota |
|---|---|---|---|---|
| Parchi e giardini (poligoni) | ds89 `parchi.geojson` (+ `parchi_4326.csv` centroidi) | cc-by | 2/11/2026 | frequency NEVER; GeoJSON caricato 6/5/2024, CSV/SHP 2/3/2021; anno dei dati non dichiarato |
| Aree gioco | ds724 | cc-by | 2/11/2026 | 983 poligoni, risorsa 25/11/2024 |
| Aree fruizione cani | ds52 | cc-by | 2/11/2026 | 423 poligoni, risorsa 21/11/2024 |
| Giardini condivisi | ds2187 | cc-by | 2/11/2026 | 15 poligoni |
| Orti urbani | ds2186 | cc-by | 2/11/2026 | 181 poligoni |
| Esposizione al calore NIL (SPOTTED, luglio 2024) | ds2811 | cc-by | 2/11/2026 | metodo su portale con registrazione, non letto |
| Aree verdi per zona e superficie 2014 | ds339 | cc-by | 1/11/2026 (filone alberi) | CSV latin-1, decimali con virgola |
| Verde urbano 2011-2024; mq per abitante; incidenza | ds1323, ds2926, ds2927 | cc-by | 1/11/2026 (filone alberi) | ds2926/2927 riprendono ISTAT tavole 12.1 e 11.1; ISTAT non scaricato |
| Alberi 2025, residenti, NIL, suolo, tempi a piedi | filoni alberi, citta-15-minuti, suolo | cc-by | - | riusati, non rifatti |
| OpenStreetMap leisure=park/garden/playground/dog_park | Overpass (overpass.kumi.systems, 2/11/2026 09:33 UTC; overpass-api.de ha dato 502) | ODbL | 2/11/2026 | solo controllo; non ripubblicato |

**Standard (verificato il 2/11/2026 sul testo trascritto da bosettiegatti.eu, pagina "Decreto interministeriale 2 aprile 1968, n. 1444")**: è un decreto interministeriale (non un "DM" semplice). Art. 3: per gli insediamenti residenziali dotazione minima di 18 m² per abitante "insediato o da insediare" di spazi pubblici o riservati ad attività collettive, verde pubblico o parcheggio; lettera c) **9,00 m² "di aree per spazi pubblici attrezzati a parco e per il gioco e lo sport, effettivamente utilizzabili per tali impianti con esclusione di fasce verdi lungo le strade"**; a) 4,50 istruzione, b) 2,00 interesse comune, d) 2,50 parcheggi. Art. 4 n. 2: nelle zone A e B le aree contano in misura doppia. Vale per i piani, non è un esame per quartiere. Pubblicazione in G.U. n. 97 del 16/4/1968 (da una seconda fonte, Edizioni Europee; non controllata sulla G.U.). Un primo tentativo su normattiva con un URN sbagliato ha restituito un altro atto: ignorato.

## 3. Metodo (scripts/build.py, risultati in `pulito/controlli.json`)
- NIL: 88 poligoni vigenti (ds964, `citta-15-minuti/raw/comune_milano/nil_vigenti/`), UTM 32N; superficie dai poligoni (181,76 km²; controllo contro `alberi/pulito/nil_alberi.csv`); residenti ds205 2024 (1.407.044).
- **A**: i 1.065 pezzi di ds89 (area calcolata in metri = `AREA_MQ` del file, mediana 1,0000, un solo pezzo oltre l'1%) uniti per `ZONA_CODICE_ARE` (74 parchi) e poi tutti insieme (le sovrapposizioni contano una volta: somma dei pezzi 7,737 km², unione 7,360); intersezione con ogni NIL.
- **B**: A + ds339 classi 1-3 (957 aree, 16,45 km²; 72 sono già in ds89; restano 885 aree, 8,99 km²). Collocazione: (1) 843 aree (6,21 km²) con alberi 2025 con lo stesso `id_area` = `Zona_Area` di ds339: superficie 2014 divisa fra NIL in proporzione agli alberi; (2) 3 aree con un poligono di gioco/cani/orti con lo stesso id_area; (3) **39 aree, 1,28 km², non collocate** (la prima è il Bosco in città, 7_402, Italia Nostra, 118 ha nel 2014; OSM ne disegna 56 ha, quasi tutti nel NIL "Parco Bosco in città", 666 residenti). **Prova del metodo**: sui 71 parchi ds89 che hanno anche alberi, il 95,2% della superficie finisce nel NIL giusto. 63 aree finiscono su più NIL. Un'area (9_234, viale Sarca - Silvestri) non ha la superficie nel file: conta 0.
- Escluse: classe 4 (arredo urbano, 3,47 km²), 5a (giardini scolastici), 5b, 5d (cimiteri), 5e (sport), 5f (edifici pubblici). Sono scelte mie, coerenti con "con esclusione di fasce verdi lungo le strade" ma non identiche al testo del decreto: la classe "verde attrezzato" contiene anche piccoli giardini e non separa i campi sportivi.
- "Senza i grandi parchi" = senza i parchi con almeno 40 ha (ds89: Cave 142 ha, Lambro 77, Trenno 59, Forlanini 55; per le aree solo ds339, quelle con almeno 40 ha).
- **Distanza**: `citta-15-minuti/out/civici_tempi.csv`, campo `min_parchi`, civici residenziali (46.895; 1 senza NIL scartato; 153 senza tempo = "oltre il limite"). Quote per NIL = quota di civici (ogni civico pesa uguale dentro il NIL); città = peso NIL (residenti 2024 / civici).
- **Schede per anno**: `data_ini` dei poligoni gioco/cani/orti/condivisi per anno e per NIL (punto rappresentativo del poligono).
- **Confronti**: Spearman con IC 95% da 5.000 ricampionamenti (seme 1) dei NIL: 64 NIL con almeno 5.000 residenti per i valori per abitante, 88 per le quote di superficie.

## 4. Difetti dei dati verificati (alla pagina: "Limiti dei dati")
1. ds89 non ha anno; i suoi 74 parchi sono tutti anche in ds339 (2014): non è più recente. 1.065 pezzi, 737 sotto i 500 m², molti sovrapposti.
2. ds339 è del 2014 e senza mappa; il Comune conta +2,49 km² di parchi e verde attrezzato dal 2014 al 2024 (ds1323) che non sono collocati.
3. ds1323: la riga 2018 "Gestione Comunale;Verde attrezzato;6534108;972" ha un campo in più (letto il primo valore; non verificabile se fosse una virgola decimale sbagliata); il 2024 ha 6 valori vuoti (aree naturali protette, orti urbani, altre tipologie, per i due tipi di gestione).
4. ds339: 1 area senza superficie.
5. `data_ini` 2003: 22% delle aree gioco e 18% delle aree cani (importazione dell'archivio, ipotesi).
6. ds205 ha le superfici scambiate per 3 NIL (già in `alberi/NOTE.md`): usati i poligoni.
7. Parchi con pochi residenti (Parco Nord 100, Sempione 0, Forlanini 2.675...): fuori classifica; i 24 NIL sotto i 5.000 residenti tengono il 31,9% del verde B.
8. Gratosoglio: 18 m² per abitante (B) ma 29 minuti dal parco più vicino (gli 81 parchi sono solo quelli disegnati: manca il Parco Agricolo Sud). Quantità e vicinanza usano insiemi di parchi diversi.
9. SPOTTED (calore, verde): indici da satellite, metodo su portale con registrazione (non fatta). Il legame verde-calore può essere in parte scontato.
10. B è collocato con gli alberi: il legame con gli alberi è in parte costruito (con A più debole, +0,43).

## 5. Cosa non ho fatto
Nessun account, nessun aggiramento. Non ho scaricato ISTAT (le tavole 11.1 e 12.1 sono usate tramite le copie del Comune: la licenza ISTAT CC BY 4.0 non è stata verificata qui). Non ho aggiornato con i parchi dopo il 2014 (nessuna fonte aperta con anni di apertura trovata). Non ho usato Copernicus Urban Atlas (login). Non ho calcolato il tempo a piedi verso le aree dell'elenco 2014 (senza geometria).
