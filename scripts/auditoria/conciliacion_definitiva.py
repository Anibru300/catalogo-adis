# -*- coding: utf-8 -*-
"""Conciliacion definitiva de naturalezas (decisiones del dueno 2026-11-06).
Solo genera el documento de aprobacion; NO escribe en produccion."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
d = json.load(open(ROOT / '60_DATA/revision_gastos_2026-11-06.json', encoding='utf-8'))
gastos = d['gastos']

# ===== NATURALEZAS DEFINITIVAS (autorizadas para preparar, NO aplicadas) =====
DEF = {
    # RETIRO (17)
    'GAS-2026-0004': 'retiro', 'GAS-2026-0009': 'retiro', 'GAS-2026-0010': 'retiro',
    'GAS-2026-0025': 'retiro', 'GAS-2026-0029': 'retiro', 'GAS-2026-0030': 'retiro',
    'GAS-2026-0031': 'retiro', 'GAS-2026-0032': 'retiro', 'GAS-2026-0034': 'retiro',
    'GAS-2026-0036': 'retiro', 'GAS-2026-0038': 'retiro', 'GAS-2026-0041': 'retiro',
    'GAS-2026-0046': 'retiro', 'GAS-2026-0050': 'retiro', 'GAS-2026-0051': 'retiro',
    'GAS-2026-0055': 'retiro', 'GAS-2026-0056': 'retiro',
    # INVENTARIO (9)
    'GAS-2026-0005': 'inventario', 'GAS-2026-0006': 'inventario', 'GAS-2026-0013': 'inventario',
    'GAS-2026-0014': 'inventario', 'GAS-2026-0018': 'inventario', 'GAS-2026-0019': 'inventario',
    'GAS-2026-0020': 'inventario', 'GAS-2026-0039': 'inventario', 'GAS-2026-0040': 'inventario',
    # INVERSION (2)
    'GAS-2026-0011': 'inversion', 'GAS-2026-0016': 'inversion',
    # OPERATIVO (21)
    'GAS-2026-0001': 'operativo', 'GAS-2026-0002': 'operativo', 'GAS-2026-0003': 'operativo',
    'GAS-2026-0007': 'operativo', 'GAS-2026-0008': 'operativo', 'GAS-2026-0012': 'operativo',
    'GAS-2026-0015': 'operativo', 'GAS-2026-0017': 'operativo', 'GAS-2026-0033': 'operativo',
    'GAS-2026-0035': 'operativo', 'GAS-2026-0037': 'operativo', 'GAS-2026-0042': 'operativo',
    'GAS-2026-0043': 'operativo', 'GAS-2026-0044': 'operativo', 'GAS-2026-0045': 'operativo',
    'GAS-2026-0047': 'operativo', 'GAS-2026-0048': 'operativo', 'GAS-2026-0049': 'operativo',
    'GAS-2026-0052': 'operativo', 'GAS-2026-0053': 'operativo', 'GAS-2026-0054': 'operativo',
}

filas = []
for g in sorted(gastos, key=lambda x: str(x.get('folio'))):
    f = str(g.get('folio'))
    est = str(g.get('estado'))
    nat = 'cancelado' if est == 'CANCELADA' else DEF.get(f)
    assert nat is not None or est == 'CANCELADA', f'folio sin clasificar: {f}'
    filas.append({
        'folio': f, 'fecha': str(g.get('fecha'))[:10], 'desc': str(g.get('descripcion') or '—'),
        'monto': float(g.get('monto') or 0), 'moneda': g.get('moneda'),
        'tc': g.get('tipo_cambio'), 'base': float(g.get('monto_base') or 0),
        'cat': str(g.get('categoria')), 'estado': est, 'nat': nat,
    })

activos = [x for x in filas if x['estado'] == 'ACTIVA']
cancelados = [x for x in filas if x['estado'] == 'CANCELADA']
total_activos = sum(x['base'] for x in activos)
assert len(activos) == 49, f'activos={len(activos)}'
assert len(cancelados) == 7, f'cancelados={len(cancelados)}'
assert abs(total_activos - 97371.04) < 0.01, f'total={total_activos}'
# sin duplicados ni omisiones
folios = [x['folio'] for x in activos]
assert len(set(folios)) == 49

nats = ['inventario', 'operativo', 'retiro', 'inversion']
tot = {n: sum(x['base'] for x in activos if x['nat'] == n) for n in nats}
cnt = {n: sum(1 for x in activos if x['nat'] == n) for n in nats}

nombres = {'inventario': 'Compra de inventario', 'operativo': 'Gasto operativo',
           'retiro': 'Retiro del propietario', 'inversion': 'Inversion en activos'}

L = []
L.append('# CONCILIACION DEFINITIVA — CLASIFICACION DE LOS 49 GASTOS ACTIVOS\n')
L.append('> Fecha: 2026-11-06 · Decisiones del propietario incorporadas · SOLO LECTURA.')
L.append('> Preparado para aprobacion final. `reclasificar_fase1.py --aplicar` NO ha sido ejecutado.\n')

L.append('## 1) LAS CINCO GASOLINAS (operativo, segun decision del dueno)\n')
L.append('| Folio | Fecha | Concepto | Importe | Moneda | TC historico | MXN base |')
L.append('|---|---|---|---:|---|---:|---:|')
for x in activos:
    if x['folio'] in ('GAS-2026-0002', 'GAS-2026-0012', 'GAS-2026-0033', 'GAS-2026-0045', 'GAS-2026-0053'):
        L.append(f"| {x['folio']} | {x['fecha']} | {x['desc'][:40]} | {x['monto']:,.2f} | {x['moneda']} | {x['tc']} | {x['base']:,.2f} |")
L.append('')
L.append('## 2) LOS CUATRO CONSUMOS DE ALIMENTOS (operativo, segun decision del dueno)\n')
L.append('| Folio | Fecha | Concepto | Importe | Moneda | TC historico | MXN base |')
L.append('|---|---|---|---:|---|---:|---:|')
for x in activos:
    if x['folio'] in ('GAS-2026-0007', 'GAS-2026-0017', 'GAS-2026-0047', 'GAS-2026-0052'):
        L.append(f"| {x['folio']} | {x['fecha']} | {x['desc'][:40]} | {x['monto']:,.2f} | {x['moneda']} | {x['tc']} | {x['base']:,.2f} |")
L.append('')

L.append('## 3) TABLA DEFINITIVA POR FOLIO (49 activos, agrupados por naturaleza)\n')
for n in nats:
    sub = [x for x in activos if x['nat'] == n]
    L.append(f"### {nombres[n]} — {cnt[n]} movimientos · ${tot[n]:,.2f} MXN ({tot[n]/total_activos*100:.2f}% del total)\n")
    L.append('| Folio | Fecha | Concepto original | Importe | Mon | TC | MXN base | Categoria actual |')
    L.append('|---|---|---|---:|---|---:|---:|---|')
    for x in sub:
        L.append(f"| {x['folio']} | {x['fecha']} | {x['desc'][:45].replace('|','/')} | "
                 f"{x['monto']:,.2f} | {x['moneda']} | {x['tc']} | {x['base']:,.2f} | {x['cat'][:24].replace('|','/')} |")
    L.append('')

L.append('## 4) RESUMEN FINANCIERO CONCILIADO\n')
L.append('| Naturaleza | Movimientos | Total MXN | % del total |')
L.append('|---|---:|---:|---:|')
for n in nats:
    L.append(f"| {nombres[n]} | {cnt[n]} | ${tot[n]:,.2f} | {tot[n]/total_activos*100:.2f}% |")
L.append(f'| **TOTAL ACTIVOS** | **49** | **${total_activos:,.2f}** | **100.00%** |')
L.append(f"\nCancelados excluidos: 7 movimientos de prueba ($7.00 MXN): "
         + ', '.join(x['folio'] for x in cancelados) + '.\n')

L.append('## 5) INCONSISTENCIAS CATEGORIA ACTUAL vs NATURALEZA DEFINITIVA\n')
incons = []
for x in activos:
    c, n = x['cat'], x['nat']
    msg = None
    if c == 'Inversión' and n == 'operativo':
        msg = 'categoria "Inversion" pero es gasto del periodo -> operativo'
    if c == 'Gastos personales' and n != 'retiro':
        msg = 'categoria personal con naturaleza no-retiro'
    if c == 'Otro' and n == 'inventario':
        msg = 'categoria "Otro" que en realidad es mercancia -> inventario'
    if c == 'Equipos' and n == 'operativo':
        msg = 'categoria "Equipos" pero son camisolas (consumible) -> operativo'
    if c in ('Materiales', 'Compra de material') and n == 'inventario':
        msg = 'categoria material; segun dueno es mercancia para reventa -> inventario'
    if msg:
        incons.append(f"- **{x['folio']}** ({x['desc'][:35]}, ${x['base']:,.2f}): {msg}.")
L.extend(incons)
L.append('\n> Nota: la categoria se conserva como descriptiva; la naturaleza manda el')
L.append('> tratamiento contable. Renombrar categorias es opcional y NO esta en este cambio.\n')

L.append('## 6) MOVIMIENTOS SENSIBLES (decision tomada; reversibles individualmente)\n')
L.append('- **GAS-2026-0034** gastos medicos $7,000 -> retiro (uso personal).')
L.append('- **GAS-2026-0031** medicina $600 -> retiro.')
L.append('- **GAS-2026-0055** "otro, condina o tanda" $3,000 -> retiro (compromiso personal).')
L.append('- **GAS-2026-0038** tiras LED $1,800 -> retiro (segun tu decision; categoria decia personal).')
L.append('- **GAS-2026-0025** ajuste menor $1 -> retiro (segun tu decision).')
L.append('- **GAS-2026-0047 / 0056 / 0046** sin descripcion ($500 / $600 / $1,200) -> clasificados')
L.append('  por categoria (operativo / retiro / retiro). Revisables individualmente con un solo comando.\n')

L.append('## 7) GARANTIAS DE LA RECLASIFICACION (que NO toca)\n')
L.append('- `gasto_clasificar` solo escribe la **columna 13 (naturaleza)** de la fila del gasto.')
L.append('- No modifica: importes (col 4), moneda (5), tipo de cambio (6), monto_base (7),')
L.append('  fecha (1), categoria (2), descripcion (3), folio (10), estado (11), pagado (12).')
L.append('- No toca la hoja Pagos (los pagos y su TC quedan intactos), ni inventario, ni folios.')
L.append('- Cada cambio queda en la bitacora como `gasto_clasificado <folio> · <anterior> → <nueva>`.')
L.append('- Es reversible: reclasificar de vuelta a `por_clasificar` restaura el estado actual.\n')

L.append('## 8) PLAN DE APLICACION (pendiente de tu autorizacion expresa)\n')
L.append('1. `python scripts/auditoria/reclasificar_fase1.py` (dry-run: muestra este plan).')
L.append('2. `ADIS_RECLASIFICAR_PROD=si python scripts/auditoria/reclasificar_fase1.py --aplicar`')
L.append('   (el script exige esta variable explicita en produccion).')
L.append('3. Verificacion posterior (solo lectura): control_ie muestra la distribucion real;')
L.append('   retiros ~$24,804.72; el P&L deja de tener "sin clasificar".')

out = '\n'.join(L)
dest = ROOT / '99_DOCUMENTACION/CONCILIACION_DEFINITIVA_CLASIFICACION_2026-11-06.md'
dest.write_text(out, encoding='utf-8')
print(f'OK -> {dest}')
print(f'\nTOTAL ACTIVOS: ${total_activos:,.2f} (verificado == 97,371.04)')
for n in nats:
    print(f'  {nombres[n]:<26} {cnt[n]:>2} mov · ${tot[n]:>10,.2f} · {tot[n]/total_activos*100:>6.2f}%')
print(f'  cancelados excluidos: {len(cancelados)}')
print(f'  inconsistencias categoria-naturaleza: {len(incons)}')
