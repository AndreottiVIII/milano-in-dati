# Imprese che nascono e muoiono - NOTE (fase 1 + pagina)

Scaricato il 2 novembre 2026. Programmi in `scripts/`, si lanciano con `python -I -X utf8 scripts/<nome>.py <percorso assoluto di imprese> [<percorso assoluto di docs>]` (vedi STATO.md). Dati grezzi in `raw/` (file non fidati, mai eseguiti), tabelle pulite in `pulito/`, pagina in `docs/imprese/` (scritta da `scripts/pagina.py`).

## 1. In breve

1. **La fonte giusta è Movimprese** (InfoCamere per conto di Unioncamere): file annuali "Totale imprese" 2000-2025 con registrate, attive, iscrizioni, cessazioni, per **provincia**, divisione ATECO e forma giuridica; le cancellazioni d'ufficio sono nel file "CDU" dentro lo stesso archivio. Uso e diffusione "consentiti previa citazione della fonte".
2. **Per il solo comune di Milano non ho trovato dati aperti su iscrizioni e cessazioni.** Il Comune pubblica solo lo stock di imprese attive per settore (ds691, 2010-2025) e per forma giuridica (ds1481, 2011-2017, fonte ASIA).
3. **Donne, giovani, stranieri**: Movimprese scaricabile non li ha. Li ho presi dalle tabelle del Rapporto Milano Produttiva della Camera di commercio di Milano Monza Brianza Lodi (edizioni 2019-2026, anni 2018-2025), lette dal testo dei PDF. Si controllano sui totali di Movimprese: coincidono al numero in tutti gli 8 anni.
4. **Quello che torna**: iscritte e cessate (senza d'ufficio) di Milano 2018-2025 uguali alla Camera; tasso di crescita 2025 Milano +2,37%, Monza +1,06%, Lodi +0,38%, Lombardia +1,41%, Italia +0,96% uguali alla tabella 1 del Rapporto 2026; Italia 2025: 323.533 iscritte, 266.934 cessate, 5.849.524 registrate uguali; Milano attive 2025 314.726 uguale. Dal 2021 la colonna "cessazioni non d'ufficio" pubblicata coincide con quella calcolata da me in tutte le righe (`pulito/controlli.json`).
5. **Non ottenuto**: Istat ASIA unità locali per comune (vedi 5.4).

## 2. Fonti, una per una

### 2.1 Movimprese (InfoCamere / Unioncamere)
- Pagina: https://www.infocamere.it/principali-soluzioni/movimprese.html, sezione "Archivio Documenti" (modulo GET senza captcha: `?searchForDownload_anno=<anno>&searchForDownload_periodo=a&searchForDownload_tipo=2d`). I link ai file sono `/dam/jcr:.../<anno>_a_2d.<data>.zip`.
- **Il modulo "Scarica CSV" ha un reCAPTCHA: non l'ho usato né aggirato.** I file dell'archivio documenti sono pubblici e senza captcha.
- Scaricati con `scripts/scarica_movimprese.py` (pausa 1,5 s, User-Agent dichiarato): `raw/movimprese/<anno>_a_2d.zip`, anni 1995-2025, 31 file, 43 MB, hash e URL in `raw/movimprese/download_log.csv`. Anni 1995-1996: Excel vecchi (non usati); **1997-1999: sono programmi eseguibili (.exe), mai aperti**; 2000-2025: file di testo (`movi_YY.txt` con tabulazioni, latin-1) e `CDUAAAA.xls(x)`.
- Condizioni d'uso: PDF di InfoCamere "Movimprese - Condizioni di utilizzo" (aggiornate 30/4/2025), in `raw/web_probe/condizioni.pdf`: l'uso e la diffusione sono consentiti previa citazione della fonte; InfoCamere declina responsabilità sulle rielaborazioni. Glossario: `raw/web_probe/glossario_movimprese.pdf`. Citazione usata: "Movimprese - InfoCamere, per conto di Unioncamere".
- Colonne (da `TRACCIATO.TXT`): REG (registrate), ATT (attive), ISC (iscritte), CES (cessate, lorde), VAR (variazioni), per forma giuridica TOT, SC (società di capitali), SP (società di persone), DI (ditte individuali), AF (altre forme). Dal 2021 anche `CES..NOUFF` (cessazioni non d'ufficio). `PROV = 0` è il totale regionale.
- Ho scelto di non usare `repers.txt`/`capers.txt` (persone con cariche, per sesso ed età): il glossario non ne spiega il significato esatto, e non sono "imprese femminili".
- Non usati: `reunloc` (unità locali), `moviS1/moviS2` (semestri).

### 2.2 Rapporto Milano Produttiva (Camera di commercio di Milano Monza Brianza Lodi)
- Pagina: https://ester.milomb.camcom.it/rapporto-mp ; PDF `https://ester.milomb.camcom.it/sites/default/files/rapporto-mp/<anno>/<file>.pdf`: 2019 `milano-produttiva-2019-parte-1-capitolo-2.pdf` (anno dati 2018), 2020 `01-capitolo2.pdf` (2019), 2021 `02-capitolo-2.pdf` (2020), 2022 `02-capitolo-2.pdf` (2021), 2023 `02-capitolo-imprese.pdf` (2022), 2024 `02-capitolo-imprese.pdf` (2023), 2025 `02-capitolo-imprese0.pdf` (2024), 2026 `02-capitolo-imprese.pdf` (2025). In `raw/camera_commercio/` (PDF e testo estratto `mp<edizione>_cap_imprese.txt`), 8,2 MB.
- **Nessuna licenza dichiarata sul sito** (solo informativa privacy): non ripubblico i PDF, riporto solo i numeri delle tabelle (fatti), con la citazione. Se vuoi essere più prudente si può chiedere alla Camera: `ester` è il sito "Economia e statistica dei territori".
- Tabelle usate: "Imprese iscritte e cessate per settore e tipologia" (tabella 2: righe Totale, forme giuridiche, Artigiane/Giovanili/Femminili/Straniere, colonne Milano) e "Imprese giovanili, femminili e straniere ... per area geografica" (tabella 7 o 8: imprese attive e addetti, riga Milano). I settori della tabella 2 non li uso (alcune cifre dei servizi sono spezzate nel testo del PDF).
- Definizione (Rapporto 2026, nota 8): "femminili, giovanili e straniere" = proprietà e controllo detenuti per più del 50% da donne, da giovani under 35, da cittadini di nazionalità estera.

### 2.3 Comune di Milano (CKAN, CC BY)
- Ricerca CKAN con 7 parole chiave: `raw/comune_ckan/search_*.json` (169 dataset distinti). Scaricati (`scripts/scarica_comune.py`, `raw/comune_<id>/`): ds691 imprese attive per settore 2010-2025, ds1481 imprese per forma giuridica 2011-2017 (ASIA), ds1482 addetti per forma giuridica 2011-2018, ds2954 e ds512 (attività commerciali, serie storica), ds202 (aperture e chiusure di attività commerciali, solo 2018, 530 KB). Usati: ds691, ds1481. Gli altri sono pronti per eventuali approfondimenti sul commercio.
- **ds691: nel 2025 il Comune usa ATECO 2025** (la riparazione di auto e moto passa in "altre attività di servizi"; compaiono "Commercio all'ingrosso e al dettaglio", "Attività editoriali...", "Attività amministrative..."): i settori 2025 non si confrontano con il 2010-2024 (scritto nel campo `notes` del dataset). Il totale invece sì.

### 2.4 Istat ASIA unità locali per comune (CC BY 4.0) - NON OTTENUTO
- Dataflow `183_285_DF_DICA_ASIAULP_1` ("Unità locali e addetti - Principali dati"), dimensioni `FREQ.REF_AREA.DATA_TYPE.ECON_ACTIVITY_NACE_2007.PERS_EMPL_SIZE_CLASS`, tipi dato `LU` (unità locali) e `LUEMPD` (addetti), Milano = `015146`. Elenco dei dataflow e struttura scaricati (`raw/web_probe/istat_dataflow.xml`, `istat_dsd_asiaul.xml`).
- Dopo due richieste riuscite (elenco e struttura) il server `esploradati.istat.it` non accetta più connessioni dal mio indirizzo (timeout di connessione): probabile blocco per limite di richieste (Istat ne ammette poche al minuto). Non ho riprovato in modo insistente. Il programma `scripts/scarica_istat_asiaul.py` è pronto (una sola richiesta per tentativo, tentativi a 10 minuti): `raw/istat_asiaul/log.txt` ha l'esito.

## 3. Pulizia (`scripts/build.py`, risultati in `pulito/`)
- `mov_province_totale.csv`: una riga per anno (2000-2025) e territorio (106 province o regione), solo riga TOT. `mov_milano_settori.csv`: Milano, tutte le righe ATECO (2009-2025; prima del 2009 solo TOT, perché ATECO 2002 non è confrontabile).
- **Cessazioni non d'ufficio = CES - CDU** (CDU dal file `CDUAAAA.xls`, foglio ANNO), come dice il glossario dal 2006. Il file CDU **non ha la riga "NC" (non classificate)**: la ricavo per differenza (TOT meno somma delle sezioni). Per 2000-2005 non esistono le d'ufficio: restano le lorde.
- **Trappole del file CDU**: "NA" (Napoli) letto come valore mancante da pandas, con il risultato che le righe di Napoli finiscono sul totale regionale e la Campania compare due volte (Italia 6.444.059 invece di 5.849.524): corretto con `keep_default_na=False`; controllo sul totale Italia.
- Italia = somma delle righe regione.

## 4. Numeri principali (tutti in `docs/imprese/data/riepilogo.json`, campo `origine`)
- Milano (provincia senza Monza) 2025: registrate 389.542, attive 314.726, iscritte 26.262, cessate lorde 24.606, d'ufficio 7.523, cessate senza d'ufficio 17.083, saldo +9.179, crescita +2,37% (`mov_province_totale.csv`, prov MI, anno 2025).
- Iscritte "non classificate" 2025: 10.394 su 26.262 = 39,6% (`mov_milano_settori.csv`, CODAT NC).
- Forma giuridica 2025: iscritte società di capitali 14.904 (56,8%), ditte individuali 10.107 (38,5%); 2009: 8.296 (36,0%) e 11.298 (49,0%).
- Milano è 2ª su 105 province per crescita nel 2025 (Roma +2,54%), 1ª nel 2023; natalità 6,77% (Italia 5,51%), mortalità 4,41% (Italia 4,54%).
- Straniere: 6.669 iscritte 2025 su 26.262 (25,4%), 56.824 attive su 314.726 (18,1%) (Camera, tabelle 2 e 8).

## 5. Limiti ("trappole") dei dati - sono tutti nella pagina, sezione "Limiti dei dati"
1. Iscritta non è "aperta", cessata non è "chiusa": sono atti del Registro; le registrate (389.542) sono molte di più delle attive (314.726).
2. Cancellazioni d'ufficio: 7.523 nel 2025, 14.962 nel 2007, 501 nel 2016; vanno a ondate per forma giuridica. Cambiano stock (attive, registrate) e cessazioni lorde.
3. Non classificate: ~40% delle iscritte senza settore; i saldi per settore dell'anno sono parziali.
4. Perimetro: Monza e Brianza è provincia a sé dal 2007 (MB compare nei file dal 2007; Milano registrate 443.346 nel 2006, 367.178 nel 2007). La serie "dal 2000" somma MI+MB.
5. ATECO 2025 dal 2025 (Comune); Movimprese 2025 è ancora ATECO 2007 (nota Camera: nuovi codici introdotti dal secondo trimestre 2025).
6. Categorie femminili/giovanili/straniere: soglia >50%; entrare/uscire dalla categoria non è nascere/chiudere (glossario Movimprese).
7. I tassi non sono tassi di sopravvivenza delle nuove imprese.

## 6. Cosa non ho fatto / da decidere
- Istat ASIA unità locali per comune (5.4): da riprovare più tardi.
- Camera di commercio Milano Monza Brianza Lodi: non ho trovato un catalogo di open data; i PDF del Rapporto sono l'unica fonte per le categorie. Se si vuole un dato riutilizzabile con licenza chiara si può scrivere alla Camera (Studi, Statistica e Programmazione).
- Comune: ds202 (aperture e chiusure di attività commerciali, solo 2018) e ds2954/ds512 (commercio al dettaglio) non sono usati nella pagina; si possono unire alle pagine ../botteghe/ e ../ristoranti/.
- Rapporti Camera 2018 e prima (anni 2017 e precedenti) per allungare le categorie.
- Dati per CAP/quartiere non esistono.
