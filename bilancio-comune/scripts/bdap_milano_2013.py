import requests, csv, io, sys
H={'User-Agent':'milano-in-dati/1.0 (research; polite)'}
url='https://bdap-opendata.rgs.mef.gov.it/SpodCkanApi/api/3/datastore/dump/dc1c560d-4e7b-4a2b-9048-b96027c60099.csv'
out=open('raw/bdap_campione/entrate_2013_MILANO_estratto.csv','w',encoding='utf-8',newline='')
n=0;k=0
with requests.get(url,headers=H,stream=True,timeout=(30,300)) as r:
    r.encoding='cp1252'
    first=True
    for line in r.iter_lines(decode_unicode=True):
        if not line: continue
        n+=1
        if first or '"COMUNE DI MILANO"' in line:
            out.write(line+'\n'); k+=1; first=False
print('righe totali',n,'milano',k)
