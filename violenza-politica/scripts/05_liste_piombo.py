import sys, json, re
sys.path.insert(0, sys.argv[1]); import wp
raw = sys.argv[2]
titles = [f"Persone uccise negli anni di piombo ({y})" for y in range(1969, 1982)] + ["Persone uccise per violenza politica (1982)", "Cronologia delle persone uccise durante gli anni di piombo", "Cronologia degli anni di piombo e della strategia della tensione", "Cronologia dello squadrismo"]
out = {}
for t in titles:
    d = wp.api(action="query", prop="revisions|info", titles=t, rvprop="content|ids|timestamp", rvslots="main", inprop="url")
    p = d["query"]["pages"][0]
    if p.get("missing"): print("MISSING", t); continue
    r = p["revisions"][0]
    out[t] = {"text": r["slots"]["main"]["content"], "revid": r["revid"], "ts": r["timestamp"]}
    print(t, len(out[t]["text"]))
json.dump(out, open(raw+"/liste_piombo.json", "w", encoding="utf-8"), ensure_ascii=False)
