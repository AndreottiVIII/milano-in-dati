import requests, json, sys, time
H={'User-Agent':'milano-in-dati/1.0 (research; polite)'}
seen={}
for q in ['bilancio','rendiconto','spesa','entrate','PEG','piano esecutivo di gestione','missioni','programmi','previsioni','consuntivo','tributi','imposte','missione','capitolo','sanzioni','Area C','contravvenzioni','debito','mutui','personale','spese']:
    for start in (0,100):
        r=requests.get('https://dati.comune.milano.it/api/3/action/package_search',params={'q':q,'rows':100,'start':start},headers=H,timeout=60)
        j=r.json()['result']
        for p in j['results']:
            seen[p['name']]=p
        if len(j['results'])<100: break
        time.sleep(1)
    time.sleep(1)
print(len(seen))
json.dump(seen,open(sys.argv[1],'w'))
