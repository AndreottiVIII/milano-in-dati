import requests,sys,time,json,os
H={'User-Agent':'milano-in-dati/1.0 (ricerca open data)'}
out='C:/Users/davide/Desktop/ClaudeTower/milano-in-dati/citta-15-minuti/raw/_catalogo/'
qs=["farmacie","medici medicina generale","asili nido","scuole","biblioteche","mercati comunali coperti","mercati settimanali","mercati agricoli contadini","parchi giardini","impianti sportivi","uffici postali poste","esercizi di vicinato","redditi irpef sub-comunale","popolazione NIL quartieri","civici numeri civici coordinate","confini NIL nuclei identita locale","confine comune di Milano","CAP codice avviamento postale","sezioni di censimento"]
for q in qs:
    fn=out+q.replace(' ','_')+'.json'
    if os.path.exists(fn): continue
    for t in range(4):
        try:
            r=requests.get('https://dati.comune.milano.it/api/3/action/package_search',params={'q':q,'rows':20},headers=H,timeout=120).json()
            if r['success']: break
        except Exception as e: print('err',e,flush=True)
        time.sleep(5)
    json.dump(r,open(fn,'w'))
    print('###',q,r['result']['count'],flush=True)
    for p in r['result']['results']:
        print(' ',p['name'],'|',p['title'][:90],'|',p.get('metadata_modified','')[:10],'|',[x['format'] for x in p['resources']],flush=True)
    time.sleep(1)
