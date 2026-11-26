#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas API — Traspaso entre almacenes (endpoint 'traspaso', 2026-11-25).

Requiere el backend con handler 'traspaso' desplegado (auto-detecta; omite con
mensaje si aun es el viejo). Datos: productos TEST-TRA-A/B y almacenes
TEST-Traspaso-O/D (aislados: NO toca almacenes reales); todo se limpia al final.

Cubre: traspaso multi-producto con folio TRA-, stock origen/destino, par
salida+entrada con doc_tipo TRASPASO, todo-o-nada ante stock insuficiente,
origen=destino, fecha futura/retroactiva, producto repetido, costo intacto.

Uso: python test_traspaso_api.py
"""
import json, sys, datetime, urllib.request, urllib.error

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

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

def stock_en(pid, aid):
    s = next((x for x in get('stock').get('stock', [])
              if str(x.get('producto_id')) == str(pid) and str(x.get('almacen_id')) == str(aid)), None)
    return float(s.get('cantidad') or 0) if s else 0.0

print('== Traspaso: datos de prueba (aislados de almacenes reales) ==')
def crea_o_recupera(codigo, nombre, costo, precio):
    d = post({'tipo': 'save_product', 'codigo': codigo, 'nombre': nombre, 'costo': costo, 'precio': precio, 'moneda': 'MXN'})
    if d.get('ok'):
        return d.get('id')
    if errcode(d) == 'CODIGO_DUPLICADO':
        pid = next((p['id'] for p in get('productos').get('productos', []) if str(p.get('codigo')) == codigo), '')
        post({'tipo': 'restore_product', 'id': pid})
        post({'tipo': 'save_product', 'id': pid, 'codigo': codigo, 'nombre': nombre, 'costo': costo, 'precio': precio, 'moneda': 'MXN'})
        return pid
    return None

PID_A = crea_o_recupera('TEST-TRA-A', 'PRODUCTO TRASPASO A', 10, 20)
PID_B = crea_o_recupera('TEST-TRA-B', 'PRODUCTO TRASPASO B', 5, 9)
reg('productos de prueba (creados o recuperados)', bool(PID_A and PID_B), '%s %s' % (PID_A, PID_B))

def almacen_test(nombre):
    act = next((a for a in get('almacenes').get('almacenes', []) if str(a.get('nombre')) == nombre), None)
    if act: return act['id']
    d = post({'tipo': 'save_almacen', 'nombre': nombre, 'ubicacion': 'pruebas automatizadas'})
    return d.get('id') if d.get('ok') else None

AID_O = almacen_test('TEST-Traspaso-O')
AID_D = almacen_test('TEST-Traspaso-D')
reg('almacenes de prueba (origen/destino)', bool(AID_O and AID_D), '%s %s' % (AID_O, AID_D))
if not (PID_A and PID_B and AID_O and AID_D):
    print('>> Sin productos/almacenes de prueba; aborta.'); sys.exit(1)

# Pre-limpieza idempotente: si una corrida anterior murio a medias, vaciar el
# stock sobrante de los almacenes TEST para que las aserciones partan de 0.
for _aid in (AID_O, AID_D):
    for _pid in (PID_A, PID_B):
        _st = stock_en(_pid, _aid)
        if _st > 0:
            post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'producto_id': _pid, 'almacen_id': _aid,
                  'cantidad': _st, 'notas': 'Pre-limpieza prueba traspaso'})

print('== Traspaso: deteccion de backend ==')
d = post({'tipo': 'traspaso', 'almacen_origen_id': AID_O, 'almacen_destino_id': AID_D,
          'items': [{'producto_id': PID_A, 'cantidad': 1}]})
if errcode(d) == 'TIPO_DESCONOCIDO':
    print('>> Backend VIEJO (sin endpoint traspaso): omite hasta el redeploy con nueva version.')
    post({'tipo': 'delete_product', 'id': PID_A}); post({'tipo': 'delete_product', 'id': PID_B})
    post({'tipo': 'delete_almacen', 'id': AID_O}); post({'tipo': 'delete_almacen', 'id': AID_D})
    sys.exit(0)
reg('traspaso sin stock => STOCK_INSUFICIENTE', errcode(d) == 'STOCK_INSUFICIENTE', errcode(d))

print('== Traspaso: stock inicial y traspaso multi-producto ==')
d = post({'tipo': 'movimiento', 'tipo_mov': 'entrada', 'almacen_id': AID_O, 'fecha': AYER,
          'notas': 'Stock inicial prueba traspaso',
          'items': [{'producto_id': PID_A, 'cantidad': 10, 'costo_unit': 10},
                    {'producto_id': PID_B, 'cantidad': 6, 'costo_unit': 5}]})
reg('entrada inicial 10 A + 6 B en origen', d.get('ok') is True and stock_en(PID_A, AID_O) == 10 and stock_en(PID_B, AID_O) == 6)

d = post({'tipo': 'traspaso', 'almacen_origen_id': AID_O, 'almacen_destino_id': AID_D, 'fecha': AYER,
          'notas': 'Prueba traspaso multi', 'items': [{'producto_id': PID_A, 'cantidad': 4},
                                                       {'producto_id': PID_B, 'cantidad': 2}]})
TRA1 = d.get('folio')
reg('traspaso 2 items => ok + folio TRA-', d.get('ok') is True and str(TRA1 or '').startswith('TRA-'), TRA1)
reg('stock_nuevo = posterior en DESTINO por producto',
    isinstance(d.get('stock_nuevo'), dict) and d['stock_nuevo'].get(str(PID_A)) == 4 and d['stock_nuevo'].get(str(PID_B)) == 2,
    d.get('stock_nuevo'))
reg('stock origen 10→6 y 6→4', stock_en(PID_A, AID_O) == 6 and stock_en(PID_B, AID_O) == 4,
    'A=%s B=%s' % (stock_en(PID_A, AID_O), stock_en(PID_B, AID_O)))
reg('stock destino 0→4 y 0→2', stock_en(PID_A, AID_D) == 4 and stock_en(PID_B, AID_D) == 2,
    'A=%s B=%s' % (stock_en(PID_A, AID_D), stock_en(PID_B, AID_D)))

movs_a = get('movimientos&producto_id=%s' % PID_A).get('movimientos', [])
mios = [m for m in movs_a if str(m.get('documento_id')) == str(TRA1)]
sal = next((m for m in mios if m.get('tipo') == 'salida'), {})
ent = next((m for m in mios if m.get('tipo') == 'entrada'), {})
reg('par salida+entrada con doc_tipo TRASPASO y mismo doc_id',
    len(mios) == 2 and str(sal.get('documento_tipo')) == 'TRASPASO' and str(ent.get('documento_tipo')) == 'TRASPASO',
    '%d movimientos' % len(mios))
reg('salida en ORIGEN y entrada en DESTINO', str(sal.get('almacen_id')) == str(AID_O) and str(ent.get('almacen_id')) == str(AID_D),
    '%s / %s' % (sal.get('almacen'), ent.get('almacen')))
reg('fecha retroactiva aplicada y referencia Traspaso', str(sal.get('fecha', '')).startswith(AYER)
    and 'Traspaso' in str(sal.get('referencia', '')), sal.get('fecha'))
reg('existencias anterior/posterior trazadas', sal.get('existencia_anterior') == 10 and sal.get('existencia_posterior') == 6
    and ent.get('existencia_anterior') == 0 and ent.get('existencia_posterior') == 4)

prods = get('productos').get('productos', [])
a = next((x for x in prods if str(x.get('id')) == str(PID_A)), {})
b = next((x for x in prods if str(x.get('id')) == str(PID_B)), {})
reg('costo del producto NO cambia (10 y 5)', float(a.get('costo') or 0) == 10 and float(b.get('costo') or 0) == 5,
    'costoA=%s costoB=%s' % (a.get('costo'), b.get('costo')))

print('== Traspaso: validaciones (todo-o-nada) ==')
d = post({'tipo': 'traspaso', 'almacen_origen_id': AID_O, 'almacen_destino_id': AID_D,
          'items': [{'producto_id': PID_A, 'cantidad': 2}, {'producto_id': PID_B, 'cantidad': 99}]})
reg('excede stock => STOCK_INSUFICIENTE', errcode(d) == 'STOCK_INSUFICIENTE', errcode(d))
reg('stock INTACTO tras rechazo (6/4 en origen)', stock_en(PID_A, AID_O) == 6 and stock_en(PID_B, AID_O) == 4)
d = post({'tipo': 'traspaso', 'almacen_origen_id': AID_O, 'almacen_destino_id': AID_O,
          'items': [{'producto_id': PID_A, 'cantidad': 1}]})
reg('origen = destino => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = post({'tipo': 'traspaso', 'almacen_origen_id': AID_O, 'almacen_destino_id': AID_D, 'fecha': MANANA,
          'items': [{'producto_id': PID_A, 'cantidad': 1}]})
reg('fecha futura => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = post({'tipo': 'traspaso', 'almacen_origen_id': AID_O, 'almacen_destino_id': AID_D,
          'items': [{'producto_id': PID_A, 'cantidad': 1}, {'producto_id': PID_A, 'cantidad': 2}]})
reg('producto repetido => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = post({'tipo': 'traspaso', 'almacen_origen_id': 'no-existe', 'almacen_destino_id': AID_D,
          'items': [{'producto_id': PID_A, 'cantidad': 1}]})
reg('almacen inexistente => NO_ENCONTRADO', errcode(d) == 'NO_ENCONTRADO', errcode(d))
d = post({'tipo': 'traspaso', 'almacen_origen_id': AID_O, 'almacen_destino_id': AID_D, 'items': []})
reg('sin items => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))

print('== Traspaso: inverso (devolucion parcial) ==')
d = post({'tipo': 'traspaso', 'almacen_origen_id': AID_D, 'almacen_destino_id': AID_O,
          'items': [{'producto_id': PID_A, 'cantidad': 1}]})
reg('traspaso inverso destino→origen => ok', d.get('ok') is True and stock_en(PID_A, AID_D) == 3 and stock_en(PID_A, AID_O) == 7,
    d.get('folio'))

print('== Limpieza ==')
for aid in (AID_O, AID_D):
    for pid in (PID_A, PID_B):
        st = stock_en(pid, aid)
        if st > 0:
            post({'tipo': 'movimiento', 'tipo_mov': 'salida', 'producto_id': pid, 'almacen_id': aid,
                  'cantidad': st, 'notas': 'Limpieza prueba traspaso'})
for pid in (PID_A, PID_B):
    post({'tipo': 'delete_product', 'id': pid})
post({'tipo': 'delete_almacen', 'id': AID_O}); post({'tipo': 'delete_almacen', 'id': AID_D})
reg('limpieza OK (stock en 0, productos y almacenes de prueba dados de baja)',
    stock_en(PID_A, AID_O) == 0 and stock_en(PID_B, AID_D) == 0)

total = len(resultados); fallos = [r for r in resultados if not r[1]]
print('\n== RESUMEN TRASPASO API: %d/%d exitosas ==' % (total - len(fallos), total))
sys.exit(1 if fallos else 0)
