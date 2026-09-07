#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba puntual: cotizador con precio final unico + fix de foco en costo."""
import sys, pathlib, threading, functools, http.server
from playwright.sync_api import sync_playwright

ADMIN = pathlib.Path(__file__).resolve().parents[2] / 'public'
USUARIO, CLAVE = 'Adis', 'Adisdiseño2026'

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ADMIN))
server = http.server.HTTPServer(('127.0.0.1', 0), handler)
puerto = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:%d/admin.html' % puerto

errores = []
ok = True
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on('pageerror', lambda e: errores.append('pageerror: %s' % e))
    page.on('console', lambda m: errores.append('console.error: %s' % m.text) if m.type == 'error' else None)
    page.goto(BASE)
    page.wait_for_timeout(800)
    page.fill('#loginUser', USUARIO)
    page.fill('#loginPass', CLAVE)
    page.click('#loginView button[type="submit"], #loginView .btn-solid')
    page.wait_for_selector('#appView:not(.hidden)', timeout=15000)
    page.wait_for_timeout(2000)

    # abrir pestana proposal
    page.evaluate('''() => {
        const el = document.querySelector('.tab[data-tab="proposal"]');
        const g = el.closest('details.mgroup');
        if (g && !g.open) g.open = true;
    }''')
    page.click('.tab[data-tab="proposal"]')
    page.wait_for_timeout(600)

    # 1. La tabla de partidas ya no existe
    partidas = page.evaluate('() => !!document.getElementById("pItems")')
    print(('  PASS ' if not partidas else '  FAIL ') + 'tabla de partidas eliminada del formulario')

    # 2. Existe el cuadro de precio final
    existe = page.evaluate('() => !!document.getElementById("pPrecioFinal")')
    print(('  PASS ' if existe else '  FAIL ') + 'cuadro de precio final presente')

    # 3. Escribir precio final actualiza INVERSION TOTAL
    page.fill('#pPrecioFinal', '45000')
    page.wait_for_timeout(300)
    total = page.text_content('#pTotalTxt') or ''
    print(('  PASS ' if '$45,000.00' in total else '  FAIL ') + 'total refleja precio final: ' + total)

    # 4. FOCO: teclear en costo sin perder el foco (el bug de "un numero por click")
    page.click('#pCosto')
    foco_ok = True
    for ch in '25000':
        page.keyboard.type(ch)
        page.wait_for_timeout(80)
        activo = page.evaluate('() => document.activeElement && document.activeElement.id')
        if activo != 'pCosto':
            foco_ok = False
            print('  FAIL foco perdido tras teclear %r (activo=%s)' % (ch, activo))
            break
    print(('  PASS ' if foco_ok else '  FAIL ') + 'foco se mantiene al teclear en costo')

    # 5. Utilidad estimada = total - costo
    util = page.text_content('#pUtil') or ''
    print(('  PASS ' if '$20,000.00' in util and '44%' in util else '  FAIL ') + 'utilidad estimada: ' + util)

    # 6. Guardar propuesta valida precio final (vaciarlo debe avisar)
    page.fill('#pPrecioFinal', '')
    page.evaluate('() => { prop.precioFinal=""; }')
    page.wait_for_timeout(200)
    page.evaluate('() => saveProposal()')
    page.wait_for_timeout(400)
    body = page.text_content('body') or ''
    print(('  PASS ' if 'precio final' in body.lower() else '  FAIL ') + 'validacion de precio final al guardar')

    # 7. El documento (vista previa) no muestra partidas ni IVA
    doc = page.inner_html('#propPreview')
    sin_partidas = 'P. unit' not in doc and 'Importe' not in doc
    print(('  PASS ' if sin_partidas else '  FAIL ') + 'documento sin tabla de partidas')

    browser.close()

print('Errores de JS capturados: %d' % len(errores))
for e in errores[:5]:
    print('  ' + e)
sys.exit(1 if errores or not ok else 0)
