"""Scarica dal CKAN del Comune di Milano i dataset elencati (metadati + file CSV/GeoJSON).
Uso: python -I scarica_comune.py <cartella_raw>   (riprendibile: salta i file gia presenti)"""
import requests,sys,time,json,os,re
RAW=sys.argv[1]
H={'User-Agent':'milano-in-dati/1.0 (ricerca open data; davide.caniatti)'}
API='https://dati.comune.milano.it/api/3/action/package_show'
# (cartella, id dataset, formati da scaricare)
DS=[
('farmacie','ds501_farmacie-nel-comune-di-milano',['CSV','GeoJSON']),
('mmg','ds234-sociale-medici-medicina-generale',['CSV','GeoJSON']),
('nidi','ds47-istruzione-asili-nido-localizzazione-delle-strutture',['CSV','GeoJSON']),
('scuole_infanzia_2025','ds3014-infogeo-scuole-infanzia-localizzazione-2025-2026',['CSV','GeoJSON']),
('scuole_infanzia_ds671','ds671-infogeo-scuole-infanzia-localizzazione',['CSV','GeoJSON']),
('scuole_primarie','ds40-infogeo-scuole-primarie-localizzazione',['CSV','GeoJSON']),
('scuole_sec1_2025','ds3016-infogeo-scuole-secondarie-i-grado-localizzazione-2025-2026',['CSV','GeoJSON']),
('scuole_sec1_ds46','ds46-infogeo-scuole-secondarie-i-grado-localizzazione',['CSV','GeoJSON']),
('scuole_sec2','ds78_infogeo_scuole_secondarie_ii_grado_localizzazione_',['CSV','GeoJSON']),
('scuole_edifici_statali_2020','ds1863-elenco-e-localizzazione-degli-edifici-scolastici-attivi-scuole-statali-as-2020-2021',['CSV','GeoJSON']),
('scuole_paritarie_2020','ds1582-istruzione-scuole-paritarie-anagrafica-2020-2021',['CSV','GeoJSON']),
('biblioteche_sistema','ds1306-sistema-bibliotecario-milano',['CSV','GeoJSON']),
('biblioteche_rionali_2013','ds287-cultura-biblioteche-rionali-caratteristiche-localizzazione-2013-2015',['CSV']),
('biblioteche_loc_2007','ds41_infogeo_biblioteche_localizzazione_2007',['CSV','GeoJSON']),
('mercati_coperti','ds2471-mercati-comunali-coperti',['CSV','GeoJSON']),
('mercati_settimanali','ds291-economia-mercati-settimanali-scoperti',['CSV','GeoJSON']),
('mercati_agricoltori','ds2629-mercati-degli-agricoltori',['CSV','GeoJSON']),
('parchi','ds89_infogeo_parchi_giardini_localizzazione_',['CSV','GeoJSON']),
('sport_ds1640','ds1640_infogeo_impianti_sportivi_localizzazione',['CSV','GeoJSON']),
('sport_ds34','ds34_infogeo_impianti_sportivi_localizzazione_',['CSV','GeoJSON']),
('poste','ds555_uffici_postali_milano',['CSV','GeoJSON']),
('vicinato','ds49-economia-esercizi-vicinato-sede-fissa',['CSV','GeoJSON']),
('civici','ds634-numeri-civici-coordinate',['CSV']),
('nil_vigenti','ds964-nil-vigenti-pgt-2030',['CSV','GeoJSON']),
('confine_comune','ds2841-confini-amministrativi-del-comune-di-milano',['CSV','GeoJSON']),
('redditi_2020_ai2019','ds1590-redditi-e-principali-variabili-irpef-su-base-sub-comunale-2020-ai-2019',['CSV']),
('redditi_2021_ai2020','ds1830-redditi-e-principali-variabili-irpef-su-base-sub-comunale-2021-ai-2020',['CSV']),
('redditi_2022_ai2021','ds2275-redditi-e-variabili-irpef-su-base-sub-comunale-2022-a-i-2021',['CSV']),
('redditi_2023_ai2022','ds2734-redditi-e-variabili-irpef-su-base-sub-comunale-2023-a-i-2022',['CSV']),
('redditi_2024_ai2023','ds2946-redditi-e-variabili-irpef-su-base-sub-comunale-2024-a-i-2023',['CSV']),
('redditi_2025_ai2024','ds3009-redditi-e-variabili-irpef-su-base-sub-comunale-2025-a-i-2024',['CSV']),
('pop_cittadinanza_quartiere','ds27-popolazione-residenti-cittadinanza-quartiere-serie-storica',['CSV']),
('pop_caratteristiche_quartiere','ds205-sociale-caratteristiche-demografiche-territoriali-quartiere',['CSV']),
]
def get(url,**kw):
    for t in range(6):
        try:
            r=requests.get(url,headers=H,timeout=180,**kw)
            if r.status_code==200: return r
            print('  HTTP',r.status_code,url[:90],flush=True)
        except Exception as e: print('  err',str(e)[:100],flush=True)
        time.sleep(10*(t+1))
    return None
for cart,pid,fmts in DS:
    d=os.path.join(RAW,cart); os.makedirs(d,exist_ok=True)
    mp=os.path.join(d,'_metadati.json')
    if os.path.exists(mp): pkg=json.load(open(mp,encoding='utf-8'))
    else:
        r=get(API,params={'id':pid})
        if r is None: print('FALLITO metadati',pid,flush=True); continue
        pkg=r.json()['result']; json.dump(pkg,open(mp,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
        time.sleep(1)
    for res in pkg['resources']:
        if res['format'] not in fmts: continue
        fn=re.sub(r'[^A-Za-z0-9._-]','_',res['url'].split('/')[-1])
        fp=os.path.join(d,fn)
        if os.path.exists(fp) and os.path.getsize(fp)>0: print('gia presente',fp,flush=True); continue
        r=get(res['url'])
        if r is None: print('FALLITO',res['url'],flush=True); continue
        open(fp,'wb').write(r.content)
        print('ok',cart,fn,len(r.content),flush=True)
        time.sleep(1.5)
print('FINITO',flush=True)
