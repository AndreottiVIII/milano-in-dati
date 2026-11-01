"""Costruisce le tabelle annuali dei passeggeri della metropolitana, con la fonte di ogni numero.
Ingressi: pulito/report24_metro_linea_anno.csv (grafico AMAT letto dal vettoriale), pulito/atm_carta_mobilita_numeri.csv,
e valori citati a mano da testi (ogni riga ha 'fonte' e 'dove').
Output: pulito/metro_passeggeri_linea_anno.csv  (anno, linea, passeggeri_mln, metodo, fonte, dove)
        pulito/metro_passeggeri_totale_anno.csv (anno, passeggeri_mln, metodo, fonte, dove)
Uso: python -I -X utf8 10_annuali.py <pulito_dir>"""
import sys, csv, os
P = sys.argv[1]
linea = []
for r in csv.DictReader(open(os.path.join(P, "report24_metro_linea_anno.csv"), encoding="utf-8")):
    linea.append([int(r["anno"]), r["linea"], float(r["passeggeri_mln_letto_da_grafico"]), "letto_da_grafico_vettoriale_+-0.5mln",
                  "AMAT, Report della Mobilita 2024 (3a ed.), PDF cleancitiescampaign.org, scaricato 2026-11-01", "pdf pag. 48 (stampata 94), grafico 'Passeggeri rete metropolitana'"])
# 2025, per linea: citato da Wikipedia che rimanda al Report della Mobilita 2025 di AMAT (non ottenuto)
for l, v in (("M1", 117994445), ("M2", 93538925), ("M3", 76498903), ("M4", 34511170), ("M5", 29863421)):
    linea.append([2025, l, round(v/1e6, 3), "citato_da_fonte_secondaria", "it.wikipedia.org 'Metropolitana di Milano' (CC BY-SA 4.0), che cita AMAT Report della Mobilita 2025 (settembre 2026): NON verificato sul report",
                  "wikitext, tabella Rete, colonna 'Passeggeri anno 2025'"])
linea.sort(key=lambda r: (r[1], r[0]))
w = csv.writer(open(os.path.join(P, "metro_passeggeri_linea_anno.csv"), "w", newline="", encoding="utf-8"))
w.writerow(["anno", "linea", "passeggeri_mln", "metodo", "fonte", "dove"]); w.writerows(linea)
tot = []
IG = "Il Giorno, 21/3/2024, G. Anastasio, 'trasporto pubblico milano dati passeggeri' (cita 'dati di Comune e Atm', documento non indicato)"
for a, v in ((2015, 346.2), (2017, 348.2), (2018, 369.0), (2019, 386.8), (2020, 166.1), (2021, 205.1), (2022, 284.7), (2023, 331.3)):
    tot.append([a, v, "citato_da_stampa", IG, "tabella nel testo"])
tot.append([2018, 369.0, "testo_ufficiale", "ATM, Bilancio consolidato 2018 (PDF atm.it ATM_bilancio_finanziario_interno_web_.pdf)", "pdf pag. 7 (stampata III), lettera agli azionisti: 'In metropolitana i passeggeri sono stati 369 milioni, +21 milioni'"])
tot.append([2024, 341.0, "testo_ufficiale_'oltre'", "AMAT, Report della Mobilita 2024", "pdf pag. 48 (stampata 94): 'oltre 341 milioni di passeggeri all'anno conteggiati dai tornelli'"])
tot.append([2025, 352.406864, "citato_da_fonte_secondaria", "it.wikipedia.org 'Metropolitana di Milano' (che cita AMAT Report 2025, non verificato); la somma delle 5 linee coincide col totale", "infobox 'pass_anno'"])
for r in linea:
    pass
tot.sort(key=lambda r: (r[0], r[2]))
w = csv.writer(open(os.path.join(P, "metro_passeggeri_totale_anno.csv"), "w", newline="", encoding="utf-8"))
w.writerow(["anno", "passeggeri_mln", "metodo", "fonte", "dove"]); w.writerows(tot)
print(len(linea), "righe linea;", len(tot), "righe totale")
