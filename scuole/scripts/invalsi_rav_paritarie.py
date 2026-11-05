"""Punteggi INVALSI delle scuole paritarie di Milano, se la pagina pubblica "Indicatori" SNV esiste (molte danno 404).
Uso: python -I -X utf8 invalsi_rav_paritarie.py <cartella scuole>
User-Agent dichiarato, 5 secondi tra le richieste, una passata; si ferma su 403, 429, login o anti-bot.
Salva solo le righe di istituto: mai plesso, indirizzo o sezione.
"""
import csv, glob, http.cookiejar, json, os, re, sys, time, urllib.error, urllib.request
import pandas as pd

BASE = sys.argv[1]
OUT = os.path.join(BASE, "raw", "invalsi_rav_par")
os.makedirs(OUT, exist_ok=True)
URL = "https://snv.pubblica.istruzione.it/SistemaNazionaleValutazione"
NUM = re.compile(r"-?\d+(?:[.,]\d+)?")
num = lambda s: float(s.replace(",", ".")) if NUM.fullmatch(s or "") else None


def parse(b):
    t = b.decode("utf8", "replace")
    t = re.sub(r"<script.*?</script>|<style.*?</style>", "", t, flags=re.S)
    c = [re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", x)).strip() for x in re.findall(r"<t[dh]\b[^>]*>(.*?)</t[dh]>", t, flags=re.S)]
    anni = sorted(set(re.findall(r"a\.s\. (\d{4}/\d{4})", t)))
    teste = [i for i, x in enumerate(c) if x.startswith("Istituto/Plesso")]
    out = []
    for n, i in enumerate(teste):
        fine = teste[n + 1] - 2 if n + 1 < len(teste) else len(c)
        grado_tab, materia = c[i - 2], c[i - 1]
        j = i + 1
        cols = []
        while j < fine and c[j] != "Riferimenti":
            cols.append(c[j])
            j += 1
        j += 1
        while j < fine and c[j].startswith("Punteggio"):
            j += 1
        rif = [num(x) for x in c[j:j + 3]]
        j += 3
        while j < fine:
            x = c[j]
            if " - classi " in x and not x.startswith("Plesso"):
                v = c[j + 1:j + 1 + len(cols)]
                r = dict(grado=x, grado_tabella=grado_tab, materia=materia, lombardia=rif[0], nord_ovest=rif[1], italia=rif[2])
                for name, val in zip(cols, v):
                    k = name.lower()
                    if k.startswith("punteggio medio"):
                        r["punteggio"] = num(val)
                    elif k.startswith("percentuale di partecipazione"):
                        r["partecipazione"] = num(val)
                    elif k.startswith("diff"):
                        r["diff_escs"] = num(val)
                    elif "background" in k:
                        r["copertura_background"] = num(val)
                out.append(r)
            j += 1
    return anni, out


f = sorted(glob.glob(os.path.join(BASE, "raw", "miur", "SCUANAGRAFEPAR*.csv")))[-1]
g = pd.read_csv(f, dtype=str, keep_default_na=False, encoding="latin-1", sep=None, engine="python")
m = g[(g.CODICECOMUNESCUOLA == "F205") & ~g.DESCRIZIONETIPOLOGIAGRADOISTRUZIONESCUOLA.str.contains("INFANZIA")].drop_duplicates("CODICESCUOLA")
print("paritarie", len(m), flush=True)
ultimo = 0.0
for cod, den, tip in zip(m.CODICESCUOLA, m.DENOMINAZIONESCUOLA, m.DESCRIZIONETIPOLOGIAGRADOISTRUZIONESCUOLA):
    p = os.path.join(OUT, cod + ".json")
    if os.path.exists(p):
        continue
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op.addheaders = [("User-Agent", "milano-in-dati/1.0")]
    ris = dict(istituto=cod, nome=den, tipo=tip, data_raccolta=time.strftime("%Y-%m-%d"), anni=[], righe=[], http=200)
    try:
        for u in (f"{URL}/scuolaInChiaro.do?dispatch=indicatori&scuolainserita={cod}", f"{URL}/mvc/descrittoriNonQs/loadDsc/2.2.a/2.2.a.1/"):
            time.sleep(max(0, 5 - (time.time() - ultimo)))
            ultimo = time.time()
            with op.open(u, timeout=120) as r:
                b = r.read()
                fin = r.geturl()
            low = b[:200000].lower()
            if "login" in fin.lower() or "iam.pubblica" in fin or b"captcha" in low or b"access denied" in low:
                print("STOP", cod, flush=True)
                sys.exit(1)
        ris["anni"], ris["righe"] = parse(b)
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            print("STOP", e.code, flush=True)
            sys.exit(1)
        ris["http"] = e.code
    except Exception as e:
        print(cod, "errore", repr(e)[:70], flush=True)
        continue
    json.dump(ris, open(p, "w", encoding="utf8"), ensure_ascii=False)
    print(cod, ris["http"], ris["anni"], len(ris["righe"]), flush=True)
righe = []
for f in sorted(glob.glob(os.path.join(OUT, "*.json"))):
    d = json.load(open(f, encoding="utf8"))
    for r in d["righe"]:
        righe.append(dict(istituto=d["istituto"], nome=d["nome"], tipo=d["tipo"], anni=";".join(d["anni"]), **r))
camp = ["istituto", "nome", "tipo", "anni", "grado", "grado_tabella", "materia", "punteggio", "partecipazione", "diff_escs", "copertura_background", "lombardia", "nord_ovest", "italia"]
with open(os.path.join(BASE, "pulito", "invalsi_paritarie.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, camp, delimiter=";", extrasaction="ignore")
    w.writeheader()
    w.writerows(righe)
print("FINE righe", len(righe), "scuole con righe", len({r["istituto"] for r in righe}), flush=True)
