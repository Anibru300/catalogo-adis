# -*- coding: utf-8 -*-
"""Prueba E2E post-redeploy: upload_foto real + save_product con foto_2..4 (sin cambiar datos)."""
import sys, time, json
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = "http://localhost:8000/admin.html"
OUT = r"C:\Users\Carlos\Desktop\Pagina\capturas de pantalla de inventario"
TMP = Path(r"C:\Users\Carlos\Desktop\Pagina\_tmp_foto_prueba.jpg")

# JPEG 300x200 naranja generado con PIL si existe, si no con bytes minimos
def hacer_jpeg():
    try:
        from PIL import Image
        img = Image.new("RGB", (300, 200), (197, 160, 89))
        img.save(TMP, "JPEG", quality=85)
    except Exception:
        # fallback: 1x1 px jpeg
        import base64
        TMP.write_bytes(base64.b64decode(
            "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkK"
            "DA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/2wBDAQMDAwQDBAgEBAgQCAkICBAQEBAQEBAQEBAQ"
            "EBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBD/wAARCAABAAEDASIAAhEBAxEB/8QAHwAA"
            "AQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEG"
            "E1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZ"
            "WmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJ"
            "ytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcI"
            "CQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLR"
            "ChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaH"
            "iImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP0"
            "9fb3+Pn6/9oADAMBAAIRAxEAPwD3+iikozXTYQUUUUAFFFFABRRRQB//2Q=="))

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

    # --- 1) subida REAL de foto al producto HJPVC-101 (sin guardar el producto) ---
    page.evaluate("showProductForm(document.querySelector('#invTable tr').dataset.pid)")
    time.sleep(0.8)
    hacer_jpeg()
    page.set_input_files("#pFotoFile", str(TMP))
    # esperar a que el slot se llene con URL de Drive
    page.wait_for_function(
        "galeriaFotos.some(f=>f && f.indexOf('drive.google.com')>=0)", timeout=60000)
    url_foto = page.evaluate("galeriaFotos.find(f=>f && f.indexOf('drive.google.com')>=0)")
    print("URL foto subida:", url_foto)
    # la miniatura debe ser publicamente accesible
    resp = page.request.get(url_foto)
    print("Thumbnail HTTP:", resp.status, "bytes:", len(resp.body()))
    page.screenshot(path=OUT + r"\post_deploy_1_subida.png")

    # --- 2) re-guardar el MISMO producto con sus datos (extiende hoja a 19 cols) ---
    prod = page.evaluate("(function(){const p=biz.productos.find(x=>x.codigo==='HJPVC-101');return p;})()")
    r = page.evaluate("""async (prod) => {
      const resp = await apiPost({tipo:'save_product', id: prod.id, codigo: prod.codigo, nombre: prod.nombre,
        categoria: prod.categoria||'', subcategoria: prod.subcategoria||'', proveedor: prod.proveedor||'',
        costo: prod.costo||0, precio: prod.precio||0, unidad: prod.unidad||'pieza',
        stock_minimo: prod.stock_minimo||0, moneda: prod.moneda||'MXN', foto: prod.foto||'',
        foto_2:'', foto_3:'', foto_4:'', estado: prod.estado||'activo',
        descripcion: prod.descripcion||'', notas: prod.notas||''});
      return resp;
    }""", prod)
    print("save_product (re-guardado igual):", json.dumps(r, ensure_ascii=False)[:200])

    # --- 3) verificar que GET productos ya trae foto_2..4 ---
    d = page.evaluate("async () => await apiGet('productos')")
    p101 = [p for p in d["productos"] if p.get("codigo") == "HJPVC-101"][0]
    tiene_cols = {k: (k in p101) for k in ["foto", "foto_2", "foto_3", "foto_4"]}
    print("Columnas en GET productos:", tiene_cols, "| foto:", p101.get("foto"))
    page.evaluate("closeBizForms()")
    b.close()

if TMP.exists():
    TMP.unlink()

ok = (resp.status == 200 and "drive.google.com" in url_foto and r.get("ok")
      and all(tiene_cols.values()) and not errors)
print("RESULTADO:", "OK" if ok else "FALLO")
print("Errores JS:", len(errors))
for e in errors[:5]: print(" -", e[:200])
sys.exit(0 if ok else 1)
