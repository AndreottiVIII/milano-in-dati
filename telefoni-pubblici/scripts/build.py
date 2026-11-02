"""Costruisce i dati della pagina docs/telefoni-pubblici/ (telefoni pubblici di Milano).
Uso: python -I -X utf8 build.py <raw assoluta> <docs/telefoni-pubblici/data assoluta> <out assoluta>
Legge in raw: tim_cabine.json, osm_telefoni.json, POSAS_2026_it_Comuni.zip, scarico.json.
Scrive: <data>/pagina.json (solo conteggi aggregati), <data>/osm_telefoni_mappa.json (punti OpenStreetMap, ODbL),
        <data>/LICENZE.txt, <out>/controlli.txt.
REGOLA: l'elenco TIM non si puo' ripubblicare (note legali TIM). In <data> vanno solo numeri aggregati: nessuna riga,
nessun indirizzo. Il programma controlla che nessuna via TIM compaia nei file scritti."""
import sys, os, re, csv, json, zipfile, collections

RAW, DATA, OUT = sys.argv[1:4]
os.makedirs(DATA, exist_ok=True); os.makedirs(OUT, exist_ok=True)
ctl = []
def C(s=""): ctl.append(s); print(s)

scarico = json.load(open(os.path.join(RAW, "scarico.json"), encoding="utf8"))
tim = json.loads(open(os.path.join(RAW, "tim_cabine.json"), encoding="utf-8-sig").read())
osm = json.load(open(os.path.join(RAW, "osm_telefoni.json"), encoding="utf8"))
m = re.search(r"cabine(\d{2})(\d{2})(\d{4})\.json", scarico["tim"]["url"])
data_tim = "%s-%s-%s" % (m.group(3), m.group(2), m.group(1))   # aaaa-mm-gg dal nome del file TIM
CAMPI = ["REGIONE", "DESCRIZIONE_PROVINCIA", "DESCRIZIONE_COMUNE", "DESC_VIA", "CODE_CAP_GIS", "MEZZO_DI_PAGAMENTO", "ACCESSO", "STATO"]
assert all(set(CAMPI) <= set(r) for r in tim), "campi TIM cambiati"

# ---------- ISTAT: popolazione residente al 1/1/2026 (stima). La riga con Eta = 999 e' il totale del comune.
z = zipfile.ZipFile(os.path.join(RAW, "POSAS_2026_it_Comuni.zip"))
txt = z.read(z.namelist()[0]).decode("utf-8-sig")
titolo = txt.splitlines()[0].strip('"')
pop, nome = {}, {}
somma_eta = collections.Counter()
for r in csv.reader(txt.splitlines()[2:], delimiter=";"):
    if not r or not r[0].isdigit(): continue          # salta la riga di note finale
    if r[2] == "999": pop[r[0]] = int(r[5]); nome[r[0]] = r[1]
    else: somma_eta[r[0]] += int(r[5])
assert all(pop[c] == somma_eta[c] for c in pop), "totale ISTAT diverso dalla somma per eta"
top = sorted(pop, key=lambda c: -pop[c])[:12]
C("ISTAT: %s" % titolo)
C("Comuni nel file: %d; controllo: riga totale (Eta 999) = somma delle eta per tutti i comuni: OK" % len(pop))
C("I 12 comuni piu popolosi: " + ", ".join("%s %d" % (nome[c], pop[c]) for c in top))

# ---------- TIM: conteggi
def U(s): return re.sub(r"\s+", " ", (s or "").strip().upper())
def chiave_via(r): return re.sub(r"[^A-Z0-9 ]", "", U(r["DESC_VIA"])) + "|" + U(r["CODE_CAP_GIS"])
n_it = len(tim)
stato_it = collections.Counter(r["STATO"] for r in tim)
acc_it = collections.Counter(r["ACCESSO"] for r in tim)
pag_it = collections.Counter(r["MEZZO_DI_PAGAMENTO"] for r in tim)
C("\nTIM, file dati al %s (url: %s)" % (data_tim, scarico["tim"]["url"]))
C("Righe in Italia: %d; STATO %s; ACCESSO %s; MEZZO_DI_PAGAMENTO %s" % (n_it, dict(stato_it), dict(acc_it), dict(pag_it)))
n_com = len({(U(r["DESCRIZIONE_PROVINCIA"]), U(r["DESCRIZIONE_COMUNE"])) for r in tim})
C("Regioni: %d; province: %d; comuni (provincia+nome): %d" % (len({r["REGIONE"] for r in tim}), len({r["DESCRIZIONE_PROVINCIA"] for r in tim}), n_com))
C("Campi vuoti: " + str({k: sum(1 for r in tim if not (r[k] or "").strip()) for k in CAMPI}))

citta = []
for c in top:
    nm = U(nome[c])
    righe = [r for r in tim if U(r["DESCRIZIONE_COMUNE"]) == nm]
    prov = {U(r["DESCRIZIONE_PROVINCIA"]) for r in righe}
    chiavi = collections.Counter(chiave_via(r) for r in righe)
    ripet = len(righe) - len(chiavi)
    st = collections.Counter(r["STATO"] for r in righe)
    ac = collections.Counter(r["ACCESSO"] for r in righe)
    citta.append(dict(nome=nome[c], codice_istat=c, abitanti=pop[c], telefoni=len(righe), attivi=st["ATTIVO"], in_rimozione=st["IN RIMOZIONE"],
                      per_10000=round(len(righe) / pop[c] * 10000, 2), indirizzi_distinti=len(chiavi), righe_con_indirizzo_ripetuto=ripet,
                      accesso=dict(ac)))
    C("  %-9s righe %4d (attivi %d, in rimozione %d) abitanti %9d -> %5.2f ogni 10.000; indirizzi distinti %d, righe che ripetono un indirizzo %d (%.1f%%); province nel file: %s" %
      (nome[c], len(righe), st["ATTIVO"], st["IN RIMOZIONE"], pop[c], len(righe) / pop[c] * 10000, len(chiavi), ripet, 100 * ripet / max(1, len(righe)), sorted(prov)))
    assert len(prov) == 1, "nome di comune presente in piu province: " + nome[c]
mil = next(x for x in citta if x["codice_istat"] == "015146")
acc_m = mil["accesso"]

# ---------- OSM
els = osm["elements"]
assert all(e["tags"].get("amenity") == "telephone" for e in els)
punti = []
for e in els:
    t = e["tags"]
    lat, lon = e.get("lat"), e.get("lon")
    if lat is None: lat, lon = e["center"]["lat"], e["center"]["lon"]
    punti.append([e["type"][0] + str(e["id"]), round(lat, 6), round(lon, 6), t.get("operator", ""), t.get("check_date", ""), t.get("covered", "")])
con_cd = [p for p in punti if p[4]]
def anno(p): return int(p[4][:4]) if re.match(r"\d{4}", p[4]) else None
rec = sum(1 for p in con_cd if anno(p) and anno(p) >= 2025)
ops = collections.Counter(("TIM o Telecom Italia" if re.match(r"(?i)(tim|telecom)", p[3]) else ("altro operatore" if p[3] else "operatore non indicato")) for p in punti)
C("\nOSM: %d elementi (%s), dati del %s; con check_date %d (2025-2026: %d); operatori %s" % (len(punti), dict(collections.Counter(e["type"] for e in els)), osm["osm3s"]["timestamp_osm_base"], len(con_cd), rec, dict(ops)))
C("Punti OSM fuori da un rettangolo largo attorno a Milano: %d" % sum(1 for p in punti if not (45.35 < p[1] < 45.60 and 8.95 < p[2] < 9.35)))

# ---------- risultati
pct = lambda a, b: round(100 * a / b, 1)
out = dict(
    data_elenco_tim=data_tim, data_scarico=scarico["tim"]["data_scarico"], osm_timestamp=osm["osm3s"]["timestamp_osm_base"],
    istat_titolo=titolo,
    italia=dict(telefoni=n_it, attivi=stato_it["ATTIVO"], in_rimozione=stato_it["IN RIMOZIONE"], accesso=dict(acc_it), comuni_con_telefoni=n_com),
    milano=dict(mil, quota_stradali=pct(acc_m.get("Impianto Stradale", 0), mil["telefoni"]),
                quota_italia_stradali=pct(acc_it["Impianto Stradale"], n_it),
                quota_italia_commerciali=pct(acc_it["Esercizio Commerciale"], n_it),
                quota_su_italia=pct(mil["telefoni"], n_it)),
    citta=sorted(citta, key=lambda x: -x["telefoni"]),
    osm=dict(n=len(punti), con_data_verifica=len(con_cd), verificati_2025_2026=rec, operatori=dict(ops)),
)
json.dump(out, open(os.path.join(DATA, "pagina.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
json.dump(dict(colonne=["id", "lat", "lon", "operatore", "verificato", "coperto"], punti=punti, osm_timestamp=osm["osm3s"]["timestamp_osm_base"]),
          open(os.path.join(DATA, "osm_telefoni_mappa.json"), "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
open(os.path.join(DATA, "LICENZE.txt"), "w", encoding="utf8").write(
"""Milano in dati - Telefoni pubblici: licenze dei file in questa cartella
Dati scaricati il %s.

- osm_telefoni_mappa.json: punti con amenity=telephone dentro il Comune di Milano, da OpenStreetMap (dati del %s).
  (c) OpenStreetMap contributors, Open Database Licence (ODbL) 1.0. Chi riusa o ripubblica questo file deve citare la fonte
  e distribuire i dati derivati con la stessa licenza (share-alike). https://www.openstreetmap.org/copyright
- pagina.json: solo conteggi. I numeri sui telefoni TIM sono calcolati dall'elenco pubblicato da TIM (dati al %s).
  L'elenco TIM non e' ripubblicato: le note legali di TIM (https://www.tim.it/note-legali) non lo permettono senza consenso scritto.
  Qui ci sono solo totali, senza indirizzi e senza righe dell'elenco.
- Abitanti: ISTAT, popolazione residente al 1 gennaio 2026 (stima), https://demo.istat.it/ .
- I programmi e le note sono nel repository del progetto.
""" % (scarico["tim"]["data_scarico"], osm["osm3s"]["timestamp_osm_base"][:10], data_tim))

# ---------- controllo: nessuna via TIM nei file scritti
scritti = "".join(open(os.path.join(DATA, f), encoding="utf8").read().upper() for f in os.listdir(DATA))
vie = {re.sub(r"\s+", " ", r["DESC_VIA"].strip().upper()) for r in tim if len(r["DESC_VIA"].strip()) > 12}
trovate = [v for v in vie if v in scritti]
C("\nControllo licenza: indirizzi TIM (piu lunghi di 12 caratteri, %d distinti) trovati nei file in docs: %d" % (len(vie), len(trovate)))
assert not trovate, "indirizzi TIM nei file pubblici!"
C("\nConfronto con i conteggi preliminari di chi ha commissionato la pagina:")
for nome_, v, att in [("Italia", n_it, 10002), ("Italia attivi", stato_it["ATTIVO"], 9886), ("Italia in rimozione", stato_it["IN RIMOZIONE"], 116),
                      ("Milano", mil["telefoni"], 627), ("Milano attivi", mil["attivi"], 624), ("Milano in rimozione", mil["in_rimozione"], 3),
                      ("Milano stradali", acc_m.get("Impianto Stradale"), 444), ("Milano commerciali", acc_m.get("Esercizio Commerciale"), 68), ("Milano altro", acc_m.get("ALTRO"), 115),
                      ("Milano righe che ripetono indirizzo", mil["righe_con_indirizzo_ripetuto"], 78), ("OSM elementi", len(punti), 273), ("OSM con check_date", len(con_cd), 142)]:
    C("  %-36s calcolato %s, atteso %s %s" % (nome_, v, att, "OK" if v == att else "<-- DIVERSO"))
open(os.path.join(OUT, "controlli.txt"), "w", encoding="utf8").write("\n".join(ctl) + "\n")
