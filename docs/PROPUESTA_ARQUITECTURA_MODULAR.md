# 🧩 Propuesta de Arquitectura Modular — Plataforma ADIS

> FASES 1–3 del proceso acordado: auditoría, mapa y propuesta.
> **No se modificó código.** Auditoría realizada el 2026-09-13 sobre el repo en
> `C:\Users\Carlos\Desktop\Pagina` (commit `7419450`, working tree limpio).
> Este documento es la base para decidir la FASE 5 (migración), módulo por módulo.

---

## 1. ESTRUCTURA ACTUAL (lo que existe realmente hoy)

### 1.1 Los tres monolitos

| Artefacto | Líneas | Rol | Problema de escala |
|---|---|---|---|
| `generar_web.py` | 8 944 | Genera TODO el sitio público: 24+ páginas ES/EN, CSS (2 150 líneas en un string), chatbot, buscador, tracker, i18n, sitemap, products.json | Un solo archivo toca marketing, diseño, SEO, datos, chatbot y analítica. Cualquier edición exige cargarlo casi completo |
| `admin/index.html` | 3 093 | Panel ERP completo: 1 bloque `<style>` (283 líneas) + 1 bloque `<script>` (~2 100 líneas), ~150 funciones JS, sidebar ya implementada | Todos los módulos de negocio comparten un solo espacio global. No hay forma de tocar "Ventas" sin convivir con todo el resto |
| `admin/apps-script.gs` | 1 888 | Backend completo: ~25 acciones GET y ~35 handlers POST | Encabezados de hojas duplicados, helpers mezclados con handlers, índices de columna hardcodeados |

**Suma: ~14 000 líneas de código en 3 archivos.** Esta es la razón principal por la que cualquier cambio localizado exige contexto global.

### 1.2 Salida y datos

- `public/` (187 MB, versionado en git): sitio generado + `img/` (753 archivos) + `media/` (94) + `catalogos/` (297) + `admin.html` (copia exacta de `admin/index.html`, verificada idéntica).
- `public/en/`: 24 páginas espejo en inglés.
- Backend de datos: **Google Sheets** (14+ pestañas: Productos, Almacenes, Stock, Movimientos, Ventas, Gastos, Cotizaciones, Leads, Clientes, Proveedores, OrdenesCompra, Proyectos, Proyectos_Movs, Pagos, Cobros, Reseñas, Visitas, Config, Log).
- Fuente del catálogo público: carpeta en Drive (`G:\Mi unidad\ADIS DISEÑO\CATALOGO FINAL`) — **distinta** de la hoja Productos del ERP.
- Datos de investigación/traducción: `investigacion_data.json`, `investigacion_data_en.json`, `traducciones_productos.json` (raíz del proyecto).
- Deploy: GitHub Actions (`deploy.yml`) sirve `public/` en GitHub Pages; dominio propio vía `CNAME`.

### 1.3 Pruebas y scripts

- `scripts/auditoria/`: **11 suites de pruebas vivas** (fase0_api, fase0_regresión, fase1–6_api, cotizador, flujo, movimientos_ui, movimientos_lote_api) + **22 scripts one-off ya ejecutados** (auditorías, fixes, comparadores, importación maestra).
- `scripts/legacy/`: 7 generadores obsoletos.
- `backups/` (ignorado por git, 13 respaldos) y `screenshots/` (ignorado, 76 archivos) — bien aislados.

### 1.4 Basura acumulada en raíz y repo

- `Material de Facebock/`: 39 MB, **38 archivos versionados en git** (videos de Facebook).
- `Informe_Consultoria_UXUI_ADIS_vs_TeknoStep.docx`: 12,7 MB versionado.
- `Formato de Cotizacion nuevo.docx`, `informe_docx_extraido.txt`, `informe_webux.agent.final.md`, `__pycache__/`.
- Docs internos repetidos y desactualizados (ver §5).

---

## 2. SECCIONES DETECTADAS (módulos de negocio reales)

Detectados en el código (no inventados — cada uno tiene handlers backend + UI frontend):

| # | Módulo | Frontend (tabs admin) | Backend (handlers) | Estado |
|---|---|---|---|---|
| A | **Autenticación / Sesión** | login, logout, manejarSesion | `login`, `logout`, `me` | ✅ |
| B | **Existencias** (productos, almacenes, stock, movimientos) | `inventory` (entrada/salida/ajuste/lotes, precios, historial, CSV/imprimir) | `productos`, `almacenes`, `stock`, `movimientos`, `save_product`, `update_precios`, `delete_product`, `restore_product`, `save_almacen`, `delete_almacen`, `movimiento`, `import_productos` | ✅ |
| C | **Compras** (proveedores + órdenes de compra) | `oc` (OC, recepción, proveedores, PDF) | `proveedores`, `oc`, `save_proveedor`, `delete_proveedor`, `save_oc`, `cambiar_estado_oc`, `recibir_oc` | ✅ |
| D | **Comercial** (leads + clientes) | `leads`, `clientes` (directorio, convertir lead) | `leads`, `clientes`, `save_cliente`, `delete_cliente`, `lead`, `convertLead` (implícito) | ✅ |
| E | **Cotizador** | `proposal` (profesional) + `quotes` (historial, aprobar) | `quotes`, `quote`, `set_estado_quote`, `crear_proyecto_desde_cotizacion` | ✅ |
| F | **Proyectos** | `proyectos` (ficha, estados) | `proyectos`, `save_proyecto`, `proyecto_mov`, `cambiar_estado_proyecto` | ✅ |
| G | **Ventas + Cobros (CxC)** | `sales`, `cobros` | `ventas`, `venta`, `cxc`, `registrar_cobro`, `anular_venta` | ✅ |
| H | **Gastos + Pagos (CxP)** | `expenses` | `gastos`, `gasto`, `gasto_pago`/`registrar_pago`, `gasto_cancelar`, `delete_gasto`, `pagos`, `cxp` | ✅ |
| I | **Resultados** (P&L, flujo de caja, alertas, dashboard) | `pnl`, `flujocaja`, `dash` (Resumen + cmdk) | `estado_resultados`, `flujo_caja`, `alertas` | ✅ |
| J | **Marketing** (reseñas, analítica, estadísticas) | `reviews`, `flow`, `analytics` | `reviews`, `reviews_admin`, `review`, `delete_review`, `visitas`, `track` | ✅ (estadísticas = placeholder) |
| K | **Sistema** (config, bitácora, ayuda, purga) | `ayuda` + formularios sueltos | `config`, `getLog` (implícito), `delete_row`, `admin_purge` | ✅ |
| L | **Sitio público** (catálogo, chatbot, buscador, tracker, i18n, calculadora, leads-form, reseñas) | — (fuera del panel) | `lead`, `track`, `reviews` (públicos) | ✅ |
| M | **Infraestructura** (generador, design system, deploy) | — | — | ✅ |

**Hallazgo clave:** el código ya está **más avanzado que la documentación**. La auditoría
del 2026-09-06 y `ADMIN_ARCHITECTURE.md` describen "Fase 0/1", pero el backend ya implementa
Compras, Clientes, Proyectos, Cobros/CxC, Pagos/CxP, Flujo de caja, Alertas, `admin_purge`,
y el frontend ya tiene sidebar agrupada, dashboard (`dash`), buscador Ctrl+K (`cmdk`) y
confirmaciones propias (`confirma`). Las fases 2–7 del Plan Maestro están **en gran parte
ya construidas**; la documentación no lo refleja.

---

## 3. MAPA DE DEPENDENCIAS REAL

```
                 ┌──────────────────────────────────────────────┐
                 │ 00_CORE: Auth(token) · Lock · Errores · CFG  │
                 │ · Folios · aplicarMovimiento() · aBase() ·   │
                 │ · hoja()/esquemas · Google Sheets (14 hojas) │
                 └───────┬───────────────────────┬──────────────┘
                         │                       │
        ┌────────────────┼───────────┬───────────┼────────────────┐
        ▼                ▼           ▼           ▼                ▼
   EXISTENCIAS      COMERCIAL    GASTOS/PAGOS  MARKETING      SITIO PÚBLICO
   (B)              (D)          (H)           (J)            (L)
   Productos        Leads        Gastos        Reseñas        Chatbot/Buscador
   Stock            Clientes     CxP/Pagos     Visitas        Tracker
   Movimientos      │            │             │              Lead form
        ▲          │            │             │              (3 endpoints
        │          ▼            │             │               públicos)
        │      COTIZADOR (E)    │             │
        │      Cotizaciones ────┼──► PROYECTOS (F)
        │          │            │        │
        │          │            │        ▼
        │          │            │   VENTAS+COBROS (G) ──► CxC
        │          │            │        │ (descuenta stock)
        │          │            │        ▼
        └──────────┴────────────┴──► RESULTADOS (I): P&L · Flujo caja · Alertas · Dash
                         ▲
                   COMPRAS (C): recibir_oc ──► entrada de stock (aplicarMovimiento)
```

### Ficha por módulo (resumen — cada CONTEXTO.md la expande)

**EXISTENCIAS (B)**
- *DEPENDE DE:* 00_CORE (auth, cfg, folios, `aplicarMovimiento`, hoja Productos/Stock/Movimientos).
- *ALIMENTA A:* Ventas (stock+costo), Compras (recepción OC), Proyectos (salidas por obra),
  Resultados (valor de inventario, costos), Cotizador (catálogo/precios).
- *COMPARTE DATOS CON:* todos los módulos operativos (hojas Productos/Stock/Movimientos).
- *FUNCIONES COMPARTIDAS:* `aplicarMovimiento()` (regla central: la existencia SOLO cambia aquí),
  `snapStock()`, `filaPorId()`, `siguienteFolio()`.
- *BASE DE DATOS:* Sheets `Productos`, `Almacenes`, `Stock`, `Movimientos`, `Config`.
- *PERMISOS:* token admin.

**COMPRAS (C)** — *DEPENDE DE:* Existencias, Finanzas (CxP). *ALIMENTA A:* Existencias
(`recibir_oc` → entrada automática), Resultados. *BD:* `Proveedores`, `OrdenesCompra`.

**COMERCIAL (D)** — *DEPENDE DE:* Core. *ALIMENTA A:* Cotizador (lead→cotización→cliente),
Proyectos (cliente→proyecto). *BD:* `Leads`, `Clientes`. *Endpoints públicos:* `lead`.

**COTIZADOR (E)** — *DEPENDE DE:* Core, Existencias (productos/precios), Comercial (cliente/lead).
*ALIMENTA A:* Proyectos (cotización aprobada), Comercial (estados). *BD:* `Cotizaciones`, `Config`
(folio). *Nota:* hay **dos** cotizadores en el panel (simple + profesional) — ver §5.

**PROYECTOS (F)** — *DEPENDE DE:* Comercial, Cotizador, Existencias (salidas por proyecto).
*ALIMENTA A:* Ventas, Resultados (rentabilidad). *BD:* `Proyectos`, `Proyectos_Movs`.

**VENTAS+COBROS (G)** — *DEPENDE DE:* Existencias (stock, costo), Proyectos. *ALIMENTA A:*
Resultados (ingresos/utilidad), Flujo de caja (cobros), CxC. *BD:* `Ventas`, `Cobros`.

**GASTOS+PAGOS (H)** — *DEPENDE DE:* Core, Compras (proveedor). *ALIMENTA A:* Resultados,
Flujo de caja (pagos), CxP. *BD:* `Gastos`, `Pagos`.

**RESULTADOS (I)** — *DEPENDE DE:* Ventas, Gastos, Cobros, Pagos (solo lectura agregada).
*ALIMENTA A:* Dashboard (dash). *BD:* lectura de `Ventas`, `Gastos`, `Cobros`, `Pagos`, `Stock`.

**MARKETING (J)** — *DEPENDE DE:* Core. *ALIMENTA A:* Sitio público (reseñas). *BD:*
`Reseñas`, `Visitas`, `Visitas_Archivo`. *Endpoints públicos:* `reviews`, `track`.

**SITIO PÚBLICO (L)** — *DEPENDE DE:* Core (3 endpoints públicos), datos del catálogo en Drive.
*NO* depende del ERP (products.json público **sin costos**, generado del catálogo Drive —
fuente distinta de la hoja Productos; ver §5 problema 5).

---

## 4. ARCHIVOS Y COMPONENTES COMPARTIDOS

### Compartidos por todo (00_CORE material)

| Componente | Ubicación actual | Usado por |
|---|---|---|
| URL del backend Apps Script | **Hardcodeada ×4**: `generar_web.py` L33-34, `admin/index.html` L950, `scripts/auditoria/importar_maestro.py` L13, `test_fase0_api.py` L21 | Sitio + panel + scripts |
| Autenticación (token, límite intentos, logout) | `apps-script.gs` (login/logout/me) + `admin/index.html` (apiGet/apiPost/manejarSesion) | Todo el ERP |
| Helpers backend: `conLock`, `conErrores`, `AdisError`, `cfg/cfgSet`, `snapStock`, `aplicarMovimiento`, `siguienteFolio`, `filaPorId`, `hoja`, `filasComoObjetos`, `aBase` | `apps-script.gs` L1–~430 | Todos los handlers |
| Cliente API JS: `apiGet/apiPost`, `errMsg`, `$`, `esc`, `fmtMoney`, `notice`, `confirma` | `admin/index.html` L962–1050 | Todas las pestañas |
| Esquemas de hojas (ENC_*) y hojas Sheets | `apps-script.gs` (encabezados duplicados ×2-×3) | Todo el backend |
| Folios y contadores Config | `apps-script.gs` + hoja `Config` | Cotizador, Ventas, Movimientos, OC, Proyectos, Gastos, Pagos |
| Sistema de diseño público | `generar_web.py` L1396–3555 (CSS string único, 2 150 líneas: tokens `:root`, botones, tarjetas, tablas, modales, header/footer, chatbot, buscador, responsive) | Las 48 páginas del sitio |
| i18n ES/EN del sitio | `generar_web.py`: `TRANSLATIONS` (L59), `t()`, `i18n()`, `p()`, `set_lang()`, `hreflang_tags()` + 3 JSON en raíz | Sitio público |
| Chatbot + buscador + tracker JS | `generar_web.py` dentro de `generate_footer()` (L4424–6513, ~2 090 líneas dentro de la función) | Todas las páginas públicas |
| Header/footer/mega-menú | `generate_header()` L4311, `generate_footer()` L4424 | Sitio público |
| CSS del panel admin | `admin/index.html` L10–293 (variables propias, distintas del sitio) | Panel |
| products.json (público, sin costos) | generado en `main()` | Buscador + chatbot del sitio |
| `window.__adisProducts` | inyectado por footer del sitio | Buscador + chatbot (compartido) |
| Deploy | `.github/workflows/deploy.yml` (sirve `public/`) + `CNAME` | Todo |

### Funciones duplicadas detectadas

1. **Dos cotizadores** en el panel: simple (`saveQuote`/`quoteData`/`loadQuotes`) y profesional
   (`prop`/`buildProposalHTML`/`saveProposal`). La propia auditoría del 2026-09-06 lo señaló (C.6); sigue pendiente.
2. **Encabezados de hojas duplicados literalmente** en `apps-script.gs` (Movimientos ×3, Productos ×2).
3. **Dos fuentes de productos**: hoja `Productos` (ERP, con costos) vs `products.json` (web, sin costos,
   generado del catálogo Drive). Un producto nuevo se captura dos veces o las fuentes divergen.
4. **Emojis como iconos** persisten en la navegación del panel (la Fase 7 preveía Lucide; no se hizo).
5. **API URL y credenciales** dispersas (ver tabla anterior; credenciales ADMIN_USUARIO/ADMIN_CLAVE
   siguen en el repo — pendiente del dueño desde Fase 0).

---

## 5. PROBLEMAS DE ARQUITECTURA ENCONTRADOS

1. **Monolitos extremos** (3 archivos, ~14 000 líneas): impiden trabajo con contexto mínimo. Es el problema que esta propuesta resuelve.
2. **Documentación desactualizada e inconsistente con el código**: `ADMIN_ARCHITECTURE.md` dice "Fase 0" pero el código tiene fases 2–6 + purga; `HANDOFF.md` menciona "push pendiente" cuando el repo está limpio y al día; `RESUMEN.md` describe un estado de julio. Riesgo real: decisiones futuras basadas en docs falsos.
3. **Backend monolítico** con esquemas duplicados e índices de columna hardcodeados por posición (frágil ante migraciones).
4. **Acoplamiento del frontend del sitio**: chatbot + buscador + tracker viven *dentro* de `generate_footer()`; el footer no es un footer, es medio generador. El header inyecta el buscador. No hay fronteras entre "layout", "componentes interactivos" y "datos".
5. **Divergencia de fuentes de productos** (Sheet vs products.json/Drive) — riesgo de catálogo desalineado web↔ERP.
6. **Configuración dispersa**: URL backend ×4, constantes de negocio en `generar_web.py`, credenciales en el `.gs`, JSON de datos en raíz.
7. **Dos sistemas de diseño**: sitio público (negro/grafito + dorado, CSS en generador) y panel (CSS propio embebido, variables distintas). No hay tokens compartidos ni guía.
8. **Repo pesado y con basura versionada**: 39 MB de videos de Facebook + 12,7 MB de docx + 187 MB de `public/` con media versionada. Clones lentos, riesgo de corrupción (ya ocurrió con Drive/desktop.ini).
9. **Scripts muertos mezclados con vivos** en `scripts/auditoria/` (22 one-off + dataset de 261 productos) y `scripts/legacy/` (7 obsoletos).
10. **Raíz del proyecto como cajón de sastre**: docx, informes, txt extraídos, `__pycache__`, Material de Facebock.
11. **Panel: emojis en nav, `confirm()` residual** (mejorado con `confirma`, pendiente de verificar cobertura), onclick inline por doquier.
12. **Pruebas**: 11 suites vivas pero las de fases 2–6 no están documentadas en `ADMIN_ARCHITECTURE.md` §11 (solo lista fase 0/4/5/6).

---

## 6. ESTRUCTURA DE CARPETAS PROPUESTA

Principio rector: **dos ejes** — capas transversales en `00_CORE` y módulos de negocio numerados.
Cada módulo contiene sus 3 capas (frontend, backend, datos) + su `CONTEXTO.md`, de modo que
trabajar un módulo = leer `00_CORE` + ese módulo. `public/` sigue siendo salida generada
(no se toca a mano; su fuente vive en los módulos).

```
Pagina/
│
├── 00_CORE/                        # Todo lo transversal (la "plataforma")
│   ├── CONTEXTO.md                 # Contexto global (ver §8)
│   ├── config/
│   │   └── plataforma.json         # ÚNICA fuente de URL backend, SITE_URL, WhatsApp, claves de Config
│   ├── design_system/
│   │   ├── tokens.css              # Colores, tipografías, espaciados, radios, sombras
│   │   ├── componentes_publico.css # Botones, tarjetas, tablas, formularios, modales, badges, nav (sitio)
│   │   ├── componentes_admin.css   # Mismo lenguaje, tema claro de panel (sobre tokens compartidos)
│   │   └── UI.md                   # Guía de uso del sistema de diseño
│   ├── i18n/
│   │   ├── translations.py         # TRANSLATIONS + t()/i18n() (extraídos de generar_web.py)
│   │   ├── traducciones_productos.json
│   │   └── investigacion_data.json / _en.json
│   ├── shared_py/                  # Helpers del generador: minify, picture_tag, webp, schemas SEO
│   ├── shared_js/                  # api-client.js, ui.js (notice/confirma/errMsg) — usados por admin y sitio
│   └── auth/                       # Documentación del modelo de auth (token, roles, sesión)
│
├── 01_EXISTENCIAS/                 # Productos, almacenes, stock, movimientos (lotes)
│   ├── CONTEXTO.md
│   ├── admin/   existencias.js + existencias.html (fragmentos)
│   ├── backend/ existencias.gs
│   └── tests/   test_movimientos_ui.py, test_movimientos_lote_api.py, test_fase1_api.py
│
├── 02_COMPRAS/                     # Proveedores + Órdenes de compra + recepción
│   ├── CONTEXTO.md · admin/ · backend/ · tests/ (test_fase2_api.py)
│
├── 03_COTIZADOR/                   # Cotizador profesional + historial + PDF/WhatsApp
│   ├── CONTEXTO.md · admin/ · backend/ · tests/ (test_cotizador_precio_final.py, test_flujo_cotizador.py)
│
├── 04_COMERCIAL/                   # Leads + Clientes
│   ├── CONTEXTO.md · admin/ · backend/ · tests/ (test_fase3_api.py)
│
├── 05_PROYECTOS/                   # Proyectos (ficha financiera, salidas por obra)
│   ├── CONTEXTO.md · admin/ · backend/ · tests/ (test_fase4_api.py)
│
├── 06_VENTAS/                      # Ventas + Cobros + CxC
│   ├── CONTEXTO.md · admin/ · backend/ · tests/ (test_fase4_api.py)
│
├── 07_ADMINISTRACION/              # Gastos + Pagos + CxP
│   ├── CONTEXTO.md · admin/ · backend/ · tests/ (test_fase5_api.py)
│
├── 08_RESULTADOS/                  # P&L + Flujo de caja + Alertas + Dashboard Resumen
│   ├── CONTEXTO.md · admin/ · backend/ · tests/ (test_fase6_api.py)
│
├── 09_MARKETING/                   # Reseñas + Analítica (Flujo) + Estadísticas
│   ├── CONTEXTO.md · admin/ · backend/ · tests/
│
├── 10_SITIO_PUBLICO/               # El sitio web (fuente del generador)
│   ├── CONTEXTO.md
│   ├── generador/    index.py, contacto.py, nosotros.py, privacidad.py, proyectos.py,
│   │                 sabias_que.py, categorias.py, sitemap.py, build.py (main)
│   ├── componentes/  header.py, footer.py, chatbot.py, buscador.py, tracker.py,
│   │                 calculadora.py, tarjetas.py, galerias.py
│   └── media/        (fuentes de public/media: videos, transformaciones, proyecto-*)
│
├── 11_SISTEMA/                     # Config, bitácora, ayuda, purga, importación maestra
│   ├── CONTEXTO.md · admin/ · backend/ (admin_purge, delete_row, import) · tests/
│
├── 50_BUILD/                       # Ensamblado y despliegue
│   ├── build_admin.py              # Concatena 00_CORE/shared_js + admin/*.js + CSS → public/admin.html
│   ├── build_sitio.py              # Orquesta 10_SITIO_PUBLICO → public/ (aquí vive el antiguo main())
│   └── deploy/                     # deploy.yml (documentado; el workflow real sigue en .github/)
│
├── 60_DATA/                        # Pipeline de datos
│   ├── catalogo_drive.md           # Documentación de la fuente en Drive (solo lectura)
│   ├── importar_maestro.py         # Migración Excel→Sheets (ya ejecutada; conservada por trazabilidad)
│   └── dataset_maestro.json
│
├── 90_ARCHIVO/                     # Nada de esto se lee para trabajar (git puede dejar de trackearlo)
│   ├── legacy/                     # scripts/legacy + one-off de auditoría ya ejecutados
│   ├── material_facebook/          # (hoy "Material de Facebock", 39 MB)
│   └── documentos_fuentes/         # docx de cotización/informe/investigación
│
├── 99_DOCUMENTACION/
│   ├── MAPA_PLATAFORMA.md          # Mapa de módulos + dependencias (este doc, mantenido)
│   ├── ARQUITECTURA_BACKEND.md     # Sucesor de ADMIN_ARCHITECTURE.md (estado REAL del código)
│   ├── HISTORIAL_CAMBIOS.md        # Log de decisiones arquitectónicas
│   └── sesiones/                   # RESUMEN_SESION_*.md (rotar; 3-4 recientes)
│
├── public/                         # SALIDA generada (sigue en git por Pages; no se edita a mano)
├── assets/                         # Logo, QR (fuenten de marca)
├── backups/                        # (ignorado por git, como hoy)
└── screenshots/                    # (ignorado por git, como hoy)
```

### Por qué así y no una carpeta plana pura

El ejemplo del usuario (01_EXISTENCIAS…08_RESULTADOS en raíz) funciona para el negocio,
pero hay piezas que **no pertenecen a ningún módulo de negocio** (auth, design system, i18n,
build, deploy) y otras que son **compartidas por todos** (`aplicarMovimiento`, folios, Config).
Si se repartieran por módulo quedarían duplicadas o con dueño ambiguo. Por eso `00_CORE`
centraliza lo transversal y cada módulo declara en su `CONTEXTO.md` qué usa de Core.
Regla: **un módulo solo puede importar de `00_CORE` y de sus dependencias declaradas;
nunca de hermanos directamente.**

---

## 7. QUÉ CONTIENE CADA CONTEXTO.md (plantilla)

```
# CONTEXTO — <NOMBRE_DEL_MODULO>

## Qué hace este módulo
## Qué información maneja
## Archivos del módulo (rutas exactas)
## Base de datos / fuentes (hojas Sheets, columnas que toca)
## APIs / endpoints (GET/POST propios y públicos que expone)
## Funciones principales (frontend y backend, con archivo:línea)
## Entradas que recibe (payloads, parámetros)
## Información que genera (salidas, efectos secundarios, hojas que escribe)
## DEPENDE DE (módulos + piezas de 00_CORE)
## ALIMENTA A (módulos que consumen su información)
## COMPARTE DATOS CON (hojas/estado compartido)
## FUNCIONES COMPARTIDAS que usa (aplicarMovimiento, folios, aBase…)
## PERMISOS NECESARIOS (token admin / endpoints públicos)
## Reglas de negocio que deben respetarse
## QUÉ NO DEBE MODIFICARSE al editar este módulo
## Archivos que deben revisarse ANTES de cambiar algo
## Ejemplos de interacción con otros módulos (flujos reales)
## Pruebas que lo cubren (cómo correrlas)
## Historial de cambios del módulo
```

---

## 8. CONTEXTO GLOBAL (00_CORE/CONTEXTO.md) — qué permanece ahí

1. **Visión de la plataforma**: qué es (catálogo web + mini-ERP sobre Google Sheets, sin servidor propio).
2. **Mapa de módulos numerado** con enlaces a cada `CONTEXTO.md`.
3. **Contrato del backend**: formato de éxito plano `{ok,…}`, error `{ok:false,error:{code,message}}`,
   lista de códigos de error, regla "nunca HTML de Google".
4. **Autenticación y seguridad**: token UUID 8h en CacheService, límite de intentos, endpoints públicos
   (`lead`, `track`, `reviews`, `login`, `logout`), reglas del tracker (rate-limit, dedup, archivo).
5. **Regla central de existencias**: la existencia SOLO cambia por `aplicarMovimiento()` —
   es la invariante #1 de toda la plataforma.
6. **Modelo de datos global**: lista de las 14+ hojas con esquema completo y dueño-módulo por hoja;
   regla "columnas nuevas SIEMPRE al final" (migración aditiva); `HOJAS_BORRABLES`;
   históricos protegidos (Ventas/Movimientos jamás se borran).
7. **Folios e IDs**: formatos (ADIS-, VEN-, MOV-, LOTE-, PRY-, GAS-, PAG-), contadores en Config,
   IDs UUID 8 chars, "nunca número de fila como ID".
8. **Moneda dual**: `moneda_base`, `tipo_cambio`, `aBase()`; regla MXN↔USD.
9. **Integridad transaccional**: `conLock`, validación previa, compensación best-effort, límites reales de Sheets.
10. **Configuración global**: `plataforma.json` (URL backend única, SITE_URL, WhatsApp) y rutina de
    redeploy (✏️ Nueva versión; si la URL cambia, actualizar SOLO `plataforma.json` + rebuild).
11. **Sistema de diseño**: tokens (paleta negro grafito `#0d0d0d`/dorado `#C5A059`/`#E8D5A3`, Montserrat),
    regla "dorado = acento (10%), superficies neutras (90%)", componentes disponibles y guía `UI.md`.
12. **i18n**: patrón `t()/i18n()/p()/set_lang()`, regla "toda ruta relativa con `p()`, todo texto con `t()`".
13. **Build y deploy**: `python 50_BUILD/build_sitio.py`, `build_admin.py`, GitHub Pages desde `public/`.
14. **Lecciones técnicas** (las de RESUMEN_SESION_2026-09-07: búsquedas sin acento, mocks con claves exactas, etc.).
15. **Convenciones**: ES en docs y código del negocio, no renombrar columnas, no tocar `public/` a mano.

## 9. QUÉ PERMANECE EXCLUSIVAMENTE DENTRO DE CADA MÓDULO

- Lógica de UI de sus pestañas (HTML/JS del tab).
- Sus handlers backend y validaciones específicas.
- Sus payloads y formatos de documento (ej. el PDF del cotizador vive solo en 03_COTIZADOR).
- Sus reglas de negocio particulares (ej. "lote todo-o-nada" en Existencias; "gasto ≠ pago" en Administración).
- Sus pruebas.
- Decisiones locales y su historial.

**Ejemplo de frontera:** el módulo Ventas *usa* `aplicarMovimiento()` (de Core/Existencias) pero
no lo modifica; si Ventas necesita un nuevo tipo de documento, se propone el cambio en Existencias,
no se copia la función.

---

## 10. PLAN DE MIGRACIÓN PASO A PASO (FASES 5–7)

> Criterio rector: **cero cambios de comportamiento**. En cada paso el sitio y el panel deben
> quedar byte-equivalentes (salvo rutas internas) y las suites de pruebas deben seguir pasando.

### Pre-migración (acuerdos necesarios del dueño)
- **P0** — Decidir el destino de `Material de Facebock/` (39 MB) y los docx: mover a `90_ARCHIVO/`
  y dejar de trackearlos en git (no afecta el sitio; reduce el repo).
- **P0** — Aprobar la numeración de módulos (§6) o ajustarla a los nombres preferidos.
- **P1** — Rotar `ADMIN_CLAVE` (pendiente desde Fase 0; independiente de esta migración).

### Fase M1 — Cimientos sin mover lógica (bajo riesgo)
1. Crear `00_CORE/config/plataforma.json` con la URL del backend; `generar_web.py` y
   `admin/index.html` lo leen en build. (Elimina la duplicación ×4 sin cambiar salidas.)
2. Extraer el bloque CSS del sitio (L1396–3555) a `00_CORE/design_system/componentes_publico.css`
   + `tokens.css`; el generador lo lee. Mismo contenido, fuera del .py.
3. Extraer `TRANSLATIONS` + helpers i18n a `00_CORE/i18n/`; mover los 3 JSON ahí.
4. **Verificación**: regenerar sitio → `git diff public/` debe mostrar cambios triviales o nulos;
   correr `test_fase0_regresion.py`.

### Fase M2 — Documentación de contexto (sin tocar código)
5. Redactar `00_CORE/CONTEXTO.md` (§8) y `99_DOCUMENTACION/MAPA_PLATAFORMA.md` con el mapa real (§3).
6. Redactar los 11 `CONTEXTO.md` de módulos con el estado ACTUAL del código (esto de paso
   corrige la documentación desactualizada: fases 2–7 ya existen).
7. Reescribir `ARQUITECTURA_BACKEND.md` para reflejar el backend real de 1 888 líneas.

### Fase M3 — Modularizar el sitio público (10_SITIO_PUBLICO)
8. Dividir `generar_web.py` en módulos Python por página/componente (§6). `build_sitio.py`
   ensambla. Misma salida HTML byte-a-byte (verificación con diff de `public/`).
9. Extraer chatbot/buscador/tracker de `generate_footer()` a `10_SITIO_PUBLICO/componentes/`.

### Fase M4 — Modularizar el panel admin (20→09 admin/)
10. Crear `50_BUILD/build_admin.py`: lee `00_CORE/shared_js/` + CSS + `admin/*.js` de cada módulo
    y genera `admin/index.html` (hoy: copia directa). Verificación: byte-equivalente al actual.
11. Después, y solo después, ir moviendo el JS de cada pestaña a su módulo (empezando por el que
    el dueño indique), con `test_fase0_regresion.py` como red de seguridad en cada paso.

### Fase M5 — Modularizar el backend (.gs)
12. Apps Script admite varios archivos `.gs` en el mismo proyecto (scope compartido). Dividir
    `apps-script.gs` en `core.gs` (auth/lock/folios/helpers/esquemas) + `existencias.gs`,
    `compras.gs`, `cotizador.gs`, etc. Mismo comportamiento.
13. Regla: el dueño despliega con ✏️ Nueva versión; suites `test_faseN_api.py` tras cada redeploy
    (ya documentado en cada CONTEXTO.md).

### Fase M6 — Limpieza y validación final
14. Mover one-off scripts a `90_ARCHIVO/legacy/`, suites vivas a `XX_modulo/tests/`.
15. Correr **todas** las suites (API + Playwright + cotizador + movimientos).
16. Actualizar `MAPA_PLATAFORMA.md`, `HISTORIAL_CAMBIOS.md` y el handoff.

### Qué NO se hace en esta migración (decisiones de producto, separadas)
- Unificar los dos cotizadores (propuesta: eliminar el simple, Fase 3 del plan maestro).
- Unificar fuentes de productos (propuesta: `products.json` se genera desde la hoja Productos
  filtrando costos — una sola captura).
- Migrar iconos emoji→SVG en el panel.
- Reemplazar Estadísticas (Looker Studio placeholder).
Cada una se decide y ejecuta dentro de su módulo, con su propio CONTEXTO ya en mano.

---

## 11. RIESGOS Y MITIGACIONES

| Riesgo | Mitigación |
|---|---|
| Romper el sitio al dividir el generador | Verificación byte-a-byte de `public/` tras cada paso (M1–M3) |
| Romper el panel al dividir el HTML | `build_admin.py` produce archivo equivalente; `test_fase0_regresion.py` (19/19) en cada paso |
| Romper el backend al dividir .gs | Apps Script multi-archivo mantiene scope global; suites `test_faseN_api.py` en vivo tras redeploy |
| La documentación vuelva a desactualizarse | Regla: **ningún PR/commit de módulo se acepta sin tocar su `CONTEXTO.md`** si cambia dependencias, hojas o endpoints |
| Pérdida de historial al mover archivos | `git mv` (conserva historia); commits pequeños por módulo |
| Tocar `public/` a mano por costumbre | `public/` se regenera siempre; se añade nota en `00_CORE/CONTEXTO.md` y cabecera generada |

---

*Propuesta generada tras auditoría de código real (sin modificaciones). Próximo paso:
revisión y aprobación por el dueño → ajuste de numeración/nombres → inicio Fase M1,
y luego desarrollo módulo por módulo empezando por la sección que se indique.*
