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
