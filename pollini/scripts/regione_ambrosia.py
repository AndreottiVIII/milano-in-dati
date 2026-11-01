"""Legge dai PDF delle note di Regione Lombardia (raw/regione_ambrosia/) il massimo giornaliero e il totale stagionale
di polline di Ambrosia per stazione, e li scrive in pulito/ambrosia_regione_lombardia.csv.
Uso: python -I -X utf8 regione_ambrosia.py <P = cartella pollini assoluta>
2016: tabella-immagine nel PDF (le celle vuote spostano il testo): valori letti sull'immagine e confrontati col testo.
2024 e 2025: letti dal testo del PDF (pdftotext) e controllati contro il numero di stazioni."""
import csv, os, re, subprocess, sys

P = sys.argv[1]
R = os.path.join(P, "raw", "regione_ambrosia")


def txt(f):
    return subprocess.run(["pdftotext", "-layout", os.path.join(R, f), "-"], capture_output=True, text=True,
                          encoding="latin-1").stdout


rows = []
# 2016 (massimi giornalieri soltanto), ordine delle colonne come nella tabella del PDF
st16 = ["Magenta", "Busto Arsizio", "Rho", "Legnano", "Casatenovo", "Desio", "Mantova", "Pavia", "Vertemate con Minoprio", "Sondrio"]
v16 = [67, 110, 86, 61, 39, 105, 6, 23, 7, 3]
t = txt("Nota%20regionale.pdf")
nums = re.findall(r"giornaliera\s+([\d ]+)\n", t)
assert nums and [int(x) for x in nums[0].split()] == [67, 86, 61, 39, 105, 6, 23, 7, 3], nums  # 9 numeri nel testo, Busto A. (110) e' su un'altra riga
for s, v in zip(st16, v16):
    rows.append((2016, s, v, "", "Nota Regione Lombardia (copia sul sito ATS Brianza, Nota regionale.pdf)"))
# 2024
t = txt("ats_insubria-registro-ufficiale-2025-0046901.pdf")
st24 = ["Milano", "Magenta", "Busto Arsizio", "Rho", "Legnano", "Desio", "Sondrio", "Vertemate con Minoprio"]
m = re.search(r"giornaliera massima\)\s*\n?\s*([\d ]+)\n", t.replace("(pollini/m3 giornaliera massima )", "giornaliera massima)\n"))
mx = [int(x) for x in re.search(r"massima \)\s+([\d ]+)\n", t).group(1).split()]
sg = [int(x) for x in re.search(r"stagionale \(pollini/m3\)\s+([\d ]+)\n", t).group(1).split()]
assert len(mx) == len(sg) == len(st24) == 8, (mx, sg)
for s, a, b in zip(st24, mx, sg):
    rows.append((2024, s, a, b, "Nota Regione Lombardia 30/4/2025 (ATS Insubria prot. 0046901)"))
# 2025
t = txt("rescaldina_prot14804_2026.pdf")
st25 = ["Milano", "Magenta", "Busto Arsizio", "Rho", "Legnano", "Lodi", "Pavia", "Desio", "Sondrio"]
mx = [int(x) for x in re.search(r"Concentrazione giornaliera\s+([\d ]+)\n", t).group(1).split()]
sg = [int(x) for x in re.search(r"Anno 2025\s+([\d ]+)\n", t).group(1).split()]
assert len(mx) == len(sg) == len(st25) == 9, (mx, sg)
for s, a, b in zip(st25, mx, sg):
    rows.append((2025, s, a, b, "Allegato 1 nota Regione Lombardia (Comune di Rescaldina prot. 14804 del 8/7/2026)"))
with open(os.path.join(P, "pulito", "ambrosia_regione_lombardia.csv"), "w", encoding="utf8", newline="") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["anno", "stazione", "massimo_giornaliero_granuli_m3", "totale_stagionale_granuli_m3", "fonte"])
    w.writerows(rows)
print(len(rows), "righe")
