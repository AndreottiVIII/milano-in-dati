import sys, json, collections, re, csv
inp, out_streets, out_qids = sys.argv[1:4]
d = json.load(open(inp, encoding='utf8'))
streets = collections.OrderedDict()
KEEP = ['name','name:etymology','name:etymology:wikidata','subject:wikidata','old_name','loc_ref']
for e in d['elements']:
    t = e['tags']; name = t['name'].strip()
    s = streets.setdefault(name, dict(name=name, n_elementi=0, highway=collections.Counter(), way_ids=[],
        etym_wd=set(), etym_txt=set(), old_name=set(), loc_ref_codes=set(), place_square=False))
    s['n_elementi'] += 1
    s['highway'][t.get('highway') or ('place=square' if t.get('place')=='square' else '?')] += 1
    s['way_ids'].append(f"{e['type'][0]}{e['id']}")
    for q in re.split(r'\s*;\s*', t.get('name:etymology:wikidata','')):
        if q: s['etym_wd'].add(q)
    if t.get('name:etymology'): s['etym_txt'].add(t['name:etymology'])
    if t.get('old_name'): s['old_name'].add(t['old_name'])
    if t.get('loc_ref'): s['loc_ref_codes'].add(t['loc_ref'].split('_')[0])
    if t.get('place')=='square': s['place_square']=True
rows=[]
allq=set()
for s in streets.values():
    allq |= s['etym_wd']
    rows.append(dict(name=s['name'], n_elementi=s['n_elementi'],
        highway=';'.join(f"{k}:{v}" for k,v in s['highway'].most_common()),
        etymology_wikidata=';'.join(sorted(s['etym_wd'])), etymology_text=' | '.join(sorted(s['etym_txt'])),
        old_name=' | '.join(sorted(s['old_name'])), loc_ref_codes=';'.join(sorted(s['loc_ref_codes'])),
        place_square=int(s['place_square']), way_ids_first5=';'.join(s['way_ids'][:5])))
with open(out_streets,'w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
open(out_qids,'w').write('\n'.join(sorted(allq, key=lambda q:int(q[1:]))))
print(len(streets),'nomi unici;', sum(1 for r in rows if r['etymology_wikidata']),'con tag;', len(allq),'QID unici')
print('con loc_ref', sum(1 for r in rows if r['loc_ref_codes']))
