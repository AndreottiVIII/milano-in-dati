import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f2_geocode import Geocoder
g = Geocoder(sys.argv[1])
C = ["Piazza Duca d'Aosta, 1","via Dante, 9","Piazza Leonardo da Vinci, 32","Piazza dell'Ateneo Nuovo, 1","Piazza Tre Torri, 1","via Giambellino, 100","via Padova, 200",
"Piazza dell'Ospedale Maggiore, 3","viale Ripamonti, 200","via Mario Pagano, 47","Via Rombon, 11","via Lessona, 60","via Saponaro, 30","via delle Forze Armate, 260","viale Forlanini, 100",
"via Rogoredo, 20","via Durando, 10","Alzaia Naviglio Grande, 50","via Piccolomini, 5","Corso di Porta Romana, 100","via Calvairate, 10","via Washington, 70","viale Certosa, 22",
"via Lorenteggio, 200","via Gallarate, 100","viale Fulvio Testi, 100","via Mecenate, 76","piazzale Corvetto, 1","via Ponale, 10","corso Buenos Aires, 40","via Torino, 21","Via Roentgen, 1","via Guglielmo Roentgen, 1",
"via Sarfatti, 25","viale Sarca, 200","via Tertulliano, 70","via dei Missaglia, 97","via Barona, 100","via Gola, 20","piazza Gae Aulenti, 1","viale Papiniano, 20","via Palmanova, 100","via Cascina Merlata, 10","via Novara, 150","via Quarenghi, 10",
"Piazza San Babila, 1","via Orefici, 2","via Larga, 10","viale Monza, 100","via Giovanni Cimabue, 5","piazza Abbiategrasso, 1","via Chiesa Rossa, 50","Via Cassinis, 50","via Ripamonti, 90","Via Ripamonti, 2", "viale Corsica, 20","viale Marche, 10"]
for a in C:
    r, lv = g.indirizzo(a); print(a, '->', lv, r)
