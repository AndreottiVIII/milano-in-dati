"""Punteggi INVALSI di istituto delle superiori statali di Milano (pagina pubblica "Indicatori" SNV, riquadro 2.2.a.1).
Le superiori hanno un'etichetta e una tabella diverse dai comprensivi, che invalsi_rav_raccolta.py non leggeva.
Uso: python -I -X utf8 invalsi_rav_superiori.py <cartella scuole>
Solo gli istituti con pagina arrivata e nessuna riga letta. User-Agent dichiarato, 5 secondi tra le richieste, una passata,
si ferma su 403, 429, login o anti-bot. Salva solo le righe per tipo di scuola nell'istituto: mai plesso, indirizzo o sezione.
"""
import csv, glob, http.cookiejar, json, os, re, sys, time, urllib.error, urllib.request

BASE = sys.argv[1]
IN = os.path.join(BASE, "raw", "invalsi_rav")
OUT = os.path.join(BASE, "raw", "invalsi_rav_sup")
os.makedirs(OUT, exist_ok=True)
URL = "https://snv.pubblica.istruzione.it/SistemaNazionaleValutazione"
UA = "milano-in-dati/1.0"
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
        if not grado_tab.startswith("Scuola secondaria di II"):
            continue
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
            if " - classi " in x and not x.startswith(("Plesso", "Scuola secondaria")):
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


codici = []
for f in sorted(glob.glob(os.path.join(IN, "*.json"))):
    d = json.load(open(f, encoding="utf8"))
    if d.get("http") == 200 and not d.get("righe"):
        codici.append(d["istituto"])
# educandato e convitto: nell'anagrafe il liceo ha un suo codice, ma i punteggi stanno sotto l'istituto che lo contiene
# (Setti Carraro: MIPC110009 sotto MIVE01000P; Longone: MIPS67000C sotto MIVC01000Q)
codici += ["MIVE01000P", "MIVC01000Q"]
print("istituti", len(codici), flush=True)
ultimo = 0.0
for cod in codici:
    p = os.path.join(OUT, cod + ".json")
    if os.path.exists(p):
        continue
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    op.addheaders = [("User-Agent", UA)]
    try:
        b = b""
        for u in (f"{URL}/scuolaInChiaro.do?dispatch=indicatori&scuolainserita={cod}", f"{URL}/mvc/descrittoriNonQs/loadDsc/2.2.a/2.2.a.1/"):
            time.sleep(max(0, 5 - (time.time() - ultimo)))
            ultimo = time.time()
            with op.open(u, timeout=120) as r:
                b = r.read()
                fin = r.geturl()
            low = b[:200000].lower()
            if "login" in fin.lower() or "iam.pubblica" in fin or b"captcha" in low or b"access denied" in low:
                print("STOP", cod, fin[:80], flush=True)
                sys.exit(1)
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            print("STOP", e.code, flush=True)
            sys.exit(1)
        print(cod, "errore", e.code, flush=True)
        continue
    except Exception as e:
        print(cod, "errore", repr(e)[:80], flush=True)
        continue
    anni, righe = parse(b)
    json.dump(dict(istituto=cod, data_raccolta=time.strftime("%Y-%m-%d"), anni=anni, righe=righe), open(p, "w", encoding="utf8"), ensure_ascii=False)
    print(cod, anni, len(righe), flush=True)
righe = []
for f in sorted(glob.glob(os.path.join(OUT, "*.json"))):
    d = json.load(open(f, encoding="utf8"))
    for r in d["righe"]:
        righe.append(dict(istituto=d["istituto"], anni=";".join(d["anni"]), **r))
camp = ["istituto", "anni", "grado", "grado_tabella", "materia", "punteggio", "partecipazione", "diff_escs", "copertura_background", "lombardia", "nord_ovest", "italia"]
with open(os.path.join(BASE, "pulito", "invalsi_superiori.csv"), "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, camp, delimiter=";", extrasaction="ignore")
    w.writeheader()
    w.writerows(righe)
print("FINE righe", len(righe), "istituti con righe", len({r["istituto"] for r in righe}), flush=True)
