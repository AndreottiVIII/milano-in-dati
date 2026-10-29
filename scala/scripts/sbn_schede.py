"""Fase 2: scarica la scheda completa (full.json: note, compositore, biblioteche) dei record tenuti. Riprendibile."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sbn_lib as s, sbn_parse as p
recs, _ = p.load()
ordine = {"produzione": 0, "stagione": 1, "tournee": 2, "concerto": 3}
todo = []
for bid, r in recs.items():
    cls = p.classifica(r); anno, _f = p.anno_di(r)
    if cls in ordine and anno and 1963 <= anno <= 2024:
        todo.append((ordine[cls], anno, bid))
todo.sort()
print("schede da avere:", len(todo), flush=True)
n = 0
for i, (_o, anno, bid) in enumerate(todo):
    d, cached = s.get("full", {"bid": bid})
    if not cached:
        n += 1
        if n % 25 == 0: print(f"{i+1}/{len(todo)} scaricate {n}", flush=True)
print("FINE", flush=True)
