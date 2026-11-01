"""Controllo incrociato dei nomi delle pietre 'razziali' con i dati CDEC (Nomi della Shoah, LOD) scaricati con cdec_sparql.py.
Solo controllo: nessun dato CDEC finisce in pietre.csv. Uso: python -I -X utf8 cdec_controllo.py <pietre-inciampo_abs>"""
import sys, os, re, json, unicodedata
import pandas as pd

A = sys.argv[1]
pul = os.path.join(A, "pulito")


def tok(s):
    s = unicodedata.normalize("NFKD", (s or "").replace("’", " ").replace("'", " ")).encode("ascii", "ignore").decode().lower()
    return frozenset(re.sub(r"[^a-z ]", " ", s).split())


X = pd.read_csv(os.path.join(A, "raw", "cdec", "cdec_persone.csv"), sep=";", dtype=str, keep_default_na=False)
X["tok"] = (X.cognome + " " + X.nome).map(tok)
X["anno"] = X.nascita.str.extract(r"(\d{4})")[0].fillna("")
C = pd.read_csv(os.path.join(pul, "pietre.csv"), sep=";", dtype=str, keep_default_na=False)
C = C[(C.categoria == "razziale")].copy()
by = {}
for i, r in X.iterrows():
    by.setdefault(r.tok, []).append(i)
rows = []
for _, c in C.iterrows():
    t = tok(c.nome); cand = by.get(t, [])
    how = "nome uguale"
    if not cand:
        cand = [i for k, v in by.items() if (t <= k or k <= t) and len(t & k) >= 2 for i in v]; how = "nome incluso"
    hit = [i for i in cand if X.anno[i] == c.anno_nascita] or []
    rows.append({"id_scheda": c.id_scheda, "nome": c.nome, "anno_nascita_pietra": c.anno_nascita, "candidati_cdec": len(cand), "stesso_anno_nascita": len(hit),
                 "tipo": how if cand else "nessuno", "sopravvissuto_cdec": ";".join(sorted({X.sopravvissuto[i] for i in hit})) if hit else ""})
R = pd.DataFrame(rows)
R.to_csv(os.path.join(pul, "controllo_cdec.csv"), sep=";", index=False)
out = {"persone_cdec_scaricate": int(len(X)), "pietre_razziali": int(len(C)),
       "trovate_stesso_nome_e_anno": int((R.stesso_anno_nascita > 0).sum()), "trovate_solo_nome": int(((R.candidati_cdec > 0) & (R.stesso_anno_nascita == 0)).sum()),
       "non_trovate": int((R.candidati_cdec == 0).sum()), "cdec_sopravvissuto_true_tra_trovate": int(R.sopravvissuto_cdec.str.contains("true").sum()),
       "cdec_sopravvissuto_valori": R.sopravvissuto_cdec.value_counts().to_dict(),
       "non_trovate_elenco": R[R.candidati_cdec == 0].nome.tolist()}
json.dump(out, open(os.path.join(pul, "controllo_cdec.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(out, ensure_ascii=False, indent=1))
