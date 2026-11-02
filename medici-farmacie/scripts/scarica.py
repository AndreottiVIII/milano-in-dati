"""Scarica i file grezzi (se non ci sono gia'). Uso: python -I -X utf8 scarica.py <medici-farmacie> <milano-in-dati>
Usa curl con uno User-Agent onesto (nessun browser imitato). I file del Comune per i medici di famiglia sono copiati dal filone citta-15-minuti (stesso file del 29/10/2026)."""
import sys, os, shutil, subprocess
M, P = sys.argv[1], sys.argv[2]
UA = "milano-in-dati-ricerca/1.0 (dati aperti)"
def curl(url, dest):
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print("gia' presente", dest); return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    subprocess.run(["curl", "-sS", "-L", "-m", "300", "-A", UA, "-o", dest, url], check=True); print("scaricato", dest)
curl("https://dati.comune.milano.it/dataset/b48fdaec-a868-47a8-8b59-fc9ed65c84a4/resource/22b05e1f-c5d2-4468-90e5-c098977856ef/download/20261029_pls_final.csv", os.path.join(M, "raw", "comune_pls", "20261029_pls_final.csv"))
curl("https://dati.comune.milano.it/api/3/action/package_show?id=ds235-sociale-pediatri-libera-scelta", os.path.join(M, "raw", "comune_pls", "_metadati.json"))
curl("https://www.dati.salute.gov.it/sites/default/files/opendata/FRM_FARMA_5_20261031.csv", os.path.join(M, "raw", "salute_gov", "FRM_FARMA_5_20261031.csv"))
curl("https://www.bandi.regione.lombardia.it/servizi/servizio/concorsi/download/8a5aa2928df24977018df519242a1401?fileName=Ambiti+Territoriali+carenti+di+Assistenza+Primaria.pdf", os.path.join(M, "raw", "ats_carenti", "ambiti_carenti_AP_bandi_regione.pdf"))
src = os.path.join(P, "citta-15-minuti", "raw", "comune_milano", "mmg")
dst = os.path.join(M, "raw", "comune_mmg"); os.makedirs(dst, exist_ok=True)
for f in os.listdir(src):
    if f.endswith(".csv") or f == "_metadati.json":
        shutil.copy(os.path.join(src, f), os.path.join(dst, f))
print("ok. Per il testo del PDF dei posti carenti: pdftotext -layout ambiti_carenti_AP_bandi_regione.pdf a.txt (opzionale, serve solo a un controllo)")
