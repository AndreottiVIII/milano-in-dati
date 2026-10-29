import json, sys
d = json.load(open('pulito/_cambiasi_hocr.json', encoding='utf-8'))
for pn in map(int, sys.argv[1:]):
    p = d[pn]
    print('=== pagina', pn, p['w'], p['h'])
    ws = sorted(p['parole'], key=lambda w: (w[1] + w[3]) / 2)
    rows = []
    for w in ws:
        yc = (w[1] + w[3]) / 2
        if rows and abs(rows[-1][0] - yc) < 22:
            rows[-1][1].append(w)
            rows[-1][0] = (rows[-1][0] + yc) / 2
        else:
            rows.append([yc, [w]])
    for yc, r in rows:
        r.sort(key=lambda w: w[0])
        print(int(yc), ' | '.join('%d:%s' % (w[0], w[4]) for w in r))
