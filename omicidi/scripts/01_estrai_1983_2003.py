"""ISTAT DELITTI_DENUNCIATI_1983_2003.xls -> pulito/istat_1983_2003_omicidi_province.csv (tutti i territori).
Uso: python -I -X utf8 01_estrai_1983_2003.py <cartella omicidi>
Colonne lette per posizione, controllando l'intestazione foglio per foglio."""
import sys, os, csv, xlrd
B = sys.argv[1]
wb = xlrd.open_workbook(os.path.join(B, "raw/istat_delitti_1983_2003/estratto/DELITTI_DENUNCIATI_1983_2003.xls"))
ATTESE = {2:"Omicidi dolosi consumati", 8:"Infanticidi", 9:"Omicidi preterinten", 10:"Tentati omicidi", 58:"Totale delitti"}
SUB = {2:"A scopo di furto", 3:"Per motivi di mafia", 4:"Per motivi di onore", 5:"A scopo terroristico", 6:"Per altri motivi", 7:"Totale"}
COL = {"om_furto_rapina":2,"om_mafia":3,"om_onore_passionali":4,"om_terrorismo":5,"om_altri_motivi":6,"om_consumati":7,
       "infanticidi":8,"preterintenzionali":9,"tentati":10,"strage":1,"totale_delitti":58}
REG = {"PIEMONTE","VALLE D'AOSTA","VALLE D'AOSTA/VALLÉE D'AOSTE","LOMBARDIA","TRENTINO-ALTO ADIGE","VENETO","FRIULI-VENEZIA GIULIA","LIGURIA",
       "EMILIA-ROMAGNA","TOSCANA","UMBRIA","MARCHE","LAZIO","ABRUZZO","MOLISE","CAMPANIA","PUGLIA","BASILICATA","CALABRIA","SICILIA","SARDEGNA"}
RIP = {"NORD-OVEST","NORD-EST","CENTRO","SUD","ISOLE","ITALIA"}
out = []
prob = []
for tav, pre in (("totale","Delitti in totale - Anno "),("autori_noti","Delitti di noti - Anno ")):
    for anno in range(1983, 2004):
        s = wb.sheet_by_name(pre + str(anno))
        h4 = s.row_values(4); h5 = s.row_values(5)
        for j, t in ATTESE.items():
            if t.lower() not in str(h4[j]).lower(): prob.append((tav, anno, j, h4[j]))
        for j, t in SUB.items():
            if t.lower() not in str(h5[j]).lower(): prob.append((tav, anno, j, h5[j]))
        for i in range(6, s.nrows):
            r = s.row_values(i)
            nome = str(r[0]).strip()
            if not nome or len(nome) > 40 or not isinstance(r[7], float): continue
            up = nome.upper()
            liv = "Italia" if up == "ITALIA" else "ripartizione" if up in RIP else "regione" if nome == up else "provincia"
            d = {"tavola":tav, "anno":anno, "territorio":nome, "livello":liv}
            for k, j in COL.items():
                v = r[j] if j < len(r) else ""
                d[k] = int(v) if isinstance(v, float) else ""
            out.append(d)
with open(os.path.join(B, "pulito/istat_1983_2003_omicidi_territori.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
print("righe", len(out), "problemi intestazione", prob[:10])
# controllo: somma motivi = totale; somma province = Italia
err = 0
for d in out:
    if sum(d[k] for k in ("om_furto_rapina","om_mafia","om_onore_passionali","om_terrorismo","om_altri_motivi")) != d["om_consumati"]:
        err += 1; print("motivi != totale", d["tavola"], d["anno"], d["territorio"])
print("righe con somma motivi diversa:", err)
for anno in range(1983, 2004):
    p = sum(d["om_consumati"] for d in out if d["tavola"]=="totale" and d["anno"]==anno and d["livello"]=="provincia")
    i = [d["om_consumati"] for d in out if d["tavola"]=="totale" and d["anno"]==anno and d["livello"]=="Italia"][0]
    n = sum(1 for d in out if d["tavola"]=="totale" and d["anno"]==anno and d["livello"]=="provincia")
    m = [d for d in out if d["tavola"]=="totale" and d["anno"]==anno and d["territorio"]=="Milano"][0]
    print(anno, "province", n, "somma", p, "Italia", i, "| Milano cons", m["om_consumati"], "mafia", m["om_mafia"], "onore", m["om_onore_passionali"], "rapina", m["om_furto_rapina"], "terr", m["om_terrorismo"], "altri", m["om_altri_motivi"], "tent", m["tentati"], "infant", m["infanticidi"], "pret", m["preterintenzionali"])
