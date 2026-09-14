# -*- coding: utf-8 -*-
"""Capturas de verificacion del rediseño de Inventario (header fuera, filtro almacen)."""
import sys, time
from playwright.sync_api import sync_playwright

OUT = r"C:\Users\Carlos\Desktop\Pagina\capturas de pantalla de inventario"
URL = "http://localhost:8000/admin.html"

errors = []
with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(URL, wait_until="domcontentloaded")
    page.fill("#loginUser", "Adis")
    page.fill("#loginPass", "Adisdiseño2026")
    page.press("#loginPass", "Enter")
    page.wait_for_function("document.getElementById('loginView').style.display==='none' || document.getElementById('loginView').classList.contains('hidden') || getComputedStyle(document.getElementById('loginView')).display==='none'", timeout=30000)
    # ir a Inventario
    page.evaluate("typeof showTab==='function' && showTab('inventory')")
    page.wait_for_function("document.getElementById('invTable').children.length>0 && !document.getElementById('invTable').textContent.includes('Cargando')", timeout=60000)
    time.sleep(1.5)
    page.screenshot(path=OUT + r"\inv_fix_1_inicial.png")

    # scroll dentro del cuadro: los titulos deben quedarse ARRIBA, sin tapar filas
    page.evaluate("document.querySelector('.inv-body-scroll').scrollTop = 400")
    time.sleep(0.6)
    page.screenshot(path=OUT + r"\inv_fix_2_scrolleado.png")
    n_total = page.evaluate("document.getElementById('invTable').children.length")

    # filtro almacen Nogales
    opts = page.evaluate("Array.from(document.getElementById('invAlmacen').options).map(o=>[o.value,o.text])")
    print("Opciones almacen:", opts)
    nog = [v for v, t in opts if "nogales" in t.lower()]
    page.select_option("#invAlmacen", nog[0] if nog else opts[1][0])
    time.sleep(1.2)
    n_nog = page.evaluate("document.getElementById('invTable').children.length")
    page.screenshot(path=OUT + r"\inv_fix_3_filtro_nogales.png")

    # otro almacen (Decosonora) para comparar
    dec = [v for v, t in opts if "decosonora" in t.lower()]
    if dec:
        page.select_option("#invAlmacen", dec[0])
        time.sleep(1.2)
        n_dec = page.evaluate("document.getElementById('invTable').children.length")
        page.screenshot(path=OUT + r"\inv_fix_4_filtro_decosonora.png")
    else:
        n_dec = None

    # volver a todos
    page.select_option("#invAlmacen", "")
    time.sleep(1.2)
    n_all = page.evaluate("document.getElementById('invTable').children.length")
    page.screenshot(path=OUT + r"\inv_fix_5_todos.png")

    # altura del cuadro
    h = page.evaluate("Math.round(document.querySelector('.inv-body-scroll').getBoundingClientRect().height)")
    print(f"Filas total={n_total} nogales={n_nog} decosonora={n_dec} todos={n_all} alturaCaja={h}px")
    b.close()

print("Errores JS:", len(errors))
for e in errors[:5]: print(" -", e[:200])
sys.exit(0 if not errors else 1)
