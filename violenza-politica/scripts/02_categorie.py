import sys, json
sys.path.insert(0, sys.argv[1]); import wp
out = sys.argv[2]
ROOTS = ["Attentati terroristici in Italia", "Stragi commesse in Italia", "Stragi commesse in Italia durante gli anni di piombo",
 "Atti di terrorismo degli anni di piombo e della strategia della tensione", "Stragi e attacchi bomba neofascisti negli anni di piombo",
 "Eventi degli anni di piombo", "Vittime degli anni di piombo e della strategia della tensione", "Vittime delle Brigate Rosse",
 "Attentati e omicidi politici in Italia", "Strage di piazza Fontana", "Anni di piombo", "Stragi commesse nel Regno d'Italia",
 "Omicidi in Italia", "Terrorismo in Italia", "Attentati in Italia", "Storia di Milano", "Storia di Milano nel XX secolo",
 "Eventi a Milano", "Morti a Milano", "Morti assassinati in Italia", "Omicidi commessi dalle Brigate Rosse", "Omicidi commessi da Prima Linea",
 "Attentati terroristici del XX secolo in Italia", "Attentati terroristici del XXI secolo in Italia", "Attentati terroristici in Lombardia", "Fascismo a Milano", "Scontri di piazza in Italia"]
DEPTH = 3
pages = {}   # title -> set(of category paths)
seen = set()
def walk(cat, depth, root):
    if cat in seen: return
    seen.add(cat)
    for t in wp.members("Categoria:"+cat if not cat.startswith("Categoria:") else cat, "page"):
        pages.setdefault(t, set()).add(root + " > " + cat)
    if depth < DEPTH:
        for s in wp.members("Categoria:"+cat if not cat.startswith("Categoria:") else cat, "subcat"):
            walk(s.replace("Categoria:", ""), depth+1, root)
for r in ROOTS:
    try: walk(r, 0, r)
    except Exception as e: print("ERR", r, e)
    print(r, len(pages), len(seen), flush=True)
json.dump({k: sorted(v)[:5] for k, v in pages.items()}, open(out+"/pagine_categorie.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump(sorted(seen), open(out+"/categorie_visitate.json", "w", encoding="utf-8"), ensure_ascii=False)
