# -*- coding: utf-8 -*-
"""Fotografia a 375 px della bozza (Edge, scala 2). Se piu' alta di 7600 px si divide in parti."""
import os, sys
from playwright.sync_api import sync_playwright

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(os.path.dirname(QUI))
HTML = os.path.join(RADICE, "bozze-grafici", "vie-storiche.html")
OUT = os.path.join(RADICE, "bozze-grafici", "screen")
MAXH = 7600

with sync_playwright() as p:
    b = p.chromium.launch(channel="msedge")
    pg = b.new_context(viewport={"width": 375, "height": 800}, device_scale_factor=2).new_page()
    errori = []
    pg.on("pageerror", lambda e: errori.append(str(e)))
    pg.goto("file:///" + HTML.replace("\\", "/"))
    pg.wait_for_timeout(500)
    larg = pg.evaluate("document.documentElement.scrollWidth")
    alt = pg.evaluate("document.documentElement.scrollHeight")
    print("larghezza scroll", larg, "altezza", alt, "errori", errori)
    base = os.path.join(OUT, "vie-storiche")
    if alt <= MAXH:
        pg.screenshot(path=base + ".png", full_page=True)
    else:
        n = -(-alt // MAXH)
        h = -(-alt // n)
        for i in range(n):
            pg.screenshot(path="%s-%d.png" % (base, i + 1), full_page=True, clip={"x": 0, "y": i * h, "width": 375, "height": min(h, alt - i * h)})
    b.close()
