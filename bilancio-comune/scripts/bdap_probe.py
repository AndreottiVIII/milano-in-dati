import requests, json, time, sys
H={'User-Agent':'milano-in-dati/1.0 (research; polite)'}
B='https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/action/'
res={}
for q in ['rendiconto enti locali','rendiconto comuni','bilanci enti territoriali rendiconto spesa missioni programmi','Rendiconto - Schemi di Bilancio','Previsione - Schemi di Bilancio']:
    r=requests.get(B+'package_search',params={'q':q,'rows':50},headers=H,timeout=90)
    print(q,r.status_code)
    try: j=r.json()
    except Exception as e: print(r.text[:300]); continue
    for p in j['result']['results']:
        res[p['name']]=p
    time.sleep(2)
json.dump(res,open('raw/web_probe/bdap_search.json','w'))
for n,p in res.items():
    print(n,'|',p['title'][:110],'|',p.get('license_id'),'|',[(r['format'],r.get('url','')[:100]) for r in p['resources']][:2])
