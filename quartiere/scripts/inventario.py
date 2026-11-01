"""Inventario dei file con dati per quartiere (NIL) nelle pagine di docs/.

Uso:  python -I -X utf8 inventario.py <percorso assoluto di milano-in-dati> [<file di uscita .json>]
Scorre docs/*/data/ (csv, json, geojson, anche csv.gz) e cerca colonne o chiavi che sembrano un
identificativo o un nome di NIL. Non legge altro. Scrive (se richiesto) un JSON con l'elenco.
"""
import csv, glob, gzip, io, json, os, re, sys

NIL_RE = re.compile(r'(^|_)(id_?nil|nil|nome_?nil|nil_nome|quartiere|quartiere_nil)($|_)', re.I)


def head_csv(path):
    op = gzip.open if path.endswith('.gz') else open
    with op(path, 'rt', encoding='utf-8-sig', errors='replace') as fh:
        first = fh.readline().strip()
    d = ';' if first.count(';') > first.count(',') else ','
    return [c.strip() for c in first.split(d)]


def keys_json(path, maxbytes=40_000_000):
    if os.path.getsize(path) > maxbytes:
        return None
    with open(path, encoding='utf-8') as fh:
        try:
            data = json.load(fh)
        except Exception:
            return None
    ks = set()

    def walk(o, depth=0):
        if depth > 4:
            return
        if isinstance(o, dict):
            if 'properties' in o and isinstance(o['properties'], dict):
                ks.update(o['properties'].keys())
            for k, v in o.items():
                ks.add(k)
                if depth < 3 and not isinstance(v, (str, int, float, type(None))):
                    walk(v, depth + 1)
        elif isinstance(o, list):
            for v in o[:3]:
                walk(v, depth + 1)
    walk(data)
    return sorted(ks)


def main():
    base = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    res = []
    for p in sorted(glob.glob(os.path.join(base, 'docs', '*', 'data', '**', '*'), recursive=True)):
        if os.path.isdir(p):
            continue
        rel = os.path.relpath(p, os.path.join(base, 'docs')).replace(os.sep, '/')
        try:
            if p.endswith(('.csv', '.csv.gz')):
                cols = head_csv(p)
            elif p.endswith(('.json', '.geojson')):
                cols = keys_json(p)
                if cols is None:
                    continue
            else:
                continue
        except Exception as e:
            print('ERRORE', rel, e)
            continue
        hit = [c for c in cols if NIL_RE.search(c)]
        if hit or p.endswith('nil.geojson'):
            res.append({'file': rel, 'campi_nil': hit, 'n_campi': len(cols)})
    for r in res:
        print(r['file'], '|', ','.join(r['campi_nil']))
    print(len(res), 'file con campi NIL')
    if out:
        with open(out, 'w', encoding='utf-8') as fh:
            json.dump(res, fh, ensure_ascii=False, indent=1)


main()
