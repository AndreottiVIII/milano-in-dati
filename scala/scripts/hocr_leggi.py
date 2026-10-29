"""Legge un file hOCR (ABBYY, Internet Archive) e lo salva come JSON: per pagina, lista di righe con parole e riquadri.
Uso: python -I scripts/hocr_leggi.py <file_hocr.html> <uscita.json>"""
import re, sys, json, html
src, out = sys.argv[1], sys.argv[2]
txt = open(src, encoding='utf-8').read()
pages = []
for pm in re.finditer(r'<div class="ocr_page" id="page_(\d+)" title="bbox 0 0 (\d+) (\d+);', txt):
    pages.append((int(pm.group(1)), int(pm.group(2)), int(pm.group(3)), pm.start()))
res = []
for i, (pn, w, h, st) in enumerate(pages):
    en = pages[i+1][3] if i+1 < len(pages) else len(txt)
    chunk = txt[st:en]
    words = []
    for wm in re.finditer(r'<span class="ocrx_word"[^>]*title="bbox (\d+) (\d+) (\d+) (\d+)(?:; x_wconf (\d+))?[^"]*">(.*?)</span>', chunk, re.S):
        t = html.unescape(re.sub(r'<[^>]+>', '', wm.group(6))).strip()
        if t:
            words.append([int(wm.group(1)), int(wm.group(2)), int(wm.group(3)), int(wm.group(4)), t, int(wm.group(5) or -1)])
    res.append({'pagina': pn, 'w': w, 'h': h, 'parole': words})
json.dump(res, open(out, 'w', encoding='utf-8'), ensure_ascii=False)
print(len(res), 'pagine', sum(len(p['parole']) for p in res), 'parole')
