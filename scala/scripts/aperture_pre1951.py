"""Ricostruisce le aperture di stagione prima del 1951 (1778/79 ... 1950/51) incrociando:
 WP = lista 'Prime stagionali' (it.wikipedia), WD = Wikidata 'serata inaugurale', SL = cronistoria 'Stagioni liriche' (it.wikipedia),
 e le fonti primarie indipendenti: CA = Cambiasi 1881, RO = Romani 1862, MA = Marangoni-Vanbianchi 1922 (1906-1920), GA = Gatti vol. I (solo fatti).
Uscita: pulito/_aperture_pre1951_incroci.csv (una riga per stagione, con le liste dei candidati e il verdetto).
Uso (dalla cartella scala/): python -I -X utf8 scripts/aperture_pre1951.py"""
import sys, os, re, json, glob
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aperture_lib import kt, sim
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = lambda *a: os.path.join(ROOT, *a)
wp = pd.read_csv(P("pulito", "_aperture_wp_lista.csv")).fillna("")
cam = pd.read_csv(P("pulito", "_cambiasi_pulito.csv")).fillna("")
rom = pd.read_csv(P("pulito", "_romani_opere.csv")).fillna("")
sl = pd.read_csv(P("pulito", "_wp_stagioni.csv")).fillna("")
mar = pd.read_csv(P("pulito", "_marangoni_opere.csv")).fillna("")
gat = pd.read_csv(P("pulito", "gatti_vol1_citazioni.csv")).fillna("")
# Wikidata
wd_rows = json.load(open(P("raw", "wikidata", "premiere_p276_event.json"), encoding="utf8"))["results"]["bindings"]
wd = {}
for r in wd_rows:
    inst = r.get("instLabel", {}).get("value", ""); desc = r.get("itemDescription", {}).get("value", "")
    if "inaugurale" in inst or "inaugurale" in desc:
        q = r["item"]["value"].split("/")[-1]
        wd[q] = (r.get("date", {}).get("value", "")[:10], r["itemLabel"]["value"], desc)
wd_list = sorted(wd.values())

def season_start(lbl):
    m = re.search(r"(\d{4})/", lbl); return int(m.group(1)) if m else None
def first_match(rows, title, key="titolo"):
    for i, (_, r) in enumerate(rows.iterrows()):
        if sim(r[key], title) >= 0.8: return i + 1
    return 0
out = []
for _, w in wp.iterrows():
    Y = season_start(w.stagione)
    if Y is None or Y > 1950: continue
    title = w.titolo_grezzo
    closed = bool(re.search(r"rimase chiuso|Nessuna attività|chiuso", title + w.testo_pulito))
    row = dict(anno=Y, stagione=f"{Y}/{str(Y+1)[2:]}" if Y != 1899 else "1899/00", wp_titolo=title, wp_testo=w.testo_pulito[:160], chiuso=int(closed))
    # Wikidata
    cands = [x for x in wd_list if f"{Y}-07-01" <= x[0] <= f"{Y+1}-06-30" and (x[1].startswith("serata") or sim(x[1], title) >= 0.6 or True)]
    row["wd"] = " | ".join(f"{d} {l}" for d, l, _ in cands)
    # Stagioni liriche: prima riga con 'Carnevale' e data nella finestra dicembre Y
    s = sl[(sl.stagione.str.contains("Carnevale|autunnale", case=False)) & (sl.data.astype(str).between(f"{Y}-07-01", f"{Y+1}-06-30"))]
    row["sl"] = " | ".join(f"{r.data} {r.titolo}" for _, r in s.head(2).iterrows())
    # Cambiasi: Carnevale Y+1 (o Autunno 1778)
    if Y == 1778:
        cc = cam[(cam.anno == 1778) & (cam.stagione_nome == "Autunno")]
    else:
        cc = cam[(cam.anno == Y + 1) & (cam.stagione_nome == "Carnevale") & (cam.genere.astype(str).str.contains("opera|"))]
        cc = cc[~cc.genere.astype(str).str.contains("ballo")]
    row["cam_primo"] = cc.iloc[0].titolo if len(cc) else ""
    row["cam_primo_data"] = cc.iloc[0].data if len(cc) else ""
    row["cam_n"] = len(cc)
    row["cam_pos"] = first_match(cc, title) if (len(cc) and not closed) else 0
    # Romani: sezioni Carnevale* dell'anno Y+1 (e Y per sicurezza)
    rr = rom[(rom.anno == Y + 1) & (rom.stagione_nome.str.contains("Carnevale", case=False))] if Y != 1778 else rom[(rom.anno == 1778)]
    row["rom_primo"] = rr.iloc[0].titolo if len(rr) else ""
    row["rom_n"] = len(rr)
    row["rom_pos"] = first_match(rr, title) if (len(rr) and not closed) else 0
    # Marangoni
    mm = mar[(mar.anno.between(Y, Y + 1)) & (mar.stagione_nome.str.contains("Carnevale"))]
    row["mar_pos"] = first_match(mm, title) if len(mm) and not closed else 0
    row["mar_primo"] = mm.iloc[0].titolo if len(mm) else ""
    # Gatti
    gg = gat[(gat.anno.astype(str).str[:4].isin([str(Y), str(Y + 1)])) & (gat.segnale_spettacolo == "si")]
    row["gat_cita"] = int(any(sim(t, title) >= 0.85 for t in gg.titolo)) if not closed else 0
    out.append(row)
df = pd.DataFrame(out)
df.to_csv(P("pulito", "_aperture_pre1951_incroci.csv"), index=False, encoding="utf-8-sig")
print(len(df), "stagioni")
ind = ((df.cam_pos > 0).astype(int) + (df.rom_pos > 0).astype(int) + (df.mar_pos > 0).astype(int) + df.gat_cita)
print("con almeno una fonte indipendente:", int((ind > 0).sum()), "; con 2+:", int((ind > 1).sum()), "; primo in Cambiasi:", int((df.cam_pos == 1).sum()), "; in Cambiasi:", int((df.cam_pos > 0).sum()), "; in Romani:", int((df.rom_pos > 0).sum()))
