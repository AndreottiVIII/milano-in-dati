"""Ritaglia un file .osm.pbf su un rettangolo e scrive un .osm.gz (XML OSM standard).
Nessuna libreria esterna oltre a numpy. Uso:
  python -I clip_pbf.py <in.osm.pbf> <out.osm.gz> <lat_min> <lat_max> <lon_min> <lon_max>
Tiene: strade (way con tag highway), nodi di quelle strade, nodi con tag highway/crossing/barrier,
e le relazioni di tipo restriction / route=bicycle che toccano le strade tenute.
Le strade vengono troncate al rettangolo (i nodi fuori restano fuori).
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
node_ids = []   # blocchi di array
node_lat = []
node_lon = []
tagged_nodes = {}  # id -> (lat, lon, tags)
ways = []   # (id, refs array in-box, tags)
rels = []   # (id, tags, members[(type, ref, role)])
nblocks = 0
for typ, raw in blobs(inp):
    if typ != "OSMData":
        continue
    nblocks += 1
    if nblocks % 500 == 0:
        print("blocchi", nblocks, "nodi", sum(len(x) for x in node_ids), "strade", len(ways), "%.0fs" % (time.time() - t0), flush=True)
    strings = []
    groups = []
    gran = 100
    lat_off = lon_off = 0
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
    if not strings:
        pass
    S = [s.decode("utf-8", "replace") for s in strings]
    for g in groups:
        for fn, w, v in fields(g):
            if fn == 2:  # DenseNodes
                ids = lat = lon = kv = None
                for f2, w2, v2 in fields(v):
                    if f2 == 1:
                        ids = np.cumsum(svarints(v2))
                    elif f2 == 8:
                        lat = np.cumsum(svarints(v2))
                    elif f2 == 9:
                        lon = np.cumsum(svarints(v2))
                    elif f2 == 10:
                        kv = uvarints(v2)
                la = (lat_off + gran * lat) * 1e-9
                lo = (lon_off + gran * lon) * 1e-9
                m = (la >= LAT0) & (la <= LAT1) & (lo >= LON0) & (lo <= LON1)
                if not m.any():
                    continue
                node_ids.append(ids[m])
                node_lat.append(la[m])
                node_lon.append(lo[m])
                if kv is not None and len(kv):
                    # nodi con tag: segmenti separati da 0
                    zeros = np.flatnonzero(kv == 0)
                    starts = np.concatenate(([0], zeros[:-1] + 1))
                    lens = zeros - starts
                    for idx in np.flatnonzero(lens > 0):
                        if not m[idx]:
                            continue
                        seg = kv[starts[idx]:zeros[idx]]
                        tags = {S[int(seg[j])]: S[int(seg[j + 1])] for j in range(0, len(seg), 2)}
                        if any(k in tags for k in ("highway", "crossing", "barrier", "traffic_calming", "railway", "bicycle_parking", "amenity")) and (
                                "highway" in tags or "crossing" in tags or "barrier" in tags or "traffic_calming" in tags):
                            tagged_nodes[int(ids[idx])] = (float(la[idx]), float(lo[idx]), tags)
            elif fn == 3:  # Way
                wid = None
                keys = vals = refs = None
                for f2, w2, v2 in fields(v):
                    if f2 == 1:
                        wid = v2
                    elif f2 == 2:
                        keys = uvarints(v2)
                    elif f2 == 3:
                        vals = uvarints(v2)
                    elif f2 == 8:
                        refs = np.cumsum(svarints(v2))
                if keys is None or refs is None:
                    continue
                tags = {S[int(a)]: S[int(b)] for a, b in zip(keys, vals)}
                if "highway" not in tags and tags.get("area:highway") is None:
                    continue
                ways.append((wid, refs, tags))
            elif fn == 4:  # Relation
                rid = None
                keys = vals = roles = mem = mty = None
                for f2, w2, v2 in fields(v):
                    if f2 == 1:
                        rid = v2
                    elif f2 == 2:
                        keys = uvarints(v2)
                    elif f2 == 3:
                        vals = uvarints(v2)
                    elif f2 == 8:
                        roles = uvarints(v2)
                    elif f2 == 9:
                        mem = np.cumsum(svarints(v2))
                    elif f2 == 10:
                        mty = uvarints(v2)
                if keys is None or mem is None:
                    continue
                tags = {S[int(a)]: S[int(b)] for a, b in zip(keys, vals)}
                t = tags.get("type", "")
                if t.startswith("restriction") or tags.get("route") == "bicycle" or (t == "multipolygon" and tags.get("highway")):
                    rels.append((rid, tags, [(int(mty[i]), int(mem[i]), S[int(roles[i])]) for i in range(len(mem))]))
            # nodi non-densi (campo 1): rarissimi nei file moderni, ignorati

print("lettura finita %.0fs" % (time.time() - t0), flush=True)
nid = np.concatenate(node_ids)
nla = np.concatenate(node_lat)
nlo = np.concatenate(node_lon)
order = np.argsort(nid)
nid, nla, nlo = nid[order], nla[order], nlo[order]
print("nodi nel rettangolo:", len(nid), flush=True)

kept_ways = []
used = np.zeros(len(nid), bool)
for wid, refs, tags in ways:
    pos = np.searchsorted(nid, refs)
    pos[pos >= len(nid)] = len(nid) - 1
    ok = nid[pos] == refs
    if ok.sum() < 2:
        continue
    p = pos[ok]
    used[p] = True
    kept_ways.append((wid, refs[ok], tags))
kept_way_ids = {w[0] for w in kept_ways}
print("strade tenute:", len(kept_ways), flush=True)

kept_rels = []
for rid, tags, mem in rels:
    if any(t == 1 and r in kept_way_ids for t, r, _ in mem):
        kept_rels.append((rid, tags, mem))
print("relazioni tenute:", len(kept_rels), flush=True)

used_ids = set(nid[used].tolist())
for i in tagged_nodes:
    used_ids.add(i)


def attrs(tags):
    return "".join('<tag k=%s v=%s/>\n' % (quoteattr(k), quoteattr(v)) for k, v in tags.items())


nn = 0
with gzip.open(outp, "wt", encoding="utf-8", compresslevel=6) as out:
    out.write('<?xml version="1.0" encoding="UTF-8"?>\n<osm version="0.6" generator="clip_pbf.py (milano-in-dati)">\n')
    out.write('<bounds minlat="%s" minlon="%s" maxlat="%s" maxlon="%s"/>\n' % (LAT0, LON0, LAT1, LON1))
    for i in range(len(nid)):
        n = int(nid[i])
        if n not in used_ids:
            continue
        nn += 1
        tg = tagged_nodes.get(n)
        if tg:
            out.write('<node id="%d" lat="%.7f" lon="%.7f">\n%s</node>\n' % (n, nla[i], nlo[i], attrs(tg[2])))
        else:
            out.write('<node id="%d" lat="%.7f" lon="%.7f"/>\n' % (n, nla[i], nlo[i]))
    for wid, refs, tags in kept_ways:
        out.write('<way id="%d">\n' % wid)
        out.write("".join('<nd ref="%d"/>\n' % r for r in refs.tolist()))
        out.write(attrs(tags))
        out.write("</way>\n")
    tmap = {0: "node", 1: "way", 2: "relation"}
    for rid, tags, mem in kept_rels:
        out.write('<relation id="%d">\n' % rid)
        for t, r, role in mem:
            if t == 1 and r in kept_way_ids or t == 0 and r in used_ids:
                out.write('<member type="%s" ref="%d" role=%s/>\n' % (tmap[t], r, quoteattr(role)))
        out.write(attrs(tags))
        out.write("</relation>\n")
    out.write("</osm>\n")
print("scritti nodi", nn, "strade", len(kept_ways), "relazioni", len(kept_rels), "totale %.0fs" % (time.time() - t0), flush=True)
