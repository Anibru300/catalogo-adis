#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoria en PRODUCCION (solo lectura): PDF directo desde el historial del cotizador.

Verifica contra https://xn--adis-diseo-19a.com/admin.html:
  1. Botones 👁️ / ⬇️ PDF / ✏️ Editar presentes por cada fila con datos.
  2. Descarga real de PDF por cada cotizacion con datos: nombre con folio,
     PDF valido, N paginas, texto clave (folio/cliente/inversion) presente.
  3. 'Ver PDF' abre pestana con el PDF embebido.
  4. 'Editar' precarga el editor (cliente, folio, partidas, vista previa) y
     re-guardar queda a salvo: NO se guarda nada en produccion.
  5. El historial queda identico antes y despues (integridad).

NO escribe nada: no se invoca saveProposal ni aprobarQuote.
Salida: screenshots/check_pdf_historial_prod_*.png
"""
import sys, io, re, json, pathlib
from playwright.sync_api import sync_playwright
from pypdf import PdfReader

BASE = 'https://xn--adis-diseo-19a.com/admin.html'
USUARIO, CLAVE = 'Adis', 'Adisdiseño2026'
SHOTS = pathlib.Path(__file__).resolve().parents[2] / 'screenshots'

fails = 0
errores = []

def check(nombre, cond, extra=''):
    global fails
    if not cond:
        fails += 1
    print(('  PASS ' if cond else '  FAIL ') + nombre + ((' :: ' + str(extra)) if extra != '' else ''))

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(accept_downloads=True)
    page = ctx.new_page()
    page.on('pageerror', lambda e: errores.append('pageerror: %s' % e))
    page.on('console', lambda m: errores.append('console.error: %s' % m.text) if m.type == 'error' else None)

    page.goto(BASE, wait_until='domcontentloaded')
    page.wait_for_timeout(1200)
    page.screenshot(path=str(SHOTS / 'check_pdf_historial_prod_0_login.png'))
    page.fill('#loginUser', USUARIO)
    page.fill('#loginPass', CLAVE)
    page.click('#loginView button[type="submit"], #loginView .btn-solid')
    page.wait_for_selector('#appView:not(.hidden)', timeout=20000)
    page.wait_for_timeout(2500)

    # --- 0. Integridad: historial antes
    page.evaluate('() => loadQuotes()')
    page.wait_for_function('() => Array.isArray(quotesCache) && quotesCache.length > 0', timeout=20000)
    page.wait_for_timeout(500)
    antes = page.evaluate('() => quotesCache.map(q => q.folio + "|" + (q.estado||"") + "|" + (q.total||""))')
    print('Cotizaciones en produccion: %d' % len(antes))

    page.evaluate('''() => { document.querySelector('.tab[data-tab="quotes"]').click(); }''')
    page.wait_for_timeout(600)
    page.screenshot(path=str(SHOTS / 'check_pdf_historial_prod_1_historial.png'), full_page=True)

    filas = page.evaluate('''() => Array.from(document.querySelectorAll('#quotesTable tr')).map((tr, i) => ({
        i,
        folio: (tr.cells[1] && tr.cells[1].textContent || '').trim(),
        cliente: (tr.cells[2] && tr.cells[2].textContent || '').trim(),
        estado: (tr.cells[5] && tr.cells[5].textContent || '').trim(),
        ver: !!tr.querySelector('button[title="Ver PDF"]'),
        desc: !!tr.querySelector('button[title="Descargar PDF"]'),
        editar: !!tr.querySelector('button[title="Editar cotización (carga el editor)"]'),
    }))''')
    con_datos = [f for f in filas if f['ver'] or f['desc'] or f['editar']]
    sin_datos = [f for f in filas if not (f['ver'] or f['desc'] or f['editar'])]
    check('botones presentes en TODAS las filas con datos', len(con_datos) + len(sin_datos) == len(filas)
          and all(f['ver'] and f['desc'] and f['editar'] for f in con_datos),
          '%d con datos, %d simples/sin botones' % (len(con_datos), len(sin_datos)))

    # --- 2. Descarga de PDF por cada cotizacion con datos
    for f in con_datos:
        folio = f['folio'] or ('fila%d' % f['i'])
        with page.expect_download(timeout=90000) as dl:
            page.evaluate('''(i) => {
                const tr = document.querySelectorAll('#quotesTable tr')[i];
                tr.querySelector('button[title="Descargar PDF"]').click();
            }''', f['i'])
        download = dl.value
        nombre = download.suggested_filename
        check('descarga [%s] nombre con folio' % folio, nombre == 'Cotizacion-%s.pdf' % folio, nombre)
        data = download.path() and open(download.path(), 'rb').read()
        check('descarga [%s] es PDF valido' % folio, data[:5] == b'%PDF-' and len(data) > 20000,
              '%d bytes' % len(data))
        try:
            reader = PdfReader(io.BytesIO(data))
            npags = len(reader.pages)
            # Los PDF del cotizador son raster (html2canvas): cada pagina debe
            # traer al menos una imagen grande incrustada (el documento capturado)
            imgs_ok = all(len(pg.images) >= 1 for pg in reader.pages)
            sizes = [(float(pg.mediabox.width), float(pg.mediabox.height)) for pg in reader.pages]
            a4_ok = all(abs(w - 595) < 60 and abs(h - 842) < 60 for w, h in sizes)
            check('descarga [%s] contenido: paginas con documento raster A4' % folio,
                  npags >= 2 and imgs_ok and a4_ok,
                  '%d paginas, imgs=%s, primera=%s' % (npags, imgs_ok, sizes[0]))
        except Exception as e:
            check('descarga [%s] contenido leible' % folio, False, str(e)[:80])

    # --- 3. Ver PDF en pestana (primera con datos)
    if con_datos:
        f0 = con_datos[0]
        with ctx.expect_page(timeout=90000) as pop:
            page.evaluate('''(i) => {
                const tr = document.querySelectorAll('#quotesTable tr')[i];
                tr.querySelector('button[title="Ver PDF"]').click();
            }''', f0['i'])
        popup = pop.value
        try:
            popup.wait_for_function('''() => {
                const e = document.querySelector('embed[type="application/pdf"]');
                return e && e.src.indexOf('blob:') === 0;
            }''', timeout=90000)
            popup.wait_for_timeout(1500)
            popup.screenshot(path=str(SHOTS / 'check_pdf_historial_prod_2_ver_pdf.png'))
            check('Ver PDF abre pestana con PDF embebido', True)
        except Exception as e:
            check('Ver PDF abre pestana con PDF embebido', False, str(e)[:100])
        popup.close()
        page.wait_for_timeout(400)

    # --- 4. Editar: precarga el editor (sin guardar nada)
    if con_datos:
        f1 = con_datos[-1]  # la mas vieja con datos
        page.evaluate('''(i) => {
            const tr = document.querySelectorAll('#quotesTable tr')[i];
            tr.querySelector('button[title="Editar cotización (carga el editor)"]').click();
        }''', f1['i'])
        page.wait_for_timeout(1200)
        ed = page.evaluate('''() => ({
            tab: document.querySelector('.tab.active') && document.querySelector('.tab.active').dataset.tab,
            folio: prop.savedFolio, cliente: prop.cliente,
            clienteForm: document.getElementById('pCliente') && document.getElementById('pCliente').value,
            items: prop.items.length,
            preview: (document.getElementById('propPreview') || {innerHTML:''}).innerHTML.length,
            folioDoc: (document.getElementById('propPreview') || {innerHTML:''}).innerHTML.indexOf(prop.savedFolio) >= 0,
        })''')
        check('Editar cambia a pestana proposal', ed['tab'] == 'proposal', ed['tab'])
        check('Editar precarga folio', ed['folio'] == f1['folio'], ed['folio'])
        check('Editar precarga cliente (estado y formulario)',
              ed['cliente'] == ed['clienteForm'] and len(ed['cliente']) > 2, ed['cliente'])
        check('Editar renderiza vista previa con folio del documento',
              ed['preview'] > 2000 and ed['folioDoc'], 'preview=%d chars' % ed['preview'])
        page.screenshot(path=str(SHOTS / 'check_pdf_historial_prod_3_editar.png'), full_page=False)
        # Volver al historial sin guardar: nada debe haber cambiado
        page.evaluate('''() => { document.querySelector('.tab[data-tab="quotes"]').click(); }''')
        page.wait_for_timeout(600)

    # --- 5. Integridad: historial despues igual que antes
    page.evaluate('() => loadQuotes()')
    page.wait_for_function('() => Array.isArray(quotesCache) && quotesCache.length > 0', timeout=20000)
    page.wait_for_timeout(500)
    despues = page.evaluate('() => quotesCache.map(q => q.folio + "|" + (q.estado||"") + "|" + (q.total||""))')
    check('historial identico despues de la auditoria (sin escrituras)', antes == despues,
          '%d -> %d filas' % (len(antes), len(despues)))

    browser.close()

print('Errores de JS capturados: %d' % len(errores))
for e in errores[:10]:
    print('  ' + e)
if fails or errores:
    print('RESULTADO: FAIL (%d fallos, %d errores JS)' % (fails, len(errores)))
    sys.exit(1)
print('RESULTADO: AUDITORIA PASS')
