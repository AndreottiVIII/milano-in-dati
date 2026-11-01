# Quanto si vive - FASE 1 (fonti, scarico, pulizia, stime) + pagina

Scaricato il 1 novembre 2026. Programmi in `scripts/` (si lanciano con `python -I -X utf8 scripts/<nome>.py <percorsi assoluti>`, vedi STATO.md). File grezzi in `raw/` (non fidati, mai eseguiti), tabelle in `pulito/`, pagina in `../docs/speranza-vita/`. Ogni numero qui sotto sta in un file di `pulito/` o in `docs/speranza-vita/data/riepilogo.json`.

"Quartiere" = NIL (88 Nuclei d'Identita' Locale vigenti). "SMR" = rapporto standardizzato di mortalita' (decessi osservati / attesi per l'eta', citta' = 1). "e0" = speranza di vita alla nascita **stimata** (non misurata).

## 1. In breve

1. **Sotto il livello di citta' ci sono dati aperti solo sui decessi per quartiere SENZA eta'.** Comune di Milano (CC BY): ds137 (2003-2020) e ds1940 (2021-2024), decessi dei residenti per NIL x sesso x cittadinanza; ds131 (2003-2020) e ds1937 (2021-2024) per Municipio. L'eta' dei decessi e' solo per la citta' (ds1938 2021-2024; ds338 2012-2013 a eta' singola; ISTAT 2011-2026). Nessuna tavola di mortalita' per quartiere o Municipio, ne' del Comune ne' di ATS ne' di ISTAT (ISTAT/Bes: solo province e regioni).
2. **Metodo**: standardizzazione indiretta. Tassi per eta' della citta' (22 classi ISTAT) applicati ai residenti per NIL x eta' x sesso (ds27) danno i decessi attesi; SMR = osservati/attesi; la speranza di vita del NIL = tavola abbreviata della citta' con tassi moltiplicati per l'SMR (stessa distanza proporzionale a ogni eta'). Intervalli: Poisson esatto (Garwood).
3. **Citta'** (`citta_e0_finestre.csv`, `citta_e0_annuale.csv`): e0 stimata 84,0 (uomini 81,6, donne 86,1) nel 2012-2019 e 84,7 (82,5 / 86,6) nel 2022-2024; 2019: 84,6, 2020: 82,5, 2024: 85,2. **Controllo**: ISTAT/Bes provincia di Milano 2019 84,2 (82,2 / 86,3), 2024 84,7 (82,7 / 86,7); l'accordo e' entro 0,5 anni.
4. **Differenze tra NIL** (`nil_smr_e0.csv`, 2012-2019, tutti i sessi): tra i 56 NIL con almeno 10.000 residenti, da 85,6 (Pagano) a 82,1 (Lambrate-Ortica): 3,5 anni. Altri in alto: Porta Vigentina 85,6, Duomo 85,5, Guastalla 85,4; in basso: Quarto Oggiaro 82,3, Barona 82,3, Lodi-Corvetto 82,7. Tra i NIL con almeno 3.000 residenti, 25 su 70 hanno SMR chiaramente sotto 1 e 16 chiaramente sopra (intervallo 95% che esclude 1).
5. **Ricchi e poveri** (`gruppi_reddito.csv`): cinque gruppi di NIL (>= 3.000 residenti) per reddito medio 2024 per CAP, ciascuno con circa un quinto dei residenti. Divario tra il quinto piu' ricco e il piu' povero nella e0 stimata: **1,7 anni** (84,9 contro 83,2) nel 2012-2019 e 1,7 (85,6 contro 83,9) nel 2022-2024; **uomini 2,2 (2,4 nel 2022-2024), donne 1,3 (1,0)**. Rapporto dei rischi 1,20 (intervallo 1,18-1,22). Correlazione di Spearman reddito-SMR tra NIL: -0,60 (intervallo -0,76/-0,40, 70 NIL): il reddito "spiega" circa un terzo.
6. **Stabilita'**: la classifica dei NIL e' quasi la stessa nel tempo (Spearman 0,81 tra 2012-2015 e 2016-2019; 0,75 tra 2012-2015 e 2022-2024; 0,79 tra 2016-2019 e 2022-2024) e il divario ricchi-poveri non si chiude (1,8 / 1,7 / 1,7 anni nelle tre fasi).
7. **Sorpresa (da pagina)**: il divario e' soprattutto maschile, e il reddito (per CAP) spiega solo una parte; la geografia della mortalita' e' persistente anche attraverso il Covid. Esempi fuori linea: Muggiano (reddito basso, SMR 0,79) e Lambrate-Ortica (reddito medio, SMR 1,22).
8. **Municipi** (`municipi_smr_e0.csv`): differenze piu' piccole (e0 da 83,7 nel 6 a 85,3 nel 1, 2013-2019).

## 2. Fonti e licenze (tutte scaricate il 1 novembre 2026)

- **Comune di Milano, dati.comune.milano.it, CC BY** (`license_id: cc-by` nel catalogo; versione non indicata): ds137 (decessi residenti per quartiere 2003-2020), ds1940 (2021-2024), ds131 (per Municipio 2003-2020), ds1937 (2021-2024), ds1938 (genere x eta' 2021-2024), ds338 (cause di morte, eta' singola, 2012-2013), ds337, ds222, ds1939, ds2918 (scaricati, non usati o solo per controllo). Residenti: ds27 (NIL x eta' x genere x cittadinanza 1999-2025, scaricato dal filone `popolazione/`) e ds29 (Municipio, idem). I campi sono quelli del file, ricondotti ai 88 NIL col nome (i file del Comune troncano a 50 caratteri due nomi lunghi: Niguarda..., Stadera...; 1-17 decessi l'anno hanno quartiere vuoto, 2003-2010 e 2024).
- **ISTAT, "Decessi e cause di morte: dati giornalieri comunali"**, release 25/8/2026 (dal filone `morti/pulito/decessi_giorno_eta_sesso.csv`, scope Milano, comune di residenza), CC BY 4.0 ("Salvo diversa indicazione...", note legali ISTAT).
- **ISTAT, Bes dei territori, indicatore 01SAL001 (Tavole di mortalita')**, edizione 2025, CC BY 4.0 (dal filone `benessere/`): e0 per provincia di Milano e Italia, 2004-2024. "Milano" = provincia / Citta' metropolitana, non il comune.
- **Reddito per NIL**: `quartieri-che-cambiano/out/indicatori_nil.csv` (colonna `reddito_2024`, MEF per CAP assegnato ai NIL con i civici). Solo come confronto: 38 CAP, quindi NIL dello stesso CAP hanno lo stesso valore.
- **ATS Milano**: nessuna speranza di vita per distretto o quartiere in formato aperto trovata (ricerca web, 2 ricerche + esame dei risultati). Atlante "Ricoveri e mortalita' a Milano 2005" (ASL Citta' di Milano, Servizio di Epidemiologia, Russo e Bisanti, Zadig 2005, PDF 337 pagine su ats-milano.it, copia in `raw/ats/`, **non ripubblicare**): mortalita' per 180 aree della citta' con SMR e un'associazione con il reddito ("il rischio di morte e' inversamente correlato al reddito; l'associazione e' piu' evidente negli uomini rispetto alle donne", sintesi del modulo "Tutte le cause", p. 41 del volume). Si cita solo qualitativamente come conferma dello stesso segno; i valori sono in grafici.
- **Citta' metropolitana di Milano, Osservatorio**: report "Mortalita 2020/2021" citati da una ricerca: i link diretti sono 404 o non raggiungibili; non letti.
- **ISTAT demo.istat.it, tavole di mortalita' per provincia**: non scaricate in modo diretto (il Bes contiene gia' la e0 provinciale); sotto il livello provinciale ISTAT non le pubblica.

## 3. Calcoli (`scripts/`)

- `search.py`: ricerca CKAN con 17 parole chiave (231 dataset distinti in `raw/ricerca/search_all.json`).
- `download_comune.py`: scarica i CSV dei dataset dei decessi (User-Agent dichiarato, nessuna registrazione, nessun aggiramento).
- `build.py`: `pulito/decessi_nil_anno_genere.csv` (anno, NIL, sesso, decessi, di cui italiani/stranieri), `residenti_nil_anno_cl_genere.csv` (31/12 per classe ISTAT), `decessi_citta_anno_cl_sesso.csv` (ISTAT), `controlli_build.json` (decessi NIL 2021-2024 = ds1938 esattamente; ISTAT vs Comune: 2012 -3,9%, 2013 -5,6%, 2014 -9,6%, 2015 -2,9%, 2019 -1,3%, 2020 +0,6%, 2021-2024 ~0).
- `analisi.py`: finestre 2012-2015, 2016-2019, 2012-2019, 2022-2024, 2020, 2021; anni-persona = media dei residenti 31/12 di y-1 e y (2012: solo 31/12/2012, per il salto del registro +24.579 tra 2011 e 2012); attesi riscalati in modo che il totale = decessi osservati del Comune (fattore 0,94 nel 2012-2015, 0,98 nel 2016-2019, 1,00 dal 2021); SMR e intervalli; e0 con tavola abbreviata (a0 Coale-Demeny; a(1-4); classi da 5 anni a meta'; ultima aperta 1/m); SMR "shrunk" (Poisson-gamma empirico, solo per ordine; tau 0,11-0,13) nel CSV ma non usato sulla pagina; gruppi di reddito; Spearman con 2.000 ricampionamenti; e0 annuale 2012-2024 della citta' con confronto Bes.
- `sensibilita.py`: (A) solo cittadini italiani: Spearman tra SMR di tutti e SMR italiani 0,994; reddito-SMR italiani -0,585; (B) senza Morivione: -0,611; (C) SMR quintili 1/5 invariati; (D) stabilita'; (E) quanti NIL sopra/sotto 1.
- `municipi.py`: stesso metodo per i 9 Municipi (ds131/ds1937 e ds29); windows 2013-2019 e 2022-2024.
- `pagina.py`: scrive `docs/speranza-vita/data/` (riepilogo.json, nil.geojson [geometrie semplificate lette da docs/alberi/data/nil.geojson], nil.csv, nil_finestre.csv, gruppi_reddito.csv, citta_anno.csv, municipi.csv, decessi_nil_anno_sesso.csv, correlazione_reddito.csv) con controlli interni (tutti "ok").

## 4. Limiti dei dati (anche sulla pagina)

1. **Niente eta' per NIL**: la e0 per NIL e' un modello (SMR costante a ogni eta'). Di solito i divari sociali sono piu' forti prima dei 75 anni che dopo gli 85: il divario vero e' probabilmente piu' grande di quello mostrato (e0 per NIL e per gruppi). Non verificabile con questi dati.
2. **Gli intervalli contano solo il caso (Poisson)**: non l'errore dei residenti o del modello. NIL sotto 3.000 residenti (18 su 88) non entrano nei confronti; Parco Sempione ha 0 residenti nel 2024.
3. **Registro, non censimento**: ds27 ha piu' residenti di ISTAT dal 2020 (+1,3% 2020, +2,7% 2025; popolazione/NOTE.md); gli anni-persona sono sovrastimati se i partiti non sono cancellati; il livello assoluto della e0 puo' risultarne gonfiato (confronto con Bes: +0,1 nel 2019, +0,5 nel 2024; la differenza e' anche di territorio, provincia contro comune).
4. **Convivenze/residenze per anziani non identificabili**: manca l'elenco con i posti letto (il dataset ds586 e' "RSA Aperta", 14 righe, una misura, non un elenco dei posti). **Morivione**: 7.722 residenti (2024), SMR 1,54 (2012-2019; intervallo 1,45-1,64), donne 1,68 contro uomini 1,30, quota 85+ 1,13 volte la media: eccesso di decessi che puo' dipendere da una residenza per anziani (ipotesi non verificata). Segnato "cautela" e escluso dai confronti sulla pagina; resta nei dati (e nei quintili, dove e' nel gruppo 3: tolto, i rischi dei gruppi 1 e 5 non cambiano). Il Gallaratese ha 1,76 volte la quota di over 85 senza eccesso di decessi.
5. **Reddito per CAP**: 38 CAP -> 88 NIL. Duomo, Brera, Guastalla, Porta Vigentina hanno CAP "instabili" per la variazione ma il valore 2024 c'e' (vedi quartieri-che-cambiano/NOTE.md). Solo confronto, non causa.
6. **Residenza, non luogo del decesso.**
7. **Comune vs ISTAT**: i decessi 2012-2019 del Comune sono sotto ISTAT (in media -6% nel 2012-2015, minimo -9,6% nel 2014, -2% nel 2016-2019): i tassi per eta' ISTAT sono riportati al livello del Comune (attesi riscalati). Dal 2021 coincidono.
8. **2003-2011 non usati**: i NIL esistono dal 2012 e non e' noto come il Comune abbia assegnato ai 88 NIL i morti e i residenti precedenti (stessa riserva di popolazione/NOTE.md); inoltre i tassi per eta' ISTAT iniziano nel 2011 e il registro ha salti.
9. **Covid**: 2020 (18.597 decessi del Comune) e 2021-2022 (SMR meno stabili): fuori dalla finestra principale; il 2020 compare solo nella tabella del divario.
10. **Cause di morte per NIL**: non esistono (ds337/ds338 sono per citta' e arrivano al 2013).
11. **Parole sulla pagina**: "limiti dei dati" (mai "trappole"); stima, non misura; niente cause, niente "il reddito fa morire".

## 5. Cosa NON e' stato fatto

- Nessuna e0 per NIL con l'eta' reale dei decessi (non esiste); nessun confronto con l'atlante ATS 2005 in numeri (valori nei grafici, copyright Zadig).
- Nessuna analisi per cause; nessun anno prima del 2012; nessuna scheda "Municipio x reddito".
- Possibile richiesta formale al Servizio statistica del Comune (milanostatistica.comune.milano.it) o all'ATS per i decessi per NIL x classi di eta': l'unica via per una e0 senza modello (decisione di Davide).
