"""Legge dalle pagine HTML della serata inaugurale (sito pubblico Scala) direttore, regia, scene, costumi e il cast ruolo per ruolo.
Uscita: pulito/_aperture_scala_cast.json  {anno: {direttore, regia, scene, costumi, cast:[[ruolo,nome],...], url, breve}}
Uso: python -I -X utf8 aperture_scala_cast.py <raw/aperture_scala> <raw/scala_stagioni> <out.json>"""
import sys, os, re, html, json, glob
a_dir, b_dir, out = sys.argv[1], sys.argv[2], sys.argv[3]
FILES = {2022: os.path.join(a_dir, "2022-2023__opera__boris-godunov-7-dicembre-serata-inaugurale.html"),
         2023: os.path.join(b_dir, "2023-2024__opera__don-carlo-7-dicembre-serata-inaugurale.html"),
         2024: os.path.join(b_dir, "2024-2025__opera__la-forza-del-destino-7-dicembre-serata-inaugurale.html"),
         2025: os.path.join(b_dir, "2025-2026__opera__una-lady-macbeth-del-distretto-di-mcensk-7-dicembre-serata-inaugurale.html"),
         2026: os.path.join(b_dir, "2026-2027__opera__otello-7-dicembre-serata-inaugurale.html")}
def lines(t):
    s = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    s = re.sub(r"<br\s*/?>", "\n", s); s = re.sub(r"<[^>]+>", "\n", s); s = html.unescape(s)
    return [l.strip() for l in s.split("\n") if l.strip()]
res = {}
for y, f in FILES.items():
    L = lines(open(f, encoding="utf8").read())
    # sezione cast: dopo la riga "Direttore" fino a "In breve" o "Un'ora prima"
    i = L.index("Direttore")
    j = i
    while j < len(L) and not (L[j].startswith("In breve") or L[j].startswith("Un’ora prima") or L[j].startswith("Un'ora prima") or L[j].startswith("Tutte le date") or L[j].startswith("* ")):
        j += 1
    blk = L[i:j]
    d = {}
    ci = blk.index("Cast") if "Cast" in blk else len(blk)
    tech = blk[:ci]
    keys = {"Direttore": "direttore", "Regia": "regia", "Scene": "scene", "Costumi": "costumi"}
    for k in range(0, len(tech) - 1, 2):
        if tech[k] in keys: d[keys[tech[k]]] = tech[k+1]
    rest = blk[ci+1:]
    cast = []; m = 0
    while m < len(rest) - 1:
        cast.append([rest[m], rest[m+1]]); m += 2
    d["cast"] = cast
    # "In breve" (primo paragrafo)
    br = ""
    if "In breve" in L:
        b = L.index("In breve"); 
        for l in L[b+1:b+6]:
            if len(l) > 80: br = l; break
    d["breve"] = br
    tv = [l for l in L if re.search(r"DIRETTA TELEVISIVA|Rai ?1|RAI ?1", l)][:3]
    d["tv"] = tv
    d["file"] = os.path.basename(f)
    res[y] = d
json.dump(res, open(out, "w", encoding="utf8"), ensure_ascii=False, indent=1)
for y, d in res.items(): print(y, d.get("direttore"), "|", d.get("regia"), "|", len(d["cast"]), d["cast"][:4], d["tv"][:1])
