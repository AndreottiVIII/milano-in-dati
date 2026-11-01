"""Controlli di qualita' e inventario delle fonti. Uso: python -I -X utf8 08_controlli.py <statue> <milano-in-dati>
Scrive pulito/controlli.json e pulito/inventario_fonti.csv"""
import sys, os, json, collections, math
import pandas as pd
S, P = sys.argv[1:3]
O = os.path.join(S, "pulito")
d = pd.read_csv(os.path.join(O, "opere.csv"), dtype=str).fillna("")
s = pd.read_csv(os.path.join(O, "soggetti.csv"), dtype=str).fillna("")
st1 = json.load(open(os.path.join(O, "_lavoro/stage1_log.json"), encoding="utf8"))
C = {}
C["righe_opere"] = len(d); C["id_unici"] = d.id.nunique()
C["righe_soggetti"] = len(s)
C["flag"] = collections.Counter(f for x in d.flag for f in x.split(";") if f)
C["flag"] = dict(C["flag"])
yy = d[d["anno posa"] != ""]["anno posa"].astype(int)
C["anno_posa_min_max"] = [int(yy.min()), int(yy.max())]
C["anno_posa_dopo_2026"] = int((yy > 2026).sum())
C["senza_nome"] = int((d.nome == "").sum())
C["nome_che_e_solo_un_QID"] = int(d.nome.str.fullmatch(r"Q\d+").sum())
# stesse coordinate e stesso tipo (possibili doppioni)
dd = d[d.lon != ""]
g = dd.groupby(["lon", "lat", "tipo"]).size()
C["gruppi_stessa_posizione_e_tipo(>=2)"] = int((g >= 2).sum()); C["opere_in_quei_gruppi"] = int(g[g >= 2].sum())
# persone: Q senza etichetta
C["persone_con_etichetta_che_e_un_QID"] = int(s.persona.str.fullmatch(r"Q\d+").sum())
C["persone_genere_nd"] = int((s.genere == "n.d.").sum())
C["persone_senza_professione_wikidata"] = int((s.professioni_wikidata == "").sum())
C["soggetti_trovati_per_nome_da_controllare"] = int((s.come_trovato.str.startswith("ricerca per nome") | s.come_trovato.str.startswith("nome scritto")).sum())
# copertura per fonte
cv = {}
for f, x in d.groupby("fonte"):
    cv[f] = dict(opere=len(x), con_coord=int((x.lon != "").sum()), con_anno=int((x["anno posa"] != "").sum()), con_autore=int((x.autore != "").sum()), con_persona=int(x.soggetto_tipo.isin(["persona reale", "piu' persone reali"]).sum()))
C["copertura_per_fonte"] = cv
tot = len(d)
C["quote_totali"] = {k: round(v / tot, 3) for k, v in dict(coordinate=int((d.lon != "").sum()), anno=int((d["anno posa"] != "").sum()), autore=int((d.autore != "").sum()),
                     persona=int(d.soggetto_tipo.isin(["persona reale", "piu' persone reali"]).sum())).items()}
# sovrapposizione Wikidata/OSM (stima grezza "cattura-ricattura", assume fonti indipendenti: NON lo sono, e' solo un indizio)
t = d[(d.lon != "") & d.collocazione_dedotta.str.startswith("non indicata")]
ov = {}
for nome, tipi in [("statue_busti_monumenti", ["statua", "busto", "monumento"]), ("lapidi_e_targhe", ["lapide o targa"]), ("sculture_e_installazioni", ["scultura o installazione"])]:
    x = t[t.tipo.isin(tipi)]
    w_ = x.fonte.str.contains("wikidata"); o_ = x.fonte.str.contains("osm")
    n1, n2, m = int(w_.sum()), int(o_.sum()), int((w_ & o_).sum())
    ov[nome] = dict(trovate=len(x), in_wikidata=n1, in_osm=n2, in_entrambe=m, stima_grezza_totale=round(n1 * n2 / m) if m else None)
C["sovrapposizione_wikidata_osm"] = ov
# intervalli di Wilson per le quote di donne
def wilson(k, n, z=1.96):
    if n == 0: return None
    p = k / n; den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(c - h, 4), round(c + h, 4)]
R = json.load(open(os.path.join(O, "riepilogo.json"), encoding="utf8"))
W = {}
for k in ["tutte_le_opere", "statue_monumenti_sculture", "statue_monumenti_sculture_spazio_aperto", "solo_statue_e_busti", "lapidi_e_targhe"]:
    v = R["genere"][k]
    kn = v["donne_uniche"] + v["uomini_unici"]
    W[k] = dict(donne=v["donne_uniche"], persone_di_sesso_noto=kn, quota=round(v["donne_uniche"] / kn, 4), intervallo95_wilson=wilson(v["donne_uniche"], kn))
vie = R["confronto_vie"]
W["vie_confronto"] = dict(donne=vie["donne_sicure"], persone=vie["persone_sicure"], quota=round(vie["quota_donne_vie_su_persone"], 4), intervallo95_wilson=wilson(vie["donne_sicure"], vie["persone_sicure"]))
C["quote_donne_con_intervallo"] = W
json.dump(C, open(os.path.join(O, "controlli.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(json.dumps(C, ensure_ascii=False, indent=1))

# ---------- inventario fonti
osm = json.load(open(os.path.join(S, "raw/osm/overpass_statue.json"), encoding="utf8"))
ds599 = pd.read_csv(os.path.join(S, "raw/comune_ds599/ds599.csv"), sep=";", dtype=str).fillna("")
srch = json.load(open(os.path.join(S, "raw/search_all.json"), encoding="utf8"))
inv = [
 dict(fonte="Comune di Milano - catalogo CKAN (dati.comune.milano.it)", cosa=f"ricerca con 24 parole chiave: {len(srch)} dataset trovati, nessuno su statue/monumenti/lapidi/arte pubblica", righe="", licenza="CC-BY / CC0 secondo il dataset", data_scarico="2026-11-01",
      cosa_manca="il Comune non pubblica un elenco di statue, monumenti, lapidi o arte pubblica", file="raw/search_all.json"),
 dict(fonte="Comune di Milano ds599 - schede catalografiche di beni culturali (SIRBeC, Regione Lombardia)", cosa="322 schede: capolavori nei musei (206), collezioni, musei, chiese, palazzi; solo 9 'statua', 10 'scultura', 5 'busto', schede di musei, palazzi e chiese (non monumenti all aperto)",
      righe=len(ds599), licenza="CC0 (campo license_id = cc-zero)", data_scarico="2026-11-01", cosa_manca="non e' arte pubblica: non usato nei conteggi", file="raw/comune_ds599/ds599.csv"),
 dict(fonte="Comune di Milano ds617 (opere nei musei) e ds585 (architetture)", cosa="solo individuati nel catalogo, NON scaricati: opere dentro i musei e architetture, fuori tema", righe="", licenza="CC0", data_scarico="2026-11-01", cosa_manca="", file="raw/search_all.json"),
 dict(fonte="OpenStreetMap via Overpass (historic=memorial|monument, memorial=*, tourism=artwork, historic=wayside_cross)", cosa="memoriali, monumenti, opere d'arte nel Comune di Milano (relazione admin_level 8, Q490)", righe=len(osm["elements"]),
      licenza="ODbL (obbligo di citazione e di stessa licenza per i derivati)", data_scarico=f"2026-11-01 (dati OSM del {osm['osm3s']['timestamp_osm_base']})",
      cosa_manca="solo il 57% ha un nome; soggetto strutturato (subject:wikidata) in 30 elementi su 561; data (start_date) in 69; mappatura volontaria, non completa", file="raw/osm/overpass_statue.json"),
 dict(fonte="Wikidata (SPARQL + wbgetentities)", cosa=f"{st1['wd_qid_trovati_da_sparql']} elementi che sono statua/monumento/memoriale/scultura/targa/arte pubblica in Milano (P131 o rettangolo di coordinate), {st1['wd_tenuti']} tenuti dopo filtro; 2.357+ entita' scaricate (persone, professioni, luoghi)",
      righe=st1["wd_qid_trovati_da_sparql"], licenza="CC0", data_scarico="2026-11-01", cosa_manca="140 opere senza coordinate; pochissimi anni di posa; P180/P547 (soggetto) presente solo in una parte; copertura irregolare (molte voci create per progetti locali)", file="raw/wikidata/"),
 dict(fonte="ICCD - Catalogo generale dei beni culturali (ArCo 2.0), gia' scaricato in ../beni-culturali", cosa=f"{st1['iccd_schede_milano']} schede di Milano; {st1['iccd_schede_dei_tipi_cercati']} dei tipi cercati (statua 465, lapide 107+32+4, gruppo scultoreo 38, busto 37, monumento ai caduti 11...); {st1['iccd_candidati_tenuti']} tenute",
      righe=st1["iccd_schede_milano"], licenza="metadati CC BY 4.0 secondo il catalogo, CC BY-SA 4.0 secondo ArCo/Zenodo (vedi ../beni-culturali/NOTE.md)", data_scarico="2026-10-29 (dump del 2023-12-01)",
      cosa_manca="le coordinate sono quelle del detentore (museo/chiesa): 470 schede senza coordinate, 228 con coordinate di museo; statue quasi tutte dentro Duomo/chiese", file="../beni-culturali/pulito/beni_milano.csv"),
 dict(fonte="Confini dei NIL (Comune di Milano ds964), gia' scaricati in ../citta-15-minuti", cosa="88 poligoni, per assegnare il NIL", righe=88, licenza="CC-BY", data_scarico="gia' presente", cosa_manca="", file="../citta-15-minuti/raw/comune_milano/nil_vigenti/ds964_nil_wm.geojson"),
 dict(fonte="Confronto: donne-nelle-vie/out/percentuali.json", cosa="quota di donne tra le persone a cui sono intitolate le vie (6,6%: 140 su 2.110, santi compresi)", righe=2110, licenza="ODbL/CC0/CC-BY (vedi NOTE di donne-nelle-vie)", data_scarico="2026-10-29", cosa_manca="", file="../donne-nelle-vie/out/percentuali.json"),
]
pd.DataFrame(inv).to_csv(os.path.join(O, "inventario_fonti.csv"), index=False, encoding="utf-8-sig")
print("inventario scritto")
