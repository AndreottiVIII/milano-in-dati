"""Numeri 'titolo' citati nei documenti scaricati (PDF), con pagina trovata automaticamente cercando la stringa nel testo del PDF.
Scrive pulito/numeri_citati_documenti.csv e pulito/stato_utilizzo_marzo_2023.csv (tabella 'analisi unita' per stato di utilizzo' del Comune).
Uso: python -I -X utf8 11_numeri_citati.py <case-popolari>   (percorso assoluto)
Se una stringa non compare in nessuna pagina il numero NON viene scritto come verificato."""
import sys, os, re, csv, warnings
warnings.filterwarnings("ignore")
import pymupdf

base = sys.argv[1]
RAW = os.path.join(base, "raw")
OUT = os.path.join(base, "pulito")
STR = os.path.join("comune_piano_annuale", "strategia_casa_2023_wayback_20230320.pdf")
R25 = os.path.join("regione_rapporti_sap", "rapporto_consiglio_2025_dgr6666.pdf")
MON = os.path.join("regione_rapporti_sap", "monitoraggio_assegnazioni_2025.pdf")
PRO = os.path.join("regione_rapporti_sap", "zip_2014_2022", "Rapporto al Consiglio 2020.pdf")
ITEMS = [  # (file, stringa da trovare, che cosa e', valore, data di riferimento)
    (STR, "58.506 unità SAP", "alloggi SAP in citta' (Comune + ALER)", 58506, "marzo 2023"),
    (STR, "26.489 unità abitative", "SAP di proprieta' del Comune di Milano (gestite da MM)", 26489, "marzo 2023"),
    (STR, "32.017", "SAP di proprieta' ALER in citta'", 32017, "marzo 2023"),
    (STR, "1.985", "unita' SAS (servizio abitativo sociale) in citta'", 1985, "marzo 2023"),
    (STR, "273 complessi immobiliari", "complessi immobiliari comunali in citta' (di cui 200 'cielo-terra', 22.876 unita' in 682 edifici)", 273, "marzo 2023"),
    (STR, "22.876", "unita' immobiliari nei 200 edifici 'cielo-terra' del Comune (682 edifici)", 22876, "marzo 2023"),
    (STR, "circa il 10% dello stock", "quota SAP sullo stock residenziale complessivo secondo il Comune (media nazionale 4%): denominatore non dichiarato", 10, "marzo 2023"),
    (STR, "27075 unità abitative", "unita' abitative di proprieta' del Comune a Milano", 27075, "marzo 2023"),
    (STR, "22.113 case", "case comunali assegnate", 22113, "marzo 2023"),
    (STR, "4962 sono sfitte", "case comunali 'sfitte e da ristrutturare'", 4962, "marzo 2023"),
    (STR, "500 l’anno", "turnover annuo delle case comunali (stima del Comune)", 500, "2023"),
    (R25, "33.044 unit", "unita' abitative ALER Milano nella citta' di Milano (SAP)", 33044, "2026-07-03"),
    (R25, "26.009 di propriet", "unita' abitative SAP del Comune di Milano", 26009, "2026-07-03"),
    (R25, "1.261 localizzate", "altri usi residenziali del Comune di Milano (non SAP) in citta'", 1261, "2026-07-03"),
    (R25, "circa 2.600 alloggi", "alloggi ALER nel quartiere Lorenteggio (programma di rigenerazione)", 2600, "2026"),
    (R25, "782 alloggi", "alloggi in 12 fabbricati di Gratosoglio (efficientamento)", 782, "2026"),
    (R25, "120 alloggi sfitti", "alloggi sfitti da recuperare a Gratosoglio (programma Gratosoglio 2.0)", 120, "2026"),
    (R25, "circa 250 alloggi", "alloggi SAP in via Bolla 26/42 (riqualificazione)", 250, "2026"),
    (R25, "195 alloggi destinati a SAP", "alloggi SAP in 3 stabili di San Siro (viale Mar Jonio 9, piazza Selinunte 6, via Morgantini 5)", 195, "2026"),
    (R25, "7.307 alloggi sfitti", "alloggi sfitti che le ALER prevedono di recuperare con i fondi regionali (5 ALER lombarde)", 7307, "2026"),
    (R25, "4.470 alloggi sfitti", "alloggi sfitti ristrutturati a marzo 2026 (5 ALER lombarde)", 4470, "2026-03"),
    (R25, "il 94% degli alloggi", "quota di alloggi 'in ristrutturazione' (piattaforma regionale, 23/3/2025) completata dalle ALER", 94, "2026"),
    (MON, "3.076 alloggi", "alloggi assegnati in Lombardia nel 2025 (935 comuni, 2.141 ALER)", 3076, "2025-12-31"),
]
docs = {}


def find(file, s):
    if file not in docs:
        docs[file] = pymupdf.open(os.path.join(RAW, file))
    for i, p in enumerate(docs[file], 1):
        if s in p.get_text("text"):
            return i
    return None


rows = []
for f, s, che, val, data in ITEMS:
    if val == 0:
        continue
    p = find(f, s)
    rows.append(dict(descrizione=che, valore=val, data_riferimento=data, file=f.replace("\\", "/"), pagina_pdf=p if p else "NON TROVATA", stringa_cercata=s,
                     tipo_fonte="documento ufficiale (verificato nel testo del PDF)" if p else "NON VERIFICATO"))
    print(("OK  " if p else "!!  "), che[:70], val, "p.", p)
with open(os.path.join(OUT, "numeri_citati_documenti.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# Tabella 'stato di utilizzo' (strategia 2023, p.38)
d = docs[STR]
pno = find(STR, "ANALISI UNITÀ PER STATO DI UTILIZZO")
T = [tb.extract() for tb in d[pno - 1].find_tables().tables][0]
hdr = ["SAP", "SAS", "SAT"]
rows = []
def cell(x):
    x = (x or "").replace("*", "").replace(".", "").strip()
    return int(x) if x.isdigit() else None
stato = {}
for r in T:
    lab = (r[0] or "").replace("\n", " ")
    if lab.startswith("Comune") and r[1] and r[1].strip().replace(".", "").isdigit() and len(r) >= 10 and r[3] and "Milano" in lab and "Numero" not in lab:
        pass
# estrazione esplicita delle due righe della terza tabella
tabs = [tb.extract() for tb in d[pno - 1].find_tables().tables]
t3 = next(t for t in tabs if t and t[0] and "ANALISI UNITÀ PER STATO DI UTILIZZO" in (t[0][0] or ""))
for r in t3:
    lab = (r[0] or "").replace("\n", " ").strip()
    if lab in ("Comune Milano", "Aler Milano"):
        v = [cell(x) for x in r[1:10]]
        for i, serv in enumerate(hdr):
            ass, lib, sfi = v[i * 3: i * 3 + 3]
            rows.append(dict(ente=lab.replace("Comune Milano", "Comune di Milano (MM)"), servizio=serv, assegnati=ass, liberi=lib, sfitti_per_carenze_manutentive=sfi,
                             data_riferimento="marzo 2023",
                             fonte=f"Comune di Milano, 'Una nuova strategia per la casa' (20/3/2023), p.{pno}, Tabella 03 (copia Wayback Machine 20/3/2023)",
                             nota="'liberi' del Comune = 1.141 alloggi SAP+SAT in ristrutturazione/riatto (nota * del documento)" if lab.startswith("Comune") else ""))
rows.append(dict(ente="(controllo) Comune SAP: assegnati+liberi+sfitti vs totale 26.489", servizio="SAP", assegnati=21737 + 1021 + 3731, liberi=None, sfitti_per_carenze_manutentive=None, data_riferimento="marzo 2023",
                 fonte="somma", nota="= 26.489: la tabella torna"))
rows.append(dict(ente="(controllo) ALER SAP: assegnati+liberi+sfitti vs totale 32.017", servizio="SAP", assegnati=24333 + 394 + 3274, liberi=None, sfitti_per_carenze_manutentive=None, data_riferimento="marzo 2023",
                 fonte="somma", nota="= 28.001, mancano 4.016 unita' (32.017 - 28.001): il documento non dice dove stanno (verosimilmente occupate senza titolo e altre voci)"))
with open(os.path.join(OUT, "stato_utilizzo_marzo_2023.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
for r in rows:
    print(r["ente"], r["servizio"], r["assegnati"], r["liberi"], r["sfitti_per_carenze_manutentive"])
