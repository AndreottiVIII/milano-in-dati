"""Lettore minimo di DBF e SHP (poligoni), senza librerie esterne. Usato da altri script."""
import struct
def dbf_fields(path):
    b = open(path, "rb").read(512)
    n, hl, rl = struct.unpack("<IHH", b[4:12]); fields = []; o = 32
    b = open(path, "rb").read(hl)
    while b[o] != 0x0D:
        fields.append((b[o:o+11].split(b"\0")[0].decode("latin1"), chr(b[o+11]), b[o+16])); o += 32
    return n, hl, rl, fields
def dbf_rows(path, enc="latin1"):
    n, hl, rl, fields = dbf_fields(path)
    with open(path, "rb") as f:
        f.seek(hl)
        for i in range(n):
            r = f.read(rl); p = 1; d = {}
            for name, t, l in fields:
                d[name] = r[p:p+l].decode(enc, "replace").strip(); p += l
            d["_del"] = (r[0:1] == b"*")
            yield d
def shp_polys(path):
    """genera, per ogni record, una lista di anelli (lista di (x,y)) e il tipo; None per record nulli"""
    b = open(path, "rb").read(); o = 100
    while o < len(b):
        rn, cl = struct.unpack(">ii", b[o:o+8]); o += 8; c = b[o:o+cl*2]; o += cl*2
        t = struct.unpack("<i", c[:4])[0]
        if t in (5, 15, 25):
            np_, npt = struct.unpack("<ii", c[36:44]); parts = struct.unpack(f"<{np_}i", c[44:44+4*np_]); q = 44 + 4*np_
            pts = [struct.unpack("<dd", c[q+16*k:q+16*k+16]) for k in range(npt)]
            yield [pts[parts[k]:(parts[k+1] if k+1 < np_ else npt)] for k in range(np_)]
        else:
            yield None
