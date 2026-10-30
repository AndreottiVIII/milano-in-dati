"""Wikidata SPARQL: matches with both Q1543 (AC Milan) and Q631 (Inter) as participants, plus items 'instance of Milan derby' Q862108.
Usage: python -I 04_wikidata.py <out_dir>"""
import sys, json, requests, time
out = sys.argv[1]
UA = {"User-Agent": "MilanoInDati/1.0 (research; davide.caniatti@gmail.com)", "Accept": "application/sparql-results+json"}
Q = {
 "participants": """SELECT ?m ?mLabel ?date ?instLabel WHERE { ?m wdt:P1923 wd:Q1543, wd:Q631 . OPTIONAL{?m wdt:P585 ?date} OPTIONAL{?m wdt:P31 ?inst} SERVICE wikibase:label { bd:serviceParam wikibase:language "en,it". } } ORDER BY ?date""",
 "derby_instances": """SELECT ?m ?mLabel ?date WHERE { ?m wdt:P31/wdt:P279* wd:Q862108 . OPTIONAL{?m wdt:P585 ?date} SERVICE wikibase:label { bd:serviceParam wikibase:language "en,it". } } ORDER BY ?date""",
 "teams_pair": """SELECT ?m ?mLabel ?date ?score WHERE { ?m wdt:P1344 ?x ; wdt:P31 wd:Q16510064 . ?m p:P1923 ?s1 . ?s1 ps:P1923 wd:Q1543 . ?m p:P1923 ?s2 . ?s2 ps:P1923 wd:Q631 . OPTIONAL{?m wdt:P585 ?date} SERVICE wikibase:label { bd:serviceParam wikibase:language "en,it". } }""",
}
for k, q in Q.items():
    r = requests.get("https://query.wikidata.org/sparql", params={"query": q, "format": "json"}, headers=UA, timeout=120)
    print(k, r.status_code, len(r.text))
    open(f"{out}/{k}.json", "w", encoding="utf-8").write(r.text)
    if r.status_code == 200:
        print(len(r.json()["results"]["bindings"]), "rows")
    time.sleep(3)
