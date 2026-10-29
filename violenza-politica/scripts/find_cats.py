import sys; sys.path.insert(0, sys.argv[1])
import wp
for q in ["Attentati terroristici in Italia", "Stragi in Italia", "Anni di piombo", "Vittime degli anni di piombo", "Omicidi", "Milano attentat", "Strage Milano"]:
    d = wp.api(action="query", list="search", srsearch="incategory:"+'"'+q+'"' if False else q, srnamespace="14", srlimit="15")
    print(q, [x["title"] for x in d["query"]["search"]])
