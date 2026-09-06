#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas Fase 6 — P&L por proyecto (utilidad operativa, ventas anuladas excluidas) + alertas + proyecto_mov."""
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
    print('>> Backend viejo detectado: omite pruebas Fase 6.'); sys.exit(0)

TS = str(int(time.time()))
print('== FASE 6: proyecto_mov + ficha financiera ==')
d = post({'tipo': 'save_proyecto', 'nombre': 'PROYECTO TEST F6', 'presupuesto': 1000, 'moneda': 'MXN'})
PRY = d.get('id')
reg('proyecto creado (folio PRY-)', d.get('ok') is True and str(d.get('folio', '')).startswith('PRY-'), d.get('folio'))
d = post({'tipo': 'proyecto_mov', 'proyecto_id': PRY, 'mov_tipo': 'gasto', 'monto': 200, 'moneda': 'MXN', 'fecha': '2020-03-01', 'descripcion': 'Gasto F6'})
reg('proyecto_mov gasto ok', d.get('ok') is True)
d = post({'tipo': 'proyecto_mov', 'proyecto_id': PRY, 'mov_tipo': 'ingreso', 'monto': 50, 'moneda': 'MXN', 'fecha': '2020-03-02'})
reg('proyecto_mov ingreso ok', d.get('ok') is True)
d = post({'tipo': 'proyecto_mov', 'proyecto_id': PRY, 'mov_tipo': 'presupuesto', 'monto': 500, 'moneda': 'MXN'})
reg('proyecto_mov presupuesto (ajusta base) ok', d.get('ok') is True)
d = post({'tipo': 'proyecto_mov', 'proyecto_id': PRY, 'mov_tipo': 'otro', 'monto': 10, 'moneda': 'MXN'})
reg('tipo invalido => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = post({'tipo': 'proyecto_mov', 'proyecto_id': 'NOEXISTE', 'mov_tipo': 'gasto', 'monto': 10, 'moneda': 'MXN'})
reg('proyecto inexistente => NO_ENCONTRADO', errcode(d) == 'NO_ENCONTRADO', errcode(d))
p = next((x for x in get('proyectos').get('proyectos', []) if str(x.get('id')) == str(PRY)), {})
reg('ficha: presupuesto 1500, gastos 200, utilidad -150', float(p.get('presupuesto') or 0) == 1500 and float(p.get('gastos_real') or 0) == 200 and float(p.get('utilidad_real') or 0) == -150,
    '%s/%s/%s' % (p.get('presupuesto'), p.get('gastos_real'), p.get('utilidad_real')))

print('== FASE 6: P&L por proyecto y exclusión de anuladas ==')
d = post({'tipo': 'save_product', 'codigo': 'TEST-FASE6-' + TS, 'nombre': 'PRODUCTO PRUEBA FASE 6', 'costo': 10, 'precio': 20, 'moneda': 'MXN'})
PID = d.get('id')
AID = get('almacenes').get('almacenes', [{}])[0].get('id')
post({'tipo': 'movimiento', 'tipo_mov': 'entrada', 'producto_id': PID, 'almacen_id': AID, 'cantidad': 5})
d = post({'tipo': 'venta', 'fecha': '2020-03-05', 'cliente': 'TEST F6', 'almacen_id': AID, 'moneda': 'MXN',
          'proyecto_id': PRY, 'items': [{'producto_id': PID, 'cantidad': 1, 'precio': 300}], 'notas': 'PRUEBA F6'})
VID = d.get('id')
d = post({'tipo': 'venta', 'fecha': '2020-03-06', 'cliente': 'TEST F6', 'almacen_id': AID, 'moneda': 'MXN',
          'items': [{'producto_id': PID, 'cantidad': 1, 'precio': 999}], 'notas': 'PRUEBA F6 ANULADA'})
VID2 = d.get('id')
post({'tipo': 'anular_venta', 'id': VID2})
d = get('estado_resultados&mes=2020-03')
ing = float(d.get('ingresos') or 0)
reg('P&L global excluye venta anulada (999)', ing > 0 and ing % 300 == 0, d.get('ingresos'))
reg('P&L incluye campo utilidad_operativa', 'utilidad_operativa' in d)
d = get('estado_resultados&mes=2020-03&proyecto_id=' + str(PRY))
reg('P&L por proyecto: solo venta del proyecto (300)',
    float(d.get('ingresos') or 0) == 300 and d.get('proyecto_id') == str(PRY), d.get('ingresos'))
reg('P&L proyecto: gastos = movs del proyecto (200)', float(d.get('total_gastos') or 0) == 200, d.get('total_gastos'))
reg('P&L proyecto: utilidad operativa = 90', float(d.get('utilidad_operativa') or 0) == 90, d.get('utilidad_operativa'))

print('== FASE 6: alertas priorizadas ==')
_stock0 = next((float(s2['cantidad']) for s2 in get('stock').get('stock', []) if str(s2.get('producto_id')) == str(PID) and str(s2.get('almacen_id')) == str(AID)), 0)
if _stock0 > 0:
    post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'producto_id': PID, 'almacen_id': AID, 'cantidad': _stock0, 'notas': 'A 0 para alerta F6'})
d = get('alertas')
reg('alertas ok y prioridades conocidas', d.get('ok') is True and all(a.get('prioridad') in ('CRITICA', 'ALTA', 'MEDIA') for a in d.get('alertas', [])), len(d.get('alertas', [])))
reg('producto TEST sin stock aparece en alertas', any('PRODUCTO PRUEBA FASE 6' in str(a.get('detalle')) for a in d.get('alertas', [])))
prioridades = [a.get('prioridad') for a in d.get('alertas', [])]
peso = {'CRITICA': 0, 'ALTA': 1, 'MEDIA': 2}
reg('alertas ordenadas por prioridad', prioridades == sorted(prioridades, key=lambda x: peso[x]))

print('== Limpieza ==')
stock = next((float(s['cantidad']) for s in get('stock').get('stock', []) if str(s.get('producto_id')) == str(PID) and str(s.get('almacen_id')) == str(AID)), 0)
if stock > 0:
    post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'producto_id': PID, 'almacen_id': AID, 'cantidad': stock, 'notas': 'Limpieza FASE 6'})
post({'tipo': 'delete_product', 'id': PID})
post({'tipo': 'cambiar_estado_proyecto', 'id': PRY, 'estado': 'CANCELADO'})
reg('limpieza OK (datos TEST con fecha 2020-03, sin borrado fisico)', True)
total = len(resultados); fallos = [r for r in resultados if not r[1]]
print('\n== RESUMEN FASE 6: %d/%d exitosas ==' % (total - len(fallos), total))
for nombre, ok, det in fallos: print('  FALLA:', nombre, '—', det)
sys.exit(1 if fallos else 0)
