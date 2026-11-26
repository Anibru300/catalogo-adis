#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas UI — Kardex por producto (2026-11-25).

Abre public/admin.html con Playwright y BACKEND SIMULADO (page.route):
  1. Clic en producto -> kardex con titulo, filtros (fecha/tipo) y botones CSV/Imprimir
  2. Cantidades con signo coloreado (+ verde entrada / - rojo salida)
  3. Columnas Almacen y Proveedor (Teknostep visible en la entrada por gasto)
  4. Filtro por tipo=entrada/salida
  5. CSV del kardex con encabezados y columna Proveedor
  6. Formulario de gasto: campo Proveedor (gProveedor) llega en el payload
Sin escrituras reales.

Uso: python test_kardex_ui.py
"""
import json, sys, pathlib, threading, functools, http.server, urllib.parse, datetime
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ADMIN = pathlib.Path(__file__).resolve().parents[2] / 'public'
HOY = datetime.date.today().isoformat()
AYER = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
resultados = []
def reg(nombre, ok, detalle=''):
    resultados.append((nombre, ok, detalle))
    print(('  PASS ' if ok else '  FAIL ') + nombre + (' — ' + str(detalle)[:160] if detalle else ''))

# ---------------- backend simulado ----------------
S = {
    'productos': [
        {'id': 'P1', 'codigo': 'LAM-015', 'nombre': 'Lambrín Río', 'categoria': 'Lambrin WPC',
         'costo': 99.57, 'precio': 0, 'moneda': 'MXN', 'estado': 'activo', 'unidad': 'pieza', 'stock_minimo': 0, 'foto': '', 'notas': ''},
        {'id': 'P2', 'codigo': 'HJPVC-1', 'nombre': 'Ágata', 'categoria': 'Placas PVC',
         'costo': 600, 'precio': 900, 'moneda': 'MXN', 'estado': 'activo', 'unidad': 'pieza', 'stock_minimo': 0, 'foto': '', 'notas': ''},
    ],
    'almacenes': [{'id': 'A1', 'nombre': 'Nogales', 'activo': 'si'}, {'id': 'A2', 'nombre': 'Decosonora', 'activo': 'si'}],
    'stock': {'P1|A1': 12},
    'movs': [
        {'fecha': '2026-11-25 21:58', 'tipo': 'entrada', 'producto_id': 'P1', 'producto': 'Lambrín Río',
         'almacen_id': 'A1', 'almacen': 'Nogales', 'cantidad': 14, 'costo_unit': 99.57, 'moneda': 'MXN',
         'referencia': 'Gasto GAS-2026-0060', 'proveedor': 'Teknostep', 'notas': 'Entrada de mercancía · Compra de material Teknostep — Factura 28024799',
         'id': 'MOV-2026-00091', 'usuario': 'Adis', 'existencia_anterior': 0, 'existencia_posterior': 14,
         'documento_tipo': 'GASTO', 'documento_id': 'GAS-2026-0060', 'lote': ''},
        {'fecha': '2026-11-25 22:30', 'tipo': 'salida', 'producto_id': 'P1', 'producto': 'Lambrín Río',
         'almacen_id': 'A1', 'almacen': 'Nogales', 'cantidad': 2, 'costo_unit': '', 'moneda': 'MXN',
         'referencia': 'Traspaso: Nogales → Decosonora', 'proveedor': '', 'notas': 'Traspaso entre almacenes',
         'id': 'MOV-2026-00092', 'usuario': 'Adis', 'existencia_anterior': 14, 'existencia_posterior': 12,
         'documento_tipo': 'TRASPASO', 'documento_id': 'TRA-2026-0002', 'lote': ''},
    ],
    'config': {'moneda_base': 'MXN', 'tipo_cambio': '18.5'},
}
capturas = []

def mock_api(route):
    req = route.request
    if req.method == 'POST':
        body = json.loads(req.post_data or '{}')
        capturas.append(body)
        t = body.get('tipo')
        if t == 'login':
            route.fulfill(content_type='application/json', body=json.dumps({'ok': True, 'token': 'mock'}))
        else:
            route.fulfill(content_type='application/json', body=json.dumps({'ok': True, 'folio': 'GAS-2026-9999', 'id': 'mock'}))
        return
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(req.url).query)
    base = (qs.get('action') or [''])[0].split('&')[0]
    if base == 'productos': data = {'ok': True, 'productos': S['productos']}
    elif base == 'almacenes': data = {'ok': True, 'almacenes': S['almacenes']}
    elif base == 'stock':
        det = [{'producto_id': k.split('|')[0], 'almacen_id': k.split('|')[1], 'cantidad': v, 'producto': '', 'almacen': ''}
               for k, v in S['stock'].items() if v]
        data = {'ok': True, 'stock': det}
    elif base == 'movimientos': data = {'ok': True, 'movimientos': S['movs']}
    elif base == 'proveedores': data = {'ok': True, 'proveedores': [{'id':'V1','nombre':'Teknostep','activo':'si'}]}
    elif base == 'proyectos': data = {'ok': True, 'proyectos': []}
    elif base == 'config': data = {'ok': True, **S['config']}
    elif base == 'gastos': data = {'ok': True, 'gastos': []}
    elif base == 'clientes': data = {'ok': True, 'clientes': []}
    elif base == 'cxp': data = {'ok': True, 'cxp': [], 'pagos': []}
    else: data = {'ok': True, base: []}
    route.fulfill(content_type='application/json', body=json.dumps(data))

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ADMIN))
server = http.server.HTTPServer(('127.0.0.1', 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:%d/admin.html' % server.server_address[1]

errores = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(accept_downloads=True)
    page = ctx.new_page()
    page.route('**//script.google.com/**', mock_api)
    page.on('pageerror', lambda e: errores.append('pageerror: %s' % e))
    page.on('console', lambda m: errores.append('console.error: %s' % m.text) if m.type == 'error' else None)
    page.goto(BASE)
    page.wait_for_timeout(600)
    page.fill('#loginUser', 'Adis')
    page.fill('#loginPass', 'x')
    page.click('#loginView button[type="submit"], #loginView .btn-solid')
    page.wait_for_selector('#appView:not(.hidden)', timeout=10000)
    page.wait_for_timeout(1200)
    page.evaluate('showTab("inventory")')
    page.wait_for_timeout(600)

    # 1. clic en producto -> kardex
    page.click('#invTable tr[data-pid="P1"]')
    page.wait_for_selector('#kTableWrap table', timeout=8000)
    reg('clic en producto abre el kardex', '📒 Kardex: LAM-015 · Lambrín Río' in page.locator('#invKardex').inner_text())
    reg('filtros fecha/tipo + botones CSV/Imprimir', page.locator('#kDesde').count() == 1
        and page.locator('#kTipo').count() == 1 and page.locator('#invKardex button:has-text("CSV")').count() == 1
        and page.locator('#invKardex button:has-text("Imprimir")').count() == 1)

    # 2. signos coloreados
    verdes = page.locator('#kTableWrap td span[style*="3fb96a"]')
    rojos = page.locator('#kTableWrap td span[style*="d96b5f"]')
    reg('entrada muestra +14 en verde', verdes.count() == 1 and '+14' in verdes.first.inner_text())
    reg('salida muestra -2 en rojo', rojos.count() == 1 and '-2' in rojos.first.inner_text())

    # 3. columnas almacen y proveedor
    txt = page.locator('#kTableWrap').inner_text()
    reg('columna Proveedor muestra Teknostep', 'Teknostep' in txt)
    reg('documento 🧾 Gasto GAS-2026-0060 y 🔀 TRA-2026-0002', '🧾 Gasto GAS-2026-0060' in txt and '🔀 TRA-2026-0002' in txt)
    reg('existencias trazadas (0 → 14 y 14 → 12)', '0 → 14' in txt and '14 → 12' in txt)

    # 4. filtro por tipo
    page.select_option('#kTipo', 'entrada')
    page.wait_for_timeout(200)
    reg('filtro tipo=entrada deja solo la entrada', page.locator('#kTableWrap tbody tr').count() == 1
        and 'GAS-2026-0060' in page.locator('#kTableWrap').inner_text())
    page.select_option('#kTipo', '')
    page.wait_for_timeout(200)

    # 5. CSV
    with page.expect_download() as dl_info:
        page.click('#invKardex button:has-text("CSV")')
    tmp = pathlib.Path(__file__).resolve().parent / '_tmp_kardex.csv'
    dl_info.value.save_as(str(tmp))
    contenido = tmp.read_text(encoding='utf-8-sig')
    tmp.unlink()
    reg('CSV kardex: encabezado + producto + Teknostep + cantidad con signo',
        contenido.startswith('KARDEX: LAM-015') and 'Proveedor' in contenido
        and 'Teknostep' in contenido and ',14,' in contenido, contenido.split('\n')[0][:60])

    # 6. formulario de gasto trae campo proveedor
    capturas.clear()
    page.evaluate('showTab("expenses")')
    page.wait_for_selector('#gProveedor', timeout=8000)
    reg('formulario de gasto tiene campo Proveedor', True)
    page.fill('#gMonto', '500')
    page.fill('#gProveedor', 'Teknostep')
    page.fill('#gDesc', 'Prueba kardex')
    page.click('#tab-expenses button[type="submit"], #tab-expenses .btn-solid')
    page.wait_for_timeout(800)
    pay = next((c for c in capturas if c.get('tipo') == 'gasto'), {})
    reg('payload gasto incluye proveedor', pay.get('proveedor') == 'Teknostep', str(pay.get('proveedor')))

    reg('sin errores JS', len(errores) == 0, errores[:2])
    browser.close()

total = len(resultados); fallos = [r for r in resultados if not r[1]]
print('\n== RESUMEN KARDEX UI: %d/%d exitosas ==' % (total - len(fallos), total))
sys.exit(1 if fallos else 0)
