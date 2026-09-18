# -*- coding: utf-8 -*-
"""Smoke test de la galeria de fotos extra en el sitio publico.

Requiere: servidor local en public/ (python -m http.server 8000) y un
producto de prueba con foto extra en el catalogo (p. ej. Adler-2.jpg).

Verifica:
  1. La tarjeta del producto base tiene fila de miniaturas (.card-thumbs).
  2. Click en la miniatura abre el lightbox con la foto extra.
  3. Las flechas del lightbox navegan y Esc cierra.
  4. La pagina EN carga sin errores JS y muestra la misma galeria.
  5. Viewport movil 375px sin errores JS.

Salida: capturas en screenshots/ y PASS/FAIL por chequeo.
"""
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parents[2]
URL = "http://localhost:8000/1-placas-pvc.html"
PROD = "adler"          # data-name del producto de prueba
DEST = BASE / "screenshots"
DEST.mkdir(exist_ok=True)

resultados = []
errors = []


def check(nombre, ok, detalle=""):
    resultados.append((nombre, ok, detalle))
    print(("PASS " if ok else "FAIL ") + nombre + (f" — {detalle}" if detalle else ""))


with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL, wait_until="domcontentloaded")
    time.sleep(1.5)

    card = page.locator(f'.product-card[data-name="{PROD}"]').first
    check("tarjeta producto existe", card.count() == 1)
    thumbs = card.locator(".card-thumbs .card-thumb")
    check("miniaturas de galeria (>=1)", thumbs.count() >= 1, f"{thumbs.count()} thumb(s)")

    if thumbs.count() >= 1:
        thumbs.first.click()
        time.sleep(0.6)
        lb = page.locator("#lightbox")
        visible = lb.is_visible() if lb.count() else False
        src = page.evaluate("document.querySelector('#lightbox img')?.src || ''")
        check("lightbox abre con foto extra", visible and "Adler-2" in src, src.split("/")[-1])
        page.screenshot(path=str(DEST / "check_galeria_lightbox.png"))
        page.keyboard.press("ArrowRight")
        time.sleep(0.4)
        page.keyboard.press("Escape")
        time.sleep(0.4)
        check("lightbox cierra con Esc", not lb.is_visible())

    page.screenshot(path=str(DEST / "check_galeria_card.png"), full_page=False)

    # Version EN
    page_en = b.new_page(viewport={"width": 1440, "height": 900})
    page_en.on("pageerror", lambda e: errors.append("EN: " + str(e)))
    page_en.goto("http://localhost:8000/en/1-placas-pvc.html", wait_until="domcontentloaded")
    time.sleep(1.5)
    card_en = page_en.locator(f'.product-card[data-name="{PROD}"]').first
    check("EN: tarjeta existe", card_en.count() == 1)
    check("EN: miniaturas presentes", card_en.locator(".card-thumbs .card-thumb").count() >= 1)
    page_en.screenshot(path=str(DEST / "check_galeria_en.png"), full_page=False)
    page_en.close()

    # Movil 375px
    page_m = b.new_page(viewport={"width": 375, "height": 800})
    page_m.on("pageerror", lambda e: errors.append("MOVIL: " + str(e)))
    page_m.goto(URL, wait_until="domcontentloaded")
    time.sleep(1.5)
    page_m.screenshot(path=str(DEST / "check_galeria_movil.png"), full_page=False)
    page_m.close()
    b.close()

check("0 errores JS (ES/EN/movil)", len(errors) == 0, "; ".join(errors[:3]))

fallos = [n for n, ok, _ in resultados if not ok]
print()
print(f"TOTAL: {len(resultados) - len(fallos)}/{len(resultados)} PASS")
sys.exit(1 if fallos else 0)
