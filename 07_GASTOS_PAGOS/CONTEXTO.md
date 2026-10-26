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
| `ingreso` | POST | `{fecha, concepto, monto, moneda, metodo?, notas}` → folio ING-; escribe en **Cobros** sin `venta_id` (otros ingresos: reembolsos, venta de activos) |
| `categoria` | POST | `{accion:'agregar'\|'quitar', clase:'gastos'\|'ingresos', nombre}` → catálogo configurable en `Config` (`categorias_gastos`/`categorias_ingresos`, separados por comas). OJO: el campo es `clase`, no `tipo` (`tipo` es el despachador) |

- `GET action=config` también devuelve `categorias_gastos` y `categorias_ingresos`
  (arrays; defaults en `CATEGORIAS_*_DEFAULT` de core.gs).
- Handlers: `apps-script.gs` L1267–1360. Errores: `VALIDACION` (monto > 0),
  `NO_ENCONTRADO`.

## FRONTEND (tab `expenses`)

- **Vista**: tabla de gastos con estado, CxP con saldos y botón Pagar.
- **Funciones clave**: `addExpense` L2849, `renderExpenses` L2859, `renderCXP`
  L2878, `showPagoForm` L2901, `savePago` L2914, `cancelarGasto` L2924.
- **Categorías**: el `<datalist id="gCatList">` se llena por JS desde
  `poblarCategorias()` (config del backend); la captura de otros ingresos
  (`addIngreso`, tab `cobros`) usa `#ingCatList` igual. Gestión (agregar/quitar)
  en INVENTARIO → ⚙️ Configuración → “Categorías de gastos e ingresos”
  (`pintarCategoriasConfig`/`agregarCategoria`/`quitarCategoria`, en gastos.js).
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

## GASTOS FIJOS (programados) — 2026-10-25

- Hoja nueva `GastosFijos` (esquema `ENC_GASTOS_FIJOS` en `00_CORE/backend/core.gs`,
  se crea sola al primer uso via `hoja()`). Columnas: id, concepto, categoria,
  monto, moneda, frecuencia (semanal|quincenal|mensual|anual), proxima_fecha,
  notas, estado (ACTIVA|CANCELADA), gasto_folio_ultimo, creado.
- Endpoints: `GET gastos_fijos` · `POST gasto_fijo` (accion: agregar | generar |
  quitar=baja lógica). `generar` crea un gasto GAS- normal ("(Gasto fijo) ...",
  queda POR PAGAR) y avanza proxima_fecha con `siguienteOcurrencia()` (salta al
  futuro según frecuencia; fechas parseadas a mediodía para no sufrir DST).
- Panel: pestaña nueva `Dinero → Gastos fijos (programados)` (tab `fijos` en
  `admin/plantilla.html` + JS en `07_GASTOS_PAGOS/admin/gastos.js`: loadFijos,
  addFijo, generarFijo, quitarFijo, alertas por `diasHasta_`).
- Alertas 100% cliente (sin triggers): 🔴 vencido/vence hoy, 🟠 ≤3 días. Aviso
  global 1 vez por sesión al entrar (enterApp → loadFijos → avisarVencimientosFijos).
- Renombres de menú pedidos por el dueño: "Cobros / cuentas por cobrar" →
  "Registrar ingreso"; "Gastos / cuentas por pagar" → "Registrar gasto".
- Avisos del panel (`notice`) ahora son toast flotante fijo (`#notice` fixed en
  `00_CORE/design-system/admin.css`) — antes quedaban arriba del todo y se
  perdían con el scroll. Mensajes de éxito explícitos: "✅ Ingreso/Gasto
  correcto — folio ...".
- `ingFecha` ahora se pre-llena con hoy (fLocal; antes quedaba vacío) y `gFecha`
  usa fLocal (antes toISOString UTC, se adelantaba un día después de las 6pm).
- REQUIERE REDEPLOY de `admin/apps-script.gs` (sin él la pestaña Gastos fijos
  no carga y los mensajes nuevos del panel tampoco se ven en producción).

## MEJORA DE UX — 2026-10-25 (regla del dueño: facil, intuitivo, automatizado)

- **Cuadro de ayuda en cada sección** (`details.helpbox` en `00_CORE/design-system/
  admin.css`): 17 secciones del panel explican "¿para qué sirve y cómo lo uso?"
  (la 18ª, Ayuda, es la guía completa). Textos en `admin/plantilla.html`.
- **Auto-pago de gastos**: el formulario de Registrar gasto ahora tiene
  "¿Ya lo pagaste?" (No/Sí) + método de pago. Con "Sí" registra gasto Y pago en
  un solo paso (`addExpense` encadena `gasto` → `gasto_pago` con el `id` que el
  backend ahora devuelve). Requiere redeploy del backend.
- Mensajes de confirmación tipo "✅ Gasto y pago registrados — GAS- · PAG- ·
  monto. Gasto PAGADA."
