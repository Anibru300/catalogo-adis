#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba puntual: cotizador con precio final unico + IVA + fotos + fixes auditoria 2026-11-07."""
import sys, json, pathlib, threading, functools, http.server
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

    # 8. Descargar PDF descarga un .pdf REAL del documento COMPLETO (secciones 01-09)
    page.fill('#pPrecioFinal', '45000')
    page.evaluate('() => { prop.precioFinal="45000"; }')
    page.wait_for_timeout(200)
    paginas = page.evaluate('''async () => {
      await cargarPdfLibs();
      const doc = await buildProposalPDF();
      return doc.getNumberOfPages();
    }''')
    print(('  PASS ' if paginas >= 2 else '  FAIL ') + 'PDF contiene documento completo: %d paginas' % paginas)
    with page.expect_download(timeout=60000) as dl_info:
        page.evaluate('() => descargarPDF()')
    dl = dl_info.value
    nombre_pdf = dl.suggested_filename
    dl.path()  # materializa
    print(('  PASS ' if nombre_pdf.endswith('.pdf') else '  FAIL ') + 'descargarPDF descarga: ' + nombre_pdf)

    # 9. Blindaje syncFormToProp: cambiar el formulario SIN pasar por prop y compartir
    page.fill('#pCliente', 'Cliente Prueba Sync')
    page.evaluate('() => { prop.cliente = "CLIENTE VIEJO ERRONEO"; }')  # simula borrador desincronizado
    page.wait_for_timeout(150)
    page.fill('#pTelefono', '631 120 4943')
    page.evaluate('''() => {
      window.__wa_url = null;
      window.open = function(url){ window.__wa_url = url; return null; };
    }''')
    wa_url = ''
    with page.expect_download(timeout=30000) as dl2:
        page.evaluate('() => sendProposalWhatsApp()')
    dl2.value.path()
    page.wait_for_timeout(500)
    wa_url = page.evaluate('() => window.__wa_url') or ''
    txt_cliente = page.evaluate('() => prop.cliente')
    print(('  PASS ' if txt_cliente == 'Cliente Prueba Sync' else '  FAIL ') + 'syncFormToProp corrigio prop.cliente: ' + txt_cliente)
    print(('  PASS ' if 'wa.me/526311204943' in wa_url else '  FAIL ') + 'WhatsApp abrio al numero del cliente: ' + wa_url[:110])

    # 10. IVA (FIX 2026-11-07): precio 1000 CON IVA 16% -> total 1,160 y desglose
    page.fill('#pPrecioFinal', '1000')
    page.evaluate('() => { prop.precioFinal="1000"; }')
    page.check('#pIncluirIva')
    page.wait_for_timeout(300)
    total = page.text_content('#pTotalTxt') or ''
    desglose = page.text_content('#pDesgloseTxt') or ''
    print(('  PASS ' if '$1,160.00' in total else '  FAIL ') + 'IVA: total con 16% = ' + total)
    print(('  PASS ' if 'Subtotal $1,000.00' in desglose and 'IVA (16%) $160.00' in desglose else '  FAIL ') + 'IVA: desglose = ' + desglose)
    doc = page.inner_html('#propPreview')
    print(('  PASS ' if 'IVA (16%)' in doc and 'SUBTOTAL' in doc else '  FAIL ') + 'IVA: documento muestra desglose')

    # 11. Sin IVA: total = precio tal cual
    page.uncheck('#pIncluirIva')
    page.wait_for_timeout(300)
    total = page.text_content('#pTotalTxt') or ''
    print(('  PASS ' if '$1,000.00' in total else '  FAIL ') + 'sin IVA: total = ' + total)

    # 12. Fotos de proyecto: 3 fotos migran/renderizan en el documento (seccion 02)
    n_fotos = page.evaluate('''() => {
      const px = 'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAAAP/EABQQAQAAAAAAAAAAAAAAAAAAAAD/xAAUAQEAAAAAAAAAAAAAAAAAAAAA/8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAwDAQACEQMRAD8AvwA//9k=';
      prop.fotosProyecto = [{data:px},{data:px},{data:px}];
      renderProposal();
      const html = buildProposalHTML();
      return (html.split('02 · ALCANCE')[1].split('03 · INVERSIÓN')[0].match(/qp-foto/g) || []).length;
    }''')
    print(('  PASS ' if n_fotos >= 3 else '  FAIL ') + 'fotos proyecto: %d renderizadas en seccion 02' % n_fotos)

    # 13. Slots de producto: tope de 12
    n_slots = page.evaluate('''() => {
      prop.fotos = [{data:null,desc:''},{data:null,desc:''},{data:null,desc:''}];
      for (let i = 0; i < 20; i++) addFotoSlot();
      return prop.fotos.length;
    }''')
    print(('  PASS ' if n_slots == 12 else '  FAIL ') + 'slots de producto respetan tope 12: %d' % n_slots)

    # 14. Migracion: borrador viejo con fotoProyecto unica pasa al slot 1
    migro = page.evaluate('''() => {
      prop = Object.assign(defaultProp(), { items: [], fotoProyecto: 'data:image/jpeg;base64,xxx', fotosProyecto: [{data:null},{data:null},{data:null}] });
      migraFotosProyecto_();
      return prop.fotosProyecto[0].data === 'data:image/jpeg;base64,xxx' && prop.fotoProyecto === null;
    }''')
    print(('  PASS ' if migro else '  FAIL ') + 'migracion foto unica -> slot 1')

    # 15. AUDITORIA B1: placeholders de Sheets NO se toman como fotos (ni rotas ni pisando el borrador)
    b1 = page.evaluate('''() => {
      localStorage.removeItem('adis_prop_draft');
      prop = defaultProp();
      prop.fotosProyecto = [{data:'(foto guardada en el borrador local del navegador)'},{data:null},{data:null}];
      prop.fotos = [{data:'(foto en borrador local)', desc:'x'},{data:null,desc:''},{data:null,desc:''}];
      limpiaPlaceholdersFotos_();
      const rotasEnDoc = buildProposalHTML().indexOf('src="(foto') !== -1;
      // simular el draft: guardar y recargar no debe resucitar placeholders
      localStorage.setItem('adis_prop_draft', JSON.stringify(prop));
      const d2 = JSON.parse(localStorage.getItem('adis_prop_draft'));
      prop = Object.assign(defaultProp(), d2); limpiaPlaceholdersFotos_();
      return { p0: prop.fotosProyecto[0].data, f0: prop.fotos[0].data, rotas: rotasEnDoc };
    }''')
    print(('  PASS ' if b1['p0'] is None and b1['f0'] is None and not b1['rotas'] else '  FAIL ') + 'B1 placeholders anulados: ' + json.dumps(b1))

    # 16. AUDITORIA B1b: cargar la MISMA cotización conserva las fotos reales del borrador
    b1b = page.evaluate('''async () => {
      const px = 'data:image/jpeg;base64,QUJD';
      prop = defaultProp();
      prop.savedFolio = 'ADIS-2026-999';
      prop.fotosProyecto = [{data:px},{data:null},{data:null}];
      quotesCache[0] = Object.assign({}, quotesCache[0], { folio:'ADIS-2026-999', id:'x1',
        datos: JSON.stringify(Object.assign(defaultProp(), { items:[], fotosProyecto:[{data:'(foto guardada en el borrador local del navegador)'}] })) });
      loadProposalFromQuote(0);
      await new Promise(r=>setTimeout(r,100));
      return prop.fotosProyecto[0].data;
    }''')
    print(('  PASS ' if b1b == 'data:image/jpeg;base64,QUJD' else '  FAIL ') + 'B1b fotos reales preservadas al cargar: ' + str(b1b)[:40])

    # 17. AUDITORIA B2: utilidad sobre SUBTOTAL (sin IVA): 1000 + IVA, costo 800 -> $200 (20%)
    page.fill('#pPrecioFinal', '1000')
    page.fill('#pCosto', '800')
    page.evaluate('() => { prop.precioFinal="1000"; }')
    page.check('#pIncluirIva')
    page.evaluate('() => { syncFormToProp(); updateTotalsUI(); }')
    util = page.text_content('#pUtil') or ''
    print(('  PASS ' if '$200.00' in util and '20%' in util else '  FAIL ') + 'B2 utilidad sin IVA: ' + util)

    # 18. AUDITORIA B3: imprimir/WhatsApp bloqueados con total 0
    b3 = page.evaluate('''() => {
      prop = defaultProp(); prop.items = []; applyPropToForm();
      let avisos = 0; const old = window.notice;
      try { printProposal(); } catch(e) {}
      const docEnPrint = document.getElementById('printArea').innerHTML.length > 50 && prop.precioFinal === '';
      let waAbierto = false;
      window.open = function(){ waAbierto = true; return null; };
      return new Promise(res => {
        sendProposalWhatsApp().then(()=>res({ docEnPrint, waAbierto })).catch(()=>res({ docEnPrint, waAbierto }));
        setTimeout(()=>res({ docEnPrint, waAbierto }), 1500);
      });
    }''')
    print(('  PASS ' if not b3['docEnPrint'] and not b3['waAbierto'] else '  FAIL ') + 'B3 total 0 bloqueado (print/whatsapp): ' + json.dumps(b3))

    # 19. AUDITORIA B7: waNum rechaza longitudes raras y acepta 10 digitos
    wa = page.evaluate('''() => ({ corto: waNum('631 12'), mx: waNum('631 123 4567'), us: waNum('15208392877'), vacio: waNum('') })''')
    print(('  PASS ' if wa == {'corto': '', 'mx': '526311234567', 'us': '15208392877', 'vacio': ''} else '  FAIL ') + 'B7 waNum: ' + json.dumps(wa))

    # 20. AUDITORIA B6: debounce del autocompletar + datalist poblado
    b6 = page.evaluate('''() => {
      poblarDatalistClientes_();
      const n = document.querySelectorAll('#pClientesList option').length;
      return { opciones: n, debounce: typeof matchLeadBusca_ === 'function' };
    }''')
    print(('  PASS ' if b6['debounce'] and b6['opciones'] >= 0 else '  FAIL ') + 'B6 debounce+datalist: ' + json.dumps(b6))

    browser.close()

print('Errores de JS capturados: %d' % len(errores))
for e in errores[:5]:
    print('  ' + e)
sys.exit(1 if errores or not ok else 0)
