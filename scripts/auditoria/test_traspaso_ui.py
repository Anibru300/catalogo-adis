#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas UI — Traspaso entre almacenes (2026-11-25).

Abre public/admin.html con Playwright y un BACKEND SIMULADO (page.route) que
replica el endpoint 'traspaso' (todo-o-nada, folio TRA-, par salida+entrada):
  1. Boton "⇄ Traspaso" abre el formulario multi-producto
  2. Buscador solo muestra productos con existencia en el ORIGEN
  3. Validaciones cliente: origen=destino, cantidad > disponible
  4. Traspaso de 2 productos: UN solo POST con payload correcto + notice folio
  5. Traslado rapido por chip (.wh-chip) usa el endpoint 'traspaso' (1 POST)
  6. Historial: doc_tipo TRASPASO se muestra como "🔀 TRA-..."
Sin escrituras reales: todo interceptado.

Uso: python test_traspaso_ui.py
"""
import json, sys, pathlib, threading, functools, http.server, urllib.parse, datetime
from playwright.sync_api import sync_playwright

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ADMIN = pathlib.Path(__file__).resolve().parents[2] / 'public'
HOY = datetime.date.today().isoformat()
resultados = []
def reg(nombre, ok, detalle=''):
    resultados.append((nombre, ok, detalle))
    print(('  PASS ' if ok else '  FAIL ') + nombre + (' — ' + str(detalle)[:160] if detalle else ''))

# ---------------- backend simulado ----------------
S = {
    'productos': [
        {'id': 'P1', 'codigo': 'LAM-015', 'nombre': 'Lambrín Río', 'categoria': 'Lambrin WPC',
         'costo': 99.57, 'precio': 0, 'moneda': 'MXN', 'estado': 'activo', 'unidad': 'pieza', 'stock_minimo': 0, 'foto': '', 'notas': ''},
        {'id': 'P2', 'codigo': 'LAM-005', 'nombre': 'Lambrín Brasilia', 'categoria': 'Lambrin WPC',
         'costo': 99.57, 'precio': 0, 'moneda': 'MXN', 'estado': 'activo', 'unidad': 'pieza', 'stock_minimo': 0, 'foto': '', 'notas': ''},
        {'id': 'P3', 'codigo': 'VIG-001', 'nombre': 'Viga PVC Nogal', 'categoria': 'Vigas',
         'costo': 120, 'precio': 220, 'moneda': 'MXN', 'estado': 'activo', 'unidad': 'pieza', 'stock_minimo': 0, 'foto': '', 'notas': ''},
    ],
    'almacenes': [{'id': 'A1', 'nombre': 'Nogales', 'activo': 'si'}, {'id': 'A2', 'nombre': 'Decosonora', 'activo': 'si'}],
    'stock': {'P1|A1': 14, 'P2|A1': 14, 'P1|A2': 2},
    'movs': [], 'folio_mov': 1, 'folio_tra': 1,
    'config': {'moneda_base': 'MXN', 'tipo_cambio': '18.5'},
}
capturas = []

def aplicar_traspaso(body):
    """Replica la logica del endpoint 'traspaso': valida todo, luego mueve."""
    ori, dest = str(body.get('almacen_origen_id')), str(body.get('almacen_destino_id'))
    ids = [str(a['id']) for a in S['almacenes']]
    if ori not in ids or dest not in ids:
        return {'ok': False, 'error': {'code': 'NO_ENCONTRADO', 'message': 'almacen'}}
    if ori == dest:
        return {'ok': False, 'error': {'code': 'VALIDACION', 'message': 'origen=destino'}}
    items = body.get('items') or []
    if not items:
        return {'ok': False, 'error': {'code': 'VALIDACION', 'message': 'sin items'}}
    for it in items:  # todo-o-nada: pre-valida
        cant = float(it.get('cantidad') or 0)
        if S['stock'].get(str(it.get('producto_id')) + '|' + ori, 0) - cant < 0:
            return {'ok': False, 'error': {'code': 'STOCK_INSUFICIENTE', 'message': 'sin stock'}}
    folio = 'TRA-2026-%04d' % S['folio_tra']; S['folio_tra'] += 1
    nom = {a['id']: a['nombre'] for a in S['almacenes']}
    stock_nuevo = {}
    for it in items:
        pid, cant = str(it.get('producto_id')), float(it.get('cantidad'))
        prod = next(p for p in S['productos'] if str(p['id']) == pid)
        for tipo, aid in (('salida', ori), ('entrada', dest)):
            k = pid + '|' + aid
            ant = S['stock'].get(k, 0)
            post = ant - cant if tipo == 'salida' else ant + cant
            S['stock'][k] = post
            if tipo == 'entrada': stock_nuevo[pid] = post
            S['movs'].append({'fecha': (body.get('fecha') or HOY) + ' 14:00', 'tipo': tipo,
                              'producto_id': pid, 'producto': prod['nombre'], 'almacen_id': aid,
                              'almacen': nom[aid], 'cantidad': cant, 'costo_unit': prod['costo'],
                              'moneda': 'MXN', 'referencia': 'Traspaso: %s → %s' % (nom[ori], nom[dest]),
                              'proveedor': '', 'notas': body.get('notas') or 'Traspaso entre almacenes',
                              'id': 'MOV-2026-%05d' % S['folio_mov'], 'usuario': 'Adis',
                              'existencia_anterior': ant, 'existencia_posterior': post,
                              'documento_tipo': 'TRASPASO', 'documento_id': folio, 'lote': ''})
            S['folio_mov'] += 1
    return {'ok': True, 'folio': folio, 'stock_nuevo': stock_nuevo, 'alertas': []}

def mock_api(route):
    req = route.request
    if req.method == 'POST':
        body = json.loads(req.post_data or '{}')
        t = body.get('tipo')
        if t == 'login':
            route.fulfill(content_type='application/json', body=json.dumps({'ok': True, 'token': 'mock'}))
        elif t == 'traspaso':
            capturas.append(body)
            route.fulfill(content_type='application/json', body=json.dumps(aplicar_traspaso(body)))
        else:
            capturas.append(body)
            route.fulfill(content_type='application/json', body=json.dumps({'ok': True}))
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
    elif base == 'proveedores': data = {'ok': True, 'proveedores': []}
    elif base == 'proyectos': data = {'ok': True, 'proyectos': []}
    elif base == 'config': data = {'ok': True, **S['config']}
    elif base == 'ventas': data = {'ok': True, 'ventas': []}
    elif base == 'gastos': data = {'ok': True, 'gastos': []}
    elif base == 'clientes': data = {'ok': True, 'clientes': []}
    elif base == 'reviews_admin': data = {'ok': True, 'reviews': []}
    elif base == 'cxp': data = {'ok': True, 'cxp': [], 'pagos': []}
    else: data = {'ok': True, base: []}
    route.fulfill(content_type='application/json', body=json.dumps(data))

# ---------------- servidor estatico ----------------
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ADMIN))
server = http.server.HTTPServer(('127.0.0.1', 0), handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:%d/admin.html' % server.server_address[1]

errores = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_context().new_page()
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

    page.evaluate('''() => showTab('inventory')''')
    page.wait_for_timeout(600)

    # 1. boton abre formulario
    btn = page.locator('button:has-text("⇄ Traspaso")')
    reg('boton "⇄ Traspaso" visible en toolbar de Inventario', btn.count() == 1)
    btn.click()
    page.wait_for_selector('#tOrigen', timeout=5000)
    reg('formulario abierto (origen/destino/fecha)', page.locator('#tDestino').count() == 1 and page.locator('#tFecha').count() == 1)
    reg('fecha default hoy con max=hoy', page.locator('#tFecha').get_attribute('value') == HOY and page.locator('#tFecha').get_attribute('max') == HOY)
    reg('destino auto-distinto del origen', page.locator('#tOrigen').input_value() != page.locator('#tDestino').input_value())

    # 2. buscador solo muestra productos con stock en origen
    page.fill('#tSearch', 'viga')
    page.wait_for_timeout(300)
    reg('buscador: producto SIN stock en origen no aparece', 'Sin existencia' in page.locator('#tSearchResults').inner_text())
    page.fill('#tSearch', 'lambrín')
    page.wait_for_selector('#tSearchResults .sr-item[onclick]', timeout=5000)
    reg('buscador: muestra existencia en origen', 'en origen: 14' in page.locator('#tSearchResults').inner_text())

    # 3. agregar 2 productos y capturar cantidades
    page.click('#tSearchResults .sr-item[onclick] >> nth=0')
    page.fill('#tSearch', 'brasilia')
    page.wait_for_selector('#tSearchResults .sr-item[onclick]', timeout=5000)
    page.click('#tSearchResults .sr-item[onclick] >> nth=0')
    page.wait_for_timeout(200)
    cants = page.locator('#tItems .item-row input[type=number]')
    reg('2 productos agregados', cants.count() == 2, '%d filas' % cants.count())
    cants.nth(0).fill('4'); cants.nth(0).press('Tab')
    cants.nth(1).fill('2'); cants.nth(1).press('Tab')
    page.wait_for_timeout(200)
    reg('total de piezas calculado', 'Piezas: 6' in page.locator('#tTotalTxt').inner_text())

    # 4. validacion cliente: cantidad > disponible
    cants.nth(0).fill('99'); cants.nth(0).press('Tab')
    page.wait_for_timeout(200)
    disp_val = page.locator('#tItems .item-row').nth(1).locator('input').nth(2).input_value()  # nth(0)=fila encabezado
    reg('avisa "insuficiente" si cantidad > disponible', 'insuficiente' in disp_val, disp_val)
    page.click('button:has-text("Aplicar traspaso")')
    page.wait_for_timeout(300)
    reg('guardar bloqueado con notice (sin POST)', len(capturas) == 0 and 'suficiente' in page.locator('#notice').inner_text(),
        page.locator('#notice').inner_text()[:80])
    page.locator('#tItems .item-row input[type=number]').nth(0).fill('4')
    page.locator('#tItems .item-row input[type=number]').nth(0).press('Tab')
    page.wait_for_timeout(200)

    # 5. traspaso correcto: UN solo POST con payload correcto
    page.fill('#tNotas', 'Prueba UI traspaso')
    page.click('button:has-text("Aplicar traspaso")')
    page.wait_for_timeout(1200)
    reg('exactamente 1 POST al backend', len(capturas) == 1, '%d posts' % len(capturas))
    pay = capturas[-1] if capturas else {}
    reg('payload: tipo traspaso + almacenes + fecha + notas',
        pay.get('tipo') == 'traspaso' and pay.get('almacen_origen_id') == 'A1' and pay.get('almacen_destino_id') == 'A2'
        and pay.get('fecha') == HOY and pay.get('notas') == 'Prueba UI traspaso', str(pay)[:140])
    reg('payload: 2 items sin costo (el backend lo toma del producto)',
        len(pay.get('items') or []) == 2 and all('costo_unit' not in i for i in pay['items'])
        and [i.get('cantidad') for i in pay['items']] == [4.0, 2.0], str(pay.get('items'))[:120])
    reg('notice con folio TRA- y ruta', 'TRA-2026-0001' in page.locator('#notice').inner_text()
        and 'Nogales → Decosonora' in page.locator('#notice').inner_text(), page.locator('#notice').inner_text()[:100])

    # 6. historial: doc TRASPASO con emoji 🔀
    page.wait_for_timeout(600)
    movtxt = page.locator('#movTable').inner_text()
    reg('historial muestra "🔀 TRA-2026-0001" (4 filas del traspaso)', '🔀 TRA-2026-0001' in movtxt and movtxt.count('TRA-2026-0001') >= 4)

    # 7. traslado rapido por chip usa el endpoint traspaso
    capturas.clear()
    page.wait_for_selector('#invTable .wh-chip', timeout=5000)
    page.locator('#invTable .wh-chip').first.click()
    page.wait_for_selector('#tCant', timeout=5000)
    page.fill('#tCant', '3')
    page.click('button:has-text("Aplicar traslado")')
    page.wait_for_timeout(1200)
    reg('chip: 1 solo POST (antes eran 2)', len(capturas) == 1, '%d posts' % len(capturas))
    pay = capturas[-1] if capturas else {}
    reg('chip: payload tipo traspaso 1 item', pay.get('tipo') == 'traspaso' and len(pay.get('items') or []) == 1
        and pay['items'][0].get('cantidad') == 3.0, str(pay)[:120])
    reg('chip: notice con folio TRA-', 'TRA-2026-0002' in page.locator('#notice').inner_text(), page.locator('#notice').inner_text()[:100])

    # 8. origen = destino bloqueado en cliente
    page.click('button:has-text("⇄ Traspaso")')
    page.wait_for_selector('#tOrigen', timeout=5000)
    page.select_option('#tDestino', 'A1')
    page.select_option('#tOrigen', 'A1')  # dispara traAlmacenCambio: destino se mueve solo
    page.wait_for_timeout(200)
    reg('cambiar origen reubica destino (nunca iguales)', page.locator('#tDestino').input_value() != 'A1')

    reg('sin errores JS en toda la suite', len(errores) == 0, errores[:2])
    browser.close()

total = len(resultados); fallos = [r for r in resultados if not r[1]]
print('\n== RESUMEN TRASPASO UI: %d/%d exitosas ==' % (total - len(fallos), total))
sys.exit(1 if fallos else 0)
