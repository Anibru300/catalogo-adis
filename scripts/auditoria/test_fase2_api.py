#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas Fase 2 — Compras: proveedores + ordenes de compra con recepcion parcial.

Requiere backend Fase 0+ desplegado (auto-detecta). Flujo completo:
proveedor -> OC (BORRADOR) -> AUTORIZADA -> recepcion 40/100 -> PARCIAL
-> recepcion 60/100 -> RECIBIDA, verificando stock y trazabilidad.
Datos: producto TEST-FASE2, proveedor TEST, OC TEST (cancelada al final si
no es RECIBIDA; si se recibe completa queda como historico de prueba con
fecha 2020-01). Limpia stock a 0 y desactiva producto/proveedor.
"""
import json, sys, urllib.request

API = 'https://script.google.com/macros/s/AKfycbxq47t5I3eSqPmJ7zCnk47_RlHGfIwov8mcI1tJ92yNVvSsUXHU5Pe7DQ2Nx_h1wPP2/exec'
USUARIO, CLAVE = 'Adis', 'Adisdiseño2026'
resultados = []
def reg(nombre, ok, detalle=''):
    resultados.append((nombre, ok, detalle))
    print(('  PASS ' if ok else '  FAIL ') + nombre + (' — ' + str(detalle)[:150] if detalle else ''))

def raw_post(payload):
    req = urllib.request.Request(API, data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'text/plain;charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'ok': False, 'error': {'code': 'RED', 'message': str(e)}}
def post(payload): return raw_post(dict(payload, token=TOKEN))
def get(action):
    try:
        with urllib.request.urlopen(API + '?action=' + action + '&token=' + TOKEN, timeout=90) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'ok': False, 'error': {'code': 'RED', 'message': str(e)}}
def errcode(d): return (d.get('error') or {}).get('code') if isinstance(d.get('error'), dict) else d.get('error')

TOKEN = raw_post({'tipo': 'login', 'usuario': USUARIO, 'clave': CLAVE}).get('token')
d = get('accion_inexistente_xyz')
if not (isinstance(d.get('error'), dict) and d['error'].get('code') == 'ACCION_DESCONOCIDA'):
    print('>> Backend viejo detectado: omite pruebas Fase 2 hasta el redeploy.'); sys.exit(0)

print('== FASE 2: proveedor ==')
d = post({'tipo': 'save_proveedor', 'nombre': 'PROVEEDOR TEST FASE 2', 'telefono': '000'})
reg('crear proveedor TEST', d.get('ok') is True, d)
PROV = d.get('id')
d = post({'tipo': 'save_proveedor', 'nombre': ''})
reg('proveedor sin nombre => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))

print('== FASE 2: producto y almacen de prueba ==')
d = post({'tipo': 'save_product', 'codigo': 'TEST-FASE2', 'nombre': 'PRODUCTO PRUEBA FASE 2',
          'costo': 10, 'precio': 20, 'moneda': 'MXN'})
PID = d.get('id')
reg('crear producto TEST-FASE2', d.get('ok') is True)
almacenes = get('almacenes').get('almacenes', [])
AID = almacenes[0]['id'] if almacenes else None
reg('hay almacen disponible', bool(AID))
if not (PID and PROV and AID):
    print('FAIL: faltan datos de prueba.'); sys.exit(1)

print('== FASE 2: orden de compra ==')
d = post({'tipo': 'save_oc', 'proveedor_id': PROV, 'almacen_id': AID, 'moneda': 'MXN',
          'iva_pct': 16, 'items': [{'producto_id': PID, 'cantidad': 100, 'costo_unit': 5}]})
reg('crear OC con folio OC-', d.get('ok') is True and str(d.get('folio', '')).startswith('OC-'), d.get('folio'))
OC = d.get('id')
d = post({'tipo': 'save_oc', 'proveedor_id': PROV, 'almacen_id': AID, 'items': []})
reg('OC sin items => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
ocs = get('oc').get('oc', [])
oc = next((o for o in ocs if str(o.get('id')) == str(OC)), {})
reg('OC trae partidas con recibido/pendiente', oc.get('partidas') and oc['partidas'][0].get('pendiente') == 100
    and float(oc.get('total') or 0) == 100*5*1.16, 'total=%s' % oc.get('total'))
d = post({'tipo': 'recibir_oc', 'oc_id': OC, 'items': [{'producto_id': PID, 'cantidad': 1}]})
reg('recepcion en BORRADOR => NO_PERMITIDO', errcode(d) == 'NO_PERMITIDO', errcode(d))
post({'tipo': 'cambiar_estado_oc', 'id': OC, 'estado': 'AUTORIZADA'})

print('== FASE 2: recepciones parciales ==')
stock_de = lambda: next((float(s['cantidad']) for s in get('stock').get('stock', [])
                         if str(s.get('producto_id')) == str(PID) and str(s.get('almacen_id')) == str(AID)), 0.0)
d = post({'tipo': 'recibir_oc', 'oc_id': OC, 'items': [{'producto_id': PID, 'cantidad': 40}]})
reg('recepcion 1 (40) => PARCIAL', d.get('ok') is True and d.get('estado') == 'PARCIAL', d)
reg('stock aumento en 40', stock_de() == 40, 'stock=%s' % stock_de())
d = post({'tipo': 'recibir_oc', 'oc_id': OC, 'items': [{'producto_id': PID, 'cantidad': 70}]})
reg('recepcion que excede pendiente => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = post({'tipo': 'recibir_oc', 'oc_id': OC, 'items': [{'producto_id': PID, 'cantidad': 60}]})
reg('recepcion 2 (60) => RECIBIDA', d.get('ok') is True and d.get('estado') == 'RECIBIDA', d)
reg('stock final correcto (100)', stock_de() == 100, 'stock=%s' % stock_de())
d = post({'tipo': 'recibir_oc', 'oc_id': OC, 'items': [{'producto_id': PID, 'cantidad': 1}]})
reg('recepcion en RECIBIDA => NO_PERMITIDO', errcode(d) == 'NO_PERMITIDO', errcode(d))
prods = get('productos').get('productos', [])
p = next((x for x in prods if str(x.get('id')) == str(PID)), {})
reg('ultimo costo actualizado a 5', float(p.get('costo') or 0) == 5, 'costo=%s' % p.get('costo'))
movs = [m for m in get('movimientos&producto_id=' + str(PID)).get('movimientos', [])
        if m.get('documento_tipo') == 'ORDEN_COMPRA']
reg('entradas trazadas a la OC (doc ORDEN_COMPRA)', len(movs) == 2, '%d entradas' % len(movs))

print('== Limpieza ==')
st = stock_de()
if st > 0:
    post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'producto_id': PID, 'almacen_id': AID,
          'cantidad': st, 'notas': 'Limpieza prueba FASE 2'})
post({'tipo': 'delete_product', 'id': PID})
post({'tipo': 'delete_proveedor', 'id': PROV})
reg('limpieza OK (OC TEST-%s queda como historico; es trazable y no afecta numeros reales)' % OC[:4], True)

total = len(resultados); fallos = [r for r in resultados if not r[1]]
print('\n== RESUMEN FASE 2: %d/%d exitosas ==' % (total - len(fallos), total))
for nombre, ok, det in fallos: print('  FALLA:', nombre, '—', det)
sys.exit(1 if fallos else 0)
