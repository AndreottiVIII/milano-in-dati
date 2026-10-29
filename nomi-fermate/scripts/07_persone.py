# descrizione (it) e mestieri (P106) delle persone trovate nelle catene, per classificare in modo uniforme
import requests,csv,time
H={'User-Agent':'milano-in-dati/1.0 (research; davide.caniatti@gmail.com)','Accept':'application/sparql-results+json'}
q=set()
for r in csv.DictReader(open('raw/wd_hop2.csv',encoding='utf-8')):
    if r['sex']: q.add(r['target_qid'])
for r in csv.DictReader(open('raw/wd_metro_stations.csv',encoding='utf-8')):
    if r['sex']: q.add(r['named_qid'])
q|={'Q8018','Q797915','Q193507','Q523662','Q119289','Q43689','Q462596'}
q=sorted(x for x in q if x)
print(len(q))
rows=[]
for i in range(0,len(q),60):
    ch=q[i:i+60]
    s='''SELECT ?t ?tLabel ?tDesc ?occLabel WHERE { VALUES ?t {%s} OPTIONAL{?t wdt:P106 ?occ}
 SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". } }'''%' '.join('wd:'+x for x in ch)
    for a in range(4):
        r=requests.get('https://query.wikidata.org/sparql',params={'query':s},headers=H,timeout=180)
        if r.status_code==200: break
        time.sleep(10*(a+1))
    for b in r.json()['results']['bindings']:
        g=lambda k:b.get(k,{}).get('value','')
        rows.append([g('t').split('/')[-1],g('tLabel'),g('tDesc'),g('occLabel')])
    time.sleep(2)
w=csv.writer(open('raw/wd_persone.csv','w',newline='',encoding='utf-8'));w.writerow(['qid','label','desc','occupation']);w.writerows(rows)
print(len(rows))
