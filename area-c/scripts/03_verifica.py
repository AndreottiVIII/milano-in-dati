"""Verifica copertura e struttura dei file scaricati. Uso: python -I 03_verifica.py <raw> <out_dir>"""
import sys,os,glob,zipfile,io,re
import pandas as pd
raw,out=sys.argv[1],sys.argv[2]; os.makedirs(out,exist_ok=True)
rows=[]; gates={}
for z in sorted(glob.glob(os.path.join(raw,'*','*.zip'))):
    m=re.search(r'(\d{4})_(\d{1,2})\.zip$',z)
    if not m: continue
    zf=zipfile.ZipFile(z)
    for n in zf.namelist():
        df=pd.read_csv(zf.open(n),dtype=str,low_memory=False)
        df['dt']=pd.to_datetime(df['dataora'].str[:19],errors='coerce')
        df['n']=pd.to_numeric(df['numero_transiti'],errors='coerce')
        df['day']=df['dt'].dt.date
        g=df['id_varco'].astype(str).str.strip('"').unique()
        days=df['day'].nunique()
        mi,ma=df['dt'].min(),df['dt'].max()
        mm=pd.Period(f"{m.group(1)}-{int(m.group(2)):02d}")
        expected=mm.days_in_month
        miss=sorted(set(pd.date_range(mm.start_time,mm.end_time.normalize()).date)-set(df['day'].dropna()))
        rows.append(dict(file=os.path.basename(z),mese=str(mm),righe=len(df),col=len(df.columns),giorni=days,attesi=expected,mancanti=';'.join(str(x) for x in miss),
            primo=mi,ultimo=ma,n_varchi=len(g),transiti=int(df['n'].sum()),slot_minuti=int(df['dt'].dt.minute.nunique()),
            nan_dt=int(df['dt'].isna().sum()),valori_areac=','.join(sorted(df['areac'].astype(str).unique())),
            fuori_mese=int(((df['dt'].dt.to_period('M'))!=mm).sum())))
        gates[str(mm)]=sorted(g,key=lambda x:int(x) if x.isdigit() else 999)
        print(rows[-1]['mese'],rows[-1]['righe'],days,flush=True)
pd.DataFrame(rows).to_csv(os.path.join(out,'copertura_mensili.csv'),index=False,sep=';')
pd.DataFrame([(k,len(v),','.join(v)) for k,v in gates.items()],columns=['mese','n','varchi']).to_csv(os.path.join(out,'varchi_per_mese.csv'),index=False,sep=';')
