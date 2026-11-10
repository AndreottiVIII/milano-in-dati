# Le Olimpiadi, a cose fatte: note

Bozza in `bozze-grafici/olimpiadi-v2/index.html`. Dati in `docs/olimpiadi/data/`. Programmi in `olimpiadi/scripts/`. Creata il 10/11/2026. Non pubblicata, non nel menu.

## Fonti e licenze

| Fonte | Che cosa | Licenza | Note |
|---|---|---|---|
| Simico, «Open Milano Cortina 2026» (simico.it/piano-delle-opere), pulsante «Scarica i dati»: `simico-ivll-public.s3.eu-south-1.amazonaws.com/data/data-export.zip` | 98 interventi (costo «quadro economico», fase, date, coordinate, ente attuatore) e 596 subappalti | **Non dichiarata** | Dati al 28/8/2026, aggiornati ogni 45 giorni. Scaricati il 10/11/2026 (nel lavoro di esplorazione), copia in `olimpiadi/grezzi/simico/`. |
| Eurostat, passeggeri per aeroporto (avia_paoa), già nella pagina `docs/aeroporti/` | Passeggeri mensili Linate, Malpensa, Bergamo, gen-mag 2025 e 2026 | CC BY 4.0 | Nessun nuovo download. |
| Natural Earth, confini delle province (ne_10m_admin_1_states_provinces) | Sfondo della mappa | Pubblico dominio | Scaricato il 10/11/2026 da raw.githubusercontent.com (User-Agent `milano-in-dati/1.0`), ridotto alle 110 province italiane e semplificato. |
| Comune di Milano (confini), già in `docs/hinterland/data/comuni.geojson` | Per controllare se un'opera cade dentro Milano | come la pagina Hinterland | Risultato: 0 opere su 98. |

## La questione della licenza di Simico

Cercato il 10/11/2026 (User-Agent `milano-in-dati/1.0`, robots.txt rispettato: non vieta le pagine lette):
- pagina del piano delle opere: dice solo che i dati sono «scaricabili in formato aperto» e che hanno «finalità divulgative e informative»; il «Disclaimer» parla solo dell'aggiornamento ogni 45 giorni;
- informativa privacy (`/informative-privacy/`) e pagina Disposizioni generali di Amministrazione trasparente: nessuna parola su licenza, riuso o condizioni d'uso dei dati (cercati: licenza, riutilizzo, riuso, open data, CC BY, copyright, diritti d'autore, termini d'uso);
- nel file scaricato non c'è alcun campo licenza.

**Non c'è nulla di scritto.** Si applica il principio dell'art. 52, comma 2, del Codice dell'amministrazione digitale (d.lgs. 82/2005): i dati che i soggetti dell'art. 2, comma 2 pubblicano senza una licenza espressa si intendono aperti (art. 68, comma 3), tranne i dati personali.

Simico è soggetta, per quanto ho potuto verificare:
- è una società per azioni costituita per legge (art. 3 d.l. 16/2020, «Legge Olimpica»), partecipata dai ministeri dell'Economia e delle Infrastrutture al 35% ciascuno, da Regione Lombardia e Regione Veneto e dalle Province autonome di Trento e Bolzano (5% ciascuna, secondo la pagina «Chi siamo»);
- il suo statuto richiama il d.lgs. 175/2016 (Testo unico sulle società a partecipazione pubblica): è una società a controllo pubblico (lo Stato ha il 70%);
- l'art. 2, comma 2, lettera c, del Codice include le società a controllo pubblico (escluse le quotate); Simico ha anche il Codice IPA (DUAF58ZW).

Conclusione: i dati si possono riusare citando la fonte. È però una lettura della legge, non un permesso di Simico: **conviene chiedere conferma a Simico prima di pubblicare** (e il testo della pagina lo dice). Va anche ricordato che in questa pagina non ci sono nomi di persone fisiche (i subappalti non sono usati).

## Passi

1. `scripts/scarica.py`: scarica i confini delle province (Natural Earth) e li salva in `grezzi/province_italia.geojson`.
2. `scripts/prepara.py`: legge `grezzi/simico/interventi.csv`, i passeggeri della pagina Aeroporti e i confini di Milano; scrive in `docs/olimpiadi/data/` i file `opere.csv`, `riepilogo.json`, `mappa.json`, `aeroporti_giochi.csv`.
3. La pagina legge solo `riepilogo.json` e `mappa.json`: ogni numero e ogni titolo sono calcolati lì.

Uso: `python -I -X utf8 olimpiadi/scripts/scarica.py` (solo la prima volta), poi `python -I -X utf8 olimpiadi/scripts/prepara.py`.

## Numeri di controllo (28/8/2026)

98 opere, 3.624,99 milioni di euro. Per fase: concluso 49 (891,2 milioni, 24,6%), in esecuzione 19 (630,0), in gara 9 (605,4), in progettazione 21 (1.498,4). Giochi 31 opere (466,7 milioni, 12,9%), eredità 67 (3.158,3, 87,1%), di cui strade e ferrovie 45 (2.753,9) e altro 22 (404,4). Lombardia 29 opere / 1.440,3 milioni; Veneto 25 / 1.437,1; Trento 30 / 407,9; Bolzano 14 / 339,7. Dentro il comune di Milano: 0. Concluse con fine lavori entro il 6/2/2026: 45 su 49. Fine lavori dal 2027 in poi: 39 opere, 2.025,4 milioni (55,9%). Senza data di fine: 6.

## Limiti dei dati

- **Licenza non dichiarata** (vedi sopra).
- Il costo è il «quadro economico», una previsione; non è la spesa finale e non dice chi paga gli aumenti.
- **Chi paga non c'è nei dati**: c'è solo il soggetto attuatore (chi realizza) e la stazione appaltante. La pagina lo dice e non lo confonde con chi finanzia.
- **Nessun ritardo misurabile**: c'è una sola data di fine lavori per opera, non quella prevista all'inizio, e non si sa se per le opere non concluse sia prevista. L'unico confronto possibile è la «fine lavori ante-Olimpiadi» (campo presente per 25 opere), che per i cantieri ancora in corso (9) è una scadenza intermedia legata ai Giochi; per le opere concluse (16 di quelle 25) l'etichetta è spesso una data di disallestimento o finitura dopo i Giochi e non è usata. Il grafico lo presenta come «dalla scadenza per i Giochi alla fine lavori attuale», senza parlare di ritardi.
- Una fotografia al 28/8/2026: nessuno storico dei costi.
- Non tutte le opere sono nel piano (gruppi di controllo civico dicono che mancano lavori; non verificato). Nessuna opera del piano è dentro il comune di Milano: le sedi di Milano (San Siro, Santa Giulia, Porta Romana) non compaiono; sono nella pagina `docs/sport/`.
- Ogni opera ha un solo punto: strade e ferrovie lunghe sono rappresentate da una coordinata.
- «Territorio» è quello di Simico (Lombardia, Area Dolomitica Veneto/Trento/Bolzano); nella mappa e nei numeri in alto Trento e Bolzano sono sommate in «Trentino-Alto Adige».
- **Durante i Giochi**: i dati sul sito arrivano a dicembre 2025 per i turisti (Comune e Regione) e il mensile degli aeroporti arriva a maggio 2026. Biglietti e spettatori non sono pubblicati come dati aperti. I passeggeri sono mensili: i Giochi (6-22 febbraio) sono 17 giorni su 28. Il +7,2% di febbraio non si può attribuire ai Giochi: a Linate la crescita c'è tutti i mesi. Aprile 2026 a Malpensa (-14,3%) coincide con la Pasqua in date diverse (20/4/2025, 5/4/2026); non è stata verificata altra causa.
- Correlazione non è causa.
- I subappalti (596 righe) non sono usati: sono nomi di imprese, alcuni di persone fisiche (ditte individuali).
- Senza CIG nel file di Simico non si può legare l'ANAC (la copia ANAC del progetto non ha il CUP).

## Cose da fare / decisioni per Davide

- Decidere se scrivere a Simico per confermare il riuso (consigliato prima di pubblicare).
- Il dettaglio «chi paga» richiederebbe altre fonti (decreti, CIPESS, Regioni): non cercate.
