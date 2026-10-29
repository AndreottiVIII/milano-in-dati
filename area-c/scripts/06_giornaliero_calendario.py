"""Fase 2, passo 2. Serie giornaliera pulita + calendario.
Uso: python -I 06_giornaliero_calendario.py <raw> <pulito>
Spina dorsale: ds1085 (1/9/2016-31/12/2018), ds1072 vecchio (2019-1-1..2023-11-30), ds1072 nuovo (2023-12-01..2024-11-30, campo h24).
Dove manca il giorno nella spina dorsale, si usa la somma dei mensili per varco (serie somma_mensili). Dove manca tutto: riga vuota (nessun_dato).
Le colonne di dettaglio vengono SEMPRE dai mensili (somma dei varchi) e non dalla serie ufficiale."""
import sys,glob,os,datetime as dt,pandas as pd,numpy as np
raw,out=sys.argv[1:3]; agg=os.path.join(out,'_agg')
def rd(pat,**k): return pd.read_csv(glob.glob(os.path.join(raw,pat))[0],sep=';',**k)
a=rd('ds1085*/*.csv'); a['d']=pd.to_datetime(a.data_giorno.str[:10]); a=a.set_index('d').numero_transiti_giornalieri
o=rd('ds1072*/*no_dic.csv'); o['d']=pd.to_datetime(o.data_giorno.str[:10]); o=o.set_index('d').numero_transiti_giornalieri
n=rd('ds1072*/*2025-01-17.csv'); n['d']=pd.to_datetime(n.data_giorno.str[:10]); n=n.set_index('d')
n.columns=[c.replace('totale_transiti_giornalieri_','') for c in n.columns]
print('colonne ds1072 nuovo',n.columns.tolist())
dupl={nome:int(s.index.duplicated().sum()) for nome,s in [('ds1085',a),('ds1072_vecchio',o),('ds1072_nuovo',n.h24)]}
print('duplicati',dupl)
gd=pd.read_csv(os.path.join(agg,'giorno_dim.csv'),dtype={'val':str}); gd['d']=pd.to_datetime(gd.d)
gs=pd.read_csv(os.path.join(agg,'giorno_slot.csv')); gs['d']=pd.to_datetime(gs.d)
mens=gs.groupby('d').agg(tot_mensili=('n','sum'),na=('na','sum'))
mens['quota_slot_areac']=(mens.na/mens.tot_mensili).round(4)
def piv(dim,names,prefix):
    t=gd[gd.dim==dim].pivot_table(index='d',columns='val',values='n',aggfunc='sum',fill_value=0)
    r=pd.DataFrame(index=t.index)
    for nome,codes in names.items():
        r[prefix+nome]=sum(t[c] if c in t else 0 for c in codes)
    return r
parts=[]
parts.append(piv('moto',{'moto':['1'],'auto':['0']},'tipo_'))
parts.append(piv('esenti',{'autorizzati':['1']},'esenti_'))
parts.append(piv('residenti',{'residenti':['1']},'res_'))
parts.append(piv('veicoli_servizio',{'servizio':['1']},'serv_'))
parts.append(piv('categoria_veicolo',{'persone':['4'],'merci':['3'],'bus':['2'],'altro':['1'],'nc':['0']},'veic_'))
parts.append(piv('classe_areac',{'autorizzati':['1'],'ecologici':['2'],'paganti_residenti':['3'],'paganti_servizio':['4'],'altri_paganti':['5'],'moto':['6'],'nc':['0']},'classe_'))
parts.append(piv('categoria_euro',{'euro0':['1'],'euro1':['2'],'euro2':['3'],'euro3':['4'],'euro4':['5'],'euro5':['6'],'euro6':['7'],'nc':['0']},'euro_'))
parts.append(piv('tipologia_alimentazione',{'benzina':['1'],'diesel':['2'],'elettrico':['3'],'gpl':['6'],'metano':['9'],'gpl_metano':['4'],'ibrido':['5','8','10','11','12'],'altro':['7','13','14'],'nc':['0']},'alim_'))
parts.append(piv('fap',{'si':['1']},'fap_'))
det=pd.concat(parts,axis=1)
days=pd.date_range('2016-09-01','2024-11-30'); df=pd.DataFrame(index=days); df.index.name='data'
df['totale']=np.nan; df['serie']=''; df['fonte_dataset']=''
def put(s,lo,hi,serie,ds):
    s=s[(s.index>=lo)&(s.index<=hi)]
    df.loc[s.index,'totale']=s.values; df.loc[s.index,'serie']=serie; df.loc[s.index,'fonte_dataset']=ds
put(a,'2016-09-01','2018-12-31','ufficiale','ds1085')
put(o,'2019-01-01','2023-11-30','ufficiale','ds1072')
put(n.h24,'2023-12-01','2024-11-30','ufficiale','ds1072 (file 2025-01-17, campo h24)')
df=df.join(mens[['tot_mensili','quota_slot_areac']])
solo=df.totale.isna()&df.tot_mensili.notna()
df.loc[solo,'totale']=df.loc[solo,'tot_mensili']; df.loc[solo,'serie']='somma_mensili'; df.loc[solo,'fonte_dataset']='file mensili per varco (somma)'
df['flag']='ok'
r=df.totale/df.tot_mensili
df.loc[(r-1).abs()>0.01,'flag']='scarto_ufficiale_vs_mensili_oltre_1pct'
df.loc[df.totale.isna(),'flag']='nessun_dato'
df.loc[df.tot_mensili.isna()&df.totale.notna(),'flag']='solo_ufficiale_senza_mensili'
df['rapporto_ufficiale_su_mensili']=r.round(4)
df=df.join(det)
ex=n[[c for c in n.columns if c.startswith('7.30_19.30')]].copy()
ex.columns=['uff_730_1930_auto','uff_730_1930_moto']
df=df.join(ex)
it={'Monday':'lun','Tuesday':'mar','Wednesday':'mer','Thursday':'gio','Friday':'ven','Saturday':'sab','Sunday':'dom'}
df.insert(0,'giorno_settimana',df.index.day_name().map(it))
df.to_csv(os.path.join(out,'ingressi_giornalieri.csv'),sep=';')
# --- calendario
def pasqua(y):
    a=y%19;b=y//100;c=y%100;d=b//4;e=b%4;f=(b+8)//25;g=(b-f+1)//3;h=(19*a+b-d-g+15)%30;i=c//4;k=c%4;l=(32+2*e+2*i-h-k)%7;m=(a+11*h+22*l)//451
    mo=(h+l-7*m+114)//31; da=(h+l-7*m+114)%31+1; return dt.date(y,mo,da)
fest={}
for y in range(2012,2026):
    for (m,d,nome) in [(1,1,'Capodanno'),(1,6,'Epifania'),(4,25,'Liberazione'),(5,1,'Festa del lavoro'),(6,2,'Festa della Repubblica'),(8,15,'Ferragosto'),(11,1,'Ognissanti'),(12,8,'Immacolata'),(12,25,'Natale'),(12,26,'Santo Stefano')]:
        fest[dt.date(y,m,d)]=nome
    p=pasqua(y); fest[p]='Pasqua'; fest[p+dt.timedelta(1)]="Lunedi dell'Angelo"
    fest[dt.date(y,12,7)]="Sant'Ambrogio (patrono di Milano)"
cal=pd.DataFrame(index=days); cal.index.name='data'
cal['giorno_settimana']=df.giorno_settimana
cal['festivo']=[fest.get(d.date(),'') for d in days]
cal['agosto']=(days.month==8).astype(int)
cal['natale_24dic_6gen']=(((days.month==12)&(days.day>=24))|((days.month==1)&(days.day<=6))).astype(int)
cal['lavorativo']=((days.dayofweek<5)&(cal.festivo=='')).astype(int)
cal['covid_fase']=''
cal.loc[(days>='2020-03-09')&(days<='2020-05-03'),'covid_fase']='lockdown_nazionale'
cal.loc[(days>='2020-05-04')&(days<='2020-06-02'),'covid_fase']='fase2_riaperture_graduali'
cal['areac_flag_quota']=df.quota_slot_areac
cal['areac_flag_attivo']=np.where(df.quota_slot_areac.isna(),np.nan,(df.quota_slot_areac>0.3).astype(float))
cal.to_csv(os.path.join(out,'calendario.csv'),sep=';')
print(df.flag.value_counts()); print(df.serie.value_counts())
print(df[df.flag.str.startswith('scarto')][['totale','tot_mensili','rapporto_ufficiale_su_mensili']].to_string())
print(df[df.flag=='nessun_dato'].index.strftime('%Y-%m-%d').tolist())
w=cal[(cal.lavorativo==1)&(cal.areac_flag_attivo==0)]; print('lavorativi con flag areac spento',len(w)); print(w.index.strftime('%Y-%m-%d').tolist())
