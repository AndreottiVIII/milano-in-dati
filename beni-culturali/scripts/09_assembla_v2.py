"""Monta la bozza bozze-grafici/beni-culturali-v2/index.html: CSS del modello (Rifiuti) + extra + corpo + script."""
import os, re
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
S = os.path.join(R, 'beni-culturali', 'scripts')
rif = open(os.path.join(R, 'docs', 'rifiuti', 'index.html'), encoding='utf-8').read()
css = re.search(r'<style>(.*?)</style>', rif, re.S).group(1)
extra = """
/* beni culturali */
.ch svg .halo{paint-order:stroke;stroke:#fff;stroke-width:3.5px;stroke-linejoin:round;font-weight:800}
.ch svg .w2{fill:#fff;font-size:12px}
.ch svg .k2{fill:var(--ink);font-size:12px}
.ch svg.mp{overflow:hidden;background:#fff}
.opz{border:3px solid var(--ink);padding:0 12px 6px;margin:1.6em 0 0}
.opzl{display:block;background:var(--ink);color:#fff;font-weight:800;font-size:1.6rem;line-height:1;padding:10px 12px;margin:0 -12px 12px}
.find{margin:14px 0 0}
.find label{display:block;font-weight:750;margin:0 0 4px}
.find input,.find select{width:100%;font:inherit;font-size:16px;padding:11px 12px;border:2px solid var(--ink);border-radius:0;background:#fff;color:var(--ink)}
.find input:focus,.find select:focus{outline:3px solid var(--mi);outline-offset:1px}
.ris{background:var(--soft);border-left:6px solid var(--ink);padding:10px 12px;margin:10px 0 12px;font-size:.92rem;line-height:1.35}
.ris b.big{font-size:1.25rem;display:block;line-height:1.15;margin-bottom:2px}
.ris p{margin:.45em 0 0}
.stk{display:flex;height:16px;margin:8px 0 4px;background:#fff}
.stk i{display:block;height:100%}
.stl{display:flex;flex-wrap:wrap;gap:2px 12px;font-size:.85rem}
.stl span{white-space:nowrap}
.stl i{display:inline-block;width:11px;height:11px;border-radius:2px;margin-right:5px}
ul.ex,ul.rl{padding-left:1.1em;margin:.3em 0}
ul.ex li,ul.rl li{margin:.5em 0;line-height:1.3}
ul.rl{list-style:none;padding:0}
ul.rl li{border-bottom:1px solid var(--grid);padding-bottom:.5em}
.m{color:var(--mut)}
button{font:inherit;font-weight:700;padding:10px 16px;border:2px solid var(--ink);background:#fff;cursor:pointer;border-radius:0;min-height:44px}
.find select{appearance:auto}
.ch svg text.m,.ch svg .m{fill:var(--mut)}
"""
corpo = open(os.path.join(S, '_pagina_v2_corpo.html'), encoding='utf-8').read()
js = open(os.path.join(S, '_pagina_v2.js'), encoding='utf-8').read()
html = ('<!doctype html>\n<html lang="it"><head><meta charset="utf-8"><link rel="icon" href="data:,"><meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '<title>Milano in dati · I beni culturali di Milano</title>\n<style>' + css + extra + '</style>' + corpo + '\n<script>\n' + js + '</script></body></html>\n')
out = os.path.join(R, 'bozze-grafici', 'beni-culturali-v2')
os.makedirs(out, exist_ok=True)
open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(html)
print(len(html))
