# -*- coding: utf-8 -*-
"""Fase 1 - Importa el dataset maestro a Google Sheets y verifica integridad.

Requiere que el script apps-script.gs (version con import_productos/reset)
este desplegado. Uso:
    python scripts/auditoria/importar_maestro.py
"""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parents[2]
URL = 'https://script.google.com/macros/s/AKfycbzkRT6m7oTOhUCpiUsfjq_PUsgzQILCHaRxHoae-XA3AH0gAlZxhR0kWcH7hmJdRcXp/exec'
CREDS = {'usuario': 'Adis', 'clave': 'Adisdiseño2026'}

dataset = json.load(open(BASE / 'scripts/auditoria/dataset_maestro.json', encoding='utf-8'))

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto('about:blank')

    def post(payload):
        payload = dict(payload)
        r = pg.evaluate("""async ({URL, payload}) => {
          const res = await fetch(URL, {method:'POST', headers:{'Content-Type':'text/plain;charset=utf-8'}, body: JSON.stringify(payload)});
          return await res.text();
        }""", {'URL': URL, 'payload': payload})
        return json.loads(r)

    def get(qs):
        r = pg.evaluate("""async ({URL, qs}) => {
          const res = await fetch(URL + '?' + qs);
          return await res.text();
        }""", {'URL': URL, 'qs': qs})
        return json.loads(r)

    # 1. login
    login = post({'tipo': 'login', **CREDS})
    assert login.get('ok'), f'Login fallo: {login}'
    token = login['token']
    print('1. Login OK')
    T = {'token': token}

    # 2. limpieza de datos de prueba anteriores
    post({'tipo': 'delete_almacen', 'id': 'ed23fa7f', **T})   # Nogales (PRUEBA)
    post({'tipo': 'delete_row', 'sheet': 'Ventas', 'row': 2, **T})
    post({'tipo': 'delete_row', 'sheet': 'Gastos', 'row': 2, **T})
    post({'tipo': 'delete_row', 'sheet': 'Reseñas', 'row': 2, **T})
    print('2. Datos de prueba anteriores limpiados')

    # 3. importacion con reset
    imp = post({'tipo': 'import_productos', 'reset': True,
                'rows': dataset['productos'], 'stock': dataset['stock'], **T})
    print(f"3. Importacion: {imp.get('importados')} productos, {imp.get('stock')} existencias")
    if imp.get('errores'):
        print('   ERRORES:', imp['errores'])

    # 4. verificacion de integridad contra el dataset
    prod = get(f'action=productos&token={token}')['productos']
    stock = get(f'action=stock&token={token}')['stock']
    codigos_api = sorted(str(p['codigo']) for p in prod)
    codigos_ds = sorted(str(r['codigo']) for r in dataset['productos'])
    print(f'4. Integridad: {len(prod)} productos en Sheets vs {len(dataset["productos"])} en dataset')
    faltan = set(codigos_ds) - set(codigos_api)
    sobran = set(codigos_api) - set(codigos_ds)
    print('   Faltan:', faltan or 'ninguno', '| Sobran:', sobran or 'ninguno')
    dupes = {c for c in codigos_api if codigos_api.count(c) > 1}
    print('   Duplicados:', dupes or 'ninguno')
    print(f'   Filas de stock: {len(stock)} (esperadas: {len(dataset["stock"])})')
    costos_ok = 0
    by_code = {str(r['codigo']): r for r in dataset['productos']}
    for p in prod:
        ds = by_code.get(str(p['codigo']))
        if ds and abs((float(p['costo']) or 0) - (float(ds['costo']) or 0)) < 0.01:
            costos_ok += 1
    print(f'   Costos coincidentes: {costos_ok}/{len(dataset["productos"])}')
    b.close()
print('\nIMPORTACION COMPLETA' if not faltan and not dupes else '\nREVISAR DIFERENCIAS')
