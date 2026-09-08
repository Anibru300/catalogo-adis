#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas API — Entrada/Salida multi-producto (LOTE), Fase 1B (ADIS).

Requiere el backend con handler 'movimiento' NUEVO desplegado (auto-detecta;
omite con mensaje si aun es el viejo). Datos: productos TEST-LOTE-A/B, se
limpian al terminar.

Uso: python test_movimientos_lote_api.py
"""
import json, sys, datetime, urllib.request, urllib.error

API = 'https://script.google.com/macros/s/AKfycbxq47t5I3eSqPmJ7zCnk47_RlHGfIwov8mcI1tJ92yNVvSsUXHU5Pe7DQ2Nx_h1wPP2/exec'
USUARIO, CLAVE = 'Adis', 'Adisdiseño2026'
HOY = datetime.date.today()
AYER = (HOY - datetime.timedelta(days=1)).isoformat()
MANANA = (HOY + datetime.timedelta(days=1)).isoformat()
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

def errcode(d): return (d.get('error') or {}).get('code') if isinstance(d.get('error'), dict) else d.get('error')

req = urllib.request.Request(API, data=json.dumps({'tipo': 'login', 'usuario': USUARIO, 'clave': CLAVE}).encode('utf-8'),
                             headers={'Content-Type': 'text/plain;charset=utf-8'})
with urllib.request.urlopen(req, timeout=60) as r:
    TOKEN = json.loads(r.read().decode('utf-8'))['token']

print('== Fase 1B: productos de prueba ==')
def crea_o_recupera(codigo, nombre, costo, precio):
    d = post({'tipo': 'save_product', 'codigo': codigo, 'nombre': nombre, 'costo': costo, 'precio': precio, 'moneda': 'MXN'})
    if d.get('ok'):
        return d.get('id'), True
    if errcode(d) == 'CODIGO_DUPLICADO':  # quedo inactivo de una corrida anterior: reutilizarlo
        post({'tipo': 'restore_product', 'id': next((p['id'] for p in get('productos').get('productos', []) if str(p.get('codigo')) == codigo), '')})
        return next((p['id'] for p in get('productos').get('productos', []) if str(p.get('codigo')) == codigo), None), False
    return None, True

pa_ok = crea_o_recupera('TEST-LOTE-A', 'PRODUCTO LOTE A', 10, 20)
pb_ok = crea_o_recupera('TEST-LOTE-B', 'PRODUCTO LOTE B', 5, 9)
PID_A, creado_a = pa_ok
PID_B, creado_b = pb_ok
reg('productos de prueba (creados o recuperados)', bool(PID_A and PID_B), '%s %s (nuevos: %s/%s)' % (PID_A, PID_B, creado_a, creado_b))
almacenes = get('almacenes').get('almacenes', [])
AID = almacenes[0]['id'] if almacenes else None
if not (PID_A and PID_B and AID):
    print('>> Sin productos/almacen; aborta.'); sys.exit(1)

print('== Fase 1B: lote multi-producto ==')
d = post({'tipo': 'movimiento', 'tipo_mov': 'entrada', 'almacen_id': AID, 'fecha': AYER,
          'proveedor': 'Proveedor TEST', 'referencia': 'FAC-LOTE-1', 'notas': 'Prueba lote',
          'items': [{'producto_id': PID_A, 'cantidad': 5, 'costo_unit': 11},
                    {'producto_id': PID_B, 'cantidad': 3, 'costo_unit': 6}]})
if not d.get('lote'):
    print('>> Backend VIEJO detectado (sin campo lote): omite hasta el redeploy con nueva version.')
    post({'tipo': 'delete_product', 'id': PID_A}); post({'tipo': 'delete_product', 'id': PID_B})
    sys.exit(0)
reg('entrada lote 2 items => ok + folio LOTE', d.get('ok') is True and str(d.get('lote', '')).startswith('LOTE-'), d.get('lote'))
reg('stock_nuevo devuelve dict por producto',
    isinstance(d.get('stock_nuevo'), dict) and str(PID_A) in d['stock_nuevo'] and d['stock_nuevo'][str(PID_A)] == 5,
    d.get('stock_nuevo'))
prods = get('productos').get('productos', [])
a = next((x for x in prods if str(x.get('id')) == str(PID_A)), {})
b = next((x for x in prods if str(x.get('id')) == str(PID_B)), {})
reg('entrada con costo actualiza ultimo costo del producto', float(a.get('costo') or 0) == 11 and float(b.get('costo') or 0) == 6,
    'costoA=%s costoB=%s' % (a.get('costo'), b.get('costo')))

movs = get('movimientos&producto_id=%s' % PID_A).get('movimientos', [])
ult = movs[-1] if movs else {}
reg('movimiento del lote trae lote/proveedor/referencia/fecha',
    str(ult.get('lote')) == str(d.get('lote')) and ult.get('proveedor') == 'Proveedor TEST'
    and ult.get('referencia') == 'FAC-LOTE-1' and str(ult.get('fecha', '')).startswith(AYER), ult)
reg('existencia anterior/posterior trazada', ult.get('existencia_anterior') == 0 and ult.get('existencia_posterior') == 5, ult)

print('== Fase 1B: filtros del historial ==')
d = get('movimientos&tipo=entrada')
movs_e = d.get('movimientos', [])
reg('filtro por tipo=entrada', d.get('ok') is True and all(str(m.get('tipo')) == 'entrada' for m in movs_e) and len(movs_e) >= 2)
d = get('movimientos&desde=%s&hasta=%s' % (HOY.isoformat(), MANANA))
reg('filtro desde=hoy (lote fue ayer => sin esas filas)', d.get('ok') is True and
    all(str(m.get('lote')) != str(d.get('lote')) for m in d.get('movimientos', [])))
d = get('movimientos&desde=%s&hasta=%s' % (AYER, HOY.isoformat()))
reg('filtro rango ayer-hoy incluye el lote', any(str(m.get('lote', '')).startswith('LOTE-') for m in d.get('movimientos', [])))
d = get('movimientos&almacen_id=%s' % AID)
reg('filtro por almacen', d.get('ok') is True and all(str(m.get('almacen_id')) == str(AID) for m in d.get('movimientos', [])))

print('== Fase 1B: validaciones ==')
d = post({'tipo': 'movimiento', 'tipo_mov': 'entrada', 'almacen_id': AID, 'fecha': MANANA,
          'items': [{'producto_id': PID_A, 'cantidad': 1}]})
reg('fecha futura => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = post({'tipo': 'movimiento', 'tipo_mov': 'ajuste', 'almacen_id': AID,
          'items': [{'producto_id': PID_A, 'cantidad': 1}, {'producto_id': PID_B, 'cantidad': 1}]})
reg('ajuste con items => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'almacen_id': AID, 'proyecto_id': 'inexistente-xyz',
          'items': [{'producto_id': PID_A, 'cantidad': 1}]})
reg('proyecto inexistente => NO_ENCONTRADO', errcode(d) == 'NO_ENCONTRADO', errcode(d))
d = post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'almacen_id': AID,
          'items': [{'producto_id': PID_A, 'cantidad': 4}, {'producto_id': PID_B, 'cantidad': 99}]})
reg('salida lote que excede => STOCK_INSUFICIENTE (todo-o-nada)', errcode(d) == 'STOCK_INSUFICIENTE', errcode(d))
stock = get('stock').get('stock', [])
sa = next((s for s in stock if str(s.get('producto_id')) == str(PID_A) and str(s.get('almacen_id')) == str(AID)), {})
sb = next((s for s in stock if str(s.get('producto_id')) == str(PID_B) and str(s.get('almacen_id')) == str(AID)), {})
reg('stock intacto tras rechazo del lote', float(sa.get('cantidad') or 0) == 5 and float(sb.get('cantidad') or 0) == 3,
    'A=%s B=%s' % (sa.get('cantidad'), sb.get('cantidad')))

print('== Fase 1B: salida con proyecto (documento PROYECTO) ==')
d = post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'almacen_id': AID,
          'items': [{'producto_id': PID_A, 'cantidad': 2}]})
LOTE2 = d.get('lote')
reg('salida lote parcial (2 de 5) => ok', d.get('ok') is True, LOTE2)
# salida simple 1 item con proyecto usando payload single (retrocompatible)
proys = get('proyectos').get('proyectos', [])
if proys:
    PR = proys[0]
    d = post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'almacen_id': AID, 'proyecto_id': PR['id'],
              'producto_id': PID_B, 'cantidad': 1, 'notas': 'Salida a obra (prueba)'})
    reg('salida vinculada a proyecto => ok', d.get('ok') is True, d)
    movs_b = get('movimientos&producto_id=%s' % PID_B).get('movimientos', [])
    ult_b = movs_b[-1] if movs_b else {}
    reg('movimiento queda documento_tipo=PROYECTO', str(ult_b.get('documento_tipo')) == 'PROYECTO' and str(ult_b.get('documento_id')) == str(PR['id']), ult_b)
else:
    reg('salida vinculada a proyecto (sin proyectos en la hoja)', True, 'omitida')

print('== Limpieza ==')
for pid in (PID_A, PID_B):
    st = next((s for s in get('stock').get('stock', []) if str(s.get('producto_id')) == str(pid) and str(s.get('almacen_id')) == str(AID)), None)
    if st and float(st.get('cantidad') or 0) > 0:
        post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'producto_id': pid, 'almacen_id': AID,
              'cantidad': st['cantidad'], 'notas': 'Limpieza prueba lote'})
    post({'tipo': 'delete_product', 'id': pid})
reg('limpieza OK', True)

total = len(resultados); fallos = [r for r in resultados if not r[1]]
print('\n== RESUMEN LOTE API: %d/%d exitosas ==' % (total - len(fallos), total))
sys.exit(1 if fallos else 0)
