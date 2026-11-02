"""Estrae dai PDF del Dipartimento per la giustizia minorile e di comunita' (statistiche sugli
Istituti penali per i minorenni, semestrali/annuali 2020-2025) i numeri dell'IPM di Milano
(Beccaria) e del totale nazionale: ingressi, uscite, presenti a fine periodo, presenza media.

Uso:  python -I -X utf8 ipm.py <percorso assoluto di carceri>
Scrive pulito/ipm_milano.csv (con la pagina del PDF per ogni riga).
Richiede pdftotext (poppler) nel PATH.
"""
import csv, re, subprocess, sys
from pathlib import Path


def a_num(s):
    return int(s.replace(".", ""))


def sezioni(txt):
    """Restituisce [(pagina, luogo, testo_sezione)]. Una pagina = testo tra due \\f."""
    out = []
    pagine = txt.split("\f")
    for i, p in enumerate(pagine, start=1):
        m = re.search(r"Flussi di utenza degli Istituti penali per i minorenni\s*\n\s*(Situazione Nazionale|I\.P\.M\. di [^\n]+?)\s*\n", p)
        if m:
            out.append((i, m.group(1).strip(), p))
    return out


def valori(p, etichetta):
    """Prima riga che inizia con l'etichetta: ultimi tre numeri = totale M, F, MF."""
    for riga in p.splitlines():
        if riga.strip().startswith(etichetta):
            nums = re.findall(r"\d[\d.]*(?:,\d+)?", riga[len(riga) - len(riga.lstrip()) + len(etichetta):])
            if len(nums) >= 3:
                return nums[-3:]
    return None


def main(root):
    root = Path(root)
    out = []
    for f in sorted((root / "raw" / "ipm").glob("*.pdf")):
        tx = root / "raw" / "ipm_txt" / (f.stem + ".txt")
        tx.parent.mkdir(exist_ok=True)
        if not tx.exists():
            subprocess.run(["pdftotext", "-enc", "UTF-8", "-layout", str(f), str(tx)], capture_output=True)
        txt = tx.read_text(encoding="utf8", errors="replace")
        periodo = re.search(r"(anno|primo semestre|1semestre|1sem|semestre)", f.name, re.I)
        # periodo e anno dal testo della prima pagina
        mm = re.search(r"(Anno|Primo semestre|I semestre|1\S* semestre)\s*(\d{4})", txt[:3000], re.I)
        etich = f"{mm.group(1)} {mm.group(2)}" if mm else f.stem
        for pag, luogo, p in sezioni(txt):
            if luogo not in ("Situazione Nazionale", "I.P.M. di Milano"):
                continue
            ing = valori(p, "Totale INGRESSI")
            usc = valori(p, "Totale USCITE")
            pres = valori(p, "Presenti alla fine del periodo")
            # presenza media: nell'ultima riga con tre numeri decimali
            media = None
            for riga in p.splitlines():
                n = re.findall(r"\d+,\d", riga)
                if len(n) >= 3 and "Presenza media" not in riga:
                    media = n[-1]
                    media = n[-3:]
            out.append(dict(file=f.name, periodo=etich, luogo=luogo, pagina_pdf=pag,
                            ingressi_tot=ing[2] if ing else "", uscite_tot=usc[2] if usc else "",
                            presenti_fine_M=pres[0] if pres else "", presenti_fine_F=pres[1] if pres else "",
                            presenti_fine_MF=pres[2] if pres else "",
                            media_giornaliera_MF=media[2] if media else ""))
    with open(root / "pulito" / "ipm_milano.csv", "w", newline="", encoding="utf8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
        w.writeheader()
        w.writerows(out)
    for o in out:
        print(o)


if __name__ == "__main__":
    main(sys.argv[1])
