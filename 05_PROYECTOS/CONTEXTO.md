# 🏗️ 05_PROYECTOS — Proyectos / Obras

> NIVEL 2 · Lee primero `00_CORE/CONTEXTO_GLOBAL.md` (§7 folios, §8 moneda).
> Dependencias reales: `01_EXISTENCIAS` (salidas por obra) y `04_COTIZADOR`
> (creación desde cotización). Fuente: `admin/index.html`, `admin/apps-script.gs`,
> `scripts/auditoria/test_fase4_api.py`, `test_fase6_api.py` (P&L por proyecto).

## IDENTIDAD

- **Objetivo**: administrar cada obra como una entidad con ficha financiera:
  cliente, presupuesto, estado, movimientos de dinero/material, y rentabilidad.
- **Responsabilidad**: hojas Proyectos y Proyectos_Movs; tab `proyectos`.
- **Problema que resuelve**: saber por obra cuánto se presupuestó, cuánto entró,
  cuánto se gastó en material (salidas de almacén) y cuánto queda.

## ALCANCE

- **Hace**: CRUD de proyectos, creación desde cotización aprobada, estados
  (ACTIVO/CANCELADO/FINALIZADO…), movimientos financieros del proyecto
  (ingresos/presupuestos/otros), ligar salidas de almacén a la obra.
- **NO hace**: vender (06), cotizar (04), mover stock (la salida la registra 01
  con `documento_tipo=PROYECTO`), calcular el P&L global (08 lo consume).
- **Pertenecen aquí**: hojas Proyectos, Proyectos_Movs; tab `proyectos`.

## DATOS

- **Hojas**: `Proyectos` (ENC_PROY: id, folio, nombre, cliente_id, cliente,
  cotizacion_id, cotizacion_folio, estado, moneda, presupuesto, cobrado, creado,
  usuario, notas — ver `apps-script.gs` L99), `Proyectos_Movs` (ENC_PROY_MOVS:
  id, proyecto_id, tipo, monto, moneda, tipo_cambio, monto_base, fecha, usuario,
  descripcion, doc_tipo, doc_id — L94).
- **Consume**: cliente (03), cotización (04), Config (`folio_proyecto`,
  `tipo_cambio`).
- **Genera**: proyectos con folio PRY-AAAA-NNNN, movimientos financieros por
  proyecto; las **salidas de material** se reflejan en Movimientos (01) con
  `documento_tipo=PROYECTO`.

## DEPENDENCIAS

- **DEPENDE DE**: `00_CORE`; `03_COMERCIAL` (cliente_id); `04_COTIZADOR`
  (creación desde cotización aprobada); `01_EXISTENCIAS` (salidas de material
  ligadas al proyecto).
- **ALIMENTA A**: `06_VENTAS_COBROS` (venta ligada a proyecto: `proyecto_id` en
  Ventas), `08_RESULTADOS` (rentabilidad por proyecto: P&L filtrado por
  proyecto_id en fase 6).
- **COMPARTE DATOS CON**: 01 (Movimientos doc PROYECTO), 06 (Ventas.proyecto_id).

## REGLAS DE NEGOCIO

1. Crear desde cotización **no recaptura datos**: copia cliente_id,
   cotizacion_id/folio y nombre desde la cotización aprobada.
2. Los movimientos del proyecto (`proyecto_mov`) se guardan siempre en moneda base
   (`aBase`) con tipo de cambio de Config — fuente oficial: CONTEXTO_GLOBAL §8.
3. Las salidas de almacén ligadas a obra **priorizan** documento PROYECTO sobre
   LOTE/AJUSTE (regla de 01, implementada en el handler `movimiento`).
4. Los proyectos solo aceptan salidas de material mientras están ACTIVOS (el
   selector de proyectos del formulario de salida filtra por estado).

## API / BACKEND

| Endpoint | Tipo | Detalle |
|---|---|---|
| `proyectos` | GET | Lista con datos agregados |
| `save_proyecto` | POST | Crear/editar proyecto (folio PRY- si es nuevo) |
| `proyecto_mov` | POST | `{proyecto_id, tipo: ingreso/presupuesto/otro, monto, moneda, descripcion}` |
| `cambiar_estado_proyecto` | POST | Transición de estado |
| `crear_proyecto_desde_cotizacion` | POST | `{quote_id}` → proyecto (documentado en 04) |

- Handlers: `apps-script.gs` L1421–1517. Errores: `VALIDACION`, `NO_ENCONTRADO`.

## FRONTEND (tab `proyectos`)

- **Vista**: lista de proyectos con estado y acciones; ficha del proyecto.
- **Funciones clave**: `loadProyectos` L2598, `renderProyectos` L2606,
  `crearProyectoDesdeSelect` L2631, `crearProyectoDesdeQuote` L2634,
  `showProyectoForm` L2639, `saveProyecto` L2650, `cambiarEstadoProyecto` L2664,
  `fichaProyecto` L2999, `saveProyectoMov` L3028.
- **Navegación**: el selector de proyecto en el formulario de salida de material
  (01) lista proyectos ACTIVOS; desde ventas (06) se liga `fillSaleLinks` L2774.

## PERMISOS

Token admin (rol único). Sin endpoints públicos.

## ARCHIVOS

| Archivo | Responsabilidad |
|---|---|
| `admin/index.html` L2598–2670, L2999–3038 | UI proyectos + ficha |
| `admin/apps-script.gs` L94, L99, L1421–1517 | esquemas + handlers |
| `scripts/auditoria/test_fase4_api.py` | suite API (proyectos, cobros) |
| `scripts/auditoria/test_fase6_api.py` | P&L por proyecto + anuladas excluidas |

## INTEGRACIONES

- Sheets (2 hojas) · Apps Script · 04 (cotización origen) · 01 (salidas doc
  PROYECTO) · 06 (ventas con proyecto_id) · 08 (rentabilidad por proyecto).

## QUÉ NO MODIFICAR

- El contrato de `crear_proyecto_desde_cotizacion` (lo llaman el historial del
  cotizador y las pruebas).
- La prioridad de documento PROYECTO en el handler `movimiento` (regla de 01).
- ENC_PROY / ENC_PROY_MOVS: columnas nuevas solo al final.

## PRUEBAS

- `python scripts/auditoria/test_fase4_api.py` (tras redeploy).
- `python scripts/auditoria/test_fase6_api.py` (P&L por proyecto).
- Casos críticos: crear desde cotización copia cliente; movimiento convierte
  moneda correctamente; salida de material ligada aparece en la ficha.
- Tras modificar: fase4 + fase6 + regresión fase0.

## EJEMPLOS DE INTERACCIÓN

1. **Aprobación → obra (04→05)**: cotización aprobada → proyecto con folio
   PRY- nuevo → aparece en la lista y en el selector de salidas de material.
2. **Material a obra (05←01)**: salida de almacén con `proyecto_id` →
   Movimientos con `documento_tipo=PROYECTO` → visible en la ficha del proyecto.
3. **Facturación de la obra (05→06)**: venta con `proyecto_id` → CxC y P&L
   del proyecto en 08.
