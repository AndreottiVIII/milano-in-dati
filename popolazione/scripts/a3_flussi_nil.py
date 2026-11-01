"""a3: flussi (iscrizioni/cancellazioni anagrafiche) per NIL, 2004-2024, dai dataset del Comune ds1596/ds1600 (2004-2019) e ds1954/ds1956 (2020-2024), per data dell'evento.
I nomi dei quartieri vengono agganciati agli id_nil di ds27 con una normalizzazione (minuscole, apostrofi, spazi); i non agganciati ('n.d.') restano in un file a parte.
Uso: python -I -X utf8 a3_flussi_nil.py <popolazione assoluto>   Scrive pulito/flussi_nil_anno.csv, pulito/flussi_nil_nonagganciati.csv, pulito/flussi_nil_riepilogo.csv"""
import sys, os, re, json
import pandas as pd, numpy as np
P = sys.argv[1]; out = os.path.join(P, "pulito"); raw = os.path.join(P, "raw")
ana = pd.read_csv(os.path.join(out, "nil_anagrafica.csv"))
def norm(s):
    s = s.strip().lower().replace("’", "'").replace("`", "'")
    s = re.sub(r"\s+", " ", s); s = re.sub(r"\s*-\s*", " - ", s)
    return s
key = {norm(n): i for i, n in zip(ana.id_nil, ana.nil)}
def load(files, kind):
    fr = []
    for f in files:
        x = pd.read_csv(f, sep=";"); x.columns = ["anno", "quartiere", "prov", "genere", "cit", "n"]; fr.append(x)
    x = pd.concat(fr); x["tipo"] = kind
    x["id_nil"] = x.quartiere.map(lambda s: key.get(norm(s)))
    return x
I = load([f"{raw}/comune_ds1596/ds1596-popolazione-iscrizioni-evento-quartiere.csv", f"{raw}/comune_ds1954/ds1954_popolazione_iscrizioni_evento_quartiere.csv"], "isc")
C = load([f"{raw}/comune_ds1600/ds1600-popolazione-cancellazioni-evento-quartiere.csv", f"{raw}/comune_ds1956/ds1956_popolazione_cancellazioni_evento_quartiere.csv"], "canc")
A = pd.concat([I, C])
un = A[A.id_nil.isna()].groupby(["quartiere", "tipo"]).n.sum().reset_index()
un.to_csv(os.path.join(out, "flussi_nil_nonagganciati.csv"), index=False)
print("non agganciati:\n", un)
A = A[A.id_nil.notna()].copy(); A["id_nil"] = A.id_nil.astype(int)
A["origine"] = A.prov.map({"Da altro Comune italiano": "italia", "Per altro comune italiano": "italia", "Dall'estero": "estero", "Per estero": "estero", "Altro": "altro"})
g = A.groupby(["anno", "id_nil", "tipo", "origine"]).n.sum().unstack(["tipo", "origine"]).fillna(0)
g.columns = [f"{t}_{o}" for t, o in g.columns]
g = g.reset_index()
# per cittadinanza
for cit, tag in (("Italiana", "ita"), ("Straniera", "str")):
    h = A[A.cit == cit].groupby(["anno", "id_nil", "tipo", "origine"]).n.sum().unstack(["tipo", "origine"]).fillna(0)
    h.columns = [f"{t}_{o}_{tag}" for t, o in h.columns]
    g = g.merge(h.reset_index(), on=["anno", "id_nil"], how="left")
g = g.fillna(0)
g["saldo_italia"] = g.isc_italia - g.canc_italia
g["saldo_estero"] = g.isc_estero - g.canc_estero
g["saldo_tot_senza_altro"] = g.saldo_italia + g.saldo_estero
res = pd.read_csv(os.path.join(out, "eta_nil_anno_indicatori.csv"))[["anno", "id_nil", "nil", "residenti"]]
g = g.merge(res, on=["anno", "id_nil"], how="left")
g.to_csv(os.path.join(out, "flussi_nil_anno.csv"), index=False, float_format="%.6g")
# riepilogo per periodo: saldo medio annuo per 1000 residenti (residenti medi del periodo)
rows = []
for nome, (a0, a1) in {"2004-2019": (2004, 2019), "2012-2019": (2012, 2019), "2020-2024": (2020, 2024), "2022-2024": (2022, 2024)}.items():
    q = g[(g.anno >= a0) & (g.anno <= a1)].groupby(["id_nil", "nil"]).agg(res=("residenti", "mean"), si=("saldo_italia", "sum"), se=("saldo_estero", "sum"), ii=("isc_italia", "sum"), ci=("canc_italia", "sum"), ie=("isc_estero", "sum"), ce=("canc_estero", "sum")).reset_index()
    ny = a1 - a0 + 1
    q["periodo"] = nome
    q["saldo_italia_x1000_anno"] = 1000 * q.si / ny / q.res
    q["saldo_estero_x1000_anno"] = 1000 * q.se / ny / q.res
    q["saldo_tot_x1000_anno"] = q.saldo_italia_x1000_anno + q.saldo_estero_x1000_anno
    rows.append(q)
rs = pd.concat(rows); rs.to_csv(os.path.join(out, "flussi_nil_riepilogo.csv"), index=False, float_format="%.6g")
pd.set_option("display.width", 250)
for per in ("2012-2019", "2020-2024"):
    q = rs[(rs.periodo == per) & (rs.res >= 3000)].sort_values("saldo_tot_x1000_anno")
    print(per, "peggiori"); print(q.head(6)[["nil", "res", "saldo_italia_x1000_anno", "saldo_estero_x1000_anno", "saldo_tot_x1000_anno"]].round(1).to_string())
    print(per, "migliori"); print(q.tail(6)[["nil", "res", "saldo_italia_x1000_anno", "saldo_estero_x1000_anno", "saldo_tot_x1000_anno"]].round(1).to_string())
# controllo: somma NIL vs citta' (con n.d.)
tot = A.groupby(["anno", "tipo"]).n.sum().unstack()
print(tot.tail(6))
