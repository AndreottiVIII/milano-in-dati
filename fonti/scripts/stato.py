"""Stato delle fonti di Milano in dati: "il link risponde?" e "a quando risale il dato?".

Sono due domande diverse. Un sito fermo può avere dati validi; un sito che risponde può averli vecchi.

Il programma si lancia A MANO, una volta ogni tanto. Non resta in esecuzione e non si pianifica.

Cosa fa:
  1. legge tutti i link dei file docs/fonti/data/fonti.json (senza modificarlo);
  2. per ogni sito legge prima il robots.txt; se vieta ai programmi, il link non viene controllato;
  3. fa UNA richiesta per link (GET, senza leggere né salvare la pagina), al massimo una ogni 2 secondi per sito,
     con il nome onesto "milano-in-dati/1.0", senza imitare un browser e senza aggirare i blocchi;
  4. per il catalogo del Comune (dati.comune.milano.it) usa l'API CKAN: risolve il codice breve (es. ds634)
     nel nome completo del dataset e legge metadata_modified (la data della scheda nel catalogo).

Esiti per ogni link:
  risponde         il server ha risposto (200 o reindirizzamento)
  non_risponde     nessuna risposta, errore del server, oppure l'indirizzo non esiste più (404)
  rifiuta          il server rifiuta i programmi (403, 401, 406, 429): NON vuol dire che il sito sia morto
  non_controllato  il robots.txt vieta il controllo, o non è leggibile

Scrive solo docs/fonti/data/stato.json (pagina.py non lo tocca, quindi non si perde quando pagina.py gira).
Le date "dato aggiornato a" scritte a mano stanno in periodi.json, accanto a questo file.

Uso (Python 3.12):
  python -I -X utf8 stato.py --radice <cartella milano-in-dati> [--limite N] [--solo-sito dominio] [--solo-periodi] [--prova]
    --limite N       controlla solo i primi N link (per provare)
    --solo-sito d    controlla solo i link di quel dominio
    --solo-periodi   non fa richieste: aggiorna in stato.json solo la parte "periodi" da periodi.json
    --prova          non scrive stato.json, stampa soltanto
"""
import argparse
import datetime as dt
import http.client
import json
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from pathlib import Path

NOME = "milano-in-dati/1.0"
UA = NOME + " (+https://github.com/AndreottiVIII/milano-in-dati)"
PAUSA = 2.0       # secondi minimi tra due richieste allo stesso sito
TIMEOUT = 20
CKAN = "dati.comune.milano.it"
RIFIUTA = {401, 403, 406, 429}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


APRI = urllib.request.build_opener(NoRedirect)
ULTIMA = {}  # sito -> istante dell'ultima richiesta
N_RICHIESTE = 0


def attendi(sito):
    t = ULTIMA.get(sito)
    if t is not None:
        d = PAUSA - (time.monotonic() - t)
        if d > 0:
            time.sleep(d)


def chiedi(url, leggi=False, max_byte=3_000_000):
    """Una richiesta GET. Ritorna (codice, intestazioni, corpo|None, errore|None). Non segue i reindirizzamenti."""
    global N_RICHIESTE
    sito = urllib.parse.urlsplit(url).netloc.lower()
    attendi(sito)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    ULTIMA[sito] = time.monotonic()
    N_RICHIESTE += 1
    try:
        with APRI.open(req, timeout=TIMEOUT) as r:
            corpo = r.read(max_byte) if leggi else None
            return r.status, dict(r.headers), corpo, None
    except urllib.error.HTTPError as e:
        try:
            e.close()
        except Exception:
            pass
        return e.code, dict(e.headers or {}), None, None
    except urllib.error.URLError as e:
        mot = e.reason
        if isinstance(mot, ssl.SSLError) or "CERTIFICATE" in str(mot).upper():
            return None, {}, None, "certificato non valido"
        if isinstance(mot, socket.timeout) or "timed out" in str(mot):
            return None, {}, None, "nessuna risposta entro %d secondi" % TIMEOUT
        if isinstance(mot, socket.gaierror):
            return None, {}, None, "indirizzo del sito non trovato"
        return None, {}, None, "connessione non riuscita"
    except (socket.timeout, TimeoutError):
        return None, {}, None, "nessuna risposta entro %d secondi" % TIMEOUT
    except (http.client.HTTPException, ConnectionError, OSError, ValueError) as e:
        return None, {}, None, "connessione non riuscita"
    finally:
        ULTIMA[sito] = time.monotonic()


# ------------------------------------------------------------------ robots.txt
def leggi_robots(sito):
    """Ritorna ('ok', parser) | ('rifiuta', dettaglio) | ('non_controllato', dettaglio) | ('non_risponde', dettaglio)."""
    url = "https://" + sito + "/robots.txt"
    for _ in range(3):
        cod, h, corpo, err = chiedi(url, leggi=True, max_byte=500_000)
        if err:
            return "non_risponde", err
        loc = h.get("Location") or h.get("location")
        if cod in (301, 302, 303, 307, 308) and loc:
            loc = urllib.parse.urljoin(url, loc)
            if urllib.parse.urlsplit(loc).scheme == "https":
                url = loc  # la richiesta successiva rispetta la pausa del suo sito
                continue
        break
    if cod == 200:
        testo = (corpo or b"").decode("utf-8", "replace")
        if re.search(r"<\s*(html|!doctype|head|body)", testo[:600], re.I):
            return "non_controllato", "il robots.txt del sito non contiene regole leggibili (restituisce una pagina web)"
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(testo.splitlines())
        return "ok", rp
    if cod is not None and 400 <= cod < 500:
        # robots.txt assente o non accessibile (anche 401/403): secondo lo standard (RFC 9309) non ci sono divieti.
        # Se poi il sito rifiuta il link stesso, l'esito sarà "rifiuta": nessun tentativo di aggirare il blocco.
        return "ok", None
    if cod is not None and cod >= 500:
        return "non_controllato", "robots.txt non raggiungibile (errore %d del server)" % cod
    return "non_controllato", "robots.txt non leggibile (risposta %s)" % cod


# ------------------------------------------------------------------ esito di un link
def esito_da_codice(cod, h):
    if 200 <= cod < 400:
        d = "risponde (%d)" % cod
        if cod >= 300:
            d = "risponde con un reindirizzamento (%d)" % cod
        return "risponde", d
    if cod in RIFIUTA:
        return "rifiuta", "il sito rifiuta i programmi (%d): non vuol dire che sia fuori uso" % cod
    if cod in (404, 410):
        return "non_risponde", "il sito risponde, ma l'indirizzo non esiste più (%d)" % cod
    if cod >= 500:
        return "non_risponde", "errore del server (%d)" % cod
    return "non_risponde", "risposta inattesa (%d)" % cod


def giorno(s):
    return (s or "")[:10] or None


def ckan_api(azione, **par):
    url = "https://%s/api/3/action/%s?%s" % (CKAN, azione, urllib.parse.urlencode(par))
    cod, h, corpo, err = chiedi(url, leggi=True)
    if err or cod != 200 or not corpo:
        return cod, None, err
    try:
        j = json.loads(corpo.decode("utf-8", "replace"))
    except ValueError:
        return cod, None, "risposta non leggibile"
    return cod, (j.get("result") if j.get("success") else None), None


def sintesi_dataset(p):
    ris = [giorno(r.get("last_modified")) for r in p.get("resources", []) if r.get("last_modified")]
    return {
        "nome": p.get("name"), "url": "https://%s/dataset/%s" % (CKAN, p.get("name")),
        "titolo": p.get("title"), "scheda_aggiornata": giorno(p.get("metadata_modified")),
        "file_aggiornato": max(ris) if ris else None,
    }


def codice_breve(s):
    m = re.match(r"^(ds\d+)(?:[_\-].*)?$", s, re.I)
    return m.group(1).lower() if m else None


def cerca_codici(codici):
    """Risolve i codici brevi (ds634) nei nomi completi, con ricerche a gruppi (poche richieste)."""
    out, errori = {}, None
    codici = sorted(set(codici), key=lambda c: int(c[2:]))
    for i in range(0, len(codici), 12):
        gruppo = codici[i:i + 12]
        q = " OR ".join("name:%s*" % c for c in gruppo)
        cod, ris, err = ckan_api("package_search", q=q, rows=100)
        if ris is None:
            errori = err or "catalogo non raggiungibile (%s)" % cod
            continue
        for p in ris.get("results", []):
            c = codice_breve(p.get("name", ""))
            if c in gruppo:
                out.setdefault(c, []).append(sintesi_dataset(p))
    return out, errori


# ------------------------------------------------------------------ programma
def leggi_link(radice):
    d = json.loads((radice / "docs" / "fonti" / "data" / "fonti.json").read_text(encoding="utf-8"))
    link, cod_comune = {}, set()
    for r in d["fonti"]:
        for l in r["link"]:
            l = l.split("#")[0]
            link.setdefault(l, set()).add(r["pagina"])
        if r["editore"] == "Comune di Milano":
            for x in r["dataset"]:
                if re.fullmatch(r"ds\d+", x, re.I):
                    cod_comune.add(x.lower())
    return list(link), cod_comune


def controlla(radice, limite=None, solo=None):
    link, cod_comune = leggi_link(radice)
    if solo:
        link = [l for l in link if solo in urllib.parse.urlsplit(l).netloc]
    if limite:
        link = link[:limite]
    siti = {}
    for l in link:
        siti.setdefault(urllib.parse.urlsplit(l).netloc.lower(), []).append(l)

    # --- robots.txt, un sito per volta
    robots = {}
    for s in siti:
        robots[s] = leggi_robots(s)
        print("robots", s, robots[s][0], flush=True)

    risultati = {}
    ora = lambda: dt.datetime.now().replace(microsecond=0).isoformat()

    # --- catalogo del Comune: codici brevi -> nomi completi (a gruppi)
    comune_ds, err_ckan = {}, None
    if CKAN in siti and robots[CKAN][0] == "ok":
        rp = robots[CKAN][1]
        if rp is None or rp.can_fetch(NOME, "https://%s/api/3/action/package_search" % CKAN):
            cods = set(cod_comune)
            for l in siti[CKAN]:
                c = codice_breve(urllib.parse.urlsplit(l).path.rstrip("/").split("/")[-1])
                if c:
                    cods.add(c)
            comune_ds, err_ckan = cerca_codici(cods)
            print("catalogo del Comune: %d codici risolti su %d" % (len(comune_ds), len(cods)), flush=True)
        else:
            err_ckan = "il robots.txt vieta l'API del catalogo"

    # --- un giro tra i siti per rispettare la pausa senza perdere tempo
    coda = {s: list(ls) for s, ls in siti.items()}
    while any(coda.values()):
        s = min((x for x in coda if coda[x]), key=lambda x: ULTIMA.get(x, 0))
        url = coda[s].pop(0)
        r = {"sito": s, "controllato": ora()}
        stato, rob = robots[s]
        if stato != "ok":
            r["esito"], r["dettaglio"] = stato, rob
        elif rob is not None and not rob.can_fetch(NOME, url):
            r["esito"], r["dettaglio"] = "non_controllato", "il robots.txt del sito vieta di controllare questo indirizzo ai programmi"
        elif s == CKAN and "/dataset/" in url:
            nome = urllib.parse.urlsplit(url).path.rstrip("/").split("/")[-1]
            if err_ckan:
                r["esito"], r["dettaglio"] = "non_controllato", err_ckan
            else:
                cod, res, err = ckan_api("package_show", id=nome)
                if res is not None:
                    r["esito"], r["dettaglio"] = "risponde", "risponde (catalogo del Comune)"
                    r["dataset"] = sintesi_dataset(res)
                elif cod == 404 and codice_breve(nome) and comune_ds.get(codice_breve(nome)):
                    trovati = comune_ds[codice_breve(nome)]
                    if len(trovati) == 1:
                        r["esito"] = "risponde"
                        r["dettaglio"] = "il codice breve non esiste come indirizzo: corretto con il nome completo del dataset"
                        r["dataset"] = trovati[0]
                        r["link_corretto"] = trovati[0]["url"]
                    else:
                        r["esito"], r["dettaglio"] = "non_risponde", "il codice corrisponde a più dataset: %d" % len(trovati)
                elif cod == 404:
                    r["esito"], r["dettaglio"] = "non_risponde", "dataset non trovato nel catalogo (404)"
                elif cod in RIFIUTA:
                    r["esito"], r["dettaglio"] = esito_da_codice(cod, {})
                    r["codice"] = cod
                else:
                    r["esito"], r["dettaglio"] = ("non_risponde", err or "errore del catalogo (%s)" % cod)
        else:
            cod, h, _c, err = chiedi(url)
            if err:
                r["esito"], r["dettaglio"] = "non_risponde", err
            else:
                r["esito"], r["dettaglio"] = esito_da_codice(cod, h)
                r["codice"] = cod
                loc = h.get("Location") or h.get("location")
                if loc and 300 <= cod < 400:
                    r["reindirizza_a"] = urllib.parse.urljoin(url, loc)
        risultati[url] = r
        print("%-16s %s" % (r["esito"], url[:110]), flush=True)
    return risultati, comune_ds, err_ckan, len(link)


def periodi(base):
    p = base / "periodi.json"
    if not p.exists():
        return []
    j = json.loads(p.read_text(encoding="utf-8"))
    return j.get("righe", j) if isinstance(j, dict) else j


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--radice", required=True)
    ap.add_argument("--limite", type=int)
    ap.add_argument("--solo-sito")
    ap.add_argument("--solo-periodi", action="store_true")
    ap.add_argument("--prova", action="store_true")
    a = ap.parse_args()
    radice = Path(a.radice)
    base = Path(__file__).resolve().parent
    out = radice / "docs" / "fonti" / "data" / "stato.json"

    if a.solo_periodi:
        j = json.loads(out.read_text(encoding="utf-8"))
        j["periodi"] = periodi(base)
        out.write_text(json.dumps(j, ensure_ascii=False, indent=1), encoding="utf-8")
        print("periodi aggiornati:", len(j["periodi"]))
        return

    inizio = time.monotonic()
    try:
        ris, comune_ds, err_ckan, n = controlla(radice, a.limite, a.solo_sito)
    except KeyboardInterrupt:
        print("interrotto: non scrivo nulla")
        sys.exit(1)
    cont = {}
    for r in ris.values():
        cont[r["esito"]] = cont.get(r["esito"], 0) + 1
    esito = {
        "controllato": dt.date.today().isoformat(),
        "agente": UA,
        "regola": "Se una fonte risponde e quanto è aggiornato il dato sono due cose diverse.",
        "parziale": bool(a.limite or a.solo_sito),
        "n_richieste": N_RICHIESTE,
        "durata_secondi": round(time.monotonic() - inizio),
        "conteggi": {"link": len(ris), "risponde": cont.get("risponde", 0), "non_risponde": cont.get("non_risponde", 0),
                     "rifiuta": cont.get("rifiuta", 0), "non_controllato": cont.get("non_controllato", 0)},
        "errore_catalogo": err_ckan,
        "link": ris,
        "dataset_comune": comune_ds,
        "periodi": periodi(base),
    }
    print(json.dumps(esito["conteggi"], ensure_ascii=False), "richieste:", N_RICHIESTE)
    if a.prova:
        return
    if esito["parziale"] and out.exists():
        print("controllo parziale: non sovrascrivo stato.json (usa --prova per vedere, o lancia senza limiti)")
        return
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(json.dumps(esito, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(out)
    print("scritto", out)


if __name__ == "__main__":
    main()
