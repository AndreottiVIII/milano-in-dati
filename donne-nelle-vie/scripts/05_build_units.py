"""Unisce registro Comune (CODICE_VIA) e OSM (loc_ref) in una tabella di 'strade'."""
import sys, json, re, collections, pandas as pd
osm_json, civici_csv, out_csv = sys.argv[1:4]
d = json.load(open(osm_json, encoding='utf8'))
civ = pd.read_csv(civici_csv, sep=';', dtype=str).drop_duplicates('CODICE_VIA').set_index('CODICE_VIA')
def split_q(t): return [q for q in re.split(r'\s*;\s*', t.get('name:etymology:wikidata','')) if q]
by_code = collections.defaultdict(lambda: dict(names=set(), qids=set(), hw=collections.Counter(), n=0))
by_name = collections.defaultdict(lambda: dict(codes=set(), qids=set(), hw=collections.Counter(), n=0, sq=False))
for e in d['elements']:
    t = e['tags']; name = t['name'].strip()
    code = (t.get('loc_ref','').split('_')[0]) if t.get('loc_ref') else ''
    hw = t.get('highway') or ('place=' + t.get('place',''))
    n = by_name[name]; n['n']+=1; n['hw'][hw]+=1; n['qids'].update(split_q(t))
    if code in civ.index:
        n['codes'].add(code)
        c = by_code[code]; c['names'].add(name); c['qids'].update(split_q(t)); c['hw'][hw]+=1; c['n']+=1
rows = []
used_names = set()
for code, r in civ.iterrows():
    c = by_code.get(code)
    names = set(c['names']) if c else set()
    qids = set(c['qids']) if c else set()
    # aggancio per nome (stessa dicitura) per codici non presenti come loc_ref
    full = f"{r.TIPO} {r.DESCRITTIVO}".strip()
    if not c:
        for nm in by_name:
            if nm.lower() == full.lower():
                names.add(nm); qids |= by_name[nm]['qids']
    used_names |= names
    di = r.DATA_INTITOLAZIONE if isinstance(r.DATA_INTITOLAZIONE, str) else ''
    rows.append(dict(origine='comune', codice_via=code, tipo=r.TIPO, denominazione_comune=r.DENOMINAZIONE,
        descrittivo=r.DESCRITTIVO, nome_osm=' | '.join(sorted(names)), in_osm=int(bool(names)),
        qids_osm=';'.join(sorted(qids, key=lambda q:int(q[1:]))), data_intitolazione=di,
        highway_osm=';'.join(f"{k}:{v}" for k,v in (c['hw'].most_common() if c else []))))
for nm, n in by_name.items():
    if nm in used_names: continue
    rows.append(dict(origine='solo_osm', codice_via='', tipo='', denominazione_comune='', descrittivo=nm, nome_osm=nm, in_osm=1,
        qids_osm=';'.join(sorted(n['qids'], key=lambda q:int(q[1:]))), data_intitolazione='',
        highway_osm=';'.join(f"{k}:{v}" for k,v in n['hw'].most_common())))
df = pd.DataFrame(rows)
df.to_csv(out_csv, index=False, encoding='utf-8-sig')
print(df.origine.value_counts().to_dict(), 'comune con osm:', int(df[df.origine=='comune'].in_osm.sum()))
print('con tag:', (df.qids_osm!='').groupby(df.origine).sum().to_dict())
