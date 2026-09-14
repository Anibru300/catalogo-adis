# -*- coding: utf-8 -*-
"""Captura del formulario de producto con boton de subida de foto."""
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
    page.wait_for_function("getComputedStyle(document.getElementById('loginView')).display==='none'", timeout=30000)
    page.evaluate("typeof showTab==='function' && showTab('inventory')")
    page.wait_for_function("document.getElementById('invTable').children.length>0 && !document.getElementById('invTable').textContent.includes('Cargando')", timeout=60000)
    time.sleep(1)
    # abrir formulario de edicion del primer producto
    page.evaluate("showProductForm(document.querySelector('#invTable tr').dataset.pid)")
    time.sleep(0.8)
    tiene = page.evaluate("""({
        slots: !!document.getElementById('galSlots'),
        drop: !!document.getElementById('galDrop'),
        multiple: document.getElementById('pFotoFile') && document.getElementById('pFotoFile').multiple,
        compresor: typeof fileToDataURL==='function',
        subir: typeof subirFotosGaleria==='function',
        slotsRender: document.querySelectorAll('#galSlots .gal-slot').length
    })""")
    print("Formulario galeria:", tiene)
    page.evaluate("document.querySelector('#bizForms').scrollIntoView()")
    time.sleep(0.5)
    page.screenshot(path=OUT + r"\inv_fix_6_editar_foto.png")
    # miniaturas en tabla + panel lateral con galeria
    page.evaluate("closeBizForms(); selectProduct(document.querySelector('#invTable tr').dataset.pid)")
    time.sleep(1.2)
    page.evaluate("document.querySelector('.inv-layout').scrollIntoView()")
    time.sleep(0.5)
    page.screenshot(path=OUT + r"\inv_fix_7_tabla_thumbs.png")
    b.close()

print("Errores JS:", len(errors))
for e in errors[:5]: print(" -", e[:200])
sys.exit(0 if not errors else 1)
