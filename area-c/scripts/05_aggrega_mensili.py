"""Fase 2, passo 1. Legge i 99 zip mensili (Sett 2016 - Nov 2024) e li riduce a poche tabelle piccole.
Uso: python -I 05_aggrega_mensili.py <raw> <out_dir>   (out_dir = pulito/_agg)
Scrive: varco_giorno.csv, giorno_slot.csv, giorno_dim.csv
Non cambia nessun valore: somma soltanto `numero_transiti`."""
import sys,glob,zipfile,os,re,pandas as pd
raw,out=sys.argv[1:3]; os.makedirs(out,exist_ok=True)
DIMS=['esenti','moto','residenti','veicoli_servizio','categoria_euro','tipologia_alimentazione','categoria_veicolo','classe_areac','fap']
zips=[z for z in sorted(glob.glob(os.path.join(raw,'*','*ingressi_areac_20*.zip')))]
VG=[];GS=[];GD=[];log=[]
for z in zips:
    zf=zipfile.ZipFile(z)
    for nm in zf.namelist():
        df=pd.read_csv(zf.open(nm),dtype=str)
        df['d']=df.dataora.str[:10].str.replace('/','-'); df['slot']=df.dataora.str[11:16]
        df['n']=pd.to_numeric(df.numero_transiti); df['act']=df.areac.astype(int)
        df['na']=df.n*df.act; df['nm']=df.n*(df.moto.astype(int)==1)
        g=df.groupby(['d','id_varco']).agg(n=('n','sum'),na=('na','sum'),nm=('nm','sum')).reset_index(); VG.append(g)
        s=df.groupby(['d','slot']).agg(n=('n','sum'),na=('na','sum')).reset_index(); GS.append(s)
        for dim in DIMS:
            t=df.groupby(['d',dim]).n.sum().reset_index(); t.columns=['d','val','n']; t.insert(1,'dim',dim); GD.append(t)
        log.append((os.path.basename(z),len(df),df.d.nunique(),df.n.sum(),df.n.isna().sum()))
        print(nm,len(df),flush=True)
pd.concat(VG).to_csv(os.path.join(out,'varco_giorno.csv'),index=False)
pd.concat(GS).to_csv(os.path.join(out,'giorno_slot.csv'),index=False)
pd.concat(GD).to_csv(os.path.join(out,'giorno_dim.csv'),index=False)
pd.DataFrame(log,columns=['zip','righe','giorni','transiti','n_nan']).to_csv(os.path.join(out,'log_mesi.csv'),index=False)
