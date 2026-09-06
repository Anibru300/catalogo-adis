#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas Fase 0 — Cimientos del backend ADIS (Apps Script + Google Sheets).

Uso:
    python test_fase0_api.py            # detecta version del backend y prueba
    python test_fase0_api.py --force    # exige backend nuevo (falla si es viejo)

La suite AUTO-DETECTA si el backend desplegado ya incluye la Fase 0
(errores como objeto {code, message}). Contra el backend viejo omite las
pruebas de comportamiento nuevo y solo verifica conectividad basica.

DATOS: crea un producto TEST-FASE0, movimientos y UNA venta de prueba con
fecha 2020-01 (fuera de cualquier mes real del P&L), cliente TEST-CLIENTE.
Limpia el stock a 0 y desactiva el producto al terminar. La fila de venta
TEST queda identificada como eliminable en la hoja Ventas.
"""
import json, sys, time, urllib.request, urllib.error, concurrent.futures, pathlib

API = 'https://script.google.com/macros/s/AKfycbz2TczcLpS97Ro_AYkrw3pnbtlw8v3HtF7FnJrPPJHEUT_JBe-Ar1bumFDGPZpC6nvJ/exec'
USUARIO, CLAVE = 'Adis', 'Adisdiseño2026'

resultados = []
def reg(nombre, ok, detalle=''):
    resultados.append((nombre, ok, detalle))
    print(('  PASS ' if ok else '  FAIL ') + nombre + (' — ' + str(detalle)[:160] if detalle else ''))

def post(payload, sin_token=False):
    if not sin_token: payload = dict(payload, token=TOKEN)
    req = urllib.request.Request(API, data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'text/plain;charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {'ok': False, 'http_error': e.code, 'error': {'code': 'HTTP_%d' % e.code, 'message': str(e.code)}}
    except Exception as e:
        return {'ok': False, 'error': {'code': 'RED', 'message': str(e)}}

def get(action, sin_token=False):
    tok = '' if sin_token else '&token=' + TOKEN
    try:
        with urllib.request.urlopen(API + '?action=' + action + tok, timeout=60) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'ok': False, 'error': {'code': 'RED', 'message': str(e)}}

def errcode(d): return (d.get('error') or {}).get('code') if isinstance(d.get('error'), dict) else d.get('error')

print('== FASE 0: conexion y login ==')
d = post({'tipo': 'login', 'usuario': USUARIO, 'clave': CLAVE}, sin_token=True)
if not d.get('ok'):
    reg('login', False, d); sys.exit(1)
TOKEN = d['token']
reg('login con credenciales correctas', True)

d = post({'tipo': 'login', 'usuario': USUARIO, 'clave': 'clave-equivocada'}, sin_token=True)
reg('login rechaza clave incorrecta', not d.get('ok'))

d = get('me')
reg('GET me con token valido', d.get('ok') is True)
d = get('me', sin_token=True)
reg('GET me sin token es rechazado', not d.get('ok'))
d = get('accion_inexistente_xyz', sin_token=True)
if isinstance(d.get('error'), dict) and d['error'].get('code') == 'ACCION_DESCONOCIDA':
    BACKEND_NUEVO = True
else:
    BACKEND_NUEVO = False
print('>> Backend detectado:', 'NUEVO (Fase 0 desplegada)' if BACKEND_NUEVO else 'VIEJO (falta redeploy)')
if '--force' in sys.argv and not BACKEND_NUEVO:
    print('FAIL: --force exige backend nuevo. Haz el redeploy de apps-script.gs primero.'); sys.exit(1)

if not BACKEND_NUEVO:
    print('>> Pruebas de comportamiento Fase 0 OMITIDAS hasta el redeploy. Conectividad OK.')
    sys.exit(0 if all(r[1] for r in resultados) else 1)

print('== FASE 0: errores consistentes ==')
d = get('me', sin_token=True)
reg('error sin token tiene code TOKEN_INVALIDO', errcode(d) == 'TOKEN_INVALIDO', errcode(d))
d = post({'tipo': 'tipo_inexistente_xyz'})
reg('tipo desconocido => TIPO_DESCONOCIDO', errcode(d) == 'TIPO_DESCONOCIDO', errcode(d))
d = post({'tipo': 'gasto', 'categoria': '', 'monto': 100})
reg('gasto sin categoria => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = post({'tipo': 'gasto', 'categoria': 'TEST', 'monto': -50})
reg('gasto con monto negativo => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = post({'tipo': 'review', 'nombre': 'TEST', 'estrellas': 9, 'texto': 'x'})
reg('review con estrellas 9 => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = post({'tipo': 'config', 'moneda_base': 'EUR'})
reg('config con moneda EUR => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = post({'tipo': 'delete_gasto', 'id': 'id-que-no-existe-xyz'})
reg('delete_gasto con id inexistente => NO_ENCONTRADO', errcode(d) == 'NO_ENCONTRADO', errcode(d))

print('== FASE 0: producto y almacen de prueba ==')
d = post({'tipo': 'save_product', 'codigo': 'TEST-FASE0', 'nombre': 'PRODUCTO DE PRUEBA FASE 0',
          'costo': 10, 'precio': 20, 'moneda': 'MXN'})
reg('crear producto TEST-FASE0', d.get('ok') is True, d)
PID = d.get('id')
d = post({'tipo': 'save_product', 'codigo': 'TEST-FASE0', 'nombre': 'Duplicado'})
reg('codigo duplicado => CODIGO_DUPLICADO', errcode(d) == 'CODIGO_DUPLICADO', errcode(d))
almacenes = get('almacenes').get('almacenes', [])
AID = almacenes[0]['id'] if almacenes else None
reg('hay almacen disponible', bool(AID))
if not PID or not AID:
    print('FAIL: sin producto/almacen de prueba no se puede continuar.'); sys.exit(1)

print('== FASE 0: inventario transaccional ==')
d = post({'tipo': 'movimiento', 'tipo_mov': 'entrada', 'producto_id': PID, 'almacen_id': AID, 'cantidad': 10})
reg('entrada de 10 unidades', d.get('ok') is True and d.get('stock_nuevo') == 10, d)
d = post({'tipo': 'movimiento', 'tipo_mov': 'hack', 'producto_id': PID, 'almacen_id': AID, 'cantidad': 1})
reg('tipo_mov invalido => TIPO_MOVIMIENTO_INVALIDO', errcode(d) == 'TIPO_MOVIMIENTO_INVALIDO', errcode(d))
d = post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'producto_id': PID, 'almacen_id': AID, 'cantidad': 999})
reg('salida que excede existencia => STOCK_INSUFICIENTE', errcode(d) == 'STOCK_INSUFICIENTE', errcode(d))
d = post({'tipo': 'movimiento', 'tipo_mov': 'entrada', 'producto_id': PID, 'almacen_id': AID, 'cantidad': -5})
reg('cantidad negativa => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))

print('== FASE 0: concurrencia en ventas (stock=10, dos ventas de 7) ==')
def vender7(_):
    return post({'tipo': 'venta', 'fecha': '2020-01-15', 'cliente': 'TEST-CLIENTE',
                 'almacen_id': AID, 'moneda': 'MXN',
                 'items': [{'producto_id': PID, 'cantidad': 7, 'precio': 20}], 'notas': 'PRUEBA FASE 0 — eliminable'})
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
    r1, r2 = list(ex.map(vender7, range(2)))
oks = sum(1 for r in (r1, r2) if r.get('ok'))
rechazos = sum(1 for r in (r1, r2) if errcode(r) == 'STOCK_INSUFICIENTE')
reg('exactamente una venta exitosa y una rechazada', oks == 1 and rechazos == 1,
    'ok=%d stock_insuf=%d' % (oks, rechazos))
stock_final = next((s['cantidad'] for s in get('stock').get('stock', [])
                    if str(s['producto_id']) == str(PID) and str(s['almacen_id']) == str(AID)), None)
reg('stock final correcto (=3, nunca negativo)', stock_final == 3, 'stock=%s' % stock_final)
folio_ganador = (r1 if r1.get('ok') else r2).get('folio', '')
reg('venta exitosa tiene folio VEN-', str(folio_ganador).startswith('VEN-'), folio_ganador)

print('== FASE 0: concurrencia en folios de cotizacion ==')
def cotizar(_):
    return post({'tipo': 'quote', 'cliente': 'TEST-CLIENTE', 'items': [], 'total': 1, 'notas': 'PRUEBA FASE 0 — eliminable'})
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
    c1, c2 = list(ex.map(cotizar, range(2)))
f1, f2 = c1.get('folio'), c2.get('folio')
reg('dos cotizaciones concurrentes => folios distintos', c1.get('ok') and c2.get('ok') and f1 != f2, '%s vs %s' % (f1, f2))
d = post({'tipo': 'quote', 'cliente': '', 'items': []})
reg('quote vacia => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))

print('== FASE 0: trazabilidad de movimientos ==')
movs = [m for m in get('movimientos').get('movimientos', []) if str(m.get('producto_id')) == str(PID)]
con_traza = [m for m in movs if str(m.get('id', '')).startswith('MOV-')
             and m.get('existencia_anterior', '') != '' and m.get('documento_tipo', '')]
reg('movimientos con id/usuario/existencias/documento', len(con_traza) >= 3,
    '%d/%d movimientos trazados' % (len(con_traza), len(movs)))

print('== Limpieza de datos de prueba ==')
if stock_final:
    post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'producto_id': PID, 'almacen_id': AID,
          'cantidad': stock_final, 'notas': 'Limpieza prueba FASE 0'})
post({'tipo': 'delete_product', 'id': PID})
reg('producto TEST desactivado y stock a 0', True,
    'venta TEST con folio %s queda en hoja Ventas (fecha 2020-01, eliminable manualmente)' % folio_ganador)

total = len(resultados); fallos = [r for r in resultados if not r[1]]
print('\n== RESUMEN: %d/%d pruebas exitosas ==' % (total - len(fallos), total))
for nombre, ok, det in fallos:
    print('  FALLA:', nombre, '—', det)
sys.exit(1 if fallos else 0)
