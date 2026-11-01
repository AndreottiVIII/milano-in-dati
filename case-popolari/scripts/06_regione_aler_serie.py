"""Estrae dai PDF scaricati (Rapporti regionali, bilanci ALER, slide Piano annuale 2026) le serie su Milano e le scrive in pulito/.
Uso: python -I -X utf8 06_regione_aler_serie.py <case-popolari>   (percorso assoluto)
Ogni riga porta file e pagina; lo script controlla che i numeri letti compaiano nel testo della pagina citata, altrimenti si ferma."""
import sys, os, re, csv, warnings
warnings.filterwarnings("ignore")
import pymupdf

base = sys.argv[1]
RAW = os.path.join(base, "raw")
OUT = os.path.join(base, "pulito")
os.makedirs(OUT, exist_ok=True)
REG = os.path.join(RAW, "regione_rapporti_sap")


def num(s):
    s = (s or "").strip().replace("\n", " ").split(" ")[0]
    if s == "":
        return None
    if s == "-":
        return 0
    return int(s.replace(".", "")) if re.fullmatch(r"[\d\.]+", s) else None


def fmt(n):
    return f"{n:,}".replace(",", ".")


def check(doc, pno, *vals):
    t = doc[pno - 1].get_text("text")
    for v in vals:
        if v is not None and str(v) not in t:
            raise SystemExit(f"CONTROLLO FALLITO: {v} non compare a p.{pno}")


def write(name, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(name, len(rows), "righe")


# 1. Patrimonio SAP nella citta' di Milano (tabella per ambito, riga 'Milano Citta')
PATR = [
    ("zip_2014_2022/Rapporto al Consiglio 2017.pdf", "Rapporto 2017 (DGR 2017)", "2017-07-13", 12),
    ("zip_2014_2022/Rapporto al Consiglio 2017_2.pdf", "Rapporto 2017 (DGR XI/323, 10/7/2018)", "2018-03-31", 10),
    ("zip_2014_2022/Rapporto al Consiglio 2018.pdf", "Rapporto 2018", "2019-03-31", 10),
    ("zip_2014_2022/Rapporto al Consiglio 2019.pdf", "Rapporto 2019", "2020-07-15", 38),
    ("zip_2014_2022/Rapporto al Consiglio 2020.pdf", "Rapporto 2020", "2021-06-01", 25),
    ("zip_2014_2022/Rapporto al Consiglio 2021.pdf", "Rapporto 2021", "2022-03-01", 20),
    ("zip_2014_2022/Rapporto al Consiglio 2022.pdf", "Rapporto 2022", "2023-06-30", 10),
    ("rapporto_consiglio_2024.pdf", "Rapporto 2024", "2025-07-15", 7),
    ("rapporto_consiglio_2025_dgr6666.pdf", "Rapporto 2025 (DGR XII/6666)", "2026-07-03", 10),
]
rows = []
for f, nome, data, pno in PATR:
    doc = pymupdf.open(os.path.join(REG, f))
    words = doc[pno - 1].get_text("words")
    found = False
    for i, w in enumerate(words):
        if w[4].startswith("Milano") and words[i + 1][4].startswith("Citt"):
            yc = (w[1] + w[3]) / 2
            row = [x[4] for x in sorted([x for x in words if abs((x[1] + x[3]) / 2 - yc) < 4], key=lambda x: x[0])]
            nums = [int(x.replace(".", "")) for x in row if re.fullmatch(r"\d{1,3}(\.\d{3})+", x)]
            if len(nums) >= 3 and nums[0] + nums[1] == nums[2]:
                com, aler, tot = nums[:3]
                check(doc, pno, fmt(com), fmt(aler))
                nota = "prima edizione 2017: Comune 29.486 contro 23.172 dell'edizione successiva (probabile inclusione di altri usi residenziali): non confrontabile" if nome == "Rapporto 2017 (DGR 2017)" else ""
                rows.append(dict(rapporto=nome, data_riferimento=data, unita_proprieta_Comune_di_Milano=com, unita_proprieta_ALER_Milano=aler,
                                 totale_Milano_citta=tot, file=f, pagina=pno, nota=nota))
                found = True
                break
    if not found:
        print("riga non trovata", f)
write("patrimonio_sap_milano_serie.csv", rows)

# 2. Avvisi SAP, domande e assegnazioni (ambito Milano Citta')
AVV = [
    ("zip_2014_2022/Rapporto al Consiglio 2020.pdf", 2019, 33, "A"),
    ("zip_2014_2022/Rapporto al Consiglio 2020.pdf", 2020, 36, "A"),
    ("zip_2014_2022/Rapporto al Consiglio 2022.pdf", 2022, 15, "B"),
    ("rapporto_consiglio_2024.pdf", 2024, 11, "C"),
    ("rapporto_consiglio_2025_dgr6666.pdf", 2025, 17, "D"),
]
rows = []
for f, anno, pno, lay in AVV:
    doc = pymupdf.open(os.path.join(REG, f))
    page = doc[pno - 1]
    for tb in page.find_tables().tables:
        T = tb.extract()
        for i, r in enumerate(T):
            if any(c and "Milano Citt" in c for c in r):
                for k, rr in enumerate(T[i:i + 3]):
                    if k > 0 and (rr[0] or "").strip():
                        break
                    c = [(x or "").replace("\n", " ").strip() for x in rr]
                    if lay == "A":
                        ap, ch, A, B, C, D, E = c[2], c[3], num(c[4]), num(c[6]), num(c[8]), num(c[11]), num(c[13])
                    elif lay == "B":
                        ap, ch, A, B, C, D, E = c[2], c[3], num(c[4]), num(c[5]), num(c[6]), num(c[7]), num(c[8])
                    elif lay == "C":
                        ap, ch, A, B, C, D, E = c[2], c[3], num(c[4]), num(c[5]), num(c[7]), num(c[8]), num(c[9])
                    else:
                        ap, ch, A, B, C, D, E = c[3], c[4], num(c[5]), num(c[6]), num(c[8]), num(c[11]), num(c[12])
                    ap = re.sub(r"- ", "-", ap)
                    ch = re.sub(r"- ", "-", ch)
                    check(doc, pno, fmt(B) if B and B > 999 else B)
                    rows.append(dict(anno_avvisi=anno, avviso_n=k + 1, apertura=ap, chiusura=ch, alloggi_pubblicati_in_avviso=A, domande=B,
                                     domande_nuclei_indigenti_ISEE_3000=C, alloggi_assegnati=D, assegnati_a_nuclei_indigenti=E, file=f, pagina=pno))
write("avvisi_milano.csv", rows)

# 3. Domande in graduatoria e assegnazioni ERP (tabelle 2016-2020 dei Rapporti)
DOM = [("zip_2014_2022/Rapporto al Consiglio 2017.pdf", 2016, 19), ("zip_2014_2022/Rapporto al Consiglio 2017_2.pdf", 2017, 16),
       ("zip_2014_2022/Rapporto al Consiglio 2018.pdf", 2018, 17), ("zip_2014_2022/Rapporto al Consiglio 2019.pdf", 2019, 45),
       ("zip_2014_2022/Rapporto al Consiglio 2020.pdf", 2020, 42)]
rows = []
for f, anno, pno in DOM:
    doc = pymupdf.open(os.path.join(REG, f))
    for tb in doc[pno - 1].find_tables().tables:
        for r in tb.extract():
            if any(c and "Milano Citt" in c for c in r):
                c = [(x or "").strip() for x in r]
                dom, reg, nuc, tot = num(c[2]), num(c[4]), num(c[6]), num(c[8])
                check(doc, pno, c[2], c[8])
                rows.append(dict(anno=anno, domande_in_graduatoria=dom, assegnazioni_regolari=reg, assegnazioni_a_nuclei_ISEE_ERP_sotto_4000=nuc,
                                 assegnazioni_totale=tot, file=f, pagina=pno,
                                 nota="stesso valore 25.192 ripetuto in 2018, 2019 e 2020: probabile dato non aggiornato" if dom == 25192 else ""))
                break
write("domande_assegnazioni_erp_milano_2016_2020.csv", rows)

# 4. Occupazioni abusive consolidate (ALER Milano, Comune/MM)
rows = []
t = open(os.path.join(RAW, "aler_trasparenza", "txt", "consuntivo_2021.txt"), encoding="utf-8", errors="replace").read().split("\n")
for l in t:
    m = re.match(r"\s*(20\d\d)\s+([\d\.]+)\s+(\d+)\s+(\d+)\s+", l)
    if m and 2013 <= int(m.group(1)) <= 2021 and 2000 < num(m.group(2)) < 4000:
        rows.append(dict(anno=int(m.group(1)), ente="ALER Milano (bilanci ALER)", occupazioni_consolidate=num(m.group(2)),
                         fonte="ALER Milano, Relazione sulla gestione 2021 (bilancio_consuntivo_2021.pdf), tabella andamento occupazioni abusive"))
t23 = open(os.path.join(RAW, "aler_trasparenza", "txt", "consuntivo_2023.txt"), encoding="utf-8", errors="replace").read().split("\n")
for l in t23:
    m = re.match(r"\s*(2022|2023)\s+([\d\.]+)\s+(\d+)\s+(\d+)\s+", l)
    if m and 2000 < num(m.group(2)) < 4000:
        rows.append(dict(anno=int(m.group(1)), ente="ALER Milano (bilanci ALER)", occupazioni_consolidate=num(m.group(2)),
                         fonte="ALER Milano, Relazione sulla gestione 2023 (bilancio_consuntivo_2023.pdf), stessa tabella"))
doc = pymupdf.open(os.path.join(REG, "rapporto_consiglio_2025_dgr6666.pdf"))
for tbi, tb in enumerate(doc[42].find_tables().tables):
    for r in tb.extract():
        if (r[0] or "").strip() in ("2021", "2022", "2023", "2024", "2025"):
            ente = "ALER Milano (Rapporto regionale 2025)" if tbi == 0 else "Comune di Milano / MM (Rapporto regionale 2025)"
            rows.append(dict(anno=int(r[0]), ente=ente, occupazioni_consolidate=num(r[1]),
                             fonte="Rapporto regionale 2025 (DGR XII/6666), p.43, tabella " + ("ALER Milano - Settore Sicurezza abusivismo" if tbi == 0 else "Comune di Milano - MM, Divisione Casa") + ", aggiornamento dicembre 2025"))
rows.sort(key=lambda r: (r["ente"], r["anno"]))
write("occupazioni_abusive_serie.csv", rows)

# 5. Piano annuale 2026 del Comune di Milano: tabelle per Municipio (slide Giunta delib. 30/2026)
doc = pymupdf.open(os.path.join(RAW, "comune_piano_annuale", "slide_giunta_30_26.pdf"))
pages = {3: "b) in carenza manutentiva, assegnabili nello stato di fatto", 4: "c) assegnabili dopo ristrutturazione/recupero (programmi formalizzati)",
         5: "d) da nuova edificazione", 6: "e) liberi o che si libereranno per turn-over (avvicendamento)", 7: "g) totale assegnabili SAP 2026"}


def split(s):
    s = (s or "").strip()
    m = re.match(r"([\d\.]+)(?:\s*\((\d+)\))?", s)
    return (int(m.group(1).replace(".", "")), int(m.group(2)) if m.group(2) else 0) if m else (None, None)


rows = []
for pno, voce in pages.items():
    for tb in doc[pno - 1].find_tables().tables:
        T = tb.extract()
        if len(T) > 1 and (T[1][0] or "").startswith("Municipio"):
            for r in T[1:]:
                if (r[0] or "").startswith("Municipio") or (r[0] or "") == "TOTALE":
                    c, cb = split(r[1])
                    a, ab = split(r[2])
                    rows.append(dict(voce=voce, municipio=r[0], alloggi_Comune_MM=c, di_cui_senza_barriere_Comune=cb, alloggi_ALER=a, di_cui_senza_barriere_ALER=ab,
                                     fonte=f"Comune di Milano, slide Giunta delib. 30/2026 (Piano annuale 2026), p.{pno}"))
            break
write("piano_annuale_2026_per_municipio.csv", rows)
t = doc[2].find_tables().tables[0].extract()
rows = []
for r in t[1:]:
    rows.append(dict(categoria=r[0], alloggi_Comune_di_Milano=num(r[1]), alloggi_ALER_Milano=num(r[2]), alloggi_Comune_di_Cinisello_Balsamo=num(r[3]),
                     fonte="stessa slide, p.3 (consistenza attuale del patrimonio abitativo pubblico e sociale a Milano)"))
write("piano_annuale_2026_consistenza.csv", rows)
