# Botteghe storiche di Milano - FASE 1 (fonti, scarico, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web. Ogni numero dice file e campo. Programmi in `scripts/` (ordine in STATO.md), dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle in `pulito/`. Tabella principale: `pulito/botteghe.csv` (760 attività, una riga ciascuna).

## 1. In breve

- Milano ha **due elenchi diversi** di "storiche", che non coincidono: l'**Albo comunale delle Botteghe Storiche** (50+ anni, dal 2004; 460 righe nel 2017, 626 nel 2024) e l'elenco **Negozi e Locali Storici della Regione Lombardia** (40+ anni; 546 righe a Milano al 19/10/2026). In comune: 416 attività. Insieme, 760 attività diverse (5.546 righe di 12 edizioni, unite con le regole di sezione 5).
- **Il dato nuovo è nell'Albo 2024: ha la colonna STATO (attiva/cessata).** 120 su 625 sono "cessata" (19,2%); 505 "attiva". Dei 457 negozi dell'Albo 2017, 112 (24,5%) sono "cessata" a dicembre 2024 e 6 non ci sono più nel file: un quarto in circa 7 anni.
- Il Comune non scrive **quando** hanno chiuso né cosa vuol dire "cessata". Controllo indipendente (OpenStreetMap): trova il 46,5% delle "attiva" e solo il 5,0% delle "cessata". L'etichetta sembra affidabile, ma resta un'etichetta.
- Quante sono vive oggi (stima con prove, `ancora_attiva`): **631** (349 con prova indipendente da OSM o dal registro 2026, 282 "probabili" solo perché stanno negli elenchi), **112** cessate (110 + 2), **10** contraddittorie, **7** non verificabili.
- La più antica: **Antica Trattoria Bagutto, 1284** (anno dichiarato nei due elenchi; Via Vittorini 4, NIL Monluè - Ponte Lambro). Anno di inizio mediano: **1949**; solo 58 su 760 sono anteriori al 1900; 362 (48%) sono nate tra 1945 e 1975.
- Il centro: **Municipio 1 = 360 su 760 (47,4%)**; il solo NIL Duomo ne ha 211 (27,8%); i primi 5 NIL ne hanno il 52%. 29 NIL su 88 non ne hanno nessuna.

## 2. Fonti, una per una

Licenza e data di scarico valgono per tutte: scaricate il 1/11/2026 (se non scritto altrimenti).

### 2.1 Albo Botteghe Storiche del Comune (CKAN dati.comune.milano.it) - CC-BY
- **ds2858** `ds2858-economia-botteghe-storiche-2024`, creato 3/12/2024, frequenza "NEVER": `raw/comune/ds2858/ds290_economia_botteghe_storiche_2024.csv` (+ geojson). **626 righe**, campi N., TARGA, GENERE MERCEOLOGICO, ANNO, **STATO** (attiva 506, cessata 120), INDIRIZZO, CAP, MUNICIPIO, ID_NIL, NIL, coordinate. [scripts/scarica_comune.py]
- **ds290** `ds290-economia-botteghe-storiche-2017`, creato 15/11/2017: `raw/comune/ds290/ds290_economia_botteghe_storiche_2017__.csv` (+ geojson). **460 righe**, stessi campi senza STATO e CAP, con INDIRIZZO e CIVICO separati. Una copia Wayback del 15/5/2021 ha 460 righe, 27 con testi leggermente diversi (`raw/wayback/albo_20210515.json`): non è un'edizione nuova.
- Descrizione ufficiale: Albo istituito con delibera 2220 del 5/10/2004; attività con almeno 50 anni di esercizio continuo nella stessa categoria merceologica.
- Altre copie dell'Albo: dal sito fareimpresa.comune.milano.it due PDF (copia Wayback del 12/4/2021): `Botteghe Storiche 2004 - 2017.pdf` (stesso elenco del 2017) e `Elenco Botteghe Storiche premiate anno 2019.pdf` (cerimonia 11/11/2019, solo nomi). Usato solo il PDF 2019 per sapere quali delle nuove voci del 2024 sono state premiate nel 2019 (58 su 174; `albo_riconoscimento`). Il sito oggi risponde 403: non aggiratato, non scaricato direttamente. Licenza dei PDF non dichiarata: restano in `raw/`, non vanno ripubblicati.
- Cosa manca: data di cessazione, data di iscrizione all'Albo, codice stabile tra le due edizioni (gli id sono numeri progressivi che cambiano), categorie omogenee (GENERE MERCEOLOGICO è testo libero con oltre 340 forme diverse).

### 2.2 Elenco regionale Negozi e Locali Storici (ds612 / dati.lombardia.it) - CC0
- **ds612** `ds612_elenco_attivita_storiche_e_di_tradizione_nel_comune_di_milano` (id Socrata g4x3-hs9b), frequenza BIWEEKLY, ultimo aggiornamento 19/10/2026: `raw/comune/ds612/` e `raw/lombardia/g4x3-hs9b/`. **546 righe**, campi ID_NLS, TIPO (Negozio storico 397, Locale storico 117, Bottega artigiana storica 32), RIC, INDIR_ORIG, DENOM_IMPRES, INSEGNA, INIZIO_ATT, ANNO_RICONOSCIMENTO, CAT_MERC (18 categorie), NIL, coordinate. Regione: "continuità dell'insegna e della merceologia per non meno di 40 anni".
- **czq5-nkk7** "Attività storiche e di tradizione" (tutta la Lombardia): 4.927 righe, 888 comuni, aggiornato 15/10/2026. Milano città = 546 (11,1%), provincia MI 895 (`pulito/regione_lombardia_*.csv`). Milano ha solo 32 "botteghe artigiane storiche" su 739 in regione (4%) contro il 15% dei negozi storici. Anno di inizio mediano: Lombardia 1962, Milano 1948,5. Prima del 1900: 4,1% in regione, 7,7% a Milano.
- **pccq-vbbq** "Negozi e locali storici georeferenziati nel Comune di Milano" (stesso elenco in versione 2019, ultimo aggiornamento righe 15/9/2022): **443 righe**; le coordinate sono rotte (valori 4,51 / 0,0004), servono solo gli ID. Il dataset d5uj-xwht (nome nuovo di ds612) non dà righe dall'API.
- **Edizioni nel tempo** (copie archiviate su web.archive.org, URL pubblici; `raw/wayback/` e `pulito/edizioni_conteggi.csv`): 23/7/2019 404 righe; 23/8/2019 350; 24/10/2019 349; 10/8/2020 389; 15/9/2022 443 (Socrata); 2/5/2024 468; 30/11/2024 490; 21/4/2025 490; 7/2/2026 531; 19/10/2026 546. Trovate anche copie di maggio 2024 e aprile 2025, già nel conteggio; il Comune/Regione non conserva le versioni vecchie (CKAN dà solo metadati: `raw/comune/*/_activity.json`). L'indice Wayback ha avuto periodi "Temporarily Offline"; altre copie esistono (JSON e GeoJSON 2024) e non sono state scaricate perché uguali nel contenuto alle CSV.
- Dataset trovati ma separati: locali da ballo storici (xguy-ssff, 20 righe in Lombardia, **4 a Milano**: Loolapaloosa, Magazzini Generali, Alcatraz, Hollywood Rythmoteque, decreti del 2024) e Mercati storici (z47y-7rbf, dati 2012: **25 mercati milanesi** "di valenza storica", riconoscimento 13/10/2009): `pulito/locali_da_ballo_storici_milano.csv`, `mercati_storici_milano.csv`. Dataset Bergamo/Cremona/Monza "Negozi e locali storici" (x5us-52q8, d62u-rncn, t635-fygy) scaricati, non usati (altre città).
- Cosa manca: nessuna colonna di stato o di cessazione; un'attività sparita dall'elenco non dice perché; non c'è l'anno di riconoscimento per il 28% (216 attività non nell'elenco 2026).

### 2.3 Altre fonti del Comune usate per le prove di presenza (già scaricate da altri filoni, solo lette)
- Registro commerciale del Comune 2026: ds49 esercizi di vicinato (28.131 righe, `citta-15-minuti/raw/comune_milano/vicinato/`, caricato 31/8/2026, CC-BY, insegna presente nel 17,6%) e `ristoranti/pulito/registro.csv` (ds58 in piano, ds59 fuori piano, ds250 artigianato alimentare, CC-BY). Servono come prova "debole" (c'è una pratica dello stesso settore entro 25 m) o "forte" (insegna simile entro 40 m).
- Civici del Comune ds634 (1/10/2026, 65.160 righe, CC-BY): per controllare le coordinate e trovare il NIL. **Unico geocoder usato**: nessun servizio esterno.
- NIL vigenti ds964 (poligoni) e abitanti 2024 (da `ristoranti/pulito/nil_locali_per_1000ab.csv`, 1.407.044 abitanti).
- ds588 "Imprese artigiane ARTIS" (CC0, 2008-2010): scaricato, **non usato** (non sono storiche; contiene titolari, email e partite IVA: non ripubblicare).

### 2.4 OpenStreetMap - ODbL 1.0, "© OpenStreetMap contributors"
- Estratto Geofabrik nord-ovest del 31/10/2026 (già scaricato dal filone ristoranti, `ristoranti/raw/geofabrik/`), letto con pyosmium e ritagliato sull'unione dei NIL: **23.876 elementi con nome** e tag shop/craft/amenity/office/tourism/leisure/healthcare (21.473 nodi, 2.403 poligoni ridotti al centro), `raw/osm/osm_milano_poi_con_nome.json` [scripts/estrai_osm.py]. Le relazioni (multipoligoni) non ci sono.
- Cosa NON c'è: OSM non è completo (trova meno della metà delle attività che il Comune dice attive). Assenza in OSM non vuol dire chiusura.
- Licenza: le colonne `osm_*` di `botteghe.csv` sono derivate da OSM; se si pubblica la tabella, pubblicare quelle colonne come ODbL (share-alike) con attribuzione. Un grafico o una mappa sono "Produced Work": basta l'attribuzione.

## 3. Completezza (Milano, 1/11/2026)

| Misura | Valore | Fonte |
|---|---|---|
| Attività uniche viste in almeno un elenco | 760 | `botteghe.csv` |
| In Albo 2017 / in Albo 2024 / in elenco Regione 2026 | 457 / 625 / 544 | `riepilogo.json` (righe-file 460 / 626 / 546: 3, 1 e 2 righe sono doppioni dello stesso negozio) |
| In Albo 2024 e in Regione 2026 | 416 | idem |
| Solo Regione 2026 (non in Albo 2024) / solo Albo 2024 (non in Regione 2026) | 128 / 209 | idem |
| Righe totali di tutte le edizioni | 5.546 | `edizioni_lunga.csv` |
| Con coordinate | 760 su 760 (759 dalle fonti, 1 corretta con i civici) | `botteghe.csv` `coord_da` |
| Coordinate a meno di 50 m dal civico del Comune | 670 (88%); 11 tra 50 e 200 m; 11 oltre 200 m (da controllare); 68 civico non nel file dei civici | `coord_verifica` |
| Con NIL | 760 su 760 (poligoni NIL vigenti sul punto) | idem |
| Con anno di inizio | 760; 45 con anni diversi nelle fonti (`anno_dubbio`, di solito 1-2 anni) | idem |

## 4. Numeri principali

### Per categoria (`pulito/per_settore.csv`; `settore` = mia classificazione per parole chiave su genere/categoria/insegna, 18 residui "altro")
Gioiellerie/orologerie 117; ristoranti/trattorie/osterie/pub 89; abbigliamento 72; casa e ferramenta 63; alimentari (salumerie, macellerie, enoteche...) 58; bar e caffè 57; librerie/cartolerie/edicole 53; parrucchieri/barbieri/profumerie 50; ottica e foto 28; pasticcerie/gelaterie 22; calzature e pelletterie 21; laboratori 19; servizi/spettacolo 16; panifici 14; sartorie e riparazioni 13; **farmacie 12**; sport e giocattoli 10; stampa e incisioni 8; auto/moto 7; fiori 6; salute 4; tabaccherie 3.
La classificazione è stata fatta da programma con parole chiave: non è una categoria ufficiale. `categoria` è quella ufficiale della Regione (18), "(stimata)" dove l'attività è solo nell'Albo.

### Anni di fondazione (`per_decennio_fondazione.csv`, `piu_antiche.csv`)
Prima del 1900: 58; 1900-09: 30; 1910-19: 38; 1920-29: 84; 1930-39: 101; 1940-49: 80; **1950-59: 145**; 1960-69: 127; 1970-79: 63; 1980-86: 34. Mediana 1949 (età 77 anni). 177 su 760 hanno 100 anni o più. Le più antiche: Antica Trattoria Bagutto 1284; Osteria La Pergola 1610 (cessata per il Comune, Vicolo Santa Caterina); Antica Farmacia del Lazzaretto 1750; Ditta Guenzati 1768; Libreria Bocca 1775; Ditta Raimondi di Pettinaroli 1776; Farmacia S. Eustorgio 1811; Antica Farmacia di Brera 1812. Gli anni sono quelli dichiarati dai titolari.

### Per quartiere (`per_nil.csv`)
Duomo 211, Brera 55, Buenos Aires-Porta Venezia-Porta Monforte 51, Sarpi 49, Guastalla 32, Porta Romana 30, Porta Ticinese-Conca del Naviglio 24, Magenta-San Vittore 23. Ogni 10.000 residenti (abitanti 2024): città 5,4; **Duomo 130**, Brera 30, Guastalla 21, Porta Romana 18, Sarpi 16. 29 NIL su 88 a zero (periferie e parchi: Quarto Oggiaro, Gallaratese, Comasina, QT8, Bovisasca...). Per Municipio: 1 = 360, 3 = 76, 5 = 53, 7 = 51, 8 = 49, 2 = 49, 4 = 44, 6 = 40, 9 = 34 (campo MUNICIPIO delle fonti; 4 senza).
Attenzione: il denominatore (residenti) non conta chi lavora o visita; Duomo ha pochi residenti.

### Chiuse, sparite (`pulito/botteghe_cessate_o_dubbie.csv` ha l'elenco)
Qui "chiusa" è sempre "cessata per il Comune"; la data non c'è.
- **Albo 2017 → 2024**: 457 voci nel 2017; a dicembre 2024: 339 attive, **112 cessate**, 6 non più nel file. Le 174 voci nuove del 2024: 8 già cessate (4,6%). Quindi la quota di cessate sale con gli anni di permanenza nell'Albo, non è un effetto del 2024.
- **Per tipo** (Albo 2024, 625; `cessate_per_settore_albo24.csv`): bar e caffè 1 su 45 (2,2%); farmacie 0 su 12; gioiellerie 14 su 94 (14,9%); ristoranti 10 su 73 (13,7%); abbigliamento 16 su 59 (27,1%); librerie/cartolerie 11 su 44 (25%); parrucchieri 11 su 43 (25,6%); casa/ferramenta 12 su 52 (23,1%); **panifici e pasticcerie 12 su 34 (35,3%)**. Test di Fisher sui bar: p = 0,001; sui panifici+pasticcerie: p = 0,02; sulle farmacie (12 casi): p = 0,14, troppo pochi per concludere.
- **Per epoca di fondazione** (`cessate_per_epoca_fondazione.csv`): fino al 1919: 20 su 122 (16%); 1920-44: 41 su 197 (21%); **1945-59: 49 su 180 (27%)**; 1960-69: 10 su 105 (9,5%); dal 1970: 0 su 21. Le nate nel dopoguerra chiudono più delle altre (27% contro 16%; p = 0,002).
- **Centro e resto**: Municipio 1: 15,5% (49 su 316); resto della città: 23,0% (71 su 309; p = 0,02). Duomo 34 su 187 (18,2%).
- **Elenco Regione, uscite**: 599 attività viste in almeno una copia; 55 non ci sono più nel 2026. **54 sono uscite tutte insieme tra il 23/7/2019 e il 15/8/2019** (404 → 350 righe; motivo non indicato; il file Socrata di agosto riporta aggiornamento 15/8/2019); le altre sono uscite una per volta (1 nell'ottobre 2019, 1 tra 2020 e 2022). Delle 55: 37 sono "cessata" nell'Albo 2024, 15 "attiva" (usciti dall'elenco regionale ma ancora attivi per il Comune), 3 non sono nell'Albo; **nessuna** ha un punto OSM con lo stesso nome. Quindi la pulizia del 2019 ha tolto soprattutto attività finite, ma non tutte (15 "attive").
- **L'elenco Regione non si ripulisce abbastanza**: 49 delle 544 attività dell'elenco 2026 sono "cessata" per il Comune (9%); di queste 6 hanno comunque un punto OSM con lo stesso nome (43 no).
- **Assenza ≠ chiusura**: l'estratto OSM non basta da solo; il registro 2026 ha pratiche dello stesso settore sugli stessi indirizzi anche per attività cessate (prova "debole" in 96 casi su 120, in parte cambio di gestione). Per questo il campo `ancora_attiva` ha 6 valori: `si` (prova indipendente: punto OSM con lo stesso nome e tipo compatibile entro 90 m, oppure pratica 2026 con insegna simile entro 40 m, e il Comune non la dice cessata), `probabile` (solo elenchi), `cessata` (Comune: cessata, nessuna prova contraria), `contraddittoria` (Comune: cessata, ma OSM o registro la mostrano: 10 casi, sono i cambi di gestione o punti OSM vecchi, es. Ristorante da Bruno con ultima modifica OSM 2020), `cessata_probabile` (Comune: attiva, ma il punto OSM la segna chiusa: 2 casi: Teatro Nuovo e Eliorapid Centro Stampa), `non_verificabile` (nessuna lista recente e nessuna prova: 7).

### La cosa più sorprendente
Non è la più antica (Bagutto, 1284) ma **chi chiude**: nell'Albo del Comune su 45 bar e caffè storici ne ha cessato **uno solo** (2,2%) e nessuna delle 12 farmacie, mentre **un panificio o una pasticceria storica su tre** (12 su 34) risulta cessata; e chiudono più le attività del dopoguerra (1945-59: 27%) che quelle di fine Ottocento (16%). Seconda sorpresa, sul metodo: l'elenco regionale 2026 contiene ancora 49 attività che il Comune dà per cessate.

## 5. Come sono state unite le righe (importante per capire i conteggi)
Le 5.546 righe sono state unite in 760 attività con queste regole in sequenza (`scripts/02_unifica.py`, `pulito/entita_record.csv`): (1) stesso ID_NLS della Regione; (2) stesso civico, via simile, nome simile (787 legami); (3) senza civico, stessa via, nome quasi uguale e stesso anno (4); (4) nome quasi uguale, stesso anno, meno di 150 m (95); (5) voci dell'Albo 2024 con indirizzo diverso dal resto (42 legami, di cui 16 oltre 1 km): stesso nome e anno (+-2), uno a uno. Le unioni della regola 5 vanno controllate a mano se si pubblicano singole schede: sono la parte meno sicura. Catene con più sedi (Gusella 3, Galli Giovanni 2, Fratelli Freni 2) sono tenute come attività diverse perché hanno indirizzi e anni diversi.

## 6. Limiti dei dati
1. **Due elenchi diversi, due criteri diversi** (50 anni contro 40) e due amministrazioni: contare "le botteghe storiche di Milano" richiede di dire quale. Solo 416 attività sono in entrambi.
2. **"Cessata" non è definita e non ha data.** Le chiusure fra 2017 e 2024 si leggono solo per differenza tra due fotografie; l'Albo prevede la decadenza quando vengono meno i requisiti, quindi "cessata" potrebbe anche voler dire "decaduta" (attività cambiata) e non solo "chiusa".
3. **Indirizzi e coordinate dell'Albo 2024 sbagliati in alcuni casi**: sono stati riportati su uno stradario dei civici e a volte cambiano via: "Piazza Mercanti 17" è diventata "Via Luigi Mercantini 17"; "Via Maddalena 5" "Via Maddalena Giudice Donadoni 1"; "Viale Tunisia 4" "Via Luigi Soderini 2" (5 km). 35 attività hanno l'Albo 2024 a più di 200 m dalle altre fonti (`indirizzo_discordante`). Nell'indirizzo finale ho scelto l'elenco Regione, poi l'Albo 2017, poi l'Albo 2024.
4. **Nomi con le lettere accentate rovinate** nell'Albo 2024 (e nel dataset 2022): "Citt… di Londra", "Vigan•", "Caff? Pasticceria Cucchi". Il nome finale viene dall'Albo 2017 o dalla Regione; un solo nome è rimasto rovinato (`nome_rovinato`). Il PDF 2004-2017 e un file Wayback hanno gli stessi `?`.
5. **L'anno è dichiarato dal titolare**, non verificato; 45 attività hanno anni diversi nelle fonti. Non è l'anno della bottega "così com'è": molte hanno cambiato gestione.
6. **Cambio di gestione e subentri**: la stessa insegna può continuare con altri titolari (denominazione sociale cambia) senza che l'elenco lo dica. Per questo ho abbinato per insegna e luogo e non per ragione sociale.
7. **Registro 2026**: dalla stessa via può risultare una pratica anche se l'insegna è chiusa (cambio di gestione). L'insegna è presente nel 17,6% di ds49. Perciò è solo prova debole.
8. **OSM**: nome, tipo e distanza (90 m) decidono l'abbinamento; qualche abbinamento falso resta (es. Macelleria Sirtori ↔ La Ravioleria Sarpi); il 40% dei punti trovati è stato modificato negli ultimi 12 mesi, il 79,5% negli ultimi 3 anni. 4 punti trovati sono segnati chiusi.
9. **ID_NLS Regione**: i primi ID (6xxx-7xxx) sono del 2010; i nuovi hanno 7 cifre. Un negozio può avere più ID nel tempo.
10. **Wayback**: copie senza data di aggiornamento interna; la data è quella di cattura. Il confronto 23/7/2019 → 23/8/2019 mette a confronto un CSV e un JSON del portale del Comune: può contenere differenze di esportazione.
11. **Le categorie** sono testo libero nell'Albo (oltre 340 diciture) e 18 voci nella Regione; la mia classificazione `settore` è approssimata.

12. **Nomi di persone**: `botteghe.csv` ha solo l'insegna. `pulito/entita_record.csv` e `edizioni_lunga.csv` hanno anche la denominazione sociale (`denom`), che per le ditte individuali è il nome del titolare (es. "RANCATI LUCIANO"): sono file di lavoro, da non pubblicare. Nei dati grezzi dell'Albo e del PDF 2019 compaiono nomi di titolari: restano in `raw/`.

## 7. Cosa potrebbe mostrare una pagina (idee, non fatte)
1. Mappa delle 760 con colore per stato (viva con prova / probabile / cessata) e filtro per categoria e fondazione; punti OSM-derived con attribuzione.
2. Linea del tempo di fondazione per decennio, con le più antiche ancora aperte (Bagutto 1284).
3. "Chi chiude": barre per tipo con la quota di cessate (bar 2%, panifici/pasticcerie 35%).
4. Le due liste (Comune e Regione) in un diagramma di sovrapposizione: 416 in comune, 209 solo Comune, 128 solo Regione; e la crescita dell'elenco regionale 2019-2026.
5. Il Duomo da solo: 28% delle botteghe e 130 ogni 10.000 abitanti contro 5 nella media della città.
6. Elenco delle cessate con la scheda e la prova (nomi di attività, non di persone).
Da verificare prima: la regola 5 di unione, le 11 coordinate oltre 200 m, i 10 casi "contraddittoria", e se pubblicare il nome del titolare (non presente in `botteghe.csv`: solo l'insegna).

## 8. Da decidere
- Procedere con la pagina? Sì/no, e con quale domanda centrale ("chi chiude" oppure "quanto vecchie").
- Chiedere al Comune (opendatamilano@comune.milano.it, nei metadati) cosa significa "cessata", da quando e perché le coordinate dell'Albo 2024 sono state rifatte.
- Verifica a mano di un campione (30-50 schede) con fonti pubbliche per misurare l'errore di `ancora_attiva`.
