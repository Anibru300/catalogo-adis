#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migración M4 (one-off): admin/index.html se ensambla desde partes modulares.

- CSS del panel  -> 00_CORE/design-system/admin.css
- JS del panel   -> 00_CORE/shared_js/admin_{core,nav}.js + <MODULO>/admin/*.js
- admin/plantilla.html: HTML con marcadores /*__ADMIN_CSS__*/ y /*__ADMIN_JS__*/
- 50_BUILD/build_admin.py: ensambla admin/index.html (bytes, preserva CRLF)

Verificación: el admin/index.html ensamblado debe ser idéntico al original.
"""
import pathlib

ROOT = pathlib.Path(r'C:\Users\Carlos\Desktop\Pagina')
ADMIN = ROOT / 'admin' / 'index.html'
BAK = ROOT / 'backups' / 'admin_index_pre_m4.html'
BAK.write_bytes(ADMIN.read_bytes())  # respaldo para verificación

text = ADMIN.read_bytes().decode('utf-8')
lines = text.splitlines(keepends=True)

s0 = next(i for i, l in enumerate(lines) if l.strip() == '<style>')
s1 = next(i for i, l in enumerate(lines) if l.strip() == '</style>')
j0 = next(i for i, l in enumerate(lines) if l.strip() == '<script>')
j1 = next(i for i, l in enumerate(lines) if l.strip() == '</script>')

css_inner = ''.join(lines[s0 + 1:s1])
script = lines[j0 + 1:j1]
assert len(script) == 2145, f'script inesperado: {len(script)} lineas'

# ---- parte JS: rangos (1-based dentro del script) verificados por banner
PARTS = [  # (archivo, inicio, fin, texto esperado en la linea de inicio)
    ('00_CORE/shared_js/admin_core.js',        1, 105,  '===='),
    ('08_RESULTADOS/admin/dashboard.js',       106, 152,  'dashboard ejecutivo'),
    ('00_CORE/shared_js/admin_nav.js',         153, 243,  'Ctrl+K'),
    ('09_MARKETING/admin/flujo.js',            244, 306,  'flujo (visitas'),
    ('03_COMERCIAL/admin/comercial.js',        307, 373,  'leads'),
    ('04_COTIZADOR/admin/cotizador_simple.js', 374, 467,  'cotizaciones'),
    ('04_COTIZADOR/admin/cotizador_pro.js',    468, 996,  'COTIZADOR PROFESIONAL'),
    ('09_MARKETING/admin/resenas.js',          997, 1025, 'rese'),
    ('01_EXISTENCIAS/admin/existencias.js',    1026, 1495, '===='),
    ('02_COMPRAS/admin/compras.js',            1496, 1694, '===='),
    ('05_PROYECTOS/admin/proyectos.js',        1695, 1842, '===='),
    ('06_VENTAS_COBROS/admin/ventas.js',       1843, 1902, 'ventas'),
    ('07_GASTOS_PAGOS/admin/gastos.js',        1903, 1990, 'gastos'),
    ('08_RESULTADOS/admin/resultados.js',      1991, 2135, 'FASE 5'),
    ('11_SISTEMA/admin/sistema.js',            2136, 2145, "window.addEventListener('load'"),
]

slices = []
for rel, a, b, expect in PARTS:
    first = script[a - 1]
    assert expect in first, f'{rel}: se esperaba "{expect}" en script:{a}, hay: {first.strip()[:70]}'
    chunk = ''.join(script[a - 1:b])
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(chunk.encode('utf-8'))
    slices.append(chunk)
    print(f'OK  {rel}  ({b - a + 1} lineas)')

# ---- CSS
(ROOT / '00_CORE' / 'design-system').mkdir(exist_ok=True)
(ROOT / '00_CORE' / 'design-system' / 'admin.css').write_bytes(css_inner.encode('utf-8'))
print(f'OK  00_CORE/design-system/admin.css  ({len(css_inner.splitlines())} lineas)')

# ---- plantilla con marcadores (bytes exactos)
new_text = text.replace(css_inner, '/*__ADMIN_CSS__*/', 1)
assert new_text != text
new_text = new_text.replace(''.join(script), '/*__ADMIN_JS__*/', 1)
assert '/*__ADMIN_JS__*/' in new_text
(ROOT / 'admin' / 'plantilla.html').write_bytes(new_text.encode('utf-8'))
print('OK  admin/plantilla.html (marcadores)')

# ---- verificación: reensamblar y comparar
reassembled = new_text.replace('/*__ADMIN_CSS__*/', css_inner, 1).replace('/*__ADMIN_JS__*/', ''.join(script), 1)
assert reassembled == text, 'REENSAMBLAJE NO IDENTICO'
print('OK  verificacion: reensamblaje byte-identico')

# ---- build_admin.py
build = '''#!/usr/bin/env python3
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
'''
bdir = ROOT / '50_BUILD'
bdir.mkdir(exist_ok=True)
(bdir / 'build_admin.py').write_text(build, encoding='utf-8')
print('OK  50_BUILD/build_admin.py')
