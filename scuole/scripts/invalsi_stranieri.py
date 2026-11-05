"""INVALSI microdati campione: punteggi di nativi e stranieri al crescere della quota
di stranieri in classe. Prima grezzi, poi a parita' di ESCS, poi dentro la stessa scuola.

Uso: python -I -X utf8 invalsi_stranieri.py <raw/invalsi_campione> <cartella output>

File non fidati: letti solo come testo. WLS con peso_studente, errori a grappolo fatti a mano
(numpy) sia per classe sia per scuola. Nessun tentativo di riconoscere scuole o classi.
"""
import os
import sys

import numpy as np
import pandas as pd

RAW, OUT = sys.argv[1], sys.argv[2]
ANNI = {5: ["2023-24", "2024-25", "2025-26"], 8: ["2022-23", "2023-24", "2024-25"]}
ANNO_FILE = {"2022-23": "2023", "2023-24": "2024", "2024-25": "2025", "2025-26": "2026"}
GEO = {"Lombardia": lambda d: d.cod_reg == 4, "Nord": lambda d: d.areageo_5.isin([1, 2]), "Italia": lambda d: d.areageo_5.notna()}
BINS = [-0.001, 0.05, 0.10, 0.20, 0.30, 0.50, 1.001]
BINL = ["0-5%", "5-10%", "10-20%", "20-30%", "30-50%", ">50%"]


def num(s):
    return pd.to_numeric(s.astype(str).str.strip().str.replace(",", ".", regex=False), errors="coerce")


def leggi(grado, anno, mat):
    g = f"{grado:02d}"
    rel = os.path.join(f"g{g}_{anno}", f"{ANNO_FILE[anno]}_matrice_campione_{mat}_{g}_0_1_wle_anonima.csv")
    p = os.path.join(RAW, rel)
    with open(p, "rb") as f:
        testa = f.readline().decode("latin1")
    sep = ";" if testa.count(";") > testa.count(",") else ","
    d = pd.read_csv(p, sep=sep, encoding="latin1", dtype=str, keep_default_na=False)
    d.columns = [c.strip().lower() for c in d.columns]
    d = d.rename(columns={c: "regolarita" for c in d.columns if c.startswith("regolarit")})
    y = f"wle_{mat}_200"
    out = pd.DataFrame({
        "scuola": d["scuola_anonimo"], "classe": d["classe_anonimo"], "studente": d["studente_anonimo"],
        "cod_reg": num(d["cod_reg"]), "areageo_5": num(d["areageo_5"]), "origine": num(d["origine"]),
        "genere": num(d["genere"]), "regolarita": num(d["regolarita"]), "punteggio": num(d[y]),
        "peso": num(d["peso_studente"]), "peso_classe": num(d["peso_classe"]), "peso_scuola": num(d["peso_scuola"]),
        "escs": num(d["escs_studente"]), "escs_classe": num(d["escs_classe"]),
        "luogo": num(d["luogo"]), "luogo_padre": num(d["luogo_padre"]), "luogo_madre": num(d["luogo_madre"]),
    })
    out["grado"], out["anno"], out["materia"] = grado, anno, mat
    return out


def tutto():
    pezzi = [leggi(g, a, m) for g, aa in ANNI.items() for a in aa for m in ("ita", "mat")]
    d = pd.concat(pezzi, ignore_index=True)
    d["id_scuola"] = d.grado.astype(str) + "_" + d.anno + "_" + d.scuola
    d["id_classe"] = d.id_scuola + "_" + d.classe
    # quota in classe: unione degli studenti delle due prove, per non dipendere da chi manca a una sola
    u = d.sort_values("materia").drop_duplicates(["id_classe", "studente"])
    conta = u.groupby("id_classe").agg(
        n=("studente", "size"), noti=("origine", lambda s: s.isin([1, 2, 3]).sum()),
        stranieri=("origine", lambda s: s.isin([2, 3]).sum()),
        g1=("origine", lambda s: (s == 2).sum()), g2=("origine", lambda s: (s == 3).sum()),
    ).reset_index()
    conta["quota"] = conta.stranieri / conta.noti.where(conta.noti > 0)
    conta["quota_mancante"] = 1 - conta.noti / conta.n
    d = d.merge(conta, on="id_classe", how="left")
    d["straniero"] = d.origine.isin([2, 3]).astype(float)
    # compagni: esclude se stessi (conta per gli stranieri, quasi nulla per i nativi)
    d["quota_comp"] = (d.stranieri - d.straniero) / (d.noti - 1).where(d.noti > 1)
    d["quota10"] = d.quota_comp * 10  # coefficiente = punti per +10 punti percentuali di compagni stranieri
    d["femmina"] = (d.genere == 2).astype(float)
    d["in_ritardo"] = (d.regolarita == 3).astype(float)
    d["g1"] = (d.origine == 2).astype(float)
    d["bin"] = pd.cut(d.quota, BINS, labels=BINL)
    return d, conta


def wls_cl(df, y, xs, fe=None, cl=("id_classe", "id_scuola"), pesi=True):
    """WLS con eventuale effetto fisso (weighted within) ed errori a grappolo CR1."""
    c = df[[y] + xs + list(cl) + ["peso"]].dropna().copy()  # fe e' sempre una delle colonne di cl
    w = c["peso"].values if pesi else np.ones(len(c))
    Y = c[y].values.astype(float)
    X = c[xs].values.astype(float)
    if fe:
        g = c[fe].values
        cod, inv = np.unique(g, return_inverse=True)
        sw = np.bincount(inv, w)
        Y = Y - (np.bincount(inv, w * Y) / sw)[inv]
        X = np.column_stack([X[:, j] - (np.bincount(inv, w * X[:, j]) / sw)[inv] for j in range(X.shape[1])])
    else:
        X = np.column_stack([np.ones(len(c)), X])
    XtWX = (X * w[:, None]).T @ X
    inv_ = np.linalg.pinv(XtWX)
    b = inv_ @ ((X * w[:, None]).T @ Y)
    e = Y - X @ b
    res = {"n": len(c), "b": b[0 if fe else 1:]}
    for nome in cl:
        ids, ii = np.unique(c[nome].values, return_inverse=True)
        G = len(ids)
        sc = np.zeros((G, X.shape[1]))
        np.add.at(sc, ii, X * (w * e)[:, None])
        k = X.shape[1]
        adj = G / (G - 1) * (len(c) - 1) / max(len(c) - k, 1)
        V = adj * inv_ @ (sc.T @ sc) @ inv_
        res["se_" + nome] = np.sqrt(np.diag(V))[0 if fe else 1:]
        res["G_" + nome] = G
    return res


def tq(df):
    z = 1.959964
    return z + (z ** 3 + z) / (4 * df)


def dummies(df, col):
    v = sorted(df[col].dropna().unique())
    nomi = []
    for x in v[1:]:
        n = f"_{col}_{x}"
        df[n] = (df[col] == x).astype(float)
        nomi.append(n)
    return nomi


def modelli(d):
    righe = []
    for grado in (5, 8):
        for mat in ("ita", "mat"):
            for geo, f in GEO.items():
                for gruppo, ori in (("nativi", [1]), ("stranieri", [2, 3]), ("I gen.", [2]), ("II gen.", [3])):
                    s = d[(d.grado == grado) & (d.materia == mat) & f(d) & d.origine.isin(ori) & d.quota_ok].copy()
                    if geo == "Italia" and gruppo in ("I gen.", "II gen."):
                        continue
                    if len(s) < 100:
                        continue
                    ya = dummies(s, "anno")
                    ra = dummies(s, "cod_reg") if geo != "Lombardia" else []
                    specs = {
                        "A grezzo (solo anno)": (["quota10"] + ya, None),
                        "A2 grezzo + regione": (["quota10"] + ya + ra, None),
                        "B ESCS individuale": (["quota10", "escs"] + ya + ra, None),
                        "C ESCS individuale + classe": (["quota10", "escs", "escs_classe"] + ya + ra, None),
                        "D C + genere, ritardo" + (", generazione" if gruppo == "stranieri" else ""):
                            (["quota10", "escs", "escs_classe", "femmina", "in_ritardo"] + (["g1"] if gruppo == "stranieri" else []) + ya + ra, None),
                        "E stessa scuola, ESCS individuale": (["quota10", "escs"], "id_scuola"),
                        "F stessa scuola, ESCS ind. + classe": (["quota10", "escs", "escs_classe"], "id_scuola"),
                    }
                    for nome, (xs, fe) in specs.items():
                        if geo == "Lombardia" and nome.startswith("A2"):
                            continue
                        r = wls_cl(s, "punteggio", xs, fe)
                        b = r["b"][0]
                        sec, ses = r["se_id_classe"][0], r["se_id_scuola"][0]
                        Gs = r["G_id_scuola"]
                        t = tq(Gs - 1)
                        righe.append(dict(grado=grado, materia=mat, area=geo, gruppo=gruppo, modello=nome, n_studenti=r["n"],
                                          n_classi=r["G_id_classe"], n_scuole=Gs, coef_per_10pp=round(b, 2),
                                          se_classe=round(sec, 2), se_scuola=round(ses, 2),
                                          ci95_basso=round(b - t * ses, 2), ci95_alto=round(b + t * ses, 2)))
                        if nome.startswith("C "):
                            rn = wls_cl(s, "punteggio", xs, fe, pesi=False)
                            righe.append(dict(grado=grado, materia=mat, area=geo, gruppo=gruppo, modello="C senza pesi", n_studenti=rn["n"],
                                              n_classi=rn["G_id_classe"], n_scuole=rn["G_id_scuola"], coef_per_10pp=round(rn["b"][0], 2),
                                              se_classe=round(rn["se_id_classe"][0], 2), se_scuola=round(rn["se_id_scuola"][0], 2),
                                              ci95_basso=round(rn["b"][0] - tq(rn["G_id_scuola"] - 1) * rn["se_id_scuola"][0], 2),
                                              ci95_alto=round(rn["b"][0] + tq(rn["G_id_scuola"] - 1) * rn["se_id_scuola"][0], 2)))
    return pd.DataFrame(righe)


def fasce(d):
    righe = []
    for grado in (5, 8):
        for mat in ("ita", "mat"):
            for geo, f in GEO.items():
                if geo == "Italia":
                    continue
                base = d[(d.grado == grado) & (d.materia == mat) & f(d) & d.quota_ok].copy()
                for gruppo, ori in (("nativi", [1]), ("stranieri", [2, 3])):
                    s = base[base.origine.isin(ori)].copy()
                    ya = dummies(s, "anno")
                    ra = dummies(s, "cod_reg") if geo != "Lombardia" else []
                    pres = [b for b in BINL if (s.bin == b).any()]
                    rif = "10-20%"
                    bn = []
                    for b in pres:
                        if b == rif:
                            continue
                        n = "_b_" + b
                        s[n] = (s.bin == b).astype(float)
                        bn.append(n)
                    rg = wls_cl(s, "punteggio", bn + ya, None)
                    ra1 = wls_cl(s, "punteggio", bn + ["escs"] + ya + ra, None)
                    ra2 = wls_cl(s, "punteggio", bn + ["escs", "escs_classe"] + ya + ra, None)
                    for b in pres:
                        q = s[s.bin == b]
                        riga = dict(grado=grado, materia=mat, area=geo, gruppo=gruppo, fascia=b, n_studenti=len(q),
                                    n_classi=q.id_classe.nunique(), n_scuole=q.id_scuola.nunique(),
                                    media_pesata=round(np.average(q.punteggio, weights=q.peso), 1),
                                    escs_medio=round(np.average(q.escs.fillna(q.escs.mean()), weights=q.peso), 2))
                        if b == rif:
                            riga.update(diff_grezza=0.0, se_grezza=0.0, diff_escs_ind=0.0, se_escs_ind=0.0, diff_escs_ind_classe=0.0, se_escs_ind_classe=0.0)
                        else:
                            i = bn.index("_b_" + b)
                            riga.update(diff_grezza=round(rg["b"][i], 1), se_grezza=round(rg["se_id_scuola"][i], 1),
                                        diff_escs_ind=round(ra1["b"][i], 1), se_escs_ind=round(ra1["se_id_scuola"][i], 1),
                                        diff_escs_ind_classe=round(ra2["b"][i], 1), se_escs_ind_classe=round(ra2["se_id_scuola"][i], 1))
                        righe.append(riga)
    return pd.DataFrame(righe)


def descrittivi(d, conta):
    print("=== CONTROLLI")
    for g in (5, 8):
        for a in ANNI[g]:
            for m in ("ita", "mat"):
                q = d[(d.grado == g) & (d.anno == a) & (d.materia == m)]
                print(f"G{g} {a} {m}: righe {len(q)}, scuole {q.id_scuola.nunique()}, classi {q.id_classe.nunique()}, "
                      f"media pesata {np.average(q.punteggio.dropna(), weights=q.peso[q.punteggio.notna()]):.1f}, "
                      f"somma pesi {q.peso.sum():.0f}, ESCS mancante {q.escs.isna().mean():.3f}, "
                      f"origine manc. {(~q.origine.isin([1,2,3])).mean():.3f}, Lomb. classi {q[q.cod_reg==4].id_classe.nunique()} scuole {q[q.cod_reg==4].id_scuola.nunique()}")
    # stesso studente nelle due prove: origine e quota coerenti?
    x = d[d.materia == "ita"].merge(d[d.materia == "mat"], on=["id_classe", "studente"], suffixes=("_i", "_m"))
    print("studenti nelle due prove:", len(x), "| origine uguale:", (x.origine_i == x.origine_m).mean(), "| escs uguale:",
          np.isclose(x.escs_i.fillna(-99), x.escs_m.fillna(-99)).mean(), "| corr punteggi:", round(x.punteggio_i.corr(x.punteggio_m), 3))
    print("definizione origine (genitori nati all'estero, luogo studente):")
    u = d.drop_duplicates(["id_classe", "studente"])
    u = u.assign(genit=((u.luogo_padre.isin([2, 3, 4])).astype(int) + (u.luogo_madre.isin([2, 3, 4])).astype(int)), estero=u.luogo.isin([2, 3, 4]))
    print(pd.crosstab(u.origine, [u.genit, u.estero]).to_string())
    print("ESCS mancante per origine:", u.groupby("origine").escs.apply(lambda s: round(s.isna().mean(), 3)).to_dict())
    print("Classi con quota origine mancante >25% o meno di 10 noti:", (~conta.ok).sum(), "su", len(conta))
    print()
    print("=== CHI SONO GLI ALUNNI, per area e grado (pesi studente, tutti gli anni, una prova: italiano)")
    for g in (5, 8):
        for geo, f in GEO.items():
            q = d[(d.grado == g) & (d.materia == "ita") & f(d) & d.origine.isin([1, 2, 3])]
            q2 = d[(d.grado == g) & (d.materia == "mat") & f(d) & d.origine.isin([1, 2, 3])]
            uu = q.drop_duplicates("id_classe")
            pc = uu.groupby("id_classe").quota.first()
            ss = []
            for o, nome in ((1, "nativi"), (2, "I gen."), (3, "II gen.")):
                k, k2 = q[q.origine == o], q2[q2.origine == o]
                ss.append(f"{nome}: quota {k.peso.sum()/q.peso.sum()*100:.1f}%, ITA {np.average(k.punteggio, weights=k.peso):.1f}, MAT {np.average(k2.punteggio, weights=k2.peso):.1f}, ESCS {np.average(k.escs.fillna(k.escs.mean()), weights=k.peso):.2f}")
            wq = q.drop_duplicates("id_classe")
            print(f"G{g} {geo}: studenti {len(q)}, classi {uu.shape[0]}, scuole {q.id_scuola.nunique()} | " + " | ".join(ss))
            print(f"   quota in classe: mediana {pc.median()*100:.1f}%, p10 {pc.quantile(.1)*100:.1f}, p90 {pc.quantile(.9)*100:.1f}, oltre 30%: {(pc>.3).sum()} classi, oltre 50%: {(pc>.5).sum()} classi")
    print()
    print("=== SPIEGARE LA QUOTA: chi sta nelle classi con piu' stranieri (correlazioni a livello di classe, Lombardia e Nord)")
    for g in (5, 8):
        for geo in ("Lombardia", "Nord"):
            q = d[(d.grado == g) & (d.materia == "ita") & GEO[geo](d) & d.quota_ok]
            nat = q[q.origine == 1].groupby("id_classe").agg(escs_nat=("escs", "mean"), p=("punteggio", "mean"))
            cl = q.groupby("id_classe").agg(quota=("quota", "first"), escs_classe=("escs_classe", "first")).join(nat)
            print(f"G{g} {geo}: corr(quota, ESCS classe) {cl.quota.corr(cl.escs_classe):+.2f}; corr(quota, ESCS dei soli nativi) {cl.quota.corr(cl.escs_nat):+.2f}; corr(quota, punteggio dei nativi) {cl.quota.corr(cl.p):+.2f}; classi {len(cl)}")
    print()
    print("=== VARIAZIONE DENTRO LA SCUOLA: differenza di quota tra le due classi della stessa scuola")
    for g in (5, 8):
        for geo in ("Lombardia", "Nord"):
            q = d[(d.grado == g) & GEO[geo](d) & d.quota_ok].drop_duplicates("id_classe")
            z = q.groupby("id_scuola").quota.agg(["max", "min", "count"])
            z = z[z["count"] == 2]
            dd = (z["max"] - z["min"]) * 100
            print(f"G{g} {geo}: scuole con 2 classi {len(z)}, scarto mediano {dd.median():.1f} punti, p90 {dd.quantile(.9):.1f}")


def main():
    d, conta = tutto()
    conta["ok"] = (conta.noti >= 10) & (conta.quota_mancante <= 0.25)
    d = d.merge(conta[["id_classe", "ok"]], on="id_classe", how="left")
    d["quota_ok"] = d.ok
    d = d[d.punteggio.notna() & d.peso.notna()]
    descrittivi(d, conta)
    m = modelli(d)
    f = fasce(d)
    m.to_csv(os.path.join(OUT, "invalsi_stranieri_modelli.csv"), index=False, sep=";", encoding="utf-8-sig")
    f.to_csv(os.path.join(OUT, "invalsi_stranieri_fasce.csv"), index=False, sep=";", encoding="utf-8-sig")
    pd.set_option("display.width", 220, "display.max_rows", 500, "display.max_columns", 30)
    print()
    print("=== MODELLI: nativi e stranieri, punti per +10 punti percentuali di compagni stranieri")
    print(m[(m.gruppo.isin(["nativi", "stranieri"])) & (m.area != "Italia")].to_string(index=False))
    print()
    print("=== ITALIA, solo A, A2, C, F")
    print(m[(m.area == "Italia") & (m.modello.str[:2].isin(["A ", "A2", "C ", "F "]))].to_string(index=False))
    print()
    print("=== I E II GENERAZIONE, modelli C e F")
    print(m[(m.gruppo.isin(["I gen.", "II gen."])) & (m.modello.str[:2].isin(["A ", "C ", "F "]))].to_string(index=False))
    print()
    print("=== FASCE (rif. 10-20%)")
    print(f.to_string(index=False))


if __name__ == "__main__":
    main()
