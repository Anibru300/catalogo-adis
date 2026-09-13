# 🗺️ MAPA DE DEPENDENCIAS — Plataforma ADIS

> Relaciones **reales**, extraídas del código el 2026-09-13. No inventadas.
> Fuentes: `admin/apps-script.gs` (handlers y hojas que escribe/lee),
> `admin/index.html` (tabs y llamadas apiGet/apiPost), `generar_web.py`.
> Leyenda de funciones Core: `conLock` L139 · `conErrores` L128 · `cfg` L302 ·
> `siguienteFolio` L325 · `aBase` L333 · `snapStock` L350 · `aplicarMovimiento` L380 ·
> `filaPorId` L411 · `hoja` L151 · `nuevoId` L218 · `trackProtegido` L1845.

```
                 ┌──────────────────────────────────────────────┐
                 │ 00_CORE: Auth · conLock · conErrores · cfg   │
                 │ folios · aplicarMovimiento · aBase · hojas   │
                 └───────┬───────────────────────┬──────────────┘
        ┌────────────────┼───────────┬───────────┼────────────────┐
        ▼                ▼           ▼           ▼                ▼
   01_EXISTENCIAS   03_COMERCIAL  07_GASTOS    09_MARKETING    10_SITIO_PUBLICO
   Productos        Leads         Pagos        Reseñas         (endpoints públicos
   Stock            Clientes      CxP          Analítica        lead/track/reviews)
   Movimientos         │            │
        ▲             │            │
        │             ▼            │
        │        04_COTIZADOR      │
        │        Cotizaciones ─────┼──► 05_PROYECTOS ──► 06_VENTAS_COBROS ──► CxC
        │             │            │        │ (descuenta stock vía Core)
        │             │            │        ▼
        │             │            └──► 08_RESULTADOS (P&L · Caja · Alertas · Dash)
        │             │
        └─────────────┴── 02_COMPRAS: recibir_oc ──► entrada de stock
```

## 00_CORE — Plataforma

- **FUENTE DE DATOS**: hojas Config, Log; CacheService (tokens).
- **API**: `login`, `logout`, `me`.
- **FUNCIONES CORE**: todas (son la definición del Core).
- **PERMISOS**: emite los tokens; endpoints login/logout públicos.
- **RIESGOS DE MODIFICACIÓN**: ALTOS. Tocar `aplicarMovimiento`, folios o `conErrores`
  afecta a los 11 módulos. Requiere suites fase0 + fase1 en vivo.

## 01_EXISTENCIAS — Productos, almacenes, stock, movimientos

- **DEPENDE DE**: 00_CORE (todo).
- **ALIMENTA A**: 06_VENTAS (stock/costo al vender), 02_COMPRAS (recepción OC),
  05_PROYECTOS (salidas por obra), 08_RESULTADOS (valor de inventario),
  04_COTIZADOR (catálogo/precios).
- **COMPARTE CON**: todos los operativos (hojas Productos/Stock/Movimientos/Almacenes).
- **FUENTE DE DATOS**: Sheets Productos, Almacenes, Stock, Movimientos.
- **API**: GET `productos`, `almacenes`, `stock`, `movimientos`; POST `save_product`,
  `update_precios`, `delete_product`, `restore_product`, `save_almacen`,
  `delete_almacen`, `movimiento`, `import_productos`.
- **FUNCIONES CORE UTILIZADAS**: `aplicarMovimiento` (regla central), `snapStock`,
  `siguienteFolio` (MOV-, LOTE-), `filaPorId`, `hoja`.
- **PERMISOS**: token admin (todo).
- **RIESGOS**: ALTOS. Es el dueño de la invariante de existencias; movimientos históricos
  protegidos; esquemas ENC_PROD/ENC_MOV con columnas posicionales.

## 02_COMPRAS — Proveedores y órdenes de compra

- **DEPENDE DE**: 00_CORE, 01_EXISTENCIAS (entrada de stock al recibir).
- **ALIMENTA A**: 01_EXISTENCIAS (`recibir_oc` → movimientos entrada),
  07_GASTOS_PAGOS (CxP de OC futura; hoy los gastos son manuales).
- **COMPARTE CON**: 01_EXISTENCIAS (productos, almacenes).
- **FUENTE DE DATOS**: Sheets Proveedores, OrdenesCompra, Recepciones.
- **API**: GET `proveedores`, `oc`; POST `save_proveedor`, `delete_proveedor`,
  `save_oc`, `cambiar_estado_oc`, `recibir_oc`.
- **FUNCIONES CORE**: `aplicarMovimiento` (doc ORDEN_COMPRA/RECEPCION), `siguienteFolio` (OC-).
- **PERMISOS**: token admin.
- **RIESGOS**: MEDIOS-ALTOS. `recibir_oc` mueve stock; la recepción es parcial y trazada.

## 03_COMERCIAL — Leads y clientes

- **DEPENDE DE**: 00_CORE.
- **ALIMENTA A**: 04_COTIZADOR (lead → cliente → cotización), 05_PROYECTOS (cliente).
- **COMPARTE CON**: 09_MARKETING (el lead entra por el sitio público).
- **FUENTE DE DATOS**: Sheets Leads, Clientes.
- **API**: GET `leads`, `clientes`; POST `save_cliente`, `delete_cliente`; público `lead`.
- **FUNCIONES CORE**: `nuevoId`, `hoja`, `filaPorId`.
- **PERMISOS**: escritura pública solo en `lead` (con honeypot); lectura/gestión con token.
- **RIESGOS**: BAJOS-MEDIOS. `convertLead` (frontend) copia datos lead→cliente; leads
  viven también en `HOJAS_BORRABLES` (se pueden borrar filas).

## 04_COTIZADOR — Cotizaciones

- **DEPENDE DE**: 00_CORE, 03_COMERCIAL (cliente/lead), 01_EXISTENCIAS (productos/precios).
- **ALIMENTA A**: 05_PROYECTOS (cotización aprobada → crear proyecto).
- **COMPARTE CON**: 03_COMERCIAL (estados quote), 10_SITIO_PUBLICO (captación del lead).
- **FUENTE DE DATOS**: Sheet Cotizaciones; Config (`folio_cotizacion`); localStorage
  del navegador (fotos del borrador `adis_prop_draft` — NO persisten en Sheets).
- **API**: GET `quotes`; POST `quote`, `set_estado_quote`, `crear_proyecto_desde_cotizacion`.
- **FUNCIONES CORE**: `siguienteFolio` (ADIS-), `hoja` (ENC_COTIZ), `filaPorId`.
- **PERMISOS**: token admin.
- **RIESGOS**: MEDIOS. El handler `quote` retrocompatible recibe dos formatos (simple y
  profesional); las fotos solo existen en el navegador que creó la cotización (deuda).

## 05_PROYECTOS — Proyectos / obras

- **DEPENDE DE**: 00_CORE, 03_COMERCIAL, 04_COTIZADOR, 01_EXISTENCIAS (salidas por proyecto).
- **ALIMENTA A**: 06_VENTAS_COBROS (venta ligada a proyecto), 08_RESULTADOS (rentabilidad).
- **COMPARTE CON**: 04_COTIZADOR (cotizacion_id), 06_VENTAS (proyecto_id).
- **FUENTE DE DATOS**: Sheets Proyectos, Proyectos_Movs.
- **API**: GET `proyectos`; POST `save_proyecto`, `proyecto_mov` (tipos: ingreso/
  presupuesto/otro), `cambiar_estado_proyecto`, `crear_proyecto_desde_cotizacion`.
- **FUNCIONES CORE**: `siguienteFolio` (PRY-), `aBase`, `filaPorId`.
- **PERMISOS**: token admin.
- **RIESGOS**: MEDIOS. `proyecto_mov` escribe movimientos financieros del proyecto.

## 06_VENTAS_COBROS — Ventas, cobros, CxC

- **DEPENDE DE**: 00_CORE, 01_EXISTENCIAS (descuenta stock, costo), 05_PROYECTOS.
- **ALIMENTA A**: 08_RESULTADOS (ingresos/utilidad), flujo de caja (cobros).
- **COMPARTE CON**: 01_EXISTENCIAS (Movimientos doc VENTA), 05_PROYECTOS (proyecto_id).
- **FUENTE DE DATOS**: Sheets Ventas, Cobros.
- **API**: GET `ventas`, `cxc`; POST `venta`, `registrar_cobro`, `anular_venta`.
- **FUNCIONES CORE**: `aplicarMovimiento` (salida doc VENTA), compensación best-effort,
  `siguienteFolio` (VEN-, COB-), `aBase`, `snapStock`.
- **PERMISOS**: token admin.
- **RIESGOS**: ALTOS. Es la operación más crítica (multi-hoja, compensación);
  `anular_venta` repone stock con movimientos reverso.

## 07_GASTOS_PAGOS — Gastos, pagos, CxP

- **DEPENDE DE**: 00_CORE (02_COMPRAS solo como referencia futura de proveedor).
- **ALIMENTA A**: 08_RESULTADOS (gastos), flujo de caja (pagos), P&L.
- **COMPARTE CON**: hoja Proveedores se lee en frontend para sugerir (texto libre hoy).
- **FUENTE DE DATOS**: Sheets Gastos, Pagos.
- **API**: GET `gastos`, `pagos`, `cxp`; POST `gasto`, `gasto_pago`/`registrar_pago`,
  `gasto_cancelar`, `delete_gasto`.
- **FUNCIONES CORE**: `siguienteFolio` (GAS-, PAG-), `aBase`, `filaPorId`.
- **PERMISOS**: token admin.
- **RIESGOS**: MEDIOS. `gasto_cancelar` es baja lógica; `delete_gasto` sigue siendo
  borrado físico (Gastos ∈ HOJAS_BORRABLES — decisión a revisar).

## 08_RESULTADOS — P&L, flujo de caja, alertas, dashboard

- **DEPENDE DE**: 06_VENTAS_COBROS, 07_GASTOS_PAGOS, 01_EXISTENCIAS (lectura agregada).
- **ALIMENTA A**: `dash` (dashboard del panel, mismo módulo).
- **COMPARTE CON**: todos (solo lectura; no escribe hojas de negocio, solo consume).
- **FUENTE DE DATOS**: lectura de Ventas, Gastos, Cobros, Pagos, Stock, Cotizaciones.
- **API**: GET `estado_resultados&mes=`, `flujo_caja?desde=&hasta=`, `alertas`.
- **FUNCIONES CORE**: `aBase` (lecturas), `cfg`.
- **PERMISOS**: token admin (solo lectura).
- **RIESGOS**: BAJOS (solo lectura) pero ALTA visibilidad: un cambio en filtros de fecha
  o en la definición de utilidad impacta decisiones del negocio.

## 09_MARKETING — Reseñas y analítica web

- **DEPENDE DE**: 00_CORE, 10_SITIO_PUBLICO (el sitio envía track y muestra reseñas).
- **ALIMENTA A**: 10_SITIO_PUBLICO (reseñas publicadas en testimonios; datos de visitas).
- **COMPARTE CON**: 03_COMERCIAL (leads llegan del sitio).
- **FUENTE DE DATOS**: Sheets Reseñas, Visitas, Visitas_Archivo.
- **API**: GET `reviews` (público), `reviews_admin`, `visitas`; POST `review`,
  `delete_review`, público `track`.
- **FUNCIONES CORE**: `trackProtegido` (rate-limit, dedup, archivo).
- **PERMISOS**: escritura pública en `track`; `reviews` lectura pública; gestión con token.
- **RIESGOS**: MEDIOS. `track` es el endpoint más expuesto a abuso (público + append).

## 10_SITIO_PUBLICO — Sitio web, chatbot, buscador, tracker

- **DEPENDE DE**: 00_CORE (endpoints públicos `lead`/`track`/`reviews`), catálogo en
  Drive (`G:\...\CATALOGO FINAL`, incl. `Material de Facebock/` desde P2), `assets/`.
- **ALIMENTA A**: 03_COMERCIAL (leads), 09_MARKETING (visitas).
- **COMPARTE CON**: 09_MARKETING (reseñas), 00_CORE (products.json → `__adisProducts`).
- **FUENTE DE DATOS**: catálogo Drive + `investigacion_data*.json` + `traducciones_productos.json`.
- **API**: consume `lead`, `track`, `reviews`. No expone API.
- **FUNCIONES CORE**: generador `generar_web.py` (build), no comparte código con el ERP.
- **PERMISOS**: n/a (estático; los endpoints que llama son públicos).
- **RIESGOS**: MEDIOS. Genera `public/` completo; errores rompen el sitio visible.
  **No duplicar fuentes de productos** (ver duplicación ERP/web en CONTEXTO_GLOBAL §6).

## 11_SISTEMA — Configuración, bitácora, ayuda, purga

- **DEPENDE DE**: 00_CORE.
- **ALIMENTA A**: todos (Config: moneda, tipo de cambio, folios).
- **COMPARTE CON**: hojas Config y Log (transversales).
- **FUENTE DE DATOS**: Sheets Config, Log.
- **API**: GET `config`; POST `config`, `delete_row`, `admin_purge`.
- **FUNCIONES CORE**: `cfg`/`cfgSet`, `HOJAS_BORRABLES`.
- **PERMISOS**: token admin. `admin_purge` es acción destructiva (respeta históricos).
- **RIESGOS**: ALTOS en `admin_purge` y `delete_row` (borrado físico controlado por
  lista blanca; Ventas/Movimientos excluidos por diseño).

---

### Matriz resumida

| Módulo | DEPENDE DE | ALIMENTA A | Riesgo de modificación |
|---|---|---|---|
| 00_CORE | — | todos | 🔴 Alto |
| 01_EXISTENCIAS | CORE | 02, 04, 05, 06, 08 | 🔴 Alto |
| 02_COMPRAS | CORE, 01 | 01, 07 | 🟠 Medio-Alto |
| 03_COMERCIAL | CORE | 04, 05 | 🟡 Medio-Bajo |
| 04_COTIZADOR | CORE, 01, 03 | 05 | 🟠 Medio |
| 05_PROYECTOS | CORE, 01, 03, 04 | 06, 08 | 🟠 Medio |
| 06_VENTAS_COBROS | CORE, 01, 05 | 08 | 🔴 Alto |
| 07_GASTOS_PAGOS | CORE | 08 | 🟠 Medio |
| 08_RESULTADOS | CORE, 01, 06, 07 | dash | 🟢 Bajo (solo lectura) |
| 09_MARKETING | CORE, 10 | 10 | 🟠 Medio |
| 10_SITIO_PUBLICO | CORE (público), Drive | 03, 09 | 🟠 Medio |
| 11_SISTEMA | CORE | todos (Config/Log) | 🔴 Alto (purge) |
