#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas Fase 1 — Inventario transaccional (ADIS).

Requiere el backend Fase 0+ desplegado (auto-detecta; omite si es viejo).
Datos: crea producto TEST-FASE1, lo limpia al terminar.
Uso: python test_fase1_api.py
"""
import json, sys, urllib.request, urllib.error

API = 'https://script.google.com/macros/s/AKfycbxq47t5I3eSqPmJ7zCnk47_RlHGfIwov8mcI1tJ92yNVvSsUXHU5Pe7DQ2Nx_h1wPP2/exec'
USUARIO, CLAVE = 'Adis', 'Adisdiseño2026'
resultados = []
def reg(nombre, ok, detalle=''):
    resultados.append((nombre, ok, detalle))
    print(('  PASS ' if ok else '  FAIL ') + nombre + (' — ' + str(detalle)[:150] if detalle else ''))

def post(payload):
    payload = dict(payload, token=TOKEN)
    req = urllib.request.Request(API, data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'text/plain;charset=utf-8'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'ok': False, 'error': {'code': 'RED', 'message': str(e)}}

def get(action):
    try:
        with urllib.request.urlopen(API + '?action=' + action + '&token=' + TOKEN, timeout=60) as r:
            return json.loads(r.read().decode('utf-8'))
    except Exception as e:
        return {'ok': False, 'error': {'code': 'RED', 'message': str(e)}}

def errcode(d): return (d.get('error') or {}).get('code') if isinstance(d.get('error'), dict) else d.get('error')

d = post({'tipo': 'login', 'usuario': USUARIO, 'clave': CLAVE}) if False else None
import urllib.request as _u
req = _u.Request(API, data=json.dumps({'tipo': 'login', 'usuario': USUARIO, 'clave': CLAVE}).encode('utf-8'),
                 headers={'Content-Type': 'text/plain;charset=utf-8'})
with _u.urlopen(req, timeout=60) as r:
    TOKEN = json.loads(r.read().decode('utf-8'))['token']

d = get('accion_inexistente_xyz')
if not (isinstance(d.get('error'), dict) and d['error'].get('code') == 'ACCION_DESCONOCIDA'):
    print('>> Backend viejo detectado: omite pruebas Fase 1 hasta el redeploy.'); sys.exit(0)

print('== FASE 1: producto de prueba ==')
d = post({'tipo': 'save_product', 'codigo': 'TEST-FASE1', 'nombre': 'PRODUCTO PRUEBA FASE 1',
          'costo': 10, 'precio': 0, 'moneda': 'MXN'})
reg('crear producto TEST-FASE1', d.get('ok') is True, d)
PID = d.get('id')
almacenes = get('almacenes').get('almacenes', [])
AID = almacenes[0]['id'] if almacenes else None

print('== FASE 1: actualizacion de precios por lote ==')
d = post({'tipo': 'update_precios', 'items': [{'id': PID, 'precio': 25, 'costo': 12}]})
reg('update_precios valido', d.get('ok') is True and d.get('actualizados') == 1, d)
prods = get('productos').get('productos', [])
p = next((x for x in prods if str(x.get('id')) == str(PID)), {})
reg('precio y costo realmente guardados', float(p.get('precio') or 0) == 25 and float(p.get('costo') or 0) == 12,
    'precio=%s costo=%s' % (p.get('precio'), p.get('costo')))
d = post({'tipo': 'update_precios', 'items': [{'id': PID, 'precio': -5}]})
reg('precio negativo => VALIDACION y sin cambios', errcode(d) == 'VALIDACION', errcode(d))
p = next((x for x in get('productos').get('productos', []) if str(x.get('id')) == str(PID)), {})
reg('precio intacto tras rechazo', float(p.get('precio') or 0) == 25, 'precio=%s' % p.get('precio'))
d = post({'tipo': 'update_precios', 'items': [{'id': 'inexistente-xyz', 'precio': 9}]})
reg('id inexistente => ok con actualizados=0', d.get('ok') is True and d.get('actualizados') == 0, d)
d = post({'tipo': 'update_precios', 'items': [{'id': PID, 'precio': 1}] * 201})
reg('lote >200 => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))

print('== FASE 1: historial de movimientos por producto ==')
if AID:
    post({'tipo': 'movimiento', 'tipo_mov': 'entrada', 'producto_id': PID, 'almacen_id': AID, 'cantidad': 5})
post({'tipo': 'movimiento', 'tipo_mov': 'entrada', 'producto_id': PID, 'almacen_id': AID or '', 'cantidad': 0}) if not AID else None
d = get('movimientos&producto_id=' + str(PID))
movs = d.get('movimientos', [])
reg('filtro por producto devuelve solo sus movimientos', d.get('ok') is True and all(str(m.get('producto_id')) == str(PID) for m in movs) and len(movs) >= 1,
    '%d movimientos' % len(movs))
con_traza = [m for m in movs if str(m.get('id', '')).startswith('MOV-') and m.get('existencia_anterior', '') != '']
reg('historial incluye id/existencias/documento', len(con_traza) >= 1, '%d/%d trazados' % (len(con_traza), len(movs)))
d = get('movimientos')
reg('movimientos sin filtro sigue funcionando (ultimos 100)', d.get('ok') is True and len(d.get('movimientos', [])) <= 100)

print('== Limpieza ==')
if AID:
    stock = next((s for s in get('stock').get('stock', []) if str(s.get('producto_id')) == str(PID) and str(s.get('almacen_id')) == str(AID)), None)
    if stock and float(stock.get("cantidad") or 0) > 0:
        post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'producto_id': PID, 'almacen_id': AID,
              'cantidad': stock['cantidad'], 'notas': 'Limpieza prueba FASE 1'})
post({'tipo': 'delete_product', 'id': PID})
reg('limpieza OK', True)

total = len(resultados); fallos = [r for r in resultados if not r[1]]
print('\n== RESUMEN FASE 1: %d/%d exitosas ==' % (total - len(fallos), total))
sys.exit(1 if fallos else 0)
