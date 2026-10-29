"""Fase 1: (a) quanto bene si puo' collegare CAP -> NIL, (b) comuni confinanti, (c) OSM vs dati del Comune per poste/farmacie/scuole,
(d) OSM entro 1,5 km fuori confine. Uso: python -I analisi_collegamenti.py <strand_dir>. Scrive collegamenti_risultati.json"""
import json,sys,glob
import numpy as np,pandas as pd
from matplotlib.path import Path
from scipy.spatial import cKDTree
S=sys.argv[1]; R=S+'/raw/comune_milano/'
LAT0=45.47
KX=111320*np.cos(np.radians(LAT0)); KY=110540.0
def xy(lon,lat): return np.c_[(np.asarray(lon)-9.19)*KX,(np.asarray(lat)-LAT0)*KY]
def num(s): return pd.to_numeric(s.astype(str).str.replace(',','.'),errors='coerce')
gj=lambda p: json.load(open(p,encoding='utf-8'))
conf=gj(glob.glob(R+'confine_comune/*.geojson')[0])['features'][0]['geometry']
cpoly=np.array(conf['coordinates'][0]); cpath=Path(cpoly)
cxy=xy(cpoly[:,0],cpoly[:,1])
bt=cKDTree(cxy)
def inside(lon,lat): return cpath.contains_points(np.c_[lon,lat])
def dist_boundary(lon,lat):
    # distanza approssimata al confine: al vertice piu vicino (il confine e' denso)
    return bt.query(xy(lon,lat))[0]
res={}
# (a) CAP/NIL dai punti che hanno entrambi
parts=[]
for key,pat,lo,la,cap in [('vicinato','vicinato/*.csv','LONG_X_4326','LAT_Y_4326','CAP'),('farmacie','farmacie/*.csv','LONGITUDINE','LATITUDINE','CAP'),('poste','poste/*.csv','LONG_X_4326','LAT_Y_4326','CAP'),('mmg','mmg/*.csv','LONG_X_4326','LAT_Y_4326','CAP')]:
    d=pd.read_csv(glob.glob(R+pat)[0],sep=';',dtype=str,encoding_errors='replace')
    d=pd.DataFrame({'lon':num(d[lo]),'lat':num(d[la]),'cap':d[cap],'nil':pd.to_numeric(d['ID_NIL'],errors='coerce'),'src':key}).dropna()
    parts.append(d)
P=pd.concat(parts); P=P[P.cap.str.match(r'^201\d\d$')]
res['punti_con_CAP_e_NIL']=int(len(P)); res['CAP_distinti_nei_punti']=int(P.cap.nunique())
res['CAP_non_in_tabella_redditi']=sorted(set(P.cap)-set(pd.read_csv(glob.glob(R+'redditi_2025_ai2024/*.csv')[0],sep=';',dtype=str).CAP))
# purezza: per ogni NIL, quota di punti nel CAP piu frequente; per ogni CAP, quota nel NIL piu frequente
ct=pd.crosstab(P.cap,P.nil)
res['CAP_x_NIL_celle_non_vuote']=int((ct>0).sum().sum())
res['per_CAP_quota_NIL_dominante_media']=round(float((ct.max(axis=1)/ct.sum(axis=1)).mean()),3)
res['per_NIL_quota_CAP_dominante_media']=round(float((ct.max(axis=0)/ct.sum(axis=0)).mean()),3)
res['NIL_con_un_solo_CAP_dominante>=90%']=int(((ct.max(axis=0)/ct.sum(axis=0))>=0.9).sum()); res['NIL_totali_nei_punti']=int(ct.shape[1])
res['CAP_con_NIL_dominante>=90%']=int(((ct.max(axis=1)/ct.sum(axis=1))>=0.9).sum())
res['NIL_che_toccano_>=2_CAP_con_almeno_10%']=int(((ct/ct.sum(axis=0)>=0.10).sum(axis=0)>=2).sum())
ct.to_csv(S+'/collegamento_CAP_NIL_tabella_punti.csv')
# validazione: si puo ricostruire il CAP di un civico dal punto piu vicino con CAP noto? (leave-one-out sui punti distinti)
Pu=P.drop_duplicates(['lon','lat']).reset_index(drop=True)
t=cKDTree(xy(Pu.lon,Pu.lat)); dd,ii=t.query(xy(Pu.lon,Pu.lat),k=2)
acc=(Pu.cap.values[ii[:,1]]==Pu.cap.values)
res['LOO_vicino_piu_prossimo_stesso_CAP']=round(float(acc.mean()),4); res['punti_distinti_validazione']=int(len(Pu))
# civici: assegna CAP del punto noto piu vicino
c=pd.read_csv(R+'civici/estratto/ds634_civici_coordinategeografiche_20261001_final.csv',sep=';',dtype=str)
c=c[(c.STATOCIVICO=='Applicato')].copy(); c['lon']=num(c.LONG_WGS84); c['lat']=num(c.LAT_WGS84); c=c.dropna(subset=['lon','lat'])
dc,ic=t.query(xy(c.lon,c.lat)); c['cap_stimato']=Pu.cap.values[ic]; c['dist_punto_noto_m']=dc
res['civici_applicati']=int(len(c)); res['civici_con_punto_CAP_noto_entro_100m']=int((dc<=100).sum()); res['civici_dist_mediana_m']=round(float(np.median(dc)),1); res['civici_dist_p95_m']=round(float(np.percentile(dc,95)),1)
ctc=pd.crosstab(c.ID_NIL.astype(float),c.cap_stimato)
res['civici_NIL_x_CAP_stimato_celle_non_vuote']=int((ctc>0).sum().sum())
res['civici_per_NIL_quota_CAP_dominante_media']=round(float((ctc.max(axis=1)/ctc.sum(axis=1)).mean()),3)
ctc.to_csv(S+'/collegamento_CAP_NIL_tabella_civici_stimati.csv')
# (b) comuni confinanti
om=gj(S+'/raw/osm_poi/overpass_comuni_admin8.json')['elements']
nb=[]
for e in om:
    nm=e['tags'].get('name'); pts=[]
    for m in e.get('members',[]):
        if m.get('role')=='outer' and 'geometry' in m: pts+= [(g['lon'],g['lat']) for g in m['geometry']]
    if not pts: continue
    pts=np.array(pts); dmin=float(bt.query(xy(pts[:,0],pts[:,1]))[0].min())
    nb.append((nm,round(dmin)))
nb.sort(key=lambda x:x[1])
res['comuni_osm_admin8_nel_rettangolo']=len(nb)
res['comuni_confinanti(distanza_minima_vertici_m<=150)']=[n for n,dm in nb if dm<=150 and n!='Milano']
res['comuni_vicini_non_confinanti_(150-3000m)']=[(n,dm) for n,dm in nb if 150<dm<=3000 and n!='Milano']
# (c)/(d) OSM POI
poi=gj(S+'/raw/osm_poi/overpass_poi_milano.json')['elements']
rows=[]
for e in poi:
    la=e.get('lat') or e.get('center',{}).get('lat'); lo=e.get('lon') or e.get('center',{}).get('lon')
    if la is None: continue
    tg=e['tags']; typ=tg.get('amenity') or tg.get('shop') or tg.get('leisure')
    rows.append((e['type'],e['id'],typ,tg.get('name'),lo,la,tg.get('operator'),tg.get('brand')))
O=pd.DataFrame(rows,columns=['osm_tipo','osm_id','tag','nome','lon','lat','operator','brand'])
O['dentro']=inside(O.lon,O.lat); O['dist_confine_m']=dist_boundary(O.lon,O.lat)
O['fascia']=np.where(O.dentro,'dentro',np.where(O.dist_confine_m<=1500,'fuori_entro_1500m','fuori_oltre_1500m'))
res['OSM_poi_per_tag_e_fascia']=O.groupby(['tag','fascia']).size().unstack(fill_value=0).to_dict('index')
O.to_csv(S+'/raw/osm_poi/osm_poi_milano_estratto.csv',index=False)
# poste
po=O[O.tag=='post_office']
res['OSM_poste_dentro_Milano']=int(((po.fascia=='dentro')).sum())
res['OSM_poste_dentro_con_operatore']=po[po.fascia=='dentro'].operator.fillna('(vuoto)').value_counts().head(8).to_dict()
cp=pd.read_csv(glob.glob(R+'poste/*.csv')[0],sep=';',dtype=str)
res['Comune_poste_righe']=len(cp); res['Comune_poste_per_Ente']=cp.Ente.value_counts().to_dict()
# per ogni posta Comune c'e' una OSM entro 150 m?
tp=cKDTree(xy(po[po.fascia=='dentro'].lon,po[po.fascia=='dentro'].lat))
dcp,_=tp.query(xy(num(cp.LONG_X_4326),num(cp.LAT_Y_4326)))
res['poste_Comune_con_OSM_entro_150m']=int((dcp<=150).sum())
# farmacie
fa=O[O.tag=='pharmacy']; res['OSM_farmacie_dentro']=int((fa.fascia=='dentro').sum())
cf=pd.read_csv(glob.glob(R+'farmacie/*.csv')[0],sep=';',dtype=str)
tf=cKDTree(xy(fa[fa.fascia=='dentro'].lon,fa[fa.fascia=='dentro'].lat))
dcf,_=tf.query(xy(num(cf.LONGITUDINE),num(cf.LATITUDINE)))
res['farmacie_Comune']=len(cf); res['farmacie_Comune_con_OSM_entro_100m']=int((dcf<=100).sum())
# biblioteche, scuole OSM dentro
res['OSM_library_dentro']=int(((O.tag=='library')&(O.fascia=='dentro')).sum()); res['OSM_school_dentro']=int(((O.tag=='school')&(O.fascia=='dentro')).sum())
res['OSM_park_garden_dentro']=int((O.tag.isin(['park','garden'])&(O.fascia=='dentro')).sum())
res['OSM_marketplace_dentro']=int(((O.tag=='marketplace')&(O.fascia=='dentro')).sum())
json.dump(res,open(S+'/collegamenti_risultati.json','w',encoding='utf-8'),ensure_ascii=False,indent=1,default=str)
print(json.dumps(res,ensure_ascii=False,indent=1,default=str))
