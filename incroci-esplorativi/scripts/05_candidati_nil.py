"""Due lavori sulle coppie di quartiere.
1) IPOTESI: elenco chiuso di domande che uno si aspetterebbe, scritte PRIMA di guardare il risultato di ciascuna (BH solo su questo elenco). Le risposte negative contano.
2) CANDIDATI: coppie emerse dallo screening (02), con tutti i controlli di robustezza del modulo robusta.py.
Uscite: out/nil_ipotesi.csv, out/nil_candidati_robustezza.csv, out/nil_approfondimenti.txt"""
import os
import sys
import warnings

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pandas as pd
from scipy import stats

from comune import OUT, bh, rd
from robusta import A, CTRL, FORTI, parz, scheda

# ---------------- 1. ipotesi
IP = [
    ("airbnb_x100", "var_q0_14", "Dove ci sono più Airbnb calano di più i bambini?"),
    ("airbnb_x100", "var_bambini", "Dove ci sono più Airbnb calano di più i residenti in età scolare?"),
    ("airbnb_x100", "var_alunni", "Dove ci sono più Airbnb calano di più gli alunni?"),
    ("airbnb_x100", "var_pop_14_25", "Dove ci sono più Airbnb calano i residenti?"),
    ("airbnb_x100", "var_affitto", "Dove ci sono più Airbnb salgono di più gli affitti?"),
    ("airbnb_crescita", "var_affitto", "Dove crescono di più gli Airbnb salgono di più gli affitti?"),
    ("airbnb_crescita", "var_prezzo", "Dove crescono di più gli Airbnb salgono di più i prezzi?"),
    ("nuove_case_x1000", "var_prezzo", "Dove si costruisce di più i prezzi salgono meno?"),
    ("nuove_case_x1000", "var_affitto", "Dove si costruisce di più gli affitti salgono meno?"),
    ("nuove_case_x1000", "var_alunni", "Dove si costruisce di più crescono gli alunni?"),
    ("alberi_x_kmq", "smr_22_24", "Più alberi per km2, meno mortalità?"),
    ("verde_a_pct", "smr_22_24", "Più verde (stima), meno mortalità?"),
    ("calore", "smr_22_24", "Più calore da satellite, più mortalità?"),
    ("antenne_x_kmq", "smr_22_24", "Più impianti di telefonia, più mortalità?"),
    ("medici_x1000", "smr_22_24", "Più medici di base, meno mortalità?"),
    ("minuti_medico", "smr_22_24", "Medico più lontano, più mortalità?"),
    ("farmacie_x10k", "smr_22_24", "Più farmacie, meno mortalità?"),
    ("incidenti_x1000", "smr_22_24", "Più incidenti, più mortalità?"),
    ("densita_kmq", "eccesso_2020", "Covid 2020: più densità, più eccesso di morti?"),
    ("famiglia_media", "eccesso_2020", "Covid 2020: famiglie più grandi, più eccesso?"),
    ("reddito", "eccesso_2020", "Covid 2020: redditi bassi, più eccesso?"),
    ("c15_ospedali", "eccesso_2020", "Covid 2020: ospedale vicino, meno eccesso?"),
    ("ciclabili_km_x_kmq", "incid_q_bici", "Più ciclabili, più quota di incidenti con bici?"),
    ("c15_metro", "incidenti_x1000", "Metro vicina, meno incidenti per residente?"),
    ("sosta_m2_ab", "incidenti_x1000", "Più sosta su strada, più incidenti per residente?"),
    ("nidi_x1000", "nati_x1000_donne", "Più nidi, più nati?"),
    ("c15_giochi", "nati_x1000_donne", "Aree gioco vicine, più nati?"),
    ("tempo_pieno", "gap_occ_mf", "Più tempo pieno, meno divario di lavoro tra uomini e donne?"),
    ("nidi_x1000", "gap_occ_mf", "Più nidi, meno divario di lavoro tra uomini e donne?"),
    ("paritarie", "reddito", "Più scuole paritarie dove il reddito è alto?"),
    ("associazioni_x10k", "aff_com_2021", "Più associazioni, più affluenza?"),
    ("distanza_biblioteca", "laureati", "Biblioteca lontana, meno laureati?"),
    ("targhe_resist_x10k", "sx_com21", "Più targhe della Resistenza, più voto a sinistra?"),
    ("pietre_politiche", "sx_com21", "Più pietre di deportati politici, più voto a sinistra?"),
    ("botteghe_x10k", "var_prezzo", "Più botteghe storiche, prezzi che salgono di più?"),
    ("botteghe_cessate", "airbnb_x100", "Più botteghe cessate dove ci sono più Airbnb?"),
    ("botteghe_cessate", "var_affitto", "Più botteghe cessate dove gli affitti salgono?"),
    ("var_locali", "airbnb_x100", "I locali crescono dove ci sono più Airbnb?"),
    ("var_locali", "var_q20_34", "I locali crescono dove crescono i giovani?"),
    ("edifici_pre1946", "case_non_occ", "Più palazzi vecchi, più case non occupate?"),
    ("interni_x_edificio", "famiglie_sole", "Palazzi più grandi, più persone sole?"),
    ("aler_x_abitazione", "smr_22_24", "Più case ALER, più mortalità?"),
    ("aler_x_abitazione", "aff_com_2021", "Più case ALER, meno affluenza?"),
    ("var_prezzo", "saldo_italia_20_24", "Prezzi saliti di più, più gente se ne va?"),
    ("var_prezzo", "var_q20_34", "Prezzi saliti di più, meno giovani?"),
    ("var_affitto", "var_q20_34", "Affitti saliti di più, meno giovani?"),
    ("nuovo_suolo", "calore", "Più nuovo suolo consumato, più calore?"),
    ("c15_metro", "var_prezzo", "Metro vicina, prezzi saliti di più?"),
    ("wiki_views_x_kmq", "airbnb_x100", "Luoghi più letti su Wikipedia, più Airbnb?"),
    ("beni_cult_x_kmq", "airbnb_x100", "Più beni culturali, più Airbnb?"),
]
rig = []
for a, b, dom in IP:
    x, y = A[a].values.astype(float), A[b].values.astype(float)
    ctrl = [c for c in CTRL if c not in (a, b)]
    ok = ~np.isnan(x) & ~np.isnan(y)
    r0 = stats.spearmanr(x[ok], y[ok])[0]
    r, p, n, *_ = parz(x, y, ctrl)
    rig.append(dict(domanda=dom, a=a, b=b, n=n, rho_grezzo=r0, rho_parz=p and r, p=p))
H = pd.DataFrame(rig)
H["q"] = bh(H.p.values)
H = H.sort_values("p")
H.to_csv(os.path.join(OUT, "nil_ipotesi.csv"), index=False, encoding="utf-8-sig")
pd.set_option("display.width", 220, "display.max_rows", 300, "display.max_colwidth", 70)
print(H.round(3).to_string())

# ---------------- 2. candidati
C = [
    ("aff_cam_2022", "smr_22_24"), ("aff_com_2021", "smr_22_24"), ("aff_eur_2024", "smr_22_24"), ("aff_cam_2022", "smr_12_19"), ("aff_com_2021", "smr_12_19"), ("aff_cam_2022", "smr_2020"), ("aff_cam_2022", "eccesso_2020"),
    ("laureati", "sx_cam22"), ("reddito", "sx_cam22"), ("laureati", "sx_com21"), ("reddito", "sx_com21"), ("laureati", "dx_cam22"), ("reddito", "dx_cam22"),
    ("var_laureati_91_23", "sx_cam22"), ("laureati_1991", "m5s_cam18"), ("laureati_1991", "var_dx_18_22"),
    ("disocc_2011", "aff_cam_2022"), ("gap_occ_mf", "aff_ref_2025"), ("gap_occ_mf", "aff_com_2021"), ("tasso_occ", "aff_ref_2025"),
    ("famiglia_media", "sx_eur24"), ("famiglie_sole", "sx_cam22"), ("famiglia_media", "destra_cam22"),
    ("airbnb_x100", "gioco_x10k"), ("edifici_pre1946", "gioco_x10k"),
    ("antenne_x1000", "wiki_views_x_kmq"), ("antenne_x1000", "wiki_quota_estero"), ("antenne_x1000", "airbnb_x100"), ("antenne_x_kmq", "residenti_2024"),
    ("edifici_pre1946", "q80"), ("edifici_46_70", "q80"), ("edifici_46_70", "q65"),
    ("q0_14", "c15_medici"), ("famiglia_media", "c15_medici"), ("q0_14", "medici_x1000"), ("var_pop_14_25", "medici_x1000"), ("q65", "medici_x1000"),
    ("edifici_46_70", "opere_x_kmq"), ("edifici_pre1946", "opere_x_kmq"),
    ("var_reddito", "confiscati_x10k"), ("locali_x1000", "confiscati_x10k"), ("airbnb_x100", "confiscati_x10k"),
    ("var_antenne", "var_sx_18_22"), ("incid_q_moto", "var_bambini"), ("airbnb_crescita", "sx_com21"),
    ("sosta_m2_ab", "incidenti_x1000"), ("airbnb_x100", "incidenti_x1000"),
    ("c15_giochi", "sport_comunali_x10k"), ("tasso_occ", "saldo_italia_12_19"), ("tasso_occ", "saldo_italia_20_24"),
    ("cuc_italiana", "wiki_quota_estero"), ("cuc_veg_insalate_poke", "bikemi_x_kmq"), ("artigianato_x1000", "cuc_pizza"),
    ("var_eta_media", "edifici_pre1946"), ("var_q20_34", "edifici_pre1946"),
]
rs = []
for a, b in C:
    if a in A and b in A:
        rs.append(scheda(a, b))
RS = pd.DataFrame(rs)
RS.to_csv(os.path.join(OUT, "nil_candidati_robustezza.csv"), index=False, encoding="utf-8-sig")
cols = ["a", "b", "n", "rho_grezzo", "rho_parz", "ic95_lo", "ic95_hi", "p_msr", "moran_res", "rho_senza5", "rho_loo_min", "rho_loo_max", "rho_entro_municipio", "rho_forti", "rho_mem", "rho_ge7000", "rho_laureati_al_posto_reddito"]
print(RS[cols].round(2).to_string())
print(RS[["a", "b", "x_q1", "x_q3", "effetto_iqr", "y_mediana", "y_terzo_basso", "y_terzo_alto", "nil_influenti"]].round(2).to_string())
