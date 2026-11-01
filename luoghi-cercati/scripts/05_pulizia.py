"""Passo 5: pulizia -> tabelle ordinate in pulito/.
 - views_mensili.csv   : qid;nome;lingua;mese;views   (solo mesi presenti nell'API: l'API NON restituisce i mesi con 0 visualizzazioni)
 - totali_luogo.csv    : un record per luogo, totale luglio 2015 - ultimo mese, per lingua principale, it/estero, primo/ultimo mese, picco
 - totali_lingua.csv   : totale per lingua
 - controllo_pulizia.json
Uso: python -I -X utf8 05_pulizia.py <luoghi-cercati assoluto>
Fonte dei numeri: Wikimedia REST API pageviews per-article, all-access, agent=user (CC0)."""
import sys, os, json, csv, glob, collections

base = sys.argv[1]
raw = os.path.join(base, "raw", "pageviews_mensili")
out = os.path.join(base, "pulito")
luoghi = {r["qid"]: r for r in csv.DictReader(open(os.path.join(out, "luoghi.csv"), encoding="utf8"), delimiter=";")}
MAIN = ["it", "en", "de", "fr", "es", "zh", "ja", "ru", "pt", "ar"]
rows = []
bad = []
n404 = 0
nfile = 0
meta = collections.Counter()
for f in sorted(glob.glob(os.path.join(raw, "*", "*.json"))):
    try:
        d = json.load(open(f, encoding="utf8"))
    except Exception:
        bad.append(f)
        continue
    nfile += 1
    lang = d["progetto"].split(".")[0]
    if d["http"] == 404:
        n404 += 1
        continue
    for it in d["items"]:
        ts = it["timestamp"]
        rows.append((d["qid"], lang, ts[:4] + "-" + ts[4:6], it["views"]))
    meta[d["fine"]] += 1
with open(os.path.join(out, "views_mensili.csv"), "w", encoding="utf-8", newline="") as fo:
    w = csv.writer(fo, delimiter=";")
    w.writerow(["qid", "nome", "lingua", "mese", "views"])
    for q, l, m, v in sorted(rows, key=lambda r: (r[0], r[1], r[2])):
        w.writerow([q, luoghi[q]["nome"], l, m, v])
# totali
tot = collections.defaultdict(lambda: collections.defaultdict(int))
mese = collections.defaultdict(lambda: collections.defaultdict(int))
for q, l, m, v in rows:
    tot[q][l] += v
    mese[q][m] += v
lang_tot = collections.Counter()
for q in tot:
    for l, v in tot[q].items():
        lang_tot[l] += v
with open(os.path.join(out, "totali_lingua.csv"), "w", encoding="utf-8", newline="") as fo:
    w = csv.writer(fo, delimiter=";")
    w.writerow(["lingua", "views_totali", "quota_%"])
    T = sum(lang_tot.values())
    for l, v in lang_tot.most_common():
        w.writerow([l, v, round(100 * v / T, 3)])
hdr = ["qid", "nome", "tipo", "categoria", "id_nil", "nil", "lon", "lat", "n_wikipedia", "views_totali"] + ["views_" + l for l in MAIN] + [
    "views_altre_lingue", "quota_italiano_%", "primo_mese", "ultimo_mese", "mese_picco", "views_mese_picco", "origine"]
with open(os.path.join(out, "totali_luogo.csv"), "w", encoding="utf-8", newline="") as fo:
    w = csv.writer(fo, delimiter=";")
    w.writerow(hdr)
    for q in sorted(tot, key=lambda q: -sum(tot[q].values())):
        L = luoghi[q]
        t = sum(tot[q].values())
        ms = sorted(mese[q])
        pk = max(mese[q], key=lambda m: mese[q][m])
        w.writerow([q, L["nome"], L["tipo"], L["categoria"], L["id_nil"], L["nil"], L["lon"], L["lat"], L["n_wikipedia"], t] +
                   [tot[q].get(l, 0) for l in MAIN] + [t - sum(tot[q].get(l, 0) for l in MAIN),
                    round(100 * tot[q].get("it", 0) / t, 2), ms[0], ms[-1], pk, mese[q][pk], L["origine"]])
ctrl = {"file_letti": nfile, "file_illeggibili": bad, "risposte_404": n404, "righe_mensili": len(rows),
        "luoghi_con_dati": len(tot), "luoghi_in_elenco": len(luoghi), "fine_richiesta": dict(meta),
        "mese_max": max(r[2] for r in rows), "mese_min": min(r[2] for r in rows)}
json.dump(ctrl, open(os.path.join(out, "controllo_pulizia.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(ctrl)
