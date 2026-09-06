# ADMIN_ARCHITECTURE.md — Arquitectura del Sistema Administrativo ADIS

> Documento maestro del sistema. Última actualización: **Fase 0 — 6 de septiembre de 2026**.
> Actualizar al final de cada fase. La auditoría completa previa está en
> `docs/AUDITORIA_SISTEMA_2026-09-06.md`.

---

## 1. Visión general

Panel administrativo de ADIS | Diseños & Remodelaciones sobre arquitectura de
**tres capas sin servidor propio**:

```
┌─────────────────────────────────────────────────────────────┐
│ CAPA 1 — CLIENTE                                            │
│  admin/index.html → se copia a public/admin.html (main() de │
│  generar_web.py). Monolito HTML+CSS+JS. Sesión: token en    │
│  sessionStorage (adis_admin_token / adis_admin_user).       │
├─────────────────────────────────────────────────────────────┤
│ CAPA 2 — BACKEND (Google Apps Script, V8)                   │
│  admin/apps-script.gs desplegado como Web App desde la      │
│  hoja maestra de Google Sheets.                             │
│  API: doGet?action=X&token= / POST JSON {tipo, token, ...}  │
│  Auth: token UUID en CacheService (8 h). Credenciales en    │
│  constantes del script (rotar en Apps Script).              │
├─────────────────────────────────────────────────────────────┤
│ CAPA 3 — DATOS (Google Sheets, cuenta ing.carlosurbina300)  │
│  14 pestañas (ver §3). Sheets NO es transaccional: locking  │
│  vía LockService + compensación best-effort (ver §7).       │
└─────────────────────────────────────────────────────────────┘
```

- Sitio público conectado al mismo backend solo con endpoints públicos:
  `track` (visitas), `lead` (formulario), `reviews` (testimonios).
- `products.json` (público) NO contiene costos/stock — el ERP consume la
  hoja Productos (privada, con token).

## 2. Endpoints

### GET (todos exigen token salvo `reviews`)

| action | Respuesta (ok) | Notas |
|---|---|---|
| `reviews` | `{ok, reviews:[{nombre,estrellas,texto,fecha}]}` | **Público.** Solo activas. |
| `me` | `{ok, usuario}` | Validación de sesión. |
| `leads` | `{ok, leads:[...]}` | |
| `quotes` | `{ok, quotes:[...]}` | |
| `reviews_admin` | `{ok, reviews:[...]}` | Todas (activas e inactivas). |
| `visitas` | `{ok, visitas:[...]}` | Hasta 5000 activas (ver retención §6). |
| `config` | `{ok, moneda_base, tipo_cambio}` | |
| `productos` | `{ok, productos:[...]}` | Activos e inactivos. |
| `almacenes` | `{ok, almacenes:[...]}` | Solo activos. |
| `stock` | `{ok, stock:[{producto_id,producto,almacen_id,almacen,cantidad}]}` | |
| `movimientos` | `{ok, movimientos:[...]}` | Últimos 100. |
| `ventas` | `{ok, ventas:[...]}` | Últimas 100. |
| `gastos` | `{ok, gastos:[...]}` | Todos. |
| `estado_resultados&mes=YYYY-MM` | `{ok, ingresos, costos, utilidad_bruta, gastos:{cat}, total_gastos, utilidad_neta, num_ventas, margen_bruto, margen_neto, moneda_base}` | |

| `proyectos`, `cxc` | sí | Fase 4 |
| `alertas` | sí | Fase 6: stock negativo/bajo/cero, sin precio/costo, CxC/CxP >30 días, cotizaciones pendientes viejas, OCs por recibir (CRITICA>ALTA>MEDIA) |
| `pagos`, `cxp`, `flujo_caja?desde=&hasta=` | sí | Fase 5: CxP y efectivo real (cobros−pagos) |

### POST

| tipo | Token | Escribe en | Lock |
|---|---|---|---|
| `login` | no | CacheService (token) | — |
| `logout` | no (revoca propio) | CacheService | — |
| `lead` | no | Leads | — |
| `track` | no | Visitas (+archivo) | sí |
| `quote` | sí | Cotizaciones, Config (folio), Log | sí |
| `review` | sí | Reseñas | sí |
| `delete_review` | sí | Reseñas (activa=no) | sí |
| `config` | sí | Config, Log | sí |
| `save_product` | sí | Productos, Log | sí |
| `delete_product` | sí | Productos (estado=inactivo) | sí |
| `restore_product` | sí | Productos | sí |
| `import_productos` | sí | Productos, Stock, Movimientos, Almacenes, Log | sí |
| `delete_row` | sí | hojas de `HOJAS_BORRABLES` | sí |
| `save_almacen` | sí | Almacenes | sí |
| `delete_almacen` | sí | Almacenes (activo=no) | sí |
| `movimiento` | sí | Stock, Movimientos, Log | sí |
| `venta` | sí | Stock, Movimientos, Ventas, Config (folio), Log | sí |
| `gasto` | sí | Gastos, Log | sí |
| `delete_gasto` | sí | Gastos | fecha, categoria, descripcion, monto, moneda, tipo_cambio, monto_base, id, usuario, folio (GAS-), estado (ACTIVA/CANCELADA), pagado |

| `save_proyecto`, `proyecto_mov`, `crear_proyecto_desde_cotizacion` | sí | Proyectos, Proyectos_Movs, Config, Log | sí |
| `gasto_pago` (registrar_pago) | sí | Pagos, Gastos, Log | sí |
| `gasto_cancelar` / `delete_gasto` (alias, baja lógica) | sí | Gastos, Log | sí |
| `venta_pago` (registrar_cobro) | sí | Cobros, Ventas, Log | sí |
| `venta_anular` | sí | Ventas, Stock, Movimientos, Log | sí |

### Contrato de errores (Fase 0)

Éxito: `{ok:true, ...campos planos}` (forma heredada, se migra a envelope en fase de rediseño).
Error: `{ok:false, error:{code, message}}` — nunca HTML de Google, nunca stack traces.

Códigos: `TOKEN_INVALIDO`, `CREDENCIALES_INVALIDAS`, `DEMASIADOS_INTENTOS`,
`JSON_INVALIDO`, `VALIDACION`, `NO_ENCONTRADO`, `NO_PERMITIDO`,
`CODIGO_DUPLICADO`, `STOCK_INSUFICIENTE`, `TIPO_MOVIMIENTO_INVALIDO`,
`ACCION_DESCONOCIDA`, `TIPO_DESCONOCIDO`, `ERROR_INTERNO`.

## 3. Hojas de Google Sheets (esquemas)

Columnas nuevas de la Fase 0 se agregaron **al final** (migración aditiva;
`hoja(nombre, enc)` garantiza el esquema en cada arranque).

| Hoja | Columnas |
|---|---|
| Productos | id, codigo, nombre, descripcion, categoria, subcategoria, proveedor, costo, precio, unidad, stock_minimo, moneda, foto, estado, notas, fecha_actualizacion |
| Almacenes | id, nombre, ubicacion, activo |
| Stock | producto_id, almacen_id, cantidad |
| Movimientos | fecha, tipo, producto_id, producto, almacen_id, almacen, cantidad, costo_unit, moneda, referencia, notas, **id, usuario, existencia_anterior, existencia_posterior, documento_tipo, documento_id** |
| Ventas | fecha, cliente, almacen, items, total, moneda, tipo_cambio, total_base, costo_total_base, utilidad_base, notas, **id, folio, usuario, estado, cobrado, items_json, moneda_base, tipo_cambio_base, cliente_id, proyecto_id** |
| Gastos | fecha, categoria, descripcion, monto, moneda, tipo_cambio, monto_base, **id, usuario** |
| Reseñas | fecha, nombre, estrellas, texto, activa, **id, usuario** |
| Proveedores | id, folio, nombre, contacto, telefono, email, ciudad, notas, **usuario** |
| OrdenesCompra | id, folio, proveedor_id, fecha, estado, subtotal, iva, total, moneda, recibido, items_json, usuario, notas |
| Clientes | id, folio, nombre, telefono, email, ciudad, tags, notas, **usuario, creado** |
| Proyectos | id, folio, nombre, cliente_id, cotizacion_id, estado, moneda, presupuesto, cobrado, creado, usuario, notas |
| Proyectos_Movs | id, proyecto_id, tipo, monto, moneda_base, tipo_cambio_base, monto_base, fecha, usuario, descripcion, doc_tipo, doc_id |
| Pagos | id, folio, gasto_id, gasto_folio, categoria, fecha, monto, moneda, monto_base, metodo, notas, usuario |
| Cobros | id, venta_id, fecha, monto, moneda, tipo_cambio, monto_base, metodo, notas, usuario |
| Cotizaciones | fecha, cliente, telefono, ciudad, items, total, notas, folio, proyecto, ubicacion, moneda, subtotal, iva, estado, datos, **id, usuario** |
| Leads | fecha, nombre, telefono, email, ciudad, metros, producto, mensaje, pagina, idioma |
| Visitas | fecha, hora, pagina, seccion, origen, referrer, idioma, dispositivo, navegador, ancho, ua |
| Visitas_Archivo | (igual que Visitas; retención, creada bajo demanda) |
| Config | clave, valor |
| Log | fecha, usuario, accion, detalle |

`HOJAS_BORRABLES` (endpoint `delete_row`): Leads, Cotizaciones, Reseñas,
Gastos, Stock, Visitas. **Ventas y Movimientos son histórico protegido.**

### Config (claves)

| clave | defecto | uso |
|---|---|---|
| `moneda_base` | MXN | conversión aBase() |
| `tipo_cambio` | 18.5 | MXN por 1 USD |
| `folio_cotizacion` | 1 | consecutivo ADIS-AAAA-NNN |
| `folio_venta` | 1 | consecutivo VEN-AAAA-NNNN |
| `folio_movimiento` | 1 | consecutivo MOV-AAAA-NNNNN |
| `folio_proyecto` | 1 | consecutivo PRY-NNNNNN |
| `folio_gasto` | 1 | consecutivo GAS-AAAA-NNNN |
| `folio_pago` | 1 | consecutivo PAG-AAAA-NNNN |

## 4. Identificadores y folios

- **ID interno** (relaciones entre hojas): `nuevoId()` = UUID 8 chars
  (productos, almacenes, ventas, gastos, reseñas, cotizaciones, movimientos).
- **Folio visible** (documentos): `siguienteFolio(prefijo, claveCfg, digitos)`
  bajo LockService — imposible duplicar por concurrencia; hueco posible si la
  escritura falla tras reservar (aceptado y documentado).
  Formatos: `ADIS-2026-042` (cotización, 3 díg.), `VEN-2026-0001` (venta, 4 díg.),
  `MOV-2026-00001` (movimiento, 5 díg.).
- **Regla**: nunca usar el número de fila como identificador. `filaPorId()`
  localiza filas por columna `id`. (Compatibilidad temporal: delete_review/
  delete_gasto aceptan `row` como respaldo hasta que el frontend viejo deje de usarse.)

## 5. Reglas de inventario (REGLA CENTRAL)

> **La existencia de un producto SOLO cambia mediante `aplicarMovimiento()`,
> que escribe stock + fila de Movimientos con trazabilidad completa.**

- Cada movimiento registra: `id MOV-…`, fecha, usuario, producto, almacén,
  tipo (entrada/salida/ajuste), cantidad, **existencia_anterior,
  existencia_posterior, documento_tipo, documento_id**, referencia, notas.
- `documento_tipo` actual: VENTA, COMPENSACION, AJUSTE, IMPORTACION
  (Fase 2 añadirá ORDEN_COMPRA, TRANSFERENCIA, DEVOLUCION, PROYECTO…).
- Stock negativo = excepción `STOCK_INSUFFICIENTE` (jamás se persiste).
- Stock se mantiene en hoja Stock (contador) + Movimientos (historial
  completo); snapshot por ejecución (`snapStock`) evita lecturas N+1 y hace
  que movimientos sucesivos de un mismo request se vean entre sí.

## 6. Reglas financieras

- Moneda dual: `aBase(monto, moneda, tc)` convierte a moneda_base; solo MXN↔USD.
- Ventas guardan `total`, `total_base`, `costo_total_base`, `utilidad_base`
  (utilidad = total_base − costo_total_base, calculada al precio/costo vigente
  del producto en el momento de la venta).
- Estado de resultados: filtra Ventas/Gastos por `fecha` (YYYY-MM-DD validada
  al escribir). Contable, no de caja (cobros/pagos reales llegan en Fase 5).
- **gasto ≠ pago, venta ≠ cobro** — aún no implementado (Fase 5: estados y
  CxC/CxP + flujo de efectivo).

## 7. Integridad transaccional (límites reales de Sheets)

Google Sheets **no tiene ACID**. Mecanismos implementados en Fase 0:

1. `conLock(fn)` — LockService script-level, wait 30 s, release en finally.
   Cubre validar+escribir completo en folios, stock, ventas, importaciones.
2. Validación completa **antes** de cualquier escritura (venta: items,
   cantidades, stock agregado por producto).
3. **Compensación best-effort** en venta: si falla tras mover stock, se
   revierte cada movimiento (entrada `doc_tipo=COMPENSACION`). Si la
   compensación también falla, queda `error_compensacion` en Log para
   corrección manual. Esto es el máximo garantizable sin BD transaccional.
4. Borrados lógicos para entidades vivas (producto/almacén/resena → estado),
   borrado físico solo en hojas de `HOJAS_BORRABLES`.

## 8. Autenticación y seguridad

- Login usuario/clave (constantes en el script). Límite: 5 intentos/10 min
  por usuario (CacheService). Token UUID, 8 h, CacheService; `logout` revoca.
- Endpoints públicos: `reviews`, `lead` (honeypot `empresa`), `track`
  (rate-limit 120 eventos/10 min por huella UA|idioma|ancho + dedup 45 s),
  `login`, `logout`.
- Track: retención 5000 activas; el excedente se **archiva** en
  Visitas_Archivo (jamás se borra historial por tope de filas).
- Admin: `noindex, nofollow` en el HTML + `Disallow: /admin.html` en
  robots.txt. La protección real es el login (no hay seguridad por oscuridad
  como única defensa).
- El usuario admin **no** se escribe en el Log desde Fase 0.
- **Pendiente de dueño**: rotar `ADMIN_CLAVE` (estuvo expuesta en el repo) y
  considerar mover credenciales a propiedades del script (Script Properties).

## 9. Flujos principales

### Venta (la operación más crítica)
```
POST venta → conLock:
  1. validar almacén, items (producto existe, cantidad>0)
  2. validar stock agregado por producto contra snapshot
  3. folio VEN-… (reserva bajo lock)
  4. por item: aplicarMovimiento(salida, doc VENTA, doc_id folio)
  5. appendRow Ventas (con id, folio, usuario)
  6. Log  — si 4–6 fallan: compensar con entradas COMPENSACION y re-lanzar
```

### Cotización
```
POST quote → conLock: esquema garantizado → folio ADIS-… (respeta re-guardado)
→ appendRow (datos = JSON del estado del cotizador; fotos NO viajan: viven en
localStorage del navegador que la creó — mejora planificada: Drive, Fase 3)
```

### Movimiento manual
```
POST movimiento → conLock → validar tipo (lista blanca), cantidad>0,
producto/almacén existen → aplicarMovimiento(doc AJUSTE) → Log
```

## 10. Dependencias y puntos de extensión por fase

| Fase | Punto de entrada en el backend |
|---|---|
| 3 Clientes/Cotizaciones | hoja Clientes (CLI-NNNNNN, tags lead/cliente), `save_cliente`, `lead_convertir`, `quote_estado` |
| 4 Proyectos/Ventas 2.0 | hojas Proyectos, Proyectos_Movs, Cobros; `save_proyecto`, `proyecto_mov`, `crear_proyecto_desde_cot`, `venta_pago` (cobros parciales), `venta_anular` (devolucion trazable); Ventas con estado/cobrado/folio VEN-/items_json |
| 2 Compras | nuevos tipos `orden_compra`, `recibir_oc` → `aplicarMovimiento(entrada, doc ORDEN_COMPRA)`; hojas Proveedores, OrdenesCompra |
| 3 Clientes/Cotizaciones | hoja Clientes; `quote` estado → aprobada crea proyecto; unificar cotizadores en frontend |
| 4 Proyectos/Ventas 2.0 | Ventas + `pagos` parciales (hoja Cobros); CxC calculado de Ventas−Cobros |
| 6 Finanzas | `estado_resultados` con filtro `proyecto_id` (gastos = Proyectos_Movs del proyecto), utilidad operativa y márgenes, ventas CANCELADAS excluidas del ingreso; GET `alertas` priorizadas |
| 5 Gastos/Pagos | estados pagado/pendiente en Gastos; hoja Pagos; flujo de efectivo = Cobros−Pagos por fecha |
| 6 Finanzas | estado_resultados con niveles (bruta/operativa/neta) + rentabilidad por proyecto |
| 7 Dashboard/rediseño | migración del contrato a envelope `{ok, data, error}`; sidebar; Lucide |

## 11. Pruebas

| Script | Qué valida | Cuándo |
|---|---|---|
| `scripts/auditoria/test_fase6_api.py` | API (proyecto_mov, P&L por proyecto, exclusión de anuladas, alertas priorizadas). | tras redeploy |
| `scripts/auditoria/test_fase5_api.py` | API (gasto con folio, pagos parciales, CxP, cancelar lógica, flujo de caja, P&L excluye cancelados). | tras redeploy |
| `scripts/auditoria/test_fase4_api.py` | API (proyectos, cobros parciales, CxC, anulacion con repuesto de stock). | tras redeploy |
| `scripts/auditoria/test_fase0_api.py` | API + concurrencia (ventas simultáneas, folios duplicados, errores por código). Auto-detecta backend viejo/nuevo. | tras redeploy del script |
| `scripts/auditoria/test_fase0_regresion.py` | Playwright: login + las 10 pestañas + logout, 0 errores JS. | en cada cambio del panel |
| `scripts/auditoria/test_flujo_cotizador.py` | Cotizador (backend simulado) | al tocar el cotizador |

## 12. Operación

- **Regenerar sitio**: `python generar_web.py` (copia admin/index.html → public/admin.html).
- **Publicar**: `git push origin main` (GitHub Actions publica `public/`).
- **Actualizar backend**: Apps Script → pegar `admin/apps-script.gs` → Guardar →
  **Implementar → Administrar implementaciones → ✏️ → Nueva versión** (la URL
  NO debe cambiar; si cambia, replicarla en: generar_web.py ×2,
  admin/index.html CONFIG.API_URL, scripts/auditoria/importar_maestro.py y test_fase0_api.py).
