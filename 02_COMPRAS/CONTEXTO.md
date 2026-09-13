# 🚚 02_COMPRAS — Proveedores y Órdenes de Compra

> NIVEL 2 · Lee primero `00_CORE/CONTEXTO_GLOBAL.md`. Dependencia real con
> `01_EXISTENCIAS` (recepción mueve stock). Fuente: `admin/index.html`,
> `admin/apps-script.gs`, `scripts/auditoria/test_fase2_api.py`.

## IDENTIDAD

- **Objetivo**: gestionar el ciclo completo de compra a proveedores: catálogo de
  proveedores, orden de compra con estados, y recepción parcial o total que
  alimenta el inventario con trazabilidad.
- **Responsabilidad**: hojas Proveedores, OrdenesCompra, Recepciones; UI del tab `oc`.
- **Problema que resuelve**: comprar sin papel ni Excel suelto, sabiendo qué se
  ordenó, qué llegó y qué debe pagarse.

## ALCANCE

- **Hace**: CRUD de proveedores (baja lógica), OC con partidas multi-producto,
  estados de OC, recepción parcial/total con folio, PDF/imprimir de OC.
- **NO hace**: pagar (07 registra el gasto/pago manualmente hoy), mover stock por
  sí solo (la recepción delega en `aplicarMovimiento` de Core/01).
- **Pertenecen aquí**: las 3 hojas del módulo + pestaña `oc` del panel.

## DATOS

- **Hojas**: `Proveedores` (ENC_PROV), `OrdenesCompra` (ENC_OC), `Recepciones`
  (ENC_RECEP). Esquemas: `apps-script.gs` L97, L103, L105.
- **Campos importantes**: OC.`id/folio OC-…/proveedor_id/estado/subtotal/iva/total/
  moneda/items_json/almacen_id`; Recepciones.`oc_id/oc_folio/items_json`.
- **Consume**: Productos y Almacenes (01) para partidas y destino; Config (folio_oc).
- **Genera**: OC con folio, recepciones, y movimientos de entrada en Stock/Movimientos.

## DEPENDENCIAS

- **DEPENDE DE**: `00_CORE`; `01_EXISTENCIAS` (productos, almacenes, vía
  `aplicarMovimiento` al recibir — dependencia documentada).
- **ALIMENTA A**: `01_EXISTENCIAS` (entradas de stock), `07_GASTOS_PAGOS`
  (referencia de proveedor; hoy el gasto se registra a mano).
- **COMPARTE DATOS CON**: 01 (productos/almacenes).

## REGLAS DE NEGOCIO

1. Recibir una OC **solo** genera entradas vía `aplicarMovimiento` (doc ORDEN_COMPRA
   o RECEPCION) — fuente oficial de la regla: CONTEXTO_GLOBAL §3.1.
2. La recepción puede ser **parcial**; el estado de la OC refleja lo recibido.
3. Proveedores usan baja lógica (`activo=no`).
4. La recepción con costo actualiza último costo del producto (misma regla que 01).

## API / BACKEND

| Endpoint | Tipo | Detalle |
|---|---|---|
| `proveedores` | GET | Lista de proveedores |
| `oc` | GET | Órdenes de compra |
| `save_proveedor` | POST | Crear/editar proveedor |
| `delete_proveedor` | POST | Baja lógica |
| `save_oc` | POST | Crear/editar OC (partidas, almacén destino, moneda, IVA) |
| `cambiar_estado_oc` | POST | Transición de estado |
| `recibir_oc` | POST | `{oc_id, items:[{producto_id, cantidad, costo_unit?}]}` → entrada de stock trazada |

- Handlers: `apps-script.gs` L1592–1774. Errores: `VALIDACION`, `NO_ENCONTRADO`,
  `STOCK_INSUFICIENTE` no aplica (entradas).

## FRONTEND (tab `oc`)

- **Vista**: lista de OC con badge de estado y acciones por fila; sección inferior
  de proveedores (`provAnchor`).
- **Formularios**: `showOCForm(id)` L2496 (partidas con buscador, totales+IVA),
  `showRecepForm(id)` L2570 (recepción por partida), `showProvForm()` L2471.
- **Funciones clave**: `loadOC` L2446, `renderOC` L2456, `renderProv` L2466,
  `searchOCProducts` L2519, `renderOCItems` L2535, `updateOCTotals` L2554,
  `saveOC` L2559, `cambiarEstadoOC` L2565, `saveRecepcion` L2581, `printOC` L2593.
- **Flujo**: OC → estado → recepción → stock actualizado (con `stock_nuevo` por partida).

## PERMISOS

Token admin (rol único). Sin endpoints públicos.

## ARCHIVOS

| Archivo | Responsabilidad |
|---|---|
| `admin/index.html` L2446–2597 aprox. | UI de OC y proveedores |
| `admin/apps-script.gs` L97, L103, L105, L1592–1774 | esquemas + handlers |
| `scripts/auditoria/test_fase2_api.py` | suite API (OC, recepción, proveedores) |

## INTEGRACIONES

- Sheets (3 hojas) · Apps Script · 01_EXISTENCIAS (stock) · 07 lee proveedores
  como texto libre en gastos (deuda: ligar gasto a OC pendiente).

## QUÉ NO MODIFICAR

- `aplicarMovimiento` y los ENC de hojas (agregar columnas solo al final).
- La firma de `recibir_oc` (lo consumen pruebas en vivo y el frontend).
- `HOJAS_BORRABLES` no incluye estas hojas: no agregarlas sin decisión explícita.

## PRUEBAS

- `python scripts/auditoria/test_fase2_api.py` (tras redeploy; cubre OC 100→40→60
  con stock correcto y trazado).
- Tras modificar: suite fase2 + regresión fase0 + suite de movimientos (la recepción
  escribe movimientos).

## EJEMPLOS DE INTERACCIÓN

1. **OC parcial**: OC 100 u → recibir 40 (stock +40, OC parcial) → recibir 60
   (stock +60, OC recibida; trazada a folio OC-AAAA-NNNN).
2. **Proveedor → gasto (07)**: el gasto manual captura proveedor como texto;
   la futura CxP de OC deberá referenciar `proveedor_id` (pendiente de producto).
