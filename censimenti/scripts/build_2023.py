import sys,zipfile,csv,openpyxl,os
root=sys.argv[1]; P=root+"/pulito"
def wb_rows(path):
    return openpyxl.load_workbook(path,read_only=True)
def clean(v):
    return int(v) if isinstance(v,float) and v==int(v) else v
z=zipfile.ZipFile(root+"/raw/istat_variabili_2021_comuni/Comuni_2021.zip"); 
os.makedirs(root+"/raw/estratti/Milano_2021_comuni",exist_ok=True); z.extract("Milano_indicatori_2021_sezioni.xlsx",root+"/raw/estratti/Milano_2021_comuni")
wb=wb_rows(root+"/raw/estratti/Milano_2021_comuni/Milano_indicatori_2021_sezioni.xlsx"); print(wb.sheetnames)
ws=wb.worksheets[0]; rows=[[clean(x) for x in r] for r in ws.iter_rows(values_only=True)]
print("2021 comuni file rows",len(rows)-1)
with open(P+"/sezioni_2021_dalfileComuni.csv","w",newline="",encoding="utf-8") as f: csv.writer(f).writerows(rows)
wb=wb_rows(root+"/raw/estratti/Milano_2023/Comuni_2023/Milano_2023_sezioni.xlsx")
for ws,name in zip(wb.worksheets,("sezioni_2023.csv","variabili_2023.csv")):
    with open(P+"/"+name,"w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); n=0
        for r in ws.iter_rows(values_only=True): w.writerow([clean(x) for x in r]); n+=1
    print(name,n)
