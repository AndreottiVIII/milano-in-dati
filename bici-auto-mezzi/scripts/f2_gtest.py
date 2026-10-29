import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from f2_geocode import Geocoder
g = Geocoder(sys.argv[1])
print('civici', g.n_civici, 'vie civici', len(g.street), 'vie osm', len(g.osm))
for a in ['Piazza Duca d\'Aosta, 1','via Dante, 9','via Roentgen, 1','Piazza Leonardo da Vinci, 32','Piazza dell\'Ospedale Maggiore, 3','via Spartaco incrocio via Cadore','via Pagano Mario, 47','viale Monza, palo luce 73','Piazzale Carlo Magno, 1','Piazza dell\'Ateneo Nuovo, 1','via Giambellino, 100','via Padova, 200','Piazza Tre Torri, 1','viale Ripamonti, 100']:
    print(a, '->', g.indirizzo(a))
