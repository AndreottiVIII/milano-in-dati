# I quartieri che cambiano - FASE 1 (analisi, nessuna pagina)

Fatto il 1 novembre 2026, solo con dati già su disco negli altri filoni di "Milano in dati". **Aggiornamento di sera: aggiunti botteghe storiche e nuove costruzioni (9 segnali invece di 7), rifatti i passi 03-05, e costruita la pagina `docs/quartieri-che-cambiano/` (`scripts/pagina.py`).** Nessun git, `JOURNAL.md` e `docs/` non toccati. Programmi in `scripts/` (Python 3.12, `python -I -X utf8 scripts/<nome>.py <percorso assoluto di milano-in-dati> <percorso assoluto di quartieri-che-cambiano>`, ordine in STATO.md). Tabelle in `out/`. Tutti i numeri qui sotto escono da `out/riepilogo.txt` (rifacibile con `scripts/05_riepilogo.py`) e dai file citati.

Parole: **NIL** = Nucleo di Identità Locale (88 quartieri del Comune). **Indice di cambiamento** = sintesi di nove segnali (sotto), NIL contro NIL: non misura che cosa succede alle persone. "Gentrificazione" è il nome che si dà a un quartiere dove salgono redditi, prezzi e affitti e cambiano commercio e abitanti; qui non è mai un'etichetta sulle persone e non si dice che cosa lo causa.

## 1. In breve

1. **73 NIL su 88 entrano in classifica** (almeno 2.000 residenti nel 2024, `popolazione/pulito/eta_nil_anno_indicatori.csv`, campo `residenti`). Gli altri 15 sono parchi, borghi e NIL minuscoli (`out/nil_non_in_classifica.csv`).
2. **Nove segnali di nucleo, tre blocchi**: casa (reddito reale, prezzo OMI reale, affitto OMI reale, nuove abitazioni), commercio (Airbnb ogni 100 abitazioni, locali di somministrazione, botteghe storiche perse), persone (residenti di 25-34 anni, laureati). Pesi uguali.
3. **In testa: Lambrate-Ortica, Porta Ticinese-Conchetta, Maggiore-Musocco-Certosa, Ghisolfa, Bovisa**, poi Sarpi (6°), Farini, Isola, Stazione Centrale, Parco Forlanini (`out/tipologie_nil.csv`). **In coda: Quarto Oggiaro-Vialba-Musocco, QT8, Muggiano, Quinto Romano, Trenno, Baggio, Guastalla.**
4. **Il centro storico sta in fondo**: i 4 NIL classificati del Municipio 1 (Brera, Duomo, Magenta-San Vittore, Guastalla) sono ai posti 58, 62, 66, 67 su 73 (tutti tra gli ultimi 16); nessuno dei primi 10 è nel Municipio 1. Nei prezzi OMI il centro è fermo in termini reali (zona B12: -1,3% dal 2014/2 al 2026/1, `docs/prezzi-case/data/zone_ultimo_semestre.csv`, campo `var_reale_2014_2_ultimo`).
5. **Gli estremi reggono ai cambi di pesi e di dati** (sezione 7); il centro della classifica no: un NIL cambia in media di 18 posti tra le varianti.
6. **Gli indicatori vanno poco d'accordo**: correlazione media tra coppie 0,08 (Spearman), alfa standardizzato 0,42, la prima componente spiega il 27% (`out/pca_indicatori.json`). L'indice è un riassunto che tiene insieme almeno tre storie.
7. **Che cosa è cambiato aggiungendo botteghe e costruzioni** (sezione 5b): la classifica resta simile (Spearman 0,95 con quella a sette segnali), ma cambia la testa: Lambrate-Ortica passa dal 4° al 1° posto, Sarpi dal 1° al 6°, Isola dal 2° all'8°; Maggiore-Musocco-Certosa dal 13° al 3° e Parco Forlanini dal 19° al 10° (nuove case). Salgono molto Giambellino (53° → 28°), Lorenteggio (35° → 14°), Pagano (34° → 18°); scendono NoLo (22° → 41°), Maciachini (15° → 24°), Porta Genova (8° → 16°). 10 NIL su 73 cambiano tipologia.

## 2. Come è fatto l'indice

Per ogni indicatore: valore per NIL → punteggio z (sui 73 NIL con un valore, tagliato a ±3) → media semplice dei nove z (pesi uguali); se manca un indicatore si fa la media degli altri, purché ce ne siano almeno 6 (`scripts/03_indice.py`). Le botteghe esistono per soli 23 NIL: per gli altri 50 l'indice è la media degli altri segnali. Più alto = più "salita" (reddito, prezzi, affitti, nuove case, affitti brevi, locali, botteghe perse, giovani adulti, laureati in aumento). Rango 1 = cambiamento più forte. Il **livello** (ricchezza di partenza/arrivo) è a parte: media z di reddito medio 2024, prezzo OMI 2026 e laureati 2023; serve solo per le tipologie.

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
| Botteghe storiche perse | **usato** | Albo 2017 → Albo 2024 | `botteghe/pulito/botteghe.csv`: `in_albo_2017`, `stato_albo_2024` (cessata, o assente nel 2024), `nil_id`; quota delle botteghe 2017 cessate o uscite; solo NIL con almeno 5 botteghe nell'Albo 2017 (23 NIL classificati) |
| Nuove abitazioni | **usato** | permessi 2014 → 2024 | `costruzioni/pulito/nil_costruzioni.csv`: `abitazioni_nuove_per_1000_ab_2024` (abitazioni in nuovi fabbricati con permesso di costruire ogni 1.000 residenti) |

Perché sono solo di contesto: la variazione dei residenti sale anche dove si costruisce (non è per forza un quartiere che "sale"), il verso della quota stranieri è ambiguo, le scuole sono contate dove sta la scuola, non dove abitano i bambini, e il calo è di tutta la città (mediana -7,7% tra i NIL).

Per segnalare i nuovi quartieri, `out/tipologie_nil.csv` ha anche la colonna `residenti_oltre_25pct` (residenti cresciuti di oltre il 25% dal 2014 al 2025): Parco Forlanini-Cavriano, Tre Torri, Figino, Maggiore-Musocco-Certosa.

## 4. Il collegamento ai NIL (e come si ripete)

I dati sono per CAP (reddito, 38 CAP), per zona OMI (prezzi e affitti, 40-42 zone) e per NIL (gli altri). Il ponte sono i **57.405 civici** di `citta-15-minuti/out/civici_tempi.csv` (46.896 residenziali): ognuno ha già NIL e CAP (CAP stimato dal punto con CAP noto più vicino, giusto nel 96,6% dei casi secondo `citta-15-minuti/NOTE.md`) e qui riceve la **zona OMI del 2014/2 e quella del 2026/1** con il punto-in-poligono sui perimetri di ciascun semestre (regola pari/dispari degli anelli, area 181,7 km² in entrambi). Per ogni civico: crescita = valore 2026/1 della sua zona di oggi / valore 2014/2 della sua zona di allora - 1. Così le revisioni di zona (55 → 41 → 43 zone) non spezzano la serie. **Valore di un NIL = media sui suoi civici residenziali**: è la media pesata con i residenti stimati, dato che i residenti del NIL sono distribuiti in parti uguali sui civici residenziali (stessa ipotesi del filone 9).
- 46.645 civici residenziali su 46.896 hanno un valore OMI valido per la crescita (`out/collegamenti_log.json`); 95 civici senza zona nel 2014/2, 4 nel 2026/1.
- Un NIL ha mediamente un CAP dominante: 43 NIL su 88 hanno un CAP che copre almeno il 90% dei civici, 13 meno del 60% (`out/collegamento_cap_nil.csv`, quote per NIL; zone: `collegamento_omi_nil.csv`).
- Il reddito è assegnato solo se non più della metà dei civici sta in CAP "instabili" (vedi limiti): per Duomo, Brera, Guastalla e Porta Vigentina l'indicatore reddito manca.
- Prova su altra geografia: con **tutti** i 57.405 civici invece dei soli residenziali l'indice cambia pochissimo (Spearman 0,996 con la base).

## 5. Risultati principali (nove segnali)

Mediane tra i NIL classificati (`out/riepilogo.txt`): prezzo OMI +27,3% reale, affitto OMI +37,7% reale, reddito reale per contribuente (CAP) +2,4%, nuove abitazioni 13,2 ogni 1.000 residenti, Airbnb 2,2 annunci ogni 100 abitazioni, locali +4,4%, botteghe storiche perse 21,4% (23 NIL), laureati +8,1 punti, residenti 25-34 anni +1,1 punti.

**Primi 10** (valori grezzi, nell'ordine: reddito %, prezzo %, affitto %, nuove abitazioni ogni 1.000 residenti, Airbnb ogni 100 abitazioni, locali %, botteghe perse %, 25-34 punti, laureati punti; n.d. = non calcolato; da `out/riepilogo.txt`):

| # | NIL | Posto tra le prove | Valori |
|---|---|---|---|
| 1 | Lambrate-Ortica | 1-7 | -0,1; +42,4; +113,7; 112,9; 1,6; +5,5; n.d.; +0,4; +13,1 |
| 2 | Porta Ticinese-Conchetta | 1-6 | +12,1; +44,0; +51,1; 35,7; 7,1; +6,8; 60,0; -1,1; +7,7 |
| 3 | Maggiore-Musocco-Certosa | 1-13 | -4,1; +27,3; +57,5; 196,8; 2,5; -5,7; n.d.; +5,7; +15,1 |
| 4 | Ghisolfa | 1-8 | +10,5; +47,9; +71,8; 17,3; 2,4; +6,6; n.d.; +1,2; +11,1 |
| 5 | Bovisa | 3-11 | +3,8; +33,3; +61,6; 71,3; 2,4; +7,2; n.d.; +1,8; +10,7 |
| 6 | Sarpi | 1-12 | +18,5; +40,0; +56,0; 12,6; 5,5; +15,7; 18,9; -0,6; +7,6 |
| 7 | Farini | 2-13 | +6,6; +40,2; +77,1; 16,3; 5,4; +10,7; n.d.; -2,9; +11,3 |
| 8 | Isola | 2-11 | +13,9; +28,3; +55,9; 4,9; 5,3; +17,8; 16,7; +0,5; +10,6 |
| 9 | Stazione Centrale-Ponte Seveso | 7-28 | +13,2; +28,0; +44,3; 6,7; 10,2; +3,8; 21,4; +0,2; +8,5 |
| 10 | Parco Forlanini-Cavriano | 1-43 | -0,2; +21,0; +73,8; 54,6; n.d.; n.d.; n.d.; +18,3; +1,7 |

**Ultimi 10** (dal 73° al 64°): Quarto Oggiaro-Vialba-Musocco, QT8, Muggiano, Quinto Romano, Trenno, Baggio-Olmi-Valsesia, Guastalla, Magenta-San Vittore, Bruzzano, Quarto Cagnino. Quarto Oggiaro: reddito -5,2%, prezzo +11,9%, nuove abitazioni 11,5 ogni 1.000 residenti, Airbnb 0,4 ogni 100 abitazioni, locali -6,7%, laureati +4,7 punti.

**Il centro** (botteghe storiche perse, Albo 2017 → 2024): Duomo 23,6%, Brera 21,4%, Guastalla 17,6%, Magenta-San Vittore 7,1% (mediana dei 23 NIL: 21,4%): il centro perde botteghe come gli altri, ma gli altri segnali (prezzi, affitti, nuove case) sono fermi.

**Tipologie** (regola semplice, `scripts/04_tipologie.py`; terzile del cambiamento × livello alto ≥ +0,5 / basso ≤ -0,5 in z; elenchi in `out/tipologie_nil.csv`, `out/tipologie_log.json`):
- **In salita rapida** (15 NIL, 208.347 residenti): Lambrate-Ortica, Maggiore-Musocco-Certosa, Ghisolfa, Bovisa, Farini, Parco Forlanini, Dergano, Moncucco-San Cristoforo, Lorenteggio, Adriano, Vigentino, Bicocca, Greco-Segnano, Maciachini-Maggiolina, Morivione.
- **Alti e ancora in salita** (10, 173.135 residenti): Porta Ticinese-Conchetta, Sarpi, Isola, Stazione Centrale, Porta Garibaldi-Porta Nuova, Porta Romana, Porta Genova, Pagano, De Angeli-Monte Rosa, Portello.
- **Già alti e stabili** (5): Porta Vigentina, Brera, Duomo, Magenta-San Vittore, Guastalla.
- **Fermi su livelli bassi** (17, 282.841 residenti): da Villapizzone, Comasina, Monluè, Gratosoglio, Affori a Quarto Oggiaro (elenco in `riepilogo.txt`). **Fermi su livelli medi** (3): San Siro, Stadio-Ippodromi, QT8. **Nella media** (23, 609.566 residenti; compresi NoLo, Rogoredo-Santa Giulia, Tre Torri).
- **I raggruppamenti automatici non sono chiari**: con k-means su (indice, livello) la silhouette è 0,36 (k=2), 0,44 (k=3), 0,45 (k=4), 0,47 (k=5), 0,42 (k=6); sui tre blocchi + livello 0,26-0,32. È un continuo, non gruppi separati: le tipologie sono tagli dichiarati, non cluster scoperti.

**Municipi** (media pesata con i residenti, `out/municipi.csv`): indice medio più basso nel Municipio 1 (-0,53; livello +2,11), poi nel 7 (-0,34); più alto nel 6 (+0,10), 3 (+0,09), 2 e 9 (+0,07). Le differenze tra municipi sono piccole tranne il Municipio 1.

**Contesto** (Spearman con l'indice): quota stranieri 2014→2025 -0,46 (dove l'indice è più alto la quota di stranieri è cresciuta meno: legame, non causa), livello 0,34, variazione dei residenti 0,21, scuole 0,24, età media 0,02.

### 5b. Che cosa cambia aggiungendo botteghe e costruzioni

Confronto con la classifica a sette segnali (copiata in `out/prima_sette_indicatori/`): Spearman tra le due 0,95 (variante `solo_i_sette_indicatori_di_prima` in `out/robustezza_varianti.csv`: 7 posti in comune nei primi 10, 10 negli ultimi 10). Nei primi 10 restano Lambrate, Porta Ticinese-Conchetta, Ghisolfa, Farini, Sarpi, Isola, Stazione Centrale (con altri posti); entrano Maggiore-Musocco-Certosa, Bovisa, Parco Forlanini; escono Porta Genova, Porta Garibaldi-Porta Nuova, Porta Romana. Salite: Giambellino 53° → 28°, Lorenteggio 35° → 14°, Pagano 34° → 18°, Tre Torri 57° → 46°. Discese: NoLo 22° → 41°, Maciachini 15° → 24°, Rogoredo 18° → 26°, Porta Genova 8° → 16°. 10 NIL su 73 cambiano tipologia (tra cui NoLo, Rogoredo-Santa Giulia e Ortomercato che passano a «Nella media»; Pagano e De Angeli a «Alti e ancora in salita»). La coda resta la stessa (Quarto Oggiaro 73°). I due segnali nuovi sono poco legati agli altri (Spearman: nuove case con prezzo 0,22 e laureati 0,20, con reddito -0,03; botteghe con reddito 0,29 e prezzo 0,24, con affitto 0,01).

## 6. Quello che l'indice non tiene insieme

Correlazioni tra indicatori (`out/correlazioni_indicatori.csv`, Spearman, a coppie): reddito-Airbnb 0,79, reddito-prezzo 0,56, prezzo-laureati 0,45, affitto-laureati 0,35, ma reddito-25-34 anni -0,31, Airbnb-25-34 anni -0,25, affitto-reddito -0,10, affitto-Airbnb -0,15. Tra i blocchi: casa-commercio 0,33, casa-persone 0,28, commercio-persone -0,14. Tre storie diverse:
1. **Il centro-ricco** (reddito, Airbnb, in parte prezzi): è soprattutto un fatto di livello (Airbnb e reddito 2024 a 0,77, Airbnb e prezzo 2026 a 0,84).
2. **La corona che si rimette in moto** (affitti, laureati, prezzi, nuove case): Lambrate, Bovisa, Dergano, Farini, Ghisolfa; gli affitti OMI salgono di più dove erano più bassi (Spearman affitto-reddito 2024 -0,37, affitto-prezzo 2026 -0,33): in parte è rincorsa.
3. **I giovani adulti** crescono di più dove il reddito è cresciuto meno (-0,31) e dove sale la quota di stranieri (+0,41), non nei quartieri che si arricchiscono.

## 7. Robustezza (`out/robustezza_*.csv`)

- **Varianti** (Spearman con l'indice di base; posti in comune nei primi 10 / ultimi 10): percentili al posto di z 0,94 (7/8); senza taglio a ±3 1,00 (10/10); pesi per blocchi 0,97 (9/8); casa ×2 0,98 (8/9); commercio ×2 0,96 (8/9); persone ×2 0,96 (8/8); solo i sette segnali di prima 0,95 (7/10); reddito con i CAP instabili 0,99 (10/8); Airbnb in crescita al posto del livello 1,00 (10/10); locali per codice 0,99 (9/9); tutti i civici 1,00 (10/10); OMI 2016/2→2025/2 0,97 (8/9); soglia di residenti 1.000 o 5.000: 1,00 e 0,98.
- **Togliendo un indicatore alla volta** (9 prove): Spearman da 0,95 (senza reddito o laureati) a 0,98 (senza botteghe); posti in comune tra i primi 10: da 7 a 9.
- **Pesi casuali** (5.000 estrazioni Dirichlet uniforme, seme 20261101): in almeno metà delle estrazioni sono nei primi 10 Lambrate-Ortica, Porta Ticinese-Conchetta, Maggiore-Musocco-Certosa, Ghisolfa, Bovisa, Sarpi, Farini, Isola; negli ultimi 10 Quarto Oggiaro, QT8, Muggiano, Quinto Romano, Trenno, Baggio, Guastalla, Magenta-San Vittore, Bruzzano.
- **Quanto si muovono i singoli NIL**: tra tutte le prove il posto peggiore dei primi cinque è 7, 6, 13, 8, 11; il posto migliore dei NIL dal 69° al 73° è 59, 60, 60, 61, 70. L'intervallo è in media di 18 posti (mediana 16; massimo 54, Tre Torri); con pesi casuali l'intervallo 5-95% è in media di 33 posti. **Si possono dire con sicurezza gli estremi; il centro della classifica è una scala dove i NIL si scambiano di posto.**
- **Cosa non è stato provato**: nessuna misura con dati diversi (censimento invece di anagrafe per le persone); nessun controllo con un'altra fonte di prezzi; nessun test su finestre diverse per il reddito.
- **Botteghe**: esistono per soli 23 NIL; per gli altri 50 l'indice è calcolato sugli altri segnali, quindi i due gruppi hanno una composizione diversa.

## 8. La cosa più sorprendente

**Il cambiamento più forte non è dove abitano i più ricchi, ma nella corona attorno.** I 4 NIL classificati del Municipio 1 (Brera 58°, Duomo 62°, Magenta-San Vittore 66°, Guastalla 67°; livello da +1,9 a +2,3) sono tutti tra gli ultimi 16 su 73 e nessuno dei primi 10 è nel centro storico. Il NIL che nessuno si aspetta è **Lambrate-Ortica** (1°, nelle prove dal 1° al 7°): reddito reale fermo (-0,1%), ma affitto OMI +113,7% (il più alto dei 73), laureati +13,1 punti (2°), 113 nuove abitazioni ogni 1.000 residenti (2°). Con sette segnali in testa c'era Sarpi (la "Chinatown"); con nove è 6° (reddito CAP +18,5%, prezzo +40,0%, affitto +56,0%, locali +15,7%, botteghe perse 18,9%). Cautela: la salita dell'OMI è quasi tutta dopo il 2022 (vedi limiti); per Lambrate pesa la zona D13 (affitto da 6,6 a 14,7 euro/mq al mese reali, 371 dei suoi civici; `out/civici_collegamenti.csv`); Maggiore-Musocco-Certosa (3°) sale soprattutto per l'edilizia (196,8 abitazioni ogni 1.000 residenti).

## 9. Limiti dei dati

1. **I prezzi e gli affitti OMI sono stime dell'Agenzia, non prezzi di vendita.** Reali (euro 2025) sono quasi fermi fino al 2022 e poi salgono: variazione mediana tra le zone da un semestre all'altro dell'affitto: tra -1,2% e +1,9% fino al 2022/2, poi +2,8% (2023/1), +8,1% (2023/2), +3,7% (2024/1), +3,5% (2024/2), +3,5% (2025/1), +3,1% (2025/2), +2,0% (2026/1) (da `prezzi-case/pulito/prezzi_zona_semestre_prevalente.csv`, abitazioni civili, 40 zone). Quasi tutta la salita 2014→2026 è del 2023-2026, in parte la revisione 2024 (43 zone). Il confronto tra NIL regge meglio del livello.
2. **Tre indicatori su nove non sono per NIL.** Il reddito ha 38 valori (CAP), prezzi e affitti 42 zone: NIL vicini condividono lo stesso numero (64 valori distinti di reddito su 69 NIL). Per Lambrate-Ortica 371 civici su 425 stanno nella zona D13.
3. **CAP instabili.** Le sedi fiscali dei CAP 20121 e 20122 cambiano senza motivo economico (contribuenti +49% e +57% dal 2011 al 2024 contro +9% in città; `redditi/NOTE.md` limite 5): sono esclusi, quindi Duomo, Brera, Guastalla e Porta Vigentina non hanno il reddito. Il 2011 sommando le classi è circa -1,5% del totale: le variazioni sono un po' sopravvalutate. Il reddito è del contribuente, non del residente.
4. **Airbnb è una fotografia** del 19/9/2026 (un solo portale), non una variazione; segue il livello di ricchezza (0,77 col reddito). 4 NIL classificati (Parco Forlanini, Muggiano, Tre Torri, Figino) restano senza Airbnb per il denominatore piccolo.
5. **Locali: registro dei pubblici esercizi in piano, senza date**; i "nuovi" sono differenze tra due fotografie (2019 da Wayback, 2026) e i cambi di gestione cambiano codice: si usano gli indirizzi; 12 NIL con meno di 20 pratiche nel 2019 restano senza indicatore.
6. **Botteghe storiche** (`botteghe/NOTE.md`, limiti 1-5): "cessata" è l'etichetta dell'Albo comunale, senza data e senza definizione (può voler dire anche "decaduta"); l'Albo 2024 ha indirizzi e coordinate sbagliati in alcuni casi (le coordinate finali vengono da più fonti); l'elenco del Comune e quello della Regione non coincidono (416 attività in comune su 760). Il segnale c'è solo per i 23 NIL con almeno 5 botteghe nel 2017; con pochi negozi la quota è rumorosa (Isola 16,7%, Porta Ticinese-Conchetta 60%).
7. **Nuove abitazioni** (`costruzioni/NOTE.md`, limiti 1-7): sono permessi di costruire, non cantieri finiti; solo nuovi fabbricati e ampliamenti (non ristrutturazioni); le ricostruzioni dopo demolizione sono incluse e le abitazioni demolite non si sottraggono; pochi interventi grandi spostano un quartiere (un intervento da 695 abitazioni); 54 record senza NIL. Dove si costruisce molto il "cambiamento" è anche edilizia.
8. **Censimento 2011 e 2023 non sono dello stesso tipo** (2021-2023 "permanenti", registri e campioni; `censimenti/NOTE.md`): i laureati sono su tutti i residenti per avere lo stesso denominatore, ma può restare qualche differenza di definizione. Il 2011 è assegnato ai NIL 2021 per sovrapposizione di sezioni.
9. **Residenti e 25-34 anni: anagrafe, non censimento.** L'anagrafe 2011 non coincide col censimento (+8,7% in media tra i NIL), e ha aggiustamenti statistici nel 2020-21; si usa 2014 → 2025.
10. **Scuole**: iscritti nelle scuole del NIL, non bambini residenti; 7 NIL senza scuole o con meno di 100 iscritti; calo di città (mediana -7,7%). Solo contesto.
11. **È un riassunto, non una scoperta**: indicatori poco concordi (alfa standardizzato 0,42). L'indice cambia poco con i pesi perché è una media di segnali che si compensano, non perché misuri una cosa sola.
12. **Convergenza**: gli affitti salgono di più dove erano più bassi: parte della "salita" in periferia è recupero di livello.
13. **Non misura spostamenti di persone**: nessun dato su chi lascia o arriva, né sugli sfratti. Le correlazioni non dicono cause. "Gentrificazione" è il nome che si dà a un quartiere in cui salgono redditi, prezzi e affitti e cambiano commercio e abitanti: qui non è un'etichetta per quartieri o persone.
14. **NIL fuori classifica** (15): Giardini P.ta Venezia, Parco Sempione, Triulzo Superiore, Chiaravalle, Quintosole, Ronchetto delle Rane, Cantalupa, Cascina Merlata, Roserio, Stephenson, Parco Nord, Parco delle Abbazie, Parco dei Navigli, Assiano, Parco Bosco in città.

## 10. La pagina

`docs/quartieri-che-cambiano/index.html`, dati in `docs/quartieri-che-cambiano/data/` (`riepilogo.json`, `nil.geojson`, `nil.csv`, `robustezza_varianti.csv`, `indicatori_definizioni.csv`), costruiti da `scripts/pagina.py` (`python -I -X utf8 scripts/pagina.py <milano-in-dati> <quartieri-che-cambiano> <docs>/quartieri-che-cambiano`). Sezioni: cosa sorprende, limiti dei dati in breve (prima delle classifiche), mappa (indice, ognuno dei nove segnali, tipologia) con scheda per NIL (posto e intervallo, nove segnali, limiti del NIL), classifica, grafico dei posti con intervallo, livello × cambiamento (sei tipologie dichiarate "tagli, non gruppi"), tre storie (tre mappe), prova dei pesi (nove cursori e sei preset), limiti dei dati completi, metodo, file, fonti con link alle pagine redditi, prezzi-case, affitti-brevi, ristoranti, censimenti, scuole, città dei 15 minuti. Provata in browser a 375 px: nessun errore in console, nessuno scroll orizzontale. Non toccati `docs/index.html`, `docs/menu.js`: la voce di menu la aggiunge il coordinatore.

## 11. File in `out/`

`indicatori_nil.csv` (valori grezzi), `indicatori_definizioni.csv` (fonte e finestra di ogni indicatore), `indice_nil.csv` (z, indice, ranghi, intervalli), `tipologie_nil.csv` (tabella finale), `municipi.csv`, `robustezza_varianti.csv`, `robustezza_loo.csv`, `robustezza_pesi_casuali.csv`, `correlazioni_indicatori.csv`, `pca_indicatori.json`, `tipologie_log.json`, `collegamenti_log.json`, `collegamento_cap_nil.csv`, `collegamento_omi_nil.csv`, `cap_reddito_variazione.csv`, `civici_collegamenti.csv` (civici con zona e CAP; derivato dai civici del Comune, CC BY), `nil_non_in_classifica.csv`, `riepilogo.txt`.

Licenze: i dati di partenza sono del Comune (CC BY, anche botteghe e permessi di costruire), MEF (CC BY 3.0), Agenzia delle Entrate OMI (CC BY 4.0), ISTAT (CC BY 4.0), Inside Airbnb (CC BY 4.0 ma "non ripubblicare i dati": qui solo aggregati per NIL) e OpenStreetMap non usato direttamente. Per ripubblicare: solo tabelle aggregate per NIL, non `civici_collegamenti.csv`.
