"""Estrae il testo OCR di Gatti vol.1 (pagina per pagina) in raw/gatti_testo/gatti_pagine.json. Uso: python -I -X utf8 scripts/gatti_estrai_testo.py raw/programmi_davide/programmi_scala.pdf raw/gatti_testo/gatti_pagine.json"""
import sys, json, pymupdf
d = pymupdf.open(sys.argv[1])
pag = [p.get_text("text") for p in d]
json.dump(pag, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)
print(len(pag), "pagine", sum(len(x) for x in pag), "caratteri")
