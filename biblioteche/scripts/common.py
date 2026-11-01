"""Funzioni comuni (nomi biblioteche, lettura csv, normalizzazione titoli/autori)."""
import re, unicodedata
import pandas as pd

def rd(p, **kw):
    """CSV con ; : prova utf-8 (con BOM), poi cp1252. Nessuna correzione dei valori."""
    for enc in ("utf-8-sig", "cp1252"):
        try:
            return pd.read_csv(p, sep=";", encoding=enc, **kw)
        except UnicodeDecodeError:
            continue
    raise ValueError(p)

SPECIAL = {"centrale sormani": "Sormani", "sormani": "Sormani", "biblioteca sormani": "Sormani",
           "dergano bovisa": "Dergano", "parco": "Parco Sempione", "parco sempione": "Parco Sempione",
           "valvassori peroni": "Lambrate", "lambrate": "Lambrate"}
def canon(name):
    """Nome canonico della biblioteca (come nell'elenco ds3012, senza 'Biblioteca')."""
    if name is None or (isinstance(name, float) and pd.isna(name)): return None
    s = re.sub(r"\s+", " ", str(name).strip())
    low = s.lower()
    sm = ""
    if low.endswith(" smartlocker"):
        low = low[:-len(" smartlocker")]; sm = " Smartlocker"
    if low.startswith("biblioteca "): low = low[len("biblioteca "):]
    if low.startswith("bibliobus"): return "Bibliobus"
    if low in SPECIAL: return SPECIAL[low] + sm
    return low.title().replace("'S", "'s").replace("Sant'Ambrogio", "Sant'Ambrogio") + sm

def kind_of(tipo_ds3012=None, name=""):
    n = str(name).lower()
    if "smartlocker" in n or tipo_ds3012 == "Smartlocker": return "smartlocker"
    if n.startswith("bibliobus"): return "bibliobus"
    if n.startswith("edicola") or "edicola" in n: return "edicola"
    if n.startswith("libreria") or "libreria" in n: return "libreria"
    if n.startswith("biblioteca") or tipo_ds3012 == "Biblioteca": return "biblioteca"
    return "altro"

def strip_acc(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))

VOL = re.compile(r"^\s*\[?\d+\]?\s*:\s*")
def titolo_chiave(series):
    """(chiave, visualizzato) del titolo: tolta la formula di responsabilita' dopo ' / ', il prefisso di volume, ': romanzo', le quadre."""
    t = series.str.replace("*", "", regex=False).str.split(" / ", n=1, regex=False).str[0].str.strip()
    t = t.str.replace(VOL, "", regex=True)
    t = t.str.replace(r"\s*:\s*\[?(romanzo|racconti|storia|thriller|giallo)\]?\s*$", "", regex=True, case=False)
    t = t.str.replace(r"[\[\]]", "", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
    k = t.str.lower().map(strip_acc).str.replace(r"[^\w?]+", " ", regex=True).str.strip()
    return k, t

def autore_chiave(series):
    a = series.fillna("").str.replace("*", "", regex=False).str.replace(r"<[^>]*>", "", regex=True).str.replace("_", " ", regex=False)
    a = a.str.split(" - ", n=1, regex=False).str[0].str.replace(r"\s+", " ", regex=True).str.strip()
    k = a.str.lower().map(strip_acc).str.replace(r"[^\w?, ]+", "", regex=True).str.replace(r"\s+", " ", regex=True).str.strip()
    return k, a
