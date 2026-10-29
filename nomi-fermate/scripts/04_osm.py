import requests,json
q='''[out:json][timeout:120];
(node["station"="subway"](45.38,9.03,45.56,9.46);node["railway"="station"]["subway"="yes"](45.38,9.03,45.56,9.46);node["railway"="tram_stop"](45.38,9.03,45.56,9.46););
out tags center;'''
r=requests.post('https://overpass.kumi.systems/api/interpreter',data={'data':q},headers={'User-Agent':'milano-in-dati/1.0 (research)'},timeout=180)
print(r.status_code,len(r.text))
open('raw/osm_stops.json','w',encoding='utf-8').write(r.text)
j=r.json()['elements']
print(len(j))
n=sum(1 for e in j if any(k.startswith('name:etymology') for k in e['tags']))
print('with etymology',n)
for e in j:
    if any(k.startswith('name:etymology') for k in e['tags']): print(e['tags'].get('name'),{k:v for k,v in e['tags'].items() if 'etymology' in k})
