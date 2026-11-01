"""Fase 1 - contesto da fonti nazionali: ICCU Anagrafe (biblioteche a Milano, CC0) e Istat censimento biblioteche 2025 (riga Lombardia, tavole 12 e 13).
Uso: python -I -X utf8 contesto_esterno.py <biblioteche_abs>"""
import sys, os, zipfile, io, json, warnings
import pandas as pd, openpyxl
warnings.filterwarnings("ignore")
B = sys.argv[1]; R = os.path.join(B, "raw"); O = os.path.join(B, "pulito")
z = zipfile.ZipFile(os.path.join(R, "iccu_anagrafe", "territorio.zip"))
d = pd.read_csv(io.BytesIO(z.read("territorio.csv")), sep=";", encoding="utf-8-sig", dtype=str)
log = {"iccu_righe_italia": int(len(d))}
mi = d[(d["codice istat comune"] == "015146")]
log["iccu_biblioteche_comune_milano"] = int(len(mi))
mi[["codice-isil", "denominazione", "indirizzo", "cap", "latitudine", "longitudine"]].to_csv(os.path.join(O, "iccu_biblioteche_milano.csv"), sep=";", index=False)
log["iccu_sistema_comunale_isil_it_mi01xx"] = int(mi["denominazione"].str.contains("Comune|comunale|civica|rionale", case=False).sum())
wb = openpyxl.load_workbook(os.path.join(R, "istat_biblioteche_2025", "Tavole-dati.xlsx"), read_only=True)
out = {}
for name in ["Tav. 12", "Tav. 13"]:
    ws = wb[name]
    rows = list(ws.iter_rows(values_only=True))
    out[name] = {"titolo": " ".join(str(c) for c in rows[0] if c), "intestazioni": [[c for c in r if c is not None][:12] for r in rows[3:8]],
                 "righe": [[c for c in r if c is not None] for r in rows if r and r[0] and str(r[0]).strip().lower() in ("lombardia", "italia", "nord-ovest")]}
log["istat_2025"] = out
json.dump(log, open(os.path.join(O, "contesto_esterno.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
print(json.dumps(log, ensure_ascii=False, indent=1, default=str)[:6000])
