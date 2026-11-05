"""Scarica (con ripetizioni lente se il server risponde 500) alcune pagine pubbliche del repository ISPRA e ne estrae i link di download.
Uso: python -I -X utf8 sonda_pagine.py <cartella di uscita assoluta> <sottopercorso> [...]
"""
import sys, os, re, time, urllib.request, urllib.error
B = "https://groupware.sinanet.isprambiente.it/uso-copertura-e-consumo-di-suolo/library/consumo-di-suolo/"
out = sys.argv[1]
for p in sys.argv[2:]:
    for tent in range(6):
        try:
            req = urllib.request.Request(B + p, headers={"User-Agent": "milano-in-dati/1.0"})
            t = urllib.request.urlopen(req, timeout=60).read().decode("utf8", "replace")
            open(os.path.join(out, "pag_" + p.replace("/", "__") + ".html"), "w", encoding="utf8").write(t)
            dl = sorted(set(re.findall(r'href="([^"]*/download/en/\d+/[^"]*)"', t)))
            print("##", p, len(t), flush=True)
            for h in dl:
                print("  ", h.split("consumo-di-suolo/")[-1], flush=True)
            kids = re.findall(r'href="(https://groupware[^"]*consumo-di-suolo/' + re.escape(p) + r'/[^"/?]+)"', t)
            for k in sorted(set(kids)):
                print("  >", k.split("consumo-di-suolo/")[-1], flush=True)
            break
        except urllib.error.HTTPError as e:
            print("..", p, e.code, "tentativo", tent, flush=True)
            time.sleep(15 * (tent + 1))
    time.sleep(4)
