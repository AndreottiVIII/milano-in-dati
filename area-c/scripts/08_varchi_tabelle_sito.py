"""Fase 2, passo 4. Varchi, tabelle e file JSON per la pagina docs/area-c/.
Uso: python -I 08_varchi_tabelle_sito.py <area-c dir> <docs/area-c/data dir> <aria dir>
Legge: pulito/ingressi_giornalieri.csv, calendario.csv, _agg/*, raw/ds82 (varchi), raw/ds51 (confine Area C), aria/raw
Scrive: pulito/ingressi_varco_giorno.csv, varchi.csv, eventi.csv, stazioni_aria_vicino_areac.csv, tabelle_*.csv e i JSON del sito."""
import sys,os,json,glob,math,pandas as pd,numpy as np
base,site,aria=sys.argv[1:4]; P=os.path.join(base,'pulito'); A=os.path.join(P,'_agg'); os.makedirs(site,exist_ok=True)
def sv(o,n):
    with open(os.path.join(site,n),'w',encoding='utf-8') as f: json.dump(o,f,ensure_ascii=False,separators=(',',':'))
d=pd.read_csv(os.path.join(P,'ingressi_giornalieri.csv'),sep=';',parse_dates=['data']).set_index('data')
c=pd.read_csv(os.path.join(P,'calendario.csv'),sep=';',parse_dates=['data']).set_index('data')
d=d.join(c[['festivo','agosto','natale_24dic_6gen','lavorativo']])
d['festivo']=d.festivo.fillna('')
d['tipo']=np.where(d.lavorativo==1,'L',np.where(d.festivo!='','F',np.where(d.index.day_of_week==5,'S',np.where(d.index.day_of_week==6,'D','F'))))
d['normale']=(d.agosto==0)&(d.natale_24dic_6gen==0)
d['y']=d.index.year; d['m']=d.index.month
# ---- varchi
vg=pd.read_csv(os.path.join(A,'varco_giorno.csv')); vg['d']=pd.to_datetime(vg.d); vg['id_varco']=vg.id_varco.astype(int)
vg=vg.rename(columns={'d':'data','id_varco':'id_varco','n':'transiti','nm':'di_cui_moto'})
anag=pd.read_csv(glob.glob(os.path.join(base,'raw','ds82_*','*.csv'))[0],sep=';')
anag=anag.rename(columns={'id_amat':'id_varco','label':'nome','LONG_X_4326':'lon','LAT_Y_4326':'lat'})[['id_varco','nome','lon','lat']]
nome=dict(zip(anag.id_varco,anag.nome))
vg_out=vg[['data','id_varco','transiti','di_cui_moto']].copy(); vg_out.insert(2,'nome_varco',vg_out.id_varco.map(nome))
vg_out.sort_values(['data','id_varco']).to_csv(os.path.join(P,'ingressi_varco_giorno.csv'),sep=';',index=False,date_format='%Y-%m-%d')
vgl=vg.merge(d[['tipo','normale','y','m']],left_on='data',right_index=True)
# controllo: somma varchi = totale mensili
chk=vg.groupby('data').transiti.sum();
print('somma varchi == tot_mensili:',(chk.reindex(d.index).dropna()==d.tot_mensili.dropna()).all())
ultimo=vg.groupby('id_varco').data.max(); primo=vg.groupby('id_varco').data.min()
ln=vgl[(vgl.tipo=='L')&vgl.normale]
def media_varco(df): return df.groupby('id_varco').transiti.mean()
anag['prima_data']=anag.id_varco.map(primo).dt.strftime('%Y-%m-%d'); anag['ultima_data']=anag.id_varco.map(ultimo).dt.strftime('%Y-%m-%d')
anag['stato']=np.where(anag.ultima_data<'2024-11-30','chiuso_dal_'+anag.ultima_data,'attivo')
for y in [2017,2019,2023]: anag['media_lavorativi_%d'%y]=anag.id_varco.map(media_varco(ln[ln.y==y])).round(0)
anag['media_lavorativi_2017_2024']=anag.id_varco.map(media_varco(ln)).round(0)
anag.to_csv(os.path.join(P,'varchi.csv'),sep=';',index=False)
print(anag[anag.stato!='attivo'])
# serie mensile per varco: media dei giorni lavorativi del mese
mesi=pd.period_range('2016-09','2024-11',freq='M')
gm=vgl[vgl.tipo=='L'].groupby(['id_varco',vgl.data.dt.to_period('M')]).transiti.mean().unstack()
gm=gm.reindex(columns=mesi)
varchi=[]
for _,r in anag.iterrows():
    s=gm.loc[r.id_varco] if r.id_varco in gm.index else pd.Series([np.nan]*len(mesi))
    varchi.append({'id':int(r.id_varco),'nome':r.nome.title() if isinstance(r.nome,str) else str(r.id_varco),'lat':round(r.lat,6),'lon':round(r.lon,6),'prima':r.prima_data,'ultima':r.ultima_data,
                   'm2017':None if pd.isna(r.media_lavorativi_2017) else int(r.media_lavorativi_2017),'m2019':None if pd.isna(r.media_lavorativi_2019) else int(r.media_lavorativi_2019),
                   'm2023':None if pd.isna(r.media_lavorativi_2023) else int(r.media_lavorativi_2023),'mtot':None if pd.isna(r.media_lavorativi_2017_2024) else int(r.media_lavorativi_2017_2024),
                   'serie':[None if pd.isna(v) else int(round(v)) for v in s.values]})
sv({'mese0':'2016-09','varchi':varchi},'varchi.json')
# ---- giornaliero per il grafico
full=d.reindex(pd.date_range('2016-09-01','2024-11-30'))
fcode={'ok':0,'solo_ufficiale_senza_mensili':0,'scarto_ufficiale_vs_mensili_oltre_1pct':2,'nessun_dato':3}
fl=[fcode[x] for x in d.flag]
fl=[ (1 if s=='somma_mensili' else f) for f,s in zip(fl,d.serie)]
sv({'d0':'2016-09-01','n':[None if pd.isna(v) else int(v) for v in d.totale],'tipo':''.join(d.tipo),'flag':fl},'giorni.json')
# ---- serie vecchia
v=pd.read_csv(os.path.join(P,'ingressi_giornalieri_2012-2016_conteggio_diverso.csv'),sep=';',parse_dates=['data']).set_index('data')
fm={'ok':0,'livello_ridotto_dal_2016':1,'parziale_probabile':2,'mancante':3}
sv({'d0':'2012-01-01','n':[None if pd.isna(x) else int(x) for x in v.totale],'flag':[fm[x] for x in v.flag]},'vecchia.json')
# ---- tabelle
T={}
L=d[d.tipo=='L']
rows=[]
for y,g in d.groupby('y'):
    ln_=g[(g.tipo=='L')&g.normale]; sn=g[(g.tipo=='L')&g.m.isin([9,10,11])]
    sa=g[(g.tipo=='S')&g.normale]; do=g[(g.tipo=='D')&g.normale]
    rows.append({'anno':int(y),'lavorativi_media':ln_.totale.mean(),'lavorativi_n':int(ln_.totale.notna().sum()),'lavorativi_sett_nov':sn.totale.mean(),'lav_sett_nov_n':int(sn.totale.notna().sum()),
                 'sabato':sa.totale.mean(),'domenica':do.totale.mean(),'auto_lavorativi':ln_.tipo_auto.mean(),'moto_lavorativi':ln_.tipo_moto.mean(),
                 'tutti_i_giorni_media':g.totale.mean(),'giorni_con_dato':int(g.totale.notna().sum())})
ta=pd.DataFrame(rows).set_index('anno')
b=ta.loc[2019,'lavorativi_sett_nov']; ta['indice_sett_nov_vs_2019']=ta.lavorativi_sett_nov/b*100
ta.round(1).to_csv(os.path.join(P,'tabella_per_anno.csv'),sep=';')
T['anno']=[{k:(None if pd.isna(v) else round(float(v),1)) for k,v in r.items()}|{'anno':int(i)} for i,r in ta.iterrows()]
print(ta.round(0).to_string())
# covid: mese per mese lavorativi 2019,2020,2021
mm=L.groupby(['y','m']).totale.mean().unstack(0)
T['mesi']={str(y):[None if pd.isna(x) else round(float(x)) for x in mm[y].reindex(range(1,13))] for y in mm.columns}
mm.round(0).to_csv(os.path.join(P,'tabella_mese_lavorativi.csv'),sep=';')
# giorno della settimana, anni scelti, giorni normali (fuori agosto, Natale, festivi)
nn=d[d.normale&((d.tipo.isin(['L','S','D'])))]
dowo=['lun','mar','mer','gio','ven','sab','dom']
T['dow']={'giorni':dowo}
for y in [2017,2019,2023]:
    x=nn[nn.y==y].groupby('giorno_settimana').totale.mean().reindex(dowo); T['dow'][str(y)]=[None if pd.isna(a) else round(float(a)) for a in x]
pd.DataFrame({k:v for k,v in T['dow'].items() if k!='giorni'},index=dowo).to_csv(os.path.join(P,'tabella_giorno_settimana.csv'),sep=';')
# agosto, festivi
ag=[]
for y in sorted(d.y.unique()):
    g=d[(d.y==y)&(d.tipo=='L')]
    a=g[g.agosto==1].totale.mean(); nrm=g[g.normale].totale.mean(); ag.append({'anno':int(y),'agosto':None if pd.isna(a) else round(float(a)),'normali':round(float(nrm)),'rapporto':None if pd.isna(a) else round(float(a/nrm),3)})
T['agosto']=ag
fe=d[(d.festivo!='')&(d.index.day_of_week<5)&d.totale.notna()&(d.y.isin([2017,2018,2019,2022,2023,2024]))].copy()
ref=d[(d.tipo=='L')&d.normale].groupby('y').totale.mean()
fe['rif']=fe.y.map(ref); fe['r']=fe.totale/fe.rif
ft=fe.groupby('festivo').agg(media=('totale','mean'),rapporto=('r','mean'),n=('totale','count')).sort_values('rapporto')
T['festivi']=[{'festivo':i,'media':round(float(r.media)),'rapporto':round(float(r.rapporto),2),'n':int(r.n)} for i,r in ft.iterrows()]
ft.round(3).to_csv(os.path.join(P,'tabella_festivi_infrasettimanali.csv'),sep=';')
nat=d[(d.natale_24dic_6gen==1)&(d.tipo=='L')&(d.y.isin([2017,2018,2019,2022,2023]))].totale.mean()
T['natale']={'media_lavorativi_24dic_6gen':round(float(nat)),'rif_normali':round(float(ref.loc[[2017,2018,2019,2022,2023]].mean()))}
# mezz'ora
gs=pd.read_csv(os.path.join(A,'giorno_slot.csv')); gs['d']=pd.to_datetime(gs.d)
gs=gs.merge(d[['tipo','normale','y']],left_on='d',right_index=True)
gs=gs[gs.normale&gs.tipo.isin(['L','S','D'])]
prof={}
for (y,tp),g in gs.groupby(['y','tipo']):
    nd=g.d.nunique(); s=(g.groupby('slot').n.sum()/nd)
    prof['%d_%s'%(y,tp)]=[round(float(x),1) for x in s.values]
slots=sorted(gs.slot.unique())
T['mezzora']={'slot':slots,**prof}
pr=pd.DataFrame({k:v for k,v in prof.items()},index=slots); pr.to_csv(os.path.join(P,'tabella_mezzora.csv'),sep=';')
# top varchi
tv=anag.sort_values('media_lavorativi_2017_2024',ascending=False)
T['top']=[{'id':int(r.id_varco),'nome':r.nome.title(),'m2017':None if pd.isna(r.media_lavorativi_2017) else int(r.media_lavorativi_2017),'m2019':None if pd.isna(r.media_lavorativi_2019) else int(r.media_lavorativi_2019),
           'm2023':None if pd.isna(r.media_lavorativi_2023) else int(r.media_lavorativi_2023),'mtot':int(r.media_lavorativi_2017_2024),'stato':r.stato} for _,r in tv.iterrows()]
share=tv.media_lavorativi_2019/tv.media_lavorativi_2019.sum()
T['top_quota2019_primi5']=round(float(share.head(5).sum()),3)
# categorie (lavorativi normali, per anno): quota di classi
cl=[c_ for c_ in d.columns if c_.startswith(('classe_','veic_','euro_','alim_'))]
q=d[(d.tipo=='L')&d.normale&d.tot_mensili.notna()].groupby('y')[cl+['tot_mensili','tipo_moto','esenti_autorizzati','res_residenti','serv_servizio']].mean()
qs=q[cl+['tipo_moto','esenti_autorizzati','res_residenti','serv_servizio']].div(q.tot_mensili,axis=0)*100
qs.round(1).to_csv(os.path.join(P,'tabella_composizione_pct.csv'),sep=';')
T['composizione']={str(y):{k:round(float(v),1) for k,v in r.items()} for y,r in qs.iterrows()}
sv(T,'tabelle.json')
print(qs.round(1)[['classe_autorizzati','classe_ecologici','classe_paganti_residenti','classe_paganti_servizio','classe_altri_paganti','classe_moto','veic_persone','veic_merci','euro_euro6','euro_nc','alim_diesel','alim_benzina','alim_elettrico','alim_ibrido']].to_string())
# ---- eventi
ev=[
('2012-01-16','regola','Parte Area C: ticket 5 euro, lunedi-venerdi 7.30-19.30 (nel C40 anche giovedi fino alle 18.00, da verificare)','https://www.varesenews.it/2012/01/area-c-si-parte/99280/','da verificare'),
('2017-02-13','regola','Ibride, metano, GPL e biocarburanti non sono piu esenti: pagano il ticket (esenzione scaduta il 31/12/2016, applicata dal 13/2/2017)','https://www.ilgiorno.it/milano/cronaca/area-c-ca5dcef2','da verificare'),
('2020-03-09','covid','Inizio del lockdown nazionale (fino al 3 maggio 2020)','https://it.wikipedia.org/wiki/Misure_di_contenimento_della_pandemia_di_COVID-19_in_Italia','da verificare'),
('2020-03-11','area_c','Area C sospesa per l emergenza Covid (ordinanza del sindaco: 11/3 secondo Mentelocale, 12/3 secondo Assolombarda)','https://www.mentelocale.it/milano/8302-parcheggi-gratis-area-c-b-sospese-milano-aperta-solo-stato-necessita.htm','da verificare'),
('2020-06-15','area_c','Area C riattivata (telecamere gia riaccese il 3 giugno secondo Automoto)','https://tg24.sky.it/milano/2020/06/14/area-c-milano','da verificare'),
('2020-11-05','area_c','Area C sospesa di nuovo (ordinanza urgente 53/2020 del 4/11/2020)','https://www.assolombarda.it/servizi/mobilita-e-trasporti/informazioni/covid-19-comune-di-milano-sospese-area-c-e-sosta-a-pagamento','da verificare'),
('2021-02-24','area_c','Area C riattivata con orario ridotto 10.00-19.30','https://www.mentelocale.it/milano/11581-parcheggi-gratis-milano-dopo-riattivazione-area-c-regola-dal-24-febbraio-2021.htm','da verificare'),
('2021-06-09','area_c','Torna l orario pieno 7.30-19.30','https://www.motorbox.com/auto/magazine/vivere-auto/milano-area-b-area-c-strisce-blu-gialle-attive-9-giugno-2021','da verificare'),
('2023-10-30','tariffa','Il ticket passa da 5 a 7,50 euro','https://www.sicurauto.it/news/area-c-milano-ticket-aumenta-del-50-ottobre-2023/','da verificare'),
('2024-01-01','tariffa','Residenti: accessi gratuiti da 41 a 50 l anno','https://www.sicurauto.it/news/area-c-milano-ticket-aumenta-del-50-ottobre-2023/','da verificare'),
]
chiusi=anag[anag.stato!='attivo']
for _,r in chiusi.iterrows():
    nx=(pd.Timestamp(r.ultima_data)+pd.Timedelta(days=1)).strftime('%Y-%m-%d')
    ev.append((nx,'varchi','Il varco %d (%s) non compare piu nei file mensili (ultimo giorno con dati: %s)'%(r.id_varco,r['nome'],r.ultima_data),'raw/ds82 e file mensili (dati del Comune di Milano, AMAT)','dai dati'))
ev=sorted(ev)
pd.DataFrame(ev,columns=['data','tipo','descrizione','fonte','verifica']).to_csv(os.path.join(P,'eventi.csv'),sep=';',index=False)
sv([dict(zip(['data','tipo','descrizione','fonte','verifica'],e)) for e in ev],'eventi.json')
# ---- stazioni aria vicino al confine
from shapely.geometry import shape,Point
from shapely.ops import transform
g=json.load(open(glob.glob(os.path.join(base,'raw','ds51*','*.geojson'))[0],encoding='utf-8'))
poly=[shape(f['geometry']) for f in g['features'] if f['properties'].get('tipo')=='AREA_C'][0]
lat0=45.465; kx=111320*math.cos(math.radians(lat0)); ky=110574
prj=lambda x,y,z=None:((x-9.19)*kx,(y-lat0)*ky)
pm=transform(prj,poly)
com=pd.read_csv(os.path.join(aria,'raw','comune','qaria_stazione.csv'),sep=';')
reg=pd.read_csv(os.path.join(aria,'raw','arpa','ib47-atvt_stazioni_tutte.csv'))
inv=pd.read_csv(os.path.join(aria,'out','inventario_stazioni_inquinanti.csv'))
rows=[]
corr={1:549,2:705,3:539,4:501,5:547,6:548,7:528,8:503,9:502}
for _,r in com.iterrows():
    p=transform(prj,Point(r.LONG_X_4326,r.LAT_Y_4326)); dist=pm.exterior.distance(p) if pm.geom_type=='Polygon' else pm.boundary.distance(p)
    inside=pm.contains(p)
    rows.append({'fonte':'Comune di Milano + ARPA','id_comune':int(r.id_amat),'id_arpa_stazione':corr[int(r.id_amat)],'nome':r.nome.replace(' *','').strip(),'lat':round(r.LAT_Y_4326,5),'lon':round(r.LONG_X_4326,5),
                 'dentro_area_c':bool(inside),'distanza_dal_confine_m':round(float(dist)),'fine_attivita':r.fine_operativita if r.fine_operativita<'2099' else 'in corso','inquinanti_comune':r.inquinanti,
                 'classe':'dentro' if inside else ('vicina (fino a 1,5 km)' if dist<=1500 else 'controllo (oltre 1,5 km)')})
st=pd.DataFrame(rows).sort_values('distanza_dal_confine_m')
# altre stazioni ARPA dell hinterland (entro 20 km dal centro), come possibili controlli
r2=reg[(reg.provincia=='MI')&(reg.comune!='Milano')].drop_duplicates('idstazione').copy()
ex=[]
for _,r in r2.iterrows():
    p=transform(prj,Point(r.lng,r.lat)); dist=pm.boundary.distance(p)
    if dist<=20000:
        sens=reg[reg.idstazione==r.idstazione]
        ex.append({'fonte':'ARPA Lombardia (hinterland)','id_comune':None,'id_arpa_stazione':int(r.idstazione),'nome':(r.nomestazione+' ('+r.comune+')').replace('Libert�','Libertà').replace('Ges�','Gesù'),'lat':round(r.lat,5),'lon':round(r.lng,5),'dentro_area_c':False,'distanza_dal_confine_m':round(float(dist)),
                   'fine_attivita':'in corso' if (sens.storico=='N').any() else 'chiusa','inquinanti_comune':', '.join(sorted(set(sens.nometiposensore))[:8]),'classe':'controllo (oltre 1,5 km)'})
st=pd.concat([st,pd.DataFrame(ex).sort_values('distanza_dal_confine_m')])
st.to_csv(os.path.join(P,'stazioni_aria_vicino_areac.csv'),sep=';',index=False)
sv(st.head(9).to_dict('records'),'stazioni_aria.json')
print(st[['nome','classe','distanza_dal_confine_m','fine_attivita','dentro_area_c']].head(40).to_string())
