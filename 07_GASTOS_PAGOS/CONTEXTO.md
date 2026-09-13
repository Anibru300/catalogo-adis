# 📉 07_GASTOS_PAGOS — Gastos, Pagos y CxP

> NIVEL 2 · Lee primero `00_CORE/CONTEXTO_GLOBAL.md` (§3 regla 6, §7 folios, §8
> moneda). Fuente: `admin/index.html`, `admin/apps-script.gs`,
> `scripts/auditoria/test_fase5_api.py`.

## IDENTIDAD

- **Objetivo**: registrar los gastos del negocio, pagarlos (totales o parciales)
  y mantener las cuentas por pagar, separando el gasto (hecho contable) del pago
  (salida de efectivo).
- **Responsabilidad**: hojas Gastos y Pagos; tab `expenses` (gastos + CxP).
- **Problema que resuelve**: responder "¿a quién le debemos y cuánto?" y "¿cuánto
  dinero REALMENTE salió este mes?" (junto con 08).

## ALCANCE

- **Hace**: alta de gastos por categoría con moneda y conversión, pagos
  totales/parciales con folio PAG-, cancelación lógica de gastos, CxP calculada
  (gastos no cancelados − pagos reales), borrado físico (legado).
- **NO hace**: registrar la OC que originó el gasto (02 — deuda: el gasto
  captura proveedor como texto libre), flujo de caja (08 lo consume), resultados
  (08).
- **Pertenecen aquí**: hojas Gastos, Pagos; tab `expenses`.

## DATOS

- **Hojas**: `Gastos` (ENC_GASTOS: fecha, categoria, descripcion, monto, moneda,
  tipo_cambio, monto_base, id, folio, usuario, estado, pagado — `apps-script.gs`
  L90), `Pagos` (ENC_PAGOS: id, folio, gasto_id, gasto_folio, categoria, fecha,
  monto, moneda, monto_base, metodo, notas, usuario — L92).
- **Consume**: Config (`folio_gasto`, `folio_pago`, `tipo_cambio`); proveedores
  del directorio (02) solo como sugerencia de texto.
- **Genera**: filas Gastos/Pagos; `monto_base` siempre en moneda base.

## DEPENDENCIAS

- **DEPENDE DE**: `00_CORE`. Referencia futura: `02_COMPRAS` (CxP de OC — hoy
  el gasto se registra manual, sin oc_id).
- **ALIMENTA A**: `08_RESULTADOS` (gastos por categoría en P&L; pagos en flujo
  de caja).
- **COMPARTE CON**: 08 (lectura agregada), 02 (proveedores).

## REGLAS DE NEGOCIO

1. **`gasto ≠ pago`**: el gasto nace ACTIVO/pendiente; los pagos lo van
   cubriendo (PENDIENTE→PARCIAL→PAGADA); `gasto_cancelar` es baja lógica
   (estado CANCELADA) — fuente oficial: CONTEXTO_GLOBAL §3.6.
2. Todo monto se persiste en moneda original + `monto_base` (conversión con
   `aBase` y tipo_cambio de Config).
3. `delete_gasto` sigue siendo **borrado físico** (Gastos ∈ HOJAS_BORRABLES) por
   compatibilidad; la vía preferida es `gasto_cancelar`. Revisar antes de usar
   `delete_gasto` en código nuevo.
4. Gastos cancelados quedan excluidos del P&L (fase 5) y de CxP.

## API / BACKEND

| Endpoint | Tipo | Detalle |
|---|---|---|
| `gastos` | GET | Todos |
| `pagos` | GET | Todos |
| `cxp` | GET | Gastos no cancelados vs pagos reales (saldo por gasto) |
| `gasto` | POST | `{fecha, categoria, descripcion, monto, moneda, tipo_cambio?, metodo?, notas}` → folio GAS- |
| `gasto_pago` / `registrar_pago` | POST | `{gasto_id, monto, moneda, metodo, notas}` → folio PAG-; actualiza `pagado`/estado |
| `gasto_cancelar` | POST | Baja lógica (estado CANCELADA) |
| `delete_gasto` | POST | Borrado físico (legado; acepta id + row como respaldo) |

- Handlers: `apps-script.gs` L1267–1360. Errores: `VALIDACION` (monto > 0),
  `NO_ENCONTRADO`.

## FRONTEND (tab `expenses`)

- **Vista**: tabla de gastos con estado, CxP con saldos y botón Pagar.
- **Funciones clave**: `addExpense` L2849, `renderExpenses` L2859, `renderCXP`
  L2878, `showPagoForm` L2901, `savePago` L2914, `cancelarGasto` L2924.
- **Estados**: cache de gastos en cliente; filtros por categoría/fecha en UI.

## PERMISOS

Token admin (rol único). Sin endpoints públicos.

## ARCHIVOS

| Archivo | Responsabilidad |
|---|---|
| `admin/index.html` L2849–2936 | UI gastos + pagos + CxP |
| `admin/apps-script.gs` L90, L92, L1267–1360 | esquemas + handlers |
| `scripts/auditoria/test_fase5_api.py` | suite API (folio, pagos parciales, CxP, cancelar, P&L excluye cancelados) |

## INTEGRACIONES

- Sheets (Gastos, Pagos) · Apps Script · 08 (P&L y flujo de caja) · 02
  (proveedores, como texto libre hoy).

## QUÉ NO MODIFICAR

- La retrocompatibilidad de `delete_gasto` (id + row) hasta que el frontend viejo
  deje de usarse.
- El contrato `gasto_pago`/`registrar_pago` (alias dual).
- ENC_GASTOS/ENC_PAGOS: columnas nuevas solo al final.

## PRUEBAS

- `python scripts/auditoria/test_fase5_api.py` (tras redeploy).
- Casos críticos: gasto con folio GAS-, pago parcial actualiza estado, cancelar
  excluye del P&L y de CxP, conversión de moneda correcta.
- Tras modificar: fase5 + regresión fase0.

## EJEMPLOS DE INTERACCIÓN

1. **Pago parcial (07→08)**: gasto $50k → pago $20k (PAG-) → CxP muestra $30k;
   flujo de caja cuenta $20k salidos (no $50k — efectivo real).
2. **Proveedor de compra (02→07, hoy manual)**: la recepción de OC no genera
   gasto automático; el usuario registra el gasto a mano con el proveedor como
   texto (mejora futura: CxP de OC con oc_id).
