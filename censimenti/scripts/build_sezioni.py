import sys, os, csv, io, re, xlrd, openpyxl
root=sys.argv[1]; E=root+"/raw/estratti"; P=root+"/pulito"; os.makedirs(P,exist_ok=True)
MI=15146
def wcsv(fn, header, rows):
    with open(os.path.join(P,fn),"w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(header); n=0
        for r in rows: w.writerow(r); n+=1
    print(fn,n,flush=True); return n
def clean(v):
    if isinstance(v,float) and v==int(v): return int(v)
    return v
# --- 1991, 2001 (xls CPA)
for y,f in ((1991,"dati-cpa_1991/dati-cpa_1991/R03_DatiCPA_1991.xls"),(2001,"dati-cpa_2001/dati-cpa_2001/R03_DatiCPA_2001.xls")):
    b=xlrd.open_workbook(os.path.join(E,f)); s=b.sheet_by_index(0); h=s.row_values(0)
    ic=h.index("PRO_COM")
    rows=[[clean(x) for x in s.row_values(r)] for r in range(1,s.nrows) if s.cell_value(r,ic)==MI]
    wcsv(f"sezioni_{y}.csv",h,rows)
    m=b.sheet_by_index(1)
    wcsv(f"variabili_{y}.csv",["riga"]+[f"col{i}" for i in range(m.ncols)],[[r]+m.row_values(r) for r in range(m.nrows)])
# --- 2011 csv
def rd(fn,enc="cp1252"):
    return csv.reader(io.open(fn,encoding=enc,newline=""),delimiter=";")
for tag,sub,name in (("sezioni","Sezioni di Censimento","sezioni_2011"),("areecensimento","Aree di Censimento","ace_2011"),("areesubcomunali","Aree Subcomunali","aree_subcomunali_2011")):
    r=rd(f"{E}/dati-cpa_2011/{sub}/R03_indicatori_2011_{tag}.csv"); h=next(r); ic=h.index("PROCOM")
    wcsv(name+".csv",h,[x for x in r if x and x[ic]==str(MI)])
    r=rd(f"{E}/dati-cpa_2011/{sub}/tracciato_2011_{tag}.csv"); wcsv(f"variabili_2011_{tag}.csv",["campo","definizione"],list(r))
# --- 2021 indicatori xlsx
wb=openpyxl.load_workbook(f"{E}/Dati_regionali_2021/R03_indicatori_2021_sezioni.xlsx",read_only=True)
ws=wb.worksheets[0]; it=ws.iter_rows(values_only=True); h=list(next(it)); ic=h.index("PROCOM")
wcsv("sezioni_2021.csv",h,[[clean(x) for x in r] for r in it if str(r[ic])==str(MI)])
wb=openpyxl.load_workbook(f"{E}/Dati_regionali_2021/TRACCIATO FILE REGIONALI.xlsx",read_only=True)
wcsv("variabili_2021.csv",["campo","definizione"],[r for r in wb.worksheets[0].iter_rows(values_only=True)])
# 2021 base (UTF-16 tab)
r=csv.reader(io.open(f"{E}/R03_21/TAB/SEZ_R03_21.csv",encoding="utf-16",newline=""),delimiter="\t"); h=next(r); ic=h.index("PRO_COM")
wcsv("sezioni_2021_base.csv",h,[x for x in r if x and x[ic]==str(MI)])
# --- attivita economiche (censimento industria e servizi)
rows=[]
for l in io.open(f"{E}/dati-cis_1991/R03_CIS_1991.txt",encoding="latin1"):
    if l[3:6]=="015" and l[6:9]=="146": rows.append([l[9:13].strip(),l[16:19],int(l[19:26]),int(l[26:33]),int(l[33:40]),int(l[40:47]),int(l[47:54]),int(l[54:61])])
wcsv("sezioni_1991_attivita.csv",["sezione","ateco_gruppo","imprese","unita_locali_imprese","addetti_imprese","istituzioni","unita_locali_istituzioni","addetti_istituzioni"],rows)
rows=[]
for tag,fn in (("impresa","R03_DatiCISi_2001.txt"),("unita_locale","R03_DatiCISu_2001.txt")):
    for l in io.open(f"{E}/dati-cis_2001/{fn}",encoding="latin1"):
        if l[2:5]=="015" and l[5:8]=="146": rows.append([tag,l[11:15].strip(),l[15:18],l[18:21],int(l[21:29]),int(l[29:36])])
wcsv("sezioni_2001_attivita.csv",["fonte","sezione","ateco_gruppo","tipo(002 imprese;201 ist.pubbl.;301 nonprofit)","numero","addetti"],rows)
rows=[]; r=rd(f"{E}/dati-sce_2011/Dati_SCE_2011/Sez_AttivitaEconomica/03_AttEcon_SCE_2011.txt"); h=next(r); ic=h.index("PROCOM")
wcsv("sezioni_2011_attivita.csv",h,[x for x in r if x and x[ic]=="15146"])
