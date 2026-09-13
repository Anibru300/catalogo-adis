#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migración M5 (one-off): apps-script.gs modular en archivos .gs.

Corte seguro (sin tocar lógica):
- Los handlers están INLINE dentro de doGetInterno/doPostInterno: NO se pueden
  mover a archivos sin refactor (diferido a la fase de envelope/rediseño).
- Lo que SÍ se extrae: funciones de nivel superior auto-contenidas del módulo
  09_MARKETING (origenDe_, dispositivoDe_, navegadorDe_, trackProtegido).
  En JS las declaraciones de función histan; el orden de concatenación no
  cambia el comportamiento.

Estructura resultante:
- 00_CORE/backend/core.gs        : constantes, helpers, auth, doGet/doPost (dispatch con handlers inline)
- 09_MARKETING/backend/analitica.gs : tracker + clasificadores
- 50_BUILD/concat_backend.py     : concatena en orden -> admin/apps-script.gs (artefacto de despliegue, flujo intacto)
"""
import pathlib

ROOT = pathlib.Path(r'C:\Users\Carlos\Desktop\Pagina')
GS = ROOT / 'admin' / 'apps-script.gs'
BAK = ROOT / 'backups' / 'apps_script_pre_m5.gs'
if not BAK.exists():
    BAK.write_bytes(GS.read_bytes())

text = GS.read_bytes().decode('utf-8')
lines = text.splitlines(keepends=True)
N = len(lines)

def chunk(a, b):
    return ''.join(lines[a - 1:b])

# Rangos extraidos (1-based, verificados contra grep de estructura)
R_ORIGEN = (229, 240)    # function origenDe_
R_DISPOS = (241, 247)    # function dispositivoDe_
R_NAV = (248, 262)       # function navegadorDe_
R_TRACK = (1845, N)      # function trackProtegido hasta EOF

for (a, b), fname in [(R_ORIGEN, 'origenDe_'), (R_DISPOS, 'dispositivoDe_'), (R_NAV, 'navegadorDe_'), (R_TRACK, 'trackProtegido')]:
    seg = chunk(a, b)
    assert seg.startswith(f'function {fname}'), f'{fname}: inicio inesperado: {seg[:60]!r}'
    print(f'OK  {fname}: lineas {a}-{b} ({len(seg.splitlines())} lineas)')

core = chunk(1, R_ORIGEN[0] - 1) + chunk(R_NAV[1] + 1, R_TRACK[0] - 1)
marketing = chunk(*R_ORIGEN) + chunk(*R_DISPOS) + chunk(*R_NAV) + chunk(*R_TRACK)

# sanity: core + marketing contienen exactamente las lineas del original
resto = text.replace(chunk(*R_ORIGEN), '', 1).replace(chunk(*R_DISPOS), '', 1).replace(chunk(*R_NAV), '', 1).replace(chunk(*R_TRACK), '', 1)
assert core == resto, 'core.gs debe ser el original sin los 4 chunks extraidos'
assert marketing == chunk(*R_ORIGEN) + chunk(*R_DISPOS) + chunk(*R_NAV) + chunk(*R_TRACK)
assert len(core) + len(marketing) == len(text), 'no se pierden ni se crean bytes'

cdir = ROOT / '00_CORE' / 'backend'
cdir.mkdir(parents=True, exist_ok=True)
(cdir / 'core.gs').write_bytes(core.encode('utf-8'))
m = ROOT / '09_MARKETING' / 'backend'
m.mkdir(parents=True, exist_ok=True)
(m / 'analitica.gs').write_bytes(marketing.encode('utf-8'))
print(f'OK  00_CORE/backend/core.gs ({len(core.splitlines())} lineas)')
print(f'OK  09_MARKETING/backend/analitica.gs ({len(marketing.splitlines())} lineas)')

readme = '''# Backend modular (Apps Script) — estado M5

## Archivos fuente
| Archivo | Contenido |
|---|---|
| `00_CORE/backend/core.gs` | Constantes (SHEET_*, ENC_*, credenciales, HOJAS_BORRABLES), helpers (json, conErrores, conLock, hoja, cfg, folios, aBase, snapStock, **aplicarMovimiento**, filaPorId, log_), auth (tokens) y los dispatchers `doGetInterno`/`doPostInterno` con los handlers inline. |
| `09_MARKETING/backend/analitica.gs` | `trackProtegido` (rate-limit, dedup, archivo) + clasificadores `origenDe_`/`dispositivoDe_`/`navegadorDe_`. |

## Por qué los handlers siguen en core.gs
Los handlers están **inline** dentro de los dispatchers. Moverlos exige refactor
de lógica (prohibido en la fase M: solo extracción). Se hará junto con la
migración al envelope `{ok,data,error}` (rediseño de API), no antes.

## Mapa de handlers inline por módulo (líneas de core.gs)
| Módulo | Handlers (tipo POST) / actions (GET) |
|---|---|
| 01_EXISTENCIAS | save_product, update_precios, delete_product, restore_product, import_productos, save_almacen, delete_almacen, movimiento · GET productos/almacenes/stock/movimientos |
| 02_COMPRAS | save_proveedor, delete_proveedor, save_oc, cambiar_estado_oc, recibir_oc · GET proveedores/oc |
| 03_COMERCIAL | lead (público), save_cliente, delete_cliente · GET leads/clientes |
| 04_COTIZADOR | quote, set_estado_quote, crear_proyecto_desde_cotizacion · GET quotes |
| 05_PROYECTOS | save_proyecto, proyecto_mov, cambiar_estado_proyecto · GET proyectos |
| 06_VENTAS_COBROS | venta, registrar_cobro, anular_venta · GET ventas/cxc |
| 07_GASTOS_PAGOS | gasto, gasto_pago/registrar_pago, gasto_cancelar, delete_gasto · GET gastos/pagos/cxp |
| 08_RESULTADOS | (solo lectura) · GET estado_resultados/flujo_caja/alertas |
| 09_MARKETING | review, delete_review · GET reviews/reviews_admin/visitas · track (público, en analitica.gs) |
| 11_SISTEMA | config, delete_row, admin_purge |
| 00_CORE | login, logout, me |

## Despliegue (sin cambios)
`python 50_BUILD/concat_backend.py` regenera `admin/apps-script.gs` (concatenación
en orden). El dueño sigue pegando **ese archivo** en Apps Script e implementando
✏️ Nueva versión. Validar sintaxis: `node --check admin/apps-script.gs`.
'''
(cdir / 'README.md').write_text(readme, encoding='utf-8')

concat = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Concatena los .gs modulares en admin/apps-script.gs (artefacto de despliegue).

El orden del MANIFIESTO es funcional: las asignaciones var de nivel superior en
core.gs deben ejecutarse antes que cualquier llamada en tiempo de carga.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFIESTO = [
    '00_CORE/backend/core.gs',
    '09_MARKETING/backend/analitica.gs',
]

parts = [(ROOT / rel).read_bytes().decode('utf-8') for rel in MANIFIESTO]
out = ''.join(parts)
if not out.endswith('\\n'):
    out += '\\n'
(ROOT / 'admin' / 'apps-script.gs').write_bytes(out.encode('utf-8'))
print(f'admin/apps-script.gs regenerado ({len(MANIFIESTO)} partes, {len(out.splitlines())} lineas)')
'''
bdir = ROOT / '50_BUILD'
bdir.mkdir(exist_ok=True)
(bdir / 'concat_backend.py').write_text(concat, encoding='utf-8')
print('OK  50_BUILD/concat_backend.py')
print('OK  00_CORE/backend/README.md')
