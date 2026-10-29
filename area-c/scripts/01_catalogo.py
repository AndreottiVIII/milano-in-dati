import requests,json,sys,time
H={'User-Agent':'milano-in-dati/1.0 (ricerca open data)'}
out={}
for q in ['area c','ecopass','area b','varchi','accessi','ztl','congestion','ingressi']:
    start=0
    while True:
        r=requests.get('https://dati.comune.milano.it/api/3/action/package_search',params={'q':q,'rows':100,'start':start},headers=H,timeout=60).json()['result']
        for p in r['results']: out[p['name']]=p
        start+=100
        if start>=r['count']: break
        time.sleep(0.5)
json.dump(out,open(sys.argv[1],'w'),ensure_ascii=False)
print(len(out))
