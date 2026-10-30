"""Scarica da it.wikipedia (API MediaWiki, CC BY-SA) il wikitesto delle pagine delle opere che hanno aperto la stagione, per cercarvi le discografie
dal vivo alla Scala. Cache in raw/aperture_wp/it__<titolo>.json. 2,5 s tra richieste. Uso: python -I -X utf8 aperture_scarica_it.py <cartella>"""
import sys, os, json, time, requests, re
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)"}
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
T = ["I vespri siciliani","Macbeth (opera)","La Wally","La Vestale (Spontini)","Norma (opera)","Aida","Un ballo in maschera","Turandot","Otello (Verdi)","Poliuto","La battaglia di Legnano",
 "Il trovatore","Cavalleria rusticana (opera)","L'amico Fritz","La forza del destino","Nabucco","Lucia di Lammermoor","Don Carlo","Ernani","Simon Boccanegra","L'italiana in Algeri","Fidelio",
 "Boris Godunov (opera)","Falstaff (Verdi)","Lohengrin (opera)","Carmen (opera)","Don Giovanni (opera)","Guglielmo Tell (opera)","Idomeneo (opera)","Parsifal (opera)","La Valchiria",
 "Il flauto magico","Armide (Gluck)","Il crepuscolo degli dei","Ifigenia in Aulide (Gluck)","Moïse et Pharaon","L'Europa riconosciuta","Tristano e Isotta (opera)","La traviata",
 "Giovanna d'Arco (opera)","Madama Butterfly","Andrea Chénier (opera)","Attila (opera)","Tosca (opera)","Lady Macbeth del Distretto di Mcensk","Teatro alla Scala","Stagioni liriche del Teatro alla Scala"]
for t in T:
    p = os.path.join(out, "it__" + re.sub(r'[^\w]+','_',t) + ".json")
    if os.path.exists(p): continue
    try:
        r = requests.get("https://it.wikipedia.org/w/api.php", headers=UA, timeout=60, params={"action":"query","prop":"revisions","rvprop":"ids|timestamp|content","rvslots":"main","titles":t,"format":"json","formatversion":2,"redirects":1})
        r.raise_for_status(); open(p,"w",encoding="utf8").write(r.text); print(t,len(r.text),flush=True)
    except Exception as e: print("ERR",t,e,flush=True)
    time.sleep(2.5)
