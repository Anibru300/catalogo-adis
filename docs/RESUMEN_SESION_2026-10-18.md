# Resumen de sesión — 2026-10-18

## Contexto

Dinámica acordada con el dueño: **capturar los ingresos y egresos de Adis,
catalogarlos y presentarlos en el dashboard**, dejando todo asentado en la mesa
para que cada sesión continúe sin re-explicar el sistema.

Diagnóstico de entrada: la captura de egresos ya existía (tab Gastos, folios
GAS-/PAG-), pero no había forma de registrar **ingresos que no vienen de una
venta** (reembolsos, venta de activos), las **categorías eran una lista fija
hardcodeada** en el HTML, y el dashboard solo mostraba el mes corriente (sin
evolución histórica de ingresos vs egresos).

## 1. Backend (`00_CORE/backend/core.gs` → `admin/apps-script.gs` vía `concat_backend.py`)

**Fase 0 — drift resuelto:** el desplegado tenía `ventas.porMes` que el canónico
no tenía; se portó a `core.gs`. `core.gs + analitica.gs == apps-script.gs` otra vez.

**Endpoints nuevos (requieren REDEPLOY para activarse):**

- `POST tipo:'ingreso'` `{fecha, concepto, monto, moneda, metodo?, notas?}`
  → folio `ING-AAAA-NNNN` (contador `folio_ingreso` en Config). Escribe en la
  hoja **Cobros** con `venta_id=''` — flujo de caja ya lo cuenta como entrada.
- `POST tipo:'categoria'` `{accion:'agregar'|'quitar', tipo:'gastos'|'ingresos', nombre}`
  → catálogo configurable en hoja `Config` (`categorias_gastos` /
  `categorias_ingresos`, separados por comas). Normaliza nombre (trim +
  mayúscula inicial), rechaza duplicados (case-insensitive). Quitar NO toca
  registros ya capturados.
- `GET action='finanzas_mensual'` → últimos 12 meses en un solo request:
  `{moneda_base, meses:[{mes, ingresos, gastos, por_categoria:{cat:monto}}]}`.
- `GET action='config'` → ahora también devuelve `categorias_gastos[]` y
  `categorias_ingresos[]` (defaults: las 9 de gasto históricas; `Venta de
  activos, Reembolso, Otro ingreso, Otro` para ingresos).

**Refactor:** la lógica de `estado_resultados` se extrajo al helper
`calcularEstadoResultados(mes, proyFiltro)` (reutilizado por `finanzas_mensual`).
Cambio funcional clave: en vista global (sin `proyecto_id`) los **cobros sin
`venta_id` se suman a `ingresos`** (`ingresos_extra`, `num_ingresos_extra`)
**sin doble conteo** — los cobros de ventas ya estaban contados vía hoja Ventas.

## 2. Panel admin

- **DINERO → Cobros**: tarjeta "➕ Otro ingreso" (Fecha, Concepto con datalist,
  Monto, Moneda, Método, Notas) → `addIngreso()` (gastos.js).
- **INVENTARIO → ⚙️ Configuración**: nueva tarjeta "🏷️ Categorías de gastos e
  ingresos" — chips con ✕ (doble clic = confirmar) + alta por tipo
  (`pintarCategoriasConfig`/`agregarCategoria`/`quitarCategoria`).
- **Tab Gastos**: el `<datalist id="gCatList">` ya no está hardcodeado; se llena
  desde config con `poblarCategorias()` (invocado en `loadBiz`). La captura
  sigue aceptando texto libre.
- **Tab Negocio (analytics)**: dos gráficas Chart.js nuevas alimentadas por
  `finanzas_mensual`:
  - `estFinanzasBar` — Ingresos (ventas + otros ingresos) vs Egresos, 12 meses.
  - `estGastosMesBar` — Gastos apilados por categoría (top 5 + Otro), 12 meses.
  - Degradación elegante: si el endpoint aún no existe (sin redeploy), se
    omiten sin error (patrón ya usado en `loadEstadisticas`).

## 3. Verificación

| Prueba | Resultado |
|---|---|
| `node --check` de `core.gs` / `admin/apps-script.gs` / JS ensamblado | ✅ |
| `python 50_BUILD/concat_backend.py` + `build_admin.py` | ✅ (drift 0) |
| Smoke `cap_estadisticas.py` (extendido: 2 canvas nuevos en DOM) | ✅ 11/11 PASS, 0 errores JS (gráficas nuevas SKIP hasta redeploy) |
| Nuevo `cap_tabs_finanzas.py` (Gastos/Cobros/Config) | ✅ forms y gestor renderizan, 0 errores JS |
| Regresión `test_fase0_regresion.py` | ✅ 19/19 PASS, 0 errores JS |
| `60_DATA/verificar_fuentes.py` | ✅ FUENTES CONSISTENTES |
| Capturas | `check_cobros_otro_ingreso.png`, `check_config_categorias.png`, `check_gastos_categorias.png`, `check_estadisticas.png` |

## Pendiente CRÍTICO (lo hace el dueño): REDEPLOY del backend

Activa `ingreso`, `categoria`, `finanzas_mensual` y `categorias_*` en config:

1. Hoja ERP → **Extensiones > Apps Script**.
2. Borrar todo el código y pegar `admin/apps-script.gs` (regenerado, ~2199 líneas).
   ⚠️ Copiar el archivo **recién abierto del disco**.
3. **Implementar > Administrar implementaciones > ✏️ > Versión: Nueva versión > Implementar**
   (NUNCA "Nueva implementación").
4. Esperar 2-5 min de propagación; Ctrl+F `finanzas_mensual` para verificar.
5. Después: INVENTARIO → ⚙️ Configuración → revisar categorías sugeridas
   (aparecen las defaults) y ajustar al gusto; capturar un ingreso de prueba
   en DINERO → Cobros; abrir SITIO WEB → Negocio y ver las 2 gráficas 12m.

## 4. Primera carga de datos reales del dueño (06/10/2026)

El dueño pasó movimientos en crudo; se acomodaron y subieron con el nuevo
script de consola `60_DATA/capturar_movimiento.py` (login + POST a la API,
lee API_URL de admin_core.js; también sirve para captura manual futura).

**Egresos del 06/10/2026 — YA EN LA BASE DE DATOS** (`movimientos_2026-10-06.json`):

| Folio | Categoría | Monto | Descripción |
|---|---|---|---|
| GAS-2026-0001 | Honorarios | $1,500 MXN | Pago al contador |
| GAS-2026-0002 | Gasolina | $500 MXN | Gasolina |
| GAS-2026-0003 | Mantenimiento | $837 MXN | Compra Home Depot |

**Ingresos del 06/10/2026 — PENDIENTES DE REDEPLOY** (`pendientes_ingresos_2026-10-06.json`):

| Concepto | Monto | Nota |
|---|---|---|
| Otro ingreso | $950 USD | el dueño no dio detalle; pendiente de precisar |
| Otro ingreso | $1,600 MXN | pendiente de precisar |
| Venta de esquineros | $560 MXN | |

Subirlos en cuanto el backend se redeploye (comando listo en la sección
"Estado de la mesa"). Después del redeploy también conviene agregar
"Honorarios" al catálogo de categorías (la captura acepta texto libre, pero
conviene tenerla como sugerencia).

## Estado de la mesa (para la próxima sesión)

- ✅ **REDEPLOY HECHO (18-oct)**: `finanzas_mensual`, `ingreso` y `categorias_*`
  en config YA ESTÁN ACTIVOS en producción. Verificado en vivo.
- ✅ **Cargado el día 06/10/2026 completo**: 3 egresos (GAS-0001..0003) + 3
  ingresos (ING-2026-0001: 950 USD, ING-2026-0002: 1,600 MXN, ING-2026-0003:
  560 MXN esquineros) + **sus 3 pagos** (PAG-2026-0001..0003, mismo día 06/10 —
  el dueño confirmó que ya se habían pagado). Octubre: entradas $19,735,
  salidas $2,837, flujo neto $16,898, por pagar $0.
- El script `capturar_movimiento.py` ahora acepta `{"tipo":"pago",
  "gasto_folio":"GAS-..."}` (busca el gasto por folio y liquida el saldo;
  `monto` opcional). **Regla de captura**: cuando el dueño diga que un gasto
  YA se pagó, se registra gasto + pago con la misma fecha.
- ⚠️ **Bug encontrado al probar el endpoint de categorías** (campo `tipo` usado
  como despachador y como clase → choque). Corregido a `clase` (backend +
  frontend + docs, commit `e3c8126`). **Requiere UN SEGUNDO REDEPLOY** (mismos
  pasos, el archivo a pegar sigue siendo `admin/apps-script.gs`, ahora 2201
  líneas). Sin este segundo redeploy, el gestor de categorías del panel
  (INVENTARIO → Configuración) falla; TODO LO DEMÁS ya funciona.
- Tras el segundo redeploy: probar agregar/quitar categoría desde el panel, y
  precisar con el dueño el detalle de los ingresos ING-0001/0002 ("Otro
  ingreso").
- Pendientes de fondo (sin cambio): escáner de código de barras, conteo físico
  asistido, historial de precios, exportar movimientos a Excel, GA4.
- Lección de sesión: los endpoints nuevos deben tener degradación elegante en el
  frontend hasta el redeploy (patrón reutilizado), y el drift core.gs ↔
  apps-script.gs se detecta con un diff simple — conviene hacerlo cada sesión
  que toque backend.

## Archivos tocados

- `00_CORE/backend/core.gs` — helper `calcularEstadoResultados`, `ingreso`,
  `categoria`, `finanzas_mensual`, config + categorías, drift `ventas.porMes`.
- `admin/apps-script.gs` — regenerado (artefacto de despliegue).
- `admin/plantilla.html` — form otro ingreso, datalist vacío, 2 canvas nuevos.
- `07_GASTOS_PAGOS/admin/gastos.js` — `addIngreso`, `poblarCategorias`,
  gestor de categorías.
- `01_EXISTENCIAS/admin/existencias.js` — `loadBiz` pobla categorías;
  `showConfigForm` con tarjeta de categorías.
- `09_MARKETING/admin/estadisticas.js` — `_estPintarFinanzas`,
  `_estPintarGastosMes`, `_estLabelMes`.
- `scripts/auditoria/cap_estadisticas.py` (extendido), `cap_tabs_finanzas.py` (nuevo).
- `60_DATA/capturar_movimiento.py` (nuevo — carga manual/lote de movimientos),
  `60_DATA/movimientos_2026-10-06.json` (egresos capturados),
  `60_DATA/pendientes_ingresos_2026-10-06.json` (a subir tras redeploy).
- Docs: este resumen, `07_GASTOS_PAGOS/CONTEXTO.md`, `08_RESULTADOS/CONTEXTO.md`,
  `docs/ADMIN_ARCHITECTURE.md`, `00_CORE/CONTEXTO_GLOBAL.md`.
