import csv, collections
r = list(csv.DictReader(open('pulito/_wp_stagioni.csv', encoding='utf-8')))
c = collections.Counter(int(x['anno']) // 10 * 10 for x in r)
print(sorted(c.items()))
for x in r[:3] + r[300:302] + r[-3:]:
    print(x)
print(sum(1 for x in r if not x['compositore']), 'senza compositore;', sum(1 for x in r if x['interpreti']), 'con interpreti', sum(1 for x in r if x['data']), 'con data')
for x in r:
    if not x['compositore']:
        print('NOCOMP', x['anno'], x['titolo'][:80])
