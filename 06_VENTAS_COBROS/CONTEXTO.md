# 💵 06_VENTAS_COBROS — Ventas, Cobros y CxC

> NIVEL 2 · Lee primero `00_CORE/CONTEXTO_GLOBAL.md` (§3 reglas 1-2 y 5-6, §7
> folios, §9 transaccionalidad). Es la **operación más crítica** del ERP junto
> con Existencias. Fuente: `admin/index.html`, `admin/apps-script.gs`,
> `scripts/auditoria/test_fase0_api.py` (concurrencia), `test_fase4_api.py`.

## IDENTIDAD

- **Objetivo**: registrar ventas que descuentan stock con trazabilidad total,
  cobrarlas (totales o parciales) y mantener las cuentas por cobrar al día.
- **Responsabilidad**: hojas Ventas y Cobros; tabs `sales` (nueva + historial) y
  `cobros` (CxC).
- **Problema que resuelve**: vender sin perder stock ni dinero: cada venta tiene
  folio, utilidad calculada y estado de cobro; cada cobro queda registrado.

## ALCANCE

- **Hace**: venta multi-producto con descuento automático de stock, folio
  VEN-AAAA-NNNN, cálculo de utilidad (precio − costo en moneda base), venta
  ligada a proyecto, cobros totales/parciales con folio COB-, CxC calculada
  (ventas no canceladas − cobros reales), anulación con repuesto de stock.
- **NO hace**: cotizar (04), mover stock por otra vía (usa `aplicarMovimiento`),
  flujo de caja (08 lo consume), gastos (07).
- **Pertenecen aquí**: hojas Ventas, Cobros; tabs `sales`, `cobros`.

## DATOS

- **Hojas**: `Ventas` (ENC_VENTAS: fecha, cliente, almacen, items, total,
  moneda, tipo_cambio, total_base, costo_total_base, utilidad_base, notas, id,
  folio, usuario, estado, cobrado, items_json, moneda_base, tipo_cambio_base,
  cliente_id, proyecto_id — `apps-script.gs` L87), `Cobros` (ENC_COBROS: id,
  folio, venta_id, venta_folio, cliente, proyecto_id, fecha, monto, …, L101).
- **Consume**: Productos/Stock (01) para items y costos; Clientes (03) para
  cliente_id; Proyectos (05) para proyecto_id; Config (folios, tipo_cambio).
- **Genera**: filas Ventas/Cobros, movimientos de salida (y de compensación o
  anulación) en Movimientos (01); `utilidad_base` al momento de la venta.

## DEPENDENCIAS

- **DEPENDE DE**: `00_CORE`; `01_EXISTENCIAS` (stock y costo — validación con
  snapshot y descuento vía `aplicarMovimiento`); `03_COMERCIAL` (cliente);
  `05_PROYECTOS` (proyecto opcional).
- **ALIMENTA A**: `08_RESULTADOS` (ingresos, utilidad, CxC), flujo de caja
  (cobros = entrada de efectivo real).
- **COMPARTE DATOS CON**: 01 (Movimientos doc VENTA/COMPENSACION/DEVOLUCION),
  05 (proyecto_id), 03 (cliente_id).

## REGLAS DE NEGOCIO

1. La venta **valida todo antes de escribir**: items, cantidades y stock
   agregado por producto contra snapshot.
2. Stock insuficiente = `STOCK_INSUFICIENTE` y **nada se escribe**.
3. Si la venta falla después de mover stock, hay **compensación best-effort**
   (entradas `doc_tipo=COMPENSACION`); si también falla, queda marca en Log.
4. `venta ≠ cobro`: `cobrado` y los estados (PENDIENTE/PARCIAL/PAGADA/CANCELADA)
   se actualizan con los cobros; el P&L usa la venta (contable), la caja usa
   cobros (efectivo) — fuente oficial: CONTEXTO_GLOBAL §3.6.
5. `anular_venta` repone el stock con movimientos reverso trazados y marca la
   venta CANCELADA (excluida de ingresos en P&L fase 6).
6. Ventas son **histórico protegido**: jamás se borran (no en HOJAS_BORRABLES).
7. Utilidad calculada con el **costo vigente al momento de la venta**.

## API / BACKEND

| Endpoint | Tipo | Detalle |
|---|---|---|
| `ventas` | GET | Últimas 100 |
| `venta` | POST | `{cliente, cliente_id?, proyecto_id?, almacen_id, items:[{producto_id, cantidad, precio?}], moneda, tipo_cambio?, descuento?, notas}` → `{ok, folio, utilidad_base?}` |
| `cxc` | GET | Ventas no canceladas vs cobros reales (saldo por venta) |
| `registrar_cobro` | POST | `{venta_id, monto, moneda, metodo, notas}` → folio COB-; actualiza `cobrado`/estado |
| `anular_venta` | POST | `{id}` → CANCELADA + reverso de stock |

- Handlers: `apps-script.gs` L1180–1266 (venta), L1519–1590 (cobro/anulación),
  L672–693 (cxc). Errores: `STOCK_INSUFICIENTE`, `VALIDACION`, `NO_ENCONTRADO`.

## FRONTEND (tabs `sales`, `cobros`)

- **Vistas**: formulario de venta (buscador de productos con stock, items,
  totales), historial con estado de cobro, tabla CxC con saldos y botón Cobrar.
- **Funciones clave**: `searchSaleProducts` L2789, `addSaleItem` L2798,
  `renderSaleItems` L2805, `updateSaleTotal` L2815, `saveSale` L2820,
  `renderSales` L2832, `fillSaleLinks` L2774, `loadCXC` L2724 (abs; grep lo
  ubica ~L2671), `showCobroForm` L2751, `saveCobro` L2763, `anularVenta` L2780.

## PERMISOS

Token admin (rol único). Sin endpoints públicos. `anular_venta` es acción
sensible: requiere confirmación en UI (`confirma`).

## ARCHIVOS

| Archivo | Responsabilidad |
|---|---|
| `admin/index.html` L2724–2848 aprox. | UI ventas + cobros + CxC |
| `admin/apps-script.gs` L87, L101, L672–693, L1180–1266, L1519–1590 | esquemas + handlers |
| `scripts/auditoria/test_fase0_api.py` | concurrencia de ventas + folios (en vivo) |
| `scripts/auditoria/test_fase4_api.py` | cobros parciales, CxC, anulación con repuesto |

## INTEGRACIONES

- Sheets (Ventas, Cobros) · Apps Script · 01 (stock/movimientos) · 05 (proyecto)
  · 03 (cliente) · 08 (P&L y caja consumen).

## QUÉ NO MODIFICAR

- `aplicarMovimiento`, el snapshot y la compensación (Core — proponer, no editar).
- El contrato plano de `venta` (`{ok, folio}`) — 17 integraciones del frontend.
- La exclusión de ventas CANCELADAS en resultados (regla de 08, acordada fase 6).
- ENC_VENTAS/ENC_COBROS: columnas nuevas solo al final.

## PRUEBAS

- `python scripts/auditoria/test_fase0_api.py` — **obligatoria en vivo tras
  redeploy**: 2 ventas simultáneas sobre stock 10 ⇒ 1 ok + 1 STOCK_INSUFICIENTE,
  stock final correcto; folios concurrentes distintos.
- `python scripts/auditoria/test_fase4_api.py`.
- Casos críticos: cobro parcial (PENDIENTE→PARCIAL→PAGADA), anulación repone
  stock exacto, utilidad correcta en moneda base.
- Tras modificar: fase0 + fase4 + regresión fase0 (Playwright).

## EJEMPLOS DE INTERACCIÓN

1. **Venta normal**: `saveSale` → backend valida stock (snapshot) → descuenta
   vía `aplicarMovimiento(salida, doc VENTA, folio)` → append Ventas con
   utilidad → aparece en historial y CxC con saldo pendiente.
2. **Cobro parcial (06→08)**: `registrar_cobro` $30k de $100k → estado PARCIAL →
   flujo de caja cuenta $30k como efectivo entrado; CxC muestra $70k.
3. **Anulación**: `anular_venta` → venta CANCELADA → entradas reverso en
   Movimientos → stock repuesto → P&L la excluye.
