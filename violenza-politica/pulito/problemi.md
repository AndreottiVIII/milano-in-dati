# Problemi e trappole dei dati (violenza politica, 29/10/2026)

## Differenze tra fonti
- **Attentato alla Fiera 1928**: Wikipedia dice 14 morti subito + 6 nei giorni dopo (20); Wikidata (P1120) ne ha 14. Nel sito: 20, con nota.
- **Strage del Diana 1921**: infobox «17 morti, 4 successivamente», testo «21 morti, 80 feriti», Wikidata 21. Usato 21.
- **Piazza Fontana**: 17 morti e 88 feriti (voce e Wikidata); la voce sulla Questura 1973 scrive «16 morti di Piazza Fontana» (incoerenza interna di Wikipedia).
- **Bombe del 25 aprile 1969**: infobox «circa 15 feriti», cronologia «5 feriti» allo stand FIAT.
- **Tavecchio 1972**: tabella 1972 = 14 marzo, cronologia anni di piombo = 11 marzo. Usato 14 marzo. Non esiste una voce propria (la riga della tabella non ha link).
- **Omicidio Grandi 1978**: tabella 8 novembre, cronologia 7 novembre; nome «Giampietro» (tabella) / «Giampiero» (cronologia).
- **Omicidio Mazzanti 1980**: la tabella 1980 mette «Sesto San Giovanni», la voce e la cronologia dicono via Orseolo, Milano. Messo a Milano.
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
26 casi con il motivo. Da decidere: Ambrosoli (1979), Abbruciati (1982), Saronio (1975), Lahderi (1980), Pasqua Rossa (1946). Wikipedia mette Ambrosoli e Abbruciati nell'elenco degli anni di piombo, ma i responsabili non sono gruppi politici.

## Fuori dal Comune (esclusi)
Sesto San Giovanni (Padovani, Bazzega, Alasia 1976), Segrate (Feltrinelli 1972), Settimo Milanese (Frasca 1981), Lissone (Renzi 1982), Rho, Robbiano di Mediglia, Vernio (Rapido 904, 1984).

## Eventi attesi che non abbiamo trovato (o trovato senza dati)
- **Bomba al ristorante Cova (7 ago 1920)**: solo citata nella cronologia, senza vittime indicate.
- **Attentato alla caserma Santa Barbara (ottobre 2009)**: nessuna voce su Wikipedia it trovata (la ricerca restituisce solo la voce sulla caserma).
- **Bombe del 12 dicembre 1969 oltre a quella di piazza Fontana**: il secondo ordigno (inesploso, Banca Commerciale) è solo citato nella voce.
- **Petar Chaulev (1924)**: trovato solo tramite la query Wikidata C (omicidio a Milano) e la voce inglese; la voce italiana non esiste. Incluso come omicidio politico, senza luogo preciso.
- **Viale Tibaldi 1944**: quattro partigiani fucilati, trovati tramite Wikidata C (Abico, Alippi); inclusi.
- **Morti della Resistenza e della liberazione a Milano (1945)** e uccisioni del dopoguerra (Volante Rossa, 1945-49): Wikipedia ne parla in voci generali e in biografie senza voce evento; inclusa solo Brunilde Tanzi. È una lacuna nota.
- **Anni 1946-1968**: quasi nessun evento nelle fonti usate (es. 1948 dopo l'attentato a Togliatti, 1960, 1962): non cercati uno per uno, perché fuori dalle tabelle e dalle cronologie lette.
- **Dopo il 1993**: unico evento il 2003 (Dax). Nessun attentato con morti trovato.
- **Gambizzazioni e azioni senza morti degli anni di piombo**: non incluse (categoria «Persone gambizzate durante gli anni di piombo» non percorsa).
- **Morte di Giuseppe Pinelli**: inserita come «scontro o custodia» perché Wikipedia non la classifica come omicidio.

## Dubbi sull'attribuzione del tipo
- Rapine di autofinanziamento con un morto (Saporito 1977, Carloni 1982): inserite come «omicidio politico» perché la cronologia degli anni di piombo le elenca con i gruppi armati; se si vuole essere più restrittivi si possono togliere (confidenza «bassa»/«media»).
- Brigatisti o militanti uccisi dalle forze dell'ordine (Pezzoli, Serafini, Ferrari, Sava): categoria «scontro o custodia».
