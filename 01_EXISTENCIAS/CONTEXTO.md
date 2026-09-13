# 📦 01_EXISTENCIAS — Productos, Almacenes, Stock y Movimientos

> NIVEL 2 · Lee primero `00_CORE/CONTEXTO_GLOBAL.md` (§3 reglas, §6 datos, §7 folios).
> Fuentes: `admin/index.html`, `admin/apps-script.gs`, `scripts/auditoria/test_fase1_api.py`.

## IDENTIDAD

- **Objetivo**: ser la fuente única de verdad sobre qué productos existen, dónde hay
  y cuánto hay, con trazabilidad completa de cada cambio de existencia.
- **Responsabilidad**: catálogo maestro del ERP (CRUD de productos/almacenes), stock
  por almacén, y el libro diario de movimientos (entradas, salidas, ajustes, lotes).
- **Problema que resuelve**: sin este módulo no hay ventas fiables, ni compras, ni
  resultados — es la base operativa del negocio.

## ALCANCE

- **Hace**: CRUD de productos (soft-delete), CRUD de almacenes, stock por almacén,
  movimientos entrada/salida/ajuste, **lotes multi-producto** (todo-o-nada, folio
  LOTE-), entrada con costo (actualiza último costo del producto), salida ligada a
  proyecto/obra, historial filtrable con CSV e impresión, importación masiva
  (`import_productos`), cambio masivo de precios/márgenes (`update_precios`).
- **NO hace**: vender (06), comprar (02), cotizar (04), calcular resultados (08).
- **Pertenecen aquí**: hojas Productos, Almacenes, Stock, Movimientos + su UI de
  inventario en el panel.

## DATOS

- **Hojas** (dueño de todas): `Productos` (ENC_PROD), `Almacenes`, `Stock`,
  `Movimientos` (ENC_MOV). Esquemas oficiales: `apps-script.gs` L79–86.
- **Campos importantes**: Productos.`id/codigo/nombre/costo/precio/unidad/moneda/
  estado/notas`; Movimientos.`id MOV-…/tipo/producto_id/almacen_id/cantidad/
  existencia_anterior/existencia_posterior/documento_tipo/documento_id/lote/usuario`.
- **Consume**: Config (`moneda_base`, `tipo_cambio`, folios `folio_movimiento`,
  `folio_lote`); payload de items de OC (02) y ventas (06) vía Core.
- **Genera**: filas Movimientos (trazabilidad), actualizaciones de Stock y de costo
  en Productos; `stock_nuevo` por producto en la respuesta de `movimiento`.

## DEPENDENCIAS

- **DEPENDE DE**: `00_CORE` (auth, `conLock`, `cfg`, `snapStock`, `aplicarMovimiento`,
  `siguienteFolio`, `filaPorId`, `hoja`, `aBase`).
- **ALIMENTA A**: 06_VENTAS (stock+costo), 02_COMPRAS (recepción → entrada),
  05_PROYECTOS (salida por obra), 08_RESULTADOS (valor de inventario), 04_COTIZADOR.
- **COMPARTE DATOS CON**: todos los módulos operativos (leen Productos/Stock).

## REGLAS DE NEGOCIO (fuente oficial: `00_CORE/CONTEXTO_GLOBAL.md` §3)

1. La existencia SOLO cambia por `aplicarMovimiento()` — jamás escribir Stock a mano.
2. Stock negativo jamás persiste (`STOCK_INSUFICIENTE`).
3. Lote multi-producto es **todo-o-nada**: se pre-valida stock TOTAL por
   producto+almacén antes de escribir nada.
4. Entrada con `costo_unit` actualiza el último costo del producto (col costo + fecha).
5. Prioridad de documento origen: `PROYECTO` (si viene proyecto_id) > `LOTE` > `AJUSTE`.
6. Movimientos son histórico protegido: no se borran, no están en HOJAS_BORRABLES.
7. Productos y almacenes usan **baja lógica** (`estado/activo = no`), no borrado físico.
8. Columnas nuevas SIEMPRE al final del ENC_ (migración aditiva).

## API / BACKEND (`apps-script.gs`)

| Endpoint | Tipo | Detalle |
|---|---|---|
| `productos` | GET | Activos e inactivos (sin token? **sí requiere token**) |
| `almacenes` | GET | Solo activos |
| `stock` | GET | `[{producto_id, producto, almacen_id, almacen, cantidad}]` |
| `movimientos` | GET | Últimos 100; con filtros `desde/hasta/tipo/almacen_id` hasta 500 |
| `save_product` | POST | Crear/editar producto (valida nombre; `CODIGO_DUPLICADO`) |
| `update_precios` | POST | Edición masiva de precios/márgenes |
| `delete_product` / `restore_product` | POST | Baja/alta lógica |
| `save_almacen` / `delete_almacen` | POST | CRUD almacenes (baja lógica) |
| `movimiento` | POST | Entrada/salida/ajuste 1 producto **o lote** `items[]` (máx 100). Payload: fecha (no futura), referencia, proveedor, moneda, costo_unit, proyecto_id, notas |
| `import_productos` | POST | Migración masiva con reset opcional (destructivo) |

- **Errores propios**: `STOCK_INSUFICIENTE`, `TIPO_MOVIMIENTO_INVALIDO`,
  `VALIDACION` (fecha futura, ajuste con items, cantidad ≤ 0), `NO_ENCONTRADO`.
- Respuesta `movimiento`: `{ok, stock_nuevo:{producto_id:cant}, lote}`.

## FRONTEND (`admin/index.html`, tab `inventory` + formularios del menú)

- **Vista**: `inventory` — dashboard (total/activos/sin foto/revisión), buscador con
  filtros, tabla de productos con foto lateral al seleccionar, historial por producto.
- **Formularios**: `showMovForm(tipo)` unificado entrada/salida (proveedor+factura en
  entrada, proyecto en salida, tabla de items multi-producto, totales); `showAdjustForm`
  (ajuste simple 1 producto); `showProductForm` (CRUD + descripción/fotos);
  `showPricesForm` (códigos y precios con margen); `showWarehouseForm`;
  `showConfigForm` (moneda/tipo de cambio — pertenece a 11_SISTEMA, vive aquí por UI).
- **Funciones clave**: `invMov` L1182, `showMovForm` L2354, `saveMovLote` L2424,
  `searchMovProducts` L2386, `renderInventory` L2008, `loadProductHistory` L2091,
  `renderMovs/renderMovFiltered` L2119/2149, `movCSV` L2161, `printMovs` L2176,
  `showPricesForm` L2197, `savePrices` L2229, `showProductForm` L2239, `saveAdjust` L2345.
- **Estados**: cache `movsCache`, `priceRowsCache`; filtros del historial en cliente.

## PERMISOS

- Token admin para todo. Sin roles (rol único). `import_productos` con `reset:true`
  borra Productos/Stock/Movimientos — acción crítica, solo dueño.

## ARCHIVOS (hoy, hasta migración M4/M5)

| Archivo | Responsabilidad |
|---|---|
| `admin/index.html` (L1182–1253 no; L1320–1331, L1978–2245, L2345–2445 aprox.) | UI inventario + movimientos + precios + almacenes |
| `admin/apps-script.gs` L79–86, L350–430, L459–478, L881–1180 | esquemas, `snapStock`, `aplicarMovimiento`, handlers |
| `scripts/auditoria/test_fase1_api.py` | suite API del módulo |
| `scripts/auditoria/test_movimientos_ui.py` | suite Playwright UI (21 pruebas) |
| `scripts/auditoria/test_movimientos_lote_api.py` | suite API en vivo de lotes |
| `60_DATA/importar_maestro.py`, `dataset_maestro.json` | herramienta de importación ya ejecutada (trazabilidad) |

## INTEGRACIONES

- Google Sheets (4 hojas del módulo) · Apps Script · el panel usa `biz.productos`
  (cache en `loadBiz` L1978) que **no** es products.json del sitio (duplicación
  conocida, ver CONTEXTO_GLOBAL §6) · fotos de producto: **ruta de texto, sin upload
  real** (deuda conocida).

## QUÉ NO MODIFICAR

- `aplicarMovimiento()` (Core — proponer cambios, no editar en caliente).
- ENC_MOV / ENC_PROD: solo agregar columnas al final; nunca renombrar/reordenar.
- Regla todo-o-nada del lote y la pre-validación con snapshot.
- Compensación de venta (`doc_tipo=COMPENSACION`) — la escribe 06; aquí solo se lee.
- `sync_media`/catálogo del sitio: fuera del alcance de este módulo.

## PRUEBAS

- `python scripts/auditoria/test_fase1_api.py` (API, tras redeploy).
- `python scripts/auditoria/test_movimientos_ui.py` (Playwright, backend simulado).
- `python scripts/auditoria/test_movimientos_lote_api.py` (API en vivo).
- Casos críticos: salida que excede stock (todo intacto), fecha futura rechazada,
  entrada con costo actualiza costo, lote con proyecto agrupa por folio.
- Tras modificar: correr las 3 suites + `test_fase0_regresion.py` (19 pruebas del panel).

## EJEMPLOS DE INTERACCIÓN

1. **Recepción de compra (02→01)**: `recibir_oc` llama internamente
   `aplicarMovimiento(entrada, doc ORDEN_COMPRA, doc_id folioOC)` por partida →
   Stock sube y queda trazado a la OC.
2. **Venta (06→01)**: `venta` valida stock agregado con snapshot y descuenta vía
   `aplicarMovimiento(salida, doc VENTA)`; si algo falla después, compensa con
   entradas COMPENSACION.
3. **Salida por obra (05→01)**: salida con `proyecto_id` → `documento_tipo=PROYECTO`,
   el folio LOTE va en columna `lote` para agrupar.
