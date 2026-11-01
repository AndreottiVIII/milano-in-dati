"""Riepiloghi del filone fondi-quartieri (tabelle pulite + riepilogo.json).
Uso: python -I -X utf8 07_riepilogo.py <fondi-quartieri> <milano-in-dati>
Legge pulito/progetti_perimetro.csv (script 05), raw/opencup/progetti_milano_abitativo.csv (script 06, se c'e'), bilancio-comune/pulito/spesa_missioni.csv.
Scrive pulito/riep_*.csv e pulito/riepilogo.json. Controlli: ogni totale e' ricalcolato in due modi (stampa 'ok'/'!!')."""
import sys, os, json
import pandas as pd

F, P = sys.argv[1], sys.argv[2]
PU = os.path.join(F, "pulito")
d = pd.read_csv(os.path.join(PU, "progetti_perimetro.csv"), sep=";", dtype=str, keep_default_na=False)
for c in ["importo", "pagato", "pagato_pct", "quota_pnrr", "ritardo_giorni", "nucleo"]:
    d[c] = pd.to_numeric(d[c], errors="coerce")
BAD = []


def chk(nome, a, b, tol=1):
    ok = abs(a - b) <= tol
    print(("ok  " if ok else "!!  ") + f"{nome}: {a:,.0f} vs {b:,.0f}")
    if not ok:
        BAD.append(nome)


AMB = {"ERP": "Case popolari (costruzione, ristrutturazione, efficientamento)", "ABIT": "Alloggi per l'emergenza abitativa e servizi per l'abitare",
       "QUART": "Spazi, servizi e opere nei quartieri popolari", "MOB": "Opere di mobilita' della proposta PINQuA ID 94 (fuori dal nucleo)"}
d["ambito_txt"] = d.ambito.map(AMB)
# PNC: importi aggiudicati, non finanziamenti: li tengo fuori dalle somme "finanziato" e li riporto a parte
d["somma_ok"] = (~d.fonte.str.startswith("PNC")).astype(int)
nuc = d[(d.nucleo == 1)]
nuc_s = nuc[nuc.somma_ok == 1]
largo = d[d.somma_ok == 1]


def agg(df, by):
    g = df.groupby(by).agg(progetti=("cup", "size"), finanziato=("importo", "sum"), pagato=("pagato", "sum")).reset_index()
    g["pagato_pct"] = (g.pagato / g.finanziato * 100).round(1)
    return g.sort_values("finanziato", ascending=False)


R = {}
R["totali"] = {"nucleo_progetti": int(len(nuc_s)), "nucleo_finanziato": float(nuc_s.importo.sum()), "nucleo_pagato": float(nuc_s.pagato.sum()),
               "largo_progetti": int(len(largo)), "largo_finanziato": float(largo.importo.sum()), "largo_pagato": float(largo.pagato.sum()),
               "pnc_progetti": int((d.fonte.str.startswith("PNC")).sum()), "pnc_aggiudicato": float(d[d.fonte.str.startswith("PNC")].importo.sum())}
R["totali"]["nucleo_pagato_pct"] = round(100 * R["totali"]["nucleo_pagato"] / R["totali"]["nucleo_finanziato"], 1)
chk("nucleo = somma per programma", nuc_s.importo.sum(), agg(nuc_s, "programma").finanziato.sum())
chk("nucleo = somma per ente", nuc_s.importo.sum(), agg(nuc_s, "tipo_ente").finanziato.sum())
chk("nucleo = somma per ambito", nuc_s.importo.sum(), agg(nuc_s, "ambito").finanziato.sum())

a = agg(nuc_s, ["fonte", "programma"]); a.to_csv(os.path.join(PU, "riep_per_programma.csv"), sep=";", index=False)
b = agg(nuc_s, "tipo_ente"); b.to_csv(os.path.join(PU, "riep_per_ente.csv"), sep=";", index=False)
c = agg(nuc_s, "ambito_txt"); c.to_csv(os.path.join(PU, "riep_per_ambito.csv"), sep=";", index=False)
R["per_programma"] = a.to_dict("records"); R["per_ente"] = b.to_dict("records"); R["per_ambito"] = c.to_dict("records")
# per quartiere (area) : solo progetti localizzati
q = nuc_s[nuc_s.quartiere != ""].copy()
# area = quartiere "di tutti i giorni": Lorenteggio e Giambellino insieme; gli altri col nome del NIL accorciato
ALIAS = {"53": "Lorenteggio-Giambellino", "49": "Lorenteggio-Giambellino", "41": "Gratosoglio", "14": "Niguarda", "57": "San Siro", "60": "Stadio-Ippodromi", "35": "Corvetto",
         "31": "Ponte Lambro", "81": "Bovisasca", "13": "Greco-Segnano", "43": "Tibaldi"}


def area_di(r):
    first = r.nil_id.split(";")[0]
    if first in ALIAS:
        return ALIAS[first]
    return r.nil_nome.split(";")[0].split(" - ")[0].strip()


q["area"] = q.apply(area_di, axis=1)
q["nil_ids_area"] = q.nil_id
nilset = q.groupby("area").nil_id.apply(lambda s: ";".join(sorted(set(";".join(s).split(";")), key=int)))
qa = agg(q, "area")
qa["nil_ids"] = qa.area.map(nilset)
q[["cup", "titolo", "area", "ambito", "importo"]].to_csv(os.path.join(PU, "riep_quartiere_progetti.csv"), sep=";", index=False)
qa.to_csv(os.path.join(PU, "riep_per_quartiere.csv"), sep=";", index=False)
R["per_quartiere"] = qa.to_dict("records")
R["non_localizzati"] = {"progetti": int((nuc_s.quartiere == "").sum()), "finanziato": float(nuc_s[nuc_s.quartiere == ""].importo.sum())}
chk("quartieri + non localizzati = nucleo", qa.finanziato.sum() + R["non_localizzati"]["finanziato"], nuc_s.importo.sum())
met = nuc_s.assign(m=nuc_s.metodo_quartiere.str.split(" \\(").str[0].str.slice(0, 60)).groupby("m").agg(progetti=("cup", "size"), finanziato=("importo", "sum")).reset_index()
met.to_csv(os.path.join(PU, "riep_metodo_quartiere.csv"), sep=";", index=False)
R["metodo_quartiere"] = met.to_dict("records")

# --- avanzamento
pn = d[d.fonte.str.startswith("PNRR")].copy()
pn["pinqua"] = pn.programma.str.contains("PINQuA")
av = {}
for nome, df in (("PINQuA", pn[pn.pinqua]), ("Housing First", pn[pn.programma.str.contains("Housing")]), ("Piani urbani integrati", pn[pn.programma.str.contains("Piani urbani")])):
    dopo = df.fine_prevista_iso > "2026-06-30"
    av[nome] = {"progetti": int(len(df)), "finanziato": float(df.importo.sum()), "pagato": float(df.pagato.sum()), "pagato_pct": round(100 * df.pagato.sum() / df.importo.sum(), 1),
                "quota_pnrr": float(df.quota_pnrr.sum()),
                "fine_entro_30_6_2026": {"progetti": int((~dopo).sum()), "finanziato": float(df[~dopo].importo.sum()), "pagato": float(df[~dopo].pagato.sum())},
                "fine_dopo_30_6_2026": {"progetti": int(dopo.sum()), "finanziato": float(df[dopo].importo.sum()), "pagato": float(df[dopo].pagato.sum())},
                "in_collaudo": int(df.fase.str.startswith("COLLAUDO").sum()), "in_esecuzione": int(df.fase.str.startswith("ESECUZIONE").sum())}
R["avanzamento_pnrr"] = av
pin = pn[pn.pinqua]
R["pinqua_split"] = {"case_popolari_e_abitare": float(pin[pin.ambito == "ERP"].importo.sum()), "altro": float(pin[pin.ambito != "ERP"].importo.sum()), "totale": float(pin.importo.sum()),
                     "case_pct": round(100 * pin[pin.ambito == "ERP"].importo.sum() / pin.importo.sum(), 1)}
chk("PINQuA: ERP + altro = totale", pin[pin.ambito == "ERP"].importo.sum() + pin[pin.ambito != "ERP"].importo.sum(), pin.importo.sum())
# OpenCoesione: conclusi, in corso, ritardi
oc = d[(d.fonte == "OpenCoesione") & (d.nucleo == 1)].copy()
oc["conc"] = oc.stato.isin(["Concluso", "Liquidato"])
R["opencoesione"] = {"progetti": int(len(oc)), "conclusi": int(oc.conc.sum()), "finanziato_conclusi": float(oc[oc.conc].importo.sum()), "finanziato_in_corso": float(oc[~oc.conc].importo.sum()),
                     "pagato_in_corso": float(oc[~oc.conc].pagato.sum()),
                     "ritardo_mediano_giorni": float(oc[oc.conc].ritardo_giorni.median()), "ritardo_medio_giorni": round(float(oc[oc.conc].ritardo_giorni.mean()), 0),
                     "conclusi_con_ritardo_oltre_180g": int((oc[oc.conc].ritardo_giorni > 180).sum()), "conclusi_con_data_effettiva": int(oc[oc.conc].ritardo_giorni.notna().sum()),
                     "in_corso_con_fine_prevista_passata": int(((~oc.conc) & (oc.fine_prevista_iso != "") & (oc.fine_prevista_iso < "2026-06-30")).sum()),
                     "in_corso_con_fine_prevista_passata_importo": float(oc[(~oc.conc) & (oc.fine_prevista_iso != "") & (oc.fine_prevista_iso < "2026-06-30")].importo.sum())}
big = d[d.nucleo == 1].sort_values("importo", ascending=False).head(15)
big[["fonte", "cup", "titolo", "programma", "ambito_txt", "tipo_ente", "ente_attuatore", "quartiere", "importo", "pagato", "pagato_pct", "stato", "fase", "fine_prevista_iso", "misura_importo"]].to_csv(os.path.join(PU, "riep_progetti_maggiori.csv"), sep=";", index=False)
R["progetti_maggiori"] = json.loads(big[["fonte", "cup", "titolo", "programma", "ambito_txt", "tipo_ente", "ente_attuatore", "quartiere", "importo", "pagato", "pagato_pct", "stato", "fase", "fine_prevista_iso"]].to_json(orient="records", force_ascii=False))

# --- bilancio del Comune, missione 8 (assetto del territorio ed edilizia abitativa), programma 2 = ERP
sm = pd.read_csv(os.path.join(P, "bilancio-comune", "pulito", "spesa_missioni.csv"), sep=";")
m8 = sm[(sm.missione == 8) & (sm.programma == 2) & (sm.fase == "consuntivo") & (sm.da_usare == 1) & (sm.anno >= 2015)]
bt = m8.pivot_table(index="anno", columns="titolo", values="importo", aggfunc="sum").fillna(0)
bt.columns = ["titolo_%d" % c for c in bt.columns]
bt = bt.reset_index()
bt.to_csv(os.path.join(PU, "riep_bilancio_missione8_erp.csv"), sep=";", index=False)
R["bilancio_m8_erp"] = bt.to_dict("records")
R["bilancio_m8_erp_capitale_2021_2025"] = float(bt[bt.anno.between(2021, 2025)].titolo_2.sum())

# --- OpenCUP (universo dei CUP 'abitativo' a Milano)
fo = os.path.join(F, "raw", "opencup", "progetti_milano_abitativo.csv")
if os.path.exists(fo):
    o = pd.read_csv(fo, sep=";", dtype=str, keep_default_na=False)
    o["costo"] = pd.to_numeric(o.COSTO_PROGETTO.str.replace(",", "."), errors="coerce")
    o["anno"] = pd.to_numeric(o.ANNO_DECISIONE, errors="coerce")
    o["fin"] = pd.to_numeric(o.FINANZIAMENTO_PROGETTO.str.replace(",", "."), errors="coerce")

    def ent(t):
        u = t.upper()
        if "AZIENDA LOMBARDA EDILIZIA" in u or u.startswith("ALER"):
            return "ALER Milano"
        if u.startswith("MM S.P.A"):
            return "MM spa"
        if u.startswith("COMUNE DI MILANO"):
            return "Comune di Milano"
        if u.startswith("REGIONE LOMBARDIA") or u.startswith("ARIA S.P.A"):
            return "Regione Lombardia (anche ARIA)"
        if u.startswith("CITTA' METROPOLITANA"):
            return "Citta metropolitana di Milano"
        return "altro (non incluso)"

    o["ente"] = o.SOGGETTO_TITOLARE.map(ent)
    pub = o[o.ente != "altro (non incluso)"].copy()
    perim = set(d.cup)
    pub["in_perimetro"] = pub.CUP.isin(perim).astype(int)
    oc_ent = pub.groupby(["ente", "STATO_PROGETTO"]).agg(cup=("CUP", "size"), costo=("costo", "sum")).reset_index()
    oc_ent.to_csv(os.path.join(PU, "riep_opencup_per_ente.csv"), sep=";", index=False)
    top = pub.sort_values("costo", ascending=False).head(12)
    top[["CUP", "DESCRIZIONE_SINTETICA_CUP", "ente", "costo", "fin", "STATO_PROGETTO", "ANNO_DECISIONE", "CATEGORIA_INTERVENTO", "in_perimetro"]].to_csv(os.path.join(PU, "riep_opencup_maggiori.csv"), sep=";", index=False)
    cup_oc_pnrr = set(pd.read_csv(os.path.join(F, "raw", "opencoesione", "oc_milano_tutti.csv"), sep=";", dtype=str, usecols=["CUP"]).CUP) | set(pd.read_csv(os.path.join(F, "raw", "italiadomani", "pnrr_milano_unito.csv"), sep=";", dtype=str, usecols=["CUP"]).CUP)
    a20 = pub[(pub.STATO_PROGETTO == "ATTIVO") & (pub.ANNO_DECISIONE.astype(int) >= 2020)]
    ATT2020 = {"cup": int(a20.CUP.isin(cup_oc_pnrr).sum()), "costo": float(a20[a20.CUP.isin(cup_oc_pnrr)].costo.sum())}
    R["opencup"] = {"cup_abitativo_milano": int(len(o)), "costo_totale": float(o.costo.sum()), "cup_enti_pubblici": int(len(pub)), "costo_enti_pubblici": float(pub.costo.sum()),
                    "per_ente": pub.groupby("ente").agg(cup=("CUP", "size"), costo=("costo", "sum")).reset_index().to_dict("records"),
                    "per_stato": pub.groupby("STATO_PROGETTO").agg(n=("CUP", "size"), costo=("costo", "sum")).reset_index().to_dict("records"),
                    "in_perimetro_cup": int(pub.in_perimetro.sum()), "in_perimetro_costo": float(pub[pub.in_perimetro == 1].costo.sum()),
                    "attivi_dal_2020": {"cup": int(((pub.STATO_PROGETTO == "ATTIVO") & (pub.ANNO_DECISIONE.astype(int) >= 2020)).sum()),
                                        "costo": float(pub[(pub.STATO_PROGETTO == "ATTIVO") & (pub.ANNO_DECISIONE.astype(int) >= 2020)].costo.sum())},
                    "attivi_dal_2020_in_oc_o_pnrr": ATT2020,
                    "top": json.loads(top[["CUP", "DESCRIZIONE_SINTETICA_CUP", "ente", "costo", "STATO_PROGETTO", "ANNO_DECISIONE", "in_perimetro"]].to_json(orient="records", force_ascii=False))}
    o.groupby(["SOTTOSETTORE_INTERVENTO", "CATEGORIA_INTERVENTO"]).agg(n=("CUP", "size"), costo=("costo", "sum")).reset_index().to_csv(os.path.join(PU, "riep_opencup_categorie.csv"), sep=";", index=False)
json.dump(R, open(os.path.join(PU, "riepilogo.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=float)
print(json.dumps({k: R[k] for k in ("totali", "avanzamento_pnrr", "pinqua_split", "opencoesione", "non_localizzati")}, ensure_ascii=False, indent=1, default=float))
print("controlli falliti:", BAD)
