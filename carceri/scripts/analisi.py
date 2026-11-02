"""Calcola i riepiloghi per la pagina "Le carceri di Milano" a partire da pulito/*.csv e dalle schede.

Uso:  python -I -X utf8 analisi.py <percorso assoluto di carceri>
Scrive pulito/riepilogo.json, pulito/schede_milano.csv, pulito/serie_nazionali_*.csv,
pulito/posizione_giuridica_mensile.csv, pulito/controlli.txt (aggiunge i controlli).
"""
import csv, html, json, re, sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from estrai import righe, testo, num   # noqa: E402

# Il nome di San Vittore cambia nel tempo ("FRANCESCO DI CATALDO" / "F. DI CATALDO"): si riconosce dalle parole chiave.
MI = {"SV": "SAN VITTORE", "BO": 'BOLLATE', "OP": 'OPERA'}
MZ = "MONZA"


def e_istituto(r, k):
    if r["regione"] != "LOMBARDIA":
        return False
    nome = MI.get(k, MZ)
    return (nome in r["istituto"]) if k != "MZ" else r["istituto"] == MZ
NOMI = {"SV": "San Vittore", "BO": "Bollate", "OP": "Opera"}


def n(x):
    return int(str(x).replace(".", ""))


def pct(a, b):
    return round(100.0 * a / b, 1) if b else None


def leggi_istituti(pul):
    rows = list(csv.DictReader(open(pul / "istituti_mensili.csv", encoding="utf8")))
    visto, out = {}, []
    for r in rows:                      # due pagine per il 31/12/2021 (stessi numeri): tengo la prima
        visto.setdefault(r["data"], r["file"])
        if visto[r["data"]] == r["file"]:
            for k in ("capienza", "presenti", "donne", "stranieri"):
                r[k] = int(r[k])
            out.append(r)
    return out


def scheda(root, cod, nome):
    h = (root / "raw" / "schede" / f"{cod}.html").read_text(encoding="utf8", errors="replace")
    t = testo(h[h.find('id="main-content"'):])
    m = re.search(r"posti regolamentari posti non disponibili totale detenuti (\d+) (\d+) (\d+) dati aggiornati al (\S+)", t)
    p = re.search(r"polizia penitenziaria - effettivi polizia penitenziaria - previsti amministrativi - effettivi "
                  r"amministrativi - previsti educatori - effettivi educatori - previsti (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) "
                  r"personale polizia penitenziaria aggiornato al (\S+)", t)
    s = re.search(r"Stanze di detenzione numero complessivo numero non disponibili .*? (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) (\d+) Spazi d", t)
    d = dict(scheda=cod, istituto=nome, posti_regolamentari=int(m.group(1)), posti_non_disponibili=int(m.group(2)),
             detenuti=int(m.group(3)), dati_aggiornati_al=m.group(4))
    if p:
        d.update(polizia_effettivi=int(p.group(1)), polizia_previsti=int(p.group(2)), amministrativi_effettivi=int(p.group(3)),
                 amministrativi_previsti=int(p.group(4)), educatori_effettivi=int(p.group(5)),
                 educatori_previsti=int(p.group(6)), personale_aggiornato_al=p.group(7))
    if s:
        d.update(stanze=int(s.group(1)), stanze_non_disponibili=int(s.group(2)))
    return d


def main(root):
    root = Path(root)
    pul = root / "pulito"
    ctrl = []
    ist = leggi_istituti(pul)
    date = sorted(set(r["data"] for r in ist))
    ultima = date[-1]

    # ---------- 1. serie dei tre istituti milanesi (+ Monza per confronto) ----------
    serie = {}
    for k in ("SV", "BO", "OP", "MZ"):
        nome = k
        s = []
        for d in date:
            r = [x for x in ist if x["data"] == d and e_istituto(x, k)]
            if len(r) != 1:
                ctrl.append(f"ATTENZIONE {nome} {d}: {len(r)} righe")
                continue
            r = r[0]
            s.append([d, r["capienza"], r["presenti"], r["donne"], r["stranieri"]])
        serie[k] = s
    # ---------- 2. Lombardia e Italia ----------
    tot = defaultdict(lambda: [0, 0, 0, 0])
    lom = defaultdict(lambda: [0, 0, 0, 0])
    for r in ist:
        for a in (tot, lom if r["regione"] == "LOMBARDIA" else None):
            if a is not None:
                v = a[r["data"]]
                v[0] += r["capienza"]; v[1] += r["presenti"]; v[2] += r["donne"]; v[3] += r["stranieri"]
    italia = [[d] + tot[d] for d in date]
    lombardia = [[d] + lom[d] for d in date]

    # ---------- controllo: somma degli istituti = riga della regione (tabella regionale) ----------
    reg = {}
    for r in csv.reader(open(pul / "regioni_mensili.csv", encoding="utf8")):
        if r[2] == "capienza":
            reg[(r[0], r[3])] = [n(x) for x in r[4].split("|")]   # n.istituti, capienza, presenti, donne, stranieri, ...
    agg = defaultdict(lambda: [0, 0, 0, 0, 0])
    for r in ist:
        v = agg[(r["data"], r["regione"])]
        v[0] += 1; v[1] += r["capienza"]; v[2] += r["presenti"]; v[3] += r["donne"]; v[4] += r["stranieri"]
    diff = defaultdict(list)
    for k, v in agg.items():
        w = reg.get(k)
        if not w:
            ctrl.append(f"CONTROLLO {k}: regione assente nella tabella regionale")
            continue
        for i, nome in enumerate(["istituti", "posti", "presenti", "donne", "stranieri"]):
            if v[i] != w[i]:
                diff[k[1]].append(f"{k[0]} {nome}: somma istituti {v[i]} / riga regione {w[i]}")
    ctrl.append(f"CONTROLLO somma istituti = riga regione: {len(agg)} combinazioni mese-regione; differenze in: " +
                (", ".join(f"{g} ({len(x)})" for g, x in sorted(diff.items())) or "nessuna"))
    for g, x in sorted(diff.items()):
        ctrl += [f"  differenza {g}: {y}" for y in x]
    ctrl.append("CONTROLLO Lombardia: " + ("tutte le misure coincidono in tutti i mesi" if "LOMBARDIA" not in diff else "DIFFERENZE"))

    # ---------- 3. classifica ultimo mese ----------
    ult = [r for r in ist if r["data"] == ultima and r["capienza"] >= 50 and r["tipo"] not in ("ICAM", "IP")]
    for r in ult:
        r["occ"] = 100.0 * r["presenti"] / r["capienza"]
    ult.sort(key=lambda r: -r["occ"])
    rank = {}
    for i, r in enumerate(ult, 1):
        for k in MI:
            if e_istituto(r, k):
                rank[k] = dict(posizione=i, su=len(ult), occ=round(r["occ"], 1))
    sopra100 = sum(1 for r in ult if r["occ"] > 100)
    # mediana
    occs = sorted(r["occ"] for r in ult)
    mediana = occs[len(occs) // 2]
    classifica = [dict(istituto=r["istituto"].replace("  ", " "), regione=r["regione"], tipo=r["tipo"], capienza=r["capienza"],
                       presenti=r["presenti"], occ=round(r["occ"], 1)) for r in ult]
    # distribuzione per grafico: tutte le occupazioni ordinate (+ marcatura milanesi)
    distr = [[round(r["occ"], 1), next((k for k in MI if e_istituto(r, k)), "")] for r in ult]

    # ---------- 4. posizione giuridica mensile (Lombardia, Italia) ----------
    posiz = []
    visto = set()
    for r in csv.reader(open(pul / "regioni_mensili.csv", encoding="utf8")):
        if r[2] != "posizione_totale" or r[0] == "data":
            continue
        if (r[0], r[3]) in visto:
            continue
        visto.add((r[0], r[3]))
        celle = r[4].split("|")
        if not all(re.fullmatch(r"[\d.]+", x) for x in celle):
            # refuso nella pagina del Ministero (una cella con "\\" al posto del numero): lo ricavo dal totale
            mancanti = [i for i, x in enumerate(celle) if not re.fullmatch(r"[\d.]+", x)]
            assert mancanti == [0], (r, mancanti)
            resto = [n(x) for x in celle[1:]]
            celle[0] = str(resto[7] - resto[3] - resto[4] - resto[5] - resto[6])
            ctrl.append(f"RICAVATO {r[0]} {r[3]}: cella 'in attesa di primo giudizio' illeggibile nella pagina ({r[1]}), calcolata dal totale = {celle[0]}")
        posiz.append((r[0], r[3], [n(x) for x in celle]))
    by = defaultdict(dict)
    for d, reg, v in posiz:
        by[d][reg] = v   # [in attesa, appellanti, ricorrenti, misti, tot non def, definitivi, internati, da impostare, totale]
    pg = []
    for d in date:
        if d not in by:
            continue
        row = [d]
        # Italia = somma delle regioni
        it = [sum(by[d][g][i] for g in by[d]) for i in range(9)]
        for v in (by[d].get("LOMBARDIA"), it):
            row += [v[0], v[4], v[5], v[8]]
        pg.append(row)
        # controllo: la somma delle componenti = totale
        v = by[d]["LOMBARDIA"]
        if v[0] + v[4] + v[5] + v[6] + v[7] != v[8]:
            ctrl.append(f"posizione giuridica {d} Lombardia: componenti != totale ({v})")
    with open(pul / "posizione_giuridica_mensile.csv", "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["data", "lombardia_in_attesa_primo_giudizio", "lombardia_condannati_non_definitivi",
                    "lombardia_condannati_definitivi", "lombardia_totale", "italia_in_attesa_primo_giudizio",
                    "italia_condannati_non_definitivi", "italia_condannati_definitivi", "italia_totale"])
        w.writerows(pg)
    # controllo Italia: totale delle regioni = somma istituti
    for row in pg:
        d = row[0]
        if row[8] != tot[d][1]:
            ctrl.append(f"totale Italia {d}: posizione giuridica {row[8]} != somma istituti {tot[d][1]}")
    if not any(c.startswith("totale Italia") for c in ctrl):
        ctrl.append(f"CONTROLLO totale Italia: la tabella per posizione giuridica (somma delle regioni) coincide con la somma degli istituti in tutti i {len(pg)} mesi")

    # ---------- 5. schede ----------
    sk = [scheda(root, "MII158895", "Milano San Vittore (sezione maschile)"),
          scheda(root, "MII178501", "Milano San Vittore (sezione femminile)"),
          scheda(root, "MII172344", "Milano Bollate"), scheda(root, "MII179237", "Milano Opera")]
    with open(pul / "schede_milano.csv", "w", newline="", encoding="utf8") as fh:
        keys = sorted(set(k for d in sk for k in d), key=lambda k: list(sk[0].keys()).index(k) if k in sk[0] else 99)
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(sk)

    # ---------- 6. serie nazionali ----------
    def serie_html(cod):
        return righe((root / "raw" / "serie" / f"{cod}.html").read_text(encoding="utf8", errors="replace"))
    pgn = []
    for r in serie_html("SST996131"):
        if len(r) == 10 and r[0].isdigit():
            pgn.append([int(r[0])] + [n(x) for x in r[1:]])
    with open(pul / "serie_nazionali_posizione_giuridica.csv", "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["anno", "in_attesa_primo_giudizio", "appellanti", "ricorrenti", "misti", "condannati_non_definitivi_totale",
                    "condannati_definitivi", "internati", "da_impostare", "totale"])
        w.writerows(pgn)
    ev = []
    for r in serie_html("SST241783"):
        if len(r) == 9 and r[0].isdigit():
            ev.append([int(r[0]), n(r[1]), n(r[2]), n(r[3]), float(r[4].replace(",", ".")), float(r[5].replace(",", ".")),
                       n(r[6])])
    with open(pul / "serie_nazionali_eventi_critici.csv", "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["anno", "presenza_media", "detenuti_in_custodia_nel_corso_dell_anno", "suicidi_valore_assoluto",
                    "suicidi_ogni_10000_presenti_in_media", "suicidi_ogni_10000_in_custodia", "decessi_cause_naturali"])
        w.writerows(ev)

    # ---------- 7. IPM Milano (valori letti a mano dai PDF, con pagina) ----------
    # presenza media giornaliera nell'anno, totale MF. Pagina = pagina del PDF (conteggio pdftotext).
    ipm = [
        dict(anno=2020, milano=33.4, nazionale=None, pag_mi=21, file="SST329607_IPM_2020senzaev.pdf", pdf_id="SST329607"),
        dict(anno=2021, milano=35.4, nazionale=320.3, pag_mi=21, file="SST375191_IPM_anno2021.pdf", pdf_id="SST375191"),
        dict(anno=2022, milano=39.7, nazionale=382.3, pag_mi=21, file="SST421019_IPM_anno2022.pdf", pdf_id="SST421019"),
        dict(anno=2023, milano=38.1, nazionale=425.1, pag_mi=21, file="SST467794_IPM_anno_2023.pdf", pdf_id="SST467794"),
        dict(anno=2024, milano=63.9, nazionale=556.3, pag_mi=21, file="SST1446867_IPM_anno_2024_G.pdf", pdf_id="SST1446867"),
        dict(anno=2025, milano=71.8, nazionale=587.7, pag_mi=23, file="SST1503835_IPM_2025_Copia1.pdf", pdf_id="SST1503835"),
    ]
    # verifica: ogni numero compare nel testo della pagina indicata
    for x in ipm:
        tx = (root / "raw" / "ipm_txt" / (x["file"][:-4] + ".txt")).read_text(encoding="utf8", errors="replace").split("\f")
        pag = tx[x["pag_mi"] - 1]
        v = f'{x["milano"]:.1f}'.replace(".", ",")
        if v not in pag or "I.P.M. di Milano" not in pag:
            ctrl.append(f"IPM {x['anno']}: {v} non trovato a pag. {x['pag_mi']}")
        if x["nazionale"]:
            v = f'{x["nazionale"]:.1f}'.replace(".", ",")
            if v not in tx[0]:
                ctrl.append(f"IPM nazionale {x['anno']}: {v} non trovato a pag. 1")
    with open(pul / "ipm_milano_media_giornaliera.csv", "w", newline="", encoding="utf8") as fh:
        w = csv.writer(fh)
        w.writerow(["anno", "ipm_milano_presenza_media_giornaliera", "ipm_italia_presenza_media_giornaliera", "pagina_pdf_milano",
                    "file_pdf"])
        for x in ipm:
            w.writerow([x["anno"], x["milano"], x["nazionale"] or "", x["pag_mi"], x["file"]])

    # ---------- riepilogo ----------
    ri = dict(date=date, ultima=ultima, serie=serie, italia=italia, lombardia=lombardia, rank=rank, sopra100=sopra100,
              n_classifica=len(ult), mediana_occ=round(mediana, 1), classifica=classifica, distr=distr, posiz=pg,
              schede=sk, posiz_annuale=pgn, eventi=ev, ipm=ipm)
    (pul / "riepilogo.json").write_text(json.dumps(ri, ensure_ascii=False), encoding="utf8")
    c0 = (pul / "controlli.txt").read_text(encoding="utf8").splitlines()
    c0 = [c for c in c0 if not c.startswith("ANALISI")]
    c0 += ["ANALISI: " + c for c in ctrl] or ["ANALISI: nessun avviso"]
    (pul / "controlli.txt").write_text("\n".join(c0), encoding="utf8")
    print("avvisi:", ctrl)
    print("ultima", ultima, "rank", rank, "sopra100", sopra100, "su", len(ult), "mediana", round(mediana, 1))
    for k in ("SV", "BO", "OP"):
        print(k, serie[k][0], serie[k][-1])
    print("Italia", italia[0], italia[-1]); print("Lombardia", lombardia[0], lombardia[-1])
    print("posiz", pg[0], pg[-1])
    for s in sk:
        print(s)


if __name__ == "__main__":
    main(sys.argv[1])
