import requests,csv
H={'User-Agent':'milano-in-dati/1.0 (research; davide.caniatti@gmail.com)','Accept':'application/sparql-results+json'}
ids=['Q8018','Q797915','Q193507','Q523662','Q119289','Q462596','Q15916381']
q='''SELECT ?t ?tLabel ?tDesc ?sexLabel ?nb ?nd ?occLabel WHERE { VALUES ?t {%s}
 OPTIONAL{?t wdt:P21 ?sex} OPTIONAL{?t wdt:P569 ?nb} OPTIONAL{?t wdt:P570 ?nd} OPTIONAL{?t wdt:P106 ?occ}
 SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". } }'''%' '.join('wd:'+i for i in ids)
r=requests.get('https://query.wikidata.org/sparql',params={'query':q},headers=H,timeout=120)
rows=[]
for b in r.json()['results']['bindings']:
    g=lambda k:b.get(k,{}).get('value','')
    rows.append([g('t').split('/')[-1],g('tLabel'),g('tDesc'),g('sexLabel'),g('nb')[:10],g('nd')[:10],g('occLabel')])
w=csv.writer(open('raw/wd_santi.csv','w',newline='',encoding='utf-8'));w.writerow(['qid','label','desc','sex','birth','death','occupation']);w.writerows(rows)
for x in rows: print(x)
