#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regresion Fase 0 — panel admin (admin/index.html -> public/admin.html).

Abre el panel con Playwright, hace login contra el backend VIVO y recorre
todas las pestañas capturando errores de JavaScript. El frontend parcheado
debe funcionar tanto con el backend viejo (pre-redeploy) como con el nuevo.

Uso: python test_fase0_regresion.py
"""
import sys, pathlib, threading, functools, http.server
from playwright.sync_api import sync_playwright

ADMIN = pathlib.Path(__file__).resolve().parents[2] / 'public'
USUARIO, CLAVE = 'Adis', 'Adisdiseño2026'
TABS = ['dash', 'leads', 'clientes', 'quotes', 'proposal', 'inventory', 'oc', 'sales', 'proyectos', 'cobros', 'flujocaja', 'expenses', 'pnl', 'reviews', 'analytics', 'flow']

# servir public/ por HTTP local (file:// no permite fetch de products.json)
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ADMIN))
server = http.server.HTTPServer(('127.0.0.1', 0), handler)
puerto = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:%d/admin.html' % puerto

errores = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.on('pageerror', lambda e: errores.append('pageerror: %s' % e))
    page.on('console', lambda m: errores.append('console.error: %s' % m.text) if m.type == 'error' else None)
    page.goto(BASE)
    page.wait_for_timeout(800)

    # noindex presente
    robots = page.locator('meta[name="robots"]').get_attribute('content') or ''
    print(('  PASS ' if 'noindex' in robots else '  FAIL ') + 'meta robots noindex')

    # login
    page.fill('#loginUser', USUARIO)
    page.fill('#loginPass', CLAVE)
    page.click('#loginView button[type="submit"], #loginView .btn-solid')
    try:
        page.wait_for_selector('#appView:not(.hidden)', timeout=15000)
        print('  PASS login y entrada al panel')
    except Exception:
        print('  FAIL login — appView no visible'); sys.exit(1)

    page.wait_for_timeout(2500)  # carga inicial de leads/quotes/reviews/inventario

    for tab in TABS:
        try:
            page.click('.tab[data-tab="%s"]' % tab)
            page.wait_for_timeout(1200)
            visible = page.locator('#tab-%s' % tab).is_visible()
            print(('  PASS ' if visible else '  FAIL ') + 'pestaña ' + tab)
        except Exception as e:
            print('  FAIL pestaña %s — %s' % (tab, e))

    # logout (tambien ejercita el apiPost logout best-effort)
    page.click('text=Cerrar sesión')
    page.wait_for_timeout(800)
    login_visible = page.locator('#loginView').is_visible()
    print(('  PASS ' if login_visible else '  FAIL ') + 'logout vuelve al login')
    browser.close()

print('\nErrores de JS capturados: %d' % len(errores))
for e in errores[:10]:
    print('  ', e[:200])
sys.exit(1 if errores else 0)
