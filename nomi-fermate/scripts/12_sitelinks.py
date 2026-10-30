"""Scarica da Wikidata (CC0) i link a Wikipedia (it, poi en) dei QID usati nella tabella finale delle stazioni metro.
Scrive raw/wd_sitelinks.json {qid: {it: url, en: url}}."""
import csv, json, urllib.request, urllib.parse, re
rows = list(csv.DictReader(open('pulito/fermate_metro_nomi_finale.csv', encoding='utf-8-sig')))
q = sorted({r['qid'] for r in rows if re.fullmatch(r'Q\d+', r['qid'])})
# QID dell'elemento collegato (per luoghi/edifici senza qid proprio): vedi 13_dati_pagina.py
for r in csv.DictReader(open('raw/wd_metro_stations.csv', encoding='utf-8')):
    if r['named_qid']:
        q.append(r['named_qid'])
q = sorted(set(q))
out = {}
for i in range(0, len(q), 40):
    ids = '|'.join(q[i:i+40])
    url = 'https://www.wikidata.org/w/api.php?' + urllib.parse.urlencode({'action': 'wbgetentities', 'ids': ids, 'props': 'sitelinks', 'sitefilter': 'itwiki|enwiki', 'format': 'json'})
    req = urllib.request.Request(url, headers={'User-Agent': 'milano-in-dati/1.0 (davide.caniatti@gmail.com)'})
    data = json.load(urllib.request.urlopen(req, timeout=60))
    for k, e in data.get('entities', {}).items():
        s = e.get('sitelinks', {})
        d = {}
        for lang, key in (('it', 'itwiki'), ('en', 'enwiki')):
            if key in s:
                d[lang] = f'https://{lang}.wikipedia.org/wiki/' + urllib.parse.quote(s[key]['title'].replace(' ', '_'))
        out[k] = d
json.dump(out, open('raw/wd_sitelinks.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
print(len(q), 'QID;', sum(1 for v in out.values() if v), 'con pagina Wikipedia')
