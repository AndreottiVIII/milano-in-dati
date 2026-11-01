# Biblioteche: che cosa legge Milano - FASE 1 (raccolta, pulizia, riepiloghi)

Scaricato il 1 novembre 2026. Niente pagina web, nessun giudizio. Ogni numero dice file e campo. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di biblioteche> [<percorso assoluto di milano-in-dati>]` (ordine in STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle in `pulito/`. Tutti i numeri sotto stanno in `pulito/riepilogo.json` o nelle tabelle csv indicate.

## 1. In breve

1. **I prestiti delle biblioteche del Comune sono in open data, CC-BY, molto bene: un totale mensile per punto di prestito e classe di età da gennaio 2013 a maggio 2026 (ds2986) e, per i 138 mesi da gennaio 2013 a giugno 2024, un file con una riga per ogni prestito (11.302.398 righe: titolo, autore, editore, anno di edizione, tipo di materiale, biblioteca, sesso e fascia di età di chi prende in prestito; mai l'identità).** Non esiste nulla di simile per i prestiti digitali (MLOL): non ci sono nei dati aperti.
2. **Prestiti totali (ds2986)**: 1.301.765 nel 2013, 1.009.094 nel 2018, 1.033.695 nel 2019, 428.989 nel 2020, 986.954 nel 2025. Calo 2013-2018 **-22,5%**, ripresa 2019 +2,4%, Covid 2020 -58,5%, **2025 = 95,5% del 2019 e -24,2% sul 2013**. Per abitante: 0,96 prestiti all'anno nel 2013, 0,74 nel 2019, 0,70 nel 2025.
3. **La cosa più sorprendente: i libri non se ne sono mai andati, sono spariti i DVD e i CD.** I prestiti di "libri e audiolibri" sono 861.254 nel 2013, 755.826 nel 2019, 783.700 nel 2023: **+3,7% sul 2019 e -9,0% sul 2013**; nel primo semestre 2024 sono **+14,5% sul primo semestre 2019 e solo -4,1% sul primo semestre 2013**. Il materiale non libro (DVD, CD, ecc.) è passato da 440.734 a 109.086 prestiti (**-75,2%**) tra il 2013 e il 2023 ed è **l'85% dei 389.770 prestiti persi in quel decennio** (331.648 su 389.770). I libri sono il 65,7% dei prestiti nel 2013 e l'85,1% nel 2023.
4. **Un prestito su tre (35,2% nel 2024) è un libro di un'altra biblioteca del sistema**, preso in prestito dove l'utente lo ritira (prenotazione + consegna): era 3,7% nel 2017, 23,6% nel 2019, 43,5% nel 2021. Prima del 2017 il dato non distingue (vedi trappole).
5. **Chi prende in prestito invecchia e si femminilizza**: utenti 65+ dal 19,2% (2013) al 26,6% (2025) dei prestiti; donne dal 57,9% (2013) al 64,1% (2024); minori (0-17) dal 14,0% (2013) al minimo 9,8% (2021), di nuovo 14,2% nel 2025.
6. **I best seller pesano molto meno**: il libro più prestato dell'anno passa da 1.272 prestiti (2013, Gramellini) a 473 (2023, Perrin); i primi 100 titoli valgono il 4,6% dei prestiti di libri nel 2013 e il 3,1% nel 2023; i titoli diversi prestati salgono da 113.748 a 147.026 mentre i prestiti calano.
7. **Digitale (MLOL, e-book)**: nessun dato aperto. Nel dettaglio compaiono 4 prestiti "E-BOOK READER" in 11 anni, nient'altro. Una sola cifra indiretta (Ansa citata da una rivista AIB): marzo 2020, oltre 57 mila tra prestiti e download online e +641% di iscrizioni, ma non l'ho verificata sulla fonte e non è un dato aperto.
8. **I dati nazionali (ICCU, Istat) danno solo il contesto**: ICCU elenca 305 biblioteche nel comune di Milano (registro, nessun prestito); l'Istat 2025 ha tavole solo per regione (Lombardia: 10.206.339 prestiti fisici locali nell'anno di rilevazione, 1.731.755 utenti attivi; le biblioteche del Comune di Milano, con circa 0,99 milioni di prestiti nel 2025, ne fanno l'ordine del 10%: l'anno di riferimento dell'Istat non è indicato nelle tavole che ho letto).

## 2. Fonti, una per una

Licenza di tutti i dataset del Comune: nel catalogo CKAN `license_id = cc-by`, `license_title = "Creative Commons Attribution"`, `license_url = http://www.opendefinition.org/licenses/cc-by` (la versione non è scritta). Si possono ripubblicare citando "Comune di Milano - dati.comune.milano.it". Editore dei dataset: Comune di Milano - Direzione Cultura. Data di scarico di tutto: **1 novembre 2026**. Ricerca CKAN con 17 parole chiave (`scripts/search.py`, `raw/search_all.json`): 331 dataset toccati, 166 sulle biblioteche. Scaricati 159 file (830 MB, nessun errore, `raw/download_log.csv`); i JSON sono copie dei CSV e li ho saltati.

| Dataset | Cosa | Anni | Righe | Dimensione | Note / cosa manca |
|---|---|---|---|---|---|
| **ds2986** prestiti per mese - serie storica | prestiti per mese x punto di prestito (biblioteca, bibliobus, smartlocker, edicola, libreria) x classe di età (11 classi); NIL e municipio del punto | gen 2013 - mag 2026 (aggiornamento MENSILE dichiarato, modificato 17/7/2026) | 47.547 | 4,3 MB csv | niente titoli, niente sesso, niente MLOL. **Maggio 2026 incompleto** (15.800 prestiti, 17% del maggio 2019). Esclude depositi (Boifava ecc.) |
| **ds2493-ds2612, ds2750-ds2761, ds2862-ds2867** prestiti per mese (dettaglio) | **una riga per prestito**: date inizio/fine, stato, tipo (bibliotecario, interbibliotecario, consultazione...), biblioteca "da" e "a", sesso e fascia di età, titolo, autore, editore, lingua, anno di edizione, tipo di materiale | gen 2013 - giu 2024, **138 file** (uno al mese; zip, ma marzo-maggio 2020 sono csv semplici) | 11.302.398 (67.788 a dic 2022; 19.826 byte ad aprile 2020 = 43 prestiti) | 821 MB | si ferma a **giugno 2024** (frequenza dichiarata NEVER: nessun mese dopo). Nessun identificativo dell'utente: **non si possono contare i lettori distinti**. Nessun genere letterario nel dettaglio |
| ds3012 punti di prestito del Sistema Bibliotecario | 92 punti (25 biblioteche, bibliobus con 5 fermate, smartlocker, edicole e librerie "punto di ritiro", Mudec, CDEC...), coordinate, NIL, attivo/non attivo | stato 30/9/2026 (trimestrale) | 92 | 13 KB | 23 punti non attivi senza coordinate |
| ds1306 Sistema Bibliotecario Milanese | 25 sedi con orari, CAP, mezzi | ottobre 2025 | 25 | 9 KB | usato solo per controllo (già in `citta-15-minuti`) |
| ds336 / ds286 (Sormani) | patrimonio, iscritti, prestiti per biblioteca | 2013, 2014, 2015 | 81 / 3 | 9 KB / 1 KB | |
| ds909 | iscritti, prestiti (narrativa/saggistica/multimediali) | 2016, 2017, 2018 | 88 | 10 KB | **2017 e 2018 inutilizzabili** (colonne sfalsate); 2016: Accursio e Gallaratese con "-" |
| ds928, ds1641, ds2166, ds2928, ds2929 | patrimonio, iscritti, prestiti per biblioteca (locali, in entrata, in uscita da altre biblioteche), smartlocker dal 2023 | 2019, 2020, 2021, 2022, 2023 | 29-40 ciascuno | 4-6 KB | **2024 e 2025 non esistono**; 2012 e anni prima solo parziale |
| ds99, ds161, ds162, ds163, ds167, ds168, ds101 | prestiti delle rionali per tipo di opera, mese, genere (narrativa/saggistica), Sormani con residenza degli utenti | 2007-2008, 2011 | 2.098 / 4.075 / 13.792 / 3.204 / ... | < 1 MB | solo rionali (Sormani a parte); manca il 2009-2010 e il 2012 |
| ds563, ds580-ds584 Biblioteca Braidense | patrimonio, posti, utenti, opere date in prestito | 1998-2023 | 25-260 | pochi KB | **Braidense non è comunale** (biblioteca statale, Brera): non c'entra col Sistema Bibliotecario; non usata |
| ds2467 prestito libri con ritiro in edicole e librerie, ds3019 spazi freschi: biblioteche, ds41 localizzazione biblioteche e archivi 2007-2013 | elenchi di luoghi | | 23, 13, 232 | | contorno |
| **ICCU - Anagrafe delle biblioteche italiane** `territorio.zip` | registro: denominazione, indirizzo, coordinate, ISIL, **nessun prestito** | stato 1/11/2026 (aggiornato ogni giorno) | 13.734 in Italia, 305 nel comune di Milano (codice Istat 015146) | 1 MB | licenza **CC0** (dalla pagina dei dati aperti dell'ICCU) |
| **Istat - censimento biblioteche pubbliche e private** `Tavole-dati.xlsx` | 34 tavole per regione/ripartizione/ampiezza del comune, anno 2025, pubblicate il 12/10/2026 | 2025 | 34 tavole | 227 KB | **niente dato per comune o provincia**, quindi niente Milano; licenza non indicata nella pagina (solo "per i microdati rivolgersi al Contact Centre"); non l'ho ripubblicato. Riga Lombardia di tav. 12 e 13 in `pulito/contesto_esterno.json` |
| Sistema Bibliotecario Milano (sito) | | | | | i due indirizzi che ho provato non rispondono (nessun DNS); non ho cercato oltre. Nessun dato aperto sui prestiti digitali trovato |

## 3. Pulizia e tabelle

Nessun valore è stato cancellato o corretto: le stranezze sono segnalate. Tutte le tabelle in `pulito/` (separatore `;`):

- `punti_prestito.csv` (92 punti): nome canonico (`biblioteca`: "Dergano", "Lambrate" = Valvassori Peroni, "Parco Sempione"...), tipo, coordinate, **NIL assegnato per punto in poligono** sui 88 NIL vigenti (`citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson`): 69 punti con coordinate, tutti dentro un poligono; 91 su 92 coincidono con l'ID NIL scritto nel file ds3012 (1 differenza: Edicola Cotrina, io Corsica, il file Taliedo); 70 su 70 coincidono con il codice NIL scritto nel ds2986.
- `prestiti_mese_punto_eta.csv` (ds2986 ordinato), `prestiti_anno_punto.csv`, `prestiti_anno_totale.csv`, `prestiti_anno_eta.csv`.
- `statistiche_annuali_biblioteca.csv` (280 righe, anni 2013-2016 e 2019-2023): iscritti adulti/ragazzi, patrimonio stampati, prestiti locali (stampati + multimediali), periodici, in entrata e in uscita da altre biblioteche.
- Dal dettaglio (`cubo_prestiti_completo.parquet` 775.541 righe = tutti i prestiti ridotti per mese x tipo x stato x biblioteche x età x sesso x materiale; `titoli_anno_completo.parquet` 3.017.232 righe = per anno x titolo x autore x materiale x fascia): `dettaglio_anno_tipo.csv`, `dettaglio_anno_eta_genere.csv`, `dettaglio_anno_supporto.csv`, `dettaglio_anno_ritiro_proprietaria.csv`, `top_titoli_anno.csv` (primi 25 per anno e per fascia: tutti, Minori, Adulti, Anziani), `top_autori_anno.csv`, `top_non_libri_anno.csv`, `top_editori_anno.csv`, `concentrazione_titoli_anno.csv`, `traduzioni_anno.csv`, `freschezza_libri_anno.csv`, `lingua_edizione_anno.csv`.
- Altri: `serie_lunga_rionali_2007_2011.csv`, `narrativa_saggistica.csv` (2011 e 2016), `sormani_2011_residenza_utenti.csv`, `ripresa_mensile_vs_2019.csv`, `mesi_chiusi_biblioteca_anno.csv`, `prestiti_biblioteca_anno_ranking.csv`, `quota_volumi_propri_2023.csv`, `nil_biblioteche.csv`, `catchment_biblioteche.csv`, `iccu_biblioteche_milano.csv`.
- **Definizione di "prestito valido"** nel dettaglio: stato diverso da *Annullato* e tipo diverso da *Consultazione*: 11.254.626 su 11.302.398 (le 5.420 righe annullate e le 42.401 consultazioni fuori). Dentro restano i 95.569 prestiti "In corso" (non ancora restituiti al momento dell'estrazione, 75.390 nel 2024). Per le classifiche dei titoli: solo prestito bibliotecario e interbibliotecario.
- **Riconciliazione**: ds2986 e dettaglio coincidono entro l'1% mese per mese (ds2986/dettaglio da 0,977 a 1,033 sulle serie "valide"; entro lo 0,8% sul totale annuo: es. 2013 1.301.765 contro 1.310.897; la differenza è soprattutto il Deposito Boifava, che nel dettaglio è un punto di prestito e nel ds2986 no). Totale gennaio 2013 - giugno 2024: 11.282.072 (ds2986) contro 11.302.398 (dettaglio).
- **Titoli**: chiave = titolo prima della formula di responsabilità (` / `), senza prefisso di volume, senza ": romanzo", minuscolo senza accenti; autore = primo autore, tolte le date `<1956- >` e gli asterischi dei file SBN. Edizioni diverse dello stesso libro si sommano, i volumi di una serie restano separati (L'amica geniale = 4 voci). Visualizzato: la forma più frequente.

## 4. Riepilogo (numeri in `riepilogo.json`)

### 4.1 Prestiti nel tempo (ds2986, campo `Prestiti`)
| Anno | Prestiti | % del 2019 | per abitante |
|---|---|---|---|
| 2013 | 1.301.765 | 125,9 | 0,96 |
| 2014 | 1.288.728 | 124,7 | 0,95 |
| 2015 | 1.213.896 | 117,4 | 0,89 |
| 2016 | 1.109.307 | 107,3 | 0,81 |
| 2017 | 1.037.566 | 100,4 | 0,75 |
| 2018 | 1.009.094 | 97,6 | 0,72 |
| 2019 | 1.033.695 | 100 | 0,74 |
| 2020 | 428.989 | 41,5 | 0,31 |
| 2021 | 612.525 | 59,3 | 0,44 |
| 2022 | 793.072 | 76,7 | 0,57 |
| 2023 | 934.006 | 90,4 | 0,66 |
| 2024 | 983.533 | 95,2 | 0,70 |
| 2025 | 986.954 | 95,5 | 0,70 |
| 2026 (gen-apr, mag parziale) | 342.094 gen-apr | 97,4 sullo stesso periodo del 2019 | |

Abitanti: ds205 (`Totale`, somma dei NIL), 1.353.882 nel 2013, 1.404.431 nel 2019, 1.407.044 nel 2024 (usato anche per il 2025); i non residenti prendono in prestito anche loro (alla Sormani nel 2011, 28,4% dei prestiti di libri era di chi abita fuori Milano, ds101), quindi "per abitante" è un indice, non un tasso di lettura dei milanesi.
- **Prima del Covid**: calo continuo 2013-2018, il 2019 è il primo anno in crescita (+2,4%), gennaio 2020 +7% sul gennaio 2019 e febbraio 2020 -12% (è l'ultimo mese pieno: 74.511). La caduta del 2020 non è l'inizio del calo.
- **Covid**: marzo 2020 12.299 prestiti (13% di marzo 2019), aprile **43** (chiusura totale), maggio 1.814, giugno 31%, luglio-ottobre 45-59%, novembre 2020 12.333 (13%: seconda chiusura), dicembre 40%; gennaio-febbraio 2021 42% e 55%. Il 2021 è al 59% del 2019, il 2022 al 77%, il 2023 al 90%.
- **Dopo**: solo 7 mesi su 60 (2021-2025) hanno superato lo stesso mese del 2019 (agosto 2023, feb-mar 2024, ago 2024, gen-feb 2025, ago 2025). Il 2024 e il 2025 sono fermi attorno al 95%.
- **Il 2019 è una base abbassata dai lavori**: 15 mesi-biblioteca su 300 (5%) sotto il 25% del livello normale (mediana 2024-2025 della stessa biblioteca), 31 nel 2018, 30 nel 2017, contro 5 nel 2025 (`mesi_chiusi_biblioteca_anno.csv`). Dergano ferma da aprile 2018 a dicembre 2019 (4.248 prestiti nel 2019, 38.843 nel 2025), Accursio chiusa fino a inizio 2019, Calvairate chiusa da gennaio 2020 (113 prestiti nel 2020) a metà 2021, riaperta piena nel 2024; Crescenzago e Baggio a regime ridotto nel 2019 (circa il 40% del normale). Il confronto con il 2019 sottostima quindi quanto si è perso rispetto alle biblioteche aperte.

### 4.2 Biblioteca per biblioteca (ds2986, `prestiti_biblioteca_anno_ranking.csv`)
25 biblioteche (24 di quartiere + Sormani) più Bibliobus; sul totale delle biblioteche (escluso bibliobus, smartlocker, ritiri) 963.263 prestiti nel 2025.
- **Più attive 2025** (2024 tra parentesi): Sormani 86.597 (85.938), Lambrate (Valvassori Peroni) 80.439 (77.439), Sicilia 65.276 (63.179), Venezia 62.889 (59.955), Crescenzago 56.366 (54.461). Le prime 3 fanno il 24,1% (2025) e il 23,6% (2024) dei prestiti delle biblioteche.
- **Meno attive, ultimo anno intero 2024**: Harar 14.891, Fra Cristoforo 15.299, Villapizzone 15.771, Sant'Ambrogio 16.021, Cassina Anna 16.023. Rapporto massimo/minimo 5,8 (2024). **Nel 2025 Fra Cristoforo ha 9.013 prestiti perché è praticamente chiusa da giugno a ottobre 2025** (15, 8, 0, 28, 399 prestiti), riapre a novembre con ~1.000 al mese.
- **Variazione 2025 su 2019** (con la cautela dei lavori): Venezia -31,2%, Lambrate -18,5%, Oglio -22,6%, Chiesa Rossa -21,5%, Affori -20,6%; Sormani -1,0%, Parco Sempione -3,8%, Sicilia -5,8%. Salgono solo le biblioteche chiuse o ridotte nel 2019 (Dergano, Crescenzago, Baggio, Accursio, Calvairate). Venezia: l'orario in ds1306 dice "accesso solo su appuntamento".
- **Altri punti di ritiro**: smartlocker 5.181 (2023, solo 3 punti), 10.216 (2024), 13.133 (2025), Zara dal 2025; edicole 6.712 (2021) poi 4.605, 3.622, 2.531 e **0 nel 2025**; librerie 1.512 (2021), 2.469 (2025). Bibliobus 20.241 (2013), 19.360 (2019), 7.347 (2020), 6.922 (2025): -64% su 2019. Il bibliobus ha 5 fermate, ma il dato non le distingue.
- **Per NIL** (`nil_biblioteche.csv`): **65 NIL su 88 non hanno nessuna biblioteca**, 23 ne hanno almeno una (2 NIL con due: Villapizzone-Cagnola-Boldinasco, Stadera-Chiesa Rossa-Torretta-Conca Fallata). Prestiti per 1.000 abitanti del NIL ospitante (solo NIL con almeno 5.000 abitanti): Guastalla (Sormani) 5.598, Bovisa 2.799, Porta Magenta 2.434, Porta Ticinese 2.422, Città Studi 2.226; minimi Quarto Oggiaro-Vialba-Musocco 478, Barona 987, Buenos Aires-Porta Venezia-Porta Monforte 1.006.
- **Per "bacino" (`catchment_biblioteche.csv`)**: ho assegnato ogni NIL alla biblioteca più vicina (distanza tra baricentro del NIL e biblioteca) e diviso i prestiti 2025 per gli abitanti 2024 dei NIL assegnati. Va da 2.732 (Sormani) a 322 per 1.000 abitanti (Parco Sempione) ma **non lo considero sensato come misura**: i dati non dicono dove abita chi prende in prestito, le sedi del centro attirano da tutta la città e fuori (Sormani 2011: 28,4% dei prestiti di libri a non milanesi; per i milanesi 13,6% dalla zona di decentramento 1, 19,6% dalla 4, 14,7% dalla 3), i bacini per vicinanza sono grossolani, e il valore dipende da quanti NIL cadono nel bacino (correlazione di Spearman prestiti per abitante / abitanti del bacino -0,51, p = 0,009). Usabile solo come indicazione "quartieri serviti da poche sedi" con ampie avvertenze.

### 4.3 Chi prende in prestito (ds2986 per età, dettaglio per sesso)
- Quota 65+ dei prestiti: 19,2% (2013), 25,4% (2019), 26,6% (2025). 0-17 anni: 14,0% (2013), 11,5% (2019), 9,8% (2021), 14,2% (2025). Prestiti 0-17 anni: 182.461 (2013), 119.155 (2019), 44.136 (2020), 139.677 (2025). Prestiti 65+: 249.560 (2013), 262.795 (2019), 262.720 (2025): gli anziani sono tornati al livello 2019, i ragazzi sì ma partendo da un 2019 già basso.
- Donne: 57,9% (2013), 61,2% (2019), 64,1% (2024) dei prestiti (resto: uomini, "N", vuoto). Gli iscritti dei file annuali (adulti + ragazzi, `statistiche_annuali_biblioteca.csv`): 100.683 (2013), 77.918 (2019), 44.438 (2020), 71.639 (2023); sono tesserati registrati, non utenti attivi, e la definizione può essere cambiata.

### 4.4 Cosa si legge: titoli, autori, gusti
- **Solo libri a stampa e audiolibri (`media = LIBRI E AUDIOLIBRI`)**: i titoli diversi passano da 113.748 (2013) a 147.026 (2023); la quota dei primi 100 titoli da 4,6% a 3,1%; il primo titolo da 1.272 prestiti a 473.
- **Il titolo più prestato per anno** (`top_titoli_anno.csv`): 2013 *Fai bei sogni* (Gramellini) 1.272; 2014 *E l'eco rispose* (Hosseini) 948; 2015 *L'amica geniale, storia della bambina perduta* (Ferrante) 982; 2016 *La ragazza del treno* (Hawkins) 1.471; 2017 *La ragazza del treno* 788; 2018 *L'amica geniale* vol. 1 (Ferrante) 416; 2019 *Patria* (Aramburu) 425; 2020 *La misura del tempo* (Carofiglio) 255; 2021 *I leoni di Sicilia* (Auci) 408; 2022 e 2023 *Cambiare l'acqua ai fiori* (Perrin) 601 e 473; 2024 (gennaio-giugno) *La portalettere* (Giannone) 273. Elena Ferrante occupa le prime posizioni dal 2015 al 2019 con i quattro volumi dell'*Amica geniale*.
- **Autori** (`top_autori_anno.csv`, somma di tutti i titoli): primo posto quasi sempre **Geronimo Stilton** (9.626 prestiti nel 2013, 5.448 nel 2023) contro le guide del **Touring Club Italiano** (primo nel 2019: 6.192); poi Camilleri (7.305 nel 2013, 3.275 nel 2019), Bonelli (fumetti), Simenon, Danielle Steel; **Maurizio De Giovanni sale dal 3° posto 2017 al 2° 2023** (3.773), nel 2023 Calvino è 6° (2.629), Cassar Scalia e Carofiglio 9° e 10° (2.244 e 2.239).
- **Per fascia di età** (`top_titoli_anno.csv`, colonna `fascia_utente`): gli anziani (65+) prendono Casati Modignani (primo in 4 anni su 12), Gramellini nel 2013, Carofiglio, Cassar Scalia; i minori *Diario di una schiappa*, *L'amico ritrovato*, *Il giovane Holden*, *Wonder*, *Il ladro di foglie*.
- **Più italiani**: quota dei prestiti di libri con "traduzione" nella formula di responsabilità (limite inferiore: non tutte le traduzioni lo indicano) dal 35,4% (2013) al 31,0% (2023); tra i primi 100 titoli i tradotti passano da 48 (2013) a 36 (2023) e 34 (2024). Lingua dell'edizione italiana 97,5% nel 2013 e 97,1% nel 2023.
- **Quanto sono recenti**: nessuna tendenza: il 19-25% dei prestiti è di libri usciti nell'anno o in quello prima (22,7% nel 2013, 19,5% nel 2023), età mediana del libro 5-6 anni, oltre 10 anni il 28-32%.
- **Generi**: **il dettaglio non ha un campo genere**. Non l'ho dedotto. Ci sono solo due fotografie: 2011 (ds163, rionali) narrativa 472.828, saggistica 192.522, altro 19.280 prestiti, quindi narrativa 69% dei prestiti classificati; 2016 (ds909, 24 rionali con dati) narrativa 391.797, saggistica 155.048, multimediali 292.149. Guardando le liste, molti titoli di testa sono gialli e romanzi italiani, ma sono impressioni mie, non misure.
- **DVD/film** (`top_non_libri_anno.csv`): in testa titoli di film recenti (*Il cigno nero* 694 nel 2013, *La La Land* 354 nel 2019, *Nomadland* 200 nel 2023).

### 4.5 Il sistema in rete
- Il campo `loan.from_library_dec` (biblioteca proprietaria del libro) e `loan.to_library_dec` (biblioteca in cui si ritira) coincidono sempre fino al 2016; dal 2017 si distinguono: quota di prestiti di volumi di un'altra biblioteca 3,7% (2017), 19,7% (2018), 23,6% (2019), 37,6% (2020), 43,5% (2021), 34,7% (2022), 33,7% (2023), 35,2% (2024). Nei file annuali del Comune i prestiti "in entrata" erano già nel 2013 circa 5.000 per biblioteca, quindi il fenomeno esisteva ma non era registrato come tipo di prestito.

### 4.6 Prima del 2013 (solo biblioteche rionali, Sormani esclusa)
Prestiti delle rionali: 874.187 (2007), 904.513 (2008), 1.040.075 (2011, ds99); libri 56,1%, 56,4%, 62,6%, il resto DVD (30%, 33%, 31%), audio, VHS. Anni 2009, 2010, 2012 non esistono. I valori non sono confrontabili al prestito con il ds2986 (i file 2007-2011 contano per biblioteca di prestito e per tipo di opera, senza Sormani né bibliobus nello stesso modo): indicano una crescita 2007-2011. Il 2013 è il primo anno completo di ds2986 e il più alto della serie 2013-2026; non so cosa sia successo nel 2012.

## 5. Cose strane e trappole

1. **"Interbibliotecario" cambia significato nel 2017**: fino al 2016 tutto è "prestito bibliotecario" con biblioteca di partenza = biblioteca di ritiro; dal 2017 il 23-44% dei prestiti ha il volume di un'altra biblioteca (consegna del sistema). Non è un prestito tra sistemi diversi. Il tipo "interbibliotecario" non va letto come attività nuova: è registrazione nuova. Non confrontare il campo "da biblioteca" prima/dopo.
2. **Date di fine**: il dettaglio si ferma a giugno 2024; ds2986 arriva a maggio 2026 ma **maggio 2026 è incompleto** (15.800). Il 2024 nel dettaglio è solo gennaio-giugno: confrontare solo semestri.
3. **Chiusure per lavori** nelle serie per biblioteca (punto 4.1): non leggere le variazioni per biblioteca come domanda. `mesi_chiusi_biblioteca_anno.csv` ne dà il conto.
4. **Periodici**: compaiono nel dettaglio solo dal 2018 (media `PERIODICO`): nei confronti uso `LIBRI E AUDIOLIBRI` e `NON BOOK`; "materiale a stampa" nei totali sale di 9-17 mila prestiti all'anno solo per questo.
5. **File annuali del Comune**: ds909 ha 2017 e 2018 con le colonne sfalsate (es. Accursio 2017: "Iscritti adulti" 3, "Iscritti ragazzi" 13); 2016 ha Accursio e Gallaratese a "-"; ds286 (Sormani) nel 2015 scrive 60.455 per 60455 (letto come 60455); ds336 e ds909 sono in encoding diversi (utf-8 e cp1252). "Prestiti locali" dei file annuali = volumi propri della biblioteca; il ds2986 conta ogni prestito dove viene fatto: ds2986 ≈ locali + in entrata + periodici.
6. **Record senza titolo vero**: 39.306 prestiti di libri (0,48%) hanno come titolo solo un numero ("1", "2") e nessun autore (volumi di opere in più parti catalogate male): fuori dalle classifiche e dalla concentrazione, dentro i totali (`libri_titolo_solo_numero_anno.csv`). Autore vuoto nel 5,1% dei prestiti di libri; caratteri non latini sostituiti da "?" nell'1,1% (autore) e nell'1,9% (titolo) dei prestiti: gli stessi autori con grafie diverse possono restare separati.
7. **Le classifiche dei titoli misurano anche le copie acquistate**: un titolo ha tanti prestiti anche perché la biblioteca ne ha comprate molte copie (e c'è la lista d'attesa); non è domanda pura. Gli autori in testa sono serie e guide (Stilton, Touring Club, Bonelli = fumetti).
8. **I prestiti non sono lettori**: non c'è il tesserato, quindi niente "lettori distinti", niente prestiti per lettore. "Iscritti" dei file annuali = tesserati registrati (non per forza attivi).
9. **NIL dei file**: i campi `from_library_nil`/`to_library_nil` del dettaglio usano nomi di NIL vecchi ("PADOVA", "GUASTALLA", "CITTA' STUDI"...) (Dergano in "BOVISA" è corretto anche oggi, ma Lambrate è in "CITTA' STUDI" e la Sormani in "GUASTALLA", che oggi è il NIL 4): non li ho usati come chiave; ho assegnato i NIL io con le coordinate (punto 3).
10. **Il ds2986 non è un dataset di titoli**: niente titoli, niente sesso. I titoli arrivano solo dal dettaglio.
11. **Licenza Istat non indicata**: non ho ripubblicato nulla di Istat; qui c'è una sola cifra citata. ICCU CC0 ok.
12. **Il bibliobus** ha 5 fermate ma una sola serie; in `nil_biblioteche.csv` non ha NIL.
13. **Il formato "CSV" dei dataset mensili è uno zip** (un csv di 5-30 MB dentro); marzo-maggio 2020 sono csv semplici.
14. **Digitale assente**: niente MLOL, quindi ogni "prestiti totali" è fisico. Dopo il 2020 una parte dei lettori può essere passata al digitale senza apparire qui.

## 6. Cosa potrebbe mostrare una pagina

- **La curva 2013-2026** dei prestiti totali con i tre periodi (calo, Covid, ripresa) e il confronto libri / DVD in due linee: il punto forte è che i libri non sono mai calati quanto sembra.
- **"Che cosa legge Milano"**: il titolo più prestato di ogni anno con i prestiti (lista 2013-2024), l'autore dell'anno, la classifica per fasce (ragazzi, adulti, anziani).
- **Biblioteca per biblioteca**: mappa dei 25 punti con prestiti per anno e animazione 2013-2025, con le chiusure per lavori segnalate (mesi chiusi); le più attive e le meno attive.
- **Il tuo quartiere**: quale biblioteca è più vicina (NIL), quanti prestiti, ma senza "per abitante" del bacino (vedi 4.2).
- **Chi prende in prestito**: età e sesso nel tempo (invecchiamento, più donne, ritorno dei ragazzi).
- **Dentro la rete**: quota di prestiti di volumi di altre biblioteche dal 2017, smartlocker, edicole e librerie.
- **Gli anni del Covid mese per mese** (aprile 2020: 43 prestiti).
- Avvertenze sempre visibili: solo prestito fisico, niente digitale; dettaglio fino a giugno 2024; nessun lettore distinto; classifiche influenzate dalle copie.

## 7. Cosa non ho fatto

Nessuna pagina, nessun grafico. Nessun account. Non ho cercato i prestiti digitali oltre una ricerca sul web. Non ho classificato i generi. Non ho usato il Sistema Bibliotecario Milano (sito) perché i due indirizzi provati non rispondono. Non ho aggiornato né modificato JOURNAL.md o docs/. Nessun git.
