"""Confronti tra fonti -> pulito/differenze.md (testo, italiano semplice) + pulito/copertura_stagioni_1906_1963.csv + pulito/_numeri_confronti.json
 A) Cambiasi 1881 / Romani 1862 / Wikipedia, anni 1778-1862
 B) Gatti vol.1 / Wikipedia / Wikidata / Marangoni, stagioni 1906-07 ... 1962-63
Uso: python -I -X utf8 scripts/confronti.py pulito"""
import sys, os, csv, json, re, collections, difflib, unicodedata

P = sys.argv[1]
K = json.load(open(os.path.join(P, "_chiavi_per_anno.json"), encoding="utf-8"))
rows = list(csv.DictReader(open(os.path.join(P, "cartellone.csv"), encoding="utf-8")))
def keys(a, src): return set(K.get(str(a), {}).get(src, []))
def best(k, pool, cut=0.86):
    if k in pool: return k
    m = difflib.get_close_matches(k, list(pool), n=1, cutoff=cut)
    return m[0] if m else None
out = []
num = {}
def W(s=""): out.append(s)

# ------------------------------------------------------------------ A
W("# La Scala, cartellone: differenze tra le fonti (fase 2)")
W("")
W("Scritto il 29/10/2026 dal programma `scripts/confronti.py`. Ogni numero viene da `pulito/cartellone.csv` (campi `fonte`, `anno`, `titolo`). "
  "Un titolo e' considerato lo stesso se, tolti articoli, accenti e punteggiatura, le lettere sono uguali o simili al 86% (difflib).")
W("")
W("## A. Cambiasi 1881, Romani 1862 e Wikipedia (1778-1862)")
W("")
W("Attenzione: Cambiasi e Romani contano per *anno teatrale* (il Carnevale che comincia il 26 dicembre vale per l'anno dopo); Wikipedia conta per anno del calendario. "
  "Per Wikipedia si confronta quindi anche con l'anno prima e l'anno dopo.")
tot = collections.Counter()
per_year = []
examples_c_only = []; examples_r_only = []; examples_wp_missing = []
for a in range(1778, 1863):
    C, R, Wp = keys(a, "cambiasi_1881"), keys(a, "romani_1862"), keys(a, "wikipedia_it_stagioni_liriche")
    Wp3 = Wp
    adj = set()
    for d in (-1, 0, 1):
        adj |= keys(a + d, "cambiasi_1881") | keys(a + d, "romani_1862")
    if C and R:
        tot["anni_C_e_R"] += 1
        tot["C"] += len(C); tot["R"] += len(R)
        rc = [k for k in R if best(k, C)]
        cr = [k for k in C if best(k, R)]
        tot["R_in_C"] += len(rc); tot["C_in_R"] += len(cr)
        per_year.append((a, len(C), len(R), len(rc), len(cr)))
        if len(examples_c_only) < 12: examples_c_only += [(a, k) for k in sorted(C) if not best(k, R)][:2]
        if len(examples_r_only) < 12: examples_r_only += [(a, k) for k in sorted(R) if not best(k, C)][:2]
    if Wp:
        tot["anni_con_WP"] += 1
        tot["WP"] += len(Wp)
        inC = [k for k in Wp if best(k, set().union(*(keys(a + d, "cambiasi_1881") for d in (-1, 0, 1))))]
        inR = [k for k in Wp if best(k, set().union(*(keys(a + d, "romani_1862") for d in (-1, 0, 1))))]
        inany = [k for k in Wp if best(k, adj)]
        tot["WP_in_C"] += len(inC); tot["WP_in_R"] += len(inR); tot["WP_in_C_o_R"] += len(inany)
        if len(examples_wp_missing) < 10: examples_wp_missing += [(a, k) for k in sorted(Wp) if not best(k, adj)][:1]
W("| Che cosa | Numero |")
W("|---|---|")
W("| Anni 1778-1862 con righe sia in Cambiasi sia in Romani | %d (su 85) |" % tot["anni_C_e_R"])
W("| Titoli distinti in quegli anni: Cambiasi / Romani | %d / %d |" % (tot["C"], tot["R"]))
if tot["R"]:
    W("| Titoli di Romani che si trovano anche in Cambiasi | %d (%.0f%%) |" % (tot["R_in_C"], 100 * tot["R_in_C"] / tot["R"]))
if tot["C"]:
    W("| Titoli di Cambiasi che si trovano anche in Romani | %d (%.0f%%) |" % (tot["C_in_R"], 100 * tot["C_in_R"] / tot["C"]))
W("| Anni 1778-1862 con righe nella pagina Wikipedia | %d |" % tot["anni_con_WP"])
if tot["WP"]:
    W("| Titoli Wikipedia (anni 1778-1862) | %d |" % tot["WP"])
    W("| ... trovati in Cambiasi (anno prima/uguale/dopo) | %d (%.0f%%) |" % (tot["WP_in_C"], 100 * tot["WP_in_C"] / tot["WP"]))
    W("| ... trovati in Romani | %d (%.0f%%) |" % (tot["WP_in_R"], 100 * tot["WP_in_R"] / tot["WP"]))
    W("| ... trovati in almeno uno dei due | %d (%.0f%%) |" % (tot["WP_in_C_o_R"], 100 * tot["WP_in_C_o_R"] / tot["WP"]))
num["A"] = dict(tot)
W("")
W("Come leggere: le percentuali non arrivano al 100% per tre motivi diversi che qui non si possono separare del tutto: (1) l'OCR di Cambiasi storpia i titoli (es. 'Troja distrutta' / 'Troia distrutta' si ritrovano, ma 'Calliroe -fa' no); "
  "(2) il parser di Romani legge bene solo le stagioni scritte con la formula 'Titolo. D. s.' (nel `NOTE.md` si dice quali anni mancano); (3) vere differenze tra le due cronologie.")
W("")
W("Esempi di titoli presenti in un solo libro (anno, titolo normalizzato):")
W("")
W("- Solo in Cambiasi: " + "; ".join("%d %s" % x for x in examples_c_only[:10]))
W("- Solo in Romani: " + "; ".join("%d %s" % x for x in examples_r_only[:10]))
W("- In Wikipedia ma non in Cambiasi/Romani: " + "; ".join("%d %s" % x for x in examples_wp_missing[:8]))
W("")
W("Anni in cui i due libri differiscono di piu' (anno: Cambiasi, Romani, Romani trovati in Cambiasi):")
W("")
bad = sorted(per_year, key=lambda t: -(t[2] - t[3]))[:8]
for a, c, r, rc, cr in bad:
    W("- %d: Cambiasi %d titoli, Romani %d, Romani in Cambiasi %d" % (a, c, r, rc))
W("")

# ------------------------------------------------------------------ B
W("## B. Gatti vol. I contro Wikipedia, Wikidata e Marangoni (stagioni 1906-07 ... 1962-63)")
W("")
W("Gatti (vol. I, 1964) e' il racconto, non la cronologia: dall'indice delle opere e dal testo si ricavano i titoli *citati come rappresentati* in ogni stagione (righe con `segnale_spettacolo = si`, senza i testi letterari). "
  "Non e' un elenco completo: i titoli che Gatti non nomina non ci sono.")
W("")
def season_of(date):
    y, m = int(date[:4]), int(date[5:7])
    return y if m >= 9 else y - 1
sea = {}
for y in range(1906, 1963):
    sea[y] = {"gatti": set(), "gatti_am": set(), "wp": set(), "wd": set(), "mar": set()}
for r in rows:
    try: a = int(r["anno"])
    except ValueError: continue
    k = None
    if r["fonte"] == "gatti_vol1":
        if 1906 <= a <= 1962:
            kk = re.sub(r"\s+", " ", r["titolo"])
            sea[a]["gatti"].add(kk)
            if r["affidabilita"] == "media": sea[a]["gatti_am"].add(kk)
    elif r["fonte"] == "wikipedia_it_stagioni_liriche":
        if r["data"] and re.match(r"^\d{4}-\d\d-\d\d$", r["data"]):
            s = season_of(r["data"])
            if 1906 <= s <= 1962: sea[s]["wp"].add(r["titolo"])
        elif 1906 <= a <= 1963:
            for s in (a - 1, a):   # senza data: puo' essere l'una o l'altra stagione
                if 1906 <= s <= 1962: sea[s]["wp"].add(r["titolo"])
    elif r["fonte"] == "wikidata_prime":
        if r["data"] and re.match(r"^\d{4}-\d\d-\d\d$", r["data"]):
            s = season_of(r["data"])
            if 1906 <= s <= 1962: sea[s]["wd"].add(r["titolo"])
    elif r["fonte"] == "marangoni_vanbianchi_1922":
        if 1906 <= a <= 1918: sea[a]["mar"].add(r["titolo"])
def kk(t):
    import importlib
    t = unicodedata.normalize("NFD", t.lower()); t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    t = t.replace("j", "i").replace("’", "'")
    t = re.sub(r"\(.*?\)", " ", t); t = re.sub(r"[^a-z0-9 ']+", " ", t).replace("'", " ")
    t = re.sub(r"^(il|lo|la|le|gli|i|l|un|una)\s+", "", re.sub(r"\s+", " ", t).strip())
    return re.sub(r"^(il|lo|la|le|gli|i|l)\s+", "", t)
out_rows = []
tot2 = collections.Counter()
for y in range(1906, 1963):
    d = sea[y]
    G = {kk(t) for t in d["gatti"]}; WP = {kk(t) for t in d["wp"]}; WD = {kk(t) for t in d["wd"]}; MA = {kk(t) for t in d["mar"]}
    before = WP | WD | MA
    gm = {k for k in G if best(k, before, 0.88)}
    new = G - gm
    lab = "%d-%02d" % (y, (y + 1) % 100)
    out_rows.append([lab, len(WP), len(WD), len(MA), len(before), len(G), len(gm), len(new), len(before | G)])
    tot2["WP"] += len(WP); tot2["WD"] += len(WD); tot2["MA"] += len(MA); tot2["before"] += len(before); tot2["G"] += len(G); tot2["G_in_before"] += len(gm); tot2["G_new"] += len(new); tot2["after"] += len(before | G)
    if len(before) >= 5: tot2["stag_before_ge5"] += 1
    if len(before | G) >= 5: tot2["stag_after_ge5"] += 1
    if len(before) >= 1: tot2["stag_before_ge1"] += 1
    if len(before | G) >= 1: tot2["stag_after_ge1"] += 1
    if len(WP) >= 5: tot2["stag_wp_ge5"] += 1
    if len(WP) >= 1: tot2["stag_wp_ge1"] += 1
with open(os.path.join(P, "copertura_stagioni_1906_1963.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["stagione", "titoli_wikipedia", "titoli_wikidata_prime", "titoli_marangoni", "titoli_prima_di_gatti_unione", "titoli_gatti", "gatti_gia_noti", "gatti_nuovi", "titoli_dopo_gatti_unione"])
    w.writerows(out_rows)
num["B"] = dict(tot2)
W("| Che cosa (somma sulle 57 stagioni) | Numero |")
W("|---|---|")
W("| Titoli per stagione solo da Wikipedia (le righe senza data valgono per le due stagioni possibili: numero per eccesso) | %d |" % tot2["WP"])
W("| Titoli per stagione da Wikipedia + Wikidata (prime) + Marangoni (fino al 1918) | %d |" % tot2["before"])
W("| Titoli per stagione citati da Gatti vol. I | %d |" % tot2["G"])
W("| ... di cui gia' presenti nelle altre fonti | %d |" % tot2["G_in_before"])
W("| ... di cui nuovi (solo Gatti) | %d |" % tot2["G_new"])
W("| Titoli per stagione dopo aver aggiunto Gatti | %d |" % tot2["after"])
W("| Stagioni con almeno 1 titolo: solo Wikipedia / Wikipedia+Wikidata+Marangoni / con Gatti | %d / %d / %d (su 57) |" % (tot2["stag_wp_ge1"], tot2["stag_before_ge1"], tot2["stag_after_ge1"]))
W("| Stagioni con almeno 5 titoli: solo Wikipedia / Wikipedia+Wikidata+Marangoni / con Gatti | %d / %d / %d (su 57) |" % (tot2["stag_wp_ge5"], tot2["stag_before_ge5"], tot2["stag_after_ge5"]))
W("")
W("Per stagione (file `copertura_stagioni_1906_1963.csv`): colonne titoli Wikipedia, Wikidata, Marangoni, unione prima di Gatti, titoli Gatti, gia' noti, nuovi, unione dopo Gatti.")
W("")
# titoli di Wikipedia che Gatti non nomina (limite dell'indice di Gatti)
miss = []
for y in range(1906, 1963):
    d = sea[y]
    G = {kk(t) for t in d["gatti"]}
    for t in d["wp"]:
        if not best(kk(t), G, 0.88): miss.append((y, t))
tot_wp = sum(len(sea[y]["wp"]) for y in sea)
W("Titoli di Wikipedia che Gatti non nomina nella stessa stagione: %d su %d (%.0f%%). Esempi: %s." % (len(miss), tot_wp, 100 * len(miss) / max(tot_wp, 1), "; ".join("%d-%02d %s" % (y, (y + 1) % 100, t) for y, t in miss[:8])))
num["B"]["wp_non_in_gatti"] = len(miss); num["B"]["wp_totale"] = tot_wp
W("")
W("Titoli di Gatti nuovi rispetto a tutte le altre fonti, per decennio (titoli-stagione):")
W("")
dec = collections.Counter()
for r in out_rows:
    dec[int(r[0][:4]) // 10 * 10] += r[7]
W("| Decennio | Nuovi titoli da Gatti |")
W("|---|---|")
for d_, n_ in sorted(dec.items()): W("| %d-%d | %d |" % (d_, d_ + 9, n_))
W("")
open(os.path.join(P, "differenze.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
json.dump(num, open(os.path.join(P, "_numeri_confronti.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(num, ensure_ascii=False))
