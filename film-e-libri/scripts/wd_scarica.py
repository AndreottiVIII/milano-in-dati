"""Scarica da Wikidata (CC0) le opere con P840/P915 dentro Milano. Uso: python -I wd_scarica.py <cartella_raw>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wd_lib
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
F = "?w {P} ?pl . ?pl wdt:P131* wd:Q490 ."
Q = {}
for prop, tag in (("wdt:P840", "p840"), ("wdt:P915", "p915")):
    Q[f"luoghi_{tag}"] = f"""SELECT ?w ?pl ?plLabel ?plLabel_en ?coord ?plInst ?plInstLabel ?plP131Label WHERE {{
  ?w {prop} ?pl . ?pl wdt:P131* wd:Q490 .
  OPTIONAL {{ ?pl wdt:P625 ?coord }} OPTIONAL {{ ?pl wdt:P31 ?plInst }} OPTIONAL {{ ?pl wdt:P131 ?plP131 }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en". }} }}"""
UN = "{ ?w wdt:P840 ?pl . ?pl wdt:P131* wd:Q490 } UNION { ?w wdt:P915 ?pl2 . ?pl2 wdt:P131* wd:Q490 }"
Q["opere_base"] = f"""SELECT DISTINCT ?w ?wLabel ?wDescription WHERE {{ {UN}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en". }} }}"""
Q["opere_it_en"] = f"""SELECT DISTINCT ?w ?lit ?len WHERE {{ {UN}
  OPTIONAL {{ ?w rdfs:label ?lit FILTER(lang(?lit)='it') }} OPTIONAL {{ ?w rdfs:label ?len FILTER(lang(?len)='en') }} }}"""
Q["opere_classi"] = f"""SELECT DISTINCT ?w ?c ?cLabel WHERE {{ {UN} ?w wdt:P31 ?c .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en". }} }}"""
Q["opere_anno"] = f"""SELECT ?w (MIN(?d) AS ?data) WHERE {{ {UN} ?w wdt:P577|wdt:P571|wdt:P1191 ?d . }} GROUP BY ?w"""
Q["opere_persone"] = f"""SELECT DISTINCT ?w ?prop ?p ?pLabel WHERE {{ {UN} ?w wdt:P57|wdt:P50|wdt:P58 ?p . BIND(IF(EXISTS{{?w wdt:P57 ?p}},'regia',IF(EXISTS{{?w wdt:P50 ?p}},'autore','sceneggiatura')) AS ?prop)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en". }} }}"""
Q["opere_genere"] = f"""SELECT DISTINCT ?w ?g ?gLabel WHERE {{ {UN} ?w wdt:P136 ?g .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "it,en". }} }}"""
Q["opere_id_e_link"] = f"""SELECT DISTINCT ?w ?imdb ?itwiki ?enwiki WHERE {{ {UN}
  OPTIONAL {{ ?w wdt:P345 ?imdb }}
  OPTIONAL {{ ?itwiki schema:about ?w ; schema:isPartOf <https://it.wikipedia.org/> }}
  OPTIONAL {{ ?enwiki schema:about ?w ; schema:isPartOf <https://en.wikipedia.org/> }} }}"""
for k, q in Q.items():
    wd_lib.sparql(k, q, out)
print("FINE")
