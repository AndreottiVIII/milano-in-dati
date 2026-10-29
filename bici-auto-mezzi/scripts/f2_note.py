import pandas as pd, json, sys
S = sys.argv[1]
q = pd.read_csv(S + '/out/quote_vittorie.csv', sep=';', encoding='utf-8-sig')
md = pd.read_csv(S + '/out/tempi_mediani.csv', sep=';', encoding='utf-8-sig')
inc = json.load(open(S + '/out/incidenti_geo_stima.json', encoding='utf-8'))
def tab(fa):
    s = q[q.fascia_oraria == fa]
    t = '| Distanza in linea retta | coppie | bici % | auto % | mezzi % | vittoria netta (>=10%) % | mezzi non raggiungibili % |\n|---|---|---|---|---|---|---|\n'
    for _, r in s.iterrows():
        t += '| %s | %d | %.1f | %.1f | %.1f | %.1f | %.1f |\n' % (r.distanza_in_linea_retta, r.coppie, r.bici_pct, r.auto_pct, r.mezzi_pct, r.netta_10pct_pct, r.mezzi_non_raggiungibili_pct)
    return t
def tabm(fa):
    s = md[md.fascia_oraria == fa]
    t = '| Distanza | bici | auto (solo guida) | auto (porta a porta) | mezzi | a piedi |\n|---|---|---|---|---|---|\n'
    for _, r in s.iterrows():
        t += '| %s | %s | %s | %s | %s | %s |\n' % (r.distanza_in_linea_retta, r.bici_min, r.auto_guida_min, r.auto_porta_a_porta_min, r.mezzi_min, ('%s' % r.a_piedi_min if r.a_piedi_min == r.a_piedi_min else '-'))
    return t
ti = inc['tipo_indirizzo']; sq = inc['stima_quote_pct']
note = open(S + '/NOTE.md', encoding='utf-8').read()
if '## Fase 2' in note: note = note[:note.index('---\n\n## Fase 2')].rstrip() + '\n'
P1 = """
---

## Fase 2 - motore bici / auto / mezzi (29 ottobre 2026, nessuna pagina del sito, nessun git)

Tutto e' Python puro (numpy, scipy, numba, pyproj, shapely, matplotlib): niente Java, niente Docker, niente servizi a pagamento o con chiave. Script in `scripts\\f2_*.py`, dati intermedi in `out\\`, tutte le ipotesi in `scripts\\f2_parametri.py`. Comandi per rifare tutto in `STATO.md`.

### 1. Orari dei mezzi aggiornati
- ATM/AMAT, riscaricato il 29/10/2026: `raw\\gtfs\\gtfs_comune_milano_amat_new.zip` (25,5 MB, estratto in `ext_comune_new\\`). **Versione 425, validita' 26/10/2026 - 30/11/2026** (file `feed_info.txt` e `calendar_dates.txt`, 36 giorni). Il vecchio file (versione 424, fino al 20/11) resta in `raw\\gtfs\\`. Da riscaricare dopo il 30/11.
- Trenord: file invariato (validita' fino al 12/12/2026, vedi fase 1).
- Giorno usato nel calcolo: **martedi' 3 novembre 2026** (giorno feriale normale). Corse attive quel giorno: ATM 25.133 (116.218 collegamenti tram, 61.672 metro, 385.902 bus/filobus), Trenord 2.893 (30.363 collegamenti treno, piu' i bus sostitutivi). In tutto 594.155 collegamenti tra fermate vicine e 5.485 fermate (`out\\gtfs_info.json`).

### 2. Come e' fatto il motore
- **Reti**: dal ritaglio OSM del 29/10/2026 (`out\\osm_parsed.pkl`) si costruiscono tre grafi (`out\\g_walk.npz`, `g_bike.npz`, `g_car.npz`), tenendo solo la parte connessa piu' grande: piedi 647.424 nodi e 24.597 km di archi, bici 384.345 nodi e 12.674 km (9.824 km veloci come una ciclabile: `highway=cycleway`, sentieri `bicycle=designated`, strade con corsia/pista scritta), auto 294.350 nodi e 8.819 km (sensi unici rispettati).
- **Percorsi**: Dijkstra di scipy da un punto verso tutti (bici, auto, piedi). Per l'auto, lungo l'albero dei percorsi si calcolano anche i km percorsi e se il percorso passa dentro Area C.
- **Mezzi pubblici**: algoritmo "Connection Scan" (scritto con numba) sul GTFS del giorno: a piedi dall'origine alle fermate entro 800 m, attesa dall'orario vero, cambi con margine di 45 secondi e a piedi fino a 300 m (21.294 collegamenti pedonali tra fermate, calcolati sulla rete pedonale, tra ATM e Trenord compresi), a piedi dall'ultima fermata alla meta entro 800 m. Si fa la **media di 6 partenze** (ora, +2, +4, +6, +8, +10 minuti) per non dipendere da un orario fortunato. Massimo 2 ore di viaggio.
- **Celle**: 2.915 celle di 250 m con il centro dentro il confine del Comune (181,8 km2). Di queste, 124 sono in Area C, 492 nel "semicentro" (entro 3,5 km dal Duomo), 2.299 in periferia. 423 celle (14,5%) non hanno nessuna fermata entro 800 m (parchi, campagna del sud, zone industriali): per i mezzi risultano irraggiungibili.
- **Tempi di calcolo** (PC con i5-12600K): caricare il motore 1 s, preparare le 2.915 destinazioni 2 s (una volta sola), **una partenza verso tutte le celle: 0,1-0,3 s per fascia oraria** (l'obiettivo era 30 s). 300 partenze x 2.915 celle x 3 fasce (2,6 milioni di coppie) in circa 105 secondi.
- **Fuori rete**: se l'origine o la meta sono lontane dalla strada piu' vicina, il tratto si fa a piedi in linea retta (a 5 km/h per la bici, a 4,5 km/h per le altre); fino a 727 m per l'auto (parchi).

### 3. Tabella delle ipotesi (tutte da tarare con i 20 tragitti)
| Cosa | Valore usato | Da dove viene |
|---|---|---|
| Velocita' a piedi | 4,5 km/h | mandato |
| Attesa semaforo, a piedi | 10 s | ipotesi mia |
| Bici su pista ciclabile (e strade con corsia/pista) | 15 km/h | mandato |
| Bici su strada normale | 13 km/h | mandato |
| Bici su strada di servizio / living street | 12 km/h | ipotesi mia |
| Bici su area pedonale con `bicycle=yes/designated` | 10 km/h | ipotesi mia |
| Bici a mano (area pedonale, `bicycle=dismount`) | 5 km/h | mandato |
| Bici su sterrato (`track`) | 10 km/h; fondo non asfaltato x0,8; pave' x0,85 | ipotesi mia |
| Attesa media a un semaforo, bici | 15 s | mandato |
| Attraversamento senza semaforo di una strada primary/secondary/trunk | 8 s | ipotesi mia |
| Semafori sulle ciclabili e marciapiedi | i gruppi di semafori entro 30 m (incrocio piu' attraversamenti) pesano 1/radice(n) ciascuno; sulle strade contano solo i semafori d'incrocio e gli attraversamenti semaforici isolati (nessun incrocio entro 40 m, deduplicati) | mia scelta, per non contare 4 volte lo stesso incrocio |
| Sensi unici per la bici | rispettati, tranne `oneway:bicycle=no` o corsie contromano (`cycleway=opposite*`, `cycleway:*:oneway=-1/no`) | mandato |
| Vietato alla bici | autostrade, `trunk` (salvo `bicycle=yes/designated`), `bicycle=no`, accesso privato, scale, `footway` senza `bicycle` | mandato + mia scelta |
| Bici: aprire e chiudere il lucchetto | 60 s in totale | ipotesi mia |
| Auto: velocita' di marcia tra un semaforo e l'altro, 08:00 / 12:00 / 21:00 (km/h, PRIMA della taratura) | autostrada 45/70/90; svincoli 30/40/50; trunk 35/45/60; primary 26/34/40; secondary 23/30/36; tertiary 21/27/32; unclassified 20/24/28; residential 18/22/25; servizio 12/14/15; living street 10 | ipotesi mia (valori tipici) |
| Auto: limite scritto in OSM (`maxspeed`) | velocita' mai oltre l'85% del limite | ipotesi mia |
| Auto: attesa media a un semaforo | 20 s (08:00), 15 s (12:00), 10 s (21:00) | ipotesi mia |
| Auto: taratura | un fattore per fascia, 0,916 (08:00), 1,056 (12:00), 1,158 (21:00): il tempo medio ogni 10 km sul percorso, per viaggi di 6-14 km, esce uguale all'obiettivo | `scripts\\f2_taratura.py` |
| Auto: obiettivo 08:00 | **38 min 43 s ogni 10 km** (15,5 km/h) | TomTom Traffic Index, pagina Milano, dati 2025, ora di punta mattina (https://www.tomtom.com/traffic-index/milan-traffic/). Stesso sito: media sull'anno 31 min 35 s ogni 10 km; 2022: 27 min 30 s |
| Auto: obiettivi 12:00 e 21:00 | 27 min e 21 min ogni 10 km (22 e 29 km/h) | **ipotesi mia**, non c'e' un dato libero per le due fasce: da tarare con Google Maps |
| A piedi fino all'auto e dal parcheggio alla meta | 2 min + 2 min | mandato (letto come 2 min per parte) |
| Ricerca parcheggio alla meta | Area C 12 min, semicentro (entro 3,5 km dal Duomo) 8 min, periferia 4 min | mandato (valori), raggio del semicentro scelto da me |
| Area C | si paga 7,50 euro se la meta e' dentro o il percorso passa dentro (non conta se si parte da dentro), lun-ven 7:30-19:30; alle 21:00 non si paga. Il costo non e' nei tempi | tariffa dal PDF del Comune; **orari ancora da verificare** (sezione 5 sopra); poligono: `area-c\\raw\\ds51_aree-pedonali-e-ztl\\disciplina_aree.geojson` (tipo `AREA_C`) |
| Mezzi: a piedi alla fermata | massimo 800 m (rete pedonale vera, 4,5 km/h), fermata agganciata alla rete entro 150 m | mandato |
| Mezzi: cambi a piedi | massimo 300 m di rete pedonale; margine minimo 45 s per cambiare mezzo | mandato + ipotesi mia (45 s) |
| Mezzi: partenze | martedi' 3/11/2026 alle 08:00, 12:00, 21:00, media di 6 partenze nei 10 minuti dopo | mia scelta |
| Mezzi: dati usati | ATM versione 425 (metro, tram, bus, filobus) + Trenord (S, RE, R e bus sostitutivi); niente tempo reale, niente ritardi, niente biglietti | fase 1 |

### 4. Primi risultati: chi arriva prima (300 partenze a caso x 2.915 celle, martedi' 3/11/2026)
Confronto "porta a porta": bici (con 1 min di lucchetto), auto (guida + 2 + 2 min a piedi + ricerca del parcheggio), mezzi (a piedi, attesa, viaggio, a piedi). Non conta il costo (Area C 7,50 euro, biglietti, carburante). Le celle senza fermate entro 800 m (14,5%) non permettono ai mezzi di vincere. La coppia con origine e destinazione nella stessa cella e' esclusa. "Vittoria netta" = il primo batte il secondo di almeno il 10%. File: `out\\quote_vittorie.csv`, `out\\tempi_mediani.csv`.

**Ore 08:00**
"""
P2 = """
Tempi mediani in minuti, ore 08:00 (`out\\tempi_mediani.csv` ha anche le altre fasce):
"""
P3 = """
Cose da notare (non sono risultati finali, i numeri vanno prima tarati):
- La bici vince nei viaggi corti (fino a 2 km circa) in tutte le fasce; a 4-6 km vince ancora il 44% alle 08:00 (auto lenta e 4-12 min di parcheggio), poi sempre meno. L'auto vince sempre di piu' con la distanza, e a mezzogiorno e di sera molto di piu' che alle 08:00.
- Con i valori del mandato la bici risulta lenta: circa 12 km/h in media, comprese le attese ai semafori (percorso viale Sarca - via Giambellino: 11,6 km in 58 minuti, 8 dei quali di attese). Se Google dara' tempi molto piu' bassi, i primi parametri da cambiare sono l'attesa ai semafori (15 s) e la velocita' sulle strade normali (13 km/h).
- I mezzi sono penalizzati dal fatto che le coppie sono celle a caso (non case e uffici vicini alle fermate) e dalla media su 6 partenze (attesa vera). Vincono nelle zone vicine alle linee: nelle mappe si vedono le linee M1-M5 (`out\\mappa_citta_08.png`).
- Alle 21:00 le linee hanno poche corse e si perdono molte coincidenze.
- Alle 08:00 l'auto prende a volte la Tangenziale per attraversare la citta' (autostrada tarata a 45 km/h x 0,916): da guardare nel confronto con Google.

Mappe di prova (PNG in `out\\`): `mappa_<nome>_<ora>.png` per Duomo (08:00 e 21:00), Niguarda, Gratosoglio, Cordusio: ogni cella e' colorata col mezzo che arriva prima. `mappa_citta_08|12|21.png`: per ogni cella di arrivo, la quota di partenze (delle 300 a caso) da cui vince bici, auto, mezzi. Si rifanno con `scripts\\f2_mappa.py <strand> <lon> <lat> <fascia> <nome>` e `scripts\\f2_analisi.py <strand>`.

### 5. 20 tragitti di prova per Davide
`tragitti_prova.csv` (separatore `;`, aprire con Excel) e `COME_CONTROLLARE.md`. 20 tragitti da 0,7 a 11 km in linea retta: 5 con meta in Area C, 9 nel semicentro, 6 in periferia; alcuni con partenza o arrivo a meno di 100 m da una fermata della metro, altri a oltre 1 km (colonne `metro_vicino_*`); 8 con percorso in auto dentro Area C. Giorno martedi' 3/11/2026, ore 08:00 (9 tragitti), 12:00 (6), 21:00 (5). Gli indirizzi vengono dal registro dei civici del Comune. Colonne: i tempi stimati (bici = solo pedalata; auto = solo guida e anche porta a porta; mezzi = con attesa), tre colonne vuote per Google Maps e le note.

### 6. Incidenti: quanti si possono mettere su mappa
Fonte: microdati Lombardia 2010-2024, 131.435 righe di Milano (`raw\\incidenti\\lombardia_microdati`, campo `nome_strada`). Tipi di indirizzo sull'insieme (`out\\incidenti_geo_stima.json`):
"""
P4 = """
Nota: per alcuni anni il campo ha un formato vecchio "Via - Via - civico" (`Majno Luigi -  - 14`), per altri il formato "via X, 57" / "via X incrocio via Y" / "via X, palo luce 12": il programma legge entrambi.

**Come si geocodifica gratis in locale** (`scripts\\f2_geocode.py`):
1. civico: registro dei civici del Comune (`citta-15-minuti\\raw\\comune_milano\\civici`, ds634, 57.405 civici applicati con coordinate); nome strada normalizzato (senza articoli, abbreviazioni sciolte, ordine delle parole indifferente: "Pagano Mario" = "Mario Pagano"), civico esatto, altrimenti il piu' vicino della stessa parita' entro 20 numeri.
2. incrocio: nomi delle strade in OSM (7.129 strade con nome): nodo in comune fra le due strade, altrimenti il punto piu' vicino se entro 80 m.
3. solo via (palo luce, civico non trovato, incrocio non trovato): punto mediano della via, posizione solo approssimata.
Non servono servizi esterni.

"""
P5 = """**Stima su 500 righe a caso** (seme 11, `out\\incidenti_geo_campione500.csv`): civico esatto **%s%%**, incrocio **%s%%**, civico approssimato %s%%, solo la via %s%%, nessuna posizione %s%% (autostrade/tangenziali, nomi non riconosciuti). Posizione buona (civico esatto + incrocio): **%s%% dei casi**. Tutte le coordinate trovate cadono dentro Milano. Non verificato: l'esattezza dei punti (non c'e' una verita' di confronto); l'incrocio e' il nodo OSM comune alle due strade. I non agganciati sono in gran parte nomi particolari ("Sempione -  - 41", "via X in prossimita di ...").

Per la fase dopo: geocodificare tutte le 131.435 righe richiede pochi minuti con lo stesso programma. BikeMi (325 stazioni, file del 2022): serve ancora un controllo sulle stazioni attuali.

### 7. Limiti noti
- Divieti di svolta (4.380 in OSM) e tempi dei semafori veri non usati; ZTL e corsie preferenziali non modellate; niente pendenze (Milano e' piana); lavori in corso, parcheggi pieni, ritardi non considerati.
- Le piste ciclabili sono quelle scritte in OSM; la rete ciclabile reale puo' differire.
- Il tempo di ricerca del parcheggio e' lo stesso in tutte le fasce orarie (di sera in realta' si trova prima).
- Le velocita' dell'auto per 12:00 e 21:00 sono ipotesi; quella delle 08:00 e' ancorata a TomTom, che e' una media di tutta la citta' nel 2025.
- Il programma sceglie sempre il percorso piu' veloce: Google a volte consiglia percorsi piu' tranquilli per le bici.
""" % (sq['civico_esatto'], sq['incrocio'], sq['civico_approssimato'], sq['solo_via'], sq['nessuna_posizione'], sq['posizione_buona (civico esatto + incrocio)'])
note += P1 + tab('08:00') + '\n**Ore 12:00**\n\n' + tab('12:00') + '\n**Ore 21:00**\n\n' + tab('21:00') + P2 + tabm('08:00') + P3 + ''.join('- %s: %d righe (%.1f%%)\n' % (k, v['righe'], v['quota_pct']) for k, v in ti.items()) + P4 + P5
open(S + '/NOTE.md', 'w', encoding='utf-8').write(note)
print(len(note))
