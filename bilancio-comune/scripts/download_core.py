import requests, json, os, sys, time, datetime
H={'User-Agent':'milano-in-dati/1.0 (research; polite)'}
d=json.load(open('raw/search_all.json'))
core=['ds397-','ds396-','ds399-','ds400-','ds401-','ds1936-','ds2352_','ds2738_','ds2956_','ds3013_','ds227-','ds284-','ds285-']
extra=['ds738_','ds739_','ds478-','ds312-','ds697-','ds633_']
log=open('raw/download_log.csv','a')
for n,p in sorted(d.items()):
    grp = 'core' if any(n.startswith(c) for c in core) else ('extra' if any(n.startswith(c) for c in extra) else None)
    if not grp: continue
    short=n.split('_')[0].split('-')[0]
    out=f'raw/ckan_{short}'
    os.makedirs(out,exist_ok=True)
    for r in p['resources']:
        fn=os.path.join(out,r['url'].split('/')[-1])
        if os.path.exists(fn) and os.path.getsize(fn)>0: continue
        for a in range(4):
            try:
                x=requests.get(r['url'],headers=H,timeout=180)
                if x.status_code==200:
                    open(fn,'wb').write(x.content)
                    log.write(f"{datetime.date.today()},{n},{r['format']},{fn},{len(x.content)},{r['url']}\n"); log.flush()
                    print('ok',fn,len(x.content)); break
                print(x.status_code,fn); time.sleep(5*(a+1))
            except Exception as e:
                print('err',e); time.sleep(5*(a+1))
        time.sleep(1.5)
