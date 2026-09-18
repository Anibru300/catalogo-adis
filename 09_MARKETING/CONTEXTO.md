# ⭐ 09_MARKETING — Reseñas y Analítica Web

> NIVEL 2 · Lee primero `00_CORE/CONTEXTO_GLOBAL.md` (§4 auth: endpoints
> públicos y rate-limit). Módulo de **superficie pública**: es el más expuesto
> a abuso. Fuente: `admin/index.html`, `admin/apps-script.gs`, `generar_web.py`
> (tracker en el footer), `scripts/auditoria/test_flujo_cotizador.py` (parcial).

## IDENTIDAD

- **Objetivo**: gestionar lo que el público ve y genera: reseñas publicadas en
  el sitio y analítica de visitas del sitio web.
- **Responsabilidad**: hojas Reseñas, Visitas, Visitas_Archivo; tabs `reviews`,
  `flow`, `analytics`.
- **Problema que resuelve**: testimonios frescos sin tocar código, y saber de
  dónde viene el tráfico y qué secciones se ven.

## ALCANCE

- **Hace**: publicar/eliminar reseñas (baja lógica `activa`), endpoint público
  de reseñas activas para el sitio, tracker de visitas del sitio (sendBeacon/
  fetch, dedup por sesión, clasificación de origen/dispositivo/navegador),
  panel analítico de visitas (KPIs, barras 30 días, orígenes, páginas vistas),
  retención con archivo automático.
- **NO hace**: captar leads (03 recibe el lead), mostrar las reseñas en el sitio
  (lo hace `10_SITIO_PUBLICO` consumiendo el endpoint público).
- **Pertenecen aquí**: hojas Reseñas/Visitas/Visitas_Archivo, tabs del panel,
  snippet del tracker (hoy dentro de `generar_web.py`).

## DATOS

- **Hojas**: `Reseñas` (ENC_RESENAS: fecha, nombre, estrellas, texto, activa,
  id, usuario — `apps-script.gs` L96), `Visitas` (ENC_VISITS: fecha, hora,
  pagina, seccion, origen, referrer, idioma, dispositivo, navegador, ancho, ua —
  L106), `Visitas_Archivo` (mismo esquema, retención).
- **Consume**: eventos `track` del sitio (página, secciones vistas vía
  IntersectionObserver, referrer, idioma, UA, ancho).
- **Genera**: reseñas activas (servidas al sitio), estadísticas agregadas
  (solo lectura en el panel); el excedente de 5000 filas se **archiva**, jamás
  se borra.

## DEPENDENCIAS

- **DEPENDE DE**: `00_CORE` (`trackProtegido`, CacheService para rate-limit);
  `10_SITIO_PUBLICO` (origen de los eventos y del consumo de reseñas).
- **ALIMENTA A**: `10_SITIO_PUBLICO` (reseñas en testimonios; datos de visita).
- **COMPARTE CON**: 03_COMERCIAL (los leads entran desde el mismo sitio).

## REGLAS DE NEGOCIO

1. Solo reseñas `activa=yes` se sirven al sitio (endpoint público `reviews`).
2. `track` es público con **rate-limit 120 eventos/10 min por huella
   (UA|idioma|ancho) + dedup 45 s**; el excedente de 5000 filas activas se
   archiva en Visitas_Archivo (jamás se borra historial) — fuente oficial:
   CONTEXTO_GLOBAL §4 y decisiones vigentes §14.4.
3. Reseñas validan estrellas 1–5 y nombre+texto no vacíos.
4. El tracker **no rastrea admin.html**.

## API / BACKEND

| Endpoint | Tipo | Detalle |
|---|---|---|
| `reviews` | GET **público** | Solo activas: `[{nombre, estrellas, texto, fecha}]` |
| `reviews_admin` | GET | Todas (activas e inactivas), token |
| `visitas` | GET | Hasta 5000 activas (token); se agregan en cliente |
| `review` | POST | Publicar reseña (token) |
| `delete_review` | POST | Baja lógica (token; acepta id + row como respaldo) |
| `track` | POST **público** | `{tipo:'track', pagina, seccion, origen, referrer, idioma, dispositivo, navegador, ancho, ua}` → rate-limit + dedup + append/archivo |

- Handlers: `apps-script.gs` L436–443, L445, L807 (track → `trackProtegido`
  L1845–1887), L836–864. Errores: `VALIDACION`, `NO_ENCONTRADO`.

## FRONTEND (tabs `reviews`, `flow`, `analytics`)

- **Reseñas**: `renderStars` L1943, `addReview` L1946, `loadReviewsAdmin`
  L1954, `deleteReview` L1965.
- **Flujo (analítica)**: `loadFlow` L1205 con `flowBarras` L1196 (barras CSS
  puro, sin librerías): KPIs, 30 días, orígenes, dispositivos, páginas.
- **Estadísticas** (`analytics`): placeholder — iframe Looker Studio solo si
  `CONFIG.LOOKER_STUDIO_URL` está configurada (vacío hoy).

### SEPARACIÓN Negocio / Sitio web (2026-09-17)

Los tabs quedaron divididos por dominio, sin solapamiento:

- **💼 Negocio** (`analytics`, `estadisticas.js`): finanzas — KPIs de ventas
  del mes, utilidad neta, flujo neto 30d y cotizaciones; gráficas Chart.js de
  ventas por mes, gastos por categoría y flujo de caja (zero-fill de días sin
  movimiento). Dinero en formato es-MX (`_estMoney`). La gráfica de ventas
  prefiere el agregado `porMes` del endpoint `ventas` (exacto, sin límite de
  filas) y cae a calcularlo del cliente si el backend aún no se redepliega.
- **🌐 Sitio web** (`flow`, `flujo.js`): analítica del tracker — KPIs de
  visitas (hoy/7/30d, apartados, página más vista), gráfica diaria Chart.js
  (`flowChartDiario`), doughnut de orígenes (`flowChartOrigen`), barras CSS de
  dispositivo/navegador/idioma/páginas/apartados y tabla de últimas 25. Si se
  configura `CONFIG.LOOKER_STUDIO_URL` muestra ese iframe en su lugar (la
  rama Looker se movió aquí desde Estadísticas).
- Helpers Chart.js compartidos (`_estChart`, `cargarChartJS`,
  `_estUltimos30Dias`, `EST_COLORS`) viven en `estadisticas.js`; ambos
  archivos van en el mismo bundle (`flujo.js` antes de `estadisticas.js`).
- Menú, Ctrl+K (admin_nav.js) y Ayuda renombrados: "Negocio" y "Sitio web".
- Smoke test: `scripts/auditoria/cap_estadisticas.py` cubre ambos tabs.
- **Tracker** (en el sitio): snippet dentro de `generate_footer()`
  (`generar_web.py` L4424–4532): sendBeacon/fetch con dedup por sesión;
  clasificadores `origenDe_`/`dispositivoDe_`/`navegadorDe_` en el backend.
- **Reseñas en el sitio**: `generate_testimonios()` (`generar_web.py` L8091)
  mantiene 4 tarjetas estáticas (fallback/SEO) y carga las activas al hacer
  scroll (IntersectionObserver) si `REVIEWS_URL` está configurado.

## PERMISOS

- **Público**: `track` (crear), `reviews` (leer activas).
- **Token admin**: gestionar reseñas, ver visitas.

## ARCHIVOS

| Archivo | Responsabilidad |
|---|---|
| `admin/index.html` L1196–1253, L1943–1976 | UI flujo + reseñas |
| `admin/apps-script.gs` L96, L106, L807, L836–864, L1845–1887 | esquemas + handlers + tracker |
| `generar_web.py` L4424–4532 (tracker), L8091 (`generate_testimonios`) | integración con el sitio |
| `scripts/auditoria/test_flujo_cotizador.py` | cubre parcialmente el tab Flujo |

## INTEGRACIONES

- Sheets (3 hojas) · Apps Script · sitio público (tracker + testimonios) ·
  CacheService (rate-limit/dedup).

## QUÉ NO MODIFICAR

- El rate-limit/dedup/archivo del tracker (protección contra bots que saturan
  la hoja — fue un incidente real corregido en Fase 0).
- El formato público de `reviews` (lo consume el sitio en producción).
- ENC_VISITS: columnas nuevas solo al final (el archivo usa el mismo esquema).

## PRUEBAS

- No hay suite dedicada al tracker; `test_flujo_cotizador.py` cubre el tab con
  backend simulado. Casos manuales: eventos duplicados en <45 s se descartan;
  >5000 filas archivan sin borrar; admin.html no trackea.
- Tras modificar: suite flujo + regresión fase0 + probar endpoint público
  `reviews` y envío de `track` desde el sitio generado.

## EJEMPLOS DE INTERACCIÓN

1. **Publicar reseña (panel→sitio)**: `addReview` → hoja Reseñas (activa) → el
   sitio la carga en testimonios al hacer scroll.
2. **Visita al sitio (10→09)**: cada página envía `track` → clasificadores del
   backend etiquetan origen (Google/Facebook/WhatsApp/directo) y dispositivo →
   el tab Flujo agrega en cliente.
3. **Saturation defense**: un bot que envía 10 000 eventos queda limitado por
   huella y los eventos duplicados se descartan; las filas activas se archivan,
   nunca se pierde historial.
