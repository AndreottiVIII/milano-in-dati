"""Passo 1: da ogni parte del dump ArCo 2.0 (N-Triples compressi) estrae solo i triple utili
(dati di sintesi della scheda, luogo, indirizzo, istituzione, autore) e li scrive in un file TSV per parte.

uso: python -I 02_estrai_triple.py <cartella_raw_arco> <cartella_output> [n_processi] [log_download]
Ogni riga di output: soggetto <TAB> predicato_breve <TAB> oggetto
(prefisso https://w3id.org/arco/resource/ tolto; oggetti IRI senza <>, letterali con le virgolette).
Le righe doppie (il dump ne ha molte) vengono tolte dentro ogni parte.
"""
import gzip
import os
import sys
from multiprocessing import Pool

RES = "https://w3id.org/arco/resource/"
ONT = "https://w3id.org/arco/ontology/"
ITA = "https://w3id.org/italia/onto/"
DC = "http://purl.org/dc/elements/1.1/"

PRED = {
    DC + "title": "dc_title",
    DC + "type": "dc_type",
    DC + "date": "dc_date",
    DC + "coverage": "dc_coverage",
    DC + "identifier": "dc_identifier",
    DC + "source": "dc_source",
    DC + "subject": "dc_subject",
    DC + "creator": "dc_creator",
    DC + "rights": "dc_rights",
    "http://purl.org/dc/terms/spatial": "dct_spatial",
    "http://data.cochrane.org/ontologies/pico/materialAndTechnique": "pico_material",
    "http://data.cochrane.org/ontologies/pico/author": "pico_author",
    ONT + "arco/uniqueIdentifier": "uniqueIdentifier",
    ONT + "arco/hasCulturalPropertyCataloguingCategory": "catCategory",
    ONT + "arco/hasCataloguingAgency": "cataloguingAgency",
    ONT + "location/hasCulturalPropertyAddress": "hasPropAddress",
    ONT + "location/hasTimeIndexedTypedLocation": "hasTITL",
    ONT + "location/hasCulturalInstituteOrSite": "hasCIS",
    ONT + "location/hasLocationType": "locType",
    ONT + "location/atLocation": "atLocation",
    ONT + "location/atSite": "atSite",
    ONT + "location/hasCoordinates": "hasCoordinates",
    ONT + "location/lat": "lat",
    ONT + "location/long": "long",
    ONT + "catalogue/describesCulturalProperty": "describesProp",
    ONT + "catalogue/lastUpdateDate": "lastUpdateDate",
    ONT + "catalogue/systemRecordCode": "systemRecordCode",
    ONT + "context-description/hasDating": "hasDating",
    ONT + "context-description/hasAuthorshipAttribution": "hasAuthorship",
    ONT + "context-description/hasAuthor": "hasAuthor",
    ONT + "context-description/hasAttributedAuthor": "hasAttributedAuthor",
    ONT + "context-description/hasPreferredAuthor": "hasPreferredAuthor",
    ITA + "CLV/hasAddress": "clv_hasAddress",
    ITA + "CLV/hasCity": "clv_hasCity",
    ITA + "CLV/hasProvince": "clv_hasProvince",
    ITA + "CLV/hasRegion": "clv_hasRegion",
    ITA + "CLV/fullAddress": "clv_fullAddress",
    ITA + "CLV/hasGeometry": "clv_hasGeometry",
    "http://dati.beniculturali.it/cis/institutionalCISName": "cis_name",
    "http://dati.beniculturali.it/cis/hasCISNameInTime": "cis_hasName",
    "http://dati.beniculturali.it/cis/hasSite": "cis_hasSite",
    "http://dati.beniculturali.it/cis/siteAddress": "cis_siteAddress",
}
TYPE = "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
LABEL = "http://www.w3.org/2000/01/rdf-schema#label"
LABEL_SUBJ = ("/Address/", "/Feature/", "/City/", "/Province/", "/Region/",
              "/CulturalInstituteOrSite/", "/Agent/", "/CulturalPropertyCataloguingCategory/")


def short(x):
    if x.startswith("<"):
        x = x[1:-1]
        if x.startswith(RES):
            x = x[len(RES):]
        return x
    return x.replace("\t", " ")


def process(args):
    path, outdir = args
    name = os.path.basename(path).replace(".nt.gz", ".tsv")
    seen = set()
    n_in = 0
    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            n_in += 1
            parts = line.split(" ", 2)
            if len(parts) < 3:
                continue
            s, p, o = parts
            p = p[1:-1]
            o = o.rstrip()
            if o.endswith(" ."):
                o = o[:-2]
            key = None
            if p in PRED:
                key = PRED[p]
            elif p == TYPE:
                if o.startswith("<" + ONT + "arco/") or o.startswith("<" + ONT + "location/") and "Address" in o:
                    key = "type"
                elif o.startswith("<" + ITA + "CLV/"):
                    key = "type"
            elif p == LABEL:
                if any(t in s for t in LABEL_SUBJ):
                    key = "label"
            if key is None:
                continue
            seen.add((short(s), key, short(o)))
    with open(os.path.join(outdir, name), "w", encoding="utf-8", newline="\n") as out:
        for s, k, o in sorted(seen):
            out.write(f"{s}\t{k}\t{o}\n")
    return name, n_in, len(seen)


if __name__ == "__main__":
    raw, outdir = sys.argv[1], sys.argv[2]
    nproc = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    os.makedirs(outdir, exist_ok=True)
    files = sorted(os.path.join(raw, f) for f in os.listdir(raw) if f.endswith(".nt.gz"))
    if len(sys.argv) > 4:  # log del download: usa solo i file completi (dimensione = attesa)
        ok = set()
        for l in open(sys.argv[4], encoding="utf-8"):
            w = l.split()
            if len(w) >= 5 and w[1].endswith(".nt.gz") and w[2] == w[4]:
                ok.add(w[1])
        files = [f for f in files if os.path.basename(f) in ok]
    done = {f[:-4] for f in os.listdir(outdir) if f.endswith(".tsv")}
    todo = [(f, outdir) for f in files if os.path.basename(f)[:-6] not in done]
    with Pool(nproc) as pool:
        for name, n_in, n_out in pool.imap_unordered(process, todo):
            print(name, n_in, n_out, flush=True)
