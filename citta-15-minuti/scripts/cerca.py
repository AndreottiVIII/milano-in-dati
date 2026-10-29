import requests,sys,time
H={'User-Agent':'milano-in-dati/1.0 (ricerca open data)'}
for q in sys.argv[1:]:
    r=requests.get('https://dati.comune.milano.it/api/3/action/package_search',params={'q':q,'rows':15},headers=H,timeout=60).json()['result']
    print('###',q,r['count'])
    for p in r['results']:
        print(' ',p['name'],'|',p['title'][:90],'|',p.get('metadata_modified','')[:10],'|',[x['format'] for x in p['resources']])
    time.sleep(1)
