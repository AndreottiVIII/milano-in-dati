import zipfile,os,re,sys
root=sys.argv[1]; raw=root+"/raw"
jobs={"istat_sezioni_1991/R03_91_WGS84.zip":None,"istat_sezioni_2001/R03_01_WGS84.zip":None,"istat_sezioni_2011/R03_11_WGS84.zip":None,"istat_sezioni_2021/R03_21.zip":None,
 "istat_variabili_cpa/dati-cpa_1991.zip":r"R03|racciat|\.pdf|\.txt","istat_variabili_cpa/dati-cpa_2001.zip":r"R03|racciat|\.pdf|\.txt","istat_variabili_cpa/dati-cpa_2011.zip":r"R03|racciat",
 "istat_variabili_cis/dati-cis_1991.zip":r"R03|racciat","istat_variabili_cis/dati-cis_2001.zip":r"R03|racciat","istat_variabili_cis/dati-sce_2011.zip":r"/03_|/21_|/22_|RACCIATO",
 "istat_variabili_2021/Dati_regionali_2021.zip":r"R03|TRACCIATO","istat_aree_subcomunali/ASC2011_WGS84.zip":r"Milano","istat_aree_subcomunali/ASC_21.zip":None}
for z,pat in jobs.items():
    out=os.path.join(raw,"estratti",z.split("/")[1].replace(".zip",""))
    if os.path.isdir(out) and os.listdir(out): continue
    os.makedirs(out,exist_ok=True)
    zf=zipfile.ZipFile(os.path.join(raw,z))
    for i in zf.infolist():
        if i.is_dir(): continue
        if pat and not re.search(pat,i.filename,re.I): continue
        p=os.path.realpath(os.path.join(out,i.filename))
        assert p.startswith(os.path.realpath(out))
        zf.extract(i,out)
    print("extracted",z)
