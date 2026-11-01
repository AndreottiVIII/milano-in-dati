"""Estrae dalle voci it.wikipedia (wikitext salvato in raw/wikipedia) i campi dei template {{pdi}}: data posa, luogo, coordinate, scritta.
Uso: python -I -X utf8 parse_wikipedia.py <raw_dir> <pulito_dir>
Licenza voce: CC BY-SA 4.0 (attribuire it.wikipedia, autori della voce)."""
import sys, json, re, csv, os
raw, pul = sys.argv[1], sys.argv[2]
rows = []
for fn, muni_default in [("Pietre_dinciampo_a_Milano.json", None), ("Pietre_dinciampo_nel_centro_storico_di_Milano.json", "Municipio 1")]:
    d = json.load(open(os.path.join(raw, "wikipedia", fn), encoding="utf-8"))
    rev = d["query"]["pages"][0]["revisions"][0]
    w = rev["slots"]["main"]["content"]
    # sezioni per municipio
    sec = [(m.start(), m.group(1)) for m in re.finditer(r"^===\s*(Municipio \d+)\s*===", w, re.M)]
    def muni_at(pos):
        cur = muni_default
        for s, n in sec:
            if s <= pos: cur = n
        return cur
    for tm in re.finditer(r"\{\{pdi\s*\n", w):
        # trova fine del template (bilanciando le graffe)
        i = tm.start(); depth = 0; j = i
        while j < len(w):
            if w.startswith("{{", j): depth += 1; j += 2
            elif w.startswith("}}", j):
                depth -= 1; j += 2
                if depth == 0: break
            else: j += 1
        body = w[i+5:j-2]
        # campi: righe "|nome=valore" (valore può durare più righe fino al prossimo "|campo")
        parts = re.split(r"\n\|(?=[a-z]+\d*=)", "\n" + body)
        f = {}
        for p in parts:
            m = re.match(r"([a-z]+)(\d+)=(.*)", p, re.S)
            if m: f.setdefault(int(m.group(2)), {})[m.group(1)] = m.group(3).strip()
        for k, v in sorted(f.items()):
            co = re.search(r"\{\{Coord\|([\d.]+)\|N\|([\d.]+)\|E[^}]*name=([^}|]*)", v.get("coordinate", ""))
            rows.append({"pagina": fn, "municipio_wiki": muni_at(i), "n": k, "data_posa": v.get("data", ""), "luogo": v.get("luogo", ""),
                         "lat": co.group(1) if co else "", "lon": co.group(2) if co else "",
                         "nome_da_coord": re.sub(r"^Pietra d'inciampo (per|di|a)\s*", "", co.group(3)).strip() if co else "",
                         "uniscidata": v.get("uniscidata", ""), "scritta": re.sub(r"<br\s*/?>", " / ", re.sub(r"</?small>", "", v.get("scritta", "")))})
with open(os.path.join(pul, "wikipedia_pdi.csv"), "w", encoding="utf-8", newline="") as fh:
    wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()), delimiter=";"); wr.writeheader(); wr.writerows(rows)
print(len(rows), "righe; revisione", rev["timestamp"])
