"""Legge raw/indicatori/consumo_suolo_2026_Com_Prov_Reg_Naz_v1.0.xlsx (ISPRA, CC BY 4.0) e scrive in pulito/:
  comuni_lungo.csv        tutti i comuni x tutti i fogli (anno/edizione), colonne chiave
  milano_area_completo.csv tutte le 109 colonne per Milano e per i comuni delle citta' di confronto + provincia MI
  province_lungo.csv, nazionale_lungo.csv, regioni_lungo.csv  (tutte le colonne)
  campi.csv               dizionario dei campi (foglio Descrizione_campi)
Uso: python -I -X utf8 estrai_indicatori.py <cartella suolo assoluta>
"""
import sys, os, re, csv, openpyxl

base = sys.argv[1]
src = os.path.join(base, "raw", "indicatori", "consumo_suolo_2026_Com_Prov_Reg_Naz_v1.0.xlsx")
out = os.path.join(base, "pulito")
os.makedirs(out, exist_ok=True)

wb = openpyxl.load_workbook(src, read_only=True)

# dizionario
with open(os.path.join(out, "campi.csv"), "w", newline="", encoding="utf8") as f:
    w = csv.writer(f, delimiter=";")
    for r in wb["Descrizione_campi"].iter_rows(values_only=True):
        w.writerow([r[0], r[1], r[2], r[4], r[7]])

CHIAVE = ["csuolo1", "csuolo2", "csuolo4", "csuolo5", "csuolo8", "csuolo9", "csuolo10", "csuolo11", "csuolo12",
          "csuolo13", "csuolo14", "csuolo15", "csuolo17", "csuolo18", "csuolo19", "csuolo20", "cfotov1", "cfotov2",
          "diseco1", "diseco3", "diseco6", "clammi2", "clammi3", "clammi4", "formet1", "formet2", "formet3", "formet4",
          "formet5", "sdgind3", "iscalo1", "cover10", "cover11", "cover12", "cover13"]
# citta' di confronto (codici ISTAT comune): Milano 15146, Roma 58091, Torino 1272, Napoli 63049, Bologna 37006,
# Firenze 48017, Genova 10025
CONFRONTO = {15146, 58091, 1272, 63049, 37006, 48017, 10025}
PROV_MI = 15


def sheets(prefix):
    return [ws for ws in wb.worksheets if ws.title.startswith(prefix + "_")]


def norm_head(h):
    return None if h is None else str(h).strip()


# comuni
fl = open(os.path.join(out, "comuni_lungo.csv"), "w", newline="", encoding="utf8")
wl = csv.writer(fl, delimiter=";")
righe_milano, ordine_col = [], []
wl_head = ["foglio", "anno", "revisione", "pro_com", "nome_comune", "cod_prov", "nome_provincia", "cod_reg", "nome_regione"] + CHIAVE
wl.writerow(wl_head)
n = 0
for ws in sheets("Comuni"):
    m = re.match(r"Comuni_(\d{4})(rev)?$", ws.title)
    anno, rev = int(m.group(1)), bool(m.group(2))
    it = ws.iter_rows(values_only=True)
    head = [norm_head(h) for h in next(it)]
    idx = {h: i for i, h in enumerate(head)}
    for h in head:
        if h not in ordine_col:
            ordine_col.append(h)
    for r in it:
        if r[0] is None:
            continue
        pc = int(r[idx["pro_com"]])
        riga = [ws.title, anno, int(rev), pc, r[idx["nome_comune"]], r[idx["cod_prov"] if "cod_prov" in idx else idx.get("cod_pro")],
                r[idx["nome_provincia"]], r[idx["cod_reg"]], r[idx["nome_regione"]]] + [r[idx[c]] if c in idx else None for c in CHIAVE]
        wl.writerow(riga)
        n += 1
        if pc in CONFRONTO or r[idx.get("cod_prov", idx.get("cod_pro"))] == PROV_MI:
            dd = {"foglio": ws.title, "anno": anno, "revisione": int(rev)}
            dd.update({h: v for h, v in zip(head, r)})
            righe_milano.append(dd)
    print(ws.title, "ok", flush=True)
fl.close()
with open(os.path.join(out, "milano_area_completo.csv"), "w", newline="", encoding="utf8") as fm:
    w = csv.DictWriter(fm, fieldnames=["foglio", "anno", "revisione"] + ordine_col, delimiter=";", restval="")
    w.writeheader()
    w.writerows(righe_milano)
print("righe comuni:", n)

for pref, nome in [("Province", "province_lungo.csv"), ("Regioni", "regioni_lungo.csv"), ("Nazionale", "nazionale_lungo.csv")]:
    rows, cols = [], []
    for ws in sheets(pref):
        m = re.match(rf"{pref}_(\d{{4}})(rev)?$", ws.title)
        it = ws.iter_rows(values_only=True)
        head = [norm_head(h) for h in next(it)]
        for h in head:
            if h not in cols:
                cols.append(h)
        for r in it:
            if r[0] is None:
                continue
            dd = {"foglio": ws.title, "anno": int(m.group(1)), "revisione": int(bool(m.group(2)))}
            dd.update({h: v for h, v in zip(head, r)})
            rows.append(dd)
    with open(os.path.join(out, nome), "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=["foglio", "anno", "revisione"] + cols, delimiter=";", restval="")
        w.writeheader()
        w.writerows(rows)
    print(nome, "ok", len(rows))
