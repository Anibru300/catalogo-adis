#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Revision VISUAL del PDF del cotizador (2026-11-07).
Genera PDFs reales con distintos escenarios (IVA, fotos x3/x6, texto largo),
los convierte a PNG y los deja en screenshots/pdf_check/ para inspeccion.
"""
import base64
import functools
import http.server
import io
import pathlib
import sys
import threading
import urllib.request

from PIL import Image, ImageDraw
from playwright.sync_api import sync_playwright

ADMIN = pathlib.Path(__file__).resolve().parents[2] / 'public'
SALIDA = pathlib.Path(__file__).resolve().parents[2] / 'screenshots' / 'pdf_check'
SALIDA.mkdir(parents=True, exist_ok=True)
USUARIO, CLAVE = 'Adis', 'Adisdiseño2026'

# --- imagenes de prueba reales (colores distintos para detectar solapamientos)
def img_b64(color, texto, w=1100, h=750):
    im = Image.new('RGB', (w, h), color)
    d = ImageDraw.Draw(im)
    d.rectangle([20, 20, w - 20, h - 20], outline=(255, 255, 255), width=8)
    d.text((60, h // 2 - 20), texto, fill=(255, 255, 255))
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=85)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()

FOTO_PROY = [img_b64((140, 60, 60), 'PROYECTO 1'), img_b64((60, 140, 60), 'PROYECTO 2'), img_b64((60, 60, 140), 'PROYECTO 3')]
FOTO_PROD = [img_b64((120, 90, 30), 'PRODUCTO ' + str(i + 1)) for i in range(6)]

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ADMIN))
server = http.server.HTTPServer(('127.0.0.1', 0), handler)
puerto = server.server_address[1]
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = 'http://127.0.0.1:%d/admin.html' % puerto

ESCENARIOS = [
    ('A_con_iva_fotos', dict(
        cliente='Familia Rodríguez López', telefono='631 123 4567', proyecto='Centro de TV sala principal',
        ubicacion='Nogales, Sonora', precioFinal='45000', moneda='MXN', costo='28000',
        incluirIva=True, tasaIva=16,
        area='Muro principal de sala, 14 m²', materiales='Lambrín WPC Brasil, zócalos WPC, placas PVC mármol',
        descripcion='Instalación de centro de TV decorativo con iluminación LED indirecta, nichos y cajillo para cables.',
        tipos=['Centro de TV decorativo', 'Muro decorativo'],
        especificaciones=('Lambrín WPC color Brasil con ranura V, alto brillo. Iluminación LED 3000K integrada en nichos. '
                          'Placa PVC mármol Carrara en centro con aplicación de zócalo WPC. Preparación de muro: nivelación, '
                          'impermeabilización y fijación con adhesivo de montaje y tornillería oculta. Acabado sellado '
                          'antihumedad. Tiempo estimado de instalación: 4 días de trabajo con cuadrilla de 2 personas.'),
        tiempoEntrega='4',
    )),
    ('B_sin_iva_simple', dict(
        cliente='Cliente Prueba B', telefono='', proyecto='Barra desayunador', ubicacion='Rio Rico, AZ',
        precioFinal='1250', moneda='USD', costo='700', incluirIva=False, tasaIva=16,
        area='Cocina, 3 m lineales', materiales='Placa PVC, molduras', descripcion='Revestimiento de barra.',
        tipos=['Barra decorativa'], especificaciones='Acabado mate, color nogal.', tiempoEntrega='2',
    )),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(BASE)
    page.wait_for_timeout(800)
    page.fill('#loginUser', USUARIO)
    page.fill('#loginPass', CLAVE)
    page.click('#loginView button[type="submit"], #loginView .btn-solid')
    page.wait_for_selector('#appView:not(.hidden)', timeout=15000)
    page.wait_for_timeout(2000)
    page.evaluate('''() => {
        const el = document.querySelector('.tab[data-tab="proposal"]');
        const g = el.closest('details.mgroup');
        if (g && !g.open) g.open = true;
    }''')
    page.click('.tab[data-tab="proposal"]')
    page.wait_for_timeout(600)

    for nombre, esc in ESCENARIOS:
        page.evaluate('''([esc, fproy, fprod]) => {
          prop = defaultProp();
          Object.assign(prop, esc);
          prop.items = [];
          prop.fotosProyecto = fproy.map(d => ({data: d}));
          prop.fotos = fprod.map((d, i) => ({data: d, desc: 'Referencia ' + (i + 1)}));
          prop.incluirGarantia = true; prop.incluirLogistica = true; prop.incluirAceptacion = true;
          applyPropToForm(); renderTiposChk(); renderFotoProy(); renderFotosGrid(); renderProposal();
        }''', [esc, FOTO_PROY if 'fotos' in nombre else [None, None, None], FOTO_PROD if 'fotos' in nombre else []])
        page.wait_for_timeout(300)
        with page.expect_download(timeout=60000) as dl_info:
            page.evaluate('() => descargarPDF()')
        dl = dl_info.value
        ruta = str(SALIDA / (nombre + '.pdf'))
        dl.save_as(ruta)
        print('PDF generado:', ruta)
    browser.close()

print('OK')
