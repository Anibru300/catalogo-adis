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
    # refrescar sesion (los tokens del cache de Apps Script se evictan bajo carga de pruebas)
    page.evaluate("login()")
    time.sleep(1.5)
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
    prod = page.evaluate("(function(){const pid=document.querySelector('#invTable tr').dataset.pid;return biz.productos.find(x=>String(x.id)===pid);})()")
    print("Producto de prueba:", prod.get("codigo"))
    r = page.evaluate("""async (prod) => {
      const login2 = await apiPost({tipo:'login', usuario:'Adis', clave:'Adisdiseño2026'});
      if (!login2.ok) return {save: login2, cols: null};
      const tok = login2.token;
      const post = (payload) => fetch(CONFIG.API_URL, {method:'POST', headers:{'Content-Type':'text/plain;charset=utf-8'}, body: JSON.stringify({...payload, token: tok})}).then(x=>x.json());
      const resp = await post({tipo:'save_product', id: prod.id, codigo: prod.codigo, nombre: prod.nombre,
        categoria: prod.categoria||'', subcategoria: prod.subcategoria||'', proveedor: prod.proveedor||'',
        costo: prod.costo||0, precio: prod.precio||0, unidad: prod.unidad||'pieza',
        stock_minimo: prod.stock_minimo||0, moneda: prod.moneda||'MXN', foto: prod.foto||'',
        foto_2:'', foto_3:'', foto_4:'', estado: prod.estado||'activo',
        descripcion: prod.descripcion||'', notas: prod.notas||''});
      const g = await (await fetch(CONFIG.API_URL + '?action=productos&token=' + encodeURIComponent(tok))).json();
      const yo = (g.productos||[]).filter(x=>String(x.id)===String(prod.id))[0] || {};
      return {save: resp, cols: {k_foto2:'foto_2' in yo, k_foto3:'foto_3' in yo, k_foto4:'foto_4' in yo}, foto: yo.foto};
    }""", prod)
    print("save_product (re-guardado igual):", json.dumps(r.get("save"), ensure_ascii=False)[:200])
    print("Columnas foto_2..4 presentes:", r.get("cols"), "| foto:", r.get("foto"))
    tiene_cols = {"foto": True, **{k.replace("k_", ""): v for k, v in (r.get("cols") or {}).items()}}
    p101_ok = all((r.get("cols") or {}).values())
    page.evaluate("closeBizForms()")
    b.close()

if TMP.exists():
    TMP.unlink()

ok = (resp.status == 200 and "drive.google.com" in url_foto and r.get("save", {}).get("ok")
      and p101_ok and not errors)
print("RESULTADO:", "OK" if ok else "FALLO")
print("Errores JS:", len(errors))
for e in errors[:5]: print(" -", e[:200])
sys.exit(0 if ok else 1)
