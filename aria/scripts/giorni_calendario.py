"""Giorni di PM10 e ozono per stazione e anno -> data/giorni.json (un decimale, null = giorno senza dato)."""
import csv, json, datetime, os
R = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(R, '..', '..', 'aria', 'pulito', 'aria_giornaliera.csv')
out = {'PM10': {}, 'O3': {}}
for r in csv.DictReader(open(SRC, encoding='utf-8')):
    p = r['inquinante']
    if p not in out or r['valore'] == '':
        continue
    d = datetime.date.fromisoformat(r['data'])
    st = out[p].setdefault(r['id_stazione'], {})
    y = str(d.year)
    if y not in st:
        n = 366 if d.year % 4 == 0 else 365
        st[y] = [None] * n
    st[y][d.timetuple().tm_yday - 1] = round(float(r["valore"]),1)
json.dump(out, open(os.path.join(R, 'data', 'giorni.json'), 'w', encoding='utf-8'), separators=(',', ':'))
print(os.path.getsize(os.path.join(R, 'data', 'giorni.json')))
# controllo contro annuale.json
A = json.load(open(os.path.join(R, '..', '..', 'docs', 'aria', 'data', 'annuale.json'), encoding='utf-8'))
for sid in ['528', '548']:
    for row in A['PM10']['stazioni'][sid][-6:]:
        v = out['PM10'][sid].get(str(row[0]))
        print(sid, row[0], row[4], sum(1 for x in v if x is not None and x > 50) if v else None)
