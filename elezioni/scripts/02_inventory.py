import sys, json, re, csv
src, outcsv, outjson = sys.argv[1:4]
S = json.load(open(src, encoding='utf-8'))
def num(n):
    m = re.match(r'ds(\d+)', n); return int(m.group(1)) if m else 0
def relevant(p):
    t = p['title']
    if re.search(r'Prezzi al consumo|Consiglio comunale 20|Censimento|Istituzioni|Redditi|calore|verde urbano|Territorio: localiz', t): return False
    return bool(re.search(r'elezion|referendum|elettoral|elettori|corpo elettorale', t, re.I))
def kind(t):
    tl = t.lower()
    if 'consultazione interattiva' in tl: return 'visualizzatore_html'
    if 'voti di lista' in tl: return 'voti_lista_sezione'
    if 'riepiloghi di sezione' in tl: return 'riepilogo_sezione'
    if 'risultati di sez' in tl: return 'risultati_sezione'
    if 'affluen' in tl: return 'affluenza'
    if 'affluen' in tl: return 'affluenza'
    if 'candidat' in tl or 'elenco liste' in tl: return 'candidati_liste'
    if 'collegi elettorali' in tl and 'stradario' not in tl: return 'collegi_geo'
    if 'stradario' in tl or 'abbinament' in tl: return 'stradario_civici_sezioni'
    if 'sezioni e sedi' in tl or 'elenco delle sedi' in tl or 'elenco delle sedi di voto' in tl: return 'sezioni_sedi'
    if 'plessi' in tl or 'indirizzi delle sezioni' in tl: return 'indirizzi_plessi'
    if 'barriere' in tl: return 'seggi_accessibili'
    if 'elettori per sezion' in tl or 'corpo elettorale' in tl: return 'elettori'
    return 'altro'
def etype(t):
    tl = t.lower()
    if 'referendum' in tl: return 'referendum'
    for k,v in [('regionali','regionali'),('comunali','comunali'),('municipali','municipali'),('elezioni circoscrizionali','circoscrizionali'),('amministrative','comunali/municipali'),
                ('politiche','politiche'),('parlamento europeo','europee'),('europee','europee'),('provinciali','provinciali'),('collegi','politiche')]:
        if k in tl: return v
    if 'consultazioni del' in tl: return 'consultazioni_varie(sedi)'
    return ''
def date(p):
    for e in p.get('extras', []):
        if e['key']=='temporal_coverage':
            try:
                j = json.loads(e['value']); return j[0].get('temporal_start',''), j[0].get('temporal_end','')
            except Exception: pass
    return '',''
def year(t):
    m = re.findall(r'(19[7-9]\d|20[0-2]\d)', t); return m[-1] if m else ''
def level(k):
    return {'voti_lista_sezione':'sezione','riepilogo_sezione':'sezione','risultati_sezione':'sezione','affluenza':'sezione','stradario_civici_sezioni':'civico->sezione','sezioni_sedi':'sezione (sede)','indirizzi_plessi':'plesso/sezione','elettori':'sezione','collegi_geo':'collegio (geo)','candidati_liste':'candidati/liste','seggi_accessibili':'seggio'}.get(k,'')
rows=[]; pk=[]
for n,p in sorted(S.items(), key=lambda kv: num(kv[0])):
    if not relevant(p): continue
    k = kind(p['title']); ts,te = date(p)
    pk.append(n)
    ext = {e['key']:e['value'] for e in p.get('extras',[])}
    if not p['resources']:
        rows.append(dict(dataset=n, ds=num(n), title=p['title'], kind=k, election_type=etype(p['title']), year=year(p['title']), date_start=ts, date_end=te, level=level(k), resource_id='', resource_name='', format='', size_bytes='', url='', license=p.get('license_id'), dataset_modified=p['metadata_modified'][:10], resource_modified='', frequency=ext.get('frequency','')))
    for r in p['resources']:
        rows.append(dict(dataset=n, ds=num(n), title=p['title'], kind=k, election_type=etype(p['title']), year=year(p['title']), date_start=ts, date_end=te, level=level(k), resource_id=r['id'], resource_name=r['name'], format=r['format'], size_bytes=r.get('size') or '', url=r['url'], license=p.get('license_id'), dataset_modified=p['metadata_modified'][:10], resource_modified=(r.get('last_modified') or '')[:10], frequency=ext.get('frequency','')))
with open(outcsv,'w',newline='',encoding='utf-8-sig') as f:
    w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
json.dump(pk, open(outjson,'w'))
print(len(pk),'datasets',len(rows),'resources')
from collections import Counter
print(Counter(r['kind'] for r in rows if r['resource_id']))
print(Counter((r['kind'],r['format']) for r in rows))
print(Counter(r['license'] for r in rows))
print(sum(int(r['size_bytes'] or 0) for r in rows)/1e6,'MB declared total')
