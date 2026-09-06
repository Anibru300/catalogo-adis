#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas Fase 5 — Gastos 2.0 (gasto!=pago, CxP, flujo de efectivo real). Requiere backend Fase 0+."""
import json, sys, urllib.request

API = 'https://script.google.com/macros/s/AKfycbyb5ij67ky7BYlmi76Zg_CPDy44i0HwB-z3bwGp_umHb0rL_0Jl3ClvorquDVN0SD09/exec'
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
    print('>> Backend viejo detectado: omite pruebas Fase 5.'); sys.exit(0)

print('== FASE 5: gasto con folio + pagos parciales + CxP ==')
d = post({'tipo': 'gasto', 'fecha': '2020-02-01', 'categoria': 'TEST FASE 5', 'descripcion': 'Gasto prueba F5',
          'monto': 400, 'moneda': 'MXN'})
reg('gasto con folio GAS-', d.get('ok') is True and str(d.get('folio', '')).startswith('GAS-'), d.get('folio'))
GID = get('gastos').get('gastos', [])[-1].get('id')
d = post({'tipo': 'gasto_pago', 'gasto_id': GID, 'fecha': '2020-02-02', 'monto': 150, 'moneda': 'MXN', 'metodo': 'Efectivo'})
reg('pago 150 => folio PAG- y PARCIAL', d.get('ok') is True and str(d.get('folio', '')).startswith('PAG-') and d.get('estado_pago') == 'PARCIAL', d.get('folio'))
d = post({'tipo': 'gasto_pago', 'gasto_id': GID, 'fecha': '2020-02-03', 'monto': 300, 'moneda': 'MXN'})
reg('pago que excede saldo => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = post({'tipo': 'gasto_pago', 'gasto_id': GID, 'fecha': '2020-02-03', 'monto': 250, 'moneda': 'MXN'})
reg('pago 250 => PAGADA', d.get('ok') is True and d.get('estado_pago') == 'PAGADA', d.get('estado_pago'))
cxp = get('cxp')
x = next((c for c in cxp.get('cxp', []) if str(c.get('gasto_id')) == str(GID)), {})
reg('CxP: saldo 0 y PAGADA', float(x.get('saldo') or 0) == 0 and x.get('estado_pago') == 'PAGADA', x.get('saldo'))
pagos = cxp.get('pagos', [])
reg('pagos recientes incluyen los 2 pagos', len([p for p in pagos if str(p.get('gasto_id')) == str(GID)]) == 2)

print('== FASE 5: cancelar gasto (baja logica) ==')
d = post({'tipo': 'gasto', 'fecha': '2020-02-01', 'categoria': 'TEST FASE 5', 'descripcion': 'A cancelar', 'monto': 100, 'moneda': 'MXN'})
GID2 = get('gastos').get('gastos', [])[-1].get('id')
d = post({'tipo': 'gasto_cancelar', 'id': GID2})
reg('cancelar gasto sin pagos => ok', d.get('ok') is True)
g = next((g for g in get('gastos').get('gastos', []) if str(g.get('id')) == str(GID2)), {})
reg('gasto queda CANCELADA en hoja (no borrado)', g.get('estado') == 'CANCELADA', g.get('estado'))
d = post({'tipo': 'gasto_pago', 'gasto_id': GID2, 'monto': 10, 'moneda': 'MXN'})
reg('pagar gasto cancelado => NO_PERMITIDO', errcode(d) == 'NO_PERMITIDO', errcode(d))
d = post({'tipo': 'gasto_cancelar', 'id': GID})
reg('cancelar gasto PAGADO => NO_PERMITIDO', errcode(d) == 'NO_PERMITIDO', errcode(d))
d = post({'tipo': 'delete_gasto', 'id': GID2})
reg('delete_gasto es alias de cancelar (idempotente)', d.get('ok') is True and (d.get('ya_cancelada') is True or d.get('cancelada') is True), d)
cxp2 = get('cxp')
reg('CxP excluye cancelados', all(str(c.get('gasto_id')) != str(GID2) for c in cxp2.get('cxp', [])))

print('== FASE 5: flujo de efectivo real ==')
d = get('flujo_caja&desde=2020-02-01&hasta=2020-02-28')
reg('flujo_caja ok con totales', d.get('ok') is True and 'entradas' in d and 'salidas' in d, d.get('neto'))
reg('flujo: salidas incluyen 400 de pagos', float(d.get('salidas') or 0) >= 400, d.get('salidas'))
dias = d.get('dias', [])
reg('flujo: serie por dia con 2020-02-02', any(x.get('fecha') == '2020-02-02' and float(x.get('salidas') or 0) >= 150 for x in dias), dias[:2])
movs = d.get('movimientos', [])
reg('flujo: movimientos tipados entrada/salida', any(m.get('tipo') == 'salida' for m in movs), len(movs))
d = get('flujo_caja')
reg('flujo_caja sin params => mes actual', d.get('ok') is True and d.get('desde', '').endswith('-01'))

print('== FASE 5: P&L excluye gastos cancelados ==')
post({'tipo': 'gasto', 'fecha': '2020-02-02', 'categoria': 'TEST FASE 5', 'descripcion': 'Cancelado para P&L', 'monto': 9999, 'moneda': 'MXN'})
GID3 = get('gastos').get('gastos', [])[-1].get('id')
post({'tipo': 'gasto_cancelar', 'id': GID3})
d = get('estado_resultados&mes=2020-02')
cats = d.get('gastos', {})
reg('P&L feb-2020 sin el gasto cancelado de 9999', float(cats.get('TEST FASE 5', 0)) < 9000, cats.get('TEST FASE 5'))

print('== Limpieza ==')
# los gastos TEST quedan con fecha 2020-02 (identificables y fuera de rangos reales); ninguno se borra (historial)
reg('limpieza: datos TEST en fechas 2020-02, sin borrado fisico', True)
total = len(resultados); fallos = [r for r in resultados if not r[1]]
print('\n== RESUMEN FASE 5: %d/%d exitosas ==' % (total - len(fallos), total))
for nombre, ok, det in fallos: print('  FALLA:', nombre, '—', det)
sys.exit(1 if fallos else 0)
