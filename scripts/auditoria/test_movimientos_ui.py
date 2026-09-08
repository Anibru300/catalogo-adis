#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas UI — Entrada/Salida multi-producto e historial filtrable (ADIS).

Abre public/admin.html con Playwright y un BACKEND SIMULADO (page.route):
  1. Entrada de material con 2 productos + costo + proveedor + referencia + fecha
  2. Salida de material vinculada a proyecto
  3. Historial: columnas de documento/lote, filtros por tipo y busqueda
  4. Exportacion CSV y ventana de impresion
Verifica los payloads que el frontend envia al backend.

Uso: python test_movimientos_ui.py
"""
import json, sys, pathlib, threading, functools, http.server, urllib.parse, datetime
from playwright.sync_api import sync_playwright

ADMIN = pathlib.Path(__file__).resolve().parents[2] / 'public'
HOY = datetime.date.today().isoformat()
resultados = []
def reg(nombre, ok, detalle=''):
    resultados.append((nombre, ok, detalle))
    print(('  PASS ' if ok else '  FAIL ') + nombre + (' — ' + str(detalle)[:160] if detalle else ''))

# ---------------- backend simulado ----------------
S = {
    'productos': [
        {'id': 'P1', 'codigo': 'HJPVC-001', 'nombre': 'Lambrín WPC Roble', 'categoria': 'Lambrín',
         'costo': 80, 'precio': 150, 'moneda': 'MXN', 'estado': 'activo', 'unidad': 'm²', 'stock_minimo': 5, 'foto': '', 'notas': ''},
        {'id': 'P2', 'codigo': 'HJPVC-002', 'nombre': 'Placa PVC Mármol', 'categoria': 'Placas',
         'costo': 400, 'precio': 650, 'moneda': 'MXN', 'estado': 'activo', 'unidad': 'pieza', 'stock_minimo': 2, 'foto': '', 'notas': ''},
        {'id': 'P3', 'codigo': 'HJPVC-003', 'nombre': 'Viga PVC Nogal', 'categoria': 'Vigas',
         'costo': 120, 'precio': 220, 'moneda': 'MXN', 'estado': 'activo', 'unidad': 'm', 'stock_minimo': 0, 'foto': '', 'notas': ''},
    ],
    'almacenes': [{'id': 'A1', 'nombre': 'Nogales'}, {'id': 'A2', 'nombre': 'Rio Rico'}],
    'stock': {'P1|A1': 10, 'P2|A1': 4, 'P3|A1': 20, 'P1|A2': 3},
    'movs': [
        {'fecha': '2026-09-01 10:00', 'tipo': 'entrada', 'producto_id': 'P1', 'producto': 'Lambrín WPC Roble',
         'almacen_id': 'A1', 'almacen': 'Nogales', 'cantidad': 10, 'costo_unit': 80, 'moneda': 'MXN',
         'referencia': 'FAC-100', 'proveedor': 'Proveedor TEST', 'notas': 'Compra inicial',
         'id': 'MOV-2026-00001', 'usuario': 'Adis', 'existencia_anterior': 0, 'existencia_posterior': 10,
         'documento_tipo': 'AJUSTE', 'documento_id': ''},
        {'fecha': '2026-09-03 12:00', 'tipo': 'salida', 'producto_id': 'P2', 'producto': 'Placa PVC Mármol',
         'almacen_id': 'A1', 'almacen': 'Nogales', 'cantidad': 1, 'costo_unit': '', 'moneda': 'MXN',
         'referencia': '', 'proveedor': '', 'notas': 'merma placa rayada',
         'id': 'MOV-2026-00002', 'usuario': 'Adis', 'existencia_anterior': 5, 'existencia_posterior': 4,
         'documento_tipo': 'AJUSTE', 'documento_id': ''},
        {'fecha': '2026-09-05 09:30', 'tipo': 'ajuste', 'producto_id': 'P3', 'producto': 'Viga PVC Nogal',
         'almacen_id': 'A1', 'almacen': 'Nogales', 'cantidad': 20, 'costo_unit': '', 'moneda': 'MXN',
         'referencia': '', 'proveedor': '', 'notas': 'Inventario físico',
         'id': 'MOV-2026-00003', 'usuario': 'Adis', 'existencia_anterior': 22, 'existencia_posterior': 20,
         'documento_tipo': 'AJUSTE', 'documento_id': ''},
    ],
    'folio_mov': 4, 'folio_lote': 1,
    'proveedores': [{'id': 'V1', 'nombre': 'Proveedor TEST', 'activo': 'si', 'contacto': '', 'telefono': '', 'email': ''}],
    'proyectos': [
        {'id': 'PR1', 'folio': 'PROY-2026-001', 'nombre': 'Casa López', 'estado': 'ACTIVO', 'presupuesto': 100000, 'cobrado': 0},
        {'id': 'PR2', 'folio': 'PROY-2026-002', 'nombre': 'Remodelación Vega', 'estado': 'TERMINADO', 'presupuesto': 50000, 'cobrado': 50000},
    ],
    'config': {'moneda_base': 'MXN', 'tipo_cambio': '18.5'},
}
capturas = []

def aplicar_mov(body):
    """Replica la logica del backend nuevo: pre-valida todo, luego aplica."""
    items = body.get('items') or [{'producto_id': body.get('producto_id'), 'cantidad': body.get('cantidad'),
                                   'costo_unit': body.get('costo_unit')}]
    plan = []
    for it in items:
        cant = abs(float(it.get('cantidad') or 0))
        if cant <= 0:
            return {'ok': False, 'error': {'code': 'VALIDACION', 'message': 'cantidad debe ser > 0'}}
        pid, aid = str(it.get('producto_id')), str(body.get('almacen_id'))
        prod = next((p for p in S['productos'] if str(p['id']) == pid), None)
        if not prod:
            return {'ok': False, 'error': {'code': 'NO_ENCONTRADO', 'message': 'producto'}}
        plan.append((prod, pid, aid, cant, it.get('costo_unit')))
    if body.get('tipo_mov') == 'salida':  # todo-o-nada
        for prod, pid, aid, cant, _ in plan:
            if S['stock'].get(pid + '|' + aid, 0) - cant < 0:
                return {'ok': False, 'error': {'code': 'STOCK_INSUFICIENTE', 'message': prod['nombre']}}
    lote = ''
    doc_tipo, doc_id = 'AJUSTE', ''
    if body.get('proyecto_id'):
        doc_tipo, doc_id = 'PROYECTO', str(body['proyecto_id'])
    elif len(plan) > 1 or body.get('items'):
        lote = 'LOTE-2026-%04d' % S['folio_lote']; S['folio_lote'] += 1
        doc_tipo, doc_id = 'LOTE', lote
    stock_nuevo = {}
    for prod, pid, aid, cant, cu in plan:
        ant = S['stock'].get(pid + '|' + aid, 0)
        post = ant + cant if body['tipo_mov'] == 'entrada' else (ant - cant if body['tipo_mov'] == 'salida' else cant)
        S['stock'][pid + '|' + aid] = post
        stock_nuevo[pid] = post
        S['movs'].append({'fecha': (body.get('fecha') or HOY) + ' 13:45', 'tipo': body['tipo_mov'],
                          'producto_id': pid, 'producto': prod['nombre'], 'almacen_id': aid,
                          'almacen': next((a['nombre'] for a in S['almacenes'] if str(a['id']) == aid), ''),
                          'cantidad': cant, 'costo_unit': cu if body['tipo_mov'] == 'entrada' else '',
                          'moneda': body.get('moneda') or 'MXN', 'referencia': body.get('referencia') or '',
                          'proveedor': body.get('proveedor') or '', 'notas': body.get('notas') or '',
                          'id': 'MOV-2026-%05d' % S['folio_mov'], 'usuario': 'Adis',
                          'existencia_anterior': ant, 'existencia_posterior': post,
                          'documento_tipo': doc_tipo, 'documento_id': doc_id, 'lote': lote})
        S['folio_mov'] += 1
    return {'ok': True, 'stock_nuevo': stock_nuevo, 'lote': lote}

def mock_api(route):
    req = route.request
    if req.method == 'POST':
        body = json.loads(req.post_data or '{}')
        t = body.get('tipo')
        if t == 'login':
            route.fulfill(content_type='application/json', body=json.dumps({'ok': True, 'token': 'mock'}))
        elif t == 'movimiento':
            capturas.append(body)
            route.fulfill(content_type='application/json', body=json.dumps(aplicar_mov(body)))
        else:
            route.fulfill(content_type='application/json', body=json.dumps({'ok': True}))
        return
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(req.url).query)
    action = (qs.get('action') or [''])[0]
    base = action.split('&')[0]
    if base == 'productos': data = {'ok': True, 'productos': S['productos']}
    elif base == 'almacenes': data = {'ok': True, 'almacenes': S['almacenes']}
    elif base == 'stock':
        det = [{'producto_id': k.split('|')[0], 'almacen_id': k.split('|')[1], 'cantidad': v, 'producto': '', 'almacen': ''}
               for k, v in S['stock'].items()]
        data = {'ok': True, 'stock': det}
    elif base == 'movimientos': data = {'ok': True, 'movimientos': S['movs']}
    elif base == 'proveedores': data = {'ok': True, 'proveedores': S['proveedores']}
    elif base == 'proyectos': data = {'ok': True, 'proyectos': S['proyectos']}
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

    page.evaluate('''() => { const g = document.querySelector('.tab[data-tab="inventory"]').closest('details.mgroup'); if (g) g.open = true; }''')
    page.click('.tab:has-text("Entrada de material")')
    page.wait_for_selector('#mFecha', timeout=5000)
    reg('formulario de entrada abierto (fecha/almacen/proveedor/ref)', True)
    reg('entrada: sin selector de proyecto', page.locator('#mProy').count() == 0)
    page.wait_for_selector('#mProv option:nth-child(2)', state='attached', timeout=5000)
    reg('proveedores cargados en el select', page.locator('#mProv').inner_text().find('Proveedor TEST') >= 0)

    # agregar 2 productos
    page.fill('#mSearch', 'wpc'); page.wait_for_selector('#mSearchResults .sr-item[onclick]', timeout=5000)
    page.click('#mSearchResults .sr-item[onclick] >> nth=0')
    page.fill('#mSearch', 'placa'); page.wait_for_selector('#mSearchResults .sr-item[onclick]', timeout=5000)
    page.click('#mSearchResults .sr-item[onclick] >> nth=0')
    page.wait_for_timeout(200)
    cants = page.locator('#mItems .item-row input[type=number]')
    reg('2 productos agregados al lote', cants.count() == 4, '%d inputs (cant+costo c/u)' % cants.count())  # 2 cant + 2 costo
    cants.nth(0).fill('5')   # lambrin x5
    cants.nth(1).fill('400')  # costo lambrin
    cants.nth(2).fill('2')   # placa x2
    cants.nth(3).fill('380')  # costo placa
    page.select_option('#mProv', 'Proveedor TEST')
    page.fill('#mRef', 'FAC-999')
    page.fill('#mNotas', 'Prueba entrada lote')
    total_txt = page.locator('#mTotalTxt').inner_text()
    reg('total de piezas y costo calculados', 'Piezas: 7' in total_txt and '2,760' in total_txt, total_txt)

    page.click('button:has-text("Aplicar entrada")')
    page.wait_for_timeout(1200)
    reg('entrada aplicada sin errores JS', len(errores) == 0, errores[:2])
    pay = capturas[-1]
    reg('payload: tipo entrada + 2 items', pay.get('tipo_mov') == 'entrada' and len(pay.get('items') or []) == 2, str(pay.get('items'))[:120])
    reg('payload: costos por item', [i.get('costo_unit') for i in pay['items']] == [400.0, 380.0])
    reg('payload: proveedor + referencia + fecha', pay.get('proveedor') == 'Proveedor TEST' and pay.get('referencia') == 'FAC-999' and pay.get('fecha') == HOY)
    reg('tabla muestra el lote', 'LOTE-2026-0001' in page.locator('#movTable').inner_text())
    reg('tabla muestra proveedor/referencia', 'Proveedor TEST' in page.locator('#movTable').inner_text() and 'FAC-999' in page.locator('#movTable').inner_text())

    # ---------- salida con proyecto ----------
    page.evaluate('''() => { const g = document.querySelector('.tab[data-tab="inventory"]').closest('details.mgroup'); if (g) g.open = true; }''')
    page.click('.tab:has-text("Salida de material")')
    page.wait_for_selector('#mProy', timeout=5000)
    reg('formulario de salida: con selector de proyecto', page.locator('#mProy').count() == 1)
    reg('salida: sin selector de proveedor', page.locator('#mProv').count() == 0)
    page.wait_for_selector('#mProy option[value="PR1"]', state='attached', timeout=5000)
    page.fill('#mSearch', 'placa'); page.wait_for_selector('#mSearchResults .sr-item[onclick]', timeout=5000)
    page.click('#mSearchResults .sr-item[onclick] >> nth=0')
    page.wait_for_timeout(200)
    page.locator('#mItems .item-row input[type=number]').nth(0).fill('1')
    page.select_option('#mProy', 'PR1')
    page.click('button:has-text("Aplicar salida")')
    page.wait_for_timeout(1200)
    pay = capturas[-1]
    reg('payload salida: vinculada a proyecto', pay.get('proyecto_id') == 'PR1' and pay.get('tipo_mov') == 'salida', str(pay)[:120])
    reg('tabla resuelve nombre del proyecto', 'PROY-2026-001' in page.locator('#movTable').inner_text() and 'Casa López' in page.locator('#movTable').inner_text())

    # ---------- filtros ----------
    page.select_option('#movFTipo', 'salida')
    page.wait_for_timeout(200)
    n_sal = page.locator('#movTable tr').count()
    reg('filtro por tipo=salida (2 filas: seed + nueva)', n_sal == 2, '%d filas' % n_sal)
    page.select_option('#movFTipo', '')
    page.fill('#movFBuscar', 'merma')
    page.wait_for_timeout(200)
    reg('busqueda por texto "merma" (1 fila)', page.locator('#movTable tr').count() == 1)
    page.fill('#movFBuscar', 'zzz-sin-coincidencia')
    page.wait_for_timeout(200)
    reg('sin coincidencias muestra mensaje', 'con estos filtros' in page.locator('#movTable').inner_text())
    page.fill('#movFBuscar', '')
    page.fill('#movFDesde', HOY)
    page.wait_for_timeout(200)
    reg('filtro desde=hoy excluye movimientos viejos', page.locator('#movTable tr').count() == 3, '%d filas (2 lote + 1 salida)' % page.locator('#movTable tr').count())
    page.fill('#movFDesde', '')

    # ---------- CSV ----------
    with page.expect_download() as dl_info:
        page.click('#tab-inventory button:has-text("CSV")')
    dl = dl_info.value
    tmp = pathlib.Path(__file__).resolve().parent / '_tmp_movs.csv'
    dl.save_as(str(tmp))
    contenido = tmp.read_text(encoding='utf-8-sig')
    tmp.unlink()
    reg('CSV descargado con encabezados y datos', contenido.startswith('Fecha,Tipo,Producto') and 'LOTE-2026-0001' in contenido and 'Placa PVC Mármol' in contenido)

    # ---------- imprimir (ventana) ----------
    page.evaluate('window.print = function(){}')
    page.click('#tab-inventory button:has-text("Imprimir")')
    page.wait_for_timeout(900)
    reg('imprimir sin errores JS', len(errores) == 0, errores[:2])

    browser.close()

print('\nErrores de JS capturados: %d' % len(errores))
for e in errores[:8]:
    print('  ', e[:200])
fallos = [r for r in resultados if not r[1]]
print('== RESUMEN UI MOVIMIENTOS: %d/%d exitosas ==' % (len(resultados) - len(fallos), len(resultados)))
sys.exit(1 if (fallos or errores) else 0)
