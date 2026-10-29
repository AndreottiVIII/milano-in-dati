"""Primo giro, economico: per le strade SENZA tag etymology cerca candidati su Wikidata (wbsearchentities + wbgetentities)."""
import sys, json, re, time, os, unicodedata, requests, pandas as pd
units_csv, outdir = sys.argv[1:3]
os.makedirs(outdir, exist_ok=True)
UA = {"User-Agent": "milano-in-dati/0.1 (davide.caniatti@gmail.com; street-name research)"}
API = "https://www.wikidata.org/w/api.php"
def get(params, tries=5):
    for a in range(tries):
        try:
            r = requests.get(API, params=params, headers=UA, timeout=60)
            if r.status_code == 200: return r.json()
            print('status', r.status_code, flush=True)
        except Exception as e: print('err', e, flush=True)
        time.sleep(10*(a+1))
    return None
def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii','ignore').decode().lower()
    return re.sub(r"[^a-z0-9 ]", " ", s.replace("'", " ")).split()
TYPE = r"^(via privata|via|viale|piazzale|piazza|piazzetta|largo|corso|vicolo|galleria|passaggio|bastioni|cavalcavia|strada|parco|giardino|alzaia|foro|sottopasso|sito|vicoletto|ripa|rampa|sottopassaggio|stradone|strada vicinale)\s+"
ART = r"^(del|della|dello|dell'|dei|degli|delle|di|de|d')\s*"
df = pd.read_csv(units_csv, dtype=str).fillna('')
core_hw = ('residential','tertiary','secondary','primary','unclassified','living_street','pedestrian','place=square','trunk')
def is_core(r):
    if r.origine == 'comune': return True
    return r.highway_osm.split(':')[0] in core_hw
todo = df[(df.qids_osm == '') & df.apply(is_core, axis=1)].copy()
def street_name(r):
    s = r.descrittivo if r.origine == 'comune' else re.sub(TYPE, '', r.descrittivo, flags=re.I)
    s = re.sub(r"\(.*?\)", " ", s).strip()
    s2 = re.sub(ART, '', s, flags=re.I).strip() or s
    return s2
todo['chiave'] = todo.apply(street_name, axis=1)
print(len(todo), 'strade senza tag da cercare', flush=True)
# 1. ricerca
sfile = f"{outdir}/search_results.json"
search = json.load(open(sfile, encoding='utf8')) if os.path.exists(sfile) else {}
keys = sorted(set(todo.chiave))
for i, k in enumerate(keys):
    if k in search: continue
    j = get(dict(action='wbsearchentities', search=k.title() if k.isupper() else k, language='it', uselang='it', limit=8, type='item', format='json'))
    search[k] = [dict(id=x['id'], label=x.get('label',''), desc=x.get('description',''), match=x.get('match',{}).get('text','')) for x in (j or {}).get('search', [])]
    time.sleep(0.25)
    if i % 200 == 0:
        json.dump(search, open(sfile,'w',encoding='utf8'), ensure_ascii=False); print('search', i, len(keys), flush=True)
json.dump(search, open(sfile,'w',encoding='utf8'), ensure_ascii=False)
# 2. dettagli
ids = sorted({x['id'] for v in search.values() for x in v}, key=lambda q:int(q[1:]))
efile = f"{outdir}/entities.json"
ents = json.load(open(efile, encoding='utf8')) if os.path.exists(efile) else {}
need = [q for q in ids if q not in ents]
print(len(ids), 'candidati,', len(need), 'da scaricare', flush=True)
def yr(claims, p):
    for c in claims.get(p, []):
        try:
            t = c['mainsnak']['datavalue']['value']['time']; return int(t[:5].replace('+','')) if t[0]=='+' else -int(t[1:5])
        except Exception: pass
    return ''
def qs(claims, p):
    out=[]
    for c in claims.get(p, []):
        try: out.append(c['mainsnak']['datavalue']['value']['id'])
        except Exception: pass
    return out
for i in range(0, len(need), 50):
    j = get(dict(action='wbgetentities', ids='|'.join(need[i:i+50]), props='claims|labels|descriptions|sitelinks', languages='it|en', format='json'))
    for q, e in (j or {}).get('entities', {}).items():
        cl = e.get('claims', {})
        ents[q] = dict(label_it=e.get('labels',{}).get('it',{}).get('value',''), label_en=e.get('labels',{}).get('en',{}).get('value',''),
            desc=(e.get('descriptions',{}).get('it') or e.get('descriptions',{}).get('en') or {}).get('value',''),
            p31=qs(cl,'P31'), sex=qs(cl,'P21'), occ=qs(cl,'P106'), cit=qs(cl,'P27'), birth=yr(cl,'P569'), death=yr(cl,'P570'),
            sitelinks=len(e.get('sitelinks',{})))
    time.sleep(0.5)
    if (i//50) % 20 == 0: json.dump(ents, open(efile,'w',encoding='utf8'), ensure_ascii=False); print('ents', i, len(need), flush=True)
json.dump(ents, open(efile,'w',encoding='utf8'), ensure_ascii=False)
print('FINITO scarico', flush=True)
