"""Legge le unità volumetriche dei due database topografici (2012 e 2020) e salva una tabella piccola:
anno, id edificio, porzione, altezza, area in pianta, centro (lon, lat). Dati grezzi in altezze/x12 e altezze/x20."""
import os, sys, numpy as np, shapefile, pickle
from pyproj import Transformer
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = Transformer.from_crs(7791, 4326, always_xy=True)
def leggi(path, f_id, f_por):
    r = shapefile.Reader(path, encoding='latin1')
    campi = [x[0] for x in r.fields[1:]]
    ih, ii, ip = campi.index('UN_VOL_AV'), campi.index(f_id), campi.index(f_por)
    out = []
    for sr in r.iterShapeRecords():
        pts = np.array(sr.shape.points)[:, :2]
        parts = list(sr.shape.parts) + [len(pts)]
        # area col metodo di Gauss, somma firmata di tutti gli anelli
        a = 0.0
        for k in range(len(parts) - 1):
            p = pts[parts[k]:parts[k+1]]
            s = 0.5 * np.sum(p[:-1, 0] * p[1:, 1] - p[1:, 0] * p[:-1, 1])
            a += s
        a = abs(a)  # gli anelli interni (buchi) hanno verso opposto: la somma firmata li toglie
        c = pts[parts[0]:parts[1]].mean(axis=0)
        out.append((sr.record[ii], str(sr.record[ip]), float(sr.record[ih]), a, c[0], c[1]))
    arr = np.array(out, dtype=object)
    lon, lat = T.transform(arr[:, 4].astype(float), arr[:, 5].astype(float))
    return dict(id=arr[:, 0], por=arr[:, 1], h=arr[:, 2].astype(float), area=arr[:, 3].astype(float), lon=np.array(lon), lat=np.array(lat))
d = {2020: leggi(os.path.join(R, 'x20', 'DBT 2020 - SHAPE', 'UN_VOL'), 'CEDIUV', 'UN_VOL_POR'),
     2012: leggi(os.path.join(R, 'x12', 'A020101'), 'ID_EDIF', 'UN_VOL_POR')}
pickle.dump(d, open(os.path.join(R, 'x_uv.pkl'), 'wb'))
for a, v in d.items(): print(a, len(v['h']), v['area'].sum() / 1e6, 'km2 in pianta', np.percentile(v['area'], [50, 99]))
