import gzip, csv, io
def load(path):
    f = gzip.open(path, 'rt', encoding='utf-8') if path.endswith('.gz') else open(path, encoding='utf-8')
    rows = list(csv.reader(f, delimiter='\t'))
    hdr = [h.strip() for h in rows[0]]
    keys = hdr[0].split(chr(92))[0].split(',')
    out = []
    for r in rows[1:]:
        k = dict(zip(keys, r[0].split(',')))
        v = {}
        for y, x in zip(hdr[1:], r[1:]):
            x = x.strip().split(' ')[0]
            try: v[int(y)] = float(x)
            except: pass
        out.append((k, v))
    return keys, out
