import csv,sys,collections
b='../bici-auto-mezzi/raw/gtfs/ext_comune_new/'
routes={r['route_id']:r for r in csv.DictReader(open(b+'routes.txt',encoding='utf-8-sig'))}
rt={k:v for k,v in routes.items() if v['route_type']=='0'}
trips={}
for r in csv.DictReader(open(b+'trips.txt',encoding='utf-8-sig')):
    if r['route_id'] in rt: trips[r['trip_id']]=r['route_id']
stops={r['stop_id']:r for r in csv.DictReader(open(b+'stops.txt',encoding='utf-8-sig'))}
ss=collections.defaultdict(set)
for r in csv.DictReader(open(b+'stop_times.txt',encoding='utf-8-sig')):
    t=trips.get(r['trip_id'])
    if t: ss[r['stop_id']].add(rt[t]['route_short_name'])
w=csv.writer(open(sys.argv[1],'w',newline='',encoding='utf-8'))
w.writerow(['stop_id','stop_name','lat','lon','routes'])
for sid,l in sorted(ss.items(),key=lambda x:stops[x[0]]['stop_name']):
    s=stops[sid]; w.writerow([sid,s['stop_name'],s['stop_lat'],s['stop_lon'],','.join(sorted(l,key=lambda x:(len(x),x)))])
print(len(ss),sorted({v['route_short_name'] for v in rt.values()}))
