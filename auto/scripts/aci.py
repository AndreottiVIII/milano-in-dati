"""Lettore dei file ACI Autoritratto (parco veicolare e circolante Copert), anni 2019-2025.
Usa solo la libreria standard + il lettore .ods del filone parcheggi. Modulo, non si lancia da solo."""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUTO = os.path.dirname(HERE)
ROOT = os.path.dirname(AUTO)
sys.path.insert(0, os.path.join(ROOT, "parcheggi", "scripts"))
from ods_lettore import fogli  # noqa: E402

ANNI = list(range(2019, 2026))
_cache = {}


def norm(nome):
    """'27_AV_Provincia_cilindrata' e 'AV Provincia cilindrata' -> 'av provincia cilindrata'"""
    n = re.sub(r"^\d+[_ ]+", "", nome.strip())
    return re.sub(r"\s+", " ", n.replace("_", " ")).strip().lower()


def percorso(anno, quale):
    pat = "Parco_veicolare_%d.ods" if quale == "pv" else "Circolante_Copert_%d.ods"
    p = glob.glob(os.path.join(AUTO, "raw", "aci", "x%d" % anno, "**", pat % anno), recursive=True)
    if not p:
        raise FileNotFoundError(pat % anno)
    return p[0]


def fogli_anno(anno, quale, nomi):
    """nomi: lista di nomi normalizzati da caricare. Restituisce {nome_norm: righe}"""
    chiave = (anno, quale)
    if chiave not in _cache:
        _cache[chiave] = {}
    mancanti = [n for n in nomi if n not in _cache[chiave]]
    if mancanti:
        tutti = fogli(percorso(anno, quale))
        for k, v in tutti.items():
            _cache[chiave][norm(k)] = v
    return {n: _cache[chiave].get(n) for n in nomi}


def num(s):
    if s is None:
        return 0
    s = str(s).strip().replace("\xa0", "")
    if s == "":
        return 0
    try:
        return float(s)
    except ValueError:
        return 0


def tabella(righe, n_chiavi, riga_intestazione=None):
    """Trasforma le righe di un foglio in lista di dict. n_chiavi = numero di colonne 'etichetta' a sinistra
    (riempite verso il basso quando vuote). Le intestazioni sono nella prima riga che ha 'tot' o piu' di 3 celle piene
    dopo la riga del titolo."""
    if riga_intestazione is None:
        riga_intestazione = 1
    head = [h.strip() for h in righe[riga_intestazione]]
    out = []
    ultimo = [""] * n_chiavi
    for r in righe[riga_intestazione + 1:]:
        r = list(r) + [""] * (len(head) - len(r))
        for i in range(n_chiavi):
            if r[i].strip():
                ultimo[i] = r[i].strip()
                # un'etichetta nuova a sinistra azzera quelle a destra
                for j in range(i + 1, n_chiavi):
                    if not r[j].strip():
                        ultimo[j] = ""
        d = {head[i]: ultimo[i] for i in range(n_chiavi)}
        # le colonne di etichetta lette in questa riga hanno la precedenza (gia' in ultimo)
        for i in range(n_chiavi, len(head)):
            d[head[i]] = num(r[i])
        out.append(d)
    return head, out
