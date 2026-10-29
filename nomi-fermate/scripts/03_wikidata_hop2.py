import requests,csv,time,json
H={'User-Agent':'milano-in-dati/1.0 (research; davide.caniatti@gmail.com)','Accept':'application/sparql-results+json'}
rows=list(csv.DictReader(open('raw/wd_metro_stations.csv',encoding='utf-8')))
qids=sorted({r['named_qid'] for r in rows if r['named_qid']})
out=[]
for i in range(0,len(qids),60):
    ch=qids[i:i+60]
    q='''SELECT ?n ?nLabel ?t ?tLabel ?tDesc ?sex ?sexLabel ?nb ?nd ?occLabel ?tinstLabel WHERE {
 VALUES ?n {%s}
 OPTIONAL { ?n wdt:P138 ?t . OPTIONAL{?t wdt:P21 ?sex} OPTIONAL{?t wdt:P569 ?nb} OPTIONAL{?t wdt:P570 ?nd} OPTIONAL{?t wdt:P106 ?occ} OPTIONAL{?t wdt:P31 ?tinst}}
 SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". } }'''%' '.join('wd:'+x for x in ch)
    for attempt in range(4):
        r=requests.get('https://query.wikidata.org/sparql',params={'query':q},headers=H,timeout=180)
        if r.status_code==200: break
        time.sleep(10*(attempt+1))
    for b in r.json()['results']['bindings']:
        g=lambda k:b.get(k,{}).get('value','')
        out.append([g('n').split('/')[-1],g('nLabel'),g('t').split('/')[-1],g('tLabel'),g('tDesc'),g('sexLabel'),g('nb')[:10],g('nd')[:10],g('occLabel'),g('tinstLabel')])
    time.sleep(2)
w=csv.writer(open('raw/wd_hop2.csv','w',newline='',encoding='utf-8'))
w.writerow(['named_qid','named_label','target_qid','target_label','target_desc','sex','birth','death','occupation','target_instance'])
w.writerows(out)
print(len(out))
