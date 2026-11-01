import re, unicodedata
def norm_nome(s):
    """Chiave di confronto: maiuscolo, senza accenti, senza apostrofi, punteggiatura e trattini -> spazio, spazi singoli."""
    s = unicodedata.normalize('NFD', s.upper())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = s.replace("'", '').replace('\u2019', '').replace('`', '')
    s = re.sub(r'[^A-Z ]+', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()
