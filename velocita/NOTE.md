# Quanto vanno veloci tram e bus (velocita)

Pagina: bozza in `bozze-grafici/velocita-v2/index.html`, anteprima in `docs/anteprima/velocita/`. Non pubblicata, non nel menu.

## Dati
- Comune di Milano, orari GTFS (ds929), CC BY 4.0, copia in `bici-auto-mezzi/raw/gtfs/ext_comune_new/` (feed 425, aggiornato 29/10/2026, valido fino al 30/11/2026).
- Giorno: martedì 24 novembre 2026, il giorno feriale (mar-gio) con più servizi attivi (123), lo stesso di Attesa alla fermata. Vale anche per il metrò.

## Metodo
- `scripts/prepara.py`: per ogni corsa del giorno (25.133) lunghezza del tracciato (shapes) tra la posizione della prima e dell'ultima fermata, durata dalla partenza al primo capolinea all'arrivo all'ultimo. Scrive `lavoro/corse.csv` (3 MB, di lavoro: si rigenera con lo script, va tenuto fuori da git).
- `scripts/calcola.py`: scarta le corse che coprono meno della metà della lunghezza mediana della loro linea (795, rientri e tratte brevi); mediana per linea, per fascia (punta 7-9 e 17-19, metà giornata 10-15, sera dalle 21) e per ora di partenza (5-25). Linee "di Milano" = almeno 60% del tracciato dentro il confine dei quartieri: 102 linee (16 tram, 4 filobus, 82 bus); le altre 54 sono escluse. Scrive in `docs/velocita/data/`: linee.json, tratte.json (percorsi semplificati e ritagliati), riepilogo.json, linee.csv, nil.geojson (copia di quello di negozi).
- `scripts/verifica.py`: rifà tutto in modo indipendente (csv, haversine vera, ricerca a mano della fermata più vicina) e confronta i 6 numeri.
- Filobus = linee 90, 91, 92, 93 (nel file sono segnate come bus).

## Numeri in alto (verificati, tutti coincidono)
1. Tram: mediana delle 16 linee 10,7 km/h.
2. 60 linee su 102 sotto i 15 km/h (tutti i 16 tram).
3. Alle 8 la linea mediana va il 24% più piano che alle 22 (61 linee con dati in entrambe le ore).
4. Meno di 2,5 fermate/km: 21 km/h (27 linee); più di 3,5: 12 km/h (17 linee).
5. Linea più lenta: bus 176 (Ingresso - Campo 12), 8,1 km/h.
6. Metrò: mediana 28,5 km/h (M1 27,6, M2 28,5, M3 31,2, M4 30,1, M5 26,8), 2,7 volte il tram.

## Limiti
Velocità dell'orario, non reale (niente ritardi né traffico); soste incluse; un solo giorno; i bus di quartiere (BdQ) hanno 16-30 corse e sono i più veloci; il tracciato è quello caricato dal Comune.

## Aggiornamento 15/11 (mappa al centro, tratti, metrò)
- Pagina rifatta: numeri in alto, mappa grande dei tratti con select dell'ora (tutto il giorno, 8, 13, 18, 22), classifica dei 15 tratti più lenti, profili di 6 linee (tram 9, 1, 15, filobus 91, bus 60, bus 80). Tolti: barre per linea, ore, punti fermate/km, barre metrò.
- `scripts/tratti.py` scrive `docs/velocita/data/tratti.json` (186 KB, 1.020 tratti, 82 linee). Per linea: percorso più usato, sequenza di fermate più comune, fermate unite in tratti di almeno 400 m (mediana circa 600 m). Velocità = metri sul tracciato tra prima e ultima fermata del tratto / (arrivo - partenza), mediana delle corse del 24/11/2026 che toccano entrambe; fasce: tutto il giorno, 8 (partenze 7-9), 13 (10-15), 18 (17-19), 22 (dalle 21). Tratti con meno di 10 corse o velocità fuori da 2-60 km/h senza dato. Esclusi i bus di quartiere (BQ) e i notturni (BN): anelli e poche corse, fermate non assegnabili al tracciato (davano 110 e 156 km/h). Un verso solo; dove le linee si sovrappongono si vede la più lenta (non c'è una mediana tra linee diverse sullo stesso tratto).
- `scripts/verifica_tratti.py`: ricalcolo indipendente. Km sotto 15 km/h: 75,3% alle 8 (pagina 75), 35,8% alle 22 (pagina 36), tratto più lento T27 Piazza Fontana - Largo Augusto 4,7 km/h. Differenze sotto 1 punto per la diversa ricerca del punto più vicino.
- Numeri in alto ora: 10,7 km/h tram; 60 linee su 102; 24% più piano alle 8 che alle 22; 75% dei km sotto la bici alle 8 (36% alle 22); 4,7 km/h tratto più lento; metrò 28,5 km/h (2,7 volte il tram).
- Metrò: vedi `metro/scripts/tempi.py` (docs/metro/data/tempi.json), capitolo «Quanto ci metti» nella bozza metro-v2: scambio fisso 4 minuti, percorsi solo sulla rete del metrò.
