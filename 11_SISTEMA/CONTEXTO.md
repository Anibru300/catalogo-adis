# ⚙️ 11_SISTEMA — Configuración, Bitácora, Ayuda y Purga

> NIVEL 2 · Lee primero `00_CORE/CONTEXTO_GLOBAL.md` (§6 Config, §7 folios).
> Módulo transversal pequeño pero de **alto riesgo** (operaciones destructivas).
> Fuente: `admin/index.html`, `00_CORE/backend/core.gs` (+ `09_MARKETING/backend/analitica.gs`).

## IDENTIDAD

- **Objetivo**: operar la plataforma: configuración global (moneda, tipo de
  cambio, folios), bitácora de auditoría, ayuda integrada y purga controlada de
  datos.
- **Responsabilidad**: hojas Config y Log; tab `ayuda`; formularios de
  configuración (viven en el tab `inventory` por conveniencia de UI);
  endpoints `config`, `delete_row`, `admin_purge`.
- **Problema que resuelve**: un solo lugar para la configuración del negocio y
  una pista de auditoría de quién hizo qué.

## ALCANCE

- **Hace**: leer/escribir Config (moneda_base, tipo_cambio, contadores de
  folio), registrar Log en cada operación sensible, borrado físico de filas en
  hojas de la lista blanca (`HOJAS_BORRABLES`), purga general de datos de
  prueba, pestaña de ayuda del panel.
- **NO hace**: autenticación (00_CORE), backups de Sheets (Google lo hace),
  gestión de usuarios (no existe multi-usuario aún).
- **Pertenecen aquí**: hojas Config y Log + las acciones de mantenimiento.

## DATOS

- **Hojas**: `Config` (clave, valor), `Log` (fecha, usuario, accion, detalle).
- **Campos importantes**: Config: `moneda_base` (MXN), `tipo_cambio` (MXN por
  1 USD), `folio_cotizacion`, `folio_venta`, `folio_movimiento`, `folio_lote`,
  `folio_gasto`, `folio_pago`, `folio_proyecto`, `folio_cobro`, `folio_oc`.
- **Consume**: todas las operaciones de otros módulos escriben en Log.
- **Genera**: entradas de Log; valores de Config.

## DEPENDENCIAS

- **DEPENDE DE**: `00_CORE` (todo el módulo es Core en ejecución).
- **ALIMENTA A**: **todos** (Config alimenta folios y moneda de 01–07; Log es
  consulta de auditoría).
- **COMPARTE CON**: transversal.

## REGLAS DE NEGOCIO

1. **Config con caché por ejecución** (`cfgMemo`); `cfgSet` invalida al
   escribir — no leer la hoja directamente.
2. **Folios solo vía `siguienteFolio`** bajo LockService; contador de Config
   nunca se edita a mano salvo reset explícito documentado.
3. **`HOJAS_BORRABLES`** = Leads, Cotizaciones, Reseñas, Gastos, Stock, Visitas.
   **Ventas y Movimientos jamás son borrables** (histórico protegido).
4. El usuario admin **no** se escribe en el Log (Fase 0).
5. `admin_purge` respeta los históricos protegidos.

## API / BACKEND

| Endpoint | Tipo | Detalle |
|---|---|---|
| `config` | GET | `{moneda_base, tipo_cambio}` (+ folios en escritura) |
| `config` | POST | Guardar moneda_base/tipo_cambio/folios (token) |
| `delete_row` | POST | `{hoja, id}` → borrado físico SOLO si la hoja ∈ HOJAS_BORRABLES |
| `admin_purge` | POST | Purga de datos de prueba (token; destructivo, protege históricos) |
| `getLog` (implícito en `log_`) | — | La bitácora se escribe con `log_()` en cada handler |

- Handlers: `00_CORE/backend/core.gs` (ex apps-script.gs) L865–879 (config), L1030–1045
  (delete_row), L1776+ (admin_purge). Log: `hoja(SHEET_LOG,…)` L266.
- Errores: `NO_PERMITIDO` (hoja no borrable), `VALIDACION`, `NO_ENCONTRADO`.

## FRONTEND

- **Config**: `showConfigForm` L2306 (moneda y tipo de cambio), `saveConfig`
  L2318 — accesibles desde el menú de Inventario (UI compartida, documentada
  también en 01_EXISTENCIAS).
- **Ayuda**: tab `ayuda` (contenido estático de apoyo al usuario del panel).
- **Bitácora**: lectura vía endpoint en el panel (sección de log).

## PERMISOS

Token admin (rol único). `admin_purge` y `delete_row` son acciones sensibles:
confirmación en UI; solo dueño.

## ARCHIVOS

| Archivo | Responsabilidad |
|---|---|
| `admin/index.html` L2306–2332 (config), tab ayuda | UI del módulo |
| `00_CORE/backend/core.gs` L266 (log_), L295–332 (cfg), L865–879, L1030–1045, L1776+ | handlers |

## INTEGRACIONES

- Sheets (Config, Log) · Apps Script · todos los módulos escriben Log.

## QUÉ NO MODIFICAR

- `HOJAS_BORRABLES`: quitar Ventas/Movimientos de la protección es decisión de
  negocio, no técnica.
- El contrato de Config (lectura plana) — lo consumen todos los módulos.
- Las claves de folio (renombrarlas rompe `siguienteFolio`).

## PRUEBAS

- Cubierto indirectamente por `test_fase0_api.py` (errores por código) y las
  suites de cada módulo (todas escriben Log y leen Config).
- Casos críticos: `delete_row` sobre Ventas → `NO_PERMITIDO`; folio duplicado
  imposible bajo concurrencia (suite fase0 en vivo).
- Tras modificar: suite fase0 en vivo + regresión Playwright.

## EJEMPLOS DE INTERACCIÓN

1. **Venta (06→11)**: cada venta escribe en Log (fecha, acción, folio, usuario).
2. **Purgar pruebas**: tras una sesión de testing, `admin_purge` elimina
   productos/filas de prueba respetando Ventas y Movimientos.
3. **Cambio de moneda**: `saveConfig` actualiza `tipo_cambio` → `cfgSet`
   invalida caché → la siguiente venta convierte con el nuevo tipo de cambio.
