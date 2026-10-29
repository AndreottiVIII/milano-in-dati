import sys, json, re
sys.path.insert(0, sys.argv[1]); import wp
raw = sys.argv[2]
rows = json.load(open(raw+"/piombo_righe_milano.json", encoding="utf-8"))
al = json.load(open(raw+"/piombo_righe_tutte.json", encoding="utf-8"))
rows += [r for r in al if r["luogo_raw"] == "Crescenzago"]
titles = {r["link_nome"] for r in rows if r["link_nome"]}
titles |= {"Assalto all'Avanti!", "Aldo Resega", "Sebastiano Caprino", "Mario Nicoletta", "Volante Rossa \"Martiri Partigiani\"", "Brunilde Tanzi", "Strage dell'Arena", "Strage del Diana",
 "Attentato a Vittorio Emanuele III", "Strage di Piazzale Loreto", "Bombe del 25 aprile 1969", "Strage di piazza Fontana", "Strage del Cinema Eros", "Strage di via Palestro", "Omicidio di Dax",
 "Omicidio di Giuseppe Tavecchio", "Strage della Questura di Milano", "Giovedì nero di Milano", "Pasqua Rossa", "Omicidio di Francesco Di Cataldo", "Omicidio di Luigi Marangoni", "Omicidio di Claudio Varalli e Giannino Zibecchi",
 "Omicidio di Saverio Saltarelli", "Omicidio di Roberto Franceschi", "Omicidio di Antonio Custra", "Omicidio di Fausto e Iaio", "Omicidio di Andrea Campagna", "Omicidio di Pierluigi Torregiani", "Omicidio di Emilio Alessandrini",
 "Omicidio di Renato Briano", "Omicidio di Manfredo Mazzanti", "Strage di Via Schievano", "Omicidio di Guido Galli", "Omicidio di Alberto Brasili", "Omicidio di Sergio Ramelli", "Omicidio di Gaetano Amoroso", "Omicidio di Enrico Pedenovi", "Omicidio Calabresi",
 "Giuseppe Pinelli", "Walter Tobagi", "Antonio Annarumma", "Antonio Marino (poliziotto)", "Michele Tatulli", "Strage del Rapido 904", "Delitto della Cattolica", "Strage di via Moncucco", "Incendio della Pirelli-Bicocca", "Morte di Carlo Saronio", "Carlo Saronio", "Cronologia della strage di Piazza Fontana", "Albino Abico"}
titles = sorted(t for t in titles if t)
out = {}
for i in range(0, len(titles), 20):
    b = titles[i:i+20]
    d = wp.api(action="query", titles="|".join(b), prop="revisions|info|coordinates|pageprops", rvprop="content|ids|timestamp", rvslots="main", inprop="url", redirects="1", colimit="max", ppprop="wikibase_item")
    for p in d["query"]["pages"]:
        if p.get("missing"): print("MISSING", p["title"]); continue
        r = p["revisions"][0]
        out[p["title"]] = {"text": r["slots"]["main"]["content"], "revid": r["revid"], "ts": r["timestamp"], "url": p["fullurl"], "coords": p.get("coordinates", []), "qid": p.get("pageprops", {}).get("wikibase_item")}
    redir = {x["from"]: x["to"] for x in d["query"].get("redirects", [])}
    for k, v in redir.items(): out.setdefault("__redir__", {})[k] = v
print(len(out))
json.dump(out, open(raw+"/wikitext_eventi.json", "w", encoding="utf-8"), ensure_ascii=False)
