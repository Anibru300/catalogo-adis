# 🧠 CONTEXTO GLOBAL — Plataforma ADIS

> **Este archivo es el NIVEL 1 obligatorio para trabajar en cualquier módulo.**
> Metodología: N1 este archivo → N2 `MODULO/CONTEXTO.md` → N3 archivos y pruebas
> del módulo → N4 otros módulos solo si una dependencia real lo exige.
> Regla: **el código es la fuente de verdad**; si este documento contradice el
> código, el código manda y este archivo debe corregirse.

- Plataforma: catálogo web público + mini-ERP (panel admin), sin servidor propio.
- Stack: generador Python estático → `public/` (GitHub Pages) + panel HTML/JS +
  backend Google Apps Script (V8) sobre Google Sheets.
- Repo: `https://github.com/Anibru300/catalogo-adis.git` · Sitio: `https://xn--adis-diseo-19a.com/`
- Última sincronización de este documento: **2026-09-13** (con el código en commit `7419450`).

---

## 1. Arquitectura general (tres capas)

```
CAPA 1 — CLIENTE
  Sitio público  : public/ (HTML/CSS/JS estático, bilingüe ES/EN)
  Panel admin    : admin/index.html → se copia a public/admin.html en el build
                   (monolito: 1 <style> + 1 <script>; sesión en sessionStorage)
CAPA 2 — BACKEND
  Google Apps Script (V8), fuente modular en `00_CORE/backend/core.gs` +
  `09_MARKETING/backend/analitica.gs`; `admin/apps-script.gs` es el artefacto
  de despliegue que genera `python 50_BUILD/concat_backend.py` (concatenación).
  doGet ?action=X&token=   /   POST text/plain JSON {tipo, token, ...}
  Auth: token UUID en CacheService (8 h). Credenciales en constantes del script.
CAPA 3 — DATOS
  Google Sheets (cuenta ing.carlosurbina300). 20 hojas (ver §6). NO es
  transaccional: LockService + validación previa + compensación best-effort.
```

El sitio público solo usa 3 endpoints **públicos** del backend: `lead`, `track`, `reviews`.

> **Mapeo de líneas (post-M5)**: las referencias `apps-script.gs Lnnn` de los
> CONTEXTO.md de módulo siguen siendo válidas contra `admin/apps-script.gs` y el
> backup `backups/apps_script_pre_m5.gs`. Para localizarlas en `core.gs`: si
> nnn ≥ 263, restar 34 (desplazamiento por la extracción de los clasificadores
> a `analitica.gs`). Las líneas 229–262 viven ahora en `analitica.gs` L1–34.

## 2. Mapa de módulos

| Dir | Módulo | Backend (handlers) | Frontend (tabs admin) |
|---|---|---|---|
| `00_CORE` | Plataforma compartida | core del .gs: auth, lock, folios, `aplicarMovimiento`, esquemas | apiGet/apiPost, CSS admin, helpers JS |
| `01_EXISTENCIAS` | Productos, almacenes, stock, movimientos | `productos`,`almacenes`,`stock`,`movimientos`,`save_product`,`update_precios`,`delete_product`,`restore_product`,`save_almacen`,`delete_almacen`,`movimiento`,`import_productos` | `inventory` |
| `02_COMPRAS` | Proveedores y órdenes de compra | `proveedores`,`save_proveedor`,`delete_proveedor`,`save_oc`,`cambiar_estado_oc`,`recibir_oc` | `oc` |
| `03_COMERCIAL` | Leads y clientes | `leads`,`save_cliente`,`delete_cliente`, + público `lead` | `leads`, `clientes` |
| `04_COTIZADOR` | Cotizador profesional + historial | `quotes`,`quote`,`set_estado_quote`,`crear_proyecto_desde_cotizacion` | `proposal`, `quotes` |
| `05_PROYECTOS` | Proyectos / obras | `proyectos`,`save_proyecto`,`proyecto_mov`,`cambiar_estado_proyecto` | `proyectos` |
| `06_VENTAS_COBROS` | Ventas, cobros, CxC | `ventas`,`venta`,`cxc`,`registrar_cobro`,`anular_venta` | `sales`, `cobros` |
| `07_GASTOS_PAGOS` | Gastos, pagos, CxP | `gastos`,`gasto`,`gasto_pago`,`registrar_pago`,`gasto_cancelar`,`delete_gasto`,`pagos`,`cxp` | `expenses` |
| `08_RESULTADOS` | P&L, flujo de caja, alertas, dashboard | `estado_resultados`,`flujo_caja`,`alertas` | `pnl`, `flujocaja`, `dash` |
| `09_MARKETING` | Reseñas y analítica web | `reviews`,`reviews_admin`,`review`,`delete_review`,`visitas` + público `track` | `reviews`, `flow`, `analytics` |
| `10_SITIO_PUBLICO` | Sitio web, chatbot, buscador, tracker | (los 3 públicos) | — |
| `11_SISTEMA` | Config, bitácora, ayuda, purga | `config`,`delete_row`,`admin_purge`,`getLog` | `ayuda` + formularios de config |

Mapa de relaciones: **`00_CORE/MAPA_DEPENDENCIAS.md`**.

## 3. Reglas globales (invariantes de la plataforma)

1. **La existencia SOLO cambia mediante `aplicarMovimiento()`** (`00_CORE/backend/core.gs`, ex apps-script.gs L380).
   Es la invariante #1. Ningún handler escribe en Stock directamente salvo este camino.
2. **Stock negativo jamás persiste** → `STOCK_INSUFICIENTE`.
3. **Columnas nuevas de hojas SIEMPRE al final** (migración aditiva; `hoja(nombre, enc)`
   garantiza el esquema en cada arranque). Nunca renombrar ni reordenar columnas.
4. **Nunca usar número de fila como identificador** → IDs UUID 8 chars (`nuevoId()`)
   y localización por `filaPorId()`.
5. **Ventas y Movimientos son histórico protegido**: no están en `HOJAS_BORRABLES`
   y jamás se borran (ni `admin_purge` los toca).
6. **`gasto ≠ pago`, `venta ≠ cobro`**: el P&L es contable; el flujo de caja es de
   efectivo real (Cobros−Pagos).
7. **`public/` es salida generada**: no editar a mano; regenerar con el generador.
8. Un módulo solo importa de `00_CORE` y de dependencias declaradas en su CONTEXTO.

## 4. Autenticación y autorización

- Login usuario/clave → token UUID 8 h en CacheService. Límite: 5 intentos/10 min.
- `logout` revoca el token. Token viaja en GET como query param y en POST en el body.
- **Rol único** (admin plano): cualquier token puede todo. No hay roles aún.
- Endpoints públicos (sin token): `login`, `logout`, `lead` (honeypot `empresa`),
  `track` (rate-limit 120 eventos/10 min por huella UA|idioma|ancho + dedup 45 s),
  `reviews` (solo activas).
- Panel: `noindex`, `Disallow: /admin.html`. Protección real = login.
- **Pendiente del dueño**: rotar `ADMIN_CLAVE` (expuesta en el repo).

## 5. Contrato de API

- Éxito: JSON plano `{ok:true, ...campos}` (formato heredado; envelope diferido).
- Error: `{ok:false, error:{code, message}}` — nunca HTML de Google, nunca stack trace.
- Códigos: `TOKEN_INVALIDO`, `CREDENCIALES_INVALIDAS`, `DEMASIADOS_INTENTOS`,
  `JSON_INVALIDO`, `VALIDACION`, `NO_ENCONTRADO`, `NO_PERMITIDO`,
  `CODIGO_DUPLICADO`, `STOCK_INSUFICIENTE`, `TIPO_MOVIMIENTO_INVALIDO`,
  `ACCION_DESCONOCIDA`, `TIPO_DESCONOCIDO`, `ERROR_INTERNO`.
- Frontend: `errMsg()` interpreta ambos formatos (string legacy / objeto nuevo).

## 6. Modelo de datos (Google Sheets, 20 hojas)

Productos · Almacenes · Stock · Movimientos · Ventas · Gastos · Cotizaciones ·
Leads · Clientes · Proveedores · OrdenesCompra · Recepciones · Proyectos ·
Proyectos_Movs · Cobros · Pagos · Reseñas · Visitas · Visitas_Archivo · Config · Log.

- Esquemas exactos: constantes `ENC_*` en `00_CORE/backend/core.gs` (ex apps-script.gs L79–106) (**la fuente oficial**;
  `docs/ADMIN_ARCHITECTURE.md` §3 está desactualizado).
- `Config` (clave/valor): `moneda_base` (MXN), `tipo_cambio` (MXN por 1 USD),
  contadores de folio (ver §7).
- `HOJAS_BORRABLES` = Leads, Cotizaciones, Reseñas, Gastos, Stock, Visitas.
- Dueño-módulo por hoja: ver `MAPA_DEPENDENCIAS.md`.
- `products.json` (público, SIN costos) se genera del **catálogo en Drive** — fuente
  distinta de la hoja Productos del ERP (duplicación conocida, pendiente de resolver).

## 7. Folios e IDs

`siguienteFolio(prefijo, claveCfg, digitos)` bajo LockService (hueco aceptable,
duplicado imposible). IDs internos: UUID 8 chars.

| Folio | Formato | Contador Config | Módulo |
|---|---|---|---|
| Cotización | `ADIS-AAAA-NNN` | `folio_cotizacion` | 04_COTIZADOR |
| Venta | `VEN-AAAA-NNNN` | `folio_venta` | 06_VENTAS_COBROS |
| Movimiento | `MOV-AAAA-NNNNN` | `folio_movimiento` | 01_EXISTENCIAS |
| Lote | `LOTE-AAAA-NNNN` | `folio_lote` | 01_EXISTENCIAS |
| Orden de compra | `OC-AAAA-NNNN` | `folio_oc` | 02_COMPRAS |
| Proyecto | `PRY-AAAA-NNNN` | `folio_proyecto` | 05_PROYECTOS |
| Gasto | `GAS-AAAA-NNNN` | `folio_gasto` | 07_GASTOS_PAGOS |
| Pago | `PAG-AAAA-NNNN` | `folio_pago` | 07_GASTOS_PAGOS |
| Cobro | `COB-AAAA-NNNN` | `folio_cobro` | 06_VENTAS_COBROS |

## 8. Moneda

Dual MXN/USD. `aBase(monto, moneda, tc)` convierte a `moneda_base` usando `tipo_cambio`
de Config. Solo MXN↔USD (`MONEDAS`). Los handlers persisten tanto el monto original
como `monto_base`/`total_base`.

## 9. Integridad transaccional (límites reales de Sheets)

1. `conLock(fn)` — LockService script-level, wait 30 s, release en finally.
2. Validación completa **antes** de escribir (venta: items, cantidades, stock agregado).
3. Compensación best-effort en venta (reverso `doc_tipo=COMPENSACION`; si falla, marca en Log).
4. Borrados lógicos para entidades vivas (producto/almacén/proveedor/cliente → activo=no).

## 10. Diseño global (sistema de diseño)

- **Identidad ADIS**: negro grafito + dorado. Tokens (sitio público, `:root`):
  `--gold:#C5A059`, `--gold-light:#E8D5A3`, `--black:#0F0F0F`, `--dark:#1A1A1A`,
  `--gray:#2A2A2A`, `--light:#F5F5F5`, `--white:#FFFFFF`. Tipografía: Montserrat.
- Regla: dorado = acento (~10%: botones primarios, selección, estados activos,
  bordes de detalle); superficies neutras el resto.
- El CSS del sitio vive como string único en `generar_web.py` L1396–3555 → **pendiente
  M1 → `00_CORE/design-system/`**. El panel admin tiene CSS propio embebido
  (`admin/index.html` L10–293) con las mismas variables base (es el segundo tema).
- Componentes públicos: botones (`.btn-primary` con shine), tarjetas `.card-box`,
  tablas, formularios, modales, badges (`featured_star_badge`, `new-badge`),
  mega-menú, header con topbar dorada, bottom-nav móvil, chatbot flotante.
- Iconos: SVG propios vía `svg_icon()` en el sitio; **el panel aún usa emojis**
  (deuda conocida, Fase 7 parcial).
- Guía detallada por módulo: cada CONTEXTO.md documenta sus componentes.

## 11. i18n (sitio público)

- Infra: `TRANSLATIONS` (generar_web.py L59), `t()`, `i18n()`, `i18n_fmt()`,
  `p(path)` (prefijo `../` para /en/), `set_lang()`, `hreflang_tags()`, `og_locale()`.
- Reglas: toda ruta relativa con `p()`, todo texto visible con `t()`/`i18n()`;
  chatbot con `CHATBOT_I18N` (JS) y `ct()`.
- Datos: `traducciones_productos.json`, `investigacion_data.json`, `_en.json`
  (en raíz → **pendiente M1 → `00_CORE/i18n/`**).
- El **panel admin es solo ES** (no hay i18n en admin).

## 12. Conexiones compartidas y configuración

- **URL del backend**: ✅ centralizada en M1 en `00_CORE/config/plataforma.json`
  (`url_backend`). El generador y los scripts la leen de ahí; `public/admin.html` la recibe
  por inyección en el build. Residual documentado: `admin/index.html` (fuente, M4) y fallbacks
  en scripts de desarrollo.
- `admin/index.html` `CONFIG`: `API_URL`, `LOOKER_STUDIO_URL` (vacío = placeholder),
  `WHATSAPP: '15208392877'`.
- Sitio: `LEADS_URL`, `REVIEWS_URL` (mismo script), `SITE_URL` (punycode).
- `products.json` + `window.__adisProducts` compartidos por buscador y chatbot.

## 13. Build y despliegue

```bash
# Generar todo el sitio (copia admin/index.html → public/admin.html)
"C:\Users\Carlos\AppData\Local\Programs\Python\Python313\python" generar_web.py
# Publicar: git push origin main → GitHub Actions (.github/workflows/deploy.yml) sirve public/
# Backend: `python 50_BUILD/concat_backend.py` y pegar admin/apps-script.gs
  → Implementar → ✏️ Nueva versión (la URL NO debe cambiar).
#   Si la URL cambia: replicarla en los 4 archivos de §12 (hasta M1).
```
- Python 3.13 directo (no hay venv). `desktop.ini` de Windows puede corromper `.git/refs`
  (fix: `find .git/refs -name desktop.ini -type f -delete`).
- Catálogo fuente: `G:\Mi unidad\ADIS DISEÑO\CATALOGO FINAL` (Drive, solo lectura).
- Material de media: ✅ movido (P2, 2026-09-13) a `G:\Mi unidad\ADIS DISEÑO\Material de Facebock`
  (Drive, fuera del repo y **hermana** de CATALOG_DIR: dentro de ella `scan_catalog`
  la tomaría como categoría). La ruta vive en `plataforma.json` (`material_media_dir`,
  absoluta); `sync_media()` la resuelve y requiere G: montado en el build.
  Inventario del movimiento: `99_DOCUMENTACION/INVENTARIO_Y_MOVIMIENTOS_2026-09-13.md`.

## 14. Decisiones arquitectónicas vigentes

1. Tres capas sin servidor propio; Sheets es la única BD (con sus límites documentados §9).
2. Contrato plano heredado; envelope `{ok,data,error}` **diferido** (plan en
   `99_DOCUMENTACION/PLAN_ENVELOPE_API.md`; requiere redeploy coordinado del backend).
3. `products.json` público sin costos; costos solo en hoja Productos (token).
   ✅ P1 (2026-09-13): la hoja es la fuente única de verdad; export versionado en
   `60_DATA/dataset_maestro.json` + puerta de drift `60_DATA/verificar_fuentes.py`
   (ver `00_CORE/config/FUENTES_DE_PRODUCTOS.md`). 251/251 productos cruzados, 0 drift.
4. Movimientos de visitas se archivan (Visitas_Archivo), jamás se borran por tope.
5. Dos cotizadores coexisten en el panel (simple + profesional) — **deuda reconocida**;
   la unificación es decisión de producto pendiente (ver `04_COTIZADOR/CONTEXTO.md`).
6. Documentación modular (esta estructura) como memoria técnica oficial; los docs
   antiguos de `docs/` quedan como históricos (ver `99_DOCUMENTACION/ANALISIS_DOCS_LEGACY.md`).

## 15. Lecciones técnicas (no repetir)

1. En tests, buscar sin acentos (`lambrin` ≠ `Lambrín`) y términos únicos (`pvc` casa con todos los `HJPVC-*`).
2. Los `<details class="mgroup">` del menú se cierran al navegar en tests Playwright: reabrir con evaluate.
3. Esperar options de `<select>` cerrado con `state='attached'` (visible da timeout).
4. Un mock de backend debe devolver las claves exactas que el frontend espera (`ventas`, no `ventass`).
5. `srcset` requiere URL-encoding de espacios en nombres de imagen.
6. iOS: inputs a 16px para evitar zoom automático; `@media (hover:none)` contra sticky-hover.
7. Regenerar siempre con el mismo Python 3.13; no reintroducir venvs rotos.
8. Si el sitio se ve roto tras checkout en Windows: revisar `desktop.ini` en `.git/refs`.

## 16. Convenciones

- Idioma: español (código y documentación del negocio).
- Un commit de módulo que cambie dependencias, hojas o endpoints **debe actualizar
  su `CONTEXTO.md` y, si aplica, este archivo o `MAPA_DEPENDENCIAS.md`**.
- Nada de >1 MB entra al repo sin decisión explícita (ver inventario en 99_DOCUMENTACION).
