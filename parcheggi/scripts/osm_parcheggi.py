"""Estrae da un .osm.pbf (rettangolo di Milano) tutto cio' che serve ai parcheggi. Ricavato dal lettore di bici-auto-mezzi/scripts/clip_pbf.py (solo numpy).
Uso: python -I -X utf8 osm_parcheggi.py <in.osm.pbf> <out.pkl> <lat_min> <lat_max> <lon_min> <lon_max>
Tiene:
  - nodi con amenity in (parking, parking_space, parking_entrance, bicycle_parking?, no) : solo parking*, motorcycle_parking, bicycle_parking, charging_station
  - way con amenity=parking/parking_space/motorcycle_parking/bicycle_parking o building=parking/garages, o parking=* (aree), con le coordinate
  - way con highway (tutti i tag), area:highway, con le coordinate
  - relazioni multipolygon con amenity=parking (solo tag e membri, non risolte)
Scrive un pickle con liste di dict.
"""
import sys, struct, zlib, gzip, time
import numpy as np
from xml.sax.saxutils import quoteattr

inp, outp = sys.argv[1], sys.argv[2]
LAT0, LAT1, LON0, LON1 = map(float, sys.argv[3:7])


def read_varint(b, i):
    r = 0
    s = 0
    while True:
        c = b[i]
        i += 1
        r |= (c & 0x7F) << s
        if c < 0x80:
            return r, i
        s += 7


def fields(b):
    """Itera (numero_campo, tipo_wire, valore) di un messaggio protobuf."""
    i = 0
    n = len(b)
    while i < n:
        k, i = read_varint(b, i)
        f, w = k >> 3, k & 7
        if w == 0:
            v, i = read_varint(b, i)
        elif w == 2:
            l, i = read_varint(b, i)
            v = b[i:i + l]
            i += l
        elif w == 1:
            v = b[i:i + 8]
            i += 8
        elif w == 5:
            v = b[i:i + 4]
            i += 4
        else:
            raise ValueError("wire " + str(w))
        yield f, w, v


def uvarints(buf):
    if not buf:
        return np.zeros(0, np.uint64)
    a = np.frombuffer(buf, np.uint8)
    ends = np.flatnonzero((a & 0x80) == 0)
    starts = np.concatenate(([0], ends[:-1] + 1))
    pos = np.arange(len(a)) - np.repeat(starts, ends - starts + 1)
    vals = (a & 0x7F).astype(np.uint64) << (7 * pos).astype(np.uint64)
    return np.add.reduceat(vals, starts)


def svarints(buf):
    u = uvarints(buf)
    return (u >> np.uint64(1)).astype(np.int64) ^ -((u & np.uint64(1)).astype(np.int64))


def blobs(path):
    with open(path, "rb") as f:
        while True:
            h = f.read(4)
            if len(h) < 4:
                return
            hl = struct.unpack(">I", h)[0]
            typ = None
            dsz = 0
            for fn, w, v in fields(f.read(hl)):
                if fn == 1:
                    typ = v.decode()
                elif fn == 3:
                    dsz = v
            blob = f.read(dsz)
            raw = None
            for fn, w, v in fields(blob):
                if fn == 1:
                    raw = v
                elif fn == 3:
                    raw = zlib.decompress(v)
            yield typ, raw



t0 = time.time()
PARK_AM = {"parking", "parking_space", "parking_entrance", "motorcycle_parking", "bicycle_parking", "charging_station", "car_sharing"}
ptn = []       # nodi parcheggio: (id, lat, lon, tags)
node_ids = []; node_lat = []; node_lon = []
pways = []     # way parcheggio (id, refs, tags)
hways = []     # way strada (id, refs, tags)
prels = []
nblocks = 0
for typ, raw in blobs(inp):
    if typ != "OSMData":
        continue
    nblocks += 1
    if nblocks % 500 == 0:
        print("blocchi", nblocks, "nodi", sum(len(x) for x in node_ids), "park-way", len(pways), "strade", len(hways), "%.0fs" % (time.time() - t0), flush=True)
    strings = []; groups = []; gran = 100; lat_off = lon_off = 0
    for fn, w, v in fields(raw):
        if fn == 1:
            strings = [s for _, _, s in fields(v)]
        elif fn == 2:
            groups.append(v)
        elif fn == 17:
            gran = v
        elif fn == 19:
            lat_off = v
        elif fn == 20:
            lon_off = v
    S = [s.decode("utf-8", "replace") for s in strings]
    for g in groups:
        for fn, w, v in fields(g):
            if fn == 2:
                ids = lat = lon = kv = None
                for f2, w2, v2 in fields(v):
                    if f2 == 1: ids = np.cumsum(svarints(v2))
                    elif f2 == 8: lat = np.cumsum(svarints(v2))
                    elif f2 == 9: lon = np.cumsum(svarints(v2))
                    elif f2 == 10: kv = uvarints(v2)
                la = (lat_off + gran * lat) * 1e-9
                lo = (lon_off + gran * lon) * 1e-9
                m = (la >= LAT0) & (la <= LAT1) & (lo >= LON0) & (lo <= LON1)
                if not m.any():
                    continue
                node_ids.append(ids[m]); node_lat.append(la[m]); node_lon.append(lo[m])
                if kv is not None and len(kv):
                    zeros = np.flatnonzero(kv == 0)
                    starts = np.concatenate(([0], zeros[:-1] + 1))
                    lens = zeros - starts
                    for idx in np.flatnonzero(lens > 0):
                        if not m[idx]:
                            continue
                        seg = kv[starts[idx]:zeros[idx]]
                        tags = {S[int(seg[j])]: S[int(seg[j + 1])] for j in range(0, len(seg), 2)}
                        if tags.get("amenity") in PARK_AM or "parking" in tags or tags.get("building") == "parking":
                            ptn.append((int(ids[idx]), float(la[idx]), float(lo[idx]), tags))
            elif fn == 3:
                wid = None; keys = vals = refs = None
                for f2, w2, v2 in fields(v):
                    if f2 == 1: wid = v2
                    elif f2 == 2: keys = uvarints(v2)
                    elif f2 == 3: vals = uvarints(v2)
                    elif f2 == 8: refs = np.cumsum(svarints(v2))
                if keys is None or refs is None:
                    continue
                tags = {S[int(a)]: S[int(b)] for a, b in zip(keys, vals)}
                if "highway" in tags or "area:highway" in tags:
                    hways.append((wid, refs, tags))
                elif tags.get("amenity") in PARK_AM or tags.get("building") in ("parking", "garages") or "parking" in tags or tags.get("landuse") == "garages":
                    pways.append((wid, refs, tags))
            elif fn == 4:
                rid = None; keys = vals = mem = mty = None
                for f2, w2, v2 in fields(v):
                    if f2 == 1: rid = v2
                    elif f2 == 2: keys = uvarints(v2)
                    elif f2 == 3: vals = uvarints(v2)
                    elif f2 == 9: mem = np.cumsum(svarints(v2))
                    elif f2 == 10: mty = uvarints(v2)
                if keys is None:
                    continue
                tags = {S[int(a)]: S[int(b)] for a, b in zip(keys, vals)}
                if tags.get("amenity") in PARK_AM or tags.get("building") == "parking":
                    prels.append((rid, tags, [(int(mty[i]), int(mem[i])) for i in range(len(mem))] if mem is not None else []))
print("lettura finita %.0fs" % (time.time() - t0), flush=True)
nid = np.concatenate(node_ids); nla = np.concatenate(node_lat); nlo = np.concatenate(node_lon)
order = np.argsort(nid); nid, nla, nlo = nid[order], nla[order], nlo[order]

def resolve(ways):
    out = []
    for wid, refs, tags in ways:
        pos = np.searchsorted(nid, refs); pos[pos >= len(nid)] = len(nid) - 1
        ok = nid[pos] == refs
        if ok.sum() < 2:
            continue
        p = pos[ok]
        out.append({"id": int(wid), "tags": tags, "lat": nla[p].tolist(), "lon": nlo[p].tolist(), "closed": bool(refs[0] == refs[-1]), "complete": bool(ok.all())})
    return out
res = {"parking_nodes": [{"id": i, "lat": a, "lon": b, "tags": t} for i, a, b, t in ptn],
       "parking_ways": resolve(pways), "highways": resolve(hways),
       "parking_rels": [{"id": int(i), "tags": t, "members": m} for i, t, m in prels],
       "bbox": [LAT0, LAT1, LON0, LON1], "n_nodes_in_box": int(len(nid))}
for k, v in res.items():
    if isinstance(v, list): print(k, len(v))
import pickle
pickle.dump(res, open(outp, "wb"))
print("fatto %.0fs" % (time.time() - t0))
