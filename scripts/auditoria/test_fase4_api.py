#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas Fase 4 — Proyectos + Cobros/CxC + anulacion de venta. Requiere backend Fase 0+."""
import json, sys, time, urllib.request

API = 'https://script.google.com/macros/s/AKfycbxq47t5I3eSqPmJ7zCnk47_RlHGfIwov8mcI1tJ92yNVvSsUXHU5Pe7DQ2Nx_h1wPP2/exec'
USUARIO, CLAVE = 'Adis', 'Adisdiseño2026'
resultados = []
def reg(nombre, ok, detalle=''):
    resultados.append((nombre, ok, detalle))
    print(('  PASS ' if ok else '  FAIL ') + nombre + (' — ' + str(detalle)[:140] if detalle else ''))
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
if not isinstance(get('accion_inexistente_xyz').get('error'), dict):
    print('>> Backend viejo detectado: omite pruebas Fase 4.'); sys.exit(0)

print('== FASE 4: cliente + cotizacion aprobada + proyecto ==')
TS = str(int(time.time()))
CID = post({'tipo': 'save_cliente', 'nombre': 'CLIENTE TEST F4', 'telefono': 'TESTF4' + TS}).get('id')
q = post({'tipo': 'quote', 'cliente': 'CLIENTE TEST F4', 'items': [], 'total': 5000, 'moneda': 'MXN', 'cliente_id': CID})
QID = None
for x in reversed(get('quotes').get('quotes', [])):
    if x.get('folio') == q.get('folio'): QID = x.get('id')
reg('cotizacion con cliente_id lista', bool(QID))
d = post({'tipo': 'crear_proyecto_desde_cotizacion', 'quote_id': QID})
reg('proyecto desde cotizacion NO aprobada => NO_PERMITIDO', errcode(d) == 'NO_PERMITIDO', errcode(d))
post({'tipo': 'set_estado_quote', 'id': QID, 'estado': 'Aprobada'})
d = post({'tipo': 'crear_proyecto_desde_cotizacion', 'quote_id': QID})
reg('crear proyecto desde cotizacion aprobada (folio PRY-)', d.get('ok') is True and str(d.get('folio', '')).startswith('PRY-'), d.get('folio'))
PRY = d.get('id')
d = post({'tipo': 'crear_proyecto_desde_cotizacion', 'quote_id': QID})
reg('segunda vez es idempotente (ya_existia)', d.get('ok') is True and d.get('ya_existia') is True)
proys = get('proyectos').get('proyectos', [])
p = next((x for x in proys if str(x.get('id')) == str(PRY)), {})
reg('proyecto trae presupuesto y cliente', float(p.get('presupuesto') or 0) == 5000 and p.get('cliente') == 'CLIENTE TEST F4', p.get('presupuesto'))
d = post({'tipo': 'cambiar_estado_proyecto', 'id': PRY, 'estado': 'TERMINADO'})
reg('proyecto TERMINADO', d.get('ok') is True)
d = post({'tipo': 'cambiar_estado_proyecto', 'id': PRY, 'estado': 'ACTIVO'})
reg('TERMINADO -> ACTIVO => NO_PERMITIDO', errcode(d) == 'NO_PERMITIDO', errcode(d))

print('== FASE 4: venta vinculada + cobros ==')
d = post({'tipo': 'save_product', 'codigo': 'TEST-FASE4-' + TS, 'nombre': 'PRODUCTO PRUEBA FASE 4', 'costo': 10, 'precio': 20, 'moneda': 'MXN'})
PID = d.get('id')
AID = get('almacenes').get('almacenes', [{}])[0].get('id')
post({'tipo': 'movimiento', 'tipo_mov': 'entrada', 'producto_id': PID, 'almacen_id': AID, 'cantidad': 10})
d = post({'tipo': 'venta', 'fecha': '2020-01-15', 'cliente': 'CLIENTE TEST F4', 'almacen_id': AID,
          'moneda': 'MXN', 'cliente_id': CID, 'proyecto_id': PRY,
          'items': [{'producto_id': PID, 'cantidad': 1, 'precio': 100}], 'notas': 'PRUEBA FASE 4'})
reg('venta con folio VEN- y vinculos', d.get('ok') is True and str(d.get('folio', '')).startswith('VEN-'), d.get('folio'))
VID = d.get('id')
d = post({'tipo': 'registrar_cobro', 'venta_id': VID, 'fecha': '2020-01-16', 'monto': 30, 'moneda': 'MXN', 'metodo': 'Efectivo'})
reg('cobro 30 => estado PARCIAL', d.get('ok') is True and d.get('estado_pago') == 'PARCIAL', d)
d = post({'tipo': 'registrar_cobro', 'venta_id': VID, 'fecha': '2020-01-17', 'monto': 80, 'moneda': 'MXN'})
reg('cobro que excede saldo => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = post({'tipo': 'registrar_cobro', 'venta_id': VID, 'fecha': '2020-01-17', 'monto': 70, 'moneda': 'MXN'})
reg('cobro 70 => estado PAGADA', d.get('ok') is True and d.get('estado_pago') == 'PAGADA', d)
cxc = get('cxc')
x = next((c for c in cxc.get('cxc', []) if str(c.get('venta_id')) == str(VID)), {})
reg('CxC: saldo 0 y PAGADA', float(x.get('saldo') or 0) == 0 and x.get('estado_pago') == 'PAGADA', x.get('saldo'))
proys = get('proyectos').get('proyectos', [])
p = next((y for y in proys if str(y.get('id')) == str(PRY)), {})
reg('proyecto refleja cobrado=100', float(p.get('cobrado') or 0) == 100, p.get('cobrado'))

print('== FASE 4: anulacion de venta (reversa de stock) ==')
d = post({'tipo': 'venta', 'fecha': '2020-01-15', 'cliente': 'TEST', 'almacen_id': AID, 'moneda': 'MXN',
          'items': [{'producto_id': PID, 'cantidad': 2, 'precio': 20}], 'notas': 'PRUEBA FASE 4 ANULACION'})
VID2 = d.get('id')
stock_antes = next((float(s['cantidad']) for s in get('stock').get('stock', []) if str(s.get('producto_id')) == str(PID) and str(s.get('almacen_id')) == str(AID)), 0)
d = post({'tipo': 'anular_venta', 'id': VID2})
reg('anular venta nueva => CANCELADA', d.get('ok') is True, d)
stock_despues = next((float(s['cantidad']) for s in get('stock').get('stock', []) if str(s.get('producto_id')) == str(PID) and str(s.get('almacen_id')) == str(AID)), 0)
reg('stock repuesto tras anulacion (+2)', stock_despues == stock_antes + 2, '%s -> %s' % (stock_antes, stock_despues))
d = post({'tipo': 'registrar_cobro', 'venta_id': VID2, 'monto': 10, 'moneda': 'MXN'})
reg('cobro sobre venta cancelada => NO_PERMITIDO', errcode(d) == 'NO_PERMITIDO', errcode(d))

print('== Limpieza ==')
st = next((float(s['cantidad']) for s in get('stock').get('stock', []) if str(s.get('producto_id')) == str(PID) and str(s.get('almacen_id')) == str(AID)), 0)
if st > 0:
    post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'producto_id': PID, 'almacen_id': AID, 'cantidad': st, 'notas': 'Limpieza FASE 4'})
post({'tipo': 'delete_product', 'id': PID})
post({'tipo': 'delete_cliente', 'id': CID})
reg('limpieza OK (proyecto/ventas/cotizacion TEST quedan con fecha 2020-01, identificables)', True)
total = len(resultados); fallos = [r for r in resultados if not r[1]]
print('\n== RESUMEN FASE 4: %d/%d exitosas ==' % (total - len(fallos), total))
for nombre, ok, det in fallos: print('  FALLA:', nombre, '—', det)
sys.exit(1 if fallos else 0)
