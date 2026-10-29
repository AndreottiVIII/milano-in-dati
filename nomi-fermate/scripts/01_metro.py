import csv,sys,collections
b='bici-auto-mezzi/raw/gtfs/ext_comune_new/'
routes={r['route_id']:r for r in csv.DictReader(open(b+'routes.txt',encoding='utf-8-sig'))}
mt={k for k,v in routes.items() if v['route_type']=='1'}
trips={}
for r in csv.DictReader(open(b+'trips.txt',encoding='utf-8-sig')):
    if r['route_id'] in mt: trips[r['trip_id']]=r['route_id']
stops={r['stop_id']:r for r in csv.DictReader(open(b+'stops.txt',encoding='utf-8-sig'))}
ss=collections.defaultdict(set)
for r in csv.DictReader(open(b+'stop_times.txt',encoding='utf-8-sig')):
    t=trips.get(r['trip_id'])
    if t: ss[r['stop_id']].add(t)
out=[]
for sid,l in ss.items():
    s=stops[sid]; out.append((sid,s['stop_name'],s['stop_lat'],s['stop_lon'],s['parent_station'],','.join(sorted(l))))
out.sort(key=lambda x:x[1])
w=csv.writer(open(sys.argv[1],'w',newline='',encoding='utf-8'))
w.writerow(['stop_id','stop_name','lat','lon','parent','routes'])
w.writerows(out)
print(len(out))
for o in out: print(o)
