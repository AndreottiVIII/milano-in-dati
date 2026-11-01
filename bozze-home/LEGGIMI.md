# Bozze della home di "Milano in dati"

Quattro bozze quadrate (1080 × 1080), ferme, senza navigazione. La mappa è quella vera degli 88 quartieri (NIL); i numeri vengono dalle pagine del sito.
Le anteprime in PNG sono nella cartella `anteprime/`. Il programma che disegna le bozze 1-4 è `genera_bozze.py`, quello delle bozze 5-8 è `genera_bozze_2.py` (leggono `docs/` senza toccarlo).

**1. Mosaico (`bozza_1_mosaico.svg`)**
Idea: la mappa dei quartieri al centro, colorata con la quota di stranieri nel 2023, appoggiata sulla croce rossa di Sant'Ambrogio. Intorno, i numeri delle storie in riquadri collegati al quartiere giusto (Comasina, Brera, San Siro, Trenno, Tibaldi, Rogoredo).
Colori: bianco e rosso della bandiera di Milano, nero per i testi.
Cliccabile: ogni quartiere (apre i suoi dati) e ogni riquadro (apre la storia).

**2. Metro (`bozza_2_metro.svg`)**
Idea: la home è una mappa del metrò. Le 17 storie sono fermate su 5 linee a tema (M1 clima e ambiente, M2 chi siamo, M3 muoversi, M4 cultura, M5 passioni e conflitti), con il Duomo al centro. Sotto, in grigio, la sagoma di Milano e i puntini delle 125 fermate vere.
Colori: quelli delle linee M1-M5, fascia rossa in alto come le insegne del metrò.
Cliccabile: ogni fermata (apre la storia), ogni linea (mostra solo le sue storie).

**3. Cerchi (`bozza_3_cerchi.svg`)**
Idea: Milano come città a cerchi. Al centro la Cerchia dei Navigli, i Bastioni (il confine vero di Area C) e la circonvallazione; intorno un anello di 16 storie, ognuna con un piccolo grafico; fuori, l'anello del tempo: una fetta colorata per ogni anno di temperature a Brera, dal 1763 al 2026.
Colori: blu scuro dei Navigli, arancione e giallo dei tram.
Cliccabile: ogni spicchio (apre la storia), ogni anno dell'anello esterno (apre quell'anno nelle temperature).

**4. Manifesto (`bozza_4_manifesto.svg`)**
Idea: un manifesto futurista, alla Boccioni ma di oggi: "MILANO IN DATI" enorme e inclinato, linee di forza, numeri giganti sparsi, la mappa dei quartieri in un tondo bianco.
Colori: rosso Campari, nero, bianco.
Cliccabile: ogni numero grande (apre la sua storia) e il tondo della mappa (apre i quartieri).

Note: la Cerchia dei Navigli e la circonvallazione della bozza 3 sono disegnate a mano (tracciato indicativo); i Bastioni sono il confine vero di Area C. Il 2026 è "il più caldo finora", cioè sullo stesso periodo dell'anno.

## Altre quattro bozze (5-8)

**5. Skyline (`bozza_5_skyline.svg`)**
Idea: lo skyline di Milano al tramonto è un grafico a barre. Ogni torre è alta quanti anni di dati ha la sua storia: Duomo = temperature (dal 1763), Torre Velasca = Scala (1778), Pirellone = cinema spariti (1896), Unicredit = derby (1909), il Dritto = violenza politica (1919), lo Storto = elezioni (1946), il Curvo = neve (1950), Bosco Verticale = censimenti (1991); il tram è Area C (2012). La luna è la mappa degli 88 quartieri.
Colori: cielo dal blu notte al viola, rosa e arancio dell'ora dell'aperitivo; finestre gialle, Duomo rosa come il marmo di Candoglia.

**6. Tabellone (`bozza_6_tabellone.svg`)**
Idea: il tabellone a palette delle partenze di Centrale. Ogni riga è una storia: numero, destinazione, "dal" (anno del primo dato), note ("SOPPRESSI" per i cinema, "IN RITARDO" per le donne nelle vie), binario. Sotto: striscia degli avvisi, pianta della città (88 quartieri e fermate del metrò, "voi siete qui" a Centrale) e il ventaglio dei binari. L'orologio segna le 19:09, l'anno del primo derby.
Colori: nero, giallo e bianco delle palette, blu dei cartelli di stazione.

**7. Galleria (`bozza_7_galleria.svg`)**
Idea: il pavimento dell'Ottagono della Galleria. Al centro la mappa dei quartieri a tessere di marmo, colorata con gli abitanti in più o in meno dal 1991 al 2023; intorno un anello di 88 tessere, una per quartiere, dal più svuotato al più cresciuto (Rogoredo +172%). Agli angoli quattro tondi come gli stemmi, con i numeri grandi; in quello del derby c'è il toro.
Colori: marmi rosso, nero, bianco, verde, giallo, bordi oro.

**8. Navigli (`bozza_8_navigli.svg`)**
Idea: i Navigli come linee del tempo che arrivano tutte in Darsena (il 2026). Naviglio Grande = temperature, l'acqua cambia colore anno per anno dal 1763; Martesana = derby, barche blu (Inter) e rosse (Milan) ormeggiate sulle due rive, boe bianche per i pareggi; Cerchia = Scala, uno spicchio giallo per stagione; Pavese = cinema spariti, largo quanto le sale aperte, e si asciuga. Nel cartello, la mappa vera con i Navigli al loro posto.
Colori: verde prato, blu acqua, giallo, rosso e blu delle squadre.

Note sulle bozze 5-8: i tracciati dei Navigli (bozza 8) sono schematici, anche quelli nel cartello sono indicativi. Nel Pavese entrano solo le sale oggi chiuse (119 aperte nel 1960; con le sale ancora aperte erano 123). Nella bozza 7 i quartieri a righe grigie hanno un dato poco solido (pochi abitanti).

## Altre quattro bozze (9-12)

Il programma che le disegna è `genera_bozze_3.py` (riusa i due precedenti, legge `docs/` senza toccarlo).

**9. Insegne (`bozza_9_insegne.svg`)**
Idea: una piazza di notte piena di insegne al neon. Ogni numero è un'insegna appesa al muro di mattoni: 246 derby (Inter 91 in blu, Milan 84 in rosso), 4.635 titoli alla Scala, e l'insegna CINEMA mezza spenta, come le 171 sale sparite. La mappa degli 88 quartieri è un contorno luminoso, con Comasina (38% stranieri) e Rogoredo (+172% abitanti) accese. In basso un tubo lungo che sale: la temperatura a Brera dal 1763, dal blu al rosso. Una freccia a lampadine dice "ENTRA".
Colori: fondo quasi nero, neon rosso, ciano, rosa, giallo, verde, viola.

**10. Prima pagina rosa (`bozza_10_prima_pagina.svg`)**
Idea: la prima pagina di un quotidiano sportivo inventato, su carta rosa, con la testata "Milano in dati" (nessun giornale vero). Titolone: "246 DERBY, L'INTER AVANTI DI 7", con il tabellino 91-71-84. Al posto delle foto: il saldo dei derby partita per partita dal 1909 (blu quando comanda l'Inter, rosso quando comanda il Milan) e la mappa dei quartieri in mezzatinta (più puntini, più stranieri; Comasina 38%). Sotto: "Brera, caldo da record" con una barra per anno dal 1763, le brevi (cinema, Area C, elezioni, violenza politica) e il sommario delle 17 storie.
Colori: carta rosa, nero, rosso e blu delle squadre.

**11. Memphis (`bozza_11_memphis.svg`)**
Idea: il design Memphis di Milano (anni Ottanta): colori che litigano, ghirigori, terrazzo. Il ghirigoro nero in alto è la temperatura a Brera (media su 11 anni) che sale; la mappa è una lastra di terrazzo con lo spessore, con quattro quartieri colorati (Comasina, Trenno, Tibaldi, Rogoredo); i derby sono tre totem alti quanto le vittorie (Inter 91, pari 71, Milan 84). In basso: un ventaglio per la Scala, 123 triangoli per i cinema del 1960 (28 accesi, quelli aperti oggi) e un tondo per Area C.
Colori: rosa, ciano, giallo, blu elettrico, arancio, nero e bianco.

**12. Tram Ventotto (`bozza_12_tram.svg`)**
Idea: il tram arancione del 1928 attraversa la piazza. Ogni finestrino è una storia con il suo numero (1763, 4.635, 246, 171, 167, 84, 19,6%, −16%, 88%), la porta centrale è "salite". In alto il cartello del percorso: la mappa vera con una "linea 17" inventata che passa per i quartieri delle storie (Comasina, Trenno, San Siro, Brera, Duomo, Tibaldi, Rogoredo). A sinistra la palina della fermata "Duomo"; sotto, binari e pavé a coda di pavone.
Colori: cielo blu cobalto, arancione del tram, nero, pavé di porfido.

Note sulle bozze 9-12: le curve della temperatura (bozze 9 e 11) sono medie mobili sugli anni completi, quindi il 2026, ancora in corso, non è nella curva ma solo nelle scritte ("il più caldo, finora"). Nella bozza 10 la barra rossa più alta a destra è il 2026 in corso. La "linea 17" della bozza 12 non è una linea vera: unisce i quartieri delle storie. Nessun marchio vero (giornali, aziende, ATM) è usato.

## Scelte di Davide (30/10/2026)

Tenute da parte: **1 mosaico, 2 metro, 6 tabellone, 9 insegne al neon**. Le altre restano come archivio.

## Altre quattro bozze (13-16)

Il programma che le disegna è `genera_bozze_4.py` (legge `docs/` senza toccarlo; fa anche le anteprime PNG). Solo grafica: immagini ferme, niente pulsanti né pagine che funzionano. Numeri solo quelli già usati nelle bozze precedenti (da `docs/`), più i titoli delle 19 storie.

**13. Cantiere (`bozza_13_cantiere.svg`)**
Idea: la home come un cartello di "lavori in corso". Strisce oblique nere e gialle in alto e in basso, "MILANO" enorme e "IN DATI" su targa nera. Le 19 storie sono 19 piastre numerate (01-19) a scacchiera nero/bianco, la ventesima è la mappa dei 88 quartieri.
Colori: giallo cantiere, nero, bianco, un tocco di arancione del lampeggiante.

**14. Manifesto modernista (`bozza_14_modernista.svg`)**
Idea: un manifesto da design italiano anni Sessanta, tutto minuscolo e pesante. Fascia rossa a sinistra con "milano in dati" in verticale, la mappa piena in blu, un cerchio giallo con "88", un quadrato nero con "1763 → 2026", poi l'indice delle 19 storie come una lista numerata.
Colori: rosso, blu cobalto, giallo, nero su bianco pieno.

**15. Terminale (`bozza_15_terminale.svg`)**
Idea: lo schermo di un terminale di borsa, fitto di dati. Barra di comando "STORIE <GO>", elenco delle 19 storie con sigla, il grafico vero delle temperature a Brera dal 1763, la mappa a calore degli stranieri nel 2023, le barre del derby, le "quotazioni" grandi e il nastro dei numeri in basso.
Colori: nero con arancione ambra, verde e rosso per su e giù.

**16. Risografia (`bozza_16_riso.svg`)**
Idea: una stampa a due colori fatta a mano, con i colori che non combaciano bene e si sovrappongono. Titolo "MILANO" in blu con l'ombra rosa sfalsata, la mappa a puntini rosa (più punti, più stranieri) con il contorno blu spostato, l'elenco delle 19 storie come etichette, e sotto una barra per ogni anno di temperature.
Colori: rosa fluo e blu, che sovrapposti diventano viola scuro; carta bianca con un po' di grana.

## Bozze 17-20 (alla Noorda)

Direzione di Davide: mappa di Milano, numeri e colori di Milano, semplice e pulita come la segnaletica del metrò di Bob Noorda (1964). Tutte con la mappa vera degli 88 quartieri al centro, pochi numeri veri, un solo carattere (Helvetica/Arial, due pesi), fondo bianco o grigio chiarissimo, colori piatti, niente ombre né grana. Il programma è `genera_bozze_5.py`; fa anche il foglio con tutte le bozze 1-20 (`anteprime/tutte_le_bozze.png`).

**17. Fascia MM (`bozza_17_mm.svg`)**
Idea: la fascia rossa con la scritta bianca dei cartelli del metrò, con il quadrato della "M". Sotto, la mappa grigia con Comasina in rosso e, a destra, quattro numeri (1763, 246, 4.635, 38%) separati da righe nere sottili.
Colori: rosso MM, nero, bianco, grigio chiaro per la mappa.

**18. Poster a griglia (`bozza_18_griglia.svg`)**
Idea: un poster svizzero. Titolo piccolo in alto a sinistra, la mappa grande come unica immagine (bianca con contorni neri), quattro numeri giganti (1763, 246, 4.635, 88) in colonna con righe sottili.
Colori: grigio chiarissimo, nero, un solo rosso per il titolo, il 1763 e Comasina.

**19. Le cinque linee (`bozza_19_linee.svg`)**
Idea: le 19 storie raggruppate come le linee del metrò: M1 clima e ambiente, M2 chi siamo, M3 muoversi, M4 cultura, M5 passioni e conflitti. Mappa grigia al centro con una fermata colorata per linea; sotto, cinque colonne con la linea, il nome del gruppo e le storie.
Colori: bianco, grigio, e i colori delle linee: rosso, verde, giallo, blu, lilla.

**20. Croce rossa (`bozza_20_croce.svg`)**
Idea: la bandiera di Milano, la croce rossa su fondo bianco, a tutta pagina. La mappa bianca con i contorni rossi è appoggiata al centro della croce; quattro numeri rossi nei quattro angoli (1763, 246, 4.635, 88).
Colori: solo rosso e bianco, un po' di nero per le scritte piccole.

## Copertina di tutte le ricerche (21-24)

Svolta di Davide: la home non deve avere due numeri "spot", ma essere la copertina di tutte le ricerche. Qui ogni storia è presente con un numero vero e, dove costa poco, una piccola figura fatta con i suoi dati (serie, barre, barra di percentuale, puntini). Sono 20 storie pubblicate più "Alberi" e "Affitti brevi" segnate "in arrivo": 22 in tutto. Linguaggio Noorda: bianco, colori piatti, Helvetica/Arial, righe sottili. Il colore è il tema (le linee del metrò: M1 clima e ambiente, M2 chi siamo, M3 muoversi, M4 cultura, M5 passioni e conflitti).

**Formato: 1600 × 1600**, non 1080 (con 22 storie e numeri leggibili 1080 è stretto). Programma: `genera_bozze_6.py` (legge `docs/` senza toccarlo; da dove viene ogni numero è scritto nei commenti della funzione `dati()`). Foglio con le quattro: `anteprime/bozze_21_24.png`.

**21. Tessere (`bozza_21_tessere.svg`)**
Idea: una griglia 5 × 5 di tessere uguali, come i cartelli del metrò. Una tessera per storia (nome, numero, frase, figura), più la tessera del titolo, la mappa dei 88 quartieri e la legenda dei colori.
Colori: bianco, nero, rosso per i numeri, fascia colorata (colori delle linee) in cima a ogni tessera.

**22. Mappa con le storie (`bozza_22_mappa.svg`)**
Idea: la mappa di Milano al centro e le schede in due colonne ai lati, ognuna unita con una linea a un punto della città (Scala alla Scala, derby a San Siro, aria in viale Marche, Cerchia per Area C, Palazzo Marino per elezioni e bilancio...). I punti sono indicativi: per alcune storie non c'è un luogo vero.
Colori: mappa grigio chiaro, linee e bordi nei colori delle linee, numeri rossi.

**23. Linea del tempo (`bozza_23_tempo.svg`)**
Idea: una riga per storia; la barra parte dal primo anno dei dati e arriva al 2026, il numero è a destra. Si vede subito che le serie lunghe (beni culturali, temperature, Scala) e quelle recenti (bici, 15 minuti) non hanno la stessa età. Le storie "di oggi" (donne nelle vie, nomi delle fermate) hanno un puntino.
Colori: barre nei colori delle linee, numeri rossi, righe grigie alternate.

**24. Sommario (`bozza_24_sommario.svg`)**
Idea: l'indice di un giornale o di un rapporto annuale: due colonne, storie raggruppate per linea (M1-M5), ognuna con nome, frase, numero grande e figurina. In alto la fascia rossa con la mappa piccola.
Colori: rosso, bianco, nero, pallini e figure nei colori delle linee.

Note sui numeri (tutti letti da `docs/`):
- La Scala: 4.737 è il numero di titoli diversi (senza i concerti) calcolato dal file `scala/data/titoli.json`; non coincide con il "4.635" delle bozze 1-12 (che non sono riuscito a ricostruire dal file attuale). Da controllare con la pagina.
- Area C: −15% è la media dei giorni feriali 2024 contro 2019 (`area-c/data/tabelle.json`), non il −16% delle bozze 1-12 (altro modo di calcolo).
- Bici: 88% = media pesata alle 8 di `bici-auto-mezzi/data/quote.json`. Neve: 10,5 → 2 sono le medie degli anni Cinquanta e degli anni Venti (questi ultimi incompleti).
- Temperature: "n. 1" = il 2026 è il più caldo su 264 anni nello stesso periodo (finora).
- Nelle bozze 21-24 non ci sono i numeri più "tondi" di prima (1763, 246...) tranne dove sono la cifra vera della storia (derby 246, cinema 171, elezioni 167, violenza politica 84, beni culturali 27.459).
