# -*- coding: utf-8 -*-
"""Chequeo rapido de los tabs tocados: Gastos (datalist vacio poblable),
Cobros (formulario otro ingreso) y Configuracion (gestor de categorias)."""
from playwright.sync_api import sync_playwright

errors = []
with sync_playwright() as pw:
    b = pw.chromium.launch()
    page = b.new_page(viewport={"width": 1440, "height": 900})
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto("http://localhost:8000/admin/index.html", wait_until="domcontentloaded")
    page.fill("#loginUser", "Adis")
    page.fill("#loginPass", "Adisdiseño2026")
    page.press("#loginPass", "Enter")
    page.wait_for_function("getComputedStyle(document.getElementById('loginView')).display==='none'", timeout=30000)

    page.evaluate("showTab('expenses')")
    page.wait_for_timeout(1500)
    print("expenses datalist opciones:", page.evaluate("document.querySelectorAll('#gCatList option').length"))
    print("expenses tabla filas:", page.evaluate("document.querySelectorAll('#expTable tr').length"))
    page.screenshot(path="screenshots/check_gastos_categorias.png")

    page.evaluate("showTab('cobros')")
    page.wait_for_timeout(1200)
    print("cobros form otro ingreso:", page.evaluate("!!document.getElementById('ingConcepto')"))
    print("cobros datalist opciones:", page.evaluate("document.querySelectorAll('#ingCatList option').length"))
    page.screenshot(path="screenshots/check_cobros_otro_ingreso.png")

    page.evaluate("showConfigForm()")
    page.wait_for_timeout(800)
    print("config catGastosBox existe:", page.evaluate("!!document.getElementById('catGastosBox')"))
    print("config chips gastos:", page.evaluate("document.querySelectorAll('#catGastosBox span').length"))
    print("config chips ingresos:", page.evaluate("document.querySelectorAll('#catIngresosBox span').length"))
    page.screenshot(path="screenshots/check_config_categorias.png")
    b.close()

print("ERRORES JS:", errors if errors else "ninguno")
