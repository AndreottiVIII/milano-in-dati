"""Raccolta dei punteggi INVALSI di istituto (riquadro 2.2.a.1 della pagina pubblica 'Indicatori' SNV) per gli istituti statali di Milano città.

Uso: python -I -X utf8 invalsi_rav_raccolta.py <cartella scuole>
- Elenco: anagrafe MIM statali 2025/26, comune F205, codici istituto di riferimento.
- User-Agent dichiarato, 5 secondi tra ogni richiesta, una sola passata, salta gli istituti già salvati.
- Si ferma subito su 403, 2 volte 429, redirect a login, parole captcha/robot nella risposta, 5 errori di fila.
- Salva SOLO le righe di istituto (mai plesso o sezione) in raw/invalsi_rav/<codice>.json. Le pagine HTML non vengono salvate.
"""
import csv
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

UA = "milano-in-dati/1.0"
BASE = sys.argv[1]
OUT = os.path.join(BASE, "raw", "invalsi_rav")
os.makedirs(OUT, exist_ok=True)
URL = "https://snv.pubblica.istruzione.it/SistemaNazionaleValutazione"
LOG = os.path.join(OUT, "_log.txt")
NUM = re.compile(r"-?\d+(?:[.,]\d+)?")


def log(s):
    with open(LOG, "a", encoding="utf8") as f:
        f.write(time.strftime("%H:%M:%S ") + s + "\n")


class Stop(Exception):
    pass


def num(s):
    return float(s.replace(",", ".")) if NUM.fullmatch(s or "") else None


def parse(b):
    t = b.decode("utf8", "replace")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    c = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x)).strip() for x in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", t, flags=re.S)]
    anni = sorted(set(re.findall(r"a\.s\. (\d{4}/\d{4})", t)))
    out = []
    i = 0
    while i < len(c) - 2:
        if re.match(r"Scuola .* - classi \w+$", c[i]) and c[i + 2] == "Istituto/Plesso/Classe":
            grado, mat = c[i], c[i + 1]
            j = i + 3
            cols = []
            while j < len(c) and c[j] != "Riferimenti":
                cols.append(c[j])
                j += 1
            j += 1
            rif = []
            while j < len(c) and not NUM.fullmatch(c[j]) and not c[j].startswith("Punteggio"):
                j += 1
            while j < len(c) and c[j].startswith("Punteggio"):
                j += 1
            rif = [num(x) for x in c[j:j + 3]]
            j += 3
            # riga di istituto: etichetta uguale al grado, subito dopo i riferimenti
            if j < len(c) and c[j] == grado:
                v = c[j + 1:j + 1 + len(cols)]
                r = dict(grado=grado, materia=mat, rif_prima=rif)
                for name, val in zip(cols, v):
                    n = name.lower()
                    if n.startswith("punteggio medio"):
                        r["punteggio"] = num(val)
                    elif n.startswith("percentuale di partecipazione"):
                        r["partecipazione"] = num(val)
                    elif n.startswith("diff"):
                        r["diff_escs"] = num(val)
                    elif "background" in n:
                        r["copertura_background"] = num(val)
                    else:
                        r["altro_" + name[:30]] = val
                r["lombardia"], r["nord_ovest"], r["italia"] = rif
                out.append(r)
            i = j
        else:
            i += 1
    return anni, out


def main():
    import pandas as pd

    g = pd.read_csv(os.path.join(BASE, "raw", "miur", "SCUANAGRAFESTAT20252620250901.csv"), dtype=str, keep_default_na=False)
    g = g[g.CODICECOMUNESCUOLA == "F205"]
    codici = sorted(g.CODICEISTITUTORIFERIMENTO.unique())
    log(f"avvio: {len(codici)} istituti")
    errori = 0
    n429 = 0
    ultimo = [0.0]

    def get(op, url):
        nonlocal n429
        w = 5 - (time.time() - ultimo[0])
        if w > 0:
            time.sleep(w)
        ultimo[0] = time.time()
        try:
            with op.open(url, timeout=120) as r:
                b = r.read()
                fin = r.geturl()
                st = r.status
        except urllib.error.HTTPError as e:
            if e.code == 403:
                log("403 -> stop")
                raise Stop("403")
            if e.code == 429:
                n429 += 1
                log("429")
                if n429 >= 2:
                    raise Stop("429 ripetuti")
            raise
        if "iam.pubblica" in fin or "login" in fin.lower():
            raise Stop("redirect a login: " + fin)
        low = b[:200000].lower()
        if b"captcha" in low or b"recaptcha" in low or b"are you a robot" in low or b"access denied" in low:
            raise Stop("possibile controllo anti-bot")
        return st, b

    for cod in codici:
        p = os.path.join(OUT, cod + ".json")
        if os.path.exists(p):
            continue
        cj = http.cookiejar.CookieJar()
        op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        op.addheaders = [("User-Agent", UA)]
        try:
            get(op, f"{URL}/scuolaInChiaro.do?dispatch=indicatori&scuolainserita={cod}")
            st, b = get(op, f"{URL}/mvc/descrittoriNonQs/loadDsc/2.2.a/2.2.a.1/")
            anni, righe = parse(b)
            if b"Manutenzione" in b[:5000]:
                raise urllib.error.URLError("manutenzione")
            errori = 0
            data = dict(istituto=cod, data_raccolta=time.strftime("%Y-%m-%d"), http=st, anni=anni, byte=len(b), righe=righe)
            with open(p, "w", encoding="utf8") as f:
                json.dump(data, f, ensure_ascii=False)
            log(f"{cod} ok anni={anni} righe={len(righe)}")
        except Stop as e:
            log("STOP: " + str(e))
            print("STOP", e)
            return
        except Exception as e:
            errori += 1
            log(f"{cod} errore {e!r}"[:200])
            if errori >= 5:
                log("5 errori di fila -> stop")
                return
    log("finito")


main()
