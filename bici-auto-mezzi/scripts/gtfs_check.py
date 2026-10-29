import sys, zipfile, os, pandas as pd, collections
zf, outdir = sys.argv[1], sys.argv[2]
os.makedirs(outdir, exist_ok=True)
zipfile.ZipFile(zf).extractall(outdir)
def rd(n, **k):
    p=os.path.join(outdir,n)
    return pd.read_csv(p, dtype=str, **k) if os.path.exists(p) else None
for n in ['agency.txt','feed_info.txt','calendar.txt']:
    d=rd(n); print('--',n); print(d.to_string() if d is not None else 'MISSING')
routes=rd('routes.txt'); print('routes',len(routes)); print(routes.route_type.value_counts().to_dict())
print(routes.head(3).to_string())
stops=rd('stops.txt'); print('stops',len(stops)); print(stops.columns.tolist())
if 'location_type' in stops: print(stops.location_type.value_counts(dropna=False).to_dict())
trips=rd('trips.txt'); print('trips',len(trips)); print(trips.columns.tolist())
cd=rd('calendar_dates.txt'); print('calendar_dates',len(cd), cd.date.min(), cd.date.max(), cd.exception_type.value_counts().to_dict())
print('service_ids in trips',trips.service_id.nunique())
cnt=0
for ch in pd.read_csv(os.path.join(outdir,'stop_times.txt'),dtype=str,usecols=['trip_id'],chunksize=2000000):
    cnt+=len(ch)
print('stop_times rows',cnt)
