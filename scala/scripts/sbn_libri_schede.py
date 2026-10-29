"""Scarica schede complete SBN (full.json) per una lista di BID; cache raw/sbn_libri; stampa dati e biblioteche di Milano.
Uso: python -I -X utf8 scripts/sbn_libri_schede.py BID1 BID2 ... (con i backslash, tra virgolette)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbn_lib
sbn_lib.ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "raw", "sbn_libri")
res = {}
for bid in sys.argv[1:]:
    try:
        d, c = sbn_lib.get("full", {"bid": bid})
    except sbn_lib.Blocked as e:
        print("BLOCCO:", e); sys.exit(2)
    locs = d.get("localizzazioni", [])
    mi = [f'{l["shelfmarks"][0]["shelfmark"] if l.get("shelfmarks") else l["denominazione"]}' for l in locs if any("(MI)" in (s.get("invNum") or "") or "Milano" in (s.get("invNum") or "") for s in l.get("shelfmarks", []))]
    print("###", bid, "|", d["titolo"][:140], "|", d.get("pubblicazione"), "|", d.get("descrizioneFisica"), "|", d.get("tipo"))
    print("   note:", [n[:160] for n in d.get("note", [])][:6])
    print("   n.biblioteche:", len(locs), "| Milano:", mi)
    res[bid] = d
