"""Passo 4a: cerca sul portale CKAN i confini di municipi / zone / circoscrizioni e scarica quelli dei municipi.
uso: python -I 20_confini_ckan.py <cartella elezioni>
Scarica in raw_confini\ (cartella nuova).
"""
import sys, os, json, time, urllib.request, urllib.parse

base = sys.argv[1]
out = os.path.join(base, 'raw', '_confini')
os.makedirs(out, exist_ok=True)
API = 'https://dati.comune.milano.it/api/3/action/'


def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'milano-in-dati/1.0'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


res = {}
for q in ['municipi', 'zone di decentramento', 'circoscrizioni', 'confini municipi', 'infogeo municipi', 'decentramento', 'consigli di zona', 'zone decentramento 1999', 'circoscrizioni 1997']:
    u = API + 'package_search?rows=40&q=' + urllib.parse.quote(q)
    j = json.loads(get(u))
    time.sleep(1)
    for p in j['result']['results']:
        res.setdefault(p['name'], dict(title=p['title'], notes=(p.get('notes') or '')[:200], res=[(r['format'], r['url']) for r in p['resources']]))
    print(q, j['result']['count'])
json.dump(res, open(os.path.join(out, 'ricerca_confini.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in sorted(res.items()):
    print(k[:70], '|', v['title'][:80], '|', sorted(set(f for f, _ in v['res'])))
