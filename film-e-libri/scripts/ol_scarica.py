"""Open Library search API: libri con luogo/soggetto Milano. Uso: python -I ol_scarica.py <raw/openlibrary>"""
import sys, os, json, time, requests
UA = {"User-Agent": "milano-in-dati/0.1 (research; davide.caniatti@gmail.com)"}
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
F = "key,title,author_name,first_publish_year,subject,place,language,edition_count,isbn,lccn,lcc,ddc,cover_i"
QS = {
 "place_milan_italy": 'place:"Milan (Italy)"',
 "subject_milan_italy": 'subject:"Milan (Italy)"',
 "subject_milan_italy_fiction_hdg": 'subject:"Milan (Italy) -- Fiction"',
 "place_milano": 'place:"Milano"',
 "subject_milano": 'subject:"Milano"',
 "place_milan_fiction": 'place:"Milan (Italy)" AND subject:fiction',
 "subject_milano_narrativa": 'subject:"Milano -- Narrativa"',
 "subject_milano_romanzi": 'subject:"Milano -- Romanzi"',
}
for name, q in QS.items():
    p = os.path.join(out, name + ".json")
    if os.path.exists(p): continue
    docs = []; page = 1; total = None
    while True:
        for t in range(5):
            time.sleep(2)
            r = requests.get("https://openlibrary.org/search.json", params={"q": q, "limit": 100, "page": page, "fields": F}, headers=UA, timeout=90)
            if r.status_code in (429, 500, 502, 503, 504): print("HTTP", r.status_code, "backoff", flush=True); time.sleep(30*(t+1)); continue
            r.raise_for_status(); break
        d = r.json(); total = d["numFound"]; docs += d["docs"]
        if len(d["docs"]) == 0 or len(docs) >= total: break
        page += 1
    json.dump({"query": q, "numFound": total, "docs": docs, "data": time.strftime("%Y-%m-%d")}, open(p, "w", encoding="utf8"), ensure_ascii=False)
    print(name, total, len(docs), flush=True)
print("FINE")
