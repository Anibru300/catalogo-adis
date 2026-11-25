#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba puntual: PDF directo desde el historial de cotizaciones (2026-11-25).

Verifica que la pestaña Historial tenga botones 👁️ / ⬇️ PDF / ✏️ Editar por fila,
que pdfDesdeHistorial genere el PDF con el folio correcto, y que ni el editor
ni su borrador se toquen (prop se restaura).
NO escribe nada en produccion: el quote es falso y solo vive en memoria.
"""
import sys, json, pathlib, threading, functools, http.server
from playwright.sync_api import sync_playwright

ADMIN = pathlib.Path(__file__).resolve().parents[2] / 'public'
USUARIO, CLAVE = 'Adis', 'Adisdiseño2026'

FAKE = {
    'id': 'TESTFAKE', 'folio': 'ADIS-2026-999', 'fecha': '2026-11-25',
    'cliente': 'Cliente Historial Test', 'telefono': '6311204943',
    'total': '1160.00', 'estado': 'Activa', 'cliente_id': '',
    'datos': json.dumps({
        'cliente': 'Cliente Historial Test', 'telefono': '6311204943',
        'proyecto': 'Muro de prueba', 'ubicacion': 'Nogales',
        'moneda': 'MXN', 'precioFinal': '1000', 'incluirIva': True, 'tasaIva': 16,
        'items': [{'codigo': 'X1', 'descripcion': 'Placa PVC', 'cantidad': 2,
                   'unidad': 'pza', 'precio': 500}],
    }),
}

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ADMIN))
server = http.server.HTTPServer(('127.0.0.1', 0), handler)
puerto = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:%d/admin.html' % puerto

errores = []
fails = 0
with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(accept_downloads=True)
    page = ctx.new_page()
    page.on('pageerror', lambda e: errores.append('pageerror: %s' % e))
    page.on('console', lambda m: errores.append('console.error: %s' % m.text) if m.type == 'error' else None)
    page.goto(BASE)
    page.wait_for_timeout(800)
    page.fill('#loginUser', USUARIO)
    page.fill('#loginPass', CLAVE)
    page.click('#loginView button[type="submit"], #loginView .btn-solid')
    page.wait_for_selector('#appView:not(.hidden)', timeout=15000)
    page.wait_for_timeout(1500)
    # Esperar a que el loadQuotes del login TERMINE (si no, su respuesta real
    # pisa al fake despues de la interceptacion)
    page.wait_for_function('() => Array.isArray(quotesCache) && quotesCache.length > 0', timeout=20000)
    page.wait_for_timeout(500)

    # Stub HTTP: action=quotes responde solo el quote falso (resto pasa al backend real)
    def _route(route):
        if 'action=quotes' in route.request.url:
            route.fulfill(content_type='application/json',
                          headers={'access-control-allow-origin': '*'},
                          body=json.dumps({'ok': True, 'quotes': [FAKE]}))
        else:
            route.continue_()
    page.route('**/*', _route)

    def check(nombre, cond, extra=''):
        global fails
        if not cond:
            fails += 1
        print(('  PASS ' if cond else '  FAIL ') + nombre + ((' :: ' + str(extra)) if extra else ''))

    # Recargar el historial YA con el fetch interceptado (loadQuotes corre al login, antes del route)
    page.evaluate('() => loadQuotes()')
    page.wait_for_timeout(800)

    # 1. Los 3 botones nuevos existen en la fila
    btns = page.evaluate('''() => ({
        ver: !!document.querySelector('#quotesTable button[title="Ver PDF"]'),
        desc: !!document.querySelector('#quotesTable button[title="Descargar PDF"]'),
        editar: !!document.querySelector('#quotesTable button[title="Editar cotización (carga el editor)"]'),
    })''')
    check('botones en historial: ver/descargar/editar', btns == {'ver': True, 'desc': True, 'editar': True}, btns)

    # 2. propDesdeQuote construye el objeto sin tocar la UI ni el editor
    r = page.evaluate('''() => {
        const antes = JSON.stringify(prop);
        const p = propDesdeQuote(quotesCache[0]);
        const editorIntacto = JSON.stringify(prop) === antes && prop.savedFolio !== 'ADIS-2026-999';
        return { ok: !!p, folio: p && p.savedFolio, cliente: p && p.cliente,
                 iva: p && p.incluirIva, editorIntacto,
                 items: p && p.items.length };
    }''')
    check('propDesdeQuote: datos correctos', r.get('ok') and r.get('folio') == 'ADIS-2026-999'
          and r.get('cliente') == 'Cliente Historial Test' and r.get('iva') is True and r.get('items') == 1, r)
    check('propDesdeQuote: editor intacto', r.get('editorIntacto'))

    # 3. Descargar PDF desde el historial (boton real) — no cambia de pestana
    activa_antes = page.evaluate('''() => document.querySelector('.tab.active')?.dataset.tab''')
    snap_antes = page.evaluate('() => JSON.stringify(prop)')
    page.wait_for_timeout(300)
    with page.expect_download(timeout=60000) as dl:
        page.evaluate('() => document.querySelector(\'#quotesTable button[title="Descargar PDF"]\').click()')
    download = dl.value
    nombre = download.suggested_filename
    check('descarga PDF con folio en el nombre', nombre == 'Cotizacion-ADIS-2026-999.pdf', nombre)
    page.wait_for_timeout(500)
    activa_despues = page.evaluate('''() => document.querySelector('.tab.active')?.dataset.tab''')
    snap_despues = page.evaluate('() => JSON.stringify(prop)')
    check('pestana no cambia al generar PDF', activa_despues == activa_antes, '%s -> %s' % (activa_antes, activa_despues))
    check('editor restaurado tras PDF (prop identico)', snap_despues == snap_antes)

    # 4. Ver PDF abre pestana nueva con blob
    try:
        with ctx.expect_page(timeout=60000) as pop:
            page.evaluate('() => document.querySelector(\'#quotesTable button[title="Ver PDF"]\').click()')
        popup = pop.value
        popup.wait_for_function('''() => {
            const e = document.querySelector('embed[type="application/pdf"]');
            return e && e.src.indexOf('blob:') === 0;
        }''', timeout=60000)
        url = popup.evaluate('() => document.querySelector("embed[type=\\"application/pdf\\"]").src')
        check('Ver PDF muestra el PDF en pestana (embed blob)', url.startswith('blob:'), url[:60])
        popup.close()
    except Exception as e:
        check('Ver PDF abre pestana con blob', False, str(e)[:120])
    page.wait_for_timeout(300)
    check('editor restaurado tras Ver PDF', page.evaluate('() => JSON.stringify(prop)') == snap_antes)

    browser.close()

print('Errores de JS capturados: %d' % len(errores))
for e in errores[:10]:
    print('  ' + e)
if fails or errores:
    print('RESULTADO: FAIL (%d pruebas, %d errores JS)' % (fails, len(errores)))
    sys.exit(1)
print('RESULTADO: TODO PASS')
