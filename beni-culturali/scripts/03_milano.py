"""Passo 2: dai TSV estratti (passo 1) ricava le schede legate al Comune di Milano e la loro tabella.

uso: python -I 03_milano.py <cartella_tsv> <file_csv_output> <file_conteggi_nazionali_json>

Una scheda e' "di Milano" se vale almeno uno di questi quattro criteri (tutti salvati come colonne vero/falso):
  cov_milano       dc:coverage = "Milano (MI)"  (campo riassuntivo della scheda)
  indirizzo_milano indirizzo del bene (hasCulturalPropertyAddress) con clv:hasCity = City/milano
  loc_attuale_mi   localizzazione fisica attuale (TimeIndexedTypedLocation di tipo CurrentPhysicalLocation)
                   -> Feature -> Address con clv:hasCity = City/milano
  loc_altra_mi     una qualsiasi altra localizzazione (precedente, ritrovamento, ecc.) a Milano
"""
import csv
import json
import os
import sys
from collections import defaultdict, Counter

MILANO_CITY = "City/milano"
CUR = "https://w3id.org/arco/ontology/location/CurrentPhysicalLocation"


def lines(tsvdir):
    for fn in sorted(os.listdir(tsvdir)):
        if not fn.endswith(".tsv"):
            continue
        with open(os.path.join(tsvdir, fn), encoding="utf-8") as f:
            for l in f:
                s, k, o = l.rstrip("\n").split("\t", 2)
                yield s, k, o


def cls(s):
    return s.split("/", 1)[0]


def unq(o):
    """toglie virgolette e lingua da un letterale N-Triples e decodifica gli escape piu' comuni"""
    if o.startswith('"'):
        end = o.rfind('"')
        o = o[1:end]
        if "\\" in o:
            o = (o.replace('\\"', '"').replace("\\n", " ").replace("\\r", " ").replace("\\t", " ")
                 .replace("\\\\", "\\"))
            if "\\u" in o:
                import re
                o = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), o)
    return o


def is_prop(s):
    c = cls(s)
    return not c.startswith("CatalogueRecord") and c not in (
        "Address", "Feature", "City", "Province", "Region", "Agent", "TimeIndexedTypedLocation",
        "CulturalInstituteOrSite", "Geometry", "Coordinates", "CISNameInTime")


def main(tsvdir, out_csv, out_json):
    # ---------- passo A: struttura (indirizzi, localizzazioni) ----------
    addr_city = {}
    feat_addr = defaultdict(set)
    titl_feat = defaultdict(set)
    titl_type = {}
    titl_cis = defaultdict(set)
    titl_site = defaultdict(set)
    prop_titl = defaultdict(set)
    prop_addr = defaultdict(set)
    prop_cis = defaultdict(set)
    cov_mi = set()
    labels = {}  # Address / Feature / City / CIS / Agent -> prima etichetta
    n_props = Counter()
    prop_seen = set()
    for s, k, o in lines(tsvdir):
        if k == "clv_hasCity":
            addr_city[s] = o
        elif k == "clv_hasAddress":
            feat_addr[s].add(o)
        elif k == "atLocation":
            titl_feat[s].add(o)
        elif k == "locType":
            titl_type[s] = o
        elif k == "hasCIS":
            if cls(s) == "TimeIndexedTypedLocation":
                titl_cis[s].add(o)
            else:
                prop_cis[s].add(o)
        elif k == "atSite":
            titl_site[s].add(o.rsplit("/", 1)[-1])
        elif k == "hasTITL":
            prop_titl[s].add(o)
        elif k in ("hasPropAddress", "dct_spatial"):
            prop_addr[s].add(o)
        elif k == "dc_coverage":
            if o == '"Milano (MI)"':
                cov_mi.add(s)
        elif k == "dc_identifier":
            if s not in prop_seen:
                prop_seen.add(s)
                n_props[cls(s)] += 1
        elif k == "label":
            c = cls(s)
            if c in ("Address", "Feature", "City", "CulturalInstituteOrSite"):
                # preferisci l'etichetta piu' corta per gli indirizzi (la piu' specifica) -> prima trovata
                labels.setdefault(s, unq(o))
    print("props nazionali:", len(prop_seen), "indirizzi:", len(addr_city), "milano cov:", len(cov_mi), flush=True)

    mi_addr = {a for a, c in addr_city.items() if c == MILANO_CITY}

    def feat_mi(f):
        return any(a in mi_addr for a in feat_addr.get(f, ()))

    mi_props = {}
    flags = {}
    for p in prop_seen:
        f_cov = p in cov_mi
        f_addr = any(a in mi_addr for a in prop_addr.get(p, ()))
        f_cur = f_oth = False
        for t in prop_titl.get(p, ()):
            if any(feat_mi(f) for f in titl_feat.get(t, ())):
                if titl_type.get(t) == CUR:
                    f_cur = True
                else:
                    f_oth = True
        if f_cov or f_addr or f_cur or f_oth:
            flags[p] = (f_cov, f_addr, f_cur, f_oth)
    print("schede Milano (almeno un criterio):", len(flags), flush=True)

    # ---------- passo B: attributi delle sole schede Milano ----------
    attr = defaultdict(lambda: defaultdict(list))
    rec_of = {}   # CatalogueRecordXX/id -> property
    rec_code = {}
    rec_upd = {}
    coords = {}
    agent_ids = set()
    for s, k, o in lines(tsvdir):
        if k in ("dc_title", "dc_type", "dc_date", "dc_identifier", "dc_source", "dc_subject", "dc_creator",
                 "dc_rights", "pico_material", "pico_author", "uniqueIdentifier", "catCategory",
                 "cataloguingAgency", "dc_coverage"):
            if s in flags:
                attr[s][k].append(o)
                if k == "dc_creator":
                    agent_ids.add(o)
        elif k == "describesProp":
            if o in flags:
                rec_of[s] = o
        elif k == "systemRecordCode":
            rec_code[s] = o
        elif k == "lastUpdateDate":
            rec_upd[s] = o
        elif k in ("lat", "long"):
            coords.setdefault(s, {})[k] = o
        elif k == "label" and cls(s) == "Agent":
            labels.setdefault(s, unq(o))
    agent_by_base = {}
    for k2, v2 in labels.items():
        if k2.startswith("Agent/"):
            agent_by_base.setdefault(k2[:38], v2)
    # scheda per proprieta'
    p_rec = {}
    for r, p in rec_of.items():
        p_rec[p] = r

    cols = ["id", "ambito", "classe_bene", "tipo_scheda", "codice_catalogo", "url_catalogo", "titolo", "tipo_oggetto",
            "soggetto", "autore", "datazione", "materia_tecnica", "categoria_catalogazione", "diritti",
            "copertura_dc", "cov_milano", "indirizzo_milano", "loc_attuale_mi", "loc_altra_mi",
            "indirizzo_bene", "localizzazione_attuale", "altre_localizzazioni", "istituzione", "codice_sito",
            "lat", "long", "ultimo_aggiornamento", "ente_catalogatore"]
    rows = []
    for p, (f_cov, f_addr, f_cur, f_oth) in flags.items():
        a = attr[p]
        rec = p_rec.get(p)
        scheda = ""
        if rec:
            scheda = rec.split("/", 1)[0].replace("CatalogueRecord", "")
        url = next((x for x in a["dc_source"] if x.startswith("http")), "")
        subj = [unq(x) for x in a["dc_subject"] if x.startswith('"')]
        authors = set()
        for c in a["dc_creator"] + a["pico_author"]:
            if c.startswith('"'):
                authors.add(unq(c))
                continue
            lab = labels.get(c) or agent_by_base.get(c[:38])
            if lab:
                authors.add(lab)
        authors = sorted(authors)
        cur_loc, oth_loc, inst, sites = [], [], set(), set()
        for t in prop_titl.get(p, ()):
            tt = titl_type.get(t, "").rsplit("/", 1)[-1]
            places = []
            for f in titl_feat.get(t, ()):
                lab = labels.get(f, f)
                cities = {addr_city.get(x, "") for x in feat_addr.get(f, ())}
                places.append(lab + (" [Milano]" if feat_mi(f) else ""))
            if tt == "CurrentPhysicalLocation":
                cur_loc += places
                for c in titl_cis.get(t, ()):
                    inst.add(labels.get(c, c))
                sites |= titl_site.get(t, set())
            else:
                oth_loc += [f"{tt}: {x}" for x in places]
        for c in prop_cis.get(p, ()):
            inst.add(labels.get(c, c))
        paddr = sorted({labels.get(x, x) + (" [Milano]" if x in mi_addr else "") for x in prop_addr.get(p, ())})
        cr = coords.get(p.split("/", 1)[1] + "-geometry-coordinates", {})
        if not cr:
            for gk in coords:
                if gk.startswith("Coordinates/" + p.split("/", 1)[1] + "-") and "geometry" in gk:
                    cr = coords[gk]
                    break
        rows.append({
            "id": unq(a["uniqueIdentifier"][0]) if a["uniqueIdentifier"] else p.split("/", 1)[1],
            "ambito": "sede_milano" if (f_cov or f_addr or f_cur) else "solo_luogo_collegato",
            "classe_bene": cls(p),
            "tipo_scheda": scheda,
            "codice_catalogo": rec_code.get(rec, "") and unq(rec_code[rec]) if rec else "",
            "url_catalogo": url,
            "titolo": " | ".join(unq(x) for x in a["dc_title"]),
            "tipo_oggetto": " | ".join(unq(x) for x in a["dc_type"]),
            "soggetto": " | ".join(subj),
            "autore": " | ".join(authors),
            "datazione": " | ".join(unq(x) for x in a["dc_date"]),
            "materia_tecnica": " | ".join(unq(x) for x in a["pico_material"]),
            "categoria_catalogazione": " | ".join(x.rsplit("/", 1)[-1] for x in a["catCategory"]),
            "diritti": " | ".join(unq(x) for x in a["dc_rights"]),
            "copertura_dc": " | ".join(unq(x) for x in a["dc_coverage"]),
            "cov_milano": int(f_cov), "indirizzo_milano": int(f_addr),
            "loc_attuale_mi": int(f_cur), "loc_altra_mi": int(f_oth),
            "indirizzo_bene": " | ".join(paddr),
            "localizzazione_attuale": " | ".join(sorted(set(cur_loc))),
            "altre_localizzazioni": " | ".join(sorted(set(oth_loc))),
            "istituzione": " | ".join(sorted(inst)),
            "codice_sito": " | ".join(sorted(sites)),
            "lat": unq(cr.get("lat", "")), "long": unq(cr.get("long", "")),
            "ultimo_aggiornamento": unq(rec_upd.get(rec, "")) if rec else "",
            "ente_catalogatore": " | ".join(x.rsplit("/", 1)[-1] for x in a["cataloguingAgency"]),
        })
    rows.sort(key=lambda r: r["id"])
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    nat = {"proprieta_nazionali_totale": len(prop_seen), "per_classe": dict(n_props.most_common()),
           "indirizzi_con_citta": len(addr_city), "indirizzi_milano": len(mi_addr),
           "schede_milano_almeno_un_criterio": len(flags)}
    json.dump(nat, open(out_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("scritto", out_csv, len(rows), flush=True)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
