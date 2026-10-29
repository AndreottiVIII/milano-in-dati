"""Controlli di qualita sui dataset scaricati (fase 1). Uso: python -I controlli.py <strand_dir>
Scrive <strand>/controlli_risultati.json e stampa un riepilogo. Nessuna libreria geo: punto-in-poligono con matplotlib.path."""
import json,sys,os,glob
import numpy as np,pandas as pd
from matplotlib.path import Path
S=sys.argv[1]; R=S+'/raw/comune_milano/'
def rings(geom):
    t=geom['type'];c=geom['coordinates']
    if t=='Polygon': return [c]
    if t=='MultiPolygon': return c
    raise ValueError(t)
def pip_multi(lon,lat,geom):
    pts=np.c_[lon,lat]; inside=np.zeros(len(pts),bool)
    for poly in rings(geom):
        p=Path(np.array(poly[0])); m=p.contains_points(pts)
        for h in poly[1:]: m&=~Path(np.array(h)).contains_points(pts)
        inside|=m
    return inside
def gj(path): return json.load(open(path,encoding='utf-8'))
conf=gj(glob.glob(R+'confine_comune/*.geojson')[0])['features'][0]['geometry']
nil=gj(R+'nil_vigenti/ds964_nil_wm.geojson')['features']
nil_ids=[int(f['properties']['ID_NIL']) for f in nil]
parchi=gj(R+'parchi/parchi.geojson')['features']
def which_nil(lon,lat):
    out=np.full(len(lon),-1)
    for f,i in zip(nil,nil_ids):
        m=pip_multi(lon,lat,f['geometry']); out[m&(out<0)]=i
    return out
def in_parks(lon,lat):
    m=np.zeros(len(lon),bool)
    for f in parchi: m|=pip_multi(lon,lat,f['geometry'])
    return m
def centroid(geom):
    if geom['type']=='Point': return tuple(geom['coordinates'][:2])
    xs=[];ys=[]
    for poly in rings(geom):
        a=np.array(poly[0]); xs.append(a[:,0].mean()); ys.append(a[:,1].mean())
    return np.mean(xs),np.mean(ys)
def num(s): return pd.to_numeric(s.astype(str).str.replace(',','.'),errors='coerce')
# chiave, file csv, sep, col lon, col lat, col nome, col indirizzo, col nil, col anno/stato, controllo-parchi
CFG=[
('farmacie','farmacie/*.csv',';','LONGITUDINE','LATITUDINE','DESCRIZIONE_FARMACIA','INDIRIZZO','ID_NIL',None,True),
('mmg','mmg/*.csv',';','LONG_X_4326','LAT_Y_4326','cognomeMedico','via','ID_NIL','attivo',True),
('nidi','nidi/*.csv',';','LONG_WGS84','LAT_WGS84','NOMINATIVO','INDIRIZZO','ID_NIL','CODANNOSCOLASTICO',True),
('scuole_infanzia_2025','scuole_infanzia_2025/*.csv',';','LONG_X_4326','LAT_Y_4326','DENOMINAZIONE','INDIRIZZO','ID_NIL','ANNOSCOL',True),
('scuole_infanzia_ds671','scuole_infanzia_ds671/*.csv',';','LONG_X_4326','LAT_Y_4326','DENOMINAZIONE','INDIRIZZO','ID_NIL','ANNOSCOL',True),
('scuole_primarie','scuole_primarie/*.csv',';','LONG_X_4326','LAT_Y_4326','DENOMINAZIONE','INDIRIZZO','ID_NIL','ANNOSCOL',True),
('scuole_sec1_2025','scuole_sec1_2025/*.csv',';','LONG_X_4326','LAT_Y_4326','DENOMINAZIONE','INDIRIZZO','ID_NIL','ANNOSCOL',True),
('scuole_sec1_ds46','scuole_sec1_ds46/*.csv',';','LONG_X_4326','LAT_Y_4326','DENOMINAZIONE','INDIRIZZO','ID_NIL','ANNOSCOL',True),
('scuole_sec2','scuole_sec2/*.csv',';','LONG_X_4326','LAT_Y_4326','DENOMINAZ','INDIRIZZO','ID_NIL',None,True),
('biblioteche_sistema','biblioteche_sistema/*.csv',';','long','lat','Biblioteche - Sede','Indirizzo','ID_NIL',None,True),
('mercati_coperti','mercati_coperti/*.csv',';','LONG_X_4326','LAT_Y_4326','MCC','MCC','ID_NIL','attivo',True),
('mercati_settimanali','mercati_settimanali/*.csv',';','LONG_X_4326','LAT_Y_4326','MERCATO','MERCATO','ID_NIL','status mss',True),
('mercati_agricoltori','mercati_agricoltori/*.csv',',','LONG_WGS84','LAT_WGS84','NOME_MERCATO','INDIRIZZO','ID_NIL',None,True),
('parchi','parchi/*.csv',';','LONG_X_4326_CENTROID','LAT_Y_4326_CENTROID','PARCO','CODICE_AREA',None,None,False),
('poste','poste/*.csv',';','LONG_X_4326','LAT_Y_4326','Ente','Indirizzo','ID_NIL',None,True),
('vicinato','vicinato/*.csv',';','LONG_X_4326','LAT_Y_4326','insegna','Ubicazione','ID_NIL',None,True),
]
res={}
for key,pat,sep,clon,clat,cn,ca,cnil,cdate,chkpark in CFG:
    fs=glob.glob(R+pat)
    if not fs: print('MANCA',key); continue
    d=pd.read_csv(fs[0],sep=sep,dtype=str,encoding='utf-8',encoding_errors='replace')
    r={'file':os.path.basename(fs[0]),'righe':len(d),'colonne':list(d.columns)}
    lon=num(d[clon]);lat=num(d[clat]); d['_lon']=lon;d['_lat']=lat
    miss=lon.isna()|lat.isna()|(lon==0)|(lat==0)
    r['coord_mancanti_o_zero']=int(miss.sum())
    ok=~miss
    r['lon_min_max']=[float(lon[ok].min()),float(lon[ok].max())]; r['lat_min_max']=[float(lat[ok].min()),float(lat[ok].max())]
    ins=pip_multi(lon[ok].values,lat[ok].values,conf)
    r['fuori_confine_comune']=int((~ins).sum())
    idx=d.index[ok][~ins]
    r['fuori_confine_esempi']=d.loc[idx[:4],[c for c in [cn,ca] if c in d.columns]].to_dict('records')
    wn=which_nil(lon[ok].values,lat[ok].values)
    if cnil and cnil in d.columns:
        dn=pd.to_numeric(d.loc[ok,cnil],errors='coerce').values
        r['nil_dichiarato_diverso_dal_poligono']=int(((wn!=dn)&(wn>=0)&~np.isnan(dn)).sum()); r['nil_dichiarato_mancante']=int(np.isnan(dn).sum())
    if chkpark:
        r['dentro_poligono_parco']=int(in_parks(lon[ok].values,lat[ok].values).sum())
    keyc=[c for c in [cn,ca] if c in d.columns]
    r['duplicati_nome+indirizzo']=int(d.duplicated(keyc).sum()) if keyc else None
    r['duplicati_stesso_punto']=int(d[ok].duplicated(['_lon','_lat']).sum())
    r['duplicati_righe_identiche']=int(d.drop(columns=['_lon','_lat']).duplicated().sum())
    if cdate and cdate in d.columns: r['valori_'+cdate]=d[cdate].value_counts(dropna=False).head(12).to_dict()
    r['punti_distinti']=int(d[ok].drop_duplicates(['_lon','_lat']).shape[0])
    if cdate in('ANNOSCOL','CODANNOSCOLASTICO'):
        last=sorted(d[cdate].unique())[-1]; dd=d[ok&(d[cdate]==last)]
        r['ultimo_anno']=last; r['righe_ultimo_anno']=int((d[cdate]==last).sum()); r['punti_distinti_ultimo_anno']=int(dd.drop_duplicates(['_lon','_lat']).shape[0])
    if cdate=='attivo': r['punti_distinti_attivi']=int(d[ok&(d[cdate].isin(['1','SI']))].drop_duplicates(['_lon','_lat']).shape[0])
    res[key]=r
    print(key,{k:v for k,v in r.items() if k not in('colonne','fuori_confine_esempi')},flush=True)
# sport: poligoni, centroide dal geojson
for key,fn in [('sport_ds1640','sport_ds1640/*.geojson'),('sport_ds34','sport_ds34/*.geojson')]:
    fs=glob.glob(R+fn)
    if not fs: continue
    g=gj(fs[0]); fe=g['features']
    cs=np.array([centroid(f['geometry']) if f['geometry'] else (np.nan,np.nan) for f in fe])
    ok=~np.isnan(cs[:,0])
    r={'file':os.path.basename(fs[0]),'features':len(fe),'geometria_mancante':int((~ok).sum()),'tipi_geom':pd.Series([f['geometry']['type'] if f['geometry'] else None for f in fe]).value_counts().to_dict(),'crs':g.get('crs')}
    ins=pip_multi(cs[ok,0],cs[ok,1],conf); r['centroidi_fuori_confine']=int((~ins).sum())
    props=pd.DataFrame([f['properties'] for f in fe]); r['colonne']=list(props.columns)
    for c in props.columns:
        if 'descri' in c.lower(): r['categorie']=props[c].value_counts().head(25).to_dict()
        if 'data' in c.lower(): r['data_min_max']=[str(props[c].min()),str(props[c].max())]
    res[key]=r; print(key,{k:v for k,v in r.items() if k!='colonne'},flush=True)
# parchi geojson
g=gj(R+'parchi/parchi.geojson')['features']; p=pd.DataFrame([f['properties'] for f in g])
a=num(p['AREA_MQ'])
res['parchi_poligoni']={'features':len(g),'area_mq_somma':float(a.sum()),'area_mq_min':float(a.min()),'area_mq_mediana':float(a.median()),'senza_nome':int(p['PARCO'].isna().sum()),'poligoni_sotto_500mq':int((a<500).sum()),'poligoni_sopra_10ha':int((a>100000).sum())}
print('parchi',res['parchi_poligoni'])
# scuole: anni
for key in ['scuole_infanzia_2025','scuole_infanzia_ds671','scuole_primarie','scuole_sec1_2025','scuole_sec1_ds46']:
    f=glob.glob(R+key+'/*.csv')[0]; d=pd.read_csv(f,sep=';',dtype=str,encoding_errors='replace')
    res[key]['righe_per_anno_scolastico']=d['ANNOSCOL'].value_counts().sort_index().to_dict()
    last=sorted(d['ANNOSCOL'].unique())[-1]; res[key]['ultimo_anno']=last
    res[key]['righe_ultimo_anno']=int((d['ANNOSCOL']==last).sum())
    res[key]['tipo_ultimo_anno']=d[d.ANNOSCOL==last]['TIPO'].value_counts().to_dict()
    if 'CODICE' in d: res[key]['codici_distinti_ultimo_anno']=int(d[d.ANNOSCOL==last]['CODICE'].nunique())
    print(key,'anni',res[key]['righe_per_anno_scolastico'],flush=True)
# civici
c=pd.read_csv(R+'civici/estratto/ds634_civici_coordinategeografiche_20261001_final.csv',sep=';',dtype=str)
lon=num(c['LONG_WGS84']);lat=num(c['LAT_WGS84'])
okc=~(lon.isna()|lat.isna())
ins=pip_multi(lon[okc].values,lat[okc].values,conf)
ap=(c.STATOCIVICO=='Applicato')
r={'righe':len(c),'STATOCIVICO':c.STATOCIVICO.value_counts().to_dict(),'RESIDENZIALE':c.RESIDENZIALE.value_counts(dropna=False).to_dict(),'LIVELLO':c.LIVELLO.value_counts().to_dict(),
 'coord_mancanti':int((~okc).sum()),'fuori_confine':int((~ins).sum()),'applicati':int(ap.sum()),'applicati_residenziali':int((ap&(c.RESIDENZIALE=='1')).sum()),
 'applicati_numeri_distinti(via+numero+lettera)':int(c[ap].drop_duplicates(['CODICE_VIA','NUMERO','LETTERA']).shape[0]),
 'applicati_punti_distinti':int(pd.DataFrame({'a':lon[ap],'b':lat[ap]}).drop_duplicates().shape[0]),
 'duplicati_IDMASTER':int(c.duplicated('IDMASTER').sum()),'ID_NIL_mancante':int(c.ID_NIL.isna().sum()),
 'WGS84_X_in_realta':'valori tipo 514817,0392 = metri UTM32N (EPSG:32632), NON gradi; i gradi veri sono in LONG_WGS84/LAT_WGS84',
 'DATA_ATTIVAZIONE_min_max':[c.DATA_ATTIVAZIONE.min(),c.DATA_ATTIVAZIONE.max()]}
wn=which_nil(lon[okc].values,lat[okc].values)
dn=pd.to_numeric(c.loc[okc,'ID_NIL'],errors='coerce').values
r['nil_dichiarato_diverso_dal_poligono']=int(((wn!=dn)&(wn>=0)&~np.isnan(dn)).sum()); r['fuori_da_ogni_NIL']=int((wn<0).sum())
gs=c[ap].groupby('ID_NIL').size()
r['applicati_per_NIL_min_max']=[int(gs.min()),int(gs.max())]
res['civici']=r; print('civici',r,flush=True)
json.dump(res,open(S+'/controlli_risultati.json','w',encoding='utf-8'),ensure_ascii=False,indent=1,default=str)
print('FATTO')
