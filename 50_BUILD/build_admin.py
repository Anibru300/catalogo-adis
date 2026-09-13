#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ensambla admin/index.html desde la plantilla y las partes modulares (M4).

Partes (en orden de concatenacion — respeta el orden original del script):
  ver MANIFIESTO abajo. Salida byte-identica al monolito original.

Uso: python 50_BUILD/build_admin.py   (o se invoca desde build_sitio)
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLANTILLA = ROOT / 'admin' / 'plantilla.html'
SALIDA = ROOT / 'admin' / 'index.html'

# (ruta relativa al repo). El ORDEN es funcional: los statements de nivel
# superior (state/lets/addEventListener) deben ejecutarse en este orden.
MANIFIESTO = [
    '00_CORE/shared_js/admin_core.js',
    '08_RESULTADOS/admin/dashboard.js',
    '00_CORE/shared_js/admin_nav.js',
    '09_MARKETING/admin/flujo.js',
    '03_COMERCIAL/admin/comercial.js',
    '04_COTIZADOR/admin/cotizador_simple.js',
    '04_COTIZADOR/admin/cotizador_pro.js',
    '09_MARKETING/admin/resenas.js',
    '01_EXISTENCIAS/admin/existencias.js',
    '02_COMPRAS/admin/compras.js',
    '05_PROYECTOS/admin/proyectos.js',
    '06_VENTAS_COBROS/admin/ventas.js',
    '07_GASTOS_PAGOS/admin/gastos.js',
    '08_RESULTADOS/admin/resultados.js',
    '11_SISTEMA/admin/sistema.js',
]


def ensamblar():
    css = (ROOT / '00_CORE' / 'design-system' / 'admin.css').read_bytes().decode('utf-8')
    js = ''.join((ROOT / rel).read_bytes().decode('utf-8') for rel in MANIFIESTO)
    html = PLANTILLA.read_bytes().decode('utf-8')
    assert '/*__ADMIN_CSS__*/' in html and '/*__ADMIN_JS__*/' in html, 'plantilla sin marcadores'
    html = html.replace('/*__ADMIN_CSS__*/', css, 1).replace('/*__ADMIN_JS__*/', js, 1)
    SALIDA.write_bytes(html.encode('utf-8'))  # bytes: preserva CRLF
    print(f'admin/index.html ensamblado ({len(MANIFIESTO)} partes + CSS)')


if __name__ == '__main__':
    ensamblar()
