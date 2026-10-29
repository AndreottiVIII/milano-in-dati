"""Scarica tutte le risorse dei dataset Area C (e varchi, decodifica, Area B varchi, aree ZTL) dal catalogo CKAN.
Uso: python -I 02_scarica.py <catalogo.json> <cartella_raw>   (riprendibile: salta i file gia' presenti)"""
import json,sys,os,time,re,requests
cat=json.load(open(sys.argv[1])); raw=sys.argv[2]
H={'User-Agent':'milano-in-dati/1.0 (ricerca open data; contatto davide.caniatti@gmail.com)'}
def wanted(n,t):
    s=(n+' '+t).lower()
    return ('area c' in s or 'area-c' in s or 'area_c' in s or 'varchi' in s or n.startswith('ds51_'))
sel=[p for n,p in cat.items() if wanted(n,p['title']) and 'ingressi-spett' not in n]
print(len(sel),'dataset')
log=open(os.path.join(raw,'_download_log.tsv'),'a',encoding='utf-8')
ok=fail=skip=0
for p in sorted(sel,key=lambda p:p['name']):
    dsid=re.match(r'(ds\d+)',p['name']).group(1)
    d=os.path.join(raw,dsid+'_'+re.sub(r'[^a-z0-9]+','-',p['title'].lower()).strip('-')[:60]); os.makedirs(d,exist_ok=True)
    fmts={r['format'] for r in p['resources']}
    for r in p['resources']:
        if r['format']=='JSON' and 'CSV' in fmts: continue   # JSON ridondante
        fn=os.path.basename(r['url'].split('?')[0]); f=os.path.join(d,fn)
        if os.path.exists(f) and os.path.getsize(f)>0: skip+=1; continue
        for k in range(5):
            try:
                resp=requests.get(r['url'],headers=H,timeout=180)
                if resp.status_code==429: time.sleep(30*(k+1)); continue
                resp.raise_for_status()
                open(f+'.part','wb').write(resp.content); os.replace(f+'.part',f)
                ok+=1; log.write(f"{time.strftime('%Y-%m-%d')}\t{dsid}\t{r['url']}\t{len(resp.content)}\n"); log.flush(); break
            except Exception as e:
                time.sleep(5*(k+1))
        else:
            fail+=1; log.write(f"FAIL\t{dsid}\t{r['url']}\n"); log.flush()
        time.sleep(0.7)
print('ok',ok,'skip',skip,'fail',fail)
