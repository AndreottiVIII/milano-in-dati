"""Dà a ogni pagina il suo HTML "dopo JavaScript" (molte pagine scrivono fonti e limiti con uno script).

Avvia un piccolo server locale sulla cartella docs/ e chiede a Chrome o Edge senza finestra
(--headless --dump-dom) di caricare ogni pagina. I risultati stanno in una cartella di cache.
Se non c'è un browser, o se una pagina non si carica, si usa l'HTML scritto sul disco.
"""
import functools
import http.server
import os
import shutil
import subprocess
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BROWSERS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_browser():
    for b in BROWSERS:
        if os.path.exists(b):
            return b
    return shutil.which("chrome") or shutil.which("msedge") or shutil.which("chromium")


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def _one(browser, port, slug, out, budget_ms):
    prof = tempfile.mkdtemp(prefix="fonti_prof_")
    try:
        r = subprocess.run(
            [browser, "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}",
             f"--virtual-time-budget={budget_ms}", "--dump-dom", f"http://127.0.0.1:{port}/{slug}/"],
            capture_output=True, timeout=120)
        if r.returncode == 0 and len(r.stdout) > 2000:
            out.write_bytes(r.stdout)
            return True
    except Exception:
        pass
    finally:
        shutil.rmtree(prof, ignore_errors=True)
    return False


def render_all(docs: Path, slugs, cache: Path, port=8879, jobs=4, refresh=False, budget_ms=9000):
    """Ritorna {slug: Path al file html da leggere} e l'elenco di quelle ricadute sull'HTML grezzo."""
    cache.mkdir(parents=True, exist_ok=True)
    browser = find_browser()
    result, fallback = {}, []
    todo = []
    for s in slugs:
        f = cache / f"{s}.html"
        if f.exists() and not refresh:
            result[s] = f
        elif browser:
            todo.append(s)
        else:
            result[s] = docs / s / "index.html"
            fallback.append(s)
    if todo:
        handler = functools.partial(_Quiet, directory=str(docs))
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        try:
            def work(s):
                f = cache / f"{s}.html"
                ok = _one(browser, port, s, f, budget_ms) or _one(browser, port, s, f, budget_ms * 2)
                return s, ok, f
            with ThreadPoolExecutor(jobs) as ex:
                for s, ok, f in ex.map(work, todo):
                    if ok:
                        result[s] = f
                    else:
                        result[s] = docs / s / "index.html"
                        fallback.append(s)
        finally:
            srv.shutdown()
            srv.server_close()
    return result, fallback
