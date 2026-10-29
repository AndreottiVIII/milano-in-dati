"""Tutte le ipotesi del motore in un posto solo (le stesse sono nella tabella di NOTE.md, Fase 2)."""
# --- piedi
WALK_KMH = 4.5
WALK_SIGNAL_S = 10          # attesa media a un semaforo pedonale
# --- bici
BIKE_KMH_CYCLEWAY = 19.0    # piste ciclabili, corsie/piste su strada   (Fase 3: era 15,0)
BIKE_KMH_ROAD = 17.0        # strade normali   (Fase 3: era 13,0)
BIKE_KMH_SERVICE = 15.0       # (Fase 3: era 12,0)
BIKE_KMH_PEDESTRIAN_RIDE = 10.0   # area pedonale/footway con bicycle=yes/designated
BIKE_KMH_WALKING = 5.0      # bici a mano (aree pedonali, footway dismount)
BIKE_KMH_TRACK = 10.0       # sterrati
BIKE_SIGNAL_S = 6           # attesa media a un semaforo (tempo atteso)   (Fase 3: era 15)
BIKE_MAJOR_CROSS_S = 3     # attraversamento senza semaforo di strada primary/secondary/trunk   (Fase 3: era 8)
BIKE_FIXED_S = 60           # sbloccare + chiudere la bici (totale)
# --- auto: velocita di marcia tra un semaforo e l'altro (km/h) per tipo di strada, fasce 08:00 / 12:00 / 21:00
BANDS = ['08', '12', '21']
CAR_SPEED = {   # (08, 12, 21)  PRIMA della taratura (vedi CAR_SCALE)
    'motorway': (45, 70, 90), 'motorway_link': (30, 40, 50),
    'trunk': (35, 45, 60), 'trunk_link': (28, 36, 42),
    'primary': (26, 34, 40), 'primary_link': (22, 28, 32),
    'secondary': (23, 30, 36), 'secondary_link': (20, 26, 30),
    'tertiary': (21, 27, 32), 'tertiary_link': (18, 22, 26),
    'unclassified': (20, 24, 28), 'residential': (18, 22, 25), 'road': (18, 22, 25),
    'living_street': (10, 10, 10), 'service': (12, 14, 15), 'alley': (10, 10, 10),
}
CAR_MAXSPEED_FRAC = 0.85    # velocita di marcia <= 85% del limite scritto in OSM (maxspeed)
CAR_SIGNAL_S = (20, 15, 10) # attesa media a un semaforo, per fascia
CAR_SCALE = (0.916, 0.703, 0.770)   # Fase 3: 12:00 e 21:00 erano 1,056 e 1,158
CAR_SCALE_F2 = (0.916, 1.056, 1.158) # fattore di taratura per fascia (f2_taratura.py: tempo medio ogni 10 km uguale all obiettivo)
CAR_WALK_S = 120            # a piedi fino all'auto (2 min) e, dopo il parcheggio, fino alla meta (2 min)
PARK_MIN = {'areac': 12, 'semicentro': 8, 'periferia': 4}   # minuti di ricerca parcheggio per zona di arrivo
SEMICENTRO_KM = 3.5         # raggio dal Duomo per "semicentro"
AREAC_EUR = 7.5
# --- mezzi pubblici
ACCESS_M = 800.0            # a piedi fino alla fermata (m)
TRANSFER_M = 300.0          # trasferimento a piedi tra fermate (m)
STATION_TRANSFER_M = 400.0  # verifica mezzi: tra due stazioni (metro/treno) fino a 400 m (Centrale M2-treni 373 m, Porta Venezia 363 m, Loreto 303 m)
TRANSIT_SLACK_S = 120       # margine minimo per cambiare mezzo   (Fase 3: era 45)
STATION_ACCESS_S = 60       # Fase 3: metro e stazioni: secondi in piu' per scendere/salire al binario (all'inizio e alla fine)
STOP_SNAP_MAX_M = 150.0
DEP_OFFSETS_MIN = (0, 2, 4, 6, 8, 10)    # partenze simulate, si fa la media
MAX_TRIP_S = 2 * 3600
# --- giorno di riferimento: martedi 3 novembre 2026
DATE = '20261103'
DEPARTURES = {'08': 8 * 3600, '12': 12 * 3600, '21': 21 * 3600}
CELL_M = 250
DUOMO_LL = (45.46419, 9.19191)

# --- Fase 3: se esiste out/f3_taratura.json (scritto da f3_calibra.py) i suoi valori sostituiscono quelli sopra
import json as _json, os as _os
_f = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', 'out', 'f3_taratura.json')
if _os.path.exists(_f):
    _p = _json.load(open(_f))['parametri']
    BIKE_KMH_CYCLEWAY, BIKE_KMH_ROAD, BIKE_KMH_SERVICE, BIKE_KMH_PEDESTRIAN_RIDE, BIKE_KMH_WALKING, BIKE_KMH_TRACK = _p['bike_kmh']
    BIKE_SIGNAL_S = _p['bike_signal_s']; BIKE_MAJOR_CROSS_S = _p['bike_major_cross_s']
    CAR_SCALE = tuple(_p['car_scale']); TRANSIT_SLACK_S = _p['transit_slack_s']; STATION_ACCESS_S = _p['station_access_s']
