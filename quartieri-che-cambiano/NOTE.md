# I quartieri che cambiano - FASE 1 (analisi, nessuna pagina)

Fatto il 1 novembre 2026, solo con dati già su disco negli altri filoni di "Milano in dati". Niente pagina web, nessun git, `JOURNAL.md` e `docs/` non toccati. Programmi in `scripts/` (Python 3.12, `python -I -X utf8 scripts/<nome>.py <percorso assoluto di milano-in-dati> <percorso assoluto di quartieri-che-cambiano>`, ordine in STATO.md). Tabelle in `out/`. Tutti i numeri qui sotto escono da `out/riepilogo.txt` (rifacibile con `scripts/05_riepilogo.py`) e dai file citati.

Parole: **NIL** = Nucleo di Identità Locale (88 quartieri del Comune). **Indice di cambiamento** = sintesi di sette segnali (sotto), NIL contro NIL: non misura che cosa succede alle persone. "Gentrificazione" è il nome che si dà a un quartiere dove salgono redditi, prezzi e affitti e cambiano commercio e abitanti; qui non è mai un'etichetta sulle persone e non si dice che cosa lo causa.

## 1. In breve

1. **73 NIL su 88 entrano in classifica** (almeno 2.000 residenti nel 2024, `popolazione/pulito/eta_nil_anno_indicatori.csv`, campo `residenti`). Gli altri 15 sono parchi, borghi e NIL minuscoli (elenco in `out/nil_non_in_classifica.csv` e `out/riepilogo.txt`).
2. **Sette segnali di nucleo, tre blocchi**: reddito reale, prezzo OMI reale, affitto OMI reale (casa); Airbnb ogni 100 abitazioni, locali di somministrazione (commercio); residenti di 25-34 anni, laureati (persone). Pesi uguali.
3. **In testa: Sarpi, Isola, Ghisolfa, Lambrate-Ortica, Farini**, poi Porta Ticinese-Conchetta, Stazione Centrale-Ponte Seveso, Porta Genova, Porta Garibaldi-Porta Nuova, Porta Romana (`out/tipologie_nil.csv`). **In coda: Quarto Oggiaro-Vialba-Musocco, Quinto Romano, QT8, Trenno, Guastalla, Bruzzano, Muggiano.**
4. **Il centro storico sta in fondo**: i 4 NIL classificati del Municipio 1 (Duomo, Brera, Guastalla, Magenta-San Vittore) sono ai posti 61, 59, 69, 65 su 73; nessuno dei primi 10 è nel Municipio 1. Nei prezzi OMI il centro è fermo in termini reali (zona B12: -1,3% dal 2014/2 al 2026/1, `docs/prezzi-case/data/zone_ultimo_semestre.csv`, campo `var_reale_2014_2_ultimo`).
5. **I cinque in testa e i sette in coda reggono ai cambi di pesi e di dati** (sezione 7); il centro della classifica no: un NIL cambia in media di 20 posti tra le varianti.
6. **Gli indicatori non vanno d'accordo tra loro**: correlazione media tra coppie 0,08 (Spearman), alfa di Cronbach 0,31, la prima componente spiega il 31% (`out/pca_indicatori.json`). L'indice è un riassunto utile ma tiene insieme almeno tre storie diverse (sezione 6).
7. **Mancano due ingressi**: botteghe storiche perse e nuove costruzioni (filoni non finiti, sezione 3; i file per NIL ci sono già, ma senza note: appena i filoni sono chiusi si aggiungono in `02_indicatori.py` e si rifanno 03-05).

## 2. Come è fatto l'indice

Per ogni indicatore: valore per NIL → punteggio z (sui 73 NIL, tagliato a ±3) → media semplice dei sette z (pesi uguali); se manca un indicatore si fa la media degli altri, purché ce ne siano almeno 5 (`scripts/03_indice.py`). Più alto = più "salita" (reddito, prezzi, affitti, affitti brevi, locali, giovani adulti, laureati in aumento). Rango 1 = cambiamento più forte. Il **livello** (ricchezza di partenza/arrivo) è a parte: media z di reddito medio 2024, prezzo OMI 2026 e laureati 2023; serve solo per le tipologie.

## 3. Ingressi: usati, scartati, mancanti

| Ingresso | Stato | Finestra | File e campo |
|---|---|---|---|
| Redditi per CAP | **usato** | anno d'imposta 2011 → 2024, euro 2025 | `redditi/pulito/cap_milano_media_euro2025.csv` (campi `2011`, `2024`); contribuenti: `cap_milano_contribuenti.csv` |
| Prezzi OMI | **usato** | 2014/2 → 2026/1, euro 2025 | `prezzi-case/pulito/prezzi_zona_semestre_prevalente.csv` (abitazioni civili, stato prevalente, `compr_centro_reale_2025`); perimetri: `prezzi-case/raw/geopoi/F205_20142.json`, `F205_20261.json` |
| Affitti OMI | **usato** | 2014/2 → 2026/1, euro 2025 | stesso file, campo `loc_centro_reale_2025` |
| Affitti brevi | **usato** (livello) | fotografia 19/9/2026 | `affitti-brevi/pulito/nil_riepilogo.csv`, campo `annunci_per_100_abitazioni` (NIL con `piccolo_denominatore` vuoti); crescita 2019 → 2025 in `crescita_nil.csv` (solo contesto/variante) |
| Locali (ristoranti, bar) | **usato** | registro 2019 → 2026 | `ristoranti/pulito/registro_2019_2026_nil.csv`: (`indirizzi_nuovi` - `indirizzi_scomparsi`) / `registro_2019`, solo NIL con almeno 20 pratiche nel 2019 |
| Residenti 25-34 anni | **usato** | 2014 → 2025 | `popolazione/pulito/eta_nil_anno_indicatori.csv`: `n_25_34` / `residenti` |
| Laureati | **usato** | censimento 2011 → 2023 | `censimenti/pulito/indicatori_NIL.csv`, `quota_laureati_su_residenti` |
| Variazione residenti, quota stranieri, età media | contesto (non nell'indice) | 2014 → 2025 | `eta_nil_anno_indicatori.csv`: `residenti`, `quota_stranieri`, `eta_media` |
| Scuole (iscritti) | contesto (non nell'indice) | a.s. 2015/16 → 2024/25 | `scuole/pulito/nil_iscritti_variazione_2015_2024.csv`, somma di infanzia, primaria, media |
| Botteghe storiche perse | **NON usato**: filone non finito (ricontrollato alle 21:10 circa del 1/11/2026) | - | `botteghe/pulito/botteghe.csv` (775 righe, campo `ancora_attiva`, `nil_id`) esiste ma senza `NOTE.md`, senza `STATO.md` e senza conteggi per NIL: non verificato, non usato |
| Nuove costruzioni | **NON usato**: filone non finito (ricontrollato alle 21:10 circa del 1/11/2026) | - | `costruzioni/pulito/nil_costruzioni.csv` (88 NIL, `nuove_abitazioni_2014_2024`) esiste ma senza `NOTE.md`: definizioni e limiti non verificati, non usato |

Perché sono solo di contesto: la variazione dei residenti sale anche dove si costruisce (non è per forza un quartiere che "sale"), il verso della quota stranieri è ambiguo, le scuole sono contate dove sta la scuola, non dove abitano i bambini, e il calo è di tutta la città (mediana -7,7% tra i NIL).

Come proxy dei nuovi quartieri, `out/tipologie_nil.csv` ha la colonna `residenti_oltre_25pct` (residenti cresciuti di oltre il 25% dal 2014 al 2025): Parco Forlanini-Cavriano, Tre Torri, Figino, Maggiore-Musocco-Certosa.

## 4. Il collegamento ai NIL (e come si ripete)

I dati sono per CAP (reddito, 38 CAP), per zona OMI (prezzi e affitti, 40-42 zone) e per NIL (gli altri). Il ponte sono i **57.405 civici** di `citta-15-minuti/out/civici_tempi.csv` (46.896 residenziali): ognuno ha già NIL e CAP (CAP stimato dal punto con CAP noto più vicino, giusto nel 96,6% dei casi secondo `citta-15-minuti/NOTE.md`) e qui riceve la **zona OMI del 2014/2 e quella del 2026/1** con il punto-in-poligono sui perimetri di ciascun semestre (regola pari/dispari degli anelli, area 181,7 km² in entrambi). Per ogni civico: crescita = valore 2026/1 della sua zona di oggi / valore 2014/2 della sua zona di allora - 1. Così le revisioni di zona (55 → 41 → 43 zone) non spezzano la serie. **Valore di un NIL = media sui suoi civici residenziali**: è la media pesata con i residenti stimati, dato che i residenti del NIL sono distribuiti in parti uguali sui civici residenziali (stessa ipotesi del filone 9).
- 46.645 civici residenziali su 46.896 hanno un valore OMI valido per la crescita (`out/collegamenti_log.json`); 95 civici senza zona nel 2014/2, 4 nel 2026/1.
- Un NIL ha mediamente un CAP dominante: 43 NIL su 88 hanno un CAP che copre almeno il 90% dei civici, 13 meno del 60% (`out/collegamento_cap_nil.csv`, quote per NIL; zone: `collegamento_omi_nil.csv`).
- Il reddito è assegnato solo se non più della metà dei civici sta in CAP "instabili" (vedi limiti): per Duomo, Brera, Guastalla e Porta Vigentina l'indicatore reddito manca.
- Prova su altra geografia: con **tutti** i 57.405 civici invece dei soli residenziali l'indice cambia pochissimo (Spearman 0,996 con la base).

## 5. Risultati principali

Mediane tra i NIL classificati (`out/riepilogo.txt`): prezzo OMI +27,3% reale, affitto OMI +37,7% reale, reddito reale per contribuente (CAP) +2,4%, locali +4,4%, laureati +8,1 punti, residenti 25-34 anni +1,1 punti, Airbnb 2,2 annunci ogni 100 abitazioni.

**Primi 10** (indice di base; valori grezzi: reddito %, prezzo %, affitto %, Airbnb ogni 100 abitazioni, locali %, 25-34 punti, laureati punti; da `out/riepilogo.txt`):

| # | NIL | Rango tra le varianti | Valori |
|---|---|---|---|
| 1 | Sarpi | 1-7 | +18,5; +40,0; +56,0; 5,5; +15,7; -0,6; +7,6 |
| 2 | Isola | 1-6 | +13,9; +28,3; +55,9; 5,3; +17,8; +0,5; +10,6 |
| 3 | Ghisolfa | 1-7 | +10,5; +47,9; +71,8; 2,4; +6,6; +1,2; +11,1 |
| 4 | Lambrate-Ortica | 1-17 | -0,1; +42,4; +113,7; 1,6; +5,5; +0,4; +13,1 |
| 5 | Farini | 1-9 | +6,6; +40,2; +77,1; 5,4; +10,7; -2,9; +11,3 |
| 6 | Porta Ticinese-Conchetta | 4-11 | +12,1; +44,0; +51,1; 7,1; +6,8; -1,1; +7,7 |
| 7 | Stazione Centrale-Ponte Seveso | 3-19 | +13,2; +28,0; +44,3; 10,2; +3,8; +0,2; +8,5 |
| 8 | Porta Genova | 6-13 | +7,8; +45,0; +53,0; 4,1; +2,7; +2,0; +8,1 |
| 9 | Porta Garibaldi-Porta Nuova | 4-31 | +19,0; +18,4; +17,9; 8,7; +9,8; +1,9; +5,7 |
| 10 | Porta Romana | 7-19 | +13,0; +40,1; +31,6; 4,7; +8,3; +0,6; +7,4 |

**Ultimi 10** (dal 73° al 64°): Quarto Oggiaro-Vialba-Musocco, Quinto Romano, QT8, Trenno, Guastalla, Bruzzano, Muggiano, Baggio-Olmi-Valsesia, Magenta-San Vittore, Quarto Cagnino. Quarto Oggiaro: reddito -5,2%, prezzo +11,9%, Airbnb 0,4 ogni 100 abitazioni, locali -6,7%, laureati +4,7 punti.

**Tipologie** (regola semplice, `scripts/04_tipologie.py`; terzile del cambiamento × livello alto ≥ +0,5 / basso ≤ -0,5 in z; conteggi e elenchi in `out/tipologie_nil.csv`, `out/tipologie_log.json`):
- **In salita rapida** (17 NIL, 252.654 residenti): cambiamento alto, livello non alto. Ghisolfa, Lambrate-Ortica, Farini, Bovisa, Dergano, Maggiore-Musocco-Certosa, Moncucco-San Cristoforo, Maciachini-Maggiolina, Bicocca, Rogoredo-Santa Giulia, Parco Forlanini, Morivione, Greco-Segnano, NoLo (Loreto-Casoretto), Adriano, Ortomercato, Vigentino.
- **Alti e ancora in salita** (8): Sarpi, Isola, Porta Ticinese-Conchetta, Stazione Centrale, Porta Genova, Porta Garibaldi-Porta Nuova, Porta Romana, Portello.
- **Già alti e stabili** (6): Duomo, Brera, Guastalla, Magenta-San Vittore, Porta Vigentina, Tre Torri (Tre Torri: quartiere nuovo, 5 indicatori su 7, "stabile" è da prendere con cautela).
- **Fermi su livelli bassi** (15, 211.479 residenti): Quarto Oggiaro, Quinto Romano, Trenno, Bruzzano, Muggiano, Baggio, Quarto Cagnino, Figino, Barona, Bovisasca, Forze Armate, Affori, Gratosoglio, Comasina, Monluè.
- **Fermi su livelli medi** (4): Giambellino, San Siro, Stadio-Ippodromi, QT8. **Nella media** (23, 642.586 residenti).
- **I raggruppamenti automatici non sono chiari**: con k-means su (indice, livello) la silhouette è 0,44 (k=2), 0,43 (k=3), 0,49 (k=4), 0,50 (k=5), 0,44 (k=6); sui tre blocchi + livello 0,28-0,34 (`out/tipologie_log.json`). È un continuo, non gruppi separati: le tipologie sono tagli dichiarati, non cluster scoperti.

**Municipi** (media pesata con i residenti, `out/municipi.csv`): indice medio più basso nel Municipio 1 (-0,56; livello +2,11), poi nel 7 (-0,36); più alto nel 2 (+0,14), 3 e 9 (+0,12). Le differenze tra municipi sono piccole tranne il Municipio 1.

**Contesto** (Spearman con l'indice, `out/riepilogo.txt`): quota stranieri +/- 2014→2025 -0,47 (dove l'indice è più alto la quota di stranieri è cresciuta meno: legame, non causa), livello 0,36, variazione dei residenti 0,12, scuole 0,18, età media 0,06.

## 6. Quello che l'indice non tiene insieme

Correlazioni tra indicatori (`out/correlazioni_indicatori.csv`, Spearman): reddito-Airbnb 0,79, reddito-prezzo 0,56, prezzo-laureati 0,45, affitto-laureati 0,35, ma reddito-25-34 anni -0,31, Airbnb-25-34 anni -0,25, affitto-reddito -0,10, affitto-Airbnb -0,15. Tra i blocchi: casa-commercio 0,26, casa-persone 0,18, commercio-persone -0,13. Tre storie diverse:
1. **Il centro-ricco** (reddito, Airbnb, in parte prezzi): è soprattutto un fatto di livello. Airbnb e reddito 2024 sono legati a 0,77, Airbnb e prezzo 2026 a 0,84.
2. **La corona che si rimette in moto** (affitti, laureati, prezzi): Lambrate, Bovisa, Dergano, Farini, Ghisolfa; gli affitti OMI salgono di più dove erano più bassi (Spearman affitto-reddito 2024 -0,37, affitto-prezzo 2026 -0,33): in parte è rincorsa, non solo salita.
3. **I giovani adulti** crescono di più dove il reddito è cresciuto meno (Spearman 25-34 anni - reddito -0,31) e dove sale la quota di stranieri (+0,41), non nei quartieri che si arricchiscono.

## 7. Robustezza (`out/robustezza_*.csv`)

- **Varianti** (Spearman con l'indice di base; posti in comune nei primi 10 / ultimi 10): percentili al posto di z 0,94 (7/9); senza taglio a ±3 0,99 (9/10); pesi per blocchi 0,98 (9/9); casa ×2 0,97 (9/9); commercio ×2 0,94 (9/9); persone ×2 0,95 (7/7); reddito con anche i CAP instabili 0,99 (8/8); Airbnb in crescita 2019→2025 al posto del livello 1,00 (10/9); locali contati per codice 0,98 (8/9); tutti i civici 1,00 (9/9); OMI 2016/2→2025/2 0,97 (7/9); soglia di residenti 1.000 o 5.000: 1,00 e 0,98.
- **Togliendo un indicatore alla volta**: Spearman da 0,92 (senza laureati) a 0,97 (senza Airbnb); posti in comune tra i primi 10: da 7 a 10.
- **Pesi casuali** (5.000 estrazioni Dirichlet uniforme, seme 20261101): in almeno metà delle estrazioni sono nei primi 10 Sarpi, Isola, Ghisolfa, Lambrate-Ortica, Farini, Porta Ticinese-Conchetta, Stazione Centrale, Porta Genova; negli ultimi 10 Quarto Oggiaro, Quinto Romano, QT8, Trenno, Guastalla, Bruzzano, Muggiano, Baggio, Magenta-San Vittore.
- **Quanto si muovono i singoli NIL**: tra tutte le varianti e i leave-one-out il rango massimo dei primi cinque è 7, 6, 7, 17, 9; il rango minimo degli ultimi cinque è 58, 58, 61, 66, 70. L'intervallo di rango è in media di 20 posti (mediana 18; massimo 55, Parco Forlanini); con pesi casuali l'intervallo 5-95% è in media di 34 posti. **Si possono dire con sicurezza gli estremi; il centro della classifica è una scala dove i NIL si scambiano di posto.**
- **Cosa non è stato provato**: nessuna misura con dati diversi (es. censimento invece di anagrafe per le persone); nessun controllo con un'altra fonte di prezzi (l'OMI è l'unica per zona); nessun test su finestre diverse per il reddito (solo 2011 e 2024 sono stabili).

## 8. La cosa più sorprendente

**Il cambiamento più forte non è dove abitano i più ricchi, ma nella corona attorno.** I 4 NIL classificati del Municipio 1 (Duomo, Brera, Guastalla, Magenta-San Vittore, livello da +1,9 a +2,3) stanno tutti negli ultimi 15 posti su 73, nessuno dei primi 10 è nel centro storico, e in testa c'è Sarpi (la "Chinatown": reddito del CAP +18,5%, prezzo OMI +40,0%, affitto OMI +56,0%, locali +15,7%, Airbnb 5,5 ogni 100 abitazioni), davanti a Isola, Ghisolfa, Lambrate e Farini. Il NIL che nessuno si aspetta è **Lambrate-Ortica** (4°): reddito reale fermo (-0,1%), ma affitto OMI +113,7% (il più alto dei 73) e +13,1 punti di laureati (secondo posto tra i 73). Nota di cautela: la salita dell'OMI è quasi tutta dopo il 2022 (vedi limiti) e per Lambrate pesa la zona D13 (affitto da 6,6 a 14,7 euro/mq al mese reali, 371 dei suoi civici; `out/civici_collegamenti.csv`).

## 9. Limiti dei dati

1. **I prezzi e gli affitti OMI sono stime dell'Agenzia, non prezzi di vendita.** Reali (euro 2025) sono quasi fermi fino al 2022 e poi salgono: variazione mediana tra le zone da un semestre all'altro dell'affitto: tra -1,2% e +1,9% fino al 2022/2, poi +2,8% (2023/1), +8,1% (2023/2), +3,7% (2024/1), +3,5% (2024/2), +3,5% (2025/1), +3,1% (2025/2), +2,0% (2026/1) (calcolata da `prezzi-case/pulito/prezzi_zona_semestre_prevalente.csv`, abitazioni civili, 40 zone). Quindi quasi tutta la salita 2014→2026 è del 2023-2026 e in parte è la revisione 2024 (43 zone). Non è "il mercato": è l'Agenzia che si aggiorna. Il confronto tra NIL regge meglio del livello.
2. **Tre indicatori su sette non sono per NIL.** Il reddito ha 38 valori (CAP), prezzi e affitti 42 zone: NIL vicini condividono lo stesso numero (nei NIL idonei 64 valori distinti di reddito su 69 NIL perché i NIL mescolano più CAP). Il rango di un NIL singolo è meno preciso di quanto sembri. Per Sarpi 777 civici su 1.042 stanno nella zona C16 sia nel 2014/2 sia nel 2026/1.
3. **CAP instabili.** Le sedi fiscali dei CAP 20121 e 20122 cambiano senza motivo economico (contribuenti +49% e +57% dal 2011 al 2024 contro +9% in città; `redditi/NOTE.md` limite 5): sono esclusi, quindi Duomo, Brera, Guastalla e Porta Vigentina non hanno l'indicatore reddito (con i CAP inclusi: Brera -21,8%, ma è un effetto dei contribuenti). Il 2011 sommando le classi è circa -1,5% del totale: le variazioni 2011-2024 sono un po' sopravvalutate. Il reddito è del contribuente, non del residente.
4. **Airbnb è una fotografia** del 19/9/2026 (Inside Airbnb, un solo portale), non una variazione; per costruzione segue il livello di ricchezza (0,77 col reddito). La crescita 2019→2025 sugli annunci recensiti dà quasi lo stesso ordine del livello (Spearman 0,98 tra le due). 4 NIL classificati (Parco Forlanini, Muggiano, Tre Torri, Figino) restano senza Airbnb per il denominatore piccolo (`piccolo_denominatore`).
5. **Locali: dal registro dei pubblici esercizi in piano, senza date**; i "nuovi" sono differenze tra due fotografie (2019 da Wayback, 2026) e cambi di gestione cambiano codice: si usano gli indirizzi, ma 12 NIL con meno di 20 pratiche nel 2019 restano senza indicatore. Cambio di NIL (2019) ricalcolato sui poligoni vigenti.
6. **Censimento 2011 e 2023 non sono dello stesso tipo** (2021-2023 sono "permanenti", con registri e campioni; `censimenti/NOTE.md`). I laureati sono su tutti i residenti per avere lo stesso denominatore ma la definizione di "laureato" può avere piccole differenze. Il 2011 è assegnato ai NIL 2021 per sovrapposizione di sezioni.
7. **Residenti e 25-34 anni: anagrafe, non censimento.** L'anagrafe 2011 non coincide col censimento (+8,7% in media tra i NIL, `popolazione/pulito` contro `censimenti/pulito`), e ha aggiustamenti statistici nel 2020-21; si usa 2014 → 2025 per stare lontani dal 2011-13.
8. **Scuole: iscritti nelle scuole del NIL**, non bambini residenti; 7 NIL non hanno scuole o ne hanno meno di 100 iscritti (vuoti). Calo di città (mediana -7,7%).
9. **Compone un riassunto, non una scoperta**: indicatori poco concordi (alfa 0,31). L'indice cambia poco con i pesi perché è una media di segnali che si compensano, non perché misuri una cosa sola.
10. **Convergenza**: gli affitti salgono di più dove erano più bassi: parte della "salita" in periferia è recupero di livello.
11. **Non misura spostamenti di persone**: nessun dato su chi lascia o arriva, nessun dato sugli sfratti, nessun dato sul commercio storico (botteghe) né sulle costruzioni. Le correlazioni non dicono cause.
12. **NIL fuori classifica** (15): Giardini P.ta Venezia, Parco Sempione, Triulzo Superiore, Chiaravalle, Quintosole, Ronchetto delle Rane, Cantalupa, Cascina Merlata, Roserio, Stephenson, Parco Nord, Parco delle Abbazie, Parco dei Navigli, Assiano, Parco Bosco in città. Cascina Merlata (1.130 residenti) è un quartiere nuovo che sarebbe interessante: va tolto per il filone costruzioni/botteghe.

## 10. Cosa potrebbe mostrare una pagina

1. **Mappa dei NIL** con i sette indicatori selezionabili e una vista "indice", con il rango e il suo intervallo (non un solo numero) e i NIL fuori classifica in grigio tratteggiato.
2. **Grafico livello × cambiamento** (73 punti) con le sei tipologie; il messaggio "il centro non è dove la città cambia".
3. **Scheda per NIL**: sette segnali con confronto con la mediana, tre blocchi, rango tra le varianti, tipologia, i limiti di quel NIL (reddito mancante, CAP condiviso).
4. **Cursore dei pesi** (per blocchi o singoli): chi resta in testa e in coda in ogni caso, per far vedere che gli estremi reggono e il centro no.
5. **"Le tre storie"**: tre mappe del blocco casa, commercio, persone (correlazioni tra blocchi 0,26 / 0,18 / -0,13).
6. Pagina "limiti dei dati" (sezione 9, in particolare OMI stime e CAP condivisi) prima delle classifiche.
7. Se arrivano botteghe e costruzioni: aggiungere come indicatori e rifare la robustezza (`scripts/02_indicatori.py` e `03_indice.py`, basta un campo in più nell'elenco `CORE`).

## 11. File in `out/`

`indicatori_nil.csv` (valori grezzi), `indicatori_definizioni.csv` (fonte e finestra di ogni indicatore), `indice_nil.csv` (z, indice, ranghi, intervalli), `tipologie_nil.csv` (tabella finale), `municipi.csv`, `robustezza_varianti.csv`, `robustezza_loo.csv`, `robustezza_pesi_casuali.csv`, `correlazioni_indicatori.csv`, `pca_indicatori.json`, `tipologie_log.json`, `collegamenti_log.json`, `collegamento_cap_nil.csv`, `collegamento_omi_nil.csv`, `cap_reddito_variazione.csv`, `civici_collegamenti.csv` (civici con zona e CAP; derivato dai civici del Comune, CC BY), `nil_non_in_classifica.csv`, `riepilogo.txt`.

Licenze: i dati di partenza sono del Comune (CC BY), MEF (CC BY 3.0), Agenzia delle Entrate OMI (CC BY 4.0), ISTAT (CC BY 4.0), Inside Airbnb (CC BY 4.0 ma "non ripubblicare i dati": qui solo aggregati per NIL) e OpenStreetMap non usato direttamente. Per ripubblicare: solo tabelle aggregate per NIL, non `civici_collegamenti.csv`.
