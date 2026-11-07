# -*- coding: utf-8 -*-
"""Genera el reporte de clasificacion de los 56 gastos (SOLO LECTURA)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
d = json.load(open(ROOT / '60_DATA/revision_gastos_2026-11-06.json', encoding='utf-8'))
gastos = d['gastos']

# Clasificacion propuesta: folio -> (naturaleza, confianza, justificacion)
C = {
    # RETIRO (gastos personales del propietario)
    'GAS-2026-0004': ('retiro', 'alto', 'Gastos personales de la casa'),
    'GAS-2026-0009': ('retiro', 'alto', 'Remodelacion de casa personal'),
    'GAS-2026-0010': ('retiro', 'alto', 'Insumos personales'),
    'GAS-2026-0029': ('retiro', 'alto', 'Limpieza de casa'),
    'GAS-2026-0030': ('retiro', 'alto', 'Gasto en el Oxxo (personal)'),
    'GAS-2026-0031': ('retiro', 'alto', 'Gasto en medicina personal'),
    'GAS-2026-0032': ('retiro', 'alto', 'Manutencion personal'),
    'GAS-2026-0034': ('retiro', 'alto', 'Gastos medicos personales (7,000)'),
    'GAS-2026-0036': ('retiro', 'alto', 'Gastos de la casa (200 USD)'),
    'GAS-2026-0041': ('retiro', 'alto', 'Gastos casa'),
    'GAS-2026-0046': ('retiro', 'alto', 'Sin descripcion; categoria Gastos personales'),
    'GAS-2026-0050': ('retiro', 'alto', 'Gastos de casa'),
    'GAS-2026-0051': ('retiro', 'alto', 'Comida personal'),
    'GAS-2026-0055': ('retiro', 'alto', '"otro, condina o tanda": compromiso personal'),
    'GAS-2026-0056': ('retiro', 'alto', 'Sin descripcion; categoria Gastos personales'),
    # INVENTARIO (mercancia para reventa)
    'GAS-2026-0005': ('inventario', 'alto', '5 lambrines negros + 4 Brasil "a inventario"'),
    'GAS-2026-0006': ('inventario', 'alto', '28 lambrines (mercancia)'),
    'GAS-2026-0018': ('inventario', 'alto', '6 placas PVC (mercancia)'),
    'GAS-2026-0019': ('inventario', 'alto', 'Entrada de 6 cajas de plafon rio (mercancia)'),
    'GAS-2026-0020': ('inventario', 'medio', '5 placas PVC y molduras; categoria "Compra de material"'),
    'GAS-2026-0039': ('inventario', 'medio', 'Material lambrin (mercancia tipica)'),
    'GAS-2026-0040': ('inventario', 'medio', 'Compra de lambrin (mercancia tipica)'),
    # INVERSION (activo)
    'GAS-2026-0011': ('inversion', 'alto', 'Telefono (equipo/activo del negocio)'),
    # OPERATIVO
    'GAS-2026-0001': ('operativo', 'alto', 'Honorarios al contador'),
    'GAS-2026-0015': ('operativo', 'alto', 'Nomina empleados'),
    'GAS-2026-0049': ('operativo', 'alto', 'Renta del local'),
    'GAS-2026-0054': ('operativo', 'alto', 'Contador'),
    'GAS-2026-0003': ('operativo', 'medio', 'Mantenimiento (Compra Home Depot)'),
    'GAS-2026-0035': ('operativo', 'medio', 'Camisolas de la empresa'),
    'GAS-2026-0044': ('operativo', 'alto', 'Papeleria (material indirecto)'),
    'GAS-2026-0008': ('operativo', 'alto', 'Paqueteria'),
    'GAS-2026-0042': ('operativo', 'alto', 'Paqueteria'),
    'GAS-2026-0043': ('operativo', 'alto', 'Paqueteria'),
    'GAS-2026-0037': ('operativo', 'medio', 'Relaciones publicas (gasto, no activo aunque la categoria diga Inversion)'),
    'GAS-2026-0048': ('operativo', 'medio', 'Pago de plataforma (servicio, no activo)'),
    # POR CLASIFICAR (requieren decision del dueno)
    'GAS-2026-0002': ('por_clasificar', 'medio', 'Gasolina sin contexto; probable operativo si es de trabajo'),
    'GAS-2026-0012': ('por_clasificar', 'medio', 'Combustible y viaticos a Hermosillo; probable operativo (viaje de negocio)'),
    'GAS-2026-0033': ('por_clasificar', 'bajo', '"pago de gas" 50 MXN sin contexto'),
    'GAS-2026-0045': ('por_clasificar', 'medio', 'Gasolina sin contexto'),
    'GAS-2026-0053': ('por_clasificar', 'medio', 'Gasolina 50 USD sin contexto'),
    'GAS-2026-0007': ('por_clasificar', 'bajo', 'Desayuno: operativo (equipo en ruta) o retiro (personal)'),
    'GAS-2026-0017': ('por_clasificar', 'bajo', '"Chuchucos y Monster": operativo o retiro'),
    'GAS-2026-0047': ('por_clasificar', 'bajo', 'Alimentos sin descripcion'),
    'GAS-2026-0052': ('por_clasificar', 'bajo', 'Desayuno 30 USD: operativo o retiro'),
    'GAS-2026-0013': ('por_clasificar', 'medio', 'Materiales 7,093.63: inventario (reventa) o costo_directo (obra)'),
    'GAS-2026-0014': ('por_clasificar', 'medio', 'Material 10,700: inventario (reventa) o costo_directo (obra)'),
    'GAS-2026-0016': ('por_clasificar', 'medio', 'Muestrario de cortinas: operativo (herramienta de venta) o inversion'),
    'GAS-2026-0038': ('por_clasificar', 'bajo', 'Tiras LED (Mercado Libre): categoria dice personal pero suena a material del negocio'),
    'GAS-2026-0025': ('por_clasificar', 'bajo', '"ajuste menor" de 1 MXN; sin contexto'),
}

filas = []
for g in sorted(gastos, key=lambda x: str(x.get('folio'))):
    f = str(g.get('folio'))
    nat, conf, just = C.get(f, ('por_clasificar', 'bajo', 'Sin propuesta automatica (no forzar clasificacion)'))
    filas.append({
        'folio': f, 'fecha': str(g.get('fecha'))[:10], 'desc': str(g.get('descripcion') or '—'),
        'monto': g.get('monto'), 'moneda': g.get('moneda'), 'base': float(g.get('monto_base') or 0),
        'tc': g.get('tipo_cambio'), 'cat': str(g.get('categoria')), 'estado': str(g.get('estado')),
        'nat': nat, 'conf': conf, 'just': just,
    })


def tot(nat, est):
    return sum(x['base'] for x in filas if x['nat'] == nat and x['estado'] == est)


nats = ['retiro', 'inventario', 'inversion', 'operativo', 'costo_directo', 'por_clasificar']
grupos = {n: (tot(n, 'ACTIVA'), tot(n, 'CANCELADA'),
              sum(1 for x in filas if x['nat'] == n and x['estado'] == 'ACTIVA')) for n in nats}
nombres = {'retiro': 'Retiro del propietario', 'inventario': 'Compra de inventario',
           'inversion': 'Inversion en activos', 'operativo': 'Gasto operativo',
           'costo_directo': 'Costo directo de proyecto', 'por_clasificar': 'Pendiente de clasificar'}

L = []
L.append('# REPORTE DE CLASIFICACION — 56 GASTOS HISTORICOS (ETAPA 1)\n')
L.append('> Fecha: 2026-11-06 · Fuente: produccion real (SOLO LECTURA) · **NINGUN dato fue modificado.**')
L.append('> La reclasificacion NO ha sido aplicada: este reporte es para tu revision y autorizacion.\n')
L.append('## TOTALES POR NATURALEZA PROPUESTA (MXN al tipo de cambio historico de cada registro)\n')
L.append('| Naturaleza | Movimientos activos | Total activos (MXN) | Cancelados (MXN) |')
L.append('|---|---:|---:|---:|')
for n in nats:
    a, c, na = grupos[n]
    if na or c:
        L.append(f'| {nombres[n]} | {na} | ${a:,.2f} | ${c:,.2f} |')
L.append(f'| **TOTAL** | **{sum(grupos[n][2] for n in nats)}** | '
         f'**${sum(grupos[n][0] for n in nats):,.2f}** | **${sum(grupos[n][1] for n in nats):,.2f}** |')
L.append('')
L.append('## DETALLE POR FOLIO (agrupado por naturaleza propuesta)\n')
for n in nats:
    sub = [x for x in filas if x['nat'] == n]
    if not sub:
        continue
    L.append(f'### {nombres[n]} ({len(sub)} movimientos · activos ${grupos[n][0]:,.2f})\n')
    L.append('| Folio | Fecha | Descripcion original | Importe | TC | MXN base | Categoria actual | Conf. | Justificacion |')
    L.append('|---|---|---|---:|---:|---:|---|---|---|')
    for x in sub:
        est = '' if x['estado'] == 'ACTIVA' else ' **CANCELADA**'
        desc = x['desc'][:60].replace('|', '/')
        cat = x['cat'][:26].replace('|', '/')
        just = x['just'].replace('|', '/')
        L.append(f"| {x['folio']} | {x['fecha']} | {desc} | {x['monto']:,.2f} {x['moneda']} | "
                 f"{x['tc']} | {x['base']:,.2f} | {cat} | {x['conf']} | {just}{est} |")
    L.append('')
L.append('## MOVIMIENTOS CANCELADOS (7 registros de prueba, $1 c/u)\n')
L.append('- GAS-2026-0021, -0022, -0027, -0028: pruebas de diagnostico/boton/id (sin pagos).')
L.append('- GAS-2026-0023, -0024, -0026: generados por gastos fijos de prueba "__PRUEBA__" (sin pagos).')
L.append('- Todos estan CANCELADOS (baja logica): no afectan ningun reporte. No requieren accion.\n')
L.append('## DUPLICIDADES CON COMPRAS / INVENTARIO\n')
L.append('- **No se detectaron duplicidades gasto-inventario**: la hoja Movimientos no registra')
L.append('  entradas de octubre (su ultima entrada es del 06-sep, de pruebas tecnicas). Las compras de')
L.append('  mercancia de octubre (lambrines, placas, plafones) existen SOLO como gastos GAS-.')
L.append('- **Observacion (sin accion en esta etapa)**: esas compras tampoco se registraron como')
L.append('  movimientos de entrada a inventario; si la mercancia esta fisicamente en almacen, el')
L.append('  stock no la refleja. Decision pendiente para la Etapa 2 (modulo Compras/Inventario).')
L.append('- GAS-2026-0025 ("ajuste menor", $1, con pago PAG-2026-0020): no es prueba tecnica, es un')
L.append('  ajuste real; se propone por_clasificar hasta que confirmes su motivo.\n')
L.append('## RESUMEN PARA TU AUTORIZACION\n')
L.append('Grupos listos para aplicar con `reclasificar_fase1.py --aplicar` (SOLO con tu autorizacion expresa):\n')
L.append(f"- **Retiros**: 15 folios · ${grupos['retiro'][0]:,.2f} MXN (+200 USD ya convertidos)")
L.append(f"- **Inventario**: 7 folios · ${grupos['inventario'][0]:,.2f} MXN")
L.append(f"- **Inversion**: 1 folio · ${grupos['inversion'][0]:,.2f} MXN")
L.append(f"- **Operativos**: 12 folios · ${grupos['operativo'][0]:,.2f} MXN")
L.append(f"- **Pendientes de TU decision folio por folio**: {grupos['por_clasificar'][2]} folios · "
         f"${grupos['por_clasificar'][0]:,.2f} MXN")
L.append('')
L.append('Pendientes destacados: GAS-0013/0014 (materiales grandes: reventa u obra), GAS-0016')
L.append('(muestrario), las 5 gasolinas, los 4 consumos de alimentos y GAS-0038 (tiras LED).')

out = '\n'.join(L)
dest = ROOT / '99_DOCUMENTACION/REPORTE_CLASIFICACION_GASTOS_2026-11-06.md'
dest.write_text(out, encoding='utf-8')
print(f'OK -> {dest} ({len(out)} chars)')
for n in nats:
    a, c, na = grupos[n]
    if na or c:
        print(f'  {nombres[n]:<28} activos: {na:>2} mov · ${a:>10,.2f} MXN | cancelados ${c:,.2f}')
