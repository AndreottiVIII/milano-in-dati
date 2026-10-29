import sys, json
sys.path.insert(0, sys.argv[1]); import wp
raw = sys.argv[2]
QS = ["attentato Milano bomba morti", "strage Milano bomba", "omicidio politico Milano", "ucciso a Milano militante", "ucciso a Milano Brigate Rosse", "ucciso a Milano Prima Linea",
"ucciso a Milano neofascista", "ucciso a Milano estrema sinistra", "attentato dinamitardo Milano anarchici", "attentato Milano 1921", "attentato Milano Fiera 1928", "agguato Milano terroristi",
"strage di Milano", "attentato terroristico Milano 1969", "attentato Milano mafia 1993", "omicidio Milano commando", "scontri Milano morto manifestazione", "morto negli scontri Milano",
"assassinato a Milano sindacalista", "assassinato a Milano giornalista", "assassinato a Milano magistrato", "assassinato a Milano dirigente", "ucciso Milano squadristi 1921", "ucciso Milano fascisti 1922",
"Milano attentato anarchico teatro", "bomba esplosa Milano morti ferite", "omicidio Milano Nuclei Armati Rivoluzionari", "omicidio Milano Ordine Nuovo", "omicidio Milano Avanguardia Nazionale", "Milano Autonomia operaia morto",
"Milano Lotta Continua ucciso", "Milano Movimento Studentesco morto", "attentato sede Milano morto", "Milano terrorismo islamico attentato", "Milano attentato Lega Nord", "assassinio politico Milano", "omicidio di Milano 1945 partigiano",
"Milano bombardamento strage civile", "Milano strage del 1943", "Milano eccidio", "strage di via Schievano", "attentato Milano Palestina", "attentato Milano 2000", "ucciso a Milano per motivi politici","Milano agguato brigatisti ucciso", "Milano Fronte Nazionale Rivoluzionario"]
res = {}
for q in QS:
    for off in (0, 50):
        d = wp.api(action="query", list="search", srsearch=q, srnamespace="0", srlimit="50", sroffset=str(off))
        for x in d.get("query",{}).get("search",[]):
            res.setdefault(x["title"], []).append(q)
print(len(res))
json.dump(res, open(raw+"/ricerche.json", "w", encoding="utf-8"), ensure_ascii=False)
