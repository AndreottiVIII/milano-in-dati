# Neve e nebbia a Milano - note della fase 1 (raccolta e controllo)

Domanda: a Milano nevica meno, o in modo diverso (meno episodi ma più forti)? E "che fine ha fatto la nebbia?".
Stato: fase 1 (raccolta e controllo) finita il 30/10/2026; fase 2 (pagina) fatta il 30/10/2026, vedi la sezione "Fase 2" in fondo. Tutto scaricato in blocco con programmi (nessun login, nessuna registrazione).

## 1. Fonti, indirizzi, data di scarico (30/10/2026)

| Fonte | Indirizzo | Cosa è | File scaricati |
|---|---|---|---|
| NOAA ISD (Integrated Surface Database), versione completa (non "Lite": la Lite non ha il tempo presente) | https://www.ncei.noaa.gov/pub/data/noaa/AAAA/USAF-WBAN-AAAA.gz | osservazioni orarie/tri-orarie, un file per stazione e anno | `raw\noaa\isd\160800-99999\` (80 file, 21 MB), `raw\noaa\isd\160660-99999\` (60 file, 22 MB), `raw\noaa\isd\160810-99999\` (9 file, 1,4 MB) |
| NOAA GSOD (Global Summary of the Day) | https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/AAAA/16080099999.csv | riassunto giornaliero (flag FRSHTT, SNDP, VISIB, PRCP, TEMP) | `raw\noaa\gsod\16080099999\` (69 file, 5,5 MB), `...\16066099999\` (60 file, 4,9 MB), `...\16081099999\` (9 file, 0,4 MB) |
| Storia delle stazioni ISD | https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv (e .txt) | date di inizio/fine, coordinate, quota | `raw\isd_history\isd-history.csv` (2,9 MB) |
| Inventario ISD | https://www.ncei.noaa.gov/pub/data/noaa/isd-inventory.txt | n. osservazioni per mese | `raw\isd_history\isd-inventory.txt` (17,8 MB). TRAPPOLA: per queste stazioni mostra solo il 2020-2025, non è usabile per gli anni vecchi; i conteggi veri li ho fatti io dai file |
| Documentazione | isd-format-document.pdf, isd readme, gsod readme (stessa cartella NOAA) | codici e licenza | `raw\isd_history\` |

Totale scaricato: circa 55 MB. Download riprendibile: `python -I scripts\scarica_isd_gsod.py <percorso_assoluto>\raw\noaa` (salta i file già presenti). Registro: `raw\noaa\log_download.txt`. Nessun errore, solo i 404 degli anni in cui NOAA non ha il file.

Stazioni (da isd-history.csv):
- **LINATE**: USAF-WBAN 160800-99999, WMO 16080, ICAO LIML, 107 m, inizio record 1931. È la serie principale.
- **MALPENSA**: 160660-99999, WMO 16066, ICAO LIMC, 234 m, inizio 1965. Serve di confronto.
- **LINATE_160810**: 160810-99999, "MILANO/LINATE", solo SYNOP 2005-2009 e 2015-2018 (1480 giorni). Duplicato del SYNOP di Linate sotto un altro numero. NON usato nei totali; tenuto nel file giornaliero con il nome `LINATE_160810`.
- Brera (strand 1) non esiste in ISD: per la temperatura uso `..\temperature\serie\serie_unica.csv` (solo lettura).

GSOD di Linate 1975-2025 era già in `..\temperature\raw\gsod_linate\`: ho verificato che i 51 file sono identici byte per byte a quelli che ho riscaricato (stesso hash). Il programma legge la mia copia, ma sono gli stessi dati.

## 2. Copertura (da `pulito\completezza_per_anno.csv`)

LINATE ISD (giorni con almeno 4 ore di osservazioni, per anno):
- 1931-1938: solo 1-2 osservazioni al giorno, con buchi (167-356 giorni/anno). Non utilizzabile per contare giorni di neve/nebbia.
- 1939-1950: NESSUN file.
- 1951-1955: ogni ora (24 ore/giorno), anno completo (il 1951 solo da ottobre). 1956 completo a metà (274 giorni). 1957: 2,5 osservazioni/giorno, mezzo anno. 1958: 4/giorno. 1959-1961: UNA osservazione al giorno (non basta). 1962-1963: nessun file. 1964: solo 113 giorni.
- 1965-1970: ogni 3 ore (8/giorno), anni completi. 1971: solo gennaio-marzo. 1972: nessun file.
- 1973-1983: ogni ora (METAR + SYNOP), completo.
- 1984-1989: solo SYNOP ogni 3 ore (i METAR mancano nell'ISD, anche se l'aeroporto li emetteva), completo ma più rado.
- 1990-2025: ogni ora, completo. Dal 1994 al 1998 le osservazioni orarie sono circa 16-20 al giorno (mancano alcune ore, soprattutto di notte). 2019: 351 giorni; 2024: 359; 2025 solo fino al 24 agosto.
- Inverni (novembre-marzo) con dati sufficienti (almeno 90% dei giorni con 4 ore o più): 65 inverni a Linate (1952-1956, 1958, 1965-1971, 1974-2025, mancano 1957, 1959-1964, 1972, 1973 e prima del 1952).

MALPENSA ISD: 1965 (solo 14 giorni), 1966-1971 (3-orario), 1972 mancante, 1973-2025 ore. 57 inverni sufficienti (1967-1971, 1974-2025).

GSOD Linate: 1951-1958, 1964-1971, 1973-2025 (mancano 1959-1963 e 1972). GSOD Malpensa: 1965, 1966-1971, 1973-2025 (manca 1972).

## 3. Tabelle prodotte (`pulito\`)

- `giorni_neve_nebbia.csv` - una riga per stazione e giorno (50.313 righe; Linate 27.600, Malpensa 21.233, LINATE_160810 1.480). Il "giorno" è il giorno UTC (come in GSOD), non quello locale. Colonne principali: `isd_n_obs`, `isd_n_hours` (ore diverse con almeno un rapporto), `isd_n_synoptic_hours` (ore 00,03,...,21 UTC), le bandiere di neve e nebbia (sotto), `min_vis_m`, le bandiere GSOD (`gsod_snow`, `gsod_fog`, `gsod_sndp_cm`, `gsod_prcp_mm`, `gsod_tmean_c`) e `report_types` (quanti rapporti per tipo). Vuoto = dato non esistente per quel giorno (ISD o GSOD assente), non zero.
- `inverni_neve_nebbia.csv` - totali per stazione e inverno (novembre-marzo, etichetta = anno di gennaio: inverno 2012 = nov 2011 - mar 2012). Contiene giorni attesi, giorni con dati (`pct_days_ge4h`, `winter_complete_isd` = "si" se almeno 90%), tutte le definizioni, profondità massima, pioggia equivalente nei giorni di neve GSOD, temperatura media nov-mar di Brera (`brera_tmean_nov_mar`, dalla serie unica del strand 1) e di Linate (GSOD).
- `totali_annuali.csv` - lo stesso per anno solare (la nebbia c'è anche in ottobre e aprile).
- `completezza_per_anno.csv` - per stazione e anno: giorni con dati, ore medie al giorno, quota di osservazioni con tempo presente e con visibilità, n. rapporti SYNOP e METAR/SPECI, rapporti con testo METAR completo, quota di METAR "AUTO", n. rapporti di profondità neve.
- `isd\isd_giorni_*.csv` e `isd\isd_diagnostica_*.csv` - passaggio intermedio (un file per stazione ISD). Programmi: `scripts\estrai_isd.py` poi `scripts\costruisci_giorni.py` (si rifà tutto con `python -I scripts\estrai_isd.py <abs>\raw\noaa\isd <abs>\pulito\isd` e `python -I scripts\costruisci_giorni.py <abs cartella strand>`).

## 4. Definizioni (tutte mantenute, mai mescolate)

Neve (un giorno conta se c'è almeno una osservazione che soddisfa):
- `snow_obs_strict`: tempo presente "neve in atto" - codici WMO 4677 (MW) 70-75, 77, 78, 85, 86; codici automatici (AW) 70-73, 85-87; METAR automatico (AU) neve o granuli di neve. Esclusi diamond dust (76) e ice pellets (79). QUESTA è la definizione principale.
- `snow_obs_wide`: strict + pioggia e neve mista (MW 68, 69, 83, 84; AW 45, 46, 67, 68) + neve nell'ora precedente (MW 22, 23, 26; AW 24).
- `snow_heavy_obs`: neve forte (MW 74-75, AW 73/87, AU intensità forte). Pochissimi casi, serve solo come indizio per "meno episodi ma più forti".
- `snow_synoptic_hours`: come strict ma contando solo le osservazioni delle ore 00,03,...,21 UTC (al massimo 8 al giorno): campione omogeneo nel tempo, utile per confrontare anni con 8 e anni con 24 osservazioni al giorno.
- `snow_metar_text`: neve letta direttamente nel testo del METAR (SN, SG; esclusi BLSN e DRSN), solo dal 2006.
- `snow_depth_isd_gt0` e `gsod_snow_depth_gt0`: profondità di neve al suolo maggiore di zero (campo ISD AJ1 e GSOD SNDP).
- `gsod_snow`: flag neve/ice pellets di GSOD (terza cifra di FRSHTT).
- Nelle tabelle inverno c'è anche `snow_days_union_any` = neve strict OPPURE profondità > 0 OPPURE flag GSOD.

Nebbia:
- `fog_code_strict`: almeno un'osservazione con codice di nebbia sulla stazione (MW 41-49, AW 30-35, AU nebbia FG senza descrittore).
- `fog_code_wide`: strict + nebbia nell'ora precedente, nebbia lontana, nebbia bassa (MW 28, 40, 11, 12; AW 20; AU qualunque FG).
- `fog_code_vis_lt1km`: nebbia (wide) nello stesso rapporto con visibilità sotto 1000 m. **Consigliata per confrontare gli anni**, perché la definizione internazionale di nebbia è visibilità < 1 km.
- `vis_lt1km_any`: la visibilità minima del giorno è sotto 1000 m, a prescindere dal codice (comprende anche foschia fitta, pioggia/neve forte).
- `fog_synoptic_code` e `fog_synoptic_code_vis_lt1km`: come sopra, solo ore sinottiche.
- `fog_metar_text` (FG/BCFG/MIFG/PRFG/FZFG nel testo) e `fog_metar_text_dense` (FG, FZFG, PRFG): dal 2006.
- `gsod_fog`: flag nebbia GSOD (prima cifra di FRSHTT).
- Qualità: scartati i valori con codice di qualità 2, 3, 6, 7 (sospetto/errato).

## 5. Risultati preliminari (solo numeri, nessuna interpretazione; inverni completi, medie per decennio dell'etichetta)

Linate, giorni di neve per inverno nov-mar (`snow_days_strict`): anni 1950 (1952-56,58): 10,5; 1960 (1965-69): 8,0; 1970: 10,5; 1980: 9,0; 1990: 5,8; 2000: 7,1; 2010: 8,3; 2020 (2020-2025): 2,0. Singoli inverni: da 0 (1990, 2025) a 21 (1986). Neve forte (codici "forte"): 0-3 giorni per inverno, mai oltre. Correlazione inverno per inverno tra giorni di neve e temperatura media nov-mar di Brera: circa -0,6 (Linate, 65 inverni).
Linate, giorni di nebbia per anno solare (`fog_code_vis_lt1km`, anni con dati completi): 1950: 121; 1960: 121; 1970: 108; 1980: 85; 1990: 79; 2000: 62; 2010: 53; 2020-2024: 52.
Malpensa: neve strict 7, 11, 12, 7, 9, 10, 2 (decenni 1960-2020); nebbia (vis<1 km) 90, 101, 123, 106, 55, 34, 32 giorni per anno.
Questi numeri sono preliminari: vedi le trappole sotto prima di usarli.

## 6. Cambi di strumenti/modalità trovati (non è clima)

1. **1984-1989, Linate**: nell'ISD ci sono solo i SYNOP ogni 3 ore (i METAR mancano). I conteggi con l'insieme completo delle osservazioni sono quindi meno sensibili; per questo ho creato le colonne "sinottiche" (stesse 8 ore in tutti gli anni).
2. **1994-1998, entrambe le stazioni**: le osservazioni scendono a circa 9.000 l'anno (da 20.000-27.000) e la quota di rapporti con "tempo presente" scende al 40%; dal 1999 risale al 98%. In quegli stessi anni i giorni di nebbia calano insieme a Linate e a Malpensa (Malpensa: 142 giorni nel 1994, 95 nel 1995, 58 nel 1998). Sospetto di cambio di codifica/di flusso dati, non solo di clima.
3. **1999-2004**: quasi ogni rapporto METAR ha un codice di tempo presente anche se non c'è nulla (92%); dal 2006 il codice c'è solo quando c'è un fenomeno (circa 30%). Quindi "assenza di codice" non vuol dire "dato mancante" dopo il 2005, ma lo vuol dire prima. Per questo non ho usato la quota di tempo presente come misura di completezza dei giorni.
4. **2006**: nell'ISD compare per la prima volta il testo completo del METAR (campo REM). Da lì i giorni di nebbia per codice di Linate salgono (SYNOP a ore sinottiche: 46 nel 2005, 69 nel 2006) mentre i giorni con codice di nebbia E visibilità < 1 km non salgono: dal 2006 il codice nebbia comprende anche nebbia a banchi (BCFG, MIFG) con visibilità sopra 1 km. A Malpensa lo stesso stacco si vede dal 2016-2018. Per questo motivo `fog_code_vis_lt1km` è più omogenea di `fog_code_strict` e di `gsod_fog`.
5. **Differenza Linate-Malpensa (giorni di nebbia con vis<1 km)**: Malpensa ha 28-70 giorni in più per anno nel 1982-1994, differenza vicino a zero nel 1998-2005, poi Linate ha 15-30 giorni in più dal 2006. Salti a 1982, 1995-1998, 2006: sono candidati a cambi non climatici (strumenti di visibilità, metadati: Malpensa ha quota 211/234 m e coordinate che cambiano nel 1981, nel 1998 e nel 2013; Linate cambia coordinate nel 1986, 1998-2000, 2010, 2013).
6. **Automazione**: nell'ISD i METAR di Linate con la parola AUTO compaiono dal 2018 (1,1% nel 2018, 5,1% nel 2019, 23,1% nel 2020, 11,6% nel 2021, poi 1-5%). Sono quasi tutti emessi di notte (ore 21-04 UTC). Nello stesso periodo compaiono i gruppi AW (tempo presente automatico: 77 rapporti nel 2018, 500 nel 2020). Controllo fatto sulle notti nov-feb 2019-2025: nei METAR AUTO la visibilità è sotto 1 km nel 22% dei casi e nel testo c'è FG nel 19,5%; nei METAR non automatici 11,6% e 11,3%. Non c'è quindi sottostima da parte dei sensori, ma il campione AUTO è piccolo e non confrontabile (periodi di chiusura notturna/Covid). Il tipo di rapporto "AUTO" nel campo tipo (non nel testo) compare solo 8 volte (2005-2012). Non c'è nessun file che dichiari quando i sensori sono entrati in servizio: andrebbe chiesto a ENAV/Aeronautica o all'ARPA.
7. **2013-2017**: la visibilità manca nel 18-36% dei rapporti ISD di Linate (probabilmente i CAVOK); torna a posto nel 2018. Non tocca `vis_lt1km_any` (se c'è nebbia c'è la visibilità).
8. **Coordinate Linate**: SYNOP e METAR hanno posizioni diverse in ISD dal 2010 (SYNOP 45,450 N 9,267 E, 104 m; METAR 45,445 N 9,277 E, 108 m): due punti di osservazione o due codifiche. Prima del 1956 la quota era 120 m, poi 103-107 m.

Nessun salto improvviso "pulito" è stato attribuito al clima prima di aver escluso questi cambi; la parte di analisi spetta alla fase 2.

## 7. Trappole dei dati

- **Profondità della neve inaffidabile**: tutti i rapporti ISD di profondità (campo AJ1, 11.011 rapporti) hanno il codice di condizione "9 = mancante" anche con un valore presente, e compaiono valori assurdi (264, 287 cm a Linate nel gennaio 1991; 225 cm nel febbraio 1985; 179 e 269 cm nel 2002-2003 in giorni senza neve). GSOD SNDP copia questi valori. Nel file giornaliero i valori oltre 60 cm sono tolti da `snow_depth_isd_cm` e `gsod_sndp_cm` (restano in `snow_depth_isd_cm_raw` e segnalati con `snow_depth_suspect_gt60`). Dal 2012 quasi non ci sono più rapporti. Non usare la profondità per la frase "episodi più forti" senza un'altra fonte (ARPA/Brera).
- **Giorno UTC**, non locale: alcune nebbie/nevicate notturne vengono spezzate tra due giorni.
- **Numero di ore osservate cambia molto** (da 1 a 24 al giorno, vedi sezione 2): un conteggio "giorni con almeno una osservazione di nebbia" favorisce gli anni con più osservazioni. Usare `isd_n_hours`, le colonne sinottiche e la colonna `winter_complete_isd`.
- **Inverni incompleti**: gli inverni con meno del 90% dei giorni utili hanno `winter_complete_isd` = "no"; i totali ci sono lo stesso nella tabella ma non vanno confrontati. Sono tutti i 1931-1938, 1957, 1959-1964, 1972, 1973 (solo gennaio-marzo) a Linate.
- **GSOD ≠ ISD per la nebbia**: GSOD segnala nebbia con una regola che comprende anche i casi larghi (nebbia a banchi, ora precedente). Dal 2006 i giorni di nebbia GSOD sono 10-30 più alti di quelli con vis<1 km. Per la neve, GSOD e ISD strict concordano quasi sempre (GSOD un po' più alto perché comprende ice pellets).
- Il testo METAR dà qualche giorno di neve in più del codice ISD (126 contro 115 giorni a Linate da giugno 2006): nei METAR le nevicate miste (RASN) e le segnalazioni "SG" non sempre diventano codici ISD.
- **Inventario ISD inutilizzabile** per gli anni vecchi (vedi sezione 1).
- **Neve in Linate 1988-1990** (1, 1, 0 giorni): inverni davvero poveri di neve, ma in quegli anni il campione è solo sinottico ogni 3 ore; non confrontare direttamente con gli anni a 24 ore senza usare le colonne sinottiche.
- Anni non coperti da ISD né GSOD: 1939-1950, 1962-1963, 1972 (Linate); 1972 (Malpensa).

## 8. Licenza

I dati NOAA sono pubblici e gratuiti per uso di ricerca e non commerciale. Ma NOAA scrive (readme ISD): "The non-U.S. data in ISD are subject to WMO Resolution 40 restrictions, and cannot be redistributed to other users or customers" e (readme GSOD) che per i dati non statunitensi "the data or any derived product shall not be provided to other users or be used for the re-export of commercial services". I dati italiani sono quindi dati WMO Risoluzione 40.
Conseguenza pratica: **NON ripubblicare i file raw** (`raw\`) né, per prudenza, il file giornaliero completo sul sito pubblico. Sul sito si possono mostrare grafici e totali per inverno/anno con citazione "NOAA NCEI, Integrated Surface Database e Global Summary of the Day, stazioni Milano Linate e Malpensa". Il punto "prodotti derivati" va deciso da Davide prima di pubblicare tabelle scaricabili.

## 9. Cosa manca / da fare

- Una seconda fonte di verifica per la neve e la profondità (ARPA Lombardia, Osservatorio di Brera, Servizio Meteorologico AM): il progetto "temperature" ha già Brera per la temperatura.
- Informazioni ufficiali su quando Linate e Malpensa hanno cambiato strumenti di visibilità/tempo presente (non nei dati NOAA).
- Anni mancanti 1939-1950, 1962-1963, 1972; l'inverno 2026 (nov 2025 - mar 2026) non esiste ancora nei dati (ultimo giorno 24/08/2025).
- (Fase 1: nessuna analisi di tendenza né grafico. La fase 2 ha fatto la pagina, ma NON una vera analisi di tendenza: solo medie per decennio e confronti.)

## 10. Fase 2: la pagina (30/10/2026)

Pagina: `docs/neve-e-nebbia/index.html` (statica, legge `docs/neve-e-nebbia/data/*.json` con `fetch(...,{cache:'no-cache'})`), stile uguale a `docs/aria`. Non toccato `docs/index.html` (la voce in home va aggiunta a parte). Si rifanno i dati con `python -I scripts/pagina_dati.py [<cartella strand> [<cartella uscita>]]` (di default legge `pulito/` e scrive in `../docs/neve-e-nebbia/data`). Anteprima: server "milano-in-dati" (porta 8796), `http://127.0.0.1:8796/neve-e-nebbia/`; nessun errore in console, nessuno scorrimento orizzontale a 375 px.

File di dati pubblicati (solo conteggi derivati, mai osservazioni né il file giornaliero, per la Risoluzione 40 WMO): `inverni.json` (per stazione e inverno: giorni di neve strict/forte/larga/8 ore/GSOD, completezza, temperatura Brera nov-mar; correlazioni), `anni.json` (per anno: nebbia vis<1 km, solo codice, 8 ore con vis<1 km, GSOD), `decenni.json` (medie dei soli completi), `ricordi.json` (classifiche inverni, serie di giorni consecutivi con neve, elenco dei giorni con codice di neve forte), `meta.json` (bande, regola, date).

Scelte:
- Completezza: inverno o anno completo se almeno il 90% dei giorni ha 4 ore o più di osservazioni (stessa regola di `winter_complete_isd`). Solo i completi entrano nelle medie per decennio (decennio dell'etichetta; inverno = anno di gennaio). Linate 65 inverni e 63 anni completi dal 1950; Malpensa 57 e 57. Il grafico parte dal 1950 (nel 1931-38 ci sono 1-2 osservazioni al giorno).
- Neve: definizione principale `snow_obs_strict`; "forte" impilata sopra. Nebbia: due serie, `fog_code_vis_lt1km` (consigliata) e solo codice (`fog_code_strict`). Controllo con le 8 ore sinottiche (nebbia vis<1 km calcolata dal file giornaliero) nella tabella a scomparsa.
- Bande grigie con lettera su ogni grafico, ricavate dalle ore osservate al giorno: A ott 1956 - dic 1961 (Linate 1-4 osservazioni al giorno), B ago 1964 - mar 1971 (ogni 3 ore), C ago 1983 - nov 1990 (Linate solo SYNOP: inizio e fine sono quelli veri dei dati, non "1984-89"), D lug 1993 - dic 1998 (da 24 a 16-20 ore al giorno; tempo presente 40-50% nel 1994-98), E 2005-06 (cambio codifica), F dal 2018 (METAR AUTO, solo Linate). A e B sono aggiunte rispetto alla richiesta, perché i dati le mostrano.
- Neve e temperatura: correlazione Linate -0,62 (Spearman -0,65, 65 inverni), -0,66 senza gli inverni 2008-2016 (anni in cui Brera segna circa 0,65 gradi in più, vedi pagina Temperature), Malpensa -0,60. Detta solo come associazione; gli inverni 2008-2016 sono cerchi vuoti nel grafico.
- "Da ricordare": nei dati le bandiere giornaliere sono 0/1, quindi non si possono ordinare le nevicate per quantità; la pagina ordina gli inverni per giorni di neve e mostra le serie di giorni consecutivi e i giorni con codice di neve forte, con la lettera della banda accanto se cadono in un periodo dubbio. Nessuna descrizione inventata, nessun valore grezzo (né pioggia né profondità) pubblicato.
- Cosa si vede nei numeri (non ancora spiegato): Linate neve 10,5 / 8,0 / 10,5 / 9,0 / 5,8 / 7,1 / 8,3 / 2,0 giorni per inverno (decenni 1950-2020), non monotona; nebbia (vis<1 km) 121 / 121 / 108 / 85 / 79 / 62 / 53 / 52. Differenza Linate meno Malpensa per la nebbia: +18 (1966-78), -46 (1982-94), +5 (1998-2005), +18 (2006-24): troppo variabile per essere solo clima, fa pensare a cambi di strumento o di registrazione.

Da fare: voce in `docs/index.html` (non toccato qui); seconda fonte per la neve (ARPA/Brera); chiedere a ENAV/ARPA le date dei cambi di sensore; eventuale decisione di Davide su tabelle scaricabili (per ora nessuna).
