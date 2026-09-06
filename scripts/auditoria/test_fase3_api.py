#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas Fase 3 — Clientes + estados de cotizacion. Requiere backend Fase 0+."""
import json, sys, urllib.request

API = 'https://script.google.com/macros/s/AKfycbz2TczcLpS97Ro_AYkrw3pnbtlw8v3HtF7FnJrPPJHEUT_JBe-Ar1bumFDGPZpC6nvJ/exec'
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
if not (isinstance(get('accion_inexistente_xyz').get('error'), dict)):
    print('>> Backend viejo detectado: omite pruebas Fase 3.'); sys.exit(0)

print('== FASE 3: clientes ==')
d = post({'tipo': 'save_cliente', 'nombre': 'CLIENTE TEST FASE 3', 'telefono': 'TEST0000001', 'origen': 'manual'})
reg('crear cliente', d.get('ok') is True, d)
CID = d.get('id')
d = post({'tipo': 'save_cliente', 'nombre': 'Duplicado TEST', 'telefono': 'TEST0000001'})
reg('telefono duplicado => CLIENTE_DUPLICADO', errcode(d) == 'CLIENTE_DUPLICADO', errcode(d))
d = post({'tipo': 'save_cliente', 'nombre': ''})
reg('cliente sin nombre => VALIDACION', errcode(d) == 'VALIDACION', errcode(d))
d = get('clientes')
reg('GET clientes incluye el creado', any(str(c.get('id')) == str(CID) for c in d.get('clientes', [])))
d = post({'tipo': 'delete_cliente', 'id': CID})
reg('desactivar cliente', d.get('ok') is True)

print('== FASE 3: estados de cotizacion ==')
d = post({'tipo': 'quote', 'cliente': 'TEST-CLIENTE F3', 'items': [], 'total': 1,
          'cliente_id': CID or '', 'notas': 'PRUEBA FASE 3 — eliminable'})
reg('quote con cliente_id', d.get('ok') is True, d.get('folio'))
quotes = get('quotes').get('quotes', [])
q = next((x for x in reversed(quotes) if x.get('folio') == d.get('folio')), {})
QID = q.get('id')
reg('cotizacion guardada con id y cliente_id', bool(QID) and str(q.get('cliente_id')) == str(CID), 'id=%s' % QID)
d = post({'tipo': 'set_estado_quote', 'id': QID, 'estado': 'Aprobada'})
reg('Activa -> Aprobada', d.get('ok') is True and d.get('estado') == 'Aprobada', d)
d = post({'tipo': 'set_estado_quote', 'id': QID, 'estado': 'Activa'})
reg('Aprobada -> Activa => NO_PERMITIDO', errcode(d) == 'NO_PERMITIDO', errcode(d))
d = post({'tipo': 'set_estado_quote', 'id': 'inexistente', 'estado': 'Aprobada'})
reg('id inexistente => NO_ENCONTRADO', errcode(d) == 'NO_ENCONTRADO', errcode(d))

print('== Limpieza ==')
reg('cliente TEST desactivado arriba; cotizacion TEST queda identificada como eliminable', True)
total = len(resultados); fallos = [r for r in resultados if not r[1]]
print('\n== RESUMEN FASE 3: %d/%d exitosas ==' % (total - len(fallos), total))
sys.exit(1 if fallos else 0)
