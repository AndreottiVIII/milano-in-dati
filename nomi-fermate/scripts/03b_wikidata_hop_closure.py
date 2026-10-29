# completa la catena P138 (nome -> intitolato a) per i nodi non ancora interrogati, fino a 3 giri
import requests,csv,time
H={'User-Agent':'milano-in-dati/1.0 (research; davide.caniatti@gmail.com)','Accept':'application/sparql-results+json'}
f='raw/wd_hop2.csv'
rows=list(csv.reader(open(f,encoding='utf-8')))
hdr,rows=rows[0],rows[1:]
done={r[0] for r in rows}
for rnd in range(3):
    # nodi: target che sono ancora da interrogare e non sono persone (senza sesso/nascita)
    todo=sorted({r[2] for r in rows if r[2] and r[2] not in done and not r[5]})
    if not todo: break
    print('giro',rnd,len(todo))
    for i in range(0,len(todo),60):
        ch=todo[i:i+60]
        q='''SELECT ?n ?nLabel ?t ?tLabel ?tDesc ?sexLabel ?nb ?nd ?occLabel ?tinstLabel WHERE {
 VALUES ?n {%s}
 OPTIONAL { ?n wdt:P138 ?t . OPTIONAL{?t wdt:P21 ?sex} OPTIONAL{?t wdt:P569 ?nb} OPTIONAL{?t wdt:P570 ?nd} OPTIONAL{?t wdt:P106 ?occ} OPTIONAL{?t wdt:P31 ?tinst}}
 SERVICE wikibase:label { bd:serviceParam wikibase:language "it,en". } }'''%' '.join('wd:'+x for x in ch)
        for a in range(4):
            r=requests.get('https://query.wikidata.org/sparql',params={'query':q},headers=H,timeout=180)
            if r.status_code==200: break
            time.sleep(10*(a+1))
        for b in r.json()['results']['bindings']:
            g=lambda k:b.get(k,{}).get('value','')
            rows.append([g('n').split('/')[-1],g('nLabel'),g('t').split('/')[-1],g('tLabel'),g('tDesc'),g('sexLabel'),g('nb')[:10],g('nd')[:10],g('occLabel'),g('tinstLabel')])
        done.update(ch); time.sleep(2)
w=csv.writer(open(f,'w',newline='',encoding='utf-8'));w.writerow(hdr);w.writerows(rows)
print(len(rows))
