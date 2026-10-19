# -*- coding: utf-8 -*-
"""Smoke test de la nueva categoria Persianas y Cortinas en el sitio publico."""
import sys
import time
from playwright.sync_api import sync_playwright

URL = "http://localhost:8000/public/10-persianas-y-cortinas.html"
URL_EN = "http://localhost:8000/public/en/10-persianas-y-cortinas.html"
HOME = "http://localhost:8000/public/index.html"

resultados = []
errores = []

def check(nombre, ok, detalle=""):
    resultados.append((nombre, ok))
    print(("PASS " if ok else "FAIL ") + nombre + (f" — {detalle}" if detalle else ""))

with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.on("pageerror", lambda e: errores.append(str(e)))

    # 1. Pagina de la categoria
    resp = page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    check("pagina carga (200)", resp.status == 200, f"status {resp.status}")
    nombres = page.eval_on_selector_all(".product-card h3, .product-card .product-name, h3",
        "els => els.map(e => e.innerText)")
    check("7 productos visibles", any("Sheer Elegance" in n for n in nombres) and any("Cellular" in n for n in nombres),
          f"{len(nombres)} titulos")
    imgs_rotas = page.evaluate("""() => Array.from(document.images).filter(i => i.complete && i.naturalWidth === 0 && (i.getAttribute('src')||'').trim() !== '').length""")
    check("sin imagenes rotas (fotos de producto)", imgs_rotas == 0, f"{imgs_rotas} rotas")
    hay_cotizar = page.evaluate("document.body.innerText.toLowerCase().includes('cotizar')")
    check("boton Cotizar presente", hay_cotizar)
    page.screenshot(path="screenshots/check_persianas_categoria.png", full_page=True)

    # 2. Modal cotizar abre con producto
    try:
        page.click(".product-card .btn-cotizar >> nth=0", timeout=5000)
        page.wait_for_timeout(800)
        modal_visible = page.evaluate("document.querySelector('.wa-modal') && document.querySelector('.wa-modal').classList.contains('active') || document.body.innerText.includes('WhatsApp')")
        check("modal Cotizar abre", bool(modal_visible))
        page.keyboard.press("Escape")
        page.evaluate("typeof closeWaModal==='function' && closeWaModal()")
    except Exception as e:
        check("modal Cotizar abre", False, str(e)[:80])
    page.screenshot(path="screenshots/check_persianas_modal.png")

    # 3. Version EN
    resp_en = page.goto(URL_EN, wait_until="domcontentloaded")
    page.wait_for_timeout(2000)
    txt_en = page.inner_text("body")
    check("version EN carga", resp_en.status == 200 and ("Blinds" in txt_en or "Curtains" in txt_en))
    page.screenshot(path="screenshots/check_persianas_en.png")

    # 4. Home: tarjeta de la categoria y menu
    page.goto(HOME, wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    body = page.inner_text("body")
    check("home muestra Persianas y Cortinas", "Persianas y Cortinas" in body)
    check("mega-menu incluye la categoria", page.evaluate(
        "Array.from(document.querySelectorAll('.mega-item, nav a')).some(a => (a.getAttribute('href')||'').includes('10-persianas'))"))
    page.screenshot(path="screenshots/check_persianas_home.png", full_page=False)

    # 5. Imagen del mega-item carga
    img_ok = page.evaluate("""() => {
      const a = Array.from(document.querySelectorAll('.mega-item')).find(a => (a.getAttribute('href')||'').includes('10-persianas'));
      if (!a) return 'no-enlace';
      const img = a.querySelector('img');
      if (!img) return 'no-img';
      return img.complete && img.naturalWidth > 0;
    }""")
    check("imagen mega-item carga", img_ok is True, str(img_ok))
    b.close()

check("0 errores JS", len(errores) == 0, "; ".join(errores[:3]))
fallos = [n for n, ok in resultados if not ok]
print()
print(f"TOTAL: {len(resultados) - len(fallos)}/{len(resultados)} PASS")
sys.exit(1 if fallos else 0)
