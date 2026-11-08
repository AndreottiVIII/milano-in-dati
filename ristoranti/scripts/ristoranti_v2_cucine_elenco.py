"""Elenco di tutte le cucine dei ristoranti e fast food di Milano, con quanti locali ha ciascuna.
Parte da docs/ristoranti/data/locali_osm.csv (OpenStreetMap, campo "cuisine"), prende solo
ristoranti e fast food con la cucina indicata, spezza i valori sul punto e virgola e sulla virgola,
e unisce le scritture quasi uguali (per esempio "chinese" e "cinese") sotto un nome italiano.
Un locale con due scritture della stessa cucina conta una volta sola.
Uso: python -I -X utf8 ristoranti/scripts/ristoranti_v2_cucine_elenco.py
Scrive docs/ristoranti/data/cucine_elenco.csv (cucina;n_locali;scritture_osm)."""
import csv, os, re, collections

R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # progetto milano-in-dati
IN = os.path.join(R, 'docs', 'ristoranti', 'data', 'locali_osm.csv')
OUT = os.path.join(R, 'docs', 'ristoranti', 'data', 'cucine_elenco.csv')

IT = {
    'pizza': 'Pizza', 'italian_pizza': 'Pizza', 'pizza:italian': 'Pizza', 'pinz': 'Pizza', 'pinsa': 'Pinsa',
    'italian': 'Italiana', 'italiana': 'Italiana', 'italiana_contaminata': 'Italiana', 'regional': 'Regionale italiana',
    'local': 'Locale', 'milanese': 'Milanese', 'risotto': 'Risotto', 'pasta': 'Pasta', 'napoletana': 'Napoletana',
    'neapolitan': 'Napoletana', 'romana': 'Romana', 'sicilian': 'Siciliana', 'pugliese': 'Pugliese',
    'pugliese_-_siciliana': 'Pugliese', 'sardinian': 'Sarda', 'tuscan': 'Toscana', 'calabrian': 'Calabrese',
    'marchigiana': 'Marchigiana', 'piadina': 'Piadina', 'panzerotti': 'Panzerotti', 'arancini': 'Arancini',
    'pasticciotto': 'Pasticciotto', 'slow_food': 'Slow food', 'organic': 'Biologica',
    'chinese': 'Cinese', 'cinese': 'Cinese', 'chinese_dumplings': 'Ravioli cinesi', 'dumpling': 'Ravioli cinesi',
    'dumplings': 'Ravioli cinesi', 'baozi': 'Baozi', 'dim_sum': 'Dim sum', 'hot_pot': 'Hot pot', 'hotpot': 'Hot pot',
    'sichuan': 'Sichuan', 'chengdu': 'Sichuan', 'shanghai': 'Shanghai', 'hong_kong': 'Hong Kong', 'taiwanese': 'Taiwanese',
    'fried_skewers': 'Spiedini fritti', 'noodle': 'Noodles', 'noodles': 'Noodles', 'bubble_tea': 'Bubble tea',
    'japanese': 'Giapponese', 'sushi': 'Sushi', 'ramen': 'Ramen', 'edamame': 'Edamame',
    'korean': 'Coreana', 'corean': 'Coreana', 'korean_bbq': 'Barbecue coreano',
    'asian': 'Asiatica', 'oriental': 'Orientale', 'thai': 'Tailandese', 'vietnamese': 'Vietnamita',
    'filipino': 'Filippina', 'indian': 'Indiana', 'nepalese': 'Nepalese', 'bangladeshi': 'Bengalese',
    'pakistani': 'Pakistana', 'sri_lankan': 'Dello Sri Lanka', 'srilankan': 'Dello Sri Lanka', 'singalese': 'Dello Sri Lanka',
    'uzbek': 'Uzbeka', 'kyrgyz': 'Kirghiza', 'georgian': 'Georgiana', 'persian': 'Persiana',
    'kebab': 'Kebab', 'lebanese': 'Libanese', 'turkish': 'Turca', 'arab': 'Araba', 'middle_eastern': 'Mediorientale',
    'falafel': 'Falafel', 'shawarma': 'Shawarma', 'pita': 'Pita', 'egyptian': 'Egiziana', 'moroccan': 'Marocchina',
    'marocchina': 'Marocchina', 'african': 'Africana', 'eritrean': 'Eritrea', 'somali': 'Somala',
    'peruvian': 'Peruviana', 'mexican': 'Messicana', 'brazilian': 'Brasiliana', 'argentinian': 'Argentina',
    'ecuadorian': 'Ecuadoriana', 'salvadoran': 'Salvadoregna', 'venezuelan': 'Venezuelana', 'latin_american': 'Latinoamericana',
    'latin': 'Latinoamericana', 'sudamericana': 'Latinoamericana', 'tacos': 'Tacos', 'french_tacos': 'Tacos alla francese',
    'empanada': 'Empanadas', 'american': 'Americana', 'hawaiian': 'Hawaiana', 'poke': 'Poke',
    'burger': 'Hamburger', 'sandwich': 'Panini', 'panini': 'Panini', 'toast': 'Toast', 'hot_dog': 'Hot dog',
    'chicken': 'Pollo', 'wings': 'Ali di pollo', 'steak_house': 'Bistecca', 'steak': 'Bistecca', 'meat': 'Carne',
    'barbecue': 'Barbecue', 'grill': 'Griglia', 'seafood': 'Pesce e frutti di mare', 'fish': 'Pesce e frutti di mare',
    'pesce': 'Pesce e frutti di mare', 'oyster': 'Ostriche', 'caviar': 'Caviale', 'friture': 'Fritture',
    'salad': 'Insalate', 'insalate': 'Insalate', 'healthy': 'Salutare', 'dessert': 'Dolci', 'cake': 'Torte',
    'crepe': 'Crêpe', 'waffle': 'Waffle', 'pancake': 'Pancake', 'granita': 'Granita', 'ice_cream': 'Gelato',
    'açaí': 'Açaí', 'juice': 'Succhi', 'coffee_shop': 'Caffetteria', 'breakfast': 'Colazione', 'brunch': 'Brunch',
    'bakery': 'Panetteria', 'deli': 'Gastronomia', 'aperitivo': 'Aperitivo', 'wine_bar': 'Enoteca', 'pub': 'Pub',
    'birreria': 'Birreria', 'bistro': 'Bistrot', 'tapas': 'Tapas', 'soup': 'Zuppe',
    'mediterranean': 'Mediterranea', 'spanish': 'Spagnola', 'greek': 'Greca', 'french': 'Francese', 'russian': 'Russa',
    'ukrainian': 'Ucraina', 'portuguese': 'Portoghese', 'danish': 'Danese', 'austrian': 'Austriaca', 'bavarian': 'Bavarese',
    'fusion': 'Fusion', 'international': 'Internazionale', 'crossover': 'Fusion',
}

c = collections.Counter(); scritture = collections.defaultdict(collections.Counter); n_loc = 0
for x in csv.DictReader(open(IN, encoding='utf-8-sig'), delimiter=';'):
    if x['tipo'] not in ('restaurant', 'fast_food') or not x['cucina']:
        continue
    n_loc += 1
    etich = set()
    for v in re.split(r'[;,]', x['cucina']):
        t = re.sub(r'\s+', '_', v.strip().lower())
        if not t:
            continue
        if t not in IT:
            raise SystemExit('scrittura senza nome italiano: ' + t)
        etich.add(IT[t]); scritture[IT[t]][t] += 1
    for e in etich:
        c[e] += 1
rows = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))
with open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.writer(f, delimiter=';')
    w.writerow(['cucina', 'n_locali', 'scritture_osm'])
    for k, v in rows:
        w.writerow([k, v, '|'.join(sorted(scritture[k]))])
print(OUT, len(rows), 'cucine,', n_loc, 'locali con cucina indicata')
