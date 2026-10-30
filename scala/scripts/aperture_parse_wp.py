"""Legge la lista 'Prime stagionali al Teatro alla Scala' (it.wikipedia, wikitesto in raw/wikipedia/Prime_stagionali_al_Teatro_alla_Scala.json)
e la mette in una tabella: pulito/_aperture_wp_lista.csv  (una riga per stagione, 1778 ... 2028/29), con titolo, compositore, direttore, regia, cast, sala, TV,
note e le date dei giornali citati nelle note (Corriere della Sera).
Uso: python -I -X utf8 aperture_parse_wp.py <json_wikitesto> <csv_out>"""
import sys, json, re, csv
src, out = sys.argv[1], sys.argv[2]
d = json.load(open(src, encoding="utf8"))
rev = d["query"]["pages"][0]["revisions"][0]
t = rev["slots"]["main"]["content"]
print("revisione", rev["revid"], rev["timestamp"])
def clean(s):
    s = re.sub(r"<ref[^>]*?/>", "", s); s = re.sub(r"<ref.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"\[\[([^\]|]*)\|([^\]]*)\]\]", r"\2", s); s = re.sub(r"\[\[([^\]]*)\]\]", r"\1", s)
    s = s.replace("''", "").replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", s).strip(" ;,.")
# casi con due opere nella stessa serata
MULTI = {
 "Salomè di Richard Strauss e I Compagnacci di Primo Riccitelli": [("Salomè", "Richard Strauss"), ("I Compagnacci", "Primo Riccitelli")],
 "Virginia di Pietro Casella e Gli Strelizzi di Salvatore Viganò": [("Virginia", "Pietro Casella"), ("Gli Strelizzi (ballo)", "Salvatore Viganò")],
 "Adelaide di Francia di Cesare Pugni e L'assedio di Corinto di Gioachino Rossini": [("Adelaide di Francia", "Cesare Pugni"), ("L'assedio di Corinto", "Gioachino Rossini")],
 "dittico Cavalleria rusticana e L'amico Fritz di Pietro Mascagni": [("Cavalleria rusticana e L'amico Fritz (dittico)", "Pietro Mascagni")],
 "Gerusalemme, rifacimento de I Lombardi alla prima crociata, di Giuseppe Verdi": [("Gerusalemme (rifacimento de I Lombardi alla prima crociata)", "Giuseppe Verdi")],
 "Giovanna de Guzman, versione censurata de I vespri siciliani, di Giuseppe Verdi": [("Giovanna de Guzman (versione de I vespri siciliani)", "Giuseppe Verdi")],
 "Leila di Granata, rifacimento de L'ebreo, di Giuseppe Apolloni": [("Leila di Granata (rifacimento de L'ebreo)", "Giuseppe Apolloni")],
 "Turandot [op. post.] di Giacomo Puccini": [("Turandot", "Giacomo Puccini")],
}
rows = []
for line in t.split("\n"):
    m = re.match(r"\* (Stagione[^:]*?):\s*(.*)$", line)
    if not m: continue
    lab, rest = m.group(1), m.group(2)
    ym = re.search(r"(\d{4})(?:/(\d{2,4}))?", lab)
    if not ym: continue
    Y = int(ym.group(1))
    if lab.startswith("Stagione d'autunno"): tipo = "autunno 1778"
    elif "Carnevale e Quaresima" in lab: tipo = "Carnevale e Quaresima"
    elif "Carnevale" in lab: tipo = "Carnevale"
    else: tipo = "stagione"
    refs = re.findall(r"<ref[^>]*>(.*?)</ref>", rest, flags=re.S)
    cd = []
    for r in refs:
        if "Corriere" in r or "corriere" in r:
            dm = re.search(r"\|\s*data\s*=\s*([^|}]+)", r); tm = re.search(r"\|\s*titolo\s*=\s*([^|}]+)", r)
            cd.append(f"{(dm.group(1).strip() if dm else '')} «{(tm.group(1).strip() if tm else '')}»")
    sq = ""
    r2 = clean(rest)
    sala = ""; nota = ""; tv = ""; cast = ""; direttore = ""; regia = ""
    mm = re.search(r"\((?:al|alla|presso) ([^)]*)\)", r2)
    if mm: sala = mm.group(1); r2 = r2.replace(mm.group(0), "").strip()
    mm = re.search(r"\[(al [^\]]*)\]", r2)
    if mm: sala = mm.group(1)[3:]; r2 = r2.replace(mm.group(0), "").strip()
    mm = re.search(r"\[(non inaugurazione[^\]]*)\]", r2)
    if mm: nota = mm.group(1); r2 = r2.replace(mm.group(0), "").strip()
    mm = re.search(r"diretta su (.*)$", r2)
    if mm: tv = mm.group(1); r2 = r2[:mm.start()].strip(" ;,.")
    mm = re.search(r"\bcon ((?:[A-Z][\w'’.\-ùèéàìòÀ-ÿ]+ ?)+.*)$", r2)
    if mm and " con " in " " + r2: cast = mm.group(1); r2 = r2[:mm.start()].strip(" ;,.")
    mm = re.search(r"[;,]?\s*regia(?: di)?:? (.*)$", r2)
    if mm: regia = mm.group(1); r2 = r2[:mm.start()].strip(" ;,.")
    mm = re.search(r"[;,]?\s*(?:diretta da|dirette da|direttore da|direttore:?|direttore e compositore)\s+(.*)$", r2)
    if mm: direttore = mm.group(1); r2 = r2[:mm.start()].strip(" ;,.")
    mm = re.match(r"^(.*?[a-zà-ÿ'’\]\)]) *; ([A-Z][\w'’. -]+)$", r2)
    if mm and not direttore: r2, direttore = mm.group(1), mm.group(2)
    mm = re.match(r"^(.*?[a-zà-ÿ'’\]\)]) ([A-Z][a-zà-ÿ]+ [A-Z][\w'’. -]+)$", r2) if (not direttore and " di " not in r2.split(";")[-1][-20:]) else None
    regia = re.sub(r"\s*\[.*$", "", regia)
    chiuso = bool(re.search(r"rimase chiuso|Nessuna attività|chiuso", r2))
    opere = []
    if not chiuso:
        if r2 in MULTI: opere = MULTI[r2]
        else:
            r2s = r2
            mt = re.match(r"^(.*) di ([^,;]+?)(?:,? rielaborata da .*)?$", r2s)
            if mt: opere = [(mt.group(1).strip(" ,"), mt.group(2).strip())]
            else: opere = [(r2s, "")]
    rows.append(dict(stagione_wp=lab, anno=Y, tipo=tipo, opere=" + ".join(a for a, b in opere), compositori=" + ".join(b for a, b in opere),
                     direttore=direttore, regia=regia, cast_wp=cast, sala=sala, tv=tv, nota_wp=nota, chiuso=int(chiuso), testo=r2[:300], corriere="; ".join(cd)))
with open(out, "w", encoding="utf8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
print(len(rows), "righe")
