import sys, csv, re
src, dst = sys.argv[1], sys.argv[2]
PAT = re.compile(r'(\d{4})(ca)?(?:\s*-\s*(\d{2,4})(ca)?)?')
def periodi(txt):
    out = []
    for m in PAT.finditer(txt):
        a = int(m.group(1)); ca1 = bool(m.group(2))
        b = m.group(3); ca2 = bool(m.group(4))
        if b is None:
            out.append((a, a, ca1, False)); continue
        b = int(b)
        if b < 100:
            b += (a // 100) * 100
            if b < a: b += 100
        out.append((a, b, ca1, ca2))
    return out
rows = list(csv.DictReader(open(src, encoding="utf-8")))
res = []
for i, r in enumerate(rows, 1):
    p = periodi(r["periodo"])
    if not p: print("SENZA PERIODO", r); continue
    nomi = [n.strip() for n in re.split(r'\s+-\s+', r["sala"]) if n.strip()]
    ap = p[0][0]; ch = p[-1][1]
    incerto = p[0][2] or p[-1][3] or len(p) > 1 and False
    res.append({"id_elenco": f"SC{i:03d}", "nome_principale": r["sala"], "nomi_tutti": r["sala"], "indirizzo_elenco": r["indirizzo"],
        "periodo_testo": r["periodo"], "anno_apertura": ap, "anno_chiusura": ch,
        "apertura_incerta": int(p[0][2]), "chiusura_incerta": int(p[-1][3]),
        "n_periodi": len(p), "intervalli": ";".join(f"{a}-{b}" for a, b, _, _ in p), "pagina_pdf": r["pagina"]})
with open(dst, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(res[0])); w.writeheader(); w.writerows(res)
print(len(res), "righe;", "chiusura > 2017:", [x["id_elenco"] for x in res if x["anno_chiusura"] > 2017], "apertura<1896:", [x["id_elenco"] for x in res if x["anno_apertura"]<1896])
