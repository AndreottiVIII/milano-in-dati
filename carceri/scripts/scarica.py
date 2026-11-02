"""Scarica da giustizia.it le pagine di statistica (serie mensile "Detenuti italiani e
stranieri presenti e capienze per istituto", "Detenuti presenti" per regione/posizione
giuridica, serie storiche), le schede degli istituti milanesi e i PDF dei minorenni.

Uso:  python -I -X utf8 scarica.py <percorso assoluto di carceri>
Rilanciabile: salta i file gia' scaricati. User-Agent dichiarato, pausa tra le richieste,
nessun trucco anti-bot (se risponde 504 riprova con pausa; se 403/429 si ferma).
"""
import csv, html, re, sys, time, urllib.request, urllib.error
from pathlib import Path
from datetime import date

BASE = "https://www.giustizia.it/giustizia"
UA = "milano-in-dati-research/1.0 (raccolta dati aperti, uso non commerciale)"
PAUSA = 1.5


def get(url, dest, binary=False):
    if dest.exists() and dest.stat().st_size > 2000:
        return False
    for tent in range(6):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r:
                data = r.read()
            if b"504 Gateway Time-out" in data[:400]:
                raise urllib.error.HTTPError(url, 504, "gw", {}, None)
            dest.write_bytes(data)
            time.sleep(PAUSA)
            return True
        except urllib.error.HTTPError as e:
            if e.code in (403, 429):
                sys.exit(f"STOP: {e.code} su {url}")
            time.sleep(5 * (tent + 1))
        except Exception:
            time.sleep(5 * (tent + 1))
    print("FALLITO", url)
    return None


def main(root):
    raw = Path(root) / "raw"
    (raw / "mensili").mkdir(parents=True, exist_ok=True)
    (raw / "serie").mkdir(exist_ok=True)
    (raw / "schede").mkdir(exist_ok=True)
    (raw / "ipm").mkdir(exist_ok=True)
    log = []

    # 1) elenco completo (all=true) del nodo "strutture penitenziarie" 0_2_7 e dei minorenni 0_6
    elenchi = {}
    for nodo in ("0_2", "0_2_7", "0_6"):
        d = raw / f"elenco_{nodo}.html"
        get(f"{BASE}/page/it/statistiche?selectedNode={nodo}&all=true", d)
        elenchi[nodo] = d.read_text(encoding="utf8", errors="replace")
    voci = {}
    for h in elenchi.values():
        for cid, t in re.findall(r'href="[^"]*contentId=(SST\d+)[^"]*"[^>]*>\s*([^<]+)', h):
            voci[cid] = re.sub(r"\s+", " ", html.unescape(t.strip()))

    # 2) pagine mensili (capienze per istituto + Detenuti presenti per regione) e serie storiche
    mesi = {"gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4, "maggio": 5, "giugno": 6, "luglio": 7,
            "agosto": 8, "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12}
    for cid, t in sorted(voci.items()):
        tl = t.lower()
        mensile = None
        if tl.startswith("detenuti italiani e stranieri presenti e capienze per istituto"):
            mensile = "istituti"
        elif tl.startswith("detenuti presenti - aggiornamento"):
            mensile = "regioni"
        serie = any(tl.startswith(p) for p in (
            "detenuti presenti per posizione giuridica", "eventi critici", "detenuti presenti italiani e stranieri",
            "detenuti presenti stranieri per area"))
        ipm = tl.startswith("istituti penali per i minorenni")
        if not (mensile or serie or ipm):
            continue
        sub = "mensili" if mensile else ("serie" if serie else "ipm")
        dest = raw / sub / f"{cid}.html"
        if get(f"{BASE}/it/mg_1_14_1.page?contentId={cid}", dest):
            print("scaricato", cid, t[:80])
        m = re.search(r"(\d{1,2}) (\w+) (20\d\d)", t)
        log.append([sub, cid, t, f"{BASE}/it/mg_1_14_1.page?contentId={cid}", date.today().isoformat()])

    # 3) schede degli istituti
    schede = {"MII158895": "San Vittore", "MII178501": "San Vittore femminile", "MII172344": "Bollate",
              "MII179237": "Opera"}
    for cod, nome in schede.items():
        dest = raw / "schede" / f"{cod}.html"
        if get(f"{BASE}/it/dettaglio_scheda.page?s={cod}", dest):
            print("scheda", nome)
        log.append(["scheda", cod, nome, f"{BASE}/it/dettaglio_scheda.page?s={cod}", date.today().isoformat()])

    # 4) PDF minorenni: link nella pagina di ogni voce IPM
    for f in sorted((raw / "ipm").glob("SST*.html")):
        h = f.read_text(encoding="utf8", errors="replace")
        for u in re.findall(r'href="([^"]+\.pdf[^"]*)"', h, re.I):
            u = html.unescape(u)
            if u.startswith("/"):
                u = "https://www.giustizia.it" + u
            dest = raw / "ipm" / (f.stem + "_" + re.sub(r"[^A-Za-z0-9._-]", "_", u.split("/")[-1].split("?")[0]))
            if get(u, dest, binary=True):
                print("pdf", dest.name)
            log.append(["ipm_pdf", f.stem, u, u, date.today().isoformat()])

    with open(raw / "download_log.csv", "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["tipo", "id", "titolo_o_url", "url", "scaricato_il"])
        w.writerows(log)
    print("fatto, voci registrate:", len(log))


if __name__ == "__main__":
    main(sys.argv[1])
