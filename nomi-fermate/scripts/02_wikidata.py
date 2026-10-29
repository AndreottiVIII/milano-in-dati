import requests,sys,json,csv
H={'User-Agent':'milano-in-dati/1.0 (research; davide.caniatti@gmail.com)','Accept':'application/sparql-results+json'}
Q='''SELECT ?s ?sLabel ?n ?nLabel ?nDesc ?sex ?sexLabel ?nb ?nd ?inst ?instLabel ?sinst ?sinstLabel WHERE {
 SERVICE wikibase:box { ?s wdt:P625 ?loc . bd:serviceParam wikibase:cornerSouthWest "Point(9.03 45.40)"^^geo:wktLiteral . bd:serviceParam wikibase:cornerNorthEast "Point(9.46 45.56)"^^geo:wktLiteral . }
 ?s wdt:P31 ?sinst . VALUES ?sinst { wd:Q928830 wd:Q55488 wd:Q928830 }
 OPTIONAL { ?s wdt:P138 ?n . OPTIONAL{?n wdt:P21 ?sex} OPTIONAL{?n wdt:P569 ?nb} OPTIONAL{?n wdt:P570 ?nd} OPTIONAL{?n wdt:P31 ?inst}}
 SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". }
}'''
r=requests.get('https://query.wikidata.org/sparql',params={'query':Q},headers=H,timeout=180)
print(r.status_code,len(r.text))
open('raw/wd_metro_stations.json','w',encoding='utf-8').write(r.text)
j=r.json()['results']['bindings']
rows=[]
for b in j:
    g=lambda k:b.get(k,{}).get('value','')
    rows.append([g('s').split('/')[-1],g('sLabel'),g('sinstLabel'),g('n').split('/')[-1],g('nLabel'),g('nDesc'),g('sexLabel'),g('nb')[:10],g('nd')[:10],g('instLabel')])
w=csv.writer(open('raw/wd_metro_stations.csv','w',newline='',encoding='utf-8'))
w.writerow(['qid','label','station_type','named_qid','named_label','named_desc','sex','birth','death','named_instance'])
w.writerows(rows)
print(len(rows))
for r in rows: print(r[:5],r[6:])
