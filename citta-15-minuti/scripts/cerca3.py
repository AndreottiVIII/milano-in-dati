import requests,sys,time,json
H={'User-Agent':'milano-in-dati/1.0 (ricerca open data)'}
out='C:/Users/davide/Desktop/ClaudeTower/milano-in-dati/citta-15-minuti/raw/_catalogo/'
for q in sys.argv[1:]:
    for t in range(4):
        try:
            r=requests.get('https://dati.comune.milano.it/api/3/action/package_search',params={'q':q,'rows':40},headers=H,timeout=120).json()
            if r['success']: break
        except Exception as e: print('err',e,flush=True)
        time.sleep(5)
    json.dump(r,open(out+'x_'+q.replace(' ','_').replace('/','_')+'.json','w'))
    print('###',q,r['result']['count'],flush=True)
    for p in r['result']['results']:
        print(' ',p['name'][:100],'|',p['title'][:80].encode('ascii','replace').decode(),'|',p.get('metadata_modified','')[:10],'|',','.join(sorted(set(x['format'] for x in p['resources']))),flush=True)
    time.sleep(1)
