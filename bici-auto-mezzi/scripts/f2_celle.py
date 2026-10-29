"""Griglia di celle 250 m sul Comune di Milano (centri dentro il confine). Uso: python -I f2_celle.py <ABS strand> -> out/celle.npz"""
import sys, os, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from shapely.geometry import shape
from shapely.ops import transform as shp_transform
from shapely import contains_xy
from pyproj import Transformer
import f2_parametri as P
S = sys.argv[1]
f = glob.glob(S + '/../citta-15-minuti/raw/comune_milano/confine_comune/*.geojson')[0]
g = shape(json.load(open(f, encoding='utf-8'))['features'][0]['geometry'])
t = Transformer.from_crs(4326, 32632, always_xy=True); ti = Transformer.from_crs(32632, 4326, always_xy=True)
gm = shp_transform(lambda x, y, z=None: t.transform(x, y), g)
x0, y0, x1, y1 = gm.bounds; c = P.CELL_M
xs = np.arange(np.floor(x0 / c) * c + c / 2, x1, c); ys = np.arange(np.floor(y0 / c) * c + c / 2, y1, c)
X, Y = np.meshgrid(xs, ys); X = X.ravel(); Y = Y.ravel()
m = contains_xy(gm, X, Y); X = X[m]; Y = Y[m]
lon, lat = ti.transform(X, Y)
np.savez_compressed(S + '/out/celle.npz', x=X, y=Y, lon=np.asarray(lon), lat=np.asarray(lat))
print('area comune km2', round(gm.area / 1e6, 1), 'celle', len(X))
