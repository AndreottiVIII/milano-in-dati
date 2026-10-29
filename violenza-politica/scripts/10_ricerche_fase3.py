# Fase 3: ricerche per parola su Wikipedia it/en/de per colmare lacune (1900-1918, 1945-1968, dopo 1993, bombe e anarchici).
import sys, json
sys.path.insert(0, sys.argv[1]); import wpx
out = sys.argv[2]
Q = {
 "it": ["Cova bomba 1920 Milano anarchici", "Mariani Aguggini anarchici Milano bomba", "attentato anarchico Milano pacco bomba", "pacco bomba Milano anarchici FAI", "attentato caserma Santa Barbara Milano 2009",
   "attentato Milano Volante Rossa", "omicidio politico Milano 1948", "Milano 1948 attentato Togliatti scontri morti", "Milano 1960 scontri morti manifestazione", "bomba Milano 1968", "bomba Milano 1962 attentato", "attentato dinamitardo Milano 1950",
   "attentato Milano 1969 bombe treni agosto", "bombe Milano 1970 attentato", "bomba consolato Milano", "bomba Milano 1964", "bomba Milano 1967", "attentato Milano neofascisti 1945 1946", "eccidio Milano 1945 liberazione", "uccisi a Milano aprile 1945 fascisti",
   "squadristi uccisi Milano 1921 1922", "sciopero generale Milano 1904 morti", "Milano 1914 settimana rossa morti", "Milano 1917 moti pane morti", "Milano 1906 sciopero eccidio", "Milano 1908 sciopero morti", "interventisti Milano 1915 scontri", "attentato anarchico Milano 1900", "attentato Milano 1910 bomba",
   "attentato terroristico Milano 2000", "attentato terroristico Milano 2010", "attentato Milano 2015", "attentato Milano 2018 terrorismo", "attentato Milano 2016 poliziotto Sesto San Giovanni Anis Amri", "terrorismo islamico Milano attentato", "Milano ordigno esplosivo anarchici 2003 2010",
   "omicidio razzista Milano", "omicidio Abdul Guibre Abba Milano", "aggressione fascista Milano morto 1990", "omicidio Milano neofascisti 1990", "morto Milano scontri polizia 2000", "morto scontri Milano No Expo", "Milano 1 maggio 2015 No Expo",
   "agente ucciso Milano terroristi", "Nuove Brigate Rosse Milano", "Brigate Rosse Milano omicidio", "Prima Linea Milano omicidio", "Nuclei Armati Rivoluzionari Milano omicidio", "bomba Milano 1993 attentato Cosa nostra", "attentato Milano 1992 1994 1995",
   "strage Milano mafia attentato 1993 San Giorgio", "Milano Lega Nord aggressione morto", "omicidio carabiniere Milano brigatisti", "fascisti uccisi Milano 1970", "Milano 1971 attentato bomba", "Milano 1974 attentato bomba", "Milano 1975 attentato", "Milano 1976 attentato", "Milano 1977 attentato", "Milano 1978 attentato", "Milano 1979 attentato", "Milano 1980 attentato", "Milano 1981 attentato", "Milano 1982 attentato", "Milano 1984 attentato", "Milano 1985 attentato", "Milano 1986 attentato", "Milano 1987 attentato", "Milano 1988 attentato", "Milano 1989 attentato", "Milano 1990 attentato", "Milano 1991 attentato"],
 "en": ["Milan bombing anarchist", "Milan Cova bomb 1920", "Milan bomb 1920", "Santa Barbara barracks Milan attack 2009", "Milan 2009 bomb barracks Libyan Mohamed Game", "Milan terrorist attack", "Milan bombing 1960s", "Milan attack 1946", "Milan political assassination", "Milan assassination 1900s", "Milan bomb 1921 Diana theatre", "Milan Fair bomb 1928", "Volante Rossa Milan", "Milan bomb 1969 Banca Nazionale dell'Agricoltura", "Milan explosion 1970", "Milan shooting terrorists police killed", "Milan riot killed", "Milan 1948 riots", "Milan anarchist parcel bomb", "Milan 2003 killing Dax", "Milan antifascist killed", "Milan neo-fascist murder", "bomb Milan Duomo", "Milan Piazza Fontana bomb", "Milan Bocconi", "Milan 1993 car bomb Via Palestro"],
 "de": ["Anschlag Mailand Anarchisten 1920 Cova", "Attentat Mailand Kaserne Santa Barbara 2009", "Bombenanschlag Mailand", "Terroranschlag Mailand", "Mailand Attentat 1920"],
}
res = {}
for lang, qs in Q.items():
    for q in qs:
        try: res[f"{lang}|{q}"] = wpx.search(q, lang, 15)
        except Exception as e: res[f"{lang}|{q}"] = [("ERR", str(e))]
        print(lang, q, len(res[f"{lang}|{q}"]), flush=True)
json.dump(res, open(out + "/ricerche_fase3.json", "w", encoding="utf-8"), ensure_ascii=False)
