# -*- coding: utf-8 -*-
"""Prueba real del exportador Excel: hace click, captura la descarga y la inspecciona."""
import sys, time, zipfile, re
from playwright.sync_api import sync_playwright

URL = "http://localhost:8000/admin.html"
DEST = r"C:\Users\Carlos\Desktop\Pagina\capturas de pantalla de inventario"

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
    with page.expect_download(timeout=90000) as dl:
        page.evaluate("invExcel()")
    descarga = dl.value
    ruta = DEST + r"\inventario_prueba.xlsx"
    descarga.save_as(ruta)
    b.close()

print("Descargado:", ruta)
z = zipfile.ZipFile(ruta)
nombres = z.namelist()
hojas = [n for n in nombres if re.match(r"xl/worksheets/sheet\d+\.xml", n)]
imagenes = [n for n in nombres if n.startswith("xl/media/")]
wbxml = z.read("xl/workbook.xml").decode("utf-8", "ignore")
nombres_hojas = re.findall(r'<sheet[^>]*name="([^"]+)"', wbxml)
s1 = z.read("xl/worksheets/sheet1.xml").decode("utf-8", "ignore")
cf = len(re.findall(r"<conditionalFormatting", s1))
autofiltro = "<autoFilter" in s1
pane = "<pane" in s1  # freeze
filas_s1 = len(re.findall(r"<row ", s1))
print(f"Hojas: {nombres_hojas} | condFormatting: {cf} | autofiltro: {autofiltro} | freeze: {pane} | filas hoja1: {filas_s1} | imagenes: {imagenes}")
print("Errores JS:", len(errors))
for e in errors[:5]: print(" -", e[:200])
ok = len(nombres_hojas) == 2 and cf >= 1 and autofiltro and pane and len(imagenes) >= 1 and not errors
sys.exit(0 if ok else 1)
