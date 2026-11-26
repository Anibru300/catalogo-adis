#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas API — Proveedor en movimientos de entrada por gasto (2026-11-25).

Verifica que al capturar un gasto con items_inventario + proveedor, cada
MOVIMIENTO de entrada quede con la columna 'proveedor' poblada (para el
kardex del producto). Requiere backend con el 5to param de
aplicarEntradaInvGasto (si aun no se redeploya, el movimiento vuelve con
proveedor vacio y la prueba lo reporta). Datos TEST aislados; limpia al final.

Uso: python test_gasto_proveedor_api.py
"""
import json, sys, datetime, urllib.request

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

API = 'https://script.google.com/macros/s/AKfycbxq47t5I3eSqPmJ7zCnk47_RlHGfIwov8mcI1tJ92yNVvSsUXHU5Pe7DQ2Nx_h1wPP2/exec'
USUARIO, CLAVE = 'Adis', 'Adisdiseño2026'
HOY = datetime.date.today().isoformat()
resultados = []
def reg(nombre, ok, detalle=''):
    resultados.append((nombre, ok, detalle))
    print(('  PASS ' if ok else '  FAIL ') + nombre + (' — ' + str(detalle)[:160] if detalle else ''))

def post(payload):
    payload = dict(payload, token=TOKEN)
    req = urllib.request.Request(API, data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'text/plain;charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'ok': False, 'error': {'code': 'RED', 'message': str(e)}}

def get(action):
    try:
        with urllib.request.urlopen(API + '?action=' + action + '&token=' + TOKEN, timeout=90) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'ok': False, 'error': {'code': 'RED', 'message': str(e)}}

req = urllib.request.Request(API, data=json.dumps({'tipo': 'login', 'usuario': USUARIO, 'clave': CLAVE}).encode('utf-8'),
                             headers={'Content-Type': 'text/plain;charset=utf-8'})
with urllib.request.urlopen(req, timeout=60) as r:
    TOKEN = json.loads(r.read().decode('utf-8'))['token']

print('== Gasto+proveedor: datos de prueba ==')
def crea_o_recupera(codigo, nombre, costo, precio):
    d = post({'tipo': 'save_product', 'codigo': codigo, 'nombre': nombre, 'costo': costo, 'precio': precio, 'moneda': 'MXN'})
    if d.get('ok'):
        return d.get('id')
    if (d.get('error') or {}).get('code') == 'CODIGO_DUPLICADO':
        pid = next((p['id'] for p in get('productos').get('productos', []) if str(p.get('codigo')) == codigo), '')
        post({'tipo': 'restore_product', 'id': pid})
        return pid
    return None

PID = crea_o_recupera('TEST-KARDEX', 'PRODUCTO KARDEX', 10, 20)
almacenes = get('almacenes').get('almacenes', [])
AID = almacenes[0]['id'] if almacenes else None
reg('producto + almacen de prueba', bool(PID and AID), '%s %s' % (PID, AID))
if not (PID and AID):
    sys.exit(1)

print('== Gasto con items_inventario + proveedor ==')
d = post({'tipo': 'gasto', 'fecha': HOY, 'categoria': 'Compra de mercancía',
          'descripcion': 'Prueba proveedor en kardex — Factura TEST-KDX-1',
          'monto': 100, 'moneda': 'MXN', 'naturaleza': 'inventario', 'proveedor': 'Proveedor KARDEX TEST',
          'almacen_id': AID, 'items_inventario': [{'producto_id': PID, 'cantidad': 3, 'costo_unit': 10}]})
FOLIO = d.get('folio')
reg('gasto con entrada a inventario => ok', d.get('ok') is True, FOLIO)

movs = get('movimientos&producto_id=%s' % PID).get('movimientos', [])
mio = next((m for m in movs if str(m.get('documento_id')) == str(FOLIO)), {})
reg('movimiento de entrada trae proveedor', str(mio.get('proveedor')) == 'Proveedor KARDEX TEST',
    'proveedor=%r' % mio.get('proveedor'))
if mio.get('proveedor') in (None, ''):
    print('>> Si ya redeployaste el backend y sigue vacio: revisar aplicarEntradaInvGasto.')
reg('movimiento sigue siendo doc GASTO con folio', str(mio.get('documento_tipo')) == 'GASTO' and str(mio.get('documento_id')) == str(FOLIO))
reg('stock subio 3', float(mio.get('existencia_posterior') or 0) == 3, mio.get('existencia_posterior'))

print('== gasto SIN proveedor => columna vacia (retrocompatible) ==')
d = post({'tipo': 'gasto', 'fecha': HOY, 'categoria': 'Compra de mercancía',
          'descripcion': 'Prueba kardex sin proveedor', 'monto': 50, 'moneda': 'MXN',
          'naturaleza': 'inventario', 'almacen_id': AID,
          'items_inventario': [{'producto_id': PID, 'cantidad': 1, 'costo_unit': 10}]})
FOLIO2 = d.get('folio')
movs = get('movimientos&producto_id=%s' % PID).get('movimientos', [])
mio2 = next((m for m in movs if str(m.get('documento_id')) == str(FOLIO2)), {})
reg('sin proveedor => movimiento con proveedor vacio', d.get('ok') is True and str(mio2.get('proveedor') or '') == '', FOLIO2)

print('== Limpieza ==')
st = next((s for s in get('stock').get('stock', []) if str(s.get('producto_id')) == str(PID) and str(s.get('almacen_id')) == str(AID)), None)
if st and float(st.get('cantidad') or 0) > 0:
    post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'producto_id': PID, 'almacen_id': AID,
          'cantidad': st['cantidad'], 'notas': 'Limpieza prueba kardex'})
post({'tipo': 'delete_product', 'id': PID})
# los 2 gastos de prueba quedan cancelados para no ensuciar el P&L
for g in get('gastos').get('gastos', []):
    if str(g.get('folio')) in (str(FOLIO), str(FOLIO2)):
        post({'tipo': 'gasto_cancelar', 'id': g.get('id')})
reg('limpieza OK (stock 0, producto baja, gastos de prueba cancelados)', True)

total = len(resultados); fallos = [r for r in resultados if not r[1]]
print('\n== RESUMEN GASTO+PROVEEDOR API: %d/%d exitosas ==' % (total - len(fallos), total))
sys.exit(1 if fallos else 0)
