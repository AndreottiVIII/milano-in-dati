# Problemi e trappole dei dati (violenza politica, 29/10/2026)

## Differenze tra fonti
- **Attentato alla Fiera 1928**: Wikipedia dice 14 morti subito + 6 nei giorni dopo (20); Wikidata (P1120) ne ha 14 (solo i morti immediati). Riletto in fase 3: vale 20.
- **Strage del Diana 1921**: infobox «17 morti, 4 successivamente», testo «21 morti, 80 feriti», Wikidata 21. Usato 21.
- **Piazza Fontana**: 17 morti e 88 feriti (voce e Wikidata); la voce sulla Questura 1973 scrive «16 morti di Piazza Fontana» (incoerenza interna di Wikipedia).
- **Bombe del 25 aprile 1969**: infobox «circa 15 feriti», cronologia «5 feriti» allo stand FIAT. Riletto in fase 3: la voce dice 5 colpiti direttamente e circa 10 di striscio (15), 5 ricoveri; e dice che il secondo ordigno (Stazione Centrale) esplose senza feriti, mentre la cronologia lo dà per inesploso.
- **Tavecchio 1972**: tabella 1972 = 14 marzo, cronologia anni di piombo = 11 marzo. Risolto in fase 3: 11 marzo = scontri (la tabella scrive «ucciso in seguito agli scontri in piazza dell'11 marzo»; la voce «Sequestro Macchiarini» lo dà morto negli scontri, colpito da un lacrimogeno, in piazza Castello); 14 marzo = data della riga/morte. Nel file `data` = 11/3, `data_morte` = 14/3. Non esiste una voce propria.
- **Omicidio Grandi 1978**: tabella 8 novembre, cronologia 7 novembre; nome «Giampietro» (tabella) / «Giampiero» (cronologia).
- **Omicidio Mazzanti 1980**: la tabella 1980 mette «Sesto San Giovanni», la voce e la cronologia dicono via Orseolo, Milano. Riletto in fase 3: la voce dice via Orseolo all'angolo con via Savona; Sesto è il luogo di lavoro (Falck Unione). Milano.
- **Di Cataldo 1978**: la tabella scrive «Crescenzago» (quartiere di Milano, non un altro comune): incluso.
- **Ramelli, Amoroso, Franceschi, Varalli/Zibecchi**: la data della tabella è quella del decesso o dell'aggressione a seconda della riga; nel file `data` = giorno del fatto, `data_morte` = giorno del decesso.
- **Refusi nelle cronologie**: «William Waccher» per Vaccher, «Alaisa» per Alasia.
- **Incidente aereo al Grattacielo Pirelli (2002)**: Wikidata lo classifica anche come «attacco suicida» e «strage»; Wikipedia lo tratta come incidente. Escluso.
- **Query Wikidata «morti a Milano»** (C): il filtro sulla causa di morte lascia passare quasi tutti (infarti, tumori…): inutilizzabile senza filtro a valle; usata solo per controllo (8 omicidi + 5 per ferita da arma da fuoco, tutti già coperti da altre fonti).
- **Valori «sconosciuto» di Wikidata** per morti/feriti compaiono come indirizzi `genid` invece che numeri: il programma li salta.

## Persone o pagine che non sono eventi
- Le categorie «Anni di piombo» ecc. contengono molte biografie e organizzazioni (BR, Prima Linea, ecc.): non sono eventi, usate solo per scoprire eventi.
- La categoria «Morti a Milano» ha 4.904 persone: ignorata (non indica come sono morte).
- «Moti di Milano» (maggio 1898, Bava Beccaris) cade prima del 1900.

## Eventi esclusi (vedi `esclusi.csv`)
26 casi con il motivo. I cinque «DA DECIDERE» sono stati decisi da Davide il 29/10: Ambrosoli, Abbruciati, Lahderi e Pasqua Rossa sono ora eventi con la nota «Caso incerto: …»; Saronio resta qui perché le voci non dicono che sia morto nel Comune (vedi `aggiunte_fase3.md`).

## Fuori dal Comune (esclusi)
Sesto San Giovanni (Padovani, Bazzega, Alasia 1976), Segrate (Feltrinelli 1972), Settimo Milanese (Frasca 1981), Lissone (Renzi 1982), Rho, Robbiano di Mediglia, Vernio (Rapido 904, 1984).

## Eventi attesi che non abbiamo trovato (o trovato senza dati)
- **Bomba al Cova**: trovata in fase 3: due bombe, 25 giugno 1920 (un capitano dell'esercito ucciso) e 7 agosto 1920 (tre svizzeri feriti), nella voce sulla strage del Diana. Ora due eventi.
- **Attentato alla caserma Santa Barbara (ottobre 2009)**: nessuna voce propria; è descritto nella voce della caserma (it) e in «Terrorismo in Italia» (it/en). Ora un evento.
- **Bombe del 12 dicembre 1969 oltre a quella di piazza Fontana**: il secondo ordigno (inesploso, Banca Commerciale) è solo citato nella voce.
- **Petar Chaulev (1924)**: trovato solo tramite la query Wikidata C (omicidio a Milano) e la voce inglese; la voce italiana non esiste. Incluso come omicidio politico, senza luogo preciso.
- **Viale Tibaldi 1944**: quattro partigiani fucilati, trovati tramite Wikidata C (Abico, Alippi); inclusi.
- **Morti della Resistenza e della liberazione a Milano (1945)** e uccisioni del dopoguerra (Volante Rossa, 1945-49): Wikipedia ne parla in voci generali e in biografie senza voce evento; inclusa solo Brunilde Tanzi. È una lacuna nota.
- **Anni 1946-1968**: in fase 3 cercati nelle voci su Volante Rossa, Tambroni, Togliatti 1948, scioperi, categorie en/it: trovati solo il 1946 (Pasqua Rossa, caso incerto) e gli omicidi del 1947-49 della Volante Rossa. Nessun morto o bomba a Milano nel 1950-1968 nelle voci lette (via Solferino 1968: solo feriti). Gli anni '50 restano vuoti: manca la fonte, non è detto che non sia successo nulla.
- **Dopo il 1993**: oltre al 2003 (Dax), in fase 3 aggiunti Santa Barbara 2009 e due aggressioni alla Stazione Centrale (2017, 2019), tutte senza morti. Nessun attentato con morti trovato dopo il 2003.
- **Gambizzazioni e azioni senza morti degli anni di piombo**: non incluse (decisione di Davide: fuori ambito salvo morti). La categoria «Persone gambizzate durante gli anni di piombo» è stata percorsa in fase 1 ma non usata.
- **Morte di Giuseppe Pinelli**: inserita come «scontro o custodia» perché Wikipedia non la classifica come omicidio.

## Dubbi sull'attribuzione del tipo
- Rapine di autofinanziamento con un morto (Saporito 1977, Carloni 1982): inserite come «omicidio politico» perché la cronologia degli anni di piombo le elenca con i gruppi armati; se si vuole essere più restrittivi si possono togliere (confidenza «bassa»/«media»).
- Brigatisti o militanti uccisi dalle forze dell'ordine (Pezzoli, Serafini, Ferrari, Sava): categoria «scontro o custodia».

## Fase 3 (29/10/2026)
- **Bocconi 2009, lettere-bomba 1998-2000, Duomo 2000, La Scala 1976, NAR 1979**: esclusi con il motivo in `esclusi.csv`. Le due righe della lista tedesca (La Scala 1976, NAR 1979) vengono dalla Global Terrorism Database e non hanno riscontro nelle voci it/en.
- **Hosni 2017**: la lista tedesca scrive 19 maggio, l'identificativo GTD citato è del 18 maggio; messo 18 maggio, confidenza bassa.
- **Eva Maciachini**: tre grafie nelle voci (Maciachini, Macciacchini, Maciacchini). **Massaza**: «Masazza» nella voce inglese.
- **Chiaravalle Milanese**: nel 1922 era un comune a sé; oggi è un quartiere del Comune di Milano (coordinate della voce sul quartiere).
- **Date dedotte**: 23 giugno 1920 (tram di piazzale Loreto) dedotto da «il giorno seguente» nel testo della cronologia.
