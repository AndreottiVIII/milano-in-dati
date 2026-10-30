import requests, json, os, time, datetime
H={'User-Agent':'milano-in-dati/1.0 (research; polite)'}
d=json.load(open('raw/search_all.json'))
log=open('raw/download_log.csv','a')
os.makedirs('raw/ckan_siope_spese',exist_ok=True)
for n,p in sorted(d.items()):
    if 'siope' not in n.lower() or 'spese' not in n.lower() or n.startswith(('ds738','ds739')): continue
    for r in p['resources']:
        if r['format']!='CSV': continue
        fn='raw/ckan_siope_spese/'+r['url'].split('/')[-1]
        if os.path.exists(fn) and os.path.getsize(fn)>0: continue
        for a in range(4):
            try:
                x=requests.get(r['url'],headers=H,timeout=120)
                if x.status_code==200:
                    open(fn,'wb').write(x.content); log.write(f"{datetime.date.today()},{n},CSV,{fn},{len(x.content)},{r['url']}\n"); log.flush(); break
                time.sleep(5*(a+1))
            except Exception as e: time.sleep(5*(a+1))
        time.sleep(1.5)
print('done')
