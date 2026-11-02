"""Scarica i PDF del Rapporto Milano Produttiva (capitolo sulle imprese, edizioni 2019-2026) e ne estrae il testo.

Uso: python -I -X utf8 scarica_camera.py <imprese_dir>
Salta i PDF gia' presenti. Scrive raw/camera_commercio/mp<edizione>_cap_imprese.pdf e .txt (testo estratto con pypdf).
Il sito ester.milomb.camcom.it non dichiara una licenza: i PDF restano in raw/ (non si ripubblicano), si usano solo i numeri delle tabelle.
"""
import sys, os, time
import requests, pypdf
D = sys.argv[1]
OUT = os.path.join(D, "raw", "camera_commercio"); os.makedirs(OUT, exist_ok=True)
B = "https://ester.milomb.camcom.it/sites/default/files/rapporto-mp/"
FILES = {2019: "2019/milano-produttiva-2019-parte-1-capitolo-2.pdf", 2020: "2020/01-capitolo2.pdf", 2021: "2021/02-capitolo-2.pdf",
         2022: "2022/02-capitolo-2.pdf", 2023: "2023/02-capitolo-imprese.pdf", 2024: "2024/02-capitolo-imprese.pdf",
         2025: "2025/02-capitolo-imprese0.pdf", 2026: "2026/02-capitolo-imprese.pdf"}
s = requests.Session(); s.headers["User-Agent"] = "milano-in-dati research (dati aperti, uso divulgativo)"
for ed, rel in FILES.items():
    pdf = os.path.join(OUT, f"mp{ed}_cap_imprese.pdf")
    if not os.path.exists(pdf):
        r = s.get(B + rel, timeout=120); r.raise_for_status(); open(pdf, "wb").write(r.content); print("scaricato", pdf); time.sleep(1.5)
    rd = pypdf.PdfReader(pdf)
    open(os.path.join(OUT, f"mp{ed}_cap_imprese.txt"), "w", encoding="utf8").write("\n".join(f"--- p{i+1}\n" + p.extract_text() for i, p in enumerate(rd.pages)))
