"""Scarica da en/it Wikipedia (API MediaWiki, CC BY-SA) il wikitesto delle pagine delle opere che hanno aperto la stagione della Scala.
Cache in raw/aperture_wp/<lingua>__<titolo>.json (salta i file presenti). 2,5 s tra richieste. Uso: python -I -X utf8 aperture_scarica.py <cartella_raw_aperture_wp>"""
import sys, os, json, time, requests, re
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)"}
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
PAGES = [
 ("en","I vespri siciliani"),("en","Macbeth (opera)"),("en","La Wally"),("en","La vestale"),("en","Norma (opera)"),("en","Aida"),
 ("en","Un ballo in maschera"),("en","Turandot"),("en","Otello (Verdi)"),("en","Poliuto"),("en","La battaglia di Legnano"),("en","Il trovatore"),
 ("en","Cavalleria rusticana"),("en","L'amico Fritz"),("en","La forza del destino"),("en","Nabucco"),("en","Lucia di Lammermoor (opera)"),("en","Don Carlos (opera)"),
 ("en","Ernani"),("en","Simon Boccanegra"),("en","L'italiana in Algeri"),("en","Fidelio"),("en","Boris Godunov (opera)"),("en","Falstaff (opera)"),
 ("en","Lohengrin (opera)"),("en","Carmen"),("en","Don Giovanni"),("en","Guillaume Tell (opera)"),("en","Idomeneo"),("en","Parsifal"),("en","Die Walküre"),
 ("en","The Magic Flute"),("en","Armide (Gluck)"),("en","Götterdämmerung"),("en","Iphigénie en Aulide"),("en","Moïse et Pharaon"),("en","L'Europa riconosciuta"),
 ("en","Tristan und Isolde"),("en","La traviata"),("en","Giovanna d'Arco (opera)"),("en","Madama Butterfly"),("en","Andrea Chénier"),("en","Attila (opera)"),
 ("en","Tosca"),("en","Lady Macbeth of the Mtsensk District"),("en","Otello (Verdi)"),
 ("en","La Scala"),("en","Teatro alla Scala"),("en","Teatro alla Scala season openings"),("en","A riveder le stelle"),
 ("it","Prima della Scala"),("it","A riveder le stelle"),
]
for lang, t in PAGES:
    p = os.path.join(out, lang + "__" + re.sub(r'[^\w]+','_',t) + ".json")
    if os.path.exists(p): continue
    try:
        r = requests.get(f"https://{lang}.wikipedia.org/w/api.php", headers=UA, timeout=60, params={
            "action":"query","prop":"revisions","rvprop":"ids|timestamp|content","rvslots":"main","titles":t,"format":"json","formatversion":2,"redirects":1})
        r.raise_for_status(); open(p,"w",encoding="utf8").write(r.text); print(lang,t,len(r.text), flush=True)
    except Exception as e:
        print("ERR",lang,t,e, flush=True)
    time.sleep(2.5)
